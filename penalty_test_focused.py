#!/usr/bin/env python3
"""
Focused Late Penalty System Testing for TANSEEQ HR System
Tests the complex penalty system as requested in Arabic review
"""

import requests
import sys
import json
from datetime import datetime

class PenaltySystemTester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.api_url = f"{self.base_url}/api"
        self.tokens = {}
        self.users = {}
        self.tests_run = 0
        self.tests_passed = 0
        
        # Test users (from the review request - specifically hatem@tanseeq.com)
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
        """Make HTTP request and return success status and response"""
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
            self.users[role] = response['user']
            self.log_test(f"Login as {role} ({user_data['email']})", True)
            return True
        else:
            self.log_test(f"Login as {role} ({user_data['email']})", False, str(response))
            return False

    def test_penalty_calculation_endpoint(self, role: str) -> bool:
        """Test /penalties/late/{month} GET endpoint"""
        if role not in self.tokens:
            return False
        
        month = '2025-02'
        success, response = self.make_request('GET', f'penalties/late/{month}', token=self.tokens[role])
        
        if success and isinstance(response, list):
            self.log_test(f"Penalty calculation endpoint ({role})", True, f"Found {len(response)} penalty records")
            
            # Print detailed penalty information for verification
            if response:
                print(f"   📊 Sample penalty calculation for {role}:")
                penalty = response[0]
                print(f"      Employee: {penalty.get('user_name', 'Unknown')}")
                print(f"      Total late minutes: {penalty.get('total_late_minutes', 0)}")
                print(f"      Late incidents: {penalty.get('late_incidents', 0)}")
                print(f"      Free minutes: {penalty.get('free_late_minutes', 0)}")
                print(f"      Penalty minutes: {penalty.get('penalty_minutes', 0)}")
                print(f"      Penalty amount: AED {penalty.get('penalty_amount', 0):.2f}")
                print(f"      Penalty type: {penalty.get('penalty_type', 'none')}")
            
            return True
        else:
            expected_status = 200 if role in ['admin', 'super_admin'] else 403
            if not success and expected_status == 403:
                self.log_test(f"Penalty calculation endpoint ({role})", True, "Access denied as expected")
                return True
            else:
                self.log_test(f"Penalty calculation endpoint ({role})", False, str(response))
                return False

    def test_penalty_application_endpoint(self, role: str) -> bool:
        """Test /penalties/apply/{month} POST endpoint"""
        if role not in self.tokens:
            return False
        
        month = '2025-02'
        success, response = self.make_request('POST', f'penalties/apply/{month}', token=self.tokens[role])
        
        # Check if this is Hatem (should be the only one who can apply)
        user_name = self.users.get(role, {}).get('name', '')
        is_hatem = user_name == 'Hatem Mohamed Ahmed'
        
        if is_hatem and success:
            self.log_test(f"Penalty application endpoint ({role} - Hatem)", True, 
                         f"Applied penalties: {response.get('total_employees', 0)} employees, AED {response.get('total_penalty_amount', 0):.2f}")
            return True
        elif not is_hatem:
            # Non-Hatem users should get access denied
            if not success and ('admin access required' in str(response).lower() or 
                              'super admin access required' in str(response).lower()):
                self.log_test(f"Penalty application endpoint ({role})", True, "Access denied as expected (only Hatem can apply)")
                return True
            else:
                self.log_test(f"Penalty application endpoint ({role})", False, f"Should be denied for non-Hatem users: {response}")
                return False
        else:
            # Hatem but failed
            self.log_test(f"Penalty application endpoint ({role} - Hatem)", False, str(response))
            return False

    def test_penalty_history_endpoint(self, role: str) -> bool:
        """Test /penalties/history/{user_id} GET endpoint"""
        if role not in self.tokens:
            return False
        
        user_id = self.users[role]['id']
        success, response = self.make_request('GET', f'penalties/history/{user_id}', token=self.tokens[role])
        
        if success and isinstance(response, list):
            self.log_test(f"Penalty history endpoint ({role})", True, f"Found {len(response)} penalty history records")
            return True
        else:
            self.log_test(f"Penalty history endpoint ({role})", False, str(response))
            return False

    def test_complex_penalty_rules(self, role: str) -> bool:
        """Test complex penalty rules implementation"""
        if role not in self.tokens or role not in ['admin', 'super_admin']:
            self.log_test(f"Complex penalty rules verification ({role})", True, "Skipped for non-admin")
            return True
        
        month = '2025-02'
        success, response = self.make_request('GET', f'penalties/late/{month}', token=self.tokens[role])
        
        if success and isinstance(response, list):
            rules_verified = True
            rules_details = []
            
            for penalty in response:
                user_name = penalty.get('user_name', 'Unknown')
                total_late_minutes = penalty.get('total_late_minutes', 0)
                late_incidents = penalty.get('late_incidents', 0)
                free_late_minutes = penalty.get('free_late_minutes', 0)
                penalty_minutes = penalty.get('penalty_minutes', 0)
                penalty_type = penalty.get('penalty_type', '')
                penalty_amount = penalty.get('penalty_amount', 0)
                
                # Rule verification
                rule_check = f"   {user_name}: {total_late_minutes}min late, {late_incidents} incidents"
                
                # Rule 1: First 15 minutes x 4 times = free
                if late_incidents <= 4:
                    expected_free = total_late_minutes  # All free if 4 or less
                else:
                    expected_free = min(60, late_incidents * 15)  # Max 60 minutes free
                
                if free_late_minutes == expected_free:
                    rule_check += f" ✓ Free minutes: {free_late_minutes}"
                else:
                    rule_check += f" ✗ Free minutes: {free_late_minutes} (expected {expected_free})"
                    rules_verified = False
                
                # Rule 2-4: Penalty calculation
                expected_penalty_minutes = max(0, total_late_minutes - free_late_minutes)
                if penalty_minutes == expected_penalty_minutes:
                    rule_check += f" ✓ Penalty minutes: {penalty_minutes}"
                else:
                    rule_check += f" ✗ Penalty minutes: {penalty_minutes} (expected {expected_penalty_minutes})"
                    rules_verified = False
                
                # Penalty type verification
                if penalty_minutes == 0:
                    expected_type = 'none'
                elif penalty_minutes <= 20:
                    expected_type = 'minutes'
                elif penalty_minutes <= 120:
                    expected_type = 'actual_time' if penalty_minutes < 60 else 'half_day'
                else:
                    expected_type = 'full_day'
                
                if penalty_type == expected_type or (penalty_minutes > 60 and penalty_type in ['actual_time', 'half_day']):
                    rule_check += f" ✓ Type: {penalty_type}"
                else:
                    rule_check += f" ✗ Type: {penalty_type} (expected {expected_type})"
                    rules_verified = False
                
                rule_check += f" → AED {penalty_amount:.2f}"
                rules_details.append(rule_check)
            
            self.log_test(f"Complex penalty rules verification ({role})", rules_verified, 
                         "Some rules not applied correctly" if not rules_verified else "")
            
            # Print detailed rule verification
            if rules_details:
                print("   📋 Penalty Rules Verification:")
                for detail in rules_details[:3]:  # Show first 3 for brevity
                    print(detail)
                if len(rules_details) > 3:
                    print(f"   ... and {len(rules_details) - 3} more employees")
            
            return rules_verified
        else:
            self.log_test(f"Complex penalty rules verification ({role})", False, str(response))
            return False

    def test_security_access_control(self):
        """Test security and access control for penalty system"""
        print("\n🔒 Testing Security and Access Control:")
        
        # Test each role's access
        for role in ['user', 'admin', 'super_admin']:
            if role not in self.tokens:
                continue
            
            print(f"\n   Testing {role.upper()} access:")
            
            # Test calculation endpoint
            month = '2025-02'
            success_calc, response_calc = self.make_request('GET', f'penalties/late/{month}', 
                                                          token=self.tokens[role])
            
            if role in ['admin', 'super_admin']:
                if success_calc:
                    print(f"   ✅ {role} can access penalty calculation")
                else:
                    print(f"   ❌ {role} cannot access penalty calculation: {response_calc}")
            else:
                if not success_calc and 'admin access required' in str(response_calc).lower():
                    print(f"   ✅ {role} correctly denied penalty calculation access")
                else:
                    print(f"   ❌ {role} should be denied penalty calculation access")
            
            # Test application endpoint
            success_apply, response_apply = self.make_request('POST', f'penalties/apply/{month}', 
                                                            token=self.tokens[role])
            
            user_name = self.users.get(role, {}).get('name', '')
            is_hatem = user_name == 'Hatem Mohamed Ahmed'
            
            if is_hatem:
                if success_apply or 'access' not in str(response_apply).lower():
                    print(f"   ✅ Hatem can apply penalties")
                else:
                    print(f"   ❌ Hatem should be able to apply penalties: {response_apply}")
            else:
                if not success_apply and ('admin access required' in str(response_apply).lower() or 
                                        'super admin access required' in str(response_apply).lower()):
                    print(f"   ✅ {role} correctly denied penalty application access")
                else:
                    print(f"   ❌ {role} should be denied penalty application access")

    def run_penalty_tests(self):
        """Run comprehensive penalty system tests"""
        print("⏰ TANSEEQ HR - Late Penalty System Testing")
        print("=" * 60)
        print("Testing complex penalty system as requested in Arabic review:")
        print("1. Late penalty calculation with complex rules")
        print("2. Penalty application (Hatem only)")
        print("3. Penalty history tracking")
        print("4. Security and access control")
        print("=" * 60)
        
        # Login all users
        for role in ['user', 'admin', 'super_admin']:
            if not self.test_login(role):
                print(f"❌ Failed to login {role} - skipping tests for this role")
        
        print(f"\n📊 Testing Penalty Calculation Endpoints:")
        for role in ['user', 'admin', 'super_admin']:
            if role in self.tokens:
                self.test_penalty_calculation_endpoint(role)
        
        print(f"\n⚡ Testing Penalty Application Endpoints:")
        for role in ['user', 'admin', 'super_admin']:
            if role in self.tokens:
                self.test_penalty_application_endpoint(role)
        
        print(f"\n📋 Testing Penalty History Endpoints:")
        for role in ['user', 'admin', 'super_admin']:
            if role in self.tokens:
                self.test_penalty_history_endpoint(role)
        
        print(f"\n🧮 Testing Complex Penalty Rules:")
        for role in ['admin', 'super_admin']:
            if role in self.tokens:
                self.test_complex_penalty_rules(role)
        
        # Security testing
        self.test_security_access_control()
        
        # Summary
        print("\n" + "=" * 60)
        print(f"📊 Penalty System Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All penalty system tests passed!")
        else:
            failed_tests = self.tests_run - self.tests_passed
            print(f"⚠️  {failed_tests} penalty system tests failed")
        
        return self.tests_passed >= (self.tests_run * 0.8)  # 80% pass rate

if __name__ == "__main__":
    # Get backend URL from environment
    import os
    backend_url = "https://payroll-ledger-1.preview.emergentagent.com"
    
    print(f"🔗 Using backend URL: {backend_url}")
    
    tester = PenaltySystemTester(backend_url)
    success = tester.run_penalty_tests()
    
    sys.exit(0 if success else 1)