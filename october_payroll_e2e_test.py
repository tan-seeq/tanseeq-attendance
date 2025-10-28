#!/usr/bin/env python3
"""
October Payroll Cycle E2E Validation Test
=========================================

This test validates the complete October payroll cycle workflow as requested:
1. Authenticate as Super Admin (admin@tanseeq.com/ADMIN)
2. Create or fetch existing October payroll cycle
3. Recalculate employee summaries from current deductions
4. Verify at least 3 employees (Mohamed Mostafa, Kareem/Karim, Hesham)
5. Update employees with admin overrides
6. Generate salary letter HTML with Arabic fields
7. Save CSV summary report
"""

import requests
import json
import csv
import os
from datetime import datetime, timezone
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8001/api"
ADMIN_EMAIL = "admin@tanseeq.com"
ADMIN_PASSWORD = "ADMIN"

# Target employees to verify
TARGET_EMPLOYEES = ["Mohamed Mostafa", "Kareem", "Karim", "Hesham"]

class OctoberPayrollE2ETest:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.admin_user = None
        self.october_cycle = None
        self.test_results = []
        self.employee_summaries = []
        
    def log_result(self, test_name, status, details="", error=None):
        """Log test result"""
        result = {
            "test_name": test_name,
            "status": status,
            "details": details,
            "error": str(error) if error else None,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status_icon = "✅" if status == "PASS" else "❌"
        print(f"{status_icon} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
        if error:
            print(f"   Error: {error}")
    
    def authenticate_super_admin(self):
        """Step 1: Authenticate as Super Admin"""
        try:
            login_data = {
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            }
            
            response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data["access_token"]
                self.admin_user = data["user"]
                
                # Set authorization header for future requests
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                self.log_result(
                    "Super Admin Authentication",
                    "PASS",
                    f"Authenticated as {self.admin_user['name']} ({self.admin_user['role']})"
                )
                return True
            else:
                self.log_result(
                    "Super Admin Authentication",
                    "FAIL",
                    f"HTTP {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Super Admin Authentication", "FAIL", error=e)
            return False
    
    def get_or_create_october_cycle(self):
        """Step 2: Get or create October payroll cycle"""
        try:
            # First, try to get existing payroll cycles
            response = self.session.get(f"{BASE_URL}/payroll/cycles")
            
            if response.status_code == 200:
                cycles = response.json()
                
                # Look for October 2025 cycle
                october_cycle = None
                for cycle in cycles:
                    if ("2025-10" in cycle.get("period", "") or 
                        "2025-10" in cycle.get("month", "") or 
                        "October" in cycle.get("period", "")):
                        october_cycle = cycle
                        break
                
                if october_cycle:
                    self.october_cycle = october_cycle
                    self.log_result(
                        "October Cycle Retrieval",
                        "PASS",
                        f"Found existing October cycle: {october_cycle['id']}"
                    )
                    return True
                else:
                    # Create new October cycle
                    return self.create_october_cycle()
            else:
                self.log_result(
                    "October Cycle Retrieval",
                    "FAIL",
                    f"HTTP {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("October Cycle Retrieval", "FAIL", error=e)
            return False
    
    def create_october_cycle(self):
        """Create new October payroll cycle"""
        try:
            cycle_data = {
                "month": "2025-10",
                "period": "2025-10",
                "start_date": "2025-10-01",
                "end_date": "2025-10-31",
                "description": "October 2025 Payroll Cycle - E2E Test"
            }
            
            response = self.session.post(f"{BASE_URL}/payroll/cycles", json=cycle_data)
            
            if response.status_code in [200, 201]:
                self.october_cycle = response.json()
                self.log_result(
                    "October Cycle Creation",
                    "PASS",
                    f"Created October cycle: {self.october_cycle['id']}"
                )
                return True
            else:
                self.log_result(
                    "October Cycle Creation",
                    "FAIL",
                    f"HTTP {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("October Cycle Creation", "FAIL", error=e)
            return False
    
    def recalculate_employee_summaries(self):
        """Step 3: Recalculate employee summaries from current deductions"""
        try:
            cycle_id = self.october_cycle["id"]
            response = self.session.post(f"{BASE_URL}/payroll/cycles/{cycle_id}/recalculate")
            
            if response.status_code == 200:
                result = response.json()
                self.log_result(
                    "Employee Summaries Recalculation",
                    "PASS",
                    f"Recalculated summaries for cycle {cycle_id}"
                )
                return True
            else:
                self.log_result(
                    "Employee Summaries Recalculation",
                    "FAIL",
                    f"HTTP {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Employee Summaries Recalculation", "FAIL", error=e)
            return False
    
    def verify_target_employees(self):
        """Step 4: Verify at least 3 target employees with required fields"""
        try:
            cycle_id = self.october_cycle["id"]
            response = self.session.get(f"{BASE_URL}/payroll/cycles/{cycle_id}/summary")
            
            if response.status_code == 200:
                summary_data = response.json()
                employee_summaries = summary_data.get("employee_summaries", [])
                
                # Find target employees
                found_employees = []
                for summary in employee_summaries:
                    employee_name = summary.get("employee_name", "")
                    
                    # Check if this employee matches any target name
                    for target in TARGET_EMPLOYEES:
                        if target.lower() in employee_name.lower():
                            found_employees.append(summary)
                            break
                
                if len(found_employees) >= 3:
                    # Verify required fields for each employee
                    required_fields = [
                        "base_salary", "total_allowances", "gross_salary",
                        "manual_deductions", "attendance_deductions", 
                        "advance_deductions", "total_deductions", "net_salary"
                    ]
                    
                    all_valid = True
                    for employee in found_employees[:3]:  # Take first 3
                        missing_fields = []
                        for field in required_fields:
                            if field not in employee:
                                missing_fields.append(field)
                        
                        if missing_fields:
                            all_valid = False
                            self.log_result(
                                f"Employee Verification - {employee.get('employee_name')}",
                                "FAIL",
                                f"Missing fields: {missing_fields}"
                            )
                        else:
                            self.employee_summaries.append(employee)
                            self.log_result(
                                f"Employee Verification - {employee.get('employee_name')}",
                                "PASS",
                                f"All required fields present"
                            )
                    
                    if all_valid:
                        self.log_result(
                            "Target Employees Verification",
                            "PASS",
                            f"Verified {len(found_employees)} target employees with all required fields"
                        )
                        return True
                    else:
                        return False
                else:
                    self.log_result(
                        "Target Employees Verification",
                        "FAIL",
                        f"Found only {len(found_employees)} target employees, need at least 3"
                    )
                    return False
            else:
                self.log_result(
                    "Target Employees Verification",
                    "FAIL",
                    f"HTTP {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Target Employees Verification", "FAIL", error=e)
            return False
    
    def update_employees_with_overrides(self):
        """Step 5: Update employees with sample admin overrides"""
        try:
            if not self.employee_summaries:
                self.log_result(
                    "Employee Updates with Overrides",
                    "FAIL",
                    "No employee summaries available for updates"
                )
                return False
            
            cycle_id = self.october_cycle["id"]
            
            # Prepare sample overrides for first employee
            first_employee = self.employee_summaries[0]
            employee_id = first_employee.get("employee_id")
            
            override_data = {
                "employees": [
                    {
                        "employee_id": employee_id,
                        "manual_deductions": first_employee.get("manual_deductions", 0) + 100,  # Add 100 AED override
                        "bonus": 500,  # Add bonus
                        "notes": "E2E Test Override - October Cycle"
                    }
                ]
            }
            
            response = self.session.put(
                f"{BASE_URL}/payroll/cycles/{cycle_id}/update-employees",
                json=override_data
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log_result(
                    "Employee Updates with Overrides",
                    "PASS",
                    f"Successfully updated employee {first_employee.get('employee_name')} with overrides"
                )
                return True
            else:
                self.log_result(
                    "Employee Updates with Overrides",
                    "FAIL",
                    f"HTTP {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Employee Updates with Overrides", "FAIL", error=e)
            return False
    
    def generate_salary_letter_html(self):
        """Step 6: Generate salary letter HTML and verify Arabic fields"""
        try:
            if not self.employee_summaries:
                self.log_result(
                    "Salary Letter HTML Generation",
                    "FAIL",
                    "No employee summaries available for letter generation"
                )
                return False
            
            cycle_id = self.october_cycle["id"]
            employee_id = self.employee_summaries[0].get("employee_id")
            
            response = self.session.get(
                f"{BASE_URL}/payroll/cycles/{cycle_id}/employees/{employee_id}/letter"
            )
            
            if response.status_code == 200:
                html_content = response.text
                
                # Check for Arabic content
                arabic_indicators = [
                    "الراتب", "الموظف", "درهم", "الإجمالي", "الخصومات",
                    "الراتب الصافي", "التاريخ", "الشهر"
                ]
                
                found_arabic = []
                for indicator in arabic_indicators:
                    if indicator in html_content:
                        found_arabic.append(indicator)
                
                if found_arabic:
                    self.log_result(
                        "Salary Letter HTML Generation",
                        "PASS",
                        f"Generated HTML letter with Arabic fields: {found_arabic}"
                    )
                    return True
                else:
                    self.log_result(
                        "Salary Letter HTML Generation",
                        "FAIL",
                        "HTML generated but no Arabic fields detected"
                    )
                    return False
            else:
                self.log_result(
                    "Salary Letter HTML Generation",
                    "FAIL",
                    f"HTTP {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Salary Letter HTML Generation", "FAIL", error=e)
            return False
    
    def save_csv_summary(self):
        """Step 7: Save CSV summary of the three employees"""
        try:
            # Create exports directory if it doesn't exist
            exports_dir = Path("/app/exports")
            exports_dir.mkdir(exist_ok=True)
            
            csv_file_path = exports_dir / "october_cycle_validation.csv"
            
            if not self.employee_summaries:
                self.log_result(
                    "CSV Summary Generation",
                    "FAIL",
                    "No employee summaries available for CSV export"
                )
                return False
            
            # Prepare CSV data
            fieldnames = [
                "employee_name", "employee_id", "base_salary", "total_allowances",
                "gross_salary", "manual_deductions", "attendance_deductions",
                "advance_deductions", "total_deductions", "net_salary"
            ]
            
            with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for employee in self.employee_summaries[:3]:  # Take first 3
                    row_data = {field: employee.get(field, 0) for field in fieldnames}
                    writer.writerow(row_data)
            
            self.log_result(
                "CSV Summary Generation",
                "PASS",
                f"Saved CSV summary to {csv_file_path} with {len(self.employee_summaries[:3])} employees"
            )
            return True
            
        except Exception as e:
            self.log_result("CSV Summary Generation", "FAIL", error=e)
            return False
    
    def run_full_e2e_test(self):
        """Run the complete October payroll E2E validation"""
        print("🚀 Starting October Payroll Cycle E2E Validation")
        print("=" * 60)
        
        # Step 1: Authentication
        if not self.authenticate_super_admin():
            return False
        
        # Step 2: Get/Create October cycle
        if not self.get_or_create_october_cycle():
            return False
        
        # Step 3: Recalculate summaries
        if not self.recalculate_employee_summaries():
            return False
        
        # Step 4: Verify target employees
        if not self.verify_target_employees():
            return False
        
        # Step 5: Update with overrides
        if not self.update_employees_with_overrides():
            return False
        
        # Step 6: Generate salary letter
        if not self.generate_salary_letter_html():
            return False
        
        # Step 7: Save CSV summary
        if not self.save_csv_summary():
            return False
        
        return True
    
    def generate_final_report(self):
        """Generate final PASS/FAIL report"""
        print("\n" + "=" * 60)
        print("📊 OCTOBER PAYROLL E2E VALIDATION REPORT")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            print(f"{status_icon} {result['test_name']}: {result['status']}")
            if result["details"]:
                print(f"   └─ {result['details']}")
            if result["error"]:
                print(f"   └─ Error: {result['error']}")
        
        # Overall result
        overall_status = "PASS" if failed_tests == 0 else "FAIL"
        print(f"\n🎯 OVERALL RESULT: {overall_status}")
        
        if overall_status == "PASS":
            print("✅ October payroll cycle E2E validation completed successfully!")
            print("✅ All required functionality is working correctly")
            print("✅ CSV summary saved to /app/exports/october_cycle_validation.csv")
        else:
            print("❌ October payroll cycle E2E validation failed!")
            print("❌ Critical issues found that need to be addressed")
        
        return overall_status == "PASS"

def main():
    """Main execution function"""
    test = OctoberPayrollE2ETest()
    
    try:
        success = test.run_full_e2e_test()
        test.generate_final_report()
        
        # Save detailed results to JSON
        results_file = Path("/app/exports/october_e2e_test_results.json")
        results_file.parent.mkdir(exist_ok=True)
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                "test_results": test.test_results,
                "employee_summaries": test.employee_summaries,
                "october_cycle": test.october_cycle,
                "overall_success": success,
                "timestamp": datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        return success
        
    except Exception as e:
        print(f"❌ Critical error during E2E test execution: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)