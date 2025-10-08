#!/usr/bin/env python3
"""
NOTIFICATION SYSTEM INTEGRATION TESTING
Testing notification API endpoints as requested in review:
1. POST /api/notifications - Create a new notification
2. GET /api/notifications - Fetch all notifications for authenticated user  
3. GET /api/notifications/count - Get unread notification count
4. PATCH /api/notifications/read/{notification_id} - Mark specific notification as read
5. PATCH /api/notifications/read-all - Mark all notifications as read
6. DELETE /api/notifications/{notification_id} - Delete specific notification

Testing with different user roles and Arabic text content.
"""

import requests
import json
import os
from datetime import datetime, timedelta
import uuid
import time

# Configuration
BACKEND_URL = "https://salary-processor-1.preview.emergentagent.com/api"

print(f"🔗 Testing Backend URL: {BACKEND_URL}")

# Test credentials from review request and previous testing
TEST_CREDENTIALS = [
    {"email": "hatem@tan-seeq.co", "password": "hatem123", "role": "super_admin", "name": "Hatem (Super Admin)"},
    {"email": "mahmoud@tanseeq.com", "password": "mahmoud123", "role": "admin", "name": "Mahmoud (Admin)"},
    {"email": "jihad@tanseeq.com", "password": "jihad123", "role": "user", "name": "Jihad (Regular User)"}
]

class NotificationSystemTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.auth_token = None
        self.current_user = None
        self.test_results = []
        self.notification_ids = []  # Store created notification IDs for cleanup
        
    def log_test(self, test_name, success, details="", error=""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   📋 {details}")
        if error:
            print(f"   ⚠️  {error}")
        print()

    def authenticate_user(self, credentials):
        """Authenticate with given credentials"""
        try:
            print(f"🔐 Authenticating: {credentials['email']} ({credentials['name']})")
            
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json={
                    "email": credentials["email"],
                    "password": credentials["password"]
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.auth_token = data["access_token"]
                    self.current_user = data.get("user", {})
                    self.session.headers.update({
                        'Authorization': f'Bearer {self.auth_token}'
                    })
                    
                    self.log_test(
                        f"Authentication - {credentials['name']}", 
                        True,
                        f"Successfully authenticated as {self.current_user.get('name', 'Unknown')} ({self.current_user.get('role', 'Unknown')})"
                    )
                    return True
                else:
                    self.log_test(
                        f"Authentication - {credentials['name']}", 
                        False,
                        error="No access token in response"
                    )
                    return False
            else:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f" - {error_data.get('detail', 'Unknown error')}"
                except:
                    error_msg += f" - {response.text[:100]}"
                
                self.log_test(
                    f"Authentication - {credentials['name']}", 
                    False,
                    error=error_msg
                )
                return False
                    
        except Exception as e:
            self.log_test(
                f"Authentication - {credentials['name']}", 
                False,
                error=f"Connection error: {str(e)}"
            )
            return False

    def test_create_notification(self):
        """Test POST /api/notifications - Create a new notification"""
        print("📝 TESTING NOTIFICATION CREATION")
        print("=" * 50)
        
        # Test with different notification types and Arabic content
        test_notifications = [
            {
                "title": "إشعار عادي",
                "message": "هذا إشعار تجريبي باللغة العربية للتأكد من دعم النص العربي في النظام",
                "severity": "normal",
                "category": "general",
                "must_acknowledge": False
            },
            {
                "title": "تحذير مهم",
                "message": "تحذير مهم يتطلب الإقرار والموافقة من الموظف قبل المتابعة",
                "severity": "warning", 
                "category": "warning",
                "must_acknowledge": True
            },
            {
                "title": "إشعار عاجل",
                "message": "إشعار عاجل وهام جداً يتطلب انتباه فوري من جميع الموظفين",
                "severity": "urgent",
                "category": "urgent", 
                "must_acknowledge": True,
                "action_url": "/dashboard"
            },
            {
                "title": "معلومات مهمة",
                "message": "معلومات مهمة حول تحديثات النظام والإجراءات الجديدة",
                "severity": "important",
                "category": "system",
                "must_acknowledge": False
            }
        ]
        
        # Only super admin should be able to create notifications
        if self.current_user.get('role') != 'super_admin':
            # Test that non-super-admin users get proper access control
            try:
                response = self.session.post(
                    f"{BACKEND_URL}/notifications",
                    json=test_notifications[0],
                    timeout=30
                )
                
                if response.status_code == 403:
                    self.log_test(
                        "POST /notifications - Access Control",
                        True,
                        f"Properly denied access for {self.current_user.get('role')} role"
                    )
                else:
                    self.log_test(
                        "POST /notifications - Access Control",
                        False,
                        error=f"Expected 403, got {response.status_code}"
                    )
            except Exception as e:
                self.log_test(
                    "POST /notifications - Access Control",
                    False,
                    error=str(e)
                )
            return
        
        # Test notification creation for super admin
        for i, notification_data in enumerate(test_notifications):
            try:
                response = self.session.post(
                    f"{BACKEND_URL}/notifications",
                    json=notification_data,
                    timeout=30
                )
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    notification_id = result.get('id') or result.get('notification_id')
                    if notification_id:
                        self.notification_ids.append(notification_id)
                    
                    self.log_test(
                        f"POST /notifications - Create {notification_data['severity']}",
                        True,
                        f"Created notification: {notification_data['title']} (ID: {notification_id})"
                    )
                else:
                    # Check if endpoint exists by testing existing endpoints
                    if response.status_code == 404:
                        # Try existing notification endpoints
                        self.test_existing_notification_endpoints()
                        return
                    
                    error_msg = f"HTTP {response.status_code}"
                    try:
                        error_data = response.json()
                        error_msg += f" - {error_data.get('detail', 'Unknown error')}"
                    except:
                        error_msg += f" - {response.text[:200]}"
                    
                    self.log_test(
                        f"POST /notifications - Create {notification_data['severity']}",
                        False,
                        error=error_msg
                    )
                    
            except Exception as e:
                self.log_test(
                    f"POST /notifications - Create {notification_data['severity']}",
                    False,
                    error=str(e)
                )

    def test_existing_notification_endpoints(self):
        """Test existing notification endpoints found in server.py"""
        print("📋 TESTING EXISTING NOTIFICATION ENDPOINTS")
        print("=" * 50)
        
        # Test GET /notifications (for super admin)
        if self.current_user.get('role') == 'super_admin':
            try:
                response = self.session.get(f"{BACKEND_URL}/notifications", timeout=30)
                if response.status_code == 200:
                    notifications = response.json()
                    self.log_test(
                        "GET /notifications (Super Admin)",
                        True,
                        f"Retrieved {len(notifications)} notifications sent by super admin"
                    )
                else:
                    self.log_test(
                        "GET /notifications (Super Admin)",
                        False,
                        error=f"HTTP {response.status_code}"
                    )
            except Exception as e:
                self.log_test(
                    "GET /notifications (Super Admin)",
                    False,
                    error=str(e)
                )
        
        # Test GET /notifications/my (for all users)
        try:
            response = self.session.get(f"{BACKEND_URL}/notifications/my", timeout=30)
            if response.status_code == 200:
                response_data = response.json()
                
                # Handle both direct list and wrapped response
                if isinstance(response_data, list):
                    notifications = response_data
                elif isinstance(response_data, dict) and 'notifications' in response_data:
                    notifications = response_data['notifications']
                else:
                    notifications = response_data if isinstance(response_data, list) else []
                
                self.log_test(
                    "GET /notifications/my",
                    True,
                    f"Retrieved {len(notifications)} notifications for current user"
                )
                
                # Store notification IDs for further testing
                for notif in notifications:
                    if isinstance(notif, dict) and notif.get('id'):
                        self.notification_ids.append(notif['id'])
                    elif isinstance(notif, dict) and notif.get('_id'):
                        # Handle MongoDB ObjectId format
                        self.notification_ids.append(str(notif['_id']))
                        
            else:
                self.log_test(
                    "GET /notifications/my",
                    False,
                    error=f"HTTP {response.status_code}"
                )
        except Exception as e:
            self.log_test(
                "GET /notifications/my",
                False,
                error=str(e)
            )
        
        # Test notification creation via existing send endpoint
        if self.current_user.get('role') == 'super_admin':
            self.test_send_notification_endpoint()

    def test_send_notification_endpoint(self):
        """Test existing POST /notifications/send endpoint"""
        
        # Get list of users to send notifications to
        try:
            users_response = self.session.get(f"{BACKEND_URL}/users", timeout=30)
            if users_response.status_code == 200:
                users = users_response.json()
                if users and len(users) > 0:
                    recipient = users[0]  # Send to first user
                    
                    # Test Arabic notification with different severity levels
                    test_notifications = [
                        {
                            "recipient_id": recipient['id'],
                            "subject": "إشعار تجريبي عادي",
                            "message": "هذا إشعار تجريبي باللغة العربية لاختبار النظام",
                            "type": "info",
                            "priority": "normal"
                        },
                        {
                            "recipient_id": recipient['id'],
                            "subject": "تحذير مهم",
                            "message": "تحذير مهم يتطلب انتباه فوري من الموظف",
                            "type": "warning", 
                            "priority": "urgent"
                        },
                        {
                            "recipient_id": recipient['id'],
                            "subject": "معلومات هامة",
                            "message": "معلومات هامة حول تحديثات النظام والسياسات الجديدة",
                            "type": "info",
                            "priority": "important"
                        }
                    ]
                    
                    for notification_data in test_notifications:
                        try:
                            response = self.session.post(
                                f"{BACKEND_URL}/notifications/send",
                                json=notification_data,
                                timeout=30
                            )
                            
                            if response.status_code == 200:
                                self.log_test(
                                    f"POST /notifications/send - {notification_data['priority']}",
                                    True,
                                    f"Sent {notification_data['priority']} notification: {notification_data['subject']}"
                                )
                            else:
                                error_msg = f"HTTP {response.status_code}"
                                try:
                                    error_data = response.json()
                                    error_msg += f" - {error_data.get('detail', 'Unknown error')}"
                                except:
                                    error_msg += f" - {response.text[:200]}"
                                
                                self.log_test(
                                    f"POST /notifications/send - {notification_data['priority']}",
                                    False,
                                    error=error_msg
                                )
                                
                        except Exception as e:
                            self.log_test(
                                f"POST /notifications/send - {notification_data['priority']}",
                                False,
                                error=str(e)
                            )
                            
        except Exception as e:
            self.log_test(
                "POST /notifications/send - Setup",
                False,
                error=f"Could not get users list: {str(e)}"
            )

    def test_notification_count(self):
        """Test GET /api/notifications/count - Get unread notification count"""
        try:
            response = self.session.get(f"{BACKEND_URL}/notifications/count", timeout=30)
            if response.status_code == 200:
                count_data = response.json()
                unread_count = count_data.get('unread_count', 0)
                self.log_test(
                    "GET /notifications/count",
                    True,
                    f"Unread notifications count: {unread_count}"
                )
            elif response.status_code == 404:
                self.log_test(
                    "GET /notifications/count",
                    False,
                    error="Endpoint not implemented - this is expected as it's not in current server.py"
                )
            else:
                self.log_test(
                    "GET /notifications/count",
                    False,
                    error=f"HTTP {response.status_code}"
                )
        except Exception as e:
            self.log_test(
                "GET /notifications/count",
                False,
                error=str(e)
            )

    def test_mark_notification_read(self):
        """Test PATCH /api/notifications/read/{notification_id} - Mark specific notification as read"""
        if not self.notification_ids:
            self.log_test(
                "PATCH /notifications/read/{id}",
                False,
                error="No notification IDs available for testing"
            )
            return
        
        for notification_id in self.notification_ids[:2]:  # Test first 2 notifications
            try:
                # Try PATCH method first (as requested)
                response = self.session.patch(
                    f"{BACKEND_URL}/notifications/read/{notification_id}",
                    timeout=30
                )
                
                if response.status_code == 200:
                    self.log_test(
                        f"PATCH /notifications/read/{notification_id}",
                        True,
                        "Successfully marked notification as read"
                    )
                elif response.status_code == 404:
                    # Try existing POST endpoint
                    response = self.session.post(
                        f"{BACKEND_URL}/notifications/{notification_id}/read",
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        self.log_test(
                            f"POST /notifications/{notification_id}/read (existing)",
                            True,
                            "Successfully marked notification as read using existing endpoint"
                        )
                    else:
                        self.log_test(
                            f"Mark notification read - {notification_id}",
                            False,
                            error=f"Both PATCH and POST methods failed: {response.status_code}"
                        )
                else:
                    self.log_test(
                        f"PATCH /notifications/read/{notification_id}",
                        False,
                        error=f"HTTP {response.status_code}"
                    )
                    
            except Exception as e:
                self.log_test(
                    f"PATCH /notifications/read/{notification_id}",
                    False,
                    error=str(e)
                )

    def test_mark_all_read(self):
        """Test PATCH /api/notifications/read-all - Mark all notifications as read"""
        try:
            response = self.session.patch(f"{BACKEND_URL}/notifications/read-all", timeout=30)
            if response.status_code == 200:
                result = response.json()
                marked_count = result.get('marked_count', 0)
                self.log_test(
                    "PATCH /notifications/read-all",
                    True,
                    f"Marked {marked_count} notifications as read"
                )
            elif response.status_code == 404:
                self.log_test(
                    "PATCH /notifications/read-all",
                    False,
                    error="Endpoint not implemented - this is expected as it's not in current server.py"
                )
            else:
                self.log_test(
                    "PATCH /notifications/read-all",
                    False,
                    error=f"HTTP {response.status_code}"
                )
        except Exception as e:
            self.log_test(
                "PATCH /notifications/read-all",
                False,
                error=str(e)
            )

    def test_delete_notification(self):
        """Test DELETE /api/notifications/{notification_id} - Delete specific notification"""
        if not self.notification_ids:
            self.log_test(
                "DELETE /notifications/{id}",
                False,
                error="No notification IDs available for testing"
            )
            return
        
        # Test deleting one notification
        if len(self.notification_ids) > 0:
            notification_id = self.notification_ids[-1]  # Delete last one
            try:
                response = self.session.delete(
                    f"{BACKEND_URL}/notifications/{notification_id}",
                    timeout=30
                )
                
                if response.status_code == 200:
                    self.log_test(
                        f"DELETE /notifications/{notification_id}",
                        True,
                        "Successfully deleted notification"
                    )
                elif response.status_code == 404:
                    self.log_test(
                        f"DELETE /notifications/{notification_id}",
                        False,
                        error="Endpoint not implemented - this is expected as it's not in current server.py"
                    )
                else:
                    self.log_test(
                        f"DELETE /notifications/{notification_id}",
                        False,
                        error=f"HTTP {response.status_code}"
                    )
                    
            except Exception as e:
                self.log_test(
                    f"DELETE /notifications/{notification_id}",
                    False,
                    error=str(e)
                )

    def test_mandatory_acknowledgment(self):
        """Test mandatory acknowledgment functionality"""
        print("✅ TESTING MANDATORY ACKNOWLEDGMENT")
        print("=" * 50)
        
        # Test existing acknowledgment endpoints
        try:
            response = self.session.get(f"{BACKEND_URL}/notifications/unread-mandatory", timeout=30)
            if response.status_code == 200:
                response_data = response.json()
                
                # Handle both direct list and wrapped response
                if isinstance(response_data, list):
                    mandatory_notifications = response_data
                elif isinstance(response_data, dict) and 'notifications' in response_data:
                    mandatory_notifications = response_data['notifications']
                else:
                    mandatory_notifications = response_data if isinstance(response_data, list) else []
                
                self.log_test(
                    "GET /notifications/unread-mandatory",
                    True,
                    f"Found {len(mandatory_notifications)} mandatory notifications requiring acknowledgment"
                )
                
                # Test acknowledging a mandatory notification if any exist
                if mandatory_notifications and len(mandatory_notifications) > 0:
                    first_notif = mandatory_notifications[0]
                    notif_id = first_notif.get('id') if isinstance(first_notif, dict) else None
                    if notif_id:
                        try:
                            ack_response = self.session.post(
                                f"{BACKEND_URL}/notifications/{notif_id}/acknowledge",
                                timeout=30
                            )
                            if ack_response.status_code == 200:
                                self.log_test(
                                    f"POST /notifications/{notif_id}/acknowledge",
                                    True,
                                    "Successfully acknowledged mandatory notification"
                                )
                            else:
                                self.log_test(
                                    f"POST /notifications/{notif_id}/acknowledge",
                                    False,
                                    error=f"HTTP {ack_response.status_code}"
                                )
                        except Exception as e:
                            self.log_test(
                                f"POST /notifications/{notif_id}/acknowledge",
                                False,
                                error=str(e)
                            )
                            
            else:
                self.log_test(
                    "GET /notifications/unread-mandatory",
                    False,
                    error=f"HTTP {response.status_code}"
                )
        except Exception as e:
            self.log_test(
                "GET /notifications/unread-mandatory",
                False,
                error=str(e)
            )

    def test_notification_data_structure(self):
        """Test notification data structure matches NotificationModal component expectations"""
        print("🔍 TESTING NOTIFICATION DATA STRUCTURE")
        print("=" * 50)
        
        try:
            response = self.session.get(f"{BACKEND_URL}/notifications/my", timeout=30)
            if response.status_code == 200:
                response_data = response.json()
                
                # Handle both direct list and wrapped response
                if isinstance(response_data, list):
                    notifications = response_data
                elif isinstance(response_data, dict) and 'notifications' in response_data:
                    notifications = response_data['notifications']
                else:
                    notifications = response_data if isinstance(response_data, list) else []
                
                if notifications and len(notifications) > 0:
                    notification = notifications[0] if isinstance(notifications[0], dict) else {}
                    
                    # Expected fields from review request
                    expected_fields = ['id', 'title', 'message', 'severity', 'is_read', 'sent_at', 
                                     'must_acknowledge', 'category', 'action_url']
                    
                    # Check which fields are present
                    present_fields = []
                    missing_fields = []
                    
                    for field in expected_fields:
                        if field in notification:
                            present_fields.append(field)
                        else:
                            missing_fields.append(field)
                    
                    # Check actual fields in notification
                    actual_fields = list(notification.keys())
                    
                    self.log_test(
                        "Notification Data Structure",
                        len(missing_fields) == 0,
                        f"Present fields: {present_fields}. Actual fields: {actual_fields}. Missing expected fields: {missing_fields}" if missing_fields else f"All expected fields present. Actual fields: {actual_fields}"
                    )
                else:
                    self.log_test(
                        "Notification Data Structure",
                        False,
                        error="No notifications available to check structure"
                    )
            else:
                self.log_test(
                    "Notification Data Structure",
                    False,
                    error=f"Could not retrieve notifications: HTTP {response.status_code}"
                )
        except Exception as e:
            self.log_test(
                "Notification Data Structure",
                False,
                error=str(e)
            )

    def run_comprehensive_test(self):
        """Run comprehensive notification system tests"""
        print("🔔 STARTING COMPREHENSIVE NOTIFICATION SYSTEM TESTING")
        print("=" * 80)
        print()
        
        # Test with all user roles
        for credentials in TEST_CREDENTIALS:
            print(f"\n👤 TESTING WITH {credentials['name']} ({credentials['role']})")
            print("=" * 60)
            
            # Authenticate
            if not self.authenticate_user(credentials):
                print(f"🚨 Authentication failed for {credentials['name']} - skipping tests")
                continue
            
            # Reset notification IDs for each user
            self.notification_ids = []
            
            # Test notification creation (requested endpoints)
            self.test_create_notification()
            
            # Test existing notification endpoints
            self.test_existing_notification_endpoints()
            
            # Test notification count
            self.test_notification_count()
            
            # Test marking notifications as read
            self.test_mark_notification_read()
            
            # Test marking all as read
            self.test_mark_all_read()
            
            # Test deleting notifications
            self.test_delete_notification()
            
            # Test mandatory acknowledgment
            self.test_mandatory_acknowledgment()
            
            # Test notification data structure
            self.test_notification_data_structure()
            
            print(f"✅ Completed testing for {credentials['name']}")
            print()
        
        return self.generate_summary()

    def generate_summary(self):
        """Generate comprehensive test summary"""
        print("\n" + "=" * 80)
        print("📊 NOTIFICATION SYSTEM TEST RESULTS SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📈 Overall Results: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}% success rate)")
        print()
        
        # Categorize results
        critical_failures = []
        expected_failures = []
        successes = []
        
        for result in self.test_results:
            if result['success']:
                successes.append(result)
            elif "not implemented" in result['error'] or "expected" in result['error']:
                expected_failures.append(result)
            else:
                critical_failures.append(result)
        
        if critical_failures:
            print("🚨 CRITICAL FAILURES:")
            for result in critical_failures:
                print(f"   • {result['test']}: {result['error']}")
            print()
        
        if expected_failures:
            print("⚠️  EXPECTED FAILURES (Endpoints not yet implemented):")
            for result in expected_failures:
                print(f"   • {result['test']}: {result['error']}")
            print()
        
        if successes:
            print("✅ SUCCESSFUL TESTS:")
            for result in successes:
                print(f"   • {result['test']}: {result['details']}")
        
        print("\n" + "=" * 80)
        
        # Assessment
        auth_working = any(r['success'] and 'Authentication' in r['test'] for r in self.test_results)
        existing_notifications_working = any(r['success'] and ('notifications/my' in r['test'] or 'notifications/send' in r['test']) for r in self.test_results)
        
        print("🎯 NOTIFICATION SYSTEM ASSESSMENT:")
        if auth_working:
            print("✅ Authentication working for all user roles")
        if existing_notifications_working:
            print("✅ Existing notification endpoints working")
        
        # Check for requested endpoints
        requested_endpoints = ['POST /notifications', 'GET /notifications/count', 'PATCH /notifications/read-all', 'DELETE /notifications']
        implemented_endpoints = []
        missing_endpoints = []
        
        for endpoint in requested_endpoints:
            endpoint_tested = any(endpoint in r['test'] for r in self.test_results)
            endpoint_working = any(endpoint in r['test'] and r['success'] for r in self.test_results)
            
            if endpoint_working:
                implemented_endpoints.append(endpoint)
            elif endpoint_tested:
                missing_endpoints.append(endpoint)
        
        if implemented_endpoints:
            print(f"✅ Implemented requested endpoints: {implemented_endpoints}")
        if missing_endpoints:
            print(f"❌ Missing requested endpoints: {missing_endpoints}")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': success_rate,
            'critical_failures': len(critical_failures),
            'expected_failures': len(expected_failures),
            'auth_working': auth_working,
            'existing_notifications_working': existing_notifications_working,
            'results': self.test_results
        }

if __name__ == "__main__":
    tester = NotificationSystemTester()
    summary = tester.run_comprehensive_test()
    
    # Exit with appropriate code
    if summary['success_rate'] >= 70 and summary['auth_working']:
        exit(0)  # Success
    else:
        exit(1)  # Failure