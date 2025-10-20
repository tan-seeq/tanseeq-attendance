"""
Advanced Attendance Deduction System
=====================================
نظام احتساب خصومات التأخير والانصراف المبكر المتقدم

Business Rules:
- Working days: Sunday to Thursday (exclude Friday & Saturday)
- Working hours: 9:00 AM - 6:00 PM (8 hours + 1 hour break)
- Cycle period: From 29th of previous month to 28th of current month
- Late tolerance: Any minute after 9:00 AM
- Early leave: Any minute before 6:00 PM
- Excluded employees: Hatem Mohamed Ahmed, Tareq Abdel Moneim Alwazzan

Deduction Formula:
deduction_amount = (basic_salary / (working_days_in_cycle * 480)) * deficit_minutes
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date, time, timedelta
import calendar
from motor.motor_asyncio import AsyncIOMotorDatabase


# ============================================
# Models
# ============================================

class AdvancedDeduction(BaseModel):
    """Advanced deduction record for a single day"""
    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    employee_id: str
    employee_name: str
    date: str  # YYYY-MM-DD format
    check_in: Optional[str] = None  # HH:MM:SS
    check_out: Optional[str] = None  # HH:MM:SS
    is_working_day: bool = True  # False for Friday/Saturday
    is_absent: bool = False
    late_minutes: int = 0
    early_leave_minutes: int = 0
    total_work_minutes: int = 0  # Actual work time (excluding break)
    deficit_minutes: int = 0  # Missing minutes from 480
    deduction_amount: float = 0.0
    cycle_start: str  # YYYY-MM-DD
    cycle_end: str  # YYYY-MM-DD
    payroll_cycle_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class EmployeeDeductionSummary(BaseModel):
    """Monthly summary of deductions for an employee"""
    employee_id: str
    employee_name: str
    basic_salary: float
    cycle_start: str
    cycle_end: str
    total_working_days: int  # Only Sun-Thu in the period
    days_present: int
    days_absent: int
    total_late_minutes: int
    total_early_leave_minutes: int
    total_deficit_minutes: int
    total_deduction_amount: float
    daily_records: List[AdvancedDeduction] = []


# ============================================
# Excluded Employees
# ============================================

EXCLUDED_EMPLOYEES = [
    "حاتم محمد أحمد",
    "Hatem Mohamed Ahmed",
    "طارق عبد المنعم الوزان",
    "Tareq Abdel Moneim Alwazzan",
    "Tariq Abdel Moneim Alwazzan",
]


def is_employee_excluded(employee_name: str) -> bool:
    """Check if employee is excluded from deductions"""
    name_lower = employee_name.lower().strip()
    for excluded in EXCLUDED_EMPLOYEES:
        if excluded.lower() in name_lower or name_lower in excluded.lower():
            return True
    return False


# ============================================
# Date Calculations
# ============================================

def get_cycle_dates(month: int, year: int) -> tuple:
    """
    Get cycle start and end dates
    Cycle: 29th of previous month to 28th of current month
    
    Example: October 2025 → 2025-09-29 to 2025-10-28
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
    Get all working days (Sunday-Thursday) in cycle period
    Excludes Friday (4) and Saturday (5)
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


def is_working_day(check_date: date) -> bool:
    """Check if date is a working day (Sun-Thu)"""
    day_of_week = (check_date.weekday() + 1) % 7
    return day_of_week <= 4  # Sunday(0) to Thursday(4)


# ============================================
# Deduction Calculations
# ============================================

