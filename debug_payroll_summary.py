#!/usr/bin/env python3
"""
Debug script to check payroll cycle summary structure
"""

import requests
import json

# Configuration
BASE_URL = "https://hr-attendance-system.preview.emergentagent.com/api"
TEST_ACCOUNT = {"email": "admin@tanseeq.com", "password": "ADMIN"}

def debug_payroll_summary():
    session = requests.Session()
    
    # Authenticate
    response = session.post(f"{BASE_URL}/auth/login", json=TEST_ACCOUNT)
    if response.status_code != 200:
        print(f"❌ Authentication failed: {response.status_code}")
        return
    
    token = response.json()["access_token"]
    session.headers.update({"Authorization": f"Bearer {token}"})
    print("✅ Authentication successful")
    
    # Get payroll cycles
    response = session.get(f"{BASE_URL}/payroll/cycles")
    if response.status_code != 200:
        print(f"❌ Failed to get cycles: {response.status_code}")
        return
    
    cycles_data = response.json()
    if isinstance(cycles_data, list):
        cycles = cycles_data
    else:
        cycles = cycles_data.get('cycles', [])
    
    if not cycles:
        print("❌ No cycles found")
        return
    
    cycle_id = cycles[0].get('id')
    print(f"📋 Using cycle ID: {cycle_id}")
    
    # Get cycle summary
    response = session.get(f"{BASE_URL}/payroll/cycles/{cycle_id}/summary")
    print(f"📊 Summary response status: {response.status_code}")
    
    if response.status_code == 200:
        summary_data = response.json()
        print("📄 Summary data structure:")
        print(json.dumps(summary_data, indent=2, default=str))
    else:
        print(f"❌ Summary failed: {response.text}")

if __name__ == "__main__":
    debug_payroll_summary()