#!/usr/bin/env python3
"""
🔧 Data Cleanup Script: Remove Duplicate Attendance Records
============================================================
CRITICAL FIX: Remove duplicate attendance records that are causing
incorrect payroll deduction calculations.

Problem: Multiple attendance records exist for the same employee on the same date,
causing the deductions engine to process duplicates and calculate wrong amounts.

Solution:
1. Identify duplicates (same user_id + date)
2. Keep the LATEST record (by created_at timestamp)
3. Delete older duplicates
4. Add unique index to prevent future duplicates
"""

import asyncio
import sys
from motor.motor_asyncio import AsyncIOMotorClient
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'tanseeq_hr')

async def cleanup_duplicate_attendance():
    """Remove duplicate attendance records and add unique constraint"""
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("=" * 70)
    print("🔧 ATTENDANCE DATA CLEANUP - REMOVING DUPLICATES")
    print("=" * 70)
    
    # Step 1: Analyze duplicates
    print("\n📊 Step 1: Analyzing duplicate records...")
    
    duplicate_pipeline = [
        {
            "$group": {
                "_id": {
                    "user_id": "$user_id",
                    "date": "$date"
                },
                "count": {"$sum": 1},
                "records": {"$push": {
                    "id": "$id",
                    "created_at": "$created_at",
                    "check_in": "$check_in",
                    "status": "$status"
                }}
            }
        },
        {
            "$match": {
                "count": {"$gt": 1}  # Only duplicates
            }
        },
        {
            "$sort": {"count": -1}
        }
    ]
    
    duplicates = await db.attendance.aggregate(duplicate_pipeline).to_list(None)
    
    if not duplicates:
        print("✅ No duplicate records found!")
        return
    
    print(f"⚠️  Found {len(duplicates)} sets of duplicate records")
    
    # Show sample duplicates
    print("\n📋 Sample duplicates (first 5):")
    for i, dup in enumerate(duplicates[:5]):
        user_id = dup["_id"]["user_id"]
        date = dup["_id"]["date"]
        count = dup["count"]
        print(f"   {i+1}. User: {user_id[:8]}..., Date: {date}, Count: {count}")
        for j, rec in enumerate(dup["records"][:3]):  # Show first 3 records
            check_in = rec.get("check_in", "N/A")
            status = rec.get("status", "N/A")
            print(f"      - Record {j+1}: check_in={check_in}, status={status}")
    
    # Calculate total duplicates to remove
    total_duplicates = sum(d["count"] - 1 for d in duplicates)  # Keep 1, remove rest
    print(f"\n📊 Total duplicate records to remove: {total_duplicates}")
    
    # Step 2: Remove duplicates (keep latest by created_at)
    print("\n🗑️  Step 2: Removing duplicate records (keeping latest)...")
    
    removed_count = 0
    
    for dup in duplicates:
        user_id = dup["_id"]["user_id"]
        date = dup["_id"]["date"]
        records = dup["records"]
        
        # Sort by created_at (latest first), keep first, delete rest
        records_sorted = sorted(
            records,
            key=lambda x: x.get("created_at", "1970-01-01T00:00:00"),
            reverse=True
        )
        
        # IDs to keep (latest)
        keep_id = records_sorted[0]["id"]
        
        # IDs to delete (older duplicates)
        delete_ids = [r["id"] for r in records_sorted[1:]]
        
        if delete_ids:
            result = await db.attendance.delete_many({
                "id": {"$in": delete_ids}
            })
            removed_count += result.deleted_count
            
            if removed_count % 50 == 0:  # Progress update every 50 deletions
                print(f"   ⏳ Processed {removed_count} deletions...")
    
    print(f"✅ Removed {removed_count} duplicate attendance records")
    
    # Step 3: Verify cleanup
    print("\n✅ Step 3: Verifying cleanup...")
    
    remaining_duplicates = await db.attendance.aggregate(duplicate_pipeline).to_list(None)
    
    if remaining_duplicates:
        print(f"⚠️  Warning: {len(remaining_duplicates)} duplicate sets still remain")
    else:
        print("✅ All duplicates successfully removed!")
    
    # Step 4: Create unique index
    print("\n🔒 Step 4: Creating unique index to prevent future duplicates...")
    
    try:
        # Drop existing index if it exists (non-unique)
        try:
            await db.attendance.drop_index("user_id_1_date_1")
            print("   ℹ️  Dropped existing non-unique index")
        except:
            pass  # Index doesn't exist, that's fine
        
        # Create unique compound index
        await db.attendance.create_index(
            [("user_id", 1), ("date", 1)],
            unique=True,
            name="user_id_date_unique"
        )
        print("✅ Created unique index: user_id + date")
        print("   → Future duplicate inserts will be prevented automatically")
        
    except Exception as e:
        print(f"⚠️  Could not create unique index: {e}")
        print("   → You may need to run this manually in MongoDB")
    
    # Step 5: Final statistics
    print("\n" + "=" * 70)
    print("📊 CLEANUP SUMMARY")
    print("=" * 70)
    
    total_records = await db.attendance.count_documents({})
    print(f"✅ Total attendance records after cleanup: {total_records}")
    print(f"🗑️  Duplicates removed: {removed_count}")
    print(f"📅 Unique employee-date combinations: {total_records}")
    print("\n✅ Data cleanup complete! Payroll calculations should now be accurate.")
    
    client.close()

if __name__ == "__main__":
    print(f"\n🚀 Starting cleanup at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    asyncio.run(cleanup_duplicate_attendance())
    print(f"\n✅ Cleanup finished at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
