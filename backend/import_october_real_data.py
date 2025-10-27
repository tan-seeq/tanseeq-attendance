#!/usr/bin/env python3
"""
Import REAL October 2025 attendance data from user
"""
import asyncio
import sys
from motor.motor_asyncio import AsyncIOMotorClient
import os
from pathlib import Path
from datetime import datetime
import uuid

sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv()

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'tanseeq_hr')

# Real attendance data from user (manually extracted from Excel/HTML table)
ATTENDANCE_DATA = [
    # Format: (emp_name, date, check_in, check_out, status)
    ("HESHAM AHMED MOHAMED MOSTAFA", "2025-10-27", "09:04:27", None, "present"),
    ("Mohamed AHMED MOHAMED MOSTAFA", "2025-10-27", "08:47:38", None, "present"),
    ("TAREK ABDELMONEM ZAKI ALWAZAN", "2025-10-27", "08:43:53", None, "present"),
    ("KARIM MOHAMED MOUSTAFA ABDELMEGEUID", "2025-10-27", "08:41:43", None, "present"),
    ("Hatem Mohamed Ahmed", "2025-10-27", "07:35:00", None, "present"),
    
    ("HESHAM AHMED MOHAMED MOSTAFA", "2025-10-26", "09:24:36", "18:21:33", "late"),
    ("TAREK ABDELMONEM ZAKI ALWAZAN", "2025-10-26", "08:32:25", "15:31:43", "present"),
    ("KARIM MOHAMED MOUSTAFA ABDELMEGEUID", "2025-10-26", "08:53:20", "18:21:53", "present"),
    ("Hatem Mohamed Ahmed", "2025-10-26", "08:32:01", "17:25:00", "present"),
    ("Mohamed AHMED MOHAMED MOSTAFA", "2025-10-26", None, None, "absent"),  # ABSENCE
    
    ("HESHAM AHMED MOHAMED MOSTAFA", "2025-10-23", "09:03:36", "18:04:00", "present"),
    ("Mohamed AHMED MOHAMED MOSTAFA", "2025-10-23", "09:01:57", "18:04:00", "present"),
    ("KARIM MOHAMED MOUSTAFA ABDELMEGEUID", "2025-10-23", "08:49:23", "18:03:00", "present"),
    ("TAREK ABDELMONEM ZAKI ALWAZAN", "2025-10-23", "08:12:47", "15:18:27", "present"),
    
    ("Mohamed AHMED MOHAMED MOSTAFA", "2025-10-22", None, None, "absent"),  # ABSENCE
    ("TAREK ABDELMONEM ZAKI ALWAZAN", "2025-10-22", "08:25:02", "15:15:57", "present"),
    ("KARIM MOHAMED MOUSTAFA ABDELMEGEUID", "2025-10-22", "08:54:59", "17:31:57", "present"),
    ("HESHAM AHMED MOHAMED MOSTAFA", "2025-10-22", "09:05:01", "17:32:05", "present"),
    ("Hatem Mohamed Ahmed", "2025-10-22", "08:22:00", "17:52:03", "present"),
    
    ("Mohamed AHMED MOHAMED MOSTAFA", "2025-10-21", "09:42:21", "20:20:11", "late"),
    ("HESHAM AHMED MOHAMED MOSTAFA", "2025-10-21", "09:03:20", "18:11:58", "present"),
    ("KARIM MOHAMED MOUSTAFA ABDELMEGEUID", "2025-10-21", "08:50:52", "18:12:04", "present"),
    ("Hatem Mohamed Ahmed", "2025-10-21", "07:14:29", "17:00:00", "present"),
    
    ("Mohamed AHMED MOHAMED MOSTAFA", "2025-10-20", "09:22:05", "18:00:17", "late"),
    ("HESHAM AHMED MOHAMED MOSTAFA", "2025-10-20", "09:17:03", "17:57:22", "late"),
    ("KARIM MOHAMED MOUSTAFA ABDELMEGEUID", "2025-10-20", "08:52:36", "17:52:00", "present"),
    ("Hatem Mohamed Ahmed", "2025-10-20", "08:22:59", "16:38:00", "present"),
    ("TAREK ABDELMONEM ZAKI ALWAZAN", "2025-10-20", "08:22:58", "15:19:06", "present"),
    
    ("Hatem Mohamed Ahmed", "2025-10-19", "09:08:54", "17:10:00", "present"),
    ("TAREK ABDELMONEM ZAKI ALWAZAN", "2025-10-19", "08:11:05", "15:31:16", "present"),
    ("KARIM MOHAMED MOUSTAFA ABDELMEGEUID", "2025-10-19", "08:52:40", "17:01:05", "present"),
    ("HESHAM AHMED MOHAMED MOSTAFA", "2025-10-19", "09:09:10", "17:01:32", "late"),
    ("Mohamed AHMED MOHAMED MOSTAFA", "2025-10-19", "10:12:43", "18:02:53", "late"),
    
    ("Mohamed AHMED MOHAMED MOSTAFA", "2025-10-16", "09:29:13", "17:28:00", "late"),
    ("HESHAM AHMED MOHAMED MOSTAFA", "2025-10-16", "09:13:54", "17:49:38", "late"),
    ("KARIM MOHAMED MOUSTAFA ABDELMEGEUID", "2025-10-16", "08:50:22", "17:49:52", "present"),
    ("Hatem Mohamed Ahmed", "2025-10-16", "08:10:43", "14:18:00", "present"),
    ("TAREK ABDELMONEM ZAKI ALWAZAN", "2025-10-16", "08:10:42", "15:30:33", "present"),
    
    ("Mohamed AHMED MOHAMED MOSTAFA", "2025-10-15", "09:50:43", "20:34:47", "late"),
    ("Hatem Mohamed Ahmed", "2025-10-15", "08:45:57", "17:00:00", "present"),
    ("HESHAM AHMED MOHAMED MOSTAFA", "2025-10-15", "09:07:50", "18:40:51", "late"),
    ("KARIM MOHAMED MOUSTAFA ABDELMEGEUID", "2025-10-15", "08:50:59", "18:40:20", "present"),
    ("TAREK ABDELMONEM ZAKI ALWAZAN", "2025-10-15", "08:28:35", "15:17:50", "present"),
    
    ("TAREK ABDELMONEM ZAKI ALWAZAN", "2025-10-14", "08:00:49", "15:21:22", "present"),
    ("KARIM MOHAMED MOUSTAFA ABDELMEGEUID", "2025-10-14", "08:50:39", "17:54:56", "present"),
    ("HESHAM AHMED MOHAMED MOSTAFA", "2025-10-14", "09:04:34", "20:59:12", "late"),
    ("Mohamed AHMED MOHAMED MOSTAFA", "2025-10-14", "09:24:17", "18:00:00", "late"),
    
    ("Mohamed AHMED MOHAMED MOSTAFA", "2025-10-13", "09:27:32", "18:31:37", "late"),
    ("TAREK ABDELMONEM ZAKI ALWAZAN", "2025-10-13", "09:00:37", "15:49:28", "present"),
    ("HESHAM AHMED MOHAMED MOSTAFA", "2025-10-13", "09:02:58", "17:55:49", "present"),
    ("KARIM MOHAMED MOUSTAFA ABDELMEGEUID", "2025-10-13", "08:54:37", "17:56:19", "present"),
    
    ("Hatem Mohamed Ahmed", "2025-10-12", "08:18:09", "17:00:00", "present"),
    ("Mohamed AHMED MOHAMED MOSTAFA", "2025-10-12", "09:31:25", "19:27:44", "late"),
    ("HESHAM AHMED MOHAMED MOSTAFA", "2025-10-12", "09:11:41", "17:53:54", "late"),
    ("KARIM MOHAMED MOUSTAFA ABDELMEGEUID", "2025-10-12", "08:52:00", "17:44:05", "present"),
    ("TAREK ABDELMONEM ZAKI ALWAZAN", "2025-10-12", "08:10:30", "15:39:24", "present"),
    
    ("KARIM MOHAMED MOUSTAFA ABDELMEGEUID", "2025-10-09", "08:45:41", "17:45:00", "present"),
    ("Hatem Mohamed Ahmed", "2025-10-09", "08:34:16", "17:00:00", "present"),
    ("TAREK ABDELMONEM ZAKI ALWAZAN", "2025-10-09", "08:22:56", "15:14:23", "present"),
    ("Mohamed AHMED MOHAMED MOSTAFA", "2025-10-09", "10:19:06", "18:20:31", "late"),
    ("HESHAM AHMED MOHAMED MOSTAFA", "2025-10-09", "09:08:12", "17:45:00", "late"),
    ("GEHAD MOHAMED KAMAL AHMED", "2025-10-09", "09:07:03", "11:49:40", "late"),
    
    ("Mohamed AHMED MOHAMED MOSTAFA", "2025-10-08", "09:58:00", "15:59:00", "late"),
    ("HESHAM AHMED MOHAMED MOSTAFA", "2025-10-08", "09:10:21", "17:54:40", "late"),
    ("GEHAD MOHAMED KAMAL AHMED", "2025-10-08", "08:56:01", "17:54:32", "present"),
    ("KARIM MOHAMED MOUSTAFA ABDELMEGEUID", "2025-10-08", "08:54:13", "17:39:14", "present"),
    ("Hatem Mohamed Ahmed", "2025-10-08", "08:10:16", "16:29:33", "present"),
    ("TAREK ABDELMONEM ZAKI ALWAZAN", "2025-10-08", "08:10:10", "15:24:26", "present"),
    
    ("Mohamed AHMED MOHAMED MOSTAFA", "2025-10-07", "09:16:52", "18:00:00", "late"),
    ("Hatem Mohamed Ahmed", "2025-10-07", "07:45:15", "17:50:00", "present"),
    ("TAREK ABDELMONEM ZAKI ALWAZAN", "2025-10-07", "08:24:50", "15:27:29", "present"),
    ("KARIM MOHAMED MOUSTAFA ABDELMEGEUID", "2025-10-07", "08:55:35", "17:52:11", "present"),
    ("GEHAD MOHAMED KAMAL AHMED", "2025-10-07", "09:05:06", "17:56:06", "late"),
    ("HESHAM AHMED MOHAMED MOSTAFA", "2025-10-07", "09:07:24", "17:52:00", "late"),
    
    ("Mohamed AHMED MOHAMED MOSTAFA", "2025-10-06", "10:07:03", "14:59:00", "late"),
    ("TAREK ABDELMONEM ZAKI ALWAZAN", "2025-10-06", "08:23:51", "15:32:54", "present"),
    ("Hatem Mohamed Ahmed", "2025-10-06", "08:36:33", "16:43:23", "present"),
    ("KARIM MOHAMED MOUSTAFA ABDELMEGEUID", "2025-10-06", "08:52:18", "17:50:11", "present"),
    ("GEHAD MOHAMED KAMAL AHMED", "2025-10-06", "08:58:56", "18:01:43", "present"),
    ("HESHAM AHMED MOHAMED MOSTAFA", "2025-10-06", "09:06:12", "18:00:21", "late"),
    
    ("Hatem Mohamed Ahmed", "2025-10-05", "08:31:27", "16:30:00", "present"),
    ("GEHAD MOHAMED KAMAL AHMED", "2025-10-05", "09:00:51", "17:56:12", "present"),
    ("HESHAM AHMED MOHAMED MOSTAFA", "2025-10-05", "09:04:22", "18:13:38", "late"),
    ("Mohamed AHMED MOHAMED MOSTAFA", "2025-10-05", "08:57:38", "18:04:37", "present"),
    ("KARIM MOHAMED MOUSTAFA ABDELMEGEUID", "2025-10-05", "08:44:52", "18:03:44", "present"),
    ("TAREK ABDELMONEM ZAKI ALWAZAN", "2025-10-05", "08:23:06", "15:41:46", "present"),
    
    ("HESHAM AHMED MOHAMED MOSTAFA", "2025-10-02", "10:00:48", "17:56:01", "late"),
    ("TAREK ABDELMONEM ZAKI ALWAZAN", "2025-10-02", "08:33:46", "15:32:51", "present"),
    ("Hatem Mohamed Ahmed", "2025-10-02", "08:12:26", "17:40:00", "present"),
    ("Mohamed AHMED MOHAMED MOSTAFA", "2025-10-02", "08:55:05", "17:40:09", "present"),
    ("KARIM MOHAMED MOUSTAFA ABDELMEGEUID", "2025-10-02", "09:07:15", "17:54:49", "late"),
    ("GEHAD MOHAMED KAMAL AHMED", "2025-10-02", "09:01:46", "17:55:27", "late"),
    
    ("HESHAM AHMED MOHAMED MOSTAFA", "2025-10-01", "10:15:34", "18:15:00", "late"),
    ("Mohamed AHMED MOHAMED MOSTAFA", "2025-10-01", "09:12:17", "23:12:30", "late"),
    ("Hatem Mohamed Ahmed", "2025-10-01", "08:05:35", "17:30:00", "present"),
    ("TAREK ABDELMONEM ZAKI ALWAZAN", "2025-10-01", "08:10:22", "15:07:08", "present"),
    ("GEHAD MOHAMED KAMAL AHMED", "2025-10-01", "09:00:00", "18:00:00", "present"),
    ("KARIM MOHAMED MOUSTAFA ABDELMEGEUID", "2025-10-01", "09:00:00", "18:15:00", "present"),
    
    ("Mohamed AHMED MOHAMED MOSTAFA", "2025-09-30", "08:55:29", "20:19:14", "present"),
    ("TAREK ABDELMONEM ZAKI ALWAZAN", "2025-09-30", "08:26:05", "14:04:01", "present"),
    ("Hatem Mohamed Ahmed", "2025-09-30", "07:31:25", "17:30:00", "present"),
    ("GEHAD MOHAMED KAMAL AHMED", "2025-09-30", "09:01:39", "17:58:45", "late"),
    ("KARIM MOHAMED MOUSTAFA ABDELMEGEUID", "2025-09-30", "09:08:52", "17:33:13", "late"),
    ("HESHAM AHMED MOHAMED MOSTAFA", "2025-09-30", "09:24:37", "17:58:10", "late"),
    
    ("Mohamed AHMED MOHAMED MOSTAFA", "2025-09-29", "09:59:41", "18:21:17", "late"),
    ("HESHAM AHMED MOHAMED MOSTAFA", "2025-09-29", "09:28:20", "18:46:02", "late"),
    ("KARIM MOHAMED MOUSTAFA ABDELMEGEUID", "2025-09-29", "09:07:24", "17:52:54", "late"),
    ("GEHAD MOHAMED KAMAL AHMED", "2025-09-29", "08:56:57", "18:01:00", "present"),
    ("TAREK ABDELMONEM ZAKI ALWAZAN", "2025-09-29", "08:55:14", "15:31:14", "present"),
    ("Hatem Mohamed Ahmed", "2025-09-29", "08:24:14", "17:30:00", "present"),
]

