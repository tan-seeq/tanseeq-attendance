# ✨ إضافة ميزة "نوع الإجازة" في جدول الحضور

## التاريخ: 2025-10-12
## الحالة: ✅ تم التنفيذ

---

## 🎯 المطلوب

إضافة عمود **"نوع الإجازة"** في جدول إدارة الحضور لتوضيح نوع الإجازة لكل موظف غائب.

### أمثلة:
- جهاد → 🏖️ إجازة سنوية
- حاتم → 🤒 إجازة مرضية  
- محمد → 👤 إجازة شخصية

---

## ✅ التنفيذ

### 1. Frontend - عمود جديد في الجدول

#### أ. إضافة عمود في Header:
```jsx
<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
  نوع الإجازة
</th>
```

#### ب. إضافة خلية البيانات:
```jsx
<td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
  {editingRecord === record.id && editData.status === 'absent' ? (
    // وضع التعديل: Dropdown لاختيار نوع الإجازة
    <select
      value={editData.leave_type || ''}
      onChange={(e) => setEditData({...editData, leave_type: e.target.value})}
      className="w-full px-2 py-1 border border-gray-300 rounded"
    >
      <option value="">-- اختر نوع الإجازة --</option>
      <option value="annual">إجازة سنوية</option>
      <option value="sick">إجازة مرضية</option>
      <option value="personal">إجازة شخصية</option>
      <option value="emergency">إجازة طارئة</option>
      <option value="unpaid">إجازة بدون راتب</option>
      <option value="maternity">إجازة أمومة</option>
      <option value="study">إجازة دراسية</option>
      <option value="other">أخرى</option>
    </select>
  ) : (
    // وضع العرض: Badge ملون حسب نوع الإجازة
    <span className={`px-2 py-1 text-xs font-medium rounded-full ${...}`}>
      {record.leave_type === 'annual' ? '🏖️ إجازة سنوية' :
       record.leave_type === 'sick' ? '🤒 إجازة مرضية' :
       record.leave_type === 'personal' ? '👤 إجازة شخصية' :
       ...}
    </span>
  )}
</td>
```

---

### 2. Frontend - تحديث Modal إنشاء الغياب

تم إضافة حقل "نوع الإجازة" في modal إنشاء سجل الغياب:

```jsx
<div>
  <label className="block text-sm font-medium text-gray-700">نوع الإجازة</label>
  <select
    value={absenceData.leave_type || ''}
    onChange={(e) => setAbsenceData({...absenceData, leave_type: e.target.value})}
    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
  >
    <option value="">-- اختر نوع الإجازة --</option>
    <option value="annual">🏖️ إجازة سنوية</option>
    <option value="sick">🤒 إجازة مرضية</option>
    <option value="personal">👤 إجازة شخصية</option>
    <option value="emergency">🚨 إجازة طارئة</option>
    <option value="unpaid">💰 إجازة بدون راتب</option>
    <option value="maternity">👶 إجازة أمومة</option>
    <option value="study">📚 إجازة دراسية</option>
    <option value="other">📋 أخرى</option>
  </select>
</div>
```

---

### 3. Frontend - تحديث الـ State و Handlers

#### تحديث `handleEdit`:
```jsx
setEditData({
  check_in: record.check_in || '',
  check_out: record.check_out || '',
  status: backendStatus,
  reason: record.absence_reason || '',
  leave_type: record.leave_type || ''  // ✅ إضافة leave_type
});
```

#### تحديث `handleSave`:
```jsx
const updateData = {
  check_in: editData.check_in || null,
  check_out: editData.check_out || null,
  status: editData.status,
  reason: editData.reason || null,
  leave_type: editData.leave_type || null  // ✅ إرسال leave_type
};
```

---

### 4. Backend - حفظ نوع الإجازة

#### أ. في `/api/attendance/{attendance_id}` (تحديث سجل):
```python
# عند تغيير الحالة إلى absent
elif new_status == "absent":
    reason = update_data.get("reason", "غياب")
    update_fields["absence_reason"] = reason
    update_fields["check_in"] = None
    update_fields["check_out"] = None
    update_fields["working_hours"] = 0
    changes.append(f"set absence reason: {reason}")
    
    # ✅ Set leave type if provided
    leave_type = update_data.get("leave_type")
    if leave_type:
        update_fields["leave_type"] = leave_type
        changes.append(f"set leave type: {leave_type}")
```

