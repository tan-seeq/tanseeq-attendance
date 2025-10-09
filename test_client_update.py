#!/usr/bin/env python3
"""
Quick test for client update functionality
"""

import requests
import json
import time

BASE_URL = "https://tanseeq-payroll-1.preview.emergentagent.com/api"

def test_client_update():
    session = requests.Session()
    
    # Authenticate
    login_data = {"email": "admin@tanseeq.com", "password": "ADMIN"}
    response = session.post(f"{BASE_URL}/auth/login", json=login_data)
    
    if response.status_code != 200:
        print(f"❌ Authentication failed: {response.status_code}")
        return
    
    token = response.json()["access_token"]
    session.headers.update({"Authorization": f"Bearer {token}"})
    print("✅ Authenticated successfully")
    
    # Create a test client first
    client_data = {
        "company_name": "Test Update Client",
        "client_code": f"TUC-{int(time.time())}",
        "industry": "Testing",
        "notes": "Client for update testing"
    }
    
    response = session.post(f"{BASE_URL}/work-reports/clients", json=client_data)
    if response.status_code not in [200, 201]:
        print(f"❌ Client creation failed: {response.status_code} - {response.text}")
        return
    
    client_id = response.json()["id"]
    print(f"✅ Created test client: {client_id}")
    
    # Test update
    update_data = {
        "is_active": False,
        "notes": "Updated - deactivated for testing"
    }
    
    response = session.put(f"{BASE_URL}/work-reports/clients/{client_id}", json=update_data)
    if response.status_code == 200:
        print("✅ Client update successful")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"❌ Client update failed: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_client_update()