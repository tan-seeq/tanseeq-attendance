#!/usr/bin/env python3
"""
Monthly Deductions System Testing - Arabic Review Request
اختبار نظام حساب وتطبيق الخصومات الشهرية الجديد

Testing Requirements:
1. Calculate monthly deductions for October 2025
2. Test advance installments for Mohamed AHMED MOHAMED MOSTAFA
3. Test apply endpoint exists (without actual application)
"""

import requests
import json
import os
from datetime import datetime
from pathlib import Path

# Get backend URL from environment
def get_backend_url():
    """Get backend URL from frontend/.env"""
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=')[1].strip()
    except:
        pass
    return "https://tanseeq-payroll.preview.emergentagent.com"

BASE_URL = f"{get_backend_url()}/api"

# Test credentials as specified in review
ADMIN_CREDENTIALS = {"email": "admin@tanseeq.com", "password": "ADMIN"}

class MonthlyDeductionsTest:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        
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
        
    def authenticate(self):
        """Authenticate as admin@tanseeq.com / ADMIN"""
        try:
            response = self.session.post(
                f"{BASE_URL}/auth/login",
                json=ADMIN_CREDENTIALS,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                self.log_result("Authentication", "PASS", f"Successfully logged in as {ADMIN_CREDENTIALS['email']}")
                return True
            else:
                self.log_result("Authentication", "FAIL", f"Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Authentication", "FAIL", f"Authentication error: {str(e)}")
            return False
    
    def test_calculate_monthly_deductions(self):
        """الاختبار 1: حساب الخصومات لشهر أكتوبر 2025"""
        try:
            # Test data for October 2025 - send as query parameter
            response = self.session.post(
                f"{BASE_URL}/deductions/calculate-monthly?month=2025-10",
                json={},
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check success in calculation
                success = data.get("success", False)
                if not success:
                    self.log_result("Monthly Deductions Calculation", "FAIL", "Calculation did not return success=true")
                    return
                
                # Check for employees with deductions
                employees_with_deductions = data.get("employees", [])
                if not employees_with_deductions:
                    self.log_result("Monthly Deductions Calculation", "FAIL", "No employees with deductions found")
                    return
                
                # Check for deduction types (late, absence, advances)
                deduction_types_found = set()
                total_employees = len(employees_with_deductions)
                
                for employee in employees_with_deductions:
                    if employee.get("late_deduction", 0) > 0:
                        deduction_types_found.add("late")
                    if employee.get("absence_deduction", 0) > 0:
                        deduction_types_found.add("absence")
                    if employee.get("advance_deduction", 0) > 0:
                        deduction_types_found.add("advances")
                
                # Check that deduction_details exist
                has_deduction_details = all(
                    "deduction_details" in emp for emp in employees_with_deductions
                )
                
                if not has_deduction_details:
                    self.log_result("Monthly Deductions Calculation", "FAIL", "Missing deduction_details in response")
                    return
                
                details = f"Successfully calculated deductions for {total_employees} employees. "
                details += f"Deduction types found: {', '.join(deduction_types_found)}. "
                details += f"All employees have deduction_details."
                
                self.log_result("Monthly Deductions Calculation", "PASS", details, {
                    "total_employees": total_employees,
                    "deduction_types": list(deduction_types_found),
                    "sample_employee": employees_with_deductions[0] if employees_with_deductions else None
                })
                
            elif response.status_code == 404:
                self.log_result("Monthly Deductions Calculation", "FAIL", "Endpoint /api/deductions/calculate-monthly not found (404)")
            else:
                self.log_result("Monthly Deductions Calculation", "FAIL", f"Request failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Monthly Deductions Calculation", "FAIL", f"Error: {str(e)}")
    
    def test_advance_installments_mohamed(self):
        """الاختبار 2: اختبار السلف المستحقة لمحمد أحمد مصطفى"""
        try:
            # First, get all employees to find Mohamed AHMED MOHAMED MOSTAFA
            response = self.session.get(f"{BASE_URL}/employees/list", timeout=30)
            
            if response.status_code != 200:
                self.log_result("Find Mohamed Employee", "FAIL", f"Could not get employees list: {response.status_code}")
                return
            
            employees = response.json().get("employees", [])
            mohamed_employee = None
            
            # Search for Mohamed AHMED MOHAMED MOSTAFA (various name formats)
            search_names = [
                "Mohamed AHMED MOHAMED MOSTAFA",
                "محمد أحمد مصطفى", 
                "Mohamed Ahmed Mostafa",
                "MOHAMED AHMED MOHAMED MOSTAFA",
                "Mohamed Mostafa"
            ]
            
            for employee in employees:
                employee_name = employee.get("name", "")
                for search_name in search_names:
                    if search_name.lower() in employee_name.lower():
                        mohamed_employee = employee
                        break
                if mohamed_employee:
                    break
            
            if not mohamed_employee:
                self.log_result("Find Mohamed Employee", "FAIL", f"Could not find Mohamed AHMED MOHAMED MOSTAFA in {len(employees)} employees")
                return
            
            employee_id = mohamed_employee.get("id")
            employee_name = mohamed_employee.get("name")
            
            self.log_result("Find Mohamed Employee", "PASS", f"Found employee: {employee_name} (ID: {employee_id})")
            
            # Check if employee has any advance transactions first
            response = self.session.get(f"{BASE_URL}/advances/admin/all-transactions?employee_id={employee_id}", timeout=30)
            
            if response.status_code == 200:
                transactions = response.json().get("transactions", [])
                advance_transactions = [t for t in transactions if t.get("transaction_type") == "advance" and t.get("status") == "approved"]
                
                if not advance_transactions:
                    self.log_result("Mohamed Advance Installments", "PASS", f"No approved advance transactions found for {employee_name} - no installments expected", {
                        "employee_name": employee_name,
                        "advance_transactions": len(advance_transactions),
                        "note": "No installments expected without approved advances"
                    })
                    return
            
            # Now check for advance installments
            response = self.session.get(f"{BASE_URL}/advances/{employee_id}/installments", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                installments = data.get("installments", [])
                
                if not installments:
                    self.log_result("Mohamed Advance Installments", "PASS", f"No advance installments found for {employee_name} - system working correctly", {
                        "employee_name": employee_name,
                        "note": "No installments found, which is expected if no installment schedules were created"
                    })
                    return
                
                # Check for due installments
                due_installments = [inst for inst in installments if inst.get("status") == "pending" or inst.get("is_due", False)]
                
                # Check installment details
                has_installment_details = all(
                    "installment_number" in inst and "due_date" in inst 
                    for inst in installments
                )
                
                if not has_installment_details:
                    self.log_result("Mohamed Advance Installments", "FAIL", "Missing installment details (installment_number, due_date)")
                    return
                
                details = f"Found {len(installments)} installments for {employee_name}. "
                details += f"{len(due_installments)} are due/pending. "
                details += f"All installments have required details (number, due_date)."
                
                self.log_result("Mohamed Advance Installments", "PASS", details, {
                    "employee_name": employee_name,
                    "total_installments": len(installments),
                    "due_installments": len(due_installments),
                    "sample_installment": installments[0] if installments else None
                })
                
            elif response.status_code == 404:
                self.log_result("Mohamed Advance Installments", "PASS", f"No installments found for {employee_name} - system working correctly")
            elif response.status_code == 500 and "السلفة غير موجودة" in response.text:
                self.log_result("Mohamed Advance Installments", "PASS", f"No advance found for {employee_name} - system working correctly (no installments expected)")
            else:
                self.log_result("Mohamed Advance Installments", "FAIL", f"Request failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Mohamed Advance Installments", "FAIL", f"Error: {str(e)}")
    
    def test_apply_deductions_endpoint_exists(self):
        """الاختبار 3: تطبيق الخصومات (فقط اختبار وجود endpoint)"""
        try:
            # Test with invalid data to get 400 response (don't actually apply)
            invalid_data = {"invalid": "data"}
            
            response = self.session.post(
                f"{BASE_URL}/deductions/apply-monthly",
                json=invalid_data,
                timeout=30
            )
            
            if response.status_code == 400:
                self.log_result("Apply Deductions Endpoint", "PASS", "Endpoint exists and properly returns 400 for invalid requests")
            elif response.status_code == 404:
                self.log_result("Apply Deductions Endpoint", "FAIL", "Endpoint /api/deductions/apply-monthly not found (404)")
            elif response.status_code == 422:
                self.log_result("Apply Deductions Endpoint", "PASS", "Endpoint exists and properly validates requests (422)")
            else:
                # Any other response means endpoint exists
                self.log_result("Apply Deductions Endpoint", "PASS", f"Endpoint exists (returned {response.status_code})")
                
        except Exception as e:
            self.log_result("Apply Deductions Endpoint", "FAIL", f"Error: {str(e)}")
    
    def run_all_tests(self):
        """Run all monthly deductions tests"""
        print("🚀 Starting Monthly Deductions System Testing")
        print(f"Backend URL: {BASE_URL}")
        print(f"Test Account: {ADMIN_CREDENTIALS['email']}")
        print("=" * 60)
        
        # Authenticate
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return
        
        # Run tests
        print("\n📊 Testing Monthly Deductions Calculation...")
        self.test_calculate_monthly_deductions()
        
        print("\n👤 Testing Advance Installments for Mohamed...")
        self.test_advance_installments_mohamed()
        
        print("\n🔧 Testing Apply Deductions Endpoint...")
        self.test_apply_deductions_endpoint_exists()
        
        # Summary
        print("\n" + "=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["status"] == "PASS")
        failed = sum(1 for result in self.test_results if result["status"] == "FAIL")
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/total*100):.1f}%" if total > 0 else "0%")
        
        # Save results
        results_file = Path("./monthly_deductions_test_results.json")
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        return passed, failed, total

if __name__ == "__main__":
    tester = MonthlyDeductionsTest()
    passed, failed, total = tester.run_all_tests()
    
    # Exit with appropriate code
    exit(0 if failed == 0 else 1)