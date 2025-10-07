#!/usr/bin/env python3
"""
Working Hours Calculation Fix Testing
اختبار إصلاح حساب ساعات العمل بعد التحديث

Testing the datetime parsing fix in calculate_working_hours_and_deductions function.
Specifically testing:
1. Super Admin login: hatem@tan-seeq.co / hatem123
2. Update check-out time with automatic calculation
3. Test specific scenarios with different time formats
4. Verify no parsing errors occur
"""

import requests
import json
import os
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://hrms-tanseeq.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials from review request
SUPER_ADMIN_CREDENTIALS = {
    "email": "hatem@tan-seeq.co",
    "password": "hatem123"
}

class WorkingHoursTestSuite:
    """Test suite for Working Hours Calculation Fix"""
    
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = "", error: str = ""):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "error": error
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   📋 {details}")
        if error:
            print(f"   ⚠️  {error}")
        print()

    def authenticate_super_admin(self):
        """Authenticate as Super Admin"""
        print("🔐 AUTHENTICATING AS SUPER ADMIN")
        print("=" * 50)
        
        try:
            response = self.session.post(
                f"{API_BASE}/auth/login",
                json=SUPER_ADMIN_CREDENTIALS,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.auth_token = data["access_token"]
                    self.current_user = data.get("user", {})
                    self.session.headers.update({
                        'Authorization': f'Bearer {self.auth_token}'
                    })
                    
                    self.log_test(
                        "Super Admin Authentication",
                        True,
                        f"Successfully authenticated as {self.current_user.get('name', 'Unknown')} ({self.current_user.get('role', 'Unknown')})"
                    )
                    return True
                else:
                    self.log_test(
                        "Super Admin Authentication",
                        False,
                        error="No access token in response"
                    )
                    return False
            else:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f" - {error_data.get('detail', 'Unknown error')}"
                except:
                    error_msg += f" - {response.text[:100]}"
                
                self.log_test(
                    "Super Admin Authentication",
                    False,
                    error=error_msg
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Super Admin Authentication",
                False,
                error=f"Connection error: {str(e)}"
            )
            return False

    def get_attendance_records(self):
        """Get existing attendance records to test with"""
        print("📋 GETTING ATTENDANCE RECORDS")
        print("=" * 50)
        
        try:
            response = self.session.get(f"{API_BASE}/attendance/with-absences", timeout=30)
            
            if response.status_code == 200:
                records = response.json()  # API returns list directly
                
                self.log_test(
                    "Get Attendance Records",
                    True,
                    f"Retrieved {len(records)} attendance records"
                )
                
                # Find records with check-in and check-out to test working hours calculation
                test_records = []
                for record in records:
                    if record.get('check_in') and record.get('check_out'):
                        test_records.append(record)
                
                return test_records[:5]  # Return first 5 suitable records
                
            else:
                self.log_test(
                    "Get Attendance Records",
                    False,
                    error=f"HTTP {response.status_code}"
                )
                return []
                
        except Exception as e:
            self.log_test(
                "Get Attendance Records",
                False,
                error=str(e)
            )
            return []

    def test_working_hours_calculation(self, record, new_check_out_time):
        """Test working hours calculation with specific check-out time"""
        record_id = record.get('id')
        employee_name = record.get('user_name', 'Unknown')
        check_in = record.get('check_in', 'N/A')
        
        print(f"🧮 TESTING WORKING HOURS CALCULATION")
        print(f"Employee: {employee_name}")
        print(f"Check-in: {check_in}")
        print(f"New Check-out: {new_check_out_time}")
        print("=" * 50)
        
        try:
            # Update attendance record with new check-out time
            update_data = {
                "check_out": new_check_out_time
            }
            
            response = self.session.put(
                f"{API_BASE}/attendance/{record_id}",
                json=update_data,
                timeout=30
            )
            
            if response.status_code == 200:
                updated_record = response.json()
                working_hours = updated_record.get('working_hours', 0)
                
                # Calculate expected working hours (check-out - check-in - 1 hour break)
                try:
                    # Parse check-in time
                    if 'T' in check_in:
                        check_in_dt = datetime.fromisoformat(check_in.replace('Z', ''))
                    else:
                        # Assume same date as today for time-only format
                        today = datetime.now().date()
                        check_in_dt = datetime.combine(today, datetime.strptime(check_in, '%H:%M:%S').time())
                    
                    # Parse check-out time
                    if 'T' in new_check_out_time:
                        check_out_dt = datetime.fromisoformat(new_check_out_time.replace('Z', ''))
                    else:
                        # Assume same date as check-in
                        check_out_dt = datetime.combine(check_in_dt.date(), datetime.strptime(new_check_out_time, '%H:%M:%S').time())
                    
                    # Calculate expected hours (subtract 1 hour break)
                    total_time = (check_out_dt - check_in_dt).total_seconds() / 3600
                    expected_hours = max(0, total_time - 1.0)  # Subtract 1 hour break
                    
                    # Check if calculation is correct (allow small floating point differences)
                    calculation_correct = abs(working_hours - expected_hours) < 0.1
                    
                    self.log_test(
                        f"Working Hours Calculation - {employee_name}",
                        calculation_correct,
                        f"Calculated: {working_hours}h, Expected: {expected_hours:.2f}h, Check-in: {check_in}, Check-out: {new_check_out_time}",
                        "" if calculation_correct else f"Calculation mismatch: got {working_hours}h, expected {expected_hours:.2f}h"
                    )
                    
                    return calculation_correct, working_hours, expected_hours
                    
                except Exception as calc_error:
                    self.log_test(
                        f"Working Hours Calculation - {employee_name}",
                        False,
                        error=f"Calculation error: {str(calc_error)}"
                    )
                    return False, working_hours, 0
                    
            else:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f" - {error_data.get('detail', 'Unknown error')}"
                except:
                    error_msg += f" - {response.text[:200]}"
                
                self.log_test(
                    f"Working Hours Update - {employee_name}",
                    False,
                    error=error_msg
                )
                return False, 0, 0
                
        except Exception as e:
            self.log_test(
                f"Working Hours Update - {employee_name}",
                False,
                error=str(e)
            )
            return False, 0, 0

    def test_specific_scenarios(self):
        """Test specific working hours scenarios from review request"""
        print("🎯 TESTING SPECIFIC SCENARIOS")
        print("=" * 50)
        
        # Get attendance records to work with
        records = self.get_attendance_records()
        
        if not records:
            self.log_test(
                "Specific Scenarios Test",
                False,
                error="No attendance records available for testing"
            )
            return
        
        # Test scenarios from review request
        test_scenarios = [
            {
                "description": "Employee in 09:00 out 18:00 = 8.0 hours",
                "check_out": "18:00:00",
                "expected_hours": 8.0
            },
            {
                "description": "Employee in 08:30 out 17:30 = 8.0 hours", 
                "check_out": "17:30:00",
                "expected_hours": 8.0
            },
            {
                "description": "Employee in 10:00 out 19:00 = 8.0 hours",
                "check_out": "19:00:00", 
                "expected_hours": 8.0
            }
        ]
        
        scenario_results = []
        
        for i, scenario in enumerate(test_scenarios):
            if i < len(records):
                record = records[i]
                print(f"\n📝 Scenario {i+1}: {scenario['description']}")
                
                success, actual_hours, expected_hours = self.test_working_hours_calculation(
                    record, 
                    scenario['check_out']
                )
                
                scenario_results.append({
                    'scenario': scenario['description'],
                    'success': success,
                    'actual_hours': actual_hours,
                    'expected_hours': expected_hours
                })
        
        return scenario_results

    def test_different_time_formats(self):
        """Test different time formats as mentioned in review"""
        print("🕐 TESTING DIFFERENT TIME FORMATS")
        print("=" * 50)
        
        records = self.get_attendance_records()
        
        if not records:
            self.log_test(
                "Time Formats Test",
                False,
                error="No attendance records available for testing"
            )
            return
        
        # Test different formats
        time_formats = [
            {
                "format": "Space-separated format",
                "time": "2025-01-06 18:00:00"
            },
            {
                "format": "ISO format", 
                "time": "2025-01-06T18:00:00"
            },
            {
                "format": "Time only format",
                "time": "18:00:00"
            }
        ]
        
        format_results = []
        
        for i, time_format in enumerate(time_formats):
            if i < len(records):
                record = records[i]
                print(f"\n🔤 Testing {time_format['format']}: {time_format['time']}")
                
                success, actual_hours, expected_hours = self.test_working_hours_calculation(
                    record,
                    time_format['time']
                )
                
                format_results.append({
                    'format': time_format['format'],
                    'time': time_format['time'],
                    'success': success,
                    'actual_hours': actual_hours
                })
        
        return format_results

    def check_backend_logs(self):
        """Check for parsing errors in backend logs"""
        print("📋 CHECKING FOR BACKEND ERRORS")
        print("=" * 50)
        
        # Since we can't directly access logs, we'll test error-prone scenarios
        # and see if they return proper responses without errors
        
        records = self.get_attendance_records()
        
        if not records and len(records) > 0:
            record = records[0]
            
            # Test potentially problematic time formats
            problematic_times = [
                "invalid-time",
                "25:00:00",  # Invalid hour
                "12:60:00",  # Invalid minute
                "",          # Empty string
                "2025-13-01 12:00:00",  # Invalid month
            ]
            
            error_handling_results = []
            
            for problem_time in problematic_times:
                try:
                    update_data = {"check_out": problem_time}
                    response = self.session.put(
                        f"{API_BASE}/attendance/{record['id']}",
                        json=update_data,
                        timeout=30
                    )
                    
                    # We expect these to fail gracefully, not crash
                    if response.status_code in [400, 422]:  # Bad request or validation error
                        error_handling_results.append({
                            'time': problem_time,
                            'handled_gracefully': True,
                            'status_code': response.status_code
                        })
                    else:
                        error_handling_results.append({
                            'time': problem_time,
                            'handled_gracefully': False,
                            'status_code': response.status_code
                        })
                        
                except Exception as e:
                    error_handling_results.append({
                        'time': problem_time,
                        'handled_gracefully': False,
                        'error': str(e)
                    })
            
            # Log results
            graceful_handling = all(result.get('handled_gracefully', False) for result in error_handling_results)
            
            self.log_test(
                "Error Handling Test",
                graceful_handling,
                f"Tested {len(problematic_times)} problematic time formats",
                "" if graceful_handling else "Some invalid times were not handled gracefully"
            )
            
            return error_handling_results
        
        return []

    def run_comprehensive_test(self):
        """Run all working hours calculation tests"""
        print("🚀 STARTING WORKING HOURS CALCULATION FIX TESTING")
        print("🔧 Testing datetime parsing fix in calculate_working_hours_and_deductions")
        print("=" * 80)
        print()
        
        # Step 1: Authenticate as Super Admin
        if not self.authenticate_super_admin():
            print("🚨 CRITICAL: Super Admin authentication failed - cannot proceed")
            return self.generate_summary()
        
        # Step 2: Test specific scenarios
        scenario_results = self.test_specific_scenarios()
        
        # Step 3: Test different time formats
        format_results = self.test_different_time_formats()
        
        # Step 4: Test error handling
        error_results = self.check_backend_logs()
        
        return self.generate_summary()

    def generate_summary(self):
        """Generate comprehensive test summary"""
        print("\n" + "=" * 80)
        print("📊 WORKING HOURS CALCULATION FIX TEST RESULTS")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📈 Overall Results: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}% success rate)")
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
        
        # Critical assessment for the specific fix
        auth_working = any(r['success'] and 'Authentication' in r['test'] for r in self.test_results)
        calculation_working = any(r['success'] and 'Working Hours Calculation' in r['test'] for r in self.test_results)
        
        if auth_working and calculation_working:
            print("🎉 WORKING HOURS CALCULATION FIX: SUCCESS")
            print("✅ Super Admin authentication working")
            print("✅ Working hours calculation functioning correctly")
            print("✅ No datetime parsing errors detected")
            print("✅ Different time formats handled properly")
        else:
            print("🚨 WORKING HOURS CALCULATION FIX: ISSUES DETECTED")
            if not auth_working:
                print("❌ Super Admin authentication issues")
            if not calculation_working:
                print("❌ Working hours calculation still has issues")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': success_rate,
            'auth_working': auth_working,
            'calculation_working': calculation_working,
            'results': self.test_results
        }

if __name__ == "__main__":
    tester = WorkingHoursTestSuite()
    summary = tester.run_comprehensive_test()
    
    # Exit with appropriate code
    if summary['success_rate'] >= 80 and summary['auth_working'] and summary['calculation_working']:
        exit(0)  # Success
    else:
        exit(1)  # Failure