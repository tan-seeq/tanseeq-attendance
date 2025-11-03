#!/usr/bin/env python3
"""
🎯 FINAL UNIFIED DEDUCTIONS ENGINE VALIDATION - CORRECTED
Final validation with precise employee name matching
"""

import requests
import json
from datetime import datetime

# Configuration
BACKEND_URL = "https://attend-deduct-hr.preview.emergentagent.com/api"
SUPER_ADMIN_EMAIL = "admin@tanseeq.com"
SUPER_ADMIN_PASSWORD = "ADMIN"

def authenticate():
    """Authenticate and get token"""
    session = requests.Session()
    response = session.post(
        f"{BACKEND_URL}/auth/login",
        json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD},
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        session.headers.update({"Authorization": f"Bearer {token}"})
        print(f"✅ Authenticated as {data.get('user', {}).get('name', 'Unknown')}")
        return session
    else:
        print(f"❌ Authentication failed: {response.status_code}")
        return None

def validate_unified_deductions():
    """Final validation of unified deductions engine"""
    session = authenticate()
    if not session:
        return
    
    print("\n🚨 FINAL UNIFIED DEDUCTIONS ENGINE VALIDATION")
    print("=" * 60)
    
    # Get monthly calculation for October 2025
    response = session.post(
        f"{BACKEND_URL}/deductions/calculate-monthly",
        params={"month": "2025-10"},
        timeout=60
    )
    
    if response.status_code != 200:
        print(f"❌ Monthly calculation failed: {response.status_code}")
        return
    
    data = response.json()
    employees = data.get("employees", [])
    
    print(f"✅ Engine Version: {data.get('engine_version')}")
    print(f"✅ Found {len(employees)} employees")
    
    # Validate specific requirements
    validation_results = {
        "engine_version_correct": data.get("engine_version") == "unified_v1.0",
        "employees_array_present": len(employees) > 0,
        "tarek_wazzan_exempt": False,
        "hatem_mohamed_ahmed_exempt": False,
        "grace_policy_working": False,
        "daily_fields_complete": False,
        "custom_calculation_consistent": False
    }
    
    # Check exempt employees with precise matching
    for emp in employees:
        name = emp.get("employee_name", "").strip()
        total_deduction = emp.get("total_deduction", 0)
        
        # Precise matching for Tarek Wazzan
        if name.lower() in ["tarek wazzan", "طارق وزان"]:
            validation_results["tarek_wazzan_exempt"] = (total_deduction == 0)
            print(f"✅ Tarek Wazzan: {total_deduction} AED (exempt: {total_deduction == 0})")
        
        # Precise matching for Hatem Mohamed Ahmed
        if name.lower() in ["hatem mohamed ahmed", "حاتم محمد أحمد", "hatem mohamed", "حاتم محمد"]:
            validation_results["hatem_mohamed_ahmed_exempt"] = (total_deduction == 0)
            print(f"✅ Hatem Mohamed Ahmed: {total_deduction} AED (exempt: {total_deduction == 0})")
    
    # Check grace policy
    grace_examples = 0
    for emp in employees:
        daily_records = emp.get("daily_records", [])
        for record in daily_records:
            if (record.get("late_minutes", 0) <= 15 and 
                record.get("grace_applied", False) and 
                record.get("deduction_amount", 0) == 0):
                grace_examples += 1
                break
    
    validation_results["grace_policy_working"] = grace_examples > 0
    print(f"✅ Grace Policy: {grace_examples} employees with grace applications")
    
    # Check daily fields
    total_records = sum(len(emp.get("daily_records", [])) for emp in employees)
    required_fields = ["deductible_minutes", "late_minutes", "early_leave_minutes", "rule_applied"]
    complete_records = 0
    
    for emp in employees:
        for record in emp.get("daily_records", []):
            if all(field in record for field in required_fields):
                complete_records += 1
    
    field_coverage = (complete_records / total_records * 100) if total_records > 0 else 0
    validation_results["daily_fields_complete"] = field_coverage >= 95
    print(f"✅ Daily Fields: {complete_records}/{total_records} records ({field_coverage:.1f}%) complete")
    
    # Test custom calculation consistency
    monthly_total = sum(emp.get("total_deduction", 0) for emp in employees)
    
    custom_response = session.post(
        f"{BACKEND_URL}/deductions/calculate-custom",
        params={"mode": "custom", "from_date": "2025-09-29", "to_date": "2025-10-28"},
        timeout=60
    )
    
    if custom_response.status_code == 200:
        custom_data = custom_response.json()
        custom_total = sum(emp.get("total_deduction", 0) for emp in custom_data.get("employees", []))
        validation_results["custom_calculation_consistent"] = abs(monthly_total - custom_total) < 0.01
        print(f"✅ Custom Calculation: Monthly={monthly_total:.2f}, Custom={custom_total:.2f} (consistent: {abs(monthly_total - custom_total) < 0.01})")
    else:
        print(f"❌ Custom calculation failed: {custom_response.status_code}")
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 VALIDATION SUMMARY")
    print("=" * 60)
    
    passed_validations = sum(validation_results.values())
    total_validations = len(validation_results)
    success_rate = (passed_validations / total_validations * 100)
    
    for key, value in validation_results.items():
        status = "✅ PASS" if value else "❌ FAIL"
        print(f"{status} {key.replace('_', ' ').title()}")
    
    print(f"\n📊 SUCCESS RATE: {passed_validations}/{total_validations} ({success_rate:.1f}%)")
    
    if success_rate >= 85:
        print("🎉 VALIDATION RESULT: EXCELLENT - System ready for production")
    elif success_rate >= 70:
        print("⚠️ VALIDATION RESULT: GOOD - Minor issues to address")
    else:
        print("❌ VALIDATION RESULT: CRITICAL ISSUES - Immediate attention required")
    
    # Save results
    results = {
        "validation_results": validation_results,
        "success_rate": success_rate,
        "total_employees": len(employees),
        "monthly_total_deductions": monthly_total,
        "timestamp": datetime.now().isoformat()
    }
    
    with open("/app/final_unified_deductions_validation.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📁 Results saved to: /app/final_unified_deductions_validation.json")
    
    return validation_results, success_rate

if __name__ == "__main__":
    validate_unified_deductions()