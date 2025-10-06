# نظام الحضور والخصومات المتقدم - أكتوبر 2025
# Advanced Attendance & Deduction System - October 2025

## نظرة عامة | Overview

نظام متقدم لإدارة خصومات الحضور والتأخير وفقاً للقواعد الجديدة المطبقة في أكتوبر 2025.

Advanced system for managing attendance and lateness deductions according to the new rules implemented in October 2025.

## القواعد الأساسية | Core Rules

### المرات المجانية | Free Occurrences
- **4 مرات مجانية شهرياً** لكل موظف
- كل مرة مجانية تغطي **حتى 15 دقيقة** تأخير
- تُستخدم المرات المجانية تلقائياً للتأخير البسيط (≤ 20 دقيقة)

### فئات الخصومات | Deduction Categories

#### 1. التأخير البسيط (1-20 دقيقة)
- **أول 4 مرات**: مجانية (حتى 15 دقيقة لكل مرة)
- **بعد استنزاف المرات المجانية**: خصم بالدقائق الفعلية

#### 2. التأخير الكبير (أكثر من 20 دقيقة)
- **خصم مباشر** بالدقائق الفعلية
- **لا يستفيد من المرات المجانية**

#### 3. التأخير المتوسط (60-120 دقيقة)
- **خصم نصف يوم** من الراتب

#### 4. التأخير الشديد (أكثر من 120 دقيقة)
- **خصم يوم كامل** من الراتب

### الاستثناءات | Exceptions

#### الموظفين المعفيين من الخصومات
- **حاتم** (`hatem@tan-seeq.co`): معفى من جميع الخصومات
- يتم تسجيل الحضور ولكن بدون خصومات مالية

#### الموظفين بنهاية مرنة
- **طارق**: دخول مبكر مسموح + خروج مرن
- لا خصومات على الخروج المبكر

## الملفات الأساسية | Core Files

### Backend Files
```
backend/
├── attendance_engine.py      # محرك الحضور والخصومات الرئيسي
├── attendance_models.py      # نماذج البيانات والتعريفات
├── server.py                # API endpoints (lines 1862-2614)
└── test_attendance_system.py # اختبارات النظام
```

### Frontend Files
```
frontend/src/components/AttendanceDeductions/
├── AttendanceDeductionsAdmin.js  # واجهة السوبر أدمن
└── MyAttendanceDeductions.js     # واجهة الموظف
```

## API Endpoints

### للموظفين | Employee Endpoints
```
GET  /api/deductions?employee_id={id}&month={YYYY-MM}  # جلب خصوماتي
GET  /api/attendance/stats/{employee_id}/{month}       # إحصائيات الحضور
GET  /api/notifications?category=deduction             # إشعارات الخصومات
```

### للإدارة | Admin Endpoints
```
GET    /api/deductions                    # جميع الخصومات
POST   /api/deductions/manual             # إنشاء خصم يدوي
PATCH  /api/deductions/{id}               # تعديل خصم
POST   /api/deductions/{id}/void          # إلغاء خصم
GET    /api/attendance/policies/{emp_id}  # سياسة الحضور
POST   /api/attendance/policies           # إنشاء سياسة جديدة
```

## نماذج البيانات | Data Models

### PayrollDeduction
```python
{
    "id": "uuid",
    "employee_id": "string",
    "employee_name": "string",
    "deduction_type": "lateness|early_leave|missing_checkout|manual",
    "category": "minutes|half_day|full_day|custom",
    "date": "YYYY-MM-DD",
    "minutes": 0,
    "amount": 0.0,
    "daily_rate": 0.0,
    "reason": "string",
    "source": "auto|manual",
    "is_voided": false
}
```

### MonthlyLatenessCounters
```python
{
    "employee_id": "string",
    "month": "YYYY-MM",
    "free_occurrences_used": 0,
    "free_occurrences_limit": 4,
    "total_late_days": 0,
    "total_late_minutes": 0,
    "total_deduction_amount": 0.0
}
```

## أمثلة الاستخدام | Usage Examples

### حساب خصم التأخير
```python
from attendance_engine import AttendanceEngine
from attendance_models import DeductionType

engine = AttendanceEngine(db)
await engine.initialize()

# خصم تأخير 10 دقائق (مرة مجانية)
deduction, is_free = await engine.apply_deduction_rules(
    employee_id="emp_001",
    minutes=10,
    deduction_type=DeductionType.LATENESS,
    use_free_occurrences=True
)

if is_free:
    print("تم استخدام مرة مجانية")
else:
    print(f"مبلغ الخصم: {deduction.amount:.2f} درهم")
```

