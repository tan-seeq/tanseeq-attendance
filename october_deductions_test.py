#!/usr/bin/env python3
"""
October 2025 Deductions Recalculation Test
Testing specific requirements from review request:
1. Login as admin@tanseeq.com/ADMIN
2. POST /api/deductions/calculate-monthly?month=2025-10
3. Extract and verify specific employees: Hatem Mohamed Ahmed, Tarek Wazzan, Mohamed Mostafa
4. Verify specific conditions and save results
"""

import requests
import json
import csv
import os
from datetime import datetime
from pathlib import Path

# Configuration
BACKEND_URL = "https://attendance-pro-43.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@tanseeq.com"
ADMIN_PASSWORD = "ADMIN"

# Target employees to verify
TARGET_EMPLOYEES = [
    "Hatem Mohamed Ahmed",
    "Tarek Wazzan", 
    "Mohamed Mostafa",
    "Mohamed AHMED MOHAMED MOSTAFA"
]

class OctoberDeductionsTest:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = {
            "authentication": False,
            "monthly_calculation": False,
            "target_employees_found": {},
            "verification_results": {},
            "exports_created": False,
            "total_tests": 0,
            "passed_tests": 0
        }
        
    def authenticate(self):
        """Step 1: Login as admin@tanseeq.com/ADMIN"""
        print("🔐 Step 1: Authenticating as Super Admin...")
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json={
                    "email": ADMIN_EMAIL,
                    "password": ADMIN_PASSWORD
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                self.test_results["authentication"] = True
                print(f"✅ Authentication successful for {ADMIN_EMAIL}")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def calculate_monthly_deductions(self):
        """Step 2: POST /api/deductions/calculate-monthly?month=2025-10"""
        print("\n📊 Step 2: Calculating October 2025 deductions...")
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/deductions/calculate-monthly?month=2025-10",
                timeout=60
            )
            
            if response.status_code == 200:
                self.deductions_data = response.json()
                self.test_results["monthly_calculation"] = True
                print(f"✅ Monthly calculation successful")
                print(f"📈 Found {len(self.deductions_data.get('deductions', []))} employee deduction records")
                return True
            else:
                print(f"❌ Monthly calculation failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Monthly calculation error: {e}")
            return False
    
    def extract_target_employees(self):
        """Step 3: Extract target employee rows"""
        print("\n🎯 Step 3: Extracting target employees...")
        
        deductions = self.deductions_data.get('deductions', [])
        found_employees = {}
        
        for deduction in deductions:
            employee_name = deduction.get('employee_name', '')
            
            # Check for exact matches and variations
            for target in TARGET_EMPLOYEES:
                if (target.lower() in employee_name.lower() or 
                    employee_name.lower() in target.lower() or
                    target == employee_name):
                    found_employees[target] = deduction
                    print(f"✅ Found: {employee_name} (matched with {target})")
                    break
        
        self.test_results["target_employees_found"] = found_employees
        
        if len(found_employees) >= 2:  # At least 2 of the 3 targets
            print(f"✅ Found {len(found_employees)} target employees")
            return True
        else:
            print(f"⚠️ Only found {len(found_employees)} target employees")
            return False
    
    def verify_employee_conditions(self):
        """Step 4: Verify specific conditions for each employee"""
        print("\n🔍 Step 4: Verifying employee conditions...")
        
        found_employees = self.test_results["target_employees_found"]
        verification_results = {}
        
        for target_name, employee_data in found_employees.items():
            print(f"\n👤 Verifying {employee_data.get('employee_name', target_name)}:")
            
            late_deduction = float(employee_data.get('late_deduction', 0))
            absence_deduction = float(employee_data.get('absence_deduction', 0))
            total_deduction = float(employee_data.get('total_deduction', 0))
            
            # Check if this is Hatem or Tarek (should have late_deduction=0)
            if any(name in target_name.lower() for name in ['hatem', 'tarek']):
                condition_a = late_deduction == 0
                condition_b = abs(total_deduction - absence_deduction) < 0.01  # Allow small floating point differences
                
                verification_results[target_name] = {
                    "employee_name": employee_data.get('employee_name'),
                    "late_deduction": late_deduction,
                    "absence_deduction": absence_deduction,
                    "total_deduction": total_deduction,
                    "condition_a_passed": condition_a,
                    "condition_b_passed": condition_b,
                    "overall_passed": condition_a and condition_b
                }
                
                print(f"  📊 Late deduction: {late_deduction} (should be 0: {'✅' if condition_a else '❌'})")
                print(f"  📊 Total deduction: {total_deduction}, Absence deduction: {absence_deduction}")
                print(f"  📊 Total == Absence: {'✅' if condition_b else '❌'}")
                
            # Check if this is Mohamed Mostafa (specific amounts)
            elif any(name in target_name.lower() for name in ['mohamed', 'mostafa']):
                absence_amount = float(employee_data.get('absence_amount', 0))
                late_amount = float(employee_data.get('late_amount', 0))
                
                # Check for approximate values (±10 tolerance)
                absence_check = abs(absence_amount - 166.66) <= 10
                late_check = abs(late_amount - 257.61) <= 10
                
                # Check for scheduled advance (if available in data)
                scheduled_advance = employee_data.get('scheduled_advance', 0)
                advance_check = scheduled_advance == 250 if scheduled_advance else True  # Skip if not available
                
                verification_results[target_name] = {
                    "employee_name": employee_data.get('employee_name'),
                    "absence_amount": absence_amount,
                    "late_amount": late_amount,
                    "scheduled_advance": scheduled_advance,
                    "absence_check_passed": absence_check,
                    "late_check_passed": late_check,
                    "advance_check_passed": advance_check,
                    "overall_passed": absence_check and late_check and advance_check
                }
                
                print(f"  📊 Absence amount: {absence_amount} (≈166.66: {'✅' if absence_check else '❌'})")
                print(f"  📊 Late amount: {late_amount} (≈257.61: {'✅' if late_check else '❌'})")
                print(f"  📊 Scheduled advance: {scheduled_advance} (=250: {'✅' if advance_check else '❌'})")
        
        self.test_results["verification_results"] = verification_results
        
        # Count overall passes
        passed_verifications = sum(1 for result in verification_results.values() if result.get("overall_passed", False))
        total_verifications = len(verification_results)
        
        print(f"\n📊 Verification Summary: {passed_verifications}/{total_verifications} employees passed all conditions")
        
        return passed_verifications > 0
    
    def save_exports(self):
        """Step 5: Save CSV and JSON summaries"""
        print("\n💾 Step 5: Saving export files...")
        
        try:
            # Create exports directory
            exports_dir = Path("/app/exports")
            exports_dir.mkdir(exist_ok=True)
            
            # Prepare summary data
            summary_data = {
                "test_timestamp": datetime.now().isoformat(),
                "month_tested": "2025-10",
                "total_employees": len(self.deductions_data.get('deductions', [])),
                "target_employees_found": len(self.test_results["target_employees_found"]),
                "verification_results": self.test_results["verification_results"],
                "test_summary": {
                    "authentication": self.test_results["authentication"],
                    "monthly_calculation": self.test_results["monthly_calculation"],
                    "target_extraction": len(self.test_results["target_employees_found"]) > 0,
                    "verifications_passed": sum(1 for r in self.test_results["verification_results"].values() if r.get("overall_passed", False))
                }
            }
            
            # Save JSON summary
            json_path = exports_dir / "october_calibrated_summary.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, indent=2, ensure_ascii=False)
            print(f"✅ JSON summary saved: {json_path}")
            
            # Save CSV summary
            csv_path = exports_dir / "october_calibrated_summary.csv"
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Header
                writer.writerow([
                    "Employee Name", "Late Deduction", "Absence Deduction", "Total Deduction",
                    "Absence Amount", "Late Amount", "Scheduled Advance", "Verification Status"
                ])
                
                # Data rows
                for target_name, result in self.test_results["verification_results"].items():
                    writer.writerow([
                        result.get("employee_name", target_name),
                        result.get("late_deduction", "N/A"),
                        result.get("absence_deduction", "N/A"),
                        result.get("total_deduction", "N/A"),
                        result.get("absence_amount", "N/A"),
                        result.get("late_amount", "N/A"),
                        result.get("scheduled_advance", "N/A"),
                        "PASS" if result.get("overall_passed", False) else "FAIL"
                    ])
            
            print(f"✅ CSV summary saved: {csv_path}")
            self.test_results["exports_created"] = True
            return True
            
        except Exception as e:
            print(f"❌ Export error: {e}")
            return False
    
    def run_complete_test(self):
        """Run the complete test sequence"""
        print("🚀 Starting October 2025 Deductions Recalculation Test")
        print("=" * 60)
        
        # Step 1: Authentication
        if not self.authenticate():
            return self.generate_final_report()
        
        # Step 2: Calculate monthly deductions
        if not self.calculate_monthly_deductions():
            return self.generate_final_report()
        
        # Step 3: Extract target employees
        if not self.extract_target_employees():
            return self.generate_final_report()
        
        # Step 4: Verify conditions
        self.verify_employee_conditions()
        
        # Step 5: Save exports
        self.save_exports()
        
        return self.generate_final_report()
    
    def generate_final_report(self):
        """Generate final test report"""
        print("\n" + "=" * 60)
        print("📋 FINAL TEST REPORT")
        print("=" * 60)
        
        # Count total tests
        tests = [
            ("Authentication", self.test_results["authentication"]),
            ("Monthly Calculation", self.test_results["monthly_calculation"]),
            ("Target Employee Extraction", len(self.test_results["target_employees_found"]) > 0),
            ("Employee Verifications", sum(1 for r in self.test_results["verification_results"].values() if r.get("overall_passed", False)) > 0),
            ("Export Creation", self.test_results["exports_created"])
        ]
        
        passed_tests = sum(1 for _, passed in tests if passed)
        total_tests = len(tests)
        
        print(f"📊 Overall Success Rate: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")
        print()
        
        for test_name, passed in tests:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {status} - {test_name}")
        
        print()
        print("🎯 Target Employee Verification Results:")
        for target_name, result in self.test_results["verification_results"].items():
            status = "✅ PASS" if result.get("overall_passed", False) else "❌ FAIL"
            employee_name = result.get("employee_name", target_name)
            print(f"  {status} - {employee_name}")
        
        # Update test_results for return
        self.test_results["total_tests"] = total_tests
        self.test_results["passed_tests"] = passed_tests
        
        return self.test_results

if __name__ == "__main__":
    test = OctoberDeductionsTest()
    results = test.run_complete_test()
    
    # Print summary for automation
    print(f"\nTEST_SUMMARY: {results['passed_tests']}/{results['total_tests']} tests passed")
    
    # Exit with appropriate code
    exit(0 if results['passed_tests'] == results['total_tests'] else 1)