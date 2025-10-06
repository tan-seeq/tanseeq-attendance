"""
Advanced Attendance & Deduction System Models
نماذج نظام الحضور والخصومات المتقدم - أكتوبر 2025
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date, time
from enum import Enum
import uuid

# ====================
# ENUMS & CONSTANTS  
# ====================

class DeductionType(str, Enum):
    LATENESS = "lateness"                    # خصم تأخير
    EARLY_LEAVE = "early_leave"             # خصم خروج مبكر  
    MISSING_CHECKOUT = "missing_checkout"    # عدم تسجيل انصراف
    MANUAL = "manual"                       # خصم يدوي
    ABSENCE = "absence"                     # غياب

class DeductionCategory(str, Enum):
    MINUTES = "minutes"                     # خصم دقائق
    HALF_DAY = "half_day"                  # نصف يوم
    FULL_DAY = "full_day"                  # يوم كامل
    CUSTOM = "custom"                      # مخصص

class DeductionSource(str, Enum):
    AUTO = "auto"                          # تلقائي
    MANUAL = "manual"                      # يدوي من السوبر أدمن

class AttendanceStatus(str, Enum):
    PRESENT = "present"                    # حاضر
    LATE = "late"                         # متأخر
    EARLY_LEAVE = "early_leave"           # خروج مبكر
    MISSING_CHECKOUT = "missing_checkout"  # لم يسجل انصراف
    ABSENT = "absent"                     # غائب

class NotificationSeverity(str, Enum):
    NORMAL = "normal"                     # عادي
    IMPORTANT = "important"               # مهم
    WARNING = "warning"                   # تحذير
    URGENT = "urgent"                     # عاجل

# ====================
# ATTENDANCE POLICIES
# ====================

class AttendancePolicy(BaseModel):
    """سياسة حضور الموظف"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str
    employee_name: str
    
    # أوقات العمل
    start_time: time = Field(default=time(9, 0), description="وقت الدخول المطلوب")
    end_time: time = Field(default=time(18, 0), description="وقت الخروج المطلوب")
    
    # استثناءات
    no_penalties: bool = Field(default=False, description="بدون خصومات (مثل حاتم)")
    early_start_allowed: bool = Field(default=False, description="دخول مبكر مسموح")
    end_flexible: bool = Field(default=False, description="خروج مرن (مثل طارق)")
    
    # إعدادات متقدمة
    grace_period_minutes: int = Field(default=0, description="فترة سماح بالدقائق")
    custom_working_hours: Optional[int] = Field(default=None, description="ساعات عمل مخصصة")
    
    # تواريخ
    effective_from: date = Field(default_factory=date.today)
    effective_until: Optional[date] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

# ====================
# DAILY ATTENDANCE
# ====================

class DailyAttendance(BaseModel):
    """سجل الحضور اليومي"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str
    employee_name: str
    date: date
    
    # أوقات الحضور
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    
    # حسابات التأخير والخروج المبكر
    late_minutes: int = Field(default=0, description="دقائق التأخير")
    early_leave_minutes: int = Field(default=0, description="دقائق الخروج المبكر")
    
    # الحالة والإحصائيات
    status: AttendanceStatus = AttendanceStatus.PRESENT
    working_hours: float = Field(default=0.0, description="ساعات العمل الفعلية")
    
    # معلومات المعالجة
    computed_at: Optional[datetime] = None
    recomputed_at: Optional[datetime] = None
    notes: Optional[str] = None

# ====================
# MONTHLY COUNTERS
# ====================

class MonthlyLatenessCounters(BaseModel):
    """عدادات التأخير الشهرية"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str
    employee_name: str
    month: str  # Format: YYYY-MM
    
    # عدادات المرات المجانية (4 مرات × 15 دقيقة)
    free_occurrences_used: int = Field(default=0, description="المرات المجانية المستخدمة")
    free_occurrences_limit: int = Field(default=4, description="حد المرات المجانية")
    
    # إحصائيات شهرية
    total_late_days: int = Field(default=0, description="إجمالي أيام التأخير")
    total_late_minutes: int = Field(default=0, description="إجمالي دقائق التأخير")
    total_deduction_amount: float = Field(default=0.0, description="إجمالي مبلغ الخصومات")
    
    # تواريخ
    created_at: datetime = Field(default_factory=datetime.now)
    reset_at: Optional[datetime] = None

