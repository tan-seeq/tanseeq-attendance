"""
نظام الرواتب المتكامل مع الخصومات والسلف - TANSEEQ HR
Integrated Payroll System with Deductions & Advances

Features:
- Payroll cycles (open/closed)
- Installment scheduling for advances
- Automatic deduction integration
- Real-time salary recalculation
- Comprehensive reporting
"""

from datetime import datetime, date, time, timezone
from uae_datetime_utils import to_iso_string_uae
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum
import uuid
import calendar

# ====================
# ENUMS & CONSTANTS
# ====================

class PayrollStatus(str, Enum):
    """حالة دورة الراتب"""
    OPEN = "open"                    # مفتوحة للتعديل
    PROCESSING = "processing"        # قيد المعالجة
    CLOSED = "closed"               # مقفولة ومعتمدة
    CANCELLED = "cancelled"         # ملغاة

class PayrollItemType(str, Enum):
    """نوع عنصر الراتب"""
    BASE_SALARY = "base_salary"             # الراتب الأساسي
    ALLOWANCE = "allowance"                 # بدل
    OVERTIME = "overtime"                   # أوفرتايم
    BONUS = "bonus"                         # مكافأة
    DEDUCTION_ATTENDANCE = "deduction_attendance"  # خصم حضور
    DEDUCTION_ADVANCE = "deduction_advance"        # خصم سلفة (قسط)
    DEDUCTION_MANUAL = "deduction_manual"          # خصم يدوي
    DEDUCTION_LEAVE = "deduction_leave"            # خصم إجازة
    DEDUCTION_OTHER = "deduction_other"            # خصومات أخرى

class DeductionCeiling(str, Enum):
    """أنواع سقف الخصومات"""
    PERCENTAGE = "percentage"        # نسبة مئوية
    FIXED_AMOUNT = "fixed_amount"   # مبلغ ثابت
    NO_LIMIT = "no_limit"          # بدون حد أقصى

class InstallmentStatus(str, Enum):
    """حالة القسط"""
    PENDING = "pending"             # في الانتظار
    DEDUCTED = "deducted"          # تم خصمه
    SKIPPED = "skipped"            # تم تخطيه (راتب غير كافي)
    CANCELLED = "cancelled"         # ملغى

# ====================
# PAYROLL CYCLE MODEL
# ====================

