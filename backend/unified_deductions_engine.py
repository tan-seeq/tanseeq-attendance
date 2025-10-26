"""
Unified Deductions Engine
=========================
محرك موحد لحساب خصومات الحضور والانصراف

✅ Single Source of Truth لجميع الصفحات
✅ قواعد موحدة وثابتة
✅ Round(2) في النهاية فقط
✅ Timezone: Asia/Dubai

Business Rules (Updated):
- Working hours: 09:00-18:00 (540 minutes including break)
- Grace Period: 5 minutes ONLY (not 15×4)
- Deduction Rate: DailyRate / 540 per minute
- Absent Day: Full DailyRate
- Excluded: Hatem, Tareq (no deductions)
- Cycle: 29th prev month → 28th current month
"""

from typing import List, Optional, Dict
from datetime import datetime, date, time, timedelta
from pydantic import BaseModel, Field
import pytz

# ============================================
# Constants
# ============================================

GRACE_PERIOD_MINUTES = 5  # ✅ Updated from 15×4 to 5 minutes
STANDARD_START_TIME = time(9, 0)   # 09:00
STANDARD_END_TIME = time(18, 0)    # 18:00
TOTAL_WORK_MINUTES = 540  # Including break
BREAK_MINUTES = 60

UAE_TZ = pytz.timezone('Asia/Dubai')

EXCLUDED_EMPLOYEES = [
    "حاتم محمد أحمد",
    "Hatem Mohamed Ahmed",
    "طارق عبد المنعم الوزان",
    "Tareq Abdel Moneim Alwazzan",
    "Tariq Abdel Moneim Alwazzan",
    "TAREK ABDELMONEM ZAKI ALWAZAN"
]

# ============================================
# Models
# ============================================

class DailyDeductionRecord(BaseModel):
    """تفاصيل خصم يوم واحد"""
    date: str  # YYYY-MM-DD
    status: str  # present, late, absent, leave, holiday
    check_in: Optional[str] = None  # HH:MM:SS
    check_out: Optional[str] = None  # HH:MM:SS
    total_work_minutes: int = 0
    late_minutes: int = 0
    early_leave_minutes: int = 0
    deficit_minutes: int = 0
    working_hours: float = 0.0
    deduction_amount: float = 0.0
    rule_applied: str = ""
    deduction_type: str = "none"  # none, late, absence, early_leave
    note: str = ""
    is_absent: bool = False


class EmployeeDeductionSummary(BaseModel):
    """ملخص خصومات الموظف للفترة"""
    employee_id: str
    employee_name: str
    monthly_salary: float
    cycle_start: str
    cycle_end: str
    late_count: int = 0
    absence_count: int = 0
    total_late_minutes: int = 0
    total_early_leave_minutes: int = 0
    late_deduction: float = 0.0
    absence_deduction: float = 0.0
    total_deduction: float = 0.0
    deduction_details: List[str] = []
    daily_breakdown: List[DailyDeductionRecord] = []


# ============================================
# Helper Functions
# ============================================

def is_employee_excluded(employee_name: str) -> bool:
    """التحقق من الموظفين المستثنيين"""
    name_lower = employee_name.lower().strip()
    for excluded in EXCLUDED_EMPLOYEES:
        if excluded.lower() in name_lower or name_lower in excluded.lower():
            return True
    return False


def get_cycle_dates(month: int, year: int) -> tuple:
    """
    حساب تواريخ الدورة الشهرية
    29th prev month → 28th current month
    """
    if month == 1:
        cycle_start = date(year - 1, 12, 29)
    else:
        cycle_start = date(year, month - 1, 29)
    
    cycle_end = date(year, month, 28)
    
    return cycle_start, cycle_end


def get_working_days_in_cycle(cycle_start: date, cycle_end: date) -> List[date]:
    """
    جميع أيام العمل في الدورة (الأحد-الخميس)
    """
    working_days = []
    current = cycle_start
    
    while current <= cycle_end:
        # weekday(): Monday=0, Sunday=6
        day_of_week = (current.weekday() + 1) % 7
        # Working days: Sunday(0) to Thursday(4)
        if day_of_week <= 4:
            working_days.append(current)
        current += timedelta(days=1)
    
    return working_days


