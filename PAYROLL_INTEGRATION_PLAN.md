# خطة الربط التكاملي للرواتب والخصومات والسلف - TANSEEQ HR

## 1. تحليل الوضع الحالي

### أنظمة موجودة:
- ✅ نظام السلف والعهد (advances_model.py)
- ✅ نظام الخصومات المتقدم (attendance_models.py) 
- ✅ نظام الرواتب الأساسي (server.py: payroll endpoints)
- ✅ نظام الحضور والانصراف

### الفجوات المحددة:
- ❌ لا يوجد ربط تلقائي بين الخصومات والرواتب
- ❌ لا يوجد نظام دورات الرواتب (مفتوحة/مقفولة)
- ❌ لا يوجد جدولة أقساط السلف
- ❌ لا يوجد سقف استقطاع شهري
- ❌ لا تُحدث التقارير لحظياً

## 2. النماذج المطلوب تطويرها

### أ) نموذج دورة الراتب (Payroll Cycle)
```python
class PayrollCycle(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    month: str  # YYYY-MM format
    year: int
    status: PayrollStatus  # OPEN, CLOSED, PROCESSING
    
    # Dates
    start_date: date
    end_date: date  
    cutoff_date: date  # آخر تاريخ للتعديلات
    
    # Financial totals
    total_gross_salary: float = 0.0
    total_deductions: float = 0.0
    total_net_salary: float = 0.0
    
    # Control
    is_locked: bool = False
    locked_by: Optional[str] = None
    locked_at: Optional[datetime] = None
    
    # Audit
    created_by: str
    created_at: datetime = Field(default_factory=datetime.now)
    finalized_by: Optional[str] = None
    finalized_at: Optional[datetime] = None
```

### ب) نموذج الأقساط المجدولة (Installment Schedule)
```python
class InstallmentSchedule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    advance_transaction_id: str
    employee_id: str
    
    # Schedule details
    total_amount: float
    installment_amount: float
    number_of_installments: int
    current_installment: int = 1
    
    # Dates
    start_date: date  # بداية الاستقطاع
    end_date: date    # نهاية الاستقطاع
    
    # Status
    is_active: bool = True
    completed_installments: int = 0
    remaining_balance: float
    
    # Deduction control
    max_monthly_deduction_rate: float = 0.33  # 33% maximum
    respect_deduction_ceiling: bool = True
```

### ج) نموذج العنصر في الراتب (Payroll Line Item)
```python
class PayrollLineItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    payroll_cycle_id: str
    employee_id: str
    
    # Item details
    item_type: PayrollItemType  # SALARY, ALLOWANCE, DEDUCTION, INSTALLMENT
    source_type: str  # attendance, advance, manual, etc.
    source_id: Optional[str] = None
    
    description: str
    amount: float
    currency: str = "AED"
    
    # Categories
    is_taxable: bool = True
    affects_eos: bool = True  # يؤثر على مكافأة نهاية الخدمة
```

## 3. المراحل التطويرية

### المرحلة 1: إنشاء النماذج الأساسية (1-2 أيام)
- [ ] إنشاء نماذج PayrollCycle
- [ ] إنشاء نماذج InstallmentSchedule  
- [ ] إنشاء نماذج PayrollLineItem
- [ ] إنشاء Enums للحالات والأنواع
- [ ] تحديث قاعدة البيانات

### المرحلة 2: نظام دورات الرواتب (2-3 أيام)
- [ ] إنشاء/إدارة دورات الرواتب
- [ ] قفل/فتح الدورات  
- [ ] صلاحيات التعديل بعد القفل
- [ ] Audit trail للتعديلات

### المرحلة 3: ربط الخصومات التلقائي (2-3 أيام)
- [ ] ربط خصومات الحضور بالدورة المفتوحة
- [ ] ترحيل الخصومات للدورة القادمة عند الحاجة
- [ ] إعادة حساب الراتب الصافي فورياً
- [ ] تطبيق سقف الاستقطاع الشهري

### المرحلة 4: نظام الأقساط المجدولة (3-4 أيام)  
- [ ] إنشاء جدولة الأقساط للسلف
- [ ] اقتطاع الأقساط تلقائياً من الراتب
- [ ] إدارة الرصيد المرحّل
- [ ] معالجة حالات عدم كفاية الراتب

### المرحلة 5: التقارير المتكاملة (2-3 أيام)
- [ ] تقرير الرواتب الشهري المحدث
- [ ] كشف الخصومات التفصيلي
- [ ] سجل السلف والأقساط
- [ ] تسوية الرواتب
- [ ] تصدير PDF/Excel

### المرحلة 6: واجهات المستخدم (3-4 أيام)
- [ ] واجهة إدارة دورات الرواتب
- [ ] واجهة عرض كشف الراتب للموظف
- [ ] واجهة السوبر أدمن للتقارير
- [ ] إشعارات real-time للتغييرات

### المرحلة 7: الاختبار الشامل (2-3 أيام)
- [ ] Unit tests للوظائف الحسابية
- [ ] Integration tests للربط
- [ ] End-to-end testing للسيناريوهات
- [ ] Performance testing للتقارير

## 4. معايير القبول التفصيلية

### أ) الوظيفية
1. إنشاء خصم حضور → يظهر فوراً في دورة الراتب المفتوحة
2. إنشاء سلفة مقسطة → القسط الأول يُخصم في الدورة التالية
3. قفل دورة راتب → منع أي تعديلات + رسائل واضحة
4. تجاوز سقف الاستقطاع → تحذير + إيقاف تلقائي
5. تحديث مبلغ خصم → إعادة حساب الصافي فوراً

### ب) التقارير
1. تطابق أرقام الشاشة مع PDF/Excel بنسبة 100%
2. سرعة تحميل التقارير ≤ 3 ثوان
3. تصدير البيانات ≤ 10 ثوان
4. تحديث فوري للأرقام بدون إعادة تحميل

### ج) الأمان والتدقيق
1. جميع التعديلات مسجلة في Audit Log
2. صلاحيات واضحة لكل عملية
3. لا يمكن حذف البيانات من دورة مقفولة
4. رقابة على محاولات التجاوز

## 5. الجدول الزمني

| المرحلة | المدة | البدء | الانتهاء |
|---------|------|-------|----------|
| المرحلة 1 | 2 أيام | يوم 1 | يوم 2 |
| المرحلة 2 | 3 أيام | يوم 3 | يوم 5 |  
| المرحلة 3 | 3 أيام | يوم 6 | يوم 8 |
| المرحلة 4 | 4 أيام | يوم 9 | يوم 12 |
| المرحلة 5 | 3 أيام | يوم 13 | يوم 15 |
| المرحلة 6 | 4 أيام | يوم 16 | يوم 19 |
| المرحلة 7 | 3 أيام | يوم 20 | يوم 22 |

**إجمالي: 22 يوم عمل (حوالي شهر)**

## 6. المتطلبات التقنية

### قاعدة البيانات
- إضافة Collections جديدة: payroll_cycles, installment_schedules, payroll_line_items
- إنشاء Indexes للأداء
- Migration scripts للبيانات الموجودة

### الأداء
- Caching للحسابات المعقدة
- Background jobs للعمليات الثقيلة
- Database optimization للاستعلامات

### التكامل
- Event-driven architecture للتحديثات الفورية
- WebSocket connections للتحديثات المباشرة
- API versioning للتوافق المستقبلي