class PayrollCycle(BaseModel):
    """دورة الراتب الشهرية"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # معرف الدورة
    month: str = Field(description="YYYY-MM format")
    year: int
    display_name: str = Field(description="اسم الدورة للعرض")
    
    # التواريخ
    start_date: date = Field(description="تاريخ بداية الدورة")
    end_date: date = Field(description="تاريخ نهاية الدورة")
    cutoff_date: date = Field(description="آخر موعد للتعديلات")
    
    # الحالة والتحكم
    status: PayrollStatus = PayrollStatus.OPEN
    is_locked: bool = Field(default=False)
    
    # الإجماليات المالية
    total_employees: int = Field(default=0)
    total_gross_salary: float = Field(default=0.0, description="إجمالي الرواتب")
    total_allowances: float = Field(default=0.0, description="إجمالي البدلات")
    total_deductions: float = Field(default=0.0, description="إجمالي الخصومات")
    total_net_salary: float = Field(default=0.0, description="إجمالي الصافي")
    
    # إعدادات الخصومات
    default_deduction_ceiling_type: DeductionCeiling = DeductionCeiling.PERCENTAGE
    default_deduction_ceiling_value: float = Field(default=0.33, description="33% كحد أقصى افتراضي")
    
    # التدقيق والتحكم
    created_by: str
    created_by_name: str
    created_at: datetime = Field(default_factory=datetime.now)
    
    locked_by: Optional[str] = None
    locked_by_name: Optional[str] = None
    locked_at: Optional[datetime] = None
    lock_reason: Optional[str] = None
    
    finalized_by: Optional[str] = None
    finalized_by_name: Optional[str] = None  
    finalized_at: Optional[datetime] = None
    
    # ملاحظات
    notes: Optional[str] = None
    
    @validator('month')
    def validate_month(cls, v):
        try:
            datetime.strptime(v, "%Y-%m")
            return v
        except ValueError:
            raise ValueError('تنسيق الشهر يجب أن يكون YYYY-MM')
    
    @validator('display_name', pre=True, always=True)
    def generate_display_name(cls, v, values):
        if v:
            return v
        if 'month' in values and values['month']:
            year, month_num = values['month'].split('-')
            months_ar = {
                '01': 'يناير', '02': 'فبراير', '03': 'مارس', '04': 'أبريل',
                '05': 'مايو', '06': 'يونيو', '07': 'يوليو', '08': 'أغسطس', 
                '09': 'سبتمبر', '10': 'أكتوبر', '11': 'نوفمبر', '12': 'ديسمبر'
            }
            return f"راتب {months_ar.get(month_num, month_num)} {year}"
        return "دورة راتب"

# ====================  
# INSTALLMENT SCHEDULE MODEL
# ====================

class InstallmentSchedule(BaseModel):
    """جدولة أقساط السلف"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # ربط بالسلفة
    advance_transaction_id: str
    employee_id: str
    employee_name: str
    
    # تفاصيل الجدولة
    total_amount: float = Field(gt=0, description="المبلغ الإجمالي للسلفة")
    installment_amount: float = Field(gt=0, description="مبلغ القسط الشهري")
    number_of_installments: int = Field(ge=1, description="عدد الأقساط")
    
    # التقدم
    current_installment: int = Field(default=1)
    completed_installments: int = Field(default=0)
    remaining_balance: float = Field(description="الرصيد المتبقي")
    
    # التواريخ
    start_date: date = Field(description="تاريخ بداية الاستقطاع")
    scheduled_end_date: date = Field(description="تاريخ الانتهاء المجدول")
    actual_end_date: Optional[date] = None
    
    # الحالة والتحكم
    is_active: bool = Field(default=True)
    is_completed: bool = Field(default=False)
    
    # ضوابط الخصم
    respect_deduction_ceiling: bool = Field(default=True, description="احترام سقف الخصم الشهري")
    max_deduction_percentage: float = Field(default=0.33, description="الحد الأقصى للخصم كنسبة من الراتب")
    
    # معلومات الإنشاء
    created_by: str
    created_by_name: str
    created_at: datetime = Field(default_factory=datetime.now)
    
    # معلومات التعديل
    updated_by: Optional[str] = None
    updated_by_name: Optional[str] = None
    updated_at: Optional[datetime] = None
    
    # الإلغاء
    is_cancelled: bool = Field(default=False)
    cancelled_by: Optional[str] = None
    cancelled_by_name: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    
    @validator('remaining_balance', pre=True, always=True)
    def calculate_remaining_balance(cls, v, values):
        if 'total_amount' in values and 'completed_installments' in values and 'installment_amount' in values:
            total = values['total_amount']
            paid = values['completed_installments'] * values['installment_amount']
            return max(0, total - paid)
        return v or 0

# ====================
# INDIVIDUAL INSTALLMENT MODEL  
# ====================