def parse_time_safe(time_str: Optional[str]) -> Optional[time]:
    """تحويل string إلى time بأمان"""
    if not time_str:
        return None
    try:
        return datetime.strptime(time_str, "%H:%M:%S").time()
    except:
        return None


# ============================================
# Core Calculation Logic
# ============================================

def calculate_single_day_deduction(
    date_str: str,
    check_in: Optional[str],
    check_out: Optional[str],
    monthly_salary: float,
    is_on_leave: bool = False,
    is_holiday: bool = False
) -> DailyDeductionRecord:
    """
    حساب خصم يوم واحد
    ✅ محرك موحد - نفس المنطق لجميع الصفحات
    
    Returns:
        DailyDeductionRecord مع جميع التفاصيل
    """
    
    # حساب معدل الدقيقة الواحدة
    daily_rate = monthly_salary / 30
    minute_rate = daily_rate / TOTAL_WORK_MINUTES
    
    record = DailyDeductionRecord(
        date=date_str,
        status="present",
        check_in=check_in,
        check_out=check_out,
        total_work_minutes=0,
        late_minutes=0,
        early_leave_minutes=0,
        deficit_minutes=0,
        working_hours=0.0,
        deduction_amount=0.0,
        rule_applied="No deduction",
        deduction_type="none",
        note="",
        is_absent=False
    )
    
    # ✅ إجازة معتمدة أو عطلة رسمية = لا خصم
    if is_on_leave:
        record.status = "leave"
        record.rule_applied = "Approved Leave"
        record.note = "إجازة معتمدة - لا خصم"
        return record
    
    if is_holiday:
        record.status = "holiday"
        record.rule_applied = "Public Holiday"
        record.note = "عطلة رسمية - لا خصم"
        return record
    
    # ✅ غياب (لا يوجد check-in)
    if not check_in:
        record.status = "absent"
        record.is_absent = True
        record.deduction_amount = round(daily_rate, 2)
        record.rule_applied = "Full-day absence"
        record.deduction_type = "absence"
        record.note = "غياب بدون مبرر - خصم يوم كامل"
        record.deficit_minutes = TOTAL_WORK_MINUTES
        return record
    
    # ✅ check-in موجود لكن بدون check-out = معامل كغياب
    if not check_out:
        record.status = "absent"
        record.is_absent = True
        record.deduction_amount = round(daily_rate, 2)
        record.rule_applied = "No check-out (treated as absent)"
        record.deduction_type = "absence"
        record.note = "لا يوجد تسجيل انصراف - خصم يوم كامل"
        record.deficit_minutes = TOTAL_WORK_MINUTES
        return record
    
    # ✅ تحويل الأوقات
    check_in_time = parse_time_safe(check_in)
    check_out_time = parse_time_safe(check_out)
    
    if not check_in_time or not check_out_time:
        # أوقات غير صحيحة
        record.status = "absent"
        record.is_absent = True
        record.deduction_amount = round(daily_rate, 2)
        record.rule_applied = "Invalid times"
        record.deduction_type = "absence"
        record.note = "أوقات غير صحيحة - خصم يوم كامل"
        return record
    
    # ✅ حساب دقائق التأخير (بعد 09:00)
    if check_in_time > STANDARD_START_TIME:
        check_in_dt = datetime.combine(date.today(), check_in_time)
        standard_dt = datetime.combine(date.today(), STANDARD_START_TIME)
        late_minutes = int((check_in_dt - standard_dt).total_seconds() / 60)
        
        # ✅ Grace Period: 5 minutes
        if late_minutes > GRACE_PERIOD_MINUTES:
            record.late_minutes = late_minutes - GRACE_PERIOD_MINUTES
            record.status = "late"
        else:
            record.late_minutes = 0
            record.status = "present"
    
    # ✅ حساب الانصراف المبكر (قبل 18:00)
    if check_out_time < STANDARD_END_TIME:
        check_out_dt = datetime.combine(date.today(), check_out_time)
        standard_dt = datetime.combine(date.today(), STANDARD_END_TIME)
        record.early_leave_minutes = int((standard_dt - check_out_dt).total_seconds() / 60)
    
    # ✅ حساب إجمالي ساعات العمل
    check_in_dt = datetime.combine(date.today(), check_in_time)
    check_out_dt = datetime.combine(date.today(), check_out_time)
    
    if check_out_time < check_in_time:
        check_out_dt += timedelta(days=1)
    
    total_minutes = int((check_out_dt - check_in_dt).total_seconds() / 60)
    record.total_work_minutes = max(0, total_minutes - BREAK_MINUTES)
    record.working_hours = round(record.total_work_minutes / 60, 2)
    
    # ✅ حساب العجز الكلي
    record.deficit_minutes = record.late_minutes + record.early_leave_minutes
    
    # ✅ حساب الخصم المالي
    if record.deficit_minutes > 0:
        record.deduction_amount = round(minute_rate * record.deficit_minutes, 2)
        
        if record.late_minutes > 0 and record.early_leave_minutes > 0:
            record.rule_applied = f"Late {record.late_minutes}m + Early leave {record.early_leave_minutes}m"
            record.deduction_type = "combined"
            record.note = f"تأخير {record.late_minutes} دقيقة + انصراف مبكر {record.early_leave_minutes} دقيقة"
        elif record.late_minutes > 0:
            record.rule_applied = f"Late {record.late_minutes}m (after 5m grace)"
            record.deduction_type = "late"
            record.note = f"تأخير {record.late_minutes} دقيقة بعد فترة السماح"
        elif record.early_leave_minutes > 0:
            record.rule_applied = f"Early leave {record.early_leave_minutes}m"
            record.deduction_type = "early_leave"
            record.note = f"انصراف مبكر {record.early_leave_minutes} دقيقة"
    else:
        record.rule_applied = "On time"
        record.note = "حضور وانصراف في الوقت المحدد"
    
    return record


