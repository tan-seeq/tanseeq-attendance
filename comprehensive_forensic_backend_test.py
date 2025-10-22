#!/usr/bin/env python3
"""
🔥 COMPREHENSIVE END-TO-END BACKEND TESTING - FORENSIC LEVEL
Comprehensive system testing from scratch as requested in review
"""

import requests
import json
import os
from datetime import datetime, timedelta
import uuid

# Configuration
BACKEND_URL = "https://tanseeq-attendance.preview.emergentagent.com/api"

# Test Credentials as specified in review
TEST_CREDENTIALS = {
    "super_admin": {"email": "admin@tanseeq.com", "password": "ADMIN"},
    "admin": {"email": "mahmoud@tanseeq.com", "password": "mahmoud123"},
    "user": {"email": "jihad@tanseeq.com", "password": "jihad123"}
}

class ComprehensiveBackendTester:
    def __init__(self):
        self.tokens = {}
        self.test_results = []
        self.evidence = {}
        
    def log_test(self, test_name, success, details, response_data=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {details}")
        
    def authenticate_all_users(self):
        """1. AUTHENTICATION & USER MANAGEMENT"""
        print("\n🔐 1. AUTHENTICATION & USER MANAGEMENT TESTING")
        
        for role, creds in TEST_CREDENTIALS.items():
            try:
                response = requests.post(f"{BACKEND_URL}/auth/login", json=creds)
                
                if response.status_code == 200:
                    data = response.json()
                    self.tokens[role] = data["access_token"]
                    self.log_test(
                        f"Login {role}",
                        True,
                        f"Successfully logged in as {role} ({creds['email']})",
                        {"user_id": data["user"]["id"], "role": data["user"]["role"]}
                    )
                    
                    # Test /auth/me endpoint
                    headers = {"Authorization": f"Bearer {self.tokens[role]}"}
                    me_response = requests.get(f"{BACKEND_URL}/auth/me", headers=headers)
                    
                    if me_response.status_code == 200:
                        self.log_test(
                            f"Auth/me {role}",
                            True,
                            f"Successfully retrieved user info for {role}",
                            me_response.json()
                        )
                    else:
                        self.log_test(
                            f"Auth/me {role}",
                            False,
                            f"Failed to get user info: {me_response.status_code}",
                            me_response.text
                        )
                        
                else:
                    self.log_test(
                        f"Login {role}",
                        False,
                        f"Login failed: {response.status_code} - {response.text}"
                    )
                    
            except Exception as e:
                self.log_test(f"Login {role}", False, f"Exception: {str(e)}")
        
        # Test invalid credentials
        try:
            invalid_response = requests.post(f"{BACKEND_URL}/auth/login", 
                                          json={"email": "invalid@test.com", "password": "wrong"})
            if invalid_response.status_code == 401:
                self.log_test("Invalid credentials test", True, "Correctly rejected invalid credentials")
            else:
                self.log_test("Invalid credentials test", False, f"Unexpected response: {invalid_response.status_code}")
        except Exception as e:
            self.log_test("Invalid credentials test", False, f"Exception: {str(e)}")
    
    def test_attendance_system(self):
        """2. ATTENDANCE SYSTEM (CRITICAL)"""
        print("\n⏰ 2. ATTENDANCE SYSTEM TESTING")
        
        # Test as User (jihad)
        if "user" in self.tokens:
            headers = {"Authorization": f"Bearer {self.tokens['user']}"}
            
            # Test check-in
            try:
                checkin_response = requests.post(f"{BACKEND_URL}/attendance/check-in", headers=headers)
                if checkin_response.status_code in [200, 400]:  # 400 if already checked in
                    self.log_test(
                        "User check-in",
                        True,
                        f"Check-in response: {checkin_response.status_code}",
                        checkin_response.json()
                    )
                else:
                    self.log_test(
                        "User check-in",
                        False,
                        f"Unexpected check-in response: {checkin_response.status_code}",
                        checkin_response.text
                    )
            except Exception as e:
                self.log_test("User check-in", False, f"Exception: {str(e)}")
            
            # Test get own attendance
            try:
                attendance_response = requests.get(f"{BACKEND_URL}/attendance", headers=headers)
                if attendance_response.status_code == 200:
                    data = attendance_response.json()
                    self.log_test(
                        "User attendance records",
                        True,
                        f"Retrieved {len(data)} attendance records",
                        {"count": len(data), "sample": data[:2] if data else []}
                    )
                else:
                    self.log_test(
                        "User attendance records",
                        False,
                        f"Failed to get attendance: {attendance_response.status_code}",
                        attendance_response.text
                    )
            except Exception as e:
                self.log_test("User attendance records", False, f"Exception: {str(e)}")
        
        # Test as Super Admin
        if "super_admin" in self.tokens:
            headers = {"Authorization": f"Bearer {self.tokens['super_admin']}"}
            
            # Test get all attendance records
            try:
                all_attendance_response = requests.get(f"{BACKEND_URL}/attendance", headers=headers)
                if all_attendance_response.status_code == 200:
                    data = all_attendance_response.json()
                    self.log_test(
                        "Super Admin all attendance",
                        True,
                        f"Retrieved {len(data)} total attendance records",
                        {"count": len(data)}
                    )
                    
                    # Check for 9:15 AM late tracking rule
                    late_records = [r for r in data if r.get("late_minutes", 0) > 0]
                    self.log_test(
                        "9:15 AM late tracking verification",
                        len(late_records) > 0,
                        f"Found {len(late_records)} records with late_minutes > 0",
                        {"late_records_count": len(late_records)}
                    )
                    
                else:
                    self.log_test(
                        "Super Admin all attendance",
                        False,
                        f"Failed to get all attendance: {all_attendance_response.status_code}",
                        all_attendance_response.text
                    )
            except Exception as e:
                self.log_test("Super Admin all attendance", False, f"Exception: {str(e)}")
    
    def test_deductions_system(self):
        """3. ADVANCED DEDUCTIONS SYSTEM (CRITICAL)"""
        print("\n💰 3. ADVANCED DEDUCTIONS SYSTEM TESTING")
        
        if "super_admin" in self.tokens:
            headers = {"Authorization": f"Bearer {self.tokens['super_admin']}"}
            
            # Test monthly deductions calculation
            try:
                month = "2025-10"
                monthly_response = requests.post(f"{BACKEND_URL}/deductions/calculate-monthly?month={month}", headers=headers)
                if monthly_response.status_code == 200:
                    data = monthly_response.json()
                    self.log_test(
                        "Monthly deductions calculation",
                        True,
                        f"Successfully calculated monthly deductions for {month}",
                        {"employee_count": len(data) if isinstance(data, list) else "N/A"}
                    )
                else:
                    self.log_test(
                        "Monthly deductions calculation",
                        False,
                        f"Failed monthly calculation: {monthly_response.status_code}",
                        monthly_response.text
                    )
            except Exception as e:
                self.log_test("Monthly deductions calculation", False, f"Exception: {str(e)}")
            
            # Test custom date range calculation
            try:
                custom_response = requests.post(
                    f"{BACKEND_URL}/deductions/calculate?from=2025-10-01&to=2025-10-31", 
                    headers=headers
                )
                if custom_response.status_code == 200:
                    self.log_test(
                        "Custom date range deductions",
                        True,
                        "Successfully calculated custom date range deductions"
                    )
                else:
                    self.log_test(
                        "Custom date range deductions",
                        False,
                        f"Failed custom calculation: {custom_response.status_code}",
                        custom_response.text
                    )
            except Exception as e:
                self.log_test("Custom date range deductions", False, f"Exception: {str(e)}")
            
            # Test apply monthly deductions
            try:
                apply_response = requests.post(f"{BACKEND_URL}/deductions/apply-monthly", headers=headers)
                if apply_response.status_code in [200, 400]:  # 400 if already applied
                    self.log_test(
                        "Apply monthly deductions",
                        True,
                        f"Apply deductions response: {apply_response.status_code}"
                    )
                else:
                    self.log_test(
                        "Apply monthly deductions",
                        False,
                        f"Failed to apply deductions: {apply_response.status_code}",
                        apply_response.text
                    )
            except Exception as e:
                self.log_test("Apply monthly deductions", False, f"Exception: {str(e)}")
    
    def test_payroll_system(self):
        """4. PAYROLL SYSTEM (CRITICAL)"""
        print("\n💼 4. PAYROLL SYSTEM TESTING")
        
        if "super_admin" in self.tokens:
            headers = {"Authorization": f"Bearer {self.tokens['super_admin']}"}
            
            # Test get payroll cycles
            try:
                cycles_response = requests.get(f"{BACKEND_URL}/payroll/cycles", headers=headers)
                if cycles_response.status_code == 200:
                    cycles = cycles_response.json()
                    self.log_test(
                        "Payroll cycles list",
                        True,
                        f"Retrieved {len(cycles)} payroll cycles",
                        {"cycles_count": len(cycles)}
                    )
                    
                    # Test cycle details if cycles exist
                    if cycles:
                        cycle_id = cycles[0]["id"]
                        
                        # Test cycle details
                        detail_response = requests.get(f"{BACKEND_URL}/payroll/cycles/{cycle_id}", headers=headers)
                        if detail_response.status_code == 200:
                            self.log_test(
                                "Payroll cycle details",
                                True,
                                f"Retrieved details for cycle {cycle_id}"
                            )
                        else:
                            self.log_test(
                                "Payroll cycle details",
                                False,
                                f"Failed to get cycle details: {detail_response.status_code}"
                            )
                        
                        # Test cycle summary
                        summary_response = requests.get(f"{BACKEND_URL}/payroll/cycles/{cycle_id}/summary", headers=headers)
                        if summary_response.status_code == 200:
                            self.log_test(
                                "Payroll cycle summary",
                                True,
                                f"Retrieved summary for cycle {cycle_id}"
                            )
                        else:
                            self.log_test(
                                "Payroll cycle summary",
                                False,
                                f"Failed to get cycle summary: {summary_response.status_code}"
                            )
                        
                        # Test FIXED ledger endpoint
                        ledger_response = requests.get(f"{BACKEND_URL}/payroll/cycles/{cycle_id}/ledger", headers=headers)
                        if ledger_response.status_code == 200:
                            ledger_data = ledger_response.json()
                            self.log_test(
                                "Payroll ledger (FIXED)",
                                True,
                                f"Successfully retrieved ledger entries",
                                {"entries_count": len(ledger_data) if isinstance(ledger_data, list) else "N/A"}
                            )
                        else:
                            self.log_test(
                                "Payroll ledger (FIXED)",
                                False,
                                f"Ledger endpoint failed: {ledger_response.status_code} (should not be 405)",
                                ledger_response.text
                            )
                        
                else:
                    self.log_test(
                        "Payroll cycles list",
                        False,
                        f"Failed to get cycles: {cycles_response.status_code}",
                        cycles_response.text
                    )
            except Exception as e:
                self.log_test("Payroll cycles list", False, f"Exception: {str(e)}")
    
    def test_advances_system(self):
        """6. ADVANCES & CUSTODY SYSTEM"""
        print("\n💳 6. ADVANCES & CUSTODY SYSTEM TESTING")
        
        # Test as User (jihad)
        if "user" in self.tokens:
            headers = {"Authorization": f"Bearer {self.tokens['user']}"}
            
            # Test get my balance
            try:
                balance_response = requests.get(f"{BACKEND_URL}/advances/my-balance", headers=headers)
                if balance_response.status_code == 200:
                    balance_data = balance_response.json()
                    self.log_test(
                        "User balance retrieval",
                        True,
                        f"Retrieved balance: {balance_data.get('total_available', 'N/A')} AED",
                        balance_data
                    )
                else:
                    self.log_test(
                        "User balance retrieval",
                        False,
                        f"Failed to get balance: {balance_response.status_code}",
                        balance_response.text
                    )
            except Exception as e:
                self.log_test("User balance retrieval", False, f"Exception: {str(e)}")
            
            # Test get my transactions
            try:
                transactions_response = requests.get(f"{BACKEND_URL}/advances/my-transactions", headers=headers)
                if transactions_response.status_code == 200:
                    transactions_data = transactions_response.json()
                    transactions = transactions_data.get("transactions", [])
                    self.log_test(
                        "User transactions retrieval",
                        True,
                        f"Retrieved {len(transactions)} transactions",
                        {"transactions_count": len(transactions)}
                    )
                else:
                    self.log_test(
                        "User transactions retrieval",
                        False,
                        f"Failed to get transactions: {transactions_response.status_code}",
                        transactions_response.text
                    )
            except Exception as e:
                self.log_test("User transactions retrieval", False, f"Exception: {str(e)}")
        
        # Test as Super Admin
        if "super_admin" in self.tokens:
            headers = {"Authorization": f"Bearer {self.tokens['super_admin']}"}
            
            # Test get all balances
            try:
                all_balances_response = requests.get(f"{BACKEND_URL}/advances/admin/all-balances", headers=headers)
                if all_balances_response.status_code == 200:
                    balances_data = all_balances_response.json()
                    balances = balances_data.get("employee_balances", [])
                    self.log_test(
                        "Admin all balances",
                        True,
                        f"Retrieved balances for {len(balances)} employees",
                        {"employees_count": len(balances)}
                    )
                else:
                    self.log_test(
                        "Admin all balances",
                        False,
                        f"Failed to get all balances: {all_balances_response.status_code}",
                        all_balances_response.text
                    )
            except Exception as e:
                self.log_test("Admin all balances", False, f"Exception: {str(e)}")
            
            # Test pending approvals
            try:
                pending_response = requests.get(f"{BACKEND_URL}/advances/admin/pending-approvals", headers=headers)
                if pending_response.status_code == 200:
                    pending_data = pending_response.json()
                    pending = pending_data.get("pending_transactions", [])
                    self.log_test(
                        "Admin pending approvals",
                        True,
                        f"Retrieved {len(pending)} pending transactions",
                        {"pending_count": len(pending)}
                    )
                else:
                    self.log_test(
                        "Admin pending approvals",
                        False,
                        f"Failed to get pending approvals: {pending_response.status_code}",
                        pending_response.text
                    )
            except Exception as e:
                self.log_test("Admin pending approvals", False, f"Exception: {str(e)}")
            
            # Test all transactions
            try:
                all_transactions_response = requests.get(f"{BACKEND_URL}/advances/admin/all-transactions", headers=headers)
                if all_transactions_response.status_code == 200:
                    all_transactions_data = all_transactions_response.json()
                    all_transactions = all_transactions_data.get("transactions", [])
                    self.log_test(
                        "Admin all transactions",
                        True,
                        f"Retrieved {len(all_transactions)} total transactions",
                        {"total_transactions": len(all_transactions)}
                    )
                else:
                    self.log_test(
                        "Admin all transactions",
                        False,
                        f"Failed to get all transactions: {all_transactions_response.status_code}",
                        all_transactions_response.text
                    )
            except Exception as e:
                self.log_test("Admin all transactions", False, f"Exception: {str(e)}")
    
    def test_leave_management(self):
        """7. LEAVE MANAGEMENT"""
        print("\n🏖️ 7. LEAVE MANAGEMENT TESTING")
        
        # Test as User
        if "user" in self.tokens:
            headers = {"Authorization": f"Bearer {self.tokens['user']}"}
            
            try:
                my_leaves_response = requests.get(f"{BACKEND_URL}/leaves/my", headers=headers)
                if my_leaves_response.status_code == 200:
                    leaves_data = my_leaves_response.json()
                    self.log_test(
                        "User leave requests",
                        True,
                        f"Retrieved {len(leaves_data)} leave requests",
                        {"leaves_count": len(leaves_data)}
                    )
                else:
                    self.log_test(
                        "User leave requests",
                        False,
                        f"Failed to get user leaves: {my_leaves_response.status_code}",
                        my_leaves_response.text
                    )
            except Exception as e:
                self.log_test("User leave requests", False, f"Exception: {str(e)}")
        
        # Test as Admin
        if "admin" in self.tokens:
            headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            
            try:
                all_leaves_response = requests.get(f"{BACKEND_URL}/leaves", headers=headers)
                if all_leaves_response.status_code == 200:
                    all_leaves_data = all_leaves_response.json()
                    self.log_test(
                        "Admin all leave requests",
                        True,
                        f"Retrieved {len(all_leaves_data)} total leave requests",
                        {"total_leaves": len(all_leaves_data)}
                    )
                else:
                    self.log_test(
                        "Admin all leave requests",
                        False,
                        f"Failed to get all leaves: {all_leaves_response.status_code}",
                        all_leaves_response.text
                    )
            except Exception as e:
                self.log_test("Admin all leave requests", False, f"Exception: {str(e)}")
    
    def test_work_reports(self):
        """8. WORK REPORTS (MongoDB)"""
        print("\n📊 8. WORK REPORTS SYSTEM TESTING")
        
        if "admin" in self.tokens:
            headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            
            # Test get clients
            try:
                clients_response = requests.get(f"{BACKEND_URL}/work-reports/clients", headers=headers)
                if clients_response.status_code == 200:
                    clients_data = clients_response.json()
                    self.log_test(
                        "Work reports clients",
                        True,
                        f"Retrieved {len(clients_data)} clients",
                        {"clients_count": len(clients_data)}
                    )
                else:
                    self.log_test(
                        "Work reports clients",
                        False,
                        f"Failed to get clients: {clients_response.status_code}",
                        clients_response.text
                    )
            except Exception as e:
                self.log_test("Work reports clients", False, f"Exception: {str(e)}")
            
            # Test get work logs
            try:
                logs_response = requests.get(f"{BACKEND_URL}/work-reports/logs", headers=headers)
                if logs_response.status_code == 200:
                    logs_data = logs_response.json()
                    self.log_test(
                        "Work reports logs",
                        True,
                        f"Retrieved work logs successfully",
                        {"response_type": type(logs_data).__name__}
                    )
                else:
                    self.log_test(
                        "Work reports logs",
                        False,
                        f"Failed to get work logs: {logs_response.status_code}",
                        logs_response.text
                    )
            except Exception as e:
                self.log_test("Work reports logs", False, f"Exception: {str(e)}")
    
    def test_notifications(self):
        """9. NOTIFICATIONS SYSTEM"""
        print("\n🔔 9. NOTIFICATIONS SYSTEM TESTING")
        
        # Test as User
        if "user" in self.tokens:
            headers = {"Authorization": f"Bearer {self.tokens['user']}"}
            
            try:
                my_notifications_response = requests.get(f"{BACKEND_URL}/notifications/my", headers=headers)
                if my_notifications_response.status_code == 200:
                    notifications_data = my_notifications_response.json()
                    self.log_test(
                        "User notifications",
                        True,
                        f"Retrieved {len(notifications_data)} notifications",
                        {"notifications_count": len(notifications_data)}
                    )
                else:
                    self.log_test(
                        "User notifications",
                        False,
                        f"Failed to get user notifications: {my_notifications_response.status_code}",
                        my_notifications_response.text
                    )
            except Exception as e:
                self.log_test("User notifications", False, f"Exception: {str(e)}")
            
            # Test unread mandatory notifications
            try:
                unread_response = requests.get(f"{BACKEND_URL}/notifications/unread-mandatory", headers=headers)
                if unread_response.status_code == 200:
                    unread_data = unread_response.json()
                    self.log_test(
                        "Unread mandatory notifications",
                        True,
                        f"Retrieved unread mandatory notifications",
                        {"unread_count": len(unread_data) if isinstance(unread_data, list) else "N/A"}
                    )
                else:
                    self.log_test(
                        "Unread mandatory notifications",
                        False,
                        f"Failed to get unread notifications: {unread_response.status_code}",
                        unread_response.text
                    )
            except Exception as e:
                self.log_test("Unread mandatory notifications", False, f"Exception: {str(e)}")
        
        # Test as Super Admin
        if "super_admin" in self.tokens:
            headers = {"Authorization": f"Bearer {self.tokens['super_admin']}"}
            
            try:
                all_notifications_response = requests.get(f"{BACKEND_URL}/notifications", headers=headers)
                if all_notifications_response.status_code == 200:
                    all_notifications_data = all_notifications_response.json()
                    self.log_test(
                        "Admin all notifications",
                        True,
                        f"Retrieved {len(all_notifications_data)} total notifications",
                        {"total_notifications": len(all_notifications_data)}
                    )
                else:
                    self.log_test(
                        "Admin all notifications",
                        False,
                        f"Failed to get all notifications: {all_notifications_response.status_code}",
                        all_notifications_response.text
                    )
            except Exception as e:
                self.log_test("Admin all notifications", False, f"Exception: {str(e)}")
    
    def test_marketing_visits(self):
        """10. MARKETING VISITS"""
        print("\n🚗 10. MARKETING VISITS TESTING")
        
        if "user" in self.tokens:
            headers = {"Authorization": f"Bearer {self.tokens['user']}"}
            
            # Test get active visit
            try:
                active_response = requests.get(f"{BACKEND_URL}/marketing-visits/active", headers=headers)
                if active_response.status_code == 200:
                    active_data = active_response.json()
                    self.log_test(
                        "Marketing visits active",
                        True,
                        f"Retrieved active visit status",
                        active_data
                    )
                else:
                    self.log_test(
                        "Marketing visits active",
                        False,
                        f"Failed to get active visit: {active_response.status_code}",
                        active_response.text
                    )
            except Exception as e:
                self.log_test("Marketing visits active", False, f"Exception: {str(e)}")
    
    def test_health_endpoints(self):
        """13. HEALTH & INFRASTRUCTURE"""
        print("\n🏥 13. HEALTH & INFRASTRUCTURE TESTING")
        
        # Test health endpoint
        try:
            health_response = requests.get(f"{BACKEND_URL}/healthz")
            if health_response.status_code == 200:
                self.log_test(
                    "Health check",
                    True,
                    "Health endpoint responding correctly"
                )
            else:
                self.log_test(
                    "Health check",
                    False,
                    f"Health endpoint failed: {health_response.status_code}"
                )
        except Exception as e:
            self.log_test("Health check", False, f"Exception: {str(e)}")
        
        # Test readiness endpoint
        try:
            ready_response = requests.get(f"{BACKEND_URL}/readyz")
            if ready_response.status_code == 200:
                self.log_test(
                    "Readiness check",
                    True,
                    "Readiness endpoint responding correctly"
                )
            else:
                self.log_test(
                    "Readiness check",
                    False,
                    f"Readiness endpoint failed: {ready_response.status_code}"
                )
        except Exception as e:
            self.log_test("Readiness check", False, f"Exception: {str(e)}")
        
        # Test root endpoint
        try:
            # Remove /api from root endpoint
            root_url = BACKEND_URL.replace("/api", "")
            root_response = requests.get(root_url)
            if root_response.status_code == 200:
                self.log_test(
                    "Root endpoint",
                    True,
                    "Root endpoint responding correctly"
                )
            else:
                self.log_test(
                    "Root endpoint",
                    False,
                    f"Root endpoint failed: {root_response.status_code}"
                )
        except Exception as e:
            self.log_test("Root endpoint", False, f"Exception: {str(e)}")
    
    def test_rbac_enforcement(self):
        """Test Role-Based Access Control"""
        print("\n🔒 RBAC ENFORCEMENT TESTING")
        
        if "user" in self.tokens:
            headers = {"Authorization": f"Bearer {self.tokens['user']}"}
            
            # Test user trying to access admin endpoint (should get 403)
            try:
                forbidden_response = requests.get(f"{BACKEND_URL}/advances/admin/all-balances", headers=headers)
                if forbidden_response.status_code == 403:
                    self.log_test(
                        "RBAC enforcement",
                        True,
                        "User correctly denied access to admin endpoint (403)"
                    )
                else:
                    self.log_test(
                        "RBAC enforcement",
                        False,
                        f"RBAC failed - expected 403, got {forbidden_response.status_code}"
                    )
            except Exception as e:
                self.log_test("RBAC enforcement", False, f"Exception: {str(e)}")
    
    def run_comprehensive_test(self):
        """Run all comprehensive tests"""
        print("🔥 STARTING COMPREHENSIVE END-TO-END BACKEND TESTING - FORENSIC LEVEL")
        print("=" * 80)
        
        # Run all test modules
        self.authenticate_all_users()
        self.test_attendance_system()
        self.test_deductions_system()
        self.test_payroll_system()
        self.test_advances_system()
        self.test_leave_management()
        self.test_work_reports()
        self.test_notifications()
        self.test_marketing_visits()
        self.test_health_endpoints()
        self.test_rbac_enforcement()
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate comprehensive test summary"""
        print("\n" + "=" * 80)
        print("🎯 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 OVERALL RESULTS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests} ✅")
        print(f"   Failed: {failed_tests} ❌")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        # Critical system assessment
        critical_modules = [
            "Authentication", "Attendance", "Deductions", "Payroll", "Advances"
        ]
        
        print(f"\n🔥 CRITICAL MODULES STATUS:")
        for module in critical_modules:
            module_tests = [t for t in self.test_results if module.lower() in t["test"].lower()]
            if module_tests:
                module_passed = len([t for t in module_tests if t["success"]])
                module_total = len(module_tests)
                module_rate = (module_passed / module_total * 100) if module_total > 0 else 0
                status = "🟢 OPERATIONAL" if module_rate >= 80 else "🔴 CRITICAL ISSUES"
                print(f"   {module}: {module_passed}/{module_total} ({module_rate:.1f}%) {status}")
        
        # Failed tests details
        failed_test_results = [t for t in self.test_results if not t["success"]]
        if failed_test_results:
            print(f"\n❌ FAILED TESTS DETAILS:")
            for test in failed_test_results:
                print(f"   • {test['test']}: {test['details']}")
        
        # Production readiness assessment
        if success_rate >= 90:
            print(f"\n🟢 PRODUCTION READINESS: EXCELLENT ({success_rate:.1f}%)")
        elif success_rate >= 75:
            print(f"\n🟡 PRODUCTION READINESS: GOOD ({success_rate:.1f}%) - Minor issues need attention")
        else:
            print(f"\n🔴 PRODUCTION READINESS: CRITICAL ISSUES ({success_rate:.1f}%) - Major fixes required")
        
        # Save detailed results
        self.save_results()
    
    def save_results(self):
        """Save detailed test results to file"""
        results_file = "comprehensive_forensic_test_results.json"
        
        summary_data = {
            "test_run": {
                "timestamp": datetime.now().isoformat(),
                "backend_url": BACKEND_URL,
                "total_tests": len(self.test_results),
                "passed_tests": len([t for t in self.test_results if t["success"]]),
                "failed_tests": len([t for t in self.test_results if not t["success"]]),
                "success_rate": (len([t for t in self.test_results if t["success"]]) / len(self.test_results) * 100) if self.test_results else 0
            },
            "test_results": self.test_results,
            "evidence": self.evidence
        }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Detailed results saved to: {results_file}")

if __name__ == "__main__":
    tester = ComprehensiveBackendTester()
    tester.run_comprehensive_test()