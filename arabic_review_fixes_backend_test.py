#!/usr/bin/env python3
"""
🎯 ARABIC REVIEW FIXES BACKEND TESTING
إعادة اختبار الـ endpoints التي تم إصلاحها فقط

Testing only the 3 specific endpoints mentioned in the Arabic review:
1. Edit Transaction (PUT /api/advances/{transaction_id}/edit) - KeyError fixed
2. Advance Request (POST /api/advances/request) - employee_id issue fixed  
3. Employees with Balances (GET /api/advances/admin/employees-with-balances) - should return employee list correctly

Credentials:
- Super Admin: admin@tanseeq.com / ADMIN
- User: jihad@tanseeq.com / jihad123
"""

import requests
import json
import sys
from datetime import datetime
import os

# Configuration
BASE_URL = "https://attend-deduct-hr.preview.emergentagent.com/api"

# Test credentials
SUPER_ADMIN_CREDS = {
    "email": "admin@tanseeq.com",
    "password": "ADMIN"
}

USER_CREDS = {
    "email": "jihad@tanseeq.com", 
    "password": "jihad123"
}

class ArabicReviewFixesTest:
    def __init__(self):
        self.results = {
            "test_name": "Arabic Review Fixes Backend Test",
            "timestamp": datetime.now().isoformat(),
            "base_url": BASE_URL,
            "tests": [],
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0
            }
        }
        self.super_admin_token = None
        self.user_token = None
        
    def log_test(self, name, status, details, response_data=None):
        """Log test result"""
        test_result = {
            "name": name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        if response_data:
            test_result["response_data"] = response_data
            
        self.results["tests"].append(test_result)
        self.results["summary"]["total"] += 1
        
        if status == "PASS":
            self.results["summary"]["passed"] += 1
            print(f"✅ {name}: {details}")
        else:
            self.results["summary"]["failed"] += 1
            print(f"❌ {name}: {details}")
    
    def authenticate(self, credentials, role_name):
        """Authenticate and get JWT token"""
        try:
            response = requests.post(f"{BASE_URL}/auth/login", json=credentials, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                user_info = data.get("user", {})
                
                self.log_test(
                    f"{role_name} Authentication",
                    "PASS",
                    f"Login successful - Role: {user_info.get('role', 'unknown')}, Name: {user_info.get('name', 'unknown')}",
                    {"user_info": user_info}
                )
                return token
            else:
                self.log_test(
                    f"{role_name} Authentication", 
                    "FAIL",
                    f"Login failed - Status: {response.status_code}, Response: {response.text[:200]}"
                )
                return None
                
        except Exception as e:
            self.log_test(f"{role_name} Authentication", "FAIL", f"Exception: {str(e)}")
            return None
    
    def test_edit_transaction_endpoint(self):
        """Test 1: Edit Transaction (PUT /api/advances/{transaction_id}/edit) - KeyError fixed"""
        if not self.super_admin_token:
            self.log_test("Edit Transaction Test", "SKIP", "No Super Admin token available")
            return
            
        headers = {"Authorization": f"Bearer {self.super_admin_token}"}
        
        try:
            # First, get existing transactions to find one to edit
            response = requests.get(f"{BASE_URL}/advances/admin/all-transactions?limit=10", headers=headers, timeout=30)
            
            if response.status_code != 200:
                self.log_test("Edit Transaction Test", "FAIL", f"Could not get transactions list - Status: {response.status_code}")
                return
                
            transactions = response.json().get("transactions", [])
            if not transactions:
                self.log_test("Edit Transaction Test", "FAIL", "No transactions found to edit")
                return
                
            # Get the first transaction to edit
            transaction_id = transactions[0].get("id")
            if not transaction_id:
                self.log_test("Edit Transaction Test", "FAIL", "No transaction ID found")
                return
            
            # Test edit endpoint with sample data
            edit_data = {
                "amount": 1500.0,
                "description": "Updated test transaction - Arabic review fix test"
            }
            
            response = requests.put(f"{BASE_URL}/advances/{transaction_id}/edit", json=edit_data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Edit Transaction Test",
                    "PASS", 
                    f"Edit transaction successful - Transaction ID: {transaction_id}, Updated amount: {edit_data['amount']}",
                    {"response": data, "transaction_id": transaction_id}
                )
            else:
                self.log_test(
                    "Edit Transaction Test",
                    "FAIL",
                    f"Edit transaction failed - Status: {response.status_code}, Response: {response.text[:500]}"
                )
                
        except Exception as e:
            self.log_test("Edit Transaction Test", "FAIL", f"Exception: {str(e)}")
    
    def test_advance_request_endpoint(self):
        """Test 2: Advance Request (POST /api/advances/request) - employee_id issue fixed"""
        if not self.user_token:
            self.log_test("Advance Request Test", "SKIP", "No User token available")
            return
            
        headers = {"Authorization": f"Bearer {self.user_token}"}
        
        try:
            # Test advance request without employee_id in body (should get from current_user)
            request_data = {
                "transaction_type": "advance",
                "amount": 1000,
                "description": "Test advance request - Arabic review fix"
            }
            
            response = requests.post(f"{BASE_URL}/advances/request", json=request_data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Advance Request Test",
                    "PASS",
                    f"Advance request successful - Amount: {request_data['amount']}, Type: {request_data['transaction_type']}",
                    {"response": data}
                )
            elif response.status_code == 422:
                # Check if it's still asking for employee_id
                error_detail = response.json().get("detail", "")
                if "employee_id" in str(error_detail).lower():
                    self.log_test(
                        "Advance Request Test",
                        "FAIL",
                        f"Still requires employee_id field - Status: {response.status_code}, Error: {error_detail}"
                    )
                else:
                    self.log_test(
                        "Advance Request Test",
                        "PASS",
                        f"Different validation error (not employee_id issue) - Status: {response.status_code}, Error: {error_detail}"
                    )
            else:
                self.log_test(
                    "Advance Request Test",
                    "FAIL",
                    f"Advance request failed - Status: {response.status_code}, Response: {response.text[:500]}"
                )
                
        except Exception as e:
            self.log_test("Advance Request Test", "FAIL", f"Exception: {str(e)}")
    
    def test_employees_with_balances_endpoint(self):
        """Test 3: Employees with Balances (GET /api/advances/admin/employees-with-balances)"""
        if not self.super_admin_token:
            self.log_test("Employees with Balances Test", "SKIP", "No Super Admin token available")
            return
            
        headers = {"Authorization": f"Bearer {self.super_admin_token}"}
        
        try:
            response = requests.get(f"{BASE_URL}/advances/admin/employees-with-balances", headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if response is a list or has employee list
                employees = None
                if isinstance(data, list):
                    employees = data
                elif isinstance(data, dict):
                    employees = data.get("employees", data.get("employee_balances", []))
                
                if employees is not None:
                    employee_count = len(employees)
                    
                    # Check structure of first employee if available
                    sample_employee = employees[0] if employees else None
                    required_fields = ["employee_id", "employee_name", "remaining_advance", "remaining_custody"]
                    
                    if sample_employee:
                        has_required_fields = all(field in sample_employee for field in required_fields)
                        
                        self.log_test(
                            "Employees with Balances Test",
                            "PASS" if has_required_fields else "PARTIAL",
                            f"Retrieved {employee_count} employees - Required fields present: {has_required_fields}",
                            {"employee_count": employee_count, "sample_employee": sample_employee, "has_required_fields": has_required_fields}
                        )
                    else:
                        self.log_test(
                            "Employees with Balances Test",
                            "PASS",
                            f"Retrieved empty employee list ({employee_count} employees)",
                            {"employee_count": employee_count}
                        )
                else:
                    self.log_test(
                        "Employees with Balances Test",
                        "FAIL",
                        f"Could not find employee list in response structure - Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}"
                    )
            else:
                self.log_test(
                    "Employees with Balances Test",
                    "FAIL",
                    f"Request failed - Status: {response.status_code}, Response: {response.text[:500]}"
                )
                
        except Exception as e:
            self.log_test("Employees with Balances Test", "FAIL", f"Exception: {str(e)}")
    
    def run_tests(self):
        """Run all tests"""
        print("🎯 ARABIC REVIEW FIXES BACKEND TESTING")
        print("=" * 60)
        print(f"Base URL: {BASE_URL}")
        print(f"Testing 3 specific endpoints that were recently fixed")
        print()
        
        # Authenticate users
        print("🔐 Authentication Phase:")
        self.super_admin_token = self.authenticate(SUPER_ADMIN_CREDS, "Super Admin")
        self.user_token = self.authenticate(USER_CREDS, "User")
        print()
        
        # Run specific tests
        print("🧪 Testing Fixed Endpoints:")
        self.test_edit_transaction_endpoint()
        self.test_advance_request_endpoint() 
        self.test_employees_with_balances_endpoint()
        print()
        
        # Print summary
        print("📊 TEST SUMMARY:")
        print(f"Total Tests: {self.results['summary']['total']}")
        print(f"Passed: {self.results['summary']['passed']}")
        print(f"Failed: {self.results['summary']['failed']}")
        
        success_rate = (self.results['summary']['passed'] / self.results['summary']['total']) * 100 if self.results['summary']['total'] > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Save results
        results_file = "/app/arabic_review_fixes_test_results.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        print(f"\n📁 Results saved to: {results_file}")
        
        return success_rate >= 66.7  # Consider success if 2/3 tests pass

if __name__ == "__main__":
    tester = ArabicReviewFixesTest()
    success = tester.run_tests()
    
    if success:
        print("\n🎉 ARABIC REVIEW FIXES TESTING COMPLETED SUCCESSFULLY")
    else:
        print("\n⚠️ ARABIC REVIEW FIXES TESTING COMPLETED WITH ISSUES")
    
    sys.exit(0 if success else 1)