class IndividualInstallment(BaseModel):
    """قسط فردي"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # الربط
    schedule_id: str
    payroll_cycle_id: Optional[str] = None
    employee_id: str
    
    # تفاصيل القسط
    installment_number: int
    scheduled_amount: float
    actual_amount: float = Field(default=0.0)
    due_date: date
    
    # الحالة
    status: InstallmentStatus = InstallmentStatus.PENDING
    processed_at: Optional[datetime] = None
    
    # أسباب التخطي أو التأجيل
    skip_reason: Optional[str] = None
    notes: Optional[str] = None

# ====================
# PAYROLL LINE ITEM MODEL
# ====================

class PayrollLineItem(BaseModel):
    """عنصر في كشف الراتب"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # الربط
    payroll_cycle_id: str
    employee_id: str
    employee_name: str
    
    # تصنيف العنصر
    item_type: PayrollItemType
    source_type: str = Field(description="المصدر: attendance, advance, manual, etc.")
    source_id: Optional[str] = None
    source_reference: Optional[str] = None
    
    # تفاصيل مالية
    description: str = Field(description="وصف العنصر")
    description_ar: Optional[str] = None
    amount: float = Field(description="المبلغ")
    currency: str = Field(default="AED")
    
    # التصنيف المحاسبي
    is_taxable: bool = Field(default=True)
    affects_eos: bool = Field(default=True, description="يؤثر على مكافأة نهاية الخدمة")
    is_recurring: bool = Field(default=False, description="عنصر متكرر")
    
    # التحكم
    is_editable: bool = Field(default=True)
    is_system_generated: bool = Field(default=False)
    
    # التدقيق
    created_by: str
    created_by_name: str 
    created_at: datetime = Field(default_factory=datetime.now)
    
    updated_by: Optional[str] = None
    updated_by_name: Optional[str] = None
    updated_at: Optional[datetime] = None
    
    # الإلغاء
    is_voided: bool = Field(default=False)
    voided_by: Optional[str] = None
    voided_by_name: Optional[str] = None
    voided_at: Optional[datetime] = None
    void_reason: Optional[str] = None

# ====================
# EMPLOYEE PAYROLL SUMMARY MODEL
# ====================

class EmployeePayrollSummary(BaseModel):
    """ملخص راتب الموظف"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # الموظف والدورة
    payroll_cycle_id: str
    employee_id: str
    employee_name: str
    employee_position: str
    department: Optional[str] = None
    
    # الراتب الأساسي
    base_salary: float = Field(default=0.0)
    daily_rate: float = Field(default=0.0)
    
    # الاستحقاقات
    total_allowances: float = Field(default=0.0)
    overtime_amount: float = Field(default=0.0)
    bonus_amount: float = Field(default=0.0)
    
    # إجمالي الاستحقاقات
    gross_salary: float = Field(default=0.0)
    
    # الخصومات
    attendance_deductions: float = Field(default=0.0)
    advance_deductions: float = Field(default=0.0)
    manual_deductions: float = Field(default=0.0)
    other_deductions: float = Field(default=0.0)
    
    # إجمالي الخصومات
    total_deductions: float = Field(default=0.0)
    
    # الصافي
    net_salary: float = Field(default=0.0)
    
    # إحصائيات الحضور
    working_days: int = Field(default=0)
    present_days: int = Field(default=0)
    absent_days: int = Field(default=0)
    late_days: int = Field(default=0)
    
    # حالة المعالجة
    is_calculated: bool = Field(default=False)
    calculated_at: Optional[datetime] = None
    calculation_notes: Optional[str] = None
    
    # الموافقة
    is_approved: bool = Field(default=False)
    approved_by: Optional[str] = None
    approved_by_name: Optional[str] = None
    approved_at: Optional[datetime] = None

# ====================
# DEDUCTION CEILING MODEL
# ====================

class EmployeeDeductionCeiling(BaseModel):
    """سقف خصومات الموظف"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    employee_id: str
    employee_name: str
    
    # نوع السقف
    ceiling_type: DeductionCeiling = DeductionCeiling.PERCENTAGE
    ceiling_value: float = Field(default=0.33, description="القيمة (نسبة أو مبلغ)")
    
    # استثناءات
    exclude_attendance_deductions: bool = Field(default=False)
    exclude_advance_deductions: bool = Field(default=False)
    exclude_manual_deductions: bool = Field(default=False)
    
    # فعالية
    effective_from: date = Field(default_factory=date.today)
    effective_until: Optional[date] = None
    is_active: bool = Field(default=True)
    
    # التدقيق
    created_by: str
    created_by_name: str
    created_at: datetime = Field(default_factory=datetime.now)
    
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None

# ====================
# REQUEST/RESPONSE MODELS
# ====================

class CreatePayrollCycleRequest(BaseModel):
    """طلب إنشاء دورة راتب"""
    month: str = Field(description="YYYY-MM format")
    notes: Optional[str] = None
    auto_generate_line_items: bool = Field(default=True, description="إنشاء عناصر الراتب تلقائياً")

