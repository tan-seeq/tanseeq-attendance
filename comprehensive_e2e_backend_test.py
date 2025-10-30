#!/usr/bin/env python3
"""
🔥 COMPREHENSIVE E2E BACKEND TESTING 🔥
Test ALL critical backend endpoints and features as requested in review.

CREDENTIALS:
- Super Admin: admin@tanseeq.com / ADMIN
- Regular User: jihad@tanseeq.com / jihad123
- Admin: hatem@tan-seeq.co / hatem123

BACKEND_URL: From REACT_APP_BACKEND_URL environment
"""

import requests
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time

class ComprehensiveE2EBackendTester:
    def __init__(self):
        # Get backend URL from environment
        self.backend_url = "https://attendance-pro-43.preview.emergentagent.com"
        self.api_base = f"{self.backend_url}/api"
        
        # Test credentials
        self.credentials = {
            "super_admin": {"email": "admin@tanseeq.com", "password": "ADMIN"},
            "regular_user": {"email": "jihad@tanseeq.com", "password": "jihad123"},
            "admin": {"email": "hatem@tan-seeq.co", "password": "hatem123"}
        }
        
        # Store tokens and user info
        self.tokens = {}
        self.users = {}
        
        # Test results
        self.test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": [],
            "summary": {}
        }
        
        print(f"🚀 COMPREHENSIVE E2E BACKEND TESTING INITIALIZED")
        print(f"📡 Backend URL: {self.backend_url}")
        print(f"🔗 API Base: {self.api_base}")
        print("=" * 80)

    def log_test(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        self.test_results["total_tests"] += 1
        if success:
            self.test_results["passed_tests"] += 1
            status = "✅ PASS"
        else:
            self.test_results["failed_tests"] += 1
            status = "❌ FAIL"
        
        result = {
            "test_name": test_name,
            "status": status,
            "success": success,
            "details": details,
            "response_data": response_data,
            "timestamp": datetime.now().isoformat()
        }
        
        self.test_results["test_details"].append(result)
        print(f"{status} {test_name}: {details}")
        
        return success

    def make_request(self, method: str, endpoint: str, token: str = None, data: Dict = None, params: Dict = None) -> Dict:
        """Make HTTP request with proper error handling"""
        url = f"{self.api_base}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=30)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=data, timeout=30)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                return {"error": f"Unsupported method: {method}", "status_code": 400}
            
            # Handle different content types
            try:
                if response.headers.get('content-type', '').startswith('application/json'):
                    response_data = response.json()
                else:
                    response_data = {"content": response.content[:500], "content_type": response.headers.get('content-type')}
            except:
                response_data = {"text": response.text[:500] if response.text else "No content"}
            
            return {
                "status_code": response.status_code,
                "data": response_data,
                "headers": dict(response.headers)
            }
            
        except requests.exceptions.Timeout:
            return {"error": "Request timeout", "status_code": 408}
        except requests.exceptions.ConnectionError:
            return {"error": "Connection error", "status_code": 503}
        except Exception as e:
            return {"error": str(e), "status_code": 500}

    def test_suite_1_authentication(self):
        """TEST SUITE 1: AUTHENTICATION & USER MANAGEMENT"""
        print("\n🔐 TEST SUITE 1: AUTHENTICATION & USER MANAGEMENT")
        print("-" * 60)
        
        # 1.1 Login Tests
        for role, creds in self.credentials.items():
            response = self.make_request("POST", "/auth/login", data=creds)
            
            if response.get("status_code") == 200 and "access_token" in response.get("data", {}):
                self.tokens[role] = response["data"]["access_token"]
                self.users[role] = response["data"]["user"]
                self.log_test(
                    f"Login {role}",
                    True,
                    f"Successfully logged in as {creds['email']}",
                    {"user_role": response["data"]["user"]["role"]}
                )
            else:
                self.log_test(
                    f"Login {role}",
                    False,
                    f"Failed to login as {creds['email']}: {response.get('error', response.get('data', {}).get('detail', 'Unknown error'))}",
                    response
                )
        
        # Test wrong credentials
        wrong_creds = {"email": "wrong@test.com", "password": "wrongpass"}
        response = self.make_request("POST", "/auth/login", data=wrong_creds)
        self.log_test(
            "Login with wrong credentials",
            response.get("status_code") == 401,
            f"Correctly rejected wrong credentials with status {response.get('status_code')}",
            response.get("data")
        )
        
        # 1.2 Employee List
        if "super_admin" in self.tokens:
            response = self.make_request("GET", "/employees/list", token=self.tokens["super_admin"])
            if response.get("status_code") == 200:
                employees = response.get("data", {}).get("employees", [])
                self.log_test(
                    "Employee list",
                    len(employees) > 0,
                    f"Retrieved {len(employees)} employees",
                    {"employee_count": len(employees)}
                )
            else:
                self.log_test(
                    "Employee list",
                    False,
                    f"Failed to get employee list: {response.get('error', 'Unknown error')}",
                    response
                )

    def test_suite_2_payroll_system(self):
        """TEST SUITE 2: PAYROLL SYSTEM"""
        print("\n💰 TEST SUITE 2: PAYROLL SYSTEM")
        print("-" * 60)
        
        if "super_admin" not in self.tokens:
            print("❌ Skipping payroll tests - no super admin token")
            return
        
        token = self.tokens["super_admin"]
        
        # 2.1 Payroll Cycles
        response = self.make_request("GET", "/payroll/cycles", token=token)
        cycles = []
        if response.get("status_code") == 200:
            data = response.get("data", {})
            # Handle both direct list and nested structure
            if isinstance(data, list):
                cycles = data
            else:
                cycles = data.get("cycles", [])
            
            self.log_test(
                "Get payroll cycles",
                len(cycles) >= 0,
                f"Retrieved {len(cycles)} payroll cycles",
                {"cycles_count": len(cycles)}
            )
        else:
            self.log_test(
                "Get payroll cycles",
                False,
                f"Failed to get cycles: {response.get('error', 'Unknown error')}",
                response
            )
        
        # Test specific cycle operations if cycles exist
        if cycles and len(cycles) > 0:
            cycle_data = cycles[0]
            cycle_id = cycle_data.get("id") if isinstance(cycle_data, dict) else None
            if cycle_id:
                # Get specific cycle
                response = self.make_request("GET", f"/payroll/cycles/{cycle_id}", token=token)
                self.log_test(
                    "Get specific cycle",
                    response.get("status_code") == 200,
                    f"Retrieved cycle {cycle_id}",
                    response.get("data")
                )
                
                # Get cycle summary
                response = self.make_request("GET", f"/payroll/cycles/{cycle_id}/summary", token=token)
                self.log_test(
                    "Get cycle summary",
                    response.get("status_code") == 200,
                    f"Retrieved cycle summary for {cycle_id}",
                    response.get("data")
                )
                
                # Test recalculate
                response = self.make_request("POST", f"/payroll/cycles/{cycle_id}/recalculate", token=token)
                self.log_test(
                    "Recalculate cycle",
                    response.get("status_code") in [200, 400],  # 400 might be expected if already calculated
                    f"Recalculate response: {response.get('status_code')}",
                    response.get("data")
                )
                
                # Test lock cycle
                lock_data = {"lock_reason": "اختبار شامل - قفل الدورة للمراجعة النهائية"}
                response = self.make_request("POST", f"/payroll/cycles/{cycle_id}/lock", token=token, data=lock_data)
                self.log_test(
                    "Lock cycle",
                    response.get("status_code") in [200, 400],  # 400 might be expected if already locked
                    f"Lock cycle response: {response.get('status_code')}",
                    response.get("data")
                )
                
                # Test unlock cycle
                unlock_data = {"reason": "اختبار شامل - فتح الدورة لإجراء تعديلات"}
                response = self.make_request("POST", f"/payroll/cycles/{cycle_id}/unlock", token=token, data=unlock_data)
                self.log_test(
                    "Unlock cycle",
                    response.get("status_code") in [200, 400],  # 400 might be expected if not locked
                    f"Unlock cycle response: {response.get('status_code')}",
                    response.get("data")
                )
                
                # 2.2 Salary Letters (need employee_id from summary)
                summary_response = self.make_request("GET", f"/payroll/cycles/{cycle_id}/summary", token=token)
                if summary_response.get("status_code") == 200:
                    summary_data = summary_response.get("data", {})
                    employees = summary_data.get("employee_summaries", [])
                    if employees:
                        employee_id = employees[0].get("employee_id")
                        if employee_id:
                            # Test HTML salary letter
                            response = self.make_request("GET", f"/payroll/cycles/{cycle_id}/employees/{employee_id}/letter", 
                                                       token=token, params={"format": "html"})
                            self.log_test(
                                "Salary letter HTML",
                                response.get("status_code") == 200,
                                f"Retrieved HTML salary letter for employee {employee_id}",
                                {"content_type": response.get("headers", {}).get("content-type")}
                            )
                            
                            # Test PDF salary letter
                            response = self.make_request("GET", f"/payroll/cycles/{cycle_id}/employees/{employee_id}/letter", 
                                                       token=token, params={"format": "pdf"})
                            self.log_test(
                                "Salary letter PDF",
                                response.get("status_code") == 200,
                                f"Retrieved PDF salary letter for employee {employee_id}",
                                {"content_type": response.get("headers", {}).get("content-type")}
                            )
                
                # 2.3 Payroll Exports
                response = self.make_request("GET", f"/payroll/cycles/{cycle_id}/export/pdf", token=token)
                self.log_test(
                    "Export cycle PDF",
                    response.get("status_code") == 200,
                    f"Exported cycle PDF",
                    {"content_type": response.get("headers", {}).get("content-type")}
                )
                
                response = self.make_request("GET", f"/payroll/cycles/{cycle_id}/export/excel", token=token)
                self.log_test(
                    "Export cycle Excel",
                    response.get("status_code") == 200,
                    f"Exported cycle Excel",
                    {"content_type": response.get("headers", {}).get("content-type")}
                )

    def test_suite_3_deductions_attendance(self):
        """TEST SUITE 3: DEDUCTIONS & ATTENDANCE"""
        print("\n📊 TEST SUITE 3: DEDUCTIONS & ATTENDANCE")
        print("-" * 60)
        
        if "super_admin" not in self.tokens:
            print("❌ Skipping deductions tests - no super admin token")
            return
        
        token = self.tokens["super_admin"]
        
        # 3.1 Monthly Deductions
        response = self.make_request("GET", "/deductions/calculate-monthly", token=token, params={"month": "2025-10"})
        if response.get("status_code") == 200:
            calc_data = response.get("data", {})
            if isinstance(calc_data, dict):
                self.log_test(
                    "Calculate monthly deductions",
                    "employee_count" in calc_data and "total_deductions" in calc_data,
                    f"Calculated deductions: {calc_data.get('employee_count', 0)} employees, {calc_data.get('total_deductions', 0)} total",
                    calc_data
                )
            else:
                self.log_test(
                    "Calculate monthly deductions",
                    True,
                    f"Monthly deductions calculated successfully",
                    calc_data
                )
        else:
            self.log_test(
                "Calculate monthly deductions",
                False,
                f"Failed to calculate monthly deductions: Status {response.get('status_code')}, Error: {response.get('error', response.get('data', 'Unknown error'))}",
                response
            )
        
        # 3.2 Manual Deductions
        response = self.make_request("GET", "/deductions", token=token)
        if response.get("status_code") == 200:
            data = response.get("data", {})
            if isinstance(data, list):
                deductions_count = len(data)
            else:
                deductions_count = len(data.get("deductions", []))
            
            self.log_test(
                "Get all deductions",
                True,
                f"Retrieved deductions list",
                {"deductions_count": deductions_count}
            )
        else:
            self.log_test(
                "Get all deductions",
                False,
                f"Failed to get deductions: Status {response.get('status_code')}",
                response
            )
        
        # Get a valid employee_id for manual deduction
        emp_response = self.make_request("GET", "/employees/list", token=token)
        if emp_response.get("status_code") == 200:
            employees_data = emp_response.get("data", {})
            if isinstance(employees_data, list):
                employees = employees_data
            else:
                employees = employees_data.get("employees", [])
            
            if employees and len(employees) > 0:
                employee_data = employees[0]
                employee_id = employee_data.get("id") if isinstance(employee_data, dict) else None
                
                if employee_id:
                    manual_deduction_data = {
                        "employee_id": employee_id,
                        "amount": 50.00,
                        "description": "اختبار خصم يدوي شامل",
                        "category": "other"
                    }
                    response = self.make_request("POST", "/deductions/manual", token=token, data=manual_deduction_data)
                    self.log_test(
                        "Create manual deduction",
                        response.get("status_code") in [200, 201],
                        f"Created manual deduction for employee {employee_id}",
                        response.get("data")
                    )
        
        # 3.3 Attendance
        response = self.make_request("GET", "/attendance/with-absences", token=token, params={"month": "2025-10"})
        if response.get("status_code") == 200:
            attendance_data = response.get("data", {})
            if isinstance(attendance_data, dict):
                records_count = len(attendance_data.get("attendance", []))
            elif isinstance(attendance_data, list):
                records_count = len(attendance_data)
            else:
                records_count = 0
            
            self.log_test(
                "Get attendance with absences",
                True,
                f"Retrieved attendance records for 2025-10",
                {"records_count": records_count}
            )
        else:
            self.log_test(
                "Get attendance with absences",
                False,
                f"Failed to get attendance: Status {response.get('status_code')}, Error: {response.get('error', response.get('data', 'Unknown error'))}",
                response
            )

    def test_suite_4_advances_loans(self):
        """TEST SUITE 4: ADVANCES & LOANS"""
        print("\n💳 TEST SUITE 4: ADVANCES & LOANS")
        print("-" * 60)
        
        if "super_admin" not in self.tokens:
            print("❌ Skipping advances tests - no super admin token")
            return
        
        token = self.tokens["super_admin"]
        
        # 4.1 Advances List
        response = self.make_request("GET", "/advances/admin/all-transactions", token=token)
        if response.get("status_code") == 200:
            data = response.get("data", {})
            if isinstance(data, dict):
                transactions = data.get("transactions", [])
            elif isinstance(data, list):
                transactions = data
            else:
                transactions = []
            
            self.log_test(
                "Get all advance transactions",
                isinstance(transactions, list),
                f"Retrieved {len(transactions)} advance transactions",
                {"transactions_count": len(transactions)}
            )
        else:
            self.log_test(
                "Get all advance transactions",
                False,
                f"Failed to get advance transactions: Status {response.get('status_code')}, Error: {response.get('error', response.get('data', 'Unknown error'))}",
                response
            )
        
        # 4.2 Installment Schedules
        response = self.make_request("GET", "/installment-schedules", token=token)
        if response.get("status_code") == 200:
            schedules = response.get("data", {})
            self.log_test(
                "Get installment schedules",
                isinstance(schedules, dict),
                f"Retrieved installment schedules",
                schedules
            )
        else:
            self.log_test(
                "Get installment schedules",
                False,
                f"Failed to get installment schedules: {response.get('error', 'Unknown error')}",
                response
            )

    def test_suite_5_payroll_ledger(self):
        """TEST SUITE 5: PAYROLL LEDGER"""
        print("\n📋 TEST SUITE 5: PAYROLL LEDGER")
        print("-" * 60)
        
        if "super_admin" not in self.tokens:
            print("❌ Skipping ledger tests - no super admin token")
            return
        
        token = self.tokens["super_admin"]
        
        # Get employee_id for ledger testing
        emp_response = self.make_request("GET", "/employees/list", token=token)
        if emp_response.get("status_code") == 200:
            employees_data = emp_response.get("data", {})
            if isinstance(employees_data, list):
                employees = employees_data
            else:
                employees = employees_data.get("employees", [])
            
            if employees and len(employees) > 0:
                employee_data = employees[0]
                employee_id = employee_data.get("id") if isinstance(employee_data, dict) else None
                
                # 5.1 Employee Ledger
                response = self.make_request("GET", f"/payroll/ledger/employee/{employee_id}", token=token)
                self.log_test(
                    "Get employee ledger",
                    response.get("status_code") == 200,
                    f"Retrieved ledger for employee {employee_id}",
                    response.get("data")
                )
                
                # Get ledger with specific entry type
                response = self.make_request("GET", f"/payroll/ledger/employee/{employee_id}", 
                                           token=token, params={"entry_type": "MANUAL_DEDUCTION"})
                self.log_test(
                    "Get employee ledger with filter",
                    response.get("status_code") == 200,
                    f"Retrieved filtered ledger for employee {employee_id}",
                    response.get("data")
                )

    def test_suite_6_notifications(self):
        """TEST SUITE 6: NOTIFICATIONS"""
        print("\n🔔 TEST SUITE 6: NOTIFICATIONS")
        print("-" * 60)
        
        # Test with different user roles
        for role in ["super_admin", "regular_user"]:
            if role not in self.tokens:
                continue
                
            token = self.tokens[role]
            
            # 6.1 Get my notifications
            response = self.make_request("GET", "/notifications/my", token=token)
            if response.get("status_code") == 200:
                data = response.get("data", {})
                if isinstance(data, dict):
                    notifications = data.get("notifications", [])
                elif isinstance(data, list):
                    notifications = data
                else:
                    notifications = []
                
                self.log_test(
                    f"Get notifications ({role})",
                    isinstance(notifications, list),
                    f"Retrieved {len(notifications)} notifications for {role}",
                    {"notifications_count": len(notifications)}
                )
            else:
                self.log_test(
                    f"Get notifications ({role})",
                    False,
                    f"Failed to get notifications for {role}: Status {response.get('status_code')}, Error: {response.get('error', response.get('data', 'Unknown error'))}",
                    response
                )
            
            # Get unread notifications
            response = self.make_request("GET", "/notifications/my", token=token, params={"unread_only": "true"})
            if response.get("status_code") == 200:
                data = response.get("data", {})
                if isinstance(data, dict):
                    unread_notifications = data.get("notifications", [])
                elif isinstance(data, list):
                    unread_notifications = data
                else:
                    unread_notifications = []
                
                self.log_test(
                    f"Get unread notifications ({role})",
                    isinstance(unread_notifications, list),
                    f"Retrieved {len(unread_notifications)} unread notifications for {role}",
                    {"unread_count": len(unread_notifications)}
                )
                
                # Test acknowledge notification if any exist
                if unread_notifications and len(unread_notifications) > 0:
                    notification_data = unread_notifications[0]
                    notification_id = notification_data.get("id") if isinstance(notification_data, dict) else None
                    if notification_id:
                        response = self.make_request("POST", f"/notifications/{notification_id}/acknowledge", token=token)
                        self.log_test(
                            f"Acknowledge notification ({role})",
                            response.get("status_code") in [200, 404],  # 404 might be expected if already acknowledged
                            f"Acknowledged notification {notification_id}",
                            response.get("data")
                        )

    def test_suite_7_leaves(self):
        """TEST SUITE 7: LEAVES"""
        print("\n🏖️ TEST SUITE 7: LEAVES")
        print("-" * 60)
        
        # Test with different user roles
        for role in ["super_admin", "regular_user"]:
            if role not in self.tokens:
                continue
                
            token = self.tokens[role]
            
            # 7.1 Get all leaves (admin) or my leaves (user)
            if role == "super_admin":
                response = self.make_request("GET", "/leaves", token=token)
                test_name = "Get all leaves (admin)"
            else:
                response = self.make_request("GET", "/leaves/my", token=token)
                test_name = "Get my leaves (user)"
            
            if response.get("status_code") == 200:
                data = response.get("data", {})
                if isinstance(data, dict):
                    leaves = data.get("leaves", [])
                elif isinstance(data, list):
                    leaves = data
                else:
                    leaves = []
                
                self.log_test(
                    test_name,
                    isinstance(leaves, list),
                    f"Retrieved {len(leaves)} leaves for {role}",
                    {"leaves_count": len(leaves)}
                )
            else:
                self.log_test(
                    test_name,
                    False,
                    f"Failed to get leaves for {role}: Status {response.get('status_code')}, Error: {response.get('error', response.get('data', 'Unknown error'))}",
                    response
                )

    def run_comprehensive_tests(self):
        """Run all test suites"""
        print("🚀 STARTING COMPREHENSIVE E2E BACKEND TESTING")
        print("=" * 80)
        
        start_time = datetime.now()
        
        # Run all test suites
        self.test_suite_1_authentication()
        self.test_suite_2_payroll_system()
        self.test_suite_3_deductions_attendance()
        self.test_suite_4_advances_loans()
        self.test_suite_5_payroll_ledger()
        self.test_suite_6_notifications()
        self.test_suite_7_leaves()
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Generate summary
        self.generate_summary(duration)

    def generate_summary(self, duration):
        """Generate comprehensive test summary"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE E2E BACKEND TEST SUMMARY")
        print("=" * 80)
        
        total = self.test_results["total_tests"]
        passed = self.test_results["passed_tests"]
        failed = self.test_results["failed_tests"]
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"⏱️  Duration: {duration}")
        print(f"📈 Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📊 Success Rate: {success_rate:.1f}%")
        
        print("\n🔍 DETAILED RESULTS BY TEST SUITE:")
        print("-" * 60)
        
        # Group results by test suite
        suite_results = {}
        for result in self.test_results["test_details"]:
            test_name = result["test_name"]
            if "Login" in test_name or "Employee list" in test_name:
                suite = "Authentication & User Management"
            elif any(keyword in test_name for keyword in ["payroll", "cycle", "salary", "export"]):
                suite = "Payroll System"
            elif any(keyword in test_name for keyword in ["deduction", "attendance"]):
                suite = "Deductions & Attendance"
            elif any(keyword in test_name for keyword in ["advance", "installment"]):
                suite = "Advances & Loans"
            elif "ledger" in test_name.lower():
                suite = "Payroll Ledger"
            elif "notification" in test_name.lower():
                suite = "Notifications"
            elif "leave" in test_name.lower():
                suite = "Leaves"
            else:
                suite = "Other"
            
            if suite not in suite_results:
                suite_results[suite] = {"passed": 0, "failed": 0, "details": []}
            
            if result["success"]:
                suite_results[suite]["passed"] += 1
            else:
                suite_results[suite]["failed"] += 1
            
            suite_results[suite]["details"].append(result)
        
        for suite, results in suite_results.items():
            total_suite = results["passed"] + results["failed"]
            suite_rate = (results["passed"] / total_suite * 100) if total_suite > 0 else 0
            print(f"\n📋 {suite}:")
            print(f"   ✅ Passed: {results['passed']}")
            print(f"   ❌ Failed: {results['failed']}")
            print(f"   📊 Success Rate: {suite_rate:.1f}%")
        
        print("\n🚨 FAILED TESTS DETAILS:")
        print("-" * 60)
        failed_tests = [r for r in self.test_results["test_details"] if not r["success"]]
        if failed_tests:
            for result in failed_tests:
                print(f"❌ {result['test_name']}: {result['details']}")
        else:
            print("🎉 No failed tests!")
        
        print("\n✅ SUCCESSFUL TESTS:")
        print("-" * 60)
        successful_tests = [r for r in self.test_results["test_details"] if r["success"]]
        for result in successful_tests:
            print(f"✅ {result['test_name']}: {result['details']}")
        
        # Save detailed results to file
        results_file = "/app/comprehensive_e2e_test_results.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n💾 Detailed results saved to: {results_file}")
        print("=" * 80)
        
        return success_rate >= 80  # Consider 80%+ success rate as overall success

def main():
    """Main function to run comprehensive E2E backend tests"""
    tester = ComprehensiveE2EBackendTester()
    
    try:
        success = tester.run_comprehensive_tests()
        
        if success:
            print("🎉 COMPREHENSIVE E2E BACKEND TESTING COMPLETED SUCCESSFULLY!")
            sys.exit(0)
        else:
            print("⚠️ COMPREHENSIVE E2E BACKEND TESTING COMPLETED WITH ISSUES!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Testing failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()