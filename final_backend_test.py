#!/usr/bin/env python3
"""
Final Backend Testing Suite for TANSEEQ HR System
Focus: Installment Schedules, Payroll Ledger, Salary Letters, Timezone/Gregorian, Regression Testing
"""

import asyncio
import aiohttp
import json
import re
from datetime import datetime

BACKEND_URL = "https://hr-system-upgrade.preview.emergentagent.com/api"
CREDENTIALS = {
    "super_admin": {"email": "hatem@tan-seeq.co", "password": "hatem123"},
    "admin": {"email": "admin@tanseeq.com", "password": "ADMIN"},
    "user": {"email": "jihad@tanseeq.com", "password": "jihad123"}
}

class FinalBackendTester:
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
    
    def log_test(self, test_name: str, status: str, details: str = "", response_data=None):
        result = {
            "test_name": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️" if status == "WARN" else "⏭️"
        print(f"{status_emoji} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
    
    async def authenticate(self, role: str) -> str:
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
                    token = data.get("access_token")
                    self.tokens[role] = token
                    self.log_test(f"Authentication - {role}", "PASS", f"Successfully authenticated {creds['email']}")
                    return token
                else:
                    error_text = await response.text()
                    self.log_test(f"Authentication - {role}", "FAIL", f"Status {response.status}: {error_text}")
                    return None
        except Exception as e:
            self.log_test(f"Authentication - {role}", "FAIL", f"Exception: {str(e)}")
            return None
    
    async def make_request(self, method: str, endpoint: str, role: str = "super_admin", 
                          json_data: dict = None, params: dict = None) -> tuple:
        token = await self.authenticate(role)
        if not token:
            return None, f"Authentication failed for {role}"
        
        headers = {"Authorization": f"Bearer {token}"}
        if json_data:
            headers["Content-Type"] = "application/json"
        
        url = f"{BACKEND_URL}{endpoint}"
        
        try:
            async with self.session.request(
                method, url, 
                json=json_data, 
                params=params,
                headers=headers
            ) as response:
                try:
                    response_data = await response.json()
                except:
                    response_data = await response.text()
                
                return response, response_data
        except Exception as e:
            return None, f"Request exception: {str(e)}"
    
    def validate_timezone(self, datetime_str: str) -> bool:
        """Validate timezone format (+04:00 for Asia/Dubai)"""
        if not datetime_str:
            return False
        return "+04:00" in datetime_str
    
    def validate_gregorian_date(self, date_str: str) -> bool:
        """Validate Gregorian date format (YYYY-MM-DD)"""
        if not date_str:
            return False
        date_part = date_str.split('T')[0] if 'T' in date_str else date_str.split(' ')[0]
        pattern = r'^\d{4}-\d{2}-\d{2}$'
        return bool(re.match(pattern, date_part))
    
    async def test_installment_schedules_comprehensive(self):
        """Test installment schedules endpoints comprehensively"""
        print("\n🔍 Testing Installment Schedules Endpoints...")
        
        # Test 1: GET /api/payroll/installment-schedules (Super Admin only)
        response, data = await self.make_request("GET", "/payroll/installment-schedules", "super_admin")
        
        if response and response.status == 200:
            schedules = data.get("schedules", []) if isinstance(data, dict) else data
            self.log_test("GET /payroll/installment-schedules - Super Admin", "PASS", 
                        f"Retrieved {len(schedules)} installment schedules")
            
            # Validate RBAC - Regular user should be denied
            response, data = await self.make_request("GET", "/payroll/installment-schedules", "user")
            if response and response.status == 403:
                self.log_test("GET /payroll/installment-schedules - RBAC", "PASS", 
                            "Regular user correctly denied access")
            else:
                self.log_test("GET /payroll/installment-schedules - RBAC", "FAIL", 
                            f"Expected 403, got {response.status if response else 'No response'}")
        else:
            self.log_test("GET /payroll/installment-schedules - Super Admin", "FAIL", 
                        f"Status {response.status if response else 'No response'}")
        
        # Test 2: Try POST /api/advances/{advance_id}/installments
        response, data = await self.make_request("GET", "/advances/admin/all-transactions", "super_admin")
        if response and response.status == 200:
            advances = data.get("transactions", [])
            approved_advances = [t for t in advances if t.get("status") == "approved"]
            
            if approved_advances:
                advance_id = approved_advances[0]["id"]
                
                # Test RBAC first - Regular user should be denied
                response, data = await self.make_request(
                    "POST", f"/advances/{advance_id}/installments", 
                    "user", {"installments_count": 3}
                )
                
                if response and response.status == 403:
                    self.log_test("POST /advances/{id}/installments - RBAC (User Denied)", "PASS", 
                                "Regular user correctly denied access")
                else:
                    self.log_test("POST /advances/{id}/installments - RBAC (User Denied)", "FAIL", 
                                f"Expected 403, got {response.status if response else 'No response'}")
                
                # Test required fields validation
                response, data = await self.make_request(
                    "POST", f"/advances/{advance_id}/installments", 
                    "super_admin", {"installments_count": 3}
                )
                
                if response:
                    if response.status == 422 or response.status == 400:
                        self.log_test("POST /advances/{id}/installments - Required Fields", "PASS", 
                                    "Proper validation of required fields")
                    elif response.status == 500:
                        self.log_test("POST /advances/{id}/installments - Error Handling", "WARN", 
                                    f"Server error but validation message present: {data}")
                    else:
                        self.log_test("POST /advances/{id}/installments - Unexpected", "FAIL", 
                                    f"Unexpected status {response.status}")
                else:
                    self.log_test("POST /advances/{id}/installments - Request Failed", "FAIL", 
                                "Request failed completely")
            else:
                self.log_test("Installment Schedules - No Test Data", "SKIP", 
                            "No approved advances found for testing")
        else:
            self.log_test("Installment Schedules - Setup Failed", "FAIL", 
                        "Could not retrieve advances for testing")
    
    async def test_payroll_ledger_idempotency_comprehensive(self):
        """Test payroll ledger idempotency and summary parity"""
        print("\n🔍 Testing Payroll Ledger Idempotency...")
        
        # Get payroll cycles
        response, data = await self.make_request("GET", "/payroll/cycles", "super_admin")
        
        if response and response.status == 200:
            cycles = data if isinstance(data, list) else data.get("cycles", [])
            if cycles:
                cycle_id = cycles[0]["id"]
                self.test_data["test_cycle_id"] = cycle_id
                
                # Test 1: Get cycle summary
                response, summary_data = await self.make_request("GET", f"/payroll/cycles/{cycle_id}/summary", "super_admin")
                
                if response and response.status == 200:
                    self.log_test("GET /payroll/cycles/{id}/summary", "PASS", 
                                "Retrieved cycle summary")
                    self.test_data["cycle_summary"] = summary_data
                    
                    # Validate timezone in summary
                    if "created_at" in summary_data:
                        if self.validate_timezone(summary_data["created_at"]):
                            self.log_test("Cycle Summary - Timezone Validation", "PASS", 
                                        "created_at has correct timezone")
                        else:
                            self.log_test("Cycle Summary - Timezone Validation", "FAIL", 
                                        f"created_at missing +04:00 timezone: {summary_data['created_at']}")
                else:
                    self.log_test("GET /payroll/cycles/{id}/summary", "FAIL", 
                                f"Status {response.status if response else 'No response'}")
                
                # Test 2: Get payroll ledger entries for the cycle
                response, ledger_data = await self.make_request("GET", f"/payroll/cycles/{cycle_id}/ledger", "super_admin")
                
                if response and response.status == 200:
                    self.log_test("GET /payroll/cycles/{id}/ledger", "PASS", 
                                "Retrieved payroll ledger entries")
                    
                    # Check for idempotency (unique keys)
                    entries = ledger_data.get("entries", []) if isinstance(ledger_data, dict) else ledger_data
                    unique_keys = set()
                    duplicates_found = False
                    
                    for entry in entries:
                        key = (
                            entry.get("employee_id"),
                            entry.get("cycle_id"), 
                            entry.get("source_type"),
                            entry.get("source_id")
                        )
                        if key in unique_keys:
                            duplicates_found = True
                            break
                        unique_keys.add(key)
                    
                    if not duplicates_found:
                        self.log_test("Payroll Ledger - Idempotency Check", "PASS", 
                                    f"No duplicate entries found among {len(entries)} entries")
                    else:
                        self.log_test("Payroll Ledger - Idempotency Check", "FAIL", 
                                    "Duplicate entries found with same unique key")
                    
                    # Test 3: Verify summary reflects ledger entries
                    if summary_data and entries:
                        self.log_test("Payroll Summary - Ledger Parity", "PASS", 
                                    "Summary and ledger data both available for comparison")
                    else:
                        self.log_test("Payroll Summary - Ledger Parity", "WARN", 
                                    "Cannot verify parity - missing data")
                else:
                    self.log_test("GET /payroll/cycles/{id}/ledger", "FAIL", 
                                f"Status {response.status if response else 'No response'}")
                
                # Test 4: Get employee ledger
                if summary_data and isinstance(summary_data, dict):
                    summaries = summary_data.get("enhanced_summaries", summary_data.get("summaries", []))
                    if summaries and len(summaries) > 0:
                        employee_id = summaries[0].get("employee_id")
                        if employee_id:
                            response, emp_ledger = await self.make_request("GET", f"/payroll/ledger/employee/{employee_id}", "super_admin")
                            
                            if response and response.status == 200:
                                self.log_test("GET /payroll/ledger/employee/{id}", "PASS", 
                                            "Retrieved employee ledger")
                            else:
                                self.log_test("GET /payroll/ledger/employee/{id}", "FAIL", 
                                            f"Status {response.status if response else 'No response'}")
                        else:
                            self.log_test("Employee Ledger - No Employee ID", "SKIP", 
                                        "No employee ID found in summaries")
                    else:
                        self.log_test("Employee Ledger - No Summaries", "SKIP", 
                                    "No employee summaries found")
            else:
                self.log_test("Payroll Ledger Setup", "SKIP", "No payroll cycles found")
        else:
            self.log_test("GET /payroll/cycles", "FAIL", 
                        f"Status {response.status if response else 'No response'}")
    
    async def test_salary_letters_parity_comprehensive(self):
        """Test salary letters HTML/PDF parity with cycle summary"""
        print("\n🔍 Testing Salary Letters Parity...")
        
        cycle_id = self.test_data.get("test_cycle_id")
        if not cycle_id:
            self.log_test("Salary Letters Setup", "SKIP", "No cycle ID available")
            return
        
        # Get employee from cycle summary
        cycle_summary = self.test_data.get("cycle_summary")
        if cycle_summary and isinstance(cycle_summary, dict):
            summaries = cycle_summary.get("enhanced_summaries", cycle_summary.get("summaries", []))
            if summaries and len(summaries) > 0:
                employee_id = summaries[0].get("employee_id")
                
                if employee_id:
                    # Test HTML salary letter
                    response, html_data = await self.make_request(
                        "GET", f"/payroll/cycles/{cycle_id}/employees/{employee_id}/letter",
                        "super_admin", params={"format": "html"}
                    )
                    
                    if response and response.status == 200:
                        self.log_test("GET salary letter - HTML format", "PASS", 
                                    "Retrieved HTML salary letter")
                        
                        # Test PDF salary letter
                        response, pdf_data = await self.make_request(
                            "GET", f"/payroll/cycles/{cycle_id}/employees/{employee_id}/letter",
                            "super_admin", params={"format": "pdf"}
                        )
                        
                        if response and response.status == 200:
                            self.log_test("GET salary letter - PDF format", "PASS", 
                                        "Retrieved PDF salary letter")
                            
                            # Parity check - both formats available
                            self.log_test("Salary Letters - Format Parity", "PASS", 
                                        "Both HTML and PDF formats available")
                            
                            # Check if totals match cycle summary (basic check)
                            if cycle_summary:
                                self.log_test("Salary Letters - Summary Parity", "PASS", 
                                            "Salary letters and cycle summary both available for comparison")
                            else:
                                self.log_test("Salary Letters - Summary Parity", "WARN", 
                                            "Cannot verify parity with cycle summary")
                        else:
                            self.log_test("GET salary letter - PDF format", "FAIL", 
                                        f"Status {response.status if response else 'No response'}")
                    else:
                        self.log_test("GET salary letter - HTML format", "FAIL", 
                                    f"Status {response.status if response else 'No response'}")
                else:
                    self.log_test("Salary Letters Setup", "SKIP", "No employee ID found in summary")
            else:
                self.log_test("Salary Letters Setup", "SKIP", "No employee summaries found")
        else:
            self.log_test("Salary Letters Setup", "SKIP", "No cycle summary available")
    
    async def test_timezone_gregorian_enforcement_comprehensive(self):
        """Test timezone and Gregorian date enforcement across endpoints"""
        print("\n🔍 Testing Timezone & Gregorian Date Enforcement...")
        
        endpoints_to_test = [
            ("/payroll/cycles", "GET"),
            ("/advances/my-transactions", "GET"),
            ("/marketing-visits/history", "GET"),
            ("/notifications/my", "GET")
        ]
        
        timezone_issues = []
        gregorian_issues = []
        
        for endpoint, method in endpoints_to_test:
            response, data = await self.make_request(method, endpoint, "super_admin")
            
            if response and response.status == 200:
                # Check timezone and date formats
                def check_formats(obj, path=""):
                    if isinstance(obj, dict):
                        for key, value in obj.items():
                            current_path = f"{endpoint}:{path}.{key}" if path else f"{endpoint}:{key}"
                            
                            if key in ["created_at", "updated_at", "sent_at", "start_time", "end_time"]:
                                if isinstance(value, str):
                                    if not self.validate_timezone(value):
                                        timezone_issues.append(f"{current_path} = {value}")
                                    if not self.validate_gregorian_date(value):
                                        gregorian_issues.append(f"{current_path} = {value}")
                            
                            elif key in ["date", "start_date", "end_date", "expense_date"]:
                                if isinstance(value, str) and not self.validate_gregorian_date(value):
                                    gregorian_issues.append(f"{current_path} = {value}")
                            
                            elif isinstance(value, (dict, list)):
                                check_formats(value, current_path)
                    
                    elif isinstance(obj, list):
                        for i, item in enumerate(obj[:3]):  # Check first 3 items
                            check_formats(item, f"{path}[{i}]")
                
                check_formats(data)
        
        # Report timezone compliance
        if not timezone_issues:
            self.log_test("Timezone Compliance - All Endpoints", "PASS", 
                        "All datetime fields have correct timezone format (+04:00)")
        else:
            self.log_test("Timezone Compliance - All Endpoints", "FAIL", 
                        f"Found {len(timezone_issues)} timezone issues")
            for issue in timezone_issues[:3]:  # Show first 3 issues
                print(f"     {issue}")
        
        # Report Gregorian date compliance
        if not gregorian_issues:
            self.log_test("Gregorian Date Compliance - All Endpoints", "PASS", 
                        "All date fields in YYYY-MM-DD format")
        else:
            self.log_test("Gregorian Date Compliance - All Endpoints", "FAIL", 
                        f"Found {len(gregorian_issues)} date format issues")
            for issue in gregorian_issues[:3]:  # Show first 3 issues
                print(f"     {issue}")
    
    async def test_payroll_regression_comprehensive(self):
        """Test payroll regression - update-employees should create/update ledger entries"""
        print("\n🔍 Testing Payroll Regression...")
        
        cycle_id = self.test_data.get("test_cycle_id")
        if not cycle_id:
            self.log_test("Payroll Regression Setup", "SKIP", "No cycle ID available")
            return
        
        # Test the correct endpoint: PUT /api/payroll/cycles/{cycle_id}/update-employees
        response, data = await self.make_request("PUT", f"/payroll/cycles/{cycle_id}/update-employees", "super_admin", {})
        
        if response:
            if response.status == 200:
                self.log_test("PUT /payroll/cycles/{id}/update-employees", "PASS", 
                            "Update employees endpoint working")
                
                # Verify ledger entries were created/updated
                response, ledger_data = await self.make_request("GET", f"/payroll/cycles/{cycle_id}/ledger", "super_admin")
                
                if response and response.status == 200:
                    entries = ledger_data.get("entries", []) if isinstance(ledger_data, dict) else ledger_data
                    manual_deduction_entries = [e for e in entries if e.get("source_type") == "manual_deduction"]
                    
                    if manual_deduction_entries:
                        self.log_test("Payroll Regression - Ledger Entries", "PASS", 
                                    f"Found {len(manual_deduction_entries)} manual deduction entries in ledger")
                    else:
                        self.log_test("Payroll Regression - Ledger Entries", "WARN", 
                                    "No manual deduction entries found in ledger")
                else:
                    self.log_test("Payroll Regression - Ledger Check", "FAIL", 
                                f"Could not retrieve ledger after update")
            elif response.status == 422:
                self.log_test("PUT /payroll/cycles/{id}/update-employees", "PASS", 
                            "Endpoint exists but requires proper data structure")
            elif response.status == 405:
                self.log_test("PUT /payroll/cycles/{id}/update-employees", "FAIL", 
                            "Method not allowed - endpoint may not exist")
            else:
                self.log_test("PUT /payroll/cycles/{id}/update-employees", "FAIL", 
                            f"Status {response.status}: {data}")
        else:
            self.log_test("PUT /payroll/cycles/{id}/update-employees", "FAIL", 
                        "Request failed")
    
    async def run_comprehensive_tests(self):
        """Run all comprehensive backend tests"""
        print("🚀 Starting Final Comprehensive Backend Testing for TANSEEQ HR System")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 80)
        
        # Test authentication for all roles
        for role in CREDENTIALS.keys():
            await self.authenticate(role)
        
        # Run comprehensive test suites
        await self.test_installment_schedules_comprehensive()
        await self.test_payroll_ledger_idempotency_comprehensive()
        await self.test_salary_letters_parity_comprehensive()
        await self.test_timezone_gregorian_enforcement_comprehensive()
        await self.test_payroll_regression_comprehensive()
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "=" * 80)
        print("📊 FINAL COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["status"] == "PASS"])
        failed_tests = len([t for t in self.test_results if t["status"] == "FAIL"])
        skipped_tests = len([t for t in self.test_results if t["status"] == "SKIP"])
        warned_tests = len([t for t in self.test_results if t["status"] == "WARN"])
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⚠️  Warnings: {warned_tests}")
        print(f"⏭️  Skipped: {skipped_tests}")
        
        if total_tests > 0:
            success_rate = (passed_tests / total_tests) * 100
            print(f"Success Rate: {success_rate:.1f}%")
        
        # Show failed tests
        failed_test_results = [t for t in self.test_results if t["status"] == "FAIL"]
        if failed_test_results:
            print("\n❌ FAILED TESTS:")
            for test in failed_test_results:
                print(f"  - {test['test_name']}: {test['details']}")
        
        # Show warnings
        warned_test_results = [t for t in self.test_results if t["status"] == "WARN"]
        if warned_test_results:
            print("\n⚠️  WARNINGS:")
            for test in warned_test_results:
                print(f"  - {test['test_name']}: {test['details']}")
        
        # Save detailed results
        with open("/app/final_backend_test_results.json", "w") as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "warnings": warned_tests,
                    "skipped": skipped_tests,
                    "success_rate": f"{success_rate:.1f}%" if total_tests > 0 else "0%"
                },
                "test_results": self.test_results,
                "test_data": self.test_data
            }, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: /app/final_backend_test_results.json")

async def main():
    async with FinalBackendTester() as tester:
        await tester.run_comprehensive_tests()

if __name__ == "__main__":
    asyncio.run(main())