class CreateInstallmentScheduleRequest(BaseModel):
    """طلب إنشاء جدولة أقساط"""
    advance_transaction_id: str
    installment_amount: float = Field(gt=0)
    number_of_installments: int = Field(ge=1, le=60)  # حد أقصى 5 سنوات
    start_date: date
    respect_deduction_ceiling: bool = Field(default=True)

class UpdateInstallmentScheduleRequest(BaseModel):
    """طلب تعديل جدولة أقساط"""
    installment_amount: Optional[float] = Field(None, gt=0)
    start_date: Optional[date] = None
    respect_deduction_ceiling: Optional[bool] = None
    notes: Optional[str] = None

class CreatePayrollLineItemRequest(BaseModel):
    """طلب إنشاء عنصر راتب"""
    payroll_cycle_id: str
    employee_id: str
    item_type: PayrollItemType
    source_type: str
    source_id: Optional[str] = None
    description: str
    amount: float
    is_recurring: bool = Field(default=False)

class PayrollCalculationRequest(BaseModel):
    """طلب حساب الراتب"""
    payroll_cycle_id: str
    employee_ids: Optional[List[str]] = None  # None = جميع الموظفين
    force_recalculation: bool = Field(default=False)

class LockPayrollCycleRequest(BaseModel):
    """طلب قفل دورة الراتب"""
    lock_reason: Optional[str] = None

class EditEmployeePayrollData(BaseModel):
    """بيانات تعديل راتب موظف"""
    employee_id: str
    employee_name: str
    base_salary: float = Field(ge=0)
    allowances: float = Field(default=0.0, ge=0)
    manual_deductions: float = Field(default=0.0, ge=0)
    deduction_notes: Optional[str] = None

class UpdatePayrollCycleRequest(BaseModel):
    """طلب تعديل بيانات دورة الراتب"""
    employees: List[EditEmployeePayrollData]
    notes: Optional[str] = None

# ====================
# RESPONSE MODELS
# ====================

class PayrollCycleResponse(BaseModel):
    """استجابة دورة الراتب"""
    id: str
    month: str
    display_name: str
    status: str
    is_locked: bool
    total_employees: int
    total_gross_salary: float
    total_deductions: float
    total_net_salary: float
    created_at: str
    locked_at: Optional[str] = None

class InstallmentScheduleResponse(BaseModel):
    """استجابة جدولة الأقساط"""
    id: str
    advance_transaction_id: str
    employee_name: str
    total_amount: float
    installment_amount: float
    number_of_installments: int
    completed_installments: int
    remaining_balance: float
    is_active: bool
    is_completed: bool
    start_date: str
    scheduled_end_date: str

class PayrollSummaryResponse(BaseModel):
    """استجابة ملخص الراتب"""
    employee_id: str
    employee_name: str
    base_salary: float
    gross_salary: float
    total_deductions: float
    net_salary: float
    working_days: int
    present_days: int

class DeductionCeilingCheckResponse(BaseModel):
    """استجابة فحص سقف الخصومات"""
    employee_id: str
    current_deductions: float
    ceiling_amount: float
    remaining_capacity: float
    is_within_limit: bool
    warning_message: Optional[str] = None

# ====================
# ARABIC TRANSLATIONS
# ====================

PAYROLL_STATUS_AR = {
    PayrollStatus.OPEN: "مفتوحة",
    PayrollStatus.PROCESSING: "قيد المعالجة", 
    PayrollStatus.CLOSED: "مقفولة",
    PayrollStatus.CANCELLED: "ملغاة"
}

PAYROLL_ITEM_TYPE_AR = {
    PayrollItemType.BASE_SALARY: "الراتب الأساسي",
    PayrollItemType.ALLOWANCE: "بدل",
    PayrollItemType.OVERTIME: "أوفرتايم",
    PayrollItemType.BONUS: "مكافأة",
    PayrollItemType.DEDUCTION_ATTENDANCE: "خصم حضور",
    PayrollItemType.DEDUCTION_ADVANCE: "خصم سلفة",
    PayrollItemType.DEDUCTION_MANUAL: "خصم يدوي",
    PayrollItemType.DEDUCTION_LEAVE: "خصم إجازة",
    PayrollItemType.DEDUCTION_OTHER: "خصومات أخرى"
}

