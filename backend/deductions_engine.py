"""
Advanced Attendance Deduction System for TANSEEQ HR
====================================================
Single source of truth for all attendance deduction calculations.

Business Rules (COMPANY ACTUAL RULES):
---------------------------------------
1. **Grace Period System**:
   - First 15 minutes late × 4 times per month = FREE (مجاناً)
   - After 4 times: Minutes are accumulated and deducted

2. **Late Arrival Rules**:
   - ≤15 minutes (within 4 free times): No deduction
   - >15 to 20 minutes: Deduct actual time (hourly rate)
   - >20 to 60 minutes: Deduct actual time
   - 60-120 minutes (1-2 hours): Half day deduction (نصف يوم)
   - >120 minutes (>2 hours): Full day deduction (يوم كامل)

3. **Absence**: Full day deduction

4. **Excluded Employees**:
   - Hatem Mohamed Ahmed (حاتم محمد أحمد): Flexible schedule (absence only)
   - Tarek Wazzan (طارق عبد المنعم الوزان): Flexible schedule (absence only)
     - Exempt from late/early leave deductions
     - Only absence is counted

5. **Working Hours**: 09:00-18:00 (9 hours)
6. **Cycle Period**: 29th previous month to 28th current month
"""

from datetime import datetime, date, time, timedelta
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field
import uuid


# ============================================
# Configuration Constants
# ============================================

WORKING_HOURS_START = time(9, 0)  # 09:00 AM
WORKING_HOURS_END = time(18, 0)   # 18:00 PM (6:00 PM)
GRACE_PERIOD_MINUTES = 15  # First 15 minutes
MAX_FREE_LATES = 4  # 4 times per month

# Excluded employees
# NOTE: No one is fully exempt anymore. Both Hatem and Tarek follow flexible schedule (absence-only deduction)
FULLY_EXEMPT_EMPLOYEES: List[str] = []

FLEXIBLE_SCHEDULE_EMPLOYEES = [
    # Tarek variants
    "طارق عبد المنعم الوزان",
    "tareq abdel moneim alwazzan",
    "Tareq Abdel Moneim Alwazzan",
    "Tariq Abdel Moneim Alwazzan",
    "Tarek Abdel Moneim Alwazzan",
    "tarek wazzan",
    "Tarek Wazzan",
    # Hatem variants
    "حاتم محمد أحمد",
    "hatem mohamed ahmed",
    "Hatem Mohamed Ahmed",
]


# ============================================
# Models
# ============================================

class DailyDeductionDetail(BaseModel):
    """Details for a single day's deduction calculation"""
    date: str  # YYYY-MM-DD
    check_in: Optional[str] = None  # HH:MM:SS
    check_out: Optional[str] = None  # HH:MM:SS
    is_working_day: bool = True
    is_absent: bool = False
    is_on_leave: bool = False
    is_public_holiday: bool = False
    
    # Time calculations
    late_minutes: int = 0
    early_leave_minutes: int = 0
    under_hours_minutes: int = 0
    total_work_minutes: int = 0
    
    # Deduction calculation
    grace_applied: bool = False
    deductible_minutes: int = 0  # After grace period (for exact-time cases)
    deduction_amount: float = 0.0
    
    # Metadata
    rule_applied: str = ""
    note: str = ""


class EmployeeDeductionSummary(BaseModel):
    """Complete deduction summary for an employee"""
    employee_id: str
    employee_name: str
    basic_salary: float
    
    # Cycle info
    cycle_start: str  # YYYY-MM-DD
    cycle_end: str  # YYYY-MM-DD
    total_working_days: int
    
    # Attendance summary
    days_present: int = 0
    days_absent: int = 0
    days_late: int = 0
    
    # Time summary
    total_late_minutes: int = 0
    total_early_leave_minutes: int = 0
    total_under_hours_minutes: int = 0
    
    # Deduction breakdown
    late_deduction: float = 0.0
    absence_deduction: float = 0.0
    total_deduction: float = 0.0
    
    # Daily details
    daily_records: List[DailyDeductionDetail] = []
    
    # Human-readable details
    deduction_details: List[str] = []


# ============================================
# Helper Functions
# ============================================

