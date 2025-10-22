# 🔄 إرشادات مسح Cache المتصفح - تحديث نظام الخصومات

## ⚠️ المشكلة:
بعد إعادة النشر، المتصفح يحتفظ بالكود القديم في الـ Cache، لذلك التحديثات لا تظهر مباشرة.

---

## ✅ الحلول (اختر أحدها):

### **الحل 1: Hard Reload (الأسرع)** ⚡
اضغط على أحد المفاتيح التالية حسب نظامك:

**Windows / Linux:**
```
Ctrl + F5
```
أو
```
Ctrl + Shift + R
```

**Mac:**
```
Command + Shift + R
```

---

### **الحل 2: مسح Cache الكامل** 🗑️

#### **Google Chrome:**
1. اضغط `Ctrl + Shift + Delete` (Windows/Linux) أو `Command + Shift + Delete` (Mac)
2. اختر Time range: **"All time"**
3. اختار فقط:
   - ✅ **Cached images and files**
   - ❌ (اترك الباقي غير محدد)
4. اضغط **"Clear data"**
5. أعد تحميل الصفحة `F5`

#### **Firefox:**
1. اضغط `Ctrl + Shift + Delete`
2. Time range: **"Everything"**
3. اختر:
   - ✅ **Cache**
4. اضغط **"Clear Now"**
5. أعد تحميل الصفحة

#### **Safari (Mac):**
1. Safari Menu → **Preferences**
2. **Advanced** tab
3. فعّل **"Show Develop menu"**
4. من قائمة Develop → اختر **"Empty Caches"**
5. أعد تحميل الصفحة

---

### **الحل 3: Incognito/Private Mode** 🕵️
افتح الموقع في نافذة خاصة:

**Chrome/Edge:**
```
Ctrl + Shift + N
```

**Firefox:**
```
Ctrl + Shift + P
```

**Safari:**
```
Command + Shift + N
```

ثم افتح: `https://hrapp-tanseeq.emergent.host`

---

### **الحل 4: Disable Cache في Developer Tools** 👨‍💻

1. افتح Developer Tools: اضغط `F12`
2. اذهب إلى **Network** tab
3. فعّل ✅ **"Disable cache"**
4. أبقِ Developer Tools مفتوح أثناء التصفح
5. أعد تحميل الصفحة

---

## 🎯 كيف تتأكد أن الـ Cache تم مسحه؟

بعد تطبيق أحد الحلول:

1. **اذهب إلى صفحة الخصومات المتقدمة**
2. **اختر Custom Period**: من 2025-10-01 إلى 2025-10-15
3. **اضغط Calculate Deductions**
4. **اضغط View Details** لأحد الموظفين
5. **تأكد من وجود Daily Breakdown Table مع البيانات**

### ✅ **إذا رأيت:**
```
Daily Breakdown Table
Date | Status | Deduction | Deficit | ...
2025-10-01 | Deducted | 93.94 | 124 | ...
2025-10-02 | Deducted | 91.67 | 121 | ...
...
```
**✅ Cache تم مسحه بنجاح!**

### ❌ **إذا رأيت:**
```
No daily records available. Please try Monthly Calculation mode for detailed breakdown.
```
**❌ Cache مازال موجود - جرب حل آخر من الأعلى**

---

## 🔍 لماذا تحدث هذه المشكلة؟

عندما يتم تحديث الـ Frontend:
1. الكود الجديد موجود في السيرفر ✅
2. المتصفح يحتفظ بنسخة قديمة في Memory/Disk ❌
3. لا يطلب النسخة الجديدة إلا بعد مسح الـ Cache ✅

---

## 📱 للهواتف المحمولة:

### **Android Chrome:**
1. Settings → Privacy → Clear browsing data
2. Advanced → Cached images and files
3. Clear data

### **iOS Safari:**
1. Settings → Safari
2. Clear History and Website Data
3. Confirm

---

## 🆘 إذا استمرت المشكلة:

إذا جربت جميع الحلول أعلاه والمشكلة مازالت موجودة:

1. تأكد من إعادة النشر تمت بنجاح
2. تأكد من أن URL صحيح: `https://hrapp-tanseeq.emergent.host`
3. جرب متصفح آخر تماماً (مثلاً: Chrome → Firefox)
4. تواصل مع الدعم الفني

---

## ✅ بعد مسح الـ Cache:

### **ستعمل الميزات التالية:**

1. ✅ **Monthly Calculation** - زر حساب الخصومات في Dashboard
   - لن يظهر خطأ 400
   - سيعيد بيانات صحيحة للموظفين

2. ✅ **Custom Period** - التفاصيل اليومية
   - Daily Breakdown سيظهر بالبيانات الكاملة
   - لن تظهر رسالة "No daily records available"

3. ✅ **Apply Deductions** - تطبيق الخصومات
   - سيعمل بشكل صحيح
   - سيرسل البيانات بصيغة JSON

---

**تم إعداد هذا الدليل بواسطة:** فريق تطوير TANSEEQ HR  
**التاريخ:** 2025-10-22  
**الإصدار:** v1.0
