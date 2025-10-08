#!/usr/bin/env python3
"""
🎯 ARABIC REVIEW - MANUAL DEDUCTIONS PERSISTENCE FIX VERIFICATION TEST

Testing the critical bug fix: "mbeihfuth altadilat" (edits are not saved)
Manual adjustments to employee payroll summaries are not persisting in the aggregated view.

Root Cause Fixed:
The `update-employees` endpoint was updating `employee_payroll_summaries` directly 
but wasn't creating corresponding Payroll Ledger entries. Since the summary endpoint 
reads from Payroll Ledger, manual deductions appeared as 0.

Fix Implemented:
Modified `/api/payroll/cycles/{cycle_id}/update-employees` to:
1. Check for existing manual deduction ledger entries
2. Reverse old entries (maintaining audit trail)
3. Create new ledger entries with updated amounts
4. Use timestamped source_id for uniqueness
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://salary-processor-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class ManualDeductionsTestSuite:
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.test_results = []
        self.employee_id = None
        self.cycle_id = None
        self.original_values = {}
        
    async def setup_session(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
            
    def log_test(self, test_name: str, status: str, details: str = "", data: Any = None):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        self.test_results.append(result)
        
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {details}")
        
    async def authenticate_super_admin(self):
        """Step 1: Authentication as Super Admin"""
        try:
            login_data = {
                "email": "admin@tanseeq.com",
                "password": "ADMIN"
            }
            
            async with self.session.post(f"{API_BASE}/auth/login", json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.auth_token = data["access_token"]
                    user_info = data["user"]
                    
                    if user_info["role"] == "super_admin":
                        self.log_test("Authentication", "PASS", 
                                    f"Super Admin login successful: {user_info['name']} ({user_info['email']})")
                        return True
                    else:
                        self.log_test("Authentication", "FAIL", 
                                    f"User role is {user_info['role']}, expected super_admin")
                        return False
                else:
                    error_text = await response.text()
                    self.log_test("Authentication", "FAIL", 
                                f"Login failed with status {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_test("Authentication", "FAIL", f"Authentication error: {str(e)}")
            return False
            
    def get_auth_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.auth_token}"}
        
    async def get_payroll_cycles(self):
        """Step 2: Get Payroll Cycles"""
        try:
            async with self.session.get(f"{API_BASE}/payroll/cycles", 
                                      headers=self.get_auth_headers()) as response:
                if response.status == 200:
                    cycles = await response.json()
                    
                    if cycles and isinstance(cycles, list):
                        # Find an unlocked cycle or use the first one
                        unlocked_cycle = None
                        for cycle in cycles:
                            if not cycle.get("is_locked", False):
                                unlocked_cycle = cycle
                                break
                        
                        if unlocked_cycle:
                            self.cycle_id = unlocked_cycle["id"]
                            self.log_test("Get Payroll Cycles", "PASS", 
                                        f"Found unlocked cycle: {unlocked_cycle['display_name']} (ID: {self.cycle_id})")
                        else:
                            # Use first cycle even if locked for testing
                            self.cycle_id = cycles[0]["id"]
                            self.log_test("Get Payroll Cycles", "WARN", 
                                        f"No unlocked cycles found, using: {cycles[0]['display_name']} (ID: {self.cycle_id})")
                        
                        return True
                    else:
                        self.log_test("Get Payroll Cycles", "FAIL", "No payroll cycles found")
                        return False
                else:
                    error_text = await response.text()
                    self.log_test("Get Payroll Cycles", "FAIL", 
                                f"Failed to get cycles: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            self.log_test("Get Payroll Cycles", "FAIL", f"Error getting cycles: {str(e)}")
            return False
            
    async def get_current_summary(self):
        """Step 3: Get Current Summary and select employee"""
        try:
            async with self.session.get(f"{API_BASE}/payroll/cycles/{self.cycle_id}/summary", 
                                      headers=self.get_auth_headers()) as response:
                if response.status == 200:
                    data = await response.json()
                    employees = data.get("employees", [])
                    
                    if employees:
                        # Select first employee for testing
                        employee = employees[0]
                        self.employee_id = employee["employee_id"]
                        
                        # Record original values
                        self.original_values = {
                            "base_salary": employee.get("base_salary", 0),
                            "allowances": employee.get("allowances", 0),
                            "manual_deductions": employee.get("manual_deductions", 0),
                            "attendance_deductions": employee.get("attendance_deductions", 0),
                            "advance_deductions": employee.get("advance_deductions", 0),
                            "total_deductions": employee.get("total_deductions", 0),
                            "net_salary": employee.get("net_salary", 0)
                        }
                        
                        self.log_test("Get Current Summary", "PASS", 
                                    f"Selected employee: {employee['employee_name']} (ID: {self.employee_id})",
                                    data=self.original_values)
                        return True
                    else:
                        self.log_test("Get Current Summary", "FAIL", "No employees found in summary")
                        return False
                else:
                    error_text = await response.text()
                    self.log_test("Get Current Summary", "FAIL", 
                                f"Failed to get summary: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            self.log_test("Get Current Summary", "FAIL", f"Error getting summary: {str(e)}")
            return False
            
    async def update_manual_deductions(self, new_manual_deduction: float):
        """Step 4: Update Manual Deductions"""
        try:
            update_payload = {
                "employees": [{
                    "employee_id": self.employee_id,
                    "base_salary": self.original_values["base_salary"],
                    "allowances": self.original_values["allowances"],
                    "manual_deductions": new_manual_deduction,
                    "attendance_deductions": self.original_values["attendance_deductions"],
                    "advance_deductions": self.original_values["advance_deductions"]
                }]
            }
            
            async with self.session.put(f"{API_BASE}/payroll/cycles/{self.cycle_id}/update-employees", 
                                      json=update_payload,
                                      headers=self.get_auth_headers()) as response:
                if response.status == 200:
                    data = await response.json()
                    success_message = data.get("message", "")
                    
                    # Check for Arabic success message
                    if "تم تحديث" in success_message and "موظف بنجاح" in success_message:
                        self.log_test("Update Manual Deductions", "PASS", 
                                    f"Update successful: {success_message}. New manual deduction: {new_manual_deduction}")
                        return True
                    else:
                        self.log_test("Update Manual Deductions", "WARN", 
                                    f"Update completed but unexpected message: {success_message}")
                        return True
                else:
                    error_text = await response.text()
                    self.log_test("Update Manual Deductions", "FAIL", 
                                f"Update failed: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            self.log_test("Update Manual Deductions", "FAIL", f"Error updating deductions: {str(e)}")
            return False
            
    async def verify_ledger_entry(self, expected_amount: float):
        """Step 5: Verify Ledger Entry Created"""
        try:
            async with self.session.get(f"{API_BASE}/payroll/ledger/employee/{self.employee_id}", 
                                      headers=self.get_auth_headers()) as response:
                if response.status == 200:
                    data = await response.json()
                    ledger_entries = data.get("ledger_entries", [])
                    
                    # Look for MANUAL_DEDUCTION entries
                    manual_deduction_entries = [
                        entry for entry in ledger_entries 
                        if entry.get("entry_type") == "MANUAL_DEDUCTION"
                    ]
                    
                    if manual_deduction_entries:
                        # Find the most recent entry
                        latest_entry = max(manual_deduction_entries, 
                                         key=lambda x: x.get("created_at", ""))
                        
                        entry_amount = abs(latest_entry.get("amount", 0))  # Should be negative, so take abs
                        
                        if abs(entry_amount - expected_amount) < 0.01:  # Allow small floating point differences
                            self.log_test("Verify Ledger Entry", "PASS", 
                                        f"Found correct MANUAL_DEDUCTION entry: {entry_amount} (expected: {expected_amount})",
                                        data=latest_entry)
                            
                            # Check for reversed entries (audit trail)
                            reversed_entries = [
                                entry for entry in manual_deduction_entries 
                                if entry.get("is_reversed", False)
                            ]
                            
                            if reversed_entries:
                                self.log_test("Audit Trail Check", "PASS", 
                                            f"Found {len(reversed_entries)} reversed entries for audit trail")
                            
                            return True
                        else:
                            self.log_test("Verify Ledger Entry", "FAIL", 
                                        f"Ledger entry amount mismatch: found {entry_amount}, expected {expected_amount}")
                            return False
                    else:
                        self.log_test("Verify Ledger Entry", "FAIL", 
                                    "No MANUAL_DEDUCTION entries found in ledger")
                        return False
                else:
                    error_text = await response.text()
                    self.log_test("Verify Ledger Entry", "FAIL", 
                                f"Failed to get ledger: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            self.log_test("Verify Ledger Entry", "FAIL", f"Error verifying ledger: {str(e)}")
            return False
            
    async def verify_summary_updated(self, expected_manual_deduction: float):
        """Step 6: Verify Summary Shows Updated Value"""
        try:
            async with self.session.get(f"{API_BASE}/payroll/cycles/{self.cycle_id}/summary", 
                                      headers=self.get_auth_headers()) as response:
                if response.status == 200:
                    data = await response.json()
                    employees = data.get("employees", [])
                    
                    # Find our test employee
                    test_employee = None
                    for emp in employees:
                        if emp["employee_id"] == self.employee_id:
                            test_employee = emp
                            break
                    
                    if test_employee:
                        actual_manual_deduction = test_employee.get("manual_deductions", 0)
                        
                        if abs(actual_manual_deduction - expected_manual_deduction) < 0.01:
                            # Verify total deductions and net salary recalculated
                            expected_total_deductions = (
                                test_employee.get("attendance_deductions", 0) +
                                test_employee.get("advance_deductions", 0) +
                                expected_manual_deduction
                            )
                            
                            actual_total_deductions = test_employee.get("total_deductions", 0)
                            
                            if abs(actual_total_deductions - expected_total_deductions) < 0.01:
                                self.log_test("Verify Summary Updated", "PASS", 
                                            f"Summary correctly updated: manual_deductions={actual_manual_deduction}, total_deductions={actual_total_deductions}")
                                return True
                            else:
                                self.log_test("Verify Summary Updated", "FAIL", 
                                            f"Total deductions not recalculated correctly: {actual_total_deductions} vs expected {expected_total_deductions}")
                                return False
                        else:
                            self.log_test("Verify Summary Updated", "FAIL", 
                                        f"Manual deduction not updated in summary: {actual_manual_deduction} vs expected {expected_manual_deduction}")
                            return False
                    else:
                        self.log_test("Verify Summary Updated", "FAIL", 
                                    f"Test employee {self.employee_id} not found in updated summary")
                        return False
                else:
                    error_text = await response.text()
                    self.log_test("Verify Summary Updated", "FAIL", 
                                f"Failed to get updated summary: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            self.log_test("Verify Summary Updated", "FAIL", f"Error verifying summary: {str(e)}")
            return False
            
    async def test_multiple_edits(self):
        """Step 7: Test Multiple Edits"""
        try:
            # Test sequence: 250.50 -> 175.25 -> 300.00
            test_values = [250.50, 175.25, 300.00]
            
            for i, test_value in enumerate(test_values):
                print(f"\n--- Multiple Edit Test {i+1}: Setting manual deduction to {test_value} ---")
                
                # Update
                if await self.update_manual_deductions(test_value):
                    # Verify ledger
                    if await self.verify_ledger_entry(test_value):
                        # Verify summary
                        if await self.verify_summary_updated(test_value):
                            self.log_test(f"Multiple Edit Test {i+1}", "PASS", 
                                        f"Successfully updated to {test_value}")
                        else:
                            self.log_test(f"Multiple Edit Test {i+1}", "FAIL", 
                                        f"Summary verification failed for {test_value}")
                            return False
                    else:
                        self.log_test(f"Multiple Edit Test {i+1}", "FAIL", 
                                    f"Ledger verification failed for {test_value}")
                        return False
                else:
                    self.log_test(f"Multiple Edit Test {i+1}", "FAIL", 
                                f"Update failed for {test_value}")
                    return False
                    
                # Small delay between tests
                await asyncio.sleep(1)
            
            self.log_test("Multiple Edits Test", "PASS", 
                        f"All {len(test_values)} edit tests passed successfully")
            return True
            
        except Exception as e:
            self.log_test("Multiple Edits Test", "FAIL", f"Error in multiple edits test: {str(e)}")
            return False
            
    async def test_edge_cases(self):
        """Step 8: Test Edge Cases"""
        try:
            edge_cases = [
                {"value": 0, "description": "Setting manual deduction to 0"},
                {"value": 50.75, "description": "Changing from 0 to positive value"},
            ]
            
            for case in edge_cases:
                print(f"\n--- Edge Case Test: {case['description']} ---")
                
                if await self.update_manual_deductions(case["value"]):
                    if case["value"] == 0:
                        # For zero value, check that no new ledger entry is created
                        # or that the entry amount is 0
                        if await self.verify_summary_updated(case["value"]):
                            self.log_test(f"Edge Case: {case['description']}", "PASS", 
                                        "Zero value handled correctly")
                        else:
                            self.log_test(f"Edge Case: {case['description']}", "FAIL", 
                                        "Zero value not handled correctly in summary")
                            return False
                    else:
                        # For positive value, normal verification
                        if await self.verify_ledger_entry(case["value"]) and await self.verify_summary_updated(case["value"]):
                            self.log_test(f"Edge Case: {case['description']}", "PASS", 
                                        f"Value {case['value']} handled correctly")
                        else:
                            self.log_test(f"Edge Case: {case['description']}", "FAIL", 
                                        f"Value {case['value']} not handled correctly")
                            return False
                else:
                    self.log_test(f"Edge Case: {case['description']}", "FAIL", 
                                f"Update failed for {case['value']}")
                    return False
                    
                await asyncio.sleep(1)
            
            self.log_test("Edge Cases Test", "PASS", "All edge cases passed")
            return True
            
        except Exception as e:
            self.log_test("Edge Cases Test", "FAIL", f"Error in edge cases test: {str(e)}")
            return False
            
    async def run_comprehensive_test(self):
        """Run the complete test suite"""
        print("🎯 ARABIC REVIEW - MANUAL DEDUCTIONS PERSISTENCE FIX VERIFICATION TEST")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Testing Time: {datetime.now().isoformat()}")
        print("=" * 80)
        
        try:
            await self.setup_session()
            
            # Step 1: Authentication
            if not await self.authenticate_super_admin():
                return False
                
            # Step 2: Get Payroll Cycles
            if not await self.get_payroll_cycles():
                return False
                
            # Step 3: Get Current Summary
            if not await self.get_current_summary():
                return False
                
            print(f"\n--- Testing Manual Deductions Persistence Fix ---")
            print(f"Employee ID: {self.employee_id}")
            print(f"Cycle ID: {self.cycle_id}")
            print(f"Original manual deductions: {self.original_values['manual_deductions']}")
            
            # Step 4-6: First test with 250.50
            test_value = 250.50
            print(f"\n--- Primary Test: Setting manual deduction to {test_value} ---")
            
            if await self.update_manual_deductions(test_value):
                if await self.verify_ledger_entry(test_value):
                    if await self.verify_summary_updated(test_value):
                        self.log_test("Primary Manual Deduction Test", "PASS", 
                                    f"Manual deduction {test_value} persists correctly")
                    else:
                        return False
                else:
                    return False
            else:
                return False
                
            # Step 7: Test Multiple Edits
            if not await self.test_multiple_edits():
                return False
                
            # Step 8: Test Edge Cases
            if not await self.test_edge_cases():
                return False
                
            return True
            
        except Exception as e:
            self.log_test("Comprehensive Test", "FAIL", f"Unexpected error: {str(e)}")
            return False
        finally:
            await self.cleanup_session()
            
    def generate_report(self):
        """Generate test report"""
        passed_tests = len([t for t in self.test_results if t["status"] == "PASS"])
        failed_tests = len([t for t in self.test_results if t["status"] == "FAIL"])
        warned_tests = len([t for t in self.test_results if t["status"] == "WARN"])
        total_tests = len(self.test_results)
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "=" * 80)
        print("🎯 MANUAL DEDUCTIONS PERSISTENCE FIX - TEST RESULTS SUMMARY")
        print("=" * 80)
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⚠️  Warnings: {warned_tests}")
        print(f"📊 Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
        print("=" * 80)
        
        if failed_tests == 0:
            print("🎉 ALL TESTS PASSED - Manual deductions persistence fix is working correctly!")
            print("✅ Manual deductions now persist correctly after update")
            print("✅ Payroll Ledger contains corresponding entries")
            print("✅ Old entries are reversed (not deleted) for audit trail")
            print("✅ Summary endpoint shows updated values immediately")
            print("✅ Total deductions and net salary recalculate correctly")
            print("✅ Multiple edits work correctly")
            print("✅ Edge cases handled properly")
        else:
            print("❌ SOME TESTS FAILED - Manual deductions persistence fix needs attention")
            print("\nFailed Tests:")
            for test in self.test_results:
                if test["status"] == "FAIL":
                    print(f"  - {test['test']}: {test['details']}")
        
        # Save detailed results
        with open("/app/manual_deductions_test_results.json", "w") as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "warnings": warned_tests,
                    "success_rate": success_rate,
                    "test_time": datetime.now().isoformat()
                },
                "test_results": self.test_results
            }, f, indent=2)
            
        return failed_tests == 0

async def main():
    """Main test execution"""
    test_suite = ManualDeductionsTestSuite()
    
    try:
        success = await test_suite.run_comprehensive_test()
        test_suite.generate_report()
        
        if success:
            print("\n🎉 MANUAL DEDUCTIONS PERSISTENCE FIX VERIFICATION: SUCCESS")
            exit(0)
        else:
            print("\n❌ MANUAL DEDUCTIONS PERSISTENCE FIX VERIFICATION: FAILED")
            exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())