def is_fully_exempt(employee_name: str) -> bool:
    """Check if employee is fully exempt from ALL deductions"""
    if not employee_name:
        return False
    
    if not FULLY_EXEMPT_EMPLOYEES:
        return False
    
    name_lower = employee_name.lower().strip()
    for exempt in FULLY_EXEMPT_EMPLOYEES:
        exempt_lower = exempt.lower().strip()
        if exempt_lower in name_lower or name_lower in exempt_lower:
            return True
    return False


def is_flexible_schedule(employee_name: str) -> bool:
    """Check if employee has flexible schedule (Tarek/Hatem)"""
    if not employee_name:
        return False
    
    name_lower = employee_name.lower().strip()
    for flex in FLEXIBLE_SCHEDULE_EMPLOYEES:
        flex_lower = flex.lower().strip()
        if flex_lower in name_lower or name_lower in flex_lower:
            return True
    return False


def get_cycle_dates(month: int, year: int) -> tuple:
    """
    Calculate cycle start and end dates.
    
    Cycle: 29th of previous month to 28th of current month
    Example: October 2025 → 2025-09-29 to 2025-10-28
    
    Args:
        month: Month number (1-12)
        year: Year (e.g., 2025)
        
    Returns:
        Tuple of (cycle_start_date, cycle_end_date)
    """
    # Start: 29th of previous month
    if month == 1:
        cycle_start = date(year - 1, 12, 29)
    else:
        cycle_start = date(year, month - 1, 29)
    
    # End: 28th of current month
    cycle_end = date(year, month, 28)
    
    return cycle_start, cycle_end


def get_working_days_in_cycle(cycle_start: date, cycle_end: date) -> List[date]:
    """
    Get all working days (Sunday-Thursday) in cycle period.
    Excludes Friday (4) and Saturday (5).
    """
    working_days = []
    current = cycle_start
    while current <= cycle_end:
        day_of_week = (current.weekday() + 1) % 7  # Sunday=0
        if day_of_week <= 4:  # Sunday-Thursday
            working_days.append(current)
        current += timedelta(days=1)
    return working_days


def _fmt_time_to_str(t: Optional[time]) -> Optional[str]:
    if not t:
        return None
    return t.strftime("%H:%M:%S")


