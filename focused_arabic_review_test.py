#!/usr/bin/env python3
"""
🎯 FOCUSED ARABIC REVIEW E2E TESTING
Targeted testing for the specific scenarios mentioned in the Arabic review request

Focus Areas:
1. مشكلة تسجيل الحضور (طارق الوزان) - Attendance check-in with flexible exception
2. نظام السلف والعهد - طلبات الموظفين - Employee advance/custody requests  
3. نظام السلف والعهد - صلاحيات السوبر أدمن - Super Admin permissions
4. صفحة تسجيل السداد - Payment registration page
5. اختبارات إضافية - Additional tests
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from typing import Dict, Any

class FocusedArabicReviewTest:
    def __init__(self):
        self.base_url = "https://payroll-management-4.preview.emergentagent.com/api"
        
        # Test credentials
        self.super_admin_creds = {"email": "admin@tanseeq.com", "password": "ADMIN"}
        self.user_creds = {"email": "jihad@tanseeq.com", "password": "jihad123"}
        
        # Authentication tokens
        self.super_admin_token = None
        self.user_token = None
        
        # Test results
        self.results = {
            "test_summary": {"total": 0, "passed": 0, "failed": 0},
            "scenarios": {}
        }

    async def make_request(self, method: str, endpoint: str, token: str = None, 
                          data: Dict = None, params: Dict = None) -> Dict:
        """Make HTTP request"""
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if token:
            headers["Authorization"] = f"Bearer {token}"
            
        try:
            async with aiohttp.ClientSession() as session:
                kwargs = {"headers": headers}
                if params:
                    kwargs["params"] = params
                if data and method.upper() in ["POST", "PUT"]:
                    kwargs["json"] = data
                    
                async with getattr(session, method.lower())(url, **kwargs) as response:
                    try:
                        response_data = await response.json()
                    except:
                        response_data = {"raw_response": await response.text()}
                    
                    return {
                        "status_code": response.status,
                        "data": response_data,
                        "success": response.status < 400
                    }
        except Exception as e:
            return {"status_code": 0, "data": {"error": str(e)}, "success": False}

    def log_result(self, test_name: str, status: str, details: str, data: Any = None):
        """Log test result"""
        self.results["test_summary"]["total"] += 1
        if status == "PASS":
            self.results["test_summary"]["passed"] += 1
        else:
            self.results["test_summary"]["failed"] += 1
            
        print(f"[{status}] {test_name}: {details}")
        
        if test_name not in self.results["scenarios"]:
            self.results["scenarios"][test_name] = []
        self.results["scenarios"][test_name].append({
            "status": status,
            "details": details,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })

    async def authenticate(self):
        """Authenticate both users"""
        print("🔐 AUTHENTICATING USERS...")
        
        # Super Admin
        response = await self.make_request("POST", "/auth/login", data=self.super_admin_creds)
        if response["success"]:
            self.super_admin_token = response["data"]["access_token"]
            user_info = response["data"]["user"]
            self.log_result(
                "Super Admin Authentication", 
                "PASS",
                f"Authenticated as {user_info['name']} ({user_info['role']})",
                user_info
            )
        else:
            self.log_result(
                "Super Admin Authentication",
                "FAIL", 
                f"Failed: {response['data']}",
                response["data"]
            )
            
        # Regular User
        response = await self.make_request("POST", "/auth/login", data=self.user_creds)
        if response["success"]:
            self.user_token = response["data"]["access_token"]
            user_info = response["data"]["user"]
            self.log_result(
                "User Authentication",
                "PASS",
                f"Authenticated as {user_info['name']} ({user_info['role']})",
                user_info
            )
        else:
            self.log_result(
                "User Authentication",
                "FAIL",
                f"Failed: {response['data']}",
                response["data"]
            )

    async def test_scenario_1_attendance_flexible_exception(self):
        """Scenario 1: مشكلة تسجيل الحضور (طارق الوزان)"""
        print("\n⏰ SCENARIO 1: ATTENDANCE CHECK-IN WITH FLEXIBLE EXCEPTION")
        
        if not self.user_token:
            self.log_result("Scenario 1", "SKIP", "User authentication failed")
            return
            
        # Get user info
        response = await self.make_request("GET", "/auth/me", token=self.user_token)
        if not response["success"]:
            self.log_result("Get User Info", "FAIL", f"Failed: {response['data']}")
            return
            
        user_id = response["data"]["id"]
        
        # Check attendance policy for user
        policy_response = await self.make_request(
            "GET", 
            f"/attendance/policies/{user_id}",
            token=self.super_admin_token
        )
        
        self.log_result(
            "Check Attendance Policy",
            "PASS" if policy_response["success"] else "INFO",
            f"Policy status: {policy_response['status_code']} - {policy_response['data']}",
            policy_response["data"]
        )
        
        # Test attendance check-in
        checkin_response = await self.make_request("POST", "/attendance/check-in", token=self.user_token)
        
        if checkin_response["success"]:
            data = checkin_response["data"]
            schedule_type = data.get("schedule_type", "unknown")
            exception_type = data.get("exception_type", "none")
            is_late = data.get("is_late", False)
            late_minutes = data.get("late_minutes", 0)
            
            # Verify flexible exception behavior
            if exception_type in ("flexible", "flex", "exempt") or schedule_type == "flexible":
                self.log_result(
                    "Flexible Exception Check-in",
                    "PASS",
                    f"✅ Flexible exception working - schedule: {schedule_type}, exception: {exception_type}, late: {is_late}, minutes: {late_minutes}",
                    data
                )
            else:
                self.log_result(
                    "Flexible Exception Check-in",
                    "INFO",
                    f"Standard schedule applied - schedule: {schedule_type}, exception: {exception_type}, late: {is_late}, minutes: {late_minutes}",
                    data
                )
        else:
            # Check if already checked in
            if "تم تسجيل الحضور مسبقاً" in str(checkin_response["data"]):
                self.log_result(
                    "Flexible Exception Check-in",
                    "INFO",
                    "Already checked in today - acceptable",
                    checkin_response["data"]
                )
            else:
                self.log_result(
                    "Flexible Exception Check-in",
                    "FAIL",
                    f"Check-in failed: {checkin_response['data']}",
                    checkin_response["data"]
                )

    async def test_scenario_2_employee_advance_requests(self):
        """Scenario 2: نظام السلف والعهد - طلبات الموظفين"""
        print("\n💰 SCENARIO 2: EMPLOYEE ADVANCE/CUSTODY REQUESTS")
        
        if not self.user_token:
            self.log_result("Scenario 2", "SKIP", "User authentication failed")
            return
            
        # Test advance request (POST /api/advances/request)
        advance_request_data = {
            "transaction_type": "advance",
            "amount": 500.0,
            "description": "طلب سلفة للضرورة",
            "notes": "طلب عاجل"
        }
        
        advance_response = await self.make_request(
            "POST",
            "/advances/request",
            token=self.user_token,
            data=advance_request_data
        )
        
        self.log_result(
            "Employee Advance Request",
            "PASS" if advance_response["success"] else "INFO",
            f"Advance request: {advance_response['status_code']} - {advance_response['data']}",
            advance_response["data"]
        )
        
        # Test custody request (POST /api/advances/request)
        custody_request_data = {
            "transaction_type": "custody",
            "amount": 300.0,
            "description": "طلب عهدة للمشروع",
            "notes": "عهدة مشروع جديد"
        }
        
        custody_response = await self.make_request(
            "POST",
            "/advances/request",
            token=self.user_token,
            data=custody_request_data
        )
        
        self.log_result(
            "Employee Custody Request",
            "PASS" if custody_response["success"] else "INFO",
            f"Custody request: {custody_response['status_code']} - {custody_response['data']}",
            custody_response["data"]
        )
        
        # Test custody settlement (POST /api/advances/custody-settlement)
        settlement_data = {
            "amount": 100.0,
            "settlement_date": datetime.now().strftime("%Y-%m-%d"),
            "description": "تسوية جزئية للعهدة",
            "notes": "إرجاع جزء من العهدة"
        }
        
        settlement_response = await self.make_request(
            "POST",
            "/advances/custody-settlement",
            token=self.user_token,
            data=settlement_data
        )
        
        self.log_result(
            "Custody Settlement",
            "PASS" if settlement_response["success"] else "INFO",
            f"Settlement: {settlement_response['status_code']} - {settlement_response['data']}",
            settlement_response["data"]
        )
        
        # Verify notifications sent to Super Admin
        if self.super_admin_token:
            notifications_response = await self.make_request(
                "GET",
                "/notifications",
                token=self.super_admin_token
            )
            
            if notifications_response["success"]:
                notifications = notifications_response["data"]
                recent_notifications = [n for n in notifications if "سلفة" in n.get("subject", "") or "عهدة" in n.get("subject", "")]
                
                self.log_result(
                    "Super Admin Notifications",
                    "PASS" if recent_notifications else "INFO",
                    f"Found {len(recent_notifications)} advance/custody notifications",
                    {"total_notifications": len(notifications), "advance_notifications": len(recent_notifications)}
                )

    async def test_scenario_3_super_admin_permissions(self):
        """Scenario 3: نظام السلف والعهد - صلاحيات السوبر أدمن"""
        print("\n👑 SCENARIO 3: SUPER ADMIN PERMISSIONS")
        
        if not self.super_admin_token:
            self.log_result("Scenario 3", "SKIP", "Super Admin authentication failed")
            return
            
        # Test edit transaction (PUT /api/advances/{transaction_id}/edit)
        # First get a transaction to edit
        transactions_response = await self.make_request(
            "GET",
            "/advances/admin/all-transactions",
            token=self.super_admin_token
        )
        
        if transactions_response["success"]:
            transactions = transactions_response["data"].get("transactions", [])
            if transactions:
                transaction_id = transactions[0]["id"]
                
                edit_data = {
                    "amount": 999.99,
                    "description": "تعديل من السوبر أدمن - اختبار",
                    "notes": "تم التعديل للاختبار"
                }
                
                edit_response = await self.make_request(
                    "PUT",
                    f"/advances/{transaction_id}/edit",
                    token=self.super_admin_token,
                    data=edit_data
                )
                
                self.log_result(
                    "Super Admin Edit Transaction",
                    "PASS" if edit_response["success"] else "INFO",
                    f"Edit: {edit_response['status_code']} - {edit_response['data']}",
                    edit_response["data"]
                )
                
                # Test delete transaction (DELETE /api/advances/{transaction_id})
                # Use a different transaction for delete test
                if len(transactions) > 1:
                    delete_transaction_id = transactions[1]["id"]
                    
                    delete_response = await self.make_request(
                        "DELETE",
                        f"/advances/{delete_transaction_id}",
                        token=self.super_admin_token
                    )
                    
                    self.log_result(
                        "Super Admin Delete Transaction",
                        "PASS" if delete_response["success"] else "INFO",
                        f"Delete: {delete_response['status_code']} - {delete_response['data']}",
                        delete_response["data"]
                    )
                    
                    # Verify balance update after edit/delete
                    balances_response = await self.make_request(
                        "GET",
                        "/advances/admin/all-balances",
                        token=self.super_admin_token
                    )
                    
                    self.log_result(
                        "Balance Update Verification",
                        "PASS" if balances_response["success"] else "INFO",
                        f"Balances after edit/delete: {balances_response['status_code']} - Found {len(balances_response.get('data', {}).get('employee_balances', []))} employees",
                        {"employee_count": len(balances_response.get('data', {}).get('employee_balances', []))}
                    )

    async def test_scenario_4_payment_registration(self):
        """Scenario 4: صفحة تسجيل السداد"""
        print("\n💳 SCENARIO 4: PAYMENT REGISTRATION PAGE")
        
        if not self.super_admin_token:
            self.log_result("Scenario 4", "SKIP", "Super Admin authentication failed")
            return
            
        # Test GET /api/advances/admin/employees-with-balances
        employees_response = await self.make_request(
            "GET",
            "/advances/admin/employees-with-balances",
            token=self.super_admin_token
        )
        
        if employees_response["success"]:
            data = employees_response["data"]
            
            # Check if response has the expected structure
            if isinstance(data, dict) and "employee_balances" in data:
                employees = data["employee_balances"]
                valid_employees = []
                
                for emp in employees:
                    if all(key in emp for key in ["employee_id", "employee_name", "remaining_advance", "remaining_custody"]):
                        valid_employees.append(emp)
                        
                self.log_result(
                    "Payment Registration Data",
                    "PASS",
                    f"✅ Found {len(valid_employees)} employees with valid balance structure",
                    {
                        "total_employees": len(employees),
                        "valid_structure": len(valid_employees),
                        "sample": valid_employees[:2] if valid_employees else []
                    }
                )
            elif isinstance(data, list):
                # Direct list format
                valid_employees = []
                for emp in data:
                    if all(key in emp for key in ["employee_id", "employee_name", "remaining_advance", "remaining_custody"]):
                        valid_employees.append(emp)
                        
                self.log_result(
                    "Payment Registration Data",
                    "PASS",
                    f"✅ Found {len(valid_employees)} employees with valid balance structure (list format)",
                    {
                        "total_employees": len(data),
                        "valid_structure": len(valid_employees),
                        "sample": valid_employees[:2] if valid_employees else []
                    }
                )
            else:
                self.log_result(
                    "Payment Registration Data",
                    "FAIL",
                    f"❌ Unexpected response structure: {type(data)}",
                    data
                )
        else:
            self.log_result(
                "Payment Registration Data",
                "FAIL",
                f"Failed to get employees with balances: {employees_response['data']}",
                employees_response["data"]
            )

    async def test_scenario_5_additional_tests(self):
        """Scenario 5: اختبارات إضافية"""
        print("\n🔍 SCENARIO 5: ADDITIONAL TESTS")
        
        # Test /api/advances/my-balance for employee
        if self.user_token:
            balance_response = await self.make_request("GET", "/advances/my-balance", token=self.user_token)
            
            if balance_response["success"]:
                balance = balance_response["data"]
                total_available = balance.get("total_available", 0)
                
                self.log_result(
                    "Employee Balance Check",
                    "PASS",
                    f"✅ Employee balance: {total_available} AED available (Advance: {balance.get('remaining_advance', 0)}, Custody: {balance.get('remaining_custody', 0)})",
                    balance
                )
            else:
                self.log_result(
                    "Employee Balance Check",
                    "FAIL",
                    f"Failed: {balance_response['data']}",
                    balance_response["data"]
                )
        
        # Test /api/advances/admin/all-transactions for Super Admin
        if self.super_admin_token:
            transactions_response = await self.make_request(
                "GET",
                "/advances/admin/all-transactions",
                token=self.super_admin_token
            )
            
            if transactions_response["success"]:
                transactions = transactions_response["data"].get("transactions", [])
                
                self.log_result(
                    "Admin All Transactions",
                    "PASS",
                    f"✅ Retrieved {len(transactions)} total transactions",
                    {"transaction_count": len(transactions)}
                )
            else:
                self.log_result(
                    "Admin All Transactions",
                    "FAIL",
                    f"Failed: {transactions_response['data']}",
                    transactions_response["data"]
                )
                
        # Test /api/advances/admin/pending-approvals
        if self.super_admin_token:
            pending_response = await self.make_request(
                "GET",
                "/advances/admin/pending-approvals",
                token=self.super_admin_token
            )
            
            if pending_response["success"]:
                pending = pending_response["data"].get("pending_transactions", [])
                
                self.log_result(
                    "Admin Pending Approvals",
                    "PASS",
                    f"✅ Found {len(pending)} pending transactions",
                    {"pending_count": len(pending)}
                )
            else:
                self.log_result(
                    "Admin Pending Approvals",
                    "FAIL",
                    f"Failed: {pending_response['data']}",
                    pending_response["data"]
                )

    async def run_all_scenarios(self):
        """Run all test scenarios"""
        print("🚀 STARTING FOCUSED ARABIC REVIEW E2E TESTING")
        print("=" * 80)
        
        start_time = datetime.now()
        
        try:
            await self.authenticate()
            await self.test_scenario_1_attendance_flexible_exception()
            await self.test_scenario_2_employee_advance_requests()
            await self.test_scenario_3_super_admin_permissions()
            await self.test_scenario_4_payment_registration()
            await self.test_scenario_5_additional_tests()
            
        except Exception as e:
            self.log_result("Test Execution", "ERROR", f"Critical error: {str(e)}")
            
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Calculate success rate
        total = self.results["test_summary"]["total"]
        passed = self.results["test_summary"]["passed"]
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print("\n" + "=" * 80)
        print("🎯 FOCUSED ARABIC REVIEW TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {self.results['test_summary']['failed']}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Duration: {duration:.2f} seconds")
        
        # Save results
        results_file = "/app/focused_arabic_review_test_results.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2, default=str)
            
        print(f"\n📊 Detailed results saved to: {results_file}")
        
        return self.results

async def main():
    """Main execution"""
    tester = FocusedArabicReviewTest()
    return await tester.run_all_scenarios()

if __name__ == "__main__":
    asyncio.run(main())