#!/usr/bin/env python3
"""
Script to add flexible schedule to all existing employees
إضافة الدوام المرن لجميع الموظفين الحاليين
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime

# MongoDB connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017/tanseeq_hr")
client = AsyncIOMotorClient(MONGO_URL)
db = client[os.environ.get('DB_NAME', 'tanseeq_hr')]

async def add_flexible_schedule_to_all_employees():
    """Add flexible schedule to all existing employees"""
    print("🔄 Adding flexible schedule to all employees...")
    
    # Update all users to have flexible schedule
    result = await db.users.update_many(
        {}, # Empty filter to update all documents
        {
            "$set": {
                "has_flexible_schedule": True,
                "flexible_hours_per_day": 8.0,
                "flexible_start_range": "07:00-11:00",  # Can start between 7 AM and 11 AM
                "flexible_end_range": "15:00-24:00",    # Can end between 3 PM and midnight
                "max_daily_hours": 13.0,                # Maximum 13 hours per day
                "min_daily_hours": 8.0,                 # Minimum 8 hours per day
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    print(f"✅ Updated {result.modified_count} employees with flexible schedule")
    
    # Print all users to verify
    users = await db.users.find({}).to_list(1000)
    print(f"\n📋 Current employees status:")
    for user in users:
        print(f"  - {user['name']} ({user['email']}): Flexible Schedule = {user.get('has_flexible_schedule', False)}")
    
    return result.modified_count

async def main():
    """Main function"""
    print("🚀 TANSEEQ HR - Adding Flexible Schedule to All Employees")
    print("=" * 60)
    
    try:
        updated_count = await add_flexible_schedule_to_all_employees()
        print(f"\n✅ Successfully updated {updated_count} employees")
        print("\n🎯 New flexible schedule features:")
        print("  - Can work 8-13 hours per day")
        print("  - Can start between 7 AM and 11 AM")
        print("  - Can end between 3 PM and midnight")
        print("  - No restrictions on checkout time")
        print("  - Full flexibility for all employees")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(main())