### إنشاء خصم يدوي
```python
deduction = await engine.create_manual_deduction(
    employee_id="emp_001",
    deduction_type=DeductionType.MANUAL,
    category=DeductionCategory.CUSTOM,
    target_date=date.today(),
    amount=100.0,
    reason="خصم إداري",
    created_by="admin_001"
)
```

## المهام المجدولة | Scheduled Tasks

### AttendanceScheduler
```python
scheduler = AttendanceScheduler(engine)

# تحذير عدم تسجيل الانصراف - 18:10
await scheduler.check_missing_checkouts_warning()

# معالجة نهائية لعدم تسجيل الانصراف - 23:59
await scheduler.process_missing_checkouts_final()

# إعادة احتساب يومي - 01:00
await scheduler.daily_recompute()

# تصفير العدادات الشهرية - أول يوم من الشهر
await scheduler.monthly_reset()
```

## الإشعارات | Notifications

### أنواع الإشعارات
- **تحذير تأخير**: عند استخدام مرة مجانية
- **خصم تأخير**: عند تطبيق خصم فعلي
- **خصم خروج مبكر**: عند الخروج قبل الوقت المحدد
- **عدم تسجيل انصراف**: تحذير في 18:10 وخصم في 23:59
- **خصم يدوي**: عند إضافة خصم من الإدارة
- **إلغاء خصم**: عند إلغاء خصم من الإدارة

## الأمان والصلاحيات | Security & Permissions

### صلاحيات الموظف
- عرض خصوماته الشخصية فقط
- عرض إحصائيات حضوره
- استلام الإشعارات وإقرارها

### صلاحيات الأدمن
- عرض جميع الخصومات
- إنشاء وتعديل وإلغاء الخصومات
- إدارة سياسات الحضور
- عرض إحصائيات جميع الموظفين

### صلاحيات السوبر أدمن
- جميع صلاحيات الأدمن
- إدارة إعدادات النظام
- الوصول لسجلات التدقيق

## التشغيل والاختبار | Running & Testing

### تشغيل الاختبارات
```bash
cd /app/backend
python test_attendance_system.py
```

### تهيئة النظام
```python
from attendance_engine import AttendanceEngine

engine = AttendanceEngine(db)
await engine.initialize()  # إنشاء الفهارس والإعدادات
```

## الصيانة | Maintenance

### تنظيف البيانات القديمة
```python
# حذف الخصومات الملغية القديمة (أكثر من سنة)
old_date = datetime.now() - timedelta(days=365)
await db.payroll_deductions.delete_many({
    "is_voided": True,
    "voided_at": {"$lt": old_date.isoformat()}
})
```

### إعادة احتساب الخصومات
```python
# إعادة احتساب شهر معين
await engine.process_daily_attendance(
    employee_id="emp_001",
    target_date=date(2025, 10, 15),
    force_recompute=True
)
```

## الدعم والتطوير | Support & Development

### إضافة قواعد جديدة
1. تحديث `AttendanceSystemConfig` في `attendance_models.py`
2. تعديل `apply_deduction_rules` في `attendance_engine.py`
3. إضافة اختبارات في `test_attendance_system.py`
4. تحديث الواجهات في `frontend/`

### تخصيص الاستثناءات
```python
# في get_employee_policy()
if user_doc.get("email") == "new_exempt@company.com":
    policy = AttendancePolicy(
        employee_id=employee_id,
        employee_name=user_doc.get("name", ""),
        no_penalties=True  # معفى من الخصومات
    )
```

---

## ملاحظات مهمة | Important Notes

⚠️ **تأكد من تشغيل المهام المجدولة** لضمان عمل النظام بشكل صحيح

⚠️ **راجع الإعدادات** قبل التطبيق في بيئة الإنتاج

⚠️ **احتفظ بنسخ احتياطية** من قاعدة البيانات قبل التحديثات الكبيرة

✅ **النظام جاهز للاستخدام** مع جميع القواعد المطلوبة

---

**تم التطوير بواسطة**: فريق تطوير تنسيق  
**تاريخ الإصدار**: أكتوبر 2025  
**الإصدار**: 1.0.0