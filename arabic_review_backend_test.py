#!/usr/bin/env python3
"""
Arabic Review Backend Testing - اختبار شامل للـ Backend بناءً على قائمة الأعطال المرصودة
Testing specific issues mentioned in the Arabic review request
"""

import requests
import json
import sys
from datetime import datetime, timedelta
import os

# Configuration
BACKEND_URL = "https://tanseeq-hr-fix.preview.emergentagent.com/api"

# Test credentials
SUPER_ADMIN_CREDENTIALS = {
    "email": "admin@tanseeq.com",
    "password": "ADMIN"
}

REGULAR_USER_CREDENTIALS = {
    "email": "jihad@tanseeq.com", 
    "password": "jihad123"
}

class ArabicReviewTester:
    def __init__(self):
        self.super_admin_token = None
        self.regular_user_token = None
        self.test_results = []
        self.cycle_id = None
        self.employee_id = None
        
    def log_test(self, test_name, status, details, response_body=None):
        """Log test results"""
        result = {
            "test": test_name,
            "status": "✅ PASS" if status else "❌ FAIL", 
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        if response_body:
            # Only show first 10 lines of response as requested
            if isinstance(response_body, dict):
                result["response_preview"] = str(response_body)[:500] + "..." if len(str(response_body)) > 500 else str(response_body)
            else:
                lines = str(response_body).split('\n')[:10]
                result["response_preview"] = '\n'.join(lines)
        
        self.test_results.append(result)
        print(f"{result['status']} {test_name}: {details}")
        if response_body and len(str(response_body)) < 200:
            print(f"   Response: {response_body}")
        print()

    def authenticate(self):
        """Authenticate both users"""
        print("🔐 Authenticating users...")
        
        # Super Admin authentication
        try:
            response = requests.post(f"{BACKEND_URL}/auth/login", json=SUPER_ADMIN_CREDENTIALS)
            if response.status_code == 200:
                self.super_admin_token = response.json()["access_token"]
                self.log_test("Super Admin Authentication", True, f"Status: {response.status_code}")
            else:
                self.log_test("Super Admin Authentication", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Super Admin Authentication", False, f"Exception: {str(e)}")
            return False
            
        # Regular User authentication  
        try:
            response = requests.post(f"{BACKEND_URL}/auth/login", json=REGULAR_USER_CREDENTIALS)
            if response.status_code == 200:
                self.regular_user_token = response.json()["access_token"]
                self.log_test("Regular User Authentication", True, f"Status: {response.status_code}")
            else:
                self.log_test("Regular User Authentication", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Regular User Authentication", False, f"Exception: {str(e)}")
            return False
            
        return True

    def get_payroll_cycles(self):
        """Get payroll cycles to use for testing"""
        print("📊 Getting payroll cycles...")
        
        headers = {"Authorization": f"Bearer {self.super_admin_token}"}
        try:
            response = requests.get(f"{BACKEND_URL}/payroll/cycles", headers=headers)
            if response.status_code == 200:
                cycles = response.json()
                if cycles and len(cycles) > 0:
                    self.cycle_id = cycles[0].get("id")
                    self.log_test("Get Payroll Cycles", True, f"Found {len(cycles)} cycles, using cycle_id: {self.cycle_id}")
                    return True
                else:
                    self.log_test("Get Payroll Cycles", False, "No cycles found")
                    return False
            else:
                self.log_test("Get Payroll Cycles", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Get Payroll Cycles", False, f"Exception: {str(e)}")
            return False

    def get_employee_id(self):
        """Get an employee ID for salary letter testing"""
        print("👤 Getting employee ID...")
        
        headers = {"Authorization": f"Bearer {self.super_admin_token}"}
        try:
            response = requests.get(f"{BACKEND_URL}/employees/list", headers=headers)
            if response.status_code == 200:
                employees = response.json()
                if employees and len(employees) > 0:
                    self.employee_id = employees[0].get("id")
                    self.log_test("Get Employee ID", True, f"Using employee_id: {self.employee_id}")
                    return True
                else:
                    self.log_test("Get Employee ID", False, "No employees found")
                    return False
            else:
                self.log_test("Get Employee ID", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Get Employee ID", False, f"Exception: {str(e)}")
            return False

    def test_payroll_cycle_operations(self):
        """Test payroll cycle operations - HIGH PRIORITY"""
        print("🔥 Testing HIGH PRIORITY: Payroll Cycle Operations...")
        
        if not self.cycle_id:
            self.log_test("Payroll Cycle Operations", False, "No cycle_id available")
            return
            
        headers = {"Authorization": f"Bearer {self.super_admin_token}"}
        
        # Test 1: POST /api/payroll/cycles/{cycle_id}/recalculate
        try:
            response = requests.post(f"{BACKEND_URL}/payroll/cycles/{self.cycle_id}/recalculate", headers=headers)
            success = response.status_code not in [405, 404, 500]
            self.log_test("POST /api/payroll/cycles/{cycle_id}/recalculate", success, 
                         f"Status: {response.status_code}", response.text[:200])
        except Exception as e:
            self.log_test("POST /api/payroll/cycles/{cycle_id}/recalculate", False, f"Exception: {str(e)}")

        # Test 2: POST /api/payroll/cycles/{cycle_id}/lock
        try:
            lock_data = {"lock_reason": "اختبار قفل الدورة"}
            response = requests.post(f"{BACKEND_URL}/payroll/cycles/{self.cycle_id}/lock", 
                                   headers=headers, json=lock_data)
            success = response.status_code not in [405, 404, 500]
            self.log_test("POST /api/payroll/cycles/{cycle_id}/lock", success, 
                         f"Status: {response.status_code}", response.text[:200])
        except Exception as e:
            self.log_test("POST /api/payroll/cycles/{cycle_id}/lock", False, f"Exception: {str(e)}")

        # Test 3: POST /api/payroll/cycles/{cycle_id}/unlock  
        try:
            unlock_data = {"reason": "اختبار فتح الدورة"}
            response = requests.post(f"{BACKEND_URL}/payroll/cycles/{self.cycle_id}/unlock", 
                                   headers=headers, json=unlock_data)
            success = response.status_code not in [405, 404, 500]
            self.log_test("POST /api/payroll/cycles/{cycle_id}/unlock", success, 
                         f"Status: {response.status_code}", response.text[:200])
        except Exception as e:
            self.log_test("POST /api/payroll/cycles/{cycle_id}/unlock", False, f"Exception: {str(e)}")

    def test_payroll_summary_aggregation(self):
        """Test payroll summary data aggregation - HIGH PRIORITY"""
        print("✅ Testing HIGH PRIORITY: Payroll Summary Data Aggregation...")
        
        if not self.cycle_id:
            self.log_test("Payroll Summary Aggregation", False, "No cycle_id available")
            return
            
        headers = {"Authorization": f"Bearer {self.super_admin_token}"}
        
        try:
            response = requests.get(f"{BACKEND_URL}/payroll/cycles/{self.cycle_id}/summary", headers=headers)
            if response.status_code == 200:
                summary_data = response.json()
                
                # Check if summary contains required fields
                required_fields = ["attendance_deductions", "advance_deductions", "manual_deductions"]
                has_required_fields = all(field in str(summary_data) for field in required_fields)
                
                # Check if employees have required deduction fields
                employees_valid = True
                if isinstance(summary_data, dict) and "employees" in summary_data:
                    for emp in summary_data["employees"][:3]:  # Check first 3 employees
                        emp_fields = ["attendance_deductions", "advance_deductions", "manual_deductions", 
                                    "total_deductions", "net_salary"]
                        if not all(field in emp for field in emp_fields):
                            employees_valid = False
                            break
                
                success = has_required_fields and employees_valid
                details = f"Status: {response.status_code}, Required fields present: {has_required_fields}, Employee fields valid: {employees_valid}"
                self.log_test("GET /api/payroll/cycles/{cycle_id}/summary", success, details, summary_data)
            else:
                self.log_test("GET /api/payroll/cycles/{cycle_id}/summary", False, 
                             f"Status: {response.status_code}", response.text[:200])
        except Exception as e:
            self.log_test("GET /api/payroll/cycles/{cycle_id}/summary", False, f"Exception: {str(e)}")

    def test_monthly_deductions_calculation(self):
        """Test monthly deductions calculation - HIGH PRIORITY"""
        print("❌ Testing HIGH PRIORITY: Monthly Deductions Calculation...")
        
        headers = {"Authorization": f"Bearer {self.super_admin_token}"}
        
        try:
            # Test with current month
            current_month = datetime.now().strftime("%Y-%m")
            response = requests.post(f"{BACKEND_URL}/deductions/calculate-monthly?month={current_month}", headers=headers)
            success = response.status_code not in [405, 404, 500]
            self.log_test("POST /api/deductions/calculate-monthly", success, 
                         f"Status: {response.status_code} for month {current_month}", response.text[:200])
        except Exception as e:
            self.log_test("POST /api/deductions/calculate-monthly", False, f"Exception: {str(e)}")

    def test_leaves_my_endpoint(self):
        """Test leaves/my endpoint - HIGH PRIORITY"""
        print("❌ Testing HIGH PRIORITY: Leaves My Endpoint...")
        
        headers = {"Authorization": f"Bearer {self.regular_user_token}"}
        
        try:
            response = requests.get(f"{BACKEND_URL}/leaves/my", headers=headers)
            success = response.status_code not in [404, 500]
            self.log_test("GET /api/leaves/my (Regular User)", success, 
                         f"Status: {response.status_code}", response.text[:200])
        except Exception as e:
            self.log_test("GET /api/leaves/my (Regular User)", False, f"Exception: {str(e)}")

    def test_installment_schedules(self):
        """Test installment schedules endpoint - HIGH PRIORITY"""
        print("❌ Testing HIGH PRIORITY: Installment Schedules...")
        
        headers = {"Authorization": f"Bearer {self.super_admin_token}"}
        
        try:
            response = requests.get(f"{BACKEND_URL}/payroll/installment-schedules", headers=headers)
            success = response.status_code == 200 and "error" not in response.text.lower()
            details = f"Status: {response.status_code}"
            if not success and response.status_code == 200:
                details += ", Contains error in response"
            self.log_test("GET /api/payroll/installment-schedules", success, details, response.text[:200])
        except Exception as e:
            self.log_test("GET /api/payroll/installment-schedules", False, f"Exception: {str(e)}")

    def test_salary_letters(self):
        """Test salary letters endpoints"""
        print("📄 Testing: Salary Letters...")
        
        if not self.cycle_id or not self.employee_id:
            self.log_test("Salary Letters", False, "Missing cycle_id or employee_id")
            return
            
        headers = {"Authorization": f"Bearer {self.super_admin_token}"}
        
        # Test HTML format
        try:
            response = requests.get(f"{BACKEND_URL}/payroll/cycles/{self.cycle_id}/employees/{self.employee_id}/letter?format=html", 
                                  headers=headers)
            success = response.status_code == 200
            self.log_test("GET Salary Letter (HTML)", success, 
                         f"Status: {response.status_code}", response.text[:200])
        except Exception as e:
            self.log_test("GET Salary Letter (HTML)", False, f"Exception: {str(e)}")

        # Test PDF format
        try:
            response = requests.get(f"{BACKEND_URL}/payroll/cycles/{self.cycle_id}/employees/{self.employee_id}/letter?format=pdf", 
                                  headers=headers)
            success = response.status_code == 200
            self.log_test("GET Salary Letter (PDF)", success, 
                         f"Status: {response.status_code}, Content-Type: {response.headers.get('content-type', 'N/A')}")
        except Exception as e:
            self.log_test("GET Salary Letter (PDF)", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all tests in the Arabic review"""
        print("🚀 Starting Arabic Review Backend Testing...")
        print("=" * 60)
        
        # Step 1: Authentication
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
            
        # Step 2: Get test data
        if not self.get_payroll_cycles():
            print("⚠️ Could not get payroll cycles. Some tests will be skipped.")
            
        if not self.get_employee_id():
            print("⚠️ Could not get employee ID. Salary letter tests will be skipped.")
        
        # Step 3: Run priority tests
        print("\n🔥 HIGH PRIORITY TESTS:")
        print("-" * 40)
        self.test_payroll_cycle_operations()
        self.test_payroll_summary_aggregation()
        self.test_monthly_deductions_calculation()
        self.test_leaves_my_endpoint()
        self.test_installment_schedules()
        
        print("\n📄 SALARY LETTERS TESTS:")
        print("-" * 40)
        self.test_salary_letters()
        
        # Step 4: Generate summary
        self.generate_summary()
        
        return True

    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "=" * 60)
        print("📊 ARABIC REVIEW TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if "✅ PASS" in r["status"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\n🔥 CRITICAL ISSUES FOUND:")
        print("-" * 40)
        for result in self.test_results:
            if "❌ FAIL" in result["status"]:
                print(f"❌ {result['test']}: {result['details']}")
        
        print("\n✅ WORKING ENDPOINTS:")
        print("-" * 40)
        for result in self.test_results:
            if "✅ PASS" in result["status"]:
                print(f"✅ {result['test']}: {result['details']}")
        
        # Save detailed results
        with open("/app/arabic_review_test_results.json", "w", encoding="utf-8") as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Detailed results saved to: /app/arabic_review_test_results.json")

if __name__ == "__main__":
    tester = ArabicReviewTester()
    success = tester.run_all_tests()
    
    if not success:
        sys.exit(1)