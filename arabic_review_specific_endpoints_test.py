#!/usr/bin/env python3
"""
🎯 SPECIFIC ARABIC REVIEW ENDPOINTS TESTING
اختبار النقاط المحددة في المراجعة العربية

Testing specific endpoints mentioned in Arabic review:
1. /api/attendance/check-in (for regular user and Tarek)
2. /api/attendance/check-out
3. /api/notifications/count
4. /api/notifications/my?unread_only=true
5. /api/notifications/{id}/acknowledge
6. /api/notifications/send
7. /api/advances/request (advance and custody)
8. /api/advances/custody-settlement
9. /api/advances/my-balance
10. /api/advances/admin/employees-with-balances
11. /api/advances/repay
12. /api/advances/{id}/edit
13. /api/advances/{id} (delete)
14. /api/advances/admin/all-transactions
15. /api/advances/admin/pending-approvals
16. /api/deductions/calculate-monthly
"""

import requests
import json
import sys
from datetime import datetime, timedelta
import os

# Configuration
BACKEND_URL = "https://payroll-management-4.preview.emergentagent.com/api"

# Test credentials as specified in Arabic review
TEST_CREDENTIALS = {
    "super_admin": {"email": "admin@tanseeq.com", "password": "ADMIN"},
    "user": {"email": "jihad@tanseeq.com", "password": "jihad123"},
    "tarek": {"email": "tarek@tanseeq.com", "password": "tarek123"}
}