#### ب. في `/api/attendance/create-absence` (إنشاء سجل غياب):
```python
# ✅ Get leave type if provided
leave_type = attendance_data.get("leave_type")

# Create absence record
absence_record = {
    "id": str(uuid.uuid4()),
    "user_id": user_id,
    "user_name": user.get("name", ""),
    "date": date,
    "check_in": None,
    "check_out": None,
    "working_hours": 0,
    "status": "absent",
    "is_late": False,
    "absence_reason": reason,
    "leave_type": leave_type,  # ✅ Add leave type
    "created_by": current_user.id,
    "created_by_name": current_user.name,
    "is_manual_entry": True,
    "created_at": datetime.utcnow()
}
```

---

## 🎨 أنواع الإجازات المدعومة

| القيمة | الاسم بالعربية | الـ Emoji | اللون |
|-------|----------------|-----------|-------|
| `annual` | إجازة سنوية | 🏖️ | أزرق |
| `sick` | إجازة مرضية | 🤒 | أحمر |
| `personal` | إجازة شخصية | 👤 | بنفسجي |
| `emergency` | إجازة طارئة | 🚨 | برتقالي |
| `unpaid` | إجازة بدون راتب | 💰 | رمادي |
| `maternity` | إجازة أمومة | 👶 | وردي (indigo) |
| `study` | إجازة دراسية | 📚 | نيلي (indigo) |
| `other` | أخرى | 📋 | نيلي (indigo) |

---

## 🖼️ مثال على العرض

### في الجدول:

| الموظف | التاريخ | الحالة | سبب الغياب | نوع الإجازة |
|--------|---------|--------|-----------|-------------|
| جهاد | 2025-10-12 | 🔴 غائب | إجازة اعتيادية | 🏖️ إجازة سنوية |
| حاتم | 2025-10-12 | 🔴 غائب | مريض | 🤒 إجازة مرضية |
| محمد | 2025-10-12 | 🔴 غائب | ظروف عائلية | 👤 إجازة شخصية |
| أحمد | 2025-10-12 | 🟢 حاضر | -- | -- |

---

## 📊 تدفق البيانات

### 1. إنشاء سجل غياب جديد:
```
Admin → يفتح Modal "إنشاء سجل غياب"
     → يختار الموظف + التاريخ + سبب الغياب + نوع الإجازة
     → يضغط "إنشاء"
     → Frontend يرسل POST /api/attendance/create-absence
     → Backend يحفظ في MongoDB (attendance collection)
     → الجدول يُحدّث تلقائياً
     → يظهر نوع الإجازة في العمود الجديد ✅
```

### 2. تعديل سجل موجود:
```
Admin → يضغط "تعديل" على سجل
     → يغير الحالة إلى "غائب"
     → يختار نوع الإجازة من Dropdown
     → يضغط "حفظ"
     → Frontend يرسل PUT /api/attendance/{id}
     → Backend يُحدّث leave_type في MongoDB
     → الجدول يُحدّث ويظهر نوع الإجازة ✅
```

---

## 🧪 كيفية الاختبار

### اختبار 1: إنشاء سجل غياب مع نوع إجازة

1. **تسجيل الدخول كـ Super Admin**
2. **اذهب لصفحة "إدارة الحضور"**
3. **اضغط "إنشاء سجل غياب"**
4. **املأ البيانات:**
   - ID الموظف: `employee-001`
   - التاريخ: `2025-10-12`
   - سبب الغياب: `إجازة سنوية مستحقة`
   - نوع الإجازة: `إجازة سنوية` 🏖️
5. **اضغط "إنشاء سجل غياب"**
6. **✅ يجب أن يظهر السجل في الجدول مع نوع الإجازة**

---

### اختبار 2: تعديل سجل موجود

1. **في جدول الحضور، اضغط "تعديل" على أي سجل**
2. **غيّر الحالة إلى "غائب"**
3. **اختر نوع الإجازة من القائمة المنسدلة**
4. **اضغط "حفظ" ✅**
5. **✅ يجب أن يُحفظ نوع الإجازة ويظهر في الجدول**

---

### اختبار 3: التحقق من الألوان والـ Badges

تأكد من أن كل نوع إجازة يظهر بالـ Badge واللون الصحيح:

- 🏖️ إجازة سنوية → خلفية زرقاء فاتحة
- 🤒 إجازة مرضية → خلفية حمراء فاتحة
- 👤 إجازة شخصية → خلفية بنفسجية فاتحة
- 🚨 إجازة طارئة → خلفية برتقالية فاتحة
- 💰 إجازة بدون راتب → خلفية رمادية

---

## 📋 البيانات في MongoDB

### بنية السجل في `attendance` collection:

```json
{
  "id": "attendance-uuid",
  "user_id": "employee-001",
  "user_name": "جهاد محمد",
  "date": "2025-10-12",
  "status": "absent",
  "absence_reason": "إجازة سنوية مستحقة",
  "leave_type": "annual",  // ✅ حقل جديد
  "check_in": null,
  "check_out": null,
  "working_hours": 0,
  "is_manual_entry": true,
  "created_by": "admin_001",
  "created_by_name": "Admin User",
  "created_at": "2025-10-12T08:00:00Z"
}
```

---

## 🎁 فوائد الميزة

### 1. وضوح أكبر:
- معرفة نوع الإجازة مباشرة من الجدول
- لا حاجة لفتح تفاصيل السجل

### 2. تحليل أفضل:
- إمكانية فلترة حسب نوع الإجازة
- إحصائيات دقيقة (كم إجازة مرضية، كم إجازة سنوية)

### 3. إدارة محسّنة:
- تتبع استخدام الإجازات السنوية
- مراقبة الإجازات المرضية المتكررة
- التخطيط بناءً على أنواع الإجازات

### 4. واجهة جميلة:
- Badges ملونة حسب النوع
- Emoji لسهولة التعرف البصري
- تصميم احترافي

---

## 🚀 التحسينات المستقبلية

### 1. فلترة حسب نوع الإجازة:
```jsx
<select onChange={e => filterByLeaveType(e.target.value)}>
  <option value="">جميع الأنواع</option>
  <option value="annual">إجازة سنوية</option>
  <option value="sick">إجازة مرضية</option>
  ...
</select>
```

### 2. إحصائيات نوع الإجازة:
```jsx
<div className="stats">
  <div>إجازات سنوية: {annualCount}</div>
  <div>إجازات مرضية: {sickCount}</div>
  <div>إجازات شخصية: {personalCount}</div>
</div>
```

### 3. تقارير حسب نوع الإجازة:
- تقرير شهري بأنواع الإجازات
- تقرير موظف واحد (استخدامه للإجازات)
- مقارنة بين الموظفين

### 4. رصيد الإجازات:
- ربط مع نظام الإجازات
- خصم من رصيد الإجازات السنوية تلقائياً
- تنبيه عند نفاد الرصيد

---

## ✅ Checklist

- [x] إضافة عمود في Frontend
- [x] إضافة Dropdown في وضع التعديل
- [x] إضافة حقل في modal إنشاء الغياب
- [x] تحديث `handleEdit` لإضافة `leave_type`
- [x] تحديث `handleSave` لإرسال `leave_type`
- [x] تحديث Backend endpoint `PUT /attendance/{id}`
- [x] تحديث Backend endpoint `POST /attendance/create-absence`
- [x] إضافة Badges ملونة حسب النوع
- [x] إضافة Emoji لكل نوع
- [x] اختبار التنفيذ

---

## 📞 في حالة وجود مشاكل

إذا لم يظهر نوع الإجازة:

1. **تحقق من Developer Console (F12)**
   - هل يتم إرسال `leave_type` في request؟
   - هل يعود `leave_type` في response؟

2. **تحقق من قاعدة البيانات:**
   ```bash
   db.attendance.findOne({"status": "absent"})
   # يجب أن ترى حقل "leave_type"
   ```

3. **تحقق من Backend logs:**
   ```bash
   tail -f /var/log/supervisor/backend.err.log
   ```

---

**المطور:** AI Engineer  
**التاريخ:** 2025-10-12  
**الملفات المُعدّلة:**
- `/app/frontend/src/App.js` (AttendanceManagement component)
- `/app/backend/server.py` (endpoints: PUT /attendance/{id}, POST /attendance/create-absence)
**الحالة:** ✅ تم التنفيذ والاختبار  
**الأولوية:** ⭐ ميزة جديدة (مُكتمل)
