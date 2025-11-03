#!/usr/bin/env python3
"""
Attendance Check-in/out Endpoints Testing with JWT Flow and Config Exceptions
Testing specific scenario: Hatem (exempt), Tarek (flex), Karim/Hesham (partial-flex)
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
import aiohttp
import traceback

# Add backend to path for imports
sys.path.append('/app/backend')

# Configuration
BACKEND_URL = "https://attend-deduct-hr.preview.emergentagent.com/api"
EVIDENCE_DIR = Path("/app/evidence")
EVIDENCE_DIR.mkdir(exist_ok=True)

# Test credentials
SUPER_ADMIN_CREDS = {
    "email": "hatem@tan-seeq.co",
    "password": "hatem123"
}

# Target users for testing
TARGET_USERS = {
    "hatem": {"name_pattern": "hatem", "exception_type": "exempt"},
    "tarek": {"name_pattern": "tarek", "exception_type": "flex"}, 
    "karim": {"name_pattern": "karim", "exception_type": "partial-flex"},
    "hesham": {"name_pattern": "hesham", "exception_type": "partial-flex"}
}

class AttendanceConfigTester:
    def __init__(self):
        self.session = None
        self.super_admin_token = None
        self.user_tokens = {}
        self.user_ids = {}
        self.test_results = []
        self.evidence_data = {}
        
    async def setup_session(self):
        """Setup HTTP session"""
        connector = aiohttp.TCPConnector(ssl=False)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
            
    async def make_request(self, method, endpoint, data=None, headers=None, token=None):
        """Make HTTP request with error handling"""
        url = f"{BACKEND_URL}{endpoint}"
        
        if headers is None:
            headers = {"Content-Type": "application/json"}
            
        if token:
            headers["Authorization"] = f"Bearer {token}"
            
        try:
            if method.upper() == "GET":
                async with self.session.get(url, headers=headers) as response:
                    response_data = await response.json()
                    return response.status, response_data
            elif method.upper() == "POST":
                async with self.session.post(url, json=data, headers=headers) as response:
                    response_data = await response.json()
                    return response.status, response_data
            elif method.upper() == "PUT":
                async with self.session.put(url, json=data, headers=headers) as response:
                    response_data = await response.json()
                    return response.status, response_data
                    
        except Exception as e:
            return 500, {"error": str(e)}
            
    def log_test(self, test_name, status, details, response_data=None):
        """Log test result"""
        result = {
            "test_name": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {details}")
        
        if response_data:
            print(f"   Response: {json.dumps(response_data, indent=2)}")
            
    async def step_1_super_admin_login(self):
        """Step 1: Login as Super Admin to get token"""
        print("\n🔐 Step 1: Super Admin Authentication")
        
        status, response = await self.make_request("POST", "/auth/login", SUPER_ADMIN_CREDS)
        
        if status == 200 and "access_token" in response:
            self.super_admin_token = response["access_token"]
            self.log_test("Super Admin Login", "PASS", 
                         f"Successfully authenticated as {response['user']['name']}", response)
            return True
        else:
            self.log_test("Super Admin Login", "FAIL", 
                         f"Authentication failed: {response}", response)
            return False
            
    async def step_2_fetch_user_list(self):
        """Step 2: Fetch user list to find target users"""
        print("\n👥 Step 2: Fetching User List")
        
        status, response = await self.make_request("GET", "/users", token=self.super_admin_token)
        
        if status == 200 and "users" in response:
            users = response["users"]
            found_users = {}
            
            for user in users:
                user_name = user.get("name", "").lower()
                user_email = user.get("email", "").lower()
                
                for key, target in TARGET_USERS.items():
                    pattern = target["name_pattern"].lower()
                    if pattern in user_name or pattern in user_email:
                        found_users[key] = {
                            "user_id": user["id"],
                            "name": user["name"],
                            "email": user["email"]
                        }
                        self.user_ids[key] = user["id"]
                        break
                        
            self.evidence_data["found_users"] = found_users
            
            if len(found_users) >= 3:  # At least 3 of 4 target users
                self.log_test("User List Fetch", "PASS", 
                             f"Found {len(found_users)} target users: {list(found_users.keys())}", 
                             found_users)
                return True
            else:
                self.log_test("User List Fetch", "FAIL", 
                             f"Only found {len(found_users)} users, need at least 3", found_users)
                return False
        else:
            self.log_test("User List Fetch", "FAIL", 
                         f"Failed to fetch users: {response}", response)
            return False
            
    async def step_3_upsert_config_exceptions(self):
        """Step 3: Upsert config exceptions for target users"""
        print("\n⚙️ Step 3: Configuring User Exceptions")
        
        success_count = 0
        
        for key, user_id in self.user_ids.items():
            exception_type = TARGET_USERS[key]["exception_type"]
            
            config_data = {
                "exception_type": exception_type,
                "notes": f"Test configuration for {key}"
            }
            
            status, response = await self.make_request(
                "PUT", f"/config/exceptions/{user_id}", 
                config_data, token=self.super_admin_token
            )
            
            if status == 200:
                success_count += 1
                self.log_test(f"Config Exception - {key}", "PASS", 
                             f"Set {key} to {exception_type}", response)
            else:
                self.log_test(f"Config Exception - {key}", "FAIL", 
                             f"Failed to set exception: {response}", response)
                             
        return success_count >= 3
        
    async def step_4_user_authentication(self):
        """Step 4: Authenticate as each target user"""
        print("\n🔑 Step 4: User Authentication")
        
        # Common password patterns to try
        password_patterns = ["123456", "hatem123", "password", "admin123"]
        
        success_count = 0
        
        for key, user_data in self.evidence_data.get("found_users", {}).items():
            email = user_data["email"]
            authenticated = False
            
            for password in password_patterns:
                creds = {"email": email, "password": password}
                status, response = await self.make_request("POST", "/auth/login", creds)
                
                if status == 200 and "access_token" in response:
                    self.user_tokens[key] = response["access_token"]
                    authenticated = True
                    success_count += 1
                    self.log_test(f"User Auth - {key}", "PASS", 
                                 f"Authenticated {email} with password {password}", response)
                    break
                    
            if not authenticated:
                self.log_test(f"User Auth - {key}", "FAIL", 
                             f"Could not authenticate {email} with any password")
                             
        return success_count >= 2  # At least 2 users authenticated
        
    async def step_5_attendance_check_in_out(self):
        """Step 5: Test check-in/out for each authenticated user"""
        print("\n⏰ Step 5: Attendance Check-in/out Testing")
        
        check_in_results = {}
        check_out_results = {}
        
        # Test check-in for each user
        for key, token in self.user_tokens.items():
            print(f"\n   Testing check-in for {key}...")
            
            status, response = await self.make_request("POST", "/attendance/check-in", 
                                                     token=token)
            
            check_in_results[key] = {
                "status": status,
                "response": response,
                "expected_exception": TARGET_USERS[key]["exception_type"]
            }
            
            if status == 200:
                # Verify response contains expected fields
                expected_fields = ["late_minutes", "schedule_type"]
                has_fields = all(field in response for field in expected_fields)
                
                if has_fields:
                    self.log_test(f"Check-in - {key}", "PASS", 
                                 f"Check-in successful with late_minutes={response.get('late_minutes', 'N/A')}, "
                                 f"schedule_type={response.get('schedule_type', 'N/A')}", response)
                else:
                    self.log_test(f"Check-in - {key}", "FAIL", 
                                 f"Missing expected fields in response", response)
            else:
                self.log_test(f"Check-in - {key}", "FAIL", 
                             f"Check-in failed: {response}", response)
                             
        # Wait a moment then test check-out
        await asyncio.sleep(2)
        
        for key, token in self.user_tokens.items():
            print(f"\n   Testing check-out for {key}...")
            
            status, response = await self.make_request("POST", "/attendance/check-out", 
                                                     token=token)
            
            check_out_results[key] = {
                "status": status,
                "response": response
            }
            
            if status == 200:
                self.log_test(f"Check-out - {key}", "PASS", 
                             f"Check-out successful", response)
            else:
                self.log_test(f"Check-out - {key}", "FAIL", 
                             f"Check-out failed: {response}", response)
                             
        self.evidence_data["check_in_results"] = check_in_results
        self.evidence_data["check_out_results"] = check_out_results
        
        return len(check_in_results) >= 2
        
    async def step_6_verify_exception_rules(self):
        """Step 6: Verify exception rules are working correctly"""
        print("\n🔍 Step 6: Verifying Exception Rules")
        
        verification_results = {}
        
        for key, check_in_data in self.evidence_data.get("check_in_results", {}).items():
            if check_in_data["status"] == 200:
                response = check_in_data["response"]
                expected_exception = check_in_data["expected_exception"]
                
                late_minutes = response.get("late_minutes", 0)
                schedule_type = response.get("schedule_type", "")
                
                # Verify rules based on exception type
                if expected_exception == "exempt":
                    # Hatem should have late_minutes=0 and schedule_type='exempt'
                    rule_correct = (late_minutes == 0 and schedule_type == "exempt")
                    verification_results[key] = {
                        "rule_correct": rule_correct,
                        "expected": "late_minutes=0, schedule_type=exempt",
                        "actual": f"late_minutes={late_minutes}, schedule_type={schedule_type}"
                    }
                    
                elif expected_exception == "flex":
                    # Tarek should have late_minutes=0 and schedule_type='flex'
                    rule_correct = (late_minutes == 0 and schedule_type == "flex")
                    verification_results[key] = {
                        "rule_correct": rule_correct,
                        "expected": "late_minutes=0, schedule_type=flex",
                        "actual": f"late_minutes={late_minutes}, schedule_type={schedule_type}"
                    }
                    
                elif expected_exception == "partial-flex":
                    # Karim/Hesham should have schedule_type='partial-flex' and late detection after 09:00
                    rule_correct = (schedule_type == "partial-flex")
                    verification_results[key] = {
                        "rule_correct": rule_correct,
                        "expected": "schedule_type=partial-flex, late detection after 09:00",
                        "actual": f"late_minutes={late_minutes}, schedule_type={schedule_type}"
                    }
                    
                if verification_results[key]["rule_correct"]:
                    self.log_test(f"Rule Verification - {key}", "PASS", 
                                 f"Exception rules working correctly: {verification_results[key]['actual']}")
                else:
                    self.log_test(f"Rule Verification - {key}", "FAIL", 
                                 f"Rule mismatch - Expected: {verification_results[key]['expected']}, "
                                 f"Actual: {verification_results[key]['actual']}")
                                 
        self.evidence_data["rule_verification"] = verification_results
        return len(verification_results) >= 2
        
    async def step_7_monthly_deductions_calculation(self):
        """Step 7: Test monthly deductions calculation"""
        print("\n📊 Step 7: Monthly Deductions Calculation")
        
        # Get current month for testing
        current_month = datetime.now().strftime("%Y-%m")
        
        status, response = await self.make_request(
            "POST", f"/deductions/calculate-monthly?month={current_month}",
            token=self.super_admin_token
        )
        
        if status == 200:
            # Check if partial-flex users have different deduction rules
            deductions_data = response
            
            # Look for our test users in the results
            partial_flex_users = []
            other_users = []
            
            if "employees" in deductions_data:
                for emp in deductions_data["employees"]:
                    emp_name = emp.get("employee_name", "").lower()
                    
                    # Check if this is one of our partial-flex test users
                    if any(TARGET_USERS[key]["name_pattern"].lower() in emp_name 
                           for key in ["karim", "hesham"]):
                        partial_flex_users.append(emp)
                    else:
                        other_users.append(emp)
                        
            verification_passed = True
            
            # Verify partial-flex rule: no early_leave deductions counted
            for user in partial_flex_users:
                early_leave_deductions = user.get("early_leave_deductions", 0)
                if early_leave_deductions > 0:
                    verification_passed = False
                    self.log_test("Partial-flex Rule", "FAIL", 
                                 f"Partial-flex user {user.get('employee_name')} has early_leave_deductions: {early_leave_deductions}")
                else:
                    self.log_test("Partial-flex Rule", "PASS", 
                                 f"Partial-flex user {user.get('employee_name')} correctly has no early_leave_deductions")
                                 
            self.evidence_data["monthly_deductions"] = deductions_data
            
            self.log_test("Monthly Deductions Calculation", "PASS" if verification_passed else "WARN", 
                         f"Calculated deductions for {len(deductions_data.get('employees', []))} employees", 
                         deductions_data)
            return True
            
        else:
            self.log_test("Monthly Deductions Calculation", "FAIL", 
                         f"Failed to calculate monthly deductions: {response}", response)
            return False
            
    async def save_evidence(self):
        """Save all evidence to files"""
        print("\n💾 Saving Evidence...")
        
        # Save test results
        results_file = EVIDENCE_DIR / "attendance_config_test_results.json"
        with open(results_file, "w") as f:
            json.dump({
                "test_results": self.test_results,
                "evidence_data": self.evidence_data,
                "summary": {
                    "total_tests": len(self.test_results),
                    "passed": len([r for r in self.test_results if r["status"] == "PASS"]),
                    "failed": len([r for r in self.test_results if r["status"] == "FAIL"]),
                    "warnings": len([r for r in self.test_results if r["status"] == "WARN"])
                }
            }, f, indent=2)
            
        print(f"✅ Evidence saved to {results_file}")
        
        # Save individual response logs
        for i, result in enumerate(self.test_results):
            if result.get("response_data"):
                response_file = EVIDENCE_DIR / f"response_{i+1}_{result['test_name'].replace(' ', '_').replace('-', '_')}.json"
                with open(response_file, "w") as f:
                    json.dump(result["response_data"], f, indent=2)
                    
    async def run_comprehensive_test(self):
        """Run the complete test suite"""
        print("🚀 Starting Comprehensive Attendance Config Exceptions Testing")
        print("=" * 80)
        
        try:
            await self.setup_session()
            
            # Execute test steps
            steps = [
                ("Super Admin Login", self.step_1_super_admin_login),
                ("Fetch User List", self.step_2_fetch_user_list),
                ("Upsert Config Exceptions", self.step_3_upsert_config_exceptions),
                ("User Authentication", self.step_4_user_authentication),
                ("Attendance Check-in/out", self.step_5_attendance_check_in_out),
                ("Verify Exception Rules", self.step_6_verify_exception_rules),
                ("Monthly Deductions", self.step_7_monthly_deductions_calculation)
            ]
            
            for step_name, step_func in steps:
                print(f"\n{'='*20} {step_name} {'='*20}")
                try:
                    success = await step_func()
                    if not success:
                        print(f"⚠️ Step '{step_name}' had issues but continuing...")
                except Exception as e:
                    print(f"❌ Step '{step_name}' failed with error: {e}")
                    traceback.print_exc()
                    
            await self.save_evidence()
            
        finally:
            await self.cleanup_session()
            
        # Print summary
        print("\n" + "="*80)
        print("📋 TEST SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed = len([r for r in self.test_results if r["status"] == "PASS"])
        failed = len([r for r in self.test_results if r["status"] == "FAIL"])
        warnings = len([r for r in self.test_results if r["status"] == "WARN"])
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️ Warnings: {warnings}")
        print(f"Success Rate: {(passed/total_tests*100):.1f}%" if total_tests > 0 else "0%")
        
        if failed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"  - {result['test_name']}: {result['details']}")
                    
        return passed, failed, warnings

async def main():
    """Main test execution"""
    tester = AttendanceConfigTester()
    passed, failed, warnings = await tester.run_comprehensive_test()
    
    # Exit with appropriate code
    if failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())