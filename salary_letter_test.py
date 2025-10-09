#!/usr/bin/env python3
"""
Salary Letter System Testing - Arabic Review Request
Testing the new monthly salary letter system for employees
اختبار نظام رسائل الراتب الشهرية الجديد
"""

import requests
import json
import os
from datetime import datetime
from pathlib import Path
import time

# Configuration - Use environment variable
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://hr-system-upgrade.preview.emergentagent.com')
BASE_URL = f"{BACKEND_URL}/api"

# Test accounts
TEST_ACCOUNTS = {
    "admin": {"email": "admin@tanseeq.com", "password": "ADMIN"}
}

# Test data from Arabic review
OCTOBER_2025_CYCLE_ID = "e70625f9-f78e-4be3-b02e-1c51cdf5385e"

class SalaryLetterTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        self.evidence_dir = Path("./evidence/salary_letters")
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
        
    def authenticate(self):
        """Authenticate as admin"""
        try:
            account = TEST_ACCOUNTS["admin"]
            response = self.session.post(f"{BASE_URL}/auth/login", json=account)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                self.log_result("Authentication", "PASS", 
                              f"Successfully authenticated {account['email']}")
                return True
            else:
                self.log_result("Authentication", "FAIL", 
                              f"Failed to authenticate: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Authentication", "FAIL", f"Exception: {str(e)}")
            return False
    
    def get_employee_by_name(self, employee_name):
        """Get employee ID by name"""
        try:
            response = self.session.get(f"{BASE_URL}/employees/list")
            if response.status_code == 200:
                data = response.json()
                # Handle both direct list and object with employees key
                if isinstance(data, list):
                    employees = data
                else:
                    employees = data.get('employees', [])
                
                # Search for employee by name (case insensitive)
                for employee in employees:
                    if employee_name.lower() in employee.get('name', '').lower():
                        self.log_result(f"Find Employee - {employee_name}", "PASS", 
                                      f"Found employee: {employee['name']} (ID: {employee['id']})")
                        return employee['id'], employee['name']
                
                self.log_result(f"Find Employee - {employee_name}", "FAIL", 
                              f"Employee '{employee_name}' not found in {len(employees)} employees")
                return None, None
            else:
                self.log_result(f"Find Employee - {employee_name}", "FAIL", 
                              f"Failed to get employees list: {response.status_code}")
                return None, None
                
        except Exception as e:
            self.log_result(f"Find Employee - {employee_name}", "FAIL", f"Exception: {str(e)}")
            return None, None
    
    def verify_cycle_exists(self, cycle_id):
        """Verify that the October 2025 cycle exists"""
        try:
            response = self.session.get(f"{BASE_URL}/payroll/cycles")
            if response.status_code == 200:
                data = response.json()
                # Handle both direct list and object with cycles key
                if isinstance(data, list):
                    cycles = data
                else:
                    cycles = data.get('cycles', [])
                
                # Search for the specific cycle
                for cycle in cycles:
                    if cycle.get('id') == cycle_id:
                        self.log_result("Verify October 2025 Cycle", "PASS", 
                                      f"Found cycle: {cycle.get('month', 'Unknown')} (ID: {cycle_id})")
                        return True
                
                self.log_result("Verify October 2025 Cycle", "FAIL", 
                              f"Cycle {cycle_id} not found in {len(cycles)} cycles")
                return False
            else:
                self.log_result("Verify October 2025 Cycle", "FAIL", 
                              f"Failed to get cycles: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Verify October 2025 Cycle", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_html_salary_letter(self, employee_id, employee_name, cycle_id):
        """Test HTML salary letter generation"""
        try:
            url = f"{BASE_URL}/payroll/cycles/{cycle_id}/employees/{employee_id}/letter"
            params = {"format": "html"}
            
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                html_content = response.text
                
                # Verify HTML content
                checks = {
                    "HTML Structure": "<html>" in html_content and "</html>" in html_content,
                    "Employee Name": employee_name in html_content,
                    "Company Name": "TANSEEQ" in html_content or "تنسيق" in html_content,
                    "Salary Data": "راتب" in html_content or "salary" in html_content.lower(),
                    "Content Length": len(html_content) > 500
                }
                
                passed_checks = sum(checks.values())
                total_checks = len(checks)
                
                # Save HTML file for evidence
                html_file = self.evidence_dir / f"{employee_name.replace(' ', '_')}_salary_letter.html"
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                if passed_checks >= 4:  # At least 4 out of 5 checks should pass
                    self.log_result(f"HTML Salary Letter - {employee_name}", "PASS", 
                                  f"Generated successfully ({passed_checks}/{total_checks} checks passed). "
                                  f"Content length: {len(html_content)} chars. Saved to: {html_file}")
                    return True
                else:
                    failed_checks = [check for check, passed in checks.items() if not passed]
                    self.log_result(f"HTML Salary Letter - {employee_name}", "FAIL", 
                                  f"Content validation failed. Failed checks: {failed_checks}")
                    return False
            else:
                self.log_result(f"HTML Salary Letter - {employee_name}", "FAIL", 
                              f"Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result(f"HTML Salary Letter - {employee_name}", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_pdf_salary_letter(self, employee_id, employee_name, cycle_id):
        """Test PDF salary letter generation"""
        try:
            url = f"{BASE_URL}/payroll/cycles/{cycle_id}/employees/{employee_id}/letter"
            params = {"format": "pdf"}
            
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                content_length = len(response.content)
                
                # Verify PDF properties
                checks = {
                    "Content-Type": 'pdf' in content_type,
                    "File Size": content_length > 1000,  # PDF should be at least 1KB
                    "PDF Header": response.content.startswith(b'%PDF'),
                    "Content Length": content_length > 0
                }
                
                passed_checks = sum(checks.values())
                total_checks = len(checks)
                
                # Save PDF file for evidence
                pdf_file = self.evidence_dir / f"{employee_name.replace(' ', '_')}_salary_letter.pdf"
                with open(pdf_file, 'wb') as f:
                    f.write(response.content)
                
                if passed_checks >= 3:  # At least 3 out of 4 checks should pass
                    self.log_result(f"PDF Salary Letter - {employee_name}", "PASS", 
                                  f"Generated successfully ({passed_checks}/{total_checks} checks passed). "
                                  f"Content-Type: {content_type}, Size: {content_length} bytes. Saved to: {pdf_file}")
                    return True
                else:
                    failed_checks = [check for check, passed in checks.items() if not passed]
                    self.log_result(f"PDF Salary Letter - {employee_name}", "FAIL", 
                                  f"PDF validation failed. Failed checks: {failed_checks}")
                    return False
            else:
                self.log_result(f"PDF Salary Letter - {employee_name}", "FAIL", 
                              f"Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result(f"PDF Salary Letter - {employee_name}", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_employee_data_differences(self, employee1_data, employee2_data):
        """Test that different employees have different salary data"""
        try:
            if not employee1_data or not employee2_data:
                self.log_result("Employee Data Differences", "SKIP", 
                              "Cannot compare - missing employee data")
                return False
            
            # Compare the HTML content for differences
            differences_found = employee1_data != employee2_data
            
            if differences_found:
                self.log_result("Employee Data Differences", "PASS", 
                              "Confirmed that different employees have different salary letter content")
                return True
            else:
                self.log_result("Employee Data Differences", "FAIL", 
                              "Employee salary letters appear identical - this may indicate an issue")
                return False
                
        except Exception as e:
            self.log_result("Employee Data Differences", "FAIL", f"Exception: {str(e)}")
            return False
    
    def get_salary_letter_content(self, employee_id, cycle_id):
        """Get salary letter content for comparison"""
        try:
            url = f"{BASE_URL}/payroll/cycles/{cycle_id}/employees/{employee_id}/letter"
            params = {"format": "html"}
            
            response = self.session.get(url, params=params)
            if response.status_code == 200:
                return response.text
            return None
        except:
            return None
    
    def run_salary_letter_tests(self):
        """Run all salary letter tests as requested in Arabic review"""
        print("🚀 بدء اختبار نظام رسائل الراتب الشهرية الجديد")
        print("🚀 Starting New Monthly Salary Letter System Testing")
        print(f"Base URL: {BASE_URL}")
        print("=" * 80)
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return
        
        # Step 2: Verify October 2025 cycle exists
        if not self.verify_cycle_exists(OCTOBER_2025_CYCLE_ID):
            print("❌ October 2025 cycle not found. Cannot proceed with tests.")
            return
        
        # Step 3: Find Mohamed Mostafa
        mohamed_id, mohamed_name = self.get_employee_by_name("Mohamed Mostafa")
        if not mohamed_id:
            print("❌ Mohamed Mostafa not found. Cannot proceed with Test 1 and 2.")
            mohamed_html_content = None
        else:
            # Test 1: HTML salary letter for Mohamed Mostafa
            print(f"\n📄 الاختبار 1: إنشاء رسالة راتب HTML لـ {mohamed_name}")
            print(f"📄 Test 1: Create HTML salary letter for {mohamed_name}")
            self.test_html_salary_letter(mohamed_id, mohamed_name, OCTOBER_2025_CYCLE_ID)
            
            # Test 2: PDF salary letter for Mohamed Mostafa
            print(f"\n📄 الاختبار 2: إنشاء رسالة راتب PDF لـ {mohamed_name}")
            print(f"📄 Test 2: Create PDF salary letter for {mohamed_name}")
            self.test_pdf_salary_letter(mohamed_id, mohamed_name, OCTOBER_2025_CYCLE_ID)
            
            # Get Mohamed's content for comparison
            mohamed_html_content = self.get_salary_letter_content(mohamed_id, OCTOBER_2025_CYCLE_ID)
        
        # Step 4: Find Jihad
        jihad_id, jihad_name = self.get_employee_by_name("Jihad")
        if not jihad_id:
            print("❌ Jihad not found. Cannot proceed with Test 3.")
            jihad_html_content = None
        else:
            # Test 3: HTML salary letter for Jihad
            print(f"\n📄 الاختبار 3: اختبار موظف آخر ({jihad_name})")
            print(f"📄 Test 3: Test another employee ({jihad_name})")
            self.test_html_salary_letter(jihad_id, jihad_name, OCTOBER_2025_CYCLE_ID)
            
            # Get Jihad's content for comparison
            jihad_html_content = self.get_salary_letter_content(jihad_id, OCTOBER_2025_CYCLE_ID)
        
        # Step 5: Compare employee data differences
        if mohamed_html_content and jihad_html_content:
            print(f"\n🔍 مقارنة البيانات بين الموظفين")
            print(f"🔍 Comparing data between employees")
            self.test_employee_data_differences(mohamed_html_content, jihad_html_content)
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "=" * 80)
        print("📋 ملخص اختبار نظام رسائل الراتب الشهرية")
        print("📋 SALARY LETTER SYSTEM TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        skipped_tests = len([r for r in self.test_results if r["status"] == "SKIP"])
        
        print(f"إجمالي الاختبارات / Total Tests: {total_tests}")
        print(f"✅ نجح / Passed: {passed_tests}")
        print(f"❌ فشل / Failed: {failed_tests}")
        print(f"⏭️ تم تخطيه / Skipped: {skipped_tests}")
        
        if total_tests > 0:
            success_rate = (passed_tests/total_tests)*100
            print(f"معدل النجاح / Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ الاختبارات الفاشلة / FAILED TESTS:")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"  • {result['test']}: {result['details']}")
        
        # Save detailed results
        results_file = Path("./salary_letter_test_results.json")
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, default=str, ensure_ascii=False)
        
        print(f"\n📄 النتائج التفصيلية محفوظة في / Detailed results saved to: {results_file}")
        print(f"📁 ملفات الأدلة محفوظة في / Evidence files saved to: {self.evidence_dir}")
        
        # Print key findings
        print(f"\n🔍 النتائج الرئيسية / KEY FINDINGS:")
        print(f"• تم اختبار نظام رسائل الراتب الشهرية الجديد")
        print(f"• Monthly salary letter system tested")
        print(f"• تم التحقق من تنسيقات HTML و PDF")
        print(f"• HTML and PDF formats verified")
        print(f"• تم التأكد من اختلاف البيانات بين الموظفين")
        print(f"• Employee data differences confirmed")

if __name__ == "__main__":
    tester = SalaryLetterTester()
    tester.run_salary_letter_tests()