def calculate_daily_deduction(
    check_in: Optional[str],
    check_out: Optional[str],
    daily_rate: float,
    employee_name: str,
    work_date: date,
    late_count_so_far: int,  # Number of times late this month (before this day)
    is_on_leave: bool = False,
    is_public_holiday: bool = False,
    working_hours: Optional[float] = None,
) -> DailyDeductionDetail:
    """
    Calculate deduction for a single day using COMPANY ACTUAL RULES.

    Rules:
    ------
    1. Grace Period: First 15 minutes late × 4 times per month = FREE
    2. Late >120 minutes: Full day deduction
    3. Late 60-120 minutes: Half day deduction
    4. Otherwise: Deduct exact late time unless grace applied
    5. Absence: Full day deduction
    """
    detail = DailyDeductionDetail(
        date=work_date.strftime("%Y-%m-%d"),
        check_in=check_in,
        check_out=check_out
    )

    # Public holiday or approved leave - no deduction
    if is_public_holiday or is_on_leave:
        detail.is_public_holiday = is_public_holiday
        detail.is_on_leave = is_on_leave
        detail.rule_applied = "Public Holiday" if is_public_holiday else "Approved Leave"
        detail.note = "لا يوجد خصم - عطلة رسمية" if is_public_holiday else "لا يوجد خصم - إجازة معتمدة"
        return detail

    # Support fallback when only working hours are provided (no times)
    if (not check_in or not check_out) and working_hours is not None:
        # Company rule: normal day is 9 hours. Deduct deficit minutes if under 9 hours
        deficit_minutes = max(0, int((9.0 - working_hours) * 60))
        detail.total_work_minutes = int(working_hours * 60)
        if deficit_minutes > 0:
            hourly_rate = daily_rate / 8
            detail.deduction_amount = round((deficit_minutes / 60) * hourly_rate, 2)
            detail.rule_applied = "Under-hours Deduction (hours-only record)"
            detail.note = f"نقص ساعات: {deficit_minutes} دقيقة"
            detail.deductible_minutes = deficit_minutes
        else:
            detail.rule_applied = "On Time (hours-only record)"
            detail.note = "ساعات العمل مكتملة"
        return detail

    # No check-in → Absent (full daily rate deduction)
    if not check_in:
        detail.is_absent = True
        detail.deduction_amount = round(daily_rate, 2)
        detail.rule_applied = "Full Day Absence"
        detail.note = "غياب - خصم يوم كامل"
        detail.deductible_minutes = 540
        return detail

    # Check-in but no check-out → treat as absent
    if not check_out:
        detail.is_absent = True
        detail.deduction_amount = round(daily_rate, 2)
        detail.rule_applied = "No Check-out (Treated as Absent)"
        detail.note = "لم يتم تسجيل الانصراف - يعتبر غياب"
        detail.deductible_minutes = 540
        return detail

    # Parse times safely
    try:
        check_in_time = datetime.strptime(check_in, "%H:%M:%S").time()
        check_out_time = datetime.strptime(check_out, "%H:%M:%S").time()
    except Exception:
        # Invalid time format → treat as absent
        detail.is_absent = True
        detail.deduction_amount = round(daily_rate, 2)
        detail.rule_applied = "Invalid Time Format"
        detail.note = "صيغة وقت غير صحيحة - يعتبر غياب"
        detail.deductible_minutes = 540
        return detail

    # Calculate late minutes (after 09:00 AM)
    late_minutes = 0
    if check_in_time > WORKING_HOURS_START:
        check_in_dt = datetime.combine(work_date, check_in_time)
        standard_dt = datetime.combine(work_date, WORKING_HOURS_START)
        late_minutes = int((check_in_dt - standard_dt).total_seconds() / 60)
    detail.late_minutes = late_minutes

    # Calculate early leave (if before 18:00 PM)
    early_leave_minutes = 0
    if check_out_time < WORKING_HOURS_END:
        check_out_dt = datetime.combine(work_date, check_out_time)
        standard_dt = datetime.combine(work_date, WORKING_HOURS_END)
        early_leave_minutes = int((standard_dt - check_out_dt).total_seconds() / 60)
    detail.early_leave_minutes = early_leave_minutes

    # Calculate total work minutes
    check_in_dt = datetime.combine(work_date, check_in_time)
    check_out_dt = datetime.combine(work_date, check_out_time)
    if check_out_time < check_in_time:
        check_out_dt += timedelta(days=1)
    total_minutes_worked = int((check_out_dt - check_in_dt).total_seconds() / 60)
    detail.total_work_minutes = total_minutes_worked

    # Apply COMPANY RULES for deduction (late arrival based)
    if late_minutes == 0:
        detail.rule_applied = "On Time"
        detail.note = "حضور في الموعد"
        detail.deductible_minutes = 0
        return detail

    hourly_rate = daily_rate / 8  # 8 working hours per day (company convention)

    if late_minutes > 120:
        # >2 hours late → Full day
        detail.deduction_amount = round(daily_rate, 2)
        detail.rule_applied = "Full Day Deduction (>2 hours late)"
        detail.note = f"تأخير أكثر من ساعتين ({late_minutes} دقيقة) - خصم يوم كامل"
        detail.deductible_minutes = 540
    elif late_minutes >= 60:
        # 1-2 hours late → Half day
        detail.deduction_amount = round(daily_rate / 2, 2)
        detail.rule_applied = "Half Day Deduction (1-2 hours late)"
        detail.note = f"تأخير من ساعة إلى ساعتين ({late_minutes} دقيقة) - خصم نصف يوم"
        detail.deductible_minutes = 270
    elif late_minutes <= GRACE_PERIOD_MINUTES and late_count_so_far < MAX_FREE_LATES:
        # Grace period
        detail.grace_applied = True
        detail.deduction_amount = 0.0
        detail.rule_applied = f"Grace Period Applied ({late_count_so_far + 1}/{MAX_FREE_LATES} free)"
        detail.note = f"داخل حد الجريس: {late_minutes} دقيقة (مرة {late_count_so_far + 1} من {MAX_FREE_LATES} مجانية)"
        detail.deductible_minutes = 0
    else:
        # Exact time deduction
        detail.deduction_amount = round((late_minutes / 60) * hourly_rate, 2)
        if late_count_so_far >= MAX_FREE_LATES:
            detail.rule_applied = "Accumulated After Grace Period"
            detail.note = f"تأخير {late_minutes} دقيقة (بعد انتهاء الجريس المجاني)"
        else:
            detail.rule_applied = "Exact Time Deduction (>15 min)"
            detail.note = f"تأخير {late_minutes} دقيقة - خصم بالوقت الفعلي"
        detail.deductible_minutes = late_minutes

    return detail


