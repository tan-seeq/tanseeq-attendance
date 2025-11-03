#!/usr/bin/env python3
"""
Advanced Deductions System End-to-End Test - October 2025
Testing specific review request for deductions calculation
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://attend-deduct-hr.preview.emergentagent.com/api"
TEST_CREDENTIALS = {
    "email": "admin@tanseeq.com",
    "password": "ADMIN"
}

class AdvancedDeductionsTest:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        
    def log_result(self, test_name, success, details, expected=None, actual=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        if expected is not None:
            result["expected"] = expected
        if actual is not None:
            result["actual"] = actual
        
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        
    def authenticate(self):
        """Authenticate as admin@tanseeq.com"""
        try:
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=TEST_CREDENTIALS,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.session.headers.update({
                    "Authorization": f"Bearer {self.token}"
                })
                self.log_result(
                    "Authentication", 
                    True, 
                    f"Successfully logged in as {TEST_CREDENTIALS['email']}"
                )
                return True
            else:
                self.log_result(
                    "Authentication", 
                    False, 
                    f"Login failed: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Authentication", False, f"Login error: {str(e)}")
            return False
    
    def test_monthly_deductions_calculation(self):
        """Test /api/deductions/calculate-monthly?month=2025-10"""
        try:
            response = self.session.post(
                f"{BACKEND_URL}/deductions/calculate-monthly?month=2025-10",
                timeout=60
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Monthly Deductions API Call",
                    False,
                    f"API returned {response.status_code}: {response.text}"
                )
                return None
            
            self.log_result(
                "Monthly Deductions API Call",
                True,
                f"API returned 200 OK"
            )
            
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                self.log_result(
                    "Response JSON Parsing",
                    False,
                    f"Failed to parse JSON: {str(e)}"
                )
                return None
                
            self.log_result(
                "Response JSON Parsing",
                True,
                "Successfully parsed JSON response"
            )
            
            return data
            
        except Exception as e:
            self.log_result(
                "Monthly Deductions API Call",
                False,
                f"Request error: {str(e)}"
            )
            return None
    
    def verify_response_structure(self, data):
        """Verify response structure according to review requirements"""
        if not data:
            return False
            
        # Check for required keys
        required_keys = ["summaries", "employees", "success"]
        missing_keys = []
        
        for key in required_keys:
            if key not in data:
                missing_keys.append(key)
        
        if missing_keys:
            self.log_result(
                "Response Structure - Required Keys",
                False,
                f"Missing required keys: {missing_keys}",
                expected=required_keys,
                actual=list(data.keys())
            )
            return False
        
        self.log_result(
            "Response Structure - Required Keys",
            True,
            f"All required keys present: {required_keys}"
        )
        
        # Check success field
        success_value = data.get("success")
        if success_value is not True:
            self.log_result(
                "Response Structure - Success Field",
                False,
                f"Success field is not True",
                expected=True,
                actual=success_value
            )
            return False
        
        self.log_result(
            "Response Structure - Success Field",
            True,
            "Success field is True"
        )
        
        # Check summaries array exists
        summaries = data.get("summaries")
        if not isinstance(summaries, list):
            self.log_result(
                "Response Structure - Summaries Array",
                False,
                f"Summaries is not an array",
                expected="list",
                actual=type(summaries).__name__
            )
            return False
        
        self.log_result(
            "Response Structure - Summaries Array",
            True,
            f"Summaries array exists with {len(summaries)} items"
        )
        
        # Check employees array exists
        employees = data.get("employees")
        if not isinstance(employees, list):
            self.log_result(
                "Response Structure - Employees Array",
                False,
                f"Employees is not an array",
                expected="list",
                actual=type(employees).__name__
            )
            return False
        
        self.log_result(
            "Response Structure - Employees Array",
            True,
            f"Employees array exists with {len(employees)} items"
        )
        
        return True
    
    def verify_employee_count(self, data):
        """Verify employee count = 13"""
        if not data:
            return False
            
        employees = data.get("employees", [])
        employee_count = len(employees)
        
        if employee_count != 13:
            self.log_result(
                "Employee Count Verification",
                False,
                f"Expected 13 employees, got {employee_count}",
                expected=13,
                actual=employee_count
            )
            return False
        
        self.log_result(
            "Employee Count Verification",
            True,
            f"Correct employee count: {employee_count}"
        )
        return True
    
    def verify_total_deductions(self, data):
        """Verify total_deductions > 0"""
        if not data:
            return False
            
        employees = data.get("employees", [])
        total_deductions = 0
        
        for employee in employees:
            emp_deduction = employee.get("total_deduction", 0)
            if isinstance(emp_deduction, (int, float)):
                total_deductions += emp_deduction
        
        if total_deductions <= 0:
            self.log_result(
                "Total Deductions Verification",
                False,
                f"Total deductions should be > 0, got {total_deductions}",
                expected="> 0",
                actual=total_deductions
            )
            return False
        
        self.log_result(
            "Total Deductions Verification",
            True,
            f"Total deductions: {total_deductions} AED"
        )
        return True
    
    def verify_sample_employees(self, data):
        """Verify first 3 employees structure and specific expected values"""
        if not data:
            return False
            
        employees = data.get("employees", [])
        if len(employees) < 3:
            self.log_result(
                "Sample Employees Verification",
                False,
                f"Need at least 3 employees for sampling, got {len(employees)}"
            )
            return False
        
        # Check first 3 employees structure
        required_fields = ["employee_name", "total_deduction", "absence_deduction", "daily_records"]
        
        for i in range(3):
            employee = employees[i]
            missing_fields = []
            
            for field in required_fields:
                if field not in employee:
                    missing_fields.append(field)
            
            if missing_fields:
                self.log_result(
                    f"Employee {i+1} Structure",
                    False,
                    f"Missing fields: {missing_fields}",
                    expected=required_fields,
                    actual=list(employee.keys())
                )
                continue
            
            # Verify daily_records is array
            daily_records = employee.get("daily_records")
            if not isinstance(daily_records, list):
                self.log_result(
                    f"Employee {i+1} Daily Records",
                    False,
                    f"daily_records is not an array",
                    expected="list",
                    actual=type(daily_records).__name__
                )
                continue
            
            self.log_result(
                f"Employee {i+1} Structure",
                True,
                f"All required fields present: {employee.get('employee_name', 'Unknown')}"
            )
        
        # Check for specific expected employees and their deductions
        expected_employees = {
            "Hatem": {"expected_deduction": 2933, "expected_days": 16},
            "Jihad": {"expected_deduction": 630, "expected_days": 7},
            "Tarek Wazzan": {"expected_deduction": 2400, "expected_days": 18}
        }
        
        found_employees = {}
        for employee in employees:
            emp_name = employee.get("employee_name", "")
            total_deduction = employee.get("total_deduction", 0)
            absence_deduction = employee.get("absence_deduction", 0)
            
            # Check for Hatem
            if "حاتم" in emp_name or "Hatem" in emp_name:
                found_employees["Hatem"] = {
                    "name": emp_name,
                    "total_deduction": total_deduction,
                    "absence_deduction": absence_deduction
                }
            
            # Check for Jihad
            if "جهاد" in emp_name or "Jihad" in emp_name:
                found_employees["Jihad"] = {
                    "name": emp_name,
                    "total_deduction": total_deduction,
                    "absence_deduction": absence_deduction
                }
            
            # Check for Tarek Wazzan
            if "طارق" in emp_name or "Tarek" in emp_name or "وزان" in emp_name or "Wazzan" in emp_name:
                found_employees["Tarek Wazzan"] = {
                    "name": emp_name,
                    "total_deduction": total_deduction,
                    "absence_deduction": absence_deduction
                }
        
        # Verify expected employees
        for expected_name, expected_data in expected_employees.items():
            if expected_name in found_employees:
                actual_data = found_employees[expected_name]
                actual_deduction = actual_data["total_deduction"]
                expected_deduction = expected_data["expected_deduction"]
                
                # Allow 10% tolerance for deduction amounts
                tolerance = expected_deduction * 0.1
                if abs(actual_deduction - expected_deduction) <= tolerance:
                    self.log_result(
                        f"Expected Employee - {expected_name}",
                        True,
                        f"Found {actual_data['name']} with deduction {actual_deduction} AED (expected ~{expected_deduction})"
                    )
                else:
                    self.log_result(
                        f"Expected Employee - {expected_name}",
                        False,
                        f"Found {actual_data['name']} but deduction {actual_deduction} AED differs significantly from expected ~{expected_deduction}",
                        expected=f"~{expected_deduction} AED",
                        actual=f"{actual_deduction} AED"
                    )
            else:
                self.log_result(
                    f"Expected Employee - {expected_name}",
                    False,
                    f"Employee {expected_name} not found in response"
                )
        
        return True
    
    def run_comprehensive_test(self):
        """Run the complete test suite"""
        print("🚀 Starting Advanced Deductions System End-to-End Test - October 2025")
        print("=" * 80)
        
        # Step 1: Authentication
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Step 2: Call monthly deductions API
        print("\n📊 Testing Monthly Deductions Calculation...")
        deductions_data = self.test_monthly_deductions_calculation()
        
        if not deductions_data:
            print("❌ Monthly deductions API call failed. Cannot proceed with verification.")
            return False
        
        # Step 3: Verify response structure
        print("\n🔍 Verifying Response Structure...")
        if not self.verify_response_structure(deductions_data):
            print("❌ Response structure verification failed.")
            return False
        
        # Step 4: Verify employee count
        print("\n👥 Verifying Employee Count...")
        if not self.verify_employee_count(deductions_data):
            print("❌ Employee count verification failed.")
            return False
        
        # Step 5: Verify total deductions
        print("\n💰 Verifying Total Deductions...")
        if not self.verify_total_deductions(deductions_data):
            print("❌ Total deductions verification failed.")
            return False
        
        # Step 6: Verify sample employees
        print("\n🎯 Verifying Sample Employees...")
        if not self.verify_sample_employees(deductions_data):
            print("❌ Sample employees verification failed.")
            return False
        
        return True
    
    def generate_report(self):
        """Generate final test report"""
        print("\n" + "=" * 80)
        print("📋 ADVANCED DEDUCTIONS SYSTEM TEST REPORT")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 Test Summary:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests}")
        print(f"   Failed: {failed_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   - {result['test']}: {result['details']}")
        
        print(f"\n🎯 Overall Result: {'✅ PASS' if success_rate >= 80 else '❌ FAIL'}")
        
        # Save detailed results
        with open("/app/advanced_deductions_test_results.json", "w") as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "failed_tests": failed_tests,
                    "success_rate": success_rate,
                    "timestamp": datetime.now().isoformat()
                },
                "test_results": self.test_results
            }, f, indent=2)
        
        return success_rate >= 80

def main():
    """Main test execution"""
    tester = AdvancedDeductionsTest()
    
    try:
        success = tester.run_comprehensive_test()
        final_result = tester.generate_report()
        
        if final_result:
            print("\n🎉 Advanced Deductions System test completed successfully!")
            sys.exit(0)
        else:
            print("\n🚨 Advanced Deductions System test failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()