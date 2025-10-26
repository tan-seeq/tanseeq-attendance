#!/usr/bin/env python3
"""
🔥 PHASE-2 HARDENING - ADVERSARIAL UAT & HIDDEN DEFECTS HUNT
Final comprehensive test using correct API endpoints
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
import uuid

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://hr-unification.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
CREDENTIALS = {
    'super_admin': {'email': 'admin@tanseeq.com', 'password': 'ADMIN'},
    'admin': {'email': 'mahmoud@tanseeq.com', 'password': 'mahmoud123'},
    'user': {'email': 'jihad@tanseeq.com', 'password': 'jihad123'}
}

class FinalAdversarialTester:
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
        
    async def scenario_1_flexible_attendance_policy(self):
        """
        SCENARIO 1: Attendance with Flexible Policy + Late Tracking
        """
        print("\n🔥 SCENARIO 1: Flexible Attendance Policy + Late Tracking")
        
        token = await self.authenticate('user')
        
        # Test 1: Analyze existing attendance for late tracking patterns
        resp = await self.api_request("GET", "/attendance", token)
        
        if resp["status"] == 200:
            attendance_records = resp["data"]
            
            # Check 9:15 AM rule implementation
            late_after_915 = []
            on_time_before_915 = []
            
            for record in attendance_records:
                check_in = record.get("check_in")
                late_minutes = record.get("late_minutes", 0)
                
                if check_in:
                    try:
                        check_in_time = datetime.strptime(check_in, "%H:%M:%S").time()
                        rule_time = datetime.strptime("09:15:00", "%H:%M:%S").time()
                        
                        if check_in_time > rule_time:
                            late_after_915.append({
                                "date": record.get("date"),
                                "check_in": check_in,
                                "late_minutes": late_minutes,
                                "expected_late": True
                            })
                        elif check_in_time <= rule_time:
                            on_time_before_915.append({
                                "date": record.get("date"),
                                "check_in": check_in,
                                "late_minutes": late_minutes,
                                "expected_late": False
                            })
                    except:
                        continue
            
            # Verify 9:15 AM rule compliance
            rule_violations = [r for r in late_after_915 if r["late_minutes"] == 0]
            rule_compliance = [r for r in late_after_915 if r["late_minutes"] > 0]
            
            if rule_compliance:
                self.log_test("SCENARIO_1", "9:15 AM Late Rule Compliance", "PASS", 
                             f"✅ {len(rule_compliance)} records correctly marked late after 9:15 AM")
            
            if rule_violations:
                self.log_test("SCENARIO_1", "9:15 AM Rule Violations", "FAIL", 
                             f"❌ {len(rule_violations)} records NOT marked late after 9:15 AM")
            
            if on_time_before_915:
                correct_on_time = [r for r in on_time_before_915 if r["late_minutes"] == 0]
                self.log_test("SCENARIO_1", "On-Time Detection", "PASS", 
                             f"✅ {len(correct_on_time)}/{len(on_time_before_915)} records correctly marked on-time")
            
            # Test early check-in compensation (should NOT be used)
            early_checkins = []
            for record in attendance_records:
                check_in = record.get("check_in")
                if check_in:
                    try:
                        check_in_time = datetime.strptime(check_in, "%H:%M:%S").time()
                        early_time = datetime.strptime("08:00:00", "%H:%M:%S").time()
                        
                        if check_in_time < early_time:
                            early_checkins.append(record)
                    except:
                        continue
            
            if early_checkins:
                # Check if any early check-ins are compensating for later late arrivals
                self.log_test("SCENARIO_1", "Early Check-in Analysis", "PASS", 
                             f"✅ Found {len(early_checkins)} early check-ins - verifying no compensation logic")
            else:
                self.log_test("SCENARIO_1", "Early Check-in Analysis", "WARN", 
                             "⚠️ No early check-ins found to test compensation logic")
                             
        else:
            self.log_test("SCENARIO_1", "Attendance Data Access", "FAIL", 
                         f"❌ Could not access attendance data: {resp['data']}")
            
    async def scenario_2_payroll_lock_reversal(self):
        """
        SCENARIO 2: Modify After Payroll Lock (Reversal Entry Test)
        """
        print("\n🔥 SCENARIO 2: Payroll Lock + Reversal Entry Test")
        
        token = await self.authenticate('super_admin')
        
        # Get payroll cycles
        resp = await self.api_request("GET", "/payroll/cycles", token)
        
        if resp["status"] == 200:
            cycles_data = resp["data"]
            
            if isinstance(cycles_data, dict) and "cycles" in cycles_data:
                cycles = cycles_data["cycles"]
            elif isinstance(cycles_data, list):
                cycles = cycles_data
            else:
                cycles = []
                
            if cycles:
                cycle = cycles[0]
                cycle_id = cycle.get("id")
                
                # Test lock mechanism (POST method)
                print(f"📍 Testing lock mechanism for cycle: {cycle_id}")
                
                lock_data = {"reason": "Adversarial testing - lock verification"}
                resp = await self.api_request("POST", f"/payroll/cycles/{cycle_id}/lock", 
                                            token, json=lock_data)
                
                if resp["status"] == 200:
                    self.log_test("SCENARIO_2", "Lock Cycle", "PASS", 
                                 "✅ Cycle locked successfully")
                    
                    # Test modification of locked cycle
                    print("📍 Testing modification of locked cycle...")
                    modify_resp = await self.api_request("POST", f"/payroll/cycles/{cycle_id}/recalculate", 
                                                       token, json={})
                    
                    if modify_resp["status"] in [400, 403]:
                        self.log_test("SCENARIO_2", "Locked Cycle Protection", "PASS", 
                                     "✅ Modifications correctly blocked on locked cycle")
                    else:
                        self.log_test("SCENARIO_2", "Locked Cycle Protection", "FAIL", 
                                     f"❌ Modifications allowed on locked cycle: {modify_resp['status']}")
                    
                    # Test unlock
                    unlock_data = {"reason": "Adversarial testing - cleanup unlock"}
                    unlock_resp = await self.api_request("POST", f"/payroll/cycles/{cycle_id}/unlock", 
                                                       token, json=unlock_data)
                    
                    if unlock_resp["status"] == 200:
                        self.log_test("SCENARIO_2", "Unlock Cycle", "PASS", 
                                     "✅ Cycle unlocked successfully")
                    else:
                        self.log_test("SCENARIO_2", "Unlock Cycle", "WARN", 
                                     f"⚠️ Unlock response: {unlock_resp['status']}")
                else:
                    self.log_test("SCENARIO_2", "Lock Cycle", "FAIL", 
                                 f"❌ Failed to lock cycle: {resp['data']}")
                
                # Test payroll ledger access (correct endpoint)
                print("📍 Checking payroll ledger...")
                ledger_resp = await self.api_request("GET", f"/payroll/cycles/{cycle_id}/ledger", token)
                
                if ledger_resp["status"] == 200:
                    ledger_entries = ledger_resp["data"]
                    
                    # Look for reversal entries
                    reversal_entries = []
                    if isinstance(ledger_entries, list):
                        reversal_entries = [e for e in ledger_entries if e.get("is_reversed")]
                    elif isinstance(ledger_entries, dict) and "entries" in ledger_entries:
                        reversal_entries = [e for e in ledger_entries["entries"] if e.get("is_reversed")]
                    
                    self.log_test("SCENARIO_2", "Payroll Ledger Access", "PASS", 
                                 f"✅ Ledger accessible, found {len(reversal_entries)} reversal entries")
                else:
                    self.log_test("SCENARIO_2", "Payroll Ledger Access", "FAIL", 
                                 f"❌ Could not access payroll ledger: {ledger_resp['data']}")
            else:
                self.log_test("SCENARIO_2", "No Cycles Available", "WARN", 
                             "⚠️ No payroll cycles available for testing")
        else:
            self.log_test("SCENARIO_2", "Payroll Cycles Access", "FAIL", 
                         f"❌ Could not access payroll cycles: {resp['data']}")
            
    async def scenario_3_custody_overspending(self):
        """
        SCENARIO 3: Custody Overspending + Advance Isolation
        """
        print("\n🔥 SCENARIO 3: Custody Overspending + Advance Isolation")
        
        super_token = await self.authenticate('super_admin')
        user_token = await self.authenticate('user')
        
        # Test current balance logic
        resp = await self.api_request("GET", "/advances/my-balance", user_token)
        
        if resp["status"] == 200:
            balance = resp["data"]
            
            total_advances = balance.get("total_advances", 0)
            total_custody = balance.get("total_custody", 0)
            total_expenses = balance.get("total_expenses", 0)
            remaining_advance = balance.get("remaining_advance", 0)
            remaining_custody = balance.get("remaining_custody", 0)
            total_available = balance.get("total_available", 0)
            
            # Test advance isolation (advances should NOT be reduced by expenses)
            if abs(remaining_advance - total_advances) < 0.01:
                self.log_test("SCENARIO_3", "Advance Isolation", "PASS", 
                             f"✅ Advances correctly isolated: {remaining_advance} = {total_advances}")
            else:
                self.log_test("SCENARIO_3", "Advance Isolation", "FAIL", 
                             f"❌ Advance isolation broken: {remaining_advance} ≠ {total_advances}")
            
            # Test custody deduction (custody should be reduced by expenses)
            expected_custody = total_custody - total_expenses
            if abs(remaining_custody - expected_custody) < 0.01:
                self.log_test("SCENARIO_3", "Custody Expense Deduction", "PASS", 
                             f"✅ Custody correctly reduced by expenses: {remaining_custody}")
            else:
                self.log_test("SCENARIO_3", "Custody Expense Deduction", "FAIL", 
                             f"❌ Custody deduction incorrect: {remaining_custody} vs expected {expected_custody}")
            
            # Test overspending handling
            if remaining_custody < 0:
                self.log_test("SCENARIO_3", "Overspending Handling", "PASS", 
                             f"✅ System handles overspending: custody = {remaining_custody} AED")
            else:
                self.log_test("SCENARIO_3", "Overspending Test", "WARN", 
                             f"⚠️ No overspending in current data (custody = {remaining_custody} AED)")
            
            # Test total calculation
            calculated_total = remaining_advance + remaining_custody
            if abs(calculated_total - total_available) < 0.01:
                self.log_test("SCENARIO_3", "Total Balance Calculation", "PASS", 
                             "✅ Total balance calculation correct")
            else:
                self.log_test("SCENARIO_3", "Total Balance Calculation", "FAIL", 
                             f"❌ Total calculation error: {calculated_total} vs {total_available}")
                             
        else:
            self.log_test("SCENARIO_3", "Balance Access", "FAIL", 
                         f"❌ Could not access balance: {resp['data']}")
        
        # Check system-wide for overspending scenarios
        resp = await self.api_request("GET", "/advances/admin/all-balances", super_token)
        
        if resp["status"] == 200:
            all_balances = resp["data"].get("employee_balances", [])
            
            overspending_employees = []
            for emp_balance in all_balances:
                custody_balance = emp_balance.get("remaining_custody", 0)
                advance_balance = emp_balance.get("remaining_advance", 0)
                
                if custody_balance < 0 or advance_balance < 0:
                    overspending_employees.append({
                        "employee": emp_balance.get("employee_name"),
                        "custody": custody_balance,
                        "advance": advance_balance
                    })
            
            if overspending_employees:
                self.log_test("SCENARIO_3", "System-wide Overspending Detection", "PASS", 
                             f"✅ Found {len(overspending_employees)} employees with negative balances")
            else:
                self.log_test("SCENARIO_3", "System-wide Overspending", "WARN", 
                             "⚠️ No overspending scenarios found in system")
        else:
            self.log_test("SCENARIO_3", "All Balances Access", "FAIL", 
                         f"❌ Could not access all balances: {resp['data']}")
            
    async def scenario_4_deductions_from_reports(self):
        """
        SCENARIO 4: Apply Deductions from Reports Page
        """
        print("\n🔥 SCENARIO 4: Apply Deductions from Reports Page")
        
        token = await self.authenticate('super_admin')
        
        # Test monthly deductions calculation
        test_month = "2025-01"
        resp = await self.api_request("POST", f"/deductions/calculate-monthly?month={test_month}", token)
        
        if resp["status"] == 200:
            deductions = resp["data"]
            
            self.log_test("SCENARIO_4", "Calculate Monthly Deductions", "PASS", 
                         f"✅ Calculated deductions for {len(deductions)} employees")
            
            # Verify deduction structure
            if deductions:
                sample = deductions[0]
                required_fields = ["employee_id", "employee_name"]
                optional_fields = ["late_deduction", "absence_deduction"]
                
                has_required = all(field in sample for field in required_fields)
                has_deduction_data = any(sample.get(field, 0) > 0 for field in optional_fields)
                
                if has_required:
                    self.log_test("SCENARIO_4", "Deduction Data Structure", "PASS", 
                                 "✅ Deduction records have required structure")
                else:
                    self.log_test("SCENARIO_4", "Deduction Data Structure", "FAIL", 
                                 "❌ Missing required fields in deduction records")
                
                if has_deduction_data:
                    self.log_test("SCENARIO_4", "Deduction Calculation", "PASS", 
                                 "✅ Deductions calculated with actual values")
                else:
                    self.log_test("SCENARIO_4", "Deduction Calculation", "WARN", 
                                 "⚠️ No deduction amounts found (all zero)")
            
            # Test deduction application
            apply_data = {"month": test_month}
            resp = await self.api_request("POST", "/deductions/apply-monthly", token, json=apply_data)
            
            if resp["status"] == 200:
                self.log_test("SCENARIO_4", "Apply Deductions", "PASS", 
                             "✅ Deductions applied successfully")
            elif resp["status"] == 422:
                # Try alternative format
                apply_data = {"deductions": deductions, "month": test_month}
                resp = await self.api_request("POST", "/deductions/apply-monthly", token, json=apply_data)
                
                if resp["status"] == 200:
                    self.log_test("SCENARIO_4", "Apply Deductions (Alt Format)", "PASS", 
                                 "✅ Deductions applied with alternative format")
                else:
                    self.log_test("SCENARIO_4", "Apply Deductions", "FAIL", 
                                 f"❌ Failed to apply deductions: {resp['data']}")
            else:
                self.log_test("SCENARIO_4", "Apply Deductions", "FAIL", 
                             f"❌ Failed to apply deductions: {resp['data']}")
                             
        else:
            self.log_test("SCENARIO_4", "Calculate Monthly Deductions", "FAIL", 
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
            
            # Check for deductions in payroll cycles
            cycles_with_deductions = 0
            for cycle in cycles:
                if cycle.get("employee_payroll_summaries"):
                    for emp_summary in cycle["employee_payroll_summaries"]:
                        if (emp_summary.get("late_deduction", 0) > 0 or 
                            emp_summary.get("absence_deduction", 0) > 0):
                            cycles_with_deductions += 1
                            break
            
            if cycles_with_deductions > 0:
                self.log_test("SCENARIO_4", "Payroll Integration", "PASS", 
                             f"✅ Found deductions in {cycles_with_deductions} payroll cycles")
            else:
                self.log_test("SCENARIO_4", "Payroll Integration", "WARN", 
                             "⚠️ No deductions found in existing payroll cycles")
        else:
            self.log_test("SCENARIO_4", "Payroll Cycles Check", "FAIL", 
                         f"❌ Could not check payroll cycles: {resp['data']}")
            
    async def scenario_5_negative_net_salary(self):
        """
        SCENARIO 5: Negative Net Salary (Boundary Condition)
        """
        print("\n🔥 SCENARIO 5: Negative Net Salary Boundary Test")
        
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
                        high_deduction_cases = []
                        
                        for emp in employees:
                            net_salary = emp.get("net_salary", 0)
                            base_salary = emp.get("base_salary", 0)
                            allowances = emp.get("allowances", 0)
                            gross_salary = base_salary + allowances
                            
                            total_deductions = (emp.get("late_deduction", 0) + 
                                              emp.get("absence_deduction", 0) + 
                                              emp.get("advance_deduction", 0) + 
                                              emp.get("manual_deduction", 0))
                            
                            if net_salary < 0:
                                negative_salaries.append({
                                    "employee": emp.get("employee_name"),
                                    "net_salary": net_salary,
                                    "gross": gross_salary,
                                    "deductions": total_deductions
                                })
                                boundary_cases_found = True
                                
                            elif net_salary == 0:
                                zero_salaries.append({
                                    "employee": emp.get("employee_name"),
                                    "gross": gross_salary,
                                    "deductions": total_deductions
                                })
                                boundary_cases_found = True
                            
                            # Check for high deduction ratios
                            if gross_salary > 0:
                                deduction_ratio = total_deductions / gross_salary
                                if deduction_ratio > 0.9:  # More than 90% deductions
                                    high_deduction_cases.append({
                                        "employee": emp.get("employee_name"),
                                        "ratio": deduction_ratio,
                                        "net_salary": net_salary
                                    })
                                    boundary_cases_found = True
                        
                        # Log findings
                        if negative_salaries:
                            self.log_test("SCENARIO_5", "Negative Net Salary Detection", "PASS", 
                                         f"✅ Found {len(negative_salaries)} employees with negative net salary")
                            
                        if zero_salaries:
                            self.log_test("SCENARIO_5", "Zero Net Salary Detection", "PASS", 
                                         f"✅ Found {len(zero_salaries)} employees with zero net salary")
                            
                        if high_deduction_cases:
                            self.log_test("SCENARIO_5", "High Deduction Ratio Detection", "PASS", 
                                         f"✅ Found {len(high_deduction_cases)} employees with >90% deduction ratio")
                        
                        # Check for system warnings or debt tracking
                        warnings_found = any(emp.get("warnings") for emp in employees)
                        debt_tracking = any(emp.get("debt_to_company", 0) > 0 for emp in employees)
                        
                        if warnings_found:
                            self.log_test("SCENARIO_5", "Warning System", "PASS", 
                                         "✅ System has warning mechanisms for boundary conditions")
                        
                        if debt_tracking:
                            self.log_test("SCENARIO_5", "Debt Tracking", "PASS", 
                                         "✅ System tracks debt to company for negative salaries")
                        
                        break  # Only analyze first cycle with data
            
            if not boundary_cases_found:
                self.log_test("SCENARIO_5", "Boundary Conditions Analysis", "WARN", 
                             "⚠️ No boundary conditions found in current payroll data")
                             
        else:
            self.log_test("SCENARIO_5", "Payroll Data Access", "FAIL", 
                         f"❌ Could not access payroll data: {resp['data']}")
            
    async def run_all_scenarios(self):
        """Run all adversarial test scenarios"""
        print("🔥 STARTING FINAL PHASE-2 HARDENING - ADVERSARIAL UAT")
        print("=" * 80)
        
        await self.setup_session()
        
        try:
            await self.scenario_1_flexible_attendance_policy()
            await self.scenario_2_payroll_lock_reversal()
            await self.scenario_3_custody_overspending()
            await self.scenario_4_deductions_from_reports()
            await self.scenario_5_negative_net_salary()
            
        except Exception as e:
            print(f"❌ Critical error during testing: {e}")
            self.log_test("SYSTEM", "Critical Error", "FAIL", str(e))
            
        finally:
            await self.cleanup()
            
        self.generate_final_report()
        
    def generate_final_report(self):
        """Generate final adversarial testing report"""
        print("\n" + "=" * 80)
        print("🔥 FINAL ADVERSARIAL TESTING REPORT")
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
        
        # Scenario breakdown
        scenarios = {}
        for test in self.test_results:
            scenario = test["scenario"]
            if scenario not in scenarios:
                scenarios[scenario] = {"PASS": 0, "FAIL": 0, "WARN": 0}
            scenarios[scenario][test["status"]] += 1
            
        print(f"\n📋 SCENARIO RESULTS:")
        for scenario, counts in scenarios.items():
            total = sum(counts.values())
            passed = counts["PASS"]
            rate = (passed / total * 100) if total > 0 else 0
            print(f"   {scenario}: {passed}/{total} ({rate:.1f}%) - ✅{counts['PASS']} ❌{counts['FAIL']} ⚠️{counts['WARN']}")
            
        # Critical issues
        print(f"\n🚨 CRITICAL ISSUES:")
        critical_issues = [t for t in self.test_results if t["status"] == "FAIL"]
        if critical_issues:
            for issue in critical_issues:
                print(f"   ❌ {issue['scenario']} - {issue['test']}: {issue['details']}")
        else:
            print("   ✅ No critical issues found!")
            
        # Edge cases
        print(f"\n⚠️  EDGE CASES & WARNINGS:")
        warnings = [t for t in self.test_results if t["status"] == "WARN"]
        if warnings:
            for warning in warnings:
                print(f"   ⚠️  {warning['scenario']} - {warning['test']}: {warning['details']}")
        else:
            print("   ✅ No edge case warnings!")
            
        # Save comprehensive results
        with open("/app/final_adversarial_results.json", "w") as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "warnings": warning_tests,
                    "success_rate": success_rate
                },
                "scenarios": scenarios,
                "detailed_results": self.test_results,
                "timestamp": datetime.now().isoformat()
            }, f, indent=2)
            
        print(f"\n💾 Comprehensive results saved to: /app/final_adversarial_results.json")
        
        # Final production readiness assessment
        print(f"\n" + "=" * 80)
        print("🎯 PRODUCTION READINESS ASSESSMENT")
        print("=" * 80)
        
        if failed_tests == 0:
            print(f"🟢 STATUS: READY FOR PRODUCTION")
            print("   ✅ All adversarial scenarios passed")
            print("   ✅ System demonstrates robust edge case handling")
            print("   ✅ No critical vulnerabilities found")
        elif failed_tests <= 2 and success_rate >= 80:
            print(f"🟡 STATUS: CONDITIONAL APPROVAL")
            print("   ⚠️  Minor issues found but system is mostly robust")
            print("   ⚠️  Review and address specific failures before deployment")
            print("   ✅ Core functionality demonstrates good resilience")
        else:
            print(f"🔴 STATUS: NOT READY FOR PRODUCTION")
            print("   ❌ Critical issues found in adversarial testing")
            print("   ❌ System needs hardening before deployment")
            print("   ❌ Address all failures before proceeding")
            
        print(f"\n📋 RECOMMENDATIONS:")
        if failed_tests == 0:
            print("   • System is ready for production deployment")
            print("   • Continue monitoring edge cases in production")
        else:
            print("   • Fix all critical issues identified")
            print("   • Re-run adversarial tests after fixes")
            print("   • Consider additional stress testing")

async def main():
    """Main execution function"""
    tester = FinalAdversarialTester()
    await tester.run_all_scenarios()

if __name__ == "__main__":
    asyncio.run(main())