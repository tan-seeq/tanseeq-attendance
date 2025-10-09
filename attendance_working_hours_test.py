#!/usr/bin/env python3
"""
اختبار مشكلة حساب ساعات العمل عند تعديل وقت الانصراف
Testing Working Hours Calculation Issue When Modifying Checkout Time

This test specifically addresses the user's reported issue:
- Super Admin edited checkout time but working hours were not automatically calculated
- Testing the PATCH/PUT /api/attendance/{attendance_id} endpoint
- Verifying automatic working hours recalculation
- Testing different scenarios and time formats
"""

import requests
import json
import os
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://tanseeq-payroll-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials from review request
SUPER_ADMIN_CREDENTIALS = {
    "email": "hatem@tan-seeq.co",
    "password": "hatem123"
}

class AttendanceWorkingHoursTestSuite:
    """Test suite for Working Hours Calculation Issue"""
    
    def __init__(self):
        self.super_admin_token = None
        self.super_admin_user = None
        self.test_results = []
        self.session = requests.Session()
        
    def log_test(self, test_name: str, success: bool, details: str = "", error: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "error": error
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   📋 {details}")
        if error:
            print(f"   ⚠️  {error}")
        print()

    def authenticate_super_admin(self):
        """Authenticate as Super Admin"""
        print("🔐 AUTHENTICATING AS SUPER ADMIN")
        print("=" * 60)
        
        try:
            response = self.session.post(
                f"{API_BASE}/auth/login",
                json=SUPER_ADMIN_CREDENTIALS,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.super_admin_token = data["access_token"]
                    self.super_admin_user = data.get("user", {})
                    self.session.headers.update({
                        'Authorization': f'Bearer {self.super_admin_token}'
                    })
                    
                    self.log_test(
                        "Super Admin Authentication", 
                        True,
                        f"Successfully authenticated as {self.super_admin_user.get('name', 'Unknown')} ({self.super_admin_user.get('role', 'Unknown')})"
                    )
                    return True
                else:
                    self.log_test("Super Admin Authentication", False, error="No access token in response")
                    return False
            else:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f" - {error_data.get('detail', 'Unknown error')}"
                except:
                    error_msg += f" - {response.text[:100]}"
                
                self.log_test("Super Admin Authentication", False, error=error_msg)
                return False
                        
        except Exception as e:
            self.log_test("Super Admin Authentication", False, error=f"Connection error: {str(e)}")
            return False

    def get_attendance_records(self):
        """Get attendance records to find test data"""
        print("📋 GETTING ATTENDANCE RECORDS FOR TESTING")
        print("=" * 60)
        
        try:
            # Try to get attendance records with absences (enhanced view)
            response = self.session.get(f"{API_BASE}/attendance/with-absences", timeout=30)
            
            if response.status_code == 200:
                records = response.json()  # API returns direct array
                
                self.log_test(
                    "Get Attendance Records",
                    True,
                    f"Retrieved {len(records)} attendance records"
                )
                
                # Find suitable test records
                test_records = []
                for record in records:
                    # Look for records with check_in but potentially missing check_out or working_hours
                    if record.get('check_in') and record.get('status') != 'absent':
                        test_records.append(record)
                
                return test_records[:5]  # Return first 5 suitable records
                
            else:
                self.log_test("Get Attendance Records", False, error=f"HTTP {response.status_code}")
                return []
                
        except Exception as e:
            self.log_test("Get Attendance Records", False, error=str(e))
            return []

    def test_checkout_time_update_scenario_1(self, attendance_record):
        """Test Scenario 1: Employee with check-in but no check-out time"""
        print("🧪 TESTING SCENARIO 1: Employee with check-in but no check-out")
        print("=" * 60)
        
        attendance_id = attendance_record.get('id')
        employee_name = attendance_record.get('user_name', 'Unknown')
        original_check_in = attendance_record.get('check_in')
        original_check_out = attendance_record.get('check_out')
        original_working_hours = attendance_record.get('working_hours')
        
        print(f"Testing with employee: {employee_name}")
        print(f"Original check_in: {original_check_in}")
        print(f"Original check_out: {original_check_out}")
        print(f"Original working_hours: {original_working_hours}")
        
        # Test updating checkout time to 18:00
        test_checkout_time = "18:00"
        
        try:
            update_data = {
                "check_out": test_checkout_time
            }
            
            response = self.session.put(
                f"{API_BASE}/attendance/{attendance_id}",
                json=update_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Verify the record was updated
                updated_response = self.session.get(f"{API_BASE}/attendance/with-absences", timeout=30)
                if updated_response.status_code == 200:
                    updated_records = updated_response.json()  # API returns direct array
                    updated_record = next((r for r in updated_records if r.get('id') == attendance_id), None)
                    
                    if updated_record:
                        new_check_out = updated_record.get('check_out')
                        new_working_hours = updated_record.get('working_hours')
                        
                        # Calculate expected working hours (09:00 to 18:00 = 9 hours - 1 hour break = 8 hours)
                        if original_check_in:
                            expected_hours = self.calculate_expected_hours(original_check_in, test_checkout_time)
                            
                            success = (
                                new_check_out == test_checkout_time and 
                                new_working_hours is not None and 
                                new_working_hours > 0
                            )
                            
                            details = f"Updated check_out to {new_check_out}, working_hours calculated as {new_working_hours} (expected ~{expected_hours})"
                            
                            if success and abs(new_working_hours - expected_hours) <= 0.5:  # Allow 30 min tolerance
                                self.log_test(
                                    f"Scenario 1 - Update Checkout Time ({employee_name})",
                                    True,
                                    details
                                )
                            else:
                                self.log_test(
                                    f"Scenario 1 - Update Checkout Time ({employee_name})",
                                    False,
                                    error=f"Working hours calculation issue: got {new_working_hours}, expected ~{expected_hours}"
                                )
                        else:
                            self.log_test(
                                f"Scenario 1 - Update Checkout Time ({employee_name})",
                                False,
                                error="No original check_in time to calculate expected hours"
                            )
                    else:
                        self.log_test(
                            f"Scenario 1 - Update Checkout Time ({employee_name})",
                            False,
                            error="Could not retrieve updated record"
                        )
                else:
                    self.log_test(
                        f"Scenario 1 - Update Checkout Time ({employee_name})",
                        False,
                        error="Could not retrieve updated attendance records"
                    )
            else:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f" - {error_data.get('detail', 'Unknown error')}"
                except:
                    error_msg += f" - {response.text[:200]}"
                
                self.log_test(
                    f"Scenario 1 - Update Checkout Time ({employee_name})",
                    False,
                    error=error_msg
                )
                
        except Exception as e:
            self.log_test(
                f"Scenario 1 - Update Checkout Time ({employee_name})",
                False,
                error=str(e)
            )

    def test_checkout_time_update_scenario_2(self, attendance_record):
        """Test Scenario 2: Employee with both check-in and check-out, modify check-out"""
        print("🧪 TESTING SCENARIO 2: Employee with both times, modify check-out")
        print("=" * 60)
        
        attendance_id = attendance_record.get('id')
        employee_name = attendance_record.get('user_name', 'Unknown')
        original_check_in = attendance_record.get('check_in')
        original_check_out = attendance_record.get('check_out')
        original_working_hours = attendance_record.get('working_hours')
        
        # Skip if no original check_out
        if not original_check_out:
            print(f"Skipping {employee_name} - no original check_out time")
            return
        
        print(f"Testing with employee: {employee_name}")
        print(f"Original check_in: {original_check_in}")
        print(f"Original check_out: {original_check_out}")
        print(f"Original working_hours: {original_working_hours}")
        
        # Test updating checkout time to a different time
        test_checkout_time = "17:30"  # Different from original
        
        try:
            update_data = {
                "check_out": test_checkout_time
            }
            
            response = self.session.put(
                f"{API_BASE}/attendance/{attendance_id}",
                json=update_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Verify the record was updated
                updated_response = self.session.get(f"{API_BASE}/attendance/with-absences", timeout=30)
                if updated_response.status_code == 200:
                    updated_records = updated_response.json()  # API returns direct array
                    updated_record = next((r for r in updated_records if r.get('id') == attendance_id), None)
                    
                    if updated_record:
                        new_check_out = updated_record.get('check_out')
                        new_working_hours = updated_record.get('working_hours')
                        
                        # Calculate expected working hours
                        if original_check_in:
                            expected_hours = self.calculate_expected_hours(original_check_in, test_checkout_time)
                            
                            success = (
                                new_check_out == test_checkout_time and 
                                new_working_hours is not None and 
                                new_working_hours != original_working_hours  # Should be different
                            )
                            
                            details = f"Updated check_out from {original_check_out} to {new_check_out}, working_hours recalculated from {original_working_hours} to {new_working_hours} (expected ~{expected_hours})"
                            
                            if success:
                                self.log_test(
                                    f"Scenario 2 - Modify Checkout Time ({employee_name})",
                                    True,
                                    details
                                )
                            else:
                                self.log_test(
                                    f"Scenario 2 - Modify Checkout Time ({employee_name})",
                                    False,
                                    error=f"Working hours not recalculated properly: got {new_working_hours}, expected ~{expected_hours}"
                                )
                        else:
                            self.log_test(
                                f"Scenario 2 - Modify Checkout Time ({employee_name})",
                                False,
                                error="No original check_in time to calculate expected hours"
                            )
                    else:
                        self.log_test(
                            f"Scenario 2 - Modify Checkout Time ({employee_name})",
                            False,
                            error="Could not retrieve updated record"
                        )
                else:
                    self.log_test(
                        f"Scenario 2 - Modify Checkout Time ({employee_name})",
                        False,
                        error="Could not retrieve updated attendance records"
                    )
            else:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f" - {error_data.get('detail', 'Unknown error')}"
                except:
                    error_msg += f" - {response.text[:200]}"
                
                self.log_test(
                    f"Scenario 2 - Modify Checkout Time ({employee_name})",
                    False,
                    error=error_msg
                )
                
        except Exception as e:
            self.log_test(
                f"Scenario 2 - Modify Checkout Time ({employee_name})",
                False,
                error=str(e)
            )

    def test_time_format_handling(self, attendance_record):
        """Test different time formats (HH:MM vs HH:MM:SS)"""
        print("🧪 TESTING TIME FORMAT HANDLING")
        print("=" * 60)
        
        attendance_id = attendance_record.get('id')
        employee_name = attendance_record.get('user_name', 'Unknown')
        
        # Test both HH:MM and HH:MM:SS formats
        time_formats = [
            ("18:00", "HH:MM format"),
            ("18:00:00", "HH:MM:SS format")
        ]
        
        for test_time, format_desc in time_formats:
            try:
                update_data = {
                    "check_out": test_time
                }
                
                response = self.session.put(
                    f"{API_BASE}/attendance/{attendance_id}",
                    json=update_data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    # Verify the record was updated
                    updated_response = self.session.get(f"{API_BASE}/attendance/with-absences", timeout=30)
                    if updated_response.status_code == 200:
                        updated_records = updated_response.json()  # API returns direct array
                        updated_record = next((r for r in updated_records if r.get('id') == attendance_id), None)
                        
                        if updated_record and updated_record.get('working_hours') is not None:
                            self.log_test(
                                f"Time Format Test - {format_desc} ({employee_name})",
                                True,
                                f"Successfully handled {format_desc}, working_hours: {updated_record.get('working_hours')}"
                            )
                        else:
                            self.log_test(
                                f"Time Format Test - {format_desc} ({employee_name})",
                                False,
                                error="Working hours not calculated"
                            )
                    else:
                        self.log_test(
                            f"Time Format Test - {format_desc} ({employee_name})",
                            False,
                            error="Could not retrieve updated record"
                        )
                else:
                    self.log_test(
                        f"Time Format Test - {format_desc} ({employee_name})",
                        False,
                        error=f"HTTP {response.status_code}"
                    )
                    
            except Exception as e:
                self.log_test(
                    f"Time Format Test - {format_desc} ({employee_name})",
                    False,
                    error=str(e)
                )

    def test_calculation_logic_verification(self):
        """Test the calculation logic with known values"""
        print("🧪 TESTING CALCULATION LOGIC VERIFICATION")
        print("=" * 60)
        
        # Test the example from the review request:
        # Employee checked in at 09:00, checkout at 18:00
        # Should calculate working_hours = 8.0 hours (9 hours - 1 hour break)
        
        test_cases = [
            {
                "check_in": "09:00",
                "check_out": "18:00", 
                "expected_hours": 8.0,
                "description": "Standard 9-6 schedule (review example)"
            },
            {
                "check_in": "09:00",
                "check_out": "17:00",
                "expected_hours": 7.0,
                "description": "8 hours total - 1 hour break = 7 hours"
            },
            {
                "check_in": "08:30",
                "check_out": "17:30",
                "expected_hours": 8.0,
                "description": "9 hours total - 1 hour break = 8 hours"
            }
        ]
        
        for test_case in test_cases:
            expected = test_case["expected_hours"]
            calculated = self.calculate_expected_hours(test_case["check_in"], test_case["check_out"])
            
            success = abs(calculated - expected) <= 0.1  # Allow small tolerance
            
            self.log_test(
                f"Calculation Logic - {test_case['description']}",
                success,
                f"Check-in: {test_case['check_in']}, Check-out: {test_case['check_out']}, Expected: {expected}h, Calculated: {calculated}h" if success else "",
                f"Calculation mismatch: expected {expected}h, got {calculated}h" if not success else ""
            )

    def calculate_expected_hours(self, check_in_str, check_out_str):
        """Calculate expected working hours based on the logic in the backend"""
        try:
            # Parse times (assume same date)
            today = datetime.now().date()
            
            # Handle both HH:MM and HH:MM:SS formats
            if len(check_in_str) == 5:  # HH:MM
                check_in_time = datetime.strptime(f"{today} {check_in_str}:00", "%Y-%m-%d %H:%M:%S")
            else:  # HH:MM:SS
                check_in_time = datetime.strptime(f"{today} {check_in_str}", "%Y-%m-%d %H:%M:%S")
                
            if len(check_out_str) == 5:  # HH:MM
                check_out_time = datetime.strptime(f"{today} {check_out_str}:00", "%Y-%m-%d %H:%M:%S")
            else:  # HH:MM:SS
                check_out_time = datetime.strptime(f"{today} {check_out_str}", "%Y-%m-%d %H:%M:%S")
            
            # Calculate total worked time
            total_worked_time = (check_out_time - check_in_time).total_seconds() / 3600.0
            
            # Subtract break time (1 hour = 60 minutes)
            break_time_hours = 60 / 60.0  # 1 hour
            net_worked_hours = max(0, total_worked_time - break_time_hours)
            
            return round(net_worked_hours, 2)
            
        except Exception as e:
            print(f"Error calculating expected hours: {e}")
            return 0.0

    def test_api_response_structure(self, attendance_record):
        """Test that API response shows updated hours and data is saved"""
        print("🧪 TESTING API RESPONSE STRUCTURE")
        print("=" * 60)
        
        attendance_id = attendance_record.get('id')
        employee_name = attendance_record.get('user_name', 'Unknown')
        
        try:
            update_data = {
                "check_out": "18:00"
            }
            
            response = self.session.put(
                f"{API_BASE}/attendance/{attendance_id}",
                json=update_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Check response structure
                has_message = "message" in result
                has_changes = "changes" in result
                
                # Verify data persistence by fetching the record again
                fetch_response = self.session.get(f"{API_BASE}/attendance/with-absences", timeout=30)
                if fetch_response.status_code == 200:
                    records = fetch_response.json()  # API returns direct array
                    updated_record = next((r for r in records if r.get('id') == attendance_id), None)
                    
                    if updated_record:
                        data_persisted = (
                            updated_record.get('check_out') == "18:00" and
                            updated_record.get('working_hours') is not None
                        )
                        
                        success = has_message and has_changes and data_persisted
                        
                        details = f"Response structure: message={has_message}, changes={has_changes}, data_persisted={data_persisted}"
                        if has_changes:
                            details += f", changes={result.get('changes', [])}"
                        
                        self.log_test(
                            f"API Response Structure ({employee_name})",
                            success,
                            details if success else "",
                            "Response structure or data persistence issue" if not success else ""
                        )
                    else:
                        self.log_test(
                            f"API Response Structure ({employee_name})",
                            False,
                            error="Could not find updated record in database"
                        )
                else:
                    self.log_test(
                        f"API Response Structure ({employee_name})",
                        False,
                        error="Could not fetch records to verify persistence"
                    )
            else:
                self.log_test(
                    f"API Response Structure ({employee_name})",
                    False,
                    error=f"HTTP {response.status_code}"
                )
                
        except Exception as e:
            self.log_test(
                f"API Response Structure ({employee_name})",
                False,
                error=str(e)
            )

    def run_comprehensive_test(self):
        """Run all tests for working hours calculation issue"""
        print("🚀 STARTING WORKING HOURS CALCULATION TESTING")
        print("اختبار مشكلة حساب ساعات العمل عند تعديل وقت الانصراف")
        print("=" * 80)
        print()
        
        # Step 1: Authenticate as Super Admin
        if not self.authenticate_super_admin():
            print("🚨 CRITICAL: Super Admin authentication failed - cannot proceed")
            return self.generate_summary()
        
        # Step 2: Get attendance records for testing
        test_records = self.get_attendance_records()
        if not test_records:
            print("🚨 CRITICAL: No attendance records found for testing")
            return self.generate_summary()
        
        print(f"Found {len(test_records)} attendance records for testing")
        print()
        
        # Step 3: Test calculation logic verification
        self.test_calculation_logic_verification()
        
        # Step 4: Test different scenarios with actual records
        for i, record in enumerate(test_records[:3]):  # Test with first 3 records
            print(f"\n--- Testing with Record {i+1}: {record.get('user_name', 'Unknown')} ---")
            
            # Scenario 1: Update checkout time
            self.test_checkout_time_update_scenario_1(record)
            
            # Scenario 2: Modify existing checkout time (if applicable)
            self.test_checkout_time_update_scenario_2(record)
            
            # Test time format handling
            self.test_time_format_handling(record)
            
            # Test API response structure
            self.test_api_response_structure(record)
        
        return self.generate_summary()

    def generate_summary(self):
        """Generate comprehensive test summary"""
        print("\n" + "=" * 80)
        print("📊 WORKING HOURS CALCULATION TEST RESULTS")
        print("تقرير اختبار حساب ساعات العمل")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📈 Overall Results: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}% success rate)")
        print()
        
        # Categorize results
        auth_tests = [r for r in self.test_results if 'Authentication' in r['test']]
        calculation_tests = [r for r in self.test_results if 'Calculation Logic' in r['test']]
        scenario_tests = [r for r in self.test_results if 'Scenario' in r['test']]
        format_tests = [r for r in self.test_results if 'Time Format' in r['test']]
        api_tests = [r for r in self.test_results if 'API Response' in r['test']]
        
        # Critical issues analysis
        critical_issues = []
        
        if not any(r['success'] for r in auth_tests):
            critical_issues.append("❌ Authentication failed - cannot access system")
        
        if not any(r['success'] for r in calculation_tests):
            critical_issues.append("❌ Calculation logic verification failed")
        
        if not any(r['success'] for r in scenario_tests):
            critical_issues.append("❌ Working hours not being calculated when checkout time is updated")
        
        if not any(r['success'] for r in format_tests):
            critical_issues.append("❌ Time format handling issues")
        
        if not any(r['success'] for r in api_tests):
            critical_issues.append("❌ API response or data persistence issues")
        
        if critical_issues:
            print("🚨 CRITICAL ISSUES IDENTIFIED:")
            for issue in critical_issues:
                print(f"   {issue}")
            print()
        
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   • {result['test']}: {result['error']}")
            print()
        
        print("✅ PASSED TESTS:")
        for result in self.test_results:
            if result['success']:
                print(f"   • {result['test']}: {result['details']}")
        
        print("\n" + "=" * 80)
        print("🔍 ROOT CAUSE ANALYSIS:")
        
        if critical_issues:
            print("The reported issue appears to be confirmed. Possible causes:")
            print("1. The PUT /api/attendance/{attendance_id} endpoint may not be properly calling calculate_working_hours_and_deductions")
            print("2. Time format parsing issues between frontend (HH:MM) and backend (HH:MM:SS)")
            print("3. Database update not persisting the calculated working_hours field")
            print("4. The calculation function may have bugs in the time parsing logic")
        else:
            print("✅ Working hours calculation appears to be functioning correctly")
            print("The issue may be intermittent or related to specific conditions not tested")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': success_rate,
            'critical_issues': critical_issues,
            'results': self.test_results
        }

if __name__ == "__main__":
    tester = AttendanceWorkingHoursTestSuite()
    summary = tester.run_comprehensive_test()
    
    # Exit with appropriate code
    if summary['success_rate'] >= 70 and not summary['critical_issues']:
        exit(0)  # Success
    else:
        exit(1)  # Issues found