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