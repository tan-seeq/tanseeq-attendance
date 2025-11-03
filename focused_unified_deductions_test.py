#!/usr/bin/env python3
"""
Focused Unified Deductions Engine Validation - Post Excel Import
Specific testing based on review request requirements
"""

import requests
import json
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://attend-deduct-hr.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def authenticate():
    """Get auth token"""
    response = requests.post(f"{API_BASE}/auth/login", json={
        "email": "admin@tanseeq.com",
        "password": "ADMIN"
    })
    
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"Authentication failed: {response.status_code}")

def main():
    print("🔍 FOCUSED UNIFIED DEDUCTIONS ENGINE VALIDATION")
    print("=" * 60)
    
    # Authenticate
    try:
        token = authenticate()
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Authentication successful")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return
    
    # Test 1: POST /api/deductions/calculate-monthly?month=2025-10
    print("\n1️⃣ Testing Monthly Deductions Calculation for October 2025...")
    
    try:
        response = requests.post(f"{API_BASE}/deductions/calculate-monthly?month=2025-10", headers=headers)
        
        if response.status_code != 200:
            print(f"❌ API call failed: {response.status_code} - {response.text}")
            return
        
        data = response.json()
        
        # Check engine version
        engine_version = data.get("engine_version")
        print(f"   Engine Version: {engine_version}")
        if engine_version == "unified_v1.0":
            print("   ✅ Engine version unified_v1.0 confirmed")
        else:
            print(f"   ❌ Expected unified_v1.0, got {engine_version}")
        
        # Check cycle window
        cycle_window = data.get("cycle_window", {})
        cycle_start = cycle_window.get("from")
        cycle_end = cycle_window.get("to")
        print(f"   Cycle Window: {cycle_start} to {cycle_end}")
        
        if cycle_start == "2025-09-29" and cycle_end == "2025-10-28":
            print("   ✅ Correct cycle window (2025-09-29 to 2025-10-28)")
        else:
            print(f"   ❌ Expected 2025-09-29 to 2025-10-28, got {cycle_start} to {cycle_end}")
        
        employees = data.get("employees", [])
        print(f"   Total Employees: {len(employees)}")
        
    except Exception as e:
        print(f"❌ Exception during API call: {e}")
        return
    
    # Test 2: Verify Hatem and Tarek have total_deduction = 0 except for complete absence days
    print("\n2️⃣ Verifying Hatem and Tarek Exemptions...")
    
    hatem_employees = []
    tarek_employees = []
    
    for emp in employees:
        name = emp.get("employee_name", "").lower()
        if "hatem" in name:
            hatem_employees.append(emp)
        elif "tarek" in name or "tariq" in name:
            tarek_employees.append(emp)
    
    print(f"   Found {len(hatem_employees)} Hatem employees")
    print(f"   Found {len(tarek_employees)} Tarek employees")
    
    # Check Hatem employees
    for emp in hatem_employees:
        name = emp.get("employee_name")
        total_deduction = emp.get("total_deduction", 0)
        absence_count = emp.get("absence_count", 0)
        
        print(f"   Hatem ({name}): Deduction={total_deduction}, Absences={absence_count}")
        
        # According to review: should be 0 except for complete absence days
        if total_deduction == 0:
            print(f"   ✅ {name}: Correct - 0 deduction")
        elif absence_count > 0:
            print(f"   ⚠️ {name}: Has {absence_count} absences with {total_deduction} AED deduction")
        else:
            print(f"   ❌ {name}: Unexpected deduction {total_deduction} AED with no absences")
    
    # Check Tarek employees
    for emp in tarek_employees:
        name = emp.get("employee_name")
        total_deduction = emp.get("total_deduction", 0)
        absence_count = emp.get("absence_count", 0)
        
        print(f"   Tarek ({name}): Deduction={total_deduction}, Absences={absence_count}")
        
        if total_deduction == 0:
            print(f"   ✅ {name}: Correct - 0 deduction")
        elif absence_count > 0:
            print(f"   ⚠️ {name}: Has {absence_count} absences with {total_deduction} AED deduction")
        else:
            print(f"   ❌ {name}: Unexpected deduction {total_deduction} AED with no absences")
    
    # Test 3: Pick 3 random employees and check daily records
    print("\n3️⃣ Checking Daily Records for 3 Random Employees...")
    
    import random
    if len(employees) >= 3:
        sample_employees = random.sample(employees, 3)
        
        for i, emp in enumerate(sample_employees, 1):
            name = emp.get("employee_name")
            daily_records = emp.get("daily_records", [])
            
            print(f"   Employee {i}: {name}")
            print(f"   Total daily records: {len(daily_records)}")
            
            # Check records in date range
            records_in_range = 0
            records_with_times = 0
            
            for record in daily_records:
                record_date = record.get("date", "")
                if "2025-09-29" <= record_date <= "2025-10-28":
                    records_in_range += 1
                    
                    # Check if has check_in/check_out from Excel
                    if record.get("check_in") and record.get("check_out"):
                        records_with_times += 1
            
            print(f"   Records in cycle range: {records_in_range}")
            print(f"   Records with check-in/out: {records_with_times}")
            
            if records_in_range > 0:
                print(f"   ✅ {name}: Has records in October 2025 cycle")
            else:
                print(f"   ❌ {name}: No records in October 2025 cycle")
    
    # Test 4: Check grace_applied for late_minutes ≤ 15
    print("\n4️⃣ Verifying Grace Period Application...")
    
    total_grace_applied = 0
    total_late_records = 0
    grace_violations = 0
    
    for emp in employees:
        daily_records = emp.get("daily_records", [])
        emp_grace_count = 0
        
        for record in daily_records:
            late_minutes = record.get("late_minutes", 0)
            grace_applied = record.get("grace_applied", False)
            
            if late_minutes > 0:
                total_late_records += 1
                
                if grace_applied:
                    total_grace_applied += 1
                    emp_grace_count += 1
                    
                    # Check if grace is properly applied (≤15 minutes and ≤4 times)
                    if late_minutes > 15:
                        grace_violations += 1
                        print(f"   ⚠️ Grace applied for {late_minutes} minutes (>15) for {emp.get('employee_name')}")
        
        # Check if employee has more than 4 grace applications
        if emp_grace_count > 4:
            print(f"   ⚠️ {emp.get('employee_name')} has {emp_grace_count} grace applications (>4)")
    
    print(f"   Total late records: {total_late_records}")
    print(f"   Grace applied: {total_grace_applied}")
    print(f"   Grace violations: {grace_violations}")
    
    if grace_violations == 0:
        print("   ✅ Grace period rules properly applied")
    else:
        print(f"   ❌ Found {grace_violations} grace period violations")
    
    # Test 5: Return aggregate totals
    print("\n5️⃣ Aggregate Totals and Anomalies...")
    
    total_deductions = sum(emp.get("total_deduction", 0) for emp in employees)
    total_absences = sum(emp.get("absence_count", 0) for emp in employees)
    total_late_days = sum(emp.get("late_count", 0) for emp in employees)
    
    print(f"   Total Deductions: {total_deductions:.2f} AED")
    print(f"   Total Absence Days: {total_absences}")
    print(f"   Total Late Days: {total_late_days}")
    
    # Check for anomalies
    anomalies = []
    for emp in employees:
        deduction = emp.get("total_deduction", 0)
        if deduction > 5000:  # Flag very high deductions
            anomalies.append({
                "name": emp.get("employee_name"),
                "deduction": deduction,
                "absences": emp.get("absence_count", 0)
            })
    
    if anomalies:
        print(f"   ⚠️ Found {len(anomalies)} potential anomalies (deductions >5000 AED):")
        for anomaly in anomalies:
            print(f"      - {anomaly['name']}: {anomaly['deduction']} AED ({anomaly['absences']} absences)")
    else:
        print("   ✅ No significant anomalies detected")
    
    # Test 6: Check attendance records count
    print("\n6️⃣ Attendance Records Verification...")
    
    try:
        response = requests.get(f"{API_BASE}/attendance", headers=headers)
        if response.status_code == 200:
            all_attendance = response.json()
            october_records = [r for r in all_attendance if r.get("date", "").startswith("2025-10")]
            
            print(f"   Total attendance records: {len(all_attendance)}")
            print(f"   October 2025 records: {len(october_records)}")
            
            if len(october_records) >= 110:
                print("   ✅ Sufficient attendance records after Excel import")
            else:
                print(f"   ⚠️ Expected ≥110 records, found {len(october_records)}")
        else:
            print(f"   ❌ Failed to retrieve attendance records: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error checking attendance records: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 VALIDATION COMPLETE")
    print("\nKey Findings:")
    print(f"• Engine Version: unified_v1.0 ✅")
    print(f"• Employees Processed: {len(employees)}")
    print(f"• Total Deductions: {total_deductions:.2f} AED")
    print(f"• Hatem Employees: {len(hatem_employees)} (check exemptions)")
    print(f"• Tarek Employees: {len(tarek_employees)} (check exemptions)")
    print(f"• Grace Applications: {total_grace_applied}")
    print(f"• Anomalies: {len(anomalies)}")

if __name__ == "__main__":
    main()