#!/usr/bin/env python3
"""
🔔 NOTIFICATIONS FIX TESTING - Arabic Review Request
اختبار سريع للإشعارات بعد الإصلاح

Focus: Test ONLY the two specific endpoints mentioned in Arabic review:
1. /api/notifications/count - should return unread_count
2. /api/notifications/my?unread_only=true - should work without errors

User: jihad@tanseeq.com / jihad123
"""

import requests
import json
import os
from datetime import datetime

# Configuration
BACKEND_URL = "https://payroll-management-4.preview.emergentagent.com/api"
TEST_USER_EMAIL = "jihad@tanseeq.com"
TEST_USER_PASSWORD = "jihad123"

class NotificationsFixTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.user_info = None
        self.test_results = []
        
    def log_test(self, test_name, status, details, response_data=None):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {details}")
        
        if response_data and status == "FAIL":
            print(f"   Response: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
    
    def authenticate(self):
        """Authenticate user"""
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.user_info = data["user"]
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                
                self.log_test(
                    "User Authentication", 
                    "PASS", 
                    f"Successfully authenticated {TEST_USER_EMAIL}",
                    {"user_id": self.user_info["id"], "role": self.user_info["role"]}
                )
                return True
            else:
                self.log_test(
                    "User Authentication", 
                    "FAIL", 
                    f"Authentication failed: {response.status_code}",
                    response.json() if response.content else None
                )
                return False
                
        except Exception as e:
            self.log_test("User Authentication", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_notifications_count(self):
        """Test /api/notifications/count endpoint"""
        try:
            response = self.session.get(f"{BACKEND_URL}/notifications/count")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if response has unread_count field
                if "unread_count" in data:
                    unread_count = data["unread_count"]
                    self.log_test(
                        "Notifications Count Endpoint", 
                        "PASS", 
                        f"Successfully retrieved unread_count: {unread_count}",
                        data
                    )
                    return True
                else:
                    self.log_test(
                        "Notifications Count Endpoint", 
                        "FAIL", 
                        "Response missing 'unread_count' field",
                        data
                    )
                    return False
            else:
                self.log_test(
                    "Notifications Count Endpoint", 
                    "FAIL", 
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code, "response": response.text}
                )
                return False
                
        except Exception as e:
            self.log_test("Notifications Count Endpoint", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_notifications_my_unread_only(self):
        """Test /api/notifications/my?unread_only=true endpoint"""
        try:
            response = self.session.get(f"{BACKEND_URL}/notifications/my?unread_only=true")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if response is valid JSON and has expected structure
                if isinstance(data, dict):
                    notifications = data.get("notifications", []) if "notifications" in data else data
                    
                    self.log_test(
                        "Notifications My Unread Only", 
                        "PASS", 
                        f"Successfully retrieved unread notifications: {len(notifications) if isinstance(notifications, list) else 'N/A'} items",
                        {"count": len(notifications) if isinstance(notifications, list) else "N/A", "structure": type(data).__name__}
                    )
                    return True
                else:
                    self.log_test(
                        "Notifications My Unread Only", 
                        "FAIL", 
                        f"Unexpected response structure: {type(data).__name__}",
                        data
                    )
                    return False
            else:
                self.log_test(
                    "Notifications My Unread Only", 
                    "FAIL", 
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code, "response": response.text}
                )
                return False
                
        except Exception as e:
            self.log_test("Notifications My Unread Only", "FAIL", f"Exception: {str(e)}")
            return False
    
    def run_tests(self):
        """Run all notification tests"""
        print("🔔 NOTIFICATIONS FIX TESTING - Arabic Review Request")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test User: {TEST_USER_EMAIL}")
        print("=" * 60)
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with tests")
            return False
        
        # Step 2: Test notifications/count endpoint
        count_result = self.test_notifications_count()
        
        # Step 3: Test notifications/my?unread_only=true endpoint
        unread_result = self.test_notifications_my_unread_only()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed_tests = sum(1 for result in self.test_results if result["status"] == "PASS")
        total_tests = len(self.test_results)
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Specific results for the two requested endpoints
        print("\n🎯 SPECIFIC ENDPOINT RESULTS:")
        print(f"✅ /api/notifications/count: {'WORKING' if count_result else 'FAILED'}")
        print(f"✅ /api/notifications/my?unread_only=true: {'WORKING' if unread_result else 'FAILED'}")
        
        # Overall assessment
        if count_result and unread_result:
            print("\n🎉 CONCLUSION: Both requested notification endpoints are working correctly after the fix!")
            return True
        else:
            print("\n🚨 CONCLUSION: One or both notification endpoints still have issues.")
            return False
    
    def save_results(self):
        """Save test results to file"""
        results_file = "/app/evidence/notifications_fix_test_results.json"
        os.makedirs("/app/evidence", exist_ok=True)
        
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump({
                "test_summary": {
                    "backend_url": BACKEND_URL,
                    "test_user": TEST_USER_EMAIL,
                    "timestamp": datetime.now().isoformat(),
                    "total_tests": len(self.test_results),
                    "passed_tests": sum(1 for r in self.test_results if r["status"] == "PASS"),
                    "success_rate": f"{(sum(1 for r in self.test_results if r['status'] == 'PASS') / len(self.test_results) * 100):.1f}%" if self.test_results else "0%"
                },
                "test_results": self.test_results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Test results saved to: {results_file}")

def main():
    """Main test execution"""
    tester = NotificationsFixTester()
    
    try:
        success = tester.run_tests()
        tester.save_results()
        
        # Exit with appropriate code
        exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        tester.save_results()
        exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        tester.save_results()
        exit(1)

if __name__ == "__main__":
    main()