# 📋 TANSEEQ Work Reports - Error Codes & Messages Reference

## 🔐 Authentication Errors (AUTH_001 - AUTH_099)

| Code | Status | English Message | Arabic Message | Action Required |
|------|--------|----------------|----------------|-----------------|
| AUTH_001 | 401 | Invalid email or password | البريد الإلكتروني أو كلمة المرور غير صحيحة | Verify credentials |
| AUTH_002 | 401 | Authentication token expired | انتهت صلاحية رمز المصادقة | Re-login required |
| AUTH_003 | 401 | Authentication token invalid | رمز المصادقة غير صالح | Clear session and re-login |
| AUTH_004 | 403 | Insufficient permissions | صلاحيات غير كافية | Contact administrator |
| AUTH_005 | 403 | Super Admin access required | مطلوب صلاحية المدير العام | Super Admin only |
| AUTH_006 | 403 | Admin access required | مطلوب صلاحية الإدارة | Admin or Super Admin only |
| AUTH_007 | 423 | Account locked due to failed attempts | الحساب مغلق بسبب المحاولات الفاشلة | Contact support |
| AUTH_008 | 400 | Missing authentication header | رأس المصادقة مفقود | Include Bearer token |

## 👥 Client Management Errors (CLIENT_100 - CLIENT_199)

| Code | Status | English Message | Arabic Message | Action Required |
|------|--------|----------------|----------------|-----------------|
| CLIENT_100 | 404 | Client not found | العميل غير موجود | Verify client ID |
| CLIENT_101 | 400 | Company name is required | اسم الشركة مطلوب | Provide company name |
| CLIENT_102 | 409 | Client code already exists | رمز العميل موجود بالفعل | Use different client code |
| CLIENT_103 | 400 | Invalid email format | تنسيق البريد الإلكتروني غير صالح | Provide valid email |
| CLIENT_104 | 400 | Invalid phone number format | تنسيق رقم الهاتف غير صالح | Use valid phone format |
| CLIENT_105 | 403 | Cannot delete client with active work logs | لا يمكن حذف عميل له سجلات عمل نشطة | Archive work logs first |
| CLIENT_106 | 413 | Client data too large | بيانات العميل كبيرة جداً | Reduce data size |
| CLIENT_107 | 422 | Client validation failed | فشل في التحقق من بيانات العميل | Check required fields |

## 🔑 Credential Management Errors (CRED_200 - CRED_299)

| Code | Status | English Message | Arabic Message | Action Required |
|------|--------|----------------|----------------|-----------------|
| CRED_200 | 404 | Credential not found | بيانات الاعتماد غير موجودة | Verify credential ID |
| CRED_201 | 400 | Credential type is required | نوع بيانات الاعتماد مطلوب | Specify credential type |
| CRED_202 | 409 | Duplicate credential for this type | بيانات اعتماد مكررة لهذا النوع | Use existing or update |
| CRED_203 | 400 | Password encryption failed | فشل في تشفير كلمة المرور | Try again or contact support |
| CRED_204 | 500 | Password decryption failed | فشل في فك تشفير كلمة المرور | Contact system administrator |
| CRED_205 | 403 | Re-authentication required for password access | مطلوب إعادة المصادقة للوصول لكلمة المرور | Re-authenticate |
| CRED_206 | 429 | Too many password access attempts | محاولات كثيرة للوصول لكلمة المرور | Wait before trying again |
| CRED_207 | 400 | Invalid credential format | تنسيق بيانات الاعتماد غير صالح | Check data format |

## 📝 Work Log Errors (LOG_300 - LOG_399)

| Code | Status | English Message | Arabic Message | Action Required |
|------|--------|----------------|----------------|-----------------|
| LOG_300 | 404 | Work log not found | سجل العمل غير موجود | Verify log ID |
| LOG_301 | 400 | Description is required | الوصف مطلوب | Provide work description |
| LOG_302 | 400 | Client is required | العميل مطلوب | Select a client |
| LOG_303 | 400 | Activity type is required | نوع النشاط مطلوب | Select activity type |
| LOG_304 | 400 | Date is required | التاريخ مطلوب | Provide valid date |
| LOG_305 | 400 | Invalid time format | تنسيق الوقت غير صالح | Use HH:MM format |
| LOG_306 | 400 | End time must be after start time | وقت الانتهاء يجب أن يكون بعد وقت البداية | Check time values |
| LOG_307 | 409 | Time overlap with existing log | تداخل وقتي مع سجل عمل موجود | Choose different times |
| LOG_308 | 400 | Duration must be positive | المدة يجب أن تكون موجبة | Enter valid duration |
| LOG_309 | 400 | Hourly rate must be positive | المعدل بالساعة يجب أن يكون موجباً | Enter valid rate |
| LOG_310 | 403 | Cannot edit other user's work log | لا يمكن تعديل سجل عمل مستخدم آخر | Contact administrator |
| LOG_311 | 403 | Cannot delete invoiced work log | لا يمكن حذف سجل عمل مفوتر | Contact billing department |

## 🏃‍♂️ Activity Type Errors (ACTIVITY_400 - ACTIVITY_499)

