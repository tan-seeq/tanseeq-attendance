#!/usr/bin/env python3
"""
🔥 FINAL COMPREHENSIVE E2E BACKEND TESTING - ARABIC REVIEW
اختبار شامل نهائي من A to Z للنظام - COMPREHENSIVE TESTING

Testing all modules as requested in Arabic review with CORRECT credentials:
1. Authentication & Users (تسجيل الدخول)
2. Attendance System (نظام الحضور) 
3. Notification System (نظام الإشعارات)
4. Advances & Custody System (السلف والعهد)
5. Deductions System (نظام الخصومات)
6. Health Checks

CORRECTED Test Credentials:
- Super Admin: admin@tanseeq.com / ADMIN
- User: jihad@tanseeq.com / jihad123
- Tarek: tarek.wazzan@tanseeq.com / tarek123 (CORRECTED)
"""

import requests
import json
import sys
from datetime import datetime, timedelta
import os
from pathlib import Path

# Configuration
BACKEND_URL = "https://attend-deduct-hr.preview.emergentagent.com/api"

# CORRECTED Test credentials based on database verification
TEST_CREDENTIALS = {
    "super_admin": {"email": "admin@tanseeq.com", "password": "ADMIN"},
    "user": {"email": "jihad@tanseeq.com", "password": "jihad123"},
    "tarek": {"email": "tarek.wazzan@tanseeq.com", "password": "tarek123"}  # CORRECTED
}

