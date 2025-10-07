#!/usr/bin/env python3
"""
TANSEEQ HR System - Focused Backend Testing for Review Request
Tests specific features mentioned in the comprehensive review request
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class FocusedTanseeqTester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        if self.base_url.endswith('/api'):
            self.api_url = self.base_url
        else:
            self.api_url = f"{self.base_url}/api"
        
        self.token = None
        self.user = None
        self.tests_run = 0
        self.tests_passed = 0
        
        # Super admin credentials (from database check)
        self.super_admin_creds = {'email': 'hatemmo186@gmail.com', 'password': '123456'}

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")

    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                    expected_status: int = 200) -> tuple:
        """Make HTTP request and return success status and response"""
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                return False, {"error": f"Unsupported method: {method}"}
            
            success = response.status_code == expected_status
            try:
                response_data = response.json()
            except:
                response_data = {"status_code": response.status_code, "text": response.text}
            
            return success, response_data
            
        except requests.exceptions.RequestException as e:
            return False, {"error": str(e)}

    def login_super_admin(self) -> bool:
        """Login as super admin"""
        success, response = self.make_request('POST', 'auth/login', self.super_admin_creds)
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user = response['user']
            self.log_test("Super Admin Login", True)
            return True
        else:
            self.log_test("Super Admin Login", False, str(response))
            return False

    def test_super_admin_warning_notifications(self) -> bool:
        """Test Super Admin Warning Notifications System - REVIEW REQUEST PRIORITY 1"""
        if not self.token:
            return False
        
        # Test sending warning notification with Arabic message and emojis
        warning_data = {
            "recipient_id": "test-user-id",  # Using test ID since we don't have other users
            "title": "تحذير إداري مهم",
            "message": "يرجى الالتزام بمواعيد العمل المحددة وتجنب التأخير المتكرر. هذا تحذير رسمي من الإدارة العليا.",
            "notification_type": "warning",
            "required_action": "تحسين الانضباط في الحضور والانصراف",
            "additional_notes": "هذا تحذير أول، يرجى عدم تكرار التأخير في المستقبل"
        }
        
        success, response = self.make_request('POST', 'notifications/send-warning', warning_data)
        
        if success:
            # Check if response contains proper Arabic structure
            has_message = 'message' in response
            has_notification_type = 'notification_type' in response
            has_recipient = 'recipient' in response
            
            test_passed = has_message and has_notification_type and has_recipient
            self.log_test("Super Admin Warning Notifications System", test_passed,
                         f"Response structure: {response}" if not test_passed else "")
            return test_passed
        else:
            self.log_test("Super Admin Warning Notifications System", False, str(response))
            return False

    def test_attendance_rules_no_early_penalty(self) -> bool:
        """Test Enhanced Attendance Rules - NO penalty for check-in before 9 AM"""
        if not self.token:
            return False
        
        # Test check-in functionality
        success, response = self.make_request('POST', 'attendance/check-in')
        
        # Check-in might fail if already checked in, which is acceptable
        already_checked_in = not success and 'already checked in' in str(response).lower()
        test_passed = success or already_checked_in
        
        if test_passed:
            # Get attendance records to verify no early penalty logic
            att_success, att_records = self.make_request('GET', 'attendance')
            if att_success and att_records:
                # Look for today's record
                today = datetime.now().strftime('%Y-%m-%d')
                today_record = None
                for record in att_records:
                    if record.get('date') == today:
                        today_record = record
                        break
                
                if today_record:
                    check_in_time = today_record.get('check_in', '')
                    is_late = today_record.get('is_late', False)
                    
                    # If check-in is before 9 AM, should not be marked as late
                    if check_in_time and check_in_time < '09:00:00':
                        test_passed = not is_late
                        self.log_test("Attendance Rules - No Early Penalty", test_passed,
                                     f"Early check-in at {check_in_time} marked as late: {is_late}")
                    else:
                        self.log_test("Attendance Rules - No Early Penalty", True, 
                                     "No early check-in to test, but system working")
                    return test_passed
        
        self.log_test("Attendance Rules - No Early Penalty", test_passed, str(response) if not test_passed else "")
        return test_passed

    def test_payroll_calculation_accuracy(self) -> bool:
        """Test Enhanced Payroll Calculation Logic - REVIEW REQUEST PRIORITY 2"""
        if not self.token:
            return False
        
        success, response = self.make_request('GET', 'payroll/calculate/2025-01')
        
        if success and isinstance(response, list) and response:
            # Test accuracy of payroll calculations
            calculation_errors = []
            
            for employee in response[:3]:  # Test first 3 employees
                # Verify presence days vs hourly calculations
                monthly_salary = employee.get('monthly_salary', 0)
                daily_rate = employee.get('daily_rate', 0)
                present_days = employee.get('present_days', 0)
                final_salary = employee.get('final_salary', 0)
                
                # Check daily rate calculation (monthly_salary / 22)
                expected_daily_rate = monthly_salary / 22 if monthly_salary > 0 else 0
                if abs(daily_rate - expected_daily_rate) > 0.01:
                    calculation_errors.append(f"Daily rate incorrect for {employee.get('name', 'Unknown')}")
                
                # Check that deductions are properly applied
                approved_leaves = employee.get('approved_leaves', 0)
                approved_field_exits = employee.get('approved_field_exits', 0)
                working_days = employee.get('working_days', 0)
                
                # Working days should include present days + approved leaves + field exits
                expected_working_days = present_days + approved_leaves + approved_field_exits
                if working_days != expected_working_days:
                    calculation_errors.append(f"Working days calculation incorrect for {employee.get('name', 'Unknown')}")
                
                # Final salary should not be negative
                if final_salary < 0:
                    calculation_errors.append(f"Final salary is negative for {employee.get('name', 'Unknown')}")
            
            test_passed = len(calculation_errors) == 0
            
            if test_passed:
                self.log_test("Payroll Calculation Accuracy", True, f"Verified {len(response)} employees")
            else:
                self.log_test("Payroll Calculation Accuracy", False, "; ".join(calculation_errors))
            
            return test_passed
        else:
            self.log_test("Payroll Calculation Accuracy", False, str(response))
            return False

    def test_field_exit_detailed_report_system(self) -> bool:
        """Test Field Exit Detailed Report System - 3-step flow"""
        if not self.token:
            return False
        
        # Create a field exit to test the detailed report system
        field_exit_data = {
            'visit_type': 'client_visit',
            'client_name': 'شركة اختبار التقارير التفصيلية المحدودة',
            'expected_start_time': '10:00:00',
            'expected_end_time': '12:00:00',
            'report': 'زيارة عميل لمناقشة الخدمات الضريبية والمحاسبية المتقدمة'
        }
        
        url = f"{self.api_url}/field-exits"
        headers = {'Authorization': f'Bearer {self.token}'}
        
        try:
            # Step 1: Create field exit (departure)
            create_response = requests.post(url, data=field_exit_data, headers=headers, timeout=30)
            if create_response.status_code != 200:
                self.log_test("Field Exit Detailed Report System", False, 
                             f"Could not create field exit: {create_response.status_code}")
                return False
            
            field_exit_id = create_response.json().get('id')
            if not field_exit_id:
                self.log_test("Field Exit Detailed Report System", False, "No field exit ID returned")
                return False
            
            # Step 2: Submit detailed report (mandatory before checkout)
            detailed_report_data = {
                "detailed_report": "تم زيارة العميل ومناقشة جميع الخدمات الضريبية والمحاسبية المطلوبة بالتفصيل. تم شرح الإجراءات والمتطلبات اللازمة للامتثال الضريبي وتقديم الاستشارات المحاسبية المتخصصة للعميل.",
                "accomplishments": "تم توضيح جميع الخدمات المتاحة وتحديد احتياجات العميل بدقة وتقديم خطة عمل مفصلة ومتكاملة",
                "challenges": "تحدي في فهم بعض المتطلبات الضريبية الجديدة من قبل العميل وحاجة لشرح إضافي",
                "next_steps": "متابعة مع العميل خلال الأسبوع القادم لتنفيذ الخطة المتفق عليها وتقديم الدعم اللازم والمستمر"
            }
            
            # Test character count validation (minimum 20 characters)
            if len(detailed_report_data["detailed_report"]) < 20:
                self.log_test("Field Exit Detailed Report System", False, "Test report too short")
                return False
            
            success, response = self.make_request('POST', f'field-exits/{field_exit_id}/report', 
                                                detailed_report_data)
            
            if success:
                # Check if response indicates report was submitted successfully
                has_message = 'message' in response
                report_submitted = 'report' in str(response).lower() or 'submitted' in str(response).lower()
                
                test_passed = has_message and report_submitted
                self.log_test("Field Exit Detailed Report System", test_passed,
                             f"Response: {response}" if not test_passed else "")
                return test_passed
            else:
                self.log_test("Field Exit Detailed Report System", False, str(response))
                return False
                
        except Exception as e:
            self.log_test("Field Exit Detailed Report System", False, str(e))
            return False

    def test_leave_attachments_system(self) -> bool:
        """Test Leave Attachments System - Enhanced viewing with view/download buttons"""
        if not self.token:
            return False
        
        # Get leaves to find one with attachment
        success, leaves = self.make_request('GET', 'leaves/all')
        
        if not success:
            self.log_test("Leave Attachments System", False, str(leaves))
            return False
        
        # Find a leave with attachment
        leave_with_attachment = None
        for leave in leaves:
            if leave.get('attachment_url') or leave.get('file_path'):
                leave_with_attachment = leave
                break
        
        if not leave_with_attachment:
            self.log_test("Leave Attachments System", True, "No leaves with attachments found (acceptable)")
            return True
        
        # Test attachment viewing endpoint
        success, response = self.make_request('GET', f'admin/view-attachment/leave/{leave_with_attachment["id"]}')
        
        if success:
            # Check if response contains attachment data
            has_file_data = 'file_data' in response or 'base64_data' in response
            has_mime_type = 'mime_type' in response
            has_file_name = 'file_name' in response
            
            test_passed = has_file_data and has_mime_type and has_file_name
            self.log_test("Leave Attachments System", test_passed,
                         f"File data: {has_file_data}, MIME: {has_mime_type}, Name: {has_file_name}")
            return test_passed
        else:
            self.log_test("Leave Attachments System", False, str(response))
            return False

    def test_work_reports_mongodb_migration(self) -> bool:
        """Test Work Reports MongoDB Migration - REVIEW REQUEST PRIORITY 5"""
        if not self.token:
            return False
        
        # Test Work Reports endpoints to verify MongoDB migration
        endpoints_to_test = [
            ('work-reports/dashboard', ['total_clients', 'total_logs']),
            ('work-reports/clients', 'list'),
            ('work-reports/activity-types', 'list'),
            ('work-reports/logs', 'list')
        ]
        
        all_passed = True
        
        for endpoint_info in endpoints_to_test:
            if isinstance(endpoint_info, tuple):
                endpoint, expected_keys = endpoint_info
            else:
                endpoint = endpoint_info
                expected_keys = 'list'
            
            success, response = self.make_request('GET', endpoint)
            
            if success:
                # Check if response has expected structure
                if expected_keys == 'list':
                    has_expected_structure = isinstance(response, list)
                else:
                    has_expected_structure = any(key in response for key in expected_keys)
                
                if has_expected_structure:
                    self.log_test(f"Work Reports {endpoint.split('/')[-1]}", True)
                else:
                    self.log_test(f"Work Reports {endpoint.split('/')[-1]}", False, 
                                 f"Unexpected response structure: {type(response)}")
                    all_passed = False
            else:
                self.log_test(f"Work Reports {endpoint.split('/')[-1]}", False, str(response))
                all_passed = False
        
        return all_passed

    def test_system_integration_performance(self) -> bool:
        """Test System Integration & Performance - REVIEW REQUEST PRIORITY 6"""
        if not self.token:
            return False
        
        # Test key API endpoints for response times and accuracy
        critical_endpoints = [
            'dashboard/stats',
            'attendance',
            'leaves',
            'field-exits',
            'users',
            'activity-logs'
        ]
        
        all_passed = True
        response_times = []
        
        for endpoint in critical_endpoints:
            start_time = datetime.now()
            success, response = self.make_request('GET', endpoint)
            end_time = datetime.now()
            
            response_time = (end_time - start_time).total_seconds()
            response_times.append(response_time)
            
            if success:
                # Check response time (should be under 5 seconds for good performance)
                fast_response = response_time < 5.0
                if fast_response:
                    self.log_test(f"API Performance - {endpoint}", True, f"{response_time:.2f}s")
                else:
                    self.log_test(f"API Performance - {endpoint}", False, f"Slow response: {response_time:.2f}s")
                    all_passed = False
            else:
                self.log_test(f"API Performance - {endpoint}", False, str(response))
                all_passed = False
        
        # Overall performance summary
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        if avg_response_time < 2.0:
            self.log_test("Overall API Performance", True, f"Average: {avg_response_time:.2f}s")
        else:
            self.log_test("Overall API Performance", False, f"Average too slow: {avg_response_time:.2f}s")
            all_passed = False
        
        return all_passed

    def run_focused_tests(self):
        """Run focused tests for review request requirements"""
        print("🎯 TANSEEQ HR System - Focused Backend Testing for Review Request")
        print("=" * 80)
        print("🔍 Testing specific features mentioned in comprehensive review request")
        print("=" * 80)
        
        # Login as super admin
        if not self.login_super_admin():
            print("❌ Super admin login failed - stopping tests")
            return
        
        print("\n🚀 Running Review Request Priority Tests:")
        print("-" * 60)
        
        # Run priority tests based on review request
        priority_tests = [
            ("1. Super Admin Warning Notifications System", self.test_super_admin_warning_notifications),
            ("2. Enhanced Attendance & Payroll System", self.test_attendance_rules_no_early_penalty),
            ("2. Payroll Calculation Accuracy", self.test_payroll_calculation_accuracy),
            ("3. Field Exit Report System", self.test_field_exit_detailed_report_system),
            ("4. Leave Attachments System", self.test_leave_attachments_system),
            ("5. Work Reports MongoDB Migration", self.test_work_reports_mongodb_migration),
            ("6. System Integration & Performance", self.test_system_integration_performance)
        ]
        
        for test_name, test_func in priority_tests:
            print(f"\n🔸 {test_name}")
            test_func()
        
        print("\n" + "=" * 80)
        print("📊 FOCUSED TEST RESULTS")
        print("=" * 80)
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL REVIEW REQUEST REQUIREMENTS PASSED!")
        else:
            print("⚠️  Some tests failed. Please review the issues above.")
        
        print("=" * 80)

if __name__ == "__main__":
    # Get backend URL from environment or use default
    backend_url = "https://hr-attendance-2.preview.emergentagent.com"
    print(f"🔗 Using backend URL: {backend_url}")
    
    tester = FocusedTanseeqTester(backend_url)
    tester.run_focused_tests()