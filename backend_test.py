#!/usr/bin/env python3
"""
TANSEEQ HR System Backend API Testing
Tests all backend endpoints with different user roles
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class TanseeqAPITester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.api_url = f"{self.base_url}/api"
        self.tokens = {}
        self.users = {}
        self.tests_run = 0
        self.tests_passed = 0
        
        # Test users (from the review request)
        self.test_users = {
            'super_admin': {'email': 'hatem@tanseeq.com', 'password': 'hatem123'},
            'admin': {'email': 'mahmoud@tanseeq.com', 'password': 'mahmoud123'},
            'user': {'email': 'jihad@tanseeq.com', 'password': 'jihad123'}
        }

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")

    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                    token: Optional[str] = None, expected_status: int = 200) -> tuple:
        """Make HTTP request and return success status and response"""
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                return False, {"error": f"Unsupported method: {method}"}
            
            success = response.status_code == expected_status
            try:
                response_data = response.json()
            except:
                response_data = {"status_code": response.status_code, "text": response.text}
            
            return success, response_data
            
        except requests.exceptions.RequestException as e:
            return False, {"error": str(e)}

    def test_root_endpoint(self):
        """Test root endpoint"""
        try:
            response = requests.get(self.base_url, timeout=10)
            success = response.status_code == 200
            self.log_test("Root endpoint", success, 
                         f"Status: {response.status_code}" if not success else "")
            return success
        except Exception as e:
            self.log_test("Root endpoint", False, str(e))
            return False

    def test_login(self, role: str) -> bool:
        """Test login for specific role"""
        user_data = self.test_users[role]
        success, response = self.make_request('POST', 'auth/login', user_data)
        
        if success and 'access_token' in response:
            self.tokens[role] = response['access_token']
            self.users[role] = response['user']
            self.log_test(f"Login as {role}", True)
            return True
        else:
            self.log_test(f"Login as {role}", False, str(response))
            return False

    def test_dashboard_stats(self, role: str) -> bool:
        """Test dashboard stats endpoint"""
        if role not in self.tokens:
            return False
            
        success, response = self.make_request('GET', 'dashboard/stats', 
                                            token=self.tokens[role])
        
        if success:
            # Verify response structure based on role
            if role == 'user':
                expected_keys = ['attendance_today', 'pending_leaves', 'pending_field_exits']
            else:  # admin or super_admin
                expected_keys = ['total_users', 'present_today', 'pending_leaves', 'pending_field_exits']
            
            has_expected_keys = all(key in response for key in expected_keys)
            self.log_test(f"Dashboard stats ({role})", has_expected_keys,
                         f"Missing keys: {set(expected_keys) - set(response.keys())}" if not has_expected_keys else "")
            return has_expected_keys
        else:
            self.log_test(f"Dashboard stats ({role})", False, str(response))
            return False

    def test_attendance_check_in(self, role: str) -> bool:
        """Test attendance check-in"""
        if role not in self.tokens:
            return False
            
        success, response = self.make_request('POST', 'attendance/check-in', 
                                            token=self.tokens[role])
        
        # Check-in might fail if already checked in, so we accept both 200 and 400
        if success or (not success and response.get('detail') == 'Already checked in today'):
            self.log_test(f"Attendance check-in ({role})", True)
            return True
        else:
            self.log_test(f"Attendance check-in ({role})", False, str(response))
            return False

    def test_attendance_records(self, role: str) -> bool:
        """Test getting attendance records"""
        if role not in self.tokens:
            return False
            
        success, response = self.make_request('GET', 'attendance', 
                                            token=self.tokens[role])
        
        if success and isinstance(response, list):
            self.log_test(f"Get attendance records ({role})", True)
            return True
        else:
            self.log_test(f"Get attendance records ({role})", False, str(response))
            return False

    def test_users_endpoint(self, role: str) -> bool:
        """Test users endpoint (admin only)"""
        if role not in self.tokens:
            return False
            
        expected_status = 200 if role in ['admin', 'super_admin'] else 403
        success, response = self.make_request('GET', 'users', 
                                            token=self.tokens[role],
                                            expected_status=expected_status)
        
        if expected_status == 200:
            success = success and isinstance(response, list)
        
        self.log_test(f"Get users ({role})", success, str(response) if not success else "")
        return success

    def test_leaves_endpoint(self, role: str) -> bool:
        """Test leaves endpoint"""
        if role not in self.tokens:
            return False
            
        success, response = self.make_request('GET', 'leaves', 
                                            token=self.tokens[role])
        
        if success and isinstance(response, list):
            self.log_test(f"Get leaves ({role})", True)
            return True
        else:
            self.log_test(f"Get leaves ({role})", False, str(response))
            return False

    def test_field_exits_endpoint(self, role: str) -> bool:
        """Test field exits endpoint"""
        if role not in self.tokens:
            return False
            
        success, response = self.make_request('GET', 'field-exits', 
                                            token=self.tokens[role])
        
        if success and isinstance(response, list):
            self.log_test(f"Get field exits ({role})", True)
            return True
        else:
            self.log_test(f"Get field exits ({role})", False, str(response))
            return False

    def test_activity_logs(self, role: str) -> bool:
        """Test activity logs endpoint (super admin only)"""
        if role not in self.tokens:
            return False
            
        expected_status = 200 if role == 'super_admin' else 403
        success, response = self.make_request('GET', 'activity-logs', 
                                            token=self.tokens[role],
                                            expected_status=expected_status)
        
        if expected_status == 200:
            success = success and isinstance(response, list)
        
        self.log_test(f"Get activity logs ({role})", success, str(response) if not success else "")
        return success

    def test_reports_endpoints(self, role: str) -> bool:
        """Test reports endpoints (admin only)"""
        if role not in self.tokens:
            return False
            
        expected_status = 200 if role in ['admin', 'super_admin'] else 403
        
        # Test attendance report
        success1, response1 = self.make_request('GET', 'reports/attendance', 
                                              token=self.tokens[role],
                                              expected_status=expected_status)
        
        # Test leaves report  
        success2, response2 = self.make_request('GET', 'reports/leaves', 
                                              token=self.tokens[role],
                                              expected_status=expected_status)
        
        # Test payroll report
        success3, response3 = self.make_request('GET', 'reports/payroll', 
                                              token=self.tokens[role],
                                              expected_status=expected_status)
        
        if expected_status == 200:
            success1 = success1 and isinstance(response1, list)
            success2 = success2 and isinstance(response2, list)
            success3 = success3 and isinstance(response3, list)
        
        overall_success = success1 and success2 and success3
        self.log_test(f"Reports endpoints ({role})", overall_success, 
                     f"Attendance: {success1}, Leaves: {success2}, Payroll: {success3}")
        return overall_success

    def test_logout(self, role: str) -> bool:
        """Test logout endpoint"""
        if role not in self.tokens:
            return False
            
        success, response = self.make_request('POST', 'auth/logout', 
                                            token=self.tokens[role])
        
        self.log_test(f"Logout ({role})", success, str(response) if not success else "")
        return success

    def run_comprehensive_tests(self):
        """Run all tests for all roles"""
        print("🚀 Starting TANSEEQ HR Backend API Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Test root endpoint first
        if not self.test_root_endpoint():
            print("❌ Root endpoint failed - stopping tests")
            return False
        
        # Test each role
        for role in ['user', 'admin', 'super_admin']:
            print(f"\n🔐 Testing {role.upper()} role:")
            print("-" * 30)
            
            # Login
            if not self.test_login(role):
                print(f"❌ Login failed for {role} - skipping role tests")
                continue
            
            # Core endpoints
            self.test_dashboard_stats(role)
            self.test_attendance_check_in(role)
            self.test_attendance_records(role)
            self.test_leaves_endpoint(role)
            self.test_field_exits_endpoint(role)
            
            # Role-specific endpoints
            self.test_users_endpoint(role)
            self.test_activity_logs(role)
            self.test_reports_endpoints(role)
            
            # Logout
            self.test_logout(role)
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return False

def main():
    # Get backend URL from frontend .env
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    backend_url = line.split('=', 1)[1].strip()
                    break
            else:
                print("❌ Could not find REACT_APP_BACKEND_URL in frontend/.env")
                return 1
    except Exception as e:
        print(f"❌ Error reading frontend/.env: {e}")
        return 1
    
    print(f"🔗 Using backend URL: {backend_url}")
    
    # Run tests
    tester = TanseeqAPITester(backend_url)
    success = tester.run_comprehensive_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())