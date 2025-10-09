#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Integrated Payroll & Deductions System
Testing Arabic Review Request Requirements:
- Payroll cycles management (create, lock, unlock)
- Installment schedules for advances
- Salary calculations and summaries
- Employee payroll history
- Role-based access control
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
import sys
import os

# Backend URL from frontend .env
BACKEND_URL = "https://tanseeq-hr-fix.preview.emergentagent.com"

# Test credentials from review request
SUPER_ADMIN_CREDENTIALS = {
    "email": "hatem@tan-seeq.co",
    "password": "hatem123"
}

REGULAR_USER_CREDENTIALS = {
    "email": "jihad@tanseeq.com", 
    "password": "jihad123"
}

class PayrollSystemTester:
    def __init__(self):
        self.session = None
        self.super_admin_token = None
        self.regular_user_token = None
        self.test_results = []
        self.created_cycle_id = None
        self.test_advance_id = None
        
    async def setup_session(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'Content-Type': 'application/json'}
        )
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
            
    async def authenticate_user(self, credentials, user_type):
        """Authenticate user and get JWT token"""
        try:
            async with self.session.post(
                f"{BACKEND_URL}/api/auth/login",
                json=credentials
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    token = data.get('access_token')
                    user_info = data.get('user', {})
                    self.log_result(f"✅ {user_type} Authentication", True, 
                                  f"Login successful for {credentials['email']}, Role: {user_info.get('role', 'unknown')}")
                    return token
                else:
                    error_text = await response.text()
                    self.log_result(f"❌ {user_type} Authentication", False, 
                                  f"Login failed: {response.status} - {error_text}")
                    return None
        except Exception as e:
            self.log_result(f"❌ {user_type} Authentication", False, f"Exception: {str(e)}")
            return None
            
    async def make_authenticated_request(self, method, endpoint, token, data=None, params=None):
        """Make authenticated API request"""
        headers = {'Authorization': f'Bearer {token}'}
        if data:
            headers['Content-Type'] = 'application/json'
            
        try:
            async with self.session.request(
                method, 
                f"{BACKEND_URL}{endpoint}",
                headers=headers,
                json=data,
                params=params
            ) as response:
                response_text = await response.text()
                try:
                    response_data = json.loads(response_text) if response_text else {}
                except:
                    response_data = {"raw_response": response_text}
                    
                return response.status, response_data
        except Exception as e:
            return 500, {"error": str(e)}
            
    def log_result(self, test_name, success, details):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        print(f"   Details: {details}")
        print()
        
    async def test_payroll_cycle_creation(self):
        """Test POST /api/payroll/cycles - Create new payroll cycle (Super Admin)"""
        test_name = "Payroll Cycle Creation (Super Admin)"
        
        # Test data for October 2025 as requested in review
        cycle_data = {
            "month": "2025-10",
            "display_name": "دورة راتب أكتوبر 2025",
            "description": "دورة راتب أكتوبر 2025 - اختبار النظام المتكامل",
            "notes": "دورة اختبار للنظام المتكامل للرواتب والخصومات والسلف"
        }
        
        status, response = await self.make_authenticated_request(
            "POST", "/api/payroll/cycles", self.super_admin_token, cycle_data
        )
        
        if status == 201 and response.get("success"):
            self.created_cycle_id = response.get("cycle_id")
            self.log_result(test_name, True, 
                          f"Cycle created successfully for {cycle_data['month']}, ID: {self.created_cycle_id}")
        elif status == 400 and "already exists" in str(response):
            # Cycle already exists, try to get existing one
            status, cycles_response = await self.make_authenticated_request(
                "GET", "/api/payroll/cycles", self.super_admin_token, params={"month": "2025-10"}
            )
            if status == 200 and cycles_response.get("cycles"):
                self.created_cycle_id = cycles_response["cycles"][0].get("id")
                self.log_result(test_name, True, 
                              f"Using existing cycle for {cycle_data['month']}, ID: {self.created_cycle_id}")
            else:
                self.log_result(test_name, False, f"Failed to create or find cycle: {status} - {response}")
        else:
            self.log_result(test_name, False, f"Failed to create cycle: {status} - {response}")
            
    async def test_payroll_cycles_retrieval(self):
        """Test GET /api/payroll/cycles - Get payroll cycles with filtering"""
        test_name = "Payroll Cycles Retrieval"
        
        status, response = await self.make_authenticated_request(
            "GET", "/api/payroll/cycles", self.super_admin_token
        )
        
        if status == 200 and "cycles" in response:
            cycles_count = len(response["cycles"])
            self.log_result(test_name, True, 
                          f"Retrieved {cycles_count} payroll cycles successfully")
        else:
            self.log_result(test_name, False, f"Failed to retrieve cycles: {status} - {response}")
            
    async def test_payroll_cycle_lock(self):
        """Test POST /api/payroll/cycles/{id}/lock - Lock payroll cycle"""
        test_name = "Payroll Cycle Lock"
        
        if not self.created_cycle_id:
            self.log_result(test_name, False, "No cycle ID available for testing")
            return
            
        lock_data = {
            "lock_reason": "اختبار قفل دورة الراتب للمراجعة النهائية"
        }
        
        status, response = await self.make_authenticated_request(
            "POST", f"/api/payroll/cycles/{self.created_cycle_id}/lock", 
            self.super_admin_token, lock_data
        )
        
        if status == 200 and response.get("success"):
            self.log_result(test_name, True, 
                          f"Cycle locked successfully: {response.get('message', 'No message')}")
        else:
            self.log_result(test_name, False, f"Failed to lock cycle: {status} - {response}")
            
    async def test_payroll_cycle_unlock(self):
        """Test POST /api/payroll/cycles/{id}/unlock - Unlock locked payroll cycle"""
        test_name = "Payroll Cycle Unlock"
        
        if not self.created_cycle_id:
            self.log_result(test_name, False, "No cycle ID available for testing")
            return
            
        unlock_data = {
            "unlock_reason": "إعادة فتح الدورة لإضافة تعديلات إضافية"
        }
        
        status, response = await self.make_authenticated_request(
            "POST", f"/api/payroll/cycles/{self.created_cycle_id}/unlock", 
            self.super_admin_token, unlock_data
        )
        
        if status == 200 and response.get("success"):
            self.log_result(test_name, True, 
                          f"Cycle unlocked successfully: {response.get('message', 'No message')}")
        else:
            self.log_result(test_name, False, f"Failed to unlock cycle: {status} - {response}")
            
    async def test_advance_installments_creation(self):
        """Test POST /api/advances/{id}/installments - Create installment schedule for advance"""
        test_name = "Advance Installments Creation"
        
        # First, try to find an existing advance to create installments for
        status, advances_response = await self.make_authenticated_request(
            "GET", "/api/advances/admin/all-transactions", self.super_admin_token,
            params={"transaction_type": "advance", "limit": 10}
        )
        
        if status == 200 and advances_response.get("transactions"):
            # Find an advance transaction
            advance_transaction = None
            for transaction in advances_response["transactions"]:
                if transaction.get("transaction_type") == "advance":
                    advance_transaction = transaction
                    break
                    
            if advance_transaction:
                self.test_advance_id = advance_transaction["id"]
                
                installment_data = {
                    "number_of_installments": 6,
                    "start_month": "2025-11",
                    "installment_amount": round(advance_transaction["amount"] / 6, 2),
                    "notes": "جدولة أقساط شهرية للسلفة"
                }
                
                status, response = await self.make_authenticated_request(
                    "POST", f"/api/advances/{self.test_advance_id}/installments", 
                    self.super_admin_token, installment_data
                )
                
                if status == 201 and response.get("success"):
                    self.log_result(test_name, True, 
                                  f"Installments created: {installment_data['number_of_installments']} installments of {installment_data['installment_amount']} AED")
                else:
                    self.log_result(test_name, False, f"Failed to create installments: {status} - {response}")
            else:
                self.log_result(test_name, False, "No advance transactions found to create installments for")
        else:
            self.log_result(test_name, False, f"Failed to retrieve advances: {status} - {advances_response}")
            
    async def test_advance_installments_retrieval(self):
        """Test GET /api/advances/{id}/installments - Get advance installment schedule"""
        test_name = "Advance Installments Retrieval"
        
        if not self.test_advance_id:
            self.log_result(test_name, False, "No advance ID available for testing")
            return
            
        status, response = await self.make_authenticated_request(
            "GET", f"/api/advances/{self.test_advance_id}/installments", 
            self.super_admin_token
        )
        
        if status == 200 and "installments" in response:
            installments_count = len(response["installments"])
            self.log_result(test_name, True, 
                          f"Retrieved {installments_count} installments successfully")
        else:
            self.log_result(test_name, False, f"Failed to retrieve installments: {status} - {response}")
            
    async def test_payroll_cycle_calculation(self):
        """Test GET /api/payroll/cycles/{id}/calculate - Calculate salaries for specific cycle"""
        test_name = "Payroll Cycle Calculation"
        
        if not self.created_cycle_id:
            self.log_result(test_name, False, "No cycle ID available for testing")
            return
            
        status, response = await self.make_authenticated_request(
            "GET", f"/api/payroll/cycles/{self.created_cycle_id}/calculate", 
            self.super_admin_token
        )
        
        if status == 200 and "calculations" in response:
            calculations = response["calculations"]
            employees_count = len(calculations)
            total_gross = sum(calc.get("gross_salary", 0) for calc in calculations)
            total_deductions = sum(calc.get("total_deductions", 0) for calc in calculations)
            total_net = sum(calc.get("net_salary", 0) for calc in calculations)
            
            self.log_result(test_name, True, 
                          f"Calculated salaries for {employees_count} employees. Total Gross: {total_gross} AED, Total Deductions: {total_deductions} AED, Total Net: {total_net} AED")
        else:
            self.log_result(test_name, False, f"Failed to calculate cycle: {status} - {response}")
            
    async def test_payroll_cycle_summary(self):
        """Test GET /api/payroll/cycles/{id}/summary - Get payroll cycle summary"""
        test_name = "Payroll Cycle Summary"
        
        if not self.created_cycle_id:
            self.log_result(test_name, False, "No cycle ID available for testing")
            return
            
        status, response = await self.make_authenticated_request(
            "GET", f"/api/payroll/cycles/{self.created_cycle_id}/summary", 
            self.super_admin_token
        )
        
        if status == 200 and "summary" in response:
            summary = response["summary"]
            self.log_result(test_name, True, 
                          f"Retrieved cycle summary: {summary.get('total_employees', 0)} employees, Total Payroll: {summary.get('total_payroll', 0)} AED")
        else:
            self.log_result(test_name, False, f"Failed to retrieve summary: {status} - {response}")
            
    async def test_employee_payroll_history(self):
        """Test GET /api/payroll/employee/{id} - Get employee salary history"""
        test_name = "Employee Payroll History (Super Admin)"
        
        # Get a test employee ID first
        status, users_response = await self.make_authenticated_request(
            "GET", "/api/users", self.super_admin_token
        )
        
        if status == 200 and isinstance(users_response, list) and len(users_response) > 0:
            test_employee = users_response[0]
        elif status == 200 and isinstance(users_response, dict) and users_response.get("users"):
            test_employee = users_response["users"][0]
            employee_id = test_employee["id"]
            
            status, response = await self.make_authenticated_request(
                "GET", f"/api/payroll/employee/{employee_id}", 
                self.super_admin_token
            )
            
            if status == 200 and "payroll_history" in response:
                history_count = len(response["payroll_history"])
                self.log_result(test_name, True, 
                              f"Retrieved payroll history for {test_employee.get('name', 'Unknown')}: {history_count} records")
            else:
                self.log_result(test_name, False, f"Failed to retrieve payroll history: {status} - {response}")
        else:
            self.log_result(test_name, False, "Failed to get employee list for testing")
            
    async def test_regular_user_access_restrictions(self):
        """Test access restrictions for regular user (403 responses)"""
        test_name = "Regular User Access Restrictions"
        
        if not self.regular_user_token:
            self.log_result(test_name, False, "Regular user token not available")
            return
            
        # Test endpoints that should be restricted
        restricted_endpoints = [
            ("POST", "/api/payroll/cycles", {"month": "2025-11"}),
            ("GET", "/api/payroll/cycles", None),
            ("POST", f"/api/payroll/cycles/test-id/lock", {"lock_reason": "test"}),
            ("POST", f"/api/payroll/cycles/test-id/unlock", {"unlock_reason": "test"}),
            ("POST", "/api/advances/test-id/installments", {"number_of_installments": 3}),
        ]
        
        restricted_count = 0
        for method, endpoint, data in restricted_endpoints:
            status, response = await self.make_authenticated_request(
                method, endpoint, self.regular_user_token, data
            )
            if status == 403:
                restricted_count += 1
                
        if restricted_count == len(restricted_endpoints):
            self.log_result(test_name, True, 
                          f"All {restricted_count} super admin endpoints properly restricted for regular user")
        else:
            self.log_result(test_name, False, 
                          f"Only {restricted_count}/{len(restricted_endpoints)} endpoints properly restricted")
            
    async def test_regular_user_own_payroll_access(self):
        """Test regular user can access their own payroll history"""
        test_name = "Regular User Own Payroll Access"
        
        if not self.regular_user_token:
            self.log_result(test_name, False, "Regular user token not available")
            return
            
        # Get current user info to get their ID
        status, user_info = await self.make_authenticated_request(
            "GET", "/api/auth/me", self.regular_user_token
        )
        
        if status == 200 and user_info.get("id"):
            user_id = user_info["id"]
            
            status, response = await self.make_authenticated_request(
                "GET", f"/api/payroll/employee/{user_id}", 
                self.regular_user_token
            )
            
            if status == 200:
                payroll_count = len(response) if isinstance(response, list) else len(response.get('payroll_history', []))
                self.log_result(test_name, True, 
                              f"Regular user can access own payroll history: {payroll_count} records")
            else:
                self.log_result(test_name, False, f"Failed to access own payroll: {status} - {response}")
        else:
            self.log_result(test_name, False, "Failed to get user info")
            
    async def test_database_collections_verification(self):
        """Verify new database collections exist by testing endpoints that use them"""
        test_name = "Database Collections Verification"
        
        collections_tested = []
        
        # Test payroll_cycles collection
        status, response = await self.make_authenticated_request(
            "GET", "/api/payroll/cycles", self.super_admin_token
        )
        if status == 200:
            collections_tested.append("payroll_cycles")
            
        # Test installment_schedules collection (if we have an advance ID)
        if self.test_advance_id:
            status, response = await self.make_authenticated_request(
                "GET", f"/api/advances/{self.test_advance_id}/installments", 
                self.super_admin_token
            )
            if status == 200:
                collections_tested.append("installment_schedules")
                
        self.log_result(test_name, len(collections_tested) > 0, 
                      f"Verified {len(collections_tested)} database collections: {', '.join(collections_tested)}")
        
    async def test_deduction_ceiling_validation(self):
        """Test 33% salary deduction ceiling"""
        test_name = "Deduction Ceiling Validation (33%)"
        
        if not self.created_cycle_id:
            self.log_result(test_name, False, "No cycle ID available for testing")
            return
            
        # Get cycle calculations to check deduction limits
        status, response = await self.make_authenticated_request(
            "GET", f"/api/payroll/cycles/{self.created_cycle_id}/calculate", 
            self.super_admin_token
        )
        
        if status == 200 and "calculations" in response:
            calculations = response["calculations"]
            ceiling_violations = 0
            
            for calc in calculations:
                gross_salary = calc.get("gross_salary", 0)
                total_deductions = calc.get("total_deductions", 0)
                
                if gross_salary > 0:
                    deduction_percentage = (total_deductions / gross_salary) * 100
                    if deduction_percentage > 33:
                        ceiling_violations += 1
                        
            if ceiling_violations == 0:
                self.log_result(test_name, True, 
                              f"All employees respect 33% deduction ceiling. Tested {len(calculations)} employees")
            else:
                self.log_result(test_name, False, 
                              f"{ceiling_violations} employees exceed 33% deduction ceiling")
        else:
            self.log_result(test_name, False, f"Failed to get calculations for ceiling test: {status} - {response}")
            
    async def run_all_tests(self):
        """Run all payroll system tests"""
        print("🚀 Starting Comprehensive Payroll & Deductions System Testing")
        print("=" * 80)
        print()
        
        await self.setup_session()
        
        try:
            # Authentication
            print("🔐 AUTHENTICATION PHASE")
            print("-" * 40)
            self.super_admin_token = await self.authenticate_user(SUPER_ADMIN_CREDENTIALS, "Super Admin")
            self.regular_user_token = await self.authenticate_user(REGULAR_USER_CREDENTIALS, "Regular User")
            
            if not self.super_admin_token:
                print("❌ Cannot proceed without Super Admin authentication")
                return
                
            print("\n📊 PAYROLL CYCLES TESTING PHASE")
            print("-" * 40)
            await self.test_payroll_cycle_creation()
            await self.test_payroll_cycles_retrieval()
            await self.test_payroll_cycle_lock()
            await self.test_payroll_cycle_unlock()
            
            print("\n💰 ADVANCES INSTALLMENTS TESTING PHASE")
            print("-" * 40)
            await self.test_advance_installments_creation()
            await self.test_advance_installments_retrieval()
            
            print("\n🧮 SALARY CALCULATIONS TESTING PHASE")
            print("-" * 40)
            await self.test_payroll_cycle_calculation()
            await self.test_payroll_cycle_summary()
            await self.test_employee_payroll_history()
            
            print("\n🔒 ACCESS CONTROL TESTING PHASE")
            print("-" * 40)
            await self.test_regular_user_access_restrictions()
            await self.test_regular_user_own_payroll_access()
            
            print("\n🗄️ INTEGRATION TESTING PHASE")
            print("-" * 40)
            await self.test_database_collections_verification()
            await self.test_deduction_ceiling_validation()
            
        finally:
            await self.cleanup_session()
            
        # Print summary
        print("\n" + "=" * 80)
        print("📋 TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📊 Success Rate: {success_rate:.1f}%")
        print()
        
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")
            print()
            
        print("✅ PASSED TESTS:")
        for result in self.test_results:
            if result["success"]:
                print(f"   • {result['test']}")
                
        return success_rate >= 80  # Consider 80%+ as overall success

async def main():
    """Main test execution"""
    tester = PayrollSystemTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎉 OVERALL RESULT: PAYROLL SYSTEM TESTING SUCCESSFUL")
        sys.exit(0)
    else:
        print("\n⚠️ OVERALL RESULT: PAYROLL SYSTEM TESTING NEEDS ATTENTION")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())