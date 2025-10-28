"""
Unified Deductions Engine (restored) with:
- October 2025 Calibration (env-controlled, auto-off after 2025-10-31)
- Exceptions by user_id from DB config (flex, partial-flex)
- Flexible: absence only (no late/early)
- Partial-flex: lateness only (no early-leave/under-hours)
- Grace 15 min up to 4 times
- Half day (60-120m late), Full day (>120m late)
- Working window 09:00-18:00
"""
from __future__ import annotations
import os
from datetime import datetime, date, time, timedelta
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel
from config_service import get_exception_type

# Calibration via env and auto-off after 2025-10-31
CALIBRATION_OCTOBER_ENV = os.environ.get("CALIBRATION_OCTOBER", "true").lower() == "true"
CALIB_FROM = date(2025, 9, 29)
CALIB_TO = date(2025, 10, 31)
NO_DATA_NO_DEDUCTION = os.environ.get("NO_DATA_NO_DEDUCTION", "true").lower() == "true"

WORKING_HOURS_START = time(9, 0)
WORKING_HOURS_END = time(18, 0)
GRACE_MIN = 15
MAX_FREE_LATES = 4

class DailyDeductionDetail(BaseModel):
    date: str
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    is_working_day: bool = True
    is_absent: bool = False
    is_on_leave: bool = False
    is_public_holiday: bool = False

    late_minutes: int = 0
    early_leave_minutes: int = 0
    under_hours_minutes: int = 0
    total_work_minutes: int = 0

    grace_applied: bool = False
    deductible_minutes: int = 0
    deduction_amount: float = 0.0

    rule_applied: str = ""
    note: str = ""

class EmployeeDeductionSummary(BaseModel):
    employee_id: str
    employee_name: str
    basic_salary: float
    cycle_start: str
    cycle_end: str
    total_working_days: int

    days_present: int = 0
    days_absent: int = 0
    days_late: int = 0

    total_late_minutes: int = 0
    total_early_leave_minutes: int = 0
    total_under_hours_minutes: int = 0

    late_deduction: float = 0.0
    absence_deduction: float = 0.0
    total_deduction: float = 0.0

    daily_records: List[DailyDeductionDetail] = []
    deduction_details: List[str] = []

# Helpers

def _lower(s: str) -> str:
    return (s or "").strip().lower()

def _parse_time_safe(ts: Optional[str]) -> Optional[time]:
    if not ts:
        return None
    s = ts.strip()
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(s, fmt).time()
        except Exception:
            continue
    return None

def get_cycle_dates(month: int, year: int) -> tuple[date, date]:
    if month == 1:
        return date(year - 1, 12, 29), date(year, month, 28)
    return date(year, month - 1, 29), date(year, month, 28)

def get_working_days_in_cycle(cstart: date, cend: date) -> List[date]:
    days = []
    cur = cstart
    while cur <= cend:
        # Sunday(0) to Thursday(4)
        if ((cur.weekday() + 1) % 7) <= 4:
            days.append(cur)
        cur += timedelta(days=1)
    return days

# Core calculation for a single day

