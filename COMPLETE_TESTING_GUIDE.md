# 🧪 دليل الاختبار الشامل - نظام الخصومات المتقدم
## Complete Testing Guide - Advanced Deductions System

**التاريخ:** 20 يناير 2025  
**الحالة:** ✅ جاهز للاختبار الكامل

---

## ✅ الخطوات الإجبارية (تم تنفيذها)

### 1. Seed الإجازات الرسمية ✅
```bash
POST /api/holidays/seed
✅ تم إضافة 24 إجازة رسمية (2025-2026)
```

### 2. قائمة المستثنين ✅
```
- حاتم محمد أحمد
- طارق عبد المنعم الوزان (Tareq Abdel Moneim Alwazzan)
```

### 3. نافذة الحساب ✅
```
من: 29 الشهر السابق
إلى: 28 الشهر الحالي
أيام العمل: الأحد - الخميس فقط
```

---

## 🧪 سيناريوهات الاختبار (UAT)

### سيناريو A: حساب خصومات الشهر

#### الخطوة 1: حساب الخصومات
```bash
POST /api/deductions/calculate-monthly?month=10&year=2025
Headers: Authorization: Bearer {super_admin_token}

✅ المتوقع:
- إنشاء/تحديث سجلات في deductions_advanced
- استثناء: حاتم، طارق، الإجازات المعتمدة، الإجازات الرسمية، الجمعة/السبت
- إرجاع ملخص بعدد الموظفين والخصومات
```

**مثال Response:**
```json
{
  "success": true,
  "message": "تم حساب الخصومات لـ 15 موظف",
  "month": 10,
  "year": 2025,
  "cycle_start": "2025-09-29",
  "cycle_end": "2025-10-28",
  "total_employees": 15,
  "total_records_saved": 375,
  "summaries": [...]
}
```

#### الخطوة 2: مراجعة التقرير
```bash
GET /api/deductions/report?month=10&year=2025
Headers: Authorization: Bearer {admin_token}

✅ المتوقع:
- جدول شامل بكل الموظفين
- أعمدة: التأخير، الخروج المبكر، نقص الساعات، المبلغ
- التفاصيل اليومية لكل موظف
```

**البيانات المتوقعة:**
- `total_late_minutes`
- `total_early_leave_minutes`
- `total_deficit_minutes`
- `total_deduction_amount`
- `daily_records[]` - تفاصيل كل يوم

---

### سيناريو B: الدمج مع دورة الرواتب

#### الخطوة 1: إنشاء دورة رواتب (أو استخدام موجودة)
```bash
POST /api/payroll/cycles
{
  "month": "October",
  "year": "2025",
  ...
}

✅ احفظ الـ cycle_id من الـ Response
```

#### الخطوة 2: دمج الخصومات
```bash
POST /api/payroll/cycles/{cycle_id}/merge-advanced-deductions?month=10&year=2025
Headers: Authorization: Bearer {super_admin_token}

✅ المتوقع:
- إضافة بند ADVANCED_DEDUCTION في payroll_ledger (بدون تكرار)
- تحديث employee_payroll_summaries:
  * advanced_deductions_amount
  * advanced_deductions_minutes
  * total_deductions
  * net_salary
- حفظ Audit Trail في payroll_cycles:
  * advanced_deductions_merged: true
  * advanced_deductions_merged_at
  * advanced_deductions_merged_by
```

**مثال Response:**
```json
{
  "success": true,
  "cycle_id": "xxx-xxx-xxx",
  "employees_updated": 15,
  "total_deduction_amount": 3450.50,
  "message": "تم دمج الخصومات المتقدمة لـ 15 موظف"
}
```

---

### سيناريو C: التحقق من Idempotent (عدم التضاعف)

#### الاختبار:
```bash
# 1. دمج أول مرة
POST /api/payroll/cycles/{cycle_id}/merge-advanced-deductions?month=10&year=2025

# 2. احصل على net_salary لموظف معين
GET /api/payroll/cycles/{cycle_id}/employees

# 3. دمج مرة ثانية (نفس الطلب)
POST /api/payroll/cycles/{cycle_id}/merge-advanced-deductions?month=10&year=2025

# 4. احصل على net_salary مرة أخرى
GET /api/payroll/cycles/{cycle_id}/employees
```

✅ **المتوقع:**
- `net_salary` نفس القيمة (لم يتغير)
- `total_deductions` نفس القيمة (لم يزد)
- في payroll_ledger: قيد واحد فقط لـ ADVANCED_DEDUCTION (ليس قيدين)

