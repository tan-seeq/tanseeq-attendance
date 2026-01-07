#!/usr/bin/env python3
"""
Investigation of Manual Absence Creation Endpoints
"""

import requests
import json

# Configuration
BASE_URL = "https://hrapp-tanseeq-replaced-1761028017.emergent.host/api"
SUPER_ADMIN_EMAIL = "admin@tanseeq.com"
SUPER_ADMIN_PASSWORD = "ADMIN"

def investigate_absence_endpoints():
    session = requests.Session()
    
    # Login first
    login_data = {"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD}
    login_response = session.post(f"{BASE_URL}/auth/login", json=login_data)
    
    if login_response.status_code != 200:
        print("❌ Login failed")
        return
    
    token = login_response.json().get("access_token")
    session.headers.update({"Authorization": f"Bearer {token}"})
    
    print("🔍 Investigating Manual Absence Creation Endpoints...")
    
    # Test various potential endpoints
    endpoints_to_test = [
        ("/attendance", "GET"),
        ("/attendance", "POST"),
        ("/attendance/admin/create-absence", "POST"),
        ("/attendance/mark-absence", "POST"),
        ("/attendance/admin/mark-absence", "POST"),
        ("/attendance/absence/create", "POST"),
        ("/admin/attendance/create-absence", "POST"),
        ("/attendance/create-absence", "POST"),
        ("/attendance/admin/absence", "POST"),
        ("/attendance/absence", "POST"),
    ]
    
    for endpoint, method in endpoints_to_test:
        try:
            if method == "GET":
                response = session.get(f"{BASE_URL}{endpoint}")
            elif method == "POST":
                # Try with minimal test data
                test_data = {
                    "user_id": "test-user",
                    "date": "2025-01-15",
                    "reason": "Test absence"
                }
                response = session.post(f"{BASE_URL}{endpoint}", json=test_data)
            
            print(f"{method} {endpoint}: {response.status_code}")
            
            if response.status_code not in [404, 405]:
                print(f"  Response: {response.text[:200]}...")
                
        except Exception as e:
            print(f"{method} {endpoint}: ERROR - {str(e)}")
    
    # Check if there are any attendance-related endpoints by looking at existing attendance records
    print("\n🔍 Checking existing attendance endpoints...")
    
    attendance_response = session.get(f"{BASE_URL}/attendance")
    if attendance_response.status_code == 200:
        print(f"✅ GET /attendance works - found attendance records")
        
        # Try to see if we can create attendance records
        create_attendance_data = {
            "user_id": "test-user-id",
            "user_name": "Test User",
            "date": "2025-01-15",
            "status": "absent",
            "reason": "Manual absence test"
        }
        
        create_response = session.post(f"{BASE_URL}/attendance", json=create_attendance_data)
        print(f"POST /attendance: {create_response.status_code}")
        if create_response.status_code not in [404, 405]:
            print(f"  Response: {create_response.text[:200]}...")

if __name__ == "__main__":
    investigate_absence_endpoints()