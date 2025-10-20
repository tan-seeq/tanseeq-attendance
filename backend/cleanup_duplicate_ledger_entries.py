"""
Cleanup Script: Remove Duplicate Ledger Entries
================================================
This script removes duplicate payroll ledger entries that occurred
due to the old reversal-based update logic.

Strategy:
1. For each (cycle_id, employee_id, source_type) combination
2. Keep only the LATEST entry (by created_at timestamp)
3. Delete all older duplicates

IMPORTANT: Run this on a backup/staging environment first!
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/hr_system')


async def cleanup_duplicate_ledger_entries():
    """Remove duplicate ledger entries, keep only latest"""
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.get_database()
    ledger_collection = db.payroll_ledger
    
    print("🔍 Analyzing payroll_ledger for duplicates...")
    
    # Aggregate to find duplicates
    pipeline = [
        {
            "$match": {
                "source_type": {"$in": ["MANUAL_DEDUCTION", "ATTENDANCE_DEDUCTION", "ADVANCE_INSTALLMENT"]}
            }
        },
        {
            "$group": {
                "_id": {
                    "cycle_id": "$cycle_id",
                    "employee_id": "$employee_id",
                    "source_type": "$source_type"
                },
                "entries": {"$push": {"id": "$id", "created_at": "$created_at", "amount": "$amount"}},
                "count": {"$sum": 1}
            }
        },
        {
            "$match": {"count": {"$gt": 1}}  # Only groups with duplicates
        }
    ]
    
    duplicates = await ledger_collection.aggregate(pipeline).to_list(None)
    
    if not duplicates:
        print("✅ No duplicates found!")
        client.close()
        return
    
    print(f"⚠️ Found {len(duplicates)} groups with duplicate entries")
    
    total_deleted = 0
    
    for dup in duplicates:
        group_key = dup["_id"]
        entries = dup["entries"]
        count = dup["count"]
        
        print(f"\n📊 Group: cycle={group_key['cycle_id'][:8]}..., employee={group_key['employee_id'][:8]}..., type={group_key['source_type']}")
        print(f"   Found {count} entries (duplicates: {count - 1})")
        
        # Sort entries by created_at (latest first)
        entries_sorted = sorted(entries, key=lambda e: e.get("created_at", ""), reverse=True)
        
        # Keep the latest entry
        latest_entry = entries_sorted[0]
        entries_to_delete = entries_sorted[1:]  # All older entries
        
        print(f"   ✅ Keeping latest entry: {latest_entry['id'][:8]}... (amount: {latest_entry['amount']})")
        print(f"   🗑️ Deleting {len(entries_to_delete)} older entries...")
        
        # Delete older entries
        for entry in entries_to_delete:
            result = await ledger_collection.delete_one({"id": entry["id"]})
            if result.deleted_count > 0:
                print(f"      ❌ Deleted: {entry['id'][:8]}... (amount: {entry['amount']})")
                total_deleted += 1
    
    print(f"\n✅ Cleanup complete! Deleted {total_deleted} duplicate entries")
    
    # Optionally recalculate employee summaries
    print("\n🔄 Recalculating employee payroll summaries...")
    
    # Get all unique (cycle_id, employee_id) pairs
    affected_pairs = await ledger_collection.aggregate([
        {
            "$group": {
                "_id": {
                    "cycle_id": "$cycle_id",
                    "employee_id": "$employee_id"
                }
            }
        }
    ]).to_list(None)
    
    summaries_collection = db.employee_payroll_summaries
    
    for pair in affected_pairs:
        cycle_id = pair["_id"]["cycle_id"]
        employee_id = pair["_id"]["employee_id"]
        
        # Recalculate totals from ledger
        ledger_entries = await ledger_collection.find({
            "cycle_id": cycle_id,
            "employee_id": employee_id,
            "is_reversed": {"$ne": True}
        }).to_list(None)
        
        attendance_ded = sum(abs(e["amount"]) for e in ledger_entries if e["source_type"] == "ATTENDANCE_DEDUCTION")
        manual_ded = sum(abs(e["amount"]) for e in ledger_entries if e["source_type"] == "MANUAL_DEDUCTION")
        advance_ded = sum(abs(e["amount"]) for e in ledger_entries if e["source_type"] == "ADVANCE_INSTALLMENT")
        
        total_deductions = attendance_ded + manual_ded + advance_ded
        
        # Update summary
        summary = await summaries_collection.find_one({
            "payroll_cycle_id": cycle_id,
            "employee_id": employee_id
        })
        
        if summary:
            base_salary = summary.get("base_salary", 0)
            allowances = summary.get("total_allowances", 0)
            gross_salary = base_salary + allowances
            net_salary = max(0, gross_salary - total_deductions)
            
            await summaries_collection.update_one(
                {
                    "payroll_cycle_id": cycle_id,
                    "employee_id": employee_id
                },
                {
                    "$set": {
                        "attendance_deductions": attendance_ded,
                        "manual_deductions": manual_ded,
                        "advance_deductions": advance_ded,
                        "total_deductions": total_deductions,
                        "net_salary": net_salary
                    }
                }
            )
            print(f"   ✅ Updated summary for employee {employee_id[:8]}... in cycle {cycle_id[:8]}...")
    
    print(f"\n🎉 All done! Cleaned up {total_deleted} duplicate entries and recalculated summaries.")
    
    client.close()


if __name__ == "__main__":
    print("=" * 60)
    print("PAYROLL LEDGER CLEANUP SCRIPT")
    print("=" * 60)
    print("⚠️ WARNING: This script will DELETE duplicate ledger entries!")
    print("⚠️ Make sure you have a backup before proceeding!")
    print("=" * 60)
    
    confirm = input("\nType 'YES' to proceed with cleanup: ")
    
    if confirm == "YES":
        asyncio.run(cleanup_duplicate_ledger_entries())
    else:
        print("❌ Cleanup cancelled.")
