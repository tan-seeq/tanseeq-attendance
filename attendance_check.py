#!/usr/bin/env python3
"""
Check attendance records for October 2025 to understand the data discrepancy
"""

import asyncio
import aiohttp
import json

# Backend URL from environment
BACKEND_URL = "https://hr-attendance-system.preview.emergentagent.com/api"

# Test credentials
ADMIN_CREDENTIALS = {"email": "admin@tanseeq.com", "password": "ADMIN"}

async def check_attendance_data():
    """Check attendance records for October 2025"""
    
    async with aiohttp.ClientSession() as session:
        # Authenticate
        async with session.post(f"{BACKEND_URL}/auth/login", json=ADMIN_CREDENTIALS) as response:
            if response.status != 200:
                print(f"❌ Authentication failed: {response.status}")
                return
            
            data = await response.json()
            token = data["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
        
        # Get attendance records
        async with session.get(f"{BACKEND_URL}/attendance", headers=headers) as response:
            if response.status == 200:
                attendance_data = await response.json()
                print(f"📊 Total attendance records: {len(attendance_data)}")
                
                # Filter for October 2025 cycle (2025-09-29 to 2025-10-28)
                october_records = []
                for record in attendance_data:
                    date = record.get("date", "")
                    if "2025-09-29" <= date <= "2025-10-28":
                        october_records.append(record)
                
                print(f"📅 October 2025 cycle records: {len(october_records)}")
                
                # Group by employee
                employee_records = {}
                for record in october_records:
                    emp_name = record.get("user_name", "Unknown")
                    if emp_name not in employee_records:
                        employee_records[emp_name] = []
                    employee_records[emp_name].append(record)
                
                print(f"\n👥 Employees with October 2025 attendance:")
                for emp_name, records in employee_records.items():
                    present_days = len([r for r in records if r.get("status") != "absent"])
                    absent_days = len([r for r in records if r.get("status") == "absent"])
                    late_days = len([r for r in records if r.get("is_late", False)])
                    
                    print(f"   {emp_name}: {len(records)} records ({present_days} present, {absent_days} absent, {late_days} late)")
                    
                    # Check for specific employees
                    if any(name in emp_name.lower() for name in ["hesham", "حسام"]):
                        print(f"      🔍 HESHAM FOUND: {len(records)} records")
                        for record in records[:3]:  # Show first 3 records
                            print(f"         {record.get('date')}: {record.get('status')} - Check-in: {record.get('check_in')} - Late: {record.get('is_late', False)}")
                    
                    if any(name in emp_name.lower() for name in ["mohamed", "محمد", "mostafa", "مصطفى"]):
                        print(f"      🔍 MOHAMED FOUND: {len(records)} records")
                        for record in records[:3]:  # Show first 3 records
                            print(f"         {record.get('date')}: {record.get('status')} - Check-in: {record.get('check_in')} - Late: {record.get('is_late', False)}")
                
                # Save detailed data
                with open("/app/october_attendance_analysis.json", "w", encoding="utf-8") as f:
                    json.dump({
                        "total_records": len(attendance_data),
                        "october_records": len(october_records),
                        "employee_summary": {emp: len(records) for emp, records in employee_records.items()},
                        "detailed_records": october_records[:50]  # First 50 records for analysis
                    }, f, indent=2, ensure_ascii=False)
                
                print(f"\n📁 Detailed analysis saved to: /app/october_attendance_analysis.json")
                
            else:
                print(f"❌ Failed to get attendance records: {response.status}")

if __name__ == "__main__":
    asyncio.run(check_attendance_data())