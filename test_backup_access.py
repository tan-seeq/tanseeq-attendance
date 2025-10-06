#!/usr/bin/env python3
"""
Try to find super_admin access or test backup with different approaches
"""

import requests
import json

def test_backup_with_admin(token, base_url):
    """Test if backup endpoints work with admin access"""
    api_url = f"{base_url}/api"
    
    # Test different backup endpoints
    endpoints_to_test = [
        'backup/stats',
        'backup/manual',
        'backup/create-download',
        'backup/list-files'
    ]
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    for endpoint in endpoints_to_test:
        try:
            if 'manual' in endpoint or 'create-download' in endpoint:
                response = requests.post(f"{api_url}/{endpoint}", headers=headers, timeout=30)
            else:
                response = requests.get(f"{api_url}/{endpoint}", headers=headers, timeout=30)
            
            print(f"📍 {endpoint}: Status {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"   ✅ Success: {list(result.keys())}")
                except:
                    print(f"   ✅ Success: {len(response.content)} bytes")
            elif response.status_code == 403:
                try:
                    error = response.json()
                    print(f"   ❌ Access denied: {error.get('detail', 'Unknown')}")
                except:
                    print(f"   ❌ Access denied")
            else:
                try:
                    error = response.json()
                    print(f"   ❌ Error: {error.get('detail', 'Unknown')}")
                except:
                    print(f"   ❌ Error: {response.text[:100]}")
                    
        except Exception as e:
            print(f"📍 {endpoint}: Exception - {str(e)}")

def get_users_list(token, base_url):
    """Get list of users to see if there are other super_admins"""
    api_url = f"{base_url}/api"
    url = f"{api_url}/users"
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            users = response.json()
            print(f"📊 Found {len(users)} users:")
            
            for user in users:
                print(f"   👤 {user.get('name', 'N/A')} ({user.get('email', 'N/A')}) - Role: {user.get('role', 'N/A')}")
                
            return users
        else:
            print(f"❌ Failed to get users: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error getting users: {str(e)}")
        return []

def login_and_test(email, password, base_url):
    """Login and test backup system"""
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
            
            # Get users list
            print("\n🔍 Getting users list...")
            get_users_list(token, base_url)
            
            # Test backup endpoints
            print("\n🔍 Testing backup endpoints...")
            test_backup_with_admin(token, base_url)
            
            return True
        else:
            print(f"❌ Login failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return False

if __name__ == "__main__":
    backend_url = "https://hr-management-11.preview.emergentagent.com"
    
    print("🔍 Testing backup system access...")
    print("=" * 50)
    
    login_and_test('mahmoud@tanseeq.com', 'mahmoud123', backend_url)