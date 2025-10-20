"""
Payroll Integration for Advanced Deductions
============================================
ربط الخصومات المتقدمة مع دورة الرواتب تلقائياً
"""

from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional, Dict
from advanced_deductions_system import get_cycle_dates
from datetime import datetime


async def merge_advanced_deductions_to_payroll(
    db: AsyncIOMotorDatabase,
    cycle_id: str,
    month: int,
    year: int,
    created_by: str
) -> Dict:
    """
    Merge advanced deductions into payroll cycle
    
    This function:
    1. Gets the cycle date range (29 → 28)
    2. Fetches advanced deductions for all employees in that range
    3. Updates employee_payroll_summaries with advanced_deductions_amount
    4. Creates/updates ADVANCED_DEDUCTION entries in payroll_ledger
    5. Recalculates net_salary
    
    Args:
        db: MongoDB database
        cycle_id: Payroll cycle ID
        month: Month (1-12)
        year: Year (e.g., 2025)
        created_by: User ID who triggered this
        
    Returns:
        Dict with statistics
    """
    from payroll_ledger_service import PayrollLedgerService
    
    ledger_service = PayrollLedgerService(db)
    
    # Get cycle dates
    cycle_start, cycle_end = get_cycle_dates(month, year)
    cycle_start_str = cycle_start.strftime("%Y-%m-%d")
    cycle_end_str = cycle_end.strftime("%Y-%m-%d")
    
    print(f"\n🔗 Merging advanced deductions to payroll cycle {cycle_id}")
    print(f"   Cycle: {cycle_start_str} → {cycle_end_str}")
    
    # Get all deductions for this cycle
    deductions = await db.deductions_advanced.find({
        "cycle_start": cycle_start_str,
        "cycle_end": cycle_end_str
    }).to_list(None)
    
    if not deductions:
        print("   ⚠️ No advanced deductions found for this cycle")
        return {
            "employees_updated": 0,
            "total_deduction_amount": 0.0,
            "message": "No deductions found"
        }
    
    # Group by employee
    employee_deductions = {}
    for ded in deductions:
        emp_id = ded["employee_id"]
        if emp_id not in employee_deductions:
            employee_deductions[emp_id] = {
                "employee_id": emp_id,
                "employee_name": ded["employee_name"],
                "total_minutes": 0,
                "total_amount": 0.0,
                "days_count": 0
            }
        
        employee_deductions[emp_id]["total_minutes"] += ded.get("deficit_minutes", 0)
        employee_deductions[emp_id]["total_amount"] += ded.get("deduction_amount", 0.0)
        employee_deductions[emp_id]["days_count"] += 1
    
    print(f"   📊 Found deductions for {len(employee_deductions)} employees")
    
    # Update each employee's payroll summary
    employees_updated = 0
    total_merged_amount = 0.0
    
    for emp_id, ded_data in employee_deductions.items():
        emp_name = ded_data["employee_name"]
        total_amount = ded_data["total_amount"]
        total_minutes = ded_data["total_minutes"]
        
        print(f"\n   👤 {emp_name}:")
        print(f"      Deficit: {total_minutes} min → {total_amount:.2f} AED")
        
        # Get employee's payroll summary
        summary = await db.employee_payroll_summaries.find_one({
            "payroll_cycle_id": cycle_id,
            "employee_id": emp_id
        })
        
        if not summary:
            print(f"      ⚠️ No payroll summary found - skipping")
            continue
        
        # ✅ Step 1: Delete old ADVANCED_DEDUCTION entries in ledger (prevent duplication)
        delete_result = await db.payroll_ledger.delete_many({
            "employee_id": emp_id,
            "cycle_id": cycle_id,
            "source_type": "ADVANCED_DEDUCTION"
        })
        
        if delete_result.deleted_count > 0:
            print(f"      🗑️ Deleted {delete_result.deleted_count} old ledger entries")
        
        # ✅ Step 2: Create new ADVANCED_DEDUCTION entry
        if total_amount > 0:
            await ledger_service.create_entry(
                employee_id=emp_id,
                cycle_id=cycle_id,
                source_type="ADVANCED_DEDUCTION",
                source_id=f"advanced_ded_{cycle_id}_{emp_id}",
                amount=-abs(total_amount),  # Negative for deduction
                description=f"خصومات متقدمة (تأخير وانصراف مبكر) - {total_minutes} دقيقة",
                created_by=created_by
            )
            print(f"      ✅ Created ledger entry: -{total_amount:.2f} AED")
        
        # ✅ Step 3: Update payroll summary
        current_deductions = summary.get("total_deductions", 0.0)
        base_salary = summary.get("base_salary", 0.0)
        allowances = summary.get("total_allowances", 0.0)
        
        # Recalculate total deductions (sum from ledger)
        ledger_entries = await db.payroll_ledger.find({
            "employee_id": emp_id,
            "cycle_id": cycle_id,
            "is_reversed": {"$ne": True}
        }).to_list(None)
        
        new_total_deductions = sum(abs(e["amount"]) for e in ledger_entries if e["amount"] < 0)
        
        # Recalculate net salary
        gross_salary = base_salary + allowances
        new_net_salary = max(0, gross_salary - new_total_deductions)
        
        # Update summary
        await db.employee_payroll_summaries.update_one(
            {
                "payroll_cycle_id": cycle_id,
                "employee_id": emp_id
            },
            {
                "$set": {
                    "advanced_deductions_amount": total_amount,
                    "advanced_deductions_minutes": total_minutes,
                    "total_deductions": new_total_deductions,
                    "net_salary": new_net_salary,
                    "updated_at": datetime.now().isoformat()
                }
            }
        )
        
        print(f"      💰 Updated summary:")
        print(f"         Total Deductions: {current_deductions:.2f} → {new_total_deductions:.2f}")
        print(f"         Net Salary: {new_net_salary:.2f}")
        
        employees_updated += 1
        total_merged_amount += total_amount
    
    # Update cycle totals
    await db.payroll_cycles.update_one(
        {"id": cycle_id},
        {
            "$set": {
                "advanced_deductions_merged": True,
                "advanced_deductions_merged_at": datetime.now().isoformat(),
                "advanced_deductions_merged_by": created_by
            }
        }
    )
    
    print(f"\n   ✅ Merged complete!")
    print(f"      Employees: {employees_updated}")
    print(f"      Total Amount: {total_merged_amount:.2f} AED")
    
    return {
        "employees_updated": employees_updated,
        "total_deduction_amount": round(total_merged_amount, 2),
        "message": f"تم دمج الخصومات المتقدمة لـ {employees_updated} موظف"
    }


