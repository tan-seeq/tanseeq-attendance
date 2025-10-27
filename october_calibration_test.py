#!/usr/bin/env python3
"""
FINAL OCTOBER CALIBRATION VALIDATION TEST
=========================================

This test validates the unified deductions engine for October 2025 with specific
employee verification requirements as requested in the review.

Requirements:
1. Login as admin@tanseeq.com/ADMIN
2. POST /api/deductions/calculate-monthly?month=2025-10
3. Build per-employee summary with fields:
   - employee_name
   - absence_days
   - absence_amount (salary/30 rule)
   - late_minutes
   - late_amount (DailyRate/540)
   - scheduled_advances (if present)
   - total_deduction
4. Verify specific employees:
   - Hatem Mohamed Ahmed and Tarek Wazzan -> late_amount=0 and total_deduction==absence_amount
   - Mohamed Mostafa -> absence≈166.66, late≈257.61, scheduled_advance=250
5. Save results to /app/exports/october_calibrated_summary.json and .csv
6. Update test_result.md with pass/fail status
"""

import requests
import json
import csv
import os
from datetime import datetime
from pathlib import Path

# Configuration
BACKEND_URL = "https://deduction-logic.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@tanseeq.com"
ADMIN_PASSWORD = "ADMIN"

class OctoberCalibrationValidator:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.results = {
            "test_timestamp": datetime.now().isoformat(),
            "authentication": {"status": "pending"},
            "api_call": {"status": "pending"},
            "employee_summaries": [],
            "validations": {
                "hatem_mohamed_ahmed": {"status": "pending"},
                "tarek_wazzan": {"status": "pending"},
                "mohamed_mostafa": {"status": "pending"}
            },
            "exports": {"json": "pending", "csv": "pending"},
            "overall_status": "pending"
        }
        
    def authenticate(self):
        """Step 1: Login as admin@tanseeq.com/ADMIN"""
        print("🔐 Step 1: Authenticating as Super Admin...")
        
        try:
            login_data = {
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                
                self.results["authentication"] = {
                    "status": "success",
                    "user_role": data.get("user", {}).get("role"),
                    "user_name": data.get("user", {}).get("name")
                }
                print(f"✅ Authentication successful: {data.get('user', {}).get('name')} ({data.get('user', {}).get('role')})")
                return True
            else:
                self.results["authentication"] = {
                    "status": "failed",
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                print(f"❌ Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.results["authentication"] = {
                "status": "error",
                "error": str(e)
            }
            print(f"❌ Authentication error: {e}")
            return False
    
    def calculate_monthly_deductions(self):
        """Step 2: POST /api/deductions/calculate-monthly?month=2025-10"""
        print("📊 Step 2: Calculating monthly deductions for October 2025...")
        
        try:
            response = self.session.post(f"{BACKEND_URL}/deductions/calculate-monthly?month=2025-10")
            
            if response.status_code == 200:
                data = response.json()
                
                self.results["api_call"] = {
                    "status": "success",
                    "engine_version": data.get("engine_version"),
                    "cycle_window": data.get("cycle_window"),
                    "total_employees": len(data.get("employees", [])),
                    "total_deductions": data.get("total_deductions", 0)
                }
                
                print(f"✅ API call successful:")
                print(f"   Engine Version: {data.get('engine_version')}")
                print(f"   Cycle Window: {data.get('cycle_window')}")
                print(f"   Total Employees: {len(data.get('employees', []))}")
                print(f"   Total Deductions: {data.get('total_deductions', 0)} AED")
                
                return data
            else:
                self.results["api_call"] = {
                    "status": "failed",
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                print(f"❌ API call failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.results["api_call"] = {
                "status": "error",
                "error": str(e)
            }
            print(f"❌ API call error: {e}")
            return None
    
    def build_employee_summaries(self, deductions_data):
        """Step 3: Build per-employee summary with required fields"""
        print("📋 Step 3: Building per-employee summaries...")
        
        employees = deductions_data.get("employees", [])
        summaries = []
        
        for employee in employees:
            # Use the actual API response structure
            absence_deduction = employee.get("absence_deduction", 0)
            late_deduction = employee.get("late_deduction", 0)
            total_deduction = employee.get("total_deduction", 0)
            
            # Calculate absence days from daily records
            daily_records = employee.get("daily_records", [])
            absence_days = employee.get("absence_count", 0)
            total_late_minutes = employee.get("total_late_minutes", 0)
            
            # Get scheduled advances (check if present in API response)
            scheduled_advances = employee.get("scheduled_advances", 0)
            
            summary = {
                "employee_name": employee.get("employee_name", ""),
                "absence_days": absence_days,
                "absence_amount": round(absence_deduction, 2),
                "late_minutes": total_late_minutes,
                "late_amount": round(late_deduction, 2),
                "scheduled_advances": scheduled_advances,
                "total_deduction": total_deduction,
                # Additional fields for analysis
                "monthly_salary": employee.get("monthly_salary", 0),
                "daily_rate": employee.get("daily_rate", 0),
                "employee_id": employee.get("employee_id", "")
            }
            
            summaries.append(summary)
            
        self.results["employee_summaries"] = summaries
        print(f"✅ Built summaries for {len(summaries)} employees")
        
        return summaries
    
    def validate_specific_employees(self, summaries):
        """Step 4: Validate specific employees as requested"""
        print("🔍 Step 4: Validating specific employees...")
        
        # Find employees by name
        hatem_mohamed_ahmed = None
        tarek_wazzan = None
        mohamed_mostafa = None
        
        for summary in summaries:
            name = summary["employee_name"].lower()
            if "hatem" in name and "mohamed" in name and "ahmed" in name:
                hatem_mohamed_ahmed = summary
            elif "tarek" in name and "wazzan" in name:
                tarek_wazzan = summary
            elif "mohamed" in name and "mostafa" in name:
                mohamed_mostafa = summary
        
        # Validate Hatem Mohamed Ahmed
        if hatem_mohamed_ahmed:
            late_amount_zero = hatem_mohamed_ahmed["late_amount"] == 0
            total_equals_absence = hatem_mohamed_ahmed["total_deduction"] == hatem_mohamed_ahmed["absence_amount"]
            
            self.results["validations"]["hatem_mohamed_ahmed"] = {
                "status": "pass" if (late_amount_zero and total_equals_absence) else "fail",
                "found": True,
                "late_amount": hatem_mohamed_ahmed["late_amount"],
                "total_deduction": hatem_mohamed_ahmed["total_deduction"],
                "absence_amount": hatem_mohamed_ahmed["absence_amount"],
                "late_amount_zero": late_amount_zero,
                "total_equals_absence": total_equals_absence
            }
            
            print(f"🔍 Hatem Mohamed Ahmed:")
            print(f"   Late Amount: {hatem_mohamed_ahmed['late_amount']} (should be 0)")
            print(f"   Total Deduction: {hatem_mohamed_ahmed['total_deduction']}")
            print(f"   Absence Amount: {hatem_mohamed_ahmed['absence_amount']}")
            print(f"   ✅ Late Amount = 0: {late_amount_zero}")
            print(f"   ✅ Total = Absence: {total_equals_absence}")
        else:
            self.results["validations"]["hatem_mohamed_ahmed"] = {
                "status": "fail",
                "found": False,
                "error": "Employee not found"
            }
            print("❌ Hatem Mohamed Ahmed not found")
        
        # Validate Tarek Wazzan
        if tarek_wazzan:
            late_amount_zero = tarek_wazzan["late_amount"] == 0
            total_equals_absence = tarek_wazzan["total_deduction"] == tarek_wazzan["absence_amount"]
            
            self.results["validations"]["tarek_wazzan"] = {
                "status": "pass" if (late_amount_zero and total_equals_absence) else "fail",
                "found": True,
                "late_amount": tarek_wazzan["late_amount"],
                "total_deduction": tarek_wazzan["total_deduction"],
                "absence_amount": tarek_wazzan["absence_amount"],
                "late_amount_zero": late_amount_zero,
                "total_equals_absence": total_equals_absence
            }
            
            print(f"🔍 Tarek Wazzan:")
            print(f"   Late Amount: {tarek_wazzan['late_amount']} (should be 0)")
            print(f"   Total Deduction: {tarek_wazzan['total_deduction']}")
            print(f"   Absence Amount: {tarek_wazzan['absence_amount']}")
            print(f"   ✅ Late Amount = 0: {late_amount_zero}")
            print(f"   ✅ Total = Absence: {total_equals_absence}")
        else:
            self.results["validations"]["tarek_wazzan"] = {
                "status": "fail",
                "found": False,
                "error": "Employee not found"
            }
            print("❌ Tarek Wazzan not found")
        
        # Validate Mohamed Mostafa
        if mohamed_mostafa:
            absence_approx_166 = abs(mohamed_mostafa["absence_amount"] - 166.66) <= 10  # ±10 AED tolerance
            late_approx_257 = abs(mohamed_mostafa["late_amount"] - 257.61) <= 10  # ±10 AED tolerance
            scheduled_advance_250 = mohamed_mostafa["scheduled_advances"] == 250
            
            self.results["validations"]["mohamed_mostafa"] = {
                "status": "pass" if (absence_approx_166 and late_approx_257 and scheduled_advance_250) else "fail",
                "found": True,
                "absence_amount": mohamed_mostafa["absence_amount"],
                "late_amount": mohamed_mostafa["late_amount"],
                "scheduled_advances": mohamed_mostafa["scheduled_advances"],
                "absence_approx_166": absence_approx_166,
                "late_approx_257": late_approx_257,
                "scheduled_advance_250": scheduled_advance_250
            }
            
            print(f"🔍 Mohamed Mostafa:")
            print(f"   Absence Amount: {mohamed_mostafa['absence_amount']} (should be ≈166.66)")
            print(f"   Late Amount: {mohamed_mostafa['late_amount']} (should be ≈257.61)")
            print(f"   Scheduled Advances: {mohamed_mostafa['scheduled_advances']} (should be 250)")
            print(f"   ✅ Absence ≈ 166.66: {absence_approx_166}")
            print(f"   ✅ Late ≈ 257.61: {late_approx_257}")
            print(f"   ✅ Scheduled Advance = 250: {scheduled_advance_250}")
        else:
            self.results["validations"]["mohamed_mostafa"] = {
                "status": "fail",
                "found": False,
                "error": "Employee not found"
            }
            print("❌ Mohamed Mostafa not found")
    
    def export_results(self, summaries):
        """Step 5: Save results to JSON and CSV files"""
        print("💾 Step 5: Exporting results...")
        
        # Create exports directory
        exports_dir = Path("/app/exports")
        exports_dir.mkdir(exist_ok=True)
        
        try:
            # Export to JSON
            json_path = exports_dir / "october_calibrated_summary.json"
            export_data = {
                "metadata": {
                    "test_timestamp": self.results["test_timestamp"],
                    "engine_version": self.results["api_call"].get("engine_version"),
                    "cycle_window": self.results["api_call"].get("cycle_window"),
                    "total_employees": len(summaries)
                },
                "employee_summaries": summaries,
                "validations": self.results["validations"]
            }
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.results["exports"]["json"] = "success"
            print(f"✅ JSON exported to: {json_path}")
            
            # Export to CSV
            csv_path = exports_dir / "october_calibrated_summary.csv"
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                if summaries:
                    writer = csv.DictWriter(f, fieldnames=summaries[0].keys())
                    writer.writeheader()
                    writer.writerows(summaries)
            
            self.results["exports"]["csv"] = "success"
            print(f"✅ CSV exported to: {csv_path}")
            
        except Exception as e:
            self.results["exports"]["json"] = f"error: {e}"
            self.results["exports"]["csv"] = f"error: {e}"
            print(f"❌ Export error: {e}")
    
    def update_test_result_md(self):
        """Step 6: Update test_result.md with validation results"""
        print("📝 Step 6: Updating test_result.md...")
        
        try:
            # Determine overall status
            validations = self.results["validations"]
            all_passed = all(v.get("status") == "pass" for v in validations.values())
            overall_status = "PASS" if all_passed else "FAIL"
            
            self.results["overall_status"] = overall_status
            
            # Create status note
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status_note = f"""
        -working: {"true" if all_passed else "false"}
        -agent: "testing"
        -comment: "🎯 FINAL OCTOBER CALIBRATION VALIDATION COMPLETED - {overall_status}: Conducted comprehensive validation of unified deductions engine for October 2025 as requested in review. VALIDATION RESULTS: 1) ✅ AUTHENTICATION: admin@tanseeq.com/ADMIN successful 2) ✅ API ENDPOINT: POST /api/deductions/calculate-monthly?month=2025-10 operational 3) ✅ ENGINE VERSION: {self.results['api_call'].get('engine_version', 'N/A')} confirmed 4) SPECIFIC EMPLOYEE VALIDATIONS: Hatem Mohamed Ahmed - {validations['hatem_mohamed_ahmed']['status'].upper()} (late_amount={validations['hatem_mohamed_ahmed'].get('late_amount', 'N/A')}, total_deduction={validations['hatem_mohamed_ahmed'].get('total_deduction', 'N/A')}), Tarek Wazzan - {validations['tarek_wazzan']['status'].upper()} (late_amount={validations['tarek_wazzan'].get('late_amount', 'N/A')}, total_deduction={validations['tarek_wazzan'].get('total_deduction', 'N/A')}), Mohamed Mostafa - {validations['mohamed_mostafa']['status'].upper()} (absence≈{validations['mohamed_mostafa'].get('absence_amount', 'N/A')}, late≈{validations['mohamed_mostafa'].get('late_amount', 'N/A')}, advance={validations['mohamed_mostafa'].get('scheduled_advances', 'N/A')}) 5) ✅ EXPORTS: Results saved to /app/exports/october_calibrated_summary.json and .csv 6) OVERALL STATUS: {overall_status} - {'All validations passed successfully' if all_passed else 'Some validations failed - see details above'}. Test completed at {timestamp}."
"""
            
            # Read current test_result.md
            with open("/app/test_result.md", "r", encoding="utf-8") as f:
                content = f.read()
            
            # Find the Unified Deductions Engine Production Validation section
            if "Unified Deductions Engine Production Validation" in content:
                # Append to existing task
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if "task: \"Unified Deductions Engine Production Validation\"" in line:
                        # Find the status_history section for this task
                        j = i + 1
                        while j < len(lines) and not lines[j].strip().startswith("status_history:"):
                            j += 1
                        
                        if j < len(lines):
                            # Insert the new status note after status_history
                            lines.insert(j + 1, status_note)
                            break
                
                # Write back to file
                with open("/app/test_result.md", "w", encoding="utf-8") as f:
                    f.write('\n'.join(lines))
                
                print(f"✅ Updated test_result.md with {overall_status} status")
            else:
                print("⚠️ Unified Deductions Engine Production Validation section not found in test_result.md")
                
        except Exception as e:
            print(f"❌ Error updating test_result.md: {e}")
    
    def run_validation(self):
        """Run the complete October calibration validation"""
        print("🚀 Starting Final October Calibration Validation")
        print("=" * 60)
        
        # Step 1: Authentication
        if not self.authenticate():
            return False
        
        # Step 2: Calculate monthly deductions
        deductions_data = self.calculate_monthly_deductions()
        if not deductions_data:
            return False
        
        # Step 3: Build employee summaries
        summaries = self.build_employee_summaries(deductions_data)
        
        # Step 4: Validate specific employees
        self.validate_specific_employees(summaries)
        
        # Step 5: Export results
        self.export_results(summaries)
        
        # Step 6: Update test_result.md
        self.update_test_result_md()
        
        # Final summary
        print("\n" + "=" * 60)
        print("🎯 FINAL OCTOBER CALIBRATION VALIDATION SUMMARY")
        print("=" * 60)
        
        validations = self.results["validations"]
        all_passed = all(v.get("status") == "pass" for v in validations.values())
        
        print(f"Overall Status: {'✅ PASS' if all_passed else '❌ FAIL'}")
        print(f"Authentication: {'✅' if self.results['authentication']['status'] == 'success' else '❌'}")
        print(f"API Call: {'✅' if self.results['api_call']['status'] == 'success' else '❌'}")
        print(f"Hatem Mohamed Ahmed: {'✅ PASS' if validations['hatem_mohamed_ahmed']['status'] == 'pass' else '❌ FAIL'}")
        print(f"Tarek Wazzan: {'✅ PASS' if validations['tarek_wazzan']['status'] == 'pass' else '❌ FAIL'}")
        print(f"Mohamed Mostafa: {'✅ PASS' if validations['mohamed_mostafa']['status'] == 'pass' else '❌ FAIL'}")
        print(f"Exports: {'✅' if self.results['exports']['json'] == 'success' else '❌'}")
        
        return all_passed

if __name__ == "__main__":
    validator = OctoberCalibrationValidator()
    success = validator.run_validation()
    exit(0 if success else 1)