| Code | Status | English Message | Arabic Message | Action Required |
|------|--------|----------------|----------------|-----------------|
| ACTIVITY_400 | 404 | Activity type not found | نوع النشاط غير موجود | Verify activity ID |
| ACTIVITY_401 | 400 | Activity name is required | اسم النشاط مطلوب | Provide activity name |
| ACTIVITY_402 | 409 | Activity name already exists | اسم النشاط موجود بالفعل | Use different name |
| ACTIVITY_403 | 400 | Invalid default rate | المعدل الافتراضي غير صالح | Enter valid rate |
| ACTIVITY_404 | 403 | Cannot delete activity with work logs | لا يمكن حذف نشاط له سجلات عمل | Archive activity instead |
| ACTIVITY_405 | 403 | Admin access required for activity management | مطلوب صلاحية الإدارة لإدارة الأنشطة | Contact administrator |

## 📊 Import/Export Errors (IO_500 - IO_599)

| Code | Status | English Message | Arabic Message | Action Required |
|------|--------|----------------|----------------|-----------------|
| IO_500 | 400 | File format not supported | تنسيق الملف غير مدعوم | Use Excel (.xlsx) format |
| IO_501 | 400 | File is empty or corrupted | الملف فارغ أو تالف | Upload valid Excel file |
| IO_502 | 413 | File size too large | حجم الملف كبير جداً | Use smaller file (<10MB) |
| IO_503 | 400 | Missing required columns | أعمدة مطلوبة مفقودة | Check Excel template |
| IO_504 | 422 | Data validation failed during import | فشل في التحقق من البيانات أثناء الاستيراد | Fix data and retry |
| IO_505 | 500 | Import process failed | فشل في عملية الاستيراد | Contact support with file |
| IO_506 | 429 | Too many import requests | طلبات استيراد كثيرة | Wait before trying again |
| IO_507 | 200 | Partial import completed with errors | اكتملت عملية الاستيراد الجزئي مع أخطاء | Review error report |

## 💾 Database Errors (DB_600 - DB_699)

| Code | Status | English Message | Arabic Message | Action Required |
|------|--------|----------------|----------------|-----------------|
| DB_600 | 500 | Database connection failed | فشل الاتصال بقاعدة البيانات | Contact system administrator |
| DB_601 | 500 | Database query timeout | انتهت مهلة استعلام قاعدة البيانات | Try again or contact support |
| DB_602 | 500 | Database constraint violation | انتهاك قيود قاعدة البيانات | Check data integrity |
| DB_603 | 500 | Transaction rollback required | مطلوب التراجع عن المعاملة | Operation cancelled |
| DB_604 | 507 | Database storage full | مساحة تخزين قاعدة البيانات ممتلئة | Contact system administrator |
| DB_605 | 503 | Database maintenance in progress | صيانة قاعدة البيانات جارية | Try again later |

## 🌐 API & System Errors (SYS_700 - SYS_799)

| Code | Status | English Message | Arabic Message | Action Required |
|------|--------|----------------|----------------|-----------------|
| SYS_700 | 500 | Internal server error | خطأ داخلي في الخادم | Contact support |
| SYS_701 | 503 | Service temporarily unavailable | الخدمة غير متاحة مؤقتاً | Try again later |
| SYS_702 | 429 | Rate limit exceeded | تم تجاوز حد المعدل | Wait before making more requests |
| SYS_703 | 400 | Invalid JSON format | تنسيق JSON غير صالح | Check request format |
| SYS_704 | 415 | Unsupported media type | نوع الوسائط غير مدعوم | Use application/json |
| SYS_705 | 413 | Request payload too large | حمولة الطلب كبيرة جداً | Reduce request size |
| SYS_706 | 408 | Request timeout | انتهت مهلة الطلب | Try again |
| SYS_707 | 502 | Bad gateway | بوابة سيئة | Network connectivity issue |

---

## 🔧 Frontend Error Handling

### Success Messages
```javascript
const successMessages = {
  CLIENT_CREATED: {
    en: "Client created successfully",
    ar: "تم إنشاء العميل بنجاح"
  },
  LOG_CREATED: {
    en: "Work log created successfully", 
    ar: "تم إنشاء سجل العمل بنجاح"
  },
  IMPORT_COMPLETED: {
    en: "Import completed successfully",
    ar: "تم الاستيراد بنجاح"
  }
};
```

### Error Display Component
```jsx
const ErrorMessage = ({ error }) => {
  const isArabic = document.dir === 'rtl';
  
  return (
    <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
      <strong>خطأ - Error:</strong>
      <p>{isArabic ? error.messageAr : error.messageEn}</p>
      {error.code && <small>Code: {error.code}</small>}
    </div>
  );
};
```

### Loading States
```javascript
const loadingMessages = {
  LOADING_CLIENTS: {
    en: "Loading clients...",
    ar: "جاري تحميل العملاء..."
  },
  SAVING_LOG: {
    en: "Saving work log...",
    ar: "جاري حفظ سجل العمل..."
  },
  IMPORTING_DATA: {
    en: "Importing data...",
    ar: "جاري استيراد البيانات..."
  }
};
```

---

## 🎯 Error Resolution Guide

### Common Issues & Solutions

#### Authentication Problems
1. **Token Expired** → Redirect to login
2. **Invalid Credentials** → Show error, clear form
3. **Insufficient Permissions** → Show access denied message

#### Data Validation Issues
1. **Required Fields** → Highlight missing fields
2. **Format Errors** → Show format examples
3. **Duplicate Data** → Suggest alternatives

#### Network Issues
1. **Connection Timeout** → Retry with exponential backoff
2. **Rate Limiting** → Show retry countdown
3. **Server Errors** → Show "try again later" message

### Error Reporting
All errors with codes SYS_700+ should be automatically reported to the system administrators with:
- User ID and session information
- Request details (sanitized)
- Timestamp and error context
- Client IP and user agent

---

*Last Updated: August 27, 2025*
*Error Codes Version: 1.0.0*