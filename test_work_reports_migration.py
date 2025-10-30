#!/usr/bin/env python3
"""
Work Reports MongoDB Migration Testing
Focused test for the SQLite to MongoDB migration
"""

import requests
import sys
import json
from datetime import datetime

class WorkReportsMigrationTester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        if self.base_url.endswith('/api'):
            self.api_url = self.base_url
        else:
            self.api_url = f"{self.base_url}/api"
        self.tokens = {}
        self.tests_run = 0
        self.tests_passed = 0
        
        # Test users
        self.test_users = {
            'user': {'email': 'jihad@tanseeq.com', 'password': 'jihad123'},
            'admin': {'email': 'mahmoud@tanseeq.com', 'password': 'mahmoud123'},
            'super_admin': {'email': 'hatem@tanseeq.com', 'password': 'hatem123'}
        }

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")

    def make_request(self, method: str, endpoint: str, data=None, token=None, expected_status=200):
        """Make HTTP request"""
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            else:
                return False, {"error": f"Unsupported method: {method}"}
            
            success = response.status_code == expected_status
            try:
                response_data = response.json()
            except:
                response_data = {"status_code": response.status_code, "text": response.text}
            
            return success, response_data
            
        except requests.exceptions.RequestException as e:
            return False, {"error": str(e)}

    def test_login(self, role: str) -> bool:
        """Test login for specific role"""
        user_data = self.test_users[role]
        success, response = self.make_request('POST', 'auth/login', user_data)
        
        if success and 'access_token' in response:
            self.tokens[role] = response['access_token']
            self.log_test(f"Login as {role}", True)
            return True
        else:
            self.log_test(f"Login as {role}", False, str(response))
            return False

    def test_work_reports_dashboard(self, role: str) -> bool:
        """Test Work Reports dashboard - MongoDB Migration Verification"""
        if role not in self.tokens:
            return False
            
        success, response = self.make_request('GET', 'work-reports/dashboard', 
                                            token=self.tokens[role])
        
        if success and isinstance(response, dict):
            expected_keys = ['total_clients', 'todays_logs', 'monthly_logs', 'billable_hours', 'revenue']
            has_expected_keys = all(key in response for key in expected_keys)
            
            self.log_test(f"Work Reports Dashboard MongoDB ({role})", has_expected_keys,
                         f"Response: {response}" if not has_expected_keys else "")
            return has_expected_keys
        else:
            self.log_test(f"Work Reports Dashboard MongoDB ({role})", False, str(response))
            return False

    def test_work_reports_clients(self, role: str) -> bool:
        """Test Work Reports clients - MongoDB Migration Verification"""
        if role not in self.tokens:
            return False
        
        success, response = self.make_request('GET', 'work-reports/clients', 
                                            token=self.tokens[role])
        
        if success and isinstance(response, list):
            self.log_test(f"Work Reports Clients MongoDB ({role})", True, 
                         f"Found {len(response)} clients")
            return True
        else:
            self.log_test(f"Work Reports Clients MongoDB ({role})", False, str(response))
            return False

    def test_work_reports_activity_types(self, role: str) -> bool:
        """Test Work Reports activity types - MongoDB Migration Verification"""
        if role not in self.tokens:
            return False
            
        success, response = self.make_request('GET', 'work-reports/activity-types', 
                                            token=self.tokens[role])
        
        if success and isinstance(response, list):
            self.log_test(f"Work Reports Activity Types MongoDB ({role})", True,
                         f"Found {len(response)} activity types")
            return True
        else:
            self.log_test(f"Work Reports Activity Types MongoDB ({role})", False, str(response))
            return False

    def test_mongodb_migration_verification(self, role: str) -> bool:
        """Comprehensive MongoDB Migration Verification"""
        if role not in self.tokens:
            return False
        
        migration_tests = []
        
        # Test 1: Dashboard
        dashboard_success, _ = self.make_request('GET', 'work-reports/dashboard', 
                                               token=self.tokens[role])
        migration_tests.append(('Dashboard', dashboard_success))
        
        # Test 2: Clients
        clients_success, _ = self.make_request('GET', 'work-reports/clients', 
                                             token=self.tokens[role])
        migration_tests.append(('Clients', clients_success))
        
        # Test 3: Activity Types
        activities_success, _ = self.make_request('GET', 'work-reports/activity-types', 
                                                token=self.tokens[role])
        migration_tests.append(('Activity Types', activities_success))
        
        passed_tests = sum(1 for _, success in migration_tests if success)
        total_tests = len(migration_tests)
        migration_success = passed_tests == total_tests
        
        test_details = ', '.join([f"{name}: {'✓' if success else '✗'}" for name, success in migration_tests])
        self.log_test(f"MongoDB Migration Verification ({role})", migration_success,
                     f"({passed_tests}/{total_tests}) {test_details}")
        
        return migration_success

    def test_system_integration(self, role: str) -> bool:
        """Test system integration - Work Reports doesn't interfere with main HR system"""
        if role not in self.tokens:
            return False
        
        integration_tests = []
        
        # Test main HR dashboard
        hr_success, _ = self.make_request('GET', 'dashboard/stats', token=self.tokens[role])
        integration_tests.append(('HR Dashboard', hr_success))
        
        # Test Work Reports access
        wr_success, _ = self.make_request('GET', 'work-reports/dashboard', token=self.tokens[role])
        integration_tests.append(('Work Reports', wr_success))
        
        passed_tests = sum(1 for _, success in integration_tests if success)
        total_tests = len(integration_tests)
        integration_success = passed_tests == total_tests
        
        test_details = ', '.join([f"{name}: {'✓' if success else '✗'}" for name, success in integration_tests])
        self.log_test(f"System Integration ({role})", integration_success,
                     f"({passed_tests}/{total_tests}) {test_details}")
        
        return integration_success

    def run_migration_tests(self):
        """Run Work Reports MongoDB migration tests"""
        print("🚀 Starting Work Reports MongoDB Migration Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 60)
        
        roles_to_test = ['super_admin', 'admin', 'user']
        
        for role in roles_to_test:
            print(f"\n🔐 Testing {role.upper()} role:")
            print("-" * 30)
            
            if not self.test_login(role):
                print(f"❌ Login failed for {role} - skipping role tests")
                continue
            
            # MongoDB Migration Tests
            print(f"\n📊 MongoDB Migration Tests ({role.upper()}):")
            self.test_work_reports_dashboard(role)
            self.test_work_reports_clients(role)
            self.test_work_reports_activity_types(role)
            self.test_mongodb_migration_verification(role)
            self.test_system_integration(role)
        
        # Summary
        print(f"\n" + "=" * 60)
        print(f"📊 Test Summary:")
        print(f"   Total Tests: {self.tests_run}")
        print(f"   Passed: {self.tests_passed}")
        print(f"   Failed: {self.tests_run - self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    # Get backend URL from frontend .env
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    backend_url = line.split('=', 1)[1].strip()
                    break
        else:
            backend_url = "https://attendance-pro-43.preview.emergentagent.com"
    except:
        backend_url = "https://attendance-pro-43.preview.emergentagent.com"
    
    tester = WorkReportsMigrationTester(backend_url)
    success = tester.run_migration_tests()
    
    if success:
        print("\n✅ All Work Reports MongoDB migration tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some Work Reports MongoDB migration tests failed!")
        sys.exit(1)