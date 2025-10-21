#!/usr/bin/env python3
"""
اختبار شامل للإصلاحات الحرجة - Comprehensive Critical Fixes Testing
Testing the 4 critical fixes requested in Arabic review
"""

import requests
import json
import os
from datetime import datetime, timedelta
import sys

# Get backend URL from environment
BACKEND_URL = "https://timecalc-hr.preview.emergentagent.com/api"

class CriticalFixesTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.auth_token = None
        self.test_results = []
        
    def log_test(self, test_name, success, details, response_data=None):
        """Log test results"""
        result = {
            'test': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat(),
            'response_data': response_data
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
        print(f"   Details: {details}")
        if response_data:
            print(f"   Response: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
        print()

    def authenticate(self, email, password):
        """Authenticate user and get token"""
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json={
                "email": email,
                "password": password
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data['access_token']
                self.session.headers.update({
                    'Authorization': f'Bearer {self.auth_token}'
                })
                self.log_test(
                    "Authentication", 
                    True, 
                    f"Successfully authenticated as {email}",
                    {"user_role": data['user']['role'], "user_name": data['user']['name']}
                )
                return True
            else:
                self.log_test(
                    "Authentication", 
                    False, 
                    f"Failed to authenticate: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Authentication", False, f"Authentication error: {str(e)}")
            return False

    def test_monthly_deductions_calculator(self):
        """Test 1: Monthly Deductions Calculator"""
        try:
            # Test POST /api/deductions/calculate-monthly?month=2025-10
            response = self.session.post(f"{BACKEND_URL}/deductions/calculate-monthly?month=2025-10")
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify success and employee_count > 0
                if data.get('success') and data.get('employee_count', 0) > 0:
                    self.log_test(
                        "Monthly Deductions Calculator",
                        True,
                        f"Successfully calculated deductions for {data.get('employee_count')} employees",
                        data
                    )
                    return True
                else:
                    self.log_test(
                        "Monthly Deductions Calculator",
                        False,
                        f"Calculation succeeded but employee_count is {data.get('employee_count', 0)}",
                        data
                    )
                    return False
            else:
                self.log_test(
                    "Monthly Deductions Calculator",
                    False,
                    f"Failed with status {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Monthly Deductions Calculator", False, f"Error: {str(e)}")
            return False

    def get_october_2025_cycle_id(self):
        """Get cycle ID for October 2025"""
        try:
            response = self.session.get(f"{BACKEND_URL}/payroll/cycles")
            
            if response.status_code == 200:
                cycles = response.json()
                
                # Look for October 2025 cycle
                for cycle in cycles:
                    if '2025-10' in cycle.get('month', '') or 'October 2025' in cycle.get('month', ''):
                        return cycle.get('id')
                
                # If no October 2025 cycle found, use the first available cycle
                if cycles:
                    return cycles[0].get('id')
                    
            return None
            
        except Exception as e:
            print(f"Error getting cycle ID: {str(e)}")
            return None

    def test_payroll_cycle_recalculate(self):
        """Test 2: Payroll Cycle Recalculate"""
        try:
            # Get cycle ID for October 2025
            cycle_id = self.get_october_2025_cycle_id()
            
            if not cycle_id:
                self.log_test(
                    "Payroll Cycle Recalculate",
                    False,
                    "Could not find October 2025 payroll cycle"
                )
                return False
            
            # Test POST /api/payroll/cycles/{cycle_id}/recalculate
            response = self.session.post(f"{BACKEND_URL}/payroll/cycles/{cycle_id}/recalculate")
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify success in recalculation
                if (data.get('success') or 
                    'recalculated' in str(data).lower() or 
                    'تم إعادة حساب' in data.get('message', '') or
                    data.get('employees_updated', 0) > 0):
                    self.log_test(
                        "Payroll Cycle Recalculate",
                        True,
                        f"Successfully recalculated payroll cycle {cycle_id} - {data.get('employees_updated', 0)} employees updated",
                        data
                    )
                    return True
                else:
                    self.log_test(
                        "Payroll Cycle Recalculate",
                        False,
                        f"Recalculation response unclear: {data}",
                        data
                    )
                    return False
            else:
                self.log_test(
                    "Payroll Cycle Recalculate",
                    False,
                    f"Failed with status {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Payroll Cycle Recalculate", False, f"Error: {str(e)}")
            return False

    def get_employee_id_from_cycle(self, cycle_id):
        """Get any employee ID from the cycle"""
        try:
            # Try payroll summary endpoint first (most reliable)
            response = self.session.get(f"{BACKEND_URL}/payroll/cycles/{cycle_id}/summary")
            if response.status_code == 200:
                data = response.json()
                if 'employee_summaries' in data and data['employee_summaries']:
                    return data['employee_summaries'][0].get('employee_id')
            
            # Try employees list endpoint
            response = self.session.get(f"{BACKEND_URL}/employees/list")
            if response.status_code == 200:
                data = response.json()
                if 'employees' in data and data['employees']:
                    return data['employees'][0].get('id')
                elif isinstance(data, list) and data:
                    return data[0].get('id')
            
            # Try users endpoint as fallback
            response = self.session.get(f"{BACKEND_URL}/users")
            if response.status_code == 200:
                users = response.json()
                if isinstance(users, list) and users:
                    return users[0].get('id')
                    
            return None
            
        except Exception as e:
            print(f"Error getting employee ID: {str(e)}")
            return None

    def test_salary_letter_generation(self):
        """Test 3: Salary Letter Generation"""
        try:
            # Get cycle ID for October 2025
            cycle_id = self.get_october_2025_cycle_id()
            
            if not cycle_id:
                self.log_test(
                    "Salary Letter Generation",
                    False,
                    "Could not find October 2025 payroll cycle"
                )
                return False
            
            # Get any employee ID
            employee_id = self.get_employee_id_from_cycle(cycle_id)
            
            if not employee_id:
                self.log_test(
                    "Salary Letter Generation",
                    False,
                    "Could not find any employee ID"
                )
                return False
            
            # Test GET /api/payroll/cycles/{cycle_id}/employees/{employee_id}/letter?format=html
            response = self.session.get(
                f"{BACKEND_URL}/payroll/cycles/{cycle_id}/employees/{employee_id}/letter?format=html"
            )
            
            if response.status_code == 200:
                html_content = response.text
                
                # Verify HTML generation and presence of "البيانات الأساسية"
                if "البيانات الأساسية" in html_content:
                    self.log_test(
                        "Salary Letter Generation",
                        True,
                        f"Successfully generated HTML salary letter with Arabic content",
                        {"html_length": len(html_content), "contains_arabic": True}
                    )
                    return True
                else:
                    self.log_test(
                        "Salary Letter Generation",
                        False,
                        f"HTML generated but missing 'البيانات الأساسية' text",
                        {"html_length": len(html_content), "html_preview": html_content[:200]}
                    )
                    return False
            else:
                self.log_test(
                    "Salary Letter Generation",
                    False,
                    f"Failed with status {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Salary Letter Generation", False, f"Error: {str(e)}")
            return False

    def test_lock_unlock_cycle(self):
        """Test 4: Lock/Unlock Cycle"""
        try:
            # Get cycle ID for October 2025
            cycle_id = self.get_october_2025_cycle_id()
            
            if not cycle_id:
                self.log_test(
                    "Lock/Unlock Cycle",
                    False,
                    "Could not find October 2025 payroll cycle"
                )
                return False
            
            # Test 1: Lock the cycle
            lock_response = self.session.post(
                f"{BACKEND_URL}/payroll/cycles/{cycle_id}/lock",
                json={"lock_reason": "اختبار القفل - سبب طويل جداً"}
            )
            
            if lock_response.status_code != 200:
                self.log_test(
                    "Lock/Unlock Cycle - Lock",
                    False,
                    f"Failed to lock cycle: {lock_response.status_code} - {lock_response.text}"
                )
                return False
            
            lock_data = lock_response.json()
            self.log_test(
                "Lock/Unlock Cycle - Lock",
                True,
                f"Successfully locked cycle {cycle_id}",
                lock_data
            )
            
            # Test 2: Unlock the cycle
            unlock_response = self.session.post(
                f"{BACKEND_URL}/payroll/cycles/{cycle_id}/unlock",
                json={"reason": "اختبار الفتح - سبب طويل جداً للفتح"}
            )
            
            if unlock_response.status_code == 200:
                unlock_data = unlock_response.json()
                self.log_test(
                    "Lock/Unlock Cycle - Unlock",
                    True,
                    f"Successfully unlocked cycle {cycle_id}",
                    unlock_data
                )
                return True
            else:
                self.log_test(
                    "Lock/Unlock Cycle - Unlock",
                    False,
                    f"Failed to unlock cycle: {unlock_response.status_code} - {unlock_response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Lock/Unlock Cycle", False, f"Error: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all critical fixes tests"""
        print("🚨 COMPREHENSIVE CRITICAL FIXES TESTING - اختبار شامل للإصلاحات الحرجة")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Time: {datetime.now().isoformat()}")
        print("=" * 80)
        
        # Authenticate as admin
        if not self.authenticate("admin@tanseeq.com", "ADMIN"):
            print("❌ CRITICAL: Authentication failed. Cannot proceed with tests.")
            return False
        
        # Run all tests
        test_results = []
        
        print("\n🧮 TEST 1: Monthly Deductions Calculator")
        print("-" * 50)
        test_results.append(self.test_monthly_deductions_calculator())
        
        print("\n🔄 TEST 2: Payroll Cycle Recalculate")
        print("-" * 50)
        test_results.append(self.test_payroll_cycle_recalculate())
        
        print("\n📄 TEST 3: Salary Letter Generation")
        print("-" * 50)
        test_results.append(self.test_salary_letter_generation())
        
        print("\n🔒 TEST 4: Lock/Unlock Cycle")
        print("-" * 50)
        test_results.append(self.test_lock_unlock_cycle())
        
        # Summary
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print("\n" + "=" * 80)
        print("📊 CRITICAL FIXES TEST SUMMARY")
        print("=" * 80)
        print(f"✅ Passed: {passed_tests}/{total_tests} tests")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if success_rate == 100:
            print("🎉 ALL CRITICAL FIXES ARE WORKING CORRECTLY!")
        elif success_rate >= 75:
            print("⚠️  MOST CRITICAL FIXES WORKING - Some issues need attention")
        else:
            print("🚨 CRITICAL ISSUES DETECTED - Immediate attention required")
        
        print("\n📋 DETAILED TEST RESULTS:")
        for i, result in enumerate(self.test_results, 1):
            status = "✅" if result['success'] else "❌"
            print(f"{i}. {status} {result['test']}")
            print(f"   {result['details']}")
        
        return success_rate == 100

def main():
    """Main test execution"""
    tester = CriticalFixesTester()
    success = tester.run_all_tests()
    
    # Save detailed results
    with open('/app/critical_fixes_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(tester.test_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📁 Detailed results saved to: /app/critical_fixes_test_results.json")
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()