#!/usr/bin/env python3
"""
FIX HISTORICAL ATTENDANCE DATA - Late Minutes Calculation
==========================================================
Fixes 21 attendance records with incorrect late_minutes calculation.
Records historical data corruption where check-in after 9:15 was not 
marked as late.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, time
import json

sys.path.insert(0, str(Path(__file__).parent))

from db_client import get_db
from uae_datetime_utils import to_iso_string_uae

async def fix_historical_late_minutes():
    """Fix historical attendance records with incorrect late_minutes"""
    
    db = get_db()
    LATE_THRESHOLD = time(9, 15, 0)
    
    print("\n🔧 FIXING HISTORICAL ATTENDANCE DATA")
    print("="*60)
    
    # Get all attendance records with check_in
    records = await db.attendance.find({
        "check_in": {"$exists": True, "$ne": None}
    }).to_list(None)
    
    print(f"📊 Found {len(records)} total attendance records")
    
    fixes = []
    
    for record in records:
        check_in_str = record.get("check_in")
        current_late_minutes = record.get("late_minutes", 0)
        
        if not check_in_str:
            continue
        
        try:
            # Parse check-in time (robust: handles datetime and time-only strings)
            from time_utils import safe_parse_time
            check_in_time = safe_parse_time(check_in_str)
            
            if check_in_time is None:
                continue
            
            # Calculate expected late_minutes
            if check_in_time > LATE_THRESHOLD:
                check_in_dt = datetime.combine(datetime.today(), check_in_time)
                threshold_dt = datetime.combine(datetime.today(), LATE_THRESHOLD)
                expected_late_minutes = int((check_in_dt - threshold_dt).total_seconds() / 60)
            else:
                expected_late_minutes = 0
            
            # Fix if needed
            if current_late_minutes != expected_late_minutes:
                await db.attendance.update_one(
                    {"id": record["id"]},
                    {"$set": {
                        "late_minutes": expected_late_minutes,
                        "is_late": expected_late_minutes > 0,
                        "status": "late" if expected_late_minutes > 0 else record.get("status", "present"),
                        "updated_at": to_iso_string_uae(),
                        "fixed_by": "HISTORICAL_DATA_MIGRATION",
                        "fix_timestamp": to_iso_string_uae()
                    }}
                )
                
                fixes.append({
                    "id": record["id"],
                    "employee": record.get("user_name", "Unknown"),
                    "date": record.get("date"),
                    "check_in": check_in_str,
                    "old_late_minutes": current_late_minutes,
                    "new_late_minutes": expected_late_minutes,
                    "difference": expected_late_minutes - current_late_minutes
                })
                
                print(f"  ✓ Fixed: {record.get('user_name')} ({record.get('date')}) - {check_in_str} → {expected_late_minutes} min late")
        
        except Exception as e:
            print(f"  ❌ Error processing record {record.get('id')}: {e}")
    
    # Save evidence
    evidence_file = Path(__file__).parent.parent / "evidence" / "attendance_data_fix.json"
    evidence_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(evidence_file, 'w', encoding='utf-8') as f:
        json.dump({
            "total_records_checked": len(records),
            "records_fixed": len(fixes),
            "fixes": fixes,
            "timestamp": to_iso_string_uae()
        }, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n✅ COMPLETE: Fixed {len(fixes)} attendance records")
    print(f"📄 Evidence saved: {evidence_file}")
    print("="*60)
    
    return len(fixes)

if __name__ == "__main__":
    asyncio.run(fix_historical_late_minutes())
