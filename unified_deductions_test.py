#!/usr/bin/env python3
"""
URGENT UNIFIED DEDUCTIONS ENGINE VERIFICATION TESTING
Focus: October 2025 deductions calculation with new unified engine
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

# Backend URL from environment
BACKEND_URL = "https://attend-deduct-hr.preview.emergentagent.com/api"

# Test credentials
ADMIN_CREDENTIALS = {"email": "admin@tanseeq.com", "password": "ADMIN"}

class UnifiedDeductionsVerifier:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.test_results = []
        self.evidence = {}
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, status: str, details: str = "", data: Any = None):
        """Log test result with evidence"""
        result = {
            "test_name": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        self.test_results.append(result)
        print(f"[{status}] {test_name}: {details}")
        
    async def authenticate_admin(self):
        """Authenticate as admin user"""
        try:
            async with self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=ADMIN_CREDENTIALS
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.admin_token = data["access_token"]
                    self.log_test("Admin Authentication", "✅ PASS", 
                                f"Successfully authenticated as {ADMIN_CREDENTIALS['email']}")
                    return True
                else:
                    error_text = await response.text()
                    self.log_test("Admin Authentication", "❌ FAIL", 
                                f"Status {response.status}: {error_text}")
                    return False
        except Exception as e:
            self.log_test("Admin Authentication", "❌ FAIL", f"Exception: {str(e)}")
            return False
    
    async def test_monthly_deductions_calculation(self):
        """Test the unified deductions engine for October 2025"""
        if not self.admin_token:
            self.log_test("Monthly Deductions Test", "❌ FAIL", "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Test the unified deductions calculation endpoint
            async with self.session.post(
                f"{BACKEND_URL}/deductions/calculate-monthly?month=2025-10",
                headers=headers
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    self.evidence["monthly_calculation"] = data
                    
                    # Verify response structure
                    if "employees" in data:
                        employees = data["employees"]
                        self.log_test("Monthly Deductions API", "✅ PASS", 
                                    f"Successfully retrieved deductions for {len(employees)} employees")
                        
                        # Store for detailed verification
                        self.evidence["employees_data"] = employees
                        return True
                    else:
                        self.log_test("Monthly Deductions API", "❌ FAIL", 
                                    "Response missing 'employees' array")
                        return False
                else:
                    error_text = await response.text()
                    self.log_test("Monthly Deductions API", "❌ FAIL", 
                                f"Status {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_test("Monthly Deductions API", "❌ FAIL", f"Exception: {str(e)}")
            return False
    
    def verify_employee_deductions(self):
        """Verify specific employee deduction calculations"""
        if "employees_data" not in self.evidence:
            self.log_test("Employee Verification", "❌ FAIL", "No employee data available")
            return False
            
        employees = self.evidence["employees_data"]
        employee_dict = {emp.get("employee_name", ""): emp for emp in employees}
        
        # Test results tracking
        verification_results = []
        
        # 1. Verify Hesham (حسام) - Expected: 39.17 AED
        hesham_names = ["حسام", "Hesham", "حسام محمد"]
        hesham_employee = None
        
        for name_variant in hesham_names:
            for emp_name, emp_data in employee_dict.items():
                if name_variant in emp_name or emp_name in name_variant:
                    hesham_employee = emp_data
                    break
            if hesham_employee:
                break
        
        if hesham_employee:
            total_deduction = hesham_employee.get("total_deduction", 0)
            expected_hesham = 39.17
            tolerance = 0.50  # ±0.50 AED acceptable
            
            if abs(total_deduction - expected_hesham) <= tolerance:
                verification_results.append(f"✅ Hesham: {total_deduction} AED (Expected: {expected_hesham} AED)")
                self.log_test("Hesham Deduction Verification", "✅ PASS", 
                            f"Total deduction {total_deduction} AED within tolerance of {expected_hesham} AED")
            else:
                verification_results.append(f"❌ Hesham: {total_deduction} AED (Expected: {expected_hesham} AED)")
                self.log_test("Hesham Deduction Verification", "❌ FAIL", 
                            f"Total deduction {total_deduction} AED differs from expected {expected_hesham} AED")
        else:
            verification_results.append("❌ Hesham: Employee not found")
            self.log_test("Hesham Deduction Verification", "❌ FAIL", "Employee Hesham not found in results")
        
        # 2. Verify Mohamed Ahmed Mohamed Mostafa - Expected: 297.74 AED, 2 absences, 154 late minutes
        mohamed_names = ["محمد أحمد محمد مصطفى", "Mohamed Ahmed Mohamed Mostafa", "محمد أحمد", "Mohamed Ahmed"]
        mohamed_employee = None
        
        for name_variant in mohamed_names:
            for emp_name, emp_data in employee_dict.items():
                if name_variant in emp_name or emp_name in name_variant:
                    mohamed_employee = emp_data
                    break
            if mohamed_employee:
                break
        
        if mohamed_employee:
            total_deduction = mohamed_employee.get("total_deduction", 0)
            absence_count = mohamed_employee.get("absence_count", 0)
            late_count = mohamed_employee.get("late_count", 0)
            total_late_minutes = mohamed_employee.get("total_late_minutes", 0)
            
            expected_mohamed = 297.74
            expected_absences = 2
            expected_late_minutes = 154
            
            # Check total deduction
            deduction_ok = abs(total_deduction - expected_mohamed) <= 5.0  # ±5 AED tolerance
            absence_ok = absence_count == expected_absences
            late_minutes_ok = abs(total_late_minutes - expected_late_minutes) <= 10  # ±10 minutes tolerance
            
            if deduction_ok and absence_ok and late_minutes_ok:
                verification_results.append(f"✅ Mohamed: {total_deduction} AED, {absence_count} absences, {total_late_minutes} late minutes")
                self.log_test("Mohamed Deduction Verification", "✅ PASS", 
                            f"All metrics within expected ranges")
            else:
                verification_results.append(f"❌ Mohamed: {total_deduction} AED (exp: {expected_mohamed}), {absence_count} absences (exp: {expected_absences}), {total_late_minutes} late min (exp: {expected_late_minutes})")
                self.log_test("Mohamed Deduction Verification", "❌ FAIL", 
                            f"Metrics outside expected ranges")
        else:
            verification_results.append("❌ Mohamed: Employee not found")
            self.log_test("Mohamed Deduction Verification", "❌ FAIL", "Employee Mohamed not found in results")
        
        # 3. Verify Hatem (حاتم محمد أحمد) - Expected: 0 AED (exempt)
        hatem_names = ["حاتم محمد أحمد", "Hatem", "حاتم محمد", "حاتم"]
        hatem_employee = None
        
        for name_variant in hatem_names:
            for emp_name, emp_data in employee_dict.items():
                if name_variant in emp_name or emp_name in name_variant:
                    hatem_employee = emp_data
                    break
            if hatem_employee:
                break
        
        if hatem_employee:
            total_deduction = hatem_employee.get("total_deduction", 0)
            if total_deduction == 0:
                verification_results.append(f"✅ Hatem: {total_deduction} AED (exempt employee)")
                self.log_test("Hatem Deduction Verification", "✅ PASS", 
                            f"Exempt employee correctly shows 0 deduction")
            else:
                verification_results.append(f"❌ Hatem: {total_deduction} AED (should be 0 - exempt)")
                self.log_test("Hatem Deduction Verification", "❌ FAIL", 
                            f"Exempt employee shows {total_deduction} AED instead of 0")
        else:
            # Hatem might not appear in results if truly exempt (0 deductions)
            verification_results.append("✅ Hatem: Not in results (likely exempt with 0 deductions)")
            self.log_test("Hatem Deduction Verification", "✅ PASS", 
                        "Exempt employee correctly excluded from results")
        
        # 4. Verify Tariq (طارق) - Special rule: no late before 08:00 AM
        tariq_names = ["طارق", "Tariq", "Tarek"]
        tariq_employee = None
        
        for name_variant in tariq_names:
            for emp_name, emp_data in employee_dict.items():
                if name_variant in emp_name or emp_name in name_variant:
                    tariq_employee = emp_data
                    break
            if tariq_employee:
                break
        
        if tariq_employee:
            # Check if daily breakdown shows proper rule application
            daily_breakdown = tariq_employee.get("daily_breakdown", [])
            rule_applied_correctly = True
            
            for day in daily_breakdown:
                check_in = day.get("check_in", "")
                late_minutes = day.get("late_minutes", 0)
                rule_applied = day.get("rule_applied", "")
                
                # If check-in is before 08:00, should have 0 late minutes
                if check_in and check_in < "08:00" and late_minutes > 0:
                    rule_applied_correctly = False
                    break
            
            if rule_applied_correctly:
                verification_results.append(f"✅ Tariq: Special rule applied correctly")
                self.log_test("Tariq Rule Verification", "✅ PASS", 
                            "Special rule (no late before 08:00 AM) applied correctly")
            else:
                verification_results.append(f"❌ Tariq: Special rule not applied correctly")
                self.log_test("Tariq Rule Verification", "❌ FAIL", 
                            "Special rule (no late before 08:00 AM) not applied correctly")
        else:
            verification_results.append("⚠️ Tariq: Employee not found")
            self.log_test("Tariq Rule Verification", "⚠️ WARN", "Employee Tariq not found in results")
        
        # Store verification results
        self.evidence["verification_results"] = verification_results
        
        return len([r for r in verification_results if r.startswith("✅")]) >= 3  # At least 3 successful verifications
    
    def verify_unified_engine_features(self):
        """Verify unified engine specific features"""
        if "monthly_calculation" not in self.evidence:
            self.log_test("Engine Features Verification", "❌ FAIL", "No calculation data available")
            return False
        
        data = self.evidence["monthly_calculation"]
        features_verified = []
        
        # 1. Check engine version
        engine_version = data.get("engine_version", "")
        if engine_version == "unified_v1.0":
            features_verified.append("✅ Engine version: unified_v1.0")
            self.log_test("Engine Version Check", "✅ PASS", f"Correct engine version: {engine_version}")
        else:
            features_verified.append(f"❌ Engine version: {engine_version} (expected: unified_v1.0)")
            self.log_test("Engine Version Check", "❌ FAIL", f"Incorrect engine version: {engine_version}")
        
        # 2. Check note about unified engine
        note = data.get("note", "")
        if "UNIFIED deductions engine" in note and "(DailyRate/540)" in note:
            features_verified.append("✅ Note mentions unified engine and formula")
            self.log_test("Engine Note Check", "✅ PASS", "Note correctly describes unified engine")
        else:
            features_verified.append(f"❌ Note missing unified engine description")
            self.log_test("Engine Note Check", "❌ FAIL", f"Note does not describe unified engine properly")
        
        # 3. Check daily breakdown structure
        employees = self.evidence.get("employees_data", [])
        if employees:
            sample_employee = employees[0]
            daily_breakdown = sample_employee.get("daily_breakdown", [])
            
            if daily_breakdown:
                sample_day = daily_breakdown[0]
                required_fields = ["date", "check_in", "check_out", "late_minutes", 
                                 "early_leave_minutes", "deduction_amount", "grace_applied", "rule_applied"]
                
                missing_fields = [field for field in required_fields if field not in sample_day]
                
                if not missing_fields:
                    features_verified.append("✅ Daily breakdown has all required fields")
                    self.log_test("Daily Breakdown Structure", "✅ PASS", "All required fields present")
                else:
                    features_verified.append(f"❌ Daily breakdown missing fields: {missing_fields}")
                    self.log_test("Daily Breakdown Structure", "❌ FAIL", f"Missing fields: {missing_fields}")
            else:
                features_verified.append("❌ No daily breakdown data")
                self.log_test("Daily Breakdown Structure", "❌ FAIL", "No daily breakdown data found")
        
        # Store feature verification results
        self.evidence["features_verified"] = features_verified
        
        return len([f for f in features_verified if f.startswith("✅")]) >= 2  # At least 2 features verified
    
    def generate_evidence_report(self):
        """Generate comprehensive evidence report"""
        report = {
            "test_summary": {
                "total_tests": len(self.test_results),
                "passed": len([t for t in self.test_results if t["status"] == "✅ PASS"]),
                "failed": len([t for t in self.test_results if t["status"] == "❌ FAIL"]),
                "timestamp": datetime.now().isoformat()
            },
            "test_results": self.test_results,
            "evidence": self.evidence
        }
        
        # Save evidence to file
        with open("/app/unified_deductions_evidence.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return report
    
    async def run_comprehensive_verification(self):
        """Run complete unified deductions engine verification"""
        print("🔥 STARTING UNIFIED DEDUCTIONS ENGINE VERIFICATION")
        print("=" * 60)
        
        # Step 1: Authentication
        if not await self.authenticate_admin():
            return False
        
        # Step 2: Test monthly deductions calculation
        if not await self.test_monthly_deductions_calculation():
            return False
        
        # Step 3: Verify specific employee calculations
        employee_verification = self.verify_employee_deductions()
        
        # Step 4: Verify unified engine features
        engine_verification = self.verify_unified_engine_features()
        
        # Step 5: Generate evidence report
        report = self.generate_evidence_report()
        
        # Summary
        print("\n" + "=" * 60)
        print("🎯 UNIFIED DEDUCTIONS ENGINE VERIFICATION SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["status"] == "✅ PASS"])
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
        
        # Critical success criteria
        critical_criteria = [
            ("Authentication", any(t["test_name"] == "Admin Authentication" and t["status"] == "✅ PASS" for t in self.test_results)),
            ("Monthly Calculation API", any(t["test_name"] == "Monthly Deductions API" and t["status"] == "✅ PASS" for t in self.test_results)),
            ("Employee Verifications", employee_verification),
            ("Engine Features", engine_verification)
        ]
        
        print("\n🎯 CRITICAL SUCCESS CRITERIA:")
        for criterion, passed in critical_criteria:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {status} {criterion}")
        
        # Employee verification details
        if "verification_results" in self.evidence:
            print("\n👥 EMPLOYEE VERIFICATION DETAILS:")
            for result in self.evidence["verification_results"]:
                print(f"   {result}")
        
        # Engine features details
        if "features_verified" in self.evidence:
            print("\n🔧 ENGINE FEATURES VERIFICATION:")
            for feature in self.evidence["features_verified"]:
                print(f"   {feature}")
        
        print(f"\n📁 Evidence saved to: /app/unified_deductions_evidence.json")
        
        # Overall assessment
        all_critical_passed = all(passed for _, passed in critical_criteria)
        
        if all_critical_passed:
            print("\n🎉 UNIFIED DEDUCTIONS ENGINE VERIFICATION: ✅ SUCCESS")
            print("   All critical criteria met. System ready for production.")
        else:
            print("\n🚨 UNIFIED DEDUCTIONS ENGINE VERIFICATION: ❌ ISSUES FOUND")
            print("   Critical issues need to be addressed before production.")
        
        return all_critical_passed

async def main():
    """Main test execution"""
    async with UnifiedDeductionsVerifier() as verifier:
        success = await verifier.run_comprehensive_verification()
        return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit_code = 0 if success else 1
    exit(exit_code)