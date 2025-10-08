#!/usr/bin/env python3
"""
Login Credentials Testing Script
Tests specific user accounts to identify working credentials and roles
Focus: Finding Super Admin account for Advances and Loans system access
"""

import requests
import json
from datetime import datetime
import os
import sys

# Backend URL from environment
BACKEND_URL = "https://tanseeq-payroll.preview.emergentagent.com/api"

# Test credentials as requested
TEST_CREDENTIALS = [
    {"email": "hatem@tanseeq.com", "password": "hatem123"},
    {"email": "mahmoud@tanseeq.com", "password": "mahmoud123"},
    {"email": "jihad@tanseeq.com", "password": "jihad123"},
    {"email": "admin@tanseeq.com", "password": "admin123"},
    {"email": "hatem@tan-seeq.co", "password": "hatem123"}
]

class LoginCredentialsTest:
    def __init__(self):
        self.results = []
        self.working_credentials = []
        self.super_admin_accounts = []
        
    def test_login(self, email, password):
        """Test login with specific credentials"""
        try:
            response = requests.post(
                f"{BACKEND_URL}/auth/login",
                json={"email": email, "password": password},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                user_info = data.get("user", {})
                
                result = {
                    "email": email,
                    "password": password,
                    "status": "SUCCESS",
                    "role": user_info.get("role", "unknown"),
                    "name": user_info.get("name", "unknown"),
                    "position": user_info.get("position", ""),
                    "is_active": user_info.get("is_active", False),
                    "token": data.get("access_token", "")[:50] + "..." if data.get("access_token") else ""
                }
                
                self.working_credentials.append(result)
                
                # Check if Super Admin
                if user_info.get("role") == "super_admin":
                    self.super_admin_accounts.append(result)
                    
                return result
            else:
                return {
                    "email": email,
                    "password": password,
                    "status": "FAILED",
                    "error": f"HTTP {response.status_code}: {response.text[:100]}"
                }
                
        except Exception as e:
            return {
                "email": email,
                "password": password,
                "status": "ERROR",
                "error": str(e)
            }
    
    def test_advances_access(self, token, user_info):
        """Test access to Advances and Loans system endpoints"""
        headers = {"Authorization": f"Bearer {token}"}
        
        advances_endpoints = [
            "/advances/my-balance",
            "/advances/my-transactions",
            "/advances/admin/all-balances",
            "/advances/admin/pending-approvals"
        ]
        
        access_results = {}
        
        for endpoint in advances_endpoints:
            try:
                response = requests.get(
                    f"{BACKEND_URL}{endpoint}",
                    headers=headers,
                    timeout=10
                )
                
                access_results[endpoint] = {
                    "status_code": response.status_code,
                    "accessible": response.status_code in [200, 404],  # 404 means endpoint exists but no data
                    "response": response.text[:200] if response.status_code != 200 else "SUCCESS"
                }
                
            except Exception as e:
                access_results[endpoint] = {
                    "status_code": "ERROR",
                    "accessible": False,
                    "response": str(e)
                }
        
        return access_results
    
    def test_dashboard_access(self, token):
        """Test basic dashboard access"""
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            response = requests.get(
                f"{BACKEND_URL}/dashboard/stats",
                headers=headers,
                timeout=10
            )
            
            return {
                "dashboard_accessible": response.status_code == 200,
                "status_code": response.status_code,
                "response": response.text[:200] if response.status_code != 200 else "Dashboard accessible"
            }
            
        except Exception as e:
            return {
                "dashboard_accessible": False,
                "error": str(e)
            }
    
    def run_comprehensive_test(self):
        """Run comprehensive login and access testing"""
        print("🔐 TANSEEQ LOGIN CREDENTIALS TESTING")
        print("=" * 60)
        print(f"Testing {len(TEST_CREDENTIALS)} credential sets...")
        print(f"Backend URL: {BACKEND_URL}")
        print()
        
        # Test each credential set
        for i, creds in enumerate(TEST_CREDENTIALS, 1):
            print(f"[{i}/{len(TEST_CREDENTIALS)}] Testing: {creds['email']}")
            
            result = self.test_login(creds['email'], creds['password'])
            self.results.append(result)
            
            if result['status'] == 'SUCCESS':
                print(f"  ✅ LOGIN SUCCESS - Role: {result['role']} - Name: {result['name']}")
                
                # Test Advances system access for working credentials
                if result.get('token'):
                    token = result['token'].replace('...', '')  # Remove truncation for actual testing
                    # Get full token from login response
                    login_response = requests.post(
                        f"{BACKEND_URL}/auth/login",
                        json={"email": creds['email'], "password": creds['password']},
                        timeout=10
                    )
                    if login_response.status_code == 200:
                        full_token = login_response.json().get('access_token', '')
                        
                        # Test Advances access
                        advances_access = self.test_advances_access(full_token, result)
                        result['advances_access'] = advances_access
                        
                        # Test dashboard access
                        dashboard_access = self.test_dashboard_access(full_token)
                        result['dashboard_access'] = dashboard_access
                        
                        # Check Super Admin specific access
                        if result['role'] == 'super_admin':
                            print(f"  🔑 SUPER ADMIN FOUND - Testing advanced access...")
                            accessible_endpoints = sum(1 for ep, data in advances_access.items() if data['accessible'])
                            print(f"  📊 Advances System Access: {accessible_endpoints}/{len(advances_access)} endpoints accessible")
                
            else:
                print(f"  ❌ LOGIN FAILED - {result.get('error', 'Unknown error')}")
            
            print()
        
        # Generate summary report
        self.generate_summary_report()
    
    def generate_summary_report(self):
        """Generate comprehensive summary report"""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("=" * 60)
        
        print(f"Total Credentials Tested: {len(TEST_CREDENTIALS)}")
        print(f"Working Credentials: {len(self.working_credentials)}")
        print(f"Super Admin Accounts Found: {len(self.super_admin_accounts)}")
        print()
        
        if self.working_credentials:
            print("✅ WORKING CREDENTIALS:")
            print("-" * 40)
            for cred in self.working_credentials:
                print(f"📧 Email: {cred['email']}")
                print(f"🔑 Password: {cred['password']}")
                print(f"👤 Name: {cred['name']}")
                print(f"🎭 Role: {cred['role']}")
                print(f"💼 Position: {cred['position']}")
                print(f"🟢 Active: {cred['is_active']}")
                
                # Show Advances system access if tested
                if 'advances_access' in cred:
                    accessible_count = sum(1 for ep, data in cred['advances_access'].items() if data['accessible'])
                    print(f"💰 Advances System Access: {accessible_count}/4 endpoints")
                
                # Show dashboard access
                if 'dashboard_access' in cred:
                    dashboard_status = "✅ Accessible" if cred['dashboard_access']['dashboard_accessible'] else "❌ Not Accessible"
                    print(f"📊 Dashboard Access: {dashboard_status}")
                
                print()
        
        if self.super_admin_accounts:
            print("🔑 SUPER ADMIN ACCOUNTS (Advances & Loans Access):")
            print("-" * 50)
            for admin in self.super_admin_accounts:
                print(f"🎯 RECOMMENDED FOR ADVANCES & LOANS SYSTEM:")
                print(f"   📧 Email: {admin['email']}")
                print(f"   🔑 Password: {admin['password']}")
                print(f"   👤 Name: {admin['name']}")
                print(f"   💼 Position: {admin['position']}")
                
                if 'advances_access' in admin:
                    print(f"   💰 Advances System Endpoints:")
                    for endpoint, access_data in admin['advances_access'].items():
                        status = "✅" if access_data['accessible'] else "❌"
                        print(f"      {status} {endpoint} (HTTP {access_data['status_code']})")
                print()
        else:
            print("❌ NO SUPER ADMIN ACCOUNTS FOUND")
            print("   Unable to identify accounts with full Advances & Loans system access")
            print()
        
        # Failed credentials
        failed_credentials = [r for r in self.results if r['status'] != 'SUCCESS']
        if failed_credentials:
            print("❌ FAILED CREDENTIALS:")
            print("-" * 30)
            for cred in failed_credentials:
                print(f"📧 {cred['email']} - {cred.get('error', 'Login failed')}")
            print()
        
        # Final recommendation
        print("🎯 FINAL RECOMMENDATION:")
        print("-" * 30)
        if self.super_admin_accounts:
            recommended = self.super_admin_accounts[0]
            print(f"✅ USE THIS ACCOUNT FOR ADVANCES & LOANS SYSTEM:")
            print(f"   📧 Email: {recommended['email']}")
            print(f"   🔑 Password: {recommended['password']}")
            print(f"   👤 Name: {recommended['name']}")
            print(f"   🎭 Role: {recommended['role']}")
        elif self.working_credentials:
            print(f"⚠️  Found {len(self.working_credentials)} working accounts but no Super Admin")
            print("   Super Admin access required for full Advances & Loans functionality")
            best_account = max(self.working_credentials, key=lambda x: 1 if x['role'] == 'admin' else 0)
            print(f"   Best available: {best_account['email']} ({best_account['role']})")
        else:
            print("❌ NO WORKING CREDENTIALS FOUND")
            print("   All tested accounts failed to authenticate")
        
        print("\n" + "=" * 60)

def main():
    """Main execution function"""
    print("Starting TANSEEQ Login Credentials Test...")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tester = LoginCredentialsTest()
    tester.run_comprehensive_test()
    
    # Save results to file
    with open('/app/login_test_results.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_tested': len(TEST_CREDENTIALS),
            'working_credentials': tester.working_credentials,
            'super_admin_accounts': tester.super_admin_accounts,
            'all_results': tester.results
        }, f, indent=2)
    
    print(f"📄 Detailed results saved to: /app/login_test_results.json")

if __name__ == "__main__":
    main()