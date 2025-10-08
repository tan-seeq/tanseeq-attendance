#!/usr/bin/env python3
"""
Script لترحيل البيانات الموجودة إلى نظام Payroll Ledger
يولد قيود محاسبية من الخصومات والسلف الموجودة
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import sys

# إضافة مسار backend للـ imports
sys.path.insert(0, '/app/backend')

from payroll_ledger_service import (
    trigger_manual_deduction,
    trigger_advance_installment,
    trigger_attendance_deduction
)

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_URL)
db = client.tanseeq_hr

async def migrate_existing_data():
    """ترحيل البيانات الموجودة إلى Payroll Ledger"""
    
    print("=" * 60)
    print("🔄 ترحيل البيانات إلى Payroll Ledger")
    print("=" * 60)
    
    # 1. ترحيل الخصومات اليدوية الموجودة
    print("\n📝 ترحيل الخصومات اليدوية...")
    deductions = await db.payroll_deductions.find({}).to_list(None)
    
    migrated_deductions = 0
    for ded in deductions:
        try:
            # البحث عن دورة الراتب المناسبة
            date_str = ded.get("date", "")
            if len(date_str) >= 7:  # YYYY-MM-DD
                month = date_str[:7]  # YYYY-MM
                
                cycle = await db.payroll_cycles.find_one({"month": month})
                if cycle:
                    await trigger_manual_deduction(
                        db=db,
                        employee_id=ded["employee_id"],
                        cycle_id=cycle["id"],
                        deduction_id=ded["id"],
                        amount=ded["amount"],
                        reason=ded.get("reason", "خصم يدوي"),
                        created_by=ded.get("created_by", "system")
                    )
                    migrated_deductions += 1
                    print(f"  ✅ {ded.get('employee_name', 'موظف')}: {ded['amount']} درهم")
        except Exception as e:
            print(f"  ⚠️ فشل ترحيل خصم {ded.get('id')}: {str(e)}")
    
    print(f"\n✅ تم ترحيل {migrated_deductions} خصم يدوي")
    
    # 2. ترحيل جدولات السلف النشطة
    print("\n💰 ترحيل جدولات السلف...")
    installment_schedules = await db.installment_schedules.find({
        "is_active": True,
        "is_completed": False
    }).to_list(None)
    
    migrated_installments = 0
    for schedule in installment_schedules:
        try:
            # إنشاء قيد لكل دورة مفتوحة
            open_cycles = await db.payroll_cycles.find({"is_locked": False}).to_list(None)
            
            for cycle in open_cycles:
                await trigger_advance_installment(
                    db=db,
                    employee_id=schedule["employee_id"],
                    cycle_id=cycle["id"],
                    advance_id=schedule["id"],
                    installment_amount=schedule.get("installment_amount", 0),
                    created_by="system"
                )
                migrated_installments += 1
                print(f"  ✅ {schedule.get('employee_name', 'موظف')}: {schedule.get('installment_amount', 0)} درهم")
        except Exception as e:
            print(f"  ⚠️ فشل ترحيل جدولة {schedule.get('id')}: {str(e)}")
    
    print(f"\n✅ تم ترحيل {migrated_installments} قسط")
    
    # 3. ترحيل خصومات التأخير (من سجلات الحضور)
    print("\n⏰ ترحيل خصومات التأخير...")
    attendance_records = await db.attendance.find({
        "status": "late",
        "late_minutes": {"$gt": 15}  # أكثر من 15 دقيقة
    }).to_list(None)
    
    migrated_late_deductions = 0
    for record in attendance_records:
        try:
            date_str = record.get("date", "")
            if len(date_str) >= 7:
                month = date_str[:7]
                
                cycle = await db.payroll_cycles.find_one({"month": month})
                if cycle:
                    late_minutes = record.get("late_minutes", 0)
                    deduction_amount = 10 + ((late_minutes - 15) * 1.0)  # خصم ثابت + متغير
                    
                    await trigger_attendance_deduction(
                        db=db,
                        employee_id=record["employee_id"],
                        cycle_id=cycle["id"],
                        attendance_record_id=record.get("id", record.get("_id")),
                        late_minutes=late_minutes,
                        deduction_amount=deduction_amount,
                        created_by="system"
                    )
                    migrated_late_deductions += 1
                    print(f"  ✅ {record.get('employee_name', 'موظف')}: {late_minutes} دقيقة → {deduction_amount:.2f} درهم")
        except Exception as e:
            print(f"  ⚠️ فشل ترحيل تأخير: {str(e)}")
    
    print(f"\n✅ تم ترحيل {migrated_late_deductions} خصم تأخير")
    
    # 4. إعادة حساب جميع الدورات المفتوحة
    print("\n🔄 إعادة حساب الدورات المفتوحة...")
    from payroll_ledger_service import PayrollLedgerService
    
    ledger_service = PayrollLedgerService(db)
    open_cycles = await db.payroll_cycles.find({"is_locked": False}).to_list(None)
    
    for cycle in open_cycles:
        cycle_id = cycle["id"]
        print(f"\n  📅 دورة {cycle.get('display_name', cycle_id[:8])}")
        
        employees = await db.users.find({"role": "user", "is_active": True}).to_list(None)
        
        for emp in employees:
            try:
                calculation = await ledger_service.recalculate_employee_payroll(
                    cycle_id=cycle_id,
                    employee_id=emp["id"],
                    base_salary=emp.get("monthly_salary", 0),
                    allowances=0
                )
                
                await db.employee_payroll_summaries.update_one(
                    {"payroll_cycle_id": cycle_id, "employee_id": emp["id"]},
                    {"$set": {
                        "base_salary": calculation["base_salary"],
                        "total_allowances": calculation["allowances"],
                        "gross_salary": calculation["gross_salary"],
                        "attendance_deductions": calculation["attendance_deductions"],
                        "manual_deductions": calculation["manual_deductions"],
                        "advance_deductions": calculation["advance_installments"],
                        "total_deductions": calculation["total_deductions"],
                        "net_salary": calculation["net_salary"],
                        "ledger_entries_count": calculation["ledger_entries_count"]
                    }},
                    upsert=True
                )
                
                print(f"    ✅ {emp.get('name', 'موظف')}: صافي {calculation['net_salary']:.2f} درهم ({calculation['ledger_entries_count']} قيد)")
            except Exception as e:
                print(f"    ⚠️ فشل حساب {emp.get('name')}: {str(e)}")
    
    print("\n" + "=" * 60)
    print("✅ اكتمل الترحيل بنجاح!")
    print("=" * 60)
    print(f"\nالإحصائيات:")
    print(f"  - خصومات يدوية: {migrated_deductions}")
    print(f"  - أقساط سلف: {migrated_installments}")
    print(f"  - خصومات تأخير: {migrated_late_deductions}")

if __name__ == "__main__":
    asyncio.run(migrate_existing_data())
