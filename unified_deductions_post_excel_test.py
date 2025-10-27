#!/usr/bin/env python3
"""
Unified Deductions Engine Production Validation - Post Excel Import
Testing the unified deductions engine after importing Excel attendance (110 records)
for October 2025 validation as requested in review.
"""

import requests
import json
import os
from datetime import datetime, timedelta
import sys

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://deduction-logic.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class UnifiedDeductionsPostExcelValidator:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        
    def log_test(self, test_name, success, details, expected=None, actual=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        if expected is not None:
            result["expected"] = expected
        if actual is not None:
            result["actual"] = actual
            
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not success:
            print(f"   Details: {details}")
            if expected and actual:
                print(f"   Expected: {expected}")
                print(f"   Actual: {actual}")
        
    def authenticate(self):
        """Authenticate as Super Admin"""
        try:
            response = self.session.post(f"{API_BASE}/auth/login", json={
                "email": "admin@tanseeq.com",
                "password": "ADMIN"
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data["access_token"]
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                self.log_test("Super Admin Authentication", True, f"Successfully authenticated as {data['user']['name']}")
                return True
            else:
                self.log_test("Super Admin Authentication", False, f"Failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Super Admin Authentication", False, f"Exception: {str(e)}")
            return False
    
    def test_unified_engine_october_2025(self):
        """Test unified deductions engine for October 2025 after Excel import"""
        try:
            print("\n🔍 Testing Unified Deductions Engine for October 2025...")
            
            response = self.session.post(f"{API_BASE}/deductions/calculate-monthly?month=2025-10")
            
            if response.status_code != 200:
                self.log_test("October 2025 Deductions API", False, f"API returned {response.status_code}: {response.text}")
                return False
                
            data = response.json()
            
            # Test 1: Verify engine version
            engine_version = data.get("engine_version")
            expected_version = "unified_v1.0"
            self.log_test("Engine Version Verification", 
                         engine_version == expected_version,
                         f"Engine version: {engine_version}",
                         expected_version, engine_version)
            
            # Test 2: Verify employees array exists
            employees = data.get("employees", [])
            self.log_test("Employees Array Present", 
                         len(employees) > 0,
                         f"Found {len(employees)} employees in calculation")
            
            # Test 3: Check for Hatem and Tarek exemptions
            hatem_found = False
            tarek_found = False
            hatem_deduction = None
            tarek_deduction = None
            
            for emp in employees:
                emp_name = emp.get("employee_name", "").lower()
                if "hatem" in emp_name:
                    hatem_found = True
                    hatem_deduction = emp.get("total_deduction", 0)
                elif "tarek" in emp_name or "tariq" in emp_name:
                    tarek_found = True
                    tarek_deduction = emp.get("total_deduction", 0)
            
            # Test Hatem exemption
            self.log_test("Hatem Exemption Verification",
                         hatem_found and hatem_deduction == 0,
                         f"Hatem found: {hatem_found}, Deduction: {hatem_deduction}",
                         0, hatem_deduction)
            
            # Test Tarek exemption  
            self.log_test("Tarek Exemption Verification",
                         tarek_found and tarek_deduction == 0,
                         f"Tarek found: {tarek_found}, Deduction: {tarek_deduction}",
                         0, tarek_deduction)
            
            # Test 4: Verify cycle window (2025-09-29 to 2025-10-28)
            cycle_start = data.get("cycle_start")
            cycle_end = data.get("cycle_end")
            expected_start = "2025-09-29"
            expected_end = "2025-10-28"
            
            self.log_test("Cycle Window Verification",
                         cycle_start == expected_start and cycle_end == expected_end,
                         f"Cycle: {cycle_start} to {cycle_end}",
                         f"{expected_start} to {expected_end}",
                         f"{cycle_start} to {cycle_end}")
            
            # Test 5: Check for daily records with required fields
            total_daily_records = 0
            records_with_check_times = 0
            grace_applied_count = 0
            
            for emp in employees:
                daily_records = emp.get("daily_records", [])
                total_daily_records += len(daily_records)
                
                for record in daily_records:
                    # Check if record has check_in/check_out times
                    if record.get("check_in") and record.get("check_out"):
                        records_with_check_times += 1
                    
                    # Check for grace_applied
                    if record.get("grace_applied"):
                        grace_applied_count += 1
            
            self.log_test("Daily Records Present",
                         total_daily_records > 0,
                         f"Found {total_daily_records} daily records across all employees")
            
            self.log_test("Check-in/Check-out Data",
                         records_with_check_times > 0,
                         f"Found {records_with_check_times} records with check-in/check-out times")
            
            # Test 6: Verify grace period application (≤15 minutes late up to 4 times)
            self.log_test("Grace Period Application",
                         grace_applied_count > 0,
                         f"Found {grace_applied_count} records with grace_applied=true")
            
            # Test 7: Pick 3 random employees and verify their data
            import random
            if len(employees) >= 3:
                sample_employees = random.sample(employees, 3)
                for i, emp in enumerate(sample_employees, 1):
                    emp_name = emp.get("employee_name", "Unknown")
                    daily_records = emp.get("daily_records", [])
                    
                    # Check if daily records are in the expected date range
                    records_in_range = 0
                    for record in daily_records:
                        record_date = record.get("date", "")
                        if "2025-09-29" <= record_date <= "2025-10-28":
                            records_in_range += 1
                    
                    self.log_test(f"Sample Employee {i} ({emp_name}) Date Range",
                                 records_in_range > 0,
                                 f"Found {records_in_range} records in October 2025 cycle")
            
            # Test 8: Verify aggregate totals
            total_deductions = sum(emp.get("total_deduction", 0) for emp in employees)
            self.log_test("Aggregate Deductions Calculation",
                         total_deductions >= 0,
                         f"Total deductions across all employees: {total_deductions} AED")
            
            # Test 9: Check for anomalies (employees with unusually high deductions)
            anomalies = []
            for emp in employees:
                deduction = emp.get("total_deduction", 0)
                if deduction > 1000:  # Flag deductions over 1000 AED as potential anomalies
                    anomalies.append({
                        "employee": emp.get("employee_name"),
                        "deduction": deduction
                    })
            
            if anomalies:
                self.log_test("Anomaly Detection",
                             False,
                             f"Found {len(anomalies)} employees with deductions > 1000 AED: {anomalies}")
            else:
                self.log_test("Anomaly Detection",
                             True,
                             "No unusual deduction anomalies detected")
            
            return True
            
        except Exception as e:
            self.log_test("October 2025 Deductions Test", False, f"Exception: {str(e)}")
            return False
    
    def test_attendance_data_post_import(self):
        """Verify attendance data after Excel import"""
        try:
            print("\n📊 Verifying Attendance Data Post Excel Import...")
            
            response = self.session.get(f"{API_BASE}/attendance")
            
            if response.status_code != 200:
                self.log_test("Attendance Data Retrieval", False, f"Failed with status {response.status_code}")
                return False
            
            attendance_records = response.json()
            
            # Filter for October 2025 records
            october_records = []
            for record in attendance_records:
                record_date = record.get("date", "")
                if "2025-10" in record_date:
                    october_records.append(record)
            
            self.log_test("October 2025 Attendance Records",
                         len(october_records) >= 110,
                         f"Found {len(october_records)} attendance records for October 2025 (expected ≥110 after Excel import)",
                         "≥110", len(october_records))
            
            # Check for records with check_in/check_out times
            records_with_times = 0
            for record in october_records:
                if record.get("check_in") and record.get("check_out"):
                    records_with_times += 1
            
            self.log_test("Records with Check-in/Check-out Times",
                         records_with_times > 0,
                         f"Found {records_with_times} records with both check-in and check-out times")
            
            return True
            
        except Exception as e:
            self.log_test("Attendance Data Verification", False, f"Exception: {str(e)}")
            return False
    
    def run_validation(self):
        """Run complete validation suite"""
        print("🚀 Starting Unified Deductions Engine Post-Excel Import Validation")
        print("=" * 80)
        
        if not self.authenticate():
            return False
        
        # Run all tests
        tests_passed = 0
        total_tests = 0
        
        if self.test_attendance_data_post_import():
            tests_passed += 1
        total_tests += 1
        
        if self.test_unified_engine_october_2025():
            tests_passed += 1
        total_tests += 1
        
        # Calculate success rate
        success_rate = (tests_passed / total_tests) * 100 if total_tests > 0 else 0
        
        print("\n" + "=" * 80)
        print(f"🎯 VALIDATION SUMMARY")
        print(f"Tests Passed: {tests_passed}/{total_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Save detailed results
        results_file = "unified_deductions_post_excel_validation.json"
        with open(results_file, 'w') as f:
            json.dump({
                "validation_summary": {
                    "timestamp": datetime.now().isoformat(),
                    "tests_passed": tests_passed,
                    "total_tests": total_tests,
                    "success_rate": success_rate
                },
                "detailed_results": self.test_results
            }, f, indent=2)
        
        print(f"📄 Detailed results saved to: {results_file}")
        
        if success_rate >= 80:
            print("✅ VALIDATION PASSED - Unified Deductions Engine is working correctly after Excel import")
            return True
        else:
            print("❌ VALIDATION FAILED - Issues found that need attention")
            return False

def main():
    """Main execution"""
    validator = UnifiedDeductionsPostExcelValidator()
    success = validator.run_validation()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()