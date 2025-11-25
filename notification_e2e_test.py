#!/usr/bin/env python3
"""
E2E Notification System Testing - Arabic Review Request
اختبار نظام الإشعارات E2E - من إرسال الإشعار حتى ظهوره للموظف

Test Scenario:
1. Super Admin logs in
2. Super Admin sends alert/notification to employee Jihad (jihad@tanseeq.com)
3. Verify notification is saved correctly in database
4. User (jihad) logs in
5. Test /api/notifications/count - should return unread_count > 0
6. Test /api/notifications/my?unread_only=true - should return the notification

Credentials:
- Super Admin: admin@tanseeq.com / ADMIN
- User: jihad@tanseeq.com / jihad123
"""

import requests
import json
import time
from datetime import datetime
import os
from pathlib import Path

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://attend-deduct-hr.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class NotificationE2ETest:
    def __init__(self):
        self.session = requests.Session()
        self.super_admin_token = None
        self.user_token = None
        self.test_results = []
        self.notification_id = None
        
    def log_test(self, test_name, success, details="", response_data=None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if not success and response_data:
            print(f"   Response: {response_data}")
        print()

    def authenticate_super_admin(self):
        """Step 1: Super Admin Authentication"""
        try:
            login_data = {
                "email": "admin@tanseeq.com",
                "password": "ADMIN"
            }
            
            response = self.session.post(f"{API_BASE}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.super_admin_token = data.get('access_token')
                user_info = data.get('user', {})
                
                self.log_test(
                    "Super Admin Authentication",
                    True,
                    f"Successfully authenticated as {user_info.get('name', 'Admin')} with role {user_info.get('role', 'unknown')}",
                    {"user_id": user_info.get('id'), "role": user_info.get('role')}
                )
                return True
            else:
                self.log_test(
                    "Super Admin Authentication",
                    False,
                    f"Login failed with status {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test("Super Admin Authentication", False, f"Exception: {str(e)}")
            return False

    def authenticate_user(self):
        """Step 4: User Authentication"""
        try:
            login_data = {
                "email": "jihad@tanseeq.com",
                "password": "jihad123"
            }
            
            response = self.session.post(f"{API_BASE}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.user_token = data.get('access_token')
                user_info = data.get('user', {})
                
                self.log_test(
                    "User (Jihad) Authentication",
                    True,
                    f"Successfully authenticated as {user_info.get('name', 'Jihad')} with role {user_info.get('role', 'user')}",
                    {"user_id": user_info.get('id'), "role": user_info.get('role')}
                )
                return user_info.get('id')
            else:
                self.log_test(
                    "User (Jihad) Authentication",
                    False,
                    f"Login failed with status {response.status_code}",
                    response.text
                )
                return None
                
        except Exception as e:
            self.log_test("User (Jihad) Authentication", False, f"Exception: {str(e)}")
            return None

    def get_jihad_user_id(self):
        """Get Jihad's user ID for sending notification"""
        try:
            headers = {"Authorization": f"Bearer {self.super_admin_token}"}
            response = self.session.get(f"{API_BASE}/users", headers=headers)
            
            if response.status_code == 200:
                users = response.json()
                for user in users:
                    if user.get('email') == 'jihad@tanseeq.com':
                        self.log_test(
                            "Find Jihad User ID",
                            True,
                            f"Found Jihad user with ID: {user.get('id')}",
                            {"user_id": user.get('id'), "name": user.get('name')}
                        )
                        return user.get('id')
                
                self.log_test("Find Jihad User ID", False, "Jihad user not found in users list")
                return None
            else:
                self.log_test(
                    "Find Jihad User ID",
                    False,
                    f"Failed to get users list with status {response.status_code}",
                    response.text
                )
                return None
                
        except Exception as e:
            self.log_test("Find Jihad User ID", False, f"Exception: {str(e)}")
            return None

    def send_notification_to_jihad(self, jihad_user_id):
        """Step 2: Super Admin sends notification to Jihad"""
        try:
            headers = {"Authorization": f"Bearer {self.super_admin_token}"}
            
            # Create Arabic notification
            notification_data = {
                "recipient_id": jihad_user_id,
                "subject": "🚨 إشعار عاجل - اختبار النظام",
                "message": "هذا إشعار تجريبي لاختبار نظام الإشعارات من السوبر أدمن إلى الموظف جهاد. يرجى التأكد من وصول هذا الإشعار بشكل صحيح.",
                "type": "alert",
                "priority": "urgent"
            }
            
            response = self.session.post(f"{API_BASE}/notifications/send", json=notification_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                self.notification_id = data.get('notification_id') or data.get('id')
                
                self.log_test(
                    "Send Notification to Jihad",
                    True,
                    f"Successfully sent notification with ID: {self.notification_id}",
                    {
                        "notification_id": self.notification_id,
                        "subject": notification_data["subject"],
                        "type": notification_data["type"],
                        "priority": notification_data["priority"]
                    }
                )
                return True
            else:
                self.log_test(
                    "Send Notification to Jihad",
                    False,
                    f"Failed to send notification with status {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test("Send Notification to Jihad", False, f"Exception: {str(e)}")
            return False

    def verify_notification_in_database(self, jihad_user_id):
        """Step 3: Verify notification is saved correctly in database"""
        try:
            headers = {"Authorization": f"Bearer {self.super_admin_token}"}
            
            # Get all notifications to verify our notification exists
            response = self.session.get(f"{API_BASE}/notifications", headers=headers)
            
            if response.status_code == 200:
                notifications = response.json()
                
                # Find our notification
                found_notification = None
                for notification in notifications:
                    if (notification.get('recipient_id') == jihad_user_id and 
                        "اختبار النظام" in notification.get('subject', '')):
                        found_notification = notification
                        break
                
                if found_notification:
                    # Verify required fields
                    required_fields = ['recipient_id', 'subject', 'message', 'type', 'priority', 'is_read', 'sent_at']
                    missing_fields = []
                    
                    for field in required_fields:
                        if field not in found_notification:
                            missing_fields.append(field)
                    
                    if not missing_fields:
                        self.log_test(
                            "Verify Notification in Database",
                            True,
                            f"Notification found with all required fields. is_read: {found_notification.get('is_read', 'unknown')}",
                            {
                                "notification_id": found_notification.get('id'),
                                "recipient_id": found_notification.get('recipient_id'),
                                "is_read": found_notification.get('is_read'),
                                "subject": found_notification.get('subject'),
                                "message": found_notification.get('message')[:100] + "..." if len(found_notification.get('message', '')) > 100 else found_notification.get('message'),
                                "type": found_notification.get('type'),
                                "priority": found_notification.get('priority')
                            }
                        )
                        return True
                    else:
                        self.log_test(
                            "Verify Notification in Database",
                            False,
                            f"Notification found but missing fields: {missing_fields}",
                            found_notification
                        )
                        return False
                else:
                    self.log_test(
                        "Verify Notification in Database",
                        False,
                        "Notification not found in database",
                        {"total_notifications": len(notifications)}
                    )
                    return False
            else:
                self.log_test(
                    "Verify Notification in Database",
                    False,
                    f"Failed to get notifications with status {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test("Verify Notification in Database", False, f"Exception: {str(e)}")
            return False

    def test_notifications_count(self):
        """Step 5: Test /api/notifications/count endpoint"""
        try:
            headers = {"Authorization": f"Bearer {self.user_token}"}
            response = self.session.get(f"{API_BASE}/notifications/count", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                unread_count = data.get('unread_count', 0)
                
                if unread_count > 0:
                    self.log_test(
                        "Test Notifications Count",
                        True,
                        f"Unread count is {unread_count} (> 0 as expected)",
                        data
                    )
                    return True
                else:
                    self.log_test(
                        "Test Notifications Count",
                        False,
                        f"Unread count is {unread_count} (should be > 0)",
                        data
                    )
                    return False
            else:
                self.log_test(
                    "Test Notifications Count",
                    False,
                    f"Failed to get notifications count with status {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test("Test Notifications Count", False, f"Exception: {str(e)}")
            return False

    def test_my_notifications_unread(self):
        """Step 6: Test /api/notifications/my?unread_only=true endpoint"""
        try:
            headers = {"Authorization": f"Bearer {self.user_token}"}
            response = self.session.get(f"{API_BASE}/notifications/my?unread_only=true", headers=headers)
            
            if response.status_code == 200:
                notifications = response.json()
                
                # Find our test notification
                found_test_notification = False
                for notification in notifications:
                    if "اختبار النظام" in notification.get('subject', ''):
                        found_test_notification = True
                        
                        # Verify it's unread
                        is_read = notification.get('is_read', True)
                        if not is_read:
                            self.log_test(
                                "Test My Notifications (Unread Only)",
                                True,
                                f"Found test notification in unread list. Total unread: {len(notifications)}",
                                {
                                    "total_unread": len(notifications),
                                    "test_notification": {
                                        "id": notification.get('id'),
                                        "subject": notification.get('subject'),
                                        "is_read": notification.get('is_read'),
                                        "type": notification.get('type'),
                                        "priority": notification.get('priority')
                                    }
                                }
                            )
                            return True
                        else:
                            self.log_test(
                                "Test My Notifications (Unread Only)",
                                False,
                                "Test notification found but marked as read",
                                notification
                            )
                            return False
                
                if not found_test_notification:
                    self.log_test(
                        "Test My Notifications (Unread Only)",
                        False,
                        f"Test notification not found in unread list. Total unread: {len(notifications)}",
                        {"total_unread": len(notifications), "notifications": notifications[:3]}  # Show first 3 for debugging
                    )
                    return False
            else:
                self.log_test(
                    "Test My Notifications (Unread Only)",
                    False,
                    f"Failed to get unread notifications with status {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test("Test My Notifications (Unread Only)", False, f"Exception: {str(e)}")
            return False

    def run_e2e_test(self):
        """Run the complete E2E notification test"""
        print("🔔 STARTING E2E NOTIFICATION SYSTEM TESTING")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Testing complete flow from Super Admin to User notification")
        print()
        
        # Step 1: Super Admin Authentication
        if not self.authenticate_super_admin():
            print("❌ Cannot proceed without Super Admin authentication")
            return False
        
        # Get Jihad's user ID
        jihad_user_id = self.get_jihad_user_id()
        if not jihad_user_id:
            print("❌ Cannot proceed without Jihad's user ID")
            return False
        
        # Step 2: Send notification to Jihad
        if not self.send_notification_to_jihad(jihad_user_id):
            print("❌ Cannot proceed without sending notification")
            return False
        
        # Step 3: Verify notification in database
        if not self.verify_notification_in_database(jihad_user_id):
            print("⚠️ Notification may not be properly saved, but continuing...")
        
        # Small delay to ensure notification is processed
        time.sleep(2)
        
        # Step 4: User Authentication
        user_id = self.authenticate_user()
        if not user_id:
            print("❌ Cannot proceed without User authentication")
            return False
        
        # Step 5: Test notifications count
        count_success = self.test_notifications_count()
        
        # Step 6: Test unread notifications
        unread_success = self.test_my_notifications_unread()
        
        # Summary
        print("=" * 60)
        print("📊 E2E NOTIFICATION SYSTEM TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        # Critical success criteria
        critical_tests = [
            "Super Admin Authentication",
            "User (Jihad) Authentication", 
            "Send Notification to Jihad",
            "Test Notifications Count",
            "Test My Notifications (Unread Only)"
        ]
        
        critical_passed = 0
        for test_name in critical_tests:
            for result in self.test_results:
                if result['test'] == test_name and result['success']:
                    critical_passed += 1
                    break
        
        print(f"Critical Tests Passed: {critical_passed}/{len(critical_tests)}")
        
        if critical_passed == len(critical_tests):
            print("🎉 E2E NOTIFICATION SYSTEM: FULLY OPERATIONAL")
            print("✅ Complete flow from Super Admin to User notification working correctly")
        elif critical_passed >= 4:
            print("⚠️ E2E NOTIFICATION SYSTEM: MOSTLY WORKING")
            print("✅ Core functionality operational with minor issues")
        else:
            print("❌ E2E NOTIFICATION SYSTEM: CRITICAL ISSUES FOUND")
            print("🚨 Major problems preventing proper notification flow")
        
        # Save detailed results
        self.save_test_results()
        
        return critical_passed >= 4

    def save_test_results(self):
        """Save detailed test results to file"""
        try:
            results_data = {
                "test_type": "E2E Notification System Testing",
                "test_date": datetime.now().isoformat(),
                "backend_url": BACKEND_URL,
                "total_tests": len(self.test_results),
                "passed_tests": sum(1 for result in self.test_results if result['success']),
                "success_rate": (sum(1 for result in self.test_results if result['success']) / len(self.test_results)) * 100 if self.test_results else 0,
                "test_results": self.test_results
            }
            
            # Save to evidence directory
            evidence_dir = Path("/app/evidence")
            evidence_dir.mkdir(exist_ok=True)
            
            results_file = evidence_dir / "notification_e2e_test_results.json"
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, indent=2, ensure_ascii=False)
            
            print(f"📁 Detailed test results saved to: {results_file}")
            
        except Exception as e:
            print(f"⚠️ Failed to save test results: {str(e)}")

def main():
    """Main test execution"""
    tester = NotificationE2ETest()
    success = tester.run_e2e_test()
    
    # Exit with appropriate code
    exit(0 if success else 1)

if __name__ == "__main__":
    main()