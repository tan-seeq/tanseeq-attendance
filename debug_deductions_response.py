#!/usr/bin/env python3
"""
Debug script to examine the actual deductions response data
"""

import requests
import json
from datetime import datetime

# Configuration
BACKEND_URL = "https://attendance-calc-4.preview.emergentagent.com/api"
TEST_CREDENTIALS = {
    "email": "admin@tanseeq.com",
    "password": "ADMIN"
}

def authenticate():
    """Authenticate and get token"""
    session = requests.Session()
    
    response = session.post(
        f"{BACKEND_URL}/auth/login",
        json=TEST_CREDENTIALS,
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        session.headers.update({
            "Authorization": f"Bearer {token}"
        })
        return session
    else:
        print(f"Authentication failed: {response.status_code} - {response.text}")
        return None

def get_deductions_data(session):
    """Get deductions data and examine it"""
    response = session.post(
        f"{BACKEND_URL}/deductions/calculate-monthly?month=2025-10",
        timeout=60
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"API call failed: {response.status_code} - {response.text}")
        return None

def main():
    print("🔍 Debugging Advanced Deductions Response Data")
    print("=" * 60)
    
    # Authenticate
    session = authenticate()
    if not session:
        return
    
    # Get deductions data
    data = get_deductions_data(session)
    if not data:
        return
    
    print(f"✅ Successfully retrieved deductions data")
    print(f"📊 Response structure:")
    print(f"   - success: {data.get('success')}")
    print(f"   - summaries count: {len(data.get('summaries', []))}")
    print(f"   - employees count: {len(data.get('employees', []))}")
    
    # Examine employees data
    employees = data.get("employees", [])
    print(f"\n👥 Employee Details:")
    
    for i, employee in enumerate(employees):
        name = employee.get("employee_name", "Unknown")
        total_deduction = employee.get("total_deduction", 0)
        absence_deduction = employee.get("absence_deduction", 0)
        daily_records = employee.get("daily_records", [])
        
        print(f"   {i+1:2d}. {name}")
        print(f"       Total Deduction: {total_deduction} AED")
        print(f"       Absence Deduction: {absence_deduction} AED")
        print(f"       Daily Records: {len(daily_records)} days")
        
        # Show first few daily records for context
        if daily_records and len(daily_records) > 0:
            print(f"       Sample Records:")
            for j, record in enumerate(daily_records[:3]):
                date = record.get("date", "Unknown")
                status = record.get("status", "Unknown")
                deduction = record.get("deduction_amount", 0)
                print(f"         - {date}: {status} (deduction: {deduction})")
            if len(daily_records) > 3:
                print(f"         ... and {len(daily_records) - 3} more records")
        
        print()
    
    # Focus on specific employees mentioned in review
    print(f"\n🎯 Focus on Review-Mentioned Employees:")
    
    target_employees = ["حاتم", "Hatem", "جهاد", "Jihad", "طارق", "Tarek", "وزان", "Wazzan"]
    
    for employee in employees:
        name = employee.get("employee_name", "")
        if any(target in name for target in target_employees):
            print(f"\n🔍 DETAILED ANALYSIS: {name}")
            print(f"   Total Deduction: {employee.get('total_deduction', 0)} AED")
            print(f"   Absence Deduction: {employee.get('absence_deduction', 0)} AED")
            
            daily_records = employee.get("daily_records", [])
            print(f"   Daily Records ({len(daily_records)} days):")
            
            absent_days = 0
            late_days = 0
            total_daily_deductions = 0
            
            for record in daily_records:
                date = record.get("date", "Unknown")
                status = record.get("status", "Unknown")
                deduction = record.get("deduction_amount", 0)
                
                if status == "absent":
                    absent_days += 1
                elif status == "late":
                    late_days += 1
                
                total_daily_deductions += deduction
                
                print(f"     {date}: {status} (deduction: {deduction} AED)")
            
            print(f"   Summary:")
            print(f"     - Absent days: {absent_days}")
            print(f"     - Late days: {late_days}")
            print(f"     - Total daily deductions: {total_daily_deductions} AED")
            print(f"     - Reported total deduction: {employee.get('total_deduction', 0)} AED")
            
            # Check if there's a mismatch
            if abs(total_daily_deductions - employee.get('total_deduction', 0)) > 0.01:
                print(f"     ⚠️  MISMATCH: Daily sum ({total_daily_deductions}) != Total ({employee.get('total_deduction', 0)})")
    
    # Save full response for analysis
    with open("/app/debug_deductions_full_response.json", "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Full response saved to debug_deductions_full_response.json")

if __name__ == "__main__":
    main()