def calculate_daily_deduction(
    check_in: Optional[str],
    check_out: Optional[str],
    basic_salary: float,
    total_working_days: int
) -> dict:
    """
    Calculate deduction for a single day
    
    Args:
        check_in: Time string "HH:MM:SS" or None
        check_out: Time string "HH:MM:SS" or None
        basic_salary: Monthly salary
        total_working_days: Number of working days in cycle
        
    Returns:
        dict with late_minutes, early_leave_minutes, deficit_minutes, deduction_amount
    """
    # Standard times
    STANDARD_START = time(9, 0)  # 9:00 AM
    STANDARD_END = time(18, 0)   # 6:00 PM
    REQUIRED_MINUTES = 480       # 8 hours
    BREAK_MINUTES = 60           # 1 hour break
    
    result = {
        "late_minutes": 0,
        "early_leave_minutes": 0,
        "total_work_minutes": 0,
        "deficit_minutes": 0,
        "deduction_amount": 0.0,
        "is_absent": False
    }
    
    # Case 1: No check-in (Absent)
    if not check_in:
        result["is_absent"] = True
        result["deficit_minutes"] = REQUIRED_MINUTES
        # Full day deduction
        minute_rate = basic_salary / (total_working_days * REQUIRED_MINUTES)
        result["deduction_amount"] = minute_rate * REQUIRED_MINUTES
        return result
    
    # Case 2: Check-in but no check-out (treat as absent)
    if not check_out:
        result["is_absent"] = True
        result["deficit_minutes"] = REQUIRED_MINUTES
        minute_rate = basic_salary / (total_working_days * REQUIRED_MINUTES)
        result["deduction_amount"] = minute_rate * REQUIRED_MINUTES
        return result
    
    # Parse times
    try:
        check_in_time = datetime.strptime(check_in, "%H:%M:%S").time()
        check_out_time = datetime.strptime(check_out, "%H:%M:%S").time()
    except:
        # Invalid format, treat as absent
        result["is_absent"] = True
        result["deficit_minutes"] = REQUIRED_MINUTES
        minute_rate = basic_salary / (total_working_days * REQUIRED_MINUTES)
        result["deduction_amount"] = minute_rate * REQUIRED_MINUTES
        return result
    
    # Calculate late minutes (after 9:00 AM)
    if check_in_time > STANDARD_START:
        check_in_dt = datetime.combine(date.today(), check_in_time)
        standard_dt = datetime.combine(date.today(), STANDARD_START)
        result["late_minutes"] = int((check_in_dt - standard_dt).total_seconds() / 60)
    
    # Calculate early leave minutes (before 6:00 PM)
    if check_out_time < STANDARD_END:
        check_out_dt = datetime.combine(date.today(), check_out_time)
        standard_dt = datetime.combine(date.today(), STANDARD_END)
        result["early_leave_minutes"] = int((standard_dt - check_out_dt).total_seconds() / 60)
    
    # Calculate total work time
    check_in_dt = datetime.combine(date.today(), check_in_time)
    check_out_dt = datetime.combine(date.today(), check_out_time)
    
    # Handle next-day checkout (rare but possible)
    if check_out_time < check_in_time:
        check_out_dt += timedelta(days=1)
    
    total_minutes = int((check_out_dt - check_in_dt).total_seconds() / 60)
    
    # Subtract break time
    result["total_work_minutes"] = max(0, total_minutes - BREAK_MINUTES)
    
    # Calculate deficit (missing minutes from required 480)
    result["deficit_minutes"] = max(0, REQUIRED_MINUTES - result["total_work_minutes"])
    
    # Calculate deduction amount
    if result["deficit_minutes"] > 0:
        minute_rate = basic_salary / (total_working_days * REQUIRED_MINUTES)
        result["deduction_amount"] = minute_rate * result["deficit_minutes"]
    
    return result


# ============================================
# Main Calculation Function
# ============================================

