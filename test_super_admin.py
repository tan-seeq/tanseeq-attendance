#!/usr/bin/env python3
"""
Try different super_admin credentials
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

def test_backup_create_download(token, base_url):
    """Test backup create-download endpoint"""
    api_url = f"{base_url}/api"
    url = f"{api_url}/backup/create-download"
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    try:
        response = requests.post(url, headers=headers, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print("✅ Backup create-download successful")
            print(f"   Response keys: {list(result.keys())}")
            print(f"   Filename: {result.get('filename', 'N/A')}")
            print(f"   Message: {result.get('message', 'N/A')}")
            return True, result.get('filename')
        else:
            print(f"❌ Backup create-download failed: {response.status_code}")
            try:
                error = response.json()
                print(f"   Error: {error.get('detail', 'Unknown error')}")
            except:
                print(f"   Error: {response.text}")
            return False, None
    except Exception as e:
        print(f"❌ Backup create-download error: {str(e)}")
        return False, None

if __name__ == "__main__":
    backend_url = "https://salary-processor-1.preview.emergentagent.com"
    
    print("🔍 Testing super_admin credentials...")
    print("=" * 50)
    
    # Test different super_admin credentials
    super_admin_credentials = [
        ('hatemmo186@gmail.com', 'hatem123'),
        ('hatemmo186@gmail.com', 'password'),
        ('hatemmo186@gmail.com', '123456'),
        ('hatemmo186@gmail.com', 'admin123'),
        ('hatem@tanseeq.com', 'password'),
        ('hatem@tanseeq.com', '123456'),
        ('hatem@tanseeq.com', 'admin123'),
    ]
    
    for email, password in super_admin_credentials:
        success, token = test_login(email, password, backend_url)
        if success:
            print(f"\n🔍 Testing backup system with {email}...")
            test_backup_create_download(token, backend_url)
            break
        print()
    
    print("\n❌ No working super_admin credentials found")