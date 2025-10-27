#!/usr/bin/env python3
"""
Clear October 2025 test data and verify real attendance data
"""
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

async def clear_test_data():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("🗑️  CLEARING OCTOBER 2025 TEST DATA")
    print("=" * 70)
    
    # Delete October 2025 test attendance data
    result = await db.attendance.delete_many({
        "date": {"$gte": "2025-09-29", "$lte": "2025-10-28"}
    })
    
    print(f"✅ Deleted {result.deleted_count} October 2025 test attendance records")
    
    # Check what months have real data
    print("\n📅 AVAILABLE ATTENDANCE DATA BY MONTH:")
    
    # Get distinct months
    pipeline = [
        {"$match": {"date": {"$exists": True}}},
        {"$group": {
            "_id": {
                "$substr": ["$date", 0, 7]  # Extract YYYY-MM
            },
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": -1}}
    ]
    
    months = await db.attendance.aggregate(pipeline).to_list(None)
    
    if months:
        print("\nAvailable months with attendance data:")
        for month in months:
            month_str = month["_id"]
            count = month["count"]
            print(f"   {month_str}: {count} records")
    else:
        print("\n⚠️  NO attendance data found in database!")
        print("   The system needs real attendance data to calculate deductions.")
    
    # Check specific employees mentioned by user
    print("\n👥 CHECKING SPECIFIC EMPLOYEES:")
    
    employees_to_check = [
        {"name": "TAREK", "pattern": "tarek"},
        {"name": "GEHAD", "pattern": "gehad"},
        {"name": "MOHAMED MOSTAFA", "pattern": "mostafa"}
    ]
    
    for emp_check in employees_to_check:
        emp = await db.users.find_one({
            "name": {"$regex": emp_check["pattern"], "$options": "i"}
        })
        
        if emp:
            emp_id = emp["id"]
            emp_name = emp["name"]
            
            # Get recent attendance
            recent = await db.attendance.find({
                "user_id": emp_id
            }).sort("date", -1).limit(1).to_list(1)
            
            if recent:
                last_date = recent[0]["date"]
                print(f"\n   {emp_name}:")
                print(f"   - Last attendance record: {last_date}")
            else:
                print(f"\n   {emp_name}:")
                print(f"   - ⚠️  NO attendance records found!")
    
    client.close()
    print("\n" + "=" * 70)
    print("✅ Cleanup complete!")

asyncio.run(clear_test_data())
