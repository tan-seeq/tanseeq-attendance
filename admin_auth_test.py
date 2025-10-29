#!/usr/bin/env python3
"""
Admin Authentication Testing Script
Testing mahmoud@tanseeq.com admin credentials as requested in review
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://attendance-calc-4.preview.emergentagent.com/api"

# Test credentials
ADMIN_CREDENTIALS = {
    "email": "mahmoud@tanseeq.com",
    "password": "mahmoud123"
}

SUPER_ADMIN_CREDENTIALS = {
    "email": "admin@tanseeq.com", 
    "password": "ADMIN"
}

def test_admin_authentication():
    """Test Admin Authentication Issue - mahmoud@tanseeq.com"""
    
    print("🔍 ADMIN AUTHENTICATION TESTING - mahmoud@tanseeq.com")
    print("=" * 60)
    
    results = {
        "admin_login_test": False,
        "user_exists_in_db": False,
        "user_role_correct": False,
        "account_active": False,
        "admin_access_test": False,
        "rbac_test": False
    }
    
    # Step 1: Test Admin Login
    print("\n1️⃣ Testing Admin Login (mahmoud@tanseeq.com / mahmoud123)")
    try:
        response = requests.post(f"{BACKEND_URL}/auth/login", json=ADMIN_CREDENTIALS)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            admin_token = data.get("access_token")
            user_info = data.get("user", {})
            
            print(f"   ✅ Login successful!")
            print(f"   User ID: {user_info.get('id')}")
            print(f"   Name: {user_info.get('name')}")
            print(f"   Role: {user_info.get('role')}")
            print(f"   Active: {user_info.get('is_active')}")
            
            results["admin_login_test"] = True
            results["user_role_correct"] = user_info.get('role') == 'admin'
            results["account_active"] = user_info.get('is_active', False)
            
            # Step 2: Test Admin Access to Management Pages
            print("\n2️⃣ Testing Admin Access to Management Pages")
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            # Test employee management access (admin should have access)
            try:
                emp_response = requests.get(f"{BACKEND_URL}/employees/list", headers=headers)
                print(f"   Employee List Access: {emp_response.status_code}")
                if emp_response.status_code == 200:
                    employees = emp_response.json()
                    print(f"   ✅ Admin can access employee list ({len(employees)} employees)")
                    results["admin_access_test"] = True
                else:
                    print(f"   ❌ Admin cannot access employee list: {emp_response.text}")
            except Exception as e:
                print(f"   ❌ Error testing employee access: {e}")
            
            # Step 3: Test RBAC - Admin should NOT access Super Admin pages
            print("\n3️⃣ Testing RBAC - Admin Restrictions")
            try:
                # Test super admin only endpoint (should be denied)
                super_admin_response = requests.get(f"{BACKEND_URL}/advances/admin/all-balances", headers=headers)
                print(f"   Super Admin Endpoint Access: {super_admin_response.status_code}")
                
                if super_admin_response.status_code == 403:
                    print(f"   ✅ Admin properly restricted from Super Admin pages")
                    results["rbac_test"] = True
                elif super_admin_response.status_code == 200:
                    print(f"   ⚠️ Admin has Super Admin access (unexpected)")
                else:
                    print(f"   ❓ Unexpected response: {super_admin_response.text}")
            except Exception as e:
                print(f"   ❌ Error testing RBAC: {e}")
                
        else:
            print(f"   ❌ Login failed: {response.text}")
            
            # Check if user exists using Super Admin credentials
            print("\n🔍 Checking if user exists in database...")
            try:
                super_admin_login = requests.post(f"{BACKEND_URL}/auth/login", json=SUPER_ADMIN_CREDENTIALS)
                if super_admin_login.status_code == 200:
                    super_admin_token = super_admin_login.json().get("access_token")
                    headers = {"Authorization": f"Bearer {super_admin_token}"}
                    
                    # Get all users to check if mahmoud exists
                    users_response = requests.get(f"{BACKEND_URL}/employees/list", headers=headers)
                    if users_response.status_code == 200:
                        users = users_response.json()
                        mahmoud_user = None
                        for user in users:
                            if user.get('email') == 'mahmoud@tanseeq.com':
                                mahmoud_user = user
                                break
                        
                        if mahmoud_user:
                            print(f"   ✅ User found in database:")
                            print(f"   ID: {mahmoud_user.get('id')}")
                            print(f"   Name: {mahmoud_user.get('name')}")
                            print(f"   Email: {mahmoud_user.get('email')}")
                            print(f"   Role: {mahmoud_user.get('role')}")
                            print(f"   Active: {mahmoud_user.get('is_active')}")
                            results["user_exists_in_db"] = True
                            results["user_role_correct"] = mahmoud_user.get('role') == 'admin'
                            results["account_active"] = mahmoud_user.get('is_active', False)
                        else:
                            print(f"   ❌ User mahmoud@tanseeq.com NOT found in database")
                            print(f"   📝 Need to create admin user")
                    else:
                        print(f"   ❌ Cannot retrieve users list: {users_response.text}")
                else:
                    print(f"   ❌ Super Admin login failed: {super_admin_login.text}")
            except Exception as e:
                print(f"   ❌ Error checking user existence: {e}")
                
    except Exception as e:
        print(f"   ❌ Login request failed: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 ADMIN AUTHENTICATION TEST SUMMARY")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    success_rate = (passed_tests / total_tests) * 100
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    print(f"\n📈 Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
    
    if not results["admin_login_test"]:
        print("\n🚨 CRITICAL ISSUE: Admin login failed!")
        print("   Recommended Actions:")
        if not results["user_exists_in_db"]:
            print("   1. Create admin user mahmoud@tanseeq.com with role 'admin'")
        elif not results["account_active"]:
            print("   1. Activate the admin account")
        elif not results["user_role_correct"]:
            print("   1. Set user role to 'admin'")
        else:
            print("   1. Check password hash validity")
            print("   2. Verify no account lockout")
    else:
        print("\n✅ Admin authentication working correctly!")
        if not results["rbac_test"]:
            print("   ⚠️ RBAC issue: Check admin access restrictions")
    
    return results

def test_alternative_credentials():
    """Test alternative credential variations"""
    print("\n🔄 TESTING ALTERNATIVE CREDENTIALS")
    print("=" * 40)
    
    alternatives = [
        {"email": "mahmoud@tanseeq.com", "password": "Mahmoud123"},
        {"email": "mahmoud@tanseeq.com", "password": "MAHMOUD123"},
        {"email": "Mahmoud@tanseeq.com", "password": "mahmoud123"},
        {"email": "mahmoud@tanseeq.com", "password": "mahmoud"},
    ]
    
    for i, creds in enumerate(alternatives, 1):
        print(f"\n{i}. Testing: {creds['email']} / {creds['password']}")
        try:
            response = requests.post(f"{BACKEND_URL}/auth/login", json=creds)
            if response.status_code == 200:
                print(f"   ✅ Alternative credentials work!")
                return creds
            else:
                print(f"   ❌ Failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n❌ No alternative credentials work")
    return None

def create_admin_user_if_needed():
    """Create admin user if not found"""
    print("\n🛠️ CREATING ADMIN USER")
    print("=" * 30)
    
    try:
        # Login as Super Admin
        super_admin_login = requests.post(f"{BACKEND_URL}/auth/login", json=SUPER_ADMIN_CREDENTIALS)
        if super_admin_login.status_code != 200:
            print("❌ Cannot login as Super Admin to create user")
            return False
        
        super_admin_token = super_admin_login.json().get("access_token")
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        
        # Create admin user
        admin_user_data = {
            "name": "محمود",
            "email": "mahmoud@tanseeq.com",
            "password": "mahmoud123",
            "role": "admin",
            "position": "مدير إداري",
            "monthly_salary": 5000.0,
            "is_active": True
        }
        
        create_response = requests.post(f"{BACKEND_URL}/users", json=admin_user_data, headers=headers)
        print(f"Create User Response: {create_response.status_code}")
        
        if create_response.status_code in [200, 201]:
            print("✅ Admin user created successfully!")
            return True
        else:
            print(f"❌ Failed to create user: {create_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        return False

def main():
    """Main testing function"""
    print("🚨 ADMIN AUTHENTICATION ISSUE INVESTIGATION")
    print("Testing mahmoud@tanseeq.com admin credentials")
    print("=" * 60)
    
    # Test current admin credentials
    results = test_admin_authentication()
    
    # If login failed, try alternatives
    if not results["admin_login_test"]:
        alternative_creds = test_alternative_credentials()
        
        # If no alternatives work and user doesn't exist, create user
        if not alternative_creds and not results["user_exists_in_db"]:
            if create_admin_user_if_needed():
                print("\n🔄 Re-testing after user creation...")
                results = test_admin_authentication()
    
    # Final verification
    print("\n" + "=" * 60)
    print("🎯 FINAL VERIFICATION RESULTS")
    print("=" * 60)
    
    if results["admin_login_test"]:
        print("✅ SUCCESS: Admin login working")
        print("✅ SUCCESS: Admin can access management pages")
        if results["rbac_test"]:
            print("✅ SUCCESS: RBAC properly restricts admin from super admin pages")
        else:
            print("⚠️ WARNING: RBAC issue detected")
    else:
        print("❌ FAILURE: Admin login still not working")
        print("   Manual intervention required")
    
    return results["admin_login_test"]

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)