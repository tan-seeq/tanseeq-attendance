#!/usr/bin/env python3
"""
Debug script to check database updates directly
"""

import requests
import json
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import os

# Configuration
BACKEND_URL = "https://hr-unification.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
    "email": "admin@tanseeq.com",
    "password": "ADMIN"
}

async def check_database_directly():
    """Check MongoDB directly"""
    # Connect to MongoDB
    mongo_url = "mongodb://localhost:27017"
    client = AsyncIOMotorClient(mongo_url)
    db = client["tanseeq_hr"]
    
    cycle_id = "026ce2ba-4471-482c-ac03-dbb8353ac13f"
    employee_id = "eed6d28b-7639-4d31-9386-4e99b9179d8f"
    
    print("🔍 Checking database directly...")
    
    # Check employee_payroll_summaries collection
    summary = await db.employee_payroll_summaries.find_one({
        "payroll_cycle_id": cycle_id,
        "employee_id": employee_id
    })
    
    if summary:
        print(f"📋 Employee Summary in Database:")
        print(f"   Employee: {summary.get('employee_name')}")
        print(f"   Manual Deductions: {summary.get('manual_deductions')}")
        print(f"   Base Salary: {summary.get('base_salary')}")
        print(f"   Total Deductions: {summary.get('total_deductions')}")
        print(f"   Net Salary: {summary.get('net_salary')}")
        print(f"   Updated At: {summary.get('updated_at')}")
    else:
        print("❌ No employee summary found in database")
    
    # Close connection
    client.close()

def test_api_update():
    """Test the API update"""
    session = requests.Session()
    
    # Authenticate
    response = session.post(f"{BACKEND_URL}/auth/login", json=ADMIN_CREDENTIALS)
    if response.status_code != 200:
        print(f"Authentication failed: {response.text}")
        return
    
    token = response.json().get("access_token")
    session.headers.update({"Authorization": f"Bearer {token}"})
    
    cycle_id = "026ce2ba-4471-482c-ac03-dbb8353ac13f"
    employee_id = "eed6d28b-7639-4d31-9386-4e99b9179d8f"
    
    print("🔄 Testing API update...")
    
    # Get current state
    response = session.get(f"{BACKEND_URL}/payroll/cycles/{cycle_id}/summary")
    if response.status_code == 200:
        summary = response.json()
        employees = summary.get("employee_summaries", [])
        target_employee = None
        for emp in employees:
            if emp.get("employee_id") == employee_id:
                target_employee = emp
                break
        
        if target_employee:
            print(f"📋 Before Update:")
            print(f"   Manual Deductions: {target_employee.get('manual_deductions')}")
            print(f"   Base Salary: {target_employee.get('base_salary')}")
    
    # Try update with a different value
    test_value = 150.75
    update_payload = {
        "employees": [{
            "employee_id": employee_id,
            "base_salary": 2700.0,
            "allowances": 0,
            "manual_deductions": test_value,
            "attendance_deductions": 0,
            "advance_deductions": 700.0  # Keep existing advance deductions
        }]
    }
    
    response = session.put(
        f"{BACKEND_URL}/payroll/cycles/{cycle_id}/update-employees",
        json=update_payload
    )
    
    print(f"🔄 Update Response: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   Message: {result.get('message')}")
        print(f"   Updated Count: {result.get('updated_count')}")
    else:
        print(f"   Error: {response.text}")
    
    # Check after update
    response = session.get(f"{BACKEND_URL}/payroll/cycles/{cycle_id}/summary")
    if response.status_code == 200:
        summary = response.json()
        employees = summary.get("employee_summaries", [])
        target_employee = None
        for emp in employees:
            if emp.get("employee_id") == employee_id:
                target_employee = emp
                break
        
        if target_employee:
            print(f"📋 After Update:")
            print(f"   Manual Deductions: {target_employee.get('manual_deductions')}")
            print(f"   Expected: {test_value}")
            print(f"   Match: {'✅' if target_employee.get('manual_deductions') == test_value else '❌'}")

async def main():
    print("🔍 Database Update Debug Test")
    print("=" * 50)
    
    # Test API first
    test_api_update()
    
    print("\n" + "=" * 50)
    
    # Check database directly
    await check_database_directly()

if __name__ == "__main__":
    asyncio.run(main())