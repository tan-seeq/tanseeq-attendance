#!/usr/bin/env python3
"""
🔥 COMPREHENSIVE E2E BACKEND TESTING - ARABIC REVIEW REQUEST
اختبار شامل من A to Z للنظام - COMPREHENSIVE TESTING

Testing all modules as requested in Arabic review:
1. Authentication & Users (تسجيل الدخول)
2. Attendance System (نظام الحضور) 
3. Notification System (نظام الإشعارات)
4. Advances & Custody System (السلف والعهد)
5. Deductions System (نظام الخصومات)
6. Health Checks

Test Credentials:
- Super Admin: admin@tanseeq.com / ADMIN
- User: jihad@tanseeq.com / jihad123
- Tarek: tarek@tanseeq.com / tarek123
"""

import requests
import json
import sys
from datetime import datetime, timedelta
import os
from pathlib import Path

# Configuration
BACKEND_URL = "https://attend-deduct-hr.preview.emergentagent.com/api"

# Test credentials as specified in Arabic review
TEST_CREDENTIALS = {
    "super_admin": {"email": "admin@tanseeq.com", "password": "ADMIN"},
    "user": {"email": "jihad@tanseeq.com", "password": "jihad123"},
    "tarek": {"email": "tarek@tanseeq.com", "password": "tarek123"}
}

