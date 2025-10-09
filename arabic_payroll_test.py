#!/usr/bin/env python3
"""
اختبار endpoint حفظ تعديلات الرواتب - Arabic Review Request
Testing payroll salary edits endpoint as requested in Arabic review
"""

import requests
import json
import os
from datetime import datetime

# Configuration
BACKEND_URL = "https://tanseeq-hr-fix.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
    "email": "admin@tanseeq.com",
    "password": "ADMIN"
}

class PayrollEditTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        
    def log_result(self, test_name, success, details, status_code=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "status_code": status_code,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if status_code:
            print(f"   Status Code: {status_code}")
        print(f"   Details: {details}")
        print()
        
    def authenticate(self):
        """Authenticate as admin"""
        try:
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=ADMIN_CREDENTIALS,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.session.headers.update({
                    "Authorization": f"Bearer {self.token}"
                })
                self.log_result(
                    "Admin Authentication", 
                    True, 
                    f"Successfully authenticated as {ADMIN_CREDENTIALS['email']}", 
                    response.status_code
                )
                return True
            else:
                self.log_result(
                    "Admin Authentication", 
                    False, 
                    f"Authentication failed: {response.text}", 
                    response.status_code
                )
                return False
                
        except Exception as e:
            self.log_result("Admin Authentication", False, f"Exception: {str(e)}")
            return False
    
    def get_payroll_cycles(self):
        """Step 1: Get payroll cycles"""
        try:
            response = self.session.get(f"{BACKEND_URL}/payroll/cycles", timeout=30)
            
            if response.status_code == 200:
                cycles = response.json()
                if cycles and len(cycles) > 0:
                    cycle_id = cycles[0].get("id")
                    cycle_name = cycles[0].get("cycle_name", "Unknown")
                    self.log_result(
                        "Get Payroll Cycles",
                        True,
                        f"Found {len(cycles)} cycles. Using cycle: {cycle_name} (ID: {cycle_id})",
                        response.status_code
                    )
                    return cycle_id
                else:
                    self.log_result(
                        "Get Payroll Cycles",
                        False,
                        "No payroll cycles found",
                        response.status_code
                    )
                    return None
            else:
                self.log_result(
                    "Get Payroll Cycles",
                    False,
                    f"Failed to get cycles: {response.text}",
                    response.status_code
                )
                return None
                
        except Exception as e:
            self.log_result("Get Payroll Cycles", False, f"Exception: {str(e)}")
            return None
    
    def get_cycle_summary(self, cycle_id):
        """Step 2: Get employee data from cycle summary"""
        try:
            response = self.session.get(f"{BACKEND_URL}/payroll/cycles/{cycle_id}/summary", timeout=30)
            
            if response.status_code == 200:
                summary = response.json()
                employees = summary.get("employee_summaries", [])
                
                if employees and len(employees) > 0:
                    employee = employees[0]
                    employee_id = employee.get("employee_id")
                    employee_name = employee.get("employee_name", "Unknown")
                    base_salary = employee.get("base_salary", 0)
                    current_manual_deductions = employee.get("manual_deductions", 0)
                    
                    self.log_result(
                        "Get Cycle Summary",
                        True,
                        f"Found {len(employees)} employees. Using: {employee_name} (ID: {employee_id}, Base Salary: {base_salary}, Current Manual Deductions: {current_manual_deductions})",
                        response.status_code
                    )
                    return employee_id, base_salary, current_manual_deductions
                else:
                    self.log_result(
                        "Get Cycle Summary",
                        False,
                        "No employees found in cycle summary",
                        response.status_code
                    )
                    return None, None, None
            else:
                self.log_result(
                    "Get Cycle Summary",
                    False,
                    f"Failed to get cycle summary: {response.text}",
                    response.status_code
                )
                return None, None, None
                
        except Exception as e:
            self.log_result("Get Cycle Summary", False, f"Exception: {str(e)}")
            return None, None, None
    
    def update_employee_deductions(self, cycle_id, employee_id, base_salary):
        """Step 3: Try to update manual_deductions"""
        try:
            # Test value for manual deductions
            test_manual_deductions = 100.50
            
            update_payload = {
                "employees": [{
                    "employee_id": employee_id,
                    "base_salary": base_salary,
                    "allowances": 0,
                    "manual_deductions": test_manual_deductions,
                    "attendance_deductions": 0,
                    "advance_deductions": 0
                }]
            }
            
            response = self.session.put(
                f"{BACKEND_URL}/payroll/cycles/{cycle_id}/update-employees",
                json=update_payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log_result(
                    "Update Employee Deductions",
                    True,
                    f"Update request successful. Response: {result}. Set manual_deductions to {test_manual_deductions}",
                    response.status_code
                )
                return True, test_manual_deductions
            else:
                self.log_result(
                    "Update Employee Deductions",
                    False,
                    f"Update failed: {response.text}",
                    response.status_code
                )
                return False, test_manual_deductions
                
        except Exception as e:
            self.log_result("Update Employee Deductions", False, f"Exception: {str(e)}")
            return False, 100.50
    
    def verify_update(self, cycle_id, employee_id, expected_manual_deductions):
        """Step 4: Verify the update was saved"""
        try:
            response = self.session.get(f"{BACKEND_URL}/payroll/cycles/{cycle_id}/summary", timeout=30)
            
            if response.status_code == 200:
                summary = response.json()
                employees = summary.get("employee_summaries", [])
                
                # Find the specific employee
                target_employee = None
                for emp in employees:
                    if emp.get("employee_id") == employee_id:
                        target_employee = emp
                        break
                
                if target_employee:
                    actual_manual_deductions = target_employee.get("manual_deductions", 0)
                    employee_name = target_employee.get("employee_name", "Unknown")
                    
                    if actual_manual_deductions == expected_manual_deductions:
                        self.log_result(
                            "Verify Update Saved",
                            True,
                            f"✅ SUCCESS: manual_deductions correctly saved as {actual_manual_deductions} for {employee_name}",
                            response.status_code
                        )
                        return True
                    else:
                        self.log_result(
                            "Verify Update Saved",
                            False,
                            f"❌ BUG CONFIRMED: Expected manual_deductions = {expected_manual_deductions}, but got {actual_manual_deductions} for {employee_name}. Changes are NOT being saved!",
                            response.status_code
                        )
                        return False
                else:
                    self.log_result(
                        "Verify Update Saved",
                        False,
                        f"Employee {employee_id} not found in updated summary",
                        response.status_code
                    )
                    return False
            else:
                self.log_result(
                    "Verify Update Saved",
                    False,
                    f"Failed to get updated summary: {response.text}",
                    response.status_code
                )
                return False
                
        except Exception as e:
            self.log_result("Verify Update Saved", False, f"Exception: {str(e)}")
            return False
    
    def run_full_test(self):
        """Run the complete test flow"""
        print("🎯 اختبار endpoint حفظ تعديلات الرواتب")
        print("=" * 60)
        print()
        
        # Step 1: Authenticate
        if not self.authenticate():
            return False
        
        # Step 2: Get cycle_id
        cycle_id = self.get_payroll_cycles()
        if not cycle_id:
            return False
        
        # Step 3: Get employee data
        employee_id, base_salary, current_manual_deductions = self.get_cycle_summary(cycle_id)
        if not employee_id:
            return False
        
        print(f"📋 Test Setup Complete:")
        print(f"   Cycle ID: {cycle_id}")
        print(f"   Employee ID: {employee_id}")
        print(f"   Base Salary: {base_salary}")
        print(f"   Current Manual Deductions: {current_manual_deductions}")
        print()
        
        # Step 4: Try to update manual_deductions
        update_success, test_value = self.update_employee_deductions(cycle_id, employee_id, base_salary)
        if not update_success:
            return False
        
        # Step 5: Verify the update was saved
        verification_success = self.verify_update(cycle_id, employee_id, test_value)
        
        return verification_success
    
    def save_results(self):
        """Save test results to file"""
        results_file = "/app/arabic_payroll_test_results.json"
        try:
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "test_run_time": datetime.now().isoformat(),
                    "backend_url": BACKEND_URL,
                    "total_tests": len(self.test_results),
                    "passed_tests": len([r for r in self.test_results if r["success"]]),
                    "failed_tests": len([r for r in self.test_results if not r["success"]]),
                    "results": self.test_results
                }, f, indent=2, ensure_ascii=False)
            print(f"📄 Test results saved to: {results_file}")
        except Exception as e:
            print(f"❌ Failed to save results: {e}")

def main():
    """Main test execution"""
    tester = PayrollEditTester()
    
    try:
        success = tester.run_full_test()
        
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(tester.test_results)
        passed_tests = len([r for r in tester.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if success:
            print("\n🎉 CONCLUSION: Payroll edits are working correctly!")
        else:
            print("\n🚨 CONCLUSION: BUG CONFIRMED - Payroll edits are NOT being saved!")
        
        # Save results
        tester.save_results()
        
        return success
        
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return False

if __name__ == "__main__":
    main()