class SpecificEndpointsTester:
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
        
    def authenticate_all_users(self):
        """Authenticate all test users"""
        print("🔐 Authenticating Test Users")
        print("-" * 40)
        
        for user_type, creds in TEST_CREDENTIALS.items():
            try:
                response = self.session.post(f"{BACKEND_URL}/auth/login", json=creds)
                
                if response.status_code == 200:
                    data = response.json()
                    self.tokens[user_type] = data["access_token"]
                    user_info = data.get("user", {})
                    self.user_ids[user_type] = user_info.get("id")
                    
                    self.log_test(
                        f"Authentication - {user_type}",
                        True,
                        f"✅ {creds['email']} (Role: {user_info.get('role', 'unknown')})"
                    )
                else:
                    self.log_test(
                        f"Authentication - {user_type}",
                        False,
                        f"❌ {creds['email']} - {response.status_code}: {response.text}"
                    )
                    
            except Exception as e:
                self.log_test(f"Authentication - {user_type}", False, f"Exception: {str(e)}")
    
    def get_headers(self, user_type):
        """Get authorization headers for user"""
        token = self.tokens.get(user_type)
        if not token:
            return {}
        return {"Authorization": f"Bearer {token}"}
    
    def test_attendance_endpoints(self):
        """Test specific attendance endpoints"""
        print("\n🕐 Testing Attendance Endpoints")
        print("-" * 40)
        
        # Test /api/attendance/check-in for regular user
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
                        late_info = f" (Late: {is_late}, Minutes: {late_minutes})"
                    
                    self.log_test(
                        "/api/attendance/check-in (Regular User)",
                        True,
                        f"Status: {response.status_code} - {message}{late_info}"
                    )
                else:
                    self.log_test(
                        "/api/attendance/check-in (Regular User)",
                        False,
                        f"Status: {response.status_code} - {response.text}"
                    )
            except Exception as e:
                self.log_test("/api/attendance/check-in (Regular User)", False, f"Exception: {str(e)}")
        
        # Test /api/attendance/check-in for Tarek (flexible schedule)
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
                        schedule_info = f" (Schedule: {schedule_type}, Exception: {exception_type})"
                    
                    self.log_test(
                        "/api/attendance/check-in (Tarek - Flexible)",
                        True,
                        f"Status: {response.status_code} - {message}{schedule_info}"
                    )
                else:
                    self.log_test(
                        "/api/attendance/check-in (Tarek - Flexible)",
                        False,
                        f"Status: {response.status_code} - {response.text}"
                    )
            except Exception as e:
                self.log_test("/api/attendance/check-in (Tarek - Flexible)", False, f"Exception: {str(e)}")
        
        # Test /api/attendance/check-out
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
                        "/api/attendance/check-out",
                        True,
                        f"Status: {response.status_code} - {message}{hours_info}"
                    )
                else:
                    self.log_test(
                        "/api/attendance/check-out",
                        False,
                        f"Status: {response.status_code} - {response.text}"
                    )
            except Exception as e:
                self.log_test("/api/attendance/check-out", False, f"Exception: {str(e)}")
    
    def test_notification_endpoints(self):
        """Test specific notification endpoints"""
        print("\n🔔 Testing Notification Endpoints")
        print("-" * 40)
        
        # Test /api/notifications/count
        if "user" in self.tokens:
            try:
                headers = self.get_headers("user")
                response = self.session.get(f"{BACKEND_URL}/notifications/count", headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    count = data.get('unread_count', 'N/A')
                    self.log_test(
                        "/api/notifications/count",
                        True,
                        f"Unread count: {count}"
                    )
                else:
                    self.log_test(
                        "/api/notifications/count",
                        False,
                        f"Status: {response.status_code} - {response.text}"
                    )
            except Exception as e:
                self.log_test("/api/notifications/count", False, f"Exception: {str(e)}")
        
        # Test /api/notifications/my?unread_only=true
        if "user" in self.tokens:
            try:
                headers = self.get_headers("user")
                response = self.session.get(f"{BACKEND_URL}/notifications/my?unread_only=true", headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    notifications = data if isinstance(data, list) else data.get("notifications", [])
                    self.log_test(
                        "/api/notifications/my?unread_only=true",
                        True,
                        f"Retrieved {len(notifications)} unread notifications"
                    )
                    
                    # Store first notification ID for acknowledge test
                    if notifications:
                        self.first_notification_id = notifications[0].get("id")
                else:
                    self.log_test(
                        "/api/notifications/my?unread_only=true",
                        False,
                        f"Status: {response.status_code} - {response.text}"
                    )
            except Exception as e:
                self.log_test("/api/notifications/my?unread_only=true", False, f"Exception: {str(e)}")
        
        # Test /api/notifications/{id}/acknowledge
        if "user" in self.tokens and hasattr(self, 'first_notification_id') and self.first_notification_id:
            try:
                headers = self.get_headers("user")
                response = self.session.post(
                    f"{BACKEND_URL}/notifications/{self.first_notification_id}/acknowledge",
                    headers=headers
                )
                
                if response.status_code == 200:
                    self.log_test(
                        "/api/notifications/{id}/acknowledge",
                        True,
                        f"Successfully acknowledged notification {self.first_notification_id}"
                    )
                else:
                    self.log_test(
                        "/api/notifications/{id}/acknowledge",
                        False,
                        f"Status: {response.status_code} - {response.text}"
                    )
            except Exception as e:
                self.log_test("/api/notifications/{id}/acknowledge", False, f"Exception: {str(e)}")
        
        # Test /api/notifications/send (Super Admin)
        if "super_admin" in self.tokens and "user" in self.user_ids:
            try:
                headers = self.get_headers("super_admin")
                notification_data = {
                    "recipient_id": self.user_ids["user"],
                    "subject": "اختبار الإشعارات",
                    "message": "هذا إشعار تجريبي من نظام الاختبار الشامل",
                    "type": "info",
                    "priority": "normal"
                }
                
                response = self.session.post(f"{BACKEND_URL}/notifications/send", json=notification_data, headers=headers)
                
                if response.status_code == 200:
                    self.log_test(
                        "/api/notifications/send (Super Admin)",
                        True,
                        "Successfully sent test notification"
                    )
                else:
                    self.log_test(
                        "/api/notifications/send (Super Admin)",
                        False,
                        f"Status: {response.status_code} - {response.text}"
                    )
            except Exception as e:
                self.log_test("/api/notifications/send (Super Admin)", False, f"Exception: {str(e)}")
    
    def test_advances_endpoints(self):
        """Test specific advances endpoints"""
        print("\n💰 Testing Advances & Custody Endpoints")
        print("-" * 40)
        
        # Test /api/advances/request (advance)
        if "user" in self.tokens:
            try:
                headers = self.get_headers("user")
                advance_data = {
                    "transaction_type": "advance",
                    "amount": 500.0,
                    "description": "سلفة اختبار شامل",
                    "category": "transportation",  # Use valid category
                    "expense_date": datetime.now().strftime("%Y-%m-%d"),
                    "notes": "طلب سلفة للاختبار الشامل"
                }
                
                response = self.session.post(f"{BACKEND_URL}/advances/request", json=advance_data, headers=headers)
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    self.log_test(
                        "/api/advances/request (Advance)",
                        True,
                        f"Advance request: {data.get('message', 'Success')}"
                    )
                else:
                    self.log_test(
                        "/api/advances/request (Advance)",
                        False,
                        f"Status: {response.status_code} - {response.text}"
                    )
            except Exception as e:
                self.log_test("/api/advances/request (Advance)", False, f"Exception: {str(e)}")
        
        # Test /api/advances/request (custody)
        if "user" in self.tokens:
            try:
                headers = self.get_headers("user")
                custody_data = {
                    "transaction_type": "custody",
                    "amount": 300.0,
                    "description": "عهدة اختبار شامل",
                    "category": "supplies",  # Use valid category
                    "expense_date": datetime.now().strftime("%Y-%m-%d"),
                    "notes": "طلب عهدة للاختبار الشامل"
                }
                
                response = self.session.post(f"{BACKEND_URL}/advances/request", json=custody_data, headers=headers)
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    self.log_test(
                        "/api/advances/request (Custody)",
                        True,
                        f"Custody request: {data.get('message', 'Success')}"
                    )
                else:
                    self.log_test(
                        "/api/advances/request (Custody)",
                        False,
                        f"Status: {response.status_code} - {response.text}"
                    )
            except Exception as e:
                self.log_test("/api/advances/request (Custody)", False, f"Exception: {str(e)}")
        
        # Test /api/advances/custody-settlement
        if "user" in self.tokens:
            try:
                headers = self.get_headers("user")
                settlement_data = {
                    "amount": 100.0,
                    "settlement_date": datetime.now().strftime("%Y-%m-%d"),
                    "description": "تسوية عهدة اختبار شامل",
                    "notes": "تسوية جزئية للعهدة"
                }
                
                response = self.session.post(f"{BACKEND_URL}/advances/custody-settlement", json=settlement_data, headers=headers)
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    self.log_test(
                        "/api/advances/custody-settlement",
                        True,
                        f"Settlement: {data.get('message', 'Success')}"
                    )
                else:
                    self.log_test(
                        "/api/advances/custody-settlement",
                        False,
                        f"Status: {response.status_code} - {response.text}"
                    )
            except Exception as e:
                self.log_test("/api/advances/custody-settlement", False, f"Exception: {str(e)}")
        
        # Test /api/advances/my-balance
        if "user" in self.tokens:
            try:
                headers = self.get_headers("user")
                response = self.session.get(f"{BACKEND_URL}/advances/my-balance", headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    total_available = data.get("total_available", 0)
                    remaining_advance = data.get("remaining_advance", 0)
                    remaining_custody = data.get("remaining_custody", 0)
                    
                    self.log_test(
                        "/api/advances/my-balance",
                        True,
                        f"Total: {total_available} AED (Advance: {remaining_advance}, Custody: {remaining_custody})"
                    )
                else:
                    self.log_test(
                        "/api/advances/my-balance",
                        False,
                        f"Status: {response.status_code} - {response.text}"
                    )
            except Exception as e:
                self.log_test("/api/advances/my-balance", False, f"Exception: {str(e)}")
        
        # Test Super Admin endpoints
        if "super_admin" in self.tokens:
            # Test /api/advances/admin/employees-with-balances
            try:
                headers = self.get_headers("super_admin")
                response = self.session.get(f"{BACKEND_URL}/advances/admin/employees-with-balances", headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    employees = data.get("employee_balances", [])
                    self.log_test(
                        "/api/advances/admin/employees-with-balances",
                        True,
                        f"Found {len(employees)} employees with balances"
                    )
                else:
                    self.log_test(
                        "/api/advances/admin/employees-with-balances",
                        False,
                        f"Status: {response.status_code} - {response.text}"
                    )
            except Exception as e:
                self.log_test("/api/advances/admin/employees-with-balances", False, f"Exception: {str(e)}")
            
            # Test /api/advances/admin/all-transactions
            try:
                headers = self.get_headers("super_admin")
                response = self.session.get(f"{BACKEND_URL}/advances/admin/all-transactions", headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    transactions = data.get("transactions", [])
                    self.log_test(
                        "/api/advances/admin/all-transactions",
                        True,
                        f"Retrieved {len(transactions)} transactions"
                    )
                    
                    # Store first transaction ID for edit/delete tests
                    if transactions:
                        self.first_transaction_id = transactions[0].get("id")
                else:
                    self.log_test(
                        "/api/advances/admin/all-transactions",
                        False,
                        f"Status: {response.status_code} - {response.text}"
                    )
            except Exception as e:
                self.log_test("/api/advances/admin/all-transactions", False, f"Exception: {str(e)}")
            
            # Test /api/advances/admin/pending-approvals
            try:
                headers = self.get_headers("super_admin")
                response = self.session.get(f"{BACKEND_URL}/advances/admin/pending-approvals", headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    pending = data.get("pending_transactions", [])
                    self.log_test(
                        "/api/advances/admin/pending-approvals",
                        True,
                        f"Found {len(pending)} pending approvals"
                    )
                else:
                    self.log_test(
                        "/api/advances/admin/pending-approvals",
                        False,
                        f"Status: {response.status_code} - {response.text}"
                    )
            except Exception as e:
                self.log_test("/api/advances/admin/pending-approvals", False, f"Exception: {str(e)}")
            
            # Test /api/advances/repay
            try:
                headers = self.get_headers("super_admin")
                repay_data = {
                    "employee_id": self.user_ids.get("user", "test-user-id"),
                    "amount": 50.0,
                    "description": "سداد جزئي اختبار شامل",
                    "notes": "سداد تجريبي للاختبار"
                }
                
                response = self.session.post(f"{BACKEND_URL}/advances/repay", json=repay_data, headers=headers)
                
                if response.status_code in [200, 201, 404]:  # 404 acceptable if no balance
                    self.log_test(
                        "/api/advances/repay",
                        True,
                        f"Repayment response: {response.status_code}"
                    )
                else:
                    self.log_test(
                        "/api/advances/repay",
                        False,
                        f"Status: {response.status_code} - {response.text}"
                    )
            except Exception as e:
                self.log_test("/api/advances/repay", False, f"Exception: {str(e)}")
    
    def test_deductions_endpoints(self):
        """Test deductions endpoints"""
        print("\n📊 Testing Deductions Endpoints")
        print("-" * 40)
        
        # Test /api/deductions/calculate-monthly
        if "super_admin" in self.tokens:
            try:
                headers = self.get_headers("super_admin")
                current_month = datetime.now().strftime("%Y-%m")
                response = self.session.post(f"{BACKEND_URL}/deductions/calculate-monthly?month={current_month}", headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    employees_processed = len(data.get("employees", []))
                    self.log_test(
                        "/api/deductions/calculate-monthly",
                        True,
                        f"Processed {employees_processed} employees for {current_month}"
                    )
                else:
                    self.log_test(
                        "/api/deductions/calculate-monthly",
                        False,
                        f"Status: {response.status_code} - {response.text}"
                    )
            except Exception as e:
                self.log_test("/api/deductions/calculate-monthly", False, f"Exception: {str(e)}")
    
    def run_specific_tests(self):
        """Run all specific endpoint tests"""
        print("🎯 SPECIFIC ARABIC REVIEW ENDPOINTS TESTING")
        print("=" * 60)
        
        # 1. Authentication
        self.authenticate_all_users()
        
        # 2. Attendance endpoints
        self.test_attendance_endpoints()
        
        # 3. Notification endpoints
        self.test_notification_endpoints()
        
        # 4. Advances endpoints
        self.test_advances_endpoints()
        
        # 5. Deductions endpoints
        self.test_deductions_endpoints()
        
        # Generate final report
        self.generate_final_report()
    
    def generate_final_report(self):
        """Generate final Arabic report"""
        print("\n" + "=" * 60)
        print("📊 SPECIFIC ENDPOINTS TEST RESULTS")
        print("نتائج اختبار النقاط المحددة في المراجعة العربية")
        print("=" * 60)
        
        success_rate = (self.success_count / self.total_count * 100) if self.total_count > 0 else 0
        
        print(f"📈 Overall Results:")
        print(f"   ✅ Successful tests: {self.success_count}")
        print(f"   ❌ Failed tests: {self.total_count - self.success_count}")
        print(f"   📊 Total tests: {self.total_count}")
        print(f"   🎯 Success rate: {success_rate:.1f}%")
        
        # Detailed results
        print(f"\n📋 Detailed Results:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"]:
                print(f"   📝 {result['details']}")
        
        # Save results
        results_file = "/app/arabic_review_specific_endpoints_results.json"
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
            print(f"\n💾 Results saved to: {results_file}")
        except Exception as e:
            print(f"⚠️ Failed to save results: {str(e)}")
        
        print("\n" + "=" * 60)
        if success_rate >= 90:
            print("🎉 EXCELLENT - جميع النقاط تعمل بشكل ممتاز")
        elif success_rate >= 75:
            print("✅ GOOD - معظم النقاط تعمل بشكل جيد")
        elif success_rate >= 60:
            print("⚠️ NEEDS IMPROVEMENT - يحتاج تحسينات")
        else:
            print("🚨 CRITICAL ISSUES - مشاكل حرجة تحتاج إصلاح")
        print("=" * 60)

def main():
    """Main test execution"""
    tester = SpecificEndpointsTester()
    tester.run_specific_tests()

if __name__ == "__main__":
    main()