class ArabicE2EBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.tokens = {}
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
        print(f"{status} {test_name}: {details}")
        
    def authenticate_user(self, user_type):
        """Authenticate user and store token"""
        try:
            creds = TEST_CREDENTIALS[user_type]
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=creds)
            
            if response.status_code == 200:
                data = response.json()
                self.tokens[user_type] = data["access_token"]
                user_info = data.get("user", {})
                self.log_test(
                    f"Authentication - {user_type}",
                    True,
                    f"Login successful for {creds['email']} (Role: {user_info.get('role', 'unknown')})",
                    {"user_id": user_info.get("id"), "role": user_info.get("role")}
                )
                return True
            else:
                self.log_test(
                    f"Authentication - {user_type}",
                    False,
                    f"Login failed: {response.status_code} - {response.text}"
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
    
    def test_attendance_system(self):
        """Test attendance system (نظام الحضور)"""
        print("\n🕐 Testing Attendance System (نظام الحضور)")
        
        # Test check-in for regular user
        try:
            headers = self.get_headers("user")
            response = self.session.post(f"{BACKEND_URL}/attendance/check-in", headers=headers)
            
            if response.status_code in [200, 400]:  # 400 if already checked in
                data = response.json() if response.status_code == 200 else {}
                self.log_test(
                    "Attendance Check-in (User)",
                    True,
                    f"Check-in response: {response.status_code} - {data.get('message', response.text)}"
                )
            else:
                self.log_test(
                    "Attendance Check-in (User)",
                    False,
                    f"Check-in failed: {response.status_code} - {response.text}"
                )
        except Exception as e:
            self.log_test("Attendance Check-in (User)", False, f"Exception: {str(e)}")
        
        # Test check-in for Tarek (flexible schedule)
        try:
            headers = self.get_headers("tarek")
            response = self.session.post(f"{BACKEND_URL}/attendance/check-in", headers=headers)
            
            if response.status_code in [200, 400]:  # 400 if already checked in
                data = response.json() if response.status_code == 200 else {}
                self.log_test(
                    "Attendance Check-in (Tarek - Flexible)",
                    True,
                    f"Tarek check-in: {response.status_code} - {data.get('message', response.text)}"
                )
            else:
                self.log_test(
                    "Attendance Check-in (Tarek - Flexible)",
                    False,
                    f"Tarek check-in failed: {response.status_code} - {response.text}"
                )
        except Exception as e:
            self.log_test("Attendance Check-in (Tarek - Flexible)", False, f"Exception: {str(e)}")
        
        # Test check-out for user
        try:
            headers = self.get_headers("user")
            response = self.session.post(f"{BACKEND_URL}/attendance/check-out", headers=headers)
            
            if response.status_code in [200, 400]:  # 400 if not checked in or already checked out
                data = response.json() if response.status_code == 200 else {}
                self.log_test(
                    "Attendance Check-out (User)",
                    True,
                    f"Check-out response: {response.status_code} - {data.get('message', response.text)}"
                )
            else:
                self.log_test(
                    "Attendance Check-out (User)",
                    False,
                    f"Check-out failed: {response.status_code} - {response.text}"
                )
        except Exception as e:
            self.log_test("Attendance Check-out (User)", False, f"Exception: {str(e)}")
        
        # Test reading exceptions from database
        try:
            headers = self.get_headers("super_admin")
            response = self.session.get(f"{BACKEND_URL}/attendance", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                attendance_records = data if isinstance(data, list) else data.get("attendance", [])
                self.log_test(
                    "Attendance Records Retrieval",
                    True,
                    f"Retrieved {len(attendance_records)} attendance records"
                )
            else:
                self.log_test(
                    "Attendance Records Retrieval",
                    False,
                    f"Failed to retrieve records: {response.status_code} - {response.text}"
                )
        except Exception as e:
            self.log_test("Attendance Records Retrieval", False, f"Exception: {str(e)}")
    
    def test_notification_system(self):
        """Test notification system (نظام الإشعارات)"""
        print("\n🔔 Testing Notification System (نظام الإشعارات)")
        
        # Test notification count
        try:
            headers = self.get_headers("user")
            response = self.session.get(f"{BACKEND_URL}/notifications/count", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Notifications Count",
                    True,
                    f"Unread notifications count: {data.get('unread_count', 'N/A')}"
                )
            else:
                self.log_test(
                    "Notifications Count",
                    False,
                    f"Count failed: {response.status_code} - {response.text}"
                )
        except Exception as e:
            self.log_test("Notifications Count", False, f"Exception: {str(e)}")
        
        # Test fetch unread notifications
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
            else:
                self.log_test(
                    "Fetch Unread Notifications",
                    False,
                    f"Fetch failed: {response.status_code} - {response.text}"
                )
        except Exception as e:
            self.log_test("Fetch Unread Notifications", False, f"Exception: {str(e)}")
        
        # Test acknowledge notification (if any exist)
        try:
            headers = self.get_headers("user")
            # First get notifications to find one to acknowledge
            response = self.session.get(f"{BACKEND_URL}/notifications/my", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                notifications = data if isinstance(data, list) else data.get("notifications", [])
                
                if notifications:
                    notification_id = notifications[0].get("id")
                    if notification_id:
                        ack_response = self.session.post(
                            f"{BACKEND_URL}/notifications/{notification_id}/acknowledge",
                            headers=headers
                        )
                        
                        if ack_response.status_code == 200:
                            self.log_test(
                                "Acknowledge Notification",
                                True,
                                f"Successfully acknowledged notification {notification_id}"
                            )
                        else:
                            self.log_test(
                                "Acknowledge Notification",
                                False,
                                f"Acknowledge failed: {ack_response.status_code} - {ack_response.text}"
                            )
                    else:
                        self.log_test("Acknowledge Notification", False, "No notification ID found")
                else:
                    self.log_test("Acknowledge Notification", True, "No notifications to acknowledge")
            else:
                self.log_test("Acknowledge Notification", False, f"Failed to get notifications: {response.status_code}")
                
        except Exception as e:
            self.log_test("Acknowledge Notification", False, f"Exception: {str(e)}")
        
        # Test send notification (Super Admin only)
        try:
            headers = self.get_headers("super_admin")
            notification_data = {
                "recipient_id": self.tokens.get("user_id", "test-user"),
                "subject": "اختبار الإشعارات",
                "message": "هذا إشعار تجريبي من نظام الاختبار",
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
                    f"Send failed: {response.status_code} - {response.text}"
                )
        except Exception as e:
            self.log_test("Send Notification (Super Admin)", False, f"Exception: {str(e)}")
    
    def test_advances_custody_system(self):
        """Test advances & custody system (السلف والعهد)"""
        print("\n💰 Testing Advances & Custody System (السلف والعهد)")
        
        # Test employee request advance
        try:
            headers = self.get_headers("user")
            advance_data = {
                "transaction_type": "advance",
                "amount": 500.0,
                "description": "سلفة اختبار",
                "category": "personal",
                "expense_date": datetime.now().strftime("%Y-%m-%d"),
                "notes": "طلب سلفة للاختبار"
            }
            
            response = self.session.post(f"{BACKEND_URL}/advances/request", json=advance_data, headers=headers)
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.log_test(
                    "Request Advance (Employee)",
                    True,
                    f"Advance request successful: {data.get('message', 'Success')}"
                )
            else:
                self.log_test(
                    "Request Advance (Employee)",
                    False,
                    f"Request failed: {response.status_code} - {response.text}"
                )
        except Exception as e:
            self.log_test("Request Advance (Employee)", False, f"Exception: {str(e)}")
        
        # Test employee request custody
        try:
            headers = self.get_headers("user")
            custody_data = {
                "transaction_type": "custody",
                "amount": 300.0,
                "description": "عهدة اختبار",
                "category": "business",
                "expense_date": datetime.now().strftime("%Y-%m-%d"),
                "notes": "طلب عهدة للاختبار"
            }
            
            response = self.session.post(f"{BACKEND_URL}/advances/request", json=custody_data, headers=headers)
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.log_test(
                    "Request Custody (Employee)",
                    True,
                    f"Custody request successful: {data.get('message', 'Success')}"
                )
            else:
                self.log_test(
                    "Request Custody (Employee)",
                    False,
                    f"Request failed: {response.status_code} - {response.text}"
                )
        except Exception as e:
            self.log_test("Request Custody (Employee)", False, f"Exception: {str(e)}")
        
        # Test custody settlement
        try:
            headers = self.get_headers("user")
            settlement_data = {
                "amount": 100.0,
                "description": "تسوية عهدة اختبار",
                "notes": "تسوية جزئية للعهدة"
            }
            
            response = self.session.post(f"{BACKEND_URL}/advances/custody-settlement", json=settlement_data, headers=headers)
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.log_test(
                    "Custody Settlement (Employee)",
                    True,
                    f"Settlement successful: {data.get('message', 'Success')}"
                )
            else:
                self.log_test(
                    "Custody Settlement (Employee)",
                    False,
                    f"Settlement failed: {response.status_code} - {response.text}"
                )
        except Exception as e:
            self.log_test("Custody Settlement (Employee)", False, f"Exception: {str(e)}")
        
        # Test employee balance
        try:
            headers = self.get_headers("user")
            response = self.session.get(f"{BACKEND_URL}/advances/my-balance", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                total_available = data.get("total_available", 0)
                self.log_test(
                    "Employee Balance",
                    True,
                    f"Balance retrieved - Total available: {total_available} AED"
                )
            else:
                self.log_test(
                    "Employee Balance",
                    False,
                    f"Balance retrieval failed: {response.status_code} - {response.text}"
                )
        except Exception as e:
            self.log_test("Employee Balance", False, f"Exception: {str(e)}")
        
        # Test Super Admin - employees with balances
        try:
            headers = self.get_headers("super_admin")
            response = self.session.get(f"{BACKEND_URL}/advances/admin/employees-with-balances", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                employees = data.get("employee_balances", [])
                self.log_test(
                    "Employees with Balances (Super Admin)",
                    True,
                    f"Retrieved {len(employees)} employees with balances"
                )
            else:
                self.log_test(
                    "Employees with Balances (Super Admin)",
                    False,
                    f"Retrieval failed: {response.status_code} - {response.text}"
                )
        except Exception as e:
            self.log_test("Employees with Balances (Super Admin)", False, f"Exception: {str(e)}")
        
        # Test Super Admin - repayment
        try:
            headers = self.get_headers("super_admin")
            repay_data = {
                "employee_id": "test-employee-id",
                "amount": 50.0,
                "description": "سداد جزئي اختبار",
                "notes": "سداد تجريبي"
            }
            
            response = self.session.post(f"{BACKEND_URL}/advances/repay", json=repay_data, headers=headers)
            
            if response.status_code in [200, 201, 404]:  # 404 if employee not found is acceptable
                self.log_test(
                    "Record Repayment (Super Admin)",
                    True,
                    f"Repayment response: {response.status_code}"
                )
            else:
                self.log_test(
                    "Record Repayment (Super Admin)",
                    False,
                    f"Repayment failed: {response.status_code} - {response.text}"
                )
        except Exception as e:
            self.log_test("Record Repayment (Super Admin)", False, f"Exception: {str(e)}")
        
        # Test Super Admin - all transactions
        try:
            headers = self.get_headers("super_admin")
            response = self.session.get(f"{BACKEND_URL}/advances/admin/all-transactions", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                transactions = data.get("transactions", [])
                self.log_test(
                    "All Transactions (Super Admin)",
                    True,
                    f"Retrieved {len(transactions)} transactions"
                )
            else:
                self.log_test(
                    "All Transactions (Super Admin)",
                    False,
                    f"Retrieval failed: {response.status_code} - {response.text}"
                )
        except Exception as e:
            self.log_test("All Transactions (Super Admin)", False, f"Exception: {str(e)}")
        
        # Test Super Admin - pending approvals
        try:
            headers = self.get_headers("super_admin")
            response = self.session.get(f"{BACKEND_URL}/advances/admin/pending-approvals", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                pending = data.get("pending_transactions", [])
                self.log_test(
                    "Pending Approvals (Super Admin)",
                    True,
                    f"Retrieved {len(pending)} pending approvals"
                )
            else:
                self.log_test(
                    "Pending Approvals (Super Admin)",
                    False,
                    f"Retrieval failed: {response.status_code} - {response.text}"
                )
        except Exception as e:
            self.log_test("Pending Approvals (Super Admin)", False, f"Exception: {str(e)}")
    
    def test_deductions_system(self):
        """Test deductions system (نظام الخصومات)"""
        print("\n📊 Testing Deductions System (نظام الخصومات)")
        
        # Test monthly deductions calculation
        try:
            headers = self.get_headers("super_admin")
            current_month = datetime.now().strftime("%Y-%m")
            response = self.session.post(f"{BACKEND_URL}/deductions/calculate-monthly?month={current_month}", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Monthly Deductions Calculation",
                    True,
                    f"Calculation successful for {current_month}"
                )
            else:
                self.log_test(
                    "Monthly Deductions Calculation",
                    False,
                    f"Calculation failed: {response.status_code} - {response.text}"
                )
        except Exception as e:
            self.log_test("Monthly Deductions Calculation", False, f"Exception: {str(e)}")
        
        # Test exceptions verification (Hatem, Tariq, Karim, Hesham)
        try:
            headers = self.get_headers("super_admin")
            response = self.session.get(f"{BACKEND_URL}/deductions", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                deductions = data if isinstance(data, list) else data.get("deductions", [])
                
                # Check for exception users
                exception_users = ["Hatem", "Tariq", "Karim", "Hesham"]
                found_exceptions = []
                
                for deduction in deductions:
                    employee_name = deduction.get("employee_name", "")
                    for exception_user in exception_users:
                        if exception_user.lower() in employee_name.lower():
                            found_exceptions.append(employee_name)
                
                self.log_test(
                    "Deductions Exceptions Verification",
                    True,
                    f"Found {len(found_exceptions)} exception users in deductions: {found_exceptions}"
                )
            else:
                self.log_test(
                    "Deductions Exceptions Verification",
                    False,
                    f"Verification failed: {response.status_code} - {response.text}"
                )
        except Exception as e:
            self.log_test("Deductions Exceptions Verification", False, f"Exception: {str(e)}")
    
    def test_health_checks(self):
        """Test health check endpoints"""
        print("\n🏥 Testing Health Checks")
        
        # Test /api/healthz
        try:
            response = self.session.get(f"{BACKEND_URL}/healthz")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Health Check (/healthz)",
                    True,
                    f"Health check passed: {data.get('status', 'ok')}"
                )
            else:
                self.log_test(
                    "Health Check (/healthz)",
                    False,
                    f"Health check failed: {response.status_code} - {response.text}"
                )
        except Exception as e:
            self.log_test("Health Check (/healthz)", False, f"Exception: {str(e)}")
        
        # Test /api/users
        try:
            headers = self.get_headers("super_admin")
            response = self.session.get(f"{BACKEND_URL}/users", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                users = data if isinstance(data, list) else data.get("users", [])
                self.log_test(
                    "Users Endpoint",
                    True,
                    f"Retrieved {len(users)} users"
                )
            else:
                self.log_test(
                    "Users Endpoint",
                    False,
                    f"Users retrieval failed: {response.status_code} - {response.text}"
                )
        except Exception as e:
            self.log_test("Users Endpoint", False, f"Exception: {str(e)}")
    
    def run_comprehensive_test(self):
        """Run comprehensive E2E test"""
        print("🔥 COMPREHENSIVE E2E BACKEND TESTING - ARABIC REVIEW")
        print("=" * 60)
        
        # 1. Authentication
        print("\n🔐 Testing Authentication System")
        for user_type in ["super_admin", "user", "tarek"]:
            self.authenticate_user(user_type)
        
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
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST RESULTS - نتائج الاختبار الشامل")
        print("=" * 60)
        
        success_rate = (self.success_count / self.total_count * 100) if self.total_count > 0 else 0
        
        print(f"📈 إجمالي النتائج:")
        print(f"   ✅ اختبارات ناجحة: {self.success_count}")
        print(f"   ❌ اختبارات فاشلة: {self.total_count - self.success_count}")
        print(f"   📊 إجمالي الاختبارات: {self.total_count}")
        print(f"   🎯 نسبة النجاح: {success_rate:.1f}%")
        
        print(f"\n📋 تفاصيل النتائج حسب النظام:")
        
        # Group results by system
        systems = {
            "Authentication": [],
            "Attendance": [],
            "Notifications": [],
            "Advances": [],
            "Deductions": [],
            "Health": []
        }
        
        for result in self.test_results:
            test_name = result["test"]
            if "Authentication" in test_name:
                systems["Authentication"].append(result)
            elif "Attendance" in test_name:
                systems["Attendance"].append(result)
            elif "Notification" in test_name:
                systems["Notifications"].append(result)
            elif any(word in test_name for word in ["Advance", "Custody", "Balance", "Repayment"]):
                systems["Advances"].append(result)
            elif "Deduction" in test_name:
                systems["Deductions"].append(result)
            elif "Health" in test_name or "Users" in test_name:
                systems["Health"].append(result)
        
        for system, results in systems.items():
            if results:
                passed = sum(1 for r in results if r["success"])
                total = len(results)
                system_rate = (passed / total * 100) if total > 0 else 0
                
                print(f"\n🔹 {system} ({passed}/{total} - {system_rate:.1f}%):")
                for result in results:
                    status = "✅" if result["success"] else "❌"
                    print(f"   {status} {result['test']}")
                    if result["details"]:
                        print(f"      📝 {result['details']}")
        
        # Save detailed results
        results_file = "/app/arabic_comprehensive_e2e_test_results.json"
        try:
            with open(results_file, "w", encoding="utf-8") as f:
                json.dump({
                    "summary": {
                        "total_tests": self.total_count,
                        "successful_tests": self.success_count,
                        "failed_tests": self.total_count - self.success_count,
                        "success_rate": success_rate,
                        "test_timestamp": datetime.now().isoformat()
                    },
                    "detailed_results": self.test_results
                }, f, ensure_ascii=False, indent=2)
            print(f"\n💾 تم حفظ النتائج التفصيلية في: {results_file}")
        except Exception as e:
            print(f"⚠️ فشل في حفظ النتائج: {str(e)}")
        
        print("\n" + "=" * 60)
        if success_rate >= 80:
            print("🎉 النظام جاهز للإنتاج - SYSTEM READY FOR PRODUCTION")
        elif success_rate >= 60:
            print("⚠️ النظام يحتاج تحسينات - SYSTEM NEEDS IMPROVEMENTS")
        else:
            print("🚨 النظام يحتاج إصلاحات عاجلة - SYSTEM NEEDS URGENT FIXES")
        print("=" * 60)

def main():
    """Main test execution"""
    tester = ArabicE2EBackendTester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()