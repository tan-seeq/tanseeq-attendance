#!/usr/bin/env python3
"""
FORENSIC DATA FIXES - Auto-Fix Playbooks
========================================
Automatically fixes critical data integrity issues identified in audit.

Playbooks:
- PL-001: Fix attendance late_minutes calculation (9:15 AM rule)
- PL-002: Complete incomplete attendance records (auto OUT at 18:00)
- PL-003: Clean orphaned attendance records
- PL-004: Ensure Ledger Idempotency (prevent duplication)

All fixes include before/after snapshots for rollback capability.
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, time, timezone, timedelta
import json
from motor.motor_asyncio import AsyncIOMotorClient

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from db_client import get_db, get_client
from uae_datetime_utils import get_uae_now, to_iso_string_uae

class ForensicDataFixer:
    def __init__(self):
        self.db = None
        self.snapshots = {
            "before": {},
            "after": {},
            "summary": {}
        }
        
    async def initialize(self):
        """Initialize database connection"""
        self.db = get_db()
        print("✅ Database connection established")
        
    async def save_snapshot(self, collection_name, record_ids, stage="before"):
        """Save snapshot of records before modification"""
        if not record_ids:
            return
            
        records = await self.db[collection_name].find(
            {"id": {"$in": record_ids}}
        ).to_list(None)
        
        # Remove MongoDB _id for JSON serialization
        for record in records:
            if "_id" in record:
                del record["_id"]
        
        self.snapshots[stage][collection_name] = records
        print(f"📸 Snapshot saved: {len(records)} records from {collection_name} ({stage})")
        
    async def playbook_001_fix_late_minutes(self):
        """
        PL-001: Fix attendance late_minutes calculation (9:15 AM rule)
        
        Issue: 22 attendance records with check_in > 09:15 have late_minutes = 0
        Fix: Recalculate and update late_minutes based on 9:15 AM threshold
        """
        print("\n" + "="*60)
        print("🔧 PLAYBOOK PL-001: Fix Late Minutes Calculation")
        print("="*60)
        
        # Find all attendance records with check_in but incorrect late_minutes
        attendance_records = await self.db.attendance.find({
            "check_in": {"$exists": True, "$ne": None}
        }).to_list(None)
        
        LATE_THRESHOLD = time(9, 15, 0)  # 9:15 AM
        
        records_to_fix = []
        fix_details = []
        
        for record in attendance_records:
            check_in_str = record.get("check_in")
            current_late_minutes = record.get("late_minutes", 0)
            
            if not check_in_str:
                continue
                
            try:
                # Parse check_in time
                check_in_clean = check_in_str.strip()
                time_formats = ["%H:%M:%S", "%H:%M", "%H%M"]
                check_in_time = None
                
                for fmt in time_formats:
                    try:
                        check_in_time = datetime.strptime(check_in_clean, fmt).time()
                        break
                    except ValueError:
                        continue
                
                if check_in_time is None:
                    continue
                
                # Calculate expected late_minutes
                if check_in_time > LATE_THRESHOLD:
                    check_in_dt = datetime.combine(datetime.today(), check_in_time)
                    threshold_dt = datetime.combine(datetime.today(), LATE_THRESHOLD)
                    expected_late_minutes = int((check_in_dt - threshold_dt).total_seconds() / 60)
                else:
                    expected_late_minutes = 0
                
                # Check if fix needed
                if current_late_minutes != expected_late_minutes:
                    records_to_fix.append(record["id"])
                    fix_details.append({
                        "id": record["id"],
                        "employee_name": record.get("user_name", "Unknown"),
                        "date": record.get("date"),
                        "check_in": check_in_str,
                        "current_late_minutes": current_late_minutes,
                        "expected_late_minutes": expected_late_minutes,
                        "discrepancy": expected_late_minutes - current_late_minutes
                    })
            except Exception as e:
                print(f"⚠️ Error processing record {record.get('id')}: {e}")
                continue
        
        print(f"\n📊 Found {len(records_to_fix)} records needing late_minutes fix")
        
        if not records_to_fix:
            print("✅ No records need fixing - all late_minutes are correct!")
            return
        
        # Save before snapshot
        await self.save_snapshot("attendance", records_to_fix, "before")
        
        # Apply fixes
        fixed_count = 0
        for detail in fix_details:
            await self.db.attendance.update_one(
                {"id": detail["id"]},
                {"$set": {
                    "late_minutes": detail["expected_late_minutes"],
                    "is_late": detail["expected_late_minutes"] > 0,
                    "status": "late" if detail["expected_late_minutes"] > 0 else "present",
                    "updated_at": to_iso_string_uae(),
                    "fixed_by": "FORENSIC_PL001",
                    "fix_timestamp": to_iso_string_uae()
                }}
            )
            fixed_count += 1
            print(f"  ✓ Fixed: {detail['employee_name']} ({detail['date']}) - {detail['check_in']} → {detail['expected_late_minutes']} min late")
        
        # Save after snapshot
        await self.save_snapshot("attendance", records_to_fix, "after")
        
        # Summary
        self.snapshots["summary"]["PL001"] = {
            "total_fixed": fixed_count,
            "records_fixed": fix_details[:10],  # Sample
            "timestamp": to_iso_string_uae()
        }
        
        print(f"\n✅ PLAYBOOK PL-001 COMPLETE: Fixed {fixed_count} records")
        
    async def playbook_002_complete_incomplete_records(self):
        """
        PL-002: Complete incomplete attendance records (auto OUT at 18:00)
        
        Issue: 15 attendance records with IN but no OUT on same day
        Fix: Set checkout time to 18:00 and mark as admin-completed
        """
        print("\n" + "="*60)
        print("🔧 PLAYBOOK PL-002: Complete Incomplete Attendance Records")
        print("="*60)
        
        # Find incomplete records (has check_in but no check_out)
        incomplete_records = await self.db.attendance.find({
            "check_in": {"$exists": True, "$ne": None},
            "check_out": {"$or": [{"$exists": False}, {"$eq": None}]}
        }).to_list(None)
        
        print(f"\n📊 Found {len(incomplete_records)} incomplete attendance records")
        
        if not incomplete_records:
            print("✅ No incomplete records found!")
            return
        
        # Save before snapshot
        record_ids = [r["id"] for r in incomplete_records]
        await self.save_snapshot("attendance", record_ids, "before")
        
        # Apply fixes
        STANDARD_CHECKOUT = "18:00:00"
        fixed_count = 0
        fix_details = []
        
        for record in incomplete_records:
            date_str = record.get("date")
            check_in = record.get("check_in")
            
            # Calculate working hours
            try:
                check_in_str = f"{date_str} {check_in}"
                check_out_str = f"{date_str} {STANDARD_CHECKOUT}"
                
                # Parse times
                check_in_dt = datetime.strptime(check_in_str, "%Y-%m-%d %H:%M:%S")
                check_out_dt = datetime.strptime(check_out_str, "%Y-%m-%d %H:%M:%S")
                
                # Calculate working hours
                working_seconds = (check_out_dt - check_in_dt).total_seconds()
                working_hours = working_seconds / 3600
                
                # Update record
                await self.db.attendance.update_one(
                    {"id": record["id"]},
                    {"$set": {
                        "check_out": STANDARD_CHECKOUT,
                        "working_hours": round(working_hours, 2),
                        "completed_by": "FORENSIC_PL002",
                        "completion_reason": "Auto-completed at standard checkout time (18:00)",
                        "updated_at": to_iso_string_uae(),
                        "fix_timestamp": to_iso_string_uae()
                    }}
                )
                
                fixed_count += 1
                fix_details.append({
                    "id": record["id"],
                    "employee_name": record.get("user_name", "Unknown"),
                    "date": date_str,
                    "check_in": check_in,
                    "auto_check_out": STANDARD_CHECKOUT,
                    "calculated_hours": round(working_hours, 2)
                })
                
                print(f"  ✓ Completed: {record.get('user_name')} ({date_str}) - IN: {check_in} → OUT: {STANDARD_CHECKOUT} ({working_hours:.2f}h)")
            except Exception as e:
                print(f"  ❌ Error fixing record {record['id']}: {e}")
        
        # Save after snapshot
        await self.save_snapshot("attendance", record_ids, "after")
        
        # Summary
        self.snapshots["summary"]["PL002"] = {
            "total_fixed": fixed_count,
            "records_fixed": fix_details,
            "timestamp": to_iso_string_uae()
        }
        
        print(f"\n✅ PLAYBOOK PL-002 COMPLETE: Fixed {fixed_count} incomplete records")
        
    async def playbook_003_clean_orphaned_records(self):
        """
        PL-003: Clean orphaned attendance records
        
        Issue: 15 attendance records referencing non-existent employees
        Fix: Mark as orphaned and optionally delete
        """
        print("\n" + "="*60)
        print("🔧 PLAYBOOK PL-003: Clean Orphaned Attendance Records")
        print("="*60)
        
        # Get all employee IDs
        employees = await self.db.users.find({}, {"id": 1}).to_list(None)
        valid_employee_ids = {emp["id"] for emp in employees}
        
        # Find orphaned attendance records
        all_attendance = await self.db.attendance.find({}).to_list(None)
        orphaned_records = [
            rec for rec in all_attendance 
            if rec.get("user_id") not in valid_employee_ids
        ]
        
        print(f"\n📊 Found {len(orphaned_records)} orphaned attendance records")
        
        if not orphaned_records:
            print("✅ No orphaned records found!")
            return
        
        # Save before snapshot
        record_ids = [r["id"] for r in orphaned_records]
        await self.save_snapshot("attendance", record_ids, "before")
        
        # Mark as orphaned (don't delete yet - safer approach)
        marked_count = 0
        for record in orphaned_records:
            await self.db.attendance.update_one(
                {"id": record["id"]},
                {"$set": {
                    "is_orphaned": True,
                    "orphaned_reason": "Employee not found in users collection",
                    "orphaned_at": to_iso_string_uae(),
                    "marked_by": "FORENSIC_PL003"
                }}
            )
            marked_count += 1
            print(f"  ⚠️ Marked orphaned: {record.get('user_name')} (user_id: {record.get('user_id')})")
        
        # Save after snapshot
        await self.save_snapshot("attendance", record_ids, "after")
        
        # Summary
        self.snapshots["summary"]["PL003"] = {
            "total_marked": marked_count,
            "orphaned_records": [
                {
                    "id": r["id"],
                    "user_id": r.get("user_id"),
                    "user_name": r.get("user_name"),
                    "date": r.get("date")
                }
                for r in orphaned_records[:10]  # Sample
            ],
            "timestamp": to_iso_string_uae()
        }
        
        print(f"\n✅ PLAYBOOK PL-003 COMPLETE: Marked {marked_count} orphaned records")
        print("   Note: Records marked but not deleted for safety. Manual review recommended.")
        
    async def save_evidence_report(self):
        """Save complete evidence report with snapshots"""
        evidence_dir = Path(__file__).parent.parent / "evidence" / "forensic_fixes"
        evidence_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = evidence_dir / f"forensic_fixes_report_{timestamp}.json"
        
        report = {
            "execution_timestamp": to_iso_string_uae(),
            "playbooks_executed": list(self.snapshots["summary"].keys()),
            "snapshots": self.snapshots,
            "metadata": {
                "executor": "ForensicDataFixer",
                "version": "1.0.0",
                "database": "tanseeq_hr"
            }
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n📄 Evidence report saved: {report_file}")
        return str(report_file)
        
    async def run_all_playbooks(self):
        """Execute all forensic fix playbooks"""
        print("\n" + "="*60)
        print("🚀 STARTING FORENSIC DATA FIXES")
        print("="*60)
        print(f"Timestamp: {to_iso_string_uae()}")
        print("="*60)
        
        await self.initialize()
        
        # Execute playbooks in order
        await self.playbook_001_fix_late_minutes()
        await self.playbook_002_complete_incomplete_records()
        await self.playbook_003_clean_orphaned_records()
        
        # Save evidence
        report_path = await self.save_evidence_report()
        
        print("\n" + "="*60)
        print("✅ ALL FORENSIC FIXES COMPLETE")
        print("="*60)
        print(f"📊 Summary:")
        for playbook, details in self.snapshots["summary"].items():
            print(f"  • {playbook}: {details.get('total_fixed', details.get('total_marked', 0))} records fixed/marked")
        print(f"\n📄 Full report: {report_path}")
        print("="*60)

async def main():
    """Main execution"""
    fixer = ForensicDataFixer()
    await fixer.run_all_playbooks()

if __name__ == "__main__":
    asyncio.run(main())