# ====================
# PAYROLL DEDUCTIONS
# ====================

class PayrollDeduction(BaseModel):
    """خصم من الراتب"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str
    employee_name: str
    
    # تفاصيل الخصم
    deduction_type: DeductionType
    category: DeductionCategory
    date: date
    
    # المبالغ والأوقات
    minutes: int = Field(default=0, description="دقائق الخصم")
    amount: float = Field(default=0.0, description="مبلغ الخصم بالدرهم")
    daily_rate: float = Field(default=0.0, description="الأجر اليومي")
    
    # الأسباب والتوثيق
    reason: str = Field(description="سبب الخصم")
    category_ar: Optional[str] = None
    source: DeductionSource = DeductionSource.AUTO
    
    # مرجع المصدر
    reference_id: Optional[str] = None  # مرجع الحضور أو المعاملة
    reference_type: Optional[str] = None
    
    # المرفقات
    attachments: List[Dict[str, Any]] = Field(default_factory=list)
    
    # الإلغاء (Soft Delete)
    is_voided: bool = Field(default=False)
    voided_by: Optional[str] = None
    voided_by_name: Optional[str] = None
    void_reason: Optional[str] = None
    voided_at: Optional[datetime] = None
    
    # التدقيق
    created_by: Optional[str] = None
    created_by_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_by: Optional[str] = None  
    updated_at: Optional[datetime] = None

# ====================
# NOTIFICATIONS
# ====================

class SystemNotification(BaseModel):
    """إشعار النظام"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str
    employee_name: str
    
    # محتوى الإشعار
    title: str
    message: str
    severity: NotificationSeverity = NotificationSeverity.NORMAL
    
    # الإجبارية والتفاعل
    must_acknowledge: bool = Field(default=False, description="يتطلب إقرار إجباري")
    acknowledged_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    
    # البيانات الإضافية
    data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    action_url: Optional[str] = None
    
    # التصنيف والمرجع
    category: Optional[str] = None
    reference_id: Optional[str] = None
    reference_type: Optional[str] = None
    
    # التواريخ
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None

# ====================
# SYSTEM CONFIGURATION
# ====================