INSTALLMENT_STATUS_AR = {
    InstallmentStatus.PENDING: "في الانتظار",
    InstallmentStatus.DEDUCTED: "تم خصمه",
    InstallmentStatus.SKIPPED: "تم تخطيه", 
    InstallmentStatus.CANCELLED: "ملغى"
}

DEDUCTION_CEILING_AR = {
    DeductionCeiling.PERCENTAGE: "نسبة مئوية",
    DeductionCeiling.FIXED_AMOUNT: "مبلغ ثابت",
    DeductionCeiling.NO_LIMIT: "بدون حد أقصى"
}

# ====================
# HELPER FUNCTIONS
# ====================

def get_month_boundaries(year: int, month: int) -> tuple[date, date]:
    """حساب بداية ونهاية الشهر"""
    start_date = date(year, month, 1)
    _, last_day = calendar.monthrange(year, month)
    end_date = date(year, month, last_day)
    return start_date, end_date

def calculate_installment_schedule(total_amount: float, monthly_amount: float) -> tuple[int, date]:
    """حساب عدد الأقساط وتاريخ الانتهاء"""
    number_of_installments = int(total_amount / monthly_amount)
    if total_amount % monthly_amount > 0:
        number_of_installments += 1
    
    # Calculate end date (approximate)
    from dateutil.relativedelta import relativedelta
    today = date.today()
    end_date = today + relativedelta(months=number_of_installments)
    
    return number_of_installments, end_date

def validate_deduction_ceiling(employee_salary: float, current_deductions: float, 
                              additional_deduction: float, ceiling_type: DeductionCeiling,
                              ceiling_value: float) -> tuple[bool, str]:
    """التحقق من سقف الخصومات"""
    
    if ceiling_type == DeductionCeiling.NO_LIMIT:
        return True, ""
    
    total_deductions = current_deductions + additional_deduction
    
    if ceiling_type == DeductionCeiling.PERCENTAGE:
        max_allowed = employee_salary * ceiling_value
        if total_deductions > max_allowed:
            return False, f"يتجاوز الخصم السقف المسموح ({ceiling_value*100}% من الراتب)"
    
    elif ceiling_type == DeductionCeiling.FIXED_AMOUNT:
        if total_deductions > ceiling_value:
            return False, f"يتجاوز الخصم السقف المسموح ({ceiling_value} درهم)"
    
    return True, ""

# ====================
# DATABASE HELPERS
# ====================

class PayrollDB:
    """مساعد قاعدة البيانات للرواتب"""
    
    @staticmethod
    def prepare_for_mongo(data: dict) -> dict:
        """تحضير البيانات للحفظ في MongoDB"""
        prepared = {}
        for key, value in data.items():
            if isinstance(value, (date, datetime)):
                prepared[key] = value.isoformat()
            elif isinstance(value, Enum):
                prepared[key] = value.value
            elif isinstance(value, BaseModel):
                prepared[key] = PayrollDB.prepare_for_mongo(value.dict())
            elif isinstance(value, list):
                prepared[key] = [
                    PayrollDB.prepare_for_mongo(item.dict()) if isinstance(item, BaseModel) 
                    else item for item in value
                ]
            else:
                prepared[key] = value
        return prepared
    
    @staticmethod
    def parse_from_mongo(data: dict) -> dict:
        """تحليل البيانات من MongoDB"""
        if "_id" in data:
            del data["_id"]
        
        # Convert date strings back to date objects
        for key, value in data.items():
            if isinstance(value, str):
                try:
                    if "T" in value:  # datetime
                        data[key] = datetime.fromisoformat(value.replace("Z", "+00:00"))
                    elif key.endswith("_date") and "-" in value:  # date
                        data[key] = datetime.fromisoformat(value).date()
                except (ValueError, TypeError):
                    pass  # Keep original value
        
        return data