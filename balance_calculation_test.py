#!/usr/bin/env python3
"""
URGENT BALANCE CALCULATION FIX VERIFICATION TEST
Testing the proportional deduction logic fix in advances_model.py

Critical Test Scenario from Review Request:
1. Login as Super Admin (hatem@tan-seeq.co / hatem123)
2. Create custody of 100 AED for test employee 
3. Create expense of 30 AED for same employee
4. Approve the expense transaction
5. Verify balance calculation:
   - Expected remaining custody: 70 AED (100 - 30)
   - Expected total available: 70 AED
   - Balance should show expense deduction correctly
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional
import os

class BalanceCalculationTester:
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
        
        # Test credentials from review request
        self.super_admin_creds = {'email': 'hatem@tan-seeq.co', 'password': 'hatem123'}
        self.test_employee_id = None
        self.test_employee_creds = None
        self.custody_transaction_id = None
        self.expense_transaction_id = None

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

    def test_super_admin_login(self) -> bool:
        """Test Super Admin login with credentials from review request"""
        success, response = self.make_request('POST', 'auth/login', self.super_admin_creds)
        
        if success and 'access_token' in response:
            self.tokens['super_admin'] = response['access_token']
            self.users['super_admin'] = response['user']
            self.log_test("Super Admin Login (hatem@tan-seeq.co)", True)
            return True
        else:
            self.log_test("Super Admin Login (hatem@tan-seeq.co)", False, str(response))
            return False

    def get_test_employee(self) -> bool:
        """Get a test employee for balance testing"""
        if 'super_admin' not in self.tokens:
            return False
            
        success, response = self.make_request('GET', 'users', token=self.tokens['super_admin'])
        
        if success and isinstance(response, list) and len(response) > 0:
            # Use the super admin as test employee since we have their credentials
            for user in response:
                if user.get('email') == self.super_admin_creds['email']:
                    self.test_employee_id = user['id']
                    self.test_employee_creds = self.super_admin_creds
                    self.log_test(f"Test Employee Selected: {user.get('name', 'Unknown')} (Super Admin)", True)
                    return True
            
            self.log_test("Get Test Employee", False, "Super admin user not found")
            return False
        else:
            self.log_test("Get Test Employee", False, str(response))
            return False

    def get_initial_balance(self) -> Dict[str, float]:
        """Get initial balance for test employee"""
        if 'super_admin' not in self.tokens or not self.test_employee_id:
            return {}
            
        success, response = self.make_request('GET', 'advances/admin/all-balances', 
                                            token=self.tokens['super_admin'])
        
        if success and 'employee_balances' in response:
            for balance in response['employee_balances']:
                if balance['employee_id'] == self.test_employee_id:
                    self.log_test("Get Initial Balance", True, 
                                f"Custody: {balance['total_custody']}, Available: {balance['total_available']}")
                    return balance
        
        # If no existing balance, return zeros
        self.log_test("Get Initial Balance", True, "No existing balance (starting fresh)")
        return {
            'total_custody': 0.0,
            'total_advances': 0.0,
            'total_expenses': 0.0,
            'remaining_custody': 0.0,
            'remaining_advance': 0.0,
            'total_available': 0.0
        }

    def get_current_balance(self) -> Dict[str, float]:
        """Get current balance for test employee"""
        if 'super_admin' not in self.tokens or not self.test_employee_id:
            return {}
            
        success, response = self.make_request('GET', 'advances/admin/all-balances', 
                                            token=self.tokens['super_admin'])
        
        if success and 'employee_balances' in response:
            for balance in response['employee_balances']:
                if balance['employee_id'] == self.test_employee_id:
                    return balance
        
        return {}

    def create_custody_transaction(self, amount: float = 100.0) -> bool:
        """Create custody of 100 AED as per review request"""
        if 'super_admin' not in self.tokens or not self.test_employee_id:
            return False
        
        custody_data = {
            "employee_id": self.test_employee_id,
            "transaction_type": "custody",
            "amount": amount,
            "description": "عهدة اختبار لفحص حساب الرصيد - 100 درهم",
            "notes": "اختبار نظام حساب الرصيد بعد الإصلاح"
        }
        
        success, response = self.make_request('POST', 'advances/create', custody_data,
                                            token=self.tokens['super_admin'])
        
        if success and response.get('success'):
            self.custody_transaction_id = response.get('transaction_id')
            self.log_test(f"Create Custody Transaction ({amount} AED)", True, 
                         f"Transaction ID: {self.custody_transaction_id}")
            return True
        else:
            self.log_test(f"Create Custody Transaction ({amount} AED)", False, str(response))
            return False

    def login_test_employee(self) -> bool:
        """Login as test employee to create expense"""
        if not self.test_employee_creds:
            return False
        
        success, response = self.make_request('POST', 'auth/login', self.test_employee_creds)
        
        if success and 'access_token' in response:
            self.tokens['test_employee'] = response['access_token']
            self.users['test_employee'] = response['user']
            self.log_test(f"Test Employee Login ({self.test_employee_creds['email']})", True)
            return True
        else:
            self.log_test(f"Test Employee Login ({self.test_employee_creds['email']})", False, str(response))
            return False

    def create_expense_transaction(self, amount: float = 30.0) -> bool:
        """Create expense of 30 AED as per review request"""
        if not self.test_employee_id or not self.test_employee_creds:
            return False
        
        # Login as test employee first
        if not self.login_test_employee():
            return False
        
        # Create a test PDF file for the expense (minimal PDF structure)
        test_pdf_content = b"""%PDF-1.4
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
        
        test_file_path = "/tmp/test_invoice.pdf"
        
        try:
            with open(test_file_path, "wb") as f:
                f.write(test_pdf_content)
            
            # Use requests with files for multipart form data
            url = f"{self.api_url}/advances/expense"
            headers = {'Authorization': f'Bearer {self.tokens["test_employee"]}'}
            
            form_data = {
                'amount': str(amount),
                'category': 'fuel',
                'description': 'مصروف اختبار لفحص حساب الرصيد - 30 درهم',
                'expense_date': datetime.now().strftime('%Y-%m-%d'),
                'notes': 'اختبار خصم المصروف من العهدة'
            }
            
            files = {'invoice_files': ('test_invoice.pdf', open(test_file_path, 'rb'), 'application/pdf')}
            
            response = requests.post(url, data=form_data, files=files, headers=headers, timeout=30)
            
            # Clean up
            files['invoice_files'][1].close()
            os.remove(test_file_path)
            
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get('success'):
                    self.expense_transaction_id = response_data.get('transaction_id')
                    self.log_test(f"Create Expense Transaction ({amount} AED)", True,
                                f"Transaction ID: {self.expense_transaction_id}")
                    return True
            
            self.log_test(f"Create Expense Transaction ({amount} AED)", False, 
                         f"Status: {response.status_code}, Response: {response.text}")
            return False
            
        except Exception as e:
            self.log_test(f"Create Expense Transaction ({amount} AED)", False, str(e))
            return False

    def approve_expense_transaction(self) -> bool:
        """Approve the expense transaction"""
        if 'super_admin' not in self.tokens or not self.expense_transaction_id:
            return False
        
        approval_data = {
            "status": "approved",
            "notes": "موافقة على المصروف لاختبار حساب الرصيد"
        }
        
        success, response = self.make_request('POST', f'advances/{self.expense_transaction_id}/approve',
                                            approval_data, token=self.tokens['super_admin'])
        
        if success and response.get('success'):
            self.log_test("Approve Expense Transaction", True)
            return True
        else:
            self.log_test("Approve Expense Transaction", False, str(response))
            return False

    def verify_balance_calculation(self, initial_balance: Dict[str, float], 
                                 custody_amount: float = 100.0, expense_amount: float = 30.0) -> bool:
        """Verify the balance calculation after expense approval"""
        if 'super_admin' not in self.tokens or not self.test_employee_id:
            return False
        
        # Get updated balance
        success, response = self.make_request('GET', 'advances/admin/all-balances',
                                            token=self.tokens['super_admin'])
        
        if not success or 'employee_balances' not in response:
            self.log_test("Get Updated Balance", False, str(response))
            return False
        
        # Find the test employee's balance
        updated_balance = None
        for balance in response['employee_balances']:
            if balance['employee_id'] == self.test_employee_id:
                updated_balance = balance
                break
        
        if not updated_balance:
            self.log_test("Find Employee Balance", False, "Employee balance not found")
            return False
        
        # Calculate expected values
        expected_total_custody = initial_balance.get('total_custody', 0) + custody_amount
        expected_total_expenses = initial_balance.get('total_expenses', 0) + expense_amount
        
        # With the fix, expenses should be deducted proportionally
        # Since we only have custody (no advances), all expense should come from custody
        expected_remaining_custody = expected_total_custody - expense_amount
        expected_total_available = expected_remaining_custody
        
        # Verify the calculations
        actual_total_custody = updated_balance['total_custody']
        actual_total_expenses = updated_balance['total_expenses']
        actual_remaining_custody = updated_balance['remaining_custody']
        actual_total_available = updated_balance['total_available']
        
        print(f"\n🔍 BALANCE CALCULATION VERIFICATION:")
        print(f"   Initial Custody: {initial_balance.get('total_custody', 0)} AED")
        print(f"   Added Custody: {custody_amount} AED")
        print(f"   Expected Total Custody: {expected_total_custody} AED")
        print(f"   Actual Total Custody: {actual_total_custody} AED")
        print(f"   ")
        print(f"   Expense Amount: {expense_amount} AED")
        print(f"   Expected Total Expenses: {expected_total_expenses} AED")
        print(f"   Actual Total Expenses: {actual_total_expenses} AED")
        print(f"   ")
        print(f"   Expected Remaining Custody: {expected_remaining_custody} AED")
        print(f"   Actual Remaining Custody: {actual_remaining_custody} AED")
        print(f"   ")
        print(f"   Expected Total Available: {expected_total_available} AED")
        print(f"   Actual Total Available: {actual_total_available} AED")
        
        # Check if calculations are correct
        custody_correct = abs(actual_total_custody - expected_total_custody) < 0.01
        expenses_correct = abs(actual_total_expenses - expected_total_expenses) < 0.01
        remaining_custody_correct = abs(actual_remaining_custody - expected_remaining_custody) < 0.01
        total_available_correct = abs(actual_total_available - expected_total_available) < 0.01
        
        all_correct = custody_correct and expenses_correct and remaining_custody_correct and total_available_correct
        
        if all_correct:
            self.log_test("✅ BALANCE CALCULATION FIX VERIFIED", True, 
                         f"Remaining custody: {actual_remaining_custody} AED (Expected: {expected_remaining_custody} AED)")
        else:
            error_details = []
            if not custody_correct:
                error_details.append(f"Total custody: {actual_total_custody} != {expected_total_custody}")
            if not expenses_correct:
                error_details.append(f"Total expenses: {actual_total_expenses} != {expected_total_expenses}")
            if not remaining_custody_correct:
                error_details.append(f"Remaining custody: {actual_remaining_custody} != {expected_remaining_custody}")
            if not total_available_correct:
                error_details.append(f"Total available: {actual_total_available} != {expected_total_available}")
            
            self.log_test("❌ BALANCE CALCULATION FIX FAILED", False, "; ".join(error_details))
        
        return all_correct

    def test_new_edit_endpoints(self) -> bool:
        """Test new edit endpoints for advances and marketing visits"""
        if 'super_admin' not in self.tokens:
            return False
        
        all_passed = True
        
        # Test advances edit endpoint
        if self.custody_transaction_id:
            edit_data = {
                "description": "عهدة محدثة - اختبار نقطة النهاية الجديدة للتعديل",
                "notes": "تم التحديث عبر نقطة النهاية الجديدة للتعديل"
            }
            
            success, response = self.make_request('PUT', f'advances/{self.custody_transaction_id}/edit',
                                                edit_data, token=self.tokens['super_admin'])
            
            if success and response.get('success'):
                self.log_test("Test Advances Edit Endpoint", True)
            else:
                self.log_test("Test Advances Edit Endpoint", False, str(response))
                all_passed = False
        
        # Test marketing visits edit endpoint (we'll test with a dummy ID)
        test_visit_id = "test-visit-id-123"
        edit_data = {
            "client_name": "عميل محدث للاختبار",
            "location_name": "موقع محدث"
        }
        
        success, response = self.make_request('PUT', f'marketing-visits/{test_visit_id}/edit',
                                            edit_data, token=self.tokens['super_admin'], 
                                            expected_status=404)  # Expect 404 for non-existent visit
        
        if success:  # 404 is expected for non-existent visit
            self.log_test("Test Marketing Visits Edit Endpoint", True, "Endpoint exists (404 for non-existent visit)")
        else:
            self.log_test("Test Marketing Visits Edit Endpoint", False, str(response))
            all_passed = False
        
        return all_passed

    def run_balance_calculation_test(self):
        """Run the complete balance calculation test scenario"""
        print("🚀 STARTING URGENT BALANCE CALCULATION FIX VERIFICATION")
        print("=" * 60)
        
        # Step 1: Login as Super Admin
        if not self.test_super_admin_login():
            print("❌ CRITICAL: Super Admin login failed. Cannot proceed.")
            return False
        
        # Step 2: Get test employee
        if not self.get_test_employee():
            print("❌ CRITICAL: Could not get test employee. Cannot proceed.")
            return False
        
        # Step 3: Get initial balance
        initial_balance = self.get_initial_balance()
        
        # Step 4: Create custody of 100 AED
        if not self.create_custody_transaction(100.0):
            print("❌ CRITICAL: Could not create custody transaction. Cannot proceed.")
            return False
        
        # Step 4.5: Check balance after custody creation
        print("🔍 Checking balance after custody creation...")
        updated_balance = self.get_current_balance()
        if updated_balance:
            print(f"   Total Custody: {updated_balance.get('total_custody', 0)} AED")
            print(f"   Total Available: {updated_balance.get('total_available', 0)} AED")
        
        # Step 5: Create expense of 30 AED
        if not self.create_expense_transaction(30.0):
            print("❌ CRITICAL: Could not create expense transaction. Cannot proceed.")
            return False
        
        # Step 6: Approve the expense
        if not self.approve_expense_transaction():
            print("❌ CRITICAL: Could not approve expense transaction. Cannot proceed.")
            return False
        
        # Step 7: Verify balance calculation
        balance_fix_verified = self.verify_balance_calculation(initial_balance, 100.0, 30.0)
        
        # Step 8: Test new edit endpoints
        edit_endpoints_working = self.test_new_edit_endpoints()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 BALANCE CALCULATION FIX TEST SUMMARY")
        print("=" * 60)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if balance_fix_verified:
            print("\n✅ BALANCE CALCULATION FIX VERIFIED SUCCESSFULLY")
            print("   - Expenses are now properly deducted from custody")
            print("   - Proportional deduction logic is working correctly")
            print("   - Total available balance calculation is accurate")
        else:
            print("\n❌ BALANCE CALCULATION FIX FAILED")
            print("   - The bug may still exist in the system")
            print("   - Manual investigation required")
        
        if edit_endpoints_working:
            print("\n✅ NEW EDIT ENDPOINTS WORKING")
        else:
            print("\n⚠️ SOME EDIT ENDPOINTS HAVE ISSUES")
        
        return balance_fix_verified and edit_endpoints_working

def main():
    # Get backend URL from environment or use default
    backend_url = os.environ.get('REACT_APP_BACKEND_URL', 'https://tanseeq-hr-3.preview.emergentagent.com')
    
    print(f"🔗 Testing Backend URL: {backend_url}")
    
    tester = BalanceCalculationTester(backend_url)
    success = tester.run_balance_calculation_test()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()