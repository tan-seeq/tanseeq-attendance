#!/usr/bin/env python3
"""
Test different login credentials to find working ones
"""

import requests
import json

def test_login(email, password, base_url):
    """Test login with given credentials"""
    api_url = f"{base_url}/api"
    url = f"{api_url}/auth/login"
    
    data = {'email': email, 'password': password}
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        if response.status_code == 200:
            result = response.json()
            user = result.get('user', {})
            print(f"✅ Login successful: {email}")
            print(f"   Name: {user.get('name', 'N/A')}")
            print(f"   Role: {user.get('role', 'N/A')}")
            print(f"   Token: {result.get('access_token', 'N/A')[:20]}...")
            return True, result.get('access_token')
        else:
            print(f"❌ Login failed: {email} - {response.status_code}")
            try:
                error = response.json()
                print(f"   Error: {error.get('detail', 'Unknown error')}")
            except:
                print(f"   Error: {response.text}")
            return False, None
    except Exception as e:
        print(f"❌ Login error: {email} - {str(e)}")
        return False, None

if __name__ == "__main__":
    backend_url = "https://hrapp-tanseeq.preview.emergentagent.com"
    
    print("🔍 Testing different login credentials...")
    print("=" * 50)
    
    # Test different credentials
    credentials_to_test = [
        ('hatem@tanseeq.com', 'hatem123'),
        ('admin@tanseeq.com', 'admin123'),
        ('mahmoud@tanseeq.com', 'mahmoud123'),
        ('jihad@tanseeq.com', 'jihad123'),
        ('hatem@tanseeq.com', 'password'),
        ('hatem@tanseeq.com', '123456'),
        ('super@tanseeq.com', 'super123'),
    ]
    
    working_token = None
    
    for email, password in credentials_to_test:
        success, token = test_login(email, password, backend_url)
        if success:
            working_token = token
            break
        print()
    
    if working_token:
        print(f"\n✅ Found working credentials! Token: {working_token[:20]}...")
    else:
        print("\n❌ No working credentials found")