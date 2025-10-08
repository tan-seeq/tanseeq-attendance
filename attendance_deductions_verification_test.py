#!/usr/bin/env python3
"""
اختبار التحقق من تدفق خصومات الحضور والتكامل مع Payroll Ledger
Verification Test for Attendance Deductions Flow and Payroll Ledger Integration

This test verifies the existing attendance deductions system integration
"""

import requests
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import time

# Configuration
BASE_URL = "https://tanseeq-payroll.preview.emergentagent.com/api"

# Test accounts
TEST_ACCOUNTS = {
    "super_admin": {"email": "admin@tanseeq.com", "password": "ADMIN"},
}

class AttendanceDeductionsVerificationTester:
    def __init__(self):
        self.session = requests.Session()
        self.tokens = {}
        self.test_results = []
        self.evidence_dir = Path("./evidence/attendance_deductions_verification")
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        
        # Test data
        self.mohamed_id = "33d2d833-f414-4b0c-920d-35e3ca4f853c"
        self.cycle_id = "e70625f9-f78e-4be3-b02e-1c51cdf5385e"
        
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
                        mohamed_found = True
                        print(f"✅ تم العثور على Mohamed Mostafa")
                        print(f"📋 بيانات الخصومات:")
                        print(f"   - Late Deduction: {employee.get('late_deduction', 0)}")
                        print(f"   - Absence Deduction: {employee.get('absence_deduction', 0)}")
                        print(f"   - Advance Deduction: {employee.get('advance_deduction', 0)}")
                        break
                
                if mohamed_found:
                    self.log_result("Step 1 - Calculate Monthly Deductions", "PASS", 
                                  "Successfully calculated monthly deductions")
                    return True
                else:
                    self.log_result("Step 1 - Calculate Monthly Deductions", "FAIL", 
                                  "Mohamed Mostafa not found in response")
                    return False
                    
            else:
                self.log_result("Step 1 - Calculate Monthly Deductions", "FAIL", 
                              f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Step 1 - Calculate Monthly Deductions", "FAIL", f"Exception: {str(e)}")
            return False
    
    def step_2_verify_payroll_ledger(self):
        """الخطوة 2: التحقق من Payroll Ledger"""
        print("\n🔍 الخطوة 2: التحقق من Payroll Ledger")
        
        try:
            response = self.session.get(
                f"{BASE_URL}/payroll/ledger/employee/{self.mohamed_id}",
                timeout=30
            )
            
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # البحث عن قيود ATTENDANCE_DEDUCTION
                entries = data.get("entries", [])
                attendance_deductions = []
                total_attendance_deductions = 0
                
                for entry in entries:
                    if entry.get("entry_type") == "ATTENDANCE_DEDUCTION":
                        attendance_deductions.append(entry)
                        total_attendance_deductions += entry.get("amount", 0)
                
                print(f"✅ تم العثور على {len(attendance_deductions)} قيد خصومات حضور")
                print(f"💰 إجمالي خصومات الحضور: {total_attendance_deductions}")
                
                # طباعة أول 5 قيود
                print(f"📋 أول 5 قيود من Payroll Ledger:")
                for i, entry in enumerate(entries[:5]):
                    print(f"   {i+1}. Type: {entry.get('entry_type')}, Amount: {entry.get('amount')}")
                
                if len(attendance_deductions) > 0:
                    self.log_result("Step 2 - Verify Payroll Ledger", "PASS", 
                                  f"Found {len(attendance_deductions)} ATTENDANCE_DEDUCTION entries, total: {total_attendance_deductions}")
                    return True
                else:
                    self.log_result("Step 2 - Verify Payroll Ledger", "FAIL", 
                                  "No ATTENDANCE_DEDUCTION entries found")
                    return False
            else:
                self.log_result("Step 2 - Verify Payroll Ledger", "FAIL", 
                              f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Step 2 - Verify Payroll Ledger", "FAIL", f"Exception: {str(e)}")
            return False
    
    def step_3_verify_payroll_summary(self):
        """الخطوة 3: التحقق من ملخص الرواتب"""
        print("\n📊 الخطوة 3: التحقق من ملخص الرواتب")
        
        try:
            response = self.session.get(
                f"{BASE_URL}/payroll/cycles/{self.cycle_id}/summary",
                timeout=30
            )
            
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # البحث عن Mohamed Mostafa
                employee_summaries = data.get("employee_summaries", [])
                mohamed_summary = None
                
                for summary in employee_summaries:
                    if summary.get("employee_name") == "Mohamed Mostafa":
                        mohamed_summary = summary
                        break
                
                if mohamed_summary:
                    attendance_deductions = mohamed_summary.get("attendance_deductions", 0)
                    net_salary = mohamed_summary.get("net_salary", 0)
                    base_salary = mohamed_summary.get("base_salary", 0)
                    total_deductions = mohamed_summary.get("total_deductions", 0)
                    
                    print(f"✅ تم العثور على Mohamed Mostafa في ملخص الرواتب")
                    print(f"📋 تفاصيل Mohamed Mostafa:")
                    print(f"   - Employee Name: {mohamed_summary.get('employee_name')}")
                    print(f"   - Base Salary: {base_salary}")
                    print(f"   - Attendance Deductions: {attendance_deductions}")
                    print(f"   - Total Deductions: {total_deductions}")
                    print(f"   - Net Salary: {net_salary}")
                    
                    # التحقق من صحة الحسابات
                    expected_net = base_salary - total_deductions
                    calculation_correct = abs(net_salary - expected_net) < 0.01
                    
                    if attendance_deductions > 0 and calculation_correct:
                        self.log_result("Step 3 - Verify Payroll Summary", "PASS", 
                                      f"Attendance deductions = {attendance_deductions} and net salary calculated correctly")
                        return True
                    elif attendance_deductions > 0:
                        self.log_result("Step 3 - Verify Payroll Summary", "FAIL", 
                                      f"Attendance deductions found but net salary calculation incorrect")
                        return False
                    else:
                        self.log_result("Step 3 - Verify Payroll Summary", "FAIL", 
                                      "No attendance deductions found in summary")
                        return False
                else:
                    self.log_result("Step 3 - Verify Payroll Summary", "FAIL", 
                                  "Mohamed Mostafa not found in employee summaries")
                    return False
            else:
                self.log_result("Step 3 - Verify Payroll Summary", "FAIL", 
                              f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Step 3 - Verify Payroll Summary", "FAIL", f"Exception: {str(e)}")
            return False
    
    def run_verification_test(self):
        """تشغيل اختبار التحقق"""
        print("🚀 بدء اختبار التحقق من تدفق خصومات الحضور والتكامل مع Payroll Ledger")
        print("=" * 80)
        
        # المصادقة
        if not self.authenticate("super_admin"):
            print("❌ فشل في المصادقة - إيقاف الاختبار")
            return False
        
        # تشغيل الخطوات
        steps = [
            self.step_1_calculate_monthly_deductions,
            self.step_2_verify_payroll_ledger,
            self.step_3_verify_payroll_summary
        ]
        
        all_passed = True
        for step in steps:
            if not step():
                all_passed = False
                # Continue with other steps for complete verification
        
        # النتائج النهائية
        print("\n" + "=" * 80)
        print("📊 تقرير النتائج النهائي:")
        
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        total_tests = len(self.test_results)
        
        print(f"✅ اختبارات ناجحة: {passed_tests}")
        print(f"❌ اختبارات فاشلة: {total_tests - passed_tests}")
        print(f"📊 معدل النجاح: {(passed_tests/total_tests)*100:.1f}%")
        
        # الإجابة على الأسئلة المطلوبة في المراجعة العربية
        print("\n🔍 الإجابات على الأسئلة المطلوبة:")
        print("1. Status code لكل خطوة:")
        for result in self.test_results:
            if "Step" in result["test"]:
                print(f"   - {result['test']}: {'200 OK' if result['status'] == 'PASS' else 'FAILED'}")
        
        print("2. هل القيد تم إضافته إلى Payroll Ledger؟")
        ledger_result = next((r for r in self.test_results if "Payroll Ledger" in r["test"]), None)
        if ledger_result and ledger_result["status"] == "PASS":
            print("   ✅ نعم، تم العثور على قيود ATTENDANCE_DEDUCTION في Payroll Ledger")
        else:
            print("   ❌ لا، لم يتم العثور على القيود في Payroll Ledger")
        
        print("3. هل attendance_deductions في ملخص الرواتب يعكس الخصومات؟")
        summary_result = next((r for r in self.test_results if "Payroll Summary" in r["test"]), None)
        if summary_result and summary_result["status"] == "PASS":
            print("   ✅ نعم، attendance_deductions موجود في ملخص الرواتب")
        else:
            print("   ❌ لا، attendance_deductions غير صحيح في ملخص الرواتب")
        
        print("4. هل net_salary تم حسابه بشكل صحيح؟")
        if summary_result and summary_result["status"] == "PASS":
            print("   ✅ نعم، net_salary محسوب بشكل صحيح")
        else:
            print("   ❌ لا، هناك خطأ في حساب net_salary")
        
        print("5. أي أخطاء أو مشاكل:")
        failed_tests = [r for r in self.test_results if r["status"] == "FAIL"]
        if failed_tests:
            for test in failed_tests:
                print(f"   ❌ {test['test']}: {test['details']}")
        else:
            print("   ✅ لا توجد أخطاء - النظام يعمل بشكل صحيح")
        
        # حفظ النتائج
        results_file = self.evidence_dir / "verification_test_results.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 تم حفظ النتائج في: {results_file}")
        
        return all_passed

def main():
    """تشغيل الاختبار الرئيسي"""
    tester = AttendanceDeductionsVerificationTester()
    success = tester.run_verification_test()
    
    if success:
        print("\n🎉 جميع الاختبارات نجحت!")
        exit(0)
    else:
        print("\n⚠️ بعض الاختبارات فشلت - يرجى مراجعة التفاصيل أعلاه")
        exit(1)

if __name__ == "__main__":
    main()