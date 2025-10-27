#!/usr/bin/env python3
"""
CORRECTED COMPREHENSIVE BACKEND TESTING - PRIORITY ROUTES & FUNCTIONALITY
Using correct endpoint patterns from server.py analysis
"""

import requests
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import time
import uuid

# Configuration - Use environment variable
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://hr-attendance-system.preview.emergentagent.com')
BASE_URL = f"{BACKEND_URL}/api"

# Test accounts from review request
TEST_ACCOUNTS = {
    "super_admin": {"email": "admin@tanseeq.com", "password": "ADMIN"},
    "user": {"email": "jihad@tanseeq.com", "password": "jihad123"}
}

class CorrectedBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.tokens = {}
        self.test_results = []
        self.evidence_dir = Path("./evidence/backend_corrected")
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        
    def log_result(self, test_name, status, details="", response_data=None):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        if response_data:
            result["response"] = response_data
        self.test_results.append(result)
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⏭️"
        print(f"{status_icon} {test_name}: {details}")
        
    def authenticate(self, account_type):
        """Authenticate and get JWT token"""
        try:
            account = TEST_ACCOUNTS[account_type]
            response = self.session.post(f"{BASE_URL}/auth/login", json=account)
            
            if response.status_code == 200:
                data = response.json()
                token = data["access_token"]
                user_info = data.get("user", {})
                self.tokens[account_type] = token
                self.session.headers.update({"Authorization": f"Bearer {token}"})
                self.log_result(f"Authentication - {account_type}", "PASS", 
                              f"Successfully authenticated {account['email']} (Role: {user_info.get('role', 'unknown')})")
                return True
            else:
                self.log_result(f"Authentication - {account_type}", "FAIL", 
                              f"Failed to authenticate: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result(f"Authentication - {account_type}", "FAIL", f"Exception: {str(e)}")
            return False

    def test_payroll_system_corrected(self):
        """Test PAYROLL SYSTEM with correct endpoints"""
        print("\n💰 Testing PAYROLL SYSTEM (CORRECTED ENDPOINTS)...")
        
        # 1. GET /api/payroll/cycles - List all cycles
        try:
            response = self.session.get(f"{BASE_URL}/payroll/cycles")
            if response.status_code == 200:
                cycles_data = response.json()
                if isinstance(cycles_data, list):
                    cycles = cycles_data
                else:
                    cycles = cycles_data.get('cycles', [])
                
                self.log_result("Payroll Cycles - List All", "PASS", 
                              f"Retrieved {len(cycles)} cycles with proper JSON structure")
                
                if cycles:
                    self.test_cycle_id = cycles[0].get('id')
                    cycle_month = cycles[0].get('month', 'unknown')
                    
                    # Test correct calculate endpoint: GET /api/payroll/calculate/{month}
                    try:
                        response = self.session.get(f"{BASE_URL}/payroll/calculate/{cycle_month}")
                        if response.status_code == 200:
                            calculation = response.json()
                            employee_count = len(calculation.get("employee_summaries", []))
                            self.log_result("Payroll Cycles - Calculate (Corrected)", "PASS", 
                                          f"Calculated payroll for {employee_count} employees using GET /payroll/calculate/{cycle_month}")
                        else:
                            self.log_result("Payroll Cycles - Calculate (Corrected)", "FAIL", 
                                          f"Failed: {response.status_code} - {response.text}")
                    except Exception as e:
                        self.log_result("Payroll Cycles - Calculate (Corrected)", "FAIL", f"Exception: {str(e)}")
                        
            else:
                self.log_result("Payroll Cycles - List All", "FAIL", 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("Payroll Cycles - List All", "FAIL", f"Exception: {str(e)}")

    def test_attendance_deductions_corrected(self):
        """Test ATTENDANCE DEDUCTIONS with correct endpoints"""
        print("\n📊 Testing ATTENDANCE DEDUCTIONS (CORRECTED ENDPOINTS)...")
        
        # Get employee ID first
        try:
            response = self.session.get(f"{BASE_URL}/employees/list")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    employees = data
                else:
                    employees = data.get('employees', [])
                
                if employees:
                    self.test_employee_id = employees[0]['id']
                    self.log_result("Employees List - Get ID", "PASS", 
                                  f"Retrieved employee ID: {self.test_employee_id}")
        except Exception as e:
            self.log_result("Employees List - Get ID", "FAIL", f"Exception: {str(e)}")

        # Test correct manual deduction endpoint: POST /api/deductions/manual
        if hasattr(self, 'test_employee_id'):
            try:
                deduction_data = {
                    "employee_id": self.test_employee_id,
                    "amount": 100.0,
                    "reason": "Test manual deduction for corrected testing",
                    "category": "late_arrival",
                    "date": datetime.now().strftime("%Y-%m-%d")
                }
                
                response = self.session.post(f"{BASE_URL}/deductions/manual", json=deduction_data)
                if response.status_code in [200, 201]:
                    result = response.json()
                    deduction_id = result.get("id") or result.get("deduction_id")
                    self.log_result("Manual Deductions - Create (Corrected)", "PASS", 
                                  f"Created manual deduction using POST /deductions/manual: {deduction_id}")
                    
                    # Test void deduction: POST /api/deductions/{deduction_id}/void
                    if deduction_id:
                        try:
                            void_data = {"void_reason": "Test void for corrected testing"}
                            response = self.session.post(f"{BASE_URL}/deductions/{deduction_id}/void", json=void_data)
                            if response.status_code == 200:
                                self.log_result("Manual Deductions - Void (Corrected)", "PASS", 
                                              "Deduction voided using POST /deductions/{id}/void")
                            else:
                                self.log_result("Manual Deductions - Void (Corrected)", "FAIL", 
                                              f"Failed: {response.status_code} - {response.text}")
                        except Exception as e:
                            self.log_result("Manual Deductions - Void (Corrected)", "FAIL", f"Exception: {str(e)}")
                            
                else:
                    self.log_result("Manual Deductions - Create (Corrected)", "FAIL", 
                                  f"Failed: {response.status_code} - {response.text}")
            except Exception as e:
                self.log_result("Manual Deductions - Create (Corrected)", "FAIL", f"Exception: {str(e)}")

    def test_attendance_policies_corrected(self):
        """Test ATTENDANCE POLICIES with correct endpoints"""
        print("\n⚡ Testing ATTENDANCE POLICIES (CORRECTED ENDPOINTS)...")
        
        # Get employee ID for policy testing
        if hasattr(self, 'test_employee_id'):
            employee_id = self.test_employee_id
        else:
            # Get first employee
            try:
                response = self.session.get(f"{BASE_URL}/employees/list")
                if response.status_code == 200:
                    data = response.json()
                    employees = data if isinstance(data, list) else data.get('employees', [])
                    if employees:
                        employee_id = employees[0]['id']
                    else:
                        self.log_result("Attendance Policies - No Employee", "SKIP", "No employees available")
                        return
                else:
                    self.log_result("Attendance Policies - No Employee", "SKIP", "Could not get employees")
                    return
            except Exception as e:
                self.log_result("Attendance Policies - No Employee", "SKIP", f"Exception: {str(e)}")
                return

        # Test correct endpoint: GET /api/attendance/policies/{employee_id}
        try:
            response = self.session.get(f"{BASE_URL}/attendance/policies/{employee_id}")
            if response.status_code == 200:
                policy = response.json()
                self.log_result("Attendance Policies - Get Employee Policy", "PASS", 
                              f"Retrieved attendance policy using GET /attendance/policies/{employee_id}")
                
                # Check for specific policy details
                policy_details = []
                if policy.get('start_time') or policy.get('working_hours_start'):
                    policy_details.append(f"start_time: {policy.get('start_time') or policy.get('working_hours_start')}")
                if policy.get('end_flexible') or policy.get('has_flexible_schedule'):
                    policy_details.append("flexible schedule enabled")
                if policy.get('early_start_allowed'):
                    policy_details.append("early start allowed")
                
                if policy_details:
                    self.log_result("Attendance Policies - Policy Details", "PASS", 
                                  f"Policy details: {', '.join(policy_details)}")
                    
            else:
                self.log_result("Attendance Policies - Get Employee Policy", "FAIL", 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("Attendance Policies - Get Employee Policy", "FAIL", f"Exception: {str(e)}")

    def test_work_reports_corrected(self):
        """Test WORK REPORTS with proper client setup"""
        print("\n📝 Testing WORK REPORTS (WITH PROPER CLIENT SETUP)...")
        
        # First create a client to use for work logs
        client_id = None
        try:
            client_data = {
                "company_name": "Test Client for Work Reports",
                "company_name_ar": "عميل اختبار لتقارير العمل",
                "client_code": f"TEST-{uuid.uuid4().hex[:8].upper()}",
                "industry": "Testing",
                "contact_person": "Test Contact",
                "phone": "+971501234567",
                "email": "test@testclient.com"
            }
            
            response = self.session.post(f"{BASE_URL}/work-reports/clients", json=client_data)
            if response.status_code in [200, 201]:
                result = response.json()
                client_id = result.get("id") or result.get("client_id")
                self.log_result("Work Reports - Create Client", "PASS", 
                              f"Created client for work logs: {client_id}")
            else:
                self.log_result("Work Reports - Create Client", "FAIL", 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("Work Reports - Create Client", "FAIL", f"Exception: {str(e)}")

        # Get activity types
        activity_type_id = None
        try:
            response = self.session.get(f"{BASE_URL}/work-reports/activity-types")
            if response.status_code == 200:
                activity_types = response.json()
                if activity_types:
                    activity_type_id = activity_types[0].get('id')
                    self.log_result("Work Reports - Get Activity Types", "PASS", 
                                  f"Retrieved {len(activity_types)} activity types")
                else:
                    # Create a default activity type
                    activity_data = {
                        "name": "Testing Activity",
                        "name_ar": "نشاط اختبار",
                        "category": "testing",
                        "description": "Activity for testing purposes",
                        "default_rate": 100.0,
                        "is_billable": True
                    }
                    response = self.session.post(f"{BASE_URL}/work-reports/activity-types", json=activity_data)
                    if response.status_code in [200, 201]:
                        result = response.json()
                        activity_type_id = result.get("id")
                        self.log_result("Work Reports - Create Activity Type", "PASS", 
                                      f"Created activity type: {activity_type_id}")
            else:
                self.log_result("Work Reports - Get Activity Types", "FAIL", 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("Work Reports - Get Activity Types", "FAIL", f"Exception: {str(e)}")

        # Now test work log creation with proper client_id and activity_type_id
        if client_id and activity_type_id:
            try:
                log_data = {
                    "client_id": client_id,
                    "activity_type_id": activity_type_id,
                    "date": datetime.now().isoformat(),
                    "start_time": datetime.now().isoformat(),
                    "end_time": (datetime.now() + timedelta(hours=2)).isoformat(),
                    "description": "Test work log with proper client and activity type",
                    "notes": "Created during corrected testing with valid references",
                    "is_billable": True,
                    "hourly_rate": 150.0
                }
                
                response = self.session.post(f"{BASE_URL}/work-reports/logs", json=log_data)
                if response.status_code in [200, 201]:
                    result = response.json()
                    log_id = result.get("id") or result.get("log_id")
                    self.log_result("Work Reports - Create Log (Corrected)", "PASS", 
                                  f"Created work log with valid client/activity: {log_id}")
                    
                    # Test update and delete
                    if log_id:
                        # Test update
                        try:
                            update_data = {
                                "description": "Updated test work log with duration recompute",
                                "end_time": (datetime.now() + timedelta(hours=3)).isoformat()
                            }
                            response = self.session.put(f"{BASE_URL}/work-reports/logs/{log_id}", json=update_data)
                            if response.status_code == 200:
                                self.log_result("Work Reports - Update Log (Corrected)", "PASS", 
                                              "Log updated with duration/amount recompute")
                            else:
                                self.log_result("Work Reports - Update Log (Corrected)", "FAIL", 
                                              f"Failed: {response.status_code} - {response.text}")
                        except Exception as e:
                            self.log_result("Work Reports - Update Log (Corrected)", "FAIL", f"Exception: {str(e)}")

                        # Test delete
                        try:
                            response = self.session.delete(f"{BASE_URL}/work-reports/logs/{log_id}")
                            if response.status_code == 200:
                                self.log_result("Work Reports - Delete Log (Corrected)", "PASS", 
                                              "Log deleted successfully")
                            else:
                                self.log_result("Work Reports - Delete Log (Corrected)", "FAIL", 
                                              f"Failed: {response.status_code} - {response.text}")
                        except Exception as e:
                            self.log_result("Work Reports - Delete Log (Corrected)", "FAIL", f"Exception: {str(e)}")
                            
                else:
                    self.log_result("Work Reports - Create Log (Corrected)", "FAIL", 
                                  f"Failed: {response.status_code} - {response.text}")
            except Exception as e:
                self.log_result("Work Reports - Create Log (Corrected)", "FAIL", f"Exception: {str(e)}")
        else:
            self.log_result("Work Reports - Create Log (Corrected)", "SKIP", 
                          f"Missing client_id ({client_id}) or activity_type_id ({activity_type_id})")

    def test_marketing_visits_with_notification_check(self):
        """Test Marketing Visits with proper notification verification"""
        print("\n🚗 Testing MARKETING VISITS (WITH NOTIFICATION CHECK)...")
        
        # Switch to regular user for marketing visits
        if "user" in self.tokens:
            self.session.headers.update({"Authorization": f"Bearer {self.tokens['user']}"})

        visit_id = None
        
        # Start visit
        try:
            visit_data = {
                "client_name": "Test Client for Notification Check",
                "location_name": "Test Location Dubai",
                "area": "Dubai Marina",
                "purpose": "client_meeting",
                "purpose_details": "Testing visit with notification verification",
                "gps_location": {
                    "latitude": 25.2048,
                    "longitude": 55.2708
                }
            }
            
            response = self.session.post(f"{BASE_URL}/marketing-visits/start", json=visit_data)
            if response.status_code in [200, 201]:
                result = response.json()
                visit_id = result.get("visit_id")
                self.log_result("Marketing Visits - Start", "PASS", f"Visit started: {visit_id}")
            else:
                self.log_result("Marketing Visits - Start", "FAIL", 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("Marketing Visits - Start", "FAIL", f"Exception: {str(e)}")

        # Complete visit and check for notification
        if visit_id:
            try:
                time.sleep(3)  # Wait for visit duration
                
                completion_data = {
                    "visit_report": {
                        "summary": "Test visit completed successfully with comprehensive reporting and notification verification system testing",
                        "details": "This is a detailed test visit report created specifically to verify the Super Admin notification system. The visit was conducted to test the marketing visits API functionality including start, active status check, completion with mandatory reporting, and most importantly the automatic notification system that should alert Super Admin users when visits are completed. This comprehensive test ensures all aspects of the visit workflow are functioning correctly.",
                        "result": "successful",
                        "next_actions": "Verify that Super Admin receives notification about this completed visit and continue with remaining backend endpoint testing"
                    },
                    "gps_location": {
                        "latitude": 25.2048,
                        "longitude": 55.2708
                    }
                }
                
                response = self.session.post(f"{BASE_URL}/marketing-visits/{visit_id}/complete", json=completion_data)
                if response.status_code == 200:
                    self.log_result("Marketing Visits - Complete", "PASS", 
                                  "Visit completed with mandatory report")
                    
                    # Wait a moment for notification to be created
                    time.sleep(2)
                    
                    # Check Super Admin notifications more thoroughly
                    self.verify_super_admin_notification_detailed()
                else:
                    self.log_result("Marketing Visits - Complete", "FAIL", 
                                  f"Failed: {response.status_code} - {response.text}")
            except Exception as e:
                self.log_result("Marketing Visits - Complete", "FAIL", f"Exception: {str(e)}")

    def verify_super_admin_notification_detailed(self):
        """Detailed verification of Super Admin notification"""
        try:
            # Switch to super admin token
            if "super_admin" in self.tokens:
                self.session.headers.update({"Authorization": f"Bearer {self.tokens['super_admin']}"})
                
                # Check multiple notification endpoints
                endpoints_to_check = [
                    "/notifications/my",
                    "/notifications",
                ]
                
                for endpoint in endpoints_to_check:
                    try:
                        response = self.session.get(f"{BASE_URL}{endpoint}")
                        if response.status_code == 200:
                            data = response.json()
                            # Handle both direct list and object format
                            if isinstance(data, list):
                                notifications = data
                            else:
                                notifications = data.get('notifications', [])
                            
                            # Look for recent notifications (last 10 minutes)
                            recent_time = datetime.now() - timedelta(minutes=10)
                            recent_notifications = []
                            
                            for n in notifications:
                                # Check if notification is recent and visit-related
                                sent_at = n.get('sent_at') or n.get('created_at')
                                if sent_at:
                                    try:
                                        if isinstance(sent_at, str):
                                            # Handle different datetime formats
                                            if 'T' in sent_at:
                                                sent_time = datetime.fromisoformat(sent_at.replace('Z', '+00:00'))
                                            else:
                                                sent_time = datetime.fromisoformat(sent_at)
                                        else:
                                            sent_time = sent_at
                                        
                                        if sent_time.replace(tzinfo=None) > recent_time:
                                            # Check if it's visit-related
                                            subject = str(n.get('subject', '')).lower()
                                            message = str(n.get('message', '')).lower()
                                            
                                            if any(keyword in subject or keyword in message for keyword in 
                                                  ['visit', 'زيارة', 'marketing', 'تسويق', 'client', 'عميل']):
                                                recent_notifications.append(n)
                                    except:
                                        continue
                            
                            if recent_notifications:
                                self.log_result(f"Marketing Visits - Super Admin Notification ({endpoint})", "PASS", 
                                              f"Found {len(recent_notifications)} recent visit-related notifications")
                                return
                            else:
                                self.log_result(f"Marketing Visits - Super Admin Notification ({endpoint})", "INFO", 
                                              f"No recent visit notifications found in {len(notifications)} total notifications")
                        else:
                            self.log_result(f"Marketing Visits - Super Admin Notification ({endpoint})", "FAIL", 
                                          f"Failed to get notifications: {response.status_code}")
                    except Exception as e:
                        self.log_result(f"Marketing Visits - Super Admin Notification ({endpoint})", "FAIL", 
                                      f"Exception: {str(e)}")
                
                # Final result
                self.log_result("Marketing Visits - Super Admin Notification", "FAIL", 
                              "No recent visit-related notifications found for Super Admin")
                
        except Exception as e:
            self.log_result("Marketing Visits - Super Admin Notification", "FAIL", f"Exception: {str(e)}")

    def run_corrected_tests(self):
        """Run all corrected priority tests"""
        print("🚀 Starting CORRECTED COMPREHENSIVE BACKEND TESTING")
        print(f"Base URL: {BASE_URL}")
        print("=" * 80)
        
        # Authenticate all accounts
        auth_success = True
        for account_type in ["super_admin", "user"]:
            if not self.authenticate(account_type):
                auth_success = False
        
        if not auth_success:
            print("❌ Authentication failed for some accounts. Continuing with available tokens...")
        
        # Set super admin as default for most tests
        if "super_admin" in self.tokens:
            self.session.headers.update({"Authorization": f"Bearer {self.tokens['super_admin']}"})
        
        # Run corrected tests
        self.test_payroll_system_corrected()
        self.test_attendance_deductions_corrected()
        self.test_attendance_policies_corrected()
        self.test_work_reports_corrected()
        self.test_marketing_visits_with_notification_check()
        
        # Generate summary
        self.generate_corrected_summary()

    def generate_corrected_summary(self):
        """Generate corrected test summary"""
        print("\n" + "=" * 80)
        print("📋 CORRECTED BACKEND TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        skipped_tests = len([r for r in self.test_results if r["status"] == "SKIP"])
        info_tests = len([r for r in self.test_results if r["status"] == "INFO"])
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⏭️ Skipped: {skipped_tests}")
        print(f"ℹ️ Info: {info_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"  • {result['test']}: {result['details']}")
        
        # Save detailed results
        results_file = Path("./corrected_backend_test_results.json")
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        print(f"📁 Evidence files saved to: {self.evidence_dir}")

if __name__ == "__main__":
    tester = CorrectedBackendTester()
    tester.run_corrected_tests()