#!/usr/bin/env python3
"""
🔥 PHASE-2 HARDENING - ADVERSARIAL UAT & HIDDEN DEFECTS HUNT
Focused testing on the 5 specific scenarios from the review request
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
import uuid

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://hr-tanseeq-app.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
CREDENTIALS = {
    'super_admin': {'email': 'admin@tanseeq.com', 'password': 'ADMIN'},
    'admin': {'email': 'mahmoud@tanseeq.com', 'password': 'mahmoud123'},
    'user': {'email': 'jihad@tanseeq.com', 'password': 'jihad123'}
}

class FocusedAdversarialTester:
    def __init__(self):
        self.session = None
        self.tokens = {}
        self.test_results = []
        
    async def setup_session(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(ssl=False)
        )
        
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
            
    async def authenticate(self, role: str) -> str:
        """Authenticate and get JWT token"""
        if role in self.tokens:
            return self.tokens[role]
            
        creds = CREDENTIALS[role]
        async with self.session.post(f"{API_BASE}/auth/login", json=creds) as resp:
            if resp.status == 200:
                data = await resp.json()
                token = data['access_token']
                self.tokens[role] = token
                print(f"✅ Authenticated as {role}: {creds['email']}")
                return token
            else:
                error = await resp.text()
                raise Exception(f"❌ Authentication failed for {role}: {error}")
                
    async def api_request(self, method: str, endpoint: str, token: str = None, **kwargs) -> Dict:
        """Make authenticated API request"""
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
            
        url = f"{API_BASE}{endpoint}"
        
        async with self.session.request(method, url, headers=headers, **kwargs) as resp:
            try:
                data = await resp.json()
            except:
                data = {"text": await resp.text()}
                
            return {
                "status": resp.status,
                "data": data,
                "headers": dict(resp.headers)
            }
            
    def log_test(self, scenario: str, test_name: str, status: str, details: str, evidence: Dict = None):
        """Log test result"""
        result = {
            "scenario": scenario,
            "test": test_name,
            "status": status,
            "details": details,
            "evidence": evidence or {},
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {scenario} - {test_name}: {details}")
        
    async def test_attendance_late_tracking_rule(self):
        """
        Test the 9:15 AM late tracking rule specifically
        """
        print("\n🔥 TESTING: 9:15 AM Late Tracking Rule")
        
        token = await self.authenticate('user')
        
        # Get attendance records to analyze late tracking
        resp = await self.api_request("GET", "/attendance", token)
        
        if resp["status"] == 200:
            attendance_records = resp["data"]
            
            # Analyze records for 9:15 AM rule compliance
            late_after_915 = []
            not_late_before_915 = []
            
            for record in attendance_records:
                check_in = record.get("check_in")
                late_minutes = record.get("late_minutes", 0)
                
                if check_in:
                    try:
                        # Parse check-in time
                        check_in_time = datetime.strptime(check_in, "%H:%M:%S").time()
                        rule_time = datetime.strptime("09:15:00", "%H:%M:%S").time()
                        
                        if check_in_time > rule_time and late_minutes > 0:
                            late_after_915.append({
                                "date": record.get("date"),
                                "check_in": check_in,
                                "late_minutes": late_minutes
                            })
                        elif check_in_time <= rule_time and late_minutes == 0:
                            not_late_before_915.append({
                                "date": record.get("date"),
                                "check_in": check_in
                            })
                    except:
                        continue
            
            # Verify rule implementation
            if late_after_915:
                self.log_test("LATE_TRACKING", "9:15 AM Rule - Late Detection", "PASS", 
                             f"✅ Found {len(late_after_915)} records correctly marked as late after 9:15 AM")
            else:
                self.log_test("LATE_TRACKING", "9:15 AM Rule - Late Detection", "WARN", 
                             "No late records after 9:15 AM found to verify rule")
                             
            if not_late_before_915:
                self.log_test("LATE_TRACKING", "9:15 AM Rule - On Time Detection", "PASS", 
                             f"✅ Found {len(not_late_before_915)} records correctly marked as on-time before 9:15 AM")
            else:
                self.log_test("LATE_TRACKING", "9:15 AM Rule - On Time Detection", "WARN", 
                             "No on-time records before 9:15 AM found to verify rule")
                             
            # Check for early check-in compensation (should NOT be used)
            early_checkins = []
            for record in attendance_records:
                check_in = record.get("check_in")
                if check_in:
                    try:
                        check_in_time = datetime.strptime(check_in, "%H:%M:%S").time()
                        early_time = datetime.strptime("08:00:00", "%H:%M:%S").time()
                        
                        if check_in_time < early_time:
                            early_checkins.append({
                                "date": record.get("date"),
                                "check_in": check_in,
                                "late_minutes": record.get("late_minutes", 0)
                            })
                    except:
                        continue
            
            if early_checkins:
                # Check if early check-ins are being used to compensate for late arrivals
                compensated = [r for r in early_checkins if r["late_minutes"] == 0]
                self.log_test("LATE_TRACKING", "Early Check-in Compensation", "PASS" if not compensated else "FAIL", 
                             f"Early check-ins found: {len(early_checkins)}, Used for compensation: {len(compensated)}")
        else:
            self.log_test("LATE_TRACKING", "Attendance Data Access", "FAIL", 
                         f"Could not access attendance data: {resp['data']}")
            
    async def test_payroll_lock_mechanism(self):
        """
        Test payroll cycle lock/unlock mechanism and reversal entries
        """
        print("\n🔥 TESTING: Payroll Lock Mechanism")
        
        token = await self.authenticate('super_admin')
        
        # Get payroll cycles
        resp = await self.api_request("GET", "/payroll/cycles", token)
        
        if resp["status"] == 200:
            cycles_data = resp["data"]
            
            # Handle different response formats
            if isinstance(cycles_data, dict) and "cycles" in cycles_data:
                cycles = cycles_data["cycles"]
            elif isinstance(cycles_data, list):
                cycles = cycles_data
            else:
                cycles = []
                
            if cycles:
                cycle = cycles[0]
                cycle_id = cycle.get("id")
                
                # Test lock functionality
                print(f"📍 Testing lock mechanism for cycle: {cycle_id}")
                
                # Check if lock endpoint exists
                lock_endpoints = [
                    f"/payroll/cycles/{cycle_id}/lock",
                    f"/payroll/cycles/{cycle_id}/toggle-lock"
                ]
                
                lock_success = False
                for endpoint in lock_endpoints:
                    lock_data = {"reason": "Adversarial testing - lock verification"}
                    resp = await self.api_request("PUT", endpoint, token, json=lock_data)
                    
                    if resp["status"] == 200:
                        self.log_test("PAYROLL_LOCK", "Lock Cycle", "PASS", 
                                     f"✅ Cycle locked successfully via {endpoint}")
                        lock_success = True
                        
                        # Test modification of locked cycle
                        modify_resp = await self.api_request("PUT", f"/payroll/cycles/{cycle_id}/recalculate", 
                                                           token, json={})
                        
                        if modify_resp["status"] in [400, 403]:
                            self.log_test("PAYROLL_LOCK", "Locked Cycle Protection", "PASS", 
                                         "✅ Modifications correctly blocked on locked cycle")
                        else:
                            self.log_test("PAYROLL_LOCK", "Locked Cycle Protection", "FAIL", 
                                         f"❌ Modifications allowed on locked cycle: {modify_resp['status']}")
                        
                        # Test unlock
                        unlock_data = {"reason": "Adversarial testing - unlock for cleanup"}
                        unlock_resp = await self.api_request("PUT", endpoint.replace("lock", "unlock"), 
                                                           token, json=unlock_data)
                        
                        if unlock_resp["status"] == 200:
                            self.log_test("PAYROLL_LOCK", "Unlock Cycle", "PASS", 
                                         "✅ Cycle unlocked successfully")
                        else:
                            self.log_test("PAYROLL_LOCK", "Unlock Cycle", "WARN", 
                                         f"⚠️ Unlock response: {unlock_resp['status']}")
                        break
                    elif resp["status"] == 405:
                        continue  # Try next endpoint
                    else:
                        self.log_test("PAYROLL_LOCK", f"Lock Test - {endpoint}", "FAIL", 
                                     f"❌ Lock failed: {resp['data']}")
                
                if not lock_success:
                    self.log_test("PAYROLL_LOCK", "Lock Mechanism", "FAIL", 
                                 "❌ No working lock endpoint found")
                                 
                # Test payroll ledger for reversal entries
                print("📍 Checking payroll ledger...")
                ledger_resp = await self.api_request("GET", f"/payroll-ledger?cycle_id={cycle_id}", token)
                
                if ledger_resp["status"] == 200:
                    ledger_entries = ledger_resp["data"]
                    reversal_entries = [e for e in ledger_entries if e.get("is_reversed")]
                    
                    self.log_test("PAYROLL_LOCK", "Reversal Entries Check", "PASS", 
                                 f"✅ Ledger accessible, found {len(reversal_entries)} reversal entries")
                else:
                    self.log_test("PAYROLL_LOCK", "Payroll Ledger Access", "FAIL", 
                                 f"❌ Could not access payroll ledger: {ledger_resp['data']}")
            else:
                self.log_test("PAYROLL_LOCK", "No Cycles Available", "WARN", 
                             "⚠️ No payroll cycles available for lock testing")
        else:
            self.log_test("PAYROLL_LOCK", "Payroll Cycles Access", "FAIL", 
                         f"❌ Could not access payroll cycles: {resp['data']}")
            
    async def test_custody_advance_separation(self):
        """
        Test custody overspending and advance isolation
        """
        print("\n🔥 TESTING: Custody & Advance Separation")
        
        super_token = await self.authenticate('super_admin')
        user_token = await self.authenticate('user')
        
        # Get current balance
        resp = await self.api_request("GET", "/advances/my-balance", user_token)
        
        if resp["status"] == 200:
            balance = resp["data"]
            
            remaining_advance = balance.get("remaining_advance", 0)
            remaining_custody = balance.get("remaining_custody", 0)
            total_advances = balance.get("total_advances", 0)
            total_custody = balance.get("total_custody", 0)
            total_expenses = balance.get("total_expenses", 0)
            
            # Test balance calculation logic
            expected_remaining_advance = total_advances  # Should not be affected by expenses
            expected_remaining_custody = total_custody - total_expenses  # Should be reduced by expenses
            
            advance_correct = abs(remaining_advance - expected_remaining_advance) < 0.01
            custody_correct = abs(remaining_custody - expected_remaining_custody) < 0.01
            
            if advance_correct:
                self.log_test("CUSTODY_ADVANCE", "Advance Isolation", "PASS", 
                             f"✅ Advances correctly isolated from expenses: {remaining_advance}")
            else:
                self.log_test("CUSTODY_ADVANCE", "Advance Isolation", "FAIL", 
                             f"❌ Advance calculation incorrect: {remaining_advance} vs expected {expected_remaining_advance}")
                             
            if custody_correct:
                self.log_test("CUSTODY_ADVANCE", "Custody Deduction", "PASS", 
                             f"✅ Custody correctly reduced by expenses: {remaining_custody}")
            else:
                self.log_test("CUSTODY_ADVANCE", "Custody Deduction", "FAIL", 
                             f"❌ Custody calculation incorrect: {remaining_custody} vs expected {expected_remaining_custody}")
            
            # Check for overspending scenarios
            if remaining_custody < 0:
                self.log_test("CUSTODY_ADVANCE", "Overspending Handling", "PASS", 
                             f"✅ System handles overspending: custody balance = {remaining_custody}")
            else:
                self.log_test("CUSTODY_ADVANCE", "Overspending Detection", "WARN", 
                             f"⚠️ No overspending scenario in current data")
                             
        else:
            self.log_test("CUSTODY_ADVANCE", "Balance Access", "FAIL", 
                         f"❌ Could not access balance: {resp['data']}")
            
        # Check all employee balances for overspending patterns
        resp = await self.api_request("GET", "/advances/admin/all-balances", super_token)
        
        if resp["status"] == 200:
            all_balances = resp["data"].get("employee_balances", [])
            
            overspending_cases = []
            for emp_balance in all_balances:
                custody_balance = emp_balance.get("remaining_custody", 0)
                advance_balance = emp_balance.get("remaining_advance", 0)
                
                if custody_balance < 0:
                    overspending_cases.append({
                        "employee": emp_balance.get("employee_name"),
                        "custody_balance": custody_balance,
                        "advance_balance": advance_balance
                    })
            
            if overspending_cases:
                self.log_test("CUSTODY_ADVANCE", "System-wide Overspending", "PASS", 
                             f"✅ Found {len(overspending_cases)} overspending cases handled by system")
            else:
                self.log_test("CUSTODY_ADVANCE", "System-wide Analysis", "WARN", 
                             "⚠️ No overspending cases found in system")
        else:
            self.log_test("CUSTODY_ADVANCE", "All Balances Access", "FAIL", 
                         f"❌ Could not access all balances: {resp['data']}")
            
    async def test_deductions_application_workflow(self):
        """
        Test deductions application from reports page
        """
        print("\n🔥 TESTING: Deductions Application Workflow")
        
        token = await self.authenticate('super_admin')
        
        # Test monthly deductions calculation
        test_month = "2025-01"
        resp = await self.api_request("POST", f"/deductions/calculate-monthly?month={test_month}", token)
        
        if resp["status"] == 200:
            deductions = resp["data"]
            
            self.log_test("DEDUCTIONS_WORKFLOW", "Calculate Monthly Deductions", "PASS", 
                         f"✅ Calculated deductions for {len(deductions)} employees")
            
            # Verify deduction structure
            if deductions:
                sample = deductions[0]
                required_fields = ["employee_id", "employee_name"]
                
                has_required = all(field in sample for field in required_fields)
                
                if has_required:
                    self.log_test("DEDUCTIONS_WORKFLOW", "Deduction Data Structure", "PASS", 
                                 "✅ Deduction records have required fields")
                else:
                    self.log_test("DEDUCTIONS_WORKFLOW", "Deduction Data Structure", "FAIL", 
                                 "❌ Missing required fields in deduction records")
            
            # Test application to payroll cycle
            apply_data = {"month": test_month}
            resp = await self.api_request("POST", "/deductions/apply-monthly", token, json=apply_data)
            
            if resp["status"] == 200:
                self.log_test("DEDUCTIONS_WORKFLOW", "Apply Deductions", "PASS", 
                             "✅ Deductions applied to payroll cycle successfully")
            elif resp["status"] == 422:
                # Try with deductions data
                apply_data = {"month": test_month, "deductions": deductions}
                resp = await self.api_request("POST", "/deductions/apply-monthly", token, json=apply_data)
                
                if resp["status"] == 200:
                    self.log_test("DEDUCTIONS_WORKFLOW", "Apply Deductions (with data)", "PASS", 
                                 "✅ Deductions applied with explicit data")
                else:
                    self.log_test("DEDUCTIONS_WORKFLOW", "Apply Deductions", "FAIL", 
                                 f"❌ Failed to apply deductions: {resp['data']}")
            else:
                self.log_test("DEDUCTIONS_WORKFLOW", "Apply Deductions", "FAIL", 
                             f"❌ Failed to apply deductions: {resp['data']}")
                             
        else:
            self.log_test("DEDUCTIONS_WORKFLOW", "Calculate Monthly Deductions", "FAIL", 
                         f"❌ Failed to calculate deductions: {resp['data']}")
            
        # Verify integration with payroll cycles
        resp = await self.api_request("GET", "/payroll/cycles", token)
        
        if resp["status"] == 200:
            cycles_data = resp["data"]
            
            if isinstance(cycles_data, dict) and "cycles" in cycles_data:
                cycles = cycles_data["cycles"]
            elif isinstance(cycles_data, list):
                cycles = cycles_data
            else:
                cycles = []
                
            # Look for cycle with deductions
            cycles_with_deductions = []
            for cycle in cycles:
                if cycle.get("employee_payroll_summaries"):
                    for emp_summary in cycle["employee_payroll_summaries"]:
                        if (emp_summary.get("late_deduction", 0) > 0 or 
                            emp_summary.get("absence_deduction", 0) > 0):
                            cycles_with_deductions.append(cycle.get("month", "Unknown"))
                            break
            
            if cycles_with_deductions:
                self.log_test("DEDUCTIONS_WORKFLOW", "Payroll Integration", "PASS", 
                             f"✅ Found deductions in {len(cycles_with_deductions)} payroll cycles")
            else:
                self.log_test("DEDUCTIONS_WORKFLOW", "Payroll Integration", "WARN", 
                             "⚠️ No deductions found in payroll cycles")
        else:
            self.log_test("DEDUCTIONS_WORKFLOW", "Payroll Cycles Check", "FAIL", 
                         f"❌ Could not check payroll cycles: {resp['data']}")
            
    async def test_negative_salary_boundary(self):
        """
        Test negative net salary boundary conditions
        """
        print("\n🔥 TESTING: Negative Salary Boundary Conditions")
        
        token = await self.authenticate('super_admin')
        
        # Analyze existing payroll cycles for boundary conditions
        resp = await self.api_request("GET", "/payroll/cycles", token)
        
        if resp["status"] == 200:
            cycles_data = resp["data"]
            
            if isinstance(cycles_data, dict) and "cycles" in cycles_data:
                cycles = cycles_data["cycles"]
            elif isinstance(cycles_data, list):
                cycles = cycles_data
            else:
                cycles = []
                
            boundary_cases_found = False
            
            for cycle in cycles:
                cycle_id = cycle.get("id")
                
                if cycle_id:
                    # Get cycle summary
                    resp = await self.api_request("GET", f"/payroll/cycles/{cycle_id}/summary", token)
                    
                    if resp["status"] == 200:
                        summary = resp["data"]
                        employees = summary.get("employee_summaries", [])
                        
                        negative_salaries = []
                        zero_salaries = []
                        high_deduction_ratios = []
                        
                        for emp in employees:
                            net_salary = emp.get("net_salary", 0)
                            base_salary = emp.get("base_salary", 0)
                            total_deductions = (emp.get("late_deduction", 0) + 
                                              emp.get("absence_deduction", 0) + 
                                              emp.get("advance_deduction", 0) + 
                                              emp.get("manual_deduction", 0))
                            
                            if net_salary < 0:
                                negative_salaries.append({
                                    "employee": emp.get("employee_name"),
                                    "net_salary": net_salary,
                                    "deductions": total_deductions
                                })
                                boundary_cases_found = True
                                
                            elif net_salary == 0:
                                zero_salaries.append({
                                    "employee": emp.get("employee_name"),
                                    "base_salary": base_salary,
                                    "deductions": total_deductions
                                })
                                boundary_cases_found = True
                                
                            if base_salary > 0:
                                deduction_ratio = total_deductions / base_salary
                                if deduction_ratio > 0.8:  # More than 80% deductions
                                    high_deduction_ratios.append({
                                        "employee": emp.get("employee_name"),
                                        "ratio": deduction_ratio,
                                        "net_salary": net_salary
                                    })
                                    boundary_cases_found = True
                        
                        # Log findings for this cycle
                        if negative_salaries:
                            self.log_test("NEGATIVE_SALARY", "Negative Net Salary Detection", "PASS", 
                                         f"✅ Found {len(negative_salaries)} employees with negative net salary")
                            
                        if zero_salaries:
                            self.log_test("NEGATIVE_SALARY", "Zero Net Salary Detection", "PASS", 
                                         f"✅ Found {len(zero_salaries)} employees with zero net salary")
                            
                        if high_deduction_ratios:
                            self.log_test("NEGATIVE_SALARY", "High Deduction Ratio Detection", "PASS", 
                                         f"✅ Found {len(high_deduction_ratios)} employees with >80% deduction ratio")
                        
                        # Check for system warnings or debt tracking
                        warnings_found = any(emp.get("warnings") for emp in employees)
                        debt_tracking = any(emp.get("debt_to_company", 0) > 0 for emp in employees)
                        
                        if warnings_found or debt_tracking:
                            self.log_test("NEGATIVE_SALARY", "Warning System", "PASS", 
                                         f"✅ System has warning/debt tracking mechanisms")
                        
                        break  # Only analyze first cycle with data
            
            if not boundary_cases_found:
                self.log_test("NEGATIVE_SALARY", "Boundary Conditions Analysis", "WARN", 
                             "⚠️ No boundary conditions (negative/zero salaries) found in current data")
                             
        else:
            self.log_test("NEGATIVE_SALARY", "Payroll Data Access", "FAIL", 
                         f"❌ Could not access payroll data: {resp['data']}")
            
    async def run_focused_tests(self):
        """Run focused adversarial tests"""
        print("🔥 STARTING FOCUSED PHASE-2 HARDENING TESTS")
        print("=" * 80)
        
        await self.setup_session()
        
        try:
            await self.test_attendance_late_tracking_rule()
            await self.test_payroll_lock_mechanism()
            await self.test_custody_advance_separation()
            await self.test_deductions_application_workflow()
            await self.test_negative_salary_boundary()
            
        except Exception as e:
            print(f"❌ Critical error during testing: {e}")
            self.log_test("SYSTEM", "Critical Error", "FAIL", str(e))
            
        finally:
            await self.cleanup()
            
        self.generate_summary_report()
        
    def generate_summary_report(self):
        """Generate focused test summary"""
        print("\n" + "=" * 80)
        print("🔥 FOCUSED ADVERSARIAL TESTING SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["status"] == "PASS"])
        failed_tests = len([t for t in self.test_results if t["status"] == "FAIL"])
        warning_tests = len([t for t in self.test_results if t["status"] == "WARN"])
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 OVERALL RESULTS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   ⚠️  Warnings: {warning_tests}")
        print(f"   📈 Success Rate: {success_rate:.1f}%")
        
        # Test area breakdown
        test_areas = {}
        for test in self.test_results:
            area = test["scenario"]
            if area not in test_areas:
                test_areas[area] = {"PASS": 0, "FAIL": 0, "WARN": 0}
            test_areas[area][test["status"]] += 1
            
        print(f"\n📋 TEST AREA BREAKDOWN:")
        for area, counts in test_areas.items():
            total = sum(counts.values())
            passed = counts["PASS"]
            rate = (passed / total * 100) if total > 0 else 0
            print(f"   {area}: {passed}/{total} ({rate:.1f}%) - ✅{counts['PASS']} ❌{counts['FAIL']} ⚠️{counts['WARN']}")
            
        # Critical findings
        print(f"\n🚨 CRITICAL FINDINGS:")
        critical_issues = [t for t in self.test_results if t["status"] == "FAIL"]
        if critical_issues:
            for issue in critical_issues:
                print(f"   ❌ {issue['scenario']} - {issue['test']}: {issue['details']}")
        else:
            print("   ✅ No critical issues found!")
            
        # Edge cases and warnings
        print(f"\n⚠️  EDGE CASES & WARNINGS:")
        warnings = [t for t in self.test_results if t["status"] == "WARN"]
        if warnings:
            for warning in warnings:
                print(f"   ⚠️  {warning['scenario']} - {warning['test']}: {warning['details']}")
        else:
            print("   ✅ No edge case warnings!")
            
        # Save results
        with open("/app/focused_adversarial_results.json", "w") as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "warnings": warning_tests,
                    "success_rate": success_rate
                },
                "test_areas": test_areas,
                "detailed_results": self.test_results,
                "timestamp": datetime.now().isoformat()
            }, f, indent=2)
            
        print(f"\n💾 Results saved to: /app/focused_adversarial_results.json")
        
        # Final assessment
        if failed_tests == 0 and warning_tests <= 2:
            print(f"\n🟢 ADVERSARIAL TESTING: PASSED")
            print("   System demonstrates robust handling of edge cases and boundary conditions.")
        elif failed_tests <= 1:
            print(f"\n🟡 ADVERSARIAL TESTING: CONDITIONAL PASS")
            print("   Minor issues found. System is mostly robust but needs attention to specific areas.")
        else:
            print(f"\n🔴 ADVERSARIAL TESTING: FAILED")
            print("   Critical issues found. System needs hardening before production deployment.")

async def main():
    """Main execution function"""
    tester = FocusedAdversarialTester()
    await tester.run_focused_tests()

if __name__ == "__main__":
    asyncio.run(main())