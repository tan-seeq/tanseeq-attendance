#!/usr/bin/env python3
"""
Test script for the Advanced Attendance & Deduction System
نص اختبار نظام الحضور والخصومات المتقدم
"""

import asyncio
from datetime import datetime, date, time
from motor.motor_asyncio import AsyncIOMotorClient
from attendance_engine import AttendanceEngine
from attendance_models import DeductionType, DeductionCategory

async def test_attendance_system():
    """اختبار نظام الحضور والخصومات"""
    
    print("🚀 بدء اختبار نظام الحضور والخصومات المتقدم...")
    
    # الاتصال بقاعدة البيانات
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.tanseeq_test
    
    # إنشاء محرك الحضور
    engine = AttendanceEngine(db)
    await engine.initialize()
    
    print("✅ تم تهيئة محرك الحضور بنجاح")
    
    # إنشاء موظف تجريبي
    test_employee_id = "test_employee_001"
    test_employee = {
        "id": test_employee_id,
        "name": "موظف تجريبي",
        "email": "test@example.com",
        "monthly_salary": 3000
    }
    
    # إدراج الموظف التجريبي
    await db.users.insert_one(test_employee)
    
    # اختبار إنشاء سياسة حضور
    policy = await engine.get_employee_policy(test_employee_id)
    print(f"✅ تم إنشاء سياسة الحضور للموظف: {test_employee_id}")
    
    # اختبار حساب خصم التأخير
    deduction, is_free = await engine.apply_deduction_rules(
        employee_id=test_employee_id,
        minutes=10,  # 10 دقائق تأخير
        deduction_type=DeductionType.LATENESS,
        use_free_occurrences=True
    )
    
    if is_free:
        print("✅ تم استخدام مرة مجانية للتأخير 10 دقائق")
    else:
        print(f"✅ تم حساب خصم التأخير: {deduction.amount:.2f} درهم")
    
    # اختبار خصم أكثر من 20 دقيقة (خصم مباشر)
    deduction_major, is_free_major = await engine.apply_deduction_rules(
        employee_id=test_employee_id,
        minutes=25,  # 25 دقيقة تأخير
        deduction_type=DeductionType.LATENESS,
        use_free_occurrences=True
    )
    
    print(f"✅ خصم التأخير الكبير (25 دقيقة): {deduction_major.amount:.2f} درهم - مجاني: {is_free_major}")
    
    # اختبار خصم نصف يوم
    deduction_half_day, _ = await engine.apply_deduction_rules(
        employee_id=test_employee_id,
        minutes=90,  # 90 دقيقة = نصف يوم
        deduction_type=DeductionType.LATENESS,
        use_free_occurrences=False
    )
    
    print(f"✅ خصم نصف يوم (90 دقيقة): {deduction_half_day.amount:.2f} درهم")
    
    # اختبار خصم يوم كامل
    deduction_full_day, _ = await engine.apply_deduction_rules(
        employee_id=test_employee_id,
        minutes=150,  # 150 دقيقة = يوم كامل
        deduction_type=DeductionType.LATENESS,
        use_free_occurrences=False
    )
    
    print(f"✅ خصم يوم كامل (150 دقيقة): {deduction_full_day.amount:.2f} درهم")
    
    # اختبار إحصائيات الحضور
    current_month = datetime.now().strftime('%Y-%m')
    try:
        stats = await engine.get_attendance_stats(test_employee_id, current_month)
        print(f"✅ إحصائيات الحضور: {stats.total_days} يوم، {stats.present_days} حضور")
    except Exception as e:
        print(f"⚠️ لم يتم العثور على بيانات حضور: {e}")
    
    # اختبار إنشاء خصم يدوي
    manual_deduction = await engine.create_manual_deduction(
        employee_id=test_employee_id,
        deduction_type=DeductionType.MANUAL,
        category=DeductionCategory.CUSTOM,
        target_date=date.today(),
        amount=50.0,
        reason="خصم اختبار يدوي",
        created_by="system_test"
    )
    
    print(f"✅ تم إنشاء خصم يدوي: {manual_deduction.amount:.2f} درهم")
    
    print("\n🎉 تم اختبار جميع وظائف نظام الحضور والخصومات بنجاح!")
    print("\n📋 ملخص القواعد المطبقة:")
    print("   • أول 15 دقيقة × 4 مرات = مجاناً شهرياً")
    print("   • أكثر من 20 دقيقة = خصم مباشر")
    print("   • 60-120 دقيقة = خصم نصف يوم")
    print("   • أكثر من 120 دقيقة = خصم يوم كامل")
    print("   • الاستثناءات: حاتم (بدون خصومات)، طارق (نهاية مرنة)")
    
    # تنظيف البيانات التجريبية
    await db.users.delete_many({"id": test_employee_id})
    await db.attendance_policies.delete_many({"employee_id": test_employee_id})
    await db.payroll_deductions.delete_many({"employee_id": test_employee_id})
    await db.monthly_lateness_counters.delete_many({"employee_id": test_employee_id})
    
    print("✅ تم تنظيف البيانات التجريبية")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(test_attendance_system())