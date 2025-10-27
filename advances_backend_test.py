#!/usr/bin/env python3
"""
TANSEEQ HR System - Advances and Loans Management System Backend Testing
Comprehensive testing of all 8 API endpoints with authentication and role-based access control
"""

import requests
import sys
import json
import os
import tempfile
from datetime import datetime
from typing import Dict, Any, Optional
from io import BytesIO

class AdvancesAPITester:
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
        self.created_transactions = []  # Track created transactions for cleanup
        
        # Test users (working credentials found)
        self.test_users = {
            'user': {'email': 'tarek.wazzan@tanseeq.com', 'password': 'tarek123'},
            'admin': {'email': 'admin@tanseeq.com', 'password': 'admin123'},
            'super_admin': {'email': 'hatem@tan-seeq.co', 'password': 'hatem123'}
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
        
        # Don't set Content-Type for multipart/form-data (files)
        if not files:
            headers['Content-Type'] = 'application/json'
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method.upper() == 'POST':
                if files:
                    response = requests.post(url, data=data, files=files, headers={k: v for k, v in headers.items() if k != 'Content-Type'}, timeout=30)
                else:
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

    def create_test_file(self, filename: str, content: str = "Test invoice content") -> tuple:
        """Create a temporary test file for upload"""
        if filename.endswith('.pdf'):
            # Create a simple PDF file
            temp_file = tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False)
            # Simple PDF content (minimal valid PDF)
            pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test Invoice) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
