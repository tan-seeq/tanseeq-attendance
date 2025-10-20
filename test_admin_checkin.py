#!/usr/bin/env python3
"""
Test check-in with admin user to verify the fix
"""

import requests
import json
from datetime import datetime

# Get backend URL from frontend .env
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.split('=')[1].strip()
            break

API_BASE = f"{BACKEND_URL}/api"

def test_admin_checkin():
    """Test check-in with admin user"""
    print("🔍 Testing check-in with admin user...")
    
    # Authenticate as admin
    session = requests.Session()
    response = session.post(f"{API_BASE}/auth/login", json={
        "email": "mahmoud@tanseeq.com",
        "password": "mahmoud123"
    })
    
    if response.status_code != 200:
        print(f"❌ Admin authentication failed: {response.status_code}")
        return False
    
    data = response.json()
    auth_token = data["access_token"]
    session.headers.update({"Authorization": f"Bearer {auth_token}"})
    print(f"✅ Authenticated as admin")
    
    # Try to check out first
    checkout_response = session.post(f"{API_BASE}/attendance/check-out")
    print(f"   Checkout attempt: {checkout_response.status_code}")
    
    # Now try check-in
    response = session.post(f"{API_BASE}/attendance/check-in")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Check-in successful!")
        print(f"   Response: {json.dumps(data, indent=2)}")
        
        # Check for required fields
        has_late_minutes = "late_minutes" in data
        has_is_late = "is_late" in data
        has_schedule_type = "schedule_type" in data
        
        print(f"\n🎯 FIX VERIFICATION:")
        print(f"   Has late_minutes: {has_late_minutes} (value: {data.get('late_minutes', 'N/A')})")
        print(f"   Has is_late: {has_is_late} (value: {data.get('is_late', 'N/A')})")
        print(f"   Has schedule_type: {has_schedule_type} (value: {data.get('schedule_type', 'N/A')})")
        
        # Calculate expected late_minutes
        current_time = datetime.now()
        expected_late_minutes = 0
        if current_time.hour > 9 or (current_time.hour == 9 and current_time.minute > 15):
            check_in_minutes = current_time.hour * 60 + current_time.minute
            threshold_minutes = 9 * 60 + 15  # 9:15 AM
            expected_late_minutes = check_in_minutes - threshold_minutes
        
        actual_late_minutes = data.get("late_minutes", 0)
        print(f"   Expected late_minutes: {expected_late_minutes}")
        print(f"   Actual late_minutes: {actual_late_minutes}")
        
        # Check if values are reasonable (within 2 minutes tolerance)
        late_minutes_correct = abs(actual_late_minutes - expected_late_minutes) <= 2
        
        if has_late_minutes and has_is_late and late_minutes_correct:
            print(f"\n🟢 SUCCESS: 9:15 AM Late Tracking Fix IS WORKING!")
            return True
        else:
            print(f"\n🔴 FAILED: Fix not working correctly")
            return False
        
    elif response.status_code == 400:
        error_msg = response.json().get("detail", "")
        print(f"⚠️ Already checked in: {error_msg}")
        return None
    else:
        print(f"❌ Unexpected response: {response.status_code} - {response.text}")
        return False

if __name__ == "__main__":
    result = test_admin_checkin()
    if result:
        print("\n✅ FINAL VERDICT: The 9:15 AM Late Tracking Fix is WORKING CORRECTLY")
    elif result is None:
        print("\n⚠️ Cannot test - user already checked in today")
    else:
        print("\n❌ FINAL VERDICT: The fix needs more work")