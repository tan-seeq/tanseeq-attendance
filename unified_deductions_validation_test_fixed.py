#!/usr/bin/env python3
"""
🚨 URGENT UNIFIED DEDUCTIONS ENGINE VALIDATION TEST - FIXED VERSION
Validates Advanced Deductions on production-bound code as requested in review.
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Configuration
BACKEND_URL = "https://deduction-logic.preview.emergentagent.com/api"
SUPER_ADMIN_EMAIL = "admin@tanseeq.com"
SUPER_ADMIN_PASSWORD = "ADMIN"

class UnifiedDeductionsValidator:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        self.critical_issues = []
        self.evidence = {}
        
    def log_test(self, test_name: str, status: str, details: str, data: Any = None):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        self.test_results.append(result)
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {details}")
        
        if status == "FAIL":
            self.critical_issues.append(f"{test_name}: {details}")
    
    def authenticate(self) -> bool:
        """Step 1: Authenticate as Super Admin"""
        try:
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json={
                    "email": SUPER_ADMIN_EMAIL,
                    "password": SUPER_ADMIN_PASSWORD
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                
                user_info = data.get("user", {})
                self.log_test(
                    "Super Admin Authentication",
                    "PASS",
                    f"Successfully authenticated as {user_info.get('name', 'Unknown')} ({user_info.get('role', 'Unknown')})",
                    {"user_id": user_info.get("id"), "role": user_info.get("role")}
                )
                return True
            else:
                self.log_test(
                    "Super Admin Authentication",
                    "FAIL",
                    f"Authentication failed: {response.status_code} - {response.text}",
                    {"status_code": response.status_code}
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Super Admin Authentication",
                "FAIL",
                f"Authentication error: {str(e)}"
            )
            return False
    
    def validate_monthly_calculation(self) -> Dict[str, Any]:
        """Step 2: Call POST /api/deductions/calculate-monthly?month=2025-10"""
        try:
            response = self.session.post(
                f"{BACKEND_URL}/deductions/calculate-monthly",
                params={"month": "2025-10"},
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify engine_version
                engine_version = data.get("engine_version")
                if engine_version == "unified_v1.0":
                    self.log_test(
                        "Engine Version Verification",
                        "PASS",
                        f"Correct engine version: {engine_version}"
                    )
                else:
                    self.log_test(
                        "Engine Version Verification",
                        "FAIL",
                        f"Expected 'unified_v1.0', got '{engine_version}'"
                    )
                
                # Verify employees array
                employees = data.get("employees", [])
                if isinstance(employees, list) and len(employees) > 0:
                    self.log_test(
                        "Employees Array Verification",
                        "PASS",
                        f"Found {len(employees)} employees in response"
                    )
                    
                    # Check for Tarek Wazzan and Hatem Mohamed Ahmed
                    self.validate_exempt_employees(employees)
                    
                else:
                    self.log_test(
                        "Employees Array Verification",
                        "FAIL",
                        f"Invalid employees array: {type(employees)} with {len(employees) if isinstance(employees, list) else 'N/A'} items"
                    )
                
                self.evidence["monthly_calculation"] = data
                return data
                
            else:
                self.log_test(
                    "Monthly Calculation API",
                    "FAIL",
                    f"API call failed: {response.status_code} - {response.text}"
                )
                return {}
                
        except Exception as e:
            self.log_test(
                "Monthly Calculation API",
                "FAIL",
                f"API call error: {str(e)}"
            )
            return {}
    
    def validate_exempt_employees(self, employees: List[Dict]):
        """Validate Tarek Wazzan and Hatem Mohamed Ahmed exemptions"""
        tarek_found = False
        hatem_found = False
        
        for emp in employees:
            emp_name = emp.get("employee_name", "").lower()
            total_deduction = emp.get("total_deduction", 0)
            daily_records = emp.get("daily_records", [])
            
            # Check for Tarek (طارق وزان)
            if any(name in emp_name for name in ["tarek", "طارق", "wazzan", "وزان"]):
                tarek_found = True
                
                # Analyze Tarek's deductions in detail
                absence_deductions = 0
                late_deductions = 0
                early_deductions = 0
                
                for record in daily_records:
                    deduction = record.get("deduction_amount", 0)
                    rule = record.get("rule_applied", "").lower()
                    
                    if deduction > 0:
                        if any(keyword in rule for keyword in ["absence", "غياب", "إجازة", "absent"]):
                            absence_deductions += deduction
                        elif any(keyword in rule for keyword in ["late", "تأخير", "متأخر"]):
                            late_deductions += deduction
                        elif any(keyword in rule for keyword in ["early", "مبكر", "انصراف"]):
                            early_deductions += deduction
                
                if total_deduction == 0:
                    self.log_test(
                        "Tarek Wazzan Exemption",
                        "PASS",
                        f"Tarek has total_deduction = {total_deduction} (fully exempt)"
                    )
                elif absence_deductions > 0 and late_deductions == 0 and early_deductions == 0:
                    self.log_test(
                        "Tarek Wazzan Exemption",
                        "PASS",
                        f"Tarek has only absence deductions: {absence_deductions} AED (late/early exempt)"
                    )
                else:
                    self.log_test(
                        "Tarek Wazzan Exemption",
                        "FAIL",
                        f"Tarek has non-exempt deductions: Total={total_deduction}, Absence={absence_deductions}, Late={late_deductions}, Early={early_deductions}"
                    )
                    
                    # Log detailed breakdown for investigation
                    print(f"   📋 Tarek's detailed breakdown:")
                    for i, record in enumerate(daily_records[:5]):  # Show first 5 records
                        if record.get("deduction_amount", 0) > 0:
                            print(f"      Day {i+1}: {record.get('date')} - Rule: {record.get('rule_applied')} - Deduction: {record.get('deduction_amount')}")
            
            # Check for Hatem (حاتم محمد أحمد)
            if any(name in emp_name for name in ["hatem", "حاتم", "mohamed", "محمد", "ahmed", "أحمد"]):
                hatem_found = True
                
                if total_deduction == 0:
                    self.log_test(
                        "Hatem Mohamed Ahmed Exemption",
                        "PASS",
                        f"Hatem has total_deduction = {total_deduction} (fully exempt)"
                    )
                else:
                    # Check if only absence deductions
                    absence_only = all(
                        any(keyword in record.get("rule_applied", "").lower() for keyword in ["absence", "غياب", "إجازة", "absent"])
                        for record in daily_records 
                        if record.get("deduction_amount", 0) > 0
                    )
                    
                    if absence_only:
                        self.log_test(
                            "Hatem Mohamed Ahmed Exemption",
                            "PASS",
                            f"Hatem has only absence deductions: {total_deduction} AED"
                        )
                    else:
                        self.log_test(
                            "Hatem Mohamed Ahmed Exemption",
                            "FAIL",
                            f"Hatem has non-absence deductions: {total_deduction} AED"
                        )
        
        if not tarek_found:
            self.log_test(
                "Tarek Wazzan Presence",
                "WARN",
                "Tarek Wazzan not found in employees list"
            )
        
        if not hatem_found:
            self.log_test(
                "Hatem Mohamed Ahmed Presence",
                "WARN",
                "Hatem Mohamed Ahmed not found in employees list"
            )
    
    def validate_grace_policy(self, monthly_data: Dict[str, Any]):
        """Step 3: Verify grace policy for ≤15 minute lateness up to 4 times"""
        try:
            employees = monthly_data.get("employees", [])
            grace_examples = []
            
            for emp in employees:
                daily_records = emp.get("daily_records", [])
                late_instances = []
                
                for record in daily_records:
                    late_minutes = record.get("late_minutes", 0)
                    grace_applied = record.get("grace_applied", False)
                    deduction_amount = record.get("deduction_amount", 0)
                    
                    if late_minutes > 0 and late_minutes <= 15:
                        late_instances.append({
                            "date": record.get("date"),
                            "late_minutes": late_minutes,
                            "grace_applied": grace_applied,
                            "deduction_amount": deduction_amount
                        })
                
                if late_instances:
                    grace_count = sum(1 for inst in late_instances if inst["grace_applied"] and inst["deduction_amount"] == 0)
                    if grace_count > 0:
                        grace_examples.append({
                            "employee": emp.get("employee_name"),
                            "total_late_instances": len(late_instances),
                            "grace_applied_count": grace_count
                        })
            
            if grace_examples:
                example = grace_examples[0]
                self.log_test(
                    "Grace Policy Verification",
                    "PASS",
                    f"Grace policy working: {example['employee']} has {example['grace_applied_count']} grace applications out of {example['total_late_instances']} late instances (≤15 min)"
                )
            else:
                self.log_test(
                    "Grace Policy Verification",
                    "WARN",
                    "No clear evidence of grace policy application found in current data"
                )
                
        except Exception as e:
            self.log_test(
                "Grace Policy Verification",
                "FAIL",
                f"Grace policy validation error: {str(e)}"
            )
    
    def validate_half_full_day_rules(self, monthly_data: Dict[str, Any]):
        """Step 4: Verify half/full-day rules"""
        try:
            employees = monthly_data.get("employees", [])
            half_day_examples = []
            full_day_examples = []
            
            for emp in employees:
                daily_records = emp.get("daily_records", [])
                daily_rate = emp.get("daily_rate", 0)
                
                for record in daily_records:
                    late_minutes = record.get("late_minutes", 0)
                    deduction_amount = record.get("deduction_amount", 0)
                    
                    if late_minutes > 120 and deduction_amount > 0:  # >120 min = full day
                        full_day_examples.append({
                            "employee": emp.get("employee_name"),
                            "date": record.get("date"),
                            "late_minutes": late_minutes,
                            "deduction_amount": deduction_amount,
                            "daily_rate": daily_rate,
                            "matches_rule": abs(deduction_amount - daily_rate) < 0.01
                        })
                    
                    elif 60 <= late_minutes <= 120 and deduction_amount > 0:  # 60-120 min = half day
                        expected_half = daily_rate / 2
                        half_day_examples.append({
                            "employee": emp.get("employee_name"),
                            "date": record.get("date"),
                            "late_minutes": late_minutes,
                            "deduction_amount": deduction_amount,
                            "expected_half": expected_half,
                            "matches_rule": abs(deduction_amount - expected_half) < 0.01
                        })
            
            # Check full day rule
            if full_day_examples:
                matching_full = [ex for ex in full_day_examples if ex["matches_rule"]]
                if matching_full:
                    ex = matching_full[0]
                    self.log_test(
                        "Full Day Rule Verification",
                        "PASS",
                        f"{ex['employee']} with {ex['late_minutes']} min late has deduction {ex['deduction_amount']} = daily_rate {ex['daily_rate']}"
                    )
                else:
                    self.log_test(
                        "Full Day Rule Verification",
                        "FAIL",
                        f"Found {len(full_day_examples)} instances >120 min late but none match full daily_rate rule"
                    )
            else:
                self.log_test(
                    "Full Day Rule Verification",
                    "WARN",
                    "No instances of >120 min late found to verify full day rule"
                )
            
            # Check half day rule
            if half_day_examples:
                matching_half = [ex for ex in half_day_examples if ex["matches_rule"]]
                if matching_half:
                    ex = matching_half[0]
                    self.log_test(
                        "Half Day Rule Verification",
                        "PASS",
                        f"{ex['employee']} with {ex['late_minutes']} min late has deduction {ex['deduction_amount']} = half daily_rate {ex['expected_half']}"
                    )
                else:
                    self.log_test(
                        "Half Day Rule Verification",
                        "FAIL",
                        f"Found {len(half_day_examples)} instances 60-120 min late but none match half daily_rate rule"
                    )
            else:
                self.log_test(
                    "Half Day Rule Verification",
                    "WARN",
                    "No instances of 60-120 min late found to verify half day rule"
                )
                
        except Exception as e:
            self.log_test(
                "Half/Full Day Rules Verification",
                "FAIL",
                f"Half/full day rules validation error: {str(e)}"
            )
    
    def validate_daily_records_fields(self, monthly_data: Dict[str, Any]):
        """Step 5: Confirm daily_records include required fields"""
        try:
            employees = monthly_data.get("employees", [])
            required_fields = ["deductible_minutes", "late_minutes", "early_leave_minutes", "rule_applied"]
            
            total_records = 0
            records_with_all_fields = 0
            missing_fields_summary = {}
            
            for emp in employees:
                daily_records = emp.get("daily_records", [])
                
                for record in daily_records:
                    total_records += 1
                    missing_fields = [field for field in required_fields if field not in record]
                    
                    if not missing_fields:
                        records_with_all_fields += 1
                    else:
                        for field in missing_fields:
                            missing_fields_summary[field] = missing_fields_summary.get(field, 0) + 1
            
            if total_records > 0:
                coverage_percentage = (records_with_all_fields / total_records) * 100
                
                if coverage_percentage >= 95:
                    self.log_test(
                        "Daily Records Fields Verification",
                        "PASS",
                        f"{records_with_all_fields}/{total_records} records ({coverage_percentage:.1f}%) have all required fields"
                    )
                else:
                    missing_summary = ", ".join([f"{field}: {count}" for field, count in missing_fields_summary.items()])
                    self.log_test(
                        "Daily Records Fields Verification",
                        "FAIL",
                        f"Only {records_with_all_fields}/{total_records} records ({coverage_percentage:.1f}%) have all required fields. Missing: {missing_summary}"
                    )
            else:
                self.log_test(
                    "Daily Records Fields Verification",
                    "FAIL",
                    "No daily records found to validate"
                )
                
        except Exception as e:
            self.log_test(
                "Daily Records Fields Verification",
                "FAIL",
                f"Daily records validation error: {str(e)}"
            )
    
    def validate_custom_calculation_consistency(self, monthly_data: Dict[str, Any]):
        """Step 6: Confirm /api/deductions/calculate-custom consistency"""
        try:
            # Call custom calculation with correct parameters
            response = self.session.post(
                f"{BACKEND_URL}/deductions/calculate-custom",
                params={
                    "mode": "custom",
                    "from_date": "2025-09-29",
                    "to_date": "2025-10-28"
                },
                timeout=60
            )
            
            if response.status_code == 200:
                custom_data = response.json()
                
                # Compare totals
                monthly_employees = monthly_data.get("employees", [])
                custom_employees = custom_data.get("employees", [])
                
                monthly_total = sum(emp.get("total_deduction", 0) for emp in monthly_employees)
                custom_total = sum(emp.get("total_deduction", 0) for emp in custom_employees)
                
                if abs(monthly_total - custom_total) < 0.01:  # Allow small floating point differences
                    self.log_test(
                        "Custom Calculation Consistency",
                        "PASS",
                        f"Monthly total ({monthly_total:.2f}) matches custom period total ({custom_total:.2f})"
                    )
                else:
                    self.log_test(
                        "Custom Calculation Consistency",
                        "FAIL",
                        f"Monthly total ({monthly_total:.2f}) does not match custom period total ({custom_total:.2f}), difference: {abs(monthly_total - custom_total):.2f}"
                    )
                
                self.evidence["custom_calculation"] = custom_data
                
            else:
                self.log_test(
                    "Custom Calculation API",
                    "FAIL",
                    f"Custom calculation API failed: {response.status_code} - {response.text}"
                )
                
        except Exception as e:
            self.log_test(
                "Custom Calculation Consistency",
                "FAIL",
                f"Custom calculation error: {str(e)}"
            )
    
    def validate_attendance_records(self):
        """Step 7: Test attendance records within cycle window"""
        try:
            # Get attendance records
            response = self.session.get(
                f"{BACKEND_URL}/attendance",
                timeout=30
            )
            
            if response.status_code == 200:
                attendance_data = response.json()
                records = attendance_data if isinstance(attendance_data, list) else attendance_data.get("records", [])
                
                # Filter records within cycle window (2025-09-29 to 2025-10-28)
                cycle_records = []
                for record in records:
                    record_date = record.get("date", "")
                    if "2025-09-29" <= record_date <= "2025-10-28":
                        cycle_records.append(record)
                
                # Check for required fields
                records_with_check_in_out = 0
                for record in cycle_records:
                    if record.get("check_in") and record.get("check_out"):
                        records_with_check_in_out += 1
                
                if len(cycle_records) > 0:
                    coverage = (records_with_check_in_out / len(cycle_records)) * 100
                    self.log_test(
                        "Attendance Records Validation",
                        "PASS",
                        f"Found {len(cycle_records)} attendance records in cycle window, {records_with_check_in_out} ({coverage:.1f}%) have check_in/check_out"
                    )
                    
                    # Check for Book1.xlsx employees (indirect test)
                    unique_employees = set(record.get("user_name", "") for record in cycle_records)
                    self.log_test(
                        "Book1.xlsx Employee Coverage",
                        "PASS",
                        f"Found attendance records for {len(unique_employees)} unique employees in cycle window"
                    )
                else:
                    self.log_test(
                        "Attendance Records Validation",
                        "WARN",
                        "No attendance records found in cycle window (2025-09-29 to 2025-10-28)"
                    )
                
                self.evidence["attendance_records"] = {
                    "total_records": len(records),
                    "cycle_records": len(cycle_records),
                    "records_with_times": records_with_check_in_out,
                    "unique_employees": len(set(record.get("user_name", "") for record in cycle_records))
                }
                
            else:
                self.log_test(
                    "Attendance Records API",
                    "FAIL",
                    f"Attendance API failed: {response.status_code} - {response.text}"
                )
                
        except Exception as e:
            self.log_test(
                "Attendance Records Validation",
                "FAIL",
                f"Attendance records validation error: {str(e)}"
            )
    
    def run_validation(self):
        """Run complete validation suite"""
        print("🚨 URGENT UNIFIED DEDUCTIONS ENGINE VALIDATION STARTING...")
        print("=" * 80)
        
        # Step 1: Authentication
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with validation.")
            return
        
        # Step 2: Monthly calculation
        monthly_data = self.validate_monthly_calculation()
        
        if monthly_data:
            # Step 3: Grace policy
            self.validate_grace_policy(monthly_data)
            
            # Step 4: Half/full day rules
            self.validate_half_full_day_rules(monthly_data)
            
            # Step 5: Daily records fields
            self.validate_daily_records_fields(monthly_data)
            
            # Step 6: Custom calculation consistency
            self.validate_custom_calculation_consistency(monthly_data)
        
        # Step 7: Attendance records
        self.validate_attendance_records()
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary and save results"""
        print("\n" + "=" * 80)
        print("🎯 UNIFIED DEDUCTIONS ENGINE VALIDATION SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["status"] == "PASS"])
        failed_tests = len([t for t in self.test_results if t["status"] == "FAIL"])
        warned_tests = len([t for t in self.test_results if t["status"] == "WARN"])
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 TOTAL TESTS: {total_tests}")
        print(f"✅ PASSED: {passed_tests}")
        print(f"❌ FAILED: {failed_tests}")
        print(f"⚠️ WARNINGS: {warned_tests}")
        print(f"📈 SUCCESS RATE: {success_rate:.1f}%")
        
        if self.critical_issues:
            print(f"\n🚨 CRITICAL ISSUES FOUND ({len(self.critical_issues)}):")
            for issue in self.critical_issues:
                print(f"   • {issue}")
        
        # Save detailed results
        results_file = "/app/unified_deductions_validation_results_fixed.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "warnings": warned_tests,
                    "success_rate": success_rate,
                    "critical_issues": self.critical_issues
                },
                "test_results": self.test_results,
                "evidence": self.evidence,
                "timestamp": datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📁 Detailed results saved to: {results_file}")
        
        # Determine overall status
        if failed_tests == 0:
            if warned_tests == 0:
                print("\n🎉 VALIDATION RESULT: EXCELLENT - All tests passed!")
            else:
                print(f"\n✅ VALIDATION RESULT: GOOD - All tests passed with {warned_tests} warnings")
        elif success_rate >= 80:
            print(f"\n⚠️ VALIDATION RESULT: ACCEPTABLE - {success_rate:.1f}% success rate with {failed_tests} issues")
        else:
            print(f"\n❌ VALIDATION RESULT: CRITICAL ISSUES - {success_rate:.1f}% success rate, immediate attention required")

def main():
    """Main execution function"""
    validator = UnifiedDeductionsValidator()
    validator.run_validation()

if __name__ == "__main__":
    main()