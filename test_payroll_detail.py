#!/usr/bin/env python3
"""
Test payroll calculation in detail to understand the issue
"""

import requests
import json

def test_payroll_detailed(token, base_url):
    """Test payroll calculation in detail"""
    api_url = f"{base_url}/api"
    url = f"{api_url}/payroll/calculate/2024-12"
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print("✅ Payroll calculation successful")
            print(f"📊 Found {len(result)} employee records")
            
            for i, record in enumerate(result[:3]):  # Show first 3 records
                print(f"\n👤 Employee {i+1}:")
                print(f"   Name: {record.get('name', 'N/A')}")
                print(f"   Monthly Salary: {record.get('monthly_salary', 0)}")
                print(f"   Working Days: {record.get('working_days', 0)}")
                print(f"   Late Deductions: {record.get('late_deductions', 0)}")
                print(f"   Absence Deductions: {record.get('absence_deductions', 0)}")
                print(f"   Total Deductions: {record.get('total_deductions', 0)}")
                print(f"   Final Salary: {record.get('final_salary', 0)}")
                
                # Check calculation
                monthly_salary = record.get('monthly_salary', 0)
                total_deductions = record.get('total_deductions', 0)
                final_salary = record.get('final_salary', 0)
                expected_final = monthly_salary - total_deductions
                
                print(f"   Expected Final: {expected_final}")
                print(f"   Calculation OK: {abs(final_salary - expected_final) < 0.01}")
            
            return True
        else:
            print(f"❌ Payroll calculation failed: {response.status_code}")
            try:
                error = response.json()
                print(f"   Error: {error.get('detail', 'Unknown error')}")
            except:
                print(f"   Error: {response.text}")
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
            
            # Test payroll
            test_payroll_detailed(token, base_url)
            
            return True
        else:
            print(f"❌ Login failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return False

if __name__ == "__main__":
    backend_url = "https://attendance-calc-4.preview.emergentagent.com"
    
    print("🔍 Testing payroll calculation in detail...")
    print("=" * 50)
    
    login_and_test('mahmoud@tanseeq.com', 'mahmoud123', backend_url)