# ============================================
# Main Unified Calculation Function
# ============================================

async def calculate_unified_deductions(
    db,
    month: int,
    year: int,
    custom_start_date: Optional[date] = None,
    custom_end_date: Optional[date] = None
) -> List[EmployeeDeductionSummary]:
    """
    ✅ محرك موحد لحساب الخصومات
    يُستخدم من جميع الصفحات: Dashboard, Advanced Deductions, Payroll
    
    Args:
        db: MongoDB database
        month: Month number (1-12)
        year: Year
        custom_start_date: Optional custom start (overrides cycle)
        custom_end_date: Optional custom end (overrides cycle)
    
    Returns:
        List[EmployeeDeductionSummary] مع التفاصيل اليومية الكاملة
    """
    from public_holidays import is_public_holiday, is_employee_on_approved_leave
    
    # ✅ حساب تواريخ الدورة
    if custom_start_date and custom_end_date:
        cycle_start = custom_start_date
        cycle_end = custom_end_date
    else:
        cycle_start, cycle_end = get_cycle_dates(month, year)
    
    cycle_start_str = cycle_start.strftime("%Y-%m-%d")
    cycle_end_str = cycle_end.strftime("%Y-%m-%d")
    
    # ✅ جميع أيام العمل في الدورة
    working_days = get_working_days_in_cycle(cycle_start, cycle_end)
    
    print(f"🔵 Unified Engine: {cycle_start_str} → {cycle_end_str} ({len(working_days)} working days)")
    
    # ✅ جلب جميع الموظفين النشطين
    employees = await db.users.find({"is_active": True}).to_list(None)
    
    summaries = []
    
    for emp in employees:
        employee_id = emp["id"]
        employee_name = emp["name"]
        monthly_salary = float(emp.get("monthly_salary", 0) or 0)
        
        # ✅ تخطي الموظفين المستثنيين
        if is_employee_excluded(employee_name):
            print(f"⏭️ Excluded: {employee_name}")
            continue
        
        # ✅ تخطي الموظفين بدون راتب
        if monthly_salary <= 0:
            print(f"⏭️ No salary: {employee_name}")
            continue
        
        print(f"👤 Processing: {employee_name} (Salary: {monthly_salary:.2f})")
        
        # ✅ جلب سجلات الحضور
        attendance_records = await db.attendance.find({
            "user_id": employee_id,
            "date": {"$gte": cycle_start_str, "$lte": cycle_end_str}
        }).to_list(None)
        
        attendance_map = {rec["date"]: rec for rec in attendance_records}
        
        # ✅ إنشاء ملخص الموظف
        summary = EmployeeDeductionSummary(
            employee_id=employee_id,
            employee_name=employee_name,
            monthly_salary=monthly_salary,
            cycle_start=cycle_start_str,
            cycle_end=cycle_end_str,
            late_count=0,
            absence_count=0,
            total_late_minutes=0,
            total_early_leave_minutes=0,
            late_deduction=0.0,
            absence_deduction=0.0,
            total_deduction=0.0,
            deduction_details=[],
            daily_breakdown=[]
        )
        
        # ✅ معالجة كل يوم عمل
        for work_date in working_days:
            date_str = work_date.strftime("%Y-%m-%d")
            
            # ✅ التحقق من الإجازات والعطل
            is_holiday = await is_public_holiday(db, work_date)
            is_on_leave = await is_employee_on_approved_leave(db, employee_id, work_date)
            
            # ✅ جلب سجل الحضور
            attendance = attendance_map.get(date_str)
            check_in = attendance.get("check_in") if attendance else None
            check_out = attendance.get("check_out") if attendance else None
            
            # ✅ حساب خصم اليوم
            daily_record = calculate_single_day_deduction(
                date_str=date_str,
                check_in=check_in,
                check_out=check_out,
                monthly_salary=monthly_salary,
                is_on_leave=is_on_leave,
                is_holiday=is_holiday
            )
            
            # ✅ إضافة للملخص
            summary.daily_breakdown.append(daily_record)
            
            # ✅ تحديث الإجماليات
            if daily_record.is_absent:
                summary.absence_count += 1
                summary.absence_deduction += daily_record.deduction_amount
            elif daily_record.late_minutes > 0:
                summary.late_count += 1
                summary.total_late_minutes += daily_record.late_minutes
                summary.late_deduction += daily_record.deduction_amount
            
            if daily_record.early_leave_minutes > 0:
                summary.total_early_leave_minutes += daily_record.early_leave_minutes
            
            summary.total_deduction += daily_record.deduction_amount
        
        # ✅ Round جميع المبالغ
        summary.late_deduction = round(summary.late_deduction, 2)
        summary.absence_deduction = round(summary.absence_deduction, 2)
        summary.total_deduction = round(summary.total_deduction, 2)
        
        # ✅ بناء deduction_details
        if summary.late_count > 0:
            summary.deduction_details.append(
                f"تأخير {summary.late_count} مرات - إجمالي {summary.total_late_minutes} دقيقة - خصم {summary.late_deduction:.2f} درهم"
            )
        
        if summary.absence_count > 0:
            summary.deduction_details.append(
                f"غياب {summary.absence_count} يوم - خصم {summary.absence_deduction:.2f} درهم"
            )
        
        if summary.total_early_leave_minutes > 0:
            summary.deduction_details.append(
                f"انصراف مبكر: إجمالي {summary.total_early_leave_minutes} دقيقة"
            )
        
        print(f"   ✅ Late: {summary.late_count}, Absent: {summary.absence_count}, Total: {summary.total_deduction:.2f} AED")
        
        # ✅ إضافة فقط إذا كان هناك خصومات أو نشاط
        if summary.total_deduction > 0 or summary.late_count > 0 or summary.absence_count > 0:
            summaries.append(summary)
    
    return summaries
