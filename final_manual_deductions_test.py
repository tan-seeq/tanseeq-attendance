#!/usr/bin/env python3
"""
Final comprehensive test for manual deductions persistence
"""

import requests
import json
import time

# Configuration
BASE_URL = "https://hr-system-upgrade.preview.emergentagent.com/api"
TEST_ACCOUNT = {"email": "admin@tanseeq.com", "password": "ADMIN"}

def test_manual_deductions_fix():
    session = requests.Session()
    
    # Authenticate
    response = session.post(f"{BASE_URL}/auth/login", json=TEST_ACCOUNT)
    if response.status_code != 200:
        print("❌ STILL BROKEN - Authentication failed")
        return False
    
    token = response.json()["access_token"]
    session.headers.update({"Authorization": f"Bearer {token}"})
    print("✅ Authentication successful")
    
    # Step 1: GET /api/payroll/cycles → save first cycle_id
    print("\n1️⃣ Getting payroll cycles...")
    response = session.get(f"{BASE_URL}/payroll/cycles")
    if response.status_code != 200:
        print("❌ STILL BROKEN - Failed to get payroll cycles")
        return False
    
    cycles_data = response.json()
    if isinstance(cycles_data, list):
        cycles = cycles_data
    else:
        cycles = cycles_data.get('cycles', [])
    
    if not cycles:
        print("❌ STILL BROKEN - No payroll cycles found")
        return False
    
    cycle_id = cycles[0].get('id')
    print(f"   📋 Found cycle ID: {cycle_id}")
    
    # Step 2: GET /api/payroll/cycles/{cycle_id}/summary → save first employee and current manual_deductions
    print("2️⃣ Getting payroll cycle summary...")
    response = session.get(f"{BASE_URL}/payroll/cycles/{cycle_id}/summary")
    if response.status_code != 200:
        print("❌ STILL BROKEN - Failed to get cycle summary")
        return False
    
    summary_data = response.json()
    employees = summary_data.get('employee_summaries', [])
    if not employees:
        print("❌ STILL BROKEN - No employees found in summary")
        return False
    
    # Use the first employee
    test_employee = employees[0]
    employee_id = test_employee['employee_id']
    original_manual_deductions = test_employee.get('manual_deductions', 0)
    
    print(f"   👤 Test employee ID: {employee_id}")
    print(f"   💰 Original manual_deductions: {original_manual_deductions}")
    
    # Step 3: PUT /api/payroll/cycles/{cycle_id}/update-employees with manual_deductions = 75.25
    print("3️⃣ Updating manual deductions to 75.25...")
    
    # Prepare complete update data
    update_data = {
        "employees": [
            {
                "employee_id": employee_id,
                "base_salary": 2700,  # Known base salary for Jihad
                "allowances": 0,
                "manual_deductions": 75.25,  # TARGET VALUE
                "attendance_deductions": 0,
                "advance_deductions": 700.0  # Known advance deduction
            }
        ]
    }
    
    print(f"   📤 Sending update data: {json.dumps(update_data, indent=2)}")
    
    response = session.put(f"{BASE_URL}/payroll/cycles/{cycle_id}/update-employees", json=update_data)
    print(f"   📊 Update response status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ STILL BROKEN - Failed to update employee: {response.status_code}")
        print(f"   Response: {response.text}")
        return False
    
    update_result = response.json()
    print(f"   ✅ Update successful: {update_result}")
    
    # Wait for processing
    print("   ⏳ Waiting 3 seconds for processing...")
    time.sleep(3)
    
    # Step 4: GET /api/payroll/cycles/{cycle_id}/summary again → verify manual_deductions = 75.25
    print("4️⃣ Verifying manual deductions persistence...")
    response = session.get(f"{BASE_URL}/payroll/cycles/{cycle_id}/summary")
    if response.status_code != 200:
        print("❌ STILL BROKEN - Failed to get updated summary")
        return False
    
    updated_summary = response.json()
    updated_employees = updated_summary.get('employee_summaries', [])
    
    # Find the same employee
    updated_employee = None
    for emp in updated_employees:
        if emp.get('employee_id') == employee_id:
            updated_employee = emp
            break
    
    if not updated_employee:
        print("❌ STILL BROKEN - Employee not found in updated summary")
        return False
    
    updated_manual_deductions = updated_employee.get('manual_deductions', 0)
    updated_total_deductions = updated_employee.get('total_deductions', 0)
    updated_net_salary = updated_employee.get('net_salary', 0)
    
    print(f"   💰 Updated manual_deductions: {updated_manual_deductions}")
    print(f"   💰 Updated total_deductions: {updated_total_deductions}")
    print(f"   💰 Updated net_salary: {updated_net_salary}")
    
    # Verify the fix
    if abs(updated_manual_deductions - 75.25) < 0.01:
        print("\n🎉 ✅ FIXED")
        print(f"   Before: {original_manual_deductions}")
        print(f"   After:  {updated_manual_deductions}")
        print("   Manual deductions are now properly saved and persist after reload!")
        return True
    else:
        print("\n💥 ❌ STILL BROKEN")
        print(f"   Before: {original_manual_deductions}")
        print(f"   After:  {updated_manual_deductions}")
        print(f"   Expected: 75.25")
        print("   Manual deductions are NOT being saved properly!")
        return False

if __name__ == "__main__":
    print("🚀 Final Manual Deductions Persistence Fix Test")
    print("=" * 60)
    
    success = test_manual_deductions_fix()
    
    print("\n" + "=" * 60)
    if success:
        print("🎯 FINAL RESULT: ✅ FIXED")
    else:
        print("🎯 FINAL RESULT: ❌ STILL BROKEN")
    print("=" * 60)