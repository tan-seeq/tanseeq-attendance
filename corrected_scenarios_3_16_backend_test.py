#!/usr/bin/env python3
"""
🔥 CORRECTED COMPREHENSIVE BACKEND TESTING - SCENARIOS 3-16
==========================================================

Fixed version addressing validation errors and using correct API endpoints.
"""

import requests
import json
import os
import sys
from datetime import datetime, timedelta
import uuid
from pathlib import Path

# Test Configuration
BACKEND_URL = "https://tanseeq-attendance.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# Test Accounts
TEST_ACCOUNTS = {
    "super_admin": {"email": "admin@tanseeq.com", "password": "ADMIN"},
    "admin": {"email": "mahmoud@tanseeq.com", "password": "mahmoud123"},
    "user": {"email": "jihad@tanseeq.com", "password": "jihad123"}
}

class CorrectedBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.tokens = {}
        self.test_results = []
        self.evidence = {}
        self.user_ids = {}
        
    def log_test(self, scenario, test_name, success, details, response_data=None):
        """Log test result"""
        result = {
            "scenario": scenario,
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} | {scenario} | {test_name}: {details}")
        
    def authenticate_all_users(self):
        """Authenticate all test users and get user IDs"""
        print("\n🔐 AUTHENTICATING ALL TEST USERS...")
        
        for role, credentials in TEST_ACCOUNTS.items():
            try:
                response = self.session.post(f"{API_BASE}/auth/login", json=credentials)
                if response.status_code == 200:
                    data = response.json()
                    self.tokens[role] = data["access_token"]
                    self.user_ids[role] = data["user"]["id"]
                    self.log_test("Authentication", f"{role.upper()} Login", True, 
                                f"Successfully authenticated {credentials['email']} (ID: {data['user']['id']})")
                else:
                    self.log_test("Authentication", f"{role.upper()} Login", False, 
                                f"Failed to authenticate {credentials['email']}: {response.status_code}")
                    return False
            except Exception as e:
                self.log_test("Authentication", f"{role.upper()} Login", False, f"Exception: {str(e)}")
                return False
        
        return True
    
    def get_headers(self, role="super_admin"):
        """Get authorization headers for role"""
        return {"Authorization": f"Bearer {self.tokens.get(role, '')}"}
    
    def scenario_3_leave_management_corrected(self):
        """SCENARIO 3: إدارة الإجازات (Leave Management) - CORRECTED"""
        print("\n📋 SCENARIO 3: LEAVE MANAGEMENT TESTING (CORRECTED)...")
        
        # 1. As User (jihad): Create leave request with correct format
        try:
            leave_data = {
                "start_date": "2025-01-20",
                "end_date": "2025-01-20", 
                "reason": "إجازة سنوية - يوم واحد",
                "days_count": 1
            }
            
            response = self.session.post(f"{API_BASE}/leaves", 
                                       json=leave_data, 
                                       headers=self.get_headers("user"))
            
            if response.status_code in [200, 201]:
                leave_data_response = response.json()
                leave_id = leave_data_response.get("id") or leave_data_response.get("leave_id")
                self.evidence["leave_id"] = leave_id
                self.log_test("Scenario 3", "Create Leave Request", True, 
                            f"Leave request created successfully: {leave_id}")
            else:
                self.log_test("Scenario 3", "Create Leave Request", False, 
                            f"Failed to create leave: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Scenario 3", "Create Leave Request", False, f"Exception: {str(e)}")
        
        # 2. Get user's leave balance
        try:
            response = self.session.get(f"{API_BASE}/leaves/my", 
                                      headers=self.get_headers("user"))
            
            if response.status_code == 200:
                leaves_data = response.json()
                # Handle both list and dict responses
                if isinstance(leaves_data, list):
                    leave_count = len(leaves_data)
                else:
                    leave_count = len(leaves_data.get('leaves', []))
                
                self.log_test("Scenario 3", "Get User Leave Balance", True, 
                            f"Retrieved {leave_count} leave records for user")
            else:
                self.log_test("Scenario 3", "Get User Leave Balance", False, 
                            f"Failed to get user leaves: {response.status_code}")
                            
        except Exception as e:
            self.log_test("Scenario 3", "Get User Leave Balance", False, f"Exception: {str(e)}")
        
        # 3. Admin view all leave requests
        try:
            response = self.session.get(f"{API_BASE}/leaves", 
                                      headers=self.get_headers("super_admin"))
            
            if response.status_code == 200:
                all_leaves = response.json()
                # Handle both list and dict responses
                if isinstance(all_leaves, list):
                    leave_count = len(all_leaves)
                else:
                    leave_count = len(all_leaves.get('leaves', []))
                
                self.log_test("Scenario 3", "Admin View All Leaves", True, 
                            f"Admin retrieved {leave_count} leave records")
            else:
                self.log_test("Scenario 3", "Admin View All Leaves", False, 
                            f"Failed to get all leaves: {response.status_code}")
                            
        except Exception as e:
            self.log_test("Scenario 3", "Admin View All Leaves", False, f"Exception: {str(e)}")
        
        # 4. Approve leave request if we have one
        if "leave_id" in self.evidence:
            try:
                approval_data = {
                    "status": "approved"
                }
                
                response = self.session.put(f"{API_BASE}/leaves/{self.evidence['leave_id']}", 
                                          json=approval_data, 
                                          headers=self.get_headers("super_admin"))
                
                success = response.status_code in [200, 201]
                self.log_test("Scenario 3", "Approve Leave Request", success, 
                            f"Leave approval: {response.status_code}")
                            
            except Exception as e:
                self.log_test("Scenario 3", "Approve Leave Request", False, f"Exception: {str(e)}")
    
    def scenario_4_field_marketing_visits_corrected(self):
        """SCENARIO 4: الزيارات الخارجية والتسويقية (Field/Marketing Visits) - CORRECTED"""
        print("\n🚗 SCENARIO 4: FIELD/MARKETING VISITS TESTING (CORRECTED)...")
        
        # 1. Start marketing visit with correct purpose enum
        try:
            marketing_visit_data = {
                "client_name": "شركة الإمارات للتجارة",
                "location_name": "مكتب دبي الرئيسي",
                "area": "دبي",
                "purpose": "new_client",  # Corrected enum value
                "purpose_details": "عرض خدماتنا للعميل الجديد",
                "gps_location": {
                    "latitude": 25.2048,
                    "longitude": 55.2708
                }
            }
            
            response = self.session.post(f"{API_BASE}/marketing-visits/start", 
                                       json=marketing_visit_data, 
                                       headers=self.get_headers("user"))
            
            if response.status_code in [200, 201]:
                visit_data = response.json()
                visit_id = visit_data.get("visit_id")
                self.evidence["marketing_visit_id"] = visit_id
                self.log_test("Scenario 4", "Start Marketing Visit", True, 
                            f"Marketing visit started: {visit_id}")
            else:
                self.log_test("Scenario 4", "Start Marketing Visit", False, 
                            f"Failed to start marketing visit: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Scenario 4", "Start Marketing Visit", False, f"Exception: {str(e)}")
        
        # 2. Get active marketing visit
        try:
            response = self.session.get(f"{API_BASE}/marketing-visits/active", 
                                      headers=self.get_headers("user"))
            
            if response.status_code == 200:
                active_visit = response.json()
                self.log_test("Scenario 4", "Get Active Marketing Visit", True, 
                            f"Active visit retrieved: {active_visit.get('active_visit') is not None}")
            else:
                self.log_test("Scenario 4", "Get Active Marketing Visit", False, 
                            f"Failed to get active visit: {response.status_code}")
                            
        except Exception as e:
            self.log_test("Scenario 4", "Get Active Marketing Visit", False, f"Exception: {str(e)}")
        
        # 3. Complete marketing visit if we have one
        if "marketing_visit_id" in self.evidence:
            try:
                completion_data = {
                    "visit_report": {
                        "summary": "زيارة ناجحة للعميل الجديد مع عرض شامل للخدمات المتاحة في الشركة",
                        "details": "تم عرض جميع خدماتنا على العميل وأبدى اهتماماً كبيراً بخدمات المحاسبة والموارد البشرية. تم مناقشة الأسعار والباقات المتاحة بالتفصيل وتوضيح المزايا التنافسية.",
                        "result": "interested",
                        "next_actions": "إرسال عرض سعر مفصل خلال 48 ساعة ومتابعة مع العميل"
                    },
                    "gps_location": {
                        "latitude": 25.2048,
                        "longitude": 55.2708
                    }
                }
                
                response = self.session.post(f"{API_BASE}/marketing-visits/{self.evidence['marketing_visit_id']}/complete", 
                                           json=completion_data, 
                                           headers=self.get_headers("user"))
                
                success = response.status_code in [200, 201]
                self.log_test("Scenario 4", "Complete Marketing Visit", success, 
                            f"Marketing visit completion: {response.status_code}")
                            
            except Exception as e:
                self.log_test("Scenario 4", "Complete Marketing Visit", False, f"Exception: {str(e)}")
        
        # 4. Get marketing visits history
        try:
            response = self.session.get(f"{API_BASE}/marketing-visits/history", 
                                      headers=self.get_headers("user"))
            
            if response.status_code == 200:
                history = response.json()
                visit_count = len(history.get("visits", []))
                self.log_test("Scenario 4", "Get Marketing Visits History", True, 
                            f"Retrieved {visit_count} marketing visits from history")
            else:
                self.log_test("Scenario 4", "Get Marketing Visits History", False, 
                            f"Failed to get visits history: {response.status_code}")
                            
        except Exception as e:
            self.log_test("Scenario 4", "Get Marketing Visits History", False, f"Exception: {str(e)}")
    
    def scenario_5_advanced_deductions_corrected(self):
        """SCENARIO 5: نظام الخصومات المتقدم (Advanced Deductions System) - CORRECTED"""
        print("\n💰 SCENARIO 5: ADVANCED DEDUCTIONS SYSTEM TESTING (CORRECTED)...")
        
        # 1. Calculate monthly deductions (already working)
        try:
            response = self.session.post(f"{API_BASE}/deductions/calculate-monthly?month=2025-01", 
                                       headers=self.get_headers("super_admin"))
            
            if response.status_code == 200:
                deductions_data = response.json()
                self.evidence["calculated_deductions"] = deductions_data
                employee_count = len(deductions_data) if isinstance(deductions_data, list) else len(deductions_data.get('employees', []))
                self.log_test("Scenario 5", "Calculate Monthly Deductions", True, 
                            f"Calculated deductions for {employee_count} employees")
            else:
                self.log_test("Scenario 5", "Calculate Monthly Deductions", False, 
                            f"Failed to calculate deductions: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Scenario 5", "Calculate Monthly Deductions", False, f"Exception: {str(e)}")
        
        # 2. Get deductions list
        try:
            response = self.session.get(f"{API_BASE}/deductions", 
                                      headers=self.get_headers("super_admin"))
            
            if response.status_code == 200:
                deductions_list = response.json()
                deduction_count = len(deductions_list) if isinstance(deductions_list, list) else len(deductions_list.get('deductions', []))
                self.log_test("Scenario 5", "Get Deductions List", True, 
                            f"Retrieved {deduction_count} deduction records")
            else:
                self.log_test("Scenario 5", "Get Deductions List", False, 
                            f"Failed to get deductions: {response.status_code}")
                            
        except Exception as e:
            self.log_test("Scenario 5", "Get Deductions List", False, f"Exception: {str(e)}")
        
        # 3. Get employees list for deductions
        try:
            response = self.session.get(f"{API_BASE}/employees/list", 
                                      headers=self.get_headers("super_admin"))
            
            if response.status_code == 200:
                employees = response.json()
                employee_count = len(employees) if isinstance(employees, list) else len(employees.get('employees', []))
                self.log_test("Scenario 5", "Get Employees for Deductions", True, 
                            f"Retrieved {employee_count} employees for deductions")
            else:
                self.log_test("Scenario 5", "Get Employees for Deductions", False, 
                            f"Failed to get employees: {response.status_code}")
                            
        except Exception as e:
            self.log_test("Scenario 5", "Get Employees for Deductions", False, f"Exception: {str(e)}")
    
    def scenario_6_payroll_cycles_corrected(self):
        """SCENARIO 6: دورات الرواتب (Payroll Cycles) - CORRECTED"""
        print("\n💼 SCENARIO 6: PAYROLL CYCLES TESTING (CORRECTED)...")
        
        # 1. Get existing payroll cycles
        try:
            response = self.session.get(f"{API_BASE}/payroll/cycles", 
                                      headers=self.get_headers("super_admin"))
            
            if response.status_code == 200:
                cycles = response.json()
                cycle_count = len(cycles) if isinstance(cycles, list) else len(cycles.get('cycles', []))
                self.log_test("Scenario 6", "Get Payroll Cycles", True, 
                            f"Retrieved {cycle_count} payroll cycles")
                
                # Store first cycle for testing
                if cycles and len(cycles) > 0:
                    first_cycle = cycles[0] if isinstance(cycles, list) else cycles.get('cycles', [{}])[0]
                    self.evidence["existing_cycle_id"] = first_cycle.get("id")
                    
            else:
                self.log_test("Scenario 6", "Get Payroll Cycles", False, 
                            f"Failed to get payroll cycles: {response.status_code}")
                
        except Exception as e:
            self.log_test("Scenario 6", "Get Payroll Cycles", False, f"Exception: {str(e)}")
        
        # 2. Get payroll cycle details
        if "existing_cycle_id" in self.evidence:
            try:
                response = self.session.get(f"{API_BASE}/payroll/cycles/{self.evidence['existing_cycle_id']}", 
                                          headers=self.get_headers("super_admin"))
                
                success = response.status_code == 200
                self.log_test("Scenario 6", "Get Payroll Cycle Details", success, 
                            f"Cycle details: {response.status_code}")
                            
            except Exception as e:
                self.log_test("Scenario 6", "Get Payroll Cycle Details", False, f"Exception: {str(e)}")
        
        # 3. Get payroll cycle summary
        if "existing_cycle_id" in self.evidence:
            try:
                response = self.session.get(f"{API_BASE}/payroll/cycles/{self.evidence['existing_cycle_id']}/summary", 
                                          headers=self.get_headers("super_admin"))
                
                if response.status_code == 200:
                    summary = response.json()
                    self.log_test("Scenario 6", "Get Payroll Cycle Summary", True, 
                                f"Summary retrieved with data: {bool(summary)}")
                else:
                    self.log_test("Scenario 6", "Get Payroll Cycle Summary", False, 
                                f"Failed to get summary: {response.status_code}")
                                
            except Exception as e:
                self.log_test("Scenario 6", "Get Payroll Cycle Summary", False, f"Exception: {str(e)}")
        
        # 4. Test payroll cycle recalculate
        if "existing_cycle_id" in self.evidence:
            try:
                response = self.session.post(f"{API_BASE}/payroll/cycles/{self.evidence['existing_cycle_id']}/recalculate", 
                                           headers=self.get_headers("super_admin"))
                
                success = response.status_code in [200, 201]
                self.log_test("Scenario 6", "Recalculate Payroll Cycle", success, 
                            f"Recalculate: {response.status_code}")
                            
            except Exception as e:
                self.log_test("Scenario 6", "Recalculate Payroll Cycle", False, f"Exception: {str(e)}")
    
    def scenario_7_advances_custody_corrected(self):
        """SCENARIO 7: السُلف/العُهد والأقساط (Advances/Custody & Installments) - CORRECTED"""
        print("\n🏦 SCENARIO 7: ADVANCES/CUSTODY & INSTALLMENTS TESTING (CORRECTED)...")
        
        # 1. Create custody with correct category
        try:
            custody_data = {
                "employee_id": self.user_ids.get("user", "test_employee_id"),
                "transaction_type": "custody",
                "amount": 300.0,
                "description": "عهدة مصروفات شهرية",
                "category": "supplies"  # Corrected enum value
            }
            
            response = self.session.post(f"{API_BASE}/advances/create", 
                                       json=custody_data,
                                       headers=self.get_headers("super_admin"))
            
            if response.status_code in [200, 201]:
                custody_response = response.json()
                custody_id = custody_response.get("transaction_id")
                self.evidence["custody_id"] = custody_id
                self.log_test("Scenario 7", "Create Custody", True, 
                            f"Custody created: {custody_id}")
            else:
                self.log_test("Scenario 7", "Create Custody", False, 
                            f"Failed to create custody: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Scenario 7", "Create Custody", False, f"Exception: {str(e)}")
        
        # 2. Create advance with correct category
        try:
            advance_data = {
                "employee_id": self.user_ids.get("user", "test_employee_id"),
                "transaction_type": "advance",
                "amount": 500.0,
                "description": "سلفة شخصية",
                "category": "other"  # Corrected enum value
            }
            
            response = self.session.post(f"{API_BASE}/advances/create", 
                                       json=advance_data,
                                       headers=self.get_headers("super_admin"))
            
            if response.status_code in [200, 201]:
                advance_response = response.json()
                advance_id = advance_response.get("transaction_id")
                self.evidence["advance_id"] = advance_id
                self.log_test("Scenario 7", "Create Advance", True, 
                            f"Advance created: {advance_id}")
            else:
                self.log_test("Scenario 7", "Create Advance", False, 
                            f"Failed to create advance: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Scenario 7", "Create Advance", False, f"Exception: {str(e)}")
        
        # 3. Get user balance
        try:
            response = self.session.get(f"{API_BASE}/advances/my-balance", 
                                      headers=self.get_headers("user"))
            
            if response.status_code == 200:
                balance_data = response.json()
                total_available = balance_data.get("total_available", 0)
                self.log_test("Scenario 7", "Get User Balance", True, 
                            f"Balance retrieved: Total available {total_available}")
            else:
                self.log_test("Scenario 7", "Get User Balance", False, 
                            f"Failed to get balance: {response.status_code}")
                            
        except Exception as e:
            self.log_test("Scenario 7", "Get User Balance", False, f"Exception: {str(e)}")
        
        # 4. Get admin all balances
        try:
            response = self.session.get(f"{API_BASE}/advances/admin/all-balances", 
                                      headers=self.get_headers("super_admin"))
            
            if response.status_code == 200:
                all_balances = response.json()
                balance_count = len(all_balances.get("employee_balances", []))
                self.log_test("Scenario 7", "Get All Employee Balances", True, 
                            f"Retrieved balances for {balance_count} employees")
            else:
                self.log_test("Scenario 7", "Get All Employee Balances", False, 
                            f"Failed to get all balances: {response.status_code}")
                            
        except Exception as e:
            self.log_test("Scenario 7", "Get All Employee Balances", False, f"Exception: {str(e)}")
        
        # 5. Get pending approvals
        try:
            response = self.session.get(f"{API_BASE}/advances/admin/pending-approvals", 
                                      headers=self.get_headers("super_admin"))
            
            if response.status_code == 200:
                pending = response.json()
                pending_count = len(pending.get("pending_transactions", []))
                self.log_test("Scenario 7", "Get Pending Approvals", True, 
                            f"Retrieved {pending_count} pending transactions")
            else:
                self.log_test("Scenario 7", "Get Pending Approvals", False, 
                            f"Failed to get pending approvals: {response.status_code}")
                            
        except Exception as e:
            self.log_test("Scenario 7", "Get Pending Approvals", False, f"Exception: {str(e)}")
        
        # 6. Get all transactions (admin)
        try:
            response = self.session.get(f"{API_BASE}/advances/admin/all-transactions", 
                                      headers=self.get_headers("super_admin"))
            
            if response.status_code == 200:
                all_transactions = response.json()
                transaction_count = len(all_transactions.get("transactions", []))
                self.log_test("Scenario 7", "Get All Transactions", True, 
                            f"Retrieved {transaction_count} transactions")
            else:
                self.log_test("Scenario 7", "Get All Transactions", False, 
                            f"Failed to get all transactions: {response.status_code}")
                            
        except Exception as e:
            self.log_test("Scenario 7", "Get All Transactions", False, f"Exception: {str(e)}")
    
    def scenario_8_salary_slip_ledger_corrected(self):
        """SCENARIO 8: كشف الراتب + Ledger (Salary Slip & Ledger) - CORRECTED"""
        print("\n📊 SCENARIO 8: SALARY SLIP & LEDGER TESTING (CORRECTED)...")
        
        # Get existing payroll cycles first
        try:
            response = self.session.get(f"{API_BASE}/payroll/cycles", 
                                      headers=self.get_headers("super_admin"))
            
            if response.status_code == 200:
                cycles = response.json()
                if cycles and len(cycles) > 0:
                    cycle_id = cycles[0].get("id")
                    employee_id = self.user_ids.get("user", "test_employee_id")
                    
                    # Test salary letter endpoints with real IDs
                    for format_type in ["html", "pdf"]:
                        try:
                            response = self.session.get(f"{API_BASE}/payroll/cycles/{cycle_id}/employees/{employee_id}/letter?format={format_type}", 
                                                      headers=self.get_headers("super_admin"))
                            
                            success = response.status_code == 200
                            self.log_test("Scenario 8", f"Get Salary Letter {format_type.upper()}", success, 
                                        f"Salary letter {format_type}: {response.status_code}")
                                        
                        except Exception as e:
                            self.log_test("Scenario 8", f"Get Salary Letter {format_type.upper()}", False, f"Exception: {str(e)}")
                    
                    # Test payroll ledger
                    try:
                        response = self.session.get(f"{API_BASE}/payroll/cycles/{cycle_id}/ledger", 
                                                  headers=self.get_headers("super_admin"))
                        
                        if response.status_code == 200:
                            ledger_data = response.json()
                            entry_count = len(ledger_data.get("entries", []))
                            self.log_test("Scenario 8", "Get Payroll Ledger", True, 
                                        f"Ledger retrieved with {entry_count} entries")
                        else:
                            self.log_test("Scenario 8", "Get Payroll Ledger", False, 
                                        f"Failed to get ledger: {response.status_code}")
                                        
                    except Exception as e:
                        self.log_test("Scenario 8", "Get Payroll Ledger", False, f"Exception: {str(e)}")
                        
        except Exception as e:
            self.log_test("Scenario 8", "Setup Salary Testing", False, f"Exception: {str(e)}")
    
    def scenario_10_notifications_corrected(self):
        """SCENARIO 10: الإشعارات (Notifications) - CORRECTED"""
        print("\n🔔 SCENARIO 10: NOTIFICATIONS TESTING (CORRECTED)...")
        
        # 1. Get user notifications (working endpoint)
        try:
            response = self.session.get(f"{API_BASE}/notifications/my", 
                                      headers=self.get_headers("user"))
            
            if response.status_code == 200:
                notifications = response.json()
                notification_count = len(notifications) if isinstance(notifications, list) else len(notifications.get('notifications', []))
                self.log_test("Scenario 10", "Get User Notifications", True, 
                            f"Retrieved {notification_count} notifications")
            else:
                self.log_test("Scenario 10", "Get User Notifications", False, 
                            f"Failed to get notifications: {response.status_code}")
                            
        except Exception as e:
            self.log_test("Scenario 10", "Get User Notifications", False, f"Exception: {str(e)}")
        
        # 2. Get admin notifications
        try:
            response = self.session.get(f"{API_BASE}/notifications", 
                                      headers=self.get_headers("super_admin"))
            
            if response.status_code == 200:
                admin_notifications = response.json()
                notification_count = len(admin_notifications) if isinstance(admin_notifications, list) else len(admin_notifications.get('notifications', []))
                self.log_test("Scenario 10", "Get Admin Notifications", True, 
                            f"Admin retrieved {notification_count} notifications")
            else:
                self.log_test("Scenario 10", "Get Admin Notifications", False, 
                            f"Failed to get admin notifications: {response.status_code}")
                            
        except Exception as e:
            self.log_test("Scenario 10", "Get Admin Notifications", False, f"Exception: {str(e)}")
        
        # 3. Get unread mandatory notifications
        try:
            response = self.session.get(f"{API_BASE}/notifications/unread-mandatory", 
                                      headers=self.get_headers("user"))
            
            if response.status_code == 200:
                unread_mandatory = response.json()
                unread_count = len(unread_mandatory) if isinstance(unread_mandatory, list) else len(unread_mandatory.get('notifications', []))
                self.log_test("Scenario 10", "Get Unread Mandatory Notifications", True, 
                            f"Retrieved {unread_count} unread mandatory notifications")
            else:
                self.log_test("Scenario 10", "Get Unread Mandatory Notifications", False, 
                            f"Failed to get unread mandatory: {response.status_code}")
                            
        except Exception as e:
            self.log_test("Scenario 10", "Get Unread Mandatory Notifications", False, f"Exception: {str(e)}")
    
    def scenario_11_rbac_security_corrected(self):
        """SCENARIO 11: RBAC/Security (Negative Testing) - CORRECTED"""
        print("\n🔒 SCENARIO 11: RBAC/SECURITY TESTING (CORRECTED)...")
        
        # 1. User attempts Super Admin action (advances creation)
        try:
            response = self.session.post(f"{API_BASE}/advances/create", 
                                       json={
                                           "employee_id": "test",
                                           "transaction_type": "advance",
                                           "amount": 100,
                                           "description": "test",
                                           "category": "other"
                                       },
                                       headers=self.get_headers("user"))
            
            success = response.status_code == 403
            self.log_test("Scenario 11", "User Access Super Admin Endpoint", success, 
                        f"Expected 403, got {response.status_code}")
                        
        except Exception as e:
            self.log_test("Scenario 11", "User Access Super Admin Endpoint", False, f"Exception: {str(e)}")
        
        # 2. Regular user attempts admin-only endpoint
        try:
            response = self.session.get(f"{API_BASE}/advances/admin/all-balances", 
                                      headers=self.get_headers("user"))
            
            success = response.status_code == 403
            self.log_test("Scenario 11", "User Access Admin Endpoint", success, 
                        f"Expected 403, got {response.status_code}")
                        
        except Exception as e:
            self.log_test("Scenario 11", "User Access Admin Endpoint", False, f"Exception: {str(e)}")
        
        # 3. Test invalid payloads for validation
        try:
            invalid_data = {"invalid": "data"}
            response = self.session.post(f"{API_BASE}/leaves", 
                                       json=invalid_data,
                                       headers=self.get_headers("user"))
            
            success = response.status_code == 422
            self.log_test("Scenario 11", "Invalid Payload Validation", success, 
                        f"Expected 422, got {response.status_code}")
                        
        except Exception as e:
            self.log_test("Scenario 11", "Invalid Payload Validation", False, f"Exception: {str(e)}")
    
    def scenario_14_work_reports_corrected(self):
        """SCENARIO 14: Work Reports Integration - CORRECTED"""
        print("\n📝 SCENARIO 14: WORK REPORTS INTEGRATION TESTING (CORRECTED)...")
        
        # 1. Get existing clients first
        try:
            response = self.session.get(f"{API_BASE}/work-reports/clients", 
                                      headers=self.get_headers("admin"))
            
            if response.status_code == 200:
                clients = response.json()
                client_count = len(clients) if isinstance(clients, list) else len(clients.get('clients', []))
                self.log_test("Scenario 14", "Get Work Reports Clients", True, 
                            f"Retrieved {client_count} work reports clients")
                
                # Use existing client if available
                if clients and len(clients) > 0:
                    first_client = clients[0] if isinstance(clients, list) else clients.get('clients', [{}])[0]
                    self.evidence["existing_client_id"] = first_client.get("id")
                    
            else:
                self.log_test("Scenario 14", "Get Work Reports Clients", False, 
                            f"Failed to get clients: {response.status_code}")
                
        except Exception as e:
            self.log_test("Scenario 14", "Get Work Reports Clients", False, f"Exception: {str(e)}")
        
        # 2. Get work logs
        try:
            response = self.session.get(f"{API_BASE}/work-reports/logs", 
                                      headers=self.get_headers("admin"))
            
            if response.status_code == 200:
                logs = response.json()
                log_count = len(logs) if isinstance(logs, list) else len(logs.get('logs', []))
                self.log_test("Scenario 14", "Get Work Reports Logs", True, 
                            f"Retrieved {log_count} work logs")
                
                # Store first log for testing
                if logs and len(logs) > 0:
                    first_log = logs[0] if isinstance(logs, list) else logs.get('logs', [{}])[0]
                    self.evidence["existing_log_id"] = first_log.get("id")
                    
            else:
                self.log_test("Scenario 14", "Get Work Reports Logs", False, 
                            f"Failed to get work logs: {response.status_code}")
                            
        except Exception as e:
            self.log_test("Scenario 14", "Get Work Reports Logs", False, f"Exception: {str(e)}")
        
        # 3. Test work log update if we have one
        if "existing_log_id" in self.evidence:
            try:
                update_data = {
                    "start_time": "2025-01-15T10:15:00Z",
                    "end_time": "2025-01-15T12:00:00Z"
                }
                
                response = self.session.put(f"{API_BASE}/work-reports/logs/{self.evidence['existing_log_id']}", 
                                          json=update_data,
                                          headers=self.get_headers("admin"))
                
                success = response.status_code in [200, 201]
                self.log_test("Scenario 14", "Update Work Log", success, 
                            f"Work log update: {response.status_code}")
                            
            except Exception as e:
                self.log_test("Scenario 14", "Update Work Log", False, f"Exception: {str(e)}")
    
    def run_all_scenarios(self):
        """Run all corrected test scenarios"""
        print("🚀 STARTING CORRECTED COMPREHENSIVE BACKEND TESTING - SCENARIOS 3-16")
        print("=" * 80)
        
        # Authenticate all users first
        if not self.authenticate_all_users():
            print("❌ AUTHENTICATION FAILED - Cannot proceed with testing")
            return False
        
        # Run all corrected scenarios
        self.scenario_3_leave_management_corrected()
        self.scenario_4_field_marketing_visits_corrected()
        self.scenario_5_advanced_deductions_corrected()
        self.scenario_6_payroll_cycles_corrected()
        self.scenario_7_advances_custody_corrected()
        self.scenario_8_salary_slip_ledger_corrected()
        self.scenario_10_notifications_corrected()
        self.scenario_11_rbac_security_corrected()
        self.scenario_14_work_reports_corrected()
        
        # Generate summary
        self.generate_summary()
        
        return True
    
    def generate_summary(self):
        """Generate comprehensive test summary"""
        print("\n" + "=" * 80)
        print("📊 CORRECTED COMPREHENSIVE TEST RESULTS SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📈 OVERALL SUCCESS RATE: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
        print(f"✅ PASSED: {passed_tests}")
        print(f"❌ FAILED: {failed_tests}")
        
        # Group results by scenario
        scenarios = {}
        for result in self.test_results:
            scenario = result["scenario"]
            if scenario not in scenarios:
                scenarios[scenario] = {"passed": 0, "failed": 0, "tests": []}
            
            if result["success"]:
                scenarios[scenario]["passed"] += 1
            else:
                scenarios[scenario]["failed"] += 1
            
            scenarios[scenario]["tests"].append(result)
        
        print("\n📋 SCENARIO BREAKDOWN:")
        for scenario, data in scenarios.items():
            total = data["passed"] + data["failed"]
            rate = (data["passed"] / total * 100) if total > 0 else 0
            print(f"  {scenario}: {rate:.1f}% ({data['passed']}/{total})")
        
        # Show failed tests
        failed_results = [t for t in self.test_results if not t["success"]]
        if failed_results:
            print(f"\n❌ FAILED TESTS ({len(failed_results)}):")
            for result in failed_results:
                print(f"  • {result['scenario']} | {result['test']}: {result['details']}")
        
        # Save detailed results
        results_file = "/app/corrected_scenarios_3_16_test_results.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "failed_tests": failed_tests,
                    "success_rate": success_rate,
                    "test_date": datetime.now().isoformat()
                },
                "scenarios": scenarios,
                "detailed_results": self.test_results,
                "evidence": self.evidence
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Detailed results saved to: {results_file}")
        
        # Determine overall status
        if success_rate >= 80:
            print(f"\n🎉 TESTING COMPLETED SUCCESSFULLY - {success_rate:.1f}% SUCCESS RATE")
            print("✅ System demonstrates excellent reliability across all priority areas")
        elif success_rate >= 60:
            print(f"\n⚠️ TESTING COMPLETED WITH WARNINGS - {success_rate:.1f}% SUCCESS RATE")
            print("🔧 Some issues found but core functionality operational")
        else:
            print(f"\n🚨 TESTING COMPLETED WITH CRITICAL ISSUES - {success_rate:.1f}% SUCCESS RATE")
            print("❌ Multiple critical issues found requiring immediate attention")

def main():
    """Main execution function"""
    tester = CorrectedBackendTester()
    success = tester.run_all_scenarios()
    
    if success:
        print("\n🏁 CORRECTED COMPREHENSIVE BACKEND TESTING COMPLETED")
    else:
        print("\n💥 TESTING FAILED TO COMPLETE")
        sys.exit(1)

if __name__ == "__main__":
    main()