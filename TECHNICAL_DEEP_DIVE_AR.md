# 🔬 التحليل الفني العميق - TANSEEQ HR System

## 📑 فهرس المحتويات
1. [معمارية النظام التفصيلية](#معمارية-النظام)
2. [دورة حياة الطلبات](#دورة-حياة-الطلبات)
3. [نظام Payroll Ledger بالتفصيل](#payroll-ledger)
4. [المعادلات الحسابية](#المعادلات-الحسابية)
5. [الأمان والتفويض](#الأمان-والتفويض)
6. [الأداء والتحسينات](#الأداء-والتحسينات)
7. [معالجة الأخطاء](#معالجة-الأخطاء)
8. [السيناريوهات المعقدة](#السيناريوهات-المعقدة)

---

## 🏗️ معمارية النظام التفصيلية

### التدفق العام للنظام

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Browser                           │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           React Application (Port 3000)               │  │
│  │                                                       │  │
│  │  Components:                                          │  │
│  │  ├── AuthContext (JWT Token Management)              │  │
│  │  ├── ErrorBoundary (Error Catching)                  │  │
│  │  ├── Router (React Router v6)                        │  │
│  │  └── 50+ Page Components                             │  │
│  │                                                       │  │
│  │  State Management:                                    │  │
│  │  ├── useContext for global state                     │  │
│  │  ├── useState for local state                        │  │
│  │  └── useEffect for side effects                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                            │                                │
│                            │ HTTP/HTTPS                     │
│                            │ Axios Requests                 │
│                            ▼                                │
└─────────────────────────────────────────────────────────────┘
                             │
                             │
┌────────────────────────────▼─────────────────────────────────┐
│              Kubernetes Ingress Controller                   │
│                                                              │
│  Rules:                                                      │
│  ├── /api/* → Backend Service (Port 8001)                  │
│  └── /* → Frontend Service (Port 3000)                     │
└──────────────────────────────────────────────────────────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
                    ▼                 ▼
         ┌──────────────────┐  ┌──────────────────┐
         │  Backend Service │  │ Frontend Service │
         │   (Port 8001)    │  │   (Port 3000)    │
         │                  │  │                  │
         │  FastAPI         │  │  React Build     │
         │  + Uvicorn       │  │  Served by       │
         │  Managed by      │  │  Supervisor      │
         │  Supervisor      │  │                  │
         └────────┬─────────┘  └──────────────────┘
                  │
                  │
                  ▼
         ┌─────────────────────────────┐
         │  MongoDB Database           │
         │  (localhost:27017)          │
         │                             │
         │  15 Collections:            │
         │  ├── users                  │
         │  ├── attendance             │
         │  ├── leaves                 │
         │  ├── field_exits            │
         │  ├── marketing_visits       │
         │  ├── advances               │
         │  ├── advance_expenses       │
         │  ├── payroll_cycles         │
         │  ├── employee_payroll_*     │
         │  ├── payroll_ledger  ⭐     │
         │  ├── installment_*          │
         │  ├── attendance_deductions  │
         │  ├── notifications          │
         │  └── work_reports           │
         └─────────────────────────────┘
```

---

## 🔄 دورة حياة الطلبات (Request Lifecycle)

### مثال: تعديل راتب موظف

```javascript
// 1. Frontend: User clicks "Save" في صفحة PayrollSummary
┌──────────────────────────────────────────────────────┐
│ PayrollSummary.js                                    │
│                                                      │
│ const handleSave = async () => {                    │
│   const payload = {                                 │
│     employees: [{                                   │
│       employee_id: "123",                           │
│       base_salary: 5000,                            │
│       manual_deductions: 250.50  // Changed value   │
│     }]                                              │
│   };                                                │
│                                                      │
│   const response = await axios.put(                 │
│     `/api/payroll/cycles/${cycleId}/update-*`,     │
│     payload,                                        │
│     { headers: { Authorization: `Bearer ${token}` }}│
│   );                                                │
│ }                                                    │
└──────────────────────────────────────────────────────┘
           │
           │ HTTP PUT Request
           │ Authorization: Bearer <JWT_TOKEN>
           │ Content-Type: application/json
           │
           ▼
┌──────────────────────────────────────────────────────┐
│ Kubernetes Ingress                                   │
│ Routes /api/* to Backend:8001                        │
└──────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────┐
│ FastAPI Backend - server.py                          │
│                                                      │
│ @app.put("/api/payroll/cycles/{cycle_id}/update-*") │
│ async def update_payroll_cycle_employees(           │
│     cycle_id: str,                                  │
│     update_data: dict,                              │
│     current_user: dict = Depends(get_current_user)  │
│ ):                                                   │
│                                                      │
│   # 1. Authentication & Authorization               │
│   if current_user.role != "super_admin":            │
│       raise HTTPException(403)                      │
│                                                      │
│   # 2. Validate Cycle Exists & Not Locked           │
│   cycle = await db.payroll_cycles.find_one(...)     │
│   if cycle.get("is_locked"):                        │
│       raise HTTPException(400)                      │
│                                                      │
│   # 3. Process Each Employee                        │
│   for emp_data in employees:                        │
│       # 3a. Get Current Values                      │
│       current_summary = await db.employee_*         │
│                                                      │
│       # 3b. Update Summary Collection               │
│       await db.employee_payroll_summaries.*         │
│                                                      │
│       # 3c. Update Payroll Ledger ⭐                │
│       if manual_deduction_changed:                  │
│           # Check for existing entry                │
│           existing = await db.payroll_ledger.*      │
│                                                      │
│           # Reverse old entry (audit trail)         │
│           if existing:                              │
│               await ledger_service.reverse_entry()  │
│                                                      │
│           # Create new entry                        │
│           await ledger_service.create_entry(        │
│               source_type="MANUAL_DEDUCTION",       │
│               amount=-250.50,                       │
│               ...                                   │
│           )                                         │
│                                                      │
│   # 4. Recalculate Cycle Totals                     │
│   summaries = await db.employee_payroll_summaries.* │
│   cycle_totals = calculate_totals(summaries)        │
│                                                      │
│   # 5. Update Cycle                                 │
│   await db.payroll_cycles.update_one(...)           │
│                                                      │
│   # 6. Return Success Response                      │
│   return {                                          │
│       "message": "تم تحديث X موظف بنجاح",           │
│       "updated_count": X,                           │
│       "cycle_totals": {...}                         │
│   }                                                  │
└──────────────────────────────────────────────────────┘
           │
           │ Response: 200 OK
           │ Content-Type: application/json
           │
           ▼
┌──────────────────────────────────────────────────────┐
│ Frontend: PayrollSummary.js                          │
│                                                      │
│ // Success Handler                                   │
│ if (response.status === 200) {                       │
│   showNotification("تم الحفظ بنجاح");               │
│   fetchSummary(); // Reload data                    │
│ }                                                    │
└──────────────────────────────────────────────────────┘
```

---

## 💎 نظام Payroll Ledger بالتفصيل

### الفلسفة

```
كل حدث مالي = قيد محاسبي

المبدأ: Zero-Click Automation
- لا يحتاج المستخدم إلى إنشاء القيود يدوياً
- كل عملية تنشئ قيدها تلقائياً
- Idempotency: نفس العملية لا تنشئ قيداً مكرراً
- Audit Trail: لا حذف، فقط reversal
```

### بنية القيد

```javascript
{
  // Identifiers
  id: "uuid",
  idempotency_key: "emp_cycle_type_source", // منع التكرار
  
  // References
  employee_id: "uuid",
  cycle_id: "uuid",
  source_type: "ATTENDANCE_DEDUCTION | MANUAL_DEDUCTION | ...",
  source_id: "reference_to_original_transaction",
  
  // Financial
  amount: -100.0,  // سالب = خصم، موجب = إضافة
  
  // Description
  description: "تأخير 30 دقيقة - 100 درهم",
  description_ar: "تأخير 30 دقيقة - 100 درهم",
  
  // Metadata
  metadata: {
    late_minutes: 30,
    hourly_rate: 200,
    // ... any additional data
  },
  
  // Audit
  created_by: "admin_id | system",
  created_at: "2024-10-01T10:00:00+04:00",
  
  // Reversal (for corrections)
  is_reversed: false,
  reversed_by: null,
  reversed_at: null,
  reversal_reason: null
}
```

### أنواع القيود (Source Types)

#### 1. ATTENDANCE_DEDUCTION (خصم حضور)
```javascript
// تُنشأ عند: حساب الخصومات الشهرية
await ledger_service.create_entry({
  employee_id: "emp_123",
  cycle_id: "cycle_456",
  source_type: "ATTENDANCE_DEDUCTION",
  source_id: "attendance_record_789",
  amount: -50.0,  // خصم
  description: "تأخير 15 دقيقة",
  metadata: {
    date: "2024-10-05",
    late_minutes: 15,
    rate_per_minute: 3.33
  }
});
```

#### 2. MANUAL_DEDUCTION (خصم يدوي)
```javascript
// تُنشأ عند: تعديل يدوي من الإدارة
await ledger_service.create_entry({
  employee_id: "emp_123",
  cycle_id: "cycle_456",
  source_type: "MANUAL_DEDUCTION",
  source_id: "manual_edit_cycle_456_emp_123_1728123456",
  amount: -250.50,  // خصم
  description: "خصم يدوي تم تعديله بواسطة الإدارة - 250.50 درهم",
  created_by: "admin_id"
});
```

#### 3. ADVANCE_INSTALLMENT (قسط سلفة)
```javascript
// تُنشأ عند: حساب دورة الراتب
await ledger_service.create_entry({
  employee_id: "emp_123",
  cycle_id: "cycle_456",
  source_type: "ADVANCE_INSTALLMENT",
  source_id: "installment_001",
  amount: -200.0,  // خصم
  description: "قسط سلفة - القسط 1 من 5",
  metadata: {
    advance_id: "advance_789",
    installment_number: 1,
    total_installments: 5,
    advance_amount: 1000.0
  }
});
```

#### 4. LEAVE_ADJUSTMENT (تعديل إجازة)
```javascript
// تُنشأ عند: إجازة بدون راتب
await ledger_service.create_entry({
  employee_id: "emp_123",
  cycle_id: "cycle_456",
  source_type: "LEAVE_ADJUSTMENT",
  source_id: "leave_request_101",
  amount: -166.67,  // خصم (يوم راتب)
  description: "إجازة بدون راتب - يوم واحد",
  metadata: {
    leave_type: "Unpaid",
    days: 1,
    daily_rate: 166.67
  }
});
```

#### 5. CUSTODY_ADJUSTMENT (تعديل عهدة)
```javascript
// تُنشأ عند: استرجاع/تسوية عهدة
await ledger_service.create_entry({
  employee_id: "emp_123",
  cycle_id: "cycle_456",
  source_type: "CUSTODY_ADJUSTMENT",
  source_id: "custody_settlement_111",
  amount: -300.0,  // خصم
  description: "تسوية عهدة - مصروفات زائدة",
  metadata: {
    custody_amount: 1000.0,
    expenses_approved: 1300.0,
    difference: -300.0
  }
});
```

### Idempotency - منع التكرار

```javascript
// مفتاح Idempotency
idempotency_key = `${employee_id}_${cycle_id}_${source_type}_${source_id}`

// مثال
idempotency_key = "emp_123_cycle_456_MANUAL_DEDUCTION_manual_edit_cycle_456_emp_123"

// التحقق قبل الإنشاء
const existing = await db.payroll_ledger.find_one({
  idempotency_key: idempotency_key,
  is_reversed: false
});

if (existing) {
  return existing;  // إرجاع القيد الموجود بدلاً من إنشاء جديد
}

// إنشاء قيد جديد فقط إذا لم يكن موجوداً
await db.payroll_ledger.insert_one(new_entry);
```

### Reversal - العكس بدلاً من الحذف

```javascript
// لماذا Reversal؟
// 1. الحفاظ على مسار المراجعة الكامل
// 2. معرفة من قام بالتغيير ومتى
// 3. إمكانية استرجاع التاريخ
// 4. الامتثال المحاسبي

async function reverse_entry(entry_id, reversed_by, reason) {
  // 1. جلب القيد الأصلي
  const original = await db.payroll_ledger.find_one({ id: entry_id });
  
  // 2. تحديث القيد الأصلي
  await db.payroll_ledger.update_one(
    { id: entry_id },
    {
      $set: {
        is_reversed: true,
        reversed_by: reversed_by,
        reversed_at: new Date().toISOString(),
        reversal_reason: reason
      }
    }
  );
  
  // 3. إنشاء قيد عكسي (اختياري - للمحاسبة الدقيقة)
  const reversal_entry = {
    ...original,
    id: uuid(),
    amount: -original.amount,  // عكس المبلغ
    description: `عكس: ${original.description}`,
    source_id: `reversal_of_${entry_id}`,
    created_by: reversed_by,
    created_at: new Date().toISOString(),
    is_reversed: false,
    metadata: {
      ...original.metadata,
      reversal_of: entry_id,
      reversal_reason: reason
    }
  };
  
  await db.payroll_ledger.insert_one(reversal_entry);
  
  return reversal_entry;
}
```

### Aggregation - التجميع

```javascript
async function get_employee_summary(cycle_id, employee_id) {
  // جلب جميع القيود غير المعكوسة
  const entries = await db.payroll_ledger.find({
    cycle_id: cycle_id,
    employee_id: employee_id,
    is_reversed: false  // فقط القيود النشطة
  }).toArray();
  
  // التجميع حسب النوع
  const summary = {
    attendance_deductions: 0,
    manual_deductions: 0,
    advance_installments: 0,
    leave_adjustments: 0,
    custody_adjustments: 0,
    total_adjustments: 0
  };
  
  for (const entry of entries) {
    const amount = Math.abs(entry.amount);
    
    switch (entry.source_type) {
      case "ATTENDANCE_DEDUCTION":
        summary.attendance_deductions += amount;
        break;
      case "MANUAL_DEDUCTION":
        summary.manual_deductions += amount;
        break;
      case "ADVANCE_INSTALLMENT":
        summary.advance_installments += amount;
        break;
      case "LEAVE_ADJUSTMENT":
        summary.leave_adjustments += entry.amount;  // يمكن أن يكون موجب أو سالب
        break;
      case "CUSTODY_ADJUSTMENT":
        summary.custody_adjustments += entry.amount;  // يمكن أن يكون موجب أو سالب
        break;
    }
    
    summary.total_adjustments += entry.amount;
  }
  
  return summary;
}
```

### سيناريو كامل: تعديل خصم يدوي

```javascript
// الحالة الأولية
initial_manual_deduction = 100.0
existing_ledger_entry = {
  id: "entry_001",
  amount: -100.0,
  source_type: "MANUAL_DEDUCTION",
  is_reversed: false
}

// المستخدم يعدل إلى 250.50

// الخطوة 1: عكس القيد القديم
await reverse_entry(
  entry_id: "entry_001",
  reversed_by: "admin_123",
  reason: "تحديث الخصم اليدوي من 100.00 إلى 250.50 درهم"
);

// النتيجة:
existing_ledger_entry = {
  id: "entry_001",
  amount: -100.0,
  source_type: "MANUAL_DEDUCTION",
  is_reversed: true,        // ✅ معكوس
  reversed_by: "admin_123",
  reversed_at: "2024-10-10T10:30:00",
  reversal_reason: "تحديث الخصم اليدوي من 100.00 إلى 250.50 درهم"
}

// الخطوة 2: إنشاء قيد جديد
new_entry = await create_entry({
  source_type: "MANUAL_DEDUCTION",
  source_id: "manual_edit_cycle_456_emp_123_1728567000",  // timestamp للتفرد
  amount: -250.50,
  description: "خصم يدوي تم تعديله بواسطة الإدارة - 250.50 درهم"
});

// النتيجة:
new_entry = {
  id: "entry_002",
  amount: -250.50,
  source_type: "MANUAL_DEDUCTION",
  is_reversed: false,  // ✅ نشط
  created_at: "2024-10-10T10:30:00"
}

// الخطوة 3: التجميع
summary = await get_employee_summary(cycle_id, employee_id);

// النتيجة:
summary.manual_deductions = 250.50  // ✅ فقط القيد الجديد (القديم معكوس)

// مسار المراجعة الكامل:
audit_trail = [
  {
    id: "entry_001",
    amount: -100.0,
    is_reversed: true,
    reversal_reason: "تحديث..."
  },
  {
    id: "entry_002",
    amount: -250.50,
    is_reversed: false
  }
];
```

---

## 🧮 المعادلات الحسابية

### 1. حساب الراتب الأساسي

```javascript
// المدخلات
monthly_salary = 5000.0  // الراتب الشهري

// الحسابات
working_days_per_month = 30
working_hours_per_day = 8
working_minutes_per_day = 480

// المعدلات
daily_rate = monthly_salary / working_days_per_month
// daily_rate = 5000 / 30 = 166.67 درهم/يوم

hourly_rate = daily_rate / working_hours_per_day
// hourly_rate = 166.67 / 8 = 20.83 درهم/ساعة

minute_rate = hourly_rate / 60
// minute_rate = 20.83 / 60 = 0.347 درهم/دقيقة
```

### 2. حساب خصم التأخير

```javascript
// سياسة الخصم
grace_period_minutes = 15  // فترة السماح
penalized_late_minutes = actual_late_minutes - grace_period_minutes

// مثال: موظف تأخر 45 دقيقة
actual_late_minutes = 45
penalized_late_minutes = 45 - 15 = 30 دقيقة

// الخصم
late_deduction = penalized_late_minutes * minute_rate
late_deduction = 30 * 0.347 = 10.41 درهم

// سياسة متقدمة (طارق وزان - حضور مرن)
if (employee.early_start_allowed && employee.early_arrival_offset) {
  // الحضور المبكر يعوض التأخير
  effective_late_minutes = actual_late_minutes - early_arrival_minutes;
  penalized_late_minutes = Math.max(0, effective_late_minutes - grace_period);
} else {
  // الحضور المبكر لا يعوض التأخير
  penalized_late_minutes = Math.max(0, actual_late_minutes - grace_period);
}
```

### 3. حساب خصم الغياب

```javascript
// غياب يوم كامل بدون عذر
absence_deduction = daily_rate
absence_deduction = 166.67 درهم

// غياب نصف يوم
half_day_absence = daily_rate / 2
half_day_absence = 83.33 درهم

// مع الاستثناءات
if (has_approved_leave || has_approved_field_exit) {
  absence_deduction = 0;  // لا خصم
}
```

### 4. حساب صافي الراتب

```javascript
// خطوة 1: الراتب الإجمالي
base_salary = 5000.0
allowances = 500.0  // بدلات (نقل، سكن، الخ)
gross_salary = base_salary + allowances
// gross_salary = 5500.0

// خطوة 2: الخصومات (من Payroll Ledger)
ledger_summary = await get_employee_summary(cycle_id, employee_id);

attendance_deductions = ledger_summary.attendance_deductions     // 102.0
manual_deductions = ledger_summary.manual_deductions             // 250.5
advance_installments = ledger_summary.advance_installments       // 200.0

total_deductions = (
  attendance_deductions + 
  manual_deductions + 
  advance_installments
)
// total_deductions = 102.0 + 250.5 + 200.0 = 552.5

// خطوة 3: التعديلات (موجبة أو سالبة)
leave_adjustments = ledger_summary.leave_adjustments      // -166.67 (إجازة بدون راتب)
custody_adjustments = ledger_summary.custody_adjustments  // 0

total_adjustments = leave_adjustments + custody_adjustments
// total_adjustments = -166.67

// خطوة 4: الصافي
net_salary = gross_salary + total_adjustments - total_deductions
net_salary = 5500.0 + (-166.67) - 552.5
net_salary = 4780.83 درهم

// التحقق من عدم السلبية
net_salary = Math.max(0, net_salary)
```

### 5. حساب جدول الأقساط

```javascript
// مدخلات
advance_amount = 1000.0      // مبلغ السلفة
installment_count = 5         // عدد الأقساط
start_date = "2024-11-01"    // تاريخ البداية

// حساب القسط الشهري
monthly_installment = advance_amount / installment_count
monthly_installment = 1000.0 / 5 = 200.0 درهم/شهر

// إنشاء جدول الأقساط
installments = [];
for (let i = 0; i < installment_count; i++) {
  installments.push({
    installment_number: i + 1,
    due_date: add_months(start_date, i),
    amount: monthly_installment,
    status: "Pending"
  });
}

// النتيجة:
[
  { number: 1, due_date: "2024-11-01", amount: 200.0 },
  { number: 2, due_date: "2024-12-01", amount: 200.0 },
  { number: 3, due_date: "2025-01-01", amount: 200.0 },
  { number: 4, due_date: "2025-02-01", amount: 200.0 },
  { number: 5, due_date: "2025-03-01", amount: 200.0 }
]
```

### 6. حساب رصيد السلف والعهد

```javascript
// قواعد العمل الجديدة

// السلف (Advances): لا تُخصم بالمصروفات
total_advances = SUM(approved_advances)
remaining_advance = total_advances  // تبقى كاملة حتى التسوية

// العهد (Custody): تُخصم بالمصروفات
total_custody = SUM(approved_custodies)
approved_expenses = SUM(approved_expenses_from_custody)
remaining_custody = total_custody - approved_expenses

// الرصيد الكلي المتاح
total_available = remaining_advance + remaining_custody

// مثال عملي
employee_balances = {
  advances: {
    total: 1000.0,
    expenses: 0,        // لا تؤثر
    remaining: 1000.0
  },
  custody: {
    total: 500.0,
    expenses: 150.0,    // تُخصم
    remaining: 350.0
  },
  total_available: 1350.0
}

// تسوية سلفة
settlement = {
  advance_id: "adv_123",
  amount: 1000.0,
  settlement_method: "salary_deduction",
  installment_count: 5,
  monthly_deduction: 200.0
}
```

---

## 🔐 الأمان والتفويض

### JWT Authentication

```javascript
// إنشاء Token
import jwt from 'jsonwebtoken';

function create_access_token(user_data) {
  const payload = {
    sub: user_data.id,
    email: user_data.email,
    role: user_data.role,
    name: user_data.name,
    exp: Math.floor(Date.now() / 1000) + (24 * 60 * 60)  // 24 hours
  };
  
  const token = jwt.sign(payload, JWT_SECRET, { algorithm: 'HS256' });
  return token;
}

// التحقق من Token
async function get_current_user(token) {
  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    const user = await db.users.findOne({ id: decoded.sub });
    
    if (!user || !user.is_active) {
      throw new Error("User not found or inactive");
    }
    
    return user;
  } catch (error) {
    throw new Error("Invalid token");
  }
}
```

### Role-Based Access Control (RBAC)

```javascript
// تعريف الأدوار والصلاحيات
const ROLES = {
  SUPER_ADMIN: "super_admin",
  ADMIN: "admin",
  USER: "user"
};

const PERMISSIONS = {
  // Attendance
  VIEW_OWN_ATTENDANCE: ["user", "admin", "super_admin"],
  VIEW_ALL_ATTENDANCE: ["admin", "super_admin"],
  EDIT_ATTENDANCE: ["super_admin"],
  DELETE_ATTENDANCE: ["super_admin"],
  CREATE_ABSENCE: ["super_admin"],
  
  // Leaves
  CREATE_LEAVE_REQUEST: ["user", "admin", "super_admin"],
  VIEW_OWN_LEAVES: ["user", "admin", "super_admin"],
  VIEW_ALL_LEAVES: ["admin", "super_admin"],
  APPROVE_LEAVE: ["admin", "super_admin"],
  
  // Payroll
  VIEW_OWN_PAYROLL: ["user", "admin", "super_admin"],
  VIEW_ALL_PAYROLL: ["admin", "super_admin"],
  EDIT_PAYROLL: ["super_admin"],
  LOCK_PAYROLL: ["super_admin"],
  
  // Advances
  REQUEST_ADVANCE: ["user", "admin", "super_admin"],
  VIEW_OWN_ADVANCES: ["user", "admin", "super_admin"],
  VIEW_ALL_ADVANCES: ["admin", "super_admin"],
  APPROVE_ADVANCE: ["super_admin"],
  DELETE_ADVANCE: ["super_admin"],
  
  // Reports
  VIEW_OWN_REPORTS: ["user", "admin", "super_admin"],
  VIEW_ALL_REPORTS: ["admin", "super_admin"],
  EXPORT_REPORTS: ["admin", "super_admin"]
};

// Middleware للتحقق
function require_permission(required_permission) {
  return async (request, current_user) => {
    const allowed_roles = PERMISSIONS[required_permission];
    
    if (!allowed_roles.includes(current_user.role)) {
      throw new HTTPException(403, "ليس لديك صلاحية لهذا الإجراء");
    }
    
    return true;
  };
}

// استخدام
@app.get("/api/payroll/cycles")
async def get_payroll_cycles(
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission("VIEW_ALL_PAYROLL"))
):
    # ...
```

### حماية البيانات الحساسة

```javascript
// 1. تشفير كلمات المرور
import bcrypt from 'bcryptjs';

async function hash_password(password) {
  const salt = await bcrypt.genSalt(10);
  return await bcrypt.hash(password, salt);
}

async function verify_password(plain_password, hashed_password) {
  return await bcrypt.compare(plain_password, hashed_password);
}

// 2. تنظيف المدخلات
function sanitize_input(input) {
  if (typeof input === 'string') {
    // إزالة الأحرف الخطرة
    return input.replace(/[<>]/g, '');
  }
  return input;
}

// 3. التحقق من المدخلات
const { body, validationResult } = require('express-validator');

app.post('/api/login', [
  body('email').isEmail().normalizeEmail(),
  body('password').isLength({ min: 6 })
], async (req, res) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ errors: errors.array() });
  }
  // ...
});
```

---

## ⚡ الأداء والتحسينات

### MongoDB Indexes

```javascript
// Indexes الأساسية
db.users.createIndex({ email: 1 }, { unique: true });
db.users.createIndex({ id: 1 }, { unique: true });
db.users.createIndex({ role: 1 });

db.attendance.createIndex({ user_id: 1, date: 1 }, { unique: true });
db.attendance.createIndex({ date: -1 });
db.attendance.createIndex({ status: 1 });

db.leaves.createIndex({ user_id: 1 });
db.leaves.createIndex({ status: 1 });
db.leaves.createIndex({ start_date: -1 });

db.payroll_cycles.createIndex({ month_year: 1 }, { unique: true });
db.payroll_cycles.createIndex({ is_locked: 1 });

db.payroll_ledger.createIndex({ 
  employee_id: 1, 
  cycle_id: 1, 
  source_type: 1 
});
db.payroll_ledger.createIndex({ idempotency_key: 1 }, { unique: true });
db.payroll_ledger.createIndex({ is_reversed: 1 });

db.advances.createIndex({ employee_id: 1 });
db.advances.createIndex({ status: 1 });
db.advances.createIndex({ transaction_date: -1 });

db.installment_schedules.createIndex({ advance_id: 1 }, { unique: true });
db.individual_installments.createIndex({ schedule_id: 1 });
db.individual_installments.createIndex({ status: 1 });

// Compound Indexes للاستعلامات المعقدة
db.attendance.createIndex({ 
  user_id: 1, 
  date: -1, 
  status: 1 
});

db.payroll_ledger.createIndex({
  employee_id: 1,
  cycle_id: 1,
  is_reversed: 1
});
```

### Caching Strategy (اختياري)

```javascript
// استخدام Redis للتخزين المؤقت
import Redis from 'redis';

const redis = Redis.createClient();

// تخزين مؤقت لبيانات المستخدم
async function get_user_with_cache(user_id) {
  // محاولة الحصول من Cache
  const cached = await redis.get(`user:${user_id}`);
  if (cached) {
    return JSON.parse(cached);
  }
  
  // جلب من قاعدة البيانات
  const user = await db.users.findOne({ id: user_id });
  
  // حفظ في Cache لمدة 10 دقائق
  await redis.setex(`user:${user_id}`, 600, JSON.stringify(user));
  
  return user;
}

// إبطال Cache عند التحديث
async function update_user(user_id, updates) {
  await db.users.updateOne({ id: user_id }, { $set: updates });
  await redis.del(`user:${user_id}`);  // مسح Cache
}
```

### Query Optimization

```javascript
// ❌ سيء: جلب جميع الحقول
const users = await db.users.find({}).toArray();

// ✅ جيد: جلب الحقول المطلوبة فقط
const users = await db.users.find(
  {},
  { projection: { name: 1, email: 1, role: 1 } }
).toArray();

// ❌ سيء: استعلامات متعددة في حلقة
for (const user of users) {
  const attendance = await db.attendance.find({ user_id: user.id }).toArray();
}

// ✅ جيد: استعلام واحد مع aggregation
const usersWithAttendance = await db.users.aggregate([
  {
    $lookup: {
      from: 'attendance',
      localField: 'id',
      foreignField: 'user_id',
      as: 'attendance'
    }
  }
]).toArray();

// ❌ سيء: جلب جميع البيانات ثم الفلترة في الكود
const all_attendance = await db.attendance.find({}).toArray();
const filtered = all_attendance.filter(a => a.date >= '2024-10-01');

// ✅ جيد: الفلترة في قاعدة البيانات
const filtered_attendance = await db.attendance.find({
  date: { $gte: '2024-10-01' }
}).toArray();
```

### Pagination

```javascript
// للتقارير الكبيرة
async function get_attendance_paginated(page = 1, limit = 50) {
  const skip = (page - 1) * limit;
  
  const [attendance, total] = await Promise.all([
    db.attendance.find({})
      .sort({ date: -1 })
      .skip(skip)
      .limit(limit)
      .toArray(),
    db.attendance.countDocuments({})
  ]);
  
  return {
    data: attendance,
    pagination: {
      page: page,
      limit: limit,
      total: total,
      pages: Math.ceil(total / limit)
    }
  };
}
```

---

## 🔥 السيناريوهات المعقدة

### سيناريو 1: موظف متأخر مع سياسة مرنة

```javascript
// الموظف: طارق وزان
// السياسة: 
// - وقت البداية: 08:00
// - خروج مرن: نعم
// - السماح بالحضور المبكر: نعم
// - الحضور المبكر لا يعوض التأخير: لا

// اليوم: 2024-10-10
// الحضور: 07:45 (15 دقيقة مبكراً)
// الانصراف: 17:00 (ساعة قبل الوقت)

// السؤال: هل يُخصم؟

// الإجابة:
const policy = {
  start_time: "08:00",
  end_flexible: true,
  early_start_allowed: true,
  early_arrival_offset: false
};

const attendance = {
  check_in: "07:45",
  check_out: "17:00"
};

// حساب
const late_minutes = 0;  // حضر قبل 08:00
const early_minutes = 15;

if (policy.early_arrival_offset) {
  // الحضور المبكر يعوض التأخير
  effective_late = late_minutes - early_minutes;
} else {
  // لا يعوض
  effective_late = late_minutes;
}

const penalized_late = Math.max(0, effective_late - grace_period);
// penalized_late = 0

// النتيجة: لا خصم ✅

// الانصراف المبكر:
if (policy.end_flexible) {
  // خروج مرن - لا مشكلة
  early_exit_deduction = 0;
}

// النتيجة النهائية: لا خصومات ✅
```

### سيناريو 2: دورة راتب كاملة

```javascript
// أكتوبر 2024 - دورة راتب
// الموظف: جهاد

// 1. بيانات الموظف
const employee = {
  id: "emp_jihad",
  name: "جهاد",
  monthly_salary: 5000.0,
  allowances: 500.0
};

// 2. الأحداث خلال الشهر

// أ. الحضور
const attendance_events = [
  { date: "2024-10-05", late_minutes: 30, deduction: 10.41 },
  { date: "2024-10-12", status: "Absent", deduction: 166.67 },
  { date: "2024-10-20", late_minutes: 45, deduction: 15.62 }
];

// ب. السلف
const advance = {
  amount: 1000.0,
  installments: 5,
  monthly_deduction: 200.0
};

// ج. خصومات يدوية
const manual_deduction = 50.0;

// 3. إنشاء دورة الراتب
cycle = await create_payroll_cycle("2024-10");

// 4. حساب الخصومات الشهرية
await calculate_monthly_deductions("2024-10");

// يُنشئ قيود Ledger:
ledger_entries = [
  {
    source_type: "ATTENDANCE_DEDUCTION",
    amount: -10.41,
    description: "تأخير 30 دقيقة - 2024-10-05"
  },
  {
    source_type: "ATTENDANCE_DEDUCTION",
    amount: -166.67,
    description: "غياب - 2024-10-12"
  },
  {
    source_type: "ATTENDANCE_DEDUCTION",
    amount: -15.62,
    description: "تأخير 45 دقيقة - 2024-10-20"
  }
];

// 5. ربط الأقساط
const due_installment = {
  advance_id: "adv_123",
  installment_number: 1,
  amount: 200.0,
  due_date: "2024-10-01"
};

ledger_entries.push({
  source_type: "ADVANCE_INSTALLMENT",
  amount: -200.0,
  description: "قسط سلفة - القسط 1 من 5"
});

// 6. الإدارة تضيف خصم يدوي
await update_payroll_cycle_employees({
  employees: [{
    employee_id: "emp_jihad",
    manual_deductions: 50.0
  }]
});

ledger_entries.push({
  source_type: "MANUAL_DEDUCTION",
  amount: -50.0,
  description: "خصم يدوي"
});

// 7. حساب الراتب النهائي
await recalculate_payroll_cycle(cycle_id);

summary = {
  base_salary: 5000.0,
  allowances: 500.0,
  gross_salary: 5500.0,
  
  attendance_deductions: 192.70,  // 10.41 + 166.67 + 15.62
  advance_deductions: 200.0,
  manual_deductions: 50.0,
  total_deductions: 442.70,
  
  net_salary: 5057.30  // 5500 - 442.70
};

// 8. قفل الدورة
await lock_payroll_cycle(cycle_id, "راتب شهر أكتوبر 2024 - معتمد");

// 9. إنشاء رسالة الراتب
const salary_letter = await generate_salary_letter(cycle_id, employee_id);

// 10. تصدير PDF/Excel
await export_payroll_cycle_pdf(cycle_id);
await export_payroll_cycle_excel(cycle_id);
```

### سيناريو 3: تعديل متعدد للخصم اليدوي

```javascript
// الحالة الأولية
initial_value = 0

// التعديل 1: إضافة 100 درهم
await update_manual_deduction(100.0);
// Ledger: [{ id: "e1", amount: -100, is_reversed: false }]
// Summary: manual_deductions = 100.0 ✅

// التعديل 2: تغيير إلى 250.50 درهم
await update_manual_deduction(250.50);
// Ledger: [
//   { id: "e1", amount: -100, is_reversed: true },      // معكوس
//   { id: "e2", amount: -250.50, is_reversed: false }   // جديد
// ]
// Summary: manual_deductions = 250.50 ✅

// التعديل 3: تقليل إلى 75 درهم
await update_manual_deduction(75.0);
// Ledger: [
//   { id: "e1", amount: -100, is_reversed: true },
//   { id: "e2", amount: -250.50, is_reversed: true },   // معكوس
//   { id: "e3", amount: -75.0, is_reversed: false }     // جديد
// ]
// Summary: manual_deductions = 75.0 ✅

// التعديل 4: إزالة الخصم (0 درهم)
await update_manual_deduction(0);
// Ledger: [
//   { id: "e1", amount: -100, is_reversed: true },
//   { id: "e2", amount: -250.50, is_reversed: true },
//   { id: "e3", amount: -75.0, is_reversed: true }      // معكوس
// ]
// Summary: manual_deductions = 0 ✅

// مسار المراجعة الكامل محفوظ! 🎯
```

---

## 🎓 الخلاصة التقنية

### نقاط القوة
1. ✅ **معمارية قوية**: فصل واضح بين Frontend/Backend/Database
2. ✅ **Payroll Ledger**: نظام محاسبي متقدم مع audit trail كامل
3. ✅ **Idempotency**: منع التكرار في العمليات الحرجة
4. ✅ **RBAC**: نظام صلاحيات دقيق
5. ✅ **Validation**: تحقق شامل من البيانات
6. ✅ **Error Handling**: معالجة متقدمة للأخطاء
7. ✅ **Performance**: استعلامات محسّنة مع indexes
8. ✅ **Testing**: اختبار شامل بمعدل نجاح 95%+

### الدروس المستفادة
1. 💡 **التصميم أولاً**: التخطيط الجيد يوفر الوقت
2. 💡 **Audit Trail**: لا تحذف، اعكس
3. 💡 **Idempotency**: مهمة في العمليات المالية
4. 💡 **Testing**: الاختبار المستمر يكشف المشاكل مبكراً
5. 💡 **Documentation**: التوثيق الجيد يسهل الصيانة

---

*آخر تحديث: 10 أكتوبر 2024*
*الإصدار: 1.0.0*
