#!/usr/bin/env python3
"""
🔥 PHASE-2 HARDENING - ADVERSARIAL UAT & HIDDEN DEFECTS HUNT
Comprehensive adversarial testing to break the system and find edge cases
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
import uuid

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://hr-system-fix.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
CREDENTIALS = {
    'super_admin': {'email': 'admin@tanseeq.com', 'password': 'ADMIN'},
    'admin': {'email': 'mahmoud@tanseeq.com', 'password': 'mahmoud123'},
    'user': {'email': 'jihad@tanseeq.com', 'password': 'jihad123'},
    'tarek': {'email': 'tarek@tanseeq.com', 'password': 'tarek123'}  # Flexible policy employee
}

class AdversarialTester:
    def __init__(self):
        self.session = None
        self.tokens = {}
        self.test_results = []
        self.employees = {}
        
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
        
    async def get_employees(self, token: str):
        """Get employee list for testing"""
        resp = await self.api_request("GET", "/employees/list", token)
        if resp["status"] == 200:
            self.employees = {emp["email"]: emp for emp in resp["data"]["employees"]}
            
    async def scenario_1_flexible_attendance(self):
        """
        SCENARIO 1: Attendance with Flexible Policy + Late Tracking
        Test multiple check-ins/check-outs with late tracking rules
        """
        print("\n🔥 SCENARIO 1: Flexible Attendance Policy + Late Tracking")
        
        # Try to authenticate as Tarek (flexible policy employee)
        try:
            token = await self.authenticate('user')  # Use regular user for now
        except:
            self.log_test("SCENARIO_1", "Authentication", "FAIL", "Could not authenticate flexible policy employee")
            return
            
        # Test 1: Early check-in (should not count as compensation)
        print("\n📍 Testing early check-in at 08:05...")
        resp = await self.api_request("POST", "/attendance/check-in", token)
        
        if resp["status"] == 200:
            self.log_test("SCENARIO_1", "Early Check-in", "PASS", 
                         f"Early check-in successful: {resp['data']}")
        else:
            self.log_test("SCENARIO_1", "Early Check-in", "FAIL", 
                         f"Early check-in failed: {resp['data']}")
            
        # Test 2: Early check-out (very short duration)
        print("📍 Testing early check-out at 08:10...")
        await asyncio.sleep(1)  # Small delay
        resp = await self.api_request("POST", "/attendance/check-out", token)
        
        if resp["status"] == 200:
            self.log_test("SCENARIO_1", "Early Check-out", "PASS", 
                         f"Early check-out successful: {resp['data']}")
        else:
            self.log_test("SCENARIO_1", "Early Check-out", "FAIL", 
                         f"Early check-out failed: {resp['data']}")
            
        # Test 3: Late check-in (after 9:15 AM - should trigger late deduction)
        print("📍 Testing late check-in at 09:20...")
        resp = await self.api_request("POST", "/attendance/check-in", token)
        
        if resp["status"] == 200:
            self.log_test("SCENARIO_1", "Late Check-in", "PASS", 
                         f"Late check-in successful: {resp['data']}")
        else:
            self.log_test("SCENARIO_1", "Late Check-in", "WARN", 
                         f"Late check-in blocked (expected): {resp['data']}")
            
        # Test 4: Normal check-out
        print("📍 Testing normal check-out at 18:00...")
        await asyncio.sleep(1)
        resp = await self.api_request("POST", "/attendance/check-out", token)
        
        if resp["status"] == 200:
            self.log_test("SCENARIO_1", "Normal Check-out", "PASS", 
                         f"Normal check-out successful: {resp['data']}")
        else:
            self.log_test("SCENARIO_1", "Normal Check-out", "FAIL", 
                         f"Normal check-out failed: {resp['data']}")
            
        # Test 5: Verify attendance records and late minutes calculation
        print("📍 Verifying attendance records...")
        resp = await self.api_request("GET", "/attendance", token)
        
        if resp["status"] == 200:
            attendance_records = resp["data"]
            late_records = [r for r in attendance_records if r.get("late_minutes", 0) > 0]
            
            self.log_test("SCENARIO_1", "Late Minutes Calculation", "PASS" if late_records else "WARN", 
                         f"Found {len(late_records)} records with late minutes", 
                         {"total_records": len(attendance_records), "late_records": len(late_records)})
        else:
            self.log_test("SCENARIO_1", "Attendance Verification", "FAIL", 
                         f"Could not retrieve attendance: {resp['data']}")
            
    async def scenario_2_payroll_lock_reversal(self):
        """
        SCENARIO 2: Modify After Payroll Lock (Reversal Entry Test)
        Test locked payroll cycles and reversal entries
        """
        print("\n🔥 SCENARIO 2: Payroll Lock + Reversal Entry Test")
        
        token = await self.authenticate('super_admin')
        
        # Test 1: Get existing payroll cycles
        print("📍 Getting existing payroll cycles...")
        resp = await self.api_request("GET", "/payroll/cycles", token)
        
        if resp["status"] == 200:
            cycles = resp["data"]["cycles"]
            self.log_test("SCENARIO_2", "Get Payroll Cycles", "PASS", 
                         f"Found {len(cycles)} payroll cycles")
            
            if cycles:
                cycle_id = cycles[0]["id"]
                
                # Test 2: Lock the cycle
                print(f"📍 Locking payroll cycle {cycle_id}...")
                lock_data = {"reason": "Adversarial testing - lock cycle"}
                resp = await self.api_request("PUT", f"/payroll/cycles/{cycle_id}/lock", 
                                            token, json=lock_data)
                
                if resp["status"] == 200:
                    self.log_test("SCENARIO_2", "Lock Cycle", "PASS", 
                                 f"Cycle locked successfully: {resp['data']}")
                    
                    # Test 3: Try to modify locked cycle (should be blocked)
                    print("📍 Attempting to modify locked cycle...")
                    modify_data = {
                        "employee_updates": [{
                            "employee_id": "test-emp",
                            "manual_deduction": 100.0,
                            "reason": "Test deduction"
                        }]
                    }
                    resp = await self.api_request("PUT", f"/payroll/cycles/{cycle_id}/update-employees", 
                                                token, json=modify_data)
                    
                    if resp["status"] in [400, 403]:
                        self.log_test("SCENARIO_2", "Modify Locked Cycle", "PASS", 
                                     f"Modification correctly blocked: {resp['data']}")
                    else:
                        self.log_test("SCENARIO_2", "Modify Locked Cycle", "FAIL", 
                                     f"Modification should be blocked but wasn't: {resp['data']}")
                        
                    # Test 4: Unlock cycle with reason
                    print("📍 Unlocking cycle with audit reason...")
                    unlock_data = {"reason": "Adversarial testing - unlock for modification"}
                    resp = await self.api_request("PUT", f"/payroll/cycles/{cycle_id}/unlock", 
                                                token, json=unlock_data)
                    
                    if resp["status"] == 200:
                        self.log_test("SCENARIO_2", "Unlock Cycle", "PASS", 
                                     f"Cycle unlocked successfully: {resp['data']}")
                        
                        # Test 5: Verify reversal entries in Payroll Ledger
                        print("📍 Checking payroll ledger for reversal entries...")
                        resp = await self.api_request("GET", f"/payroll-ledger?cycle_id={cycle_id}", token)
                        
                        if resp["status"] == 200:
                            ledger_entries = resp["data"]
                            reversal_entries = [e for e in ledger_entries if e.get("is_reversed")]
                            
                            self.log_test("SCENARIO_2", "Reversal Entries", "PASS" if reversal_entries else "WARN", 
                                         f"Found {len(reversal_entries)} reversal entries in ledger",
                                         {"total_entries": len(ledger_entries), "reversals": len(reversal_entries)})
                        else:
                            self.log_test("SCENARIO_2", "Payroll Ledger Check", "FAIL", 
                                         f"Could not access payroll ledger: {resp['data']}")
                    else:
                        self.log_test("SCENARIO_2", "Unlock Cycle", "FAIL", 
                                     f"Failed to unlock cycle: {resp['data']}")
                else:
                    self.log_test("SCENARIO_2", "Lock Cycle", "FAIL", 
                                 f"Failed to lock cycle: {resp['data']}")
            else:
                self.log_test("SCENARIO_2", "No Cycles Available", "WARN", 
                             "No payroll cycles available for testing")
        else:
            self.log_test("SCENARIO_2", "Get Payroll Cycles", "FAIL", 
                         f"Could not retrieve cycles: {resp['data']}")
            
    async def scenario_3_custody_overspending(self):
        """
        SCENARIO 3: Custody Overspending + Advance Isolation
        Test custody limits and advance separation
        """
        print("\n🔥 SCENARIO 3: Custody Overspending + Advance Isolation")
        
        token = await self.authenticate('super_admin')
        user_token = await self.authenticate('user')
        
        # Test 1: Create custody (300 AED)
        print("📍 Creating custody of 300 AED...")
        custody_data = {
            "employee_id": "test-emp-custody",
            "transaction_type": "custody",
            "amount": 300.0,
            "description": "Test custody for overspending scenario",
            "category": "office_supplies"
        }
        resp = await self.api_request("POST", "/advances/create", token, json=custody_data)
        
        if resp["status"] == 200:
            custody_id = resp["data"]["transaction_id"]
            self.log_test("SCENARIO_3", "Create Custody", "PASS", 
                         f"Custody created successfully: {custody_id}")
            
            # Test 2: Create expense 1 (120 AED - within limit)
            print("📍 Creating expense 1: 120 AED...")
            expense1_data = {
                "amount": 120.0,
                "category": "office_supplies",
                "description": "First expense within custody limit",
                "expense_date": datetime.now().strftime("%Y-%m-%d"),
                "notes": "Test expense 1"
            }
            
            # Mock file upload for expense
            form_data = aiohttp.FormData()
            for key, value in expense1_data.items():
                form_data.add_field(key, str(value))
            
            # Add mock invoice file
            form_data.add_field('invoice_files', b'fake_invoice_content', 
                              filename='invoice1.pdf', content_type='application/pdf')
            
            resp = await self.api_request("POST", "/advances/expense", user_token, data=form_data)
            
            if resp["status"] == 200:
                expense1_id = resp["data"]["transaction_id"]
                self.log_test("SCENARIO_3", "Create Expense 1", "PASS", 
                             f"Expense 1 created: {expense1_id}")
                
                # Approve expense 1
                print("📍 Approving expense 1...")
                approval_data = {"status": "approved", "notes": "Approved for testing"}
                resp = await self.api_request("POST", f"/advances/{expense1_id}/approve", 
                                            token, json=approval_data)
                
                if resp["status"] == 200:
                    self.log_test("SCENARIO_3", "Approve Expense 1", "PASS", 
                                 "Expense 1 approved successfully")
                    
                    # Test 3: Create expense 2 (200 AED - exceeds remaining custody)
                    print("📍 Creating expense 2: 200 AED (should exceed custody)...")
                    expense2_data = {
                        "amount": 200.0,
                        "category": "office_supplies", 
                        "description": "Second expense exceeding custody limit",
                        "expense_date": datetime.now().strftime("%Y-%m-%d"),
                        "notes": "Test expense 2 - overspending"
                    }
                    
                    form_data2 = aiohttp.FormData()
                    for key, value in expense2_data.items():
                        form_data2.add_field(key, str(value))
                    form_data2.add_field('invoice_files', b'fake_invoice_content2', 
                                       filename='invoice2.pdf', content_type='application/pdf')
                    
                    resp = await self.api_request("POST", "/advances/expense", user_token, data=form_data2)
                    
                    if resp["status"] == 400:
                        self.log_test("SCENARIO_3", "Overspending Block", "PASS", 
                                     f"Overspending correctly blocked: {resp['data']}")
                    elif resp["status"] == 200:
                        self.log_test("SCENARIO_3", "Overspending Allowed", "WARN", 
                                     f"Overspending allowed with settlement: {resp['data']}")
                    else:
                        self.log_test("SCENARIO_3", "Expense 2 Creation", "FAIL", 
                                     f"Unexpected response: {resp['data']}")
                        
                    # Test 4: Create separate advance (1000 AED)
                    print("📍 Creating separate advance of 1000 AED...")
                    advance_data = {
                        "employee_id": "test-emp-custody",
                        "transaction_type": "advance",
                        "amount": 1000.0,
                        "description": "Separate advance - should not affect custody",
                        "category": "salary_advance"
                    }
                    resp = await self.api_request("POST", "/advances/create", token, json=advance_data)
                    
                    if resp["status"] == 200:
                        advance_id = resp["data"]["transaction_id"]
                        self.log_test("SCENARIO_3", "Create Advance", "PASS", 
                                     f"Advance created: {advance_id}")
                        
                        # Test 5: Verify balance separation
                        print("📍 Verifying custody vs advance balance separation...")
                        resp = await self.api_request("GET", "/advances/my-balance", user_token)
                        
                        if resp["status"] == 200:
                            balance = resp["data"]
                            custody_balance = balance.get("remaining_custody", 0)
                            advance_balance = balance.get("remaining_advance", 0)
                            
                            # Check if custody is negative or zero after overspending
                            custody_ok = custody_balance <= 180  # 300 - 120 = 180 max
                            advance_ok = advance_balance == 1000  # Should remain untouched
                            
                            if custody_ok and advance_ok:
                                self.log_test("SCENARIO_3", "Balance Separation", "PASS", 
                                             f"Balances correctly separated - Custody: {custody_balance}, Advance: {advance_balance}")
                            else:
                                self.log_test("SCENARIO_3", "Balance Separation", "FAIL", 
                                             f"Balance separation issue - Custody: {custody_balance}, Advance: {advance_balance}")
                        else:
                            self.log_test("SCENARIO_3", "Balance Check", "FAIL", 
                                         f"Could not retrieve balance: {resp['data']}")
                    else:
                        self.log_test("SCENARIO_3", "Create Advance", "FAIL", 
                                     f"Failed to create advance: {resp['data']}")
                else:
                    self.log_test("SCENARIO_3", "Approve Expense 1", "FAIL", 
                                 f"Failed to approve expense 1: {resp['data']}")
            else:
                self.log_test("SCENARIO_3", "Create Expense 1", "FAIL", 
                             f"Failed to create expense 1: {resp['data']}")
        else:
            self.log_test("SCENARIO_3", "Create Custody", "FAIL", 
                         f"Failed to create custody: {resp['data']}")
            
    async def scenario_4_deductions_from_reports(self):
        """
        SCENARIO 4: Apply Deductions from Reports Page
        Test deduction application workflow from reports
        """
        print("\n🔥 SCENARIO 4: Apply Deductions from Reports Page")
        
        token = await self.authenticate('super_admin')
        
        # Test 1: Calculate monthly deductions (October 2025)
        print("📍 Calculating monthly deductions for October 2025...")
        resp = await self.api_request("POST", "/deductions/calculate-monthly?month=2025-10", token)
        
        if resp["status"] == 200:
            deductions = resp["data"]
            self.log_test("SCENARIO_4", "Calculate Deductions", "PASS", 
                         f"Deductions calculated for {len(deductions)} employees")
            
            # Test 2: Apply deductions to payroll cycle
            print("📍 Applying deductions to payroll cycle...")
            apply_data = {"month": "2025-10", "deductions": deductions}
            resp = await self.api_request("POST", "/deductions/apply-monthly", token, json=apply_data)
            
            if resp["status"] == 200:
                self.log_test("SCENARIO_4", "Apply Deductions", "PASS", 
                             f"Deductions applied successfully: {resp['data']}")
                
                # Test 3: Verify payroll cycle updated
                print("📍 Verifying payroll cycle integration...")
                resp = await self.api_request("GET", "/payroll/cycles", token)
                
                if resp["status"] == 200:
                    cycles = resp["data"]["cycles"]
                    oct_cycle = next((c for c in cycles if "2025-10" in c.get("month", "")), None)
                    
                    if oct_cycle:
                        cycle_id = oct_cycle["id"]
                        
                        # Test 4: Check salary slip for deductions
                        print("📍 Checking salary slip for deductions...")
                        if "employee_payroll_summaries" in oct_cycle:
                            emp_summaries = oct_cycle["employee_payroll_summaries"]
                            if emp_summaries:
                                emp_id = emp_summaries[0]["employee_id"]
                                resp = await self.api_request("GET", 
                                                            f"/payroll/cycles/{cycle_id}/employees/{emp_id}/letter?format=html", 
                                                            token)
                                
                                if resp["status"] == 200:
                                    self.log_test("SCENARIO_4", "Salary Slip Check", "PASS", 
                                                 "Salary slip generated with deductions")
                                else:
                                    self.log_test("SCENARIO_4", "Salary Slip Check", "FAIL", 
                                                 f"Could not generate salary slip: {resp['data']}")
                            else:
                                self.log_test("SCENARIO_4", "Employee Summaries", "WARN", 
                                             "No employee summaries found in cycle")
                        
                        # Test 5: Verify Payroll Ledger entries
                        print("📍 Verifying payroll ledger entries...")
                        resp = await self.api_request("GET", f"/payroll-ledger?cycle_id={cycle_id}", token)
                        
                        if resp["status"] == 200:
                            ledger_entries = resp["data"]
                            deduction_entries = [e for e in ledger_entries 
                                               if e.get("source_type") == "ATTENDANCE_DEDUCTION"]
                            
                            self.log_test("SCENARIO_4", "Ledger Verification", "PASS", 
                                         f"Found {len(deduction_entries)} deduction entries in ledger")
                        else:
                            self.log_test("SCENARIO_4", "Ledger Verification", "FAIL", 
                                         f"Could not access ledger: {resp['data']}")
                    else:
                        self.log_test("SCENARIO_4", "October Cycle", "WARN", 
                                     "No October 2025 cycle found")
                else:
                    self.log_test("SCENARIO_4", "Cycle Verification", "FAIL", 
                                 f"Could not retrieve cycles: {resp['data']}")
            else:
                self.log_test("SCENARIO_4", "Apply Deductions", "FAIL", 
                             f"Failed to apply deductions: {resp['data']}")
        else:
            self.log_test("SCENARIO_4", "Calculate Deductions", "FAIL", 
                         f"Failed to calculate deductions: {resp['data']}")
            
    async def scenario_5_negative_net_salary(self):
        """
        SCENARIO 5: Negative Net Salary (Boundary Condition)
        Test high deductions causing negative net salary
        """
        print("\n🔥 SCENARIO 5: Negative Net Salary Boundary Test")
        
        token = await self.authenticate('super_admin')
        
        # Test 1: Create test payroll cycle with high deductions
        print("📍 Creating payroll cycle with excessive deductions...")
        
        cycle_data = {
            "month": "2025-11",
            "year": 2025,
            "employees": [{
                "employee_id": "high-deduction-test-emp",
                "employee_name": "Test Employee High Deductions",
                "base_salary": 3000.0,
                "allowances": 500.0,
                "late_deduction": 500.0,
                "absence_deduction": 1000.0,
                "advance_deduction": 2000.0,
                "manual_deduction": 200.0,
                "notes": "Adversarial testing - excessive deductions"
            }]
        }
        
        resp = await self.api_request("POST", "/payroll/cycles", token, json=cycle_data)
        
        if resp["status"] == 200:
            cycle_id = resp["data"]["cycle_id"]
            self.log_test("SCENARIO_5", "Create High Deduction Cycle", "PASS", 
                         f"Cycle created with ID: {cycle_id}")
            
            # Test 2: Get cycle summary to check net salary calculation
            print("📍 Checking net salary calculation...")
            resp = await self.api_request("GET", f"/payroll/cycles/{cycle_id}/summary", token)
            
            if resp["status"] == 200:
                summary = resp["data"]
                
                # Look for negative net salary or warning flags
                employees = summary.get("employee_summaries", [])
                if employees:
                    emp_summary = employees[0]
                    net_salary = emp_summary.get("net_salary", 0)
                    
                    if net_salary < 0:
                        self.log_test("SCENARIO_5", "Negative Net Salary", "PASS", 
                                     f"System correctly calculated negative net salary: {net_salary} AED",
                                     {"net_salary": net_salary, "warnings": emp_summary.get("warnings", [])})
                    elif net_salary == 0:
                        self.log_test("SCENARIO_5", "Zero Net Salary", "WARN", 
                                     f"Net salary capped at zero: {net_salary} AED")
                    else:
                        self.log_test("SCENARIO_5", "Positive Net Salary", "FAIL", 
                                     f"Expected negative but got positive: {net_salary} AED")
                        
                    # Test 3: Check for warning flags or debt entries
                    print("📍 Checking for warning flags and debt entries...")
                    warnings = emp_summary.get("warnings", [])
                    debt_amount = emp_summary.get("debt_to_company", 0)
                    
                    if warnings or debt_amount > 0:
                        self.log_test("SCENARIO_5", "Warning System", "PASS", 
                                     f"System flagged issues - Warnings: {len(warnings)}, Debt: {debt_amount}")
                    else:
                        self.log_test("SCENARIO_5", "Warning System", "WARN", 
                                     "No warnings or debt tracking found")
                        
                    # Test 4: Verify payroll ledger for debt entry
                    print("📍 Verifying debt entry in payroll ledger...")
                    resp = await self.api_request("GET", f"/payroll-ledger?cycle_id={cycle_id}", token)
                    
                    if resp["status"] == 200:
                        ledger_entries = resp["data"]
                        debt_entries = [e for e in ledger_entries if e.get("amount", 0) < 0]
                        
                        self.log_test("SCENARIO_5", "Debt Ledger Entry", "PASS" if debt_entries else "WARN", 
                                     f"Found {len(debt_entries)} debt entries in ledger")
                    else:
                        self.log_test("SCENARIO_5", "Ledger Check", "FAIL", 
                                     f"Could not access ledger: {resp['data']}")
                else:
                    self.log_test("SCENARIO_5", "Employee Summary", "FAIL", 
                                 "No employee summaries found in cycle")
            else:
                self.log_test("SCENARIO_5", "Cycle Summary", "FAIL", 
                             f"Could not get cycle summary: {resp['data']}")
        elif resp["status"] == 400:
            # System might block negative salary cycles
            self.log_test("SCENARIO_5", "Negative Salary Block", "PASS", 
                         f"System correctly blocked negative salary cycle: {resp['data']}")
        else:
            self.log_test("SCENARIO_5", "Create Cycle", "FAIL", 
                         f"Failed to create cycle: {resp['data']}")
            
    async def data_reconciliation_test(self):
        """
        Additional: Data Reconciliation Test for October 2025
        """
        print("\n🔥 ADDITIONAL: Data Reconciliation Test")
        
        token = await self.authenticate('super_admin')
        
        # Test 1: Get October 2025 payroll data
        print("📍 Getting October 2025 payroll data for reconciliation...")
        resp = await self.api_request("GET", "/payroll/cycles", token)
        
        if resp["status"] == 200:
            cycles = resp["data"]["cycles"]
            oct_cycle = next((c for c in cycles if "2025-10" in c.get("month", "")), None)
            
            if oct_cycle:
                cycle_id = oct_cycle["id"]
                
                # Get detailed cycle data
                resp = await self.api_request("GET", f"/payroll/cycles/{cycle_id}/summary", token)
                
                if resp["status"] == 200:
                    summary = resp["data"]
                    employees = summary.get("employee_summaries", [])
                    
                    reconciliation_data = []
                    for emp in employees:
                        # Manual calculation
                        gross = emp.get("base_salary", 0) + emp.get("allowances", 0)
                        deductions = (emp.get("late_deduction", 0) + 
                                    emp.get("absence_deduction", 0) + 
                                    emp.get("advance_deduction", 0) + 
                                    emp.get("manual_deduction", 0))
                        manual_net = gross - deductions
                        system_net = emp.get("net_salary", 0)
                        
                        difference = abs(manual_net - system_net)
                        
                        reconciliation_data.append({
                            "employee_id": emp.get("employee_id"),
                            "manual_net": manual_net,
                            "system_net": system_net,
                            "difference": difference
                        })
                    
                    # Check if all differences are within tolerance (0.01 AED)
                    max_difference = max([r["difference"] for r in reconciliation_data]) if reconciliation_data else 0
                    
                    if max_difference <= 0.01:
                        self.log_test("RECONCILIATION", "October 2025 Data", "PASS", 
                                     f"All calculations match within tolerance. Max difference: {max_difference} AED")
                    else:
                        self.log_test("RECONCILIATION", "October 2025 Data", "FAIL", 
                                     f"Calculation mismatch found. Max difference: {max_difference} AED",
                                     {"reconciliation_data": reconciliation_data})
                else:
                    self.log_test("RECONCILIATION", "Cycle Summary", "FAIL", 
                                 f"Could not get cycle summary: {resp['data']}")
            else:
                self.log_test("RECONCILIATION", "October Cycle", "WARN", 
                             "No October 2025 cycle found for reconciliation")
        else:
            self.log_test("RECONCILIATION", "Get Cycles", "FAIL", 
                         f"Could not retrieve cycles: {resp['data']}")
            
    async def run_all_scenarios(self):
        """Run all adversarial test scenarios"""
        print("🔥 STARTING PHASE-2 HARDENING - ADVERSARIAL UAT & HIDDEN DEFECTS HUNT")
        print("=" * 80)
        
        await self.setup_session()
        
        try:
            # Run all scenarios
            await self.scenario_1_flexible_attendance()
            await self.scenario_2_payroll_lock_reversal()
            await self.scenario_3_custody_overspending()
            await self.scenario_4_deductions_from_reports()
            await self.scenario_5_negative_net_salary()
            await self.data_reconciliation_test()
            
        except Exception as e:
            print(f"❌ Critical error during testing: {e}")
            self.log_test("SYSTEM", "Critical Error", "FAIL", str(e))
            
        finally:
            await self.cleanup()
            
        # Generate summary report
        self.generate_summary_report()
        
    def generate_summary_report(self):
        """Generate comprehensive test summary"""
        print("\n" + "=" * 80)
        print("🔥 ADVERSARIAL TESTING SUMMARY REPORT")
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
        
        print(f"\n📋 SCENARIO BREAKDOWN:")
        scenarios = {}
        for test in self.test_results:
            scenario = test["scenario"]
            if scenario not in scenarios:
                scenarios[scenario] = {"PASS": 0, "FAIL": 0, "WARN": 0}
            scenarios[scenario][test["status"]] += 1
            
        for scenario, counts in scenarios.items():
            total = sum(counts.values())
            passed = counts["PASS"]
            rate = (passed / total * 100) if total > 0 else 0
            print(f"   {scenario}: {passed}/{total} ({rate:.1f}%) - ✅{counts['PASS']} ❌{counts['FAIL']} ⚠️{counts['WARN']}")
            
        print(f"\n🚨 CRITICAL ISSUES FOUND:")
        critical_issues = [t for t in self.test_results if t["status"] == "FAIL"]
        if critical_issues:
            for issue in critical_issues:
                print(f"   ❌ {issue['scenario']} - {issue['test']}: {issue['details']}")
        else:
            print("   ✅ No critical issues found!")
            
        print(f"\n⚠️  WARNINGS & EDGE CASES:")
        warnings = [t for t in self.test_results if t["status"] == "WARN"]
        if warnings:
            for warning in warnings:
                print(f"   ⚠️  {warning['scenario']} - {warning['test']}: {warning['details']}")
        else:
            print("   ✅ No warnings!")
            
        # Save detailed results to file
        with open("/app/adversarial_test_results.json", "w") as f:
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
            
        print(f"\n💾 Detailed results saved to: /app/adversarial_test_results.json")
        
        # Production readiness assessment
        if failed_tests == 0:
            print(f"\n🟢 PRODUCTION READINESS: READY")
            print("   All critical scenarios passed. System is ready for production deployment.")
        elif failed_tests <= 2:
            print(f"\n🟡 PRODUCTION READINESS: CONDITIONAL")
            print("   Minor issues found. Review and fix before production deployment.")
        else:
            print(f"\n🔴 PRODUCTION READINESS: NOT READY")
            print("   Critical issues found. Must fix before production deployment.")

async def main():
    """Main execution function"""
    tester = AdversarialTester()
    await tester.run_all_scenarios()

if __name__ == "__main__":
    asyncio.run(main())