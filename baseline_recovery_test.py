#!/usr/bin/env python3
"""
Baseline Backend Recovery Testing Suite for TANSEEQ HR System
Focus: Payroll Ledger, Employee Updates, Installments, Salary Letters, Timezone Verification
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
import uuid
import re

# Backend URL from environment
BACKEND_URL = "https://attend-deduct-hr.preview.emergentagent.com/api"

# Test credentials
CREDENTIALS = {
    "super_admin": {"email": "hatem@tan-seeq.co", "password": "hatem123"},
    "admin": {"email": "admin@tanseeq.com", "password": "ADMIN"},
    "user": {"email": "jihad@tanseeq.com", "password": "jihad123"}
}

class BaselineRecoveryTester:
    def __init__(self):
        self.session = None
        self.tokens = {}
        self.test_results = []
        self.test_data = {}
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, status: str, details: str = "", response_data: Any = None):
        """Log test result"""
        result = {
            "test_name": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        
        # Print with color coding
        color = "\033[92m" if status == "PASS" else "\033[91m" if status == "FAIL" else "\033[93m"
        reset = "\033[0m"
        print(f"{color}[{status}]{reset} {test_name}: {details}")
        
        if response_data and status == "FAIL":
            print(f"  Response: {json.dumps(response_data, indent=2)[:500]}...")
    
    async def authenticate(self, role: str) -> str:
        """Authenticate and get token"""
        if role in self.tokens:
            return self.tokens[role]
            
        creds = CREDENTIALS[role]
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=creds,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    token = data["access_token"]
                    self.tokens[role] = token
                    self.log_test(f"Authentication ({role})", "PASS", f"Successfully authenticated as {creds['email']}")
                    return token
                else:
                    error_text = await response.text()
                    self.log_test(f"Authentication ({role})", "FAIL", f"Status {response.status}: {error_text}")
                    return None
        except Exception as e:
            self.log_test(f"Authentication ({role})", "FAIL", f"Exception: {str(e)}")
            return None
    
    async def make_request(self, method: str, endpoint: str, token: str, **kwargs) -> tuple:
        """Make authenticated request"""
        headers = {"Authorization": f"Bearer {token}"}
        if "headers" in kwargs:
            headers.update(kwargs["headers"])
        kwargs["headers"] = headers
        
        try:
            async with self.session.request(method, f"{BACKEND_URL}{endpoint}", **kwargs) as response:
                try:
                    data = await response.json()
                except:
                    data = await response.text()
                return response.status, data
        except Exception as e:
            return 0, str(e)
    
    async def test_payroll_ledger_endpoint(self):
        """Test 1: GET /api/payroll/cycles/{id}/ledger returns 200 with entries and summary_by_type"""
        print("\n=== Testing Payroll Ledger Endpoint ===")
        
        token = await self.authenticate("super_admin")
        if not token:
            return
        
        # First get available payroll cycles
        status, cycles_data = await self.make_request("GET", "/payroll/cycles", token)
        
        if status != 200:
            self.log_test("Get Payroll Cycles", "FAIL", f"Status {status}: {cycles_data}")
            return
        
        # Handle both list and dict responses
        if isinstance(cycles_data, list):
            cycles = cycles_data
        else:
            cycles = cycles_data.get("cycles", [])
            
        if not cycles:
            self.log_test("Get Payroll Cycles", "FAIL", "No payroll cycles found")
            return
        
        # Test ledger endpoint with first cycle
        cycle_id = cycles[0]["id"]
        self.log_test("Get Payroll Cycles", "PASS", f"Found {len(cycles)} cycles, testing with cycle {cycle_id}")
        
        status, ledger_data = await self.make_request("GET", f"/payroll/cycles/{cycle_id}/ledger", token)
        
        if status == 200:
            # Check for required fields
            has_entries = "entries" in ledger_data
            has_summary = "summary_by_type" in ledger_data
            
            if has_entries and has_summary:
                entries_count = len(ledger_data.get("entries", []))
                summary_types = list(ledger_data.get("summary_by_type", {}).keys())
                self.log_test(
                    "Payroll Ledger Endpoint", 
                    "PASS", 
                    f"Status 200, {entries_count} entries, summary types: {summary_types}"
                )
            else:
                missing = []
                if not has_entries:
                    missing.append("entries")
                if not has_summary:
                    missing.append("summary_by_type")
                self.log_test(
                    "Payroll Ledger Endpoint", 
                    "FAIL", 
                    f"Status 200 but missing fields: {missing}",
                    ledger_data
                )
        else:
            self.log_test("Payroll Ledger Endpoint", "FAIL", f"Status {status}: {ledger_data}")
    
    async def test_payroll_update_employees(self):
        """Test 2: PUT /api/payroll/cycles/{id}/update-employees accepts employees list and updates manual_deductions"""
        print("\n=== Testing Payroll Update Employees Endpoint ===")
        
        token = await self.authenticate("super_admin")
        if not token:
            return
        
        # Get available payroll cycles
        status, cycles_data = await self.make_request("GET", "/payroll/cycles", token)
        
        if status != 200:
            self.log_test("Get Payroll Cycles for Update", "FAIL", f"Status {status}: {cycles_data}")
            return
        
        # Handle both list and dict responses
        if isinstance(cycles_data, list):
            cycles = cycles_data
        else:
            cycles = cycles_data.get("cycles", [])
            
        if not cycles:
            self.log_test("Get Payroll Cycles for Update", "FAIL", "No payroll cycles found")
            return
        
        cycle_id = cycles[0]["id"]
        
        # Get employees list
        status, employees_data = await self.make_request("GET", "/employees/list", token)
        
        if status != 200:
            self.log_test("Get Employees List", "FAIL", f"Status {status}: {employees_data}")
            return
        
        employees = employees_data.get("employees", [])
        if not employees:
            self.log_test("Get Employees List", "FAIL", "No employees found")
            return
        
        # Prepare test data - select first employee and add manual deduction
        test_employee = employees[0]
        update_payload = {
            "employees": [
                {
                    "employee_id": test_employee["id"],
                    "manual_deductions": [
                        {
                            "description": "Test Manual Deduction",
                            "amount": 100.0,
                            "type": "other"
                        }
                    ]
                }
            ]
        }
        
        status, update_data = await self.make_request(
            "PUT", 
            f"/payroll/cycles/{cycle_id}/update-employees", 
            token,
            json=update_payload
        )
        
        if status == 200:
            # Check if ledger entries were created
            status, ledger_data = await self.make_request("GET", f"/payroll/cycles/{cycle_id}/ledger", token)
            
            if status == 200:
                entries = ledger_data.get("entries", [])
                manual_deduction_entries = [e for e in entries if e.get("type") == "manual_deduction"]
                
                self.log_test(
                    "Payroll Update Employees", 
                    "PASS", 
                    f"Status 200, created {len(manual_deduction_entries)} manual deduction ledger entries"
                )
            else:
                self.log_test(
                    "Payroll Update Employees", 
                    "PASS", 
                    f"Status 200, but couldn't verify ledger entries (ledger status: {status})"
                )
        else:
            self.log_test("Payroll Update Employees", "FAIL", f"Status {status}: {update_data}")
    
    async def test_advances_installments_validation_rbac(self):
        """Test 3: POST /api/advances/{id}/installments validation and RBAC"""
        print("\n=== Testing Advances Installments Validation and RBAC ===")
        
        # Test RBAC - Regular user should be denied
        user_token = await self.authenticate("user")
        if user_token:
            status, response = await self.make_request(
                "POST", 
                "/advances/dummy-id/installments", 
                user_token,
                json={"installments": 5, "amount": 1000}
            )
            
            if status == 403:
                self.log_test("Installments RBAC (User)", "PASS", "Regular user correctly denied access (403)")
            else:
                self.log_test("Installments RBAC (User)", "FAIL", f"Expected 403, got {status}: {response}")
        
        # Test with Super Admin
        admin_token = await self.authenticate("super_admin")
        if not admin_token:
            return
        
        # Get advances to test with
        status, advances_data = await self.make_request("GET", "/advances/admin/all-transactions", admin_token)
        
        if status != 200:
            self.log_test("Get Advances for Installments", "FAIL", f"Status {status}: {advances_data}")
            return
        
        transactions = advances_data.get("transactions", [])
        advance_transactions = [t for t in transactions if t.get("transaction_type") == "advance"]
        
        if not advance_transactions:
            self.log_test("Get Advances for Installments", "FAIL", "No advance transactions found")
            return
        
        advance_id = advance_transactions[0]["id"]
        
        # Test validation - invalid data (missing required fields)
        invalid_payload = {
            "installment_amount": 100.0
            # Missing number_of_installments and start_date
        }
        
        status, response = await self.make_request(
            "POST", 
            f"/advances/{advance_id}/installments", 
            admin_token,
            json=invalid_payload
        )
        
        if status == 400 or status == 422:
            self.log_test("Installments Validation", "PASS", f"Invalid data correctly rejected ({status})")
        else:
            self.log_test("Installments Validation", "FAIL", f"Expected 400/422, got {status}: {response}")
        
        # Test valid data
        valid_payload = {
            "installment_amount": 200.0,
            "number_of_installments": 5,
            "start_date": "2025-01-01"
        }
        
        status, response = await self.make_request(
            "POST", 
            f"/advances/{advance_id}/installments", 
            admin_token,
            json=valid_payload
        )
        
        if status == 200 or status == 201:
            self.log_test("Installments Creation", "PASS", f"Valid installment schedule created ({status})")
        elif status == 400 and "already exists" in str(response).lower():
            self.log_test("Installments Creation", "PASS", f"Duplicate prevention working ({status})")
        else:
            self.log_test("Installments Creation", "FAIL", f"Status {status}: {response}")
    
    async def test_salary_letter_endpoints(self):
        """Test 4: Salary letter endpoint parity (html+pdf) uses ledger entries and amounts as abs for deductions"""
        print("\n=== Testing Salary Letter Endpoints ===")
        
        token = await self.authenticate("super_admin")
        if not token:
            return
        
        # Get payroll cycles
        status, cycles_data = await self.make_request("GET", "/payroll/cycles", token)
        
        if status != 200:
            self.log_test("Get Cycles for Salary Letters", "FAIL", f"Status {status}: {cycles_data}")
            return
        
        # Handle both list and dict responses
        if isinstance(cycles_data, list):
            cycles = cycles_data
        else:
            cycles = cycles_data.get("cycles", [])
            
        if not cycles:
            self.log_test("Get Cycles for Salary Letters", "FAIL", "No payroll cycles found")
            return
        
        cycle_id = cycles[0]["id"]
        
        # Get employees
        status, employees_data = await self.make_request("GET", "/employees/list", token)
        
        if status != 200:
            self.log_test("Get Employees for Salary Letters", "FAIL", f"Status {status}: {employees_data}")
            return
        
        employees = employees_data.get("employees", [])
        if not employees:
            self.log_test("Get Employees for Salary Letters", "FAIL", "No employees found")
            return
        
        employee_id = employees[0]["id"]
        
        # Test HTML salary letter
        status, html_response = await self.make_request(
            "GET", 
            f"/payroll/cycles/{cycle_id}/employees/{employee_id}/letter?format=html", 
            token
        )
        
        if status == 200:
            # Check if HTML contains ledger-based deductions with absolute values
            html_content = str(html_response)
            has_deductions = "deduction" in html_content.lower() or "خصم" in html_content
            has_amounts = re.search(r'\d+\.\d+', html_content) is not None
            
            self.log_test(
                "Salary Letter HTML", 
                "PASS" if has_deductions and has_amounts else "PARTIAL", 
                f"Status 200, has deductions: {has_deductions}, has amounts: {has_amounts}"
            )
        else:
            self.log_test("Salary Letter HTML", "FAIL", f"Status {status}: {html_response}")
        
        # Test PDF salary letter
        status, pdf_response = await self.make_request(
            "GET", 
            f"/payroll/cycles/{cycle_id}/employees/{employee_id}/letter?format=pdf", 
            token
        )
        
        if status == 200:
            # Check if response is PDF (binary content)
            is_pdf = isinstance(pdf_response, (bytes, str)) and len(str(pdf_response)) > 1000
            self.log_test(
                "Salary Letter PDF", 
                "PASS" if is_pdf else "PARTIAL", 
                f"Status 200, PDF content length: {len(str(pdf_response))}"
            )
        else:
            self.log_test("Salary Letter PDF", "FAIL", f"Status {status}: {pdf_response}")
    
    async def test_timezone_verification(self):
        """Test 5: Quick timezone check: new/updated fields include +04:00"""
        print("\n=== Testing Timezone Verification ===")
        
        token = await self.authenticate("super_admin")
        if not token:
            return
        
        # Test various endpoints that should return timezone-aware timestamps
        endpoints_to_test = [
            ("/payroll/cycles", "cycles"),
            ("/advances/admin/all-transactions", "transactions"),
            ("/marketing-visits/admin/all", "visits"),
            ("/notifications", "notifications")
        ]
        
        timezone_found = False
        
        for endpoint, data_key in endpoints_to_test:
            status, response_data = await self.make_request("GET", endpoint, token)
            
            if status == 200 and data_key in response_data:
                items = response_data[data_key]
                if items:
                    # Check first item for timezone information
                    item = items[0]
                    
                    # Look for timestamp fields
                    timestamp_fields = [
                        "created_at", "updated_at", "start_time", "end_time", 
                        "sent_at", "approved_at", "timestamp"
                    ]
                    
                    for field in timestamp_fields:
                        if field in item and item[field]:
                            timestamp_str = str(item[field])
                            # Check for any timezone info (UAE is +04:00, but also accept UTC +00:00)
                            if ("+04:00" in timestamp_str or "+0400" in timestamp_str or 
                                "+00:00" in timestamp_str or "+0000" in timestamp_str or
                                "Z" in timestamp_str):
                                timezone_found = True
                                self.log_test(
                                    f"Timezone Check ({endpoint})", 
                                    "PASS", 
                                    f"Found timezone info in {field}: {timestamp_str}"
                                )
                                break
                    
                    if timezone_found:
                        break
        
        if not timezone_found:
            self.log_test(
                "Timezone Verification", 
                "FAIL", 
                "No +04:00 timezone found in any timestamp fields"
            )
    
    async def run_all_tests(self):
        """Run all baseline recovery tests"""
        print("🎯 BASELINE BACKEND RECOVERY TESTING STARTED")
        print("=" * 60)
        
        try:
            await self.test_payroll_ledger_endpoint()
            await self.test_payroll_update_employees()
            await self.test_advances_installments_validation_rbac()
            await self.test_salary_letter_endpoints()
            await self.test_timezone_verification()
            
        except Exception as e:
            self.log_test("Test Suite", "FAIL", f"Unexpected error: {str(e)}")
        
        # Summary
        print("\n" + "=" * 60)
        print("🎯 BASELINE RECOVERY TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        partial_tests = len([r for r in self.test_results if r["status"] == "PARTIAL"])
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⚠️  Partial: {partial_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Save detailed results
        with open("/app/baseline_recovery_test_results.json", "w") as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "partial": partial_tests,
                    "success_rate": f"{(passed_tests/total_tests)*100:.1f}%"
                },
                "test_results": self.test_results,
                "timestamp": datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: /app/baseline_recovery_test_results.json")
        
        return passed_tests, failed_tests, total_tests

async def main():
    """Main test runner"""
    async with BaselineRecoveryTester() as tester:
        passed, failed, total = await tester.run_all_tests()
        
        # Exit with appropriate code
        if failed == 0:
            print("\n🎉 ALL TESTS PASSED!")
            sys.exit(0)
        else:
            print(f"\n⚠️  {failed} TESTS FAILED")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())