300
%%EOF"""
            temp_file.write(pdf_content)
            temp_file.close()
            return temp_file.name, filename
        else:
            # Create a text file for other cases
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
            temp_file.write(content)
            temp_file.close()
            return temp_file.name, filename

    def test_create_advance_super_admin_only(self) -> bool:
        """Test POST /api/advances/create - Super Admin Only"""
        print("\n=== Testing Advance/Custody Creation (Super Admin Only) ===")
        
        # Test with Super Admin (should work)
        if 'super_admin' not in self.tokens:
            self.log_test("Create advance (Super Admin)", False, "Super admin not logged in")
            return False
        
        advance_data = {
            "employee_id": self.users['user']['id'],
            "transaction_type": "advance",
            "amount": 1000.0,
            "description": "Test advance for employee",
            "notes": "Testing advance creation"
        }
        
        success, response = self.make_request('POST', 'advances/create', advance_data, 
                                            token=self.tokens['super_admin'])
        
        if success and response.get('success'):
            self.created_transactions.append(response.get('transaction_id'))
            self.log_test("Create advance (Super Admin)", True)
            advance_success = True
        else:
            self.log_test("Create advance (Super Admin)", False, str(response))
            advance_success = False
        
        # Test with regular user (should fail with 403)
        if 'user' in self.tokens:
            success, response = self.make_request('POST', 'advances/create', advance_data, 
                                                token=self.tokens['user'], expected_status=403)
            self.log_test("Create advance (User - should fail)", success, 
                         "Expected 403 but got different status" if not success else "")
        
        # Test with admin (should fail with 403)
        if 'admin' in self.tokens:
            success, response = self.make_request('POST', 'advances/create', advance_data, 
                                                token=self.tokens['admin'], expected_status=403)
            self.log_test("Create advance (Admin - should fail)", success,
                         "Expected 403 but got different status" if not success else "")
        
        return advance_success

    def test_create_custody_super_admin_only(self) -> bool:
        """Test POST /api/advances/create with custody type"""
        print("\n=== Testing Custody Creation (Super Admin Only) ===")
        
        if 'super_admin' not in self.tokens:
            self.log_test("Create custody (Super Admin)", False, "Super admin not logged in")
            return False
        
        custody_data = {
            "employee_id": self.users['user']['id'],
            "transaction_type": "custody",
            "amount": 500.0,
            "description": "Test custody for employee",
            "notes": "Testing custody creation"
        }
        
        success, response = self.make_request('POST', 'advances/create', custody_data, 
                                            token=self.tokens['super_admin'])
        
        if success and response.get('success'):
            self.created_transactions.append(response.get('transaction_id'))
            self.log_test("Create custody (Super Admin)", True)
            return True
        else:
            self.log_test("Create custody (Super Admin)", False, str(response))
            return False

    def test_expense_with_file_upload(self) -> bool:
        """Test POST /api/advances/expense - Submit expense with invoice upload"""
        print("\n=== Testing Expense Submission with File Upload ===")
        
        if 'user' not in self.tokens:
            self.log_test("Submit expense with file", False, "User not logged in")
            return False
        
        # Create a test PDF file
        temp_file_path, original_filename = self.create_test_file("test_invoice.pdf", "Test invoice content for expense")
        
        try:
            # Prepare form data
            form_data = {
                'amount': '100.0',
                'category': 'transportation',
                'description': 'Test expense with invoice upload',
                'expense_date': '2024-01-15',
                'notes': 'Testing file upload functionality'
            }
            
            # Prepare file
            with open(temp_file_path, 'rb') as f:
                files = {'invoice_files': (original_filename, f, 'application/pdf')}
                
                success, response = self.make_request('POST', 'advances/expense', 
                                                    data=form_data, files=files,
                                                    token=self.tokens['user'])
            
            if success and response.get('success'):
                self.created_transactions.append(response.get('transaction_id'))
                self.log_test("Submit expense with file upload", True)
                return True
            else:
                self.log_test("Submit expense with file upload", False, str(response))
                return False
                
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_file_path)
            except:
                pass

    def test_expense_validation(self) -> bool:
        """Test expense validation (missing files, invalid data)"""
        print("\n=== Testing Expense Validation ===")
        
        if 'user' not in self.tokens:
            self.log_test("Expense validation", False, "User not logged in")
            return False
        
        # Test without files (should fail)
        form_data = {
            'amount': '100.0',
            'category': 'transportation',
            'description': 'Test',  # Too short
            'expense_date': '2024-01-15'
        }
        
        success, response = self.make_request('POST', 'advances/expense', 
                                            data=form_data, files={},
                                            token=self.tokens['user'], expected_status=422)
        
        validation_success = success  # Should fail with 422
        self.log_test("Expense validation (no files)", validation_success,
                     "Expected 422 but got different status" if not validation_success else "")
        
        return validation_success

    def test_my_balance(self) -> bool:
        """Test GET /api/advances/my-balance - Get personal balance"""
        print("\n=== Testing Personal Balance Retrieval ===")
        
        results = []
        
        for role in ['user', 'admin', 'super_admin']:
            if role not in self.tokens:
                continue
                
            success, response = self.make_request('GET', 'advances/my-balance', 
                                                token=self.tokens[role])
            
            if success and 'employee_name' in response:
                self.log_test(f"Get my balance ({role})", True)
                results.append(True)
            else:
                self.log_test(f"Get my balance ({role})", False, str(response))
                results.append(False)
        
        return any(results)

    def test_my_transactions(self) -> bool:
        """Test GET /api/advances/my-transactions - Get personal transaction history"""
        print("\n=== Testing Personal Transaction History ===")
        
        results = []
        
        for role in ['user', 'admin', 'super_admin']:
            if role not in self.tokens:
                continue
                
            success, response = self.make_request('GET', 'advances/my-transactions', 
                                                token=self.tokens[role])
            
            if success and 'transactions' in response:
                self.log_test(f"Get my transactions ({role})", True)
                results.append(True)
            else:
                self.log_test(f"Get my transactions ({role})", False, str(response))
                results.append(False)
        
        return any(results)

    def test_admin_all_balances(self) -> bool:
        """Test GET /api/advances/admin/all-balances - Get all employee balances (Super Admin only)"""
        print("\n=== Testing All Employee Balances (Super Admin Only) ===")
        
        # Test with Super Admin (should work)
        if 'super_admin' not in self.tokens:
            self.log_test("Get all balances (Super Admin)", False, "Super admin not logged in")
            return False
        
        success, response = self.make_request('GET', 'advances/admin/all-balances', 
                                            token=self.tokens['super_admin'])
        
        if success and 'employee_balances' in response:
            self.log_test("Get all balances (Super Admin)", True)
            admin_success = True
        else:
            self.log_test("Get all balances (Super Admin)", False, str(response))
            admin_success = False
        
        # Test with regular user (should fail with 403)
        if 'user' in self.tokens:
            success, response = self.make_request('GET', 'advances/admin/all-balances', 
                                                token=self.tokens['user'], expected_status=403)
            self.log_test("Get all balances (User - should fail)", success,
                         "Expected 403 but got different status" if not success else "")
        
        # Test with admin (should fail with 403)
        if 'admin' in self.tokens:
            success, response = self.make_request('GET', 'advances/admin/all-balances', 
                                                token=self.tokens['admin'], expected_status=403)
            self.log_test("Get all balances (Admin - should fail)", success,
                         "Expected 403 but got different status" if not success else "")
        
        return admin_success

    def test_pending_approvals(self) -> bool:
        """Test GET /api/advances/admin/pending-approvals - Get pending expense approvals (Super Admin only)"""
        print("\n=== Testing Pending Approvals (Super Admin Only) ===")
        
        # Test with Super Admin (should work)
        if 'super_admin' not in self.tokens:
            self.log_test("Get pending approvals (Super Admin)", False, "Super admin not logged in")
            return False
        
        success, response = self.make_request('GET', 'advances/admin/pending-approvals', 
                                            token=self.tokens['super_admin'])
        
        if success and 'pending_transactions' in response:
            self.log_test("Get pending approvals (Super Admin)", True)
            admin_success = True
        else:
            self.log_test("Get pending approvals (Super Admin)", False, str(response))
            admin_success = False
        
        # Test with regular user (should fail with 403)
        if 'user' in self.tokens:
            success, response = self.make_request('GET', 'advances/admin/pending-approvals', 
                                                token=self.tokens['user'], expected_status=403)
            self.log_test("Get pending approvals (User - should fail)", success,
                         "Expected 403 but got different status" if not success else "")
        
        return admin_success

    def test_approve_transaction(self) -> bool:
        """Test POST /api/advances/{transaction_id}/approve - Approve/reject transactions"""
        print("\n=== Testing Transaction Approval/Rejection ===")
        
        if 'super_admin' not in self.tokens or 'user' not in self.tokens:
            self.log_test("Approve transaction", False, "Required users not logged in")
            return False
        
        # First, create an expense to have something to approve
        temp_file_path, original_filename = self.create_test_file("approval_test_invoice.pdf")
        
        try:
            form_data = {
                'amount': '200.0',
                'category': 'meals',
                'description': 'Test expense for approval testing',
                'expense_date': '2024-01-20',
                'notes': 'Created for approval testing'
            }
            
            with open(temp_file_path, 'rb') as f:
                files = {'invoice_files': (original_filename, f, 'application/pdf')}
                
                expense_success, expense_response = self.make_request('POST', 'advances/expense', 
                                                                    data=form_data, files=files,
                                                                    token=self.tokens['user'])
            
            if not expense_success:
                self.log_test("Approve transaction (create expense first)", False, str(expense_response))
                return False
                
        finally:
            try:
                os.unlink(temp_file_path)
            except:
                pass
        
        # Now get pending transactions to find one to approve
        success, response = self.make_request('GET', 'advances/admin/pending-approvals', 
                                            token=self.tokens['super_admin'])
        
        if not success or not response.get('pending_transactions'):
            self.log_test("Approve transaction", False, "No pending transactions found even after creating one")
            return False
        
        # Get the first pending transaction
        pending_transaction = response['pending_transactions'][0]
        transaction_id = pending_transaction['id']
        
        # Test approval
        approval_data = {
            "status": "approved",
            "notes": "Approved for testing purposes"
        }
        
        success, response = self.make_request('POST', f'advances/{transaction_id}/approve', 
                                            approval_data, token=self.tokens['super_admin'])
        
        if success and response.get('success'):
            self.log_test("Approve transaction (Super Admin)", True)
            approval_success = True
        else:
            self.log_test("Approve transaction (Super Admin)", False, str(response))
            approval_success = False
        
        # Test with regular user (should fail with 403)
        if 'user' in self.tokens and len(response.get('pending_transactions', [])) > 1:
            next_transaction_id = response['pending_transactions'][1]['id']
            success, response = self.make_request('POST', f'advances/{next_transaction_id}/approve', 
                                                approval_data, token=self.tokens['user'], 
                                                expected_status=403)
            self.log_test("Approve transaction (User - should fail)", success,
                         "Expected 403 but got different status" if not success else "")
        
        return approval_success

    def test_view_attachment(self) -> bool:
        """Test GET /api/advances/attachment/{transaction_id}/{attachment_id} - View attachment"""
        print("\n=== Testing Attachment Viewing ===")
        
        if 'user' not in self.tokens:
            self.log_test("View attachment", False, "User not logged in")
            return False
        
        # Get user's transactions to find one with attachments
        success, response = self.make_request('GET', 'advances/my-transactions', 
                                            token=self.tokens['user'])
        
        if not success or not response.get('transactions'):
            self.log_test("View attachment", False, "No transactions found to test attachment viewing")
            return False
        
        # Find a transaction with attachments
        transaction_with_attachment = None
        for transaction in response['transactions']:
            if transaction.get('attachments') and len(transaction['attachments']) > 0:
                transaction_with_attachment = transaction
                break
        
        if not transaction_with_attachment:
            self.log_test("View attachment", False, "No transactions with attachments found")
            return False
        
        transaction_id = transaction_with_attachment['id']
        attachment_id = transaction_with_attachment['attachments'][0]['id']
        
        # Test viewing attachment
        success, response = self.make_request('GET', f'advances/attachment/{transaction_id}/{attachment_id}', 
                                            token=self.tokens['user'])
        
        # For file responses, we expect different handling
        if success or response.get('status_code') == 200:
            self.log_test("View attachment", True)
            return True
        else:
            self.log_test("View attachment", False, str(response))
            return False

    def test_balance_calculation_logic(self) -> bool:
        """Test balance calculation logic"""
        print("\n=== Testing Balance Calculation Logic ===")
        
        if 'user' not in self.tokens:
            self.log_test("Balance calculation", False, "User not logged in")
            return False
        
        # Get current balance
        success, response = self.make_request('GET', 'advances/my-balance', 
                                            token=self.tokens['user'])
        
        if success:
            balance = response
            # Verify balance fields
            required_fields = ['total_advances', 'total_custody', 'total_expenses', 
                             'remaining_advance', 'remaining_custody', 'total_available']
            
            has_all_fields = all(field in balance for field in required_fields)
            
            # Verify calculation logic
            calculated_total = balance.get('remaining_advance', 0) + balance.get('remaining_custody', 0)
            reported_total = balance.get('total_available', 0)
            calculation_correct = abs(calculated_total - reported_total) < 0.01  # Allow for floating point precision
            
            overall_success = has_all_fields and calculation_correct
            
            self.log_test("Balance calculation logic", overall_success,
                         f"Missing fields: {set(required_fields) - set(balance.keys())}" if not has_all_fields 
                         else f"Calculation mismatch: {calculated_total} vs {reported_total}" if not calculation_correct
                         else "")
            return overall_success
        else:
            self.log_test("Balance calculation logic", False, str(response))
            return False

    def run_comprehensive_test(self):
        """Run all tests"""
        print("🚀 Starting Comprehensive Advances and Loans Management System Backend Testing")
        print(f"🌐 Testing against: {self.api_url}")
        print("=" * 80)
        
        # Login all users
        print("\n=== Authentication Testing ===")
        for role in ['user', 'admin', 'super_admin']:
            self.test_login(role)
        
        if not any(self.tokens.values()):
            print("❌ No successful logins. Cannot proceed with testing.")
            return
        
        # Test all endpoints
        test_methods = [
            self.test_create_advance_super_admin_only,
            self.test_create_custody_super_admin_only,
            self.test_expense_with_file_upload,
            self.test_expense_validation,
            self.test_my_balance,
            self.test_my_transactions,
            self.test_admin_all_balances,
            self.test_pending_approvals,
            self.test_approve_transaction,
            self.test_view_attachment,
            self.test_balance_calculation_logic
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                print(f"❌ {test_method.__name__} failed with exception: {str(e)}")
        
        # Summary
        print("\n" + "=" * 80)
        print(f"📊 TEST SUMMARY")
        print(f"✅ Passed: {self.tests_passed}/{self.tests_run}")
        print(f"❌ Failed: {self.tests_run - self.tests_passed}/{self.tests_run}")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%" if self.tests_run > 0 else "No tests run")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED! Advances and Loans Management System is working correctly.")
        else:
            print("⚠️  Some tests failed. Please review the issues above.")
        
        return self.tests_passed == self.tests_run

def main():
    # Get backend URL from environment or use default
    backend_url = "https://hr-attendance-system.preview.emergentagent.com"
    
    print(f"🔧 Backend URL: {backend_url}")
    
    tester = AdvancesAPITester(backend_url)
    success = tester.run_comprehensive_test()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()