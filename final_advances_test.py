#!/usr/bin/env python3
"""
FINAL ADVANCES MANAGEMENT SYSTEM TESTING
Testing the key business logic changes with proper balance tracking
"""

import requests
import sys
import json
import os
import tempfile
from datetime import datetime
from typing import Dict, Any, Optional

class FinalAdvancesSystemTester:
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
        
        # Working credentials
        self.test_users = {
            'super_admin': {'email': 'hatem@tan-seeq.co', 'password': 'hatem123'},
            'admin': {'email': 'admin@tanseeq.com', 'password': 'admin123'},
            'user': {'email': 'jihad@tanseeq.com', 'password': '123456'}
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
                    token: Optional[str] = None, expected_status: int = 200, files=None) -> tuple:
        """Make HTTP request and return success status and response"""
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        headers = {}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        if not files:
            headers['Content-Type'] = 'application/json'
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method.upper() == 'POST':
                if files:
                    response = requests.post(url, data=data, files=files, 
                                           headers={k: v for k, v in headers.items() if k != 'Content-Type'}, 
                                           timeout=30)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
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

    def create_test_pdf(self) -> str:
        """Create a test PDF file"""
        temp_file = tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False)
        pdf_content = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R>>endobj
4 0 obj<</Length 44>>stream
BT/F1 12 Tf 100 700 Td(Test Invoice)Tj ET
endstream endobj
xref 0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer<</Size 5/Root 1 0 R>>
startxref 300
%%EOF"""
        temp_file.write(pdf_content)
        temp_file.close()
        return temp_file.name

    def test_key_business_logic_verification(self) -> bool:
        """Test the KEY business logic: Advances NOT deducted, Custody CAN be deducted"""
        print("\n=== Testing KEY Business Logic Verification ===")
        
        if 'super_admin' not in self.tokens or 'user' not in self.tokens:
            self.log_test("Key Business Logic", False, "Required users not logged in")
            return False
        
        # Get initial balance
        success, initial_balance_response = self.make_request('GET', 'advances/my-balance', 
                                                            token=self.tokens['user'])
        if not success:
            self.log_test("Key Business Logic - Get Initial Balance", False, str(initial_balance_response))
            return False
        
        initial_balance = initial_balance_response
        initial_advances = initial_balance.get('total_advances', 0)
        initial_custody = initial_balance.get('total_custody', 0)
        initial_expenses = initial_balance.get('total_expenses', 0)
        
        print(f"Initial State: Advances={initial_advances}, Custody={initial_custody}, Expenses={initial_expenses}")
        
        # Create a small advance
        advance_data = {
            "employee_id": self.users['user']['id'],
            "transaction_type": "advance",
            "amount": 50.0,
            "description": "Test advance for business logic verification",
            "notes": "Testing that advances are NOT deducted by expenses"
        }
        
        success, response = self.make_request('POST', 'advances/create', advance_data, 
                                            token=self.tokens['super_admin'])
        if not success:
            self.log_test("Key Business Logic - Create Advance", False, str(response))
            return False
        
        # Create a small custody
        custody_data = {
            "employee_id": self.users['user']['id'],
            "transaction_type": "custody",
            "amount": 50.0,
            "description": "Test custody for business logic verification",
            "notes": "Testing that custody CAN be deducted by expenses"
        }
        
        success, response = self.make_request('POST', 'advances/create', custody_data, 
                                            token=self.tokens['super_admin'])
        if not success:
            self.log_test("Key Business Logic - Create Custody", False, str(response))
            return False
        
        # Create and approve an expense
        temp_file = self.create_test_pdf()
        try:
            form_data = {
                'amount': '25.0',
                'category': 'transportation',
                'description': 'Test expense for business logic verification',
                'expense_date': '2024-01-20',
                'notes': 'Testing business logic'
            }
            
            with open(temp_file, 'rb') as f:
                files = {'invoice_files': ('test_invoice.pdf', f, 'application/pdf')}
                success, response = self.make_request('POST', 'advances/expense', 
                                                    data=form_data, files=files,
                                                    token=self.tokens['user'])
            
            if not success:
                self.log_test("Key Business Logic - Create Expense", False, str(response))
                return False
                
            expense_transaction_id = response.get('transaction_id')
            
            # Approve the expense
            approval_data = {
                "status": "approved",
                "notes": "Approved for business logic testing"
            }
            
            success, response = self.make_request('POST', f'advances/{expense_transaction_id}/approve', 
                                                approval_data, token=self.tokens['super_admin'])
            
            if not success:
                self.log_test("Key Business Logic - Approve Expense", False, str(response))
                return False
            
            # Check final balance
            success, final_balance_response = self.make_request('GET', 'advances/my-balance', 
                                                              token=self.tokens['user'])
            
            if not success:
                self.log_test("Key Business Logic - Get Final Balance", False, str(final_balance_response))
                return False
            
            final_balance = final_balance_response
            final_advances = final_balance.get('total_advances', 0)
            final_custody = final_balance.get('total_custody', 0)
            final_expenses = final_balance.get('total_expenses', 0)
            remaining_advance = final_balance.get('remaining_advance', 0)
            remaining_custody = final_balance.get('remaining_custody', 0)
            
            print(f"Final State: Advances={final_advances}, Custody={final_custody}, Expenses={final_expenses}")
            print(f"Remaining: Advance={remaining_advance}, Custody={remaining_custody}")
            
            # CRITICAL BUSINESS LOGIC TESTS:
            # 1. Advances should NOT be deducted (remaining_advance should equal total_advances)
            advances_not_deducted = remaining_advance == final_advances
            
            # 2. Total advances should have increased by 50
            advances_increased_correctly = final_advances == initial_advances + 50
            
            # 3. Total custody should have increased by 50
            custody_increased_correctly = final_custody == initial_custody + 50
            
            # 4. Total expenses should have increased by 25
            expenses_increased_correctly = final_expenses == initial_expenses + 25
            
            # 5. Remaining custody should be less than total custody (deducted)
            custody_was_deducted = remaining_custody < final_custody
            
            all_tests_passed = (advances_not_deducted and advances_increased_correctly and 
                              custody_increased_correctly and expenses_increased_correctly and 
                              custody_was_deducted)
            
            details = f"""
            ✓ Advances NOT deducted: {advances_not_deducted} (remaining={remaining_advance}, total={final_advances})
            ✓ Advances increased correctly: {advances_increased_correctly} ({final_advances} = {initial_advances} + 50)
            ✓ Custody increased correctly: {custody_increased_correctly} ({final_custody} = {initial_custody} + 50)
            ✓ Expenses increased correctly: {expenses_increased_correctly} ({final_expenses} = {initial_expenses} + 25)
            ✓ Custody was deducted: {custody_was_deducted} (remaining={remaining_custody} < total={final_custody})
            """
            
            self.log_test("Key Business Logic Verification", all_tests_passed, details if not all_tests_passed else "")
            return all_tests_passed
                
        finally:
            try:
                os.unlink(temp_file)
            except:
                pass

    def test_all_new_endpoints(self) -> bool:
        """Test all new endpoints are working"""
        print("\n=== Testing All New Endpoints ===")
        
        if 'super_admin' not in self.tokens:
            self.log_test("New Endpoints", False, "Super admin not logged in")
            return False
        
        results = []
        
        # 1. Test /advances/admin/all-transactions
        success, response = self.make_request('GET', 'advances/admin/all-transactions', 
                                            token=self.tokens['super_admin'])
        results.append(success and 'transactions' in response)
        self.log_test("All Transactions Endpoint", results[-1], str(response) if not results[-1] else "")
        
        # 2. Test /advances/settle-advance
        settlement_data = {
            "employee_id": self.users['user']['id'],
            "settlement_amount": 100.0,
            "salary_month": "2024-02",
            "notes": "Test settlement"
        }
        
        success, response = self.make_request('POST', 'advances/settle-advance', 
                                            settlement_data, token=self.tokens['super_admin'])
        results.append(success and response.get('success'))
        self.log_test("Settlement Endpoint", results[-1], str(response) if not results[-1] else "")
        
        # 3. Test /advances/expense/{transaction_id}/set-deduction-source
        # First create an expense to test with
        temp_file = self.create_test_pdf()
        try:
            form_data = {
                'amount': '10.0',
                'category': 'supplies',
                'description': 'Test expense for deduction source',
                'expense_date': '2024-01-21',
                'notes': 'Testing deduction source endpoint'
            }
            
            with open(temp_file, 'rb') as f:
                files = {'invoice_files': ('test_invoice.pdf', f, 'application/pdf')}
                success, response = self.make_request('POST', 'advances/expense', 
                                                    data=form_data, files=files,
                                                    token=self.tokens['user'])
            
            if success:
                expense_transaction_id = response.get('transaction_id')
                
                # Test setting deduction source
                deduction_data = {"deduction_source": "custody"}
                success, response = self.make_request('PUT', f'advances/expense/{expense_transaction_id}/set-deduction-source', 
                                                    deduction_data, token=self.tokens['super_admin'])
                results.append(success)
                self.log_test("Deduction Source Endpoint", results[-1], str(response) if not results[-1] else "")
            else:
                results.append(False)
                self.log_test("Deduction Source Endpoint", False, "Failed to create test expense")
                
        finally:
            try:
                os.unlink(temp_file)
            except:
                pass
        
        return all(results)

    def run_comprehensive_test(self):
        """Run comprehensive test of the updated system"""
        print("🚀 Starting FINAL Advances Management System Testing")
        print(f"🌐 Testing against: {self.api_url}")
        print("📋 Verifying NEW business logic and endpoints")
        print("=" * 80)
        
        # Login all users
        print("\n=== Authentication Testing ===")
        for role in ['super_admin', 'admin', 'user']:
            self.test_login(role)
        
        if not any(self.tokens.values()):
            print("❌ No successful logins. Cannot proceed with testing.")
            return False
        
        # Run key tests
        test_methods = [
            self.test_key_business_logic_verification,
            self.test_all_new_endpoints
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                print(f"❌ {test_method.__name__} failed with exception: {str(e)}")
        
        # Summary
        print("\n" + "=" * 80)
        print(f"📊 FINAL TEST SUMMARY")
        print(f"✅ Passed: {self.tests_passed}/{self.tests_run}")
        print(f"❌ Failed: {self.tests_run - self.tests_passed}/{self.tests_run}")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%" if self.tests_run > 0 else "No tests run")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED! Updated Advances Management System is fully operational.")
            print("\n✅ CONFIRMED BUSINESS LOGIC CHANGES:")
            print("   1. ✅ Advances (السُلف) are NOT deducted by expenses")
            print("   2. ✅ Custody (العُهد) CAN be deducted by expenses")
            print("   3. ✅ Super Admin can see ALL transactions")
            print("   4. ✅ Settlement system with salary deduction works")
            print("   5. ✅ Expense deduction source control works")
        else:
            print("⚠️  Some tests failed. Please review the issues above.")
        
        return self.tests_passed == self.tests_run

def main():
    backend_url = "https://attendance-pro-43.preview.emergentagent.com"
    
    print(f"🔧 Backend URL: {backend_url}")
    
    tester = FinalAdvancesSystemTester(backend_url)
    success = tester.run_comprehensive_test()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()