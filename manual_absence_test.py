#!/usr/bin/env python3
"""
Test Manual Absence Creation with Correct Endpoint
"""

import requests
import json

# Configuration
BASE_URL = "https://hrapp-tanseeq-replaced-1761028017.emergent.host/api"
SUPER_ADMIN_EMAIL = "admin@tanseeq.com"
SUPER_ADMIN_PASSWORD = "ADMIN"

def test_manual_absence_creation():
    session = requests.Session()
    
    # Login first
    login_data = {"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD}
    login_response = session.post(f"{BASE_URL}/auth/login", json=login_data)
    
    if login_response.status_code != 200:
        print("❌ Login failed")
        return False
    
    token = login_response.json().get("access_token")
    session.headers.update({"Authorization": f"Bearer {token}"})
    
    print("🏥 Testing Manual Absence Creation...")
    
    # Get a test user first
    users_response = session.get(f"{BASE_URL}/users")
    if users_response.status_code != 200:
        print("❌ Could not get users list")
        return False
    
    users = users_response.json()
    test_user = None
    
    # Find a regular user (not admin/super_admin)
    for user in users:
        if user.get("role") == "user":
            test_user = user
            break
    
    if not test_user:
        print("⚠️ No regular user found for testing")
        # Use first user anyway
        test_user = users[0] if users else None
    
    if not test_user:
        print("❌ No users available for testing")
        return False
    
    print(f"✅ Using test user: {test_user.get('name')} (ID: {test_user.get('id')})")
    
    # Test the correct endpoint: POST /attendance/create-absence
    absence_data = {
        "user_id": test_user.get("id"),
        "date": "2025-01-15",
        "reason": "QA Testing - Manual Absence Creation"
    }
    
    create_response = session.post(f"{BASE_URL}/attendance/create-absence", json=absence_data)
    
    print(f"POST /attendance/create-absence: {create_response.status_code}")
    
    if create_response.status_code in [200, 201]:
        print("✅ Manual absence creation successful")
        
        response_data = create_response.json()
        absence_id = response_data.get("id")
        
        if absence_id:
            print(f"✅ Created absence with ID: {absence_id}")
            
            # Try to delete the test absence
            delete_response = session.delete(f"{BASE_URL}/attendance/delete-absence/{absence_id}")
            
            if delete_response.status_code == 200:
                print("✅ Test absence deleted successfully")
                return True
            else:
                print(f"⚠️ Could not delete test absence: {delete_response.status_code}")
                print(f"Response: {delete_response.text}")
                return True  # Still consider it a success since creation worked
        else:
            print("⚠️ No absence ID returned, but creation appeared successful")
            return True
    else:
        print(f"❌ Manual absence creation failed: {create_response.status_code}")
        print(f"Response: {create_response.text}")
        return False

if __name__ == "__main__":
    success = test_manual_absence_creation()
    print(f"\n🏁 Manual Absence Test: {'PASS' if success else 'FAIL'}")