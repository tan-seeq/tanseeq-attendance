#!/usr/bin/env python3
"""
Debug script to investigate Advanced Attendance Deductions System API responses
"""

import requests
import json
from datetime import datetime

# Configuration
BACKEND_URL = "https://hrapp-tanseeq.emergent.host/api"
SUPER_ADMIN_EMAIL = "admin@tanseeq.com"
SUPER_ADMIN_PASSWORD = "ADMIN"

def authenticate():
    """Authenticate and return session"""
    session = requests.Session()
    
    login_data = {
        "email": SUPER_ADMIN_EMAIL,
        "password": SUPER_ADMIN_PASSWORD
    }
    
    response = session.post(f"{BACKEND_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        data = response.json()
        auth_token = data.get("access_token")
        session.headers.update({"Authorization": f"Bearer {auth_token}"})
        print("✅ Authentication successful")
        return session
    else:
        print(f"❌ Authentication failed: {response.status_code}")
        return None

def debug_monthly_calculation():
    """Debug monthly calculation endpoint"""
    session = authenticate()
    if not session:
        return
    
    print("\n🔍 DEBUGGING MONTHLY CALCULATION ENDPOINT")
    print("=" * 50)
    
    response = session.post(f"{BACKEND_URL}/deductions/calculate-monthly?month=2025-10")
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    
    try:
        data = response.json()
        print(f"Response Keys: {list(data.keys())}")
        
        if "employees" in data:
            employees = data["employees"]
            print(f"Number of employees: {len(employees)}")
            
            if employees:
                first_employee = employees[0]
                print(f"First employee keys: {list(first_employee.keys())}")
                
                if "daily_breakdown" in first_employee:
                    daily_breakdown = first_employee["daily_breakdown"]
                    print(f"Daily breakdown records: {len(daily_breakdown)}")
                    
                    if daily_breakdown:
                        first_record = daily_breakdown[0]
                        print(f"First daily record keys: {list(first_record.keys())}")
                        print(f"Sample record: {json.dumps(first_record, indent=2, default=str)}")
        
        if "cycle" in data:
            cycle = data["cycle"]
            print(f"Cycle info: {json.dumps(cycle, indent=2, default=str)}")
        
        # Save full response for analysis
        with open("/app/debug_monthly_response.json", "w") as f:
            json.dump(data, f, indent=2, default=str)
        print("💾 Full response saved to debug_monthly_response.json")
        
    except Exception as e:
        print(f"❌ Error parsing response: {e}")
        print(f"Raw response: {response.text[:500]}...")

def debug_custom_period():
    """Debug custom period endpoint"""
    session = authenticate()
    if not session:
        return
    
    print("\n🔍 DEBUGGING CUSTOM PERIOD ENDPOINT")
    print("=" * 50)
    
    params = {
        "mode": "custom",
        "from_date": "2025-10-01",
        "to_date": "2025-10-14"
    }
    
    response = session.post(f"{BACKEND_URL}/deductions/calculate", params=params)
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    
    try:
        data = response.json()
        print(f"Response Keys: {list(data.keys())}")
        
        # Save full response for analysis
        with open("/app/debug_custom_period_response.json", "w") as f:
            json.dump(data, f, indent=2, default=str)
        print("💾 Full response saved to debug_custom_period_response.json")
        
    except Exception as e:
        print(f"❌ Error parsing response: {e}")
        print(f"Raw response: {response.text[:500]}...")

def debug_apply_deductions():
    """Debug apply deductions endpoint"""
    session = authenticate()
    if not session:
        return
    
    print("\n🔍 DEBUGGING APPLY DEDUCTIONS ENDPOINT")
    print("=" * 50)
    
    # First get calculation data
    calc_response = session.post(f"{BACKEND_URL}/deductions/calculate-monthly?month=2025-10")
    if calc_response.status_code != 200:
        print(f"❌ Cannot get calculation data: {calc_response.status_code}")
        return
    
    calc_data = calc_response.json()
    employees = calc_data.get("employees", [])
    
    # Test apply endpoint
    apply_data = {
        "month": "2025-10",
        "employees": employees,
        "notes": "Debug test application"
    }
    
    response = session.post(f"{BACKEND_URL}/deductions/apply-monthly", json=apply_data)
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    
    try:
        data = response.json()
        print(f"Response Keys: {list(data.keys())}")
        print(f"Response: {json.dumps(data, indent=2, default=str)}")
        
        # Save full response for analysis
        with open("/app/debug_apply_response.json", "w") as f:
            json.dump(data, f, indent=2, default=str)
        print("💾 Full response saved to debug_apply_response.json")
        
    except Exception as e:
        print(f"❌ Error parsing response: {e}")
        print(f"Raw response: {response.text[:500]}...")

if __name__ == "__main__":
    debug_monthly_calculation()
    debug_custom_period()
    debug_apply_deductions()