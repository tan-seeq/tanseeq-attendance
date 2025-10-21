#!/usr/bin/env python3
"""
Debug with delay to check if it's a timing issue
"""

import requests
import json
import time

# Configuration
BASE_URL = "https://timecalc-hr.preview.emergentagent.com/api"
TEST_ACCOUNT = {"email": "admin@tanseeq.com", "password": "ADMIN"}

def debug_with_delay():
    session = requests.Session()
    
    # Authenticate
    response = session.post(f"{BASE_URL}/auth/login", json=TEST_ACCOUNT)
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
    employee_id = "eed6d28b-7639-4d31-9386-4e99b9179d8f"
    
    print(f"📋 Using cycle ID: {cycle_id}")
    print(f"👤 Employee ID: {employee_id}")
    
    # Update with manual deductions = 88.88 (different value to be sure)
    update_data = {
        "employees": [
            {
                "employee_id": employee_id,
                "base_salary": 2700,  # Use actual base salary
                "allowances": 0,
                "manual_deductions": 88.88,  # NEW TEST VALUE
                "attendance_deductions": 0,
                "advance_deductions": 700.0
            }
        ]
    }
    
    print(f"📤 Updating manual_deductions to 88.88...")
    response = session.put(f"{BASE_URL}/payroll/cycles/{cycle_id}/update-employees", json=update_data)
    print(f"📊 Update response: {response.status_code}")
    
    if response.status_code == 200:
        print(f"✅ Update response: {response.json()}")
        
        # Wait a bit for any async processing
        print("⏳ Waiting 3 seconds...")
        time.sleep(3)
        
        # Check multiple times
        for i in range(3):
            print(f"\n🔍 Check #{i+1}:")
            response = session.get(f"{BASE_URL}/payroll/cycles/{cycle_id}/summary")
            summary_data = response.json()
            employees = summary_data.get('employee_summaries', [])
            
            # Find our employee
            test_employee = None
            for emp in employees:
                if emp.get('employee_id') == employee_id:
                    test_employee = emp
                    break
            
            if test_employee:
                manual_ded = test_employee.get('manual_deductions', 0)
                total_ded = test_employee.get('total_deductions', 0)
                net_salary = test_employee.get('net_salary', 0)
                
                print(f"   💰 manual_deductions: {manual_ded}")
                print(f"   💰 total_deductions: {total_ded}")
                print(f"   💰 net_salary: {net_salary}")
                
                if abs(manual_ded - 88.88) < 0.01:
                    print("   🎉 ✅ FOUND THE SAVED VALUE!")
                    return True
                else:
                    print("   ❌ Still not saved")
            
            if i < 2:  # Don't wait after the last check
                time.sleep(2)
        
        print("\n💥 ❌ MANUAL DEDUCTIONS STILL NOT SAVED AFTER MULTIPLE CHECKS!")
        return False
    else:
        print(f"❌ Update failed: {response.text}")
        return False

if __name__ == "__main__":
    debug_with_delay()