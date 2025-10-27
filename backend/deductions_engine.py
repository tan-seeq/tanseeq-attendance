"""
Unified Deductions Engine for TANSEEQ HR
==========================================
Single source of truth for all attendance deduction calculations.

This engine is used by:
- Dashboard deduction calculations
- Advanced Deductions page
- Monthly deduction calculations
- Custom period calculations
- Payroll integration

Business Rules (VERIFIED):
---------------------------
1. Working Hours: 09:00-18:00 (540 minutes total)
2. Grace Period: 5 minutes (first 5 minutes of late arrival are free)
3. Excluded Employees:
   - Hatem Mohamed Ahmed (حاتم محمد أحمد)
   - Tareq Abdel Moneim Alwazzan (طارق عبد المنعم الوزان)
4. Special Rules:
   - Tariq: No late deduction before 08:00 AM
5. Deduction Formula:
   - DailyRate = basic_salary / total_working_days_in_cycle
   - deduction_amount = (DailyRate / 540) * total_deduction_minutes
   - Where total_deduction_minutes = late_minutes + early_leave_minutes + under_hours_minutes
   - For absences: full DailyRate deduction

Cycle Period:
-------------
- From 29th of previous month to 28th of current month
- Example: October 2025 → 2025-09-29 to 2025-10-28
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
TOTAL_WORKING_MINUTES = 540  # 9 hours total (including break time in calculation)
GRACE_PERIOD_MINUTES = 5  # First 5 minutes are free

EXCLUDED_EMPLOYEES = [
    "حاتم محمد أحمد",
    "hatem mohamed ahmed",
    "Hatem Mohamed Ahmed",
    "طارق عبد المنعم الوزان",
    "tareq abdel moneim alwazzan",
    "Tareq Abdel Moneim Alwazzan",
    "Tariq Abdel Moneim Alwazzan",
]

# Special rule for Tariq: no late before 08:00
TARIQ_SPECIAL_RULE_TIME = time(8, 0)  # 08:00 AM
TARIQ_NAMES = [
    "طارق",
    "tariq",
    "tareq",
    "Tariq",
    "Tareq",
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
    deductible_minutes: int = 0  # After grace period
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

def is_employee_excluded(employee_name: str) -> bool:
    """
    Check if employee is excluded from deductions.
    
    Excluded employees:
    - Hatem Mohamed Ahmed
    - Tareq/Tariq Abdel Moneim Alwazzan
    """
    if not employee_name:
        return False
    
    name_lower = employee_name.lower().strip()
    
    for excluded in EXCLUDED_EMPLOYEES:
        excluded_lower = excluded.lower().strip()
        if excluded_lower in name_lower or name_lower in excluded_lower:
            return True
    
    return False


def is_tariq_special_rule(employee_name: str) -> bool:
    """
    Check if Tariq's special rule applies (no late before 08:00).
    """
    if not employee_name:
        return False
    
    name_lower = employee_name.lower().strip()
    
    for tariq_name in TARIQ_NAMES:
        if tariq_name.lower() in name_lower:
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
    
    Args:
        cycle_start: Start date of cycle
        cycle_end: End date of cycle
        
    Returns:
        List of working day dates
    """
    working_days = []
    current = cycle_start
    
    while current <= cycle_end:
        # weekday(): Monday=0, Sunday=6
        # Convert to: Sunday=0, Saturday=6
        day_of_week = (current.weekday() + 1) % 7
        
        # Working days: Sunday(0) to Thursday(4)
        if day_of_week <= 4:
            working_days.append(current)
        
        current += timedelta(days=1)
    
    return working_days


