#!/usr/bin/env python3
"""
🔔 NOTIFICATION ENDPOINTS FOCUSED TESTING
Arabic Review Request: اختبار سريع لـ endpoint الإشعارات بعد الإصلاح

Focus: Test ONLY these 2 endpoints:
1. GET /api/notifications/my?unread_only=true
2. POST /api/notifications/{id}/acknowledge

User: jihad@tanseeq.com / jihad123
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://hrapp-tanseeq-replaced-1761028017.emergent.host"
BASE_URL = f"{BACKEND_URL}/api"

# Test credentials
TEST_USER = {
    "email": "jihad@tanseeq.com",
    "password": "jihad123"
}

class NotificationEndpointsTest:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.user_token = None
        self.test_results = []
        
    def log_result(self, test_name, success, details, status_code=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "status_code": status_code,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if status_code:
            print(f"    Status: {status_code}")
        print(f"    Details: {details}")
        print()
        
    def authenticate_user(self):
        """Authenticate user and get token"""
        try:
            print("🔐 Authenticating user...")
            response = self.session.post(
                f"{BASE_URL}/auth/login",
                json=TEST_USER,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.user_token = data.get("access_token")
                self.session.headers.update({
                    'Authorization': f'Bearer {self.user_token}'
                })
                
                user_info = data.get("user", {})
                self.log_result(
                    "User Authentication",
                    True,
                    f"Successfully authenticated {user_info.get('name', 'User')} ({user_info.get('email', '')})",
                    200
                )
                return True
            else:
                self.log_result(
                    "User Authentication",
                    False,
                    f"Authentication failed: {response.text}",
                    response.status_code
                )
                return False
                
        except Exception as e:
            self.log_result(
                "User Authentication",
                False,
                f"Authentication error: {str(e)}"
            )
            return False
    
    def test_notifications_my_unread_only(self):
        """Test GET /api/notifications/my?unread_only=true"""
        try:
            print("🔔 Testing GET /api/notifications/my?unread_only=true...")
            
            response = self.session.get(
                f"{BASE_URL}/notifications/my?unread_only=true",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                notifications = data if isinstance(data, list) else data.get("notifications", [])
                
                self.log_result(
                    "GET /notifications/my?unread_only=true",
                    True,
                    f"Successfully retrieved {len(notifications)} unread notifications",
                    200
                )
                
                # Return first notification ID for acknowledge test
                if notifications and len(notifications) > 0:
                    return notifications[0].get("id")
                else:
                    print("    ℹ️  No unread notifications found")
                    return None
                    
            elif response.status_code == 500:
                self.log_result(
                    "GET /notifications/my?unread_only=true",
                    False,
                    f"500 Internal Server Error (the issue we're testing for): {response.text}",
                    500
                )
                return None
            else:
                self.log_result(
                    "GET /notifications/my?unread_only=true",
                    False,
                    f"Unexpected status code: {response.text}",
                    response.status_code
                )
                return None
                
        except Exception as e:
            self.log_result(
                "GET /notifications/my?unread_only=true",
                False,
                f"Request error: {str(e)}"
            )
            return None
    
    def test_notification_acknowledge(self, notification_id):
        """Test POST /api/notifications/{id}/acknowledge"""
        if not notification_id:
            # Try to get any notification first
            try:
                response = self.session.get(f"{BASE_URL}/notifications/my", timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    notifications = data if isinstance(data, list) else data.get("notifications", [])
                    if notifications and len(notifications) > 0:
                        notification_id = notifications[0].get("id")
                    else:
                        self.log_result(
                            "POST /notifications/{id}/acknowledge",
                            False,
                            "No notifications available to test acknowledge endpoint"
                        )
                        return
                else:
                    self.log_result(
                        "POST /notifications/{id}/acknowledge",
                        False,
                        "Could not retrieve notifications to test acknowledge endpoint"
                    )
                    return
            except Exception as e:
                self.log_result(
                    "POST /notifications/{id}/acknowledge",
                    False,
                    f"Error retrieving notifications for acknowledge test: {str(e)}"
                )
                return
        
        try:
            print(f"✅ Testing POST /api/notifications/{notification_id}/acknowledge...")
            
            response = self.session.post(
                f"{BASE_URL}/notifications/{notification_id}/acknowledge",
                json={},  # Empty body or any required data
                timeout=30
            )
            
            if response.status_code in [200, 204]:
                self.log_result(
                    "POST /notifications/{id}/acknowledge",
                    True,
                    f"Successfully acknowledged notification {notification_id}",
                    response.status_code
                )
            elif response.status_code == 404:
                self.log_result(
                    "POST /notifications/{id}/acknowledge",
                    False,
                    f"Notification not found (404): {response.text}",
                    404
                )
            elif response.status_code == 500:
                self.log_result(
                    "POST /notifications/{id}/acknowledge",
                    False,
                    f"500 Internal Server Error: {response.text}",
                    500
                )
            else:
                self.log_result(
                    "POST /notifications/{id}/acknowledge",
                    False,
                    f"Unexpected status code: {response.text}",
                    response.status_code
                )
                
        except Exception as e:
            self.log_result(
                "POST /notifications/{id}/acknowledge",
                False,
                f"Request error: {str(e)}"
            )
    
    def run_tests(self):
        """Run all notification endpoint tests"""
        print("🚀 Starting Notification Endpoints Testing")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test User: {TEST_USER['email']}")
        print("=" * 60)
        print()
        
        # Step 1: Authenticate
        if not self.authenticate_user():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Step 2: Test GET /notifications/my?unread_only=true
        notification_id = self.test_notifications_my_unread_only()
        
        # Step 3: Test POST /notifications/{id}/acknowledge
        self.test_notification_acknowledge(notification_id)
        
        # Summary
        print("=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        # Detailed results
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
            if result.get("status_code"):
                print(f"    Status: {result['status_code']}")
            print(f"    {result['details']}")
            print()
        
        # Save results
        try:
            with open("/app/notification_endpoints_test_results.json", "w", encoding="utf-8") as f:
                json.dump({
                    "test_summary": {
                        "total_tests": total_tests,
                        "passed_tests": passed_tests,
                        "failed_tests": failed_tests,
                        "success_rate": f"{(passed_tests/total_tests)*100:.1f}%"
                    },
                    "test_results": self.test_results,
                    "backend_url": BACKEND_URL,
                    "test_user": TEST_USER["email"],
                    "timestamp": datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
            print("📁 Results saved to notification_endpoints_test_results.json")
        except Exception as e:
            print(f"⚠️  Could not save results: {e}")
        
        return failed_tests == 0

def main():
    """Main function"""
    tester = NotificationEndpointsTest()
    success = tester.run_tests()
    
    if success:
        print("🎉 All notification endpoint tests passed!")
        sys.exit(0)
    else:
        print("❌ Some notification endpoint tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()