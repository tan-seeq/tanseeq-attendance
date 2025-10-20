#!/usr/bin/env python3
"""
UPDATED ADVANCES MANAGEMENT SYSTEM - COMPREHENSIVE BACKEND TESTING
Testing the redesigned system based on user feedback with new business logic:

BUSINESS LOGIC CHANGES:
1. Advances (السُلف): No longer deducted by expenses, remain until salary settlement
2. Custody (العُهد): Can be deducted by expenses directly  
3. Expenses: Super Admin chooses deduction source (advance vs custody)
4. Settlements: New settlement system for advances with salary deduction
5. Admin Transactions: Super Admin should see ALL transactions

NEW ENDPOINTS TO TEST:
1. /advances/admin/all-transactions - Super Admin view of all transactions
2. /advances/settle-advance - Settlement of advances with salary
3. /advances/expense/{transaction_id}/set-deduction-source - Choose expense deduction source
"""

import requests
import sys
import json
import os
import tempfile
from datetime import datetime
from typing import Dict, Any, Optional

class UpdatedAdvancesSystemTester:
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
        self.created_transactions = []
        
        # Test users from review request (using working credentials)
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

    def create_test_pdf(self, filename: str = "test_invoice.pdf") -> str:
        """Create a test PDF file for expense uploads"""
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

    def test_super_admin_all_transactions_view(self) -> bool:
        """Test NEW ENDPOINT: /advances/admin/all-transactions - Super Admin view of ALL transactions"""
        print("\n=== Testing Super Admin All Transactions View (NEW ENDPOINT) ===")
        
        if 'super_admin' not in self.tokens:
            self.log_test("Super Admin All Transactions", False, "Super admin not logged in")
            return False
        
        # Test the new endpoint
        success, response = self.make_request('GET', 'advances/admin/all-transactions', 
                                            token=self.tokens['super_admin'])
        
        if success and 'transactions' in response:
            transactions = response['transactions']
            
            # Verify we can see ALL transactions across all employees
            has_transactions = len(transactions) > 0
            has_proper_structure = True
            
            if has_transactions:
                # Check first transaction structure
                first_transaction = transactions[0]
                required_fields = ['id', 'employee_id', 'employee_name', 'transaction_type', 
                                 'amount', 'status', 'created_at']
                has_proper_structure = all(field in first_transaction for field in required_fields)
            
            overall_success = has_transactions and has_proper_structure
            self.log_test("Super Admin All Transactions View", overall_success,
                         f"Found {len(transactions)} transactions, proper structure: {has_proper_structure}")
            return overall_success
        else:
            self.log_test("Super Admin All Transactions View", False, str(response))
            return False

    def test_updated_balance_logic_advances_not_deducted(self) -> bool:
        """Test CRITICAL: Advances remain 100 AED after 30 AED expense (not deducted)"""
        print("\n=== Testing Updated Balance Logic: Advances NOT Deducted by Expenses ===")
        
        if 'super_admin' not in self.tokens or 'user' not in self.tokens:
            self.log_test("Updated Balance Logic", False, "Required users not logged in")
            return False
        
        # Step 1: Create advance of 100 AED
        advance_data = {
            "employee_id": self.users['user']['id'],
            "transaction_type": "advance",
            "amount": 100.0,
            "description": "Test advance 100 AED for balance logic testing",
            "notes": "Testing new business logic - advances should not be deducted by expenses"
        }
        
        success, response = self.make_request('POST', 'advances/create', advance_data, 
                                            token=self.tokens['super_admin'])
        
        if not success:
            self.log_test("Updated Balance Logic - Create Advance", False, str(response))
            return False
        
        advance_transaction_id = response.get('transaction_id')
        self.created_transactions.append(advance_transaction_id)
        
        # Step 2: Create expense of 30 AED
        temp_file = self.create_test_pdf()
        try:
            form_data = {
                'amount': '30.0',
                'category': 'transportation',
                'description': 'Test expense 30 AED for balance logic testing',
                'expense_date': '2024-01-15',
                'notes': 'Testing if advance remains 100 AED after this expense'
            }
            
            with open(temp_file, 'rb') as f:
                files = {'invoice_files': ('test_invoice.pdf', f, 'application/pdf')}
                success, response = self.make_request('POST', 'advances/expense', 
                                                    data=form_data, files=files,
                                                    token=self.tokens['user'])
            
            if not success:
                self.log_test("Updated Balance Logic - Create Expense", False, str(response))
                return False
                
            expense_transaction_id = response.get('transaction_id')
            
            # Step 3: Approve the expense
            approval_data = {
                "status": "approved",
                "notes": "Approved for balance logic testing"
            }
            
            success, response = self.make_request('POST', f'advances/{expense_transaction_id}/approve', 
                                                approval_data, token=self.tokens['super_admin'])
            
            if not success:
                self.log_test("Updated Balance Logic - Approve Expense", False, str(response))
                return False
            
            # Step 4: Check balance - advance should remain 100 AED (NOT deducted)
            success, response = self.make_request('GET', 'advances/my-balance', 
                                                token=self.tokens['user'])
            
            if success:
                balance = response
                remaining_advance = balance.get('remaining_advance', 0)
                total_expenses = balance.get('total_expenses', 0)
                
                # CRITICAL TEST: Advance should remain 100 AED despite 30 AED expense
                advance_not_deducted = remaining_advance == 100.0
                expense_recorded = total_expenses >= 30.0
                
                overall_success = advance_not_deducted and expense_recorded
                
                self.log_test("Updated Balance Logic - Advances NOT Deducted", overall_success,
                             f"Remaining advance: {remaining_advance} AED (should be 100), "
                             f"Total expenses: {total_expenses} AED (should include 30)")
                return overall_success
            else:
                self.log_test("Updated Balance Logic - Check Balance", False, str(response))
                return False
                
        finally:
            try:
                os.unlink(temp_file)
            except:
                pass

    def test_custody_deduction_by_expenses(self) -> bool:
        """Test CRITICAL: Custody CAN be deducted by expenses directly"""
        print("\n=== Testing Custody Deduction by Expenses ===")
        
        if 'super_admin' not in self.tokens or 'user' not in self.tokens:
            self.log_test("Custody Deduction Logic", False, "Required users not logged in")
            return False
        
        # Step 1: Create custody of 100 AED
        custody_data = {
            "employee_id": self.users['user']['id'],
            "transaction_type": "custody",
            "amount": 100.0,
            "description": "Test custody 100 AED for deduction testing",
            "notes": "Testing new business logic - custody should be deducted by expenses"
        }
        
        success, response = self.make_request('POST', 'advances/create', custody_data, 
                                            token=self.tokens['super_admin'])
        
        if not success:
            self.log_test("Custody Deduction - Create Custody", False, str(response))
            return False
        
        # Step 2: Create and approve expense of 30 AED
        temp_file = self.create_test_pdf()
        try:
            form_data = {
                'amount': '30.0',
                'category': 'meals',
                'description': 'Test expense 30 AED for custody deduction testing',
                'expense_date': '2024-01-16',
                'notes': 'Testing if custody is properly deducted'
            }
            
            with open(temp_file, 'rb') as f:
                files = {'invoice_files': ('test_invoice.pdf', f, 'application/pdf')}
                success, response = self.make_request('POST', 'advances/expense', 
                                                    data=form_data, files=files,
                                                    token=self.tokens['user'])
            
            if not success:
                self.log_test("Custody Deduction - Create Expense", False, str(response))
                return False
                
            expense_transaction_id = response.get('transaction_id')
            
            # Approve the expense
            approval_data = {
                "status": "approved",
                "notes": "Approved for custody deduction testing"
            }
            
            success, response = self.make_request('POST', f'advances/{expense_transaction_id}/approve', 
                                                approval_data, token=self.tokens['super_admin'])
            
            if not success:
                self.log_test("Custody Deduction - Approve Expense", False, str(response))
                return False
            
            # Step 3: Check balance - custody should be deducted to 70 AED
            success, response = self.make_request('GET', 'advances/my-balance', 
                                                token=self.tokens['user'])
            
            if success:
                balance = response
                remaining_custody = balance.get('remaining_custody', 0)
                
                # CRITICAL TEST: Custody should be deducted (100 - 30 = 70)
                custody_properly_deducted = remaining_custody == 70.0
                
                self.log_test("Custody Deduction by Expenses", custody_properly_deducted,
                             f"Remaining custody: {remaining_custody} AED (should be 70)")
                return custody_properly_deducted
            else:
                self.log_test("Custody Deduction - Check Balance", False, str(response))
                return False
                
        finally:
            try:
                os.unlink(temp_file)
            except:
                pass

    def test_settlement_system(self) -> bool:
        """Test NEW ENDPOINT: /advances/settle-advance - Settlement of advances with salary"""
        print("\n=== Testing Settlement System (NEW ENDPOINT) ===")
        
        if 'super_admin' not in self.tokens:
            self.log_test("Settlement System", False, "Super admin not logged in")
            return False
        
        # Test the new settlement endpoint
        settlement_data = {
            "employee_id": self.users['user']['id'],
            "settlement_amount": 500.0,
            "salary_month": "2024-01",
            "notes": "Test settlement with salary deduction"
        }
        
        success, response = self.make_request('POST', 'advances/settle-advance', 
                                            settlement_data, token=self.tokens['super_admin'])
        
        if success and response.get('success'):
            settlement_transaction_id = response.get('transaction_id')
            self.created_transactions.append(settlement_transaction_id)
            
            # Verify settlement transaction was created
            has_transaction_id = settlement_transaction_id is not None
            has_success_message = 'تم تسوية السلفة بنجاح' in response.get('message', '')
            
            overall_success = has_transaction_id and has_success_message
            self.log_test("Settlement System", overall_success,
                         f"Transaction ID: {settlement_transaction_id}, Success message: {has_success_message}")
            return overall_success
        else:
            self.log_test("Settlement System", False, str(response))
            return False

    def test_deduction_source_control(self) -> bool:
        """Test NEW ENDPOINT: /advances/expense/{transaction_id}/set-deduction-source"""
        print("\n=== Testing Deduction Source Control (NEW ENDPOINT) ===")
        
        if 'super_admin' not in self.tokens or 'user' not in self.tokens:
            self.log_test("Deduction Source Control", False, "Required users not logged in")
            return False
        
        # First create an expense to test with
        temp_file = self.create_test_pdf()
        try:
            form_data = {
                'amount': '50.0',
                'category': 'supplies',
                'description': 'Test expense for deduction source control',
                'expense_date': '2024-01-17',
                'notes': 'Testing deduction source selection'
            }
            
            with open(temp_file, 'rb') as f:
                files = {'invoice_files': ('test_invoice.pdf', f, 'application/pdf')}
                success, response = self.make_request('POST', 'advances/expense', 
                                                    data=form_data, files=files,
                                                    token=self.tokens['user'])
            
            if not success:
                self.log_test("Deduction Source Control - Create Expense", False, str(response))
                return False
                
            expense_transaction_id = response.get('transaction_id')
            
            # Test setting deduction source to 'advance'
            deduction_data = {"deduction_source": "advance"}
            success, response = self.make_request('PUT', f'advances/expense/{expense_transaction_id}/set-deduction-source', 
                                                deduction_data, token=self.tokens['super_admin'])
            
            if not success:
                self.log_test("Deduction Source Control - Set to Advance", False, str(response))
                return False
            
            # Test setting deduction source to 'custody'
            deduction_data = {"deduction_source": "custody"}
            success, response = self.make_request('PUT', f'advances/expense/{expense_transaction_id}/set-deduction-source', 
                                                deduction_data, token=self.tokens['super_admin'])
            
            if success:
                self.log_test("Deduction Source Control", True)
                return True
            else:
                self.log_test("Deduction Source Control - Set to Custody", False, str(response))
                return False
                
        finally:
            try:
                os.unlink(temp_file)
            except:
                pass

    def test_super_admin_access_control(self) -> bool:
        """Test that only Super Admin can access new endpoints"""
        print("\n=== Testing Super Admin Access Control for New Endpoints ===")
        
        if 'admin' not in self.tokens or 'user' not in self.tokens:
            self.log_test("Super Admin Access Control", False, "Required users not logged in")
            return False
        
        results = []
        
        # Test /advances/admin/all-transactions with regular admin (should fail)
        success, response = self.make_request('GET', 'advances/admin/all-transactions', 
                                            token=self.tokens['admin'], expected_status=403)
        results.append(success)
        self.log_test("All Transactions - Admin Access Denied", success,
                     "Expected 403 but got different status" if not success else "")
        
        # Test /advances/admin/all-transactions with regular user (should fail)
        success, response = self.make_request('GET', 'advances/admin/all-transactions', 
                                            token=self.tokens['user'], expected_status=403)
        results.append(success)
        self.log_test("All Transactions - User Access Denied", success,
                     "Expected 403 but got different status" if not success else "")
        
        # Test settlement endpoint with admin (should fail)
        settlement_data = {
            "employee_id": self.users['user']['id'],
            "settlement_amount": 100.0,
            "salary_month": "2024-01",
            "notes": "Test access control"
        }
        
        success, response = self.make_request('POST', 'advances/settle-advance', 
                                            settlement_data, token=self.tokens['admin'], 
                                            expected_status=403)
        results.append(success)
        self.log_test("Settlement - Admin Access Denied", success,
                     "Expected 403 but got different status" if not success else "")
        
        return all(results)

    def run_comprehensive_test(self):
        """Run all tests for the updated advances management system"""
        print("🚀 Starting UPDATED Advances Management System Backend Testing")
        print(f"🌐 Testing against: {self.api_url}")
        print("📋 Testing NEW business logic and endpoints based on user feedback")
        print("=" * 80)
        
        # Login all users
        print("\n=== Authentication Testing ===")
        for role in ['super_admin', 'admin', 'user']:
            self.test_login(role)
        
        if not any(self.tokens.values()):
            print("❌ No successful logins. Cannot proceed with testing.")
            return False
        
        # Test all new functionality
        test_methods = [
            self.test_super_admin_all_transactions_view,
            self.test_updated_balance_logic_advances_not_deducted,
            self.test_custody_deduction_by_expenses,
            self.test_settlement_system,
            self.test_deduction_source_control,
            self.test_super_admin_access_control
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                print(f"❌ {test_method.__name__} failed with exception: {str(e)}")
        
        # Summary
        print("\n" + "=" * 80)
        print(f"📊 UPDATED ADVANCES SYSTEM TEST SUMMARY")
        print(f"✅ Passed: {self.tests_passed}/{self.tests_run}")
        print(f"❌ Failed: {self.tests_run - self.tests_passed}/{self.tests_run}")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%" if self.tests_run > 0 else "No tests run")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED! Updated Advances Management System is working correctly.")
            print("✅ New business logic implemented successfully:")
            print("   - Advances remain until salary settlement")
            print("   - Custody can be deducted by expenses")
            print("   - Super Admin can choose deduction source")
            print("   - Settlement system operational")
        else:
            print("⚠️  Some tests failed. Please review the issues above.")
        
        return self.tests_passed == self.tests_run

def main():
    # Get backend URL from environment
    backend_url = "https://tanseeq-hr-3.preview.emergentagent.com"
    
    print(f"🔧 Backend URL: {backend_url}")
    
    tester = UpdatedAdvancesSystemTester(backend_url)
    success = tester.run_comprehensive_test()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()