def calculate_daily_deduction(
    check_in: Optional[str],
    check_out: Optional[str],
    daily_rate: float,
    employee_name: str,
    work_date: date,
    is_on_leave: bool = False,
    is_public_holiday: bool = False
) -> DailyDeductionDetail:
    """
    Calculate deduction for a single day using unified formula.
    
    Formula:
    --------
    deduction_amount = (DailyRate / 540) * deductible_minutes
    
    Where:
    - DailyRate = basic_salary / total_working_days_in_cycle
    - deductible_minutes = late_minutes + early_leave_minutes + under_hours_minutes (after grace)
    - Grace period: First 5 minutes of late are free
    
    Args:
        check_in: Check-in time string "HH:MM:SS" or None
        check_out: Check-out time string "HH:MM:SS" or None
        daily_rate: Daily rate (basic_salary / working_days)
        employee_name: Employee name (for special rules)
        work_date: Date of work
        is_on_leave: Whether employee is on approved leave
        is_public_holiday: Whether day is a public holiday
        
    Returns:
        DailyDeductionDetail object with all calculations
    """
    detail = DailyDeductionDetail(
        date=work_date.strftime("%Y-%m-%d"),
        check_in=check_in,
        check_out=check_out
    )
    
    # Case 1: Public holiday or approved leave - no deduction
    if is_public_holiday or is_on_leave:
        detail.is_public_holiday = is_public_holiday
        detail.is_on_leave = is_on_leave
        detail.rule_applied = "Public Holiday" if is_public_holiday else "Approved Leave"
        detail.note = "لا يوجد خصم - عطلة رسمية" if is_public_holiday else "لا يوجد خصم - إجازة معتمدة"
        return detail
    
    # Case 2: No check-in - Absent (full daily rate deduction)
    if not check_in:
        detail.is_absent = True
        detail.deduction_amount = daily_rate
        detail.rule_applied = "Full Day Absence"
        detail.note = "غياب - خصم يوم كامل"
        return detail
    
    # Case 3: Check-in but no check-out - treat as absent
    if not check_out:
        detail.is_absent = True
        detail.deduction_amount = daily_rate
        detail.rule_applied = "No Check-out (Treated as Absent)"
        detail.note = "لم يتم تسجيل الانصراف - يعتبر غياب"
        return detail
    
    # Case 4: Normal attendance with check-in and check-out
    try:
        check_in_time = datetime.strptime(check_in, "%H:%M:%S").time()
        check_out_time = datetime.strptime(check_out, "%H:%M:%S").time()
    except:
        # Invalid time format - treat as absent
        detail.is_absent = True
        detail.deduction_amount = daily_rate
        detail.rule_applied = "Invalid Time Format"
        detail.note = "صيغة وقت غير صحيحة - يعتبر غياب"
        return detail
    
    # Calculate late minutes (after 09:00 AM)
    late_minutes = 0
    if check_in_time > WORKING_HOURS_START:
        # Special rule for Tariq: no late before 08:00
        if is_tariq_special_rule(employee_name) and check_in_time < TARIQ_SPECIAL_RULE_TIME:
            late_minutes = 0
            detail.note = "قاعدة خاصة: لا يوجد تأخير قبل 08:00"
        else:
            check_in_dt = datetime.combine(work_date, check_in_time)
            standard_dt = datetime.combine(work_date, WORKING_HOURS_START)
            late_minutes = int((check_in_dt - standard_dt).total_seconds() / 60)
    
    detail.late_minutes = late_minutes
    
    # Calculate early leave minutes (before 18:00 PM)
    early_leave_minutes = 0
    if check_out_time < WORKING_HOURS_END:
        check_out_dt = datetime.combine(work_date, check_out_time)
        standard_dt = datetime.combine(work_date, WORKING_HOURS_END)
        early_leave_minutes = int((standard_dt - check_out_dt).total_seconds() / 60)
    
    detail.early_leave_minutes = early_leave_minutes
    
    # Calculate total work time
    check_in_dt = datetime.combine(work_date, check_in_time)
    check_out_dt = datetime.combine(work_date, check_out_time)
    
    # Handle next-day checkout (rare but possible)
    if check_out_time < check_in_time:
        check_out_dt += timedelta(days=1)
    
    total_minutes_worked = int((check_out_dt - check_in_dt).total_seconds() / 60)
    detail.total_work_minutes = total_minutes_worked
    
    # Calculate under-hours minutes (if worked less than 540 minutes)
    under_hours_minutes = max(0, TOTAL_WORKING_MINUTES - total_minutes_worked)
    detail.under_hours_minutes = under_hours_minutes
    
    # Calculate total deductible minutes
    total_deduction_minutes = late_minutes + early_leave_minutes
    
    # Apply grace period (first 5 minutes are free)
    if total_deduction_minutes > 0 and total_deduction_minutes <= GRACE_PERIOD_MINUTES:
        detail.grace_applied = True
        detail.deductible_minutes = 0
        detail.rule_applied = "Grace Period Applied"
        detail.note = f"داخل حد الجريس ({total_deduction_minutes} دقيقة ≤ {GRACE_PERIOD_MINUTES} دقائق مجانية)"
    else:
        # Deduct grace period from total
        deductible_minutes = max(0, total_deduction_minutes - GRACE_PERIOD_MINUTES)
        detail.deductible_minutes = deductible_minutes
        
        # Calculate deduction using unified formula
        # deduction_amount = (DailyRate / 540) * deductible_minutes
        minute_rate = daily_rate / TOTAL_WORKING_MINUTES
        detail.deduction_amount = round(minute_rate * deductible_minutes, 2)
        
        detail.rule_applied = "Proportional Deduction"
        detail.note = f"خصم متناسب: {deductible_minutes} دقيقة (بعد خصم {GRACE_PERIOD_MINUTES} دقائق جريس)"
    
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
    
    Args:
        db: MongoDB database instance
        employee_id: Employee ID
        employee_name: Employee name
        basic_salary: Monthly basic salary
        cycle_start: Cycle start date
        cycle_end: Cycle end date
        
    Returns:
        EmployeeDeductionSummary with all deduction details
    """
    from public_holidays import is_public_holiday, is_employee_on_approved_leave
    
    # Check if employee is excluded
    if is_employee_excluded(employee_name):
        # Return zero deductions for excluded employees
        return EmployeeDeductionSummary(
            employee_id=employee_id,
            employee_name=employee_name,
            basic_salary=basic_salary,
            cycle_start=cycle_start.strftime("%Y-%m-%d"),
            cycle_end=cycle_end.strftime("%Y-%m-%d"),
            total_working_days=0,
            deduction_details=["موظف معفى من الخصومات"]
        )
    
    # Get working days in cycle
    working_days_list = get_working_days_in_cycle(cycle_start, cycle_end)
    total_working_days = len(working_days_list)
    
    # Calculate daily rate
    daily_rate = basic_salary / total_working_days if total_working_days > 0 else 0
    
    # Get attendance records for this employee in cycle
    cycle_start_str = cycle_start.strftime("%Y-%m-%d")
    cycle_end_str = cycle_end.strftime("%Y-%m-%d")
    
    # ✅ FIX: Use aggregation to get LATEST record per date (handles duplicates)
    # This prevents counting duplicate records multiple times
    attendance_pipeline = [
        {
            "$match": {
                "user_id": employee_id,
                "date": {
                    "$gte": cycle_start_str,
                    "$lte": cycle_end_str
                }
            }
        },
        {
            "$sort": {"date": 1, "created_at": -1}  # Sort by date, then by creation time (latest first)
        },
        {
            "$group": {
                "_id": "$date",  # Group by date to eliminate duplicates
                "record": {"$first": "$$ROOT"}  # Take the first (latest) record for each date
            }
        },
        {
            "$replaceRoot": {"newRoot": "$record"}  # Flatten back to original structure
        },
        {
            "$sort": {"date": 1}  # Sort by date for processing
        }
    ]
    
    attendance_records = await db.attendance.aggregate(attendance_pipeline).to_list(None)
    
    # Create attendance map for quick lookup
    attendance_map = {rec["date"]: rec for rec in attendance_records}
    
    # Initialize summary
    summary = EmployeeDeductionSummary(
        employee_id=employee_id,
        employee_name=employee_name,
        basic_salary=basic_salary,
        cycle_start=cycle_start_str,
        cycle_end=cycle_end_str,
        total_working_days=total_working_days
    )
    
    # Process each working day
    for work_date in working_days_list:
        date_str = work_date.strftime("%Y-%m-%d")
        
        # Check if public holiday
        is_holiday = await is_public_holiday(db, work_date)
        
        # Check if employee on approved leave
        is_on_leave = await is_employee_on_approved_leave(db, employee_id, work_date)
        
        # Get attendance record
        attendance = attendance_map.get(date_str)
        check_in = attendance.get("check_in") if attendance else None
        check_out = attendance.get("check_out") if attendance else None
        
        # Calculate daily deduction
        daily_detail = calculate_daily_deduction(
            check_in=check_in,
            check_out=check_out,
            daily_rate=daily_rate,
            employee_name=employee_name,
            work_date=work_date,
            is_on_leave=is_on_leave,
            is_public_holiday=is_holiday
        )
        
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
            # On leave or holiday - count as present but no deduction
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
    """
    Calculate deductions for all active employees for a given month.
    
    This uses the unified deductions engine for consistent results.
    
    Args:
        db: MongoDB database instance
        month: Month number (1-12)
        year: Year (e.g., 2025)
        
    Returns:
        List of EmployeeDeductionSummary for all employees
    """
    # Get cycle dates
    cycle_start, cycle_end = get_cycle_dates(month, year)
    
    # Get all active employees
    employees = await db.users.find({"is_active": True}).to_list(None)
    
    summaries = []
    
    for emp in employees:
        employee_id = emp["id"]
        employee_name = emp["name"]
        basic_salary = float(emp.get("monthly_salary", 0) or 0)
        
        # Skip if no salary
        if basic_salary <= 0:
            continue
        
        # Calculate deductions for this employee
        summary = await calculate_employee_deductions(
            db=db,
            employee_id=employee_id,
            employee_name=employee_name,
            basic_salary=basic_salary,
            cycle_start=cycle_start,
            cycle_end=cycle_end
        )
        
        summaries.append(summary)
    
    return summaries


async def calculate_custom_period_deductions(
    db: AsyncIOMotorDatabase,
    start_date: date,
    end_date: date
) -> List[EmployeeDeductionSummary]:
    """
    Calculate deductions for all active employees for a custom date range.
    
    Args:
        db: MongoDB database instance
        start_date: Start date of period
        end_date: End date of period
        
    Returns:
        List of EmployeeDeductionSummary for all employees
    """
    # Get all active employees
    employees = await db.users.find({"is_active": True}).to_list(None)
    
    summaries = []
    
    for emp in employees:
        employee_id = emp["id"]
        employee_name = emp["name"]
        basic_salary = float(emp.get("monthly_salary", 0) or 0)
        
        # Skip if no salary
        if basic_salary <= 0:
            continue
        
        # Calculate deductions for this employee
        summary = await calculate_employee_deductions(
            db=db,
            employee_id=employee_id,
            employee_name=employee_name,
            basic_salary=basic_salary,
            cycle_start=start_date,
            cycle_end=end_date
        )
        
        summaries.append(summary)
    
    return summaries
