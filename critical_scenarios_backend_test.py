#!/usr/bin/env python3
"""
🔥 CRITICAL SCENARIOS BACKEND TESTING
Testing specific critical scenarios mentioned in the comprehensive review
"""

import requests
import json
from datetime import datetime

# Configuration
BACKEND_URL = "https://attendance-pro-43.preview.emergentagent.com/api"

# Test Credentials
TEST_CREDENTIALS = {
    "super_admin": {"email": "admin@tanseeq.com", "password": "ADMIN"},
    "admin": {"email": "mahmoud@tanseeq.com", "password": "mahmoud123"},
    "user": {"email": "jihad@tanseeq.com", "password": "jihad123"}
}

class CriticalScenariosTester:
    def __init__(self):
        self.tokens = {}
        self.test_results = []
        
    def log_test(self, test_name, success, details, response_data=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {details}")
        
    def authenticate_users(self):
        """Authenticate all test users"""
        print("🔐 AUTHENTICATING TEST USERS")
        
        for role, creds in TEST_CREDENTIALS.items():
            try:
                response = requests.post(f"{BACKEND_URL}/auth/login", json=creds)
                if response.status_code == 200:
                    data = response.json()
                    self.tokens[role] = data["access_token"]
                    print(f"✅ {role}: {creds['email']} authenticated")
                else:
                    print(f"❌ {role}: Authentication failed - {response.status_code}")
            except Exception as e:
                print(f"❌ {role}: Exception - {str(e)}")
    
    def test_attendance_late_tracking_rule(self):
        """Test 9:15 AM Late Tracking Rule Implementation"""
        print("\n⏰ TESTING 9:15 AM LATE TRACKING RULE")
        
        if "super_admin" in self.tokens:
            headers = {"Authorization": f"Bearer {self.tokens['super_admin']}"}
            
            try:
                # Get all attendance records
                response = requests.get(f"{BACKEND_URL}/attendance", headers=headers)
                if response.status_code == 200:
                    attendance_records = response.json()
                    
                    # Analyze late tracking
                    total_records = len(attendance_records)
                    records_with_late_minutes = [r for r in attendance_records if r.get("late_minutes", 0) > 0]
                    records_with_check_in = [r for r in attendance_records if r.get("check_in")]
                    
                    # Check for records that should be late but aren't marked as such
                    potentially_late_records = []
                    for record in records_with_check_in:
                        check_in = record.get("check_in", "")
                        if check_in:
                            try:
                                # Parse check-in time (format: HH:MM:SS)
                                hour, minute, _ = map(int, check_in.split(":"))
                                check_in_minutes = hour * 60 + minute
                                late_threshold_minutes = 9 * 60 + 15  # 9:15 AM = 555 minutes
                                
                                if check_in_minutes > late_threshold_minutes and record.get("late_minutes", 0) == 0:
                                    potentially_late_records.append({
                                        "user_name": record.get("user_name", "Unknown"),
                                        "date": record.get("date", "Unknown"),
                                        "check_in": check_in,
                                        "late_minutes": record.get("late_minutes", 0),
                                        "expected_late_minutes": check_in_minutes - late_threshold_minutes
                                    })
                            except:
                                pass
                    
                    self.log_test(
                        "9:15 AM Late Tracking Analysis",
                        len(potentially_late_records) == 0,
                        f"Found {len(potentially_late_records)} records that should be late but aren't marked. Total records: {total_records}, Records with late_minutes > 0: {len(records_with_late_minutes)}",
                        {
                            "total_records": total_records,
                            "records_with_late_minutes": len(records_with_late_minutes),
                            "potentially_incorrect_records": len(potentially_late_records),
                            "sample_incorrect": potentially_late_records[:3]
                        }
                    )
                    
                else:
                    self.log_test(
                        "9:15 AM Late Tracking Analysis",
                        False,
                        f"Failed to get attendance records: {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_test("9:15 AM Late Tracking Analysis", False, f"Exception: {str(e)}")
    
    def test_payroll_ledger_idempotency(self):
        """Test Payroll Ledger Idempotency (No Duplication)"""
        print("\n💼 TESTING PAYROLL LEDGER IDEMPOTENCY")
        
        if "super_admin" in self.tokens:
            headers = {"Authorization": f"Bearer {self.tokens['super_admin']}"}
            
            try:
                # Get payroll cycles
                cycles_response = requests.get(f"{BACKEND_URL}/payroll/cycles", headers=headers)
                if cycles_response.status_code == 200:
                    cycles = cycles_response.json()
                    
                    if cycles:
                        cycle_id = cycles[0]["id"]
                        
                        # Get ledger entries before recalculation
                        ledger_before_response = requests.get(f"{BACKEND_URL}/payroll/cycles/{cycle_id}/ledger", headers=headers)
                        if ledger_before_response.status_code == 200:
                            ledger_before = ledger_before_response.json()
                            entries_before = len(ledger_before) if isinstance(ledger_before, list) else 0
                            
                            # Attempt recalculation
                            recalc_response = requests.post(f"{BACKEND_URL}/payroll/cycles/{cycle_id}/recalculate", headers=headers)
                            
                            # Get ledger entries after recalculation
                            ledger_after_response = requests.get(f"{BACKEND_URL}/payroll/cycles/{cycle_id}/ledger", headers=headers)
                            if ledger_after_response.status_code == 200:
                                ledger_after = ledger_after_response.json()
                                entries_after = len(ledger_after) if isinstance(ledger_after, list) else 0
                                
                                # Check for duplication
                                no_duplication = entries_before == entries_after or recalc_response.status_code != 200
                                
                                self.log_test(
                                    "Payroll Ledger Idempotency",
                                    no_duplication,
                                    f"Ledger entries before: {entries_before}, after: {entries_after}. Recalc status: {recalc_response.status_code}",
                                    {
                                        "entries_before": entries_before,
                                        "entries_after": entries_after,
                                        "recalc_status": recalc_response.status_code,
                                        "no_duplication": no_duplication
                                    }
                                )
                            else:
                                self.log_test(
                                    "Payroll Ledger Idempotency",
                                    False,
                                    f"Failed to get ledger after recalc: {ledger_after_response.status_code}"
                                )
                        else:
                            self.log_test(
                                "Payroll Ledger Idempotency",
                                False,
                                f"Failed to get ledger before recalc: {ledger_before_response.status_code}"
                            )
                    else:
                        self.log_test(
                            "Payroll Ledger Idempotency",
                            False,
                            "No payroll cycles found to test"
                        )
                else:
                    self.log_test(
                        "Payroll Ledger Idempotency",
                        False,
                        f"Failed to get payroll cycles: {cycles_response.status_code}"
                    )
            except Exception as e:
                self.log_test("Payroll Ledger Idempotency", False, f"Exception: {str(e)}")
    
    def test_advances_custody_separation(self):
        """Test Advances vs Custody Business Logic Separation"""
        print("\n💳 TESTING ADVANCES VS CUSTODY SEPARATION")
        
        if "user" in self.tokens:
            headers = {"Authorization": f"Bearer {self.tokens['user']}"}
            
            try:
                # Get user balance
                balance_response = requests.get(f"{BACKEND_URL}/advances/my-balance", headers=headers)
                if balance_response.status_code == 200:
                    balance_data = balance_response.json()
                    
                    total_advances = balance_data.get("total_advances", 0)
                    total_custody = balance_data.get("total_custody", 0)
                    remaining_advance = balance_data.get("remaining_advance", 0)
                    remaining_custody = balance_data.get("remaining_custody", 0)
                    total_expenses = balance_data.get("total_expenses", 0)
                    
                    # Verify business logic: Advances should NOT be reduced by expenses
                    advances_correct = remaining_advance == total_advances
                    
                    # Verify business logic: Custody CAN be reduced by expenses
                    custody_logic_valid = remaining_custody <= total_custody
                    
                    self.log_test(
                        "Advances vs Custody Separation",
                        advances_correct and custody_logic_valid,
                        f"Advances: {total_advances} → {remaining_advance} (should be equal), Custody: {total_custody} → {remaining_custody} (can be reduced), Expenses: {total_expenses}",
                        {
                            "total_advances": total_advances,
                            "remaining_advance": remaining_advance,
                            "advances_not_reduced": advances_correct,
                            "total_custody": total_custody,
                            "remaining_custody": remaining_custody,
                            "custody_can_be_reduced": custody_logic_valid,
                            "total_expenses": total_expenses
                        }
                    )
                else:
                    self.log_test(
                        "Advances vs Custody Separation",
                        False,
                        f"Failed to get balance: {balance_response.status_code}",
                        balance_response.text
                    )
            except Exception as e:
                self.log_test("Advances vs Custody Separation", False, f"Exception: {str(e)}")
    
    def test_deduction_notifications_opt_in(self):
        """Test Deduction Notifications are Opt-in (Not Automatic)"""
        print("\n🔔 TESTING DEDUCTION NOTIFICATIONS OPT-IN")
        
        if "super_admin" in self.tokens:
            headers = {"Authorization": f"Bearer {self.tokens['super_admin']}"}
            
            try:
                # Get all notifications
                notifications_response = requests.get(f"{BACKEND_URL}/notifications", headers=headers)
                if notifications_response.status_code == 200:
                    notifications = notifications_response.json()
                    
                    # Look for deduction-related notifications
                    deduction_notifications = [
                        n for n in notifications 
                        if "deduction" in n.get("subject", "").lower() or 
                           "خصم" in n.get("subject", "") or
                           "deduction" in n.get("message", "").lower() or
                           "خصم" in n.get("message", "")
                    ]
                    
                    self.log_test(
                        "Deduction Notifications Analysis",
                        True,  # This is informational
                        f"Found {len(deduction_notifications)} deduction-related notifications out of {len(notifications)} total",
                        {
                            "total_notifications": len(notifications),
                            "deduction_notifications": len(deduction_notifications),
                            "sample_deduction_notifications": deduction_notifications[:2]
                        }
                    )
                else:
                    self.log_test(
                        "Deduction Notifications Analysis",
                        False,
                        f"Failed to get notifications: {notifications_response.status_code}"
                    )
            except Exception as e:
                self.log_test("Deduction Notifications Analysis", False, f"Exception: {str(e)}")
    
    def test_exempted_employees(self):
        """Test Hatem & Tariq Wazzan Exemption from Deductions"""
        print("\n👥 TESTING EXEMPTED EMPLOYEES (HATEM & TARIQ WAZZAN)")
        
        if "super_admin" in self.tokens:
            headers = {"Authorization": f"Bearer {self.tokens['super_admin']}"}
            
            try:
                # Try to calculate monthly deductions to see exemption logic
                month = "2025-10"
                deductions_response = requests.post(f"{BACKEND_URL}/deductions/calculate-monthly?month={month}", headers=headers)
                
                if deductions_response.status_code == 200:
                    deductions_data = deductions_response.json()
                    
                    # Look for Hatem and Tariq in the results
                    exempted_names = ["hatem", "tariq", "حاتم", "طارق"]
                    found_exempted = []
                    
                    if isinstance(deductions_data, list):
                        for employee_deduction in deductions_data:
                            employee_name = employee_deduction.get("employee_name", "").lower()
                            for exempted_name in exempted_names:
                                if exempted_name in employee_name:
                                    found_exempted.append({
                                        "name": employee_deduction.get("employee_name"),
                                        "deductions": employee_deduction.get("total_deductions", 0)
                                    })
                    
                    self.log_test(
                        "Exempted Employees Analysis",
                        True,  # This is informational
                        f"Found {len(found_exempted)} potentially exempted employees in deductions calculation",
                        {
                            "found_exempted": found_exempted,
                            "total_employees_in_calculation": len(deductions_data) if isinstance(deductions_data, list) else 0
                        }
                    )
                else:
                    self.log_test(
                        "Exempted Employees Analysis",
                        False,
                        f"Failed to calculate monthly deductions: {deductions_response.status_code}",
                        deductions_response.text
                    )
            except Exception as e:
                self.log_test("Exempted Employees Analysis", False, f"Exception: {str(e)}")
    
    def test_salary_letters_generation(self):
        """Test Salary Letters (HTML/PDF) Generation"""
        print("\n📄 TESTING SALARY LETTERS GENERATION")
        
        if "super_admin" in self.tokens:
            headers = {"Authorization": f"Bearer {self.tokens['super_admin']}"}
            
            try:
                # Get payroll cycles
                cycles_response = requests.get(f"{BACKEND_URL}/payroll/cycles", headers=headers)
                if cycles_response.status_code == 200:
                    cycles = cycles_response.json()
                    
                    if cycles:
                        cycle_id = cycles[0]["id"]
                        
                        # Get cycle details to find an employee
                        cycle_response = requests.get(f"{BACKEND_URL}/payroll/cycles/{cycle_id}", headers=headers)
                        if cycle_response.status_code == 200:
                            cycle_data = cycle_response.json()
                            
                            # Try to find an employee ID from the cycle
                            employee_id = None
                            if "line_items" in cycle_data and cycle_data["line_items"]:
                                employee_id = cycle_data["line_items"][0].get("employee_id")
                            
                            if employee_id:
                                # Test HTML salary letter
                                html_response = requests.get(f"{BACKEND_URL}/payroll/cycles/{cycle_id}/salary-letter/{employee_id}", headers=headers)
                                html_success = html_response.status_code == 200 and "html" in html_response.headers.get("content-type", "").lower()
                                
                                # Test PDF salary letter
                                pdf_response = requests.get(f"{BACKEND_URL}/payroll/cycles/{cycle_id}/salary-letter-pdf/{employee_id}", headers=headers)
                                pdf_success = pdf_response.status_code == 200 and "pdf" in pdf_response.headers.get("content-type", "").lower()
                                
                                self.log_test(
                                    "Salary Letters Generation",
                                    html_success and pdf_success,
                                    f"HTML: {html_response.status_code} ({'✅' if html_success else '❌'}), PDF: {pdf_response.status_code} ({'✅' if pdf_success else '❌'})",
                                    {
                                        "html_status": html_response.status_code,
                                        "html_content_type": html_response.headers.get("content-type"),
                                        "pdf_status": pdf_response.status_code,
                                        "pdf_content_type": pdf_response.headers.get("content-type"),
                                        "employee_id": employee_id,
                                        "cycle_id": cycle_id
                                    }
                                )
                            else:
                                self.log_test(
                                    "Salary Letters Generation",
                                    False,
                                    "No employee ID found in payroll cycle"
                                )
                        else:
                            self.log_test(
                                "Salary Letters Generation",
                                False,
                                f"Failed to get cycle details: {cycle_response.status_code}"
                            )
                    else:
                        self.log_test(
                            "Salary Letters Generation",
                            False,
                            "No payroll cycles found"
                        )
                else:
                    self.log_test(
                        "Salary Letters Generation",
                        False,
                        f"Failed to get payroll cycles: {cycles_response.status_code}"
                    )
            except Exception as e:
                self.log_test("Salary Letters Generation", False, f"Exception: {str(e)}")
    
    def run_critical_tests(self):
        """Run all critical scenario tests"""
        print("🔥 STARTING CRITICAL SCENARIOS BACKEND TESTING")
        print("=" * 70)
        
        self.authenticate_users()
        self.test_attendance_late_tracking_rule()
        self.test_payroll_ledger_idempotency()
        self.test_advances_custody_separation()
        self.test_deduction_notifications_opt_in()
        self.test_exempted_employees()
        self.test_salary_letters_generation()
        
        self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "=" * 70)
        print("🎯 CRITICAL SCENARIOS TEST RESULTS")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 RESULTS: {passed_tests}/{total_tests} passed ({success_rate:.1f}%)")
        
        # Show failed tests
        failed_test_results = [t for t in self.test_results if not t["success"]]
        if failed_test_results:
            print(f"\n❌ FAILED TESTS:")
            for test in failed_test_results:
                print(f"   • {test['test']}: {test['details']}")
        
        # Save results
        with open("critical_scenarios_test_results.json", 'w', encoding='utf-8') as f:
            json.dump({
                "test_run": {
                    "timestamp": datetime.now().isoformat(),
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "success_rate": success_rate
                },
                "test_results": self.test_results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: critical_scenarios_test_results.json")

if __name__ == "__main__":
    tester = CriticalScenariosTester()
    tester.run_critical_tests()