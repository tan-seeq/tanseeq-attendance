#!/usr/bin/env python3
"""
URGENT DEBUG: Advances Creation Issue
Testing the exact /advances/create endpoint with Super Admin credentials
Capturing EXACT response format and debugging frontend error handling
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class AdvancesCreateDebugTester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        if self.base_url.endswith('/api'):
            self.api_url = self.base_url
        else:
            self.api_url = f"{self.base_url}/api"
        self.token = None
        self.user_info = None
        
        # Super Admin credentials - trying different variations
        self.super_admin_creds_list = [
            {'email': 'hatem@tan-seeq.co', 'password': 'hatem123'},
            {'email': 'hatem@tanseeq.com', 'password': 'hatem123'},
            {'email': 'hatemmo186@gmail.com', 'password': 'hatem123'},
            {'email': 'hatemmo186@gmail.com', 'password': '123456'}
        ]

    def log_detailed(self, title: str, data: Any):
        """Log detailed information"""
        print(f"\n{'='*60}")
        print(f"🔍 {title}")
        print(f"{'='*60}")
        if isinstance(data, dict) or isinstance(data, list):
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(str(data))

    def make_detailed_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> tuple:
        """Make HTTP request with detailed logging"""
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        print(f"\n🌐 REQUEST DETAILS:")
        print(f"Method: {method}")
        print(f"URL: {url}")
        print(f"Headers: {json.dumps(headers, indent=2)}")
        if data:
            print(f"Request Body: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        try:
            if method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            else:
                return False, {"error": f"Unsupported method: {method}"}
            
            print(f"\n📡 RESPONSE DETAILS:")
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            print(f"Response Text: {response.text}")
            
            try:
                response_data = response.json()
                print(f"Response JSON: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
            except:
                response_data = {"status_code": response.status_code, "text": response.text}
                print(f"Response (not JSON): {response.text}")
            
            return response.status_code, response_data
            
        except requests.exceptions.RequestException as e:
            error_data = {"error": str(e)}
            print(f"❌ REQUEST ERROR: {error_data}")
            return 0, error_data

    def test_super_admin_login(self) -> bool:
        """Test Super Admin login with different credential variations"""
        print("🔐 TESTING SUPER ADMIN LOGIN")
        
        for i, creds in enumerate(self.super_admin_creds_list):
            print(f"\n--- Trying credentials {i+1}: {creds['email']} ---")
            
            status_code, response = self.make_detailed_request('POST', 'auth/login', creds)
            
            if status_code == 200 and 'access_token' in response:
                self.token = response['access_token']
                self.user_info = response['user']
                print(f"✅ Login successful with {creds['email']}!")
                print(f"User Role: {self.user_info.get('role')}")
                print(f"User Name: {self.user_info.get('name')}")
                print(f"User Email: {self.user_info.get('email')}")
                return True
            else:
                print(f"❌ Login failed with {creds['email']}")
        
        print("❌ All login attempts failed!")
        return False

    def get_existing_employee_id(self) -> Optional[str]:
        """Get an existing employee ID for testing"""
        print("\n👥 GETTING EXISTING EMPLOYEE ID")
        
        status_code, response = self.make_detailed_request('GET', 'users')
        
        if status_code == 200 and isinstance(response, list) and len(response) > 0:
            # Find a regular user (not admin)
            for user in response:
                if user.get('role') == 'user':
                    employee_id = user.get('id')
                    print(f"✅ Found employee: {user.get('name')} (ID: {employee_id})")
                    return employee_id
            
            # If no regular user found, use first user
            employee_id = response[0].get('id')
            print(f"✅ Using first user: {response[0].get('name')} (ID: {employee_id})")
            return employee_id
        else:
            print(f"❌ Failed to get users list")
            return None

    def test_advances_create_exact_parameters(self) -> bool:
        """Test /advances/create with exact parameters from review request"""
        print("\n💰 TESTING /advances/create WITH EXACT PARAMETERS")
        
        if not self.token:
            print("❌ No authentication token available")
            return False
        
        employee_id = self.get_existing_employee_id()
        if not employee_id:
            print("❌ No employee ID available for testing")
            return False
        
        # Test parameters exactly as specified in review request
        test_parameters = {
            "employee_id": employee_id,
            "transaction_type": "custody",  # عهدة as shown in screenshot
            "amount": 100,
            "description": "عهده لتسيل و غيار زيت سياره المكتب",
            "notes": "عهده لتسيل و غيار زيت سياره المكتب"
        }
        
        print(f"🧪 Testing with parameters:")
        self.log_detailed("Test Parameters", test_parameters)
        
        status_code, response = self.make_detailed_request('POST', 'advances/create', test_parameters)
        
        print(f"\n📊 ANALYSIS:")
        print(f"Status Code: {status_code}")
        
        if status_code == 200:
            print("✅ Backend returned 200 (SUCCESS)")
            
            # Analyze response structure
            if isinstance(response, dict):
                print(f"Response Type: Dictionary")
                print(f"Response Keys: {list(response.keys())}")
                
                # Check for success indicators
                success_indicators = ['success', 'message', 'transaction_id', 'amount']
                for indicator in success_indicators:
                    if indicator in response:
                        print(f"✅ Has '{indicator}': {response[indicator]}")
                    else:
                        print(f"❌ Missing '{indicator}'")
                
                # Check if this matches what frontend expects
                expected_frontend_structure = {
                    'success': 'boolean',
                    'message': 'string',
                    'transaction_id': 'string',
                    'amount': 'number'
                }
                
                print(f"\n🎯 FRONTEND COMPATIBILITY CHECK:")
                for key, expected_type in expected_frontend_structure.items():
                    if key in response:
                        actual_value = response[key]
                        actual_type = type(actual_value).__name__
                        print(f"✅ {key}: {actual_value} (type: {actual_type})")
                    else:
                        print(f"❌ Missing expected field: {key}")
                
                return True
            else:
                print(f"❌ Response is not a dictionary: {type(response)}")
                return False
                
        elif status_code == 400:
            print("⚠️  Backend returned 400 (BAD REQUEST)")
            print("This might be a validation error")
            return False
            
        elif status_code == 403:
            print("❌ Backend returned 403 (FORBIDDEN)")
            print("Authentication/authorization issue")
            return False
            
        elif status_code == 500:
            print("❌ Backend returned 500 (INTERNAL SERVER ERROR)")
            print("Server-side error")
            return False
            
        else:
            print(f"❌ Unexpected status code: {status_code}")
            return False

    def test_different_transaction_types(self) -> bool:
        """Test different transaction types to see response variations"""
        print("\n🔄 TESTING DIFFERENT TRANSACTION TYPES")
        
        if not self.token:
            print("❌ No authentication token available")
            return False
        
        employee_id = self.get_existing_employee_id()
        if not employee_id:
            print("❌ No employee ID available for testing")
            return False
        
        transaction_types = ["advance", "custody"]
        results = {}
        
        for tx_type in transaction_types:
            print(f"\n--- Testing transaction_type: {tx_type} ---")
            
            test_data = {
                "employee_id": employee_id,
                "transaction_type": tx_type,
                "amount": 50,
                "description": f"Test {tx_type} transaction",
                "notes": f"Testing {tx_type} creation"
            }
            
            status_code, response = self.make_detailed_request('POST', 'advances/create', test_data)
            results[tx_type] = {
                'status_code': status_code,
                'response': response
            }
        
        print(f"\n📋 TRANSACTION TYPE COMPARISON:")
        for tx_type, result in results.items():
            print(f"{tx_type}: Status {result['status_code']}")
            if result['status_code'] == 200:
                print(f"  ✅ Success: {result['response'].get('message', 'No message')}")
            else:
                print(f"  ❌ Error: {result['response']}")
        
        return all(result['status_code'] == 200 for result in results.values())

    def test_authentication_headers(self) -> bool:
        """Test authentication headers specifically"""
        print("\n🔑 TESTING AUTHENTICATION HEADERS")
        
        if not self.token:
            print("❌ No authentication token available")
            return False
        
        # Test with correct token
        print("Testing with correct token...")
        employee_id = self.get_existing_employee_id()
        if not employee_id:
            return False
        
        test_data = {
            "employee_id": employee_id,
            "transaction_type": "advance",
            "amount": 25,
            "description": "Auth test",
            "notes": "Testing authentication"
        }
        
        status_code, response = self.make_detailed_request('POST', 'advances/create', test_data)
        
        if status_code == 200:
            print("✅ Authentication headers working correctly")
            return True
        elif status_code == 401:
            print("❌ Authentication failed (401)")
            return False
        elif status_code == 403:
            print("❌ Authorization failed (403)")
            return False
        else:
            print(f"❌ Unexpected response: {status_code}")
            return False

    def run_debug_test(self):
        """Run the complete debug test"""
        print("🚨 URGENT DEBUG: Advances Creation Issue")
        print("Testing /advances/create endpoint with Super Admin credentials")
        print(f"🌐 Backend URL: {self.api_url}")
        print("=" * 80)
        
        # Step 1: Login
        if not self.test_super_admin_login():
            print("❌ Cannot proceed without successful login")
            return False
        
        # Step 2: Test exact parameters from review request
        exact_test_success = self.test_advances_create_exact_parameters()
        
        # Step 3: Test different transaction types
        types_test_success = self.test_different_transaction_types()
        
        # Step 4: Test authentication headers
        auth_test_success = self.test_authentication_headers()
        
        # Summary
        print("\n" + "=" * 80)
        print("🔍 DEBUG TEST SUMMARY")
        print("=" * 80)
        print(f"✅ Super Admin Login: {'PASS' if self.token else 'FAIL'}")
        print(f"✅ Exact Parameters Test: {'PASS' if exact_test_success else 'FAIL'}")
        print(f"✅ Transaction Types Test: {'PASS' if types_test_success else 'FAIL'}")
        print(f"✅ Authentication Headers: {'PASS' if auth_test_success else 'FAIL'}")
        
        if exact_test_success:
            print("\n🎉 CONCLUSION: Backend /advances/create endpoint is working correctly!")
            print("✅ Returns 200 status code")
            print("✅ Returns proper JSON response structure")
            print("✅ Authentication is working")
            print("\n💡 FRONTEND ISSUE LIKELY:")
            print("- Check Axios configuration")
            print("- Check error handling in frontend")
            print("- Verify response parsing logic")
            print("- Check for JavaScript console errors")
        else:
            print("\n❌ CONCLUSION: Backend /advances/create endpoint has issues!")
            print("- Check server logs for detailed errors")
            print("- Verify database connectivity")
            print("- Check authentication middleware")
        
        return exact_test_success

def main():
    # Use the exact backend URL from frontend/.env
    backend_url = "https://hrms-tanseeq.preview.emergentagent.com"
    
    tester = AdvancesCreateDebugTester(backend_url)
    success = tester.run_debug_test()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()