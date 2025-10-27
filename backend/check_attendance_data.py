#!/usr/bin/env python3
import asyncio
import sys
from motor.motor_asyncio import AsyncIOMotorClient
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv()

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'tanseeq_hr')

async def check_data():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Count total attendance records
    total = await db.attendance.count_documents({})
    print(f"📊 Total attendance records: {total}")
    
    # Count October 2025 records
    oct_count = await db.attendance.count_documents({
        "date": {"$gte": "2025-09-29", "$lte": "2025-10-28"}
    })
    print(f"📅 October 2025 cycle records: {oct_count}")
    
    # Get sample employees
    employees = await db.users.find({"is_active": True}).limit(3).to_list(3)
    
    print("\n👥 Sample employee attendance (October 2025):")
    for emp in employees:
        emp_id = emp["id"]
        emp_name = emp["name"]
        
        records = await db.attendance.find({
            "user_id": emp_id,
            "date": {"$gte": "2025-09-29", "$lte": "2025-10-28"}
        }).to_list(None)
        
        print(f"\n   {emp_name} ({emp_id[:8]}...):")
        print(f"   - Total records: {len(records)}")
        
        if len(records) > 0:
            # Check for duplicates
            dates = [r["date"] for r in records]
            unique_dates = set(dates)
            if len(dates) != len(unique_dates):
                print(f"   ⚠️  DUPLICATES FOUND: {len(dates)} records for {len(unique_dates)} dates")
                # Show duplicate dates
                from collections import Counter
                date_counts = Counter(dates)
                for date, count in date_counts.most_common(3):
                    if count > 1:
                        print(f"      - {date}: {count} records")
                        # Show details
                        dup_recs = [r for r in records if r["date"] == date]
                        for dr in dup_recs[:3]:
                            print(f"         • check_in: {dr.get('check_in')}, status: {dr.get('status')}, id: {dr.get('id')[:8]}...")
            else:
                print(f"   ✅ No duplicates: {len(records)} records for {len(unique_dates)} unique dates")
                # Show sample records
                for r in records[:3]:
                    print(f"      - {r['date']}: check_in={r.get('check_in')}, status={r.get('status')}")
    
    client.close()

asyncio.run(check_data())