async def import_attendance():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("📥 IMPORTING REAL OCTOBER 2025 ATTENDANCE DATA")
    print("=" * 70)
    
    # Get employee ID mapping
    employees = await db.users.find({"is_active": True}).to_list(None)
    name_to_id = {}
    for emp in employees:
        # Try exact match and partial match
        name = emp["name"]
        name_to_id[name] = emp["id"]
        # Also add variations
        name_to_id[name.upper()] = emp["id"]
        name_to_id[name.lower()] = emp["id"]
    
    print(f"📋 Found {len(employees)} active employees in database")
    
    inserted = 0
    skipped = 0
    
    for emp_name, date_str, check_in, check_out, status in ATTENDANCE_DATA:
        # Find employee ID
        emp_id = None
        for db_name, db_id in name_to_id.items():
            if emp_name.lower() in db_name.lower() or db_name.lower() in emp_name.lower():
                emp_id = db_id
                break
        
        if not emp_id:
            print(f"⚠️  Could not find employee: {emp_name}")
            skipped += 1
            continue
        
        # Calculate late minutes if status is "late"
        late_minutes = 0
        is_late = False
        if status == "late" and check_in:
            # Check if after 09:00
            try:
                check_in_time = datetime.strptime(check_in, "%H:%M:%S").time()
                standard_time = datetime.strptime("09:00:00", "%H:%M:%S").time()
                if check_in_time > standard_time:
                    late_minutes = int((datetime.combine(datetime.today(), check_in_time) - 
                                      datetime.combine(datetime.today(), standard_time)).total_seconds() / 60)
                    is_late = True
            except:
                pass
        
        # Insert record
        record = {
            "id": str(uuid.uuid4()),
            "user_id": emp_id,
            "user_name": emp_name,
            "date": date_str,
            "check_in": check_in,
            "check_out": check_out,
            "status": status,
            "is_late": is_late,
            "late_minutes": late_minutes,
            "early_departure_minutes": 0,
            "deducted_hours": 0,
            "working_hours": 9.0 if check_in and check_out else 0,
            "created_at": datetime.now().isoformat()
        }
        
        # Check if already exists
        existing = await db.attendance.find_one({
            "user_id": emp_id,
            "date": date_str
        })
        
        if existing:
            # Update
            await db.attendance.replace_one(
                {"user_id": emp_id, "date": date_str},
                record
            )
        else:
            # Insert
            await db.attendance.insert_one(record)
        
        inserted += 1
    
    print(f"\n✅ Imported/Updated {inserted} attendance records")
    print(f"⚠️  Skipped {skipped} records (employee not found)")
    
    # Summary
    print(f"\n📊 October 2025 Attendance Summary:")
    for emp in employees[:6]:  # Show first 6
        count = await db.attendance.count_documents({
            "user_id": emp["id"],
            "date": {"$gte": "2025-09-29", "$lte": "2025-10-28"}
        })
        print(f"   {emp['name']}: {count} days")
    
    client.close()
    print("\n✅ Data import complete!")

asyncio.run(import_attendance())
