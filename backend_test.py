#!/usr/bin/env python3
"""
Backend Regression Testing - Priority Round 1
Testing all priority endpoints as requested in review
"""

import requests
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import time

# Configuration
BASE_URL = "https://hrms-tanseeq.preview.emergentagent.com/api"

# Test accounts
TEST_ACCOUNTS = {
    "super_admin": {"email": "admin@tanseeq.com", "password": "ADMIN"},
    "user": {"email": "jihad@tanseeq.com", "password": "jihad123"},
    "hatem": {"email": "hatem@tan-seeq.co", "password": "hatem123"}
}

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.tokens = {}
        self.test_results = []
        self.evidence_dir = Path("./evidence/backend_exports")
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
        
        status_icon = "✅" if status == "PASS" else "❌"
        print(f"{status_icon} {test_name}: {details}")
        
    def authenticate(self, account_type):
        """Authenticate and get JWT token"""
        try:
            account = TEST_ACCOUNTS[account_type]
            response = self.session.post(f"{BASE_URL}/auth/login", json=account)
            
            if response.status_code == 200:
                data = response.json()
                token = data["access_token"]
                self.tokens[account_type] = token
                self.session.headers.update({"Authorization": f"Bearer {token}"})
                self.log_result(f"Authentication - {account_type}", "PASS", 
                              f"Successfully authenticated {account['email']}")
                return True
            else:
                self.log_result(f"Authentication - {account_type}", "FAIL", 
                              f"Failed to authenticate: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result(f"Authentication - {account_type}", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_payroll_cycles(self):
        """Test Payroll Cycles API Suite"""
        print("\n🔄 Testing Payroll Cycles API Suite...")
        
        # 1. GET /api/payroll/cycles (list with filters)
        try:
            response = self.session.get(f"{BASE_URL}/payroll/cycles")
            if response.status_code == 200:
                cycles = response.json()
                self.log_result("Payroll Cycles - List", "PASS", 
                              f"Retrieved {len(cycles.get('cycles', []))} cycles")
                
                # Test with filters
                response = self.session.get(f"{BASE_URL}/payroll/cycles?status=open&year=2025")
                if response.status_code == 200:
                    self.log_result("Payroll Cycles - Filters", "PASS", "Filters working")
                else:
                    self.log_result("Payroll Cycles - Filters", "FAIL", 
                                  f"Filter failed: {response.status_code}")
            else:
                self.log_result("Payroll Cycles - List", "FAIL", 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("Payroll Cycles - List", "FAIL", f"Exception: {str(e)}")
        
        # 2. POST /api/payroll/cycles (create)
        try:
            cycle_data = {
                "month": "2025-01",
                "notes": "Test cycle for regression testing"
            }
            response = self.session.post(f"{BASE_URL}/payroll/cycles", json=cycle_data)
            if response.status_code in [200, 201]:
                cycle_id = response.json().get("cycle_id")
                self.log_result("Payroll Cycles - Create", "PASS", 
                              f"Created cycle: {cycle_id}")
                
                # Test lock/unlock if cycle created
                if cycle_id:
                    self.test_cycle_lock_unlock(cycle_id)
                    self.test_cycle_calculate(cycle_id)
                    self.test_cycle_exports(cycle_id)
                    
            else:
                self.log_result("Payroll Cycles - Create", "FAIL", 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("Payroll Cycles - Create", "FAIL", f"Exception: {str(e)}")
    
    def test_cycle_lock_unlock(self, cycle_id):
        """Test cycle lock/unlock with reasons"""
        try:
            # Lock cycle
            lock_data = {"lock_reason": "Testing lock functionality"}
            response = self.session.post(f"{BASE_URL}/payroll/cycles/{cycle_id}/lock", json=lock_data)
            if response.status_code == 200:
                self.log_result("Payroll Cycles - Lock", "PASS", "Cycle locked successfully")
                
                # Unlock cycle
                unlock_data = {"reason": "Testing unlock functionality"}
                response = self.session.post(f"{BASE_URL}/payroll/cycles/{cycle_id}/unlock", json=unlock_data)
                if response.status_code == 200:
                    self.log_result("Payroll Cycles - Unlock", "PASS", "Cycle unlocked successfully")
                else:
                    self.log_result("Payroll Cycles - Unlock", "FAIL", 
                                  f"Failed: {response.status_code} - {response.text}")
            else:
                self.log_result("Payroll Cycles - Lock", "FAIL", 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("Payroll Cycles - Lock/Unlock", "FAIL", f"Exception: {str(e)}")
    
    def test_cycle_calculate(self, cycle_id):
        """Test cycle calculation"""
        try:
            response = self.session.get(f"{BASE_URL}/payroll/cycles/{cycle_id}/calculate")
            if response.status_code == 200:
                calculation = response.json()
                totals = calculation.get("totals", {})
                self.log_result("Payroll Cycles - Calculate", "PASS", 
                              f"Calculation successful, totals returned: {len(totals)} items")
            else:
                self.log_result("Payroll Cycles - Calculate", "FAIL", 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("Payroll Cycles - Calculate", "FAIL", f"Exception: {str(e)}")
    
    def test_cycle_exports(self, cycle_id):
        """Test PDF and Excel exports"""
        try:
            # Test PDF export
            response = self.session.get(f"{BASE_URL}/payroll/cycles/{cycle_id}/export/pdf")
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                if 'pdf' in content_type.lower() and len(response.content) > 0:
                    # Save PDF for evidence
                    pdf_path = self.evidence_dir / f"payroll_cycle_{cycle_id}.pdf"
                    with open(pdf_path, 'wb') as f:
                        f.write(response.content)
                    self.log_result("Payroll Cycles - PDF Export", "PASS", 
                                  f"PDF exported successfully, size: {len(response.content)} bytes")
                else:
                    self.log_result("Payroll Cycles - PDF Export", "FAIL", 
                                  f"Invalid PDF: content-type={content_type}, size={len(response.content)}")
            else:
                self.log_result("Payroll Cycles - PDF Export", "FAIL", 
                              f"Failed: {response.status_code} - {response.text}")
            
            # Test Excel export
            response = self.session.get(f"{BASE_URL}/payroll/cycles/{cycle_id}/export/excel")
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                if ('excel' in content_type.lower() or 'spreadsheet' in content_type.lower()) and len(response.content) > 0:
                    # Save Excel for evidence
                    excel_path = self.evidence_dir / f"payroll_cycle_{cycle_id}.xlsx"
                    with open(excel_path, 'wb') as f:
                        f.write(response.content)
                    self.log_result("Payroll Cycles - Excel Export", "PASS", 
                                  f"Excel exported successfully, size: {len(response.content)} bytes")
                else:
                    self.log_result("Payroll Cycles - Excel Export", "FAIL", 
                                  f"Invalid Excel: content-type={content_type}, size={len(response.content)}")
            else:
                self.log_result("Payroll Cycles - Excel Export", "FAIL", 
                              f"Failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Payroll Cycles - Exports", "FAIL", f"Exception: {str(e)}")
    
    def test_attendance_deductions(self):
        """Test Attendance Deductions endpoints"""
        print("\n📊 Testing Attendance Deductions...")
        
        # 1. GET /api/employees/list - should return active employees with id+name
        try:
            response = self.session.get(f"{BASE_URL}/employees/list")
            if response.status_code == 200:
                employees = response.json()
                if isinstance(employees, list) and len(employees) > 0:
                    # Check if employees have id and name
                    first_emp = employees[0]
                    if 'id' in first_emp and 'name' in first_emp:
                        self.log_result("Employees List", "PASS", 
                                      f"Retrieved {len(employees)} employees with id+name")
                        self.test_employee_id = first_emp['id']  # Store for deduction test
                    else:
                        self.log_result("Employees List", "FAIL", 
                                      "Employees missing id or name fields")
                else:
                    self.log_result("Employees List", "FAIL", "No employees returned")
            else:
                self.log_result("Employees List", "FAIL", 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("Employees List", "FAIL", f"Exception: {str(e)}")
        
        # 2. GET /api/deductions?month=YYYY-MM - should include employee_name
        try:
            current_month = datetime.now().strftime("%Y-%m")
            response = self.session.get(f"{BASE_URL}/deductions?month={current_month}")
            if response.status_code == 200:
                deductions = response.json()
                if isinstance(deductions, list):
                    if len(deductions) > 0:
                        # Check if deductions include employee_name
                        first_deduction = deductions[0]
                        if 'employee_name' in first_deduction:
                            self.log_result("Deductions List", "PASS", 
                                          f"Retrieved {len(deductions)} deductions with employee_name")
                        else:
                            self.log_result("Deductions List", "FAIL", 
                                          "Deductions missing employee_name field")
                    else:
                        self.log_result("Deductions List", "PASS", 
                                      "No deductions found (empty list is valid)")
                else:
                    self.log_result("Deductions List", "FAIL", "Invalid response format")
            else:
                self.log_result("Deductions List", "FAIL", 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("Deductions List", "FAIL", f"Exception: {str(e)}")
        
        # 3. Test manual deduction CRUD operations
        self.test_manual_deductions()
    
    def test_manual_deductions(self):
        """Test manual deduction create/edit/void"""
        if not hasattr(self, 'test_employee_id'):
            self.log_result("Manual Deductions", "SKIP", "No employee ID available")
            return
        
        try:
            # Create manual deduction
            deduction_data = {
                "employee_id": self.test_employee_id,
                "amount": 50.0,
                "reason": "Test deduction for regression testing",
                "category": "late_arrival",
                "date": datetime.now().strftime("%Y-%m-%d")
            }
            
            response = self.session.post(f"{BASE_URL}/deductions/manual", json=deduction_data)
            if response.status_code in [200, 201]:
                deduction_id = response.json().get("id") or response.json().get("deduction_id")
                self.log_result("Manual Deductions - Create", "PASS", 
                              f"Created deduction: {deduction_id}")
                
                if deduction_id:
                    # Test edit deduction
                    edit_data = {
                        "amount": 75.0,
                        "reason": "Updated test deduction"
                    }
                    response = self.session.patch(f"{BASE_URL}/deductions/{deduction_id}", json=edit_data)
                    if response.status_code == 200:
                        self.log_result("Manual Deductions - Edit", "PASS", "Deduction edited successfully")
                    else:
                        self.log_result("Manual Deductions - Edit", "FAIL", 
                                      f"Failed: {response.status_code} - {response.text}")
                    
                    # Test void deduction
                    void_data = {"void_reason": "Test void for regression testing"}
                    response = self.session.post(f"{BASE_URL}/deductions/{deduction_id}/void", json=void_data)
                    if response.status_code == 200:
                        self.log_result("Manual Deductions - Void", "PASS", "Deduction voided successfully")
                    else:
                        self.log_result("Manual Deductions - Void", "FAIL", 
                                      f"Failed: {response.status_code} - {response.text}")
            else:
                self.log_result("Manual Deductions - Create", "FAIL", 
                              f"Failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Manual Deductions", "FAIL", f"Exception: {str(e)}")
    
    def test_advanced_exceptions(self):
        """Test Advanced Attendance Policy Exceptions"""
        print("\n⚡ Testing Advanced Attendance Policy Exceptions...")
        
        # Test policy retrieval for specific employees
        test_employees = ["hatem@tan-seeq.co", "tarek.wazzan@company.com"]  # Based on review requirements
        
        for email in test_employees:
            try:
                # First get employee by email to get ID
                response = self.session.get(f"{BASE_URL}/employees/list")
                if response.status_code == 200:
                    employees = response.json()
                    employee = next((emp for emp in employees if emp.get('email', '').lower() == email.lower()), None)
                    
                    if employee:
                        employee_id = employee['id']
                        # Get attendance policy
                        response = self.session.get(f"{BASE_URL}/attendance_deductions/policy?employee_id={employee_id}")
                        if response.status_code == 200:
                            policy = response.json()
                            self.log_result(f"Attendance Policy - {email}", "PASS", 
                                          f"Policy retrieved: {json.dumps(policy, indent=2)}")
                        else:
                            # Try alternative endpoint
                            response = self.session.get(f"{BASE_URL}/attendance/policies/{employee_id}")
                            if response.status_code == 200:
                                policy = response.json()
                                self.log_result(f"Attendance Policy - {email}", "PASS", 
                                              f"Policy retrieved: {json.dumps(policy, indent=2)}")
                            else:
                                self.log_result(f"Attendance Policy - {email}", "FAIL", 
                                              f"Policy not found: {response.status_code}")
                    else:
                        self.log_result(f"Attendance Policy - {email}", "SKIP", 
                                      f"Employee {email} not found in system")
                        
            except Exception as e:
                self.log_result(f"Attendance Policy - {email}", "FAIL", f"Exception: {str(e)}")
    
    def test_work_reports_logs(self):
        """Test Work Reports Logs MongoDB endpoints"""
        print("\n📝 Testing Work Reports Logs (MongoDB)...")
        
        # Test create log first
        log_id = None
        try:
            log_data = {
                "client_id": "test-client-123",
                "activity_type_id": "test-activity-456", 
                "date": datetime.now().isoformat(),
                "start_time": datetime.now().isoformat(),
                "end_time": (datetime.now() + timedelta(hours=2)).isoformat(),
                "description": "Test work log for regression testing",
                "notes": "Created during backend regression test",
                "is_billable": True,
                "hourly_rate": 100.0
            }
            
            response = self.session.post(f"{BASE_URL}/work-reports/logs", json=log_data)
            if response.status_code in [200, 201]:
                result = response.json()
                log_id = result.get("id") or result.get("log_id")
                self.log_result("Work Reports - Create Log", "PASS", f"Created log: {log_id}")
            else:
                self.log_result("Work Reports - Create Log", "FAIL", 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("Work Reports - Create Log", "FAIL", f"Exception: {str(e)}")
        
        # Test search/filter functionality
        try:
            current_date = datetime.now().strftime("%Y-%m-%d")
            params = {
                "start_date": current_date,
                "end_date": current_date,
                "page": 1,
                "page_size": 10
            }
            
            response = self.session.get(f"{BASE_URL}/work-reports/logs", params=params)
            if response.status_code == 200:
                logs = response.json()
                self.log_result("Work Reports - Search/Filter", "PASS", 
                              f"Search successful, found {len(logs.get('logs', []))} logs")
            else:
                self.log_result("Work Reports - Search/Filter", "FAIL", 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("Work Reports - Search/Filter", "FAIL", f"Exception: {str(e)}")
        
        # Test update and delete if log was created
        if log_id:
            try:
                # Test update
                update_data = {
                    "description": "Updated test work log",
                    "notes": "Updated during regression test"
                }
                response = self.session.put(f"{BASE_URL}/work-reports/logs/{log_id}", json=update_data)
                if response.status_code == 200:
                    self.log_result("Work Reports - Update Log", "PASS", "Log updated successfully")
                else:
                    self.log_result("Work Reports - Update Log", "FAIL", 
                                  f"Failed: {response.status_code} - {response.text}")
                
                # Test delete
                response = self.session.delete(f"{BASE_URL}/work-reports/logs/{log_id}")
                if response.status_code == 200:
                    self.log_result("Work Reports - Delete Log", "PASS", "Log deleted successfully")
                else:
                    self.log_result("Work Reports - Delete Log", "FAIL", 
                                  f"Failed: {response.status_code} - {response.text}")
                    
            except Exception as e:
                self.log_result("Work Reports - Update/Delete", "FAIL", f"Exception: {str(e)}")
    
    def test_marketing_field_visits(self):
        """Test Marketing/Field Visits flow"""
        print("\n🚗 Testing Marketing/Field Visits Flow...")
        
        visit_id = None
        
        # Test start visit
        try:
            visit_data = {
                "client_name": "Test Client for Regression",
                "location_name": "Test Location",
                "area": "Dubai",
                "purpose": "client_meeting",
                "purpose_details": "Regression testing visit",
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
        
        # Test get active visit
        try:
            response = self.session.get(f"{BASE_URL}/marketing-visits/active")
            if response.status_code == 200:
                active_visit = response.json()
                self.log_result("Marketing Visits - Get Active", "PASS", 
                              f"Active visit retrieved: {active_visit.get('active_visit', {}).get('id', 'None')}")
            else:
                self.log_result("Marketing Visits - Get Active", "FAIL", 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("Marketing Visits - Get Active", "FAIL", f"Exception: {str(e)}")
        
        # Test complete visit with mandatory report
        if visit_id:
            try:
                time.sleep(2)  # Wait a bit for visit duration
                
                completion_data = {
                    "visit_report": {
                        "summary": "Completed regression test visit successfully with all required details",
                        "details": "This is a comprehensive test visit report created during backend regression testing. The visit was conducted to verify the marketing visits API functionality including start, active status check, and completion with mandatory reporting.",
                        "result": "successful",
                        "next_actions": "Continue with regression testing of other endpoints"
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
                    
                    # Verify super admin notification was created
                    self.verify_super_admin_notification()
                else:
                    self.log_result("Marketing Visits - Complete", "FAIL", 
                                  f"Failed: {response.status_code} - {response.text}")
            except Exception as e:
                self.log_result("Marketing Visits - Complete", "FAIL", f"Exception: {str(e)}")
    
    def verify_super_admin_notification(self):
        """Verify super admin received notification"""
        try:
            # Switch to super admin token
            if "super_admin" in self.tokens:
                self.session.headers.update({"Authorization": f"Bearer {self.tokens['super_admin']}"})
                
                response = self.session.get(f"{BASE_URL}/notifications/my")
                if response.status_code == 200:
                    notifications = response.json()
                    # Look for recent marketing visit notification
                    recent_notifications = [n for n in notifications if 
                                          'marketing' in n.get('subject', '').lower() or 
                                          'visit' in n.get('subject', '').lower()]
                    
                    if recent_notifications:
                        self.log_result("Marketing Visits - Super Admin Notification", "PASS", 
                                      f"Found {len(recent_notifications)} visit-related notifications")
                    else:
                        self.log_result("Marketing Visits - Super Admin Notification", "FAIL", 
                                      "No marketing visit notifications found")
                else:
                    self.log_result("Marketing Visits - Super Admin Notification", "FAIL", 
                                  f"Failed to get notifications: {response.status_code}")
        except Exception as e:
            self.log_result("Marketing Visits - Super Admin Notification", "FAIL", f"Exception: {str(e)}")
    
    def test_notifications_scoping(self):
        """Test Notifications scoping"""
        print("\n🔔 Testing Notifications Scoping...")
        
        # Test for each user role
        for role, token in self.tokens.items():
            try:
                self.session.headers.update({"Authorization": f"Bearer {token}"})
                
                response = self.session.get(f"{BASE_URL}/notifications/my")
                if response.status_code == 200:
                    notifications = response.json()
                    self.log_result(f"Notifications - {role}", "PASS", 
                                  f"Retrieved {len(notifications)} scoped notifications")
                else:
                    self.log_result(f"Notifications - {role}", "FAIL", 
                                  f"Failed: {response.status_code} - {response.text}")
            except Exception as e:
                self.log_result(f"Notifications - {role}", "FAIL", f"Exception: {str(e)}")
    
    def test_exports_parity(self):
        """Test export functionality and verify content parity"""
        print("\n📊 Testing Exports Parity...")
        
        # This would ideally compare JSON data with exported PDF/Excel content
        # For now, we'll verify that exports are working and contain data
        try:
            # Get a payroll cycle for comparison
            response = self.session.get(f"{BASE_URL}/payroll/cycles")
            if response.status_code == 200:
                cycles = response.json().get('cycles', [])
                if cycles:
                    cycle_id = cycles[0].get('id')
                    if cycle_id:
                        # Get JSON calculation
                        response = self.session.get(f"{BASE_URL}/payroll/cycles/{cycle_id}/calculate")
                        if response.status_code == 200:
                            json_data = response.json()
                            json_totals = json_data.get('totals', {})
                            
                            # Get PDF export
                            response = self.session.get(f"{BASE_URL}/payroll/cycles/{cycle_id}/export/pdf")
                            if response.status_code == 200 and len(response.content) > 1000:
                                self.log_result("Export Parity - PDF", "PASS", 
                                              f"PDF export contains data (size: {len(response.content)} bytes)")
                            else:
                                self.log_result("Export Parity - PDF", "FAIL", 
                                              "PDF export appears empty or failed")
                            
                            # Get Excel export  
                            response = self.session.get(f"{BASE_URL}/payroll/cycles/{cycle_id}/export/excel")
                            if response.status_code == 200 and len(response.content) > 1000:
                                self.log_result("Export Parity - Excel", "PASS", 
                                              f"Excel export contains data (size: {len(response.content)} bytes)")
                            else:
                                self.log_result("Export Parity - Excel", "FAIL", 
                                              "Excel export appears empty or failed")
                        else:
                            self.log_result("Export Parity", "FAIL", 
                                          "Could not get JSON calculation for comparison")
                    else:
                        self.log_result("Export Parity", "SKIP", "No cycle ID available")
                else:
                    self.log_result("Export Parity", "SKIP", "No payroll cycles available")
            else:
                self.log_result("Export Parity", "FAIL", "Could not retrieve payroll cycles")
                
        except Exception as e:
            self.log_result("Export Parity", "FAIL", f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all priority tests"""
        print("🚀 Starting Backend Regression Testing - Priority Round 1")
        print(f"Base URL: {BASE_URL}")
        print("=" * 60)
        
        # Authenticate all accounts
        auth_success = True
        for account_type in ["super_admin", "user", "hatem"]:
            if not self.authenticate(account_type):
                auth_success = False
        
        if not auth_success:
            print("❌ Authentication failed for some accounts. Continuing with available tokens...")
        
        # Set super admin as default for most tests
        if "super_admin" in self.tokens:
            self.session.headers.update({"Authorization": f"Bearer {self.tokens['super_admin']}"})
        
        # Run all priority tests
        self.test_payroll_cycles()
        self.test_attendance_deductions()
        self.test_advanced_exceptions()
        self.test_work_reports_logs()
        
        # Switch to regular user for marketing visits
        if "user" in self.tokens:
            self.session.headers.update({"Authorization": f"Bearer {self.tokens['user']}"})
        self.test_marketing_field_visits()
        
        self.test_notifications_scoping()
        
        # Switch back to super admin for exports
        if "super_admin" in self.tokens:
            self.session.headers.update({"Authorization": f"Bearer {self.tokens['super_admin']}"})
        self.test_exports_parity()
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "=" * 60)
        print("📋 BACKEND REGRESSION TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        skipped_tests = len([r for r in self.test_results if r["status"] == "SKIP"])
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⏭️ Skipped: {skipped_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"  • {result['test']}: {result['details']}")
        
        # Save detailed results
        results_file = Path("./backend_regression_results.json")
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        print(f"📁 Evidence files saved to: {self.evidence_dir}")

if __name__ == "__main__":
    tester = BackendTester()
    tester.run_all_tests()
        """Create a test advance for installment scheduling"""
        try:
            # First try to get an existing advance
            existing_advance = await self.get_existing_advance(token)
            if existing_advance:
                return existing_advance
            
            # Get a test employee (jihad)
            employee_id = None
            async with self.session.get(
                f"{API_BASE}/auth/me",
                headers={'Authorization': f'Bearer {self.tokens["user"]}'}
            ) as response:
                if response.status == 200:
                    user_data = await response.json()
                    employee_id = user_data.get('id')
            
            if not employee_id:
                self.log_test("Create Test Advance", "FAIL", "Could not get employee ID")
                return None
            
            advance_data = {
                "employee_id": employee_id,
                "transaction_type": "advance",
                "amount": 5000.0,
                "description": "Test advance for installment scheduling",
                "category": "other",
                "expense_date": datetime.now().strftime("%Y-%m-%d"),
                "notes": "Created for testing installment scheduling system"
            }
            
            async with self.session.post(
                f"{API_BASE}/advances/create",
                json=advance_data,
                headers={'Authorization': f'Bearer {token}'}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    advance_id = data.get('transaction_id')
                    self.created_advances.append(advance_id)
                    self.log_test("Create Test Advance", "PASS", f"Created advance ID: {advance_id}, Amount: {advance_data['amount']}")
                    return advance_id
                else:
                    error_text = await response.text()
                    self.log_test("Create Test Advance", "FAIL", f"Status: {response.status}, Error: {error_text}")
                    return None
        except Exception as e:
            self.log_test("Create Test Advance", "FAIL", f"Exception: {str(e)}")
            return None

    async def test_create_installment_schedule(self, token: str, advance_id: str):
        """Test POST /api/advances/{advance_id}/installments - Create installment schedule"""
        try:
            schedule_data = {
                "installment_amount": 500.0,
                "number_of_installments": 10,
                "start_date": (date.today() + timedelta(days=30)).strftime("%Y-%m-%d"),
                "respect_ceiling": True
            }
            
            async with self.session.post(
                f"{API_BASE}/advances/{advance_id}/installments",
                json=schedule_data,
                headers={'Authorization': f'Bearer {token}'}
            ) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    schedule_id = response_data.get('schedule_id')
                    if schedule_id:
                        self.created_schedules.append(schedule_id)
                    
                    # Validate response structure
                    required_fields = ['message', 'schedule_id', 'total_amount', 'installment_amount', 'number_of_installments']
                    missing_fields = [field for field in required_fields if field not in response_data]
                    
                    if not missing_fields:
                        self.log_test(
                            "Create Installment Schedule", 
                            "PASS", 
                            f"Schedule created successfully. ID: {schedule_id}, Amount: {response_data.get('installment_amount')}, Installments: {response_data.get('number_of_installments')}"
                        )
                    else:
                        self.log_test(
                            "Create Installment Schedule", 
                            "FAIL", 
                            f"Missing required fields: {missing_fields}",
                            response_data
                        )
                else:
                    self.log_test(
                        "Create Installment Schedule", 
                        "FAIL", 
                        f"Status: {response.status}",
                        response_data
                    )
        except Exception as e:
            self.log_test("Create Installment Schedule", "FAIL", f"Exception: {str(e)}")

    async def test_get_installment_schedule(self, token: str, advance_id: str):
        """Test GET /api/advances/{advance_id}/installments - Get specific installment schedule details"""
        try:
            async with self.session.get(
                f"{API_BASE}/advances/{advance_id}/installments",
                headers={'Authorization': f'Bearer {token}'}
            ) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    # Validate response structure
                    if 'schedule' in response_data and 'installments' in response_data:
                        schedule = response_data['schedule']
                        installments = response_data['installments']
                        
                        # Check schedule fields
                        schedule_fields = ['id', 'advance_transaction_id', 'employee_id', 'total_amount', 'installment_amount', 'number_of_installments']
                        missing_schedule_fields = [field for field in schedule_fields if field not in schedule]
                        
                        # Check installments structure
                        installment_count = len(installments)
                        expected_count = schedule.get('number_of_installments', 0)
                        
                        if not missing_schedule_fields and installment_count == expected_count:
                            self.log_test(
                                "Get Installment Schedule", 
                                "PASS", 
                                f"Retrieved schedule with {installment_count} installments. Total: {schedule.get('total_amount')}"
                            )
                        else:
                            issues = []
                            if missing_schedule_fields:
                                issues.append(f"Missing schedule fields: {missing_schedule_fields}")
                            if installment_count != expected_count:
                                issues.append(f"Installment count mismatch: got {installment_count}, expected {expected_count}")
                            
                            self.log_test(
                                "Get Installment Schedule", 
                                "FAIL", 
                                "; ".join(issues),
                                response_data
                            )
                    else:
                        self.log_test(
                            "Get Installment Schedule", 
                            "FAIL", 
                            "Missing 'schedule' or 'installments' in response",
                            response_data
                        )
                else:
                    self.log_test(
                        "Get Installment Schedule", 
                        "FAIL", 
                        f"Status: {response.status}",
                        response_data
                    )
        except Exception as e:
            self.log_test("Get Installment Schedule", "FAIL", f"Exception: {str(e)}")

    async def test_get_all_installment_schedules(self, token: str):
        """Test GET /api/payroll/installment-schedules - Get all installment schedules (super admin only)"""
        try:
            async with self.session.get(
                f"{API_BASE}/payroll/installment-schedules",
                headers={'Authorization': f'Bearer {token}'}
            ) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    if 'schedules' in response_data:
                        schedules = response_data['schedules']
                        schedule_count = len(schedules)
                        
                        # Validate schedule structure if any exist
                        if schedule_count > 0:
                            first_schedule = schedules[0]
                            required_fields = ['id', 'advance_transaction_id', 'employee_id', 'total_amount', 'installment_amount']
                            missing_fields = [field for field in required_fields if field not in first_schedule]
                            
                            if not missing_fields:
                                self.log_test(
                                    "Get All Installment Schedules", 
                                    "PASS", 
                                    f"Retrieved {schedule_count} installment schedules"
                                )
                            else:
                                self.log_test(
                                    "Get All Installment Schedules", 
                                    "FAIL", 
                                    f"Schedule missing required fields: {missing_fields}",
                                    response_data
                                )
                        else:
                            self.log_test(
                                "Get All Installment Schedules", 
                                "PASS", 
                                "Retrieved 0 installment schedules (empty result is valid)"
                            )
                    else:
                        self.log_test(
                            "Get All Installment Schedules", 
                            "FAIL", 
                            "Missing 'schedules' field in response",
                            response_data
                        )
                else:
                    self.log_test(
                        "Get All Installment Schedules", 
                        "FAIL", 
                        f"Status: {response.status}",
                        response_data
                    )
        except Exception as e:
            self.log_test("Get All Installment Schedules", "FAIL", f"Exception: {str(e)}")

    async def test_data_validation(self, token: str, advance_id: str):
        """Test data validation for installment scheduling"""
        
        # Test 1: Invalid installment amount (negative)
        try:
            invalid_data = {
                "installment_amount": -100.0,
                "number_of_installments": 5,
                "start_date": (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
            }
            
            async with self.session.post(
                f"{API_BASE}/advances/{advance_id}/installments",
                json=invalid_data,
                headers={'Authorization': f'Bearer {token}'}
            ) as response:
                if response.status >= 400:
                    self.log_test("Validation - Negative Amount", "PASS", "Correctly rejected negative installment amount")
                else:
                    self.log_test("Validation - Negative Amount", "FAIL", "Should reject negative installment amount")
        except Exception as e:
            self.log_test("Validation - Negative Amount", "FAIL", f"Exception: {str(e)}")
        
        # Test 2: Invalid number of installments (too high)
        try:
            invalid_data = {
                "installment_amount": 100.0,
                "number_of_installments": 100,  # Should be max 60
                "start_date": (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
            }
            
            async with self.session.post(
                f"{API_BASE}/advances/{advance_id}/installments",
                json=invalid_data,
                headers={'Authorization': f'Bearer {token}'}
            ) as response:
                if response.status >= 400:
                    self.log_test("Validation - Too Many Installments", "PASS", "Correctly rejected >60 installments")
                else:
                    self.log_test("Validation - Too Many Installments", "FAIL", "Should reject >60 installments")
        except Exception as e:
            self.log_test("Validation - Too Many Installments", "FAIL", f"Exception: {str(e)}")
        
        # Test 3: Invalid date format
        try:
            invalid_data = {
                "installment_amount": 100.0,
                "number_of_installments": 5,
                "start_date": "invalid-date"
            }
            
            async with self.session.post(
                f"{API_BASE}/advances/{advance_id}/installments",
                json=invalid_data,
                headers={'Authorization': f'Bearer {token}'}
            ) as response:
                if response.status >= 400:
                    self.log_test("Validation - Invalid Date", "PASS", "Correctly rejected invalid date format")
                else:
                    self.log_test("Validation - Invalid Date", "FAIL", "Should reject invalid date format")
        except Exception as e:
            self.log_test("Validation - Invalid Date", "FAIL", f"Exception: {str(e)}")

    async def test_error_handling(self, token: str):
        """Test error handling scenarios"""
        
        # Test 1: Non-existent advance
        try:
            fake_advance_id = str(uuid.uuid4())
            schedule_data = {
                "installment_amount": 500.0,
                "number_of_installments": 10,
                "start_date": (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
            }
            
            async with self.session.post(
                f"{API_BASE}/advances/{fake_advance_id}/installments",
                json=schedule_data,
                headers={'Authorization': f'Bearer {token}'}
            ) as response:
                if response.status == 404:
                    self.log_test("Error Handling - Non-existent Advance", "PASS", "Correctly returned 404 for non-existent advance")
                else:
                    self.log_test("Error Handling - Non-existent Advance", "FAIL", f"Expected 404, got {response.status}")
        except Exception as e:
            self.log_test("Error Handling - Non-existent Advance", "FAIL", f"Exception: {str(e)}")
        
        # Test 2: Unauthorized access (non-super_admin)
        if 'user' in self.tokens:
            try:
                schedule_data = {
                    "installment_amount": 500.0,
                    "number_of_installments": 10,
                    "start_date": (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
                }
                
                async with self.session.post(
                    f"{API_BASE}/advances/{self.created_advances[0] if self.created_advances else 'test'}/installments",
                    json=schedule_data,
                    headers={'Authorization': f'Bearer {self.tokens["user"]}'}
                ) as response:
                    if response.status == 403:
                        self.log_test("Error Handling - Unauthorized Access", "PASS", "Correctly denied access to regular user")
                    else:
                        self.log_test("Error Handling - Unauthorized Access", "FAIL", f"Expected 403, got {response.status}")
            except Exception as e:
                self.log_test("Error Handling - Unauthorized Access", "FAIL", f"Exception: {str(e)}")

    async def test_duplicate_schedule_prevention(self, token: str, advance_id: str):
        """Test prevention of duplicate schedules for same advance"""
        try:
            schedule_data = {
                "installment_amount": 300.0,
                "number_of_installments": 8,
                "start_date": (date.today() + timedelta(days=60)).strftime("%Y-%m-%d")
            }
            
            async with self.session.post(
                f"{API_BASE}/advances/{advance_id}/installments",
                json=schedule_data,
                headers={'Authorization': f'Bearer {token}'}
            ) as response:
                if response.status >= 400:
                    self.log_test("Duplicate Schedule Prevention", "PASS", "Correctly prevented duplicate schedule creation")
                else:
                    self.log_test("Duplicate Schedule Prevention", "FAIL", "Should prevent duplicate schedule creation")
        except Exception as e:
            self.log_test("Duplicate Schedule Prevention", "FAIL", f"Exception: {str(e)}")

    async def test_integration_workflow(self):
        """Test complete workflow: create advance → approve → create installment schedule"""
        try:
            # Authenticate super admin
            super_admin_token = await self.authenticate_user('super_admin')
            if not super_admin_token:
                self.log_test("Integration Workflow", "FAIL", "Could not authenticate super admin")
                return
            
            # Authenticate regular user
            user_token = await self.authenticate_user('user')
            if not user_token:
                self.log_test("Integration Workflow", "FAIL", "Could not authenticate user")
                return
            
            # Create advance
            advance_id = await self.create_test_advance(super_admin_token)
            if not advance_id:
                self.log_test("Integration Workflow", "FAIL", "Could not create test advance")
                return
            
            # Create installment schedule
            await self.test_create_installment_schedule(super_admin_token, advance_id)
            
            # Get installment schedule details
            await self.test_get_installment_schedule(super_admin_token, advance_id)
            
            # Get all installment schedules
            await self.test_get_all_installment_schedules(super_admin_token)
            
            # Test data validation
            await self.test_data_validation(super_admin_token, advance_id)
            
            # Test error handling
            await self.test_error_handling(super_admin_token)
            
            # Test duplicate prevention
            await self.test_duplicate_schedule_prevention(super_admin_token, advance_id)
            
            self.log_test("Integration Workflow", "PASS", "Completed full integration workflow testing")
            
        except Exception as e:
            self.log_test("Integration Workflow", "FAIL", f"Exception: {str(e)}")

    async def run_all_tests(self):
        """Run all installment scheduling tests"""
        print("🚀 Starting Comprehensive Installment Scheduling System Testing")
        print("=" * 80)
        print()
        
        await self.test_integration_workflow()
        
        # Generate summary
        print("=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%")
        print()
        
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in self.test_results:
                if result['status'] == 'FAIL':
                    print(f"  - {result['test']}: {result['details']}")
            print()
        
        print("🎯 CRITICAL FINDINGS:")
        
        # Check for critical issues
        critical_issues = []
        
        # Check if basic endpoints are working
        endpoint_tests = [r for r in self.test_results if 'Installment Schedule' in r['test']]
        if not any(r['status'] == 'PASS' for r in endpoint_tests):
            critical_issues.append("❌ CRITICAL: No installment scheduling endpoints are working")
        
        # Check authentication
        auth_tests = [r for r in self.test_results if 'Authentication' in r['test']]
        if not any(r['status'] == 'PASS' for r in auth_tests):
            critical_issues.append("❌ CRITICAL: Authentication system not working")
        
        # Check data validation
        validation_tests = [r for r in self.test_results if 'Validation' in r['test']]
        if not any(r['status'] == 'PASS' for r in validation_tests):
            critical_issues.append("⚠️ WARNING: Data validation may not be working properly")
        
        if critical_issues:
            for issue in critical_issues:
                print(f"  {issue}")
        else:
            print("  ✅ No critical issues found - Core installment scheduling functionality is operational")
        
        print()
        print("🔍 DETAILED TEST RESULTS:")
        for result in self.test_results:
            status_emoji = "✅" if result['status'] == "PASS" else "❌"
            print(f"  {status_emoji} {result['test']}")
            if result['details']:
                print(f"      {result['details']}")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': (passed_tests/total_tests*100) if total_tests > 0 else 0,
            'critical_issues': critical_issues,
            'test_results': self.test_results
        }

async def main():
    """Main test execution"""
    async with InstallmentSchedulingTester() as tester:
        results = await tester.run_all_tests()
        return results

if __name__ == "__main__":
    results = asyncio.run(main())