# ============================================
# Main Calculation Function
# ============================================

async def calculate_employee_deductions(
    db: AsyncIOMotorDatabase,
    employee_id: str,
    employee_name: str,
    basic_salary: float,
    cycle_start: date,
    cycle_end: date
) -> EmployeeDeductionSummary:
    """
    Calculate complete deduction summary for an employee.
    This is the UNIFIED calculation engine used by all parts of the system.
    """
    from public_holidays import is_public_holiday, is_employee_on_approved_leave
    
    # Fully exempt no longer used for Hatem; both are flexible schedule
    if is_fully_exempt(employee_name):
        return EmployeeDeductionSummary(
            employee_id=employee_id,
            employee_name=employee_name,
            basic_salary=basic_salary,
            cycle_start=cycle_start.strftime("%Y-%m-%d"),
            cycle_end=cycle_end.strftime("%Y-%m-%d"),
            total_working_days=0,
            deduction_details=["موظف معفى من جميع الخصومات"],
        )

    # Get working days
    working_days_list = get_working_days_in_cycle(cycle_start, cycle_end)
    total_working_days = len(working_days_list)

    # Daily rate
    daily_rate = basic_salary / total_working_days if total_working_days > 0 else 0

    # Attendance records (latest per date)
    cycle_start_str = cycle_start.strftime("%Y-%m-%d")
    cycle_end_str = cycle_end.strftime("%Y-%m-%d")
    attendance_pipeline = [
        {"$match": {"user_id": employee_id, "date": {"$gte": cycle_start_str, "$lte": cycle_end_str}}},
        {"$sort": {"date": 1, "created_at": -1}},
        {"$group": {"_id": "$date", "record": {"$first": "$$ROOT"}}},
        {"$replaceRoot": {"newRoot": "$record"}},
        {"$sort": {"date": 1}},
    ]
    attendance_records = await db.attendance.aggregate(attendance_pipeline).to_list(None)
    attendance_map = {rec["date"]: rec for rec in attendance_records}

    summary = EmployeeDeductionSummary(
        employee_id=employee_id,
        employee_name=employee_name,
        basic_salary=basic_salary,
        cycle_start=cycle_start_str,
        cycle_end=cycle_end_str,
        total_working_days=total_working_days,
    )

    is_flex_schedule = is_flexible_schedule(employee_name)
    late_count_so_far = 0

    for work_date in working_days_list:
        date_str = work_date.strftime("%Y-%m-%d")
        is_holiday = await is_public_holiday(db, work_date)
        is_on_leave = await is_employee_on_approved_leave(db, employee_id, work_date)

        attendance = attendance_map.get(date_str)
        check_in = attendance.get("check_in") if attendance else None
        check_out = attendance.get("check_out") if attendance else None
        work_hours_val = attendance.get("working_hours") if attendance else None
        try:
            working_hours = float(work_hours_val) if work_hours_val is not None else None
        except Exception:
            working_hours = None

        if is_flex_schedule:
            # Only absence is deducted
            daily_detail = DailyDeductionDetail(date=date_str, check_in=check_in, check_out=check_out)
            if is_holiday or is_on_leave:
                daily_detail.is_public_holiday = is_holiday
                daily_detail.is_on_leave = is_on_leave
                daily_detail.rule_applied = "Public Holiday" if is_holiday else "Approved Leave"
                daily_detail.note = "لا يوجد خصم - عطلة رسمية" if is_holiday else "لا يوجد خصم - إجازة معتمدة"
            elif not check_in:
                daily_detail.is_absent = True
                daily_detail.deduction_amount = round(daily_rate, 2)
                daily_detail.rule_applied = "Full Day Absence (Flexible Schedule)"
                daily_detail.note = "غياب - خصم يوم كامل (ساعات مرنة)"
                daily_detail.deductible_minutes = 540
            else:
                # Present - no deduction for flexible schedule
                if check_in:
                    try:
                        ci_time = datetime.strptime(check_in, "%H:%M:%S").time()
                        if ci_time > WORKING_HOURS_START:
                            ci_dt = datetime.combine(work_date, ci_time)
                            st_dt = datetime.combine(work_date, WORKING_HOURS_START)
                            daily_detail.late_minutes = int((ci_dt - st_dt).total_seconds() / 60)
                    except Exception:
                        pass
                daily_detail.rule_applied = "Flexible Schedule (No Late Deduction)"
                daily_detail.note = "ساعات مرنة - لا يوجد خصم تأخير"
                daily_detail.deduction_amount = 0.0
                daily_detail.deductible_minutes = 0
        else:
            daily_detail = calculate_daily_deduction(
                check_in=check_in,
                check_out=check_out,
                daily_rate=daily_rate,
                employee_name=employee_name,
                work_date=work_date,
                late_count_so_far=late_count_so_far,
                is_on_leave=is_on_leave,
                is_public_holiday=is_holiday,
            )
            # Update late count for grace tracking
            if (
                daily_detail.late_minutes > 0
                and daily_detail.late_minutes <= GRACE_PERIOD_MINUTES
                and daily_detail.grace_applied
            ):
                late_count_so_far += 1

        summary.daily_records.append(daily_detail)

        # Update summary totals
        if daily_detail.is_absent:
            summary.days_absent += 1
            summary.absence_deduction += daily_detail.deduction_amount
        elif not daily_detail.is_on_leave and not daily_detail.is_public_holiday:
            summary.days_present += 1
            if daily_detail.late_minutes > 0 or daily_detail.early_leave_minutes > 0:
                summary.days_late += 1
            summary.total_late_minutes += daily_detail.late_minutes
            summary.total_early_leave_minutes += daily_detail.early_leave_minutes
            summary.total_under_hours_minutes += daily_detail.under_hours_minutes
            summary.late_deduction += daily_detail.deduction_amount
        else:
            summary.days_present += 1

        summary.total_deduction += daily_detail.deduction_amount

    # Round totals
    summary.late_deduction = round(summary.late_deduction, 2)
    summary.absence_deduction = round(summary.absence_deduction, 2)
    summary.total_deduction = round(summary.total_deduction, 2)

    # Build human-readable details
    if summary.days_late > 0:
        summary.deduction_details.append(
            f"• تأخير: {summary.days_late} يوم - {summary.total_late_minutes} دقيقة - {summary.late_deduction:.2f} درهم"
        )
    if summary.days_absent > 0:
        summary.deduction_details.append(
            f"• غياب: {summary.days_absent} يوم - {summary.absence_deduction:.2f} درهم"
        )
    if summary.total_early_leave_minutes > 0:
        summary.deduction_details.append(
            f"• انصراف مبكر: {summary.total_early_leave_minutes} دقيقة"
        )

    return summary


