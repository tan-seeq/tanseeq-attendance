#!/usr/bin/env python3
"""
Backend Quick Sanity Retest after frontend fixes
Focus areas:
1. Auth flow /api/auth/login and /api/auth/me
2. Payroll cycles: GET list, GET single by id, calculate, and export endpoints (pdf & excel) while authenticated to ensure 200s and file content-type
3. Attendance deductions: employees/name presence and manual CRUD
4. Ensure all endpoints return 401 when unauthenticated
5. Use tokens for both admin and user
6. Return failures with payloads and status codes
"""

import requests
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import time

# Configuration - Use environment variable
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tanseeq-hr-fix.preview.emergentagent.com')
BASE_URL = f"{BACKEND_URL}/api"

# Test accounts
TEST_ACCOUNTS = {
    "admin": {"email": "admin@tanseeq.com", "password": "ADMIN"},
    "user": {"email": "jihad@tanseeq.com", "password": "jihad123"}
}

class QuickSanityTester:
    def __init__(self):
        self.session = requests.Session()
        self.tokens = {}
        self.test_results = []
        self.evidence_dir = Path("./evidence/quick_sanity")
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        
    def log_result(self, test_name, status, details="", response_data=None):
        """Log test result with detailed information"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        if response_data:
            result["response"] = {
                "status_code": response_data.get("status_code"),
                "headers": dict(response_data.get("headers", {})),
                "content_length": len(response_data.get("content", ""))
            }
        self.test_results.append(result)
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {details}")
        
    def test_authentication_flow(self):
        """Test authentication endpoints for both admin and user"""
        print("\n🔐 Testing Authentication Flow...")
        
        for role, credentials in TEST_ACCOUNTS.items():
            try:
                # Test login
                response = self.session.post(f"{BASE_URL}/auth/login", json=credentials)
                
                if response.status_code == 200:
                    data = response.json()
                    token = data.get("access_token")
                    user_info = data.get("user", {})
                    
                    if token and user_info:
                        self.tokens[role] = token
                        self.log_result(f"Auth Login - {role}", "PASS", 
                                      f"Login successful for {credentials['email']}, role: {user_info.get('role')}")
                        
                        # Test /auth/me endpoint
                        headers = {"Authorization": f"Bearer {token}"}
                        me_response = self.session.get(f"{BASE_URL}/auth/me", headers=headers)
                        
                        if me_response.status_code == 200:
                            me_data = me_response.json()
                            self.log_result(f"Auth Me - {role}", "PASS", 
                                          f"User info retrieved: {me_data.get('name')} ({me_data.get('email')})")
                        else:
                            self.log_result(f"Auth Me - {role}", "FAIL", 
                                          f"Failed: {me_response.status_code} - {me_response.text}")
                    else:
                        self.log_result(f"Auth Login - {role}", "FAIL", 
                                      "Missing token or user info in response")
                else:
                    self.log_result(f"Auth Login - {role}", "FAIL", 
                                  f"Login failed: {response.status_code} - {response.text}")
                    
            except Exception as e:
                self.log_result(f"Auth - {role}", "FAIL", f"Exception: {str(e)}")
    
    def test_unauthenticated_access(self):
        """Test that endpoints return 401 when unauthenticated"""
        print("\n🚫 Testing Unauthenticated Access (401 checks)...")
        
        # Clear any existing authorization
        if "Authorization" in self.session.headers:
            del self.session.headers["Authorization"]
        
        # Test endpoints that should require authentication
        endpoints_to_test = [
            "/auth/me",
            "/payroll/cycles",
            "/employees/list", 
            "/deductions",
            "/marketing-visits/active"
        ]
        
        for endpoint in endpoints_to_test:
            try:
                response = self.session.get(f"{BASE_URL}{endpoint}")
                
                if response.status_code == 401:
                    self.log_result(f"401 Check - {endpoint}", "PASS", 
                                  "Correctly returns 401 Unauthorized")
                else:
                    self.log_result(f"401 Check - {endpoint}", "FAIL", 
                                  f"Expected 401, got {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"401 Check - {endpoint}", "FAIL", f"Exception: {str(e)}")
    
    def test_payroll_cycles_comprehensive(self):
        """Test payroll cycles endpoints comprehensively"""
        print("\n💰 Testing Payroll Cycles Comprehensive...")
        
        # Use admin token
        if "admin" not in self.tokens:
            self.log_result("Payroll Cycles", "SKIP", "No admin token available")
            return
            
        headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
        
        # 1. GET list of cycles
        try:
            response = self.session.get(f"{BASE_URL}/payroll/cycles", headers=headers)
            
            if response.status_code == 200:
                cycles_data = response.json()
                # Handle both list and object formats
                if isinstance(cycles_data, list):
                    cycles = cycles_data
                else:
                    cycles = cycles_data.get('cycles', [])
                
                self.log_result("Payroll Cycles - List", "PASS", 
                              f"Retrieved {len(cycles)} cycles")
                
                # Test single cycle by ID if cycles exist
                if cycles:
                    cycle_id = cycles[0].get('id')
                    if cycle_id:
                        self.test_single_payroll_cycle(cycle_id, headers)
                else:
                    self.log_result("Payroll Cycles - Single", "SKIP", "No cycles available for testing")
            else:
                self.log_result("Payroll Cycles - List", "FAIL", 
                              f"Failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Payroll Cycles - List", "FAIL", f"Exception: {str(e)}")
    
    def test_single_payroll_cycle(self, cycle_id, headers):
        """Test single payroll cycle operations"""
        
        # 2. GET single cycle by ID
        try:
            response = self.session.get(f"{BASE_URL}/payroll/cycles/{cycle_id}", headers=headers)
            
            if response.status_code == 200:
                cycle_data = response.json()
                self.log_result("Payroll Cycles - Single", "PASS", 
                              f"Retrieved cycle: {cycle_data.get('month', 'Unknown')}")
            else:
                self.log_result("Payroll Cycles - Single", "FAIL", 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("Payroll Cycles - Single", "FAIL", f"Exception: {str(e)}")
        
        # 3. Calculate cycle
        try:
            response = self.session.get(f"{BASE_URL}/payroll/cycles/{cycle_id}/calculate", headers=headers)
            
            if response.status_code == 200:
                calc_data = response.json()
                totals = calc_data.get('totals', {})
                self.log_result("Payroll Cycles - Calculate", "PASS", 
                              f"Calculation successful, {len(totals)} employee totals")
            else:
                self.log_result("Payroll Cycles - Calculate", "FAIL", 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("Payroll Cycles - Calculate", "FAIL", f"Exception: {str(e)}")
        
        # 4. Test PDF Export
        try:
            response = self.session.get(f"{BASE_URL}/payroll/cycles/{cycle_id}/export/pdf", headers=headers)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                content_length = len(response.content)
                
                if 'pdf' in content_type and content_length > 0:
                    # Save PDF for evidence
                    pdf_path = self.evidence_dir / f"payroll_cycle_{cycle_id}.pdf"
                    with open(pdf_path, 'wb') as f:
                        f.write(response.content)
                    
                    self.log_result("Payroll Cycles - PDF Export", "PASS", 
                                  f"PDF exported: content-type={content_type}, size={content_length} bytes")
                else:
                    self.log_result("Payroll Cycles - PDF Export", "FAIL", 
                                  f"Invalid PDF: content-type={content_type}, size={content_length}")
            else:
                self.log_result("Payroll Cycles - PDF Export", "FAIL", 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("Payroll Cycles - PDF Export", "FAIL", f"Exception: {str(e)}")
        
        # 5. Test Excel Export
        try:
            response = self.session.get(f"{BASE_URL}/payroll/cycles/{cycle_id}/export/excel", headers=headers)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                content_length = len(response.content)
                
                if ('excel' in content_type or 'spreadsheet' in content_type) and content_length > 0:
                    # Save Excel for evidence
                    excel_path = self.evidence_dir / f"payroll_cycle_{cycle_id}.xlsx"
                    with open(excel_path, 'wb') as f:
                        f.write(response.content)
                    
                    self.log_result("Payroll Cycles - Excel Export", "PASS", 
                                  f"Excel exported: content-type={content_type}, size={content_length} bytes")
                else:
                    self.log_result("Payroll Cycles - Excel Export", "FAIL", 
                                  f"Invalid Excel: content-type={content_type}, size={content_length}")
            else:
                self.log_result("Payroll Cycles - Excel Export", "FAIL", 
                              f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("Payroll Cycles - Excel Export", "FAIL", f"Exception: {str(e)}")
    
    def test_attendance_deductions(self):
        """Test attendance deductions with employee name presence and CRUD"""
        print("\n📊 Testing Attendance Deductions...")
        
        # Test with both admin and user tokens
        for role in ["admin", "user"]:
            if role not in self.tokens:
                continue
                
            headers = {"Authorization": f"Bearer {self.tokens[role]}"}
            
            # 1. Test employees list endpoint
            try:
                response = self.session.get(f"{BASE_URL}/employees/list", headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    # Handle both direct list and object with employees key
                    if isinstance(data, list):
                        employees = data
                    else:
                        employees = data.get('employees', [])
                    
                    if employees and len(employees) > 0:
                        # Check if employees have name field
                        first_emp = employees[0]
                        if 'name' in first_emp:
                            self.log_result(f"Employees List - {role}", "PASS", 
                                          f"Retrieved {len(employees)} employees with names")
                            
                            # Store employee ID for CRUD testing (admin only)
                            if role == "admin" and 'id' in first_emp:
                                self.test_employee_id = first_emp['id']
                        else:
                            self.log_result(f"Employees List - {role}", "FAIL", 
                                          "Employees missing name field")
                    else:
                        self.log_result(f"Employees List - {role}", "FAIL", "No employees returned")
                else:
                    self.log_result(f"Employees List - {role}", "FAIL", 
                                  f"Failed: {response.status_code} - {response.text}")
            except Exception as e:
                self.log_result(f"Employees List - {role}", "FAIL", f"Exception: {str(e)}")
            
            # 2. Test deductions list with employee_name presence
            try:
                current_month = datetime.now().strftime("%Y-%m")
                response = self.session.get(f"{BASE_URL}/deductions?month={current_month}", headers=headers)
                
                if response.status_code == 200:
                    deductions = response.json()
                    if isinstance(deductions, list):
                        if len(deductions) > 0:
                            # Check if deductions include employee_name
                            first_deduction = deductions[0]
                            if 'employee_name' in first_deduction:
                                self.log_result(f"Deductions List - {role}", "PASS", 
                                              f"Retrieved {len(deductions)} deductions with employee_name")
                            else:
                                self.log_result(f"Deductions List - {role}", "FAIL", 
                                              "Deductions missing employee_name field")
                        else:
                            self.log_result(f"Deductions List - {role}", "PASS", 
                                          "No deductions found (empty list is valid)")
                    else:
                        self.log_result(f"Deductions List - {role}", "FAIL", "Invalid response format")
                else:
                    self.log_result(f"Deductions List - {role}", "FAIL", 
                                  f"Failed: {response.status_code} - {response.text}")
            except Exception as e:
                self.log_result(f"Deductions List - {role}", "FAIL", f"Exception: {str(e)}")
        
        # 3. Test manual deduction CRUD (admin only)
        if "admin" in self.tokens and hasattr(self, 'test_employee_id'):
            self.test_manual_deduction_crud()
    
    def test_manual_deduction_crud(self):
        """Test manual deduction Create, Read, Update, Delete operations"""
        headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
        deduction_id = None
        
        try:
            # CREATE - Manual deduction
            deduction_data = {
                "employee_id": self.test_employee_id,
                "amount": 25.0,
                "reason": "Quick sanity test deduction",
                "category": "late_arrival",
                "date": datetime.now().strftime("%Y-%m-%d")
            }
            
            response = self.session.post(f"{BASE_URL}/deductions/manual", json=deduction_data, headers=headers)
            if response.status_code in [200, 201]:
                result = response.json()
                deduction_id = result.get("id") or result.get("deduction_id")
                self.log_result("Manual Deductions - Create", "PASS", 
                              f"Created deduction: {deduction_id}")
            else:
                self.log_result("Manual Deductions - Create", "FAIL", 
                              f"Failed: {response.status_code} - {response.text}")
                return
            
            if deduction_id:
                # UPDATE - Edit deduction
                edit_data = {
                    "amount": 35.0,
                    "reason": "Updated quick sanity test deduction"
                }
                response = self.session.patch(f"{BASE_URL}/deductions/{deduction_id}", json=edit_data, headers=headers)
                if response.status_code == 200:
                    self.log_result("Manual Deductions - Update", "PASS", "Deduction updated successfully")
                else:
                    self.log_result("Manual Deductions - Update", "FAIL", 
                                  f"Failed: {response.status_code} - {response.text}")
                
                # DELETE/VOID - Void deduction
                void_data = {"void_reason": "Quick sanity test cleanup"}
                response = self.session.post(f"{BASE_URL}/deductions/{deduction_id}/void", json=void_data, headers=headers)
                if response.status_code == 200:
                    self.log_result("Manual Deductions - Void", "PASS", "Deduction voided successfully")
                else:
                    self.log_result("Manual Deductions - Void", "FAIL", 
                                  f"Failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Manual Deductions - CRUD", "FAIL", f"Exception: {str(e)}")
    
    def test_token_validation(self):
        """Test that both admin and user tokens work correctly"""
        print("\n🎫 Testing Token Validation...")
        
        for role, token in self.tokens.items():
            try:
                headers = {"Authorization": f"Bearer {token}"}
                
                # Test a simple authenticated endpoint
                response = self.session.get(f"{BASE_URL}/auth/me", headers=headers)
                
                if response.status_code == 200:
                    user_data = response.json()
                    self.log_result(f"Token Validation - {role}", "PASS", 
                                  f"Token valid for {user_data.get('email')} ({user_data.get('role')})")
                else:
                    self.log_result(f"Token Validation - {role}", "FAIL", 
                                  f"Token invalid: {response.status_code} - {response.text}")
                    
            except Exception as e:
                self.log_result(f"Token Validation - {role}", "FAIL", f"Exception: {str(e)}")
    
    def run_quick_sanity_tests(self):
        """Run all quick sanity tests"""
        print("🚀 Starting Backend Quick Sanity Retest")
        print(f"Base URL: {BASE_URL}")
        print("=" * 60)
        
        # 1. Test authentication flow
        self.test_authentication_flow()
        
        # 2. Test unauthenticated access returns 401
        self.test_unauthenticated_access()
        
        # 3. Test token validation
        self.test_token_validation()
        
        # 4. Test payroll cycles comprehensive
        self.test_payroll_cycles_comprehensive()
        
        # 5. Test attendance deductions
        self.test_attendance_deductions()
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "=" * 60)
        print("📋 QUICK SANITY RETEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        skipped_tests = len([r for r in self.test_results if r["status"] == "SKIP"])
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⏭️ Skipped: {skipped_tests}")
        
        if total_tests > 0:
            success_rate = (passed_tests/total_tests)*100
            print(f"Success Rate: {success_rate:.1f}%")
        
        # Show failed tests with details
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"  • {result['test']}: {result['details']}")
        
        # Show critical issues
        critical_failures = []
        for result in self.test_results:
            if result["status"] == "FAIL":
                if "Auth" in result["test"] or "401" in result["test"]:
                    critical_failures.append(result)
        
        if critical_failures:
            print("\n🚨 CRITICAL FAILURES:")
            for failure in critical_failures:
                print(f"  • {failure['test']}: {failure['details']}")
        
        # Save detailed results
        results_file = Path("./quick_sanity_results.json")
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        print(f"📁 Evidence files saved to: {self.evidence_dir}")

if __name__ == "__main__":
    tester = QuickSanityTester()
    tester.run_quick_sanity_tests()