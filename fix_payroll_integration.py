#!/usr/bin/env python3
"""
Script لإصلاح تكامل نظام الرواتب مع الخصومات والسلف
يربط الخصومات الموجودة والأقساط المستحقة بدورات الرواتب
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, date
import os

# MongoDB connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_URL)
db = client.tanseeq_hr

async def fix_payroll_integration():
    """إصلاح تكامل الرواتب مع الخصومات والسلف"""
    
    print("=" * 60)
    print("🔧 بدء إصلاح تكامل نظام الرواتب")
    print("=" * 60)
    
    # 1. جلب جميع دورات الرواتب المفتوحة
    cycles = await db.payroll_cycles.find({"is_locked": False}).to_list(None)
    print(f"\n✅ تم العثور على {len(cycles)} دورة رواتب مفتوحة")
    
    for cycle in cycles:
        cycle_id = cycle["id"]
        month = cycle["month"]
        print(f"\n📅 معالجة دورة: {cycle.get('display_name', month)} (ID: {cycle_id[:8]}...)")
        
        # 2. جلب الخصومات لهذا الشهر
        deductions = await db.payroll_deductions.find({
            "date": {"$regex": f"^{month}"}
        }).to_list(None)
        
        print(f"  📝 خصومات مرتبطة: {len(deductions)}")
        
        # 3. إنشاء line items للخصومات
        for ded in deductions:
            # التحقق من عدم وجود line item مسبقاً
            existing = await db.payroll_line_items.find_one({
                "payroll_cycle_id": cycle_id,
                "source_id": ded["id"],
                "source_type": "manual_deduction"
            })
            
            if existing:
                continue
            
            # إنشاء line item للخصم
            line_item = {
                "id": f"li-ded-{ded['id']}",
                "payroll_cycle_id": cycle_id,
                "employee_id": ded["employee_id"],
                "employee_name": ded.get("employee_name", ""),
                "item_type": "deduction_manual",
                "source_type": "manual_deduction",
                "source_id": ded["id"],
                "source_reference": f"خصم يدوي - {ded['date']}",
                "description": ded.get("reason", "خصم يدوي"),
                "description_ar": ded.get("reason", "خصم يدوي"),
                "amount": -abs(ded["amount"]),  # سالب للخصم
                "currency": "AED",
                "is_taxable": False,
                "affects_eos": False,
                "is_recurring": False,
                "is_editable": False,
                "is_system_generated": True,
                "is_voided": False,
                "created_by": "system",
                "created_by_name": "النظام - إصلاح تلقائي",
                "created_at": datetime.now().isoformat()
            }
            
            await db.payroll_line_items.insert_one(line_item)
            print(f"    ✅ تم ربط خصم {ded.get('employee_name', 'موظف')}: {ded['amount']} درهم")
        
        # 4. جلب الأقساط المستحقة لهذا الشهر
        installments = await db.installment_schedules.find({
            "is_active": True,
            "is_completed": False
        }).to_list(None)
        
        print(f"  💰 جدولات سلف نشطة: {len(installments)}")
        
        for inst in installments:
            # التحقق من عدم وجود line item مسبقاً
            existing = await db.payroll_line_items.find_one({
                "payroll_cycle_id": cycle_id,
                "source_id": inst["id"],
                "source_type": "installment"
            })
            
            if existing:
                continue
            
            # إنشاء line item للقسط
            installment_amount = inst.get("installment_amount", 0)
            
            line_item = {
                "id": f"li-inst-{inst['id']}-{month}",
                "payroll_cycle_id": cycle_id,
                "employee_id": inst["employee_id"],
                "employee_name": inst.get("employee_name", ""),
                "item_type": "deduction_advance",
                "source_type": "installment",
                "source_id": inst["id"],
                "source_reference": f"قسط سلفة - {month}",
                "description": f"قسط شهري من سلفة بإجمالي {inst.get('total_amount', 0)} درهم",
                "description_ar": f"قسط شهري من سلفة",
                "amount": -abs(installment_amount),  # سالب للخصم
                "currency": "AED",
                "is_taxable": False,
                "affects_eos": False,
                "is_recurring": True,
                "is_editable": False,
                "is_system_generated": True,
                "is_voided": False,
                "created_by": "system",
                "created_by_name": "النظام - إصلاح تلقائي",
                "created_at": datetime.now().isoformat()
            }
            
            await db.payroll_line_items.insert_one(line_item)
            print(f"    ✅ تم ربط قسط {inst.get('employee_name', 'موظف')}: {installment_amount} درهم")
        
        # 5. إعادة حساب employee summaries
        print(f"  🔄 إعادة حساب ملخصات الموظفين...")
        
        # جلب جميع الموظفين النشطين
        employees = await db.users.find({
            "role": "user",
            "is_active": True
        }).to_list(None)
        
        for emp in employees:
            emp_id = emp["id"]
            emp_name = emp.get("name", "")
            
            # جلب جميع line items للموظف
            line_items = await db.payroll_line_items.find({
                "payroll_cycle_id": cycle_id,
                "employee_id": emp_id,
                "is_voided": False
            }).to_list(None)
            
            # حساب الإجماليات
            base_salary = emp.get("monthly_salary", 0)
            allowances = 0.0
            manual_deductions = 0.0
            attendance_deductions = 0.0
            advance_deductions = 0.0
            other_deductions = 0.0
            
            for item in line_items:
                amount = item["amount"]
                item_type = item["item_type"]
                
                if item_type == "allowance":
                    allowances += amount
                elif item_type == "deduction_manual":
                    manual_deductions += abs(amount)
                elif item_type == "deduction_attendance":
                    attendance_deductions += abs(amount)
                elif item_type == "deduction_advance":
                    advance_deductions += abs(amount)
                elif item_type.startswith("deduction"):
                    other_deductions += abs(amount)
            
            gross_salary = base_salary + allowances
            total_deductions = manual_deductions + attendance_deductions + advance_deductions + other_deductions
            net_salary = max(0, gross_salary - total_deductions)
            
            # تحديث أو إنشاء employee summary
            summary_data = {
                "payroll_cycle_id": cycle_id,
                "employee_id": emp_id,
                "employee_name": emp_name,
                "employee_position": emp.get("position", ""),
                "department": emp.get("department"),
                "base_salary": base_salary,
                "daily_rate": base_salary / 22,
                "total_allowances": allowances,
                "overtime_amount": 0,
                "bonus_amount": 0,
                "gross_salary": gross_salary,
                "attendance_deductions": attendance_deductions,
                "advance_deductions": advance_deductions,
                "manual_deductions": manual_deductions,
                "other_deductions": other_deductions,
                "total_deductions": total_deductions,
                "net_salary": net_salary,
                "working_days": 0,
                "present_days": 0,
                "absent_days": 0,
                "late_days": 0,
                "is_calculated": True,
                "calculated_at": datetime.now().isoformat(),
                "is_approved": False
            }
            
            await db.employee_payroll_summaries.update_one(
                {
                    "payroll_cycle_id": cycle_id,
                    "employee_id": emp_id
                },
                {"$set": summary_data},
                upsert=True
            )
        
        # 6. تحديث إجماليات الدورة
        summaries = await db.employee_payroll_summaries.find({
            "payroll_cycle_id": cycle_id
        }).to_list(None)
        
        cycle_totals = {
            "total_employees": len(summaries),
            "total_gross_salary": sum(s.get("gross_salary", 0) for s in summaries),
            "total_allowances": sum(s.get("total_allowances", 0) for s in summaries),
            "total_deductions": sum(s.get("total_deductions", 0) for s in summaries),
            "total_net_salary": sum(s.get("net_salary", 0) for s in summaries)
        }
        
        await db.payroll_cycles.update_one(
            {"id": cycle_id},
            {"$set": cycle_totals}
        )
        
        print(f"  ✅ تم تحديث إجماليات الدورة:")
        print(f"     👥 الموظفين: {cycle_totals['total_employees']}")
        print(f"     💵 إجمالي الرواتب: {cycle_totals['total_gross_salary']:,.2f} درهم")
        print(f"     ➖ إجمالي الخصومات: {cycle_totals['total_deductions']:,.2f} درهم")
        print(f"     💰 الصافي: {cycle_totals['total_net_salary']:,.2f} درهم")
    
    print("\n" + "=" * 60)
    print("✅ تم إصلاح تكامل نظام الرواتب بنجاح!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(fix_payroll_integration())