async def calculate_monthly_deductions(
    db: AsyncIOMotorDatabase,
    month: int,
    year: int,
    payroll_cycle_id: Optional[str] = None
) -> List[EmployeeDeductionSummary]:
    """
    Calculate advanced deductions for all employees in a cycle
    
    Args:
        db: MongoDB database instance
        month: Month number (1-12)
        year: Year (e.g., 2025)
        payroll_cycle_id: Optional payroll cycle ID to link
        
    Returns:
        List of EmployeeDeductionSummary for all employees (excluding exempted ones)
    """
    from public_holidays import is_public_holiday, is_employee_on_approved_leave
    
    # Get cycle dates
    cycle_start, cycle_end = get_cycle_dates(month, year)
    cycle_start_str = cycle_start.strftime("%Y-%m-%d")
    cycle_end_str = cycle_end.strftime("%Y-%m-%d")
    
    # Get all working days in cycle
    working_days_list = get_working_days_in_cycle(cycle_start, cycle_end)
    total_working_days = len(working_days_list)
    
    print(f"📅 Cycle: {cycle_start_str} to {cycle_end_str}")
    print(f"📊 Working days (Sun-Thu): {total_working_days}")
    
    # Get all active employees
    employees = await db.users.find({"is_active": True}).to_list(None)
    
    summaries = []
    
    for emp in employees:
        employee_id = emp["id"]
        employee_name = emp["name"]
        basic_salary = float(emp.get("monthly_salary", 0) or 0)
        
        # Skip excluded employees
        if is_employee_excluded(employee_name):
            print(f"⏭️ Skipping excluded employee: {employee_name}")
            continue
        
        print(f"\n👤 Processing: {employee_name} (Salary: {basic_salary:.2f})")
        
        # Get attendance records for this employee in cycle
        attendance_records = await db.attendance.find({
            "user_id": employee_id,
            "date": {
                "$gte": cycle_start_str,
                "$lte": cycle_end_str
            }
        }).to_list(None)
        
        # Create a map of date -> attendance
        attendance_map = {rec["date"]: rec for rec in attendance_records}
        
        # Initialize summary
        summary = EmployeeDeductionSummary(
            employee_id=employee_id,
            employee_name=employee_name,
            basic_salary=basic_salary,
            cycle_start=cycle_start_str,
            cycle_end=cycle_end_str,
            total_working_days=total_working_days,
            days_present=0,
            days_absent=0,
            total_late_minutes=0,
            total_early_leave_minutes=0,
            total_deficit_minutes=0,
            total_deduction_amount=0.0,
            daily_records=[]
        )
        
        # Process each working day
        for work_date in working_days_list:
            date_str = work_date.strftime("%Y-%m-%d")
            
            # ✅ Feature 3: Check if public holiday
            is_holiday = await is_public_holiday(db, work_date)
            
            # ✅ Feature 2: Check if employee on approved leave
            is_on_leave = await is_employee_on_approved_leave(db, employee_id, work_date)
            
            # Skip deduction if public holiday or approved leave
            if is_holiday or is_on_leave:
                # Create record but with zero deduction
                daily_record = AdvancedDeduction(
                    employee_id=employee_id,
                    employee_name=employee_name,
                    date=date_str,
                    check_in=None,
                    check_out=None,
                    is_working_day=True,
                    is_absent=False,
                    late_minutes=0,
                    early_leave_minutes=0,
                    total_work_minutes=0,
                    deficit_minutes=0,
                    deduction_amount=0.0,
                    cycle_start=cycle_start_str,
                    cycle_end=cycle_end_str,
                    payroll_cycle_id=payroll_cycle_id
                )
                
                if is_holiday:
                    print(f"   🎉 {date_str}: Public Holiday - No deduction")
                if is_on_leave:
                    print(f"   🏖️ {date_str}: Approved Leave - No deduction")
                
                summary.daily_records.append(daily_record)
                summary.days_present += 1  # Count as present
                continue
            
            # Normal processing for regular working days
            attendance = attendance_map.get(date_str)
            
            check_in = attendance.get("check_in") if attendance else None
            check_out = attendance.get("check_out") if attendance else None
            
            # Calculate daily deduction
            calc = calculate_daily_deduction(
                check_in, check_out, basic_salary, total_working_days
            )
            
            # Create daily record
            daily_record = AdvancedDeduction(
                employee_id=employee_id,
                employee_name=employee_name,
                date=date_str,
                check_in=check_in,
                check_out=check_out,
                is_working_day=True,
                is_absent=calc["is_absent"],
                late_minutes=calc["late_minutes"],
                early_leave_minutes=calc["early_leave_minutes"],
                total_work_minutes=calc["total_work_minutes"],
                deficit_minutes=calc["deficit_minutes"],
                deduction_amount=calc["deduction_amount"],
                cycle_start=cycle_start_str,
                cycle_end=cycle_end_str,
                payroll_cycle_id=payroll_cycle_id
            )
            
            summary.daily_records.append(daily_record)
            
            # Update summary totals
            if calc["is_absent"]:
                summary.days_absent += 1
            else:
                summary.days_present += 1
            
            summary.total_late_minutes += calc["late_minutes"]
            summary.total_early_leave_minutes += calc["early_leave_minutes"]
            summary.total_deficit_minutes += calc["deficit_minutes"]
            summary.total_deduction_amount += calc["deduction_amount"]
        
        print(f"   Present: {summary.days_present}/{total_working_days}")
        print(f"   Total Deduction: {summary.total_deduction_amount:.2f} AED")
        
        summaries.append(summary)
    
    return summaries


# ============================================
# Database Operations
# ============================================

async def save_deductions_to_db(
    db: AsyncIOMotorDatabase,
    summaries: List[EmployeeDeductionSummary]
):
    """Save calculated deductions to database"""
    collection = db.deductions_advanced
    
    # Clear existing records for this cycle
    if summaries:
        first_summary = summaries[0]
        await collection.delete_many({
            "cycle_start": first_summary.cycle_start,
            "cycle_end": first_summary.cycle_end
        })
    
    # Insert all daily records
    all_records = []
    for summary in summaries:
        for record in summary.daily_records:
            all_records.append(record.dict())
    
    if all_records:
        await collection.insert_many(all_records)
        print(f"\n✅ Saved {len(all_records)} deduction records to database")
    
    return len(all_records)


async def get_employee_deduction_summary(
    db: AsyncIOMotorDatabase,
    employee_id: str,
    cycle_start: str,
    cycle_end: str
) -> Optional[dict]:
    """Get deduction summary for a single employee"""
    records = await db.deductions_advanced.find({
        "employee_id": employee_id,
        "cycle_start": cycle_start,
        "cycle_end": cycle_end
    }).to_list(None)
    
    if not records:
        return None
    
    # Aggregate summary
    summary = {
        "employee_id": employee_id,
        "employee_name": records[0]["employee_name"],
        "cycle_start": cycle_start,
        "cycle_end": cycle_end,
        "total_working_days": len([r for r in records if r["is_working_day"]]),
        "days_present": len([r for r in records if not r["is_absent"]]),
        "days_absent": len([r for r in records if r["is_absent"]]),
        "total_late_minutes": sum(r["late_minutes"] for r in records),
        "total_early_leave_minutes": sum(r["early_leave_minutes"] for r in records),
        "total_deficit_minutes": sum(r["deficit_minutes"] for r in records),
        "total_deduction_amount": sum(r["deduction_amount"] for r in records),
        "daily_records": records
    }
    
    return summary
