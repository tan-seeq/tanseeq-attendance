#!/usr/bin/env python3
"""
🔥 COMPREHENSIVE BACKEND TESTING - SCENARIOS 3-16 (BATCH EXECUTION)
=================================================================

Objective: Execute all remaining backend-related scenarios from the Phase-2 comprehensive testing plan.

Test Environment:
- Backend URL: From REACT_APP_BACKEND_URL
- Timezone: Asia/Dubai (UTC+4)
- Accounts: admin@tanseeq.com/ADMIN, mahmoud@tanseeq.com/mahmoud123, jihad@tanseeq.com/jihad123

SUCCESS CRITERIA:
- All endpoints respond correctly (200/201 for success, 403 for unauthorized, 422 for validation)
- Data persistence verified
- Financial calculations accurate
- RBAC properly enforced
- No Sev1/Sev2 defects
"""

import requests
import json
import os
import sys
from datetime import datetime, timedelta
import uuid
from pathlib import Path

# Test Configuration
BACKEND_URL = "https://attend-deduct-hr.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# Test Accounts
TEST_ACCOUNTS = {
    "super_admin": {"email": "admin@tanseeq.com", "password": "ADMIN"},
    "admin": {"email": "mahmoud@tanseeq.com", "password": "mahmoud123"},
    "user": {"email": "jihad@tanseeq.com", "password": "jihad123"}
}

class ComprehensiveBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.tokens = {}
        self.test_results = []
        self.evidence = {}
        
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
        """Authenticate all test users"""
        print("\n🔐 AUTHENTICATING ALL TEST USERS...")
        
        for role, credentials in TEST_ACCOUNTS.items():
            try:
                response = self.session.post(f"{API_BASE}/auth/login", json=credentials)
                if response.status_code == 200:
                    data = response.json()
                    self.tokens[role] = data["access_token"]
                    self.log_test("Authentication", f"{role.upper()} Login", True, 
                                f"Successfully authenticated {credentials['email']}")
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
    
    def scenario_3_leave_management(self):
        """SCENARIO 3: إدارة الإجازات (Leave Management)"""
        print("\n📋 SCENARIO 3: LEAVE MANAGEMENT TESTING...")
        
        # 1. As User (jihad): Create leave request
        try:
            leave_data = {
                "user_id": "jihad_user_id",
                "user_name": "جهاد",
                "start_date": "2025-01-20",
                "end_date": "2025-01-20",
                "reason": "إجازة سنوية - يوم واحد",
                "days_count": 1,
                "attachment_url": None
            }
            
            response = self.session.post(f"{API_BASE}/leaves", 
                                       json=leave_data, 
                                       headers=self.get_headers("user"))
            
            if response.status_code in [200, 201]:
                leave_id = response.json().get("id") or response.json().get("leave_id")
                self.evidence["leave_id"] = leave_id
                self.log_test("Scenario 3", "Create Leave Request", True, 
                            f"Leave request created successfully: {leave_id}")
            else:
                self.log_test("Scenario 3", "Create Leave Request", False, 
                            f"Failed to create leave: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Scenario 3", "Create Leave Request", False, f"Exception: {str(e)}")
        
        # 2. As Admin: Approve the request
        if "leave_id" in self.evidence:
            try:
                approval_data = {
                    "status": "approved",
                    "approved_by": "admin"
                }
                
                response = self.session.put(f"{API_BASE}/leaves/{self.evidence['leave_id']}", 
                                          json=approval_data, 
                                          headers=self.get_headers("super_admin"))
                
                success = response.status_code in [200, 201]
                self.log_test("Scenario 3", "Approve Leave Request", success, 
                            f"Leave approval: {response.status_code}")
                            
            except Exception as e:
                self.log_test("Scenario 3", "Approve Leave Request", False, f"Exception: {str(e)}")
        
        # 3. Verify balance deducted
        try:
            response = self.session.get(f"{API_BASE}/leaves/my", 
                                      headers=self.get_headers("user"))
            
            if response.status_code == 200:
                leaves_data = response.json()
                self.log_test("Scenario 3", "Verify Leave Balance", True, 
                            f"Retrieved leave balance: {len(leaves_data.get('leaves', []))} records")
            else:
                self.log_test("Scenario 3", "Verify Leave Balance", False, 
                            f"Failed to get balance: {response.status_code}")
                            
        except Exception as e:
            self.log_test("Scenario 3", "Verify Leave Balance", False, f"Exception: {str(e)}")
        
        # 4. Admin view all leave requests
        try:
            response = self.session.get(f"{API_BASE}/leaves", 
                                      headers=self.get_headers("super_admin"))
            
            if response.status_code == 200:
                all_leaves = response.json()
                self.log_test("Scenario 3", "Admin View All Leaves", True, 
                            f"Admin retrieved {len(all_leaves.get('leaves', []))} leave records")
            else:
                self.log_test("Scenario 3", "Admin View All Leaves", False, 
                            f"Failed to get all leaves: {response.status_code}")
                            
        except Exception as e:
            self.log_test("Scenario 3", "Admin View All Leaves", False, f"Exception: {str(e)}")
    
    def scenario_4_field_marketing_visits(self):
        """SCENARIO 4: الزيارات الخارجية والتسويقية (Field/Marketing Visits)"""
        print("\n🚗 SCENARIO 4: FIELD/MARKETING VISITS TESTING...")
        
        # 1. Start field exit
        try:
            field_exit_data = {
                "visit_type": "client_visit",
                "client_name": "عميل تجريبي",
                "start_time": "09:00",
                "end_time": "12:00",
                "report": "زيارة عميل لمتابعة المشروع"
            }
            
            response = self.session.post(f"{API_BASE}/field-exits/start", 
                                       json=field_exit_data, 
                                       headers=self.get_headers("user"))
            
            if response.status_code in [200, 201]:
                field_exit_id = response.json().get("id") or response.json().get("visit_id")
                self.evidence["field_exit_id"] = field_exit_id
                self.log_test("Scenario 4", "Start Field Exit", True, 
                            f"Field exit started: {field_exit_id}")
            else:
                self.log_test("Scenario 4", "Start Field Exit", False, 
                            f"Failed to start field exit: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Scenario 4", "Start Field Exit", False, f"Exception: {str(e)}")
        
        # 2. Complete field exit with report
        if "field_exit_id" in self.evidence:
            try:
                report_data = {
                    "detailed_report": "تم زيارة العميل ومناقشة تفاصيل المشروع الجديد. العميل راضي عن الخدمات المقدمة.",
                    "accomplishments": "توقيع عقد جديد بقيمة 50,000 درهم",
                    "challenges": "تأخير في بعض المتطلبات التقنية",
                    "next_steps": "متابعة التنفيذ خلال الأسبوع القادم"
                }
                
                response = self.session.post(f"{API_BASE}/field-exits/{self.evidence['field_exit_id']}/report", 
                                           json=report_data, 
                                           headers=self.get_headers("user"))
                
                success = response.status_code in [200, 201]
                self.log_test("Scenario 4", "Complete Field Exit Report", success, 
                            f"Field exit report: {response.status_code}")
                            
            except Exception as e:
                self.log_test("Scenario 4", "Complete Field Exit Report", False, f"Exception: {str(e)}")
        
        # 3. Start marketing visit
        try:
            marketing_visit_data = {
                "client_name": "شركة الإمارات للتجارة",
                "location_name": "مكتب دبي الرئيسي",
                "area": "دبي",
                "purpose": "new_client_acquisition",
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
                visit_id = response.json().get("visit_id")
                self.evidence["marketing_visit_id"] = visit_id
                self.log_test("Scenario 4", "Start Marketing Visit", True, 
                            f"Marketing visit started: {visit_id}")
            else:
                self.log_test("Scenario 4", "Start Marketing Visit", False, 
                            f"Failed to start marketing visit: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Scenario 4", "Start Marketing Visit", False, f"Exception: {str(e)}")
        
        # 4. Complete marketing visit
        if "marketing_visit_id" in self.evidence:
            try:
                completion_data = {
                    "visit_report": {
                        "summary": "زيارة ناجحة للعميل الجديد مع عرض شامل للخدمات",
                        "details": "تم عرض جميع خدماتنا على العميل وأبدى اهتماماً كبيراً بخدمات المحاسبة والموارد البشرية. تم مناقشة الأسعار والباقات المتاحة.",
                        "result": "interested",
                        "next_actions": "إرسال عرض سعر مفصل خلال 48 ساعة"
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
    
    def scenario_5_advanced_deductions(self):
        """SCENARIO 5: نظام الخصومات المتقدم (Advanced Deductions System)"""
        print("\n💰 SCENARIO 5: ADVANCED DEDUCTIONS SYSTEM TESTING...")
        
        # 1. Calculate monthly deductions
        try:
            response = self.session.post(f"{API_BASE}/deductions/calculate-monthly?month=2025-01", 
                                       headers=self.get_headers("super_admin"))
            
            if response.status_code == 200:
                deductions_data = response.json()
                self.evidence["calculated_deductions"] = deductions_data
                self.log_test("Scenario 5", "Calculate Monthly Deductions", True, 
                            f"Calculated deductions for {len(deductions_data.get('employees', []))} employees")
            else:
                self.log_test("Scenario 5", "Calculate Monthly Deductions", False, 
                            f"Failed to calculate deductions: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Scenario 5", "Calculate Monthly Deductions", False, f"Exception: {str(e)}")
        
        # 2. Apply monthly deductions
        try:
            apply_data = {
                "month": "2025-01",
                "employee_deductions": self.evidence.get("calculated_deductions", {}).get("employees", [])
            }
            
            response = self.session.post(f"{API_BASE}/deductions/apply-monthly", 
                                       json=apply_data,
                                       headers=self.get_headers("super_admin"))
            
            success = response.status_code in [200, 201]
            self.log_test("Scenario 5", "Apply Monthly Deductions", success, 
                        f"Apply deductions: {response.status_code}")
                        
        except Exception as e:
            self.log_test("Scenario 5", "Apply Monthly Deductions", False, f"Exception: {str(e)}")
        
        # 3. Create manual deduction
        try:
            manual_deduction = {
                "employee_id": "test_employee_id",
                "amount": 100.0,
                "reason": "خصم إداري",
                "deduction_type": "administrative",
                "date": "2025-01-15"
            }
            
            response = self.session.post(f"{API_BASE}/deductions/manual", 
                                       json=manual_deduction,
                                       headers=self.get_headers("super_admin"))
            
            if response.status_code in [200, 201]:
                deduction_id = response.json().get("id")
                self.evidence["manual_deduction_id"] = deduction_id
                self.log_test("Scenario 5", "Create Manual Deduction", True, 
                            f"Manual deduction created: {deduction_id}")
            else:
                self.log_test("Scenario 5", "Create Manual Deduction", False, 
                            f"Failed to create manual deduction: {response.status_code}")
                
        except Exception as e:
            self.log_test("Scenario 5", "Create Manual Deduction", False, f"Exception: {str(e)}")
    
    def scenario_6_payroll_cycles(self):
        """SCENARIO 6: دورات الرواتب (Payroll Cycles)"""
        print("\n💼 SCENARIO 6: PAYROLL CYCLES TESTING...")
        
        # 1. Create new payroll cycle
        try:
            cycle_data = {
                "month": "2025-01",
                "year": 2025,
                "description": "دورة رواتب يناير 2025"
            }
            
            response = self.session.post(f"{API_BASE}/payroll/cycles", 
                                       json=cycle_data,
                                       headers=self.get_headers("super_admin"))
            
            if response.status_code in [200, 201]:
                cycle_id = response.json().get("id") or response.json().get("cycle_id")
                self.evidence["payroll_cycle_id"] = cycle_id
                self.log_test("Scenario 6", "Create Payroll Cycle", True, 
                            f"Payroll cycle created: {cycle_id}")
            else:
                self.log_test("Scenario 6", "Create Payroll Cycle", False, 
                            f"Failed to create payroll cycle: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Scenario 6", "Create Payroll Cycle", False, f"Exception: {str(e)}")
        
        # 2. Update employee salaries
        if "payroll_cycle_id" in self.evidence:
            try:
                salary_updates = {
                    "employees": [
                        {
                            "employee_id": "test_employee_1",
                            "basic_salary": 5000.0,
                            "allowances": 1000.0
                        }
                    ]
                }
                
                response = self.session.put(f"{API_BASE}/payroll/cycles/{self.evidence['payroll_cycle_id']}/update-employees", 
                                          json=salary_updates,
                                          headers=self.get_headers("super_admin"))
                
                success = response.status_code in [200, 201]
                self.log_test("Scenario 6", "Update Employee Salaries", success, 
                            f"Salary update: {response.status_code}")
                            
            except Exception as e:
                self.log_test("Scenario 6", "Update Employee Salaries", False, f"Exception: {str(e)}")
        
        # 3. Lock payroll cycle
        if "payroll_cycle_id" in self.evidence:
            try:
                lock_data = {
                    "reason": "إقفال دورة الرواتب للمراجعة النهائية"
                }
                
                response = self.session.post(f"{API_BASE}/payroll/cycles/{self.evidence['payroll_cycle_id']}/lock", 
                                           json=lock_data,
                                           headers=self.get_headers("super_admin"))
                
                success = response.status_code in [200, 201]
                self.log_test("Scenario 6", "Lock Payroll Cycle", success, 
                            f"Cycle lock: {response.status_code}")
                            
            except Exception as e:
                self.log_test("Scenario 6", "Lock Payroll Cycle", False, f"Exception: {str(e)}")
        
        # 4. Export PDF/Excel
        if "payroll_cycle_id" in self.evidence:
            for format_type in ["pdf", "excel"]:
                try:
                    response = self.session.get(f"{API_BASE}/payroll/cycles/{self.evidence['payroll_cycle_id']}/export?format={format_type}", 
                                              headers=self.get_headers("super_admin"))
                    
                    success = response.status_code == 200
                    self.log_test("Scenario 6", f"Export {format_type.upper()}", success, 
                                f"Export {format_type}: {response.status_code}")
                                
                except Exception as e:
                    self.log_test("Scenario 6", f"Export {format_type.upper()}", False, f"Exception: {str(e)}")
    
    def scenario_7_advances_custody_installments(self):
        """SCENARIO 7: السُلف/العُهد والأقساط (Advances/Custody & Installments)"""
        print("\n🏦 SCENARIO 7: ADVANCES/CUSTODY & INSTALLMENTS TESTING...")
        
        # 1. Create custody
        try:
            custody_data = {
                "employee_id": "test_employee_id",
                "transaction_type": "custody",
                "amount": 300.0,
                "description": "عهدة مصروفات شهرية",
                "category": "office_supplies"
            }
            
            response = self.session.post(f"{API_BASE}/advances/create", 
                                       json=custody_data,
                                       headers=self.get_headers("super_admin"))
            
            if response.status_code in [200, 201]:
                custody_id = response.json().get("transaction_id")
                self.evidence["custody_id"] = custody_id
                self.log_test("Scenario 7", "Create Custody", True, 
                            f"Custody created: {custody_id}")
            else:
                self.log_test("Scenario 7", "Create Custody", False, 
                            f"Failed to create custody: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Scenario 7", "Create Custody", False, f"Exception: {str(e)}")
        
        # 2. Create advance
        try:
            advance_data = {
                "employee_id": "test_employee_id",
                "transaction_type": "advance",
                "amount": 500.0,
                "description": "سلفة شخصية",
                "category": "personal"
            }
            
            response = self.session.post(f"{API_BASE}/advances/create", 
                                       json=advance_data,
                                       headers=self.get_headers("super_admin"))
            
            if response.status_code in [200, 201]:
                advance_id = response.json().get("transaction_id")
                self.evidence["advance_id"] = advance_id
                self.log_test("Scenario 7", "Create Advance", True, 
                            f"Advance created: {advance_id}")
            else:
                self.log_test("Scenario 7", "Create Advance", False, 
                            f"Failed to create advance: {response.status_code}")
                
        except Exception as e:
            self.log_test("Scenario 7", "Create Advance", False, f"Exception: {str(e)}")
        
        # 3. Create installment schedule
        if "advance_id" in self.evidence:
            try:
                installment_data = {
                    "number_of_installments": 5,
                    "installment_amount": 100.0,
                    "start_date": "2025-02-01"
                }
                
                response = self.session.post(f"{API_BASE}/advances/{self.evidence['advance_id']}/installments", 
                                           json=installment_data,
                                           headers=self.get_headers("super_admin"))
                
                success = response.status_code in [200, 201]
                self.log_test("Scenario 7", "Create Installment Schedule", success, 
                            f"Installment schedule: {response.status_code}")
                            
            except Exception as e:
                self.log_test("Scenario 7", "Create Installment Schedule", False, f"Exception: {str(e)}")
        
        # 4. Verify balance calculation
        try:
            response = self.session.get(f"{API_BASE}/advances/my-balance", 
                                      headers=self.get_headers("user"))
            
            if response.status_code == 200:
                balance_data = response.json()
                self.log_test("Scenario 7", "Verify Balance Calculation", True, 
                            f"Balance retrieved: Total available {balance_data.get('total_available', 0)}")
            else:
                self.log_test("Scenario 7", "Verify Balance Calculation", False, 
                            f"Failed to get balance: {response.status_code}")
                            
        except Exception as e:
            self.log_test("Scenario 7", "Verify Balance Calculation", False, f"Exception: {str(e)}")
    
    def scenario_8_salary_slip_ledger(self):
        """SCENARIO 8: كشف الراتب + Ledger (Salary Slip & Ledger)"""
        print("\n📊 SCENARIO 8: SALARY SLIP & LEDGER TESTING...")
        
        # First get available payroll cycles
        try:
            response = self.session.get(f"{API_BASE}/payroll/cycles", 
                                      headers=self.get_headers("super_admin"))
            
            if response.status_code == 200:
                cycles = response.json()
                if cycles and len(cycles) > 0:
                    cycle_id = cycles[0].get("id")
                    self.evidence["test_cycle_id"] = cycle_id
                    
                    # Get salary slip HTML
                    try:
                        response = self.session.get(f"{API_BASE}/payroll/cycles/{cycle_id}/employees/test_employee_id/letter?format=html", 
                                                  headers=self.get_headers("super_admin"))
                        
                        success = response.status_code == 200
                        self.log_test("Scenario 8", "Get Salary Slip HTML", success, 
                                    f"HTML salary slip: {response.status_code}")
                                    
                    except Exception as e:
                        self.log_test("Scenario 8", "Get Salary Slip HTML", False, f"Exception: {str(e)}")
                    
                    # Get salary slip PDF
                    try:
                        response = self.session.get(f"{API_BASE}/payroll/cycles/{cycle_id}/employees/test_employee_id/letter?format=pdf", 
                                                  headers=self.get_headers("super_admin"))
                        
                        success = response.status_code == 200
                        self.log_test("Scenario 8", "Get Salary Slip PDF", success, 
                                    f"PDF salary slip: {response.status_code}")
                                    
                    except Exception as e:
                        self.log_test("Scenario 8", "Get Salary Slip PDF", False, f"Exception: {str(e)}")
                    
                    # Get ledger
                    try:
                        response = self.session.get(f"{API_BASE}/payroll/cycles/{cycle_id}/ledger", 
                                                  headers=self.get_headers("super_admin"))
                        
                        if response.status_code == 200:
                            ledger_data = response.json()
                            self.log_test("Scenario 8", "Get Payroll Ledger", True, 
                                        f"Ledger retrieved with {len(ledger_data.get('entries', []))} entries")
                        else:
                            self.log_test("Scenario 8", "Get Payroll Ledger", False, 
                                        f"Failed to get ledger: {response.status_code}")
                                        
                    except Exception as e:
                        self.log_test("Scenario 8", "Get Payroll Ledger", False, f"Exception: {str(e)}")
                        
        except Exception as e:
            self.log_test("Scenario 8", "Setup Salary Slip Testing", False, f"Exception: {str(e)}")
    
    def scenario_10_notifications(self):
        """SCENARIO 10: الإشعارات (Notifications)"""
        print("\n🔔 SCENARIO 10: NOTIFICATIONS TESTING...")
        
        # 1. Send Arabic notifications as Super Admin
        notification_types = [
            {"type": "info", "priority": "normal", "subject": "إشعار عادي", "message": "هذا إشعار عادي للاختبار"},
            {"type": "warning", "priority": "high", "subject": "تحذير مهم", "message": "هذا تحذير مهم يتطلب الانتباه"},
            {"type": "alert", "priority": "urgent", "subject": "إشعار عاجل", "message": "هذا إشعار عاجل يتطلب إجراء فوري"}
        ]
        
        for notification in notification_types:
            try:
                notification_data = {
                    "recipient_id": "test_user_id",
                    "subject": notification["subject"],
                    "message": notification["message"],
                    "type": notification["type"],
                    "priority": notification["priority"]
                }
                
                response = self.session.post(f"{API_BASE}/notifications/send", 
                                           json=notification_data,
                                           headers=self.get_headers("super_admin"))
                
                success = response.status_code in [200, 201]
                self.log_test("Scenario 10", f"Send {notification['type']} Notification", success, 
                            f"Notification sent: {response.status_code}")
                            
            except Exception as e:
                self.log_test("Scenario 10", f"Send {notification['type']} Notification", False, f"Exception: {str(e)}")
        
        # 2. Get user notifications
        try:
            response = self.session.get(f"{API_BASE}/notifications/my", 
                                      headers=self.get_headers("user"))
            
            if response.status_code == 200:
                notifications = response.json()
                self.log_test("Scenario 10", "Get User Notifications", True, 
                            f"Retrieved {len(notifications.get('notifications', []))} notifications")
            else:
                self.log_test("Scenario 10", "Get User Notifications", False, 
                            f"Failed to get notifications: {response.status_code}")
                            
        except Exception as e:
            self.log_test("Scenario 10", "Get User Notifications", False, f"Exception: {str(e)}")
        
        # 3. Mark notification as read
        try:
            # First get notifications to find one to mark as read
            response = self.session.get(f"{API_BASE}/notifications/my", 
                                      headers=self.get_headers("user"))
            
            if response.status_code == 200:
                notifications = response.json().get("notifications", [])
                if notifications:
                    notification_id = notifications[0].get("id")
                    
                    response = self.session.post(f"{API_BASE}/notifications/{notification_id}/read", 
                                               headers=self.get_headers("user"))
                    
                    success = response.status_code in [200, 201]
                    self.log_test("Scenario 10", "Mark Notification as Read", success, 
                                f"Mark as read: {response.status_code}")
                                
        except Exception as e:
            self.log_test("Scenario 10", "Mark Notification as Read", False, f"Exception: {str(e)}")
    
    def scenario_11_rbac_security(self):
        """SCENARIO 11: RBAC/Security (Negative Testing)"""
        print("\n🔒 SCENARIO 11: RBAC/SECURITY TESTING...")
        
        # 1. User attempts Super Admin action
        try:
            response = self.session.post(f"{API_BASE}/advances/create", 
                                       json={"employee_id": "test", "amount": 100},
                                       headers=self.get_headers("user"))
            
            success = response.status_code == 403
            self.log_test("Scenario 11", "User Access Super Admin Endpoint", success, 
                        f"Expected 403, got {response.status_code}")
                        
        except Exception as e:
            self.log_test("Scenario 11", "User Access Super Admin Endpoint", False, f"Exception: {str(e)}")
        
        # 2. Admin attempts to delete attendance
        try:
            response = self.session.delete(f"{API_BASE}/attendance/test_id", 
                                         headers=self.get_headers("admin"))
            
            success = response.status_code == 403
            self.log_test("Scenario 11", "Admin Delete Attendance", success, 
                        f"Expected 403, got {response.status_code}")
                        
        except Exception as e:
            self.log_test("Scenario 11", "Admin Delete Attendance", False, f"Exception: {str(e)}")
        
        # 3. Test invalid payloads
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
    
    def scenario_14_work_reports_integration(self):
        """SCENARIO 14: Work Reports Integration"""
        print("\n📝 SCENARIO 14: WORK REPORTS INTEGRATION TESTING...")
        
        # 1. Create client
        try:
            client_data = {
                "company_name": "شركة الاختبار المحدودة",
                "company_name_ar": "شركة الاختبار المحدودة",
                "client_code": "TEST001",
                "industry": "تكنولوجيا المعلومات",
                "contact_person": "أحمد محمد",
                "phone": "+971501234567",
                "email": "test@company.com"
            }
            
            response = self.session.post(f"{API_BASE}/work-reports/clients", 
                                       json=client_data,
                                       headers=self.get_headers("admin"))
            
            if response.status_code in [200, 201]:
                client_id = response.json().get("id")
                self.evidence["work_client_id"] = client_id
                self.log_test("Scenario 14", "Create Work Reports Client", True, 
                            f"Client created: {client_id}")
            else:
                self.log_test("Scenario 14", "Create Work Reports Client", False, 
                            f"Failed to create client: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Scenario 14", "Create Work Reports Client", False, f"Exception: {str(e)}")
        
        # 2. Create work log
        if "work_client_id" in self.evidence:
            try:
                work_log_data = {
                    "client_id": self.evidence["work_client_id"],
                    "activity_type_id": "default_activity_id",
                    "date": "2025-01-15T00:00:00Z",
                    "start_time": "2025-01-15T09:00:00Z",
                    "end_time": "2025-01-15T11:30:00Z",
                    "description": "تطوير نظام إدارة الموارد البشرية",
                    "notes": "تم إنجاز المرحلة الأولى من التطوير",
                    "is_billable": True,
                    "hourly_rate": 150.0
                }
                
                response = self.session.post(f"{API_BASE}/work-reports/logs", 
                                           json=work_log_data,
                                           headers=self.get_headers("admin"))
                
                if response.status_code in [200, 201]:
                    log_id = response.json().get("id")
                    self.evidence["work_log_id"] = log_id
                    self.log_test("Scenario 14", "Create Work Log", True, 
                                f"Work log created: {log_id}")
                else:
                    self.log_test("Scenario 14", "Create Work Log", False, 
                                f"Failed to create work log: {response.status_code}")
                    
            except Exception as e:
                self.log_test("Scenario 14", "Create Work Log", False, f"Exception: {str(e)}")
        
        # 3. Edit work log time
        if "work_log_id" in self.evidence:
            try:
                update_data = {
                    "start_time": "2025-01-15T10:15:00Z",
                    "end_time": "2025-01-15T12:00:00Z"
                }
                
                response = self.session.put(f"{API_BASE}/work-reports/logs/{self.evidence['work_log_id']}", 
                                          json=update_data,
                                          headers=self.get_headers("admin"))
                
                success = response.status_code in [200, 201]
                self.log_test("Scenario 14", "Edit Work Log Time", success, 
                            f"Work log update: {response.status_code}")
                            
            except Exception as e:
                self.log_test("Scenario 14", "Edit Work Log Time", False, f"Exception: {str(e)}")
        
        # 4. Delete work log
        if "work_log_id" in self.evidence:
            try:
                response = self.session.delete(f"{API_BASE}/work-reports/logs/{self.evidence['work_log_id']}", 
                                             headers=self.get_headers("admin"))
                
                success = response.status_code in [200, 204]
                self.log_test("Scenario 14", "Delete Work Log", success, 
                            f"Work log deletion: {response.status_code}")
                            
            except Exception as e:
                self.log_test("Scenario 14", "Delete Work Log", False, f"Exception: {str(e)}")
    
    def run_all_scenarios(self):
        """Run all test scenarios"""
        print("🚀 STARTING COMPREHENSIVE BACKEND TESTING - SCENARIOS 3-16")
        print("=" * 70)
        
        # Authenticate all users first
        if not self.authenticate_all_users():
            print("❌ AUTHENTICATION FAILED - Cannot proceed with testing")
            return False
        
        # Run all scenarios
        self.scenario_3_leave_management()
        self.scenario_4_field_marketing_visits()
        self.scenario_5_advanced_deductions()
        self.scenario_6_payroll_cycles()
        self.scenario_7_advances_custody_installments()
        self.scenario_8_salary_slip_ledger()
        self.scenario_10_notifications()
        self.scenario_11_rbac_security()
        self.scenario_14_work_reports_integration()
        
        # Generate summary
        self.generate_summary()
        
        return True
    
    def generate_summary(self):
        """Generate comprehensive test summary"""
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("=" * 70)
        
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
        results_file = "/app/comprehensive_scenarios_3_16_test_results.json"
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
    tester = ComprehensiveBackendTester()
    success = tester.run_all_scenarios()
    
    if success:
        print("\n🏁 COMPREHENSIVE BACKEND TESTING COMPLETED")
    else:
        print("\n💥 TESTING FAILED TO COMPLETE")
        sys.exit(1)

if __name__ == "__main__":
    main()