async def calculate_monthly_deductions(
    db: AsyncIOMotorDatabase,
    month: int,
    year: int
) -> List[EmployeeDeductionSummary]:
    """Calculate deductions for all active employees for a given month."""
    cycle_start, cycle_end = get_cycle_dates(month, year)
    employees = await db.users.find({"is_active": True}).to_list(None)

    summaries: List[EmployeeDeductionSummary] = []
    for emp in employees:
        employee_id = emp["id"]
        employee_name = emp["name"]
        basic_salary = float(emp.get("monthly_salary", 0) or 0)
        if basic_salary <= 0:
            continue
        summary = await calculate_employee_deductions(
            db=db,
            employee_id=employee_id,
            employee_name=employee_name,
            basic_salary=basic_salary,
            cycle_start=cycle_start,
            cycle_end=cycle_end,
        )
        summaries.append(summary)
    return summaries


async def calculate_custom_period_deductions(
    db: AsyncIOMotorDatabase,
    start_date: date,
    end_date: date
) -> List[EmployeeDeductionSummary]:
    """Calculate deductions for all active employees for a custom date range."""
    employees = await db.users.find({"is_active": True}).to_list(None)
    summaries: List[EmployeeDeductionSummary] = []
    for emp in employees:
        employee_id = emp["id"]
        employee_name = emp["name"]
        basic_salary = float(emp.get("monthly_salary", 0) or 0)
        if basic_salary <= 0:
            continue
        summary = await calculate_employee_deductions(
            db=db,
            employee_id=employee_id,
            employee_name=employee_name,
            basic_salary=basic_salary,
            cycle_start=start_date,
            cycle_end=end_date,
        )
        summaries.append(summary)
    return summaries
