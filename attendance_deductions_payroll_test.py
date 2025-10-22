#!/usr/bin/env python3
"""
اختبار تدفق خصومات الحضور والتكامل مع Payroll Ledger
Testing Attendance Deductions Flow and Payroll Ledger Integration

This test follows the exact Arabic review request:
1. Calculate monthly deductions for 2025-10
2. Extract Mohamed Mostafa's data
3. Apply monthly deductions
4. Verify in Payroll Ledger
5. Verify in Payroll Summary
"""

import requests
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import time

# Configuration
BASE_URL = "https://tanseeq-attendance.preview.emergentagent.com/api"

# Test accounts
TEST_ACCOUNTS = {
    "super_admin": {"email": "admin@tanseeq.com", "password": "ADMIN"},
    "user": {"email": "jihad@tanseeq.com", "password": "jihad123"},
    "hatem": {"email": "hatem@tan-seeq.co", "password": "hatem123"}
}

class AttendanceDeductionsPayrollTester:
    def __init__(self):
        self.session = requests.Session()
        self.tokens = {}
        self.test_results = []
        self.evidence_dir = Path("./evidence/attendance_deductions_payroll")
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        
        # Test data storage
        self.mohamed_id = None
        self.mohamed_data = None
        self.cycle_id = None
        
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
            response = self.session.post(
                f"{BASE_URL}/auth/login",
                json=account,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                self.tokens[account_type] = token
                self.session.headers.update({"Authorization": f"Bearer {token}"})
                self.log_result(f"Authentication - {account_type}", "PASS", 
                              f"Successfully authenticated {account['email']}")
                return True
            else:
                self.log_result(f"Authentication - {account_type}", "FAIL", 
                              f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result(f"Authentication - {account_type}", "FAIL", f"Exception: {str(e)}")
            return False
    
    def step_1_calculate_monthly_deductions(self):
        """الخطوة 1: حساب الخصومات الشهرية"""
        print("\n🔍 الخطوة 1: حساب الخصومات الشهرية لشهر 2025-10")
        
        try:
            response = self.session.post(
                f"{BASE_URL}/deductions/calculate-monthly?month=2025-10",
                timeout=30
            )
            
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # البحث عن Mohamed Mostafa
                employees = data.get("employees", [])
                mohamed_found = False
                
                for employee in employees:
                    if "Mohamed Mostafa" in employee.get("employee_name", ""):
                        self.mohamed_id = employee.get("employee_id")
                        self.mohamed_data = employee
                        mohamed_found = True
                        print(f"✅ تم العثور على Mohamed Mostafa - ID: {self.mohamed_id}")
                        print(f"📋 بيانات الخصومات:")
                        print(f"   - Late Deduction: {employee.get('late_deduction', 0)}")
                        print(f"   - Absence Deduction: {employee.get('absence_deduction', 0)}")
                        print(f"   - Advance Deduction: {employee.get('advance_deduction', 0)}")
                        break
                
                if mohamed_found:
                    self.log_result("Step 1 - Calculate Monthly Deductions", "PASS", 
                                  f"Found Mohamed Mostafa with deductions data")
                    return True
                else:
                    self.log_result("Step 1 - Calculate Monthly Deductions", "FAIL", 
                                  "Mohamed Mostafa not found in response")
                    print("❌ لم يتم العثور على Mohamed Mostafa في البيانات")
                    return False
                    
            else:
                self.log_result("Step 1 - Calculate Monthly Deductions", "FAIL", 
                              f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Step 1 - Calculate Monthly Deductions", "FAIL", f"Exception: {str(e)}")
            return False
    
    def step_2_get_calculated_data(self):
        """الخطوة 2: الحصول على بيانات الخصومات المحسوبة"""
        print("\n📋 الخطوة 2: استخراج بيانات Mohamed Mostafa")
        
        if not self.mohamed_data:
            self.log_result("Step 2 - Get Calculated Data", "FAIL", "No Mohamed data available")
            return False
        
        try:
            late_deduction = self.mohamed_data.get("late_deduction", 0)
            absence_deduction = self.mohamed_data.get("absence_deduction", 0)
            advance_deduction = self.mohamed_data.get("advance_deduction", 0)
            
            print(f"📊 بيانات Mohamed Mostafa المستخرجة:")
            print(f"   - Employee ID: {self.mohamed_id}")
            print(f"   - Late Deduction: {late_deduction}")
            print(f"   - Absence Deduction: {absence_deduction}")
            print(f"   - Advance Deduction: {advance_deduction}")
            
            self.log_result("Step 2 - Get Calculated Data", "PASS", 
                          f"Successfully extracted Mohamed's deduction data")
            return True
            
        except Exception as e:
            self.log_result("Step 2 - Get Calculated Data", "FAIL", f"Exception: {str(e)}")
            return False
    
    def step_3_apply_monthly_deductions(self):
        """الخطوة 3: تطبيق الخصومات"""
        print("\n⚡ الخطوة 3: تطبيق الخصومات الشهرية")
        
        if not self.mohamed_data:
            self.log_result("Step 3 - Apply Monthly Deductions", "FAIL", "No Mohamed data available")
            return False
        
        try:
            # تحضير البيانات للتطبيق
            apply_data = {
                "month": "2025-10",
                "employees": [
                    {
                        "employee_id": self.mohamed_id,
                        "employee_name": "Mohamed Mostafa",
                        "late_deduction": self.mohamed_data.get("late_deduction", 17.50),
                        "absence_deduction": self.mohamed_data.get("absence_deduction", 0),
                        "advance_deduction": self.mohamed_data.get("advance_deduction", 0),
                        "deduction_details": ["تأخير 4 مرات - 72 دقيقة قابلة للخصم"]
                    }
                ]
            }
            
            response = self.session.post(
                f"{BASE_URL}/deductions/apply-monthly",
                json=apply_data,
                timeout=30
            )
            
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ تم تطبيق الخصومات بنجاح")
                print(f"📋 Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
                
                self.log_result("Step 3 - Apply Monthly Deductions", "PASS", 
                              "Successfully applied monthly deductions")
                return True
            else:
                self.log_result("Step 3 - Apply Monthly Deductions", "FAIL", 
                              f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Step 3 - Apply Monthly Deductions", "FAIL", f"Exception: {str(e)}")
            return False
    
    def step_4_verify_payroll_ledger(self):
        """الخطوة 4: التحقق من Payroll Ledger"""
        print("\n🔍 الخطوة 4: التحقق من Payroll Ledger")
        
        if not self.mohamed_id:
            self.log_result("Step 4 - Verify Payroll Ledger", "FAIL", "No Mohamed ID available")
            return False
        
        try:
            # أولاً، نحتاج للحصول على cycle_id
            cycles_response = self.session.get(f"{BASE_URL}/payroll/cycles", timeout=30)
            
            if cycles_response.status_code == 200:
                cycles_data = cycles_response.json()
                
                # Handle different response formats
                if isinstance(cycles_data, list):
                    cycles = cycles_data
                else:
                    cycles = cycles_data.get("cycles", [])
                
                print(f"📋 Found {len(cycles)} payroll cycles")
                
                # البحث عن دورة أكتوبر 2025
                october_cycle = None
                for cycle in cycles:
                    cycle_month = cycle.get("month", "")
                    print(f"   - Cycle: {cycle_month}, ID: {cycle.get('id')}")
                    if "2025-10" in cycle_month:
                        october_cycle = cycle
                        self.cycle_id = cycle.get("id")
                        break
                
                if not october_cycle:
                    self.log_result("Step 4 - Verify Payroll Ledger", "FAIL", 
                                  "October 2025 payroll cycle not found")
                    return False
                
                print(f"✅ تم العثور على دورة الرواتب لأكتوبر 2025 - ID: {self.cycle_id}")
                
                # الآن نتحقق من Payroll Ledger
                ledger_response = self.session.get(
                    f"{BASE_URL}/payroll/cycles/{self.cycle_id}/ledger/employees/{self.mohamed_id}",
                    timeout=30
                )
                
                print(f"📊 Ledger Status Code: {ledger_response.status_code}")
                
                if ledger_response.status_code == 200:
                    ledger_data = ledger_response.json()
                    
                    # البحث عن قيد ATTENDANCE_DEDUCTION
                    ledger_entries = ledger_data.get("ledger_entries", [])
                    attendance_deduction_found = False
                    deduction_amount = 0
                    
                    for entry in ledger_entries:
                        if entry.get("entry_type") == "ATTENDANCE_DEDUCTION":
                            attendance_deduction_found = True
                            deduction_amount = entry.get("amount", 0)
                            print(f"✅ تم العثور على قيد ATTENDANCE_DEDUCTION")
                            print(f"💰 المبلغ: {deduction_amount}")
                            break
                    
                    # طباعة أول 5 أسطر من response
                    print(f"📋 أول 5 قيود من Payroll Ledger:")
                    for i, entry in enumerate(ledger_entries[:5]):
                        print(f"   {i+1}. Type: {entry.get('entry_type')}, Amount: {entry.get('amount')}")
                    
                    if attendance_deduction_found and deduction_amount == 17.50:
                        self.log_result("Step 4 - Verify Payroll Ledger", "PASS", 
                                      f"Found ATTENDANCE_DEDUCTION entry with correct amount: {deduction_amount}")
                        return True
                    elif attendance_deduction_found:
                        self.log_result("Step 4 - Verify Payroll Ledger", "FAIL", 
                                      f"Found ATTENDANCE_DEDUCTION but amount is {deduction_amount}, expected 17.50")
                        return False
                    else:
                        self.log_result("Step 4 - Verify Payroll Ledger", "FAIL", 
                                      "ATTENDANCE_DEDUCTION entry not found in ledger")
                        return False
                else:
                    self.log_result("Step 4 - Verify Payroll Ledger", "FAIL", 
                                  f"Ledger Status: {ledger_response.status_code}, Response: {ledger_response.text}")
                    return False
            else:
                self.log_result("Step 4 - Verify Payroll Ledger", "FAIL", 
                              f"Cycles Status: {cycles_response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Step 4 - Verify Payroll Ledger", "FAIL", f"Exception: {str(e)}")
            return False
    
    def step_5_verify_payroll_summary(self):
        """الخطوة 5: التحقق من ملخص الرواتب"""
        print("\n📊 الخطوة 5: التحقق من ملخص الرواتب")
        
        if not self.cycle_id:
            self.log_result("Step 5 - Verify Payroll Summary", "FAIL", "No cycle ID available")
            return False
        
        try:
            response = self.session.get(
                f"{BASE_URL}/payroll/cycles/{self.cycle_id}/summary",
                timeout=30
            )
            
            print(f"📊 Summary Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # البحث عن Mohamed Mostafa في employee_summaries
                employee_summaries = data.get("employee_summaries", [])
                mohamed_summary = None
                
                for summary in employee_summaries:
                    if summary.get("employee_name") == "Mohamed Mostafa" or self.mohamed_id in str(summary.get("employee_id", "")):
                        mohamed_summary = summary
                        break
                
                if mohamed_summary:
                    attendance_deductions = mohamed_summary.get("attendance_deductions", 0)
                    net_salary = mohamed_summary.get("net_salary", 0)
                    
                    print(f"✅ تم العثور على Mohamed Mostafa في ملخص الرواتب")
                    print(f"📋 تفاصيل Mohamed Mostafa:")
                    print(f"   - Employee Name: {mohamed_summary.get('employee_name')}")
                    print(f"   - Attendance Deductions: {attendance_deductions}")
                    print(f"   - Net Salary: {net_salary}")
                    print(f"   - Basic Salary: {mohamed_summary.get('basic_salary', 0)}")
                    print(f"   - Total Deductions: {mohamed_summary.get('total_deductions', 0)}")
                    
                    # التحقق من صحة attendance_deductions
                    if attendance_deductions == 17.50:
                        # التحقق من صحة حساب net_salary
                        basic_salary = mohamed_summary.get("basic_salary", 0)
                        total_deductions = mohamed_summary.get("total_deductions", 0)
                        expected_net = basic_salary - total_deductions
                        
                        if abs(net_salary - expected_net) < 0.01:  # تسامح في الحساب
                            self.log_result("Step 5 - Verify Payroll Summary", "PASS", 
                                          f"Attendance deductions = 17.50 and net salary calculated correctly")
                            return True
                        else:
                            self.log_result("Step 5 - Verify Payroll Summary", "FAIL", 
                                          f"Net salary calculation incorrect. Expected: {expected_net}, Got: {net_salary}")
                            return False
                    else:
                        self.log_result("Step 5 - Verify Payroll Summary", "FAIL", 
                                      f"Attendance deductions = {attendance_deductions}, expected 17.50")
                        return False
                else:
                    self.log_result("Step 5 - Verify Payroll Summary", "FAIL", 
                                  "Mohamed Mostafa not found in employee summaries")
                    return False
            else:
                self.log_result("Step 5 - Verify Payroll Summary", "FAIL", 
                              f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Step 5 - Verify Payroll Summary", "FAIL", f"Exception: {str(e)}")
            return False
    
    def run_complete_test(self):
        """تشغيل الاختبار الكامل"""
        print("🚀 بدء اختبار تدفق خصومات الحضور والتكامل مع Payroll Ledger")
        print("=" * 80)
        
        # المصادقة
        if not self.authenticate("super_admin"):
            print("❌ فشل في المصادقة - إيقاف الاختبار")
            return False
        
        # تشغيل الخطوات
        steps = [
            self.step_1_calculate_monthly_deductions,
            self.step_2_get_calculated_data,
            self.step_3_apply_monthly_deductions,
            self.step_4_verify_payroll_ledger,
            self.step_5_verify_payroll_summary
        ]
        
        all_passed = True
        for step in steps:
            if not step():
                all_passed = False
                break
        
        # النتائج النهائية
        print("\n" + "=" * 80)
        print("📊 تقرير النتائج النهائي:")
        
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        total_tests = len(self.test_results)
        
        print(f"✅ اختبارات ناجحة: {passed_tests}")
        print(f"❌ اختبارات فاشلة: {total_tests - passed_tests}")
        print(f"📊 معدل النجاح: {(passed_tests/total_tests)*100:.1f}%")
        
        # الإجابة على الأسئلة المطلوبة
        print("\n🔍 الإجابات على الأسئلة المطلوبة:")
        
        for i, result in enumerate(self.test_results, 1):
            print(f"{i}. {result['test']}: {'✅ نجح' if result['status'] == 'PASS' else '❌ فشل'}")
        
        # حفظ النتائج
        results_file = self.evidence_dir / "attendance_deductions_test_results.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 تم حفظ النتائج في: {results_file}")
        
        return all_passed

def main():
    """تشغيل الاختبار الرئيسي"""
    tester = AttendanceDeductionsPayrollTester()
    success = tester.run_complete_test()
    
    if success:
        print("\n🎉 جميع الاختبارات نجحت!")
        exit(0)
    else:
        print("\n⚠️ بعض الاختبارات فشلت - يرجى مراجعة التفاصيل أعلاه")
        exit(1)

if __name__ == "__main__":
    main()