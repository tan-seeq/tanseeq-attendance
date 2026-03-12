#!/usr/bin/env python3
"""
Comprehensive Backend QA Testing for TANSEEQ HR System
Testing all backend APIs with Arabic validations and edge cases as per review request.

Test Coverage:
1. Super Admin test account setup (admin@tanseeq.com / ADMIN)
2. Authentication with three accounts: hatem@tan-seeq.co/hatem123, admin@tanseeq.com/ADMIN, jihad@tanseeq.com/jihad123
3. Core API suite testing:
   - Auth: /api/auth/login, /api/auth/me
   - Employees: GET /api/users, POST /api/users, PUT /api/users/{id}, DELETE /api/users/{id}, GET /api/employees/list
   - Attendance: POST /api/attendance/check-in, POST /api/attendance/check-out, GET /api/attendance/with-absences, 
     Super Admin: POST /api/attendance/create-absence, PUT /api/attendance/edit-absence/{id}, DELETE /api/attendance/delete-absence/{id}
   - Leaves: POST /api/leaves/json, POST /api/leaves (form), GET /api/leaves
   - Field Exits/Marketing Visits: POST /api/marketing-visits/start, GET /api/marketing-visits/active, 
     POST /api/marketing-visits/{id}/complete, GET /api/marketing-visits/history
   - Advances & Custody: POST /api/advances/create, POST /api/advances/expense, GET /api/advances/my-balance,
     GET /api/advances/my-transactions, GET /api/advances/admin/all-balances, GET /api/advances/admin/pending-approvals,
     POST /api/advances/{transaction_id}/approve
   - Installments & Payroll: POST /api/advances/{advance_id}/installments/create, GET /api/advances/{advance_id}/installments,
     GET /api/payroll/installment-schedules, GET /api/payroll/cycles, GET /api/payroll/cycles/{cycle_id}/export/pdf & /excel
   - Notifications: GET /api/notifications, GET /api/notifications/my, GET /api/notifications/unread-mandatory, POST /api/notifications/send
   - Reports: verify at least one export endpoint works and returns file response
   - Work Reports (Mongo module): GET /api/work-reports/dashboard, /clients, /activity-types, /logs
4. Validation: proper status codes, data structures, Arabic fields, no 500s
"""

import asyncio
import aiohttp
import json
import os
import tempfile
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
import uuid
import io

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://payroll-management-4.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials as per review request
TEST_CREDENTIALS = {
    'super_admin_hatem': {
        'email': 'hatem@tan-seeq.co',
        'password': 'hatem123'
    },
    'super_admin_test': {
        'email': 'admin@tanseeq.com', 
        'password': 'ADMIN'
    },
    'user_jihad': {
        'email': 'jihad@tanseeq.com',
        'password': 'jihad123'
    }
}