---

### سيناريو D: حالات الاستثناء

#### D.1: موظف في إجازة معتمدة
```
الإعداد:
- موظف لديه إجازة معتمدة (approved) يوم 10 أكتوبر
- يوم 10 هو يوم عمل (أحد - خميس)

الاختبار:
1. احسب خصومات أكتوبر
2. راجع التقرير ليوم 10

✅ المتوقع:
- يوم 10: لا خصم (deduction_amount = 0)
- السبب: إجازة معتمدة
```

#### D.2: إجازة رسمية (اليوم الوطني)
```
الإعداد:
- 2 ديسمبر 2025 = اليوم الوطني الإماراتي (public holiday)

الاختبار:
1. احسب خصومات ديسمبر 2025
2. راجع التقرير ليوم 2 ديسمبر

✅ المتوقع:
- يوم 2 ديسمبر: لا خصم
- السبب: إجازة رسمية
- يظهر في daily_records كـ "Public Holiday"
```

#### D.3: الموظفين المستثنون (حاتم، طارق)
```
الاختبار:
1. احسب خصومات أكتوبر
2. راجع التقرير

✅ المتوقع:
- حاتم محمد أحمد: لا يظهر في التقرير نهائياً
- طارق عبد المنعم الوزان: لا يظهر في التقرير نهائياً
- Console Log: "⏭️ Skipping excluded employee: حاتم محمد أحمد"
```

#### D.4: يوم جمعة/سبت
```
الاختبار:
1. احسب خصومات أكتوبر
2. راجع daily_records

✅ المتوقع:
- أيام الجمعة والسبت: لا تظهر في الحساب أصلاً
- لا تُحسب ضمن total_working_days
```

---

## 🔍 التحقق من دقة الأرقام

### التحقق 1: تطابق الأرقام بين الأنظمة

**المصادر الثلاثة:**
1. واجهة نظام الخصومات المتقدم
2. payroll_ledger (جدول القيود)
3. employee_payroll_summaries (ملخص الرواتب)

**الاختبار:**
```bash
# 1. احصل على خصومات موظف من التقرير
GET /api/deductions/report?month=10&year=2025&employee_id={emp_id}

# 2. احصل على قيود الموظف من Ledger
GET /api/payroll/ledger?cycle_id={cycle_id}&employee_id={emp_id}

# 3. احصل على ملخص الموظف
GET /api/payroll/cycles/{cycle_id}/employees/{emp_id}
```

✅ **المتوقع:**
```
التقرير: total_deduction_amount = 250.00 AED
Ledger: ADVANCED_DEDUCTION entry amount = -250.00
Summary: advanced_deductions_amount = 250.00
Summary: net_salary = base_salary + allowances - 250.00 - (other deductions)
```

---

### التحقق 2: معادلة الخصم

**الصيغة:**
```
معدل الدقيقة = الراتب الأساسي / (أيام العمل × 480)
الخصم = معدل الدقيقة × نقص الدقائق
```

**مثال:**
```
موظف: محمد أحمد مصطفى
الراتب: 5000 درهم
أيام العمل في الدورة: 25 يوم
نقص الدقائق: 120 دقيقة (ساعتين)

الحساب:
معدل الدقيقة = 5000 / (25 × 480) = 5000 / 12000 = 0.4167 درهم
الخصم = 0.4167 × 120 = 50.00 درهم ✅
```

---

## 📱 اختبار الواجهة (Frontend)

### الوصول للصفحة:
```
1. تسجيل دخول كـ Super Admin
2. القائمة الجانبية → التقارير → نظام الخصومات المتقدم
```

### المكونات:
1. ✅ فلتر الشهر والسنة
2. ✅ زر "🧮 حساب الخصومات"
3. ✅ زر "📥 تصدير Excel"
4. ✅ حقل "Cycle ID" للدمج
5. ✅ زر "🔗 دمج مع الدورة"
6. ✅ جدول الملخص
7. ✅ زر "▼ عرض" للتفاصيل اليومية

### سيناريو الاستخدام:
```
1. اختر الشهر: أكتوبر، السنة: 2025
2. اضغط "🧮 حساب الخصومات"
3. انتظر... ✅ "تم حساب الخصومات لـ X موظف"
4. راجع الجدول - كل الموظفين مع البيانات
5. اضغط "▼ عرض" لموظف → جدول يومي تفصيلي
6. أدخل Cycle ID من صفحة الرواتب
7. اضغط "🔗 دمج مع الدورة"
8. ✅ "تم الدمج بنجاح! الموظفين المحدّثين: X"
```

