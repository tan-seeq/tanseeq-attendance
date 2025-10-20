#!/usr/bin/env python3
"""
Employee Permissions Management System Testing
Focused testing for the permissions endpoints
"""

import requests
import sys
import json
from datetime import datetime

class PermissionsAPITester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        if self.base_url.endswith('/api'):
            self.api_url = self.base_url
        else:
            self.api_url = f"{self.base_url}/api"
        self.tokens = {}
        self.users = {}
        self.tests_run = 0
        self.tests_passed = 0
        
        # Test users from review request
        self.test_users = {
            'user': {'email': 'jihad@tanseeq.com', 'password': 'jihad123'},
            'admin': {'email': 'mahmoud@tanseeq.com', 'password': 'mahmoud123'},
            'super_admin': {'email': 'hatemmo186@gmail.com', 'password': 'hatem123'}
        }

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")

    def make_request(self, method: str, endpoint: str, data=None, token=None, expected_status: int = 200):
        """Make HTTP request"""
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
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

    def test_permissions_endpoints(self):
        """Test all permissions endpoints"""
        print("🔐 Employee Permissions Management System Testing")
        print("=" * 60)
        
        # Login all users
        for role in self.test_users.keys():
            self.test_login(role)
        
        # Test each role
        for role in ['super_admin', 'admin', 'user']:
            if role not in self.tokens:
                continue
                
            print(f"\n🧪 Testing as {role.upper()}...")
            print("-" * 40)
            
            # Test permission templates
            expected_status = 200 if role == 'super_admin' else 403
            success, response = self.make_request('GET', 'work-reports/permission-templates', 
                                                token=self.tokens[role], expected_status=expected_status)
            self.log_test(f"Permission templates ({role})", success, str(response) if not success else "")
            
            # Test my permissions
            success, response = self.make_request('GET', 'work-reports/my-permissions', 
                                                token=self.tokens[role])
            self.log_test(f"My permissions ({role})", success, str(response) if not success else "")
            
            # Test permissions list
            expected_status = 200 if role == 'super_admin' else 403
            success, response = self.make_request('GET', 'work-reports/permissions', 
                                                token=self.tokens[role], expected_status=expected_status)
            self.log_test(f"Permissions list ({role})", success, str(response) if not success else "")
            
            # Test get user permissions
            user_id = self.users[role]['id']
            success, response = self.make_request('GET', f'work-reports/permissions/{user_id}', 
                                                token=self.tokens[role])
            self.log_test(f"Get user permissions ({role})", success, str(response) if not success else "")
            
            # Test create/update permissions
            expected_status = 200 if role == 'super_admin' else 403
            permission_data = {"permission_level": "user", "notes": "Test permission"}
            success, response = self.make_request('POST', f'work-reports/permissions/{user_id}', 
                                                permission_data, token=self.tokens[role], 
                                                expected_status=expected_status)
            self.log_test(f"Create/update permissions ({role})", success, str(response) if not success else "")
            
            # Test delete permissions
            expected_status = 200 if role == 'super_admin' else 403
            success, response = self.make_request('DELETE', f'work-reports/permissions/{user_id}', 
                                                token=self.tokens[role], expected_status=expected_status)
            self.log_test(f"Delete permissions ({role})", success, str(response) if not success else "")
        
        # Summary
        print("\n" + "=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        print(f"Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%")

if __name__ == "__main__":
    base_url = "https://payroll-hardening.preview.emergentagent.com"
    tester = PermissionsAPITester(base_url)
    tester.test_permissions_endpoints()