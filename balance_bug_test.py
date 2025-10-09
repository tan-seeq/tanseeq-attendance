#!/usr/bin/env python3
"""
URGENT BALANCE CALCULATION BUG INVESTIGATION
Testing the specific bug reported: Expense not being deducted from custody balance when approved

Bug Report:
- Created custody (عهدة) of 100 AED
- Created expense of 30 AED  
- But the remaining custody balance still shows 100 AED instead of 70 AED

Focus Areas:
1. /advances/my-balance endpoint calculations
2. /advances/{transaction_id}/approve endpoint logic
3. Database balance update queries
4. Balance recalculation after approval
"""

import requests
import sys
import json
import os
import tempfile
from datetime import datetime
from typing import Dict, Any, Optional

class BalanceBugTester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        if self.base_url.endswith('/api'):
            self.api_url = self.base_url
        else:
            self.api_url = f"{self.base_url}/api"
        self.tokens = {}
        self.users = {}
        self.test_data = {}
        
        # Test users - using working credentials from previous tests
        self.test_users = {
            'user': {'email': 'tarek.wazzan@tanseeq.com', 'password': 'tarek123'},
            'super_admin': {'email': 'hatem@tan-seeq.co', 'password': 'hatem123'}
        }

    def log_step(self, step: str, success: bool, details: str = "", data: Any = None):
        """Log investigation step"""
        status = "✅" if success else "❌"
        print(f"{status} {step}")
        if details:
            print(f"   📝 {details}")
        if data:
            print(f"   📊 Data: {json.dumps(data, indent=2)}")
        print()

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

    def login_users(self) -> bool:
        """Login required users"""
        print("🔐 STEP 1: Authentication")
        
        for role in ['user', 'super_admin']:
            user_data = self.test_users[role]
            success, response = self.make_request('POST', 'auth/login', user_data)
            
            if success and 'access_token' in response:
                self.tokens[role] = response['access_token']
                self.users[role] = response['user']
                self.log_step(f"Login as {role}", True, f"User: {response['user']['name']}")
            else:
                self.log_step(f"Login as {role}", False, str(response))
                return False
        
        return True

    def get_initial_balance(self) -> bool:
        """Get initial balance for the test user"""
        print("💰 STEP 2: Get Initial Balance")
        
        success, response = self.make_request('GET', 'advances/my-balance', 
                                            token=self.tokens['user'])
        
        if success:
            self.test_data['initial_balance'] = response
            self.log_step("Get initial balance", True, 
                         f"Initial custody: {response.get('remaining_custody', 0)} AED, "
                         f"Initial advance: {response.get('remaining_advance', 0)} AED, "
                         f"Total available: {response.get('total_available', 0)} AED",
                         response)
            return True
        else:
            self.log_step("Get initial balance", False, str(response))
            return False

    def create_custody_transaction(self) -> bool:
        """Create custody transaction of 100 AED (as per bug report)"""
        print("🏦 STEP 3: Create Custody Transaction (100 AED)")
        
        custody_data = {
            "employee_id": self.users['user']['id'],
            "transaction_type": "custody",
            "amount": 100.0,
            "description": "عهدة لتسيل و غيار زيت سياره المكتب",
            "notes": "Testing balance calculation bug - custody creation"
        }
        
        success, response = self.make_request('POST', 'advances/create', custody_data, 
                                            token=self.tokens['super_admin'])
        
        if success and response.get('success'):
            self.test_data['custody_transaction_id'] = response.get('transaction_id')
            self.log_step("Create custody transaction", True, 
                         f"Created custody of 100 AED, Transaction ID: {response.get('transaction_id')}")
            return True
        else:
            self.log_step("Create custody transaction", False, str(response))
            return False

    def verify_balance_after_custody(self) -> bool:
        """Verify balance after custody creation"""
        print("🔍 STEP 4: Verify Balance After Custody Creation")
        
        success, response = self.make_request('GET', 'advances/my-balance', 
                                            token=self.tokens['user'])
        
        if success:
            self.test_data['balance_after_custody'] = response
            initial_custody = self.test_data['initial_balance'].get('remaining_custody', 0)
            current_custody = response.get('remaining_custody', 0)
            expected_custody = initial_custody + 100
            
            balance_correct = abs(current_custody - expected_custody) < 0.01
            
            self.log_step("Verify balance after custody", balance_correct,
                         f"Expected custody: {expected_custody} AED, "
                         f"Actual custody: {current_custody} AED, "
                         f"Difference: {current_custody - expected_custody} AED",
                         response)
            return balance_correct
        else:
            self.log_step("Verify balance after custody", False, str(response))
            return False

    def create_test_invoice_file(self) -> str:
        """Create a test PDF invoice file"""
        temp_file = tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False)
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
(Test Invoice - 30 AED) Tj
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
        return temp_file.name

    def create_expense_transaction(self) -> bool:
        """Create expense transaction of 30 AED (as per bug report)"""
        print("💸 STEP 5: Create Expense Transaction (30 AED)")
        
        temp_file_path = self.create_test_invoice_file()
        
        try:
            form_data = {
                'amount': '30.0',
                'category': 'transportation',
                'description': 'مصروف تسيل و غيار زيت سياره المكتب',
                'expense_date': datetime.now().strftime('%Y-%m-%d'),
                'notes': 'Testing balance calculation bug - expense creation'
            }
            
            with open(temp_file_path, 'rb') as f:
                files = {'invoice_files': ('invoice_30_aed.pdf', f, 'application/pdf')}
                
                success, response = self.make_request('POST', 'advances/expense', 
                                                    data=form_data, files=files,
                                                    token=self.tokens['user'])
            
            if success and response.get('success'):
                self.test_data['expense_transaction_id'] = response.get('transaction_id')
                self.log_step("Create expense transaction", True, 
                             f"Created expense of 30 AED, Transaction ID: {response.get('transaction_id')}")
                return True
            else:
                self.log_step("Create expense transaction", False, str(response))
                return False
                
        finally:
            try:
                os.unlink(temp_file_path)
            except:
                pass

    def verify_balance_after_expense_creation(self) -> bool:
        """Verify balance after expense creation (should be unchanged until approved)"""
        print("🔍 STEP 6: Verify Balance After Expense Creation (Should be Unchanged)")
        
        success, response = self.make_request('GET', 'advances/my-balance', 
                                            token=self.tokens['user'])
        
        if success:
            self.test_data['balance_after_expense_creation'] = response
            custody_after_custody = self.test_data['balance_after_custody'].get('remaining_custody', 0)
            custody_after_expense = response.get('remaining_custody', 0)
            
            # Balance should be unchanged since expense is not approved yet
            balance_unchanged = abs(custody_after_custody - custody_after_expense) < 0.01
            
            self.log_step("Verify balance after expense creation", balance_unchanged,
                         f"Custody after custody creation: {custody_after_custody} AED, "
                         f"Custody after expense creation: {custody_after_expense} AED, "
                         f"Should be unchanged until approval",
                         response)
            return balance_unchanged
        else:
            self.log_step("Verify balance after expense creation", False, str(response))
            return False

    def approve_expense_transaction(self) -> bool:
        """Approve the expense transaction - THIS IS WHERE THE BUG SHOULD BE FIXED"""
        print("✅ STEP 7: Approve Expense Transaction (CRITICAL STEP)")
        
        if 'expense_transaction_id' not in self.test_data:
            self.log_step("Approve expense transaction", False, "No expense transaction ID available")
            return False
        
        approval_data = {
            "status": "approved",
            "notes": "Approved for balance calculation bug testing"
        }
        
        success, response = self.make_request('POST', f'advances/{self.test_data["expense_transaction_id"]}/approve', 
                                            approval_data, token=self.tokens['super_admin'])
        
        if success and response.get('success'):
            self.log_step("Approve expense transaction", True, 
                         f"Approved expense transaction {self.test_data['expense_transaction_id']}")
            return True
        else:
            self.log_step("Approve expense transaction", False, str(response))
            return False

    def verify_balance_after_approval(self) -> bool:
        """Verify balance after expense approval - THIS IS WHERE THE BUG MANIFESTS"""
        print("🚨 STEP 8: Verify Balance After Expense Approval (BUG CHECK)")
        
        success, response = self.make_request('GET', 'advances/my-balance', 
                                            token=self.tokens['user'])
        
        if success:
            self.test_data['balance_after_approval'] = response
            
            # Calculate expected values
            initial_custody = self.test_data['initial_balance'].get('remaining_custody', 0)
            expected_custody_after_approval = initial_custody + 100 - 30  # +100 custody -30 expense
            actual_custody = response.get('remaining_custody', 0)
            
            # Check if bug exists
            bug_exists = abs(actual_custody - (initial_custody + 100)) < 0.01  # Still shows 100 instead of 70
            balance_correct = abs(actual_custody - expected_custody_after_approval) < 0.01
            
            self.log_step("Verify balance after approval", balance_correct,
                         f"Expected custody after approval: {expected_custody_after_approval} AED, "
                         f"Actual custody: {actual_custody} AED, "
                         f"BUG EXISTS: {bug_exists} (balance not deducted), "
                         f"BALANCE CORRECT: {balance_correct}",
                         response)
            
            # Store bug analysis
            self.test_data['bug_analysis'] = {
                'expected_custody': expected_custody_after_approval,
                'actual_custody': actual_custody,
                'bug_exists': bug_exists,
                'balance_correct': balance_correct,
                'difference': actual_custody - expected_custody_after_approval
            }
            
            return balance_correct
        else:
            self.log_step("Verify balance after approval", False, str(response))
            return False

    def check_transaction_history(self) -> bool:
        """Check transaction history to verify all transactions are recorded"""
        print("📋 STEP 9: Check Transaction History")
        
        success, response = self.make_request('GET', 'advances/my-transactions', 
                                            token=self.tokens['user'])
        
        if success and 'transactions' in response:
            transactions = response['transactions']
            
            # Find our test transactions
            custody_found = False
            expense_found = False
            expense_approved = False
            
            for transaction in transactions:
                if transaction.get('id') == self.test_data.get('custody_transaction_id'):
                    custody_found = True
                    self.log_step("Found custody transaction", True, 
                                 f"Amount: {transaction.get('amount')}, Status: {transaction.get('status')}")
                
                if transaction.get('id') == self.test_data.get('expense_transaction_id'):
                    expense_found = True
                    expense_approved = transaction.get('status') == 'approved'
                    self.log_step("Found expense transaction", True, 
                                 f"Amount: {transaction.get('amount')}, Status: {transaction.get('status')}")
            
            all_found = custody_found and expense_found and expense_approved
            self.log_step("Check transaction history", all_found,
                         f"Custody found: {custody_found}, Expense found: {expense_found}, "
                         f"Expense approved: {expense_approved}")
            
            return all_found
        else:
            self.log_step("Check transaction history", False, str(response))
            return False

    def investigate_backend_logs(self) -> bool:
        """Check backend logs for any errors during balance calculation"""
        print("🔍 STEP 10: Backend Log Investigation")
        
        try:
            # Check supervisor logs for backend errors
            import subprocess
            result = subprocess.run(['tail', '-n', '50', '/var/log/supervisor/backend.err.log'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                error_logs = result.stdout
                if error_logs.strip():
                    self.log_step("Backend error logs found", False, 
                                 f"Recent errors:\n{error_logs}")
                    return False
                else:
                    self.log_step("Backend error logs", True, "No recent errors found")
                    return True
            else:
                self.log_step("Backend log check", False, "Could not access backend logs")
                return False
                
        except Exception as e:
            self.log_step("Backend log investigation", False, f"Error checking logs: {str(e)}")
            return False

    def run_balance_bug_investigation(self):
        """Run the complete balance calculation bug investigation"""
        print("🚨 URGENT BALANCE CALCULATION BUG INVESTIGATION")
        print("=" * 80)
        print("Bug Report: Expense not being deducted from custody balance when approved")
        print("Expected: Custody 100 AED - Expense 30 AED = Remaining 70 AED")
        print("Actual: Custody balance still shows 100 AED")
        print("=" * 80)
        
        # Investigation steps
        steps = [
            self.login_users,
            self.get_initial_balance,
            self.create_custody_transaction,
            self.verify_balance_after_custody,
            self.create_expense_transaction,
            self.verify_balance_after_expense_creation,
            self.approve_expense_transaction,
            self.verify_balance_after_approval,
            self.check_transaction_history,
            self.investigate_backend_logs
        ]
        
        results = []
        for step in steps:
            try:
                result = step()
                results.append(result)
                if not result and step.__name__ in ['login_users', 'create_custody_transaction', 'approve_expense_transaction']:
                    print(f"❌ Critical step failed: {step.__name__}. Stopping investigation.")
                    break
            except Exception as e:
                print(f"❌ {step.__name__} failed with exception: {str(e)}")
                results.append(False)
        
        # Final Analysis
        print("\n" + "=" * 80)
        print("🔬 FINAL BUG ANALYSIS")
        print("=" * 80)
        
        if 'bug_analysis' in self.test_data:
            analysis = self.test_data['bug_analysis']
            print(f"Expected custody balance: {analysis['expected_custody']} AED")
            print(f"Actual custody balance: {analysis['actual_custody']} AED")
            print(f"Difference: {analysis['difference']} AED")
            print(f"Bug exists: {'YES' if analysis['bug_exists'] else 'NO'}")
            print(f"Balance calculation correct: {'YES' if analysis['balance_correct'] else 'NO'}")
            
            if analysis['bug_exists']:
                print("\n🚨 BUG CONFIRMED: Expense is not being deducted from custody balance after approval")
                print("🔧 ROOT CAUSE ANALYSIS NEEDED:")
                print("   1. Check update_employee_balance() function in server.py")
                print("   2. Verify /advances/{transaction_id}/approve endpoint logic")
                print("   3. Check database balance update queries")
                print("   4. Verify AdvancesDB.calculate_employee_balance() method")
            else:
                print("\n✅ BUG NOT FOUND: Balance calculation appears to be working correctly")
        
        # Summary
        passed = sum(results)
        total = len(results)
        print(f"\n📊 Investigation Steps: {passed}/{total} successful")
        
        return passed, total, self.test_data.get('bug_analysis', {})

def main():
    # Get backend URL from environment
    backend_url = "https://hr-system-upgrade.preview.emergentagent.com"
    
    print(f"🔧 Backend URL: {backend_url}")
    
    tester = BalanceBugTester(backend_url)
    passed, total, bug_analysis = tester.run_balance_bug_investigation()
    
    # Exit with appropriate code
    if bug_analysis.get('bug_exists', False):
        print("\n🚨 URGENT: Balance calculation bug confirmed. Immediate fix required.")
        sys.exit(2)  # Bug confirmed
    elif bug_analysis.get('balance_correct', False):
        print("\n✅ Balance calculation working correctly. Bug may have been fixed.")
        sys.exit(0)  # Working correctly
    else:
        print("\n⚠️ Investigation incomplete or inconclusive.")
        sys.exit(1)  # Investigation failed

if __name__ == "__main__":
    main()