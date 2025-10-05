#!/usr/bin/env python3
"""
URGENT VERIFICATION: Fixed Advances Creation Issue
Testing the /advances/create endpoint after configuration fix
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class AdvancesCreationTester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        # Check if base_url already ends with /api
        if self.base_url.endswith('/api'):
            self.api_url = self.base_url
        else:
            self.api_url = f"{self.base_url}/api"
        self.tokens = {}
        self.users = {}
        self.tests_run = 0
        self.tests_passed = 0
        
        # Test credentials from review request - try multiple variations
        self.test_users = {
            'super_admin_1': {'email': 'hatem@tan-seeq.co', 'password': 'hatem123'},
            'super_admin_2': {'email': 'hatem@tanseeq.com', 'password': 'hatem123'},
            'super_admin_3': {'email': 'hatemmo186@gmail.com', 'password': 'hatem123'}
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

    def test_login_super_admin(self) -> bool:
        """Test login with Super Admin credentials from review request"""
        user_data = self.test_users['super_admin']
        success, response = self.make_request('POST', 'auth/login', user_data)
        
        if success and 'access_token' in response:
            self.tokens['super_admin'] = response['access_token']
            self.users['super_admin'] = response['user']
            self.log_test("Super Admin Login (hatem@tan-seeq.co)", True)
            return True
        else:
            self.log_test("Super Admin Login (hatem@tan-seeq.co)", False, str(response))
            return False

    def test_production_url_connectivity(self) -> bool:
        """Test connectivity to production URL"""
        try:
            response = requests.get(f"{self.base_url}/api/auth/me", timeout=30)
            # We expect 401 without token, which means the endpoint is reachable
            success = response.status_code in [401, 422]  # 401 = unauthorized, 422 = validation error
            self.log_test("Production URL Connectivity", success, 
                         f"Status: {response.status_code}" if not success else "")
            return success
        except Exception as e:
            self.log_test("Production URL Connectivity", False, str(e))
            return False

    def test_advances_create_endpoint_basic(self) -> bool:
        """Test basic /advances/create endpoint accessibility"""
        if 'super_admin' not in self.tokens:
            self.log_test("Advances Create Endpoint Basic", False, "No Super Admin token")
            return False
        
        # Test with minimal valid data
        test_data = {
            "employee_id": "test-employee-id",
            "transaction_type": "advance",
            "amount": 100.0,
            "description": "Test advance creation"
        }
        
        success, response = self.make_request('POST', 'advances/create', test_data, 
                                            token=self.tokens['super_admin'])
        
        # We expect either success or a specific error (like employee not found)
        # The key is that we don't get connection errors or 500 errors
        endpoint_accessible = success or (
            not success and 
            response.get('status_code', 0) in [400, 404] and
            'error' not in response
        )
        
        self.log_test("Advances Create Endpoint Basic Access", endpoint_accessible, 
                     str(response) if not endpoint_accessible else "")
        return endpoint_accessible

    def test_advances_create_with_real_employee(self) -> bool:
        """Test /advances/create with real employee ID from review request"""
        if 'super_admin' not in self.tokens:
            self.log_test("Advances Create Real Employee", False, "No Super Admin token")
            return False
        
        # First, get list of employees to find a valid employee_id
        success, users_response = self.make_request('GET', 'users', 
                                                   token=self.tokens['super_admin'])
        
        if not success or not users_response:
            self.log_test("Advances Create Real Employee Setup", False, "Could not get users list")
            return False
        
        # Find a valid employee ID
        employee_id = None
        for user in users_response:
            if user.get('id') and user.get('role') in ['user', 'admin']:
                employee_id = user['id']
                break
        
        if not employee_id:
            self.log_test("Advances Create Real Employee Setup", False, "No valid employee found")
            return False
        
        # Test advance creation with exact parameters from review request
        test_data = {
            "employee_id": employee_id,
            "transaction_type": "custody",
            "amount": 100,
            "description": "عهده لتسيل و غيار زيت سياره المكتب",
            "notes": "عهده لتسيل و غيار زيت سياره المكتب"
        }
        
        success, response = self.make_request('POST', 'advances/create', test_data, 
                                            token=self.tokens['super_admin'])
        
        if success:
            # Check response structure matches expected format
            has_success = response.get('success') is True
            has_message = 'message' in response
            has_transaction_id = 'transaction_id' in response
            has_amount = 'amount' in response
            
            structure_valid = has_success and has_message and has_transaction_id and has_amount
            
            self.log_test("Advances Create Real Employee", structure_valid, 
                         f"Response structure: success={has_success}, message={has_message}, transaction_id={has_transaction_id}, amount={has_amount}")
            return structure_valid
        else:
            self.log_test("Advances Create Real Employee", False, str(response))
            return False

    def test_advances_create_both_types(self) -> bool:
        """Test both advance and custody transaction types"""
        if 'super_admin' not in self.tokens:
            self.log_test("Advances Create Both Types", False, "No Super Admin token")
            return False
        
        # Get a valid employee ID
        success, users_response = self.make_request('GET', 'users', 
                                                   token=self.tokens['super_admin'])
        
        if not success or not users_response:
            self.log_test("Advances Create Both Types Setup", False, "Could not get users list")
            return False
        
        employee_id = None
        for user in users_response:
            if user.get('id') and user.get('role') in ['user', 'admin']:
                employee_id = user['id']
                break
        
        if not employee_id:
            self.log_test("Advances Create Both Types Setup", False, "No valid employee found")
            return False
        
        # Test both transaction types
        transaction_types = [
            {"type": "advance", "desc": "سلفة للموظف"},
            {"type": "custody", "desc": "عهدة للموظف"}
        ]
        
        all_passed = True
        for tx_type in transaction_types:
            test_data = {
                "employee_id": employee_id,
                "transaction_type": tx_type["type"],
                "amount": 50.0,
                "description": tx_type["desc"],
                "notes": f"اختبار {tx_type['type']}"
            }
            
            success, response = self.make_request('POST', 'advances/create', test_data, 
                                                token=self.tokens['super_admin'])
            
            if success and response.get('success'):
                self.log_test(f"Create {tx_type['type']} transaction", True)
            else:
                self.log_test(f"Create {tx_type['type']} transaction", False, str(response))
                all_passed = False
        
        return all_passed

    def test_frontend_backend_connectivity(self) -> bool:
        """Test that frontend can reach backend using production URL"""
        # Test the exact URL that frontend should be using
        frontend_backend_url = "https://hrapp-tanseeq.emergent.host/api"
        
        try:
            # Test a simple endpoint that doesn't require auth
            response = requests.get(f"{frontend_backend_url}/auth/me", timeout=30)
            # We expect 401 (unauthorized) which means the endpoint is reachable
            connectivity_ok = response.status_code == 401
            
            self.log_test("Frontend-Backend Connectivity", connectivity_ok, 
                         f"Status: {response.status_code}" if not connectivity_ok else "")
            return connectivity_ok
        except Exception as e:
            self.log_test("Frontend-Backend Connectivity", False, str(e))
            return False

    def test_advances_balance_endpoint(self) -> bool:
        """Test advances balance endpoint to verify system integration"""
        if 'super_admin' not in self.tokens:
            self.log_test("Advances Balance Endpoint", False, "No Super Admin token")
            return False
        
        success, response = self.make_request('GET', 'advances/my-balance', 
                                            token=self.tokens['super_admin'])
        
        if success:
            # Check response structure
            expected_keys = ['employee_name', 'total_advances', 'total_custody', 
                           'total_expenses', 'remaining_advance', 'remaining_custody', 
                           'total_available']
            
            has_expected_keys = all(key in response for key in expected_keys)
            self.log_test("Advances Balance Endpoint", has_expected_keys, 
                         f"Missing keys: {set(expected_keys) - set(response.keys())}" if not has_expected_keys else "")
            return has_expected_keys
        else:
            self.log_test("Advances Balance Endpoint", False, str(response))
            return False

    def test_advances_transactions_endpoint(self) -> bool:
        """Test advances transactions endpoint"""
        if 'super_admin' not in self.tokens:
            self.log_test("Advances Transactions Endpoint", False, "No Super Admin token")
            return False
        
        success, response = self.make_request('GET', 'advances/my-transactions', 
                                            token=self.tokens['super_admin'])
        
        if success:
            # Check response structure
            has_transactions_key = 'transactions' in response
            transactions_is_list = isinstance(response.get('transactions'), list)
            
            structure_valid = has_transactions_key and transactions_is_list
            self.log_test("Advances Transactions Endpoint", structure_valid, 
                         f"Has transactions key: {has_transactions_key}, Is list: {transactions_is_list}")
            return structure_valid
        else:
            self.log_test("Advances Transactions Endpoint", False, str(response))
            return False

    def run_all_tests(self):
        """Run all advances creation tests"""
        print("🚀 URGENT VERIFICATION: Fixed Advances Creation Issue")
        print("=" * 60)
        print(f"Testing URL: {self.base_url}")
        print(f"API URL: {self.api_url}")
        print("=" * 60)
        
        # Test sequence
        tests = [
            self.test_production_url_connectivity,
            self.test_login_super_admin,
            self.test_frontend_backend_connectivity,
            self.test_advances_create_endpoint_basic,
            self.test_advances_balance_endpoint,
            self.test_advances_transactions_endpoint,
            self.test_advances_create_with_real_employee,
            self.test_advances_create_both_types,
        ]
        
        for test in tests:
            test()
        
        print("=" * 60)
        print(f"Tests completed: {self.tests_passed}/{self.tests_run}")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED - Advances creation issue is FIXED!")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return False

def main():
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        # Use production URL from review request
        base_url = "https://hrapp-tanseeq.emergent.host"
    
    tester = AdvancesCreationTester(base_url)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()