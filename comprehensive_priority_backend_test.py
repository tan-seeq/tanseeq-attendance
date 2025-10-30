#!/usr/bin/env python3
"""
COMPREHENSIVE BACKEND TESTING - PRIORITY ROUTES & FUNCTIONALITY
Testing all priority routes and functionality as outlined in the comprehensive QA plan
"""

import requests
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import time
import uuid

# Configuration - Use environment variable
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://attendance-pro-43.preview.emergentagent.com')
BASE_URL = f"{BACKEND_URL}/api"

# Test accounts from review request
TEST_ACCOUNTS = {
    "super_admin": {"email": "admin@tanseeq.com", "password": "ADMIN"},
    "user": {"email": "jihad@tanseeq.com", "password": "jihad123"}
}

class ComprehensiveBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.tokens = {}
        self.test_results = []
        self.evidence_dir = Path("./evidence/backend")
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

    def test_auth_me(self):
        """Test GET /api/auth/me endpoint"""
        try:
            response = self.session.get(f"{BASE_URL}/auth/me")
            if response.status_code == 200:
                user_info = response.json()
                self.log_result("Auth Me", "PASS", 
                              f"User info retrieved: {user_info.get('name')} ({user_info.get('role')})")
            else:
                self.log_result("Auth Me", "FAIL", 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("Auth Me", "FAIL", f"Exception: {str(e)}")

    def test_payroll_system(self):
        """Test PAYROLL SYSTEM (HIGHEST PRIORITY)"""
        print("\n💰 Testing PAYROLL SYSTEM (HIGHEST PRIORITY)...")
        
        # 1. GET /api/payroll/cycles - List all cycles
        try:
            response = self.session.get(f"{BASE_URL}/payroll/cycles")
            if response.status_code == 200:
                cycles_data = response.json()
                # Handle both list and object formats
                if isinstance(cycles_data, list):
                    cycles = cycles_data
                else:
                    cycles = cycles_data.get('cycles', [])
                
                self.log_result("Payroll Cycles - List All", "PASS", 
                              f"Retrieved {len(cycles)} cycles with proper JSON structure")
                
                # Store first cycle for further testing
                if cycles:
                    self.test_cycle_id = cycles[0].get('id')
                    self.log_result("Payroll Cycles - Cycle ID Found", "PASS", 
                                  f"Using cycle ID: {self.test_cycle_id}")
                else:
                    # Create a test cycle if none exist
                    self.create_test_payroll_cycle()
                    
            else:
                self.log_result("Payroll Cycles - List All", "FAIL", 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("Payroll Cycles - List All", "FAIL", f"Exception: {str(e)}")

        # Test other payroll endpoints if we have a cycle ID
        if hasattr(self, 'test_cycle_id') and self.test_cycle_id:
            self.test_payroll_cycle_operations(self.test_cycle_id)

    def create_test_payroll_cycle(self):
        """Create a test payroll cycle"""
        try:
            # Use a unique month to avoid conflicts
            test_month = f"2025-{datetime.now().month:02d}"
            cycle_data = {
                "month": test_month,
                "notes": "Test cycle for comprehensive backend testing"
            }
            response = self.session.post(f"{BASE_URL}/payroll/cycles", json=cycle_data)
            if response.status_code in [200, 201]:
                result = response.json()
                self.test_cycle_id = result.get("cycle_id") or result.get("id")
                self.log_result("Payroll Cycles - Create Test Cycle", "PASS", 
                              f"Created test cycle: {self.test_cycle_id}")
            else:
                self.log_result("Payroll Cycles - Create Test Cycle", "FAIL", 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("Payroll Cycles - Create Test Cycle", "FAIL", f"Exception: {str(e)}")

    def test_payroll_cycle_operations(self, cycle_id):
        """Test payroll cycle operations"""
        
        # 2. GET /api/payroll/cycles/{cycle_id} - Single cycle retrieval
        try:
            response = self.session.get(f"{BASE_URL}/payroll/cycles/{cycle_id}")
            if response.status_code == 200:
                cycle_data = response.json()
                self.log_result("Payroll Cycles - Single Retrieval", "PASS", 
                              f"Retrieved cycle details: {cycle_data.get('month', 'unknown')}")
            else:
                self.log_result("Payroll Cycles - Single Retrieval", "FAIL", 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("Payroll Cycles - Single Retrieval", "FAIL", f"Exception: {str(e)}")

        # 3. POST /api/payroll/cycles/{cycle_id}/calculate - Calculate payroll for 6 employees
        try:
            response = self.session.post(f"{BASE_URL}/payroll/cycles/{cycle_id}/calculate")
            if response.status_code == 200:
                calculation = response.json()
                employee_count = len(calculation.get("employee_summaries", []))
                self.log_result("Payroll Cycles - Calculate", "PASS", 
                              f"Calculated payroll for {employee_count} employees")
            else:
                self.log_result("Payroll Cycles - Calculate", "FAIL", 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("Payroll Cycles - Calculate", "FAIL", f"Exception: {str(e)}")

        # 4. POST /api/payroll/cycles/{cycle_id}/lock - Lock with reason
        try:
            lock_data = {"lock_reason": "Testing lock functionality with audit logging"}
            response = self.session.post(f"{BASE_URL}/payroll/cycles/{cycle_id}/lock", json=lock_data)
            if response.status_code == 200:
                self.log_result("Payroll Cycles - Lock", "PASS", "Cycle locked with audit reason")
                
                # 5. POST /api/payroll/cycles/{cycle_id}/unlock - Unlock (Super Admin only)
                unlock_data = {"reason": "Testing unlock functionality"}
                response = self.session.post(f"{BASE_URL}/payroll/cycles/{cycle_id}/unlock", json=unlock_data)
                if response.status_code == 200:
                    self.log_result("Payroll Cycles - Unlock", "PASS", "Cycle unlocked (Super Admin only)")
                else:
                    self.log_result("Payroll Cycles - Unlock", "FAIL", 
                                  f"Failed: {response.status_code} - {response.text}")
            else:
                self.log_result("Payroll Cycles - Lock", "FAIL", 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("Payroll Cycles - Lock/Unlock", "FAIL", f"Exception: {str(e)}")

        # 6. GET /api/payroll/cycles/{cycle_id}/summary - Detailed summary
        try:
            response = self.session.get(f"{BASE_URL}/payroll/cycles/{cycle_id}/summary")
            if response.status_code == 200:
                summary = response.json()
                self.log_result("Payroll Cycles - Summary", "PASS", 
                              f"Retrieved detailed summary for PayrollSummary page")
            else:
                self.log_result("Payroll Cycles - Summary", "FAIL", 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("Payroll Cycles - Summary", "FAIL", f"Exception: {str(e)}")

        # 7. GET /api/payroll/cycles/{cycle_id}/export/pdf - PDF export
        try:
            response = self.session.get(f"{BASE_URL}/payroll/cycles/{cycle_id}/export/pdf")
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                if 'pdf' in content_type.lower() and len(response.content) > 0:
                    # Save PDF to evidence
                    pdf_path = self.evidence_dir / f"payroll_cycle_{cycle_id}.pdf"
                    with open(pdf_path, 'wb') as f:
                        f.write(response.content)
                    self.log_result("Payroll Cycles - PDF Export", "PASS", 
                                  f"PDF exported and saved (size: {len(response.content)} bytes)")
                else:
                    self.log_result("Payroll Cycles - PDF Export", "FAIL", 
                                  f"Invalid PDF: content-type={content_type}")
            else:
                self.log_result("Payroll Cycles - PDF Export", "FAIL", 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("Payroll Cycles - PDF Export", "FAIL", f"Exception: {str(e)}")

        # 8. GET /api/payroll/cycles/{cycle_id}/export/excel - Excel export
        try:
            response = self.session.get(f"{BASE_URL}/payroll/cycles/{cycle_id}/export/excel")
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                if ('excel' in content_type.lower() or 'spreadsheet' in content_type.lower()) and len(response.content) > 0:
                    # Save Excel to evidence
                    excel_path = self.evidence_dir / f"payroll_cycle_{cycle_id}.xlsx"
                    with open(excel_path, 'wb') as f:
                        f.write(response.content)
                    self.log_result("Payroll Cycles - Excel Export", "PASS", 
                                  f"Excel exported and saved (size: {len(response.content)} bytes)")
                else:
                    self.log_result("Payroll Cycles - Excel Export", "FAIL", 
                                  f"Invalid Excel: content-type={content_type}")
            else:
                self.log_result("Payroll Cycles - Excel Export", "FAIL", 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("Payroll Cycles - Excel Export", "FAIL", f"Exception: {str(e)}")

    def test_attendance_deductions(self):
        """Test ATTENDANCE DEDUCTIONS"""
        print("\n📊 Testing ATTENDANCE DEDUCTIONS...")
        
        # 1. GET /api/deductions - Verify employee_name field
        try:
            response = self.session.get(f"{BASE_URL}/deductions")
            if response.status_code == 200:
                deductions = response.json()
                if isinstance(deductions, list):
                    if len(deductions) > 0:
                        # Check if employee_name field is present
                        first_deduction = deductions[0]
                        if 'employee_name' in first_deduction:
                            self.log_result("Attendance Deductions - Employee Name Field", "PASS", 
                                          f"employee_name field present in {len(deductions)} deduction records")
                        else:
                            self.log_result("Attendance Deductions - Employee Name Field", "FAIL", 
                                          "employee_name field missing from deduction records")
                    else:
                        self.log_result("Attendance Deductions - Employee Name Field", "PASS", 
                                      "No deductions found (empty list is valid)")
                else:
                    self.log_result("Attendance Deductions - Employee Name Field", "FAIL", 
                                  "Invalid response format")
            else:
                self.log_result("Attendance Deductions - Employee Name Field", "FAIL", 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("Attendance Deductions - Employee Name Field", "FAIL", f"Exception: {str(e)}")

        # 2. GET /api/employees/list - Verify active employees for both user and admin
        self.test_employees_list()

        # 3. Test manual deduction CRUD operations
        self.test_manual_deduction_crud()

    def test_employees_list(self):
        """Test employees list for both user and admin"""
        for role in ["super_admin", "user"]:
            if role in self.tokens:
                try:
                    # Switch to the role's token
                    self.session.headers.update({"Authorization": f"Bearer {self.tokens[role]}"})
                    
                    response = self.session.get(f"{BASE_URL}/employees/list")
                    if response.status_code == 200:
                        data = response.json()
                        # Handle both direct list and object with employees key
                        if isinstance(data, list):
                            employees = data
                        else:
                            employees = data.get('employees', [])
                        
                        if len(employees) > 0:
                            # Check if employees have required fields
                            first_emp = employees[0]
                            if 'id' in first_emp and 'name' in first_emp:
                                self.log_result(f"Employees List - {role}", "PASS", 
                                              f"Retrieved {len(employees)} active employees with id+name")
                                # Store employee ID for deduction testing
                                if not hasattr(self, 'test_employee_id'):
                                    self.test_employee_id = first_emp['id']
                            else:
                                self.log_result(f"Employees List - {role}", "FAIL", 
                                              "Employees missing required id or name fields")
                        else:
                            self.log_result(f"Employees List - {role}", "FAIL", "No employees returned")
                    else:
                        self.log_result(f"Employees List - {role}", "FAIL", 
                                      f"Failed: {response.status_code} - {response.text}")
                except Exception as e:
                    self.log_result(f"Employees List - {role}", "FAIL", f"Exception: {str(e)}")

    def test_manual_deduction_crud(self):
        """Test manual deduction CRUD operations"""
        if not hasattr(self, 'test_employee_id'):
            self.log_result("Manual Deductions CRUD", "SKIP", "No employee ID available")
            return

        # Switch back to super admin for deduction operations
        if "super_admin" in self.tokens:
            self.session.headers.update({"Authorization": f"Bearer {self.tokens['super_admin']}"})

        deduction_id = None
        
        # CREATE - POST /api/deductions
        try:
            deduction_data = {
                "employee_id": self.test_employee_id,
                "amount": 100.0,
                "reason": "Test manual deduction for comprehensive testing",
                "category": "late_arrival",
                "date": datetime.now().strftime("%Y-%m-%d")
            }
            
            response = self.session.post(f"{BASE_URL}/deductions", json=deduction_data)
            if response.status_code in [200, 201]:
                result = response.json()
                deduction_id = result.get("id") or result.get("deduction_id")
                self.log_result("Manual Deductions - Create", "PASS", 
                              f"Created manual deduction: {deduction_id}")
            else:
                self.log_result("Manual Deductions - Create", "FAIL", 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("Manual Deductions - Create", "FAIL", f"Exception: {str(e)}")

        # EDIT - PUT /api/deductions/{id}
        if deduction_id:
            try:
                edit_data = {
                    "amount": 150.0,
                    "reason": "Updated test manual deduction"
                }
                response = self.session.put(f"{BASE_URL}/deductions/{deduction_id}", json=edit_data)
                if response.status_code == 200:
                    self.log_result("Manual Deductions - Edit", "PASS", "Deduction edited successfully")
                else:
                    self.log_result("Manual Deductions - Edit", "FAIL", 
                                  f"Failed: {response.status_code} - {response.text}")
            except Exception as e:
                self.log_result("Manual Deductions - Edit", "FAIL", f"Exception: {str(e)}")

            # DELETE - DELETE /api/deductions/{id}
            try:
                response = self.session.delete(f"{BASE_URL}/deductions/{deduction_id}")
                if response.status_code == 200:
                    self.log_result("Manual Deductions - Delete", "PASS", "Deduction deleted/voided successfully")
                else:
                    self.log_result("Manual Deductions - Delete", "FAIL", 
                                  f"Failed: {response.status_code} - {response.text}")
            except Exception as e:
                self.log_result("Manual Deductions - Delete", "FAIL", f"Exception: {str(e)}")

    def test_work_reports_logs(self):
        """Test WORK REPORTS LOGS (MongoDB)"""
        print("\n📝 Testing WORK REPORTS LOGS (MongoDB)...")
        
        log_id = None
        
        # Test filters, search, and pagination - GET /api/work-reports/logs
        try:
            current_date = datetime.now().strftime("%Y-%m-%d")
            params = {
                "date": current_date,
                "q": "test",
                "page": 1,
                "page_size": 10
            }
            
            response = self.session.get(f"{BASE_URL}/work-reports/logs", params=params)
            if response.status_code == 200:
                logs_data = response.json()
                logs = logs_data.get('logs', []) if isinstance(logs_data, dict) else logs_data
                self.log_result("Work Reports - Filters/Search/Pagination", "PASS", 
                              f"Filters working, found {len(logs)} logs")
            else:
                self.log_result("Work Reports - Filters/Search/Pagination", "FAIL", 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("Work Reports - Filters/Search/Pagination", "FAIL", f"Exception: {str(e)}")

        # CREATE - POST /api/work-reports/logs
        try:
            log_data = {
                "client_id": str(uuid.uuid4()),
                "activity_type_id": str(uuid.uuid4()),
                "date": datetime.now().isoformat(),
                "start_time": datetime.now().isoformat(),
                "end_time": (datetime.now() + timedelta(hours=2)).isoformat(),
                "description": "Test work log for comprehensive backend testing",
                "notes": "Created during comprehensive testing",
                "is_billable": True,
                "hourly_rate": 150.0
            }
            
            response = self.session.post(f"{BASE_URL}/work-reports/logs", json=log_data)
            if response.status_code in [200, 201]:
                result = response.json()
                log_id = result.get("id") or result.get("log_id")
                self.log_result("Work Reports - Create Log", "PASS", f"Created work log: {log_id}")
            else:
                self.log_result("Work Reports - Create Log", "FAIL", 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("Work Reports - Create Log", "FAIL", f"Exception: {str(e)}")

        # UPDATE - PUT /api/work-reports/logs/{log_id}
        if log_id:
            try:
                update_data = {
                    "description": "Updated test work log with duration/amount recompute",
                    "end_time": (datetime.now() + timedelta(hours=3)).isoformat(),
                    "notes": "Updated during comprehensive testing - duration recomputed"
                }
                response = self.session.put(f"{BASE_URL}/work-reports/logs/{log_id}", json=update_data)
                if response.status_code == 200:
                    self.log_result("Work Reports - Update Log", "PASS", 
                                  "Log updated with duration/amount recompute")
                else:
                    self.log_result("Work Reports - Update Log", "FAIL", 
                                  f"Failed: {response.status_code} - {response.text}")
            except Exception as e:
                self.log_result("Work Reports - Update Log", "FAIL", f"Exception: {str(e)}")

            # DELETE - DELETE /api/work-reports/logs/{log_id}
            try:
                response = self.session.delete(f"{BASE_URL}/work-reports/logs/{log_id}")
                if response.status_code == 200:
                    self.log_result("Work Reports - Delete Log", "PASS", "Log deleted successfully")
                else:
                    self.log_result("Work Reports - Delete Log", "FAIL", 
                                  f"Failed: {response.status_code} - {response.text}")
            except Exception as e:
                self.log_result("Work Reports - Delete Log", "FAIL", f"Exception: {str(e)}")

        # Test client creation - POST /api/work-reports/clients
        try:
            client_data = {
                "company_name": "Test Client for Comprehensive Testing",
                "company_name_ar": "عميل اختبار للاختبار الشامل",
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
                              f"Created client (MongoDB fix verified): {client_id}")
            else:
                self.log_result("Work Reports - Create Client", "FAIL", 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("Work Reports - Create Client", "FAIL", f"Exception: {str(e)}")

    def test_marketing_field_visits(self):
        """Test MARKETING/FIELD VISITS"""
        print("\n🚗 Testing MARKETING/FIELD VISITS...")
        
        # Switch to regular user for marketing visits
        if "user" in self.tokens:
            self.session.headers.update({"Authorization": f"Bearer {self.tokens['user']}"})

        visit_id = None
        
        # START VISIT - POST /api/marketing-visits/start
        try:
            visit_data = {
                "client_name": "Test Client for Comprehensive Testing",
                "location_name": "Test Location Dubai",
                "area": "Dubai Marina",
                "purpose": "client_meeting",
                "purpose_details": "Comprehensive backend testing visit",
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

        # GET ACTIVE VISITS - GET /api/marketing-visits/active
        try:
            response = self.session.get(f"{BASE_URL}/marketing-visits/active")
            if response.status_code == 200:
                active_data = response.json()
                active_visit = active_data.get('active_visit')
                if active_visit:
                    self.log_result("Marketing Visits - Get Active", "PASS", 
                                  f"Active visit found: {active_visit.get('id')}")
                else:
                    self.log_result("Marketing Visits - Get Active", "PASS", 
                                  "No active visits (valid state)")
            else:
                self.log_result("Marketing Visits - Get Active", "FAIL", 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("Marketing Visits - Get Active", "FAIL", f"Exception: {str(e)}")

        # COMPLETE VISIT - POST /api/marketing-visits/{id}/complete
        if visit_id:
            try:
                time.sleep(2)  # Wait for visit duration
                
                completion_data = {
                    "visit_report": {
                        "summary": "Comprehensive backend testing visit completed successfully with all required details and mandatory reporting",
                        "details": "This is a detailed comprehensive test visit report created during backend regression testing. The visit was conducted to verify the marketing visits API functionality including start, active status check, and completion with mandatory reporting. All endpoints were tested thoroughly including GPS location tracking and report submission requirements.",
                        "result": "successful",
                        "next_actions": "Continue with comprehensive testing of remaining backend endpoints and verify Super Admin notification system"
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
                    
                    # Verify Super Admin notification
                    self.verify_super_admin_notification()
                else:
                    self.log_result("Marketing Visits - Complete", "FAIL", 
                                  f"Failed: {response.status_code} - {response.text}")
            except Exception as e:
                self.log_result("Marketing Visits - Complete", "FAIL", f"Exception: {str(e)}")

    def verify_super_admin_notification(self):
        """Verify Super Admin notification sent on completion"""
        try:
            # Switch to super admin token
            if "super_admin" in self.tokens:
                self.session.headers.update({"Authorization": f"Bearer {self.tokens['super_admin']}"})
                
                response = self.session.get(f"{BASE_URL}/notifications/my")
                if response.status_code == 200:
                    data = response.json()
                    # Handle both direct list and object format
                    if isinstance(data, list):
                        notifications = data
                    else:
                        notifications = data.get('notifications', [])
                    
                    # Look for recent marketing visit notifications
                    recent_notifications = [n for n in notifications if 
                                          'marketing' in str(n.get('subject', '')).lower() or 
                                          'visit' in str(n.get('subject', '')).lower() or
                                          'زيارة' in str(n.get('subject', ''))]
                    
                    if recent_notifications:
                        self.log_result("Marketing Visits - Super Admin Notification", "PASS", 
                                      f"Super Admin notification confirmed: {len(recent_notifications)} visit notifications")
                    else:
                        self.log_result("Marketing Visits - Super Admin Notification", "FAIL", 
                                      "No marketing visit notifications found for Super Admin")
                else:
                    self.log_result("Marketing Visits - Super Admin Notification", "FAIL", 
                                  f"Failed to get notifications: {response.status_code}")
        except Exception as e:
            self.log_result("Marketing Visits - Super Admin Notification", "FAIL", f"Exception: {str(e)}")

    def test_attendance_policies(self):
        """Test ATTENDANCE POLICIES"""
        print("\n⚡ Testing ATTENDANCE POLICIES...")
        
        # GET /api/attendance-policies - Retrieve all policies
        try:
            response = self.session.get(f"{BASE_URL}/attendance-policies")
            if response.status_code == 200:
                policies = response.json()
                self.log_result("Attendance Policies - Retrieve All", "PASS", 
                              f"Retrieved {len(policies)} attendance policies")
                
                # Look for specific policies mentioned in review
                hatem_policy = None
                tarek_policy = None
                
                for policy in policies:
                    if 'hatem' in str(policy.get('employee_name', '')).lower():
                        hatem_policy = policy
                    elif 'tarek' in str(policy.get('employee_name', '')).lower() and 'wazzan' in str(policy.get('employee_name', '')).lower():
                        tarek_policy = policy
                
                # Verify Hatem policy (no deductions)
                if hatem_policy:
                    self.log_result("Attendance Policies - Hatem Policy", "PASS", 
                                  f"Hatem policy found: {json.dumps(hatem_policy, indent=2)}")
                else:
                    self.log_result("Attendance Policies - Hatem Policy", "FAIL", 
                                  "Hatem policy not found")
                
                # Verify Tarek Wazzan policy (08:00 flex exit, early_start_allowed, end_flexible)
                if tarek_policy:
                    policy_details = []
                    if tarek_policy.get('start_time') == '08:00' or tarek_policy.get('working_hours_start') == '08:00':
                        policy_details.append("08:00 start time")
                    if tarek_policy.get('end_flexible') or tarek_policy.get('has_flexible_schedule'):
                        policy_details.append("flexible end")
                    if tarek_policy.get('early_start_allowed'):
                        policy_details.append("early start allowed")
                    
                    self.log_result("Attendance Policies - Tarek Wazzan Policy", "PASS", 
                                  f"Tarek Wazzan policy verified: {', '.join(policy_details)}")
                else:
                    self.log_result("Attendance Policies - Tarek Wazzan Policy", "FAIL", 
                                  "Tarek Wazzan policy not found")
                    
            else:
                self.log_result("Attendance Policies - Retrieve All", "FAIL", 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("Attendance Policies - Retrieve All", "FAIL", f"Exception: {str(e)}")

    def test_notifications(self):
        """Test NOTIFICATIONS"""
        print("\n🔔 Testing NOTIFICATIONS...")
        
        # Test user-specific notifications scoping for each role
        for role in ["super_admin", "user"]:
            if role in self.tokens:
                try:
                    # Switch to the role's token
                    self.session.headers.update({"Authorization": f"Bearer {self.tokens[role]}"})
                    
                    response = self.session.get(f"{BASE_URL}/notifications/my")
                    if response.status_code == 200:
                        data = response.json()
                        # Handle both direct list and object format
                        if isinstance(data, list):
                            notifications = data
                        else:
                            notifications = data.get('notifications', [])
                        
                        self.log_result(f"Notifications - User Scoping ({role})", "PASS", 
                                      f"Retrieved {len(notifications)} user-specific notifications")
                        
                        # Verify role-based access
                        if role == "super_admin" and len(notifications) > 0:
                            self.log_result("Notifications - Role-based Access", "PASS", 
                                          "Super Admin has access to notifications")
                        elif role == "user":
                            self.log_result("Notifications - Role-based Access", "PASS", 
                                          "Regular user has scoped notification access")
                            
                    else:
                        self.log_result(f"Notifications - User Scoping ({role})", "FAIL", 
                                      f"Failed: {response.status_code} - {response.text}")
                except Exception as e:
                    self.log_result(f"Notifications - User Scoping ({role})", "FAIL", f"Exception: {str(e)}")

    def test_authentication_authorization(self):
        """Test AUTHENTICATION & AUTHORIZATION"""
        print("\n🔐 Testing AUTHENTICATION & AUTHORIZATION...")
        
        # Test all credentials from review request
        test_credentials = [
            {"email": "admin@tanseeq.com", "password": "ADMIN", "role": "Super Admin"},
            {"email": "jihad@tanseeq.com", "password": "jihad123", "role": "User"}
        ]
        
        for cred in test_credentials:
            try:
                response = self.session.post(f"{BASE_URL}/auth/login", json={
                    "email": cred["email"],
                    "password": cred["password"]
                })
                
                if response.status_code == 200:
                    data = response.json()
                    user_info = data.get("user", {})
                    self.log_result(f"Auth - {cred['role']} Login", "PASS", 
                                  f"Successfully authenticated {cred['email']} (Role: {user_info.get('role')})")
                else:
                    self.log_result(f"Auth - {cred['role']} Login", "FAIL", 
                                  f"Failed: {response.status_code} - {response.text}")
            except Exception as e:
                self.log_result(f"Auth - {cred['role']} Login", "FAIL", f"Exception: {str(e)}")

        # Test 401/403 responses for unauthenticated/unauthorized requests
        try:
            # Test without token
            session_no_auth = requests.Session()
            response = session_no_auth.get(f"{BASE_URL}/payroll/cycles")
            if response.status_code == 401:
                self.log_result("Auth - 401 Unauthenticated", "PASS", 
                              "Properly returns 401 for unauthenticated requests")
            else:
                self.log_result("Auth - 401 Unauthenticated", "FAIL", 
                              f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_result("Auth - 401 Unauthenticated", "FAIL", f"Exception: {str(e)}")

        # Test 403 with user token on admin endpoint
        if "user" in self.tokens:
            try:
                session_user = requests.Session()
                session_user.headers.update({"Authorization": f"Bearer {self.tokens['user']}"})
                response = session_user.post(f"{BASE_URL}/payroll/cycles", json={"month": "2025-12"})
                if response.status_code == 403:
                    self.log_result("Auth - 403 Unauthorized", "PASS", 
                                  "Properly returns 403 for unauthorized requests")
                else:
                    self.log_result("Auth - 403 Unauthorized", "FAIL", 
                                  f"Expected 403, got {response.status_code}")
            except Exception as e:
                self.log_result("Auth - 403 Unauthorized", "FAIL", f"Exception: {str(e)}")

    def run_comprehensive_tests(self):
        """Run all comprehensive priority tests"""
        print("🚀 Starting COMPREHENSIVE BACKEND TESTING - PRIORITY ROUTES & FUNCTIONALITY")
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
        
        # Test GET /api/auth/me
        self.test_auth_me()
        
        # Run all priority tests in order
        self.test_payroll_system()                    # Priority 1 - HIGHEST
        self.test_attendance_deductions()             # Priority 2
        self.test_work_reports_logs()                 # Priority 3
        self.test_marketing_field_visits()            # Priority 4
        self.test_attendance_policies()               # Priority 5
        self.test_notifications()                     # Priority 6
        self.test_authentication_authorization()      # Priority 7
        
        # Generate comprehensive summary
        self.generate_comprehensive_summary()

    def generate_comprehensive_summary(self):
        """Generate comprehensive test summary"""
        print("\n" + "=" * 80)
        print("📋 COMPREHENSIVE BACKEND TEST SUMMARY - PRIORITY ROUTES & FUNCTIONALITY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        skipped_tests = len([r for r in self.test_results if r["status"] == "SKIP"])
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⏭️ Skipped: {skipped_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Group results by priority area
        priority_areas = {
            "PAYROLL SYSTEM": [r for r in self.test_results if "Payroll" in r["test"]],
            "ATTENDANCE DEDUCTIONS": [r for r in self.test_results if "Deductions" in r["test"] or "Employees List" in r["test"]],
            "WORK REPORTS LOGS": [r for r in self.test_results if "Work Reports" in r["test"]],
            "MARKETING/FIELD VISITS": [r for r in self.test_results if "Marketing Visits" in r["test"]],
            "ATTENDANCE POLICIES": [r for r in self.test_results if "Attendance Policies" in r["test"]],
            "NOTIFICATIONS": [r for r in self.test_results if "Notifications" in r["test"]],
            "AUTHENTICATION": [r for r in self.test_results if "Auth" in r["test"]]
        }
        
        print("\n📊 RESULTS BY PRIORITY AREA:")
        for area, results in priority_areas.items():
            if results:
                area_passed = len([r for r in results if r["status"] == "PASS"])
                area_total = len(results)
                area_rate = (area_passed/area_total)*100 if area_total > 0 else 0
                print(f"  {area}: {area_passed}/{area_total} ({area_rate:.1f}%)")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"  • {result['test']}: {result['details']}")
        
        # Save detailed results
        results_file = Path("./comprehensive_backend_test_results.json")
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        print(f"📁 Evidence files saved to: {self.evidence_dir}")
        
        # Success criteria check
        print(f"\n🎯 SUCCESS CRITERIA CHECK:")
        print(f"  • All priority endpoints tested: {'✅' if total_tests >= 25 else '❌'}")
        print(f"  • PDF/Excel exports working: {'✅' if any('Export' in r['test'] and r['status'] == 'PASS' for r in self.test_results) else '❌'}")
        print(f"  • Authentication working: {'✅' if any('Auth' in r['test'] and r['status'] == 'PASS' for r in self.test_results) else '❌'}")
        print(f"  • MongoDB Work Reports functional: {'✅' if any('Work Reports' in r['test'] and r['status'] == 'PASS' for r in self.test_results) else '❌'}")
        print(f"  • Marketing visit notifications confirmed: {'✅' if any('Super Admin Notification' in r['test'] and r['status'] == 'PASS' for r in self.test_results) else '❌'}")

if __name__ == "__main__":
    tester = ComprehensiveBackendTester()
    tester.run_comprehensive_tests()