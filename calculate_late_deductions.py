#!/usr/bin/env python3
"""
Script لحساب خصومات التأخير تلقائياً من سجلات الحضور
يحسب خصومات بناءً على سياسة التأخير ويربطها بدورات الرواتب
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, date, time
import os

# MongoDB connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_URL)
db = client.tanseeq_hr

async def calculate_late_deductions():
    """حساب خصومات التأخير من سجلات الحضور"""
    
    print("=" * 60)
    print("🕐 حساب خصومات التأخير")
    print("=" * 60)
    
    # جلب سياسة الحضور الافتراضية
    default_policy = await db.attendance_policies.find_one({"is_default": True})
    if not default_policy:
        print("⚠️ لا توجد سياسة حضور افتراضية")
        return
    
    # إعدادات سياسة التأخير
    grace_period = default_policy.get("late_grace_period_minutes", 15)  # فترة سماح 15 دقيقة
    late_deduction_per_minute = default_policy.get("late_deduction_per_minute", 0.0)  # خصم لكل دقيقة
    late_deduction_flat = default_policy.get("late_deduction_flat", 10.0)  # خصم ثابت للتأخير
    
    print(f"\nسياسة التأخير:")
    print(f"  - فترة السماح: {grace_period} دقيقة")
    print(f"  - خصم لكل دقيقة: {late_deduction_per_minute} درهم")
    print(f"  - خصم ثابت: {late_deduction_flat} درهم")
    
    # جلب جميع دورات الرواتب المفتوحة
    open_cycles = await db.payroll_cycles.find({"is_locked": False}).to_list(None)
    
    print(f"\n📅 دورات الرواتب المفتوحة: {len(open_cycles)}")
    
    for cycle in open_cycles:
        cycle_id = cycle["id"]
        month = cycle["month"]  # مثلاً: "2025-10"
        print(f"\n🔄 معالجة دورة: {cycle.get('display_name', month)}")
        
        # جلب جميع سجلات الحضور لهذا الشهر
        attendance_records = await db.attendance.find({
            "date": {"$regex": f"^{month}"},
            "status": "late"
        }).to_list(None)
        
        print(f"  📊 سجلات التأخير: {len(attendance_records)}")
        
        if len(attendance_records) == 0:
            print("  ℹ️ لا توجد سجلات تأخير لهذا الشهر")
            continue
        
        # حساب خصومات التأخير لكل موظف
        employee_late_count = {}
        
        for record in attendance_records:
            employee_id = record.get("employee_id")
            employee_name = record.get("employee_name")
            late_minutes = record.get("late_minutes", 0)
            date_str = record.get("date")
            
            if not employee_id:
                continue
            
            # حساب الخصم
            if late_minutes > grace_period:
                actual_late = late_minutes - grace_period
                deduction_amount = late_deduction_flat + (actual_late * late_deduction_per_minute)
                
                # تسجيل الخصم
                if employee_id not in employee_late_count:
                    employee_late_count[employee_id] = {
                        "name": employee_name,
                        "count": 0,
                        "total_minutes": 0,
                        "total_deduction": 0
                    }
                
                employee_late_count[employee_id]["count"] += 1
                employee_late_count[employee_id]["total_minutes"] += late_minutes
                employee_late_count[employee_id]["total_deduction"] += deduction_amount
                
                print(f"    ⏰ {employee_name}: {late_minutes} دقيقة → خصم {deduction_amount:.2f} درهم")
        
        # تحديث employee summaries بخصومات التأخير
        for employee_id, data in employee_late_count.items():
            total_deduction = data["total_deduction"]
            
            # تحديث attendance_deductions في employee summary
            summary = await db.employee_payroll_summaries.find_one({
                "payroll_cycle_id": cycle_id,
                "employee_id": employee_id
            })
            
            if summary:
                # تحديث الخصومات
                new_attendance_ded = summary.get("attendance_deductions", 0) + total_deduction
                
                update_data = {
                    "attendance_deductions": new_attendance_ded,
                    "total_deductions": summary.get("manual_deductions", 0) + new_attendance_ded + summary.get("advance_deductions", 0),
                    "updated_at": datetime.now().isoformat()
                }
                
                update_data["net_salary"] = summary.get("gross_salary", 0) - update_data["total_deductions"]
                
                await db.employee_payroll_summaries.update_one(
                    {
                        "payroll_cycle_id": cycle_id,
                        "employee_id": employee_id
                    },
                    {"$set": update_data}
                )
                
                print(f"    ✅ تم تحديث {data['name']}: {data['count']} تأخيرات، إجمالي الخصم {total_deduction:.2f} درهم")
        
        # إعادة حساب إجماليات الدورة
        all_summaries = await db.employee_payroll_summaries.find({"payroll_cycle_id": cycle_id}).to_list(None)
        
        cycle_totals = {
            "total_deductions": sum(s.get("total_deductions", 0) for s in all_summaries),
            "total_net_salary": sum(s.get("net_salary", 0) for s in all_summaries)
        }
        
        await db.payroll_cycles.update_one(
            {"id": cycle_id},
            {"$set": cycle_totals}
        )
        
        print(f"  ✅ تم تحديث إجماليات الدورة")
        print(f"     إجمالي الخصومات: {cycle_totals['total_deductions']:.2f} درهم")
        print(f"     الصافي: {cycle_totals['total_net_salary']:.2f} درهم")
    
    print("\n" + "=" * 60)
    print("✅ تم حساب خصومات التأخير بنجاح!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(calculate_late_deductions())