class AttendanceSystemConfig(BaseModel):
    """إعدادات نظام الحضور"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # إعدادات العمل العامة
    default_start_time: time = Field(default=time(9, 0))
    default_end_time: time = Field(default=time(18, 0))
    working_minutes_per_day: int = Field(default=540, description="دقائق العمل في اليوم (9 ساعات)")
    
    # قواعد المرات المجانية
    free_occurrences_limit: int = Field(default=4, description="المرات المجانية شهرياً")
    free_occurrence_max_minutes: int = Field(default=15, description="الحد الأقصى للمرة المجانية")
    
    # حدود الخصومات
    half_day_threshold_minutes: int = Field(default=60, description="حد نصف اليوم")
    full_day_threshold_minutes: int = Field(default=120, description="حد اليوم الكامل")
    
    # إعدادات التحذيرات
    missing_checkout_warning_time: time = Field(default=time(18, 10))
    missing_checkout_deadline_time: time = Field(default=time(23, 59))
    
    # إعدادات التشغيل
    auto_processing_enabled: bool = Field(default=True)
    notifications_enabled: bool = Field(default=True)
    
    # التحديث
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None

# ====================
# REQUEST/RESPONSE MODELS
# ====================

class CreateDeductionRequest(BaseModel):
    """طلب إنشاء خصم يدوي"""
    employee_id: str
    deduction_type: DeductionType = DeductionType.MANUAL
    category: DeductionCategory
    date: date
    minutes: Optional[int] = None
    amount: Optional[float] = None
    reason: str = Field(min_length=5, description="سبب الخصم")
    attachments: List[Dict[str, Any]] = Field(default_factory=list)
    notes: Optional[str] = None

class UpdateDeductionRequest(BaseModel):
    """طلب تعديل خصم"""
    minutes: Optional[int] = None
    amount: Optional[float] = None
    reason: Optional[str] = None
    notes: Optional[str] = None

class VoidDeductionRequest(BaseModel):
    """طلب إلغاء خصم"""
    void_reason: str = Field(min_length=5, description="سبب الإلغاء")

class AttendanceRecomputeRequest(BaseModel):
    """طلب إعادة احتساب الحضور"""
    month: Optional[str] = None  # YYYY-MM
    employee_id: Optional[str] = None
    force: bool = Field(default=False)

class AttendanceStatsResponse(BaseModel):
    """إحصائيات الحضور"""
    employee_id: str
    employee_name: str
    month: str
    
    total_days: int
    present_days: int
    late_days: int
    absent_days: int
    
    total_late_minutes: int
    total_deduction_amount: float
    free_occurrences_remaining: int

# ====================
# ARABIC TRANSLATIONS
# ====================

DEDUCTION_TYPE_AR = {
    DeductionType.LATENESS: "خصم تأخير",
    DeductionType.EARLY_LEAVE: "خصم خروج مبكر", 
    DeductionType.MISSING_CHECKOUT: "عدم تسجيل انصراف",
    DeductionType.MANUAL: "خصم يدوي",
    DeductionType.ABSENCE: "خصم غياب"
}

DEDUCTION_CATEGORY_AR = {
    DeductionCategory.MINUTES: "خصم دقائق",
    DeductionCategory.HALF_DAY: "خصم نصف يوم",
    DeductionCategory.FULL_DAY: "خصم يوم كامل", 
    DeductionCategory.CUSTOM: "خصم مخصص"
}

ATTENDANCE_STATUS_AR = {
    AttendanceStatus.PRESENT: "حاضر",
    AttendanceStatus.LATE: "متأخر",
    AttendanceStatus.EARLY_LEAVE: "خروج مبكر",
    AttendanceStatus.MISSING_CHECKOUT: "لم يسجل انصراف",
    AttendanceStatus.ABSENT: "غائب"
}

NOTIFICATION_SEVERITY_AR = {
    NotificationSeverity.NORMAL: "عادي",
    NotificationSeverity.IMPORTANT: "مهم", 
    NotificationSeverity.WARNING: "تحذير",
    NotificationSeverity.URGENT: "عاجل"
}

# ====================
# HELPER FUNCTIONS
# ====================

def prepare_for_mongo(data):
    """تحضير البيانات للحفظ في MongoDB"""
    if isinstance(data, dict):
        prepared = {}
        for key, value in data.items():
            if isinstance(value, (date, datetime)):
                prepared[key] = value.isoformat()
            elif isinstance(value, time):
                prepared[key] = value.strftime('%H:%M:%S')
            elif isinstance(value, Enum):
                prepared[key] = value.value
            elif isinstance(value, list):
                prepared[key] = [prepare_for_mongo(item) if isinstance(item, dict) else item for item in value]
            else:
                prepared[key] = value
        return prepared
    return data

def parse_from_mongo(item):
    """تحليل البيانات من MongoDB"""
    if "_id" in item:
        del item["_id"]
    
    # Convert ISO strings back to dates/times
    for key, value in item.items():
        if isinstance(value, str):
            try:
                if "T" in value and ("+" in value or "Z" in value):
                    item[key] = datetime.fromisoformat(value.replace("Z", "+00:00"))
                elif key in ["date"] and "-" in value:
                    item[key] = datetime.fromisoformat(value).date()
                elif key in ["start_time", "end_time"] and ":" in value:
                    item[key] = datetime.strptime(value, '%H:%M:%S').time()
            except (ValueError, TypeError):
                pass  # Keep original value if parsing fails
    
    return item