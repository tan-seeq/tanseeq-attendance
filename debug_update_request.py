#!/usr/bin/env python3
"""
Debug the update request to see what's happening
"""

import requests
import json

# Configuration
BASE_URL = "https://tanseeq-hr-3.preview.emergentagent.com/api"
TEST_ACCOUNT = {"email": "admin@tanseeq.com", "password": "ADMIN"}

def debug_update_request():
    session = requests.Session()
    
    # Authenticate
    response = session.post(f"{BASE_URL}/auth/login", json=TEST_ACCOUNT)
    if response.status_code != 200:
        print(f"❌ Authentication failed: {response.status_code}")
        return
    
    token = response.json()["access_token"]
    session.headers.update({"Authorization": f"Bearer {token}"})
    print("✅ Authentication successful")
    
    # Get payroll cycles
    response = session.get(f"{BASE_URL}/payroll/cycles")
    cycles_data = response.json()
    if isinstance(cycles_data, list):
        cycles = cycles_data
    else:
        cycles = cycles_data.get('cycles', [])
    
    cycle_id = cycles[0].get('id')
    print(f"📋 Using cycle ID: {cycle_id}")
    
    # Get cycle summary BEFORE update
    response = session.get(f"{BASE_URL}/payroll/cycles/{cycle_id}/summary")
    summary_data = response.json()
    employees = summary_data.get('employee_summaries', [])
    test_employee = employees[0]
    employee_id = test_employee['employee_id']
    
    print(f"👤 Employee ID: {employee_id}")
    print(f"💰 BEFORE - manual_deductions: {test_employee.get('manual_deductions', 0)}")
    print(f"💰 BEFORE - base_salary: {test_employee.get('base_salary', 0)}")
    print(f"💰 BEFORE - total_deductions: {test_employee.get('total_deductions', 0)}")
    print(f"💰 BEFORE - net_salary: {test_employee.get('net_salary', 0)}")
    
    # Prepare update data with ALL required fields
    update_data = {
        "employees": [
            {
                "employee_id": employee_id,
                "base_salary": test_employee.get('base_salary', 0),  # Keep existing
                "allowances": test_employee.get('total_allowances', 0),  # Keep existing
                "manual_deductions": 75.25,  # NEW VALUE
                "attendance_deductions": test_employee.get('attendance_deductions', 0),  # Keep existing
                "advance_deductions": test_employee.get('advance_deductions', 0)  # Keep existing
            }
        ]
    }
    
    print(f"📤 Sending update data:")
    print(json.dumps(update_data, indent=2))
    
    # Send update request
    response = session.put(f"{BASE_URL}/payroll/cycles/{cycle_id}/update-employees", json=update_data)
    print(f"📊 Update response status: {response.status_code}")
    
    if response.status_code == 200:
        print(f"✅ Update successful: {response.json()}")
    else:
        print(f"❌ Update failed: {response.text}")
        return
    
    # Get cycle summary AFTER update
    response = session.get(f"{BASE_URL}/payroll/cycles/{cycle_id}/summary")
    updated_summary = response.json()
    updated_employees = updated_summary.get('employee_summaries', [])
    
    # Find the same employee
    updated_employee = None
    for emp in updated_employees:
        if emp.get('employee_id') == employee_id:
            updated_employee = emp
            break
    
    if updated_employee:
        print(f"💰 AFTER - manual_deductions: {updated_employee.get('manual_deductions', 0)}")
        print(f"💰 AFTER - base_salary: {updated_employee.get('base_salary', 0)}")
        print(f"💰 AFTER - total_deductions: {updated_employee.get('total_deductions', 0)}")
        print(f"💰 AFTER - net_salary: {updated_employee.get('net_salary', 0)}")
        
        # Check if manual_deductions was saved
        if abs(updated_employee.get('manual_deductions', 0) - 75.25) < 0.01:
            print("🎉 ✅ MANUAL DEDUCTIONS SAVED SUCCESSFULLY!")
        else:
            print("💥 ❌ MANUAL DEDUCTIONS NOT SAVED!")
    else:
        print("❌ Employee not found in updated summary")

if __name__ == "__main__":
    debug_update_request()