def calculate_daily_deduction(
    check_in: Optional[str],
    check_out: Optional[str],
    working_hours: Optional[float],
    late_count_so_far: int,
    work_date: date,
    hourly_rate: float,
    absence_daily_rate: float,
    is_on_leave: bool = False,
    is_public_holiday: bool = False,
) -> DailyDeductionDetail:
    d = DailyDeductionDetail(date=work_date.isoformat(), check_in=check_in, check_out=check_out)

    # Holidays / Leave
    if is_public_holiday or is_on_leave:
        d.is_public_holiday = is_public_holiday
        d.is_on_leave = is_on_leave
        d.rule_applied = "Public Holiday" if is_public_holiday else "Approved Leave"
        d.note = "لا خصم"
        return d

    # Hours-only record (no times)
    if (not check_in or not check_out) and working_hours is not None:
        worked_mins = int(max(0.0, working_hours) * 60)
        d.total_work_minutes = worked_mins
        deficit = max(0, 9 * 60 - worked_mins)
        if deficit > 0:
            d.deductible_minutes = deficit
            d.deduction_amount = round((deficit / 60) * hourly_rate, 2)
            d.rule_applied = "Under-hours (hours-only)"
            d.note = f"نقص ساعات {deficit} دقيقة"
        else:
            d.rule_applied = "On Time (hours-only)"
            d.note = "ساعات مكتملة"
        return d

    # No check-in: treat as absence
    if not check_in:
        d.is_absent = True
        d.deductible_minutes = 540
        d.deduction_amount = round(absence_daily_rate, 2)
        d.rule_applied = "Full Day Absence"
        d.note = "غياب يوم كامل"
        return d

    # No check-out: absence
    if not check_out:
        d.is_absent = True
        d.deductible_minutes = 540
        d.deduction_amount = round(absence_daily_rate, 2)
        d.rule_applied = "No Check-out (Absent)"
        d.note = "غياب - لا يوجد انصراف"
        return d

    # Parse times (support HH:MM and HH:MM:SS)
    ci_t = _parse_time_safe(check_in)
    co_t = _parse_time_safe(check_out)
    if not ci_t or not co_t:
        d.is_absent = True
        d.deductible_minutes = 540
        d.deduction_amount = round(absence_daily_rate, 2)
        d.rule_applied = "Invalid Time (Absent)"
        return d

    # Late minutes
    if ci_t > WORKING_HOURS_START:
        late = int((datetime.combine(work_date, ci_t) - datetime.combine(work_date, WORKING_HOURS_START)).total_seconds() / 60)
    else:
        late = 0
    d.late_minutes = late

    # Early leave
    if co_t < WORKING_HOURS_END:
        early = int((datetime.combine(work_date, WORKING_HOURS_END) - datetime.combine(work_date, co_t)).total_seconds() / 60)
    else:
        early = 0
    d.early_leave_minutes = early

    # Total minutes worked
    ci_dt = datetime.combine(work_date, ci_t)
    co_dt = datetime.combine(work_date, co_t)
    if co_t < ci_t:
        co_dt += timedelta(days=1)
    d.total_work_minutes = int((co_dt - ci_dt).total_seconds() / 60)

    # Apply late/early rules
    if late == 0 and early == 0:
        d.rule_applied = "On Time"
        d.note = "حضور في الموعد"
        return d

    # Lateness thresholds take precedence
    if late > 120:
        d.is_absent = True
        d.deductible_minutes = 540
        d.deduction_amount = round(absence_daily_rate, 2)
        d.rule_applied = ">2h Late → Full Day"
        return d
    if late >= 60:
        d.deductible_minutes = 270
        d.deduction_amount = round(absence_daily_rate / 2, 2)
        d.rule_applied = "1-2h Late → Half Day"
        return d

    # Grace for lateness only (does not cover early leave)
    effective_late = late
    if late <= GRACE_MIN and late_count_so_far < MAX_FREE_LATES and late > 0:
        d.grace_applied = True
        effective_late = 0

    # Exact time deduction (>15 min or after grace) using late + early
    exact_minutes = effective_late + early
    if exact_minutes == 0:
        d.rule_applied = "On Time (grace if late)"
        d.note = "حضور في الموعد (تطبيق سماح على التأخير إن وجد)"
        return d

    d.deductible_minutes = exact_minutes
    d.deduction_amount = round((exact_minutes / 60) * hourly_rate, 2)
    d.rule_applied = "Exact Time Deduction (late+early with grace)" if d.grace_applied else "Exact Time Deduction (late+early)"
    return d

