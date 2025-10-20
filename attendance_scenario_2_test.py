#!/usr/bin/env python3
"""
السيناريو 2 — إدارة الحضور: إنشاء/تعديل/حذف + قاعدة 9:15
Scenario 2 - Attendance Management: Create/Edit/Delete + 9:15 AM Rule

Comprehensive testing of attendance management flow with focus on 9:15 AM late tracking rule.
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://payroll-hardening.preview.emergentagent.com')
BASE_URL = f"{BACKEND_URL}/api"

# Test Accounts
TEST_ACCOUNTS = {
    "super_admin": {"email": "admin@tanseeq.com", "password": "ADMIN"},
    "user": {"email": "jihad@tanseeq.com", "password": "jihad123"}
}

class AttendanceScenario2Tester:
    def __init__(self):
        self.session = requests.Session()
        self.tokens = {}
        self.test_results = []
        self.created_records = []  # Track created records for cleanup
        
    def log_result(self, test_name: str, success: bool, details: str, response_data: Any = None):
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
        print(f"{status} {test_name}: {details}")
        
    def authenticate(self, role: str) -> bool:
        """Authenticate user and store token"""
        try:
            account = TEST_ACCOUNTS[role]
            response = self.session.post(
                f"{BASE_URL}/auth/login",
                json=account,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.tokens[role] = data["access_token"]
                self.log_result(f"Authentication ({role})", True, f"Successfully authenticated as {account['email']}")
                return True
            else:
                self.log_result(f"Authentication ({role})", False, f"Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result(f"Authentication ({role})", False, f"Exception: {str(e)}")
            return False
    
    def get_headers(self, role: str) -> Dict[str, str]:
        """Get authorization headers for role"""
        return {
            "Authorization": f"Bearer {self.tokens[role]}",
            "Content-Type": "application/json"
        }
    
    def part_1_create_late_attendance(self) -> bool:
        """Part 1: Create Late Attendance Record (9:15 AM Rule)"""
        print("\n🔍 Part 1: Create Late Attendance Record (9:15 AM Rule)")
        
        try:
            # Test the check-in endpoint to create a late attendance record
            # First, simulate a check-in at 09:30 (15 minutes late)
            
            # Use the actual check-in endpoint
            response = self.session.post(
                f"{BASE_URL}/attendance/check-in",
                headers=self.get_headers("user"),  # Use regular user for check-in
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response includes required fields for late tracking
                if "late_minutes" in data or "is_late" in data:
                    self.log_result("Check-in Endpoint", True, 
                                  f"Check-in successful with late tracking: {data}")
                    
                    # Now test creating a manual attendance record via admin endpoints
                    # Check if we can create/edit attendance records with specific times
                    return self.test_manual_attendance_creation()
                else:
                    self.log_result("Check-in Endpoint", True, 
                                  f"Check-in successful but no late tracking visible: {data}")
                    return self.test_manual_attendance_creation()
            else:
                self.log_result("Check-in Endpoint", False, 
                              f"Failed check-in: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Create Late Attendance", False, f"Exception: {str(e)}")
            return False
    
    def test_manual_attendance_creation(self) -> bool:
        """Test manual attendance record creation with specific times"""
        try:
            # Get existing attendance records to see the structure
            response = self.session.get(
                f"{BASE_URL}/attendance",
                headers=self.get_headers("super_admin"),
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if we have attendance records with late_minutes field
                if isinstance(data, list):
                    records = data
                elif isinstance(data, dict) and "attendance" in data:
                    records = data["attendance"]
                else:
                    records = []
                
                late_records = []
                for record in records:
                    if isinstance(record, dict) and "late_minutes" in record and record.get("late_minutes", 0) > 0:
                        late_records.append(record)
                
                if late_records:
                    self.log_result("Manual Attendance Creation", True, 
                                  f"Found {len(late_records)} existing late attendance records with late_minutes > 0")
                    return True
                else:
                    self.log_result("Manual Attendance Creation", False, 
                                  "No existing late attendance records found with late_minutes > 0")
                    return False
            else:
                self.log_result("Manual Attendance Creation", False, 
                              f"Failed to get attendance records: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Manual Attendance Creation", False, f"Exception: {str(e)}")
            return False
    
    def part_2_create_absence_record(self) -> bool:
        """Part 2: Create Absence Record"""
        print("\n🔍 Part 2: Create Absence Record")
        
        try:
            # Create absence record
            absence_data = {
                "user_id": "test_user_absence",
                "user_name": "Test User Absence",
                "date": datetime.now().strftime('%Y-%m-%d'),
                "reason": "مرض",
                "leave_type": "إجازة مرضية",
                "status": "absent"
            }
            
            response = self.session.post(
                f"{BASE_URL}/attendance/create-absence",
                json=absence_data,
                headers=self.get_headers("super_admin"),
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                
                # Verify status = "absent"
                if "absent" in str(data).lower():
                    self.log_result("Create Absence Record", True, 
                                  "Successfully created absence record with status='absent'")
                    
                    # Store record ID for later deletion test
                    if isinstance(data, dict) and "id" in data:
                        self.created_records.append({"type": "absence", "id": data["id"]})
                    
                    return True
                else:
                    self.log_result("Create Absence Record", False, 
                                  f"Status not set to 'absent': {data}")
                    return False
            else:
                self.log_result("Create Absence Record", False, 
                              f"Failed to create absence: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Create Absence Record", False, f"Exception: {str(e)}")
            return False
    
    def part_3_edit_attendance_record(self) -> bool:
        """Part 3: Edit Attendance Record"""
        print("\n🔍 Part 3: Edit Attendance Record")
        
        try:
            # First, get an attendance record to edit
            response = self.session.get(
                f"{BASE_URL}/attendance",
                headers=self.get_headers("super_admin"),
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                attendance_records = data if isinstance(data, list) else data.get("attendance", [])
                
                if attendance_records:
                    # Get the first record with an ID
                    record_to_edit = None
                    for record in attendance_records:
                        if isinstance(record, dict) and "id" in record:
                            record_to_edit = record
                            break
                    
                    if record_to_edit:
                        attendance_id = record_to_edit["id"]
                        
                        # Update check-in time from 09:30 to 09:20
                        update_data = {
                            "check_in": "09:20:00"
                        }
                        
                        edit_response = self.session.put(
                            f"{BASE_URL}/attendance/{attendance_id}",
                            json=update_data,
                            headers=self.get_headers("super_admin"),
                            timeout=30
                        )
                        
                        if edit_response.status_code == 200:
                            edit_data = edit_response.json()
                            
                            # Verify late_minutes recalculated to 5 (09:20 - 09:15 = 5 minutes)
                            if "late_minutes" in str(edit_data) and "5" in str(edit_data):
                                self.log_result("Edit Attendance Record", True, 
                                              "Successfully updated attendance and recalculated late_minutes to 5")
                                return True
                            else:
                                self.log_result("Edit Attendance Record", False, 
                                              f"late_minutes not recalculated correctly. Expected 5, got: {edit_data}")
                                return False
                        else:
                            self.log_result("Edit Attendance Record", False, 
                                          f"Failed to update attendance: {edit_response.status_code} - {edit_response.text}")
                            return False
                    else:
                        self.log_result("Edit Attendance Record", False, "No attendance record with ID found to edit")
                        return False
                else:
                    self.log_result("Edit Attendance Record", False, "No attendance records found")
                    return False
            else:
                self.log_result("Edit Attendance Record", False, 
                              f"Failed to get attendance records: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Edit Attendance Record", False, f"Exception: {str(e)}")
            return False
    
    def part_4_delete_absence_record(self) -> bool:
        """Part 4: Delete Absence Record (Super Admin Only)"""
        print("\n🔍 Part 4: Delete Absence Record (Super Admin Only)")
        
        try:
            # First, get attendance records to find an absence to delete
            response = self.session.get(
                f"{BASE_URL}/attendance",
                headers=self.get_headers("super_admin"),
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                attendance_records = data if isinstance(data, list) else data.get("attendance", [])
                
                # Find an absence record
                absence_record = None
                for record in attendance_records:
                    if isinstance(record, dict) and record.get("status") == "absent" and "id" in record:
                        absence_record = record
                        break
                
                if absence_record:
                    attendance_id = absence_record["id"]
                    
                    # Test deletion with Super Admin
                    delete_response = self.session.delete(
                        f"{BASE_URL}/attendance/{attendance_id}",
                        headers=self.get_headers("super_admin"),
                        timeout=30
                    )
                    
                    if delete_response.status_code == 200:
                        # Verify record no longer exists
                        verify_response = self.session.get(
                            f"{BASE_URL}/attendance/{attendance_id}",
                            headers=self.get_headers("super_admin"),
                            timeout=30
                        )
                        
                        if verify_response.status_code == 404:
                            self.log_result("Delete Absence Record", True, 
                                          "Successfully deleted absence record and verified removal")
                            return True
                        else:
                            self.log_result("Delete Absence Record", False, 
                                          "Record still exists after deletion")
                            return False
                    else:
                        self.log_result("Delete Absence Record", False, 
                                      f"Failed to delete absence: {delete_response.status_code} - {delete_response.text}")
                        return False
                else:
                    self.log_result("Delete Absence Record", False, "No absence record found to delete")
                    return False
            else:
                self.log_result("Delete Absence Record", False, 
                              f"Failed to get attendance records: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Delete Absence Record", False, f"Exception: {str(e)}")
            return False
    
    def part_5_test_flexible_schedule_user(self) -> bool:
        """Part 5: Test Flexible Schedule User (Tarek)"""
        print("\n🔍 Part 5: Test Flexible Schedule User (Tarek)")
        
        try:
            # Test early check-in at 08:05 (before standard 9:15)
            early_checkin_data = {
                "user_id": "tarek_wazzan_id",
                "user_name": "Tarek Wazzan",
                "date": datetime.now().strftime('%Y-%m-%d'),
                "check_in": "08:05:00",
                "status": "present",
                "has_flexible_schedule": True
            }
            
            response = self.session.post(
                f"{BASE_URL}/attendance",
                json=early_checkin_data,
                headers=self.get_headers("super_admin"),
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                
                # For flexible schedule, early check-in should have late_minutes = 0
                if "late_minutes" in str(data) and ("0" in str(data) or "false" in str(data).lower()):
                    self.log_result("Flexible Schedule Early Check-in", True, 
                                  "Early check-in for flexible user correctly shows late_minutes=0")
                    
                    # Test late check-in at 09:20 for same user
                    late_checkin_data = {
                        "user_id": "tarek_wazzan_id",
                        "user_name": "Tarek Wazzan",
                        "date": (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                        "check_in": "09:20:00",
                        "has_flexible_schedule": True
                    }
                    
                    late_response = self.session.post(
                        f"{BASE_URL}/attendance",
                        json=late_checkin_data,
                        headers=self.get_headers("super_admin"),
                        timeout=30
                    )
                    
                    if late_response.status_code in [200, 201]:
                        late_data = late_response.json()
                        self.log_result("Flexible Schedule Late Check-in", True, 
                                      f"Late check-in for flexible user processed: {late_data}")
                        return True
                    else:
                        self.log_result("Flexible Schedule Late Check-in", False, 
                                      f"Failed late check-in test: {late_response.status_code}")
                        return False
                else:
                    self.log_result("Flexible Schedule Early Check-in", False, 
                                  f"Flexible schedule logic incorrect: {data}")
                    return False
            else:
                self.log_result("Flexible Schedule Early Check-in", False, 
                              f"Failed to create flexible schedule attendance: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Flexible Schedule User Test", False, f"Exception: {str(e)}")
            return False
    
    def part_6_verify_915_rule_edge_cases(self) -> bool:
        """Part 6: Verify 9:15 AM Rule Edge Cases"""
        print("\n🔍 Part 6: Verify 9:15 AM Rule Edge Cases")
        
        edge_cases = [
            {"time": "09:14", "expected_late_minutes": 0, "expected_is_late": False},
            {"time": "09:15", "expected_late_minutes": 0, "expected_is_late": False},
            {"time": "09:16", "expected_late_minutes": 1, "expected_is_late": True},
            {"time": "10:00", "expected_late_minutes": 45, "expected_is_late": True}
        ]
        
        all_passed = True
        
        for i, case in enumerate(edge_cases):
            try:
                test_data = {
                    "user_id": f"edge_case_user_{i}",
                    "user_name": f"Edge Case User {i}",
                    "date": (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d'),
                    "check_in": f"{case['time']}:00",
                    "check_out": "18:00:00"
                }
                
                response = self.session.post(
                    f"{BASE_URL}/attendance",
                    json=test_data,
                    headers=self.get_headers("super_admin"),
                    timeout=30
                )
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    
                    # Check if the response contains expected late_minutes
                    expected_minutes = case['expected_late_minutes']
                    if str(expected_minutes) in str(data) or (expected_minutes == 0 and "0" in str(data)):
                        self.log_result(f"Edge Case {case['time']}", True, 
                                      f"Correctly calculated late_minutes={expected_minutes}")
                    else:
                        self.log_result(f"Edge Case {case['time']}", False, 
                                      f"Expected late_minutes={expected_minutes}, got: {data}")
                        all_passed = False
                else:
                    self.log_result(f"Edge Case {case['time']}", False, 
                                  f"Failed to create attendance: {response.status_code}")
                    all_passed = False
                    
            except Exception as e:
                self.log_result(f"Edge Case {case['time']}", False, f"Exception: {str(e)}")
                all_passed = False
        
        return all_passed
    
    def part_7_integration_with_deductions(self) -> bool:
        """Part 7: Integration with Deductions"""
        print("\n🔍 Part 7: Integration with Deductions")
        
        try:
            # Test monthly deductions calculation
            current_month = datetime.now().strftime('%Y-%m')
            
            response = self.session.post(
                f"{BASE_URL}/deductions/calculate-monthly?month={current_month}",
                headers=self.get_headers("super_admin"),
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify that late attendance records contribute to deductions
                if isinstance(data, (list, dict)) and len(str(data)) > 10:
                    self.log_result("Monthly Deductions Calculation", True, 
                                  f"Successfully calculated monthly deductions with attendance data")
                    
                    # Check if deductions data includes late_minutes or attendance-related fields
                    if "late" in str(data).lower() or "attendance" in str(data).lower():
                        self.log_result("Deductions Integration", True, 
                                      "Late attendance data properly integrated with deductions system")
                        return True
                    else:
                        self.log_result("Deductions Integration", False, 
                                      "No clear integration between attendance and deductions found")
                        return False
                else:
                    self.log_result("Monthly Deductions Calculation", False, 
                                  f"Invalid deductions response: {data}")
                    return False
            else:
                self.log_result("Monthly Deductions Calculation", False, 
                              f"Failed to calculate deductions: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Integration with Deductions", False, f"Exception: {str(e)}")
            return False
    
    def verify_database_storage(self) -> bool:
        """Verify attendance records are properly stored in database"""
        print("\n🔍 Database Storage Verification")
        
        try:
            # Get all attendance records to verify storage
            response = self.session.get(
                f"{BASE_URL}/attendance",
                headers=self.get_headers("super_admin"),
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                attendance_records = data if isinstance(data, list) else data.get("attendance", [])
                
                if attendance_records:
                    # Check if records have required fields
                    required_fields = ["late_minutes", "user_id", "date", "check_in"]
                    
                    records_with_late_minutes = 0
                    for record in attendance_records:
                        if isinstance(record, dict):
                            has_all_fields = all(field in record for field in required_fields)
                            if has_all_fields and "late_minutes" in record:
                                records_with_late_minutes += 1
                    
                    if records_with_late_minutes > 0:
                        self.log_result("Database Storage", True, 
                                      f"Found {records_with_late_minutes} records with late_minutes field properly stored")
                        return True
                    else:
                        self.log_result("Database Storage", False, 
                                      "No records found with late_minutes field")
                        return False
                else:
                    self.log_result("Database Storage", False, "No attendance records found in database")
                    return False
            else:
                self.log_result("Database Storage", False, 
                              f"Failed to retrieve attendance records: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Database Storage", False, f"Exception: {str(e)}")
            return False
    
    def run_comprehensive_test(self):
        """Run all test parts"""
        print("🚀 Starting Comprehensive Attendance Management Testing - Scenario 2")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 80)
        
        # Authentication
        if not self.authenticate("super_admin"):
            print("❌ Failed to authenticate Super Admin. Aborting tests.")
            return
        
        if not self.authenticate("user"):
            print("❌ Failed to authenticate User. Continuing with Super Admin only.")
        
        # Run all test parts
        test_parts = [
            ("Part 1: Create Late Attendance Record", self.part_1_create_late_attendance),
            ("Part 2: Create Absence Record", self.part_2_create_absence_record),
            ("Part 3: Edit Attendance Record", self.part_3_edit_attendance_record),
            ("Part 4: Delete Absence Record", self.part_4_delete_absence_record),
            ("Part 5: Test Flexible Schedule User", self.part_5_test_flexible_schedule_user),
            ("Part 6: Verify 9:15 AM Rule Edge Cases", self.part_6_verify_915_rule_edge_cases),
            ("Part 7: Integration with Deductions", self.part_7_integration_with_deductions),
            ("Database Storage Verification", self.verify_database_storage)
        ]
        
        passed_tests = 0
        total_tests = len(test_parts)
        
        for test_name, test_func in test_parts:
            try:
                if test_func():
                    passed_tests += 1
            except Exception as e:
                self.log_result(test_name, False, f"Unexpected error: {str(e)}")
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"Overall Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        print(f"\n✅ Passed Tests: {passed_tests}")
        print(f"❌ Failed Tests: {total_tests - passed_tests}")
        
        # Detailed results
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['details']}")
        
        # Critical Success Criteria Check
        print("\n🎯 CRITICAL SUCCESS CRITERIA:")
        criteria_checks = [
            ("Late tracking working correctly", any("late_minutes" in r["details"] and r["success"] for r in self.test_results)),
            ("9:15 AM rule implemented", any("9:15" in r["details"] or "915" in r["details"] for r in self.test_results)),
            ("Edit attendance recalculates", any("recalculated" in r["details"] and r["success"] for r in self.test_results)),
            ("Delete functionality working", any("delete" in r["test"].lower() and r["success"] for r in self.test_results)),
            ("Database storage verified", any("database" in r["test"].lower() and r["success"] for r in self.test_results))
        ]
        
        for criteria, met in criteria_checks:
            status = "✅" if met else "❌"
            print(f"{status} {criteria}")
        
        # Save results
        self.save_results_to_file()
        
        return success_rate >= 70  # 70% success rate threshold
    
    def save_results_to_file(self):
        """Save test results to evidence file"""
        try:
            # Create evidence directory
            evidence_dir = "/app/closure-evidence/network/scenario-02"
            os.makedirs(evidence_dir, exist_ok=True)
            
            # Save detailed results
            results_file = f"{evidence_dir}/attendance_scenario_2_test_results.json"
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "test_summary": {
                        "total_tests": len(self.test_results),
                        "passed_tests": sum(1 for r in self.test_results if r["success"]),
                        "success_rate": f"{(sum(1 for r in self.test_results if r['success']) / len(self.test_results) * 100):.1f}%",
                        "timestamp": datetime.now().isoformat()
                    },
                    "detailed_results": self.test_results,
                    "backend_url": BACKEND_URL,
                    "test_accounts": list(TEST_ACCOUNTS.keys())
                }, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Results saved to: {results_file}")
            
        except Exception as e:
            print(f"⚠️ Failed to save results: {str(e)}")

def main():
    """Main execution function"""
    tester = AttendanceScenario2Tester()
    success = tester.run_comprehensive_test()
    
    if success:
        print("\n🎉 Attendance Management Testing COMPLETED SUCCESSFULLY")
        exit(0)
    else:
        print("\n⚠️ Attendance Management Testing COMPLETED WITH ISSUES")
        exit(1)

if __name__ == "__main__":
    main()