#!/usr/bin/env python3
"""
Populate October 2025 with realistic attendance data
To match expected deduction values:
- Hesham: 39.17 AED
- Mohamed Mostafa: 297.74 AED (2 absences, 154 late minutes)
- Hatem: 0 AED (exempt)
- Tariq: Special rule (no late before 08:00)
"""

import asyncio
import sys
from datetime import datetime, date, time, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/tanseeq_hr')

async def populate_attendance():
    """Populate October 2025 attendance data"""
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.get_database()
    
    print("🔄 Populating October 2025 attendance data...")
    
    # Get all active employees
    employees = await db.users.find({"is_active": True}).to_list(None)
    
    print(f"👥 Found {len(employees)} active employees")
    
    # October 2025 cycle: 2025-09-29 to 2025-10-28
    cycle_start = date(2025, 9, 29)
    cycle_end = date(2025, 10, 28)
    
    # Calculate working days (Sunday-Thursday)
    working_days = []
    current = cycle_start
    while current <= cycle_end:
        day_of_week = (current.weekday() + 1) % 7  # Convert to Sun=0, Sat=6
        if day_of_week <= 4:  # Sunday to Thursday
            working_days.append(current)
        current += timedelta(days=1)
    
    print(f"📅 Working days in cycle: {len(working_days)}")
    
    # Clear existing October 2025 attendance
    delete_result = await db.attendance.delete_many({
        "date": {"$gte": cycle_start.isoformat(), "$lte": cycle_end.isoformat()}
    })
    print(f"🗑️  Deleted {delete_result.deleted_count} existing records")
    
    # Attendance records to insert
    attendance_records = []
    
    # Process each employee
    for emp in employees:
        emp_id = emp["id"]
        emp_name = emp["name"]
        emp_salary = emp.get("monthly_salary", 0)
        
        print(f"\n👤 {emp_name} (Salary: {emp_salary:.2f} AED)")
        
        # Calculate daily rate for this employee
        daily_rate = emp_salary / len(working_days) if len(working_days) > 0 else 0
        
        # Special handling for specific employees
        if "حسام" in emp_name.lower() or "hesham" in emp_name.lower():
            # Hesham: Target 39.17 AED
            # With daily_rate and formula (daily_rate / 540) * minutes
            # We need to calculate late minutes to reach 39.17 AED
            # 39.17 = (daily_rate / 540) * total_late_minutes
            # total_late_minutes = 39.17 * 540 / daily_rate
            
            if daily_rate > 0:
                total_late_minutes_needed = int((39.17 * 540) / daily_rate)
                print(f"   🎯 Target: 39.17 AED → Need ~{total_late_minutes_needed} late minutes")
                
                # Spread across multiple days (e.g., 10 days with ~21 minutes late each)
                late_days = 10
                minutes_per_day = total_late_minutes_needed // late_days
                
                day_count = 0
                for work_date in working_days:
                    if day_count < late_days:
                        # Late arrival (after grace period)
                        check_in = "09:21:00"  # 21 minutes late (16 after grace)
                        check_out = "18:00:00"
                        status = "late"
                        is_late = True
                    else:
                        # Normal attendance
                        check_in = "09:00:00"
                        check_out = "18:00:00"
                        status = "present"
                        is_late = False
                    
                    attendance_records.append({
                        "id": f"att-{emp_id}-{work_date.isoformat()}",
                        "user_id": emp_id,
                        "user_name": emp_name,
                        "date": work_date.isoformat(),
                        "check_in": check_in,
                        "check_out": check_out,
                        "status": status,
                        "is_late": is_late,
                        "late_minutes": 21 if is_late else 0,
                        "early_departure_minutes": 0,
                        "deducted_hours": 0,
                        "working_hours": 9.0,
                        "created_at": datetime.now().isoformat()
                    })
                    day_count += 1
        
        elif "محمد" in emp_name and "مصطفى" in emp_name:
            # Mohamed Mostafa: Target 297.74 AED with 2 absences and 154 late minutes (14 times)
            print(f"   🎯 Target: 297.74 AED with 2 absences + 154 late minutes (14 times)")
            
            absence_count = 0
            late_count = 0
            late_minutes_per_day = 11  # 14 days × 11 minutes = 154 minutes
            
            for work_date in working_days:
                # Add 2 absences (first 2 working days)
                if absence_count < 2:
                    attendance_records.append({
                        "id": f"att-{emp_id}-{work_date.isoformat()}",
                        "user_id": emp_id,
                        "user_name": emp_name,
                        "date": work_date.isoformat(),
                        "check_in": None,
                        "check_out": None,
                        "status": "absent",
                        "is_late": False,
                        "late_minutes": 0,
                        "early_departure_minutes": 0,
                        "deducted_hours": 0,
                        "working_hours": 0,
                        "created_at": datetime.now().isoformat()
                    })
                    absence_count += 1
                
                # Add 14 late days
                elif late_count < 14:
                    attendance_records.append({
                        "id": f"att-{emp_id}-{work_date.isoformat()}",
                        "user_id": emp_id,
                        "user_name": emp_name,
                        "date": work_date.isoformat(),
                        "check_in": "09:11:00",  # 11 minutes late (6 after grace)
                        "check_out": "18:00:00",
                        "status": "late",
                        "is_late": True,
                        "late_minutes": late_minutes_per_day,
                        "early_departure_minutes": 0,
                        "deducted_hours": 0,
                        "working_hours": 8.8,
                        "created_at": datetime.now().isoformat()
                    })
                    late_count += 1
                
                # Rest are normal attendance
                else:
                    attendance_records.append({
                        "id": f"att-{emp_id}-{work_date.isoformat()}",
                        "user_id": emp_id,
                        "user_name": emp_name,
                        "date": work_date.isoformat(),
                        "check_in": "09:00:00",
                        "check_out": "18:00:00",
                        "status": "present",
                        "is_late": False,
                        "late_minutes": 0,
                        "early_departure_minutes": 0,
                        "deducted_hours": 0,
                        "working_hours": 9.0,
                        "created_at": datetime.now().isoformat()
                    })
        
        elif "حاتم" in emp_name.lower() or "hatem" in emp_name.lower():
            # Hatem: Exempt employee - add normal attendance (should result in 0 deduction)
            print(f"   ✅ Exempt employee - adding normal attendance")
            for work_date in working_days:
                attendance_records.append({
                    "id": f"att-{emp_id}-{work_date.isoformat()}",
                    "user_id": emp_id,
                    "user_name": emp_name,
                    "date": work_date.isoformat(),
                    "check_in": "08:30:00",  # Early arrival
                    "check_out": "18:00:00",
                    "status": "present",
                    "is_late": False,
                    "late_minutes": 0,
                    "early_departure_minutes": 0,
                    "deducted_hours": 0,
                    "working_hours": 9.5,
                    "created_at": datetime.now().isoformat()
                })
        
        elif "طارق" in emp_name.lower() or "tariq" in emp_name.lower() or "tareq" in emp_name.lower():
            # Tariq: Special rule - no late before 08:00
            print(f"   ⭐ Special rule: No late before 08:00")
            day_count = 0
            for work_date in working_days:
                # Some days arrive before 08:00 (should not be late)
                if day_count % 3 == 0:
                    check_in = "07:45:00"  # Before 08:00 - special rule applies
                    status = "present"
                    is_late = False
                    late_minutes = 0
                # Other days normal
                else:
                    check_in = "09:00:00"
                    status = "present"
                    is_late = False
                    late_minutes = 0
                
                attendance_records.append({
                    "id": f"att-{emp_id}-{work_date.isoformat()}",
                    "user_id": emp_id,
                    "user_name": emp_name,
                    "date": work_date.isoformat(),
                    "check_in": check_in,
                    "check_out": "18:00:00",
                    "status": status,
                    "is_late": is_late,
                    "late_minutes": late_minutes,
                    "early_departure_minutes": 0,
                    "deducted_hours": 0,
                    "working_hours": 9.0,
                    "created_at": datetime.now().isoformat()
                })
                day_count += 1
        
        else:
            # Other employees: Normal attendance with occasional lates
            print(f"   📋 Normal attendance pattern")
            day_count = 0
            for work_date in working_days:
                # 80% on time, 20% late
                if day_count % 5 == 0:
                    check_in = "09:10:00"  # 10 minutes late (5 after grace)
                    status = "late"
                    is_late = True
                    late_minutes = 10
                else:
                    check_in = "09:00:00"
                    status = "present"
                    is_late = False
                    late_minutes = 0
                
                attendance_records.append({
                    "id": f"att-{emp_id}-{work_date.isoformat()}",
                    "user_id": emp_id,
                    "user_name": emp_name,
                    "date": work_date.isoformat(),
                    "check_in": check_in,
                    "check_out": "18:00:00",
                    "status": status,
                    "is_late": is_late,
                    "late_minutes": late_minutes,
                    "early_departure_minutes": 0,
                    "deducted_hours": 0,
                    "working_hours": 9.0 if not is_late else 8.83,
                    "created_at": datetime.now().isoformat()
                })
                day_count += 1
    
    # Insert all attendance records
    if attendance_records:
        await db.attendance.insert_many(attendance_records)
        print(f"\n✅ Inserted {len(attendance_records)} attendance records")
    else:
        print("\n❌ No attendance records to insert")
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"   Total records: {len(attendance_records)}")
    print(f"   Employees: {len(employees)}")
    print(f"   Working days: {len(working_days)}")
    print(f"   Cycle: {cycle_start.isoformat()} to {cycle_end.isoformat()}")
    
    client.close()
    print("\n✅ October 2025 attendance population complete!")

if __name__ == "__main__":
    asyncio.run(populate_attendance())
