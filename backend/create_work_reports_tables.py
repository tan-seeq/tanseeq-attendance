#!/usr/bin/env python3
"""
Create Work Reports Tables - معزول تماماً عن النظام الحالي
Daily Work Report + Clients Master Tables
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime
import uuid
from dotenv import load_dotenv

load_dotenv('.env')

async def create_work_reports_tables():
    """إنشاء جداول نظام تقارير العمل اليومي - معزولة تماماً"""
    
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'tanseeq_hr')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("🏗️ إنشاء جداول نظام تقارير العمل اليومي...")
    
    # 1. إنشاء مجموعة العملاء (Clients)
    print("📋 إنشاء مجموعة العملاء...")
    
    # إنشاء فهارس للعملاء
    await db.clients.create_index("name_ar")
    await db.clients.create_index("trn", unique=True, sparse=True)
    await db.clients.create_index("trade_license_no", sparse=True)
    await db.clients.create_index("status")
    
    # 2. إنشاء مجموعة أنواع الأنشطة (Activity Types)
    print("📝 إنشاء مجموعة أنواع الأنشطة...")
    
    await db.activity_types.create_index("code", unique=True)
    await db.activity_types.create_index("name_ar")
    
    # 3. إنشاء مجموعة سجلات العمل (Work Logs)
    print("⏰ إنشاء مجموعة سجلات العمل...")
    
    await db.work_logs.create_index([
        ("user_id", 1),
        ("work_date", -1)
    ])
    await db.work_logs.create_index([
        ("client_id", 1),
        ("work_date", -1)
    ])
    await db.work_logs.create_index("status")
    await db.work_logs.create_index("activity_type_code")
    
    # فهرس مركب لمنع تداخل الأوقات (سيتم التحقق في الكود)
    await db.work_logs.create_index([
        ("user_id", 1),
        ("work_date", 1),
        ("start_at", 1),
        ("end_at", 1)
    ])
    
    # 4. إنشاء مجموعة بيانات اعتماد العملاء (Client Credentials) - مشفرة
    print("🔐 إنشاء مجموعة بيانات اعتماد العملاء المشفرة...")
    
    await db.client_credentials.create_index("client_id", unique=True)
    
    # 5. إضافة أنواع الأنشطة الأساسية (Seed Data)
    print("🌱 إضافة بيانات أنواع الأنشطة الأساسية...")
    
    activity_types = [
        # أنشطة محاسبية
        {"code": "INV_SALES", "name_ar": "فواتير المبيعات", "name_en": "Sales Invoices", "parent_code": None, "is_external_portal": False},
        {"code": "INV_PURCHASE", "name_ar": "فواتير المشتريات", "name_en": "Purchase Invoices", "parent_code": None, "is_external_portal": False},
        {"code": "JV", "name_ar": "قيود اليومية", "name_en": "Journal Vouchers", "parent_code": None, "is_external_portal": False},
        {"code": "RV", "name_ar": "قيود القبض", "name_en": "Receipt Vouchers", "parent_code": None, "is_external_portal": False},
        {"code": "PV", "name_ar": "قيود الدفع", "name_en": "Payment Vouchers", "parent_code": None, "is_external_portal": False},
        {"code": "BANK_RECON", "name_ar": "تسوية بنكية", "name_en": "Bank Reconciliation", "parent_code": None, "is_external_portal": False},
        
        # أنشطة ضريبية
        {"code": "VAT_RETURN", "name_ar": "إقرار ضريبة القيمة المضافة", "name_en": "VAT Return", "parent_code": None, "is_external_portal": True},
        {"code": "CT_RETURN", "name_ar": "إقرار ضريبة الشركات", "name_en": "Corporate Tax Return", "parent_code": None, "is_external_portal": True},
        {"code": "VAT_VD", "name_ar": "اشعار التقدير الضريبي", "name_en": "VAT Voluntary Disclosure", "parent_code": None, "is_external_portal": True},
        
        # تحديثات الهيئة الاتحادية للضرائب
        {"code": "FTA_ID_UPDATE", "name_ar": "تحديث بيانات التعريف", "name_en": "FTA ID Update", "parent_code": None, "is_external_portal": True},
        {"code": "FTA_LICENSE_UPDATE", "name_ar": "تحديث الترخيص", "name_en": "FTA License Update", "parent_code": None, "is_external_portal": True},
        {"code": "FTA_ADDRESS_UPDATE", "name_ar": "تحديث العنوان", "name_en": "FTA Address Update", "parent_code": None, "is_external_portal": True},
        {"code": "FTA_BANK_UPDATE", "name_ar": "تحديث البيانات البنكية", "name_en": "FTA Bank Update", "parent_code": None, "is_external_portal": True},
        
        # أنشطة داخلية
        {"code": "MEETING", "name_ar": "اجتماعات", "name_en": "Meetings", "parent_code": None, "is_external_portal": False},
        {"code": "TRAINING", "name_ar": "تدريب", "name_en": "Training", "parent_code": None, "is_external_portal": False},
        {"code": "FILING", "name_ar": "حفظ وترتيب", "name_en": "Filing", "parent_code": None, "is_external_portal": False},
        {"code": "EMAILS", "name_ar": "مراسلات", "name_en": "Email Communications", "parent_code": None, "is_external_portal": False},
    ]
    
    for activity_type in activity_types:
        activity_type["id"] = str(uuid.uuid4())
        await db.activity_types.update_one(
            {"code": activity_type["code"]},
            {"$set": activity_type},
            upsert=True
        )
    
    print(f"✅ تم إضافة {len(activity_types)} نوع نشاط")
    
    # 6. إنشاء مؤشرات الأداء والإحصائيات
    print("📊 إنشاء مجموعة إحصائيات تقارير العمل...")
    
    await db.work_reports_stats.create_index([
        ("user_id", 1),
        ("report_date", -1)
    ])
    
    # 7. إظهار ملخص الجداول المنشأة
    collections_created = [
        "clients - العملاء",
        "activity_types - أنواع الأنشطة", 
        "work_logs - سجلات العمل",
        "client_credentials - بيانات اعتماد العملاء (مشفرة)",
        "work_reports_stats - إحصائيات التقارير"
    ]
    
    print("\n🎉 تم إنشاء نظام تقارير العمل اليومي بنجاح!")
    print("📋 الجداول المنشأة:")
    for collection in collections_created:
        print(f"  ✅ {collection}")
    
    print("\n🛡️ ضمان العزل: هذه الجداول معزولة تماماً عن نظام HR الحالي")
    print("📈 النظام جاهز لإضافة العملاء وسجلات العمل")
    
    client.close()
    
    return True

if __name__ == "__main__":
    asyncio.run(create_work_reports_tables())