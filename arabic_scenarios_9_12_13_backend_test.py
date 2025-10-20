#!/usr/bin/env python3
"""
🎯 ARABIC SCENARIOS 9, 12, 13 BACKEND TESTING
تنفيذ السيناريوهات المتبقية 9, 12, 13 - Backend Testing

SCENARIO 9: التقارير الشاملة (Comprehensive Reports)
SCENARIO 12: حالات مالية حدّية (Edge Cases - Negative Salary)  
SCENARIO 13: القفل/الفك + القيود العكسية (Lock/Unlock + Reversals)

Testing comprehensive reports, negative salary edge cases, and payroll lock/unlock mechanisms.
"""

import requests
import json
import os
from datetime import datetime, timedelta
import uuid

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://payroll-hardening.preview.emergentagent.com')
BASE_URL = f"{BACKEND_URL}/api"

# Test credentials
TEST_CREDENTIALS = {
    "super_admin": {"email": "admin@tanseeq.com", "password": "ADMIN"},
    "admin": {"email": "mahmoud@tanseeq.com", "password": "mahmoud123"},
    "user": {"email": "jihad@tanseeq.com", "password": "jihad123"}
}

class ArabicScenariosBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.tokens = {}
        self.test_results = []
        self.test_employee_id = None
        self.test_cycle_id = None
        
    def log_test(self, test_name, status, details, response_data=None):
        """Log test results"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {details}")
        
        if response_data and isinstance(response_data, dict):
            if response_data.get('status_code'):
                print(f"   Status: {response_data['status_code']}")
            if response_data.get('message'):
                print(f"   Message: {response_data['message']}")
    
    def authenticate(self, role):
        """Authenticate and get token"""
        if role in self.tokens:
            return self.tokens[role]
            
        creds = TEST_CREDENTIALS[role]
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", json=creds)
            if response.status_code == 200:
                data = response.json()
                token = data["access_token"]
                user_id = data["user"]["id"]
                self.tokens[role] = {"token": token, "user_id": user_id, "user_data": data["user"]}
                self.log_test(f"Authentication - {role}", "PASS", f"Login successful for {creds['email']}")
                return self.tokens[role]
            else:
                self.log_test(f"Authentication - {role}", "FAIL", f"Login failed: {response.status_code}")
                return None
        except Exception as e:
            self.log_test(f"Authentication - {role}", "FAIL", f"Login error: {str(e)}")
            return None
    
    def make_request(self, method, endpoint, role="super_admin", **kwargs):
        """Make authenticated request"""
        auth_data = self.authenticate(role)
        if not auth_data:
            return None
            
        headers = kwargs.get('headers', {})
        headers['Authorization'] = f"Bearer {auth_data['token']}"
        kwargs['headers'] = headers
        
        try:
            response = self.session.request(method, f"{BASE_URL}{endpoint}", **kwargs)
            return response
        except Exception as e:
            print(f"Request error: {str(e)}")
            return None

    # ============ SCENARIO 9: التقارير الشاملة (Comprehensive Reports) ============
    
    def test_scenario_9_comprehensive_reports(self):
        """SCENARIO 9: Testing comprehensive reports with PDF/Excel export"""
        print("\n🎯 SCENARIO 9: التقارير الشاملة (Comprehensive Reports)")
        print("=" * 70)
        
        # Test 1: Attendance Report
        self.test_attendance_report()
        
        # Test 2: Payroll Report  
        self.test_payroll_report()
        
        # Test 3: Advances Report
        self.test_advances_report()
        
        # Test 4: Installment Schedules Report
        self.test_installment_schedules_report()
    
    def test_attendance_report(self):
        """Test attendance report endpoints"""
        print("\n📊 Testing Attendance Reports...")
        
        # Get attendance data first
        response = self.make_request("GET", "/attendance")
        if response and response.status_code == 200:
            data = response.json()
            records = data.get('records', []) if isinstance(data, dict) else data
            self.log_test("Attendance Data - GET", "PASS", 
                         f"Retrieved attendance data with {len(records)} records")
        else:
            self.log_test("Attendance Data - GET", "FAIL", 
                         f"Failed to get attendance data: {response.status_code if response else 'No response'}")
        
        # Test generic report export (attendance type)
        response = self.make_request("GET", "/reports/attendance/export?format=pdf")
        if response and response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            file_size = len(response.content)
            if 'pdf' in content_type.lower() and file_size > 0:
                self.log_test("Attendance Report - PDF Export", "PASS", 
                             f"PDF generated successfully, size: {file_size} bytes")
                # Save evidence
                with open('/app/evidence_attendance_report.pdf', 'wb') as f:
                    f.write(response.content)
            else:
                self.log_test("Attendance Report - PDF Export", "FAIL", 
                             f"Invalid PDF: content-type={content_type}, size={file_size}")
        else:
            self.log_test("Attendance Report - PDF Export", "FAIL", 
                         f"PDF export failed: {response.status_code if response else 'No response'}")
        
        # Test Excel export
        response = self.make_request("GET", "/reports/attendance/export?format=excel")
        if response and response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            file_size = len(response.content)
            if ('excel' in content_type.lower() or 'spreadsheet' in content_type.lower()) and file_size > 0:
                self.log_test("Attendance Report - Excel Export", "PASS", 
                             f"Excel generated successfully, size: {file_size} bytes")
                # Save evidence
                with open('/app/evidence_attendance_report.xlsx', 'wb') as f:
                    f.write(response.content)
            else:
                self.log_test("Attendance Report - Excel Export", "FAIL", 
                             f"Invalid Excel: content-type={content_type}, size={file_size}")
        else:
            self.log_test("Attendance Report - Excel Export", "FAIL", 
                         f"Excel export failed: {response.status_code if response else 'No response'}")
    
    def test_payroll_report(self):
        """Test payroll report endpoints"""
        print("\n💰 Testing Payroll Reports...")
        
        # First get available payroll cycles
        response = self.make_request("GET", "/payroll/cycles")
        if response and response.status_code == 200:
            data = response.json()
            # Handle both list and dict responses
            if isinstance(data, list):
                cycles = data
            else:
                cycles = data.get('cycles', [])
            if cycles:
                cycle_id = cycles[0]['id']
                self.test_cycle_id = cycle_id
                self.log_test("Payroll Cycles - GET", "PASS", f"Found {len(cycles)} payroll cycles")
                
                # Test payroll report
                response = self.make_request("GET", f"/reports/payroll?cycle_id={cycle_id}")
                if response and response.status_code == 200:
                    self.log_test("Payroll Report - GET", "PASS", "Payroll report retrieved successfully")
                else:
                    self.log_test("Payroll Report - GET", "FAIL", 
                                 f"Failed to get payroll report: {response.status_code if response else 'No response'}")
                
                # Test PDF export
                response = self.make_request("GET", f"/payroll/cycles/{cycle_id}/export/pdf")
                if response and response.status_code == 200:
                    content_type = response.headers.get('content-type', '')
                    file_size = len(response.content)
                    if file_size > 0:
                        self.log_test("Payroll Report - PDF Export", "PASS", 
                                     f"PDF generated successfully, size: {file_size} bytes")
                        # Save evidence
                        with open('/app/evidence_payroll_report.pdf', 'wb') as f:
                            f.write(response.content)
                    else:
                        self.log_test("Payroll Report - PDF Export", "FAIL", 
                                     f"Empty PDF: content-type={content_type}, size={file_size}")
                else:
                    self.log_test("Payroll Report - PDF Export", "FAIL", 
                                 f"PDF export failed: {response.status_code if response else 'No response'}")
                
                # Test Excel export
                response = self.make_request("GET", f"/payroll/cycles/{cycle_id}/export/excel")
                if response and response.status_code == 200:
                    content_type = response.headers.get('content-type', '')
                    file_size = len(response.content)
                    if file_size > 0:
                        self.log_test("Payroll Report - Excel Export", "PASS", 
                                     f"Excel generated successfully, size: {file_size} bytes")
                        # Save evidence
                        with open('/app/evidence_payroll_report.xlsx', 'wb') as f:
                            f.write(response.content)
                    else:
                        self.log_test("Payroll Report - Excel Export", "FAIL", 
                                     f"Empty Excel: content-type={content_type}, size={file_size}")
                else:
                    self.log_test("Payroll Report - Excel Export", "FAIL", 
                                 f"Excel export failed: {response.status_code if response else 'No response'}")
            else:
                self.log_test("Payroll Cycles - GET", "FAIL", "No payroll cycles found")
        else:
            self.log_test("Payroll Cycles - GET", "FAIL", 
                         f"Failed to get payroll cycles: {response.status_code if response else 'No response'}")
    
    def test_advances_report(self):
        """Test advances report endpoints"""
        print("\n💳 Testing Advances Reports...")
        
        # Get advances report
        response = self.make_request("GET", "/reports/advances?month=2025-10")
        if response and response.status_code == 200:
            data = response.json()
            self.log_test("Advances Report - GET", "PASS", 
                         f"Retrieved advances report with {len(data.get('transactions', []))} transactions")
        else:
            self.log_test("Advances Report - GET", "FAIL", 
                         f"Failed to get advances report: {response.status_code if response else 'No response'}")
        
        # Test export with all transaction types
        for transaction_type in ['custody', 'advance', 'expense']:
            response = self.make_request("GET", f"/reports/advances/export?format=pdf&month=2025-10&type={transaction_type}")
            if response and response.status_code == 200:
                file_size = len(response.content)
                self.log_test(f"Advances Report - {transaction_type.title()} PDF", "PASS", 
                             f"PDF generated successfully, size: {file_size} bytes")
            else:
                self.log_test(f"Advances Report - {transaction_type.title()} PDF", "FAIL", 
                             f"PDF export failed: {response.status_code if response else 'No response'}")
    
    def test_installment_schedules_report(self):
        """Test installment schedules report"""
        print("\n📅 Testing Installment Schedules Report...")
        
        # Get installment schedules
        response = self.make_request("GET", "/reports/installments")
        if response and response.status_code == 200:
            data = response.json()
            schedules = data.get('schedules', [])
            self.log_test("Installment Schedules - GET", "PASS", 
                         f"Retrieved {len(schedules)} installment schedules")
            
            # Verify content includes required fields
            if schedules:
                schedule = schedules[0]
                required_fields = ['status', 'amount', 'due_date']
                missing_fields = [field for field in required_fields if field not in schedule]
                if not missing_fields:
                    self.log_test("Installment Schedules - Content Verification", "PASS", 
                                 "All required fields present in schedules")
                else:
                    self.log_test("Installment Schedules - Content Verification", "FAIL", 
                                 f"Missing fields: {missing_fields}")
        else:
            self.log_test("Installment Schedules - GET", "FAIL", 
                         f"Failed to get installment schedules: {response.status_code if response else 'No response'}")

    # ============ SCENARIO 12: حالات مالية حدّية (Edge Cases - Negative Salary) ============
    
    def test_scenario_12_negative_salary_edge_cases(self):
        """SCENARIO 12: Testing negative salary edge cases"""
        print("\n🎯 SCENARIO 12: حالات مالية حدّية (Edge Cases - Negative Salary)")
        print("=" * 70)
        
        # Setup test employee with specific salary structure
        self.setup_test_employee_for_edge_cases()
        
        # Apply high deductions to create negative salary scenario
        self.apply_high_deductions()
        
        # Calculate payroll and verify system behavior
        self.test_negative_salary_calculation()
        
        # Test salary slip generation for negative balance
        self.test_negative_salary_slip()
    
    def setup_test_employee_for_edge_cases(self):
        """Setup test employee with specific salary structure"""
        print("\n👤 Setting up test employee for edge cases...")
        
        # Get existing employees first
        response = self.make_request("GET", "/employees/list")
        if response and response.status_code == 200:
            employees = response.json().get('employees', [])
            if employees:
                # Use first employee for testing
                test_employee = employees[0]
                self.test_employee_id = test_employee['id']
                
                # Update employee with specific salary structure
                update_data = {
                    "monthly_salary": 3000.0,  # Basic salary: 3000 AED
                    "daily_rate": 100.0        # For allowances calculation
                }
                
                response = self.make_request("PUT", f"/employees/{self.test_employee_id}", json=update_data)
                if response and response.status_code == 200:
                    self.log_test("Test Employee Setup", "PASS", 
                                 f"Employee {test_employee['name']} configured with 3000 AED basic salary")
                else:
                    self.log_test("Test Employee Setup", "FAIL", 
                                 f"Failed to update employee: {response.status_code if response else 'No response'}")
            else:
                self.log_test("Test Employee Setup", "FAIL", "No employees found for testing")
        else:
            self.log_test("Test Employee Setup", "FAIL", 
                         f"Failed to get employees: {response.status_code if response else 'No response'}")
    
    def apply_high_deductions(self):
        """Apply high deductions to create negative salary scenario"""
        print("\n💸 Applying high deductions...")
        
        if not self.test_employee_id:
            self.log_test("High Deductions Setup", "SKIP", "No test employee available")
            return
        
        # Create multiple deductions that exceed gross salary
        deductions = [
            {"type": "late", "amount": 500.0, "description": "Late deductions (many late days)"},
            {"type": "absence", "amount": 1000.0, "description": "Absence deductions (multiple absences)"},
            {"type": "advance_installment", "amount": 1500.0, "description": "Advance installment"},
            {"type": "manual", "amount": 600.0, "description": "Manual deduction"}
        ]
        
        total_deductions = sum(d['amount'] for d in deductions)
        
        for deduction in deductions:
            deduction_data = {
                "employee_id": self.test_employee_id,
                "amount": deduction["amount"],
                "description": deduction["description"],
                "deduction_type": deduction["type"],
                "date": datetime.now().strftime("%Y-%m-%d")
            }
            
            response = self.make_request("POST", "/deductions/manual", json=deduction_data)
            if response and response.status_code in [200, 201]:
                self.log_test(f"Deduction - {deduction['type']}", "PASS", 
                             f"Applied {deduction['amount']} AED deduction")
            else:
                self.log_test(f"Deduction - {deduction['type']}", "FAIL", 
                             f"Failed to apply deduction: {response.status_code if response else 'No response'}")
        
        self.log_test("Total Deductions Applied", "INFO", 
                     f"Total deductions: {total_deductions} AED (exceeds 3500 AED gross)")
    
    def test_negative_salary_calculation(self):
        """Test payroll calculation with negative salary scenario"""
        print("\n🧮 Testing negative salary calculation...")
        
        if not self.test_cycle_id:
            self.log_test("Negative Salary Calculation", "SKIP", "No payroll cycle available")
            return
        
        # Recalculate payroll
        response = self.make_request("POST", f"/payroll/cycles/{self.test_cycle_id}/recalculate")
        if response and response.status_code == 200:
            self.log_test("Payroll Recalculation", "PASS", "Payroll recalculated successfully")
            
            # Check payroll ledger for negative balance handling
            response = self.make_request("GET", f"/payroll/cycles/{self.test_cycle_id}/ledger")
            if response and response.status_code == 200:
                ledger_data = response.json()
                entries = ledger_data.get('entries', [])
                
                # Look for negative salary handling
                negative_entries = [e for e in entries if e.get('net_salary', 0) < 0]
                if negative_entries:
                    self.log_test("Negative Salary Detection", "PASS", 
                                 f"Found {len(negative_entries)} entries with negative salary")
                    
                    # Check for proper accounting entries
                    for entry in negative_entries:
                        net_salary = entry.get('net_salary', 0)
                        if 'receivable' in str(entry).lower() or 'debt' in str(entry).lower():
                            self.log_test("Negative Salary Accounting", "PASS", 
                                         f"Proper accounting entry for {net_salary} AED negative balance")
                        else:
                            self.log_test("Negative Salary Accounting", "WARN", 
                                         f"Negative salary {net_salary} AED may need special accounting treatment")
                else:
                    # Check if system prevents negative salary
                    self.log_test("Negative Salary Prevention", "INFO", 
                                 "System may be preventing negative salary calculations")
            else:
                self.log_test("Payroll Ledger Check", "FAIL", 
                             f"Failed to get ledger: {response.status_code if response else 'No response'}")
        else:
            self.log_test("Payroll Recalculation", "FAIL", 
                         f"Recalculation failed: {response.status_code if response else 'No response'}")
    
    def test_negative_salary_slip(self):
        """Test salary slip generation for negative balance"""
        print("\n📄 Testing salary slip for negative balance...")
        
        if not self.test_employee_id or not self.test_cycle_id:
            self.log_test("Negative Salary Slip", "SKIP", "Missing test data")
            return
        
        # Generate salary slip - check available endpoints first
        response = self.make_request("GET", f"/payroll/cycles/{self.test_cycle_id}/summary")
        if response and response.status_code == 200:
            content = response.content
            file_size = len(content)
            
            if file_size > 0:
                self.log_test("Negative Salary Slip - PDF", "PASS", 
                             f"Salary slip generated, size: {file_size} bytes")
                
                # Save evidence
                with open('/app/evidence_negative_salary_slip.pdf', 'wb') as f:
                    f.write(content)
                
                # Check for Arabic warning messages (basic check)
                if b'\xd8' in content or b'\xd9' in content:  # Arabic UTF-8 byte patterns
                    self.log_test("Negative Salary Slip - Arabic Content", "PASS", 
                                 "Arabic content detected in salary slip")
                else:
                    self.log_test("Negative Salary Slip - Arabic Content", "WARN", 
                                 "No Arabic content detected in salary slip")
            else:
                self.log_test("Negative Salary Slip - PDF", "FAIL", "Empty PDF generated")
        else:
            self.log_test("Negative Salary Slip - PDF", "FAIL", 
                         f"Failed to generate salary slip: {response.status_code if response else 'No response'}")

    # ============ SCENARIO 13: القفل/الفك + القيود العكسية (Lock/Unlock + Reversals) ============
    
    def test_scenario_13_lock_unlock_reversals(self):
        """SCENARIO 13: Testing lock/unlock and reversal entries"""
        print("\n🎯 SCENARIO 13: القفل/الفك + القيود العكسية (Lock/Unlock + Reversals)")
        print("=" * 70)
        
        # Test payroll cycle locking
        self.test_payroll_cycle_lock()
        
        # Test modifications after lock (should create reversals or be blocked)
        self.test_modifications_after_lock()
        
        # Test unlock cycle (super admin only)
        self.test_payroll_cycle_unlock()
        
        # Verify reversal entries
        self.test_reversal_entries_verification()
        
        # Test cycle deletion
        self.test_cycle_deletion()
    
    def test_payroll_cycle_lock(self):
        """Test payroll cycle locking mechanism"""
        print("\n🔒 Testing payroll cycle lock...")
        
        if not self.test_cycle_id:
            self.log_test("Payroll Cycle Lock", "SKIP", "No payroll cycle available")
            return
        
        # Lock the payroll cycle
        lock_data = {
            "lock_reason": "قفل دورة الرواتب - نهاية الشهر"
        }
        
        response = self.make_request("POST", f"/payroll/cycles/{self.test_cycle_id}/lock", json=lock_data)
        if response and response.status_code == 200:
            self.log_test("Payroll Cycle Lock", "PASS", "Payroll cycle locked successfully")
            
            # Verify cycle status
            response = self.make_request("GET", f"/payroll/cycles/{self.test_cycle_id}")
            if response and response.status_code == 200:
                cycle_data = response.json()
                if cycle_data.get('status') == 'locked':
                    self.log_test("Lock Status Verification", "PASS", "Cycle status updated to 'locked'")
                else:
                    self.log_test("Lock Status Verification", "FAIL", 
                                 f"Cycle status is '{cycle_data.get('status')}', expected 'locked'")
            else:
                self.log_test("Lock Status Verification", "FAIL", 
                             f"Failed to verify cycle status: {response.status_code if response else 'No response'}")
        else:
            self.log_test("Payroll Cycle Lock", "FAIL", 
                         f"Failed to lock cycle: {response.status_code if response else 'No response'}")
    
    def test_modifications_after_lock(self):
        """Test modifications after payroll cycle is locked"""
        print("\n🚫 Testing modifications after lock...")
        
        if not self.test_employee_id or not self.test_cycle_id:
            self.log_test("Modifications After Lock", "SKIP", "Missing test data")
            return
        
        # Test 1: Try to edit employee salary
        salary_update = {"monthly_salary": 4000.0}
        response = self.make_request("PUT", f"/payroll/cycles/{self.test_cycle_id}/update-employees", json=salary_update)
        
        if response and response.status_code == 403:
            self.log_test("Salary Edit After Lock", "PASS", "Salary edit properly blocked (403 Forbidden)")
        elif response and response.status_code == 200:
            # Check if reversal entry was created
            self.log_test("Salary Edit After Lock", "INFO", "Salary edit allowed - checking for reversal entry")
        else:
            self.log_test("Salary Edit After Lock", "FAIL", 
                         f"Unexpected response: {response.status_code if response else 'No response'}")
        
        # Test 2: Try to add installment
        installment_data = {
            "advance_id": str(uuid.uuid4()),
            "amount": 500.0,
            "due_date": "2025-11-01"
        }
        response = self.make_request("POST", f"/advances/{str(uuid.uuid4())}/installments", json=installment_data)
        
        if response and response.status_code == 403:
            self.log_test("Installment Add After Lock", "PASS", "Installment addition properly blocked (403 Forbidden)")
        elif response and response.status_code == 200:
            self.log_test("Installment Add After Lock", "INFO", "Installment addition allowed - checking for reversal entry")
        else:
            self.log_test("Installment Add After Lock", "FAIL", 
                         f"Unexpected response: {response.status_code if response else 'No response'}")
        
        # Test 3: Try to delete attendance
        # First get an attendance record
        response = self.make_request("GET", "/attendance")
        if response and response.status_code == 200:
            data = response.json()
            attendance_records = data.get('records', []) if isinstance(data, dict) else data
            if attendance_records:
                attendance_id = attendance_records[0]['id']
                
                response = self.make_request("DELETE", f"/attendance/{attendance_id}")
                if response and response.status_code == 403:
                    self.log_test("Attendance Delete After Lock", "PASS", "Attendance deletion properly blocked (403 Forbidden)")
                elif response and response.status_code == 200:
                    self.log_test("Attendance Delete After Lock", "INFO", "Attendance deletion allowed - checking for reversal entry")
                else:
                    self.log_test("Attendance Delete After Lock", "FAIL", 
                                 f"Unexpected response: {response.status_code if response else 'No response'}")
            else:
                self.log_test("Attendance Delete After Lock", "SKIP", "No attendance records found")
        else:
            self.log_test("Attendance Delete After Lock", "SKIP", "Failed to get attendance records")
    
    def test_payroll_cycle_unlock(self):
        """Test payroll cycle unlock (super admin only)"""
        print("\n🔓 Testing payroll cycle unlock...")
        
        if not self.test_cycle_id:
            self.log_test("Payroll Cycle Unlock", "SKIP", "No payroll cycle available")
            return
        
        # Unlock the payroll cycle
        unlock_data = {
            "unlock_reason": "فتح لتصحيح خطأ"
        }
        
        response = self.make_request("POST", f"/payroll/cycles/{self.test_cycle_id}/unlock", json=unlock_data)
        if response and response.status_code == 200:
            self.log_test("Payroll Cycle Unlock", "PASS", "Payroll cycle unlocked successfully")
            
            # Verify cycle status
            response = self.make_request("GET", f"/payroll/cycles/{self.test_cycle_id}")
            if response and response.status_code == 200:
                cycle_data = response.json()
                if cycle_data.get('status') == 'open':
                    self.log_test("Unlock Status Verification", "PASS", "Cycle status updated to 'open'")
                else:
                    self.log_test("Unlock Status Verification", "FAIL", 
                                 f"Cycle status is '{cycle_data.get('status')}', expected 'open'")
            else:
                self.log_test("Unlock Status Verification", "FAIL", 
                             f"Failed to verify cycle status: {response.status_code if response else 'No response'}")
        else:
            self.log_test("Payroll Cycle Unlock", "FAIL", 
                         f"Failed to unlock cycle: {response.status_code if response else 'No response'}")
    
    def test_reversal_entries_verification(self):
        """Verify reversal entries in ledger"""
        print("\n🔄 Verifying reversal entries...")
        
        if not self.test_cycle_id:
            self.log_test("Reversal Entries Verification", "SKIP", "No payroll cycle available")
            return
        
        # Get payroll ledger
        response = self.make_request("GET", f"/payroll/cycles/{self.test_cycle_id}/ledger")
        if response and response.status_code == 200:
            ledger_data = response.json()
            entries = ledger_data.get('entries', [])
            
            # Look for reversal entries
            reversal_entries = [e for e in entries if e.get('entry_type') == 'REVERSAL']
            
            if reversal_entries:
                self.log_test("Reversal Entries Found", "PASS", 
                             f"Found {len(reversal_entries)} reversal entries")
                
                # Verify reversal entry structure
                for entry in reversal_entries[:3]:  # Check first 3 entries
                    required_fields = ['entry_type', 'reference', 'reason', 'created_by']
                    missing_fields = [field for field in required_fields if field not in entry]
                    
                    if not missing_fields:
                        self.log_test("Reversal Entry Structure", "PASS", 
                                     f"Reversal entry has all required fields")
                    else:
                        self.log_test("Reversal Entry Structure", "FAIL", 
                                     f"Missing fields in reversal entry: {missing_fields}")
                
                # Verify ledger balance
                total_balance = sum(e.get('amount', 0) for e in entries)
                self.log_test("Ledger Balance Verification", "PASS" if total_balance == 0 else "WARN", 
                             f"Ledger balance: {total_balance} (should be 0 if properly balanced)")
            else:
                self.log_test("Reversal Entries Found", "INFO", 
                             "No reversal entries found - system may prevent modifications instead")
        else:
            self.log_test("Reversal Entries Verification", "FAIL", 
                         f"Failed to get ledger: {response.status_code if response else 'No response'}")
    
    def test_cycle_deletion(self):
        """Test payroll cycle deletion"""
        print("\n🗑️ Testing cycle deletion...")
        
        if not self.test_cycle_id:
            self.log_test("Cycle Deletion", "SKIP", "No payroll cycle available")
            return
        
        # Try to delete the cycle
        response = self.make_request("DELETE", f"/payroll/cycles/{self.test_cycle_id}")
        if response and response.status_code == 200:
            self.log_test("Cycle Deletion", "PASS", "Payroll cycle deleted successfully")
            
            # Verify cleanup - check if cycle still exists
            response = self.make_request("GET", f"/payroll/cycles/{self.test_cycle_id}")
            if response and response.status_code == 404:
                self.log_test("Cycle Cleanup Verification", "PASS", "Cycle properly removed from database")
            else:
                self.log_test("Cycle Cleanup Verification", "FAIL", 
                             f"Cycle still exists after deletion: {response.status_code if response else 'No response'}")
        else:
            self.log_test("Cycle Deletion", "FAIL", 
                         f"Failed to delete cycle: {response.status_code if response else 'No response'}")

    def run_all_scenarios(self):
        """Run all Arabic scenarios testing"""
        print("🚀 Starting Arabic Scenarios 9, 12, 13 Backend Testing")
        print("=" * 80)
        
        try:
            # Authenticate as super admin
            auth_result = self.authenticate("super_admin")
            if not auth_result:
                print("❌ Failed to authenticate as super admin. Aborting tests.")
                return
            
            # Run all scenarios
            self.test_scenario_9_comprehensive_reports()
            self.test_scenario_12_negative_salary_edge_cases()
            self.test_scenario_13_lock_unlock_reversals()
            
            # Generate summary
            self.generate_summary()
            
        except Exception as e:
            print(f"❌ Critical error during testing: {str(e)}")
            self.log_test("Critical Error", "FAIL", str(e))
    
    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "=" * 80)
        print("📊 ARABIC SCENARIOS 9, 12, 13 - TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t['status'] == 'PASS'])
        failed_tests = len([t for t in self.test_results if t['status'] == 'FAIL'])
        skipped_tests = len([t for t in self.test_results if t['status'] == 'SKIP'])
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📈 Overall Results:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   ⏭️ Skipped: {skipped_tests}")
        print(f"   📊 Success Rate: {success_rate:.1f}%")
        
        # Scenario breakdown
        scenarios = {
            "SCENARIO 9": [t for t in self.test_results if "Report" in t['test'] or "Export" in t['test']],
            "SCENARIO 12": [t for t in self.test_results if "Negative" in t['test'] or "Edge" in t['test'] or "Deduction" in t['test']],
            "SCENARIO 13": [t for t in self.test_results if "Lock" in t['test'] or "Unlock" in t['test'] or "Reversal" in t['test']]
        }
        
        print(f"\n📋 Scenario Breakdown:")
        for scenario_name, scenario_tests in scenarios.items():
            if scenario_tests:
                scenario_passed = len([t for t in scenario_tests if t['status'] == 'PASS'])
                scenario_total = len(scenario_tests)
                scenario_rate = (scenario_passed / scenario_total * 100) if scenario_total > 0 else 0
                print(f"   {scenario_name}: {scenario_passed}/{scenario_total} ({scenario_rate:.1f}%)")
        
        # Failed tests details
        failed_test_details = [t for t in self.test_results if t['status'] == 'FAIL']
        if failed_test_details:
            print(f"\n❌ Failed Tests Details:")
            for test in failed_test_details:
                print(f"   • {test['test']}: {test['details']}")
        
        # Save detailed results
        with open('/app/arabic_scenarios_9_12_13_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n💾 Detailed results saved to: arabic_scenarios_9_12_13_test_results.json")
        print("=" * 80)

if __name__ == "__main__":
    tester = ArabicScenariosBackendTester()
    tester.run_all_scenarios()