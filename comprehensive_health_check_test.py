#!/usr/bin/env python3
"""
🔍 COMPREHENSIVE HEALTH CHECK - Pre-Deployment Validation for TANSEEQ HR System
Testing all critical APIs as requested in the review
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
import uuid

# Backend URL from environment
BACKEND_URL = "https://hrapp-tanseeq.emergent.host/api"

# Test credentials as specified in review
CREDENTIALS = {
    "super_admin": {"email": "admin@tanseeq.com", "password": "ADMIN"},
    "admin": {"email": "mahmoud@tanseeq.com", "password": "mahmoud123"},
    "user": {"email": "jihad@tanseeq.com", "password": "jihad123"}
}

class HealthCheckTester:
    def __init__(self):
        self.session = None
        self.tokens = {}
        self.test_results = []
        self.critical_issues = []
        self.success_count = 0
        self.total_tests = 0
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, status: str, details: str = "", response_data: Any = None):
        """Log test result"""
        self.total_tests += 1
        if status == "✅ PASS":
            self.success_count += 1
        elif status == "❌ FAIL":
            self.critical_issues.append(f"{test_name}: {details}")
            
        result = {
            "test_name": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        print(f"{status} {test_name}: {details}")
    
    async def make_request(self, method: str, endpoint: str, data: Dict = None, 
                          headers: Dict = None, params: Dict = None) -> Dict:
        """Make HTTP request with error handling"""
        url = f"{BACKEND_URL}{endpoint}"
        
        try:
            async with self.session.request(
                method, url, json=data, headers=headers, params=params
            ) as response:
                response_text = await response.text()
                
                try:
                    response_data = json.loads(response_text) if response_text else {}
                except json.JSONDecodeError:
                    response_data = {"raw_response": response_text}
                
                return {
                    "status_code": response.status,
                    "data": response_data,
                    "headers": dict(response.headers)
                }
        except Exception as e:
            return {
                "status_code": 0,
                "data": {"error": str(e)},
                "headers": {}
            }
    
    async def authenticate(self, role: str) -> bool:
        """Authenticate user and store token"""
        if role not in CREDENTIALS:
            self.log_test(f"Authentication Setup - {role}", "❌ FAIL", f"Unknown role: {role}")
            return False
            
        creds = CREDENTIALS[role]
        
        response = await self.make_request(
            "POST", "/auth/login",
            data={"email": creds["email"], "password": creds["password"]}
        )
        
        if response["status_code"] == 200 and "access_token" in response["data"]:
            self.tokens[role] = response["data"]["access_token"]
            user_info = response["data"].get("user", {})
            self.log_test(
                f"Authentication - {role}", 
                "✅ PASS", 
                f"Login successful for {creds['email']} (Role: {user_info.get('role', 'unknown')})"
            )
            return True
        else:
            self.log_test(
                f"Authentication - {role}", 
                "❌ FAIL", 
                f"Login failed for {creds['email']}: {response['data']}"
            )
            return False
    
    def get_auth_headers(self, role: str) -> Dict:
        """Get authorization headers for role"""
        if role in self.tokens:
            return {"Authorization": f"Bearer {self.tokens[role]}"}
        return {}
    
    async def test_health_endpoints(self):
        """Test health and readiness endpoints"""
        print("\n🏥 TESTING HEALTH ENDPOINTS")
        
        # Test /api/healthz
        response = await self.make_request("GET", "/healthz")
        if response["status_code"] == 200 and response["data"].get("status") == "ok":
            self.log_test("Health Check", "✅ PASS", "Health endpoint responding correctly")
        else:
            self.log_test("Health Check", "❌ FAIL", f"Health endpoint failed: {response}")
        
        # Test /api/readyz
        response = await self.make_request("GET", "/readyz")
        if response["status_code"] == 200 and response["data"].get("status") == "ready":
            self.log_test("Readiness Check", "✅ PASS", "Readiness endpoint responding correctly")
        else:
            self.log_test("Readiness Check", "❌ FAIL", f"Readiness endpoint failed: {response}")
    
    async def test_authentication_system(self):
        """Test authentication system with Super Admin credentials"""
        print("\n🔐 TESTING AUTHENTICATION SYSTEM")
        
        # Test Super Admin login as specified in review
        success = await self.authenticate("super_admin")
        if success:
            # Test JWT token structure
            token = self.tokens.get("super_admin", "")
            if len(token.split('.')) == 3:  # JWT has 3 parts
                self.log_test("JWT Token Structure", "✅ PASS", "JWT token has correct structure")
            else:
                self.log_test("JWT Token Structure", "❌ FAIL", "JWT token structure invalid")
        
        # Test /auth/me endpoint
        if "super_admin" in self.tokens:
            response = await self.make_request(
                "GET", "/auth/me", 
                headers=self.get_auth_headers("super_admin")
            )
            if response["status_code"] == 200:
                user_data = response["data"]
                self.log_test(
                    "User Info Endpoint", 
                    "✅ PASS", 
                    f"User info retrieved: {user_data.get('name', 'Unknown')} ({user_data.get('role', 'Unknown')})"
                )
            else:
                self.log_test("User Info Endpoint", "❌ FAIL", f"Failed to get user info: {response}")
    
    async def test_advanced_deductions_system(self):
        """Test Advanced Deductions System - PRIMARY FOCUS"""
        print("\n💰 TESTING ADVANCED DEDUCTIONS SYSTEM (PRIMARY FOCUS)")
        
        if "super_admin" not in self.tokens:
            self.log_test("Deductions System", "❌ FAIL", "No Super Admin authentication")
            return
        
        headers = self.get_auth_headers("super_admin")
        
        # A. Monthly Calculation Endpoint
        response = await self.make_request(
            "POST", "/deductions/calculate-monthly",
            params={"month": "2025-10"},
            headers=headers
        )
        
        if response["status_code"] == 200:
            data = response["data"]
            success = data.get("success", False)
            mode = data.get("mode", "")
            cycle_window = data.get("cycle_window", {})
            employees = data.get("employees", [])
            
            if success and mode == "monthly" and employees:
                # Check cycle window dates
                expected_from = "2025-09-29"
                expected_to = "2025-10-28"
                actual_from = cycle_window.get("from_date", "")
                actual_to = cycle_window.get("to_date", "")
                
                if expected_from in actual_from and expected_to in actual_to:
                    self.log_test(
                        "Monthly Deductions Calculation", 
                        "✅ PASS", 
                        f"Monthly calculation working: {len(employees)} employees, cycle {actual_from} to {actual_to}"
                    )
                    
                    # Check for daily breakdown
                    has_daily_data = any(
                        emp.get("daily_breakdown") or emp.get("daily_records") 
                        for emp in employees
                    )
                    if has_daily_data:
                        self.log_test(
                            "Daily Breakdown Data", 
                            "✅ PASS", 
                            "Employees have daily breakdown/records data"
                        )
                    else:
                        self.log_test(
                            "Daily Breakdown Data", 
                            "❌ FAIL", 
                            "Missing daily breakdown/records in employee data"
                        )
                else:
                    self.log_test(
                        "Monthly Deductions Calculation", 
                        "❌ FAIL", 
                        f"Incorrect cycle window: expected {expected_from} to {expected_to}, got {actual_from} to {actual_to}"
                    )
            else:
                self.log_test(
                    "Monthly Deductions Calculation", 
                    "❌ FAIL", 
                    f"Invalid response structure: success={success}, mode={mode}, employees_count={len(employees)}"
                )
        else:
            self.log_test(
                "Monthly Deductions Calculation", 
                "❌ FAIL", 
                f"HTTP {response['status_code']}: {response['data']}"
            )
        
        # B. Custom Period Calculation Endpoint
        response = await self.make_request(
            "POST", "/deductions/calculate",
            params={
                "mode": "custom",
                "from_date": "2025-10-01",
                "to_date": "2025-10-15"
            },
            headers=headers
        )
        
        if response["status_code"] == 200:
            data = response["data"]
            success = data.get("success", False)
            mode = data.get("mode", "")
            period = data.get("period", {})
            employees = data.get("employees", [])
            
            if success and mode == "custom" and employees:
                # Check period dates
                from_date = period.get("from_date", "")
                to_date = period.get("to_date", "")
                
                if "2025-10-01" in from_date and "2025-10-15" in to_date:
                    self.log_test(
                        "Custom Period Deductions", 
                        "✅ PASS", 
                        f"Custom period calculation working: {len(employees)} employees, {from_date} to {to_date}"
                    )
                    
                    # Check for daily breakdown
                    has_daily_data = any(
                        emp.get("daily_breakdown") or emp.get("daily_records") 
                        for emp in employees
                    )
                    if has_daily_data:
                        self.log_test(
                            "Custom Period Daily Data", 
                            "✅ PASS", 
                            "Custom period has daily breakdown data"
                        )
                    else:
                        self.log_test(
                            "Custom Period Daily Data", 
                            "❌ FAIL", 
                            "Missing daily breakdown in custom period"
                        )
                        
                    # Check for preview note
                    if "preview" in str(data).lower():
                        self.log_test(
                            "Preview Mode Indicator", 
                            "✅ PASS", 
                            "Preview-only note present in custom period"
                        )
                else:
                    self.log_test(
                        "Custom Period Deductions", 
                        "❌ FAIL", 
                        f"Incorrect period: expected 2025-10-01 to 2025-10-15, got {from_date} to {to_date}"
                    )
            else:
                self.log_test(
                    "Custom Period Deductions", 
                    "❌ FAIL", 
                    f"Invalid response: success={success}, mode={mode}, employees_count={len(employees)}"
                )
        else:
            self.log_test(
                "Custom Period Deductions", 
                "❌ FAIL", 
                f"HTTP {response['status_code']}: {response['data']}"
            )
        
        # C. Apply Monthly Deductions Endpoint
        apply_data = {
            "month": "2025-10",
            "employees": [
                {"employee_id": "test-id", "deduction_amount": 100.0}
            ],
            "notes": "Health Check Test Application"
        }
        
        response = await self.make_request(
            "POST", "/deductions/apply-monthly",
            data=apply_data,
            headers=headers
        )
        
        if response["status_code"] == 200:
            data = response["data"]
            if "employees" in str(data) and "deduction" in str(data).lower():
                self.log_test(
                    "Apply Monthly Deductions", 
                    "✅ PASS", 
                    f"Apply endpoint working: {data}"
                )
            else:
                self.log_test(
                    "Apply Monthly Deductions", 
                    "⚠️ PARTIAL", 
                    f"Apply endpoint responded but format unclear: {data}"
                )
        else:
            # 422 might be expected for validation, check if it's reasonable
            if response["status_code"] == 422:
                self.log_test(
                    "Apply Monthly Deductions", 
                    "⚠️ PARTIAL", 
                    f"Validation error (expected): {response['data']}"
                )
            else:
                self.log_test(
                    "Apply Monthly Deductions", 
                    "❌ FAIL", 
                    f"HTTP {response['status_code']}: {response['data']}"
                )
    
    async def test_users_employees_management(self):
        """Test Users/Employees Management"""
        print("\n👥 TESTING USERS/EMPLOYEES MANAGEMENT")
        
        if "super_admin" not in self.tokens:
            self.log_test("Users Management", "❌ FAIL", "No Super Admin authentication")
            return
        
        headers = self.get_auth_headers("super_admin")
        
        # Test GET /api/users
        response = await self.make_request("GET", "/users", headers=headers)
        
        if response["status_code"] == 200:
            users = response["data"]
            if isinstance(users, list) and len(users) > 0:
                # Check for key users mentioned in review
                user_emails = [user.get("email", "") for user in users if isinstance(user, dict)]
                key_users = ["admin@tanseeq.com", "mahmoud@tanseeq.com", "jihad@tanseeq.com"]
                found_users = [email for email in key_users if email in user_emails]
                
                self.log_test(
                    "Users List Retrieval", 
                    "✅ PASS", 
                    f"Retrieved {len(users)} users, key users found: {found_users}"
                )
                
                # Check user structure
                if users and isinstance(users[0], dict):
                    required_fields = ["id", "name", "email", "role"]
                    has_required = all(field in users[0] for field in required_fields)
                    if has_required:
                        self.log_test(
                            "User Data Structure", 
                            "✅ PASS", 
                            f"Users have required fields: {required_fields}"
                        )
                    else:
                        self.log_test(
                            "User Data Structure", 
                            "❌ FAIL", 
                            f"Missing required fields in user data"
                        )
            else:
                self.log_test(
                    "Users List Retrieval", 
                    "❌ FAIL", 
                    f"Invalid users data: {type(users)} with length {len(users) if hasattr(users, '__len__') else 'N/A'}"
                )
        else:
            self.log_test(
                "Users List Retrieval", 
                "❌ FAIL", 
                f"HTTP {response['status_code']}: {response['data']}"
            )
    
    async def test_attendance_data(self):
        """Test Attendance Data"""
        print("\n📅 TESTING ATTENDANCE DATA")
        
        if "super_admin" not in self.tokens:
            self.log_test("Attendance Data", "❌ FAIL", "No Super Admin authentication")
            return
        
        headers = self.get_auth_headers("super_admin")
        
        # Test GET /api/attendance
        response = await self.make_request("GET", "/attendance", headers=headers)
        
        if response["status_code"] == 200:
            attendance = response["data"]
            if isinstance(attendance, list) and len(attendance) > 0:
                # Check attendance record structure
                record = attendance[0]
                required_fields = ["date", "user_id", "status"]
                optional_fields = ["check_in", "check_out"]
                
                has_required = all(field in record for field in required_fields)
                has_some_optional = any(field in record for field in optional_fields)
                
                if has_required:
                    self.log_test(
                        "Attendance Data Retrieval", 
                        "✅ PASS", 
                        f"Retrieved {len(attendance)} attendance records with required fields"
                    )
                    
                    if has_some_optional:
                        self.log_test(
                            "Attendance Record Structure", 
                            "✅ PASS", 
                            f"Records have check-in/check-out data"
                        )
                    else:
                        self.log_test(
                            "Attendance Record Structure", 
                            "⚠️ PARTIAL", 
                            f"Records missing check-in/check-out data"
                        )
                else:
                    self.log_test(
                        "Attendance Data Retrieval", 
                        "❌ FAIL", 
                        f"Missing required fields in attendance records"
                    )
            else:
                self.log_test(
                    "Attendance Data Retrieval", 
                    "❌ FAIL", 
                    f"Invalid attendance data: {type(attendance)}"
                )
        else:
            self.log_test(
                "Attendance Data Retrieval", 
                "❌ FAIL", 
                f"HTTP {response['status_code']}: {response['data']}"
            )
    
    async def test_payroll_ledger(self):
        """Test Payroll Ledger"""
        print("\n💼 TESTING PAYROLL LEDGER")
        
        if "super_admin" not in self.tokens:
            self.log_test("Payroll Ledger", "❌ FAIL", "No Super Admin authentication")
            return
        
        headers = self.get_auth_headers("super_admin")
        
        # Test GET /api/payroll/cycles
        response = await self.make_request("GET", "/payroll/cycles", headers=headers)
        
        if response["status_code"] == 200:
            cycles = response["data"]
            if isinstance(cycles, list):
                self.log_test(
                    "Payroll Cycles Retrieval", 
                    "✅ PASS", 
                    f"Retrieved {len(cycles)} payroll cycles"
                )
                
                # Check cycle structure if cycles exist
                if cycles and isinstance(cycles[0], dict):
                    cycle = cycles[0]
                    expected_fields = ["id", "month", "year"]
                    has_expected = any(field in cycle for field in expected_fields)
                    
                    if has_expected:
                        self.log_test(
                            "Payroll Cycle Structure", 
                            "✅ PASS", 
                            f"Cycles have proper structure"
                        )
                    else:
                        self.log_test(
                            "Payroll Cycle Structure", 
                            "❌ FAIL", 
                            f"Cycles missing expected fields"
                        )
            else:
                self.log_test(
                    "Payroll Cycles Retrieval", 
                    "❌ FAIL", 
                    f"Invalid cycles data type: {type(cycles)}"
                )
        else:
            self.log_test(
                "Payroll Cycles Retrieval", 
                "❌ FAIL", 
                f"HTTP {response['status_code']}: {response['data']}"
            )
    
    async def run_comprehensive_health_check(self):
        """Run complete health check as requested in review"""
        print("🔍 STARTING COMPREHENSIVE HEALTH CHECK - Pre-Deployment Validation")
        print("=" * 80)
        
        # Test in the order specified in the review
        await self.test_health_endpoints()
        await self.test_authentication_system()
        await self.test_advanced_deductions_system()
        await self.test_users_employees_management()
        await self.test_attendance_data()
        await self.test_payroll_ledger()
        
        # Generate final report
        await self.generate_health_report()
    
    async def generate_health_report(self):
        """Generate comprehensive health check report"""
        print("\n" + "=" * 80)
        print("🏥 COMPREHENSIVE HEALTH CHECK REPORT")
        print("=" * 80)
        
        success_rate = (self.success_count / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"📊 OVERALL HEALTH: {self.success_count}/{self.total_tests} tests passed ({success_rate:.1f}%)")
        
        if success_rate >= 90:
            print("🟢 SYSTEM STATUS: EXCELLENT - Ready for production")
        elif success_rate >= 75:
            print("🟡 SYSTEM STATUS: GOOD - Minor issues need attention")
        elif success_rate >= 50:
            print("🟠 SYSTEM STATUS: FAIR - Several issues need fixing")
        else:
            print("🔴 SYSTEM STATUS: POOR - Critical issues must be resolved")
        
        # Critical issues summary
        if self.critical_issues:
            print(f"\n❌ CRITICAL ISSUES FOUND ({len(self.critical_issues)}):")
            for i, issue in enumerate(self.critical_issues, 1):
                print(f"  {i}. {issue}")
        else:
            print("\n✅ NO CRITICAL ISSUES FOUND")
        
        # Success indicators check
        print(f"\n✅ SUCCESS INDICATORS:")
        success_indicators = [
            "Health endpoints responding",
            "JWT authentication working", 
            "Advanced Deductions operational",
            "Users management accessible",
            "Attendance data available",
            "Payroll cycles accessible"
        ]
        
        for indicator in success_indicators:
            # Simple check based on test results
            found = any(indicator.lower() in result["test_name"].lower() 
                       and result["status"] == "✅ PASS" 
                       for result in self.test_results)
            status = "✅" if found else "❌"
            print(f"  {status} {indicator}")
        
        # Production readiness assessment
        print(f"\n🚀 PRODUCTION READINESS ASSESSMENT:")
        if success_rate >= 90 and len(self.critical_issues) == 0:
            print("✅ SYSTEM READY FOR DEPLOYMENT")
            print("   - All critical APIs working")
            print("   - No blocking issues found")
            print("   - Authentication system operational")
        else:
            print("❌ SYSTEM NOT READY FOR DEPLOYMENT")
            print("   - Critical issues must be resolved first")
            print("   - Recommend fixing issues before proceeding")
        
        # Save detailed results
        results_file = "/app/comprehensive_health_check_results.json"
        with open(results_file, "w") as f:
            json.dump({
                "summary": {
                    "total_tests": self.total_tests,
                    "passed_tests": self.success_count,
                    "success_rate": success_rate,
                    "critical_issues_count": len(self.critical_issues)
                },
                "critical_issues": self.critical_issues,
                "detailed_results": self.test_results,
                "timestamp": datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: {results_file}")

async def main():
    """Main test execution"""
    async with HealthCheckTester() as tester:
        await tester.run_comprehensive_health_check()

if __name__ == "__main__":
    asyncio.run(main())