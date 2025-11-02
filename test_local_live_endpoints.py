#!/usr/bin/env python3
"""
Test Live Endpoints Locally
"""

import requests
import json

BASE_URL = "http://localhost:8001/api"

def authenticate():
    """Get authentication token"""
    login_url = f"{BASE_URL}/auth/login"
    login_data = {
        "email": "admin@tanseeq.com",
        "password": "ADMIN"
    }
    
    response = requests.post(login_url, json=login_data)
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token")
    else:
        print(f"Authentication failed: {response.status_code} - {response.text}")
        return None

def test_endpoints():
    """Test live endpoints locally"""
    token = authenticate()
    if not token:
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test 1: Check live/logs endpoint
    print("Testing GET /api/live/logs...")
    response = requests.get(f"{BASE_URL}/live/logs", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}...")
    
    # Test 2: Check live/metrics endpoint
    print("\nTesting GET /api/live/metrics...")
    response = requests.get(f"{BASE_URL}/live/metrics", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}...")
    
    # Test 3: Check live/progress/frontend endpoint
    print("\nTesting POST /api/live/progress/frontend...")
    payload = {"message": "Test frontend message"}
    response = requests.post(f"{BASE_URL}/live/progress/frontend", json=payload, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")

if __name__ == "__main__":
    test_endpoints()