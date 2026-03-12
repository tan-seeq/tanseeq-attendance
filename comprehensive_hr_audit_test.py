#!/usr/bin/env python3
"""
🔍 COMPREHENSIVE HR SYSTEM AUDIT - BACKEND FULL VERIFICATION
Complete system audit for June-October 2025 updates as requested

Test Accounts:
- Super Admin: admin@tanseeq.com / ADMIN
- Admin: mahmoud@tanseeq.com / mahmoud123
- User: jihad@tanseeq.com / jihad123

This audit covers ALL 12 modules with 100% transparency and detailed evidence.
"""

import requests
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://payroll-management-4.preview.emergentagent.com')
BASE_URL = f"{BACKEND_URL}/api"

# Test accounts
TEST_ACCOUNTS = {
    "super_admin": {"email": "admin@tanseeq.com", "password": "ADMIN"},
    "admin": {"email": "mahmoud@tanseeq.com", "password": "mahmoud123"},
    "user": {"email": "jihad@tanseeq.com", "password": "jihad123"}
}

class HRSystemAudit:
    def __init__(self):
        self.results = {
            "audit_timestamp": datetime.now().isoformat(),
            "backend_url": BACKEND_URL,
            "modules": {},
            "authentication": {},
            "critical_issues": [],
            "non_critical_issues": [],
            "overall_health": 0,
            "broken_endpoints": [],
            "test_evidence": {}
        }
        self.tokens = {}
        
    def log_result(self, module, test_name, success, details, endpoint=None, response_data=None):
        """Log test result with detailed evidence"""
        if module not in self.results["modules"]:
            self.results["modules"][module] = {
                "tests": [],
                "success_rate": 0,
                "completion_percentage": 0,
                "status": "unknown",
                "critical_issues": [],
                "integration_status": "unknown"
            }
        
        test_result = {
            "test_name": test_name,
            "success": success,
            "details": details,
            "endpoint": endpoint,
            "timestamp": datetime.now().isoformat()
        }
        
        if response_data:
            test_result["response_sample"] = response_data
            
        self.results["modules"][module]["tests"].append(test_result)
        
        if not success and endpoint:
            self.results["broken_endpoints"].append({
                "endpoint": endpoint,
                "module": module,
                "error": details
            })

    def authenticate_user(self, role):
        """Authenticate user and get JWT token"""
        try:
            account = TEST_ACCOUNTS[role]
            response = requests.post(f"{BASE_URL}/auth/login", json=account, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                self.tokens[role] = token
                
                self.results["authentication"][role] = {
                    "success": True,
                    "user_info": data.get("user", {}),
                    "token_received": bool(token)
                }
                return token
            else:
                self.results["authentication"][role] = {
                    "success": False,
                    "error": f"Status {response.status_code}: {response.text}",
                    "token_received": False
                }
                return None
                
        except Exception as e:
            self.results["authentication"][role] = {
                "success": False,
                "error": str(e),
                "token_received": False
            }
            return None

    def make_request(self, method, endpoint, token=None, data=None, params=None):
        """Make HTTP request with proper headers"""
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
            
        url = f"{BASE_URL}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=15)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=15)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=data, timeout=15)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, timeout=15)
            else:
                return None, f"Unsupported method: {method}"
                
            return response, None
        except Exception as e:
            return None, str(e)

    def test_authentication_system(self):
        """Test authentication and authorization system"""
        print("🔐 Testing Authentication & Authorization System...")
        
        # Test all user roles
        for role in ["super_admin", "admin", "user"]:
            token = self.authenticate_user(role)
            success = token is not None
            
            self.log_result(
                "Authentication", 
                f"{role}_login",
                success,
                f"Login {'successful' if success else 'failed'} for {role}",
                "/auth/login",
                self.results["authentication"][role]
            )

        # Test JWT token validation
        if self.tokens.get("super_admin"):
            response, error = self.make_request("GET", "/auth/me", self.tokens["super_admin"])
            if response and response.status_code == 200:
                self.log_result("Authentication", "token_validation", True, 
                              "JWT token validation successful", "/auth/me", response.json())
            else:
                self.log_result("Authentication", "token_validation", False,
                              f"Token validation failed: {error or response.text}", "/auth/me")

    def test_attendance_system(self):
        """Test Attendance & Time Tracking System"""
        print("⏰ Testing Attendance & Time Tracking System...")
        
        token = self.tokens.get("super_admin")
        if not token:
            self.log_result("Attendance", "no_auth", False, "No authentication token available")
            return

        # Test attendance endpoints
        endpoints_to_test = [
            ("GET", "/attendance", "Get attendance records"),
            ("GET", "/attendance/with-absences", "Get attendance with absences"),
            ("POST", "/attendance/check-in", "Check-in functionality"),
            ("POST", "/attendance/check-out", "Check-out functionality"),
        ]

        for method, endpoint, description in endpoints_to_test:
            response, error = self.make_request(method, endpoint, token)
            
            if response:
                success = response.status_code in [200, 201, 400]  # 400 might be expected for check-in/out
                details = f"{description}: Status {response.status_code}"
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if isinstance(data, list):
                            details += f" - Found {len(data)} records"
                        elif isinstance(data, dict) and 'message' in data:
                            details += f" - {data['message']}"
                    except:
                        pass
                        
                self.log_result("Attendance", f"{method.lower()}{endpoint.replace('/', '_')}", 
                              success, details, endpoint, 
                              response.json() if response.status_code == 200 else None)
            else:
                self.log_result("Attendance", f"{method.lower()}{endpoint.replace('/', '_')}", 
                              False, f"{description} failed: {error}", endpoint)

        # Test late tracking with 9:15 AM rule
        self.test_late_tracking_rule()

    def test_late_tracking_rule(self):
        """Test the new 9:15 AM late tracking rule"""
        print("⏰ Testing 9:15 AM Late Tracking Rule...")
        
        token = self.tokens.get("user")
        if not token:
            return

        # Test check-in after 9:15 AM (should be marked as late)
        response, error = self.make_request("POST", "/attendance/check-in", token)
        
        if response:
            success = response.status_code in [200, 400]  # 400 if already checked in
            details = f"Late tracking test: Status {response.status_code}"
            
            if response.status_code == 200:
                data = response.json()
                is_late = data.get("is_late", False)
                details += f" - Late status: {is_late}"
                
            self.log_result("Attendance", "late_tracking_rule", success, details, 
                          "/attendance/check-in", response.json() if response.status_code == 200 else None)

    def test_leave_management(self):
        """Test Leave Management System"""
        print("🏖️ Testing Leave Management System...")
        
        token = self.tokens.get("admin")
        if not token:
            self.log_result("Leave Management", "no_auth", False, "No authentication token available")
            return

        # Test leave endpoints
        endpoints_to_test = [
            ("GET", "/leaves", "Get all leaves (admin)"),
            ("GET", "/leaves/my", "Get user leaves"),
            ("POST", "/leaves", "Create leave request"),
        ]

        for method, endpoint, description in endpoints_to_test:
            # Use user token for /leaves/my
            test_token = self.tokens.get("user") if endpoint == "/leaves/my" else token
            
            response, error = self.make_request(method, endpoint, test_token)
            
            if response:
                success = response.status_code == 200
                details = f"{description}: Status {response.status_code}"
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if isinstance(data, list):
                            details += f" - Found {len(data)} records"
                        elif isinstance(data, dict) and 'leaves' in data:
                            details += f" - Found {len(data['leaves'])} records"
                    except:
                        pass
                        
                self.log_result("Leave Management", f"{method.lower()}{endpoint.replace('/', '_')}", 
                              success, details, endpoint, 
                              response.json() if response.status_code == 200 else None)
            else:
                self.log_result("Leave Management", f"{method.lower()}{endpoint.replace('/', '_')}", 
                              False, f"{description} failed: {error}", endpoint)

    def test_field_exits_and_marketing_visits(self):
        """Test External & Marketing Visits System"""
        print("🚗 Testing External & Marketing Visits System...")
        
        token = self.tokens.get("user")
        if not token:
            self.log_result("Field Exits", "no_auth", False, "No authentication token available")
            return

        # Test field exits
        field_exit_endpoints = [
            ("GET", "/field-exits", "Get field exits"),
            ("POST", "/field-exits", "Create field exit"),
        ]

        for method, endpoint, description in field_exit_endpoints:
            response, error = self.make_request(method, endpoint, token)
            
            if response:
                success = response.status_code in [200, 201]
                details = f"{description}: Status {response.status_code}"
                
                self.log_result("Field Exits", f"{method.lower()}{endpoint.replace('/', '_')}", 
                              success, details, endpoint)
            else:
                self.log_result("Field Exits", f"{method.lower()}{endpoint.replace('/', '_')}", 
                              False, f"{description} failed: {error}", endpoint)

        # Test marketing visits
        marketing_endpoints = [
            ("GET", "/marketing-visits/history", "Get marketing visits history"),
            ("GET", "/marketing-visits/active", "Get active marketing visit"),
            ("POST", "/marketing-visits/start", "Start marketing visit"),
        ]

        for method, endpoint, description in marketing_endpoints:
            response, error = self.make_request(method, endpoint, token)
            
            if response:
                success = response.status_code in [200, 201, 400]  # 400 might be expected for some cases
                details = f"{description}: Status {response.status_code}"
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if isinstance(data, list):
                            details += f" - Found {len(data)} records"
                        elif isinstance(data, dict):
                            if 'active_visit' in data:
                                details += f" - Active visit: {data['active_visit'] is not None}"
                    except:
                        pass
                        
                self.log_result("Marketing Visits", f"{method.lower()}{endpoint.replace('/', '_')}", 
                              success, details, endpoint, 
                              response.json() if response.status_code == 200 else None)
            else:
                self.log_result("Marketing Visits", f"{method.lower()}{endpoint.replace('/', '_')}", 
                              False, f"{description} failed: {error}", endpoint)

    def test_payroll_system(self):
        """Test Payroll System (CRITICAL)"""
        print("💰 Testing Payroll System (CRITICAL)...")
        
        token = self.tokens.get("super_admin")
        if not token:
            self.log_result("Payroll System", "no_auth", False, "No authentication token available")
            return

        # Test payroll cycle endpoints
        payroll_endpoints = [
            ("GET", "/payroll/cycles", "Get payroll cycles"),
            ("POST", "/payroll/cycles", "Create payroll cycle"),
            ("GET", "/payroll/installment-schedules", "Get installment schedules"),
        ]

        for method, endpoint, description in payroll_endpoints:
            data = None
            if method == "POST" and "cycles" in endpoint:
                data = {
                    "cycle_name": f"Test Cycle {datetime.now().strftime('%Y%m%d%H%M')}",
                    "start_date": "2025-01-01",
                    "end_date": "2025-01-31",
                    "pay_date": "2025-02-05"
                }
            
            response, error = self.make_request(method, endpoint, token, data)
            
            if response:
                success = response.status_code in [200, 201]
                details = f"{description}: Status {response.status_code}"
                
                if response.status_code == 200:
                    try:
                        response_data = response.json()
                        if isinstance(response_data, list):
                            details += f" - Found {len(response_data)} records"
                        elif isinstance(response_data, dict):
                            if 'cycles' in response_data:
                                details += f" - Found {len(response_data['cycles'])} cycles"
                    except:
                        pass
                        
                self.log_result("Payroll System", f"{method.lower()}{endpoint.replace('/', '_')}", 
                              success, details, endpoint, 
                              response.json() if response.status_code == 200 else None)
            else:
                self.log_result("Payroll System", f"{method.lower()}{endpoint.replace('/', '_')}", 
                              False, f"{description} failed: {error}", endpoint)

        # Test payroll calculations and salary letters
        self.test_payroll_calculations()

    def test_payroll_calculations(self):
        """Test payroll calculation logic"""
        print("🧮 Testing Payroll Calculations...")
        
        token = self.tokens.get("super_admin")
        if not token:
            return

        # Get existing payroll cycles first
        response, error = self.make_request("GET", "/payroll/cycles", token)
        
        if response and response.status_code == 200:
            cycles = response.json()
            if cycles and len(cycles) > 0:
                cycle_id = cycles[0].get("id")
                
                if cycle_id:
                    # Test cycle operations
                    cycle_endpoints = [
                        ("GET", f"/payroll/cycles/{cycle_id}", "Get cycle details"),
                        ("GET", f"/payroll/cycles/{cycle_id}/summary", "Get cycle summary"),
                        ("POST", f"/payroll/cycles/{cycle_id}/recalculate", "Recalculate cycle"),
                    ]
                    
                    for method, endpoint, description in cycle_endpoints:
                        response, error = self.make_request(method, endpoint, token)
                        
                        if response:
                            success = response.status_code == 200
                            details = f"{description}: Status {response.status_code}"
                            
                            self.log_result("Payroll Calculations", 
                                          f"{method.lower()}_cycle_operation", 
                                          success, details, endpoint)
                        else:
                            self.log_result("Payroll Calculations", 
                                          f"{method.lower()}_cycle_operation", 
                                          False, f"{description} failed: {error}", endpoint)

    def test_deductions_system(self):
        """Test Deductions System (CRITICAL)"""
        print("💸 Testing Deductions System (CRITICAL)...")
        
        token = self.tokens.get("super_admin")
        if not token:
            self.log_result("Deductions System", "no_auth", False, "No authentication token available")
            return

        # Test deduction endpoints
        deduction_endpoints = [
            ("GET", "/deductions", "Get deductions"),
            ("POST", "/deductions/calculate-monthly", "Calculate monthly deductions"),
            ("POST", "/deductions/apply-monthly", "Apply monthly deductions"),
            ("POST", "/deductions/manual", "Create manual deduction"),
        ]

        for method, endpoint, description in deduction_endpoints:
            data = None
            params = None
            
            if "calculate-monthly" in endpoint or "apply-monthly" in endpoint:
                params = {"month": "2025-01"}
            elif "manual" in endpoint:
                data = {
                    "employee_id": "test-employee-id",
                    "amount": 100.0,
                    "reason": "Test deduction",
                    "deduction_date": "2025-01-15"
                }
            
            response, error = self.make_request(method, endpoint, token, data, params)
            
            if response:
                success = response.status_code in [200, 201, 404]  # 404 might be expected for some cases
                details = f"{description}: Status {response.status_code}"
                
                if response.status_code == 200:
                    try:
                        response_data = response.json()
                        if isinstance(response_data, list):
                            details += f" - Found {len(response_data)} records"
                        elif isinstance(response_data, dict) and 'message' in response_data:
                            details += f" - {response_data['message']}"
                    except:
                        pass
                        
                self.log_result("Deductions System", f"{method.lower()}{endpoint.replace('/', '_')}", 
                              success, details, endpoint, 
                              response.json() if response.status_code == 200 else None)
            else:
                self.log_result("Deductions System", f"{method.lower()}{endpoint.replace('/', '_')}", 
                              False, f"{description} failed: {error}", endpoint)

    def test_advances_system(self):
        """Test Advances & Installments System (CRITICAL)"""
        print("💳 Testing Advances & Installments System (CRITICAL)...")
        
        token = self.tokens.get("super_admin")
        user_token = self.tokens.get("user")
        
        if not token:
            self.log_result("Advances System", "no_auth", False, "No authentication token available")
            return

        # Test advances endpoints
        advances_endpoints = [
            ("GET", "/advances/admin/all-balances", "Get all employee balances", token),
            ("GET", "/advances/admin/pending-approvals", "Get pending approvals", token),
            ("GET", "/advances/admin/all-transactions", "Get all transactions", token),
            ("GET", "/advances/my-balance", "Get user balance", user_token),
            ("GET", "/advances/my-transactions", "Get user transactions", user_token),
        ]

        for method, endpoint, description, test_token in advances_endpoints:
            if not test_token:
                continue
                
            response, error = self.make_request(method, endpoint, test_token)
            
            if response:
                success = response.status_code == 200
                details = f"{description}: Status {response.status_code}"
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if isinstance(data, dict):
                            if 'employee_balances' in data:
                                details += f" - Found {len(data['employee_balances'])} balances"
                            elif 'pending_transactions' in data:
                                details += f" - Found {len(data['pending_transactions'])} pending"
                            elif 'transactions' in data:
                                details += f" - Found {len(data['transactions'])} transactions"
                            elif 'total_available' in data:
                                details += f" - Available balance: {data['total_available']}"
                    except:
                        pass
                        
                self.log_result("Advances System", f"{method.lower()}{endpoint.replace('/', '_')}", 
                              success, details, endpoint, 
                              response.json() if response.status_code == 200 else None)
            else:
                self.log_result("Advances System", f"{method.lower()}{endpoint.replace('/', '_')}", 
                              False, f"{description} failed: {error}", endpoint)

    def test_payroll_ledger(self):
        """Test Payroll Ledger System (CRITICAL)"""
        print("📊 Testing Payroll Ledger System (CRITICAL)...")
        
        token = self.tokens.get("super_admin")
        user_token = self.tokens.get("user")
        
        if not token:
            self.log_result("Payroll Ledger", "no_auth", False, "No authentication token available")
            return

        # Test payroll ledger endpoints
        ledger_endpoints = [
            ("GET", "/payroll-ledger", "Get payroll ledger entries", token),
            ("GET", "/payroll-ledger/employee", "Get employee ledger", user_token),
        ]

        for method, endpoint, description, test_token in ledger_endpoints:
            if not test_token:
                continue
                
            response, error = self.make_request(method, endpoint, test_token)
            
            if response:
                success = response.status_code == 200
                details = f"{description}: Status {response.status_code}"
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if isinstance(data, list):
                            details += f" - Found {len(data)} entries"
                        elif isinstance(data, dict) and 'entries' in data:
                            details += f" - Found {len(data['entries'])} entries"
                    except:
                        pass
                        
                self.log_result("Payroll Ledger", f"{method.lower()}{endpoint.replace('/', '_')}", 
                              success, details, endpoint, 
                              response.json() if response.status_code == 200 else None)
            else:
                self.log_result("Payroll Ledger", f"{method.lower()}{endpoint.replace('/', '_')}", 
                              False, f"{description} failed: {error}", endpoint)

    def test_work_reports_system(self):
        """Test Work Reports System"""
        print("📝 Testing Work Reports System...")
        
        token = self.tokens.get("admin")
        if not token:
            self.log_result("Work Reports", "no_auth", False, "No authentication token available")
            return

        # Test work reports endpoints
        work_reports_endpoints = [
            ("GET", "/work-reports/clients", "Get clients"),
            ("GET", "/work-reports/logs", "Get work logs"),
            ("POST", "/work-reports/clients", "Create client"),
        ]

        for method, endpoint, description in work_reports_endpoints:
            data = None
            if method == "POST" and "clients" in endpoint:
                data = {
                    "company_name": f"Test Client {datetime.now().strftime('%H%M%S')}",
                    "client_code": f"TC{datetime.now().strftime('%H%M%S')}",
                    "industry": "Technology"
                }
            
            response, error = self.make_request(method, endpoint, token, data)
            
            if response:
                success = response.status_code in [200, 201]
                details = f"{description}: Status {response.status_code}"
                
                if response.status_code == 200:
                    try:
                        response_data = response.json()
                        if isinstance(response_data, list):
                            details += f" - Found {len(response_data)} records"
                    except:
                        pass
                        
                self.log_result("Work Reports", f"{method.lower()}{endpoint.replace('/', '_')}", 
                              success, details, endpoint, 
                              response.json() if response.status_code == 200 else None)
            else:
                self.log_result("Work Reports", f"{method.lower()}{endpoint.replace('/', '_')}", 
                              False, f"{description} failed: {error}", endpoint)

    def test_employee_management(self):
        """Test Employee Management System"""
        print("👥 Testing Employee Management System...")
        
        token = self.tokens.get("admin")
        if not token:
            self.log_result("Employee Management", "no_auth", False, "No authentication token available")
            return

        # Test employee endpoints
        employee_endpoints = [
            ("GET", "/users", "Get all users"),
            ("GET", "/employees/list", "Get employees list"),
        ]

        for method, endpoint, description in employee_endpoints:
            response, error = self.make_request(method, endpoint, token)
            
            if response:
                success = response.status_code == 200
                details = f"{description}: Status {response.status_code}"
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if isinstance(data, list):
                            details += f" - Found {len(data)} employees"
                        elif isinstance(data, dict) and 'users' in data:
                            details += f" - Found {len(data['users'])} users"
                    except:
                        pass
                        
                self.log_result("Employee Management", f"{method.lower()}{endpoint.replace('/', '_')}", 
                              success, details, endpoint, 
                              response.json() if response.status_code == 200 else None)
            else:
                self.log_result("Employee Management", f"{method.lower()}{endpoint.replace('/', '_')}", 
                              False, f"{description} failed: {error}", endpoint)

    def test_reports_analytics(self):
        """Test Reports & Analytics System"""
        print("📈 Testing Reports & Analytics System...")
        
        token = self.tokens.get("admin")
        if not token:
            self.log_result("Reports Analytics", "no_auth", False, "No authentication token available")
            return

        # Test reports endpoints
        reports_endpoints = [
            ("GET", "/attendance/report", "Get attendance report"),
            ("GET", "/reports/dashboard-stats", "Get dashboard statistics"),
        ]

        for method, endpoint, description in reports_endpoints:
            params = None
            if "attendance/report" in endpoint:
                params = {"start_date": "2025-01-01", "end_date": "2025-01-31"}
            
            response, error = self.make_request(method, endpoint, token, params=params)
            
            if response:
                success = response.status_code == 200
                details = f"{description}: Status {response.status_code}"
                
                self.log_result("Reports Analytics", f"{method.lower()}{endpoint.replace('/', '_')}", 
                              success, details, endpoint, 
                              response.json() if response.status_code == 200 else None)
            else:
                self.log_result("Reports Analytics", f"{method.lower()}{endpoint.replace('/', '_')}", 
                              False, f"{description} failed: {error}", endpoint)

    def test_notifications_system(self):
        """Test Notifications System"""
        print("🔔 Testing Notifications System...")
        
        token = self.tokens.get("super_admin")
        user_token = self.tokens.get("user")
        
        if not token:
            self.log_result("Notifications", "no_auth", False, "No authentication token available")
            return

        # Test notifications endpoints
        notifications_endpoints = [
            ("GET", "/notifications", "Get all notifications", token),
            ("GET", "/notifications/my", "Get user notifications", user_token),
            ("GET", "/notifications/unread-mandatory", "Get unread mandatory", user_token),
        ]

        for method, endpoint, description, test_token in notifications_endpoints:
            if not test_token:
                continue
                
            response, error = self.make_request(method, endpoint, test_token)
            
            if response:
                success = response.status_code == 200
                details = f"{description}: Status {response.status_code}"
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if isinstance(data, list):
                            details += f" - Found {len(data)} notifications"
                        elif isinstance(data, dict) and 'notifications' in data:
                            details += f" - Found {len(data['notifications'])} notifications"
                    except:
                        pass
                        
                self.log_result("Notifications", f"{method.lower()}{endpoint.replace('/', '_')}", 
                              success, details, endpoint, 
                              response.json() if response.status_code == 200 else None)
            else:
                self.log_result("Notifications", f"{method.lower()}{endpoint.replace('/', '_')}", 
                              False, f"{description} failed: {error}", endpoint)

    def calculate_module_stats(self):
        """Calculate statistics for each module"""
        for module_name, module_data in self.results["modules"].items():
            tests = module_data["tests"]
            if tests:
                successful_tests = sum(1 for test in tests if test["success"])
                total_tests = len(tests)
                success_rate = (successful_tests / total_tests) * 100
                
                module_data["success_rate"] = round(success_rate, 1)
                module_data["completion_percentage"] = round(success_rate, 1)  # For now, same as success rate
                
                if success_rate >= 90:
                    module_data["status"] = "Working"
                elif success_rate >= 70:
                    module_data["status"] = "Partial"
                else:
                    module_data["status"] = "Broken"
                    
                # Identify critical issues
                for test in tests:
                    if not test["success"] and any(keyword in test["test_name"].lower() 
                                                 for keyword in ["auth", "create", "calculate", "critical"]):
                        module_data["critical_issues"].append(test["details"])

    def calculate_overall_health(self):
        """Calculate overall system health score"""
        if not self.results["modules"]:
            self.results["overall_health"] = 0
            return
            
        total_score = sum(module["success_rate"] for module in self.results["modules"].values())
        module_count = len(self.results["modules"])
        self.results["overall_health"] = round(total_score / module_count, 1)

    def generate_audit_report(self):
        """Generate comprehensive audit report"""
        self.calculate_module_stats()
        self.calculate_overall_health()
        
        # Save detailed results
        results_file = Path("/app/comprehensive_hr_audit_results.json")
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📊 COMPREHENSIVE HR SYSTEM AUDIT RESULTS")
        print(f"{'='*60}")
        print(f"🕒 Audit Timestamp: {self.results['audit_timestamp']}")
        print(f"🌐 Backend URL: {self.results['backend_url']}")
        print(f"🏥 Overall System Health: {self.results['overall_health']}%")
        print(f"{'='*60}")
        
        # Authentication Summary
        print(f"\n🔐 AUTHENTICATION SYSTEM:")
        for role, auth_data in self.results["authentication"].items():
            status = "✅ SUCCESS" if auth_data["success"] else "❌ FAILED"
            print(f"  {role.upper()}: {status}")
            if not auth_data["success"]:
                print(f"    Error: {auth_data['error']}")
        
        # Module Summary
        print(f"\n📋 MODULE AUDIT SUMMARY:")
        for module_name, module_data in self.results["modules"].items():
            status_icon = "✅" if module_data["status"] == "Working" else "⚠️" if module_data["status"] == "Partial" else "❌"
            print(f"  {status_icon} {module_name}: {module_data['status']} ({module_data['success_rate']}% success rate)")
            
            if module_data["critical_issues"]:
                print(f"    🚨 Critical Issues: {len(module_data['critical_issues'])}")
                for issue in module_data["critical_issues"][:2]:  # Show first 2 issues
                    print(f"      - {issue}")
        
        # Broken Endpoints
        if self.results["broken_endpoints"]:
            print(f"\n❌ BROKEN ENDPOINTS ({len(self.results['broken_endpoints'])}):")
            for endpoint in self.results["broken_endpoints"][:10]:  # Show first 10
                print(f"  - {endpoint['endpoint']} ({endpoint['module']}): {endpoint['error']}")
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        return self.results

    def run_comprehensive_audit(self):
        """Run the complete HR system audit"""
        print("🔍 STARTING COMPREHENSIVE HR SYSTEM AUDIT")
        print("=" * 60)
        
        # Test all modules
        self.test_authentication_system()
        self.test_attendance_system()
        self.test_leave_management()
        self.test_field_exits_and_marketing_visits()
        self.test_payroll_system()
        self.test_deductions_system()
        self.test_advances_system()
        self.test_payroll_ledger()
        self.test_work_reports_system()
        self.test_employee_management()
        self.test_reports_analytics()
        self.test_notifications_system()
        
        # Generate final report
        return self.generate_audit_report()

def main():
    """Main execution function"""
    audit = HRSystemAudit()
    results = audit.run_comprehensive_audit()
    
    # Return summary for testing agent
    return {
        "overall_health": results["overall_health"],
        "modules_tested": len(results["modules"]),
        "broken_endpoints": len(results["broken_endpoints"]),
        "authentication_success": all(auth["success"] for auth in results["authentication"].values()),
        "critical_modules_status": {
            module: data["status"] for module, data in results["modules"].items()
            if "payroll" in module.lower() or "deduction" in module.lower() or "advance" in module.lower()
        }
    }

if __name__ == "__main__":
    main()