async def recalculate_payroll_after_deductions(
    db: AsyncIOMotorDatabase,
    cycle_id: str
):
    """
    Recalculate all employee net salaries after deductions change
    
    Called after:
    - Adding/removing advanced deductions
    - Editing manual deductions
    - Any ledger changes
    """
    # Get all employees in cycle
    summaries = await db.employee_payroll_summaries.find({
        "payroll_cycle_id": cycle_id
    }).to_list(None)
    
    for summary in summaries:
        emp_id = summary["employee_id"]
        
        # Get all ledger entries
        ledger_entries = await db.payroll_ledger.find({
            "employee_id": emp_id,
            "cycle_id": cycle_id,
            "is_reversed": {"$ne": True}
        }).to_list(None)
        
        # Calculate totals
        total_deductions = sum(abs(e["amount"]) for e in ledger_entries if e["amount"] < 0)
        
        base_salary = summary.get("base_salary", 0.0)
        allowances = summary.get("total_allowances", 0.0)
        gross_salary = base_salary + allowances
        net_salary = max(0, gross_salary - total_deductions)
        
        # Update
        await db.employee_payroll_summaries.update_one(
            {"_id": summary["_id"]},
            {
                "$set": {
                    "total_deductions": total_deductions,
                    "net_salary": net_salary
                }
            }
        )
