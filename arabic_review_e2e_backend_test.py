#!/usr/bin/env python3
"""
🔥 COMPREHENSIVE E2E BACKEND TESTING - ARABIC REVIEW REQUEST
إجراء فحوصات شاملة E2E للنظام الكامل

Testing Areas:
1. مشكلة تسجيل الحضور (طارق الوزان) - Attendance check-in with flexible exception
2. نظام السلف والعهد - طلبات الموظفين - Employee advance/custody requests  
3. نظام السلف والعهد - صلاحيات السوبر أدمن - Super Admin permissions
4. صفحة تسجيل السداد - Payment registration page
5. اختبارات إضافية - Additional tests

Test Accounts:
- Super Admin: admin@tanseeq.com / ADMIN
- User: jihad@tanseeq.com / jihad123
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid

class ArabicReviewE2ETest:
    def __init__(self):
        # Get backend URL from environment
        self.base_url = "https://payroll-management-4.preview.emergentagent.com/api"
        
        # Test credentials
        self.super_admin_creds = {
            "email": "admin@tanseeq.com",
            "password": "ADMIN"
        }
        
        self.user_creds = {
            "email": "jihad@tanseeq.com", 
            "password": "jihad123"
        }
        
        # Test results storage
        self.results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "success_rate": 0.0,
            "test_summary": {
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "success_rate": 0.0
            },
            "authentication": {},
            "attendance_flexible_exception": {},
            "advances_employee_requests": {},
            "advances_super_admin_permissions": {},
            "payment_registration": {},
            "additional_tests": {},
            "detailed_logs": []
        }
        
        # Authentication tokens
        self.super_admin_token = None
        self.user_token = None
        
        # Test data
        self.test_employee_id = None
        self.test_transaction_id = None

    async def log_test(self, test_name: str, status: str, details: str, response_data: Any = None):
        """Log test result"""
        self.results["total_tests"] += 1
        self.results["test_summary"]["total_tests"] += 1
        
        if status == "PASS":
            self.results["passed_tests"] += 1
            self.results["test_summary"]["passed_tests"] += 1
        else:
            self.results["failed_tests"] += 1
            self.results["test_summary"]["failed_tests"] += 1
            
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "test_name": test_name,
            "status": status,
            "details": details,
            "response_data": response_data
        }
        
        self.results["detailed_logs"].append(log_entry)
        print(f"[{status}] {test_name}: {details}")

    async def make_request(self, method: str, endpoint: str, token: str = None, 
                          data: Dict = None, params: Dict = None) -> Dict:
        """Make HTTP request with proper error handling"""
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if token:
            headers["Authorization"] = f"Bearer {token}"
            
        try:
            async with aiohttp.ClientSession() as session:
                if method.upper() == "GET":
                    async with session.get(url, headers=headers, params=params) as response:
                        response_text = await response.text()
                        try:
                            response_data = await response.json() if response_text else {}
                        except:
                            response_data = {"raw_response": response_text}
                        
                        return {
                            "status_code": response.status,
                            "data": response_data,
                            "success": response.status < 400
                        }
                        
                elif method.upper() == "POST":
                    async with session.post(url, headers=headers, json=data, params=params) as response:
                        response_text = await response.text()
                        try:
                            response_data = await response.json() if response_text else {}
                        except:
                            response_data = {"raw_response": response_text}
                        
                        return {
                            "status_code": response.status,
                            "data": response_data,
                            "success": response.status < 400
                        }
                        
                elif method.upper() == "PUT":
                    async with session.put(url, headers=headers, json=data, params=params) as response:
                        response_text = await response.text()
                        try:
                            response_data = await response.json() if response_text else {}
                        except:
                            response_data = {"raw_response": response_text}
                        
                        return {
                            "status_code": response.status,
                            "data": response_data,
                            "success": response.status < 400
                        }
                        
                elif method.upper() == "DELETE":
                    async with session.delete(url, headers=headers, params=params) as response:
                        response_text = await response.text()
                        try:
                            response_data = await response.json() if response_text else {}
                        except:
                            response_data = {"raw_response": response_text}
                        
                        return {
                            "status_code": response.status,
                            "data": response_data,
                            "success": response.status < 400
                        }
                        
        except Exception as e:
            return {
                "status_code": 0,
                "data": {"error": str(e)},
                "success": False
            }

    async def test_authentication(self):
        """Test authentication for both Super Admin and User"""
        print("\n🔐 TESTING AUTHENTICATION...")
        
        # Test Super Admin authentication
        response = await self.make_request("POST", "/auth/login", data=self.super_admin_creds)
        
        if response["success"] and response["data"].get("access_token"):
            self.super_admin_token = response["data"]["access_token"]
            user_info = response["data"].get("user", {})
            await self.log_test(
                "Super Admin Authentication",
                "PASS",
                f"Successfully authenticated as {user_info.get('name', 'Unknown')} with role {user_info.get('role', 'Unknown')}",
                response["data"]
            )
            self.results["authentication"]["super_admin"] = {
                "status": "success",
                "user_info": user_info,
                "token_length": len(self.super_admin_token)
            }
        else:
            await self.log_test(
                "Super Admin Authentication", 
                "FAIL",
                f"Authentication failed: {response['data']}",
                response["data"]
            )
            self.results["authentication"]["super_admin"] = {
                "status": "failed",
                "error": response["data"]
            }
            
        # Test User authentication
        response = await self.make_request("POST", "/auth/login", data=self.user_creds)
        
        if response["success"] and response["data"].get("access_token"):
            self.user_token = response["data"]["access_token"]
            user_info = response["data"].get("user", {})
            await self.log_test(
                "User Authentication",
                "PASS", 
                f"Successfully authenticated as {user_info.get('name', 'Unknown')} with role {user_info.get('role', 'Unknown')}",
                response["data"]
            )
            self.results["authentication"]["user"] = {
                "status": "success",
                "user_info": user_info,
                "token_length": len(self.user_token)
            }
        else:
            await self.log_test(
                "User Authentication",
                "FAIL",
                f"Authentication failed: {response['data']}",
                response["data"]
            )
            self.results["authentication"]["user"] = {
                "status": "failed", 
                "error": response["data"]
            }

    async def test_attendance_flexible_exception(self):
        """Test attendance check-in with flexible exception (طارق الوزان scenario)"""
        print("\n⏰ TESTING ATTENDANCE FLEXIBLE EXCEPTION...")
        
        if not self.user_token:
            await self.log_test(
                "Attendance Flexible Exception",
                "SKIP",
                "User authentication required but failed"
            )
            return
            
        # First, get user info to find employee ID
        response = await self.make_request("GET", "/auth/me", token=self.user_token)
        
        if not response["success"]:
            await self.log_test(
                "Get User Info for Attendance",
                "FAIL",
                f"Failed to get user info: {response['data']}",
                response["data"]
            )
            return
            
        user_id = response["data"].get("id")
        if not user_id:
            await self.log_test(
                "Get User ID for Attendance",
                "FAIL", 
                "User ID not found in response",
                response["data"]
            )
            return
            
        # Check if user has flexible exception configured
        if self.super_admin_token:
            # Try to get current exception configuration
            config_response = await self.make_request(
                "GET", 
                f"/config/exceptions/{user_id}",
                token=self.super_admin_token
            )
            
            await self.log_test(
                "Check Exception Configuration",
                "PASS" if config_response["success"] else "INFO",
                f"Exception config status: {config_response['status_code']} - {config_response['data']}",
                config_response["data"]
            )
            
            # Set flexible exception if needed
            if self.super_admin_token:
                set_exception_response = await self.make_request(
                    "PUT",
                    f"/config/exceptions/{user_id}",
                    token=self.super_admin_token,
                    data={"exception_type": "flexible"}
                )
                
                await self.log_test(
                    "Set Flexible Exception",
                    "PASS" if set_exception_response["success"] else "INFO",
                    f"Set flexible exception: {set_exception_response['status_code']} - {set_exception_response['data']}",
                    set_exception_response["data"]
                )
        
        # Test attendance check-in with flexible exception
        checkin_response = await self.make_request("POST", "/attendance/check-in", token=self.user_token)
        
        if checkin_response["success"]:
            response_data = checkin_response["data"]
            schedule_type = response_data.get("schedule_type", "unknown")
            exception_type = response_data.get("exception_type", "none")
            is_late = response_data.get("is_late", False)
            late_minutes = response_data.get("late_minutes", 0)
            
            # Verify flexible exception behavior
            if exception_type in ("flexible", "flex") or schedule_type == "flexible":
                await self.log_test(
                    "Attendance Check-in with Flexible Exception",
                    "PASS",
                    f"✅ Flexible exception working correctly - schedule_type: {schedule_type}, exception_type: {exception_type}, is_late: {is_late}, late_minutes: {late_minutes}",
                    response_data
                )
                
                self.results["attendance_flexible_exception"] = {
                    "status": "success",
                    "schedule_type": schedule_type,
                    "exception_type": exception_type,
                    "is_late": is_late,
                    "late_minutes": late_minutes,
                    "message": response_data.get("message", "")
                }
            else:
                await self.log_test(
                    "Attendance Check-in with Flexible Exception",
                    "FAIL",
                    f"❌ Flexible exception not applied correctly - schedule_type: {schedule_type}, exception_type: {exception_type}",
                    response_data
                )
                
                self.results["attendance_flexible_exception"] = {
                    "status": "failed",
                    "issue": "Flexible exception not applied",
                    "actual_schedule_type": schedule_type,
                    "actual_exception_type": exception_type
                }
        else:
            # Check if already checked in (acceptable)
            if "تم تسجيل الحضور مسبقاً" in str(checkin_response["data"]):
                await self.log_test(
                    "Attendance Check-in with Flexible Exception",
                    "INFO",
                    "Already checked in today - this is acceptable behavior",
                    checkin_response["data"]
                )
                
                self.results["attendance_flexible_exception"] = {
                    "status": "already_checked_in",
                    "message": "Already checked in today"
                }
            else:
                await self.log_test(
                    "Attendance Check-in with Flexible Exception",
                    "FAIL",
                    f"Check-in failed: {checkin_response['data']}",
                    checkin_response["data"]
                )
                
                self.results["attendance_flexible_exception"] = {
                    "status": "failed",
                    "error": checkin_response["data"]
                }

    async def test_advances_employee_requests(self):
        """Test employee advance/custody requests"""
        print("\n💰 TESTING ADVANCES EMPLOYEE REQUESTS...")
        
        if not self.user_token:
            await self.log_test(
                "Advances Employee Requests",
                "SKIP", 
                "User authentication required but failed"
            )
            return
            
        # Test 1: Request advance (transaction_type: "advance")
        advance_request = {
            "transaction_type": "advance",
            "amount": 500.0,
            "description": "طلب سلفة للضرورة",
            "category": "personal",
            "expense_date": datetime.now().strftime("%Y-%m-%d"),
            "notes": "طلب سلفة عاجل"
        }
        
        # Note: Employee requests typically go through expense endpoint, not create
        # Test expense creation (which is how employees request advances)
        expense_response = await self.make_request(
            "POST",
            "/advances/expense",
            token=self.user_token,
            data=advance_request
        )
        
        await self.log_test(
            "Employee Advance Request",
            "PASS" if expense_response["success"] else "INFO",
            f"Advance request status: {expense_response['status_code']} - {expense_response['data']}",
            expense_response["data"]
        )
        
        # Test 2: Request custody (transaction_type: "custody") 
        custody_request = {
            "transaction_type": "custody",
            "amount": 300.0,
            "description": "طلب عهدة للمشروع",
            "category": "business",
            "expense_date": datetime.now().strftime("%Y-%m-%d"),
            "notes": "عهدة مشروع جديد"
        }
        
        custody_response = await self.make_request(
            "POST",
            "/advances/expense", 
            token=self.user_token,
            data=custody_request
        )
        
        await self.log_test(
            "Employee Custody Request",
            "PASS" if custody_response["success"] else "INFO",
            f"Custody request status: {custody_response['status_code']} - {custody_response['data']}",
            custody_response["data"]
        )
        
        # Test 3: Custody settlement
        settlement_response = await self.make_request(
            "POST",
            "/advances/custody-settlement",
            token=self.user_token,
            data={
                "amount": 100.0,
                "description": "تسوية جزئية للعهدة",
                "notes": "إرجاع جزء من العهدة"
            }
        )
        
        await self.log_test(
            "Custody Settlement",
            "PASS" if settlement_response["success"] else "INFO", 
            f"Settlement status: {settlement_response['status_code']} - {settlement_response['data']}",
            settlement_response["data"]
        )
        
        # Test 4: Check employee balance
        balance_response = await self.make_request("GET", "/advances/my-balance", token=self.user_token)
        
        if balance_response["success"]:
            balance_data = balance_response["data"]
            await self.log_test(
                "Employee Balance Check",
                "PASS",
                f"✅ Balance retrieved - Total Available: {balance_data.get('total_available', 0)} AED, Advance: {balance_data.get('remaining_advance', 0)} AED, Custody: {balance_data.get('remaining_custody', 0)} AED",
                balance_data
            )
        else:
            await self.log_test(
                "Employee Balance Check",
                "FAIL",
                f"Failed to get balance: {balance_response['data']}",
                balance_response["data"]
            )
            
        # Test 5: Get employee transactions
        transactions_response = await self.make_request("GET", "/advances/my-transactions", token=self.user_token)
        
        if transactions_response["success"]:
            transactions = transactions_response["data"].get("transactions", [])
            await self.log_test(
                "Employee Transactions History",
                "PASS",
                f"✅ Retrieved {len(transactions)} transactions",
                {"transaction_count": len(transactions), "sample": transactions[:2] if transactions else []}
            )
        else:
            await self.log_test(
                "Employee Transactions History",
                "FAIL",
                f"Failed to get transactions: {transactions_response['data']}",
                transactions_response["data"]
            )
            
        self.results["advances_employee_requests"] = {
            "advance_request": expense_response,
            "custody_request": custody_response, 
            "custody_settlement": settlement_response,
            "balance_check": balance_response,
            "transactions_history": transactions_response
        }

    async def test_advances_super_admin_permissions(self):
        """Test Super Admin permissions for advances system"""
        print("\n👑 TESTING ADVANCES SUPER ADMIN PERMISSIONS...")
        
        if not self.super_admin_token:
            await self.log_test(
                "Advances Super Admin Permissions",
                "SKIP",
                "Super Admin authentication required but failed"
            )
            return
            
        # Test 1: Get all employee balances
        balances_response = await self.make_request(
            "GET",
            "/advances/admin/all-balances", 
            token=self.super_admin_token
        )
        
        if balances_response["success"]:
            balances = balances_response["data"].get("employee_balances", [])
            await self.log_test(
                "Admin All Employee Balances",
                "PASS",
                f"✅ Retrieved balances for {len(balances)} employees",
                {"employee_count": len(balances), "sample": balances[:2] if balances else []}
            )
        else:
            await self.log_test(
                "Admin All Employee Balances",
                "FAIL",
                f"Failed to get balances: {balances_response['data']}",
                balances_response["data"]
            )
            
        # Test 2: Get pending approvals
        pending_response = await self.make_request(
            "GET",
            "/advances/admin/pending-approvals",
            token=self.super_admin_token
        )
        
        if pending_response["success"]:
            pending = pending_response["data"].get("pending_transactions", [])
            await self.log_test(
                "Admin Pending Approvals",
                "PASS",
                f"✅ Retrieved {len(pending)} pending transactions",
                {"pending_count": len(pending), "sample": pending[:2] if pending else []}
            )
        else:
            await self.log_test(
                "Admin Pending Approvals", 
                "FAIL",
                f"Failed to get pending approvals: {pending_response['data']}",
                pending_response["data"]
            )
            
        # Test 3: Get all transactions
        all_transactions_response = await self.make_request(
            "GET",
            "/advances/admin/all-transactions",
            token=self.super_admin_token
        )
        
        if all_transactions_response["success"]:
            all_transactions = all_transactions_response["data"].get("transactions", [])
            await self.log_test(
                "Admin All Transactions",
                "PASS",
                f"✅ Retrieved {len(all_transactions)} total transactions",
                {"transaction_count": len(all_transactions), "sample": all_transactions[:2] if all_transactions else []}
            )
            
            # Store a transaction ID for edit/delete testing
            if all_transactions:
                self.test_transaction_id = all_transactions[0].get("id")
        else:
            await self.log_test(
                "Admin All Transactions",
                "FAIL", 
                f"Failed to get all transactions: {all_transactions_response['data']}",
                all_transactions_response["data"]
            )
            
        # Test 4: Edit transaction (Super Admin can edit even after approval)
        if self.test_transaction_id:
            edit_response = await self.make_request(
                "PUT",
                f"/advances/{self.test_transaction_id}/edit",
                token=self.super_admin_token,
                data={
                    "amount": 999.99,
                    "description": "تعديل من السوبر أدمن - اختبار",
                    "notes": "تم التعديل للاختبار"
                }
            )
            
            await self.log_test(
                "Admin Edit Transaction",
                "PASS" if edit_response["success"] else "INFO",
                f"Edit transaction status: {edit_response['status_code']} - {edit_response['data']}",
                edit_response["data"]
            )
        else:
            await self.log_test(
                "Admin Edit Transaction",
                "SKIP",
                "No transaction ID available for testing"
            )
            
        # Test 5: Delete transaction (Super Admin can delete even after approval)
        if self.test_transaction_id:
            delete_response = await self.make_request(
                "DELETE",
                f"/advances/{self.test_transaction_id}",
                token=self.super_admin_token
            )
            
            await self.log_test(
                "Admin Delete Transaction",
                "PASS" if delete_response["success"] else "INFO",
                f"Delete transaction status: {delete_response['status_code']} - {delete_response['data']}",
                delete_response["data"]
            )
        else:
            await self.log_test(
                "Admin Delete Transaction", 
                "SKIP",
                "No transaction ID available for testing"
            )
            
        self.results["advances_super_admin_permissions"] = {
            "all_balances": balances_response,
            "pending_approvals": pending_response,
            "all_transactions": all_transactions_response,
            "edit_transaction": edit_response if self.test_transaction_id else {"skipped": True},
            "delete_transaction": delete_response if self.test_transaction_id else {"skipped": True}
        }

    async def test_payment_registration_page(self):
        """Test payment registration page endpoints"""
        print("\n💳 TESTING PAYMENT REGISTRATION PAGE...")
        
        if not self.super_admin_token:
            await self.log_test(
                "Payment Registration Page",
                "SKIP",
                "Super Admin authentication required but failed"
            )
            return
            
        # Test: Get employees with balances for payment registration
        employees_balances_response = await self.make_request(
            "GET",
            "/advances/admin/employees-with-balances",
            token=self.super_admin_token
        )
        
        if employees_balances_response["success"]:
            employees = employees_balances_response["data"]
            
            # Verify response structure
            if isinstance(employees, list):
                valid_employees = []
                for emp in employees:
                    if all(key in emp for key in ["employee_id", "employee_name", "remaining_advance", "remaining_custody"]):
                        valid_employees.append(emp)
                        
                await self.log_test(
                    "Payment Registration - Employees with Balances",
                    "PASS",
                    f"✅ Retrieved {len(valid_employees)} employees with valid balance data structure",
                    {
                        "total_employees": len(employees),
                        "valid_employees": len(valid_employees),
                        "sample": valid_employees[:3] if valid_employees else []
                    }
                )
                
                self.results["payment_registration"] = {
                    "status": "success",
                    "employees_count": len(valid_employees),
                    "sample_data": valid_employees[:3] if valid_employees else []
                }
            else:
                await self.log_test(
                    "Payment Registration - Employees with Balances",
                    "FAIL",
                    f"❌ Invalid response structure - expected list, got {type(employees)}",
                    employees_balances_response["data"]
                )
                
                self.results["payment_registration"] = {
                    "status": "failed",
                    "error": "Invalid response structure",
                    "response": employees_balances_response["data"]
                }
        else:
            await self.log_test(
                "Payment Registration - Employees with Balances",
                "FAIL",
                f"Failed to get employees with balances: {employees_balances_response['data']}",
                employees_balances_response["data"]
            )
            
            self.results["payment_registration"] = {
                "status": "failed",
                "error": employees_balances_response["data"]
            }

    async def test_additional_endpoints(self):
        """Test additional endpoints mentioned in the review"""
        print("\n🔍 TESTING ADDITIONAL ENDPOINTS...")
        
        # Test with user token
        if self.user_token:
            # Test user balance
            user_balance_response = await self.make_request("GET", "/advances/my-balance", token=self.user_token)
            
            await self.log_test(
                "User My Balance",
                "PASS" if user_balance_response["success"] else "FAIL",
                f"User balance status: {user_balance_response['status_code']} - {user_balance_response.get('data', {})}",
                user_balance_response["data"]
            )
            
        # Test with super admin token
        if self.super_admin_token:
            # Test admin all transactions
            admin_transactions_response = await self.make_request(
                "GET", 
                "/advances/admin/all-transactions",
                token=self.super_admin_token
            )
            
            await self.log_test(
                "Admin All Transactions",
                "PASS" if admin_transactions_response["success"] else "FAIL",
                f"Admin transactions status: {admin_transactions_response['status_code']} - Found {len(admin_transactions_response.get('data', {}).get('transactions', []))} transactions",
                {"transaction_count": len(admin_transactions_response.get('data', {}).get('transactions', []))}
            )
            
            # Test admin pending approvals
            admin_pending_response = await self.make_request(
                "GET",
                "/advances/admin/pending-approvals", 
                token=self.super_admin_token
            )
            
            await self.log_test(
                "Admin Pending Approvals",
                "PASS" if admin_pending_response["success"] else "FAIL",
                f"Pending approvals status: {admin_pending_response['status_code']} - Found {len(admin_pending_response.get('data', {}).get('pending_transactions', []))} pending",
                {"pending_count": len(admin_pending_response.get('data', {}).get('pending_transactions', []))}
            )
            
        self.results["additional_tests"] = {
            "user_balance": user_balance_response if self.user_token else {"skipped": "No user token"},
            "admin_transactions": admin_transactions_response if self.super_admin_token else {"skipped": "No admin token"},
            "admin_pending": admin_pending_response if self.super_admin_token else {"skipped": "No admin token"}
        }

    async def run_all_tests(self):
        """Run all E2E tests"""
        print("🚀 STARTING COMPREHENSIVE E2E BACKEND TESTING - ARABIC REVIEW")
        print("=" * 80)
        
        start_time = datetime.now()
        
        try:
            # Run all test suites
            await self.test_authentication()
            await self.test_attendance_flexible_exception()
            await self.test_advances_employee_requests()
            await self.test_advances_super_admin_permissions()
            await self.test_payment_registration_page()
            await self.test_additional_endpoints()
            
        except Exception as e:
            await self.log_test(
                "Test Suite Execution",
                "ERROR",
                f"Critical error during test execution: {str(e)}"
            )
            
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Calculate success rate
        if self.results["total_tests"] > 0:
            self.results["test_summary"]["success_rate"] = (
                self.results["passed_tests"] / self.results["total_tests"]
            ) * 100
            
        self.results["test_summary"]["duration_seconds"] = duration
        self.results["test_summary"]["start_time"] = start_time.isoformat()
        self.results["test_summary"]["end_time"] = end_time.isoformat()
        
        # Print summary
        print("\n" + "=" * 80)
        print("🎯 TEST EXECUTION SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {self.results['total_tests']}")
        print(f"Passed: {self.results['passed_tests']}")
        print(f"Failed: {self.results['failed_tests']}")
        print(f"Success Rate: {self.results['test_summary']['success_rate']:.1f}%")
        print(f"Duration: {duration:.2f} seconds")
        
        # Save results
        results_file = "/app/arabic_review_e2e_test_results.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2, default=str)
            
        print(f"\n📊 Detailed results saved to: {results_file}")
        
        return self.results

async def main():
    """Main test execution"""
    tester = ArabicReviewE2ETest()
    results = await tester.run_all_tests()
    
    # Return results for further processing
    return results

if __name__ == "__main__":
    asyncio.run(main())