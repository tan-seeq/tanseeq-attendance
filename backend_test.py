#!/usr/bin/env python3
"""
URGENT VERIFICATION: Complete System Health Check After Environment Fix
Testing all advances endpoints with the new production domain: hrapp-tanseeq.emergent.host
"""

import requests
import json
import os
from datetime import datetime, timedelta
import uuid

# Configuration - Test both local and production
LOCAL_BACKEND_URL = "http://localhost:8001/api"
PRODUCTION_BACKEND_URL = "https://hrapp-tanseeq.emergent.host/api"

print(f"🔗 Testing Local Backend URL: {LOCAL_BACKEND_URL}")
print(f"🔗 Testing Production Backend URL: {PRODUCTION_BACKEND_URL}")

# Test credentials from previous testing history
TEST_CREDENTIALS = [
    {"email": "hatem@tanseeq.com", "password": "hatem123", "role": "super_admin", "name": "Hatem (Super Admin)"},
    {"email": "hatem@tan-seeq.co", "password": "hatem123", "role": "super_admin", "name": "Hatem Alt (Super Admin)"},
    {"email": "mahmoud@tanseeq.com", "password": "admin123", "role": "admin", "name": "Mahmoud (Admin)"},
    {"email": "jihad@tanseeq.com", "password": "user123", "role": "user", "name": "Jihad (User)"},
    {"email": "admin@tanseeq.com", "password": "admin123", "role": "admin", "name": "Admin"},
    {"email": "hatemmo186@gmail.com", "password": "hatem123", "role": "super_admin", "name": "Hatem Gmail"}
]

class AdvancesSystemTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.auth_token = None
        self.current_user = None
        self.test_results = []
        
    def log_test(self, test_name, success, details="", error=""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   📋 {details}")
        if error:
            print(f"   ⚠️  {error}")
        print()

    def test_authentication(self, backend_url):
        """Test authentication with all available credentials"""
        print(f"🔐 TESTING AUTHENTICATION WITH {backend_url}")
        print("=" * 60)
        
        auth_success = False
        working_credentials = None
        
        for cred in TEST_CREDENTIALS:
            try:
                print(f"🧪 Testing login: {cred['email']} ({cred['name']})")
                
                response = self.session.post(
                    f"{backend_url}/auth/login",
                    json={
                        "email": cred["email"],
                        "password": cred["password"]
                    },
                    timeout=30
                )
                
                print(f"   Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    if "access_token" in data:
                        self.auth_token = data["access_token"]
                        self.current_user = data.get("user", {})
                        self.session.headers.update({
                            'Authorization': f'Bearer {self.auth_token}'
                        })
                        
                        working_credentials = cred
                        auth_success = True
                        
                        self.log_test(
                            f"Authentication - {cred['name']}", 
                            True,
                            f"Successfully authenticated as {self.current_user.get('name', 'Unknown')} ({self.current_user.get('role', 'Unknown')})"
                        )
                        break
                    else:
                        self.log_test(
                            f"Authentication - {cred['name']}", 
                            False,
                            error="No access token in response"
                        )
                else:
                    error_msg = f"HTTP {response.status_code}"
                    try:
                        error_data = response.json()
                        error_msg += f" - {error_data.get('detail', 'Unknown error')}"
                    except:
                        error_msg += f" - {response.text[:100]}"
                    
                    self.log_test(
                        f"Authentication - {cred['name']}", 
                        False,
                        error=error_msg
                    )
                        
            except Exception as e:
                self.log_test(
                    f"Authentication - {cred['name']}", 
                    False,
                    error=f"Connection error: {str(e)}"
                )
        
        if not auth_success:
            print("🚨 CRITICAL: No working authentication credentials found!")
            return False
            
        print(f"✅ Authentication successful with: {working_credentials['name']}")
        return True

    def test_advances_endpoints(self):
        """Test all advances system endpoints"""
        print("💰 TESTING ADVANCES SYSTEM ENDPOINTS")
        print("=" * 60)
        
        if not self.auth_token:
            self.log_test("Advances Endpoints", False, error="No authentication token available")
            return
        
        # Test 1: Get my balance
        try:
            response = self.session.get(f"{BACKEND_URL}/advances/my-balance", timeout=30)
            if response.status_code == 200:
                balance_data = response.json()
                self.log_test(
                    "GET /advances/my-balance",
                    True,
                    f"Total Available: {balance_data.get('total_available', 0)} AED, Advances: {balance_data.get('remaining_advance', 0)}, Custody: {balance_data.get('remaining_custody', 0)}"
                )
            else:
                self.log_test("GET /advances/my-balance", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("GET /advances/my-balance", False, error=str(e))

        # Test 2: Get my transactions
        try:
            response = self.session.get(f"{BACKEND_URL}/advances/my-transactions", timeout=30)
            if response.status_code == 200:
                transactions_data = response.json()
                transaction_count = len(transactions_data.get('transactions', []))
                self.log_test(
                    "GET /advances/my-transactions",
                    True,
                    f"Found {transaction_count} transactions"
                )
            else:
                self.log_test("GET /advances/my-transactions", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("GET /advances/my-transactions", False, error=str(e))

        # Test 3: Admin endpoints (if super admin)
        if self.current_user.get('role') == 'super_admin':
            # Test all balances
            try:
                response = self.session.get(f"{BACKEND_URL}/advances/admin/all-balances", timeout=30)
                if response.status_code == 200:
                    balances_data = response.json()
                    employee_count = len(balances_data.get('employee_balances', []))
                    self.log_test(
                        "GET /advances/admin/all-balances",
                        True,
                        f"Found balances for {employee_count} employees"
                    )
                else:
                    self.log_test("GET /advances/admin/all-balances", False, error=f"HTTP {response.status_code}")
            except Exception as e:
                self.log_test("GET /advances/admin/all-balances", False, error=str(e))

            # Test all transactions
            try:
                response = self.session.get(f"{BACKEND_URL}/advances/admin/all-transactions", timeout=30)
                if response.status_code == 200:
                    transactions_data = response.json()
                    transaction_count = len(transactions_data.get('transactions', []))
                    self.log_test(
                        "GET /advances/admin/all-transactions",
                        True,
                        f"Found {transaction_count} total transactions across all employees"
                    )
                else:
                    self.log_test("GET /advances/admin/all-transactions", False, error=f"HTTP {response.status_code}")
            except Exception as e:
                self.log_test("GET /advances/admin/all-transactions", False, error=str(e))

            # Test pending approvals
            try:
                response = self.session.get(f"{BACKEND_URL}/advances/admin/pending-approvals", timeout=30)
                if response.status_code == 200:
                    pending_data = response.json()
                    pending_count = len(pending_data.get('pending_transactions', []))
                    self.log_test(
                        "GET /advances/admin/pending-approvals",
                        True,
                        f"Found {pending_count} pending transactions"
                    )
                else:
                    self.log_test("GET /advances/admin/pending-approvals", False, error=f"HTTP {response.status_code}")
            except Exception as e:
                self.log_test("GET /advances/admin/pending-approvals", False, error=str(e))

            # Test advance creation (the critical endpoint from review)
            try:
                # Get a valid employee ID first
                users_response = self.session.get(f"{BACKEND_URL}/users", timeout=30)
                if users_response.status_code == 200:
                    users_data = users_response.json()
                    if users_data and len(users_data) > 0:
                        test_employee_id = users_data[0].get('id')
                    else:
                        test_employee_id = self.current_user.get('id')
                else:
                    test_employee_id = self.current_user.get('id')

                create_data = {
                    "employee_id": test_employee_id,
                    "transaction_type": "custody",
                    "amount": 50.0,
                    "description": "Test custody for system verification after URL fix",
                    "notes": "Environment fix verification test"
                }
                
                response = self.session.post(
                    f"{BACKEND_URL}/advances/create",
                    json=create_data,
                    timeout=30
                )
                
                if response.status_code in [200, 201]:
                    create_result = response.json()
                    self.log_test(
                        "POST /advances/create",
                        True,
                        f"Successfully created custody: {create_result.get('message', 'Success')} - Transaction ID: {create_result.get('transaction_id', 'N/A')}"
                    )
                else:
                    error_msg = f"HTTP {response.status_code}"
                    try:
                        error_data = response.json()
                        error_msg += f" - {error_data.get('detail', 'Unknown error')}"
                    except:
                        error_msg += f" - {response.text[:200]}"
                    self.log_test("POST /advances/create", False, error=error_msg)
                    
            except Exception as e:
                self.log_test("POST /advances/create", False, error=str(e))

    def test_general_system_health(self):
        """Test general system endpoints to verify overall health"""
        print("🏥 TESTING GENERAL SYSTEM HEALTH")
        print("=" * 60)
        
        if not self.auth_token:
            self.log_test("System Health Check", False, error="No authentication token available")
            return
        
        # Test dashboard/user info
        try:
            response = self.session.get(f"{BACKEND_URL}/auth/me", timeout=30)
            if response.status_code == 200:
                user_data = response.json()
                self.log_test(
                    "GET /auth/me",
                    True,
                    f"User: {user_data.get('name')} ({user_data.get('role')}) - Active: {user_data.get('is_active')}"
                )
            else:
                self.log_test("GET /auth/me", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("GET /auth/me", False, error=str(e))

        # Test attendance endpoint
        try:
            response = self.session.get(f"{BACKEND_URL}/attendance", timeout=30)
            if response.status_code == 200:
                attendance_data = response.json()
                self.log_test(
                    "GET /attendance",
                    True,
                    f"Attendance system accessible"
                )
            else:
                self.log_test("GET /attendance", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("GET /attendance", False, error=str(e))

    def test_database_connectivity(self):
        """Test database connectivity through API calls"""
        print("🗄️  TESTING DATABASE CONNECTIVITY")
        print("=" * 60)
        
        if not self.auth_token:
            self.log_test("Database Connectivity", False, error="No authentication token available")
            return
        
        # Test that we can retrieve data (indicates DB connection works)
        try:
            response = self.session.get(f"{BACKEND_URL}/advances/my-balance", timeout=30)
            if response.status_code == 200:
                self.log_test(
                    "Database Connection via Advances",
                    True,
                    "Successfully retrieved balance data from database"
                )
            else:
                self.log_test("Database Connection via Advances", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Database Connection via Advances", False, error=str(e))

    def run_comprehensive_test(self):
        """Run all tests in sequence"""
        print("🚀 STARTING COMPREHENSIVE SYSTEM HEALTH CHECK")
        print("🔧 Environment Fix Verification: REACT_APP_BACKEND_URL = hrapp-tanseeq.emergent.host")
        print("=" * 80)
        print()
        
        # Step 1: Test Authentication
        if not self.test_authentication():
            print("🚨 CRITICAL FAILURE: Authentication failed - cannot proceed with other tests")
            return self.generate_summary()
        
        # Step 2: Test Advances System
        self.test_advances_endpoints()
        
        # Step 3: Test General System Health
        self.test_general_system_health()
        
        # Step 4: Test Database Connectivity
        self.test_database_connectivity()
        
        return self.generate_summary()

    def generate_summary(self):
        """Generate comprehensive test summary"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📈 Overall Results: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}% success rate)")
        print()
        
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   • {result['test']}: {result['error']}")
            print()
        
        print("✅ PASSED TESTS:")
        for result in self.test_results:
            if result['success']:
                print(f"   • {result['test']}: {result['details']}")
        
        print("\n" + "=" * 80)
        
        # Critical assessment
        auth_working = any(r['success'] and 'Authentication' in r['test'] for r in self.test_results)
        advances_working = any(r['success'] and 'advances' in r['test'].lower() for r in self.test_results)
        
        if auth_working and advances_working:
            print("🎉 ENVIRONMENT FIX VERIFICATION: SUCCESS")
            print("✅ Authentication working with production URL")
            print("✅ Advances system endpoints accessible")
            print("✅ System appears to be fully operational")
        else:
            print("🚨 ENVIRONMENT FIX VERIFICATION: ISSUES DETECTED")
            if not auth_working:
                print("❌ Authentication issues persist")
            if not advances_working:
                print("❌ Advances system still has issues")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': success_rate,
            'auth_working': auth_working,
            'advances_working': advances_working,
            'results': self.test_results
        }

if __name__ == "__main__":
    tester = AdvancesSystemTester()
    summary = tester.run_comprehensive_test()
    
    # Exit with appropriate code
    if summary['success_rate'] >= 80 and summary['auth_working']:
        exit(0)  # Success
    else:
        exit(1)  # Failure