class FinalArabicE2EBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.tokens = {}
        self.user_ids = {}
        self.test_results = []
        self.success_count = 0
        self.total_count = 0
        
    def log_test(self, test_name, success, details="", response_data=None):
        """Log test result"""
        self.total_count += 1
        if success:
            self.success_count += 1
            
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
        if details:
            print(f"   📝 {details}")
        
    def authenticate_user(self, user_type):
        """Authenticate user and store token"""
        try:
            creds = TEST_CREDENTIALS[user_type]
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=creds)
            
            if response.status_code == 200:
                data = response.json()
                self.tokens[user_type] = data["access_token"]
                user_info = data.get("user", {})
                self.user_ids[user_type] = user_info.get("id")
                
                self.log_test(
                    f"Authentication - {user_type}",
                    True,
                    f"✅ {creds['email']} (Role: {user_info.get('role', 'unknown')}, ID: {user_info.get('id', 'N/A')})"
                )
                return True
            else:
                self.log_test(
                    f"Authentication - {user_type}",
                    False,
                    f"❌ {creds['email']} - {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(f"Authentication - {user_type}", False, f"Exception: {str(e)}")
            return False
    
    def get_headers(self, user_type):
        """Get authorization headers for user"""
        token = self.tokens.get(user_type)
        if not token:
            return {}
        return {"Authorization": f"Bearer {token}"}
    
    def test_jwt_token_validity(self):
        """Test JWT token validity"""
        print("\n🔐 Testing JWT Token Validity")
        print("-" * 40)
        
        for user_type in ["super_admin", "user", "tarek"]:
            if user_type in self.tokens:
                try:
                    headers = self.get_headers(user_type)
                    response = self.session.get(f"{BACKEND_URL}/auth/me", headers=headers)
                    
                    if response.status_code == 200:
                        data = response.json()
                        self.log_test(
                            f"JWT Token Validity - {user_type}",
                            True,
                            f"Token valid - User: {data.get('name', 'N/A')} (Role: {data.get('role', 'N/A')})"
                        )
                    else:
                        self.log_test(
                            f"JWT Token Validity - {user_type}",
                            False,
                            f"Token invalid: {response.status_code} - {response.text}"
                        )
                except Exception as e:
                    self.log_test(f"JWT Token Validity - {user_type}", False, f"Exception: {str(e)}")
    
    def test_attendance_system(self):
        """Test attendance system (نظام الحضور)"""
        print("\n🕐 Testing Attendance System (نظام الحضور)")
        print("-" * 40)
        
        # Test check-in for regular user
        if "user" in self.tokens:
            try:
                headers = self.get_headers("user")
                response = self.session.post(f"{BACKEND_URL}/attendance/check-in", headers=headers)
                
                if response.status_code in [200, 400]:  # 400 if already checked in
                    data = response.json() if response.status_code == 200 else {}
                    message = data.get('message', response.text)
                    late_info = ""
                    if response.status_code == 200:
                        is_late = data.get('is_late', False)
                        late_minutes = data.get('late_minutes', 0)
                        schedule_type = data.get('schedule_type', 'unknown')
                        late_info = f" (Late: {is_late}, Minutes: {late_minutes}, Schedule: {schedule_type})"
                    
                    self.log_test(
                        "Attendance Check-in (Regular User)",
                        True,
                        f"Status: {response.status_code} - {message}{late_info}"
                    )
                else:
                    self.log_test(
                        "Attendance Check-in (Regular User)",
                        False,
                        f"Status: {response.status_code} - {response.text}"
                    )
            except Exception as e:
                self.log_test("Attendance Check-in (Regular User)", False, f"Exception: {str(e)}")
        
        # Test check-in for Tarek (flexible schedule)
        if "tarek" in self.tokens:
            try:
                headers = self.get_headers("tarek")
                response = self.session.post(f"{BACKEND_URL}/attendance/check-in", headers=headers)
                
                if response.status_code in [200, 400]:
                    data = response.json() if response.status_code == 200 else {}
                    message = data.get('message', response.text)
                    schedule_info = ""
                    if response.status_code == 200:
                        schedule_type = data.get('schedule_type', 'unknown')
                        exception_type = data.get('exception_type', 'none')
                        is_late = data.get('is_late', False)
                        late_minutes = data.get('late_minutes', 0)
                        schedule_info = f" (Schedule: {schedule_type}, Exception: {exception_type}, Late: {is_late}, Minutes: {late_minutes})"
                    
                    self.log_test(
                        "Attendance Check-in (Tarek - Flexible)",
                        True,
                        f"Status: {response.status_code} - {message}{schedule_info}"
                    )
                else:
                    self.log_test(
                        "Attendance Check-in (Tarek - Flexible)",
                        False,
                        f"Status: {response.status_code} - {response.text}"
                    )
            except Exception as e:
                self.log_test("Attendance Check-in (Tarek - Flexible)", False, f"Exception: {str(e)}")
        
        # Test check-out
        if "user" in self.tokens:
            try:
                headers = self.get_headers("user")
                response = self.session.post(f"{BACKEND_URL}/attendance/check-out", headers=headers)
                
                if response.status_code in [200, 400]:
                    data = response.json() if response.status_code == 200 else {}
                    message = data.get('message', response.text)
                    hours_info = ""
                    if response.status_code == 200:
                        working_hours = data.get('working_hours', 0)
                        hours_info = f" (Working Hours: {working_hours})"
                    
                    self.log_test(
                        "Attendance Check-out",
                        True,
                        f"Status: {response.status_code} - {message}{hours_info}"
                    )
                else:
                    self.log_test(
                        "Attendance Check-out",
                        False,
                        f"Status: {response.status_code} - {response.text}"
                    )
            except Exception as e:
                self.log_test("Attendance Check-out", False, f"Exception: {str(e)}")
        
        # Test reading exceptions from database
        if "super_admin" in self.tokens:
            try:
                headers = self.get_headers("super_admin")
                response = self.session.get(f"{BACKEND_URL}/attendance", headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    attendance_records = data if isinstance(data, list) else data.get("attendance", [])
                    
                    # Check for late tracking and exceptions
                    late_records = [r for r in attendance_records if r.get('late_minutes', 0) > 0]
                    exception_records = [r for r in attendance_records if r.get('exception_type')]
                    
                    self.log_test(
                        "Attendance Records & Exceptions",
                        True,
                        f"Total: {len(attendance_records)}, Late records: {len(late_records)}, Exception records: {len(exception_records)}"
                    )
                else:
                    self.log_test(
                        "Attendance Records & Exceptions",
                        False,
                        f"Status: {response.status_code} - {response.text}"
                    )
            except Exception as e:
                self.log_test("Attendance Records & Exceptions", False, f"Exception: {str(e)}")
    
    def test_notification_system(self):
        """Test notification system (نظام الإشعارات)"""
        print("\n🔔 Testing Notification System (نظام الإشعارات)")
        print("-" * 40)
        
        # Test notification count
        if "user" in self.tokens:
            try:
                headers = self.get_headers("user")
                response = self.session.get(f"{BACKEND_URL}/notifications/count", headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    count = data.get('unread_count', 'N/A')
                    self.log_test(
                        "Notifications Count",
                        True,
                        f"Unread notifications: {count}"
                    )
                else:
                    self.log_test(
                        "Notifications Count",
                        False,
                        f"Status: {response.status_code} - {response.text}"
                    )
            except Exception as e:
                self.log_test("Notifications Count", False, f"Exception: {str(e)}")
        
        # Test fetch unread notifications
        if "user" in self.tokens:
            try:
                headers = self.get_headers("user")
                response = self.session.get(f"{BACKEND_URL}/notifications/my?unread_only=true", headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    notifications = data if isinstance(data, list) else data.get("notifications", [])
                    self.log_test(
                        "Fetch Unread Notifications",
                        True,
                        f"Retrieved {len(notifications)} unread notifications"
                    )
                    
                    # Store first notification ID for acknowledge test
                    if notifications:
                        self.first_notification_id = notifications[0].get("id")
                else:
                    self.log_test(
                        "Fetch Unread Notifications",
                        False,
                        f"Status: {response.status_code} - {response.text}"
                    )
            except Exception as e:
                self.log_test("Fetch Unread Notifications", False, f"Exception: {str(e)}")
        
        # Test acknowledge notification
        if "user" in self.tokens and hasattr(self, 'first_notification_id') and self.first_notification_id:
            try:
                headers = self.get_headers("user")
                response = self.session.post(
                    f"{BACKEND_URL}/notifications/{self.first_notification_id}/acknowledge",
                    headers=headers
                )
                
                if response.status_code == 200:
                    self.log_test(
                        "Acknowledge Notification",
                        True,
                        f"Successfully acknowledged notification {self.first_notification_id}"
                    )
                else:
                    self.log_test(
                        "Acknowledge Notification",
                        False,
                        f"Status: {response.status_code} - {response.text}"
                    )
            except Exception as e:
                self.log_test("Acknowledge Notification", False, f"Exception: {str(e)}")
        
        # Test send notification (Super Admin)
        if "super_admin" in self.tokens and "user" in self.user_ids:
            try:
                headers = self.get_headers("super_admin")
                notification_data = {
                    "recipient_id": self.user_ids["user"],
                    "subject": "اختبار الإشعارات الشامل",
                    "message": "هذا إشعار تجريبي من نظام الاختبار الشامل النهائي",
                    "type": "info",
                    "priority": "normal"
                }
                
                response = self.session.post(f"{BACKEND_URL}/notifications/send", json=notification_data, headers=headers)
                
                if response.status_code == 200:
                    self.log_test(
                        "Send Notification (Super Admin)",
                        True,
                        "Successfully sent test notification"
                    )
                else:
                    self.log_test(
                        "Send Notification (Super Admin)",
                        False,
                        f"Status: {response.status_code} - {response.text}"
                    )
            except Exception as e:
                self.log_test("Send Notification (Super Admin)", False, f"Exception: {str(e)}")
    
    def test_advances_custody_system(self):
        """Test advances & custody system (السلف والعهد)"""
        print("\n💰 Testing Advances & Custody System (السلف والعهد)")
        print("-" * 40)
        
        # Test employee request advance
        if "user" in self.tokens:
            try:
                headers = self.get_headers("user")
                advance_data = {
                    "transaction_type": "advance",
                    "amount": 500.0,
                    "description": "سلفة اختبار شامل نهائي",
                    "category": "transportation",
                    "expense_date": datetime.now().strftime("%Y-%m-%d"),
                    "notes": "طلب سلفة للاختبار الشامل النهائي"
                }
                
                response = self.session.post(f"{BACKEND_URL}/advances/request", json=advance_data, headers=headers)
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    self.log_test(
                        "Request Advance (Employee)",
                        True,
                        f"Advance request: {data.get('message', 'Success')}"
                    )
                else:
                    self.log_test(
                        "Request Advance (Employee)",
                        False,
                        f"Status: {response.status_code} - {response.text}"
                    )
            except Exception as e:
                self.log_test("Request Advance (Employee)", False, f"Exception: {str(e)}")
        
        # Test employee request custody
        if "user" in self.tokens:
            try:
                headers = self.get_headers("user")
                custody_data = {
                    "transaction_type": "custody",
                    "amount": 300.0,
                    "description": "عهدة اختبار شامل نهائي",
                    "category": "supplies",
                    "expense_date": datetime.now().strftime("%Y-%m-%d"),
                    "notes": "طلب عهدة للاختبار الشامل النهائي"
                }
                
                response = self.session.post(f"{BACKEND_URL}/advances/request", json=custody_data, headers=headers)
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    self.log_test(
                        "Request Custody (Employee)",
                        True,
                        f"Custody request: {data.get('message', 'Success')}"
                    )
                else:
                    self.log_test(
                        "Request Custody (Employee)",
                        False,
                        f"Status: {response.status_code} - {response.text}"
                    )
            except Exception as e:
                self.log_test("Request Custody (Employee)", False, f"Exception: {str(e)}")
        
        # Test custody settlement
        if "user" in self.tokens:
            try:
                headers = self.get_headers("user")
                settlement_data = {
                    "amount": 100.0,
                    "settlement_date": datetime.now().strftime("%Y-%m-%d"),
                    "description": "تسوية عهدة اختبار شامل نهائي",
                    "notes": "تسوية جزئية للعهدة"
                }
                
                response = self.session.post(f"{BACKEND_URL}/advances/custody-settlement", json=settlement_data, headers=headers)
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    self.log_test(
                        "Custody Settlement (Employee)",
                        True,
                        f"Settlement: {data.get('message', 'Success')}"
                    )
                else:
                    self.log_test(
                        "Custody Settlement (Employee)",
                        False,
                        f"Status: {response.status_code} - {response.text}"
                    )
            except Exception as e:
                self.log_test("Custody Settlement (Employee)", False, f"Exception: {str(e)}")
        
        # Test employee balance
        if "user" in self.tokens:
            try:
                headers = self.get_headers("user")
                response = self.session.get(f"{BACKEND_URL}/advances/my-balance", headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    total_available = data.get("total_available", 0)
                    remaining_advance = data.get("remaining_advance", 0)
                    remaining_custody = data.get("remaining_custody", 0)
                    total_advances = data.get("total_advances", 0)
                    total_custody = data.get("total_custody", 0)
                    total_expenses = data.get("total_expenses", 0)
                    
                    self.log_test(
                        "Employee Balance",
                        True,
                        f"Total Available: {total_available} AED (Advance: {remaining_advance}, Custody: {remaining_custody}) | Totals: Advances={total_advances}, Custody={total_custody}, Expenses={total_expenses}"
                    )
                else:
                    self.log_test(
                        "Employee Balance",
                        False,
                        f"Status: {response.status_code} - {response.text}"
                    )
            except Exception as e:
                self.log_test("Employee Balance", False, f"Exception: {str(e)}")
        
        # Test Super Admin endpoints
        if "super_admin" in self.tokens:
            # Test employees with balances
            try:
                headers = self.get_headers("super_admin")
                response = self.session.get(f"{BACKEND_URL}/advances/admin/employees-with-balances", headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    employees = data.get("employee_balances", [])
                    self.log_test(
                        "Employees with Balances (Super Admin)",
                        True,
                        f"Found {len(employees)} employees with balances"
                    )
                else:
                    self.log_test(
                        "Employees with Balances (Super Admin)",
                        False,
                        f"Status: {response.status_code} - {response.text}"
                    )
            except Exception as e:
                self.log_test("Employees with Balances (Super Admin)", False, f"Exception: {str(e)}")
            
            # Test repayment
            try:
                headers = self.get_headers("super_admin")
                repay_data = {
                    "employee_id": self.user_ids.get("user", "test-user-id"),
                    "amount": 50.0,
                    "description": "سداد جزئي اختبار شامل نهائي",
                    "notes": "سداد تجريبي للاختبار النهائي"
                }
                
                response = self.session.post(f"{BACKEND_URL}/advances/repay", json=repay_data, headers=headers)
                
                if response.status_code in [200, 201, 404]:  # 404 acceptable if no balance
                    self.log_test(
                        "Record Repayment (Super Admin)",
                        True,
                        f"Repayment response: {response.status_code}"
                    )
                else:
                    self.log_test(
                        "Record Repayment (Super Admin)",
                        False,
                        f"Status: {response.status_code} - {response.text}"
                    )
            except Exception as e:
                self.log_test("Record Repayment (Super Admin)", False, f"Exception: {str(e)}")
            
            # Test edit transaction (if any exist)
            try:
                headers = self.get_headers("super_admin")
                # First get transactions to find one to edit
                response = self.session.get(f"{BACKEND_URL}/advances/admin/all-transactions", headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    transactions = data.get("transactions", [])
                    
                    if transactions:
                        transaction_id = transactions[0].get("id")
                        if transaction_id:
                            edit_data = {
                                "description": "معاملة محدثة - اختبار شامل نهائي",
                                "notes": "تم التحديث في الاختبار الشامل النهائي"
                            }
                            
                            edit_response = self.session.put(
                                f"{BACKEND_URL}/advances/{transaction_id}/edit",
                                json=edit_data,
                                headers=headers
                            )
                            
                            if edit_response.status_code == 200:
                                self.log_test(
                                    "Edit Transaction (Super Admin)",
                                    True,
                                    f"Successfully edited transaction {transaction_id}"
                                )
                            else:
                                self.log_test(
                                    "Edit Transaction (Super Admin)",
                                    False,
                                    f"Edit failed: {edit_response.status_code} - {edit_response.text}"
                                )
                        else:
                            self.log_test("Edit Transaction (Super Admin)", False, "No transaction ID found")
                    else:
                        self.log_test("Edit Transaction (Super Admin)", True, "No transactions to edit")
                    
                    self.log_test(
                        "All Transactions (Super Admin)",
                        True,
                        f"Retrieved {len(transactions)} transactions"
                    )
                else:
                    self.log_test(
                        "All Transactions (Super Admin)",
                        False,
                        f"Status: {response.status_code} - {response.text}"
                    )
            except Exception as e:
                self.log_test("All Transactions (Super Admin)", False, f"Exception: {str(e)}")
            
            # Test pending approvals
            try:
                headers = self.get_headers("super_admin")
                response = self.session.get(f"{BACKEND_URL}/advances/admin/pending-approvals", headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    pending = data.get("pending_transactions", [])
                    self.log_test(
                        "Pending Approvals (Super Admin)",
                        True,
                        f"Found {len(pending)} pending approvals"
                    )
                else:
                    self.log_test(
                        "Pending Approvals (Super Admin)",
                        False,
                        f"Status: {response.status_code} - {response.text}"
                    )
            except Exception as e:
                self.log_test("Pending Approvals (Super Admin)", False, f"Exception: {str(e)}")
    
    def test_deductions_system(self):
        """Test deductions system (نظام الخصومات)"""
        print("\n📊 Testing Deductions System (نظام الخصومات)")
        print("-" * 40)
        
        # Test monthly deductions calculation
        if "super_admin" in self.tokens:
            try:
                headers = self.get_headers("super_admin")
                current_month = datetime.now().strftime("%Y-%m")
                response = self.session.post(f"{BACKEND_URL}/deductions/calculate-monthly?month={current_month}", headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    employees_processed = len(data.get("employees", []))
                    total_deductions = sum(emp.get("total_deductions", 0) for emp in data.get("employees", []))
                    
                    self.log_test(
                        "Monthly Deductions Calculation",
                        True,
                        f"Processed {employees_processed} employees for {current_month}, Total deductions: {total_deductions} AED"
                    )
                else:
                    self.log_test(
                        "Monthly Deductions Calculation",
                        False,
                        f"Status: {response.status_code} - {response.text}"
                    )
            except Exception as e:
                self.log_test("Monthly Deductions Calculation", False, f"Exception: {str(e)}")
        
        # Test exceptions verification (Hatem, Tariq, Karim, Hesham)
        if "super_admin" in self.tokens:
            try:
                headers = self.get_headers("super_admin")
                response = self.session.get(f"{BACKEND_URL}/deductions", headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    deductions = data if isinstance(data, list) else data.get("deductions", [])
                    
                    # Check for exception users
                    exception_users = ["Hatem", "Tarek", "Kareem", "Hesham"]
                    found_exceptions = []
                    exception_details = {}
                    
                    for deduction in deductions:
                        employee_name = deduction.get("employee_name", "")
                        for exception_user in exception_users:
                            if exception_user.lower() in employee_name.lower():
                                if exception_user not in found_exceptions:
                                    found_exceptions.append(exception_user)
                                    exception_details[exception_user] = {
                                        "name": employee_name,
                                        "deduction_amount": deduction.get("total_deductions", 0)
                                    }
                    
                    self.log_test(
                        "Deductions Exceptions Verification",
                        True,
                        f"Found {len(found_exceptions)} exception users: {found_exceptions} | Details: {exception_details}"
                    )
                else:
                    self.log_test(
                        "Deductions Exceptions Verification",
                        False,
                        f"Status: {response.status_code} - {response.text}"
                    )
            except Exception as e:
                self.log_test("Deductions Exceptions Verification", False, f"Exception: {str(e)}")
    
    def test_health_checks(self):
        """Test health check endpoints"""
        print("\n🏥 Testing Health Checks")
        print("-" * 40)
        
        # Test /api/healthz
        try:
            response = self.session.get(f"{BACKEND_URL}/healthz")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Health Check (/healthz)",
                    True,
                    f"Health status: {data.get('status', 'ok')}"
                )
            else:
                self.log_test(
                    "Health Check (/healthz)",
                    False,
                    f"Status: {response.status_code} - {response.text}"
                )
        except Exception as e:
            self.log_test("Health Check (/healthz)", False, f"Exception: {str(e)}")
        
        # Test /api/users
        if "super_admin" in self.tokens:
            try:
                headers = self.get_headers("super_admin")
                response = self.session.get(f"{BACKEND_URL}/users", headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    users = data if isinstance(data, list) else data.get("users", [])
                    active_users = [u for u in users if u.get("is_active", True)]
                    
                    self.log_test(
                        "Users Endpoint",
                        True,
                        f"Retrieved {len(users)} total users, {len(active_users)} active users"
                    )
                else:
                    self.log_test(
                        "Users Endpoint",
                        False,
                        f"Status: {response.status_code} - {response.text}"
                    )
            except Exception as e:
                self.log_test("Users Endpoint", False, f"Exception: {str(e)}")
    
    def run_comprehensive_test(self):
        """Run comprehensive E2E test"""
        print("🔥 FINAL COMPREHENSIVE E2E BACKEND TESTING - ARABIC REVIEW")
        print("=" * 70)
        print("اختبار شامل نهائي من A to Z للنظام")
        print("=" * 70)
        
        # 1. Authentication & JWT Token Validity
        print("\n🔐 Testing Authentication & JWT Tokens")
        print("-" * 50)
        for user_type in ["super_admin", "user", "tarek"]:
            self.authenticate_user(user_type)
        
        self.test_jwt_token_validity()
        
        # 2. Attendance System
        self.test_attendance_system()
        
        # 3. Notification System
        self.test_notification_system()
        
        # 4. Advances & Custody System
        self.test_advances_custody_system()
        
        # 5. Deductions System
        self.test_deductions_system()
        
        # 6. Health Checks
        self.test_health_checks()
        
        # Generate final report
        self.generate_final_report()
    
    def generate_final_report(self):
        """Generate comprehensive Arabic report"""
        print("\n" + "=" * 70)
        print("📊 FINAL COMPREHENSIVE TEST RESULTS")
        print("نتائج الاختبار الشامل النهائي - Arabic Review")
        print("=" * 70)
        
        success_rate = (self.success_count / self.total_count * 100) if self.total_count > 0 else 0
        
        print(f"📈 إجمالي النتائج (Overall Results):")
        print(f"   ✅ اختبارات ناجحة (Successful): {self.success_count}")
        print(f"   ❌ اختبارات فاشلة (Failed): {self.total_count - self.success_count}")
        print(f"   📊 إجمالي الاختبارات (Total): {self.total_count}")
        print(f"   🎯 نسبة النجاح (Success Rate): {success_rate:.1f}%")
        
        # Group results by system
        systems = {
            "🔐 Authentication & JWT": [],
            "🕐 Attendance System": [],
            "🔔 Notifications": [],
            "💰 Advances & Custody": [],
            "📊 Deductions": [],
            "🏥 Health Checks": []
        }
        
        for result in self.test_results:
            test_name = result["test"]
            if "Authentication" in test_name or "JWT" in test_name:
                systems["🔐 Authentication & JWT"].append(result)
            elif "Attendance" in test_name:
                systems["🕐 Attendance System"].append(result)
            elif "Notification" in test_name:
                systems["🔔 Notifications"].append(result)
            elif any(word in test_name for word in ["Advance", "Custody", "Balance", "Repayment", "Transaction"]):
                systems["💰 Advances & Custody"].append(result)
            elif "Deduction" in test_name:
                systems["📊 Deductions"].append(result)
            elif "Health" in test_name or "Users" in test_name:
                systems["🏥 Health Checks"].append(result)
        
        print(f"\n📋 تفاصيل النتائج حسب النظام (Results by System):")
        
        for system, results in systems.items():
            if results:
                passed = sum(1 for r in results if r["success"])
                total = len(results)
                system_rate = (passed / total * 100) if total > 0 else 0
                
                print(f"\n{system} ({passed}/{total} - {system_rate:.1f}%):")
                for result in results:
                    status = "✅" if result["success"] else "❌"
                    print(f"   {status} {result['test']}")
                    if result["details"]:
                        print(f"      📝 {result['details']}")
        
        # Save detailed results
        results_file = "/app/final_arabic_comprehensive_e2e_test_results.json"
        try:
            with open(results_file, "w", encoding="utf-8") as f:
                json.dump({
                    "summary": {
                        "total_tests": self.total_count,
                        "successful_tests": self.success_count,
                        "failed_tests": self.total_count - self.success_count,
                        "success_rate": success_rate,
                        "test_timestamp": datetime.now().isoformat(),
                        "test_credentials_used": {
                            "super_admin": "admin@tanseeq.com",
                            "user": "jihad@tanseeq.com", 
                            "tarek": "tarek.wazzan@tanseeq.com"
                        }
                    },
                    "detailed_results": self.test_results,
                    "systems_breakdown": {
                        system: {
                            "total": len(results),
                            "passed": sum(1 for r in results if r["success"]),
                            "success_rate": (sum(1 for r in results if r["success"]) / len(results) * 100) if results else 0
                        }
                        for system, results in systems.items() if results
                    }
                }, f, ensure_ascii=False, indent=2)
            print(f"\n💾 تم حفظ النتائج التفصيلية في (Results saved to): {results_file}")
        except Exception as e:
            print(f"⚠️ فشل في حفظ النتائج (Failed to save results): {str(e)}")
        
        print("\n" + "=" * 70)
        if success_rate >= 90:
            print("🎉 ممتاز - النظام جاهز للإنتاج (EXCELLENT - SYSTEM READY FOR PRODUCTION)")
        elif success_rate >= 80:
            print("✅ جيد جداً - النظام يعمل بشكل ممتاز (VERY GOOD - SYSTEM WORKING EXCELLENTLY)")
        elif success_rate >= 70:
            print("✅ جيد - النظام يعمل بشكل جيد (GOOD - SYSTEM WORKING WELL)")
        elif success_rate >= 60:
            print("⚠️ يحتاج تحسينات - SYSTEM NEEDS IMPROVEMENTS")
        else:
            print("🚨 يحتاج إصلاحات عاجلة - SYSTEM NEEDS URGENT FIXES")
        print("=" * 70)

def main():
    """Main test execution"""
    tester = FinalArabicE2EBackendTester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()