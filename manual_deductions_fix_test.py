#!/usr/bin/env python3
"""
اختبار سريع: التحقق من إصلاح حفظ التعديلات
Quick Test: Verify manual deductions save fix

Testing the specific issue mentioned in Arabic review:
1. GET /api/payroll/cycles → save first cycle_id
2. GET /api/payroll/cycles/{cycle_id}/summary → save first employee and current manual_deductions value
3. PUT /api/payroll/cycles/{cycle_id}/update-employees with manual_deductions = 75.25
4. GET /api/payroll/cycles/{cycle_id}/summary again → verify manual_deductions = 75.25

Expected output:
- ✅ FIXED if successful
- ❌ STILL BROKEN if failed
- Print values before and after
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "https://tanseeq-hr-fix.preview.emergentagent.com/api"

# Test account - Super Admin
TEST_ACCOUNT = {"email": "admin@tanseeq.com", "password": "ADMIN"}

class ManualDeductionsFixTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        
    def authenticate(self):
        """Authenticate and get JWT token"""
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", json=TEST_ACCOUNT)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                print(f"✅ Authentication successful: {TEST_ACCOUNT['email']}")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication exception: {str(e)}")
            return False
    
    def test_manual_deductions_persistence(self):
        """Test the specific manual deductions save issue"""
        print("\n🔍 Testing Manual Deductions Persistence Fix...")
        print("=" * 50)
        
        try:
            # Step 1: GET /api/payroll/cycles → save first cycle_id
            print("1️⃣ Getting payroll cycles...")
            response = self.session.get(f"{BASE_URL}/payroll/cycles")
            
            if response.status_code != 200:
                print(f"❌ STILL BROKEN - Failed to get payroll cycles: {response.status_code}")
                return False
            
            cycles_data = response.json()
            
            # Handle both list and object formats
            if isinstance(cycles_data, list):
                cycles = cycles_data
            else:
                cycles = cycles_data.get('cycles', [])
            
            if not cycles:
                print("❌ STILL BROKEN - No payroll cycles found")
                return False
            
            cycle_id = cycles[0].get('id')
            if not cycle_id:
                print("❌ STILL BROKEN - No cycle ID found")
                return False
            
            print(f"   📋 Found cycle ID: {cycle_id}")
            
            # Step 2: GET /api/payroll/cycles/{cycle_id}/summary → save first employee and current manual_deductions
            print("2️⃣ Getting payroll cycle summary...")
            response = self.session.get(f"{BASE_URL}/payroll/cycles/{cycle_id}/summary")
            
            if response.status_code != 200:
                print(f"❌ STILL BROKEN - Failed to get cycle summary: {response.status_code}")
                return False
            
            summary_data = response.json()
            
            # Find first employee with manual_deductions field
            employees = summary_data.get('employee_summaries', [])
            if not employees:
                print("❌ STILL BROKEN - No employees found in summary")
                return False
            
            test_employee = None
            for emp in employees:
                if 'employee_id' in emp:
                    test_employee = emp
                    break
            
            if not test_employee:
                print("❌ STILL BROKEN - No suitable employee found")
                return False
            
            employee_id = test_employee['employee_id']
            original_manual_deductions = test_employee.get('manual_deductions', 0.0)
            
            print(f"   👤 Test employee ID: {employee_id}")
            print(f"   💰 Original manual_deductions: {original_manual_deductions}")
            
            # Step 3: PUT /api/payroll/cycles/{cycle_id}/update-employees with manual_deductions = 75.25
            print("3️⃣ Updating manual deductions to 75.25...")
            
            # Get the current employee data to preserve other fields
            # Note: base_salary might be 0 in summary, so we need to use a reasonable value
            current_base_salary = test_employee.get('base_salary', 0)
            if current_base_salary == 0:
                current_base_salary = 2700  # Use known base salary for this employee
            current_allowances = test_employee.get('total_allowances', 0)
            current_attendance_ded = test_employee.get('attendance_deductions', 0)
            current_advance_ded = test_employee.get('advance_deductions', 0)
            
            update_data = {
                "employees": [
                    {
                        "employee_id": employee_id,
                        "base_salary": current_base_salary,
                        "allowances": current_allowances,
                        "manual_deductions": 75.25,
                        "attendance_deductions": current_attendance_ded,
                        "advance_deductions": current_advance_ded
                    }
                ]
            }
            
            response = self.session.put(f"{BASE_URL}/payroll/cycles/{cycle_id}/update-employees", json=update_data)
            
            if response.status_code != 200:
                print(f"❌ STILL BROKEN - Failed to update employee: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
            
            print("   ✅ Update request successful")
            
            # Wait a moment for the update to be processed
            import time
            time.sleep(2)
            
            # Step 4: GET /api/payroll/cycles/{cycle_id}/summary again → verify manual_deductions = 75.25
            print("4️⃣ Verifying manual deductions persistence...")
            response = self.session.get(f"{BASE_URL}/payroll/cycles/{cycle_id}/summary")
            
            if response.status_code != 200:
                print(f"❌ STILL BROKEN - Failed to get updated summary: {response.status_code}")
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
            
            updated_manual_deductions = updated_employee.get('manual_deductions', 0.0)
            
            print(f"   💰 Updated manual_deductions: {updated_manual_deductions}")
            
            # Verify the fix
            if abs(updated_manual_deductions - 75.25) < 0.01:  # Allow for floating point precision
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
                
        except Exception as e:
            print(f"\n💥 ❌ STILL BROKEN - Exception occurred: {str(e)}")
            return False
    
    def run_test(self):
        """Run the complete test"""
        print("🚀 Manual Deductions Persistence Fix Test")
        print(f"🌐 Base URL: {BASE_URL}")
        print(f"👤 Test Account: {TEST_ACCOUNT['email']}")
        print("=" * 60)
        
        # Authenticate
        if not self.authenticate():
            return False
        
        # Run the specific test
        success = self.test_manual_deductions_persistence()
        
        print("\n" + "=" * 60)
        if success:
            print("🎯 TEST RESULT: ✅ FIXED - Manual deductions save functionality is working!")
        else:
            print("🎯 TEST RESULT: ❌ STILL BROKEN - Manual deductions save functionality needs more work!")
        print("=" * 60)
        
        return success

if __name__ == "__main__":
    tester = ManualDeductionsFixTester()
    tester.run_test()