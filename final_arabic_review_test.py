#!/usr/bin/env python3
"""
Final Arabic Review Backend Testing - اختبار نهائي شامل للـ Backend
Testing all specific issues mentioned in the Arabic review request with detailed reporting
"""

import requests
import json
import sys
from datetime import datetime, timedelta

# Configuration
BACKEND_URL = "https://tanseeq-payroll-1.preview.emergentagent.com/api"

# Test credentials
SUPER_ADMIN_CREDENTIALS = {"email": "admin@tanseeq.com", "password": "ADMIN"}
REGULAR_USER_CREDENTIALS = {"email": "jihad@tanseeq.com", "password": "jihad123"}

class FinalArabicReviewTester:
    def __init__(self):
        self.super_admin_token = None
        self.regular_user_token = None
        self.test_results = []
        self.cycle_id = "026ce2ba-4471-482c-ac03-dbb8353ac13f"  # Known working cycle
        self.employee_id = "eed6d28b-7639-4d31-9386-4e99b9179d8f"  # Jihad
        
    def log_test(self, test_name, status_code, success, details, response_preview=None):
        """Log test results with Arabic review format"""
        result = {
            "test": test_name,
            "status_code": status_code,
            "result": "✅ Pass" if success else "❌ Fail",
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        
        if response_preview:
            # Show first 10 lines as requested
            lines = str(response_preview).split('\n')[:10]
            result["response_body_preview"] = '\n'.join(lines)
        
        self.test_results.append(result)
        print(f"{result['result']} {test_name}")
        print(f"   Status Code: {status_code}")
        print(f"   Details: {details}")
        if response_preview and len(str(response_preview)) < 300:
            print(f"   Response: {response_preview}")
        print()

    def authenticate(self):
        """Authenticate both users"""
        print("🔐 Authentication Testing...")
        print("=" * 50)
        
        # Super Admin
        try:
            response = requests.post(f"{BACKEND_URL}/auth/login", json=SUPER_ADMIN_CREDENTIALS)
            if response.status_code == 200:
                self.super_admin_token = response.json()["access_token"]
                self.log_test("Super Admin Login", response.status_code, True, "Authentication successful")
            else:
                self.log_test("Super Admin Login", response.status_code, False, f"Login failed: {response.text}")
                return False
        except Exception as e:
            self.log_test("Super Admin Login", 0, False, f"Exception: {str(e)}")
            return False
            
        # Regular User
        try:
            response = requests.post(f"{BACKEND_URL}/auth/login", json=REGULAR_USER_CREDENTIALS)
            if response.status_code == 200:
                self.regular_user_token = response.json()["access_token"]
                self.log_test("Regular User Login", response.status_code, True, "Authentication successful")
            else:
                self.log_test("Regular User Login", response.status_code, False, f"Login failed: {response.text}")
                return False
        except Exception as e:
            self.log_test("Regular User Login", 0, False, f"Exception: {str(e)}")
            return False
            
        return True

    def test_high_priority_payroll_operations(self):
        """Test HIGH PRIORITY: Payroll cycle operations that were showing 405 errors"""
        print("🔥 HIGH PRIORITY: Payroll Cycle Operations (Previously 405 Method Not Allowed)")
        print("=" * 70)
        
        headers = {"Authorization": f"Bearer {self.super_admin_token}"}
        
        # Test 1: Recalculate payroll
        try:
            response = requests.post(f"{BACKEND_URL}/payroll/cycles/{self.cycle_id}/recalculate", headers=headers)
            success = response.status_code == 200
            self.log_test("POST /api/payroll/cycles/{cycle_id}/recalculate (حساب الرواتب)", 
                         response.status_code, success, 
                         "Payroll recalculation endpoint", response.json() if success else response.text)
        except Exception as e:
            self.log_test("POST /api/payroll/cycles/{cycle_id}/recalculate", 0, False, f"Exception: {str(e)}")

        # Test 2: Lock cycle
        try:
            lock_data = {"lock_reason": "اختبار قفل الدورة للمراجعة العربية"}
            response = requests.post(f"{BACKEND_URL}/payroll/cycles/{self.cycle_id}/lock", 
                                   headers=headers, json=lock_data)
            success = response.status_code == 200
            self.log_test("POST /api/payroll/cycles/{cycle_id}/lock (قفل الدورة)", 
                         response.status_code, success, 
                         "Cycle lock endpoint", response.json() if success else response.text)
        except Exception as e:
            self.log_test("POST /api/payroll/cycles/{cycle_id}/lock", 0, False, f"Exception: {str(e)}")

        # Test 3: Unlock cycle
        try:
            unlock_data = {"reason": "اختبار فتح الدورة للمراجعة العربية"}
            response = requests.post(f"{BACKEND_URL}/payroll/cycles/{self.cycle_id}/unlock", 
                                   headers=headers, json=unlock_data)
            success = response.status_code == 200
            self.log_test("POST /api/payroll/cycles/{cycle_id}/unlock (فتح الدورة)", 
                         response.status_code, success, 
                         "Cycle unlock endpoint", response.json() if success else response.text)
        except Exception as e:
            self.log_test("POST /api/payroll/cycles/{cycle_id}/unlock", 0, False, f"Exception: {str(e)}")

    def test_payroll_summary_data_aggregation(self):
        """Test payroll summary data aggregation from Payroll Ledger"""
        print("✅ HIGH PRIORITY: Payroll Summary Data Aggregation")
        print("=" * 50)
        
        headers = {"Authorization": f"Bearer {self.super_admin_token}"}
        
        try:
            response = requests.get(f"{BACKEND_URL}/payroll/cycles/{self.cycle_id}/summary", headers=headers)
            if response.status_code == 200:
                summary_data = response.json()
                
                # Check for required deduction fields
                required_fields = ["attendance_deductions", "advance_deductions", "manual_deductions"]
                has_required_fields = all(field in str(summary_data) for field in required_fields)
                
                # Check employee-level data
                employee_data_valid = False
                if isinstance(summary_data, dict):
                    # Check if employees have required fields
                    sample_employee = None
                    if "employees" in summary_data and summary_data["employees"]:
                        sample_employee = summary_data["employees"][0]
                    elif "employee_summaries" in summary_data and summary_data["employee_summaries"]:
                        sample_employee = summary_data["employee_summaries"][0]
                    
                    if sample_employee:
                        emp_required_fields = ["attendance_deductions", "advance_deductions", "manual_deductions", 
                                             "total_deductions", "net_salary"]
                        employee_data_valid = all(field in sample_employee for field in emp_required_fields)
                
                success = has_required_fields and employee_data_valid
                details = f"Required fields: {has_required_fields}, Employee data: {employee_data_valid}"
                self.log_test("GET /api/payroll/cycles/{cycle_id}/summary", 
                             response.status_code, success, details, summary_data)
            else:
                self.log_test("GET /api/payroll/cycles/{cycle_id}/summary", 
                             response.status_code, False, "Failed to get summary", response.text)
        except Exception as e:
            self.log_test("GET /api/payroll/cycles/{cycle_id}/summary", 0, False, f"Exception: {str(e)}")

    def test_monthly_deductions_calculation(self):
        """Test monthly deductions calculation (Previously 405 Method Not Allowed)"""
        print("❌ HIGH PRIORITY: Monthly Deductions Calculation (Previously 405)")
        print("=" * 60)
        
        headers = {"Authorization": f"Bearer {self.super_admin_token}"}
        
        try:
            # Test with January 2025 as specified in review
            response = requests.post(f"{BACKEND_URL}/deductions/calculate-monthly?month=2025-01", headers=headers)
            success = response.status_code == 200
            self.log_test("POST /api/deductions/calculate-monthly?month=2025-01", 
                         response.status_code, success, 
                         "Monthly deductions calculation", response.json() if success else response.text)
        except Exception as e:
            self.log_test("POST /api/deductions/calculate-monthly", 0, False, f"Exception: {str(e)}")

    def test_leaves_my_endpoint(self):
        """Test leaves/my endpoint (Previously 404 Not Found)"""
        print("❌ HIGH PRIORITY: Leaves My Endpoint (Previously 404)")
        print("=" * 50)
        
        headers = {"Authorization": f"Bearer {self.regular_user_token}"}
        
        try:
            response = requests.get(f"{BACKEND_URL}/leaves/my", headers=headers)
            success = response.status_code == 200
            self.log_test("GET /api/leaves/my (Regular User)", 
                         response.status_code, success, 
                         "User's leave requests", response.json() if success else response.text)
        except Exception as e:
            self.log_test("GET /api/leaves/my", 0, False, f"Exception: {str(e)}")

    def test_installment_schedules(self):
        """Test installment schedules (Previously Unknown error)"""
        print("❌ HIGH PRIORITY: Installment Schedules (Previously Unknown Error)")
        print("=" * 60)
        
        headers = {"Authorization": f"Bearer {self.super_admin_token}"}
        
        try:
            response = requests.get(f"{BACKEND_URL}/payroll/installment-schedules", headers=headers)
            success = response.status_code == 200 and "error" not in response.text.lower()
            details = "Installment schedules retrieval"
            if response.status_code == 200 and "error" in response.text.lower():
                details += " (Contains error in response)"
            self.log_test("GET /api/payroll/installment-schedules", 
                         response.status_code, success, details, response.json() if success else response.text)
        except Exception as e:
            self.log_test("GET /api/payroll/installment-schedules", 0, False, f"Exception: {str(e)}")

    def test_salary_letters(self):
        """Test salary letters (HTML and PDF formats)"""
        print("📄 Salary Letters Testing")
        print("=" * 30)
        
        headers = {"Authorization": f"Bearer {self.super_admin_token}"}
        
        # Test HTML format
        try:
            response = requests.get(f"{BACKEND_URL}/payroll/cycles/{self.cycle_id}/employees/{self.employee_id}/letter?format=html", 
                                  headers=headers)
            success = response.status_code == 200
            details = f"HTML salary letter, Content-Type: {response.headers.get('content-type', 'N/A')}"
            self.log_test("GET Salary Letter (format=html)", 
                         response.status_code, success, details, 
                         response.text[:200] if success else response.text)
        except Exception as e:
            self.log_test("GET Salary Letter (HTML)", 0, False, f"Exception: {str(e)}")

        # Test PDF format
        try:
            response = requests.get(f"{BACKEND_URL}/payroll/cycles/{self.cycle_id}/employees/{self.employee_id}/letter?format=pdf", 
                                  headers=headers)
            success = response.status_code == 200
            details = f"PDF salary letter, Content-Type: {response.headers.get('content-type', 'N/A')}, Size: {len(response.content)} bytes"
            self.log_test("GET Salary Letter (format=pdf)", 
                         response.status_code, success, details)
        except Exception as e:
            self.log_test("GET Salary Letter (PDF)", 0, False, f"Exception: {str(e)}")

    def run_comprehensive_test(self):
        """Run comprehensive Arabic review test"""
        print("🚀 FINAL ARABIC REVIEW BACKEND TESTING")
        print("اختبار شامل للـ Backend بناءً على قائمة الأعطال المرصودة")
        print("=" * 70)
        print()
        
        # Authentication
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed.")
            return False
        
        # High Priority Tests
        self.test_high_priority_payroll_operations()
        self.test_payroll_summary_data_aggregation()
        self.test_monthly_deductions_calculation()
        self.test_leaves_my_endpoint()
        self.test_installment_schedules()
        
        # Salary Letters
        self.test_salary_letters()
        
        # Generate final report
        self.generate_final_report()
        
        return True

    def generate_final_report(self):
        """Generate comprehensive final report"""
        print("\n" + "=" * 70)
        print("📊 FINAL ARABIC REVIEW TEST REPORT")
        print("تقرير اختبار المراجعة العربية النهائي")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if "✅ Pass" in r["result"]])
        failed_tests = total_tests - passed_tests
        
        print(f"📈 SUMMARY:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        # Detailed results by status code
        print("📋 DETAILED RESULTS:")
        print("-" * 50)
        for result in self.test_results:
            status_icon = "✅" if "Pass" in result["result"] else "❌"
            print(f"{status_icon} {result['test']}")
            print(f"   Status Code: {result['status_code']}")
            print(f"   Details: {result['details']}")
            if result.get('response_body_preview'):
                print(f"   Response Preview: {result['response_body_preview'][:100]}...")
            print()
        
        # Critical Issues Summary
        failed_results = [r for r in self.test_results if "❌ Fail" in r["result"]]
        if failed_results:
            print("🚨 CRITICAL ISSUES FOUND:")
            print("-" * 30)
            for result in failed_results:
                print(f"❌ {result['test']}: Status {result['status_code']} - {result['details']}")
            print()
        
        # Working Features Summary
        passed_results = [r for r in self.test_results if "✅ Pass" in r["result"]]
        if passed_results:
            print("✅ WORKING FEATURES:")
            print("-" * 20)
            for result in passed_results:
                print(f"✅ {result['test']}: Status {result['status_code']}")
            print()
        
        # Save detailed JSON report
        with open("/app/final_arabic_review_results.json", "w", encoding="utf-8") as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Detailed JSON report saved: /app/final_arabic_review_results.json")
        print()
        
        # Final conclusion
        if failed_tests == 0:
            print("🎉 ALL TESTS PASSED! No critical issues found.")
        elif failed_tests <= 2:
            print("⚠️  Minor issues found. Most functionality working correctly.")
        else:
            print("🚨 Multiple critical issues found. Requires immediate attention.")

if __name__ == "__main__":
    tester = FinalArabicReviewTester()
    success = tester.run_comprehensive_test()
    
    if not success:
        sys.exit(1)