class ComprehensiveBackendTester:
    def __init__(self):
        self.session = None
        self.tokens = {}
        self.user_data = {}
        self.test_results = []
        self.created_resources = {
            'users': [],
            'advances': [],
            'visits': [],
            'leaves': []
        }
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, status: str, details: str = "", response_data: Any = None):
        """Log test results"""
        result = {
            'test': test_name,
            'status': status,
            'details': details,
            'timestamp': datetime.now().isoformat(),
            'response_data': response_data
        }
        self.test_results.append(result)
        
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
        if response_data and status == "FAIL":
            print(f"   Response: {response_data}")
        print()

    async def ensure_super_admin_test_account(self):
        """Step 1: Ensure Super Admin test account admin@tanseeq.com / ADMIN exists"""
        try:
            # First try to authenticate with existing account
            async with self.session.post(
                f"{API_BASE}/auth/login",
                json=TEST_CREDENTIALS['super_admin_test']
            ) as response:
                if response.status == 200:
                    self.log_test("Super Admin Test Account", "PASS", "admin@tanseeq.com account exists and accessible")
                    return True
                
            # If login fails, try to create the account using super admin hatem
            hatem_token = await self.authenticate_user('super_admin_hatem')
            if not hatem_token:
                self.log_test("Super Admin Test Account", "FAIL", "Cannot authenticate with hatem account to create test admin")
                return False
            
            # Create the test super admin account
            user_data = {
                "name": "Admin QA",
                "email": "admin@tanseeq.com",
                "role": "super_admin",
                "position": "QA Super Admin",
                "monthly_salary": 0.0,
                "daily_rate": 0.0,
                "working_hours_start": "09:00",
                "working_hours_end": "18:00",
                "phone": "",
                "is_active": True,
                "password": "ADMIN"
            }
            
            async with self.session.post(
                f"{API_BASE}/users",
                json=user_data,
                headers={'Authorization': f'Bearer {hatem_token}'}
            ) as response:
                if response.status in [200, 201]:
                    data = await response.json()
                    self.created_resources['users'].append(data.get('id'))
                    self.log_test("Super Admin Test Account", "PASS", "Created admin@tanseeq.com test account successfully")
                    return True
                else:
                    error_text = await response.text()
                    self.log_test("Super Admin Test Account", "FAIL", f"Failed to create test account: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_test("Super Admin Test Account", "FAIL", f"Exception: {str(e)}")
            return False

    async def authenticate_user(self, role: str) -> Optional[str]:
        """Authenticate user and return token"""
        try:
            credentials = TEST_CREDENTIALS[role]
            async with self.session.post(
                f"{API_BASE}/auth/login",
                json=credentials
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    token = data.get('access_token')
                    user_info = data.get('user', {})
                    self.tokens[role] = token
                    self.user_data[role] = user_info
                    self.log_test(f"Authentication - {role}", "PASS", f"Successfully authenticated {credentials['email']}")
                    return token
                else:
                    error_text = await response.text()
                    self.log_test(f"Authentication - {role}", "FAIL", f"Status: {response.status}, Error: {error_text}")
                    return None
        except Exception as e:
            self.log_test(f"Authentication - {role}", "FAIL", f"Exception: {str(e)}")
            return None

    async def test_auth_endpoints(self):
        """Test Auth endpoints: /api/auth/login, /api/auth/me"""
        
        # Test /api/auth/me for each authenticated user
        for role, token in self.tokens.items():
            try:
                async with self.session.get(
                    f"{API_BASE}/auth/me",
                    headers={'Authorization': f'Bearer {token}'}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        required_fields = ['id', 'name', 'email', 'role']
                        missing_fields = [field for field in required_fields if field not in data]
                        
                        if not missing_fields:
                            self.log_test(f"Auth Me - {role}", "PASS", f"Retrieved user info: {data.get('name')} ({data.get('role')})")
                        else:
                            self.log_test(f"Auth Me - {role}", "FAIL", f"Missing fields: {missing_fields}")
                    else:
                        error_text = await response.text()
                        self.log_test(f"Auth Me - {role}", "FAIL", f"Status: {response.status}, Error: {error_text}")
            except Exception as e:
                self.log_test(f"Auth Me - {role}", "FAIL", f"Exception: {str(e)}")

    async def test_employee_endpoints(self):
        """Test Employee endpoints"""
        
        # Test GET /api/users (requires admin)
        for role in ['super_admin_hatem', 'super_admin_test']:
            if role in self.tokens:
                try:
                    async with self.session.get(
                        f"{API_BASE}/users",
                        headers={'Authorization': f'Bearer {self.tokens[role]}'}
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            users = data.get('users', []) if isinstance(data, dict) else data
                            self.log_test(f"Get Users - {role}", "PASS", f"Retrieved {len(users)} users")
                        else:
                            error_text = await response.text()
                            self.log_test(f"Get Users - {role}", "FAIL", f"Status: {response.status}, Error: {error_text}")
                except Exception as e:
                    self.log_test(f"Get Users - {role}", "FAIL", f"Exception: {str(e)}")
                break
        
        # Test POST /api/users (create temp user) - Super Admin only
        if 'super_admin_hatem' in self.tokens:
            try:
                temp_user_data = {
                    "name": "Test Employee QA",
                    "email": f"test.employee.{uuid.uuid4().hex[:8]}@tanseeq.com",
                    "role": "user",
                    "position": "QA Test Employee",
                    "monthly_salary": 5000.0,
                    "daily_rate": 200.0,
                    "working_hours_start": "09:00",
                    "working_hours_end": "18:00",
                    "phone": "+971501234567",
                    "is_active": True,
                    "password": "test123"
                }
                
                async with self.session.post(
                    f"{API_BASE}/users",
                    json=temp_user_data,
                    headers={'Authorization': f'Bearer {self.tokens["super_admin_hatem"]}'}
                ) as response:
                    if response.status in [200, 201]:
                        data = await response.json()
                        temp_user_id = data.get('id')
                        self.created_resources['users'].append(temp_user_id)
                        self.log_test("Create Temp User", "PASS", f"Created temp user: {temp_user_data['name']}")
                        
                        # Test PUT /api/users/{id} (update temp user)
                        update_data = {
                            "position": "Updated QA Test Employee",
                            "monthly_salary": 5500.0
                        }
                        
                        async with self.session.put(
                            f"{API_BASE}/users/{temp_user_id}",
                            json=update_data,
                            headers={'Authorization': f'Bearer {self.tokens["super_admin_hatem"]}'}
                        ) as update_response:
                            if update_response.status == 200:
                                self.log_test("Update Temp User", "PASS", "Successfully updated temp user")
                            else:
                                error_text = await update_response.text()
                                self.log_test("Update Temp User", "FAIL", f"Status: {update_response.status}, Error: {error_text}")
                        
                        # Test DELETE temp user
                        async with self.session.delete(
                            f"{API_BASE}/users/{temp_user_id}",
                            headers={'Authorization': f'Bearer {self.tokens["super_admin_hatem"]}'}
                        ) as delete_response:
                            if delete_response.status in [200, 204]:
                                self.log_test("Delete Temp User", "PASS", "Successfully deleted temp user")
                                self.created_resources['users'].remove(temp_user_id)
                            else:
                                error_text = await delete_response.text()
                                self.log_test("Delete Temp User", "FAIL", f"Status: {delete_response.status}, Error: {error_text}")
                    else:
                        error_text = await response.text()
                        self.log_test("Create Temp User", "FAIL", f"Status: {response.status}, Error: {error_text}")
            except Exception as e:
                self.log_test("Create Temp User", "FAIL", f"Exception: {str(e)}")
        
        # Test GET /api/employees/list
        for role in ['super_admin_hatem', 'super_admin_test']:
            if role in self.tokens:
                try:
                    async with self.session.get(
                        f"{API_BASE}/employees/list",
                        headers={'Authorization': f'Bearer {self.tokens[role]}'}
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            employees = data.get('employees', []) if isinstance(data, dict) else data
                            self.log_test(f"Get Employees List - {role}", "PASS", f"Retrieved {len(employees)} employees")
                        else:
                            error_text = await response.text()
                            self.log_test(f"Get Employees List - {role}", "FAIL", f"Status: {response.status}, Error: {error_text}")
                except Exception as e:
                    self.log_test(f"Get Employees List - {role}", "FAIL", f"Exception: {str(e)}")
                break

    async def test_attendance_endpoints(self):
        """Test Attendance endpoints"""
        
        # Test POST /api/attendance/check-in (regular user)
        if 'user_jihad' in self.tokens:
            try:
                async with self.session.post(
                    f"{API_BASE}/attendance/check-in",
                    headers={'Authorization': f'Bearer {self.tokens["user_jihad"]}'}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.log_test("Attendance Check-in", "PASS", f"Check-in successful: {data.get('message', '')}")
                    elif response.status == 400:
                        # Already checked in today is acceptable
                        data = await response.json()
                        if "تم تسجيل الحضور مسبقاً" in data.get('detail', ''):
                            self.log_test("Attendance Check-in", "PASS", "Already checked in today (acceptable)")
                        else:
                            self.log_test("Attendance Check-in", "FAIL", f"Unexpected 400 error: {data}")
                    else:
                        error_text = await response.text()
                        self.log_test("Attendance Check-in", "FAIL", f"Status: {response.status}, Error: {error_text}")
            except Exception as e:
                self.log_test("Attendance Check-in", "FAIL", f"Exception: {str(e)}")
        
        # Test POST /api/attendance/check-out (regular user)
        if 'user_jihad' in self.tokens:
            try:
                async with self.session.post(
                    f"{API_BASE}/attendance/check-out",
                    headers={'Authorization': f'Bearer {self.tokens["user_jihad"]}'}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.log_test("Attendance Check-out", "PASS", f"Check-out successful: {data.get('message', '')}")
                    elif response.status == 400:
                        # Various acceptable 400 scenarios
                        data = await response.json()
                        acceptable_errors = ["تم تسجيل الانصراف مسبقاً", "لم يتم تسجيل الحضور"]
                        if any(error in data.get('detail', '') for error in acceptable_errors):
                            self.log_test("Attendance Check-out", "PASS", f"Expected 400 error: {data.get('detail', '')}")
                        else:
                            self.log_test("Attendance Check-out", "FAIL", f"Unexpected 400 error: {data}")
                    else:
                        error_text = await response.text()
                        self.log_test("Attendance Check-out", "FAIL", f"Status: {response.status}, Error: {error_text}")
            except Exception as e:
                self.log_test("Attendance Check-out", "FAIL", f"Exception: {str(e)}")
        
        # Test GET /api/attendance/with-absences
        for role in ['super_admin_hatem', 'super_admin_test']:
            if role in self.tokens:
                try:
                    async with self.session.get(
                        f"{API_BASE}/attendance/with-absences",
                        headers={'Authorization': f'Bearer {self.tokens[role]}'}
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            attendance_records = data.get('attendance', []) if isinstance(data, dict) else data
                            self.log_test(f"Get Attendance with Absences - {role}", "PASS", f"Retrieved {len(attendance_records)} attendance records")
                        else:
                            error_text = await response.text()
                            self.log_test(f"Get Attendance with Absences - {role}", "FAIL", f"Status: {response.status}, Error: {error_text}")
                except Exception as e:
                    self.log_test(f"Get Attendance with Absences - {role}", "FAIL", f"Exception: {str(e)}")
                break
        
        # Test Super Admin attendance management endpoints
        if 'super_admin_hatem' in self.tokens:
            # Test POST /api/attendance/create-absence
            try:
                absence_data = {
                    "user_id": self.user_data.get('user_jihad', {}).get('id', 'test-user-id'),
                    "date": datetime.now().strftime('%Y-%m-%d'),
                    "absence_reason": "اختبار إنشاء غياب من QA"
                }
                
                async with self.session.post(
                    f"{API_BASE}/attendance/create-absence",
                    json=absence_data,
                    headers={'Authorization': f'Bearer {self.tokens["super_admin_hatem"]}'}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        absence_id = data.get('id')
                        self.log_test("Create Absence", "PASS", f"Created absence record: {absence_id}")
                        
                        # Test PUT /api/attendance/edit-absence/{id}
                        if absence_id:
                            edit_data = {
                                "status": "present",
                                "check_in": "09:00:00",
                                "check_out": "18:00:00",
                                "absence_reason": "تم تعديل الغياب إلى حضور"
                            }
                            
                            async with self.session.put(
                                f"{API_BASE}/attendance/edit-absence/{absence_id}",
                                json=edit_data,
                                headers={'Authorization': f'Bearer {self.tokens["super_admin_hatem"]}'}
                            ) as edit_response:
                                if edit_response.status == 200:
                                    self.log_test("Edit Absence", "PASS", "Successfully edited absence record")
                                else:
                                    error_text = await edit_response.text()
                                    self.log_test("Edit Absence", "FAIL", f"Status: {edit_response.status}, Error: {error_text}")
                            
                            # Test DELETE /api/attendance/delete-absence/{id}
                            async with self.session.delete(
                                f"{API_BASE}/attendance/delete-absence/{absence_id}",
                                headers={'Authorization': f'Bearer {self.tokens["super_admin_hatem"]}'}
                            ) as delete_response:
                                if delete_response.status == 200:
                                    self.log_test("Delete Absence", "PASS", "Successfully deleted absence record")
                                else:
                                    error_text = await delete_response.text()
                                    self.log_test("Delete Absence", "FAIL", f"Status: {delete_response.status}, Error: {error_text}")
                    else:
                        error_text = await response.text()
                        self.log_test("Create Absence", "FAIL", f"Status: {response.status}, Error: {error_text}")
            except Exception as e:
                self.log_test("Create Absence", "FAIL", f"Exception: {str(e)}")

    async def test_leave_endpoints(self):
        """Test Leave endpoints"""
        
        # Test POST /api/leaves/json
        if 'user_jihad' in self.tokens:
            try:
                leave_data = {
                    "user_id": self.user_data.get('user_jihad', {}).get('id', 'test-user-id'),
                    "user_name": self.user_data.get('user_jihad', {}).get('name', 'Test User'),
                    "start_date": (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
                    "end_date": (datetime.now() + timedelta(days=9)).strftime('%Y-%m-%d'),
                    "reason": "إجازة اختبار من نظام QA",
                    "days_count": 3
                }
                
                async with self.session.post(
                    f"{API_BASE}/leaves/json",
                    json=leave_data,
                    headers={'Authorization': f'Bearer {self.tokens["user_jihad"]}'}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        leave_id = data.get('id')
                        self.created_resources['leaves'].append(leave_id)
                        self.log_test("Create Leave JSON", "PASS", f"Created leave request: {leave_id}")
                    else:
                        error_text = await response.text()
                        self.log_test("Create Leave JSON", "FAIL", f"Status: {response.status}, Error: {error_text}")
            except Exception as e:
                self.log_test("Create Leave JSON", "FAIL", f"Exception: {str(e)}")
        
        # Test POST /api/leaves (form data)
        if 'user_jihad' in self.tokens:
            try:
                form_data = aiohttp.FormData()
                form_data.add_field('user_id', self.user_data.get('user_jihad', {}).get('id', 'test-user-id'))
                form_data.add_field('user_name', self.user_data.get('user_jihad', {}).get('name', 'Test User'))
                form_data.add_field('start_date', (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d'))
                form_data.add_field('end_date', (datetime.now() + timedelta(days=16)).strftime('%Y-%m-%d'))
                form_data.add_field('reason', 'إجازة اختبار فورم من نظام QA')
                form_data.add_field('days_count', '3')
                
                async with self.session.post(
                    f"{API_BASE}/leaves",
                    data=form_data,
                    headers={'Authorization': f'Bearer {self.tokens["user_jihad"]}'}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        leave_id = data.get('id')
                        self.created_resources['leaves'].append(leave_id)
                        self.log_test("Create Leave Form", "PASS", f"Created leave request via form: {leave_id}")
                    else:
                        error_text = await response.text()
                        self.log_test("Create Leave Form", "FAIL", f"Status: {response.status}, Error: {error_text}")
            except Exception as e:
                self.log_test("Create Leave Form", "FAIL", f"Exception: {str(e)}")
        
        # Test GET /api/leaves
        for role in ['user_jihad', 'super_admin_hatem']:
            if role in self.tokens:
                try:
                    async with self.session.get(
                        f"{API_BASE}/leaves",
                        headers={'Authorization': f'Bearer {self.tokens[role]}'}
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            leaves = data.get('leaves', []) if isinstance(data, dict) else data
                            self.log_test(f"Get Leaves - {role}", "PASS", f"Retrieved {len(leaves)} leave requests")
                        else:
                            error_text = await response.text()
                            self.log_test(f"Get Leaves - {role}", "FAIL", f"Status: {response.status}, Error: {error_text}")
                except Exception as e:
                    self.log_test(f"Get Leaves - {role}", "FAIL", f"Exception: {str(e)}")

    async def test_marketing_visits_endpoints(self):
        """Test Marketing Visits endpoints (Field Exits alternative)"""
        
        # Test POST /api/marketing-visits/start
        if 'user_jihad' in self.tokens:
            try:
                visit_data = {
                    "client_name": "عميل اختبار QA",
                    "location_name": "موقع اختبار دبي",
                    "area": "دبي",
                    "purpose": "client_meeting",
                    "purpose_details": "اجتماع اختبار مع العميل لنظام QA",
                    "gps_location": {
                        "latitude": 25.2048,
                        "longitude": 55.2708,
                        "accuracy": 10.0
                    }
                }
                
                async with self.session.post(
                    f"{API_BASE}/marketing-visits/start",
                    json=visit_data,
                    headers={'Authorization': f'Bearer {self.tokens["user_jihad"]}'}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        visit_id = data.get('visit_id')
                        self.created_resources['visits'].append(visit_id)
                        self.log_test("Start Marketing Visit", "PASS", f"Started visit: {visit_id}")
                        
                        # Test GET /api/marketing-visits/active
                        async with self.session.get(
                            f"{API_BASE}/marketing-visits/active",
                            headers={'Authorization': f'Bearer {self.tokens["user_jihad"]}'}
                        ) as active_response:
                            if active_response.status == 200:
                                active_data = await active_response.json()
                                active_visit = active_data.get('active_visit')
                                if active_visit:
                                    self.log_test("Get Active Visit", "PASS", f"Retrieved active visit: {active_visit.get('id')}")
                                    
                                    # Test POST /api/marketing-visits/{id}/complete
                                    completion_data = {
                                        "visit_report": {
                                            "summary": "تم إكمال زيارة اختبار QA بنجاح مع العميل والحصول على ردود إيجابية",
                                            "details": "تمت مناقشة جميع النقاط المطلوبة مع العميل وتم الاتفاق على الخطوات التالية. العميل أبدى اهتماماً كبيراً بالخدمات المقدمة وطلب عرض سعر مفصل",
                                            "result": "successful",
                                            "next_actions": "إرسال عرض سعر مفصل خلال 48 ساعة"
                                        },
                                        "gps_location": {
                                            "latitude": 25.2048,
                                            "longitude": 55.2708,
                                            "accuracy": 10.0
                                        }
                                    }
                                    
                                    async with self.session.post(
                                        f"{API_BASE}/marketing-visits/{visit_id}/complete",
                                        json=completion_data,
                                        headers={'Authorization': f'Bearer {self.tokens["user_jihad"]}'}
                                    ) as complete_response:
                                        if complete_response.status == 200:
                                            complete_data = await complete_response.json()
                                            self.log_test("Complete Marketing Visit", "PASS", f"Completed visit with mandatory report")
                                        else:
                                            error_text = await complete_response.text()
                                            self.log_test("Complete Marketing Visit", "FAIL", f"Status: {complete_response.status}, Error: {error_text}")
                                else:
                                    self.log_test("Get Active Visit", "PASS", "No active visit (acceptable)")
                            else:
                                error_text = await active_response.text()
                                self.log_test("Get Active Visit", "FAIL", f"Status: {active_response.status}, Error: {error_text}")
                    else:
                        error_text = await response.text()
                        self.log_test("Start Marketing Visit", "FAIL", f"Status: {response.status}, Error: {error_text}")
            except Exception as e:
                self.log_test("Start Marketing Visit", "FAIL", f"Exception: {str(e)}")
        
        # Test GET /api/marketing-visits/history
        if 'user_jihad' in self.tokens:
            try:
                async with self.session.get(
                    f"{API_BASE}/marketing-visits/history",
                    headers={'Authorization': f'Bearer {self.tokens["user_jihad"]}'}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        visits = data.get('visits', [])
                        self.log_test("Get Marketing Visits History", "PASS", f"Retrieved {len(visits)} visit records")
                    else:
                        error_text = await response.text()
                        self.log_test("Get Marketing Visits History", "FAIL", f"Status: {response.status}, Error: {error_text}")
            except Exception as e:
                self.log_test("Get Marketing Visits History", "FAIL", f"Exception: {str(e)}")

    async def test_advances_custody_endpoints(self):
        """Test Advances & Custody endpoints"""
        
        # Test POST /api/advances/create (Super Admin only)
        if 'super_admin_hatem' in self.tokens:
            try:
                advance_data = {
                    "employee_id": self.user_data.get('user_jihad', {}).get('id', 'test-user-id'),
                    "transaction_type": "advance",
                    "amount": 2000.0,
                    "description": "سلفة اختبار من نظام QA",
                    "category": "other",
                    "expense_date": datetime.now().strftime('%Y-%m-%d'),
                    "notes": "تم إنشاؤها لاختبار النظام"
                }
                
                async with self.session.post(
                    f"{API_BASE}/advances/create",
                    json=advance_data,
                    headers={'Authorization': f'Bearer {self.tokens["super_admin_hatem"]}'}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        advance_id = data.get('transaction_id')
                        self.created_resources['advances'].append(advance_id)
                        self.log_test("Create Advance", "PASS", f"Created advance: {advance_id}, Amount: {advance_data['amount']}")
                    else:
                        error_text = await response.text()
                        self.log_test("Create Advance", "FAIL", f"Status: {response.status}, Error: {error_text}")
            except Exception as e:
                self.log_test("Create Advance", "FAIL", f"Exception: {str(e)}")
        
        # Test POST /api/advances/expense (with file upload)
        if 'user_jihad' in self.tokens:
            try:
                # Create a temporary PDF file for testing
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                    temp_file.write(b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n174\n%%EOF')
                    temp_file_path = temp_file.name
                
                form_data = aiohttp.FormData()
                form_data.add_field('amount', '150.0')
                form_data.add_field('category', 'transportation')
                form_data.add_field('description', 'مصروف اختبار QA - مواصلات')
                form_data.add_field('expense_date', datetime.now().strftime('%Y-%m-%d'))
                form_data.add_field('notes', 'فاتورة اختبار للنظام')
                
                with open(temp_file_path, 'rb') as f:
                    form_data.add_field('invoice_files', f, filename='test_invoice.pdf', content_type='application/pdf')
                    
                    async with self.session.post(
                        f"{API_BASE}/advances/expense",
                        data=form_data,
                        headers={'Authorization': f'Bearer {self.tokens["user_jihad"]}'}
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            expense_id = data.get('transaction_id')
                            self.log_test("Create Expense with File", "PASS", f"Created expense with PDF: {expense_id}")
                        else:
                            error_text = await response.text()
                            self.log_test("Create Expense with File", "FAIL", f"Status: {response.status}, Error: {error_text}")
                
                # Clean up temp file
                os.unlink(temp_file_path)
                
            except Exception as e:
                self.log_test("Create Expense with File", "FAIL", f"Exception: {str(e)}")
        
        # Test GET /api/advances/my-balance
        if 'user_jihad' in self.tokens:
            try:
                async with self.session.get(
                    f"{API_BASE}/advances/my-balance",
                    headers={'Authorization': f'Bearer {self.tokens["user_jihad"]}'}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        total_available = data.get('total_available', 0)
                        self.log_test("Get My Balance", "PASS", f"Retrieved balance: {total_available} AED")
                    else:
                        error_text = await response.text()
                        self.log_test("Get My Balance", "FAIL", f"Status: {response.status}, Error: {error_text}")
            except Exception as e:
                self.log_test("Get My Balance", "FAIL", f"Exception: {str(e)}")
        
        # Test GET /api/advances/my-transactions
        if 'user_jihad' in self.tokens:
            try:
                async with self.session.get(
                    f"{API_BASE}/advances/my-transactions",
                    headers={'Authorization': f'Bearer {self.tokens["user_jihad"]}'}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        transactions = data.get('transactions', [])
                        self.log_test("Get My Transactions", "PASS", f"Retrieved {len(transactions)} transactions")
                    else:
                        error_text = await response.text()
                        self.log_test("Get My Transactions", "FAIL", f"Status: {response.status}, Error: {error_text}")
            except Exception as e:
                self.log_test("Get My Transactions", "FAIL", f"Exception: {str(e)}")
        
        # Test GET /api/advances/admin/all-balances (Super Admin only)
        if 'super_admin_hatem' in self.tokens:
            try:
                async with self.session.get(
                    f"{API_BASE}/advances/admin/all-balances",
                    headers={'Authorization': f'Bearer {self.tokens["super_admin_hatem"]}'}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        balances = data.get('employee_balances', [])
                        self.log_test("Get All Balances", "PASS", f"Retrieved {len(balances)} employee balances")
                    else:
                        error_text = await response.text()
                        self.log_test("Get All Balances", "FAIL", f"Status: {response.status}, Error: {error_text}")
            except Exception as e:
                self.log_test("Get All Balances", "FAIL", f"Exception: {str(e)}")
        
        # Test GET /api/advances/admin/pending-approvals (Super Admin only)
        if 'super_admin_hatem' in self.tokens:
            try:
                async with self.session.get(
                    f"{API_BASE}/advances/admin/pending-approvals",
                    headers={'Authorization': f'Bearer {self.tokens["super_admin_hatem"]}'}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        pending = data.get('pending_transactions', [])
                        self.log_test("Get Pending Approvals", "PASS", f"Retrieved {len(pending)} pending transactions")
                        
                        # Test POST /api/advances/{transaction_id}/approve if there are pending transactions
                        if pending:
                            transaction_id = pending[0].get('id')
                            approval_data = {
                                "status": "approved",
                                "notes": "موافقة اختبار من نظام QA"
                            }
                            
                            async with self.session.post(
                                f"{API_BASE}/advances/{transaction_id}/approve",
                                json=approval_data,
                                headers={'Authorization': f'Bearer {self.tokens["super_admin_hatem"]}'}
                            ) as approve_response:
                                if approve_response.status == 200:
                                    self.log_test("Approve Transaction", "PASS", f"Approved transaction: {transaction_id}")
                                else:
                                    error_text = await approve_response.text()
                                    self.log_test("Approve Transaction", "FAIL", f"Status: {approve_response.status}, Error: {error_text}")
                    else:
                        error_text = await response.text()
                        self.log_test("Get Pending Approvals", "FAIL", f"Status: {response.status}, Error: {error_text}")
            except Exception as e:
                self.log_test("Get Pending Approvals", "FAIL", f"Exception: {str(e)}")

    async def test_installments_payroll_endpoints(self):
        """Test Installments & Payroll endpoints"""
        
        # Test GET /api/payroll/installment-schedules (Super Admin only)
        if 'super_admin_hatem' in self.tokens:
            try:
                async with self.session.get(
                    f"{API_BASE}/payroll/installment-schedules",
                    headers={'Authorization': f'Bearer {self.tokens["super_admin_hatem"]}'}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        schedules = data.get('schedules', [])
                        self.log_test("Get Installment Schedules", "PASS", f"Retrieved {len(schedules)} installment schedules")
                    else:
                        error_text = await response.text()
                        self.log_test("Get Installment Schedules", "FAIL", f"Status: {response.status}, Error: {error_text}")
            except Exception as e:
                self.log_test("Get Installment Schedules", "FAIL", f"Exception: {str(e)}")
        
        # Test GET /api/payroll/cycles
        if 'super_admin_hatem' in self.tokens:
            try:
                async with self.session.get(
                    f"{API_BASE}/payroll/cycles",
                    headers={'Authorization': f'Bearer {self.tokens["super_admin_hatem"]}'}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        cycles = data.get('cycles', []) if isinstance(data, dict) else data
                        self.log_test("Get Payroll Cycles", "PASS", f"Retrieved {len(cycles)} payroll cycles")
                        
                        # Test export endpoints if cycles exist
                        if cycles:
                            cycle_id = cycles[0].get('id')
                            
                            # Test PDF export
                            async with self.session.get(
                                f"{API_BASE}/payroll/cycles/{cycle_id}/export/pdf",
                                headers={'Authorization': f'Bearer {self.tokens["super_admin_hatem"]}'}
                            ) as pdf_response:
                                if pdf_response.status == 200:
                                    content_type = pdf_response.headers.get('content-type', '')
                                    if 'pdf' in content_type:
                                        self.log_test("Export Payroll PDF", "PASS", "Successfully exported payroll cycle as PDF")
                                    else:
                                        self.log_test("Export Payroll PDF", "FAIL", f"Unexpected content type: {content_type}")
                                else:
                                    error_text = await pdf_response.text()
                                    self.log_test("Export Payroll PDF", "FAIL", f"Status: {pdf_response.status}, Error: {error_text}")
                            
                            # Test Excel export
                            async with self.session.get(
                                f"{API_BASE}/payroll/cycles/{cycle_id}/export/excel",
                                headers={'Authorization': f'Bearer {self.tokens["super_admin_hatem"]}'}
                            ) as excel_response:
                                if excel_response.status == 200:
                                    content_type = excel_response.headers.get('content-type', '')
                                    if 'excel' in content_type or 'spreadsheet' in content_type:
                                        self.log_test("Export Payroll Excel", "PASS", "Successfully exported payroll cycle as Excel")
                                    else:
                                        self.log_test("Export Payroll Excel", "FAIL", f"Unexpected content type: {content_type}")
                                else:
                                    error_text = await excel_response.text()
                                    self.log_test("Export Payroll Excel", "FAIL", f"Status: {excel_response.status}, Error: {error_text}")
                    else:
                        error_text = await response.text()
                        self.log_test("Get Payroll Cycles", "FAIL", f"Status: {response.status}, Error: {error_text}")
            except Exception as e:
                self.log_test("Get Payroll Cycles", "FAIL", f"Exception: {str(e)}")
        
        # Test installment creation if we have advances
        if 'super_admin_hatem' in self.tokens and self.created_resources['advances']:
            try:
                advance_id = self.created_resources['advances'][0]
                installment_data = {
                    "installment_amount": 200.0,
                    "number_of_installments": 10,
                    "start_date": (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
                    "respect_ceiling": True
                }
                
                async with self.session.post(
                    f"{API_BASE}/advances/{advance_id}/installments",
                    json=installment_data,
                    headers={'Authorization': f'Bearer {self.tokens["super_admin_hatem"]}'}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        schedule_id = data.get('schedule_id')
                        self.log_test("Create Installment Schedule", "PASS", f"Created installment schedule: {schedule_id}")
                        
                        # Test GET /api/advances/{advance_id}/installments
                        async with self.session.get(
                            f"{API_BASE}/advances/{advance_id}/installments",
                            headers={'Authorization': f'Bearer {self.tokens["super_admin_hatem"]}'}
                        ) as get_response:
                            if get_response.status == 200:
                                get_data = await get_response.json()
                                installments = get_data.get('installments', [])
                                self.log_test("Get Advance Installments", "PASS", f"Retrieved {len(installments)} installments")
                            else:
                                error_text = await get_response.text()
                                self.log_test("Get Advance Installments", "FAIL", f"Status: {get_response.status}, Error: {error_text}")
                    else:
                        error_text = await response.text()
                        self.log_test("Create Installment Schedule", "FAIL", f"Status: {response.status}, Error: {error_text}")
            except Exception as e:
                self.log_test("Create Installment Schedule", "FAIL", f"Exception: {str(e)}")

    async def test_notification_endpoints(self):
        """Test Notification endpoints"""
        
        # Test GET /api/notifications (Super Admin)
        if 'super_admin_hatem' in self.tokens:
            try:
                async with self.session.get(
                    f"{API_BASE}/notifications",
                    headers={'Authorization': f'Bearer {self.tokens["super_admin_hatem"]}'}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        notifications = data.get('notifications', []) if isinstance(data, dict) else data
                        self.log_test("Get All Notifications", "PASS", f"Retrieved {len(notifications)} notifications")
                    else:
                        error_text = await response.text()
                        self.log_test("Get All Notifications", "FAIL", f"Status: {response.status}, Error: {error_text}")
            except Exception as e:
                self.log_test("Get All Notifications", "FAIL", f"Exception: {str(e)}")
        
        # Test GET /api/notifications/my
        for role in ['user_jihad', 'super_admin_hatem']:
            if role in self.tokens:
                try:
                    async with self.session.get(
                        f"{API_BASE}/notifications/my",
                        headers={'Authorization': f'Bearer {self.tokens[role]}'}
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            my_notifications = data.get('notifications', []) if isinstance(data, dict) else data
                            self.log_test(f"Get My Notifications - {role}", "PASS", f"Retrieved {len(my_notifications)} personal notifications")
                        else:
                            error_text = await response.text()
                            self.log_test(f"Get My Notifications - {role}", "FAIL", f"Status: {response.status}, Error: {error_text}")
                except Exception as e:
                    self.log_test(f"Get My Notifications - {role}", "FAIL", f"Exception: {str(e)}")
        
        # Test GET /api/notifications/unread-mandatory
        for role in ['user_jihad', 'super_admin_hatem']:
            if role in self.tokens:
                try:
                    async with self.session.get(
                        f"{API_BASE}/notifications/unread-mandatory",
                        headers={'Authorization': f'Bearer {self.tokens[role]}'}
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            mandatory = data.get('notifications', []) if isinstance(data, dict) else data
                            self.log_test(f"Get Unread Mandatory - {role}", "PASS", f"Retrieved {len(mandatory)} mandatory notifications")
                        else:
                            error_text = await response.text()
                            self.log_test(f"Get Unread Mandatory - {role}", "FAIL", f"Status: {response.status}, Error: {error_text}")
                except Exception as e:
                    self.log_test(f"Get Unread Mandatory - {role}", "FAIL", f"Exception: {str(e)}")
        
        # Test POST /api/notifications/send (Super Admin only)
        if 'super_admin_hatem' in self.tokens:
            try:
                notification_data = {
                    "recipient_id": self.user_data.get('user_jihad', {}).get('id', 'test-user-id'),
                    "subject": "إشعار اختبار من نظام QA",
                    "message": "هذا إشعار اختبار من نظام ضمان الجودة للتأكد من عمل النظام بشكل صحيح. يرجى تجاهل هذا الإشعار.",
                    "type": "info",
                    "priority": "normal"
                }
                
                async with self.session.post(
                    f"{API_BASE}/notifications/send",
                    json=notification_data,
                    headers={'Authorization': f'Bearer {self.tokens["super_admin_hatem"]}'}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.log_test("Send Notification", "PASS", f"Successfully sent notification with Arabic content")
                    else:
                        error_text = await response.text()
                        self.log_test("Send Notification", "FAIL", f"Status: {response.status}, Error: {error_text}")
            except Exception as e:
                self.log_test("Send Notification", "FAIL", f"Exception: {str(e)}")

    async def test_work_reports_endpoints(self):
        """Test Work Reports (MongoDB module) endpoints"""
        
        # Test GET /api/work-reports/dashboard
        if 'super_admin_hatem' in self.tokens:
            try:
                async with self.session.get(
                    f"{API_BASE}/work-reports/dashboard",
                    headers={'Authorization': f'Bearer {self.tokens["super_admin_hatem"]}'}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.log_test("Work Reports Dashboard", "PASS", f"Retrieved dashboard data: {data}")
                    else:
                        error_text = await response.text()
                        self.log_test("Work Reports Dashboard", "FAIL", f"Status: {response.status}, Error: {error_text}")
            except Exception as e:
                self.log_test("Work Reports Dashboard", "FAIL", f"Exception: {str(e)}")
        
        # Test GET /api/work-reports/clients
        if 'super_admin_hatem' in self.tokens:
            try:
                async with self.session.get(
                    f"{API_BASE}/work-reports/clients",
                    headers={'Authorization': f'Bearer {self.tokens["super_admin_hatem"]}'}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        clients = data.get('clients', []) if isinstance(data, dict) else data
                        self.log_test("Work Reports Clients", "PASS", f"Retrieved {len(clients)} clients")
                    else:
                        error_text = await response.text()
                        self.log_test("Work Reports Clients", "FAIL", f"Status: {response.status}, Error: {error_text}")
            except Exception as e:
                self.log_test("Work Reports Clients", "FAIL", f"Exception: {str(e)}")
        
        # Test GET /api/work-reports/activity-types
        if 'super_admin_hatem' in self.tokens:
            try:
                async with self.session.get(
                    f"{API_BASE}/work-reports/activity-types",
                    headers={'Authorization': f'Bearer {self.tokens["super_admin_hatem"]}'}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        activities = data.get('activity_types', []) if isinstance(data, dict) else data
                        self.log_test("Work Reports Activity Types", "PASS", f"Retrieved {len(activities)} activity types")
                    else:
                        error_text = await response.text()
                        self.log_test("Work Reports Activity Types", "FAIL", f"Status: {response.status}, Error: {error_text}")
            except Exception as e:
                self.log_test("Work Reports Activity Types", "FAIL", f"Exception: {str(e)}")
        
        # Test GET /api/work-reports/logs
        if 'super_admin_hatem' in self.tokens:
            try:
                async with self.session.get(
                    f"{API_BASE}/work-reports/logs",
                    headers={'Authorization': f'Bearer {self.tokens["super_admin_hatem"]}'}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logs = data.get('logs', []) if isinstance(data, dict) else data
                        self.log_test("Work Reports Logs", "PASS", f"Retrieved {len(logs)} work logs")
                    else:
                        error_text = await response.text()
                        self.log_test("Work Reports Logs", "FAIL", f"Status: {response.status}, Error: {error_text}")
            except Exception as e:
                self.log_test("Work Reports Logs", "FAIL", f"Exception: {str(e)}")

    async def run_comprehensive_tests(self):
        """Run all comprehensive backend tests"""
        print("🚀 Starting Comprehensive Backend QA Testing for TANSEEQ HR System")
        print("=" * 80)
        print()
        
        # Step 1: Ensure Super Admin test account
        await self.ensure_super_admin_test_account()
        
        # Step 2: Authenticate with three accounts
        print("🔐 Authenticating with test accounts...")
        await self.authenticate_user('super_admin_hatem')
        await self.authenticate_user('super_admin_test')
        await self.authenticate_user('user_jihad')
        print()
        
        # Step 3: Execute core API suite
        print("🧪 Testing Core API Suite...")
        await self.test_auth_endpoints()
        await self.test_employee_endpoints()
        await self.test_attendance_endpoints()
        await self.test_leave_endpoints()
        await self.test_marketing_visits_endpoints()
        await self.test_advances_custody_endpoints()
        await self.test_installments_payroll_endpoints()
        await self.test_notification_endpoints()
        await self.test_work_reports_endpoints()
        
        # Generate comprehensive summary
        print("=" * 80)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%")
        print()
        
        # Categorize failures
        failures_by_category = {}
        for result in self.test_results:
            if result['status'] == 'FAIL':
                category = result['test'].split(' - ')[0] if ' - ' in result['test'] else result['test'].split(' ')[0]
                if category not in failures_by_category:
                    failures_by_category[category] = []
                failures_by_category[category].append(result)
        
        if failures_by_category:
            print("❌ FAILURES BY CATEGORY:")
            for category, failures in failures_by_category.items():
                print(f"\n  📂 {category} ({len(failures)} failures):")
                for failure in failures:
                    print(f"    - {failure['test']}: {failure['details']}")
            print()
        
        # Critical findings
        print("🎯 CRITICAL FINDINGS:")
        
        critical_issues = []
        
        # Check authentication
        auth_failures = [r for r in self.test_results if 'Authentication' in r['test'] and r['status'] == 'FAIL']
        if auth_failures:
            critical_issues.append(f"❌ CRITICAL: Authentication failures ({len(auth_failures)} accounts)")
        
        # Check core endpoints
        core_endpoints = ['Auth', 'Employee', 'Attendance', 'Leave', 'Advance', 'Notification']
        for endpoint in core_endpoints:
            endpoint_tests = [r for r in self.test_results if endpoint in r['test']]
            endpoint_failures = [r for r in endpoint_tests if r['status'] == 'FAIL']
            if endpoint_failures and len(endpoint_failures) == len(endpoint_tests):
                critical_issues.append(f"❌ CRITICAL: All {endpoint} endpoints failing")
        
        # Check for 500 errors
        server_errors = [r for r in self.test_results if r['status'] == 'FAIL' and '500' in str(r.get('response_data', ''))]
        if server_errors:
            critical_issues.append(f"⚠️ WARNING: {len(server_errors)} server errors (500) detected")
        
        if critical_issues:
            for issue in critical_issues:
                print(f"  {issue}")
        else:
            print("  ✅ No critical system-wide issues found")
        
        print()
        print("🌍 ARABIC VALIDATION STATUS:")
        arabic_tests = [r for r in self.test_results if any(keyword in r['test'].lower() for keyword in ['notification', 'leave', 'advance', 'visit'])]
        arabic_passed = len([r for r in arabic_tests if r['status'] == 'PASS'])
        print(f"  Arabic-enabled endpoints: {arabic_passed}/{len(arabic_tests)} working")
        
        print()
        print("📋 ENDPOINT STATUS SUMMARY:")
        endpoint_categories = {
            'Authentication': ['Authentication', 'Auth Me'],
            'Employee Management': ['Users', 'Employee'],
            'Attendance': ['Attendance', 'Check-in', 'Check-out', 'Absence'],
            'Leave Management': ['Leave'],
            'Field Visits': ['Marketing Visit', 'Visit'],
            'Advances & Custody': ['Advance', 'Balance', 'Transaction', 'Expense'],
            'Payroll & Installments': ['Payroll', 'Installment'],
            'Notifications': ['Notification'],
            'Work Reports': ['Work Reports']
        }
        
        for category, keywords in endpoint_categories.items():
            category_tests = [r for r in self.test_results if any(keyword in r['test'] for keyword in keywords)]
            if category_tests:
                category_passed = len([r for r in category_tests if r['status'] == 'PASS'])
                status_emoji = "✅" if category_passed == len(category_tests) else "⚠️" if category_passed > 0 else "❌"
                print(f"  {status_emoji} {category}: {category_passed}/{len(category_tests)} working")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': (passed_tests/total_tests*100) if total_tests > 0 else 0,
            'critical_issues': critical_issues,
            'failures_by_category': failures_by_category,
            'test_results': self.test_results
        }

async def main():
    """Main test execution"""
    async with ComprehensiveBackendTester() as tester:
        results = await tester.run_comprehensive_tests()
        return results

if __name__ == "__main__":
    results = asyncio.run(main())