# Main per-employee calculation
async def calculate_employee_deductions(
    db: AsyncIOMotorDatabase,
    employee_id: str,
    employee_name: str,
    basic_salary: float,
    cycle_start: date,
    cycle_end: date,
) -> EmployeeDeductionSummary:
    from public_holidays import is_public_holiday, is_employee_on_approved_leave

    # Working days list
    work_days = get_working_days_in_cycle(cycle_start, cycle_end)
    total_working_days = len(work_days)

    # Determine if calibration applies (env + date window intersect)
    calibration_active = False
    if CALIBRATION_OCTOBER_ENV:
        # If any day in cycle within window
        if not (cycle_end < CALIB_FROM or cycle_start > CALIB_TO):
            calibration_active = True

    # Rates
    # Absence per-30 during calibration, otherwise per-working-days
    daily_workingdays = basic_salary / total_working_days if total_working_days > 0 else 0.0
    absence_daily_rate = (basic_salary / 30.0) if calibration_active else daily_workingdays
    # Lateness per minute
    if calibration_active:
        lateness_rate_per_min = (basic_salary / 30.0) / 540.0 if basic_salary > 0 else 0.0
        hourly_rate = lateness_rate_per_min * 60.0
    else:
        hourly_rate = (daily_workingdays / 8.0) if daily_workingdays > 0 else 0.0

    # Attendance map (latest record per date)
    cs, ce = cycle_start.isoformat(), cycle_end.isoformat()
    pipeline = [
        {"$match": {"user_id": employee_id, "date": {"$gte": cs, "$lte": ce}}},
        {"$sort": {"date": 1, "created_at": -1, "updated_at": -1}},
        {"$group": {"_id": "$date", "rec": {"$first": "$$ROOT"}}},
        {"$replaceRoot": {"newRoot": "$rec"}},
        {"$sort": {"date": 1}},
    ]
    records = await db.attendance.aggregate(pipeline).to_list(None)
    amap = {r["date"]: r for r in records}

    summary = EmployeeDeductionSummary(
        employee_id=employee_id,
        employee_name=employee_name,
        basic_salary=basic_salary,
        cycle_start=cycle_start.isoformat(),
        cycle_end=cycle_end.isoformat(),
        total_working_days=total_working_days,
    )

    # Exceptions by user_id
    exc_type = await get_exception_type(db, employee_id)  # 'flex' | 'partial-flex' | None

    late_count = 0

    for wd in work_days:
        ds = wd.isoformat()
        rec = amap.get(ds)

        if (NO_DATA_NO_DEDUCTION and calibration_active and rec is None):
            detail = DailyDeductionDetail(date=ds)
            detail.rule_applied = "Calibration Safe (no data)"
            detail.note = "لا خصم بسبب نقص البيانات"
            summary.daily_records.append(detail)
            summary.days_present += 1
            continue

        check_in = rec.get("check_in") if rec else None
        check_out = rec.get("check_out") if rec else None
        wh_val = rec.get("working_hours") if rec else None
        try:
            working_hours = float(wh_val) if wh_val is not None else None
        except Exception:
            working_hours = None

        # Flexible employees: only absence is deducted
        if exc_type == 'flex':
            detail = DailyDeductionDetail(date=ds, check_in=check_in, check_out=check_out)
            # holiday / leave
            if await is_public_holiday(db, wd) or await is_employee_on_approved_leave(db, employee_id, wd):
                detail.rule_applied = "Public Holiday / Leave"
                summary.days_present += 1
            elif not check_in and working_hours is None:
                # Absent
                detail.is_absent = True
                detail.deductible_minutes = 540
                detail.deduction_amount = round(absence_daily_rate, 2)
                detail.rule_applied = "Absence (Flexible)"
                summary.days_absent += 1
                summary.absence_deduction += detail.deduction_amount
                summary.total_deduction += detail.deduction_amount
            else:
                detail.rule_applied = "Flexible (no late)"
                summary.days_present += 1
            summary.daily_records.append(detail)
            continue

        # Non-flex flow
        detail = calculate_daily_deduction(
            check_in=check_in,
            check_out=check_out,
            working_hours=working_hours,
            late_count_so_far=late_count,
            work_date=wd,
            hourly_rate=hourly_rate,
            absence_daily_rate=absence_daily_rate,
            is_on_leave=await is_employee_on_approved_leave(db, employee_id, wd),
            is_public_holiday=await is_public_holiday(db, wd),
        )

        # partial-flex: ignore early/under-hours, only lateness
        if exc_type == 'partial-flex' and not detail.is_absent and not detail.is_public_holiday and not detail.is_on_leave:
            late_only_minutes = detail.late_minutes
            effective_late = late_only_minutes
            if late_only_minutes <= GRACE_MIN and late_count < MAX_FREE_LATES and late_only_minutes > 0:
                detail.grace_applied = True
                effective_late = 0
            # keep half/full-day thresholds if hit
            if not (detail.rule_applied.startswith("1-2h Late") or detail.rule_applied.startswith(">2h Late")):
                detail.early_leave_minutes = 0
                detail.under_hours_minutes = 0
                detail.deductible_minutes = effective_late
                detail.deduction_amount = round((effective_late / 60) * hourly_rate, 2)
                detail.rule_applied = "Partial-Flex: Lateness Only"

        # grace tracker
        if detail.late_minutes > 0 and detail.late_minutes <= GRACE_MIN and detail.grace_applied:
            late_count += 1

        summary.daily_records.append(detail)
        if detail.is_absent:
            summary.days_absent += 1
            summary.absence_deduction += detail.deduction_amount
        else:
            summary.days_present += 1
            if detail.late_minutes > 0 or detail.early_leave_minutes > 0:
                summary.days_late += 1
            summary.total_late_minutes += detail.late_minutes
            summary.total_early_leave_minutes += detail.early_leave_minutes
            summary.total_under_hours_minutes += detail.under_hours_minutes
            summary.late_deduction += detail.deduction_amount
        summary.total_deduction += detail.deduction_amount

    summary.late_deduction = round(summary.late_deduction, 2)
    summary.absence_deduction = round(summary.absence_deduction, 2)
    summary.total_deduction = round(summary.total_deduction, 2)

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

# Public functions
async def calculate_monthly_deductions(db: AsyncIOMotorDatabase, month: int, year: int) -> List[EmployeeDeductionSummary]:
    cstart, cend = get_cycle_dates(month, year)
    emps = await db.users.find({"is_active": True}).to_list(None)
    out: List[EmployeeDeductionSummary] = []
    for e in emps:
        sal = float(e.get("monthly_salary", 0) or 0)
        if sal <= 0:
            continue
        out.append(
            await calculate_employee_deductions(
                db=db,
                employee_id=e["id"],
                employee_name=e["name"],
                basic_salary=sal,
                cycle_start=cstart,
                cycle_end=cend,
            )
        )
    return out

async def calculate_custom_period_deductions(db: AsyncIOMotorDatabase, start_date: date, end_date: date) -> List[EmployeeDeductionSummary]:
    emps = await db.users.find({"is_active": True}).to_list(None)
    out: List[EmployeeDeductionSummary] = []
    for e in emps:
        sal = float(e.get("monthly_salary", 0) or 0)
        if sal <= 0:
            continue
        out.append(
            await calculate_employee_deductions(
                db=db,
                employee_id=e["id"],
                employee_name=e["name"],
                basic_salary=sal,
                cycle_start=start_date,
                cycle_end=end_date,
            )
        )
    return out
