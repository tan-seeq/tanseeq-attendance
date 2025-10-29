#!/usr/bin/env python3
"""
URGENT BUG FIX VERIFICATION: Test Advances Creation Endpoint
Testing the newly fixed /advances/create endpoint to verify FastAPI parameter validation bug is resolved.
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class AdvancesCreateTester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        if self.base_url.endswith('/api'):
            self.api_url = self.base_url
        else:
            self.api_url = f"{self.base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        
        # Super Admin credentials from review request
        self.super_admin = {'email': 'hatem@tan-seeq.co', 'password': 'hatem123'}
        self.token = None

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
                response = requests.get(url, headers=headers, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                return False, f"Unsupported method: {method}"
            
            success = response.status_code == expected_status
            return success, response
            
        except requests.exceptions.RequestException as e:
            return False, f"Request failed: {str(e)}"

    def login_super_admin(self) -> bool:
        """Login as Super Admin"""
        print(f"\n🔐 Testing Super Admin Login: {self.super_admin['email']}")
        
        success, response = self.make_request('POST', '/auth/login', {
            'email': self.super_admin['email'],
            'password': self.super_admin['password']
        })
        
        if success and hasattr(response, 'json'):
            try:
                data = response.json()
                if 'access_token' in data:
                    self.token = data['access_token']
                    user_info = data.get('user', {})
                    self.log_test(f"Super Admin Login ({self.super_admin['email']})", True, 
                                f"Role: {user_info.get('role', 'unknown')}")
                    return True
                else:
                    self.log_test("Super Admin Login", False, "No access token in response")
                    return False
            except json.JSONDecodeError:
                self.log_test("Super Admin Login", False, "Invalid JSON response")
                return False
        else:
            error_msg = "Login failed"
            if hasattr(response, 'text'):
                error_msg += f": {response.text}"
            self.log_test("Super Admin Login", False, error_msg)
            return False

    def get_employee_id(self) -> Optional[str]:
        """Get an existing employee ID for testing"""
        print("\n👥 Getting Employee List for Testing")
        
        success, response = self.make_request('GET', '/users', token=self.token)
        
        if success and hasattr(response, 'json'):
            try:
                users = response.json()
                if isinstance(users, list) and len(users) > 0:
                    # Find a regular user (not admin/super_admin)
                    for user in users:
                        if user.get('role') == 'user':
                            employee_id = user.get('id')
                            employee_name = user.get('name', 'Unknown')
                            self.log_test(f"Found Employee for Testing: {employee_name}", True, f"ID: {employee_id}")
                            return employee_id
                    
                    # If no regular user found, use any user
                    first_user = users[0]
                    employee_id = first_user.get('id')
                    employee_name = first_user.get('name', 'Unknown')
                    self.log_test(f"Using First Available User: {employee_name}", True, f"ID: {employee_id}")
                    return employee_id
                else:
                    self.log_test("Get Employee List", False, "No users found")
                    return None
            except json.JSONDecodeError:
                self.log_test("Get Employee List", False, "Invalid JSON response")
                return None
        else:
            error_msg = "Failed to get users"
            if hasattr(response, 'text'):
                error_msg += f": {response.text}"
            self.log_test("Get Employee List", False, error_msg)
            return None

    def test_advances_create_endpoint(self, employee_id: str) -> bool:
        """Test the /advances/create endpoint with the specific parameters from review request"""
        print(f"\n💰 Testing Advances Creation Endpoint - BUG FIX VERIFICATION")
        
        # Test data from review request
        test_advance = {
            "employee_id": employee_id,
            "transaction_type": "advance",
            "amount": 100.0,
            "description": "Test advance for oil change",
            "notes": "Testing the bug fix"
        }
        
        print(f"📋 Test Parameters:")
        print(f"   Employee ID: {employee_id}")
        print(f"   Transaction Type: {test_advance['transaction_type']}")
        print(f"   Amount: {test_advance['amount']} AED")
        print(f"   Description: {test_advance['description']}")
        print(f"   Notes: {test_advance['notes']}")
        
        success, response = self.make_request('POST', '/advances/create', test_advance, 
                                            token=self.token, expected_status=200)
        
        if success and hasattr(response, 'json'):
            try:
                data = response.json()
                
                # Check for successful response structure
                if data.get('success') == True:
                    transaction_id = data.get('transaction_id')
                    amount = data.get('amount')
                    message = data.get('message', '')
                    
                    self.log_test("Advances Create - Success Response", True, 
                                f"Transaction ID: {transaction_id}, Amount: {amount} AED")
                    
                    # Verify no FastAPI validation errors
                    self.log_test("Advances Create - No FastAPI Validation Errors", True, 
                                "No 'AssertionError: non-body parameters must be in path, query, header or cookie' error")
                    
                    # Verify response structure
                    required_fields = ['success', 'message', 'transaction_id', 'amount']
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if not missing_fields:
                        self.log_test("Advances Create - Response Structure", True, 
                                    "All required fields present in response")
                    else:
                        self.log_test("Advances Create - Response Structure", False, 
                                    f"Missing fields: {missing_fields}")
                    
                    return True
                else:
                    self.log_test("Advances Create - Success Flag", False, 
                                f"Expected success=True, got: {data.get('success')}")
                    return False
                    
            except json.JSONDecodeError:
                self.log_test("Advances Create - JSON Response", False, "Invalid JSON response")
                return False
        else:
            error_msg = f"HTTP {response.status_code}" if hasattr(response, 'status_code') else "Request failed"
            if hasattr(response, 'text'):
                response_text = response.text
                
                # Check specifically for the FastAPI validation error that was being fixed
                if "AssertionError: non-body parameters must be in path, query, header or cookie" in response_text:
                    self.log_test("Advances Create - FastAPI Validation Bug", False, 
                                "BUG STILL EXISTS: FastAPI parameter validation error detected")
                else:
                    error_msg += f": {response_text}"
            
            self.log_test("Advances Create - HTTP Request", False, error_msg)
            return False

    def test_advances_create_with_different_types(self, employee_id: str):
        """Test advances creation with different transaction types"""
        print(f"\n🔄 Testing Different Transaction Types")
        
        transaction_types = [
            ("custody", "Test custody for equipment"),
            ("advance", "Test advance for travel expenses")
        ]
        
        for trans_type, description in transaction_types:
            test_data = {
                "employee_id": employee_id,
                "transaction_type": trans_type,
                "amount": 150.0,
                "description": description,
                "notes": f"Testing {trans_type} creation"
            }
            
            success, response = self.make_request('POST', '/advances/create', test_data, 
                                                token=self.token, expected_status=200)
            
            if success and hasattr(response, 'json'):
                try:
                    data = response.json()
                    if data.get('success') == True:
                        self.log_test(f"Create {trans_type.title()}", True, 
                                    f"Transaction ID: {data.get('transaction_id')}")
                    else:
                        self.log_test(f"Create {trans_type.title()}", False, 
                                    f"Success flag false: {data}")
                except json.JSONDecodeError:
                    self.log_test(f"Create {trans_type.title()}", False, "Invalid JSON response")
            else:
                error_msg = f"HTTP {response.status_code}" if hasattr(response, 'status_code') else "Request failed"
                if hasattr(response, 'text'):
                    error_msg += f": {response.text}"
                self.log_test(f"Create {trans_type.title()}", False, error_msg)

    def run_all_tests(self):
        """Run all tests for advances creation bug fix verification"""
        print("=" * 80)
        print("🚀 URGENT BUG FIX VERIFICATION: Advances Creation Endpoint")
        print("=" * 80)
        print(f"🌐 API Base URL: {self.api_url}")
        print(f"📅 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Step 1: Login as Super Admin
        if not self.login_super_admin():
            print("\n❌ CRITICAL: Cannot proceed without Super Admin authentication")
            return False
        
        # Step 2: Get employee ID for testing
        employee_id = self.get_employee_id()
        if not employee_id:
            print("\n❌ CRITICAL: Cannot proceed without employee ID for testing")
            return False
        
        # Step 3: Test the specific advances creation endpoint (main bug fix verification)
        main_test_success = self.test_advances_create_endpoint(employee_id)
        
        # Step 4: Test with different transaction types
        self.test_advances_create_with_different_types(employee_id)
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 BUG FIX VERIFICATION SUMMARY")
        print("=" * 80)
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if main_test_success:
            print("\n🎉 BUG FIX VERIFICATION: SUCCESS")
            print("✅ The FastAPI parameter validation bug has been resolved")
            print("✅ /advances/create endpoint is working correctly")
            print("✅ No 'AssertionError: non-body parameters must be in path, query, header or cookie' errors")
        else:
            print("\n⚠️ BUG FIX VERIFICATION: FAILED")
            print("❌ The advances creation endpoint is still not working properly")
            print("❌ Further investigation needed")
        
        return main_test_success

def main():
    # Get backend URL from environment or use default
    import os
    backend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://attendance-calc-4.preview.emergentagent.com')
    
    print(f"🔧 Using Backend URL: {backend_url}")
    
    tester = AdvancesCreateTester(backend_url)
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()