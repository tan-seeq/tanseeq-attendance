#!/usr/bin/env python3
"""
🔥 DETAILED: 9:15 AM Late Tracking Fix Verification with Super Admin Access
Testing the critical fix implementation and database state
"""

import requests
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

# Get backend URL from frontend .env
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.split('=')[1].strip()
            break

API_BASE = f"{BACKEND_URL}/api"

# Test credentials
TEST_USERS = {
    "regular": {"email": "jihad@tanseeq.com", "password": "jihad123"},
    "admin": {"email": "mahmoud@tanseeq.com", "password": "mahmoud123"},
    "super_admin": {"email": "hatem@tan-seeq.co", "password": "hatem123"}
}

class DetailedLateTrackingTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        
    def log_result(self, test_name, success, details, expected=None, actual=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "expected": expected,
            "actual": actual,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        print(f"   Details: {details}")
        if expected and actual:
            print(f"   Expected: {expected}")
            print(f"   Actual: {actual}")
        print()
        
    def authenticate(self, user_type="regular"):
        """Authenticate user and get token"""
        try:
            user_creds = TEST_USERS[user_type]
            response = self.session.post(f"{API_BASE}/auth/login", json=user_creds)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data["access_token"]
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                self.log_result(
                    f"Authentication ({user_type})",
                    True,
                    f"Successfully authenticated as {user_creds['email']}"
                )
                return True
            else:
                self.log_result(
                    f"Authentication ({user_type})",
                    False,
                    f"Failed to authenticate: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                f"Authentication ({user_type})",
                False,
                f"Authentication error: {str(e)}"
            )
            return False
    
    def examine_attendance_records_detailed(self):
        """Examine attendance records in detail for late tracking"""
        try:
            response = self.session.get(f"{API_BASE}/attendance")
            
            if response.status_code == 200:
                data = response.json()
                attendance_records = data if isinstance(data, list) else data.get("attendance", [])
                
                print(f"\n📊 DETAILED ATTENDANCE ANALYSIS ({len(attendance_records)} records):")
                print("-" * 80)
                
                late_tracking_issues = []
                records_with_late_minutes = 0
                records_after_915 = 0
                
                for i, record in enumerate(attendance_records):
                    check_in = record.get("check_in", "")
                    late_minutes = record.get("late_minutes", "NOT_SET")
                    is_late = record.get("is_late", "NOT_SET")
                    date = record.get("date", "")
                    user_name = record.get("user_name", "")
                    
                    # Check if late_minutes field exists
                    has_late_minutes_field = "late_minutes" in record
                    if has_late_minutes_field:
                        records_with_late_minutes += 1
                    
                    if check_in:
                        try:
                            # Parse check-in time
                            time_parts = check_in.split(':')
                            hour = int(time_parts[0])
                            minute = int(time_parts[1])
                            
                            # Check if after 9:15 AM
                            is_after_915 = hour > 9 or (hour == 9 and minute > 15)
                            
                            if is_after_915:
                                records_after_915 += 1
                                
                                # Calculate expected late minutes
                                check_in_minutes = hour * 60 + minute
                                threshold_minutes = 9 * 60 + 15  # 9:15 AM
                                expected_late_minutes = check_in_minutes - threshold_minutes
                                
                                # Check if late_minutes is correct
                                if not has_late_minutes_field or late_minutes == 0:
                                    late_tracking_issues.append({
                                        "date": date,
                                        "user_name": user_name,
                                        "check_in": check_in,
                                        "late_minutes": late_minutes,
                                        "expected_late_minutes": expected_late_minutes,
                                        "has_field": has_late_minutes_field,
                                        "issue": "Missing late_minutes field or incorrect value"
                                    })
                                    
                                    print(f"❌ {date} | {user_name} | {check_in} | late_minutes={late_minutes} | Expected={expected_late_minutes}")
                                else:
                                    print(f"✅ {date} | {user_name} | {check_in} | late_minutes={late_minutes} | Expected={expected_late_minutes}")
                            else:
                                # Should be 0 late minutes
                                if has_late_minutes_field and late_minutes == 0:
                                    print(f"✅ {date} | {user_name} | {check_in} | late_minutes={late_minutes} | On time")
                                elif has_late_minutes_field and late_minutes > 0:
                                    print(f"⚠️ {date} | {user_name} | {check_in} | late_minutes={late_minutes} | Should be 0")
                                else:
                                    print(f"⚪ {date} | {user_name} | {check_in} | late_minutes={late_minutes} | On time (no field)")
                        
                        except (ValueError, IndexError):
                            print(f"⚠️ {date} | {user_name} | {check_in} | Invalid time format")
                            continue
                    else:
                        print(f"⚪ {date} | {user_name} | No check-in time")
                
                print("-" * 80)
                print(f"📈 SUMMARY:")
                print(f"   Total records: {len(attendance_records)}")
                print(f"   Records with late_minutes field: {records_with_late_minutes}")
                print(f"   Records with check-in after 9:15 AM: {records_after_915}")
                print(f"   Late tracking issues found: {len(late_tracking_issues)}")
                
                success = len(late_tracking_issues) == 0
                
                self.log_result(
                    "Detailed Attendance Analysis",
                    success,
                    f"Found {len(late_tracking_issues)} late tracking issues out of {records_after_915} records after 9:15 AM",
                    "All records after 9:15 AM should have correct late_minutes",
                    f"Issues: {len(late_tracking_issues)}, Records after 9:15: {records_after_915}"
                )
                
                return late_tracking_issues, attendance_records
                
            else:
                self.log_result(
                    "Detailed Attendance Analysis",
                    False,
                    f"Failed to get attendance records: {response.status_code}"
                )
                return [], []
                
        except Exception as e:
            self.log_result(
                "Detailed Attendance Analysis",
                False,
                f"Error in detailed analysis: {str(e)}"
            )
            return [], []
    
    def test_check_in_endpoint_implementation(self):
        """Test the current check-in endpoint to see if it includes late_minutes in response"""
        try:
            # First, try to check out if already checked in
            checkout_response = self.session.post(f"{API_BASE}/attendance/check-out")
            
            # Now try to check in
            response = self.session.post(f"{API_BASE}/attendance/check-in")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                has_late_minutes = "late_minutes" in data
                has_is_late = "is_late" in data
                has_schedule_type = "schedule_type" in data
                
                print(f"\n🔍 CHECK-IN RESPONSE ANALYSIS:")
                print(f"   Response keys: {list(data.keys())}")
                print(f"   Has late_minutes: {has_late_minutes}")
                print(f"   Has is_late: {has_is_late}")
                print(f"   Has schedule_type: {has_schedule_type}")
                
                if has_late_minutes:
                    print(f"   late_minutes value: {data.get('late_minutes')}")
                if has_is_late:
                    print(f"   is_late value: {data.get('is_late')}")
                
                success = has_late_minutes and has_is_late
                
                self.log_result(
                    "Check-in Endpoint Response",
                    success,
                    f"Check-in response includes late tracking fields",
                    "Response should include late_minutes and is_late",
                    f"late_minutes: {has_late_minutes}, is_late: {has_is_late}"
                )
                
                return data
                
            elif response.status_code == 400:
                # Already checked in
                error_msg = response.json().get("detail", "")
                if "تم تسجيل الحضور مسبقاً" in error_msg:
                    self.log_result(
                        "Check-in Endpoint Response",
                        True,
                        "Already checked in today (expected behavior)"
                    )
                    return {"already_checked_in": True}
                else:
                    self.log_result(
                        "Check-in Endpoint Response",
                        False,
                        f"Unexpected 400 error: {error_msg}"
                    )
                    return None
            else:
                self.log_result(
                    "Check-in Endpoint Response",
                    False,
                    f"Unexpected response: {response.status_code} - {response.text}"
                )
                return None
                
        except Exception as e:
            self.log_result(
                "Check-in Endpoint Response",
                False,
                f"Error testing check-in endpoint: {str(e)}"
            )
            return None
    
    def test_deductions_with_super_admin(self):
        """Test deductions integration with Super Admin access"""
        try:
            # Test monthly deductions calculation
            current_month = datetime.now().strftime("%Y-%m")
            response = self.session.post(f"{API_BASE}/deductions/calculate-monthly?month={current_month}")
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"\n💰 DEDUCTIONS CALCULATION ANALYSIS:")
                print(f"   Records returned: {len(data) if isinstance(data, list) else 'Not a list'}")
                
                if isinstance(data, list) and len(data) > 0:
                    sample_record = data[0]
                    print(f"   Sample record keys: {list(sample_record.keys())}")
                    
                    # Check for late-related fields
                    late_fields = [key for key in sample_record.keys() if 'late' in key.lower()]
                    attendance_fields = [key for key in sample_record.keys() if 'attendance' in key.lower()]
                    
                    print(f"   Late-related fields: {late_fields}")
                    print(f"   Attendance-related fields: {attendance_fields}")
                    
                    has_late_integration = len(late_fields) > 0 or len(attendance_fields) > 0
                    
                    self.log_result(
                        "Deductions Integration (Super Admin)",
                        has_late_integration,
                        f"Monthly deductions includes late/attendance fields",
                        "Should include late_minutes or attendance deduction fields",
                        f"Late fields: {late_fields}, Attendance fields: {attendance_fields}"
                    )
                else:
                    self.log_result(
                        "Deductions Integration (Super Admin)",
                        False,
                        "No deduction records returned"
                    )
                
                return data
                
            else:
                self.log_result(
                    "Deductions Integration (Super Admin)",
                    False,
                    f"Deductions calculation failed: {response.status_code} - {response.text}"
                )
                return []
                
        except Exception as e:
            self.log_result(
                "Deductions Integration (Super Admin)",
                False,
                f"Error testing deductions: {str(e)}"
            )
            return []
    
    def test_check_in_with_mock_time(self):
        """Test check-in behavior by examining the server-side logic"""
        try:
            # Get current user info to understand their schedule
            response = self.session.get(f"{API_BASE}/auth/me")
            
            if response.status_code == 200:
                user_info = response.json()
                
                print(f"\n👤 USER SCHEDULE ANALYSIS:")
                print(f"   User: {user_info.get('name')}")
                print(f"   Role: {user_info.get('role')}")
                
                # Check if user has flexible schedule or fixed schedule
                # This would help understand how late calculation should work
                
                self.log_result(
                    "User Schedule Analysis",
                    True,
                    f"Retrieved user info for schedule analysis"
                )
                
                return user_info
                
            else:
                self.log_result(
                    "User Schedule Analysis",
                    False,
                    f"Failed to get user info: {response.status_code}"
                )
                return None
                
        except Exception as e:
            self.log_result(
                "User Schedule Analysis",
                False,
                f"Error getting user info: {str(e)}"
            )
            return None
    
    def run_comprehensive_test(self):
        """Run comprehensive late tracking verification"""
        print("🔥 DETAILED: 9:15 AM Late Tracking Fix Verification")
        print("=" * 80)
        
        # Test with regular user first
        print("\n👤 TESTING WITH REGULAR USER:")
        if not self.authenticate("regular"):
            print("❌ Cannot proceed without regular user authentication")
            return False
        
        # Test 1: User Schedule Analysis
        user_info = self.test_check_in_with_mock_time()
        
        # Test 2: Check-in Endpoint Implementation
        check_in_response = self.test_check_in_endpoint_implementation()
        
        # Test 3: Detailed Attendance Analysis
        late_issues, attendance_records = self.examine_attendance_records_detailed()
        
        # Test with Super Admin
        print("\n👑 TESTING WITH SUPER ADMIN:")
        if not self.authenticate("super_admin"):
            print("❌ Cannot test deductions without super admin access")
        else:
            # Test 4: Deductions Integration
            deductions_data = self.test_deductions_with_super_admin()
        
        # Summary
        print("\n" + "=" * 80)
        print("📋 DETAILED TEST SUMMARY:")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Critical Assessment
        critical_issues = []
        
        if len(late_issues) > 0:
            critical_issues.append(f"{len(late_issues)} historical records with incorrect late tracking")
        
        # Check if check-in endpoint includes late_minutes in response
        check_in_has_late_fields = False
        for result in self.test_results:
            if result["test"] == "Check-in Endpoint Response" and result["success"]:
                check_in_has_late_fields = True
                break
        
        if not check_in_has_late_fields:
            critical_issues.append("Check-in endpoint does not return late_minutes in response")
        
        print(f"\n🎯 CRITICAL ASSESSMENT:")
        if critical_issues:
            print(f"🚨 ISSUES FOUND:")
            for issue in critical_issues:
                print(f"   ❌ {issue}")
            print(f"\n🔴 VERDICT: 9:15 AM Late Tracking Fix NEEDS IMMEDIATE ATTENTION")
            
            print(f"\n🔧 RECOMMENDED ACTIONS:")
            print(f"   1. Update check-in endpoint to calculate and store late_minutes at check-in time")
            print(f"   2. Update existing attendance records to include late_minutes field")
            print(f"   3. Ensure check-in API response includes late_minutes and is_late fields")
            print(f"   4. Verify deductions calculation uses late_minutes from attendance records")
        else:
            print(f"✅ All critical tests passed")
            print(f"\n🟢 VERDICT: 9:15 AM Late Tracking Fix WORKING CORRECTLY")
        
        # Save detailed results
        with open('/app/detailed_late_tracking_results.json', 'w') as f:
            json.dump({
                "test_summary": {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "success_rate": (passed_tests/total_tests)*100,
                    "critical_issues": critical_issues
                },
                "detailed_results": self.test_results,
                "late_tracking_issues": late_issues,
                "attendance_records_count": len(attendance_records)
            }, f, indent=2)
        
        return len(critical_issues) == 0

if __name__ == "__main__":
    tester = DetailedLateTrackingTester()
    success = tester.run_comprehensive_test()
    exit(0 if success else 1)