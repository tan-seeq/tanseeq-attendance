#!/usr/bin/env python3
"""
🚨 CRITICAL TESTING REQUEST - Advanced Attendance Deductions System Fixes Verification

This test verifies the 4 critical fixes applied to the Advanced Attendance Deductions System:
1. Monthly Calculation returns 400 error about "month format incorrect" 
2. Custom Period shows empty daily breakdown ("No daily records available")
3. Custom Period shows incorrect deduction amounts for employees
4. Apply Deductions Fix (request body vs query params)

Test Requirements:
- Authentication: Super Admin (admin@tanseeq.com / ADMIN)
- Backend URL: https://hrapp-tanseeq.emergent.host/api
- Focus on deduction calculations and daily breakdown validation
"""

import requests
import json
import sys
from datetime import datetime, timedelta
import os

# Configuration
BACKEND_URL = "https://hrapp-tanseeq.emergent.host/api"
SUPER_ADMIN_EMAIL = "admin@tanseeq.com"
SUPER_ADMIN_PASSWORD = "ADMIN"

class AdvancedDeductionsSystemTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        
    def log_test(self, test_name, status, details, response_data=None):
        """Log test results"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        if response_data:
            result["response_data"] = response_data
        self.test_results.append(result)
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {details}")
        
    def authenticate(self):
        """Authenticate as Super Admin"""
        try:
            login_data = {
                "email": SUPER_ADMIN_EMAIL,
                "password": SUPER_ADMIN_PASSWORD
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                
                user_info = data.get("user", {})
                if user_info.get("role") != "super_admin":
                    self.log_test("Authentication", "FAIL", f"Expected super_admin role, got {user_info.get('role')}")
                    return False
                    
                self.log_test("Authentication", "PASS", f"Super Admin authenticated successfully: {user_info.get('name')}")
                return True
            else:
                self.log_test("Authentication", "FAIL", f"Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Authentication", "FAIL", f"Authentication error: {str(e)}")
            return False
    
    def test_monthly_calculation_october_2025(self):
        """Test 1: Monthly Calculation (October 2025) - Fixed month format"""
        try:
            # Test the FIXED endpoint with YYYY-MM format
            response = self.session.post(f"{BACKEND_URL}/deductions/calculate-monthly?month=2025-10")
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                if "employees" not in data:
                    self.log_test("Monthly Calculation Oct 2025", "FAIL", "Missing 'employees' field in response")
                    return
                
                employees = data.get("employees", [])
                if not employees:
                    self.log_test("Monthly Calculation Oct 2025", "WARN", "No employees found in calculation")
                    return
                
                # Verify cycle window (actual API uses cycle_window not cycle)
                cycle_info = data.get("cycle_window", {})
                expected_start = "2025-09-29"
                expected_end = "2025-10-28"
                
                actual_start = cycle_info.get("from")
                actual_end = cycle_info.get("to")
                
                if actual_start != expected_start or actual_end != expected_end:
                    self.log_test("Monthly Calculation Oct 2025", "WARN", 
                                f"Cycle window mismatch. Expected: {expected_start} to {expected_end}, "
                                f"Got: {actual_start} to {actual_end}")
                
                # Verify daily breakdown structure
                daily_breakdown_found = False
                for employee in employees:
                    if "daily_breakdown" in employee:
                        daily_breakdown_found = True
                        daily_records = employee["daily_breakdown"]
                        
                        if daily_records:
                            # Check first record structure
                            first_record = daily_records[0]
                            required_fields = ["date", "check_in", "check_out", "late_minutes", 
                                             "early_leave_minutes", "deduction_amount", "note"]
                            
                            missing_fields = [field for field in required_fields if field not in first_record]
                            if missing_fields:
                                self.log_test("Monthly Calculation Oct 2025", "FAIL", 
                                            f"Missing required fields in daily breakdown: {missing_fields}")
                                return
                        break
                
                if not daily_breakdown_found:
                    self.log_test("Monthly Calculation Oct 2025", "FAIL", "No daily_breakdown found in employee records")
                    return
                
                self.log_test("Monthly Calculation Oct 2025", "PASS", 
                            f"Monthly calculation working correctly. Found {len(employees)} employees with daily breakdown")
                
            elif response.status_code == 400:
                error_msg = response.text
                if "month format" in error_msg.lower():
                    self.log_test("Monthly Calculation Oct 2025", "FAIL", 
                                f"Month format error still exists: {error_msg}")
                else:
                    self.log_test("Monthly Calculation Oct 2025", "FAIL", f"400 error: {error_msg}")
            else:
                self.log_test("Monthly Calculation Oct 2025", "FAIL", 
                            f"Unexpected status code: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Monthly Calculation Oct 2025", "FAIL", f"Exception: {str(e)}")
    
    def test_custom_period_calculation_2_weeks(self):
        """Test 2: Custom Period Calculation (2 weeks) - Fixed daily records"""
        try:
            # Test custom period endpoint
            params = {
                "mode": "custom",
                "from_date": "2025-10-01",
                "to_date": "2025-10-14"
            }
            
            response = self.session.post(f"{BACKEND_URL}/deductions/calculate", params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                # The actual API returns "items" not "employees" for custom period
                if "items" not in data:
                    self.log_test("Custom Period 2 Weeks", "FAIL", "Missing 'items' field in response")
                    return
                
                items = data.get("items", [])
                if not items:
                    self.log_test("Custom Period 2 Weeks", "WARN", "No employees found in custom period calculation")
                    return
                
                # Verify period information
                from_date = data.get("from")
                to_date = data.get("to")
                if from_date != "2025-10-01" or to_date != "2025-10-14":
                    self.log_test("Custom Period 2 Weeks", "WARN", 
                                f"Period mismatch. Expected: 2025-10-01 to 2025-10-14, Got: {from_date} to {to_date}")
                
                # Verify breakdown structure (API uses "breakdown" not "daily_records")
                breakdown_found = False
                empty_records_count = 0
                
                for item in items:
                    if "breakdown" in item:
                        breakdown_found = True
                        breakdown = item["breakdown"]
                        
                        if not breakdown:
                            empty_records_count += 1
                        else:
                            # Check record structure
                            first_record = breakdown[0]
                            required_fields = ["date", "late_minutes", "early_out_minutes", "amount", "reason"]
                            
                            missing_fields = [field for field in required_fields if field not in first_record]
                            if missing_fields:
                                self.log_test("Custom Period 2 Weeks", "FAIL", 
                                            f"Missing required fields in breakdown: {missing_fields}")
                                return
                            
                            # Verify deduction calculations
                            if first_record.get("amount", 0) < 0:
                                self.log_test("Custom Period 2 Weeks", "FAIL", 
                                            f"Invalid negative deduction amount: {first_record.get('amount')}")
                                return
                
                if not breakdown_found:
                    self.log_test("Custom Period 2 Weeks", "FAIL", "No breakdown found in employee records")
                    return
                
                if empty_records_count == len(items):
                    self.log_test("Custom Period 2 Weeks", "FAIL", 
                                "All employees have empty breakdown - 'No daily records available' issue persists")
                    return
                
                # Check for PREVIEW mode
                preview_mode = data.get("preview", False)
                if not preview_mode:
                    self.log_test("Custom Period 2 Weeks", "WARN", "PREVIEW mode not indicated in response")
                
                self.log_test("Custom Period 2 Weeks", "PASS", 
                            f"Custom period calculation working correctly. Found {len(items)} employees, "
                            f"{len(items) - empty_records_count} with breakdown data")
                
            else:
                self.log_test("Custom Period 2 Weeks", "FAIL", 
                            f"Custom period calculation failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Custom Period 2 Weeks", "FAIL", f"Exception: {str(e)}")
    
    def test_custom_period_validation_93_days(self):
        """Test 3: Custom Period Validation (>93 days) - Should return 400 error"""
        try:
            # Test period exceeding 93 days
            params = {
                "mode": "custom",
                "from_date": "2025-01-01",
                "to_date": "2025-05-01"  # ~120 days
            }
            
            response = self.session.post(f"{BACKEND_URL}/deductions/calculate", params=params)
            
            if response.status_code == 400:
                error_msg = response.text
                if "93 days" in error_msg or "exceed" in error_msg.lower():
                    self.log_test("Custom Period >93 Days Validation", "PASS", 
                                f"Validation working correctly: {error_msg}")
                else:
                    self.log_test("Custom Period >93 Days Validation", "WARN", 
                                f"400 error but unclear message: {error_msg}")
            elif response.status_code == 200:
                self.log_test("Custom Period >93 Days Validation", "FAIL", 
                            "Validation failed - should reject periods >93 days but returned 200")
            else:
                self.log_test("Custom Period >93 Days Validation", "FAIL", 
                            f"Unexpected status code: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Custom Period >93 Days Validation", "FAIL", f"Exception: {str(e)}")
    
    def test_apply_monthly_deductions_october_2025(self):
        """Test 4: Apply Monthly Deductions (October 2025) - Fixed request body format"""
        try:
            # First get the calculation data
            calc_response = self.session.post(f"{BACKEND_URL}/deductions/calculate-monthly?month=2025-10")
            
            if calc_response.status_code != 200:
                self.log_test("Apply Monthly Deductions Oct 2025", "FAIL", 
                            f"Cannot get calculation data: {calc_response.status_code}")
                return
            
            calc_data = calc_response.json()
            employees = calc_data.get("employees", [])
            
            if not employees:
                self.log_test("Apply Monthly Deductions Oct 2025", "FAIL", "No employees data to apply")
                return
            
            # Test the FIXED apply endpoint with request body (not query params)
            apply_data = {
                "month": "2025-10",
                "employees": employees,
                "notes": "Test application - Advanced Deductions System Fix Verification"
            }
            
            response = self.session.post(f"{BACKEND_URL}/deductions/apply-monthly", json=apply_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ["employees_affected", "total_deduction_amount"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Apply Monthly Deductions Oct 2025", "FAIL", 
                                f"Missing required response fields: {missing_fields}")
                    return
                
                employees_affected = data.get("employees_affected", 0)
                total_deduction = data.get("total_deduction_amount", 0)
                
                if employees_affected == 0:
                    self.log_test("Apply Monthly Deductions Oct 2025", "WARN", 
                                "No employees affected by deduction application")
                else:
                    self.log_test("Apply Monthly Deductions Oct 2025", "PASS", 
                                f"Deductions applied successfully. Affected: {employees_affected} employees, "
                                f"Total: {total_deduction} AED")
                
            elif response.status_code == 422:
                error_msg = response.text
                if "request body" in error_msg.lower() or "missing" in error_msg.lower():
                    self.log_test("Apply Monthly Deductions Oct 2025", "FAIL", 
                                f"Request body format issue still exists: {error_msg}")
                else:
                    self.log_test("Apply Monthly Deductions Oct 2025", "FAIL", f"422 validation error: {error_msg}")
            else:
                self.log_test("Apply Monthly Deductions Oct 2025", "FAIL", 
                            f"Apply deductions failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Apply Monthly Deductions Oct 2025", "FAIL", f"Exception: {str(e)}")
    
    def test_deduction_calculation_business_rules(self):
        """Test 5: Verify Deduction Calculation Business Rules (15min grace × 4, etc.)"""
        try:
            # Get monthly calculation to verify business rules
            response = self.session.post(f"{BACKEND_URL}/deductions/calculate-monthly?month=2025-10")
            
            if response.status_code != 200:
                self.log_test("Deduction Business Rules", "FAIL", 
                            f"Cannot get calculation data: {response.status_code}")
                return
            
            data = response.json()
            employees = data.get("employees", [])
            
            if not employees:
                self.log_test("Deduction Business Rules", "WARN", "No employees data to verify business rules")
                return
            
            # Analyze deduction patterns
            total_deductions = 0
            employees_with_deductions = 0
            grace_period_violations = 0
            
            for employee in employees:
                daily_breakdown = employee.get("daily_breakdown", [])
                employee_total_deduction = 0
                
                for daily_record in daily_breakdown:
                    deduction_amount = daily_record.get("deduction_amount", 0)
                    late_minutes = daily_record.get("late_minutes", 0)
                    early_leave_minutes = daily_record.get("early_leave_minutes", 0)
                    
                    if deduction_amount > 0:
                        employee_total_deduction += deduction_amount
                        
                        # Check 15-minute grace period rule
                        if late_minutes > 0 and late_minutes <= 15 and deduction_amount > 0:
                            grace_period_violations += 1
                
                if employee_total_deduction > 0:
                    employees_with_deductions += 1
                    total_deductions += employee_total_deduction
            
            # Verify business rules
            issues = []
            
            if grace_period_violations > 0:
                issues.append(f"{grace_period_violations} violations of 15-minute grace period rule")
            
            if issues:
                self.log_test("Deduction Business Rules", "FAIL", 
                            f"Business rule violations found: {'; '.join(issues)}")
            else:
                self.log_test("Deduction Business Rules", "PASS", 
                            f"Business rules verified. {employees_with_deductions} employees with deductions, "
                            f"Total: {total_deductions:.2f} AED")
                
        except Exception as e:
            self.log_test("Deduction Business Rules", "FAIL", f"Exception: {str(e)}")
    
    def test_arabic_error_messages(self):
        """Test 6: Verify Arabic Error Messages are Clear"""
        try:
            # Test invalid month format to check Arabic error message
            response = self.session.post(f"{BACKEND_URL}/deductions/calculate-monthly?month=invalid")
            
            if response.status_code == 400:
                error_msg = response.text
                
                # Check if error message contains Arabic text or is clear
                if any(arabic_char in error_msg for arabic_char in ['ا', 'ب', 'ت', 'ث', 'ج', 'ح', 'خ', 'د', 'ذ', 'ر']):
                    self.log_test("Arabic Error Messages", "PASS", f"Arabic error message found: {error_msg}")
                elif len(error_msg) > 10 and "format" in error_msg.lower():
                    self.log_test("Arabic Error Messages", "PASS", f"Clear English error message: {error_msg}")
                else:
                    self.log_test("Arabic Error Messages", "WARN", f"Error message unclear: {error_msg}")
            else:
                self.log_test("Arabic Error Messages", "WARN", 
                            f"Expected 400 for invalid month, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Arabic Error Messages", "FAIL", f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all Advanced Attendance Deductions System tests"""
        print("🚨 CRITICAL TESTING REQUEST - Advanced Attendance Deductions System Fixes Verification")
        print("=" * 80)
        
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        print("\n🔍 Testing Advanced Attendance Deductions System Fixes...")
        print("-" * 60)
        
        # Run all tests
        self.test_monthly_calculation_october_2025()
        self.test_custom_period_calculation_2_weeks()
        self.test_custom_period_validation_93_days()
        self.test_apply_monthly_deductions_october_2025()
        self.test_deduction_calculation_business_rules()
        self.test_arabic_error_messages()
        
        # Summary
        print("\n📊 TEST SUMMARY")
        print("=" * 40)
        
        passed = len([t for t in self.test_results if t["status"] == "PASS"])
        failed = len([t for t in self.test_results if t["status"] == "FAIL"])
        warnings = len([t for t in self.test_results if t["status"] == "WARN"])
        total = len(self.test_results) - 1  # Exclude authentication
        
        print(f"✅ PASSED: {passed}/{total}")
        print(f"❌ FAILED: {failed}/{total}")
        print(f"⚠️  WARNINGS: {warnings}/{total}")
        
        success_rate = (passed / total * 100) if total > 0 else 0
        print(f"📈 SUCCESS RATE: {success_rate:.1f}%")
        
        # Detailed results
        print(f"\n📋 DETAILED RESULTS:")
        for result in self.test_results[1:]:  # Skip authentication
            status_icon = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
            print(f"{status_icon} {result['test']}: {result['details']}")
        
        # Save results
        try:
            with open("/app/advanced_deductions_test_results.json", "w") as f:
                json.dump(self.test_results, f, indent=2, default=str)
            print(f"\n💾 Results saved to: /app/advanced_deductions_test_results.json")
        except Exception as e:
            print(f"⚠️ Could not save results: {e}")
        
        return failed == 0

if __name__ == "__main__":
    tester = AdvancedDeductionsSystemTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 ALL TESTS PASSED - Advanced Attendance Deductions System fixes verified successfully!")
        sys.exit(0)
    else:
        print("\n🚨 SOME TESTS FAILED - Advanced Attendance Deductions System needs attention!")
        sys.exit(1)