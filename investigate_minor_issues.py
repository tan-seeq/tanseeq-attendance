#!/usr/bin/env python3
"""
Detailed Investigation of Minor Issues Found in Production Audit
"""

import requests
import json

# Configuration
BASE_URL = "https://hrapp-tanseeq-replaced-1761028017.emergent.host/api"
SUPER_ADMIN_EMAIL = "admin@tanseeq.com"
SUPER_ADMIN_PASSWORD = "ADMIN"

def investigate_issues():
    session = requests.Session()
    
    # Login first
    login_data = {"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD}
    login_response = session.post(f"{BASE_URL}/auth/login", json=login_data)
    
    if login_response.status_code != 200:
        print("❌ Login failed")
        return
    
    token = login_response.json().get("access_token")
    session.headers.update({"Authorization": f"Bearer {token}"})
    
    print("🔍 Investigating Minor Issues Found in Audit...")
    
    # Issue 1: Payroll cycle summary missing fields
    print("\n1. 💰 Investigating Payroll Cycle Summary Structure...")
    
    cycles_response = session.get(f"{BASE_URL}/payroll/cycles")
    if cycles_response.status_code == 200:
        cycles = cycles_response.json()
        if cycles:
            first_cycle = cycles[0]
            cycle_id = first_cycle.get("id")
            
            summary_response = session.get(f"{BASE_URL}/payroll/cycles/{cycle_id}/summary")
            if summary_response.status_code == 200:
                summary_data = summary_response.json()
                print(f"✅ Payroll summary response structure:")
                print(f"   Keys: {list(summary_data.keys())}")
                
                # Check if the fields exist but with different names
                for key, value in summary_data.items():
                    if isinstance(value, (int, float)):
                        print(f"   {key}: {value}")
                
                # The issue might be that the fields exist but the test was looking for exact names
                if any(key for key in summary_data.keys() if 'salary' in key.lower() or 'total' in key.lower()):
                    print("✅ Summary fields exist but may have different names than expected")
                else:
                    print("⚠️ No salary/total fields found in summary")
    
    # Issue 2: Advanced deductions missing daily_records
    print("\n2. 📊 Investigating Advanced Deductions daily_records...")
    
    monthly_response = session.post(f"{BASE_URL}/deductions/calculate-monthly?month=2025-10")
    if monthly_response.status_code == 200:
        monthly_data = monthly_response.json()
        print(f"✅ Monthly deductions response structure:")
        print(f"   Keys: {list(monthly_data.keys())}")
        
        # Check if daily_records exists under a different structure
        for key, value in monthly_data.items():
            if isinstance(value, dict) and 'daily' in key.lower():
                print(f"   Found daily-related field: {key}")
            elif isinstance(value, list) and len(value) > 0:
                if isinstance(value[0], dict):
                    sample_keys = list(value[0].keys())
                    if any('daily' in k.lower() or 'record' in k.lower() for k in sample_keys):
                        print(f"   Found daily records in {key}: {sample_keys}")
        
        # Check if employees have daily breakdown
        if 'employees' in monthly_data:
            employees = monthly_data['employees']
            if employees and isinstance(employees[0], dict):
                emp_keys = list(employees[0].keys())
                print(f"   Employee record structure: {emp_keys}")
                
                # Look for daily breakdown in employee records
                for key in emp_keys:
                    if 'daily' in key.lower() or 'record' in key.lower() or 'breakdown' in key.lower():
                        print(f"   Found daily data in employee records: {key}")

if __name__ == "__main__":
    investigate_issues()