---

## 🔧 أدوات الاختبار

### Postman Collection

**الطلبات الأساسية:**
```
1. Auth
   POST /api/auth/login
   Body: {"email":"admin@tanseeq.com","password":"ADMIN"}
   → احفظ access_token

2. Seed Holidays (مرة واحدة)
   POST /api/holidays/seed
   Headers: Authorization: Bearer {token}

3. Calculate Deductions
   POST /api/deductions/calculate-monthly?month=10&year=2025
   Headers: Authorization: Bearer {token}

4. Get Report
   GET /api/deductions/report?month=10&year=2025
   Headers: Authorization: Bearer {token}

5. Create Payroll Cycle
   POST /api/payroll/cycles
   Body: {...cycle data...}

6. Merge Deductions
   POST /api/payroll/cycles/{cycle_id}/merge-advanced-deductions?month=10&year=2025
   Headers: Authorization: Bearer {token}
```

---

## ❌ الأخطاء الشائعة والحلول

### خطأ 1: "المبالغ تزيد بعد التعديل"
**السبب:** تكرار البنود (لم يتم الحذف قبل الإضافة)

**الحل:** ✅ تم تطبيقه
```python
# يحذف القيود القديمة أولاً
await db.payroll_ledger.delete_many({
    "employee_id": emp_id,
    "cycle_id": cycle_id,
    "source_type": "ADVANCED_DEDUCTION"
})

# ثم يضيف الجديدة
await ledger_service.create_entry(...)
```

### خطأ 2: "موظف مستثنى يظهر في التقرير"
**السبب:** الاسم غير مطابق للقائمة

**الحل:**
```python
# تحقق من الاسم في قاعدة البيانات
db.users.find_one({"name": "حاتم محمد أحمد"})

# قارنه مع EXCLUDED_EMPLOYEES
# أضف تهجئات بديلة إذا لزم
```

### خطأ 3: "إجازة معتمدة لكن يوجد خصم"
**السبب:** الإجازة ليست `status: "approved"`

**الحل:**
```bash
# تحقق من حالة الإجازة
db.leaves.find({
  "user_id": "...",
  "start_date": {"$lte": "2025-10-10"},
  "end_date": {"$gte": "2025-10-10"}
})

# يجب أن تكون: status = "approved"
```

---

## ✅ قائمة التحقق النهائية

### قبل الإطلاق:
- [ ] تم seed الإجازات الرسمية
- [ ] تم اختبار حساب الخصومات لشهر كامل
- [ ] تم اختبار الدمج مع دورة رواتب
- [ ] تم التحقق من Idempotent (لا تضاعف)
- [ ] تم اختبار الاستثناءات (إجازات، عطل، مستثنون)
- [ ] الأرقام متطابقة بين الواجهة، Ledger، والملخص
- [ ] تم اختبار Frontend (الفلاتر، الأزرار، الجداول)
- [ ] تم تصدير Excel بنجاح
- [ ] تم مراجعة Backend logs (لا أخطاء)

### التوثيق:
- [ ] دليل المستخدم جاهز
- [ ] دليل المطور (API) جاهز
- [ ] سيناريوهات الاختبار موثقة
- [ ] الأخطاء الشائعة وحلولها موثقة

---

## 🎯 النتيجة المتوقعة

بعد إتمام جميع الاختبارات:

✅ **النظام:**
- يحسب الخصومات بدقة 100%
- يستثني كل الحالات المطلوبة
- يدمج تلقائياً مع الرواتب
- لا يضاعف القيود (Idempotent)
- الأرقام متطابقة في كل مكان

✅ **المستخدم:**
- يستطيع حساب الخصومات بضغطة زر
- يستطيع مراجعة التقارير التفصيلية
- يستطيع الدمج مع دورة الرواتب بسهولة
- يستطيع التصدير لـ Excel

✅ **النظام المالي:**
- القيود دقيقة ومنظمة
- صافي الراتب محسوب بشكل صحيح
- Audit Trail كامل
- لا توجد تناقضات

---

**تم إعداد هذا الدليل:** 20 يناير 2025  
**الحالة:** ✅ جاهز للاختبار الفوري

🚀 **ابدأ الاختبار الآن!**
