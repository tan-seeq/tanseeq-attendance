#!/usr/bin/env python3
"""
Test payroll calculation for current month (2025-01) to see if there's data
"""

import requests
import json
from datetime import datetime

def test_payroll_current_month(token, base_url):
    """Test payroll calculation for current month"""
    current_month = datetime.now().strftime("%Y-%m")
    api_url = f"{base_url}/api"
    url = f"{api_url}/payroll/calculate/{current_month}"
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Payroll calculation successful for {current_month}")
            print(f"📊 Found {len(result)} employee records")
            
            for i, record in enumerate(result[:2]):  # Show first 2 records
                print(f"\n👤 Employee {i+1}:")
                print(f"   Name: {record.get('name', 'N/A')}")
                print(f"   Monthly Salary: {record.get('monthly_salary', 0)}")
                print(f"   Working Days: {record.get('working_days', 0)}")
                print(f"   Late Deductions: {record.get('late_deductions', 0)}")
                print(f"   Absence Deductions: {record.get('absence_deductions', 0)}")
                print(f"   Total Deductions: {record.get('total_deductions', 0)}")
                print(f"   Final Salary: {record.get('final_salary', 0)}")
                
                # Check if calculation makes sense
                late_deductions = record.get('late_deductions', 0)
                absence_deductions = record.get('absence_deductions', 0)
                total_deductions = record.get('total_deductions', 0)
                expected_total = late_deductions + absence_deductions
                
                print(f"   Expected Total Deductions: {expected_total}")
                print(f"   Deduction Calc OK: {abs(total_deductions - expected_total) < 0.01}")
            
            return True
        else:
            print(f"❌ Payroll calculation failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Payroll calculation error: {str(e)}")
        return False

def login_and_test(email, password, base_url):
    """Login and test payroll"""
    api_url = f"{base_url}/api"
    url = f"{api_url}/auth/login"
    
    data = {'email': email, 'password': password}
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        if response.status_code == 200:
            result = response.json()
            token = result.get('access_token')
            user = result.get('user', {})
            print(f"✅ Login successful: {user.get('name', 'N/A')} ({user.get('role', 'N/A')})")
            
            # Test payroll for current month
            test_payroll_current_month(token, base_url)
            
            return True
        else:
            print(f"❌ Login failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return False

if __name__ == "__main__":
    backend_url = "https://73054ad2-88a8-4e83-bbd6-799c0f57cc6a.preview.emergentagent.com"
    
    print("🔍 Testing payroll calculation for current month...")
    print("=" * 50)
    
    login_and_test('mahmoud@tanseeq.com', 'mahmoud123', backend_url)