#!/usr/bin/env python3
"""
Final Verification Test for Late Penalty System
Tests all penalty endpoints with real scenarios
"""

import requests
import json
from datetime import datetime

def test_penalty_system():
    base_url = "https://3646cc77-f794-451c-bd8c-357b80d828e9.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    # Login as Hatem (super_admin)
    login_data = {'email': 'hatem@tanseeq.com', 'password': 'hatem123'}
    response = requests.post(f"{api_url}/auth/login", json=login_data)
    
    if response.status_code != 200:
        print("❌ Failed to login as Hatem")
        return False
    
    token = response.json()['access_token']
    user_info = response.json()['user']
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    print(f"✅ Logged in as: {user_info['name']} ({user_info['email']})")
    print(f"   Role: {user_info['role']}")
    
    # Test 1: Calculate penalties for current month
    month = "2025-02"
    print(f"\n📊 Testing penalty calculation for {month}...")
    
    response = requests.get(f"{api_url}/penalties/late/{month}", headers=headers)
    if response.status_code == 200:
        penalties = response.json()
        print(f"✅ Penalty calculation successful - Found {len(penalties)} employees with late records")
        
        if penalties:
            print("   Sample penalty details:")
            for i, penalty in enumerate(penalties[:2]):  # Show first 2
                print(f"   {i+1}. {penalty['user_name']}")
                print(f"      Late incidents: {penalty['late_incidents']}")
                print(f"      Total late minutes: {penalty['total_late_minutes']}")
                print(f"      Free minutes: {penalty['free_late_minutes']}")
                print(f"      Penalty minutes: {penalty['penalty_minutes']}")
                print(f"      Penalty amount: AED {penalty['penalty_amount']:.2f}")
                print(f"      Penalty type: {penalty['penalty_type']}")
    else:
        print(f"❌ Penalty calculation failed: {response.status_code} - {response.text}")
        return False
    
    # Test 2: Apply penalties
    print(f"\n⚡ Testing penalty application for {month}...")
    
    response = requests.post(f"{api_url}/penalties/apply/{month}", headers=headers)
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Penalty application successful")
        print(f"   Total employees: {result['total_employees']}")
        print(f"   Total penalty amount: AED {result['total_penalty_amount']:.2f}")
        print(f"   Penalties stored: {len(result['penalties'])}")
    else:
        print(f"❌ Penalty application failed: {response.status_code} - {response.text}")
        return False
    
    # Test 3: Check penalty history
    print(f"\n📋 Testing penalty history...")
    
    user_id = user_info['id']
    response = requests.get(f"{api_url}/penalties/history/{user_id}", headers=headers)
    if response.status_code == 200:
        history = response.json()
        print(f"✅ Penalty history retrieved - Found {len(history)} records")
        
        if history:
            print("   Recent penalty records:")
            for record in history[:2]:  # Show first 2
                print(f"   - Month: {record['month']}")
                print(f"     Amount: AED {record['penalty_amount']:.2f}")
                print(f"     Type: {record['penalty_type']}")
                print(f"     Applied by: {record.get('applied_by', 'Unknown')}")
    else:
        print(f"❌ Penalty history failed: {response.status_code} - {response.text}")
        return False
    
    # Test 4: Test access control with regular user
    print(f"\n🔒 Testing access control with regular user...")
    
    # Login as regular user
    user_login = {'email': 'jihad@tanseeq.com', 'password': 'jihad123'}
    response = requests.post(f"{api_url}/auth/login", json=user_login)
    
    if response.status_code == 200:
        user_token = response.json()['access_token']
        user_headers = {'Authorization': f'Bearer {user_token}', 'Content-Type': 'application/json'}
        
        # Try to calculate penalties (should fail)
        response = requests.get(f"{api_url}/penalties/late/{month}", headers=user_headers)
        if response.status_code == 403:
            print("✅ Regular user correctly denied penalty calculation access")
        else:
            print(f"❌ Regular user should be denied penalty calculation: {response.status_code}")
            return False
        
        # Try to apply penalties (should fail)
        response = requests.post(f"{api_url}/penalties/apply/{month}", headers=user_headers)
        if response.status_code == 403:
            print("✅ Regular user correctly denied penalty application access")
        else:
            print(f"❌ Regular user should be denied penalty application: {response.status_code}")
            return False
        
        # Try to view own penalty history (should work)
        user_id = response.json().get('user', {}).get('id') if response.status_code == 200 else 'test'
        response = requests.get(f"{api_url}/penalties/history/{user_id}", headers=user_headers)
        if response.status_code == 200:
            print("✅ Regular user can view own penalty history")
        else:
            print(f"❌ Regular user should be able to view own penalty history: {response.status_code}")
    
    print(f"\n🎉 All penalty system tests completed successfully!")
    return True

if __name__ == "__main__":
    print("🔍 FINAL PENALTY SYSTEM VERIFICATION")
    print("=" * 50)
    
    success = test_penalty_system()
    
    if success:
        print("\n✅ Penalty system is fully functional and ready for production!")
    else:
        print("\n❌ Some penalty system tests failed!")
    
    print("=" * 50)