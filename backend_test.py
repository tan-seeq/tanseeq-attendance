#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Installment Scheduling System
Testing the completed installment scheduling system for advances and loans within the integrated payroll system.

Priority Testing Areas:
1. Installment Scheduling Endpoints (NEW)
2. Integration Testing
3. Data Validation
4. Error Handling
5. Database Verification
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
import uuid

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://hrms-tanseeq.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
TEST_CREDENTIALS = {
    'super_admin': {
        'email': 'hatem@tan-seeq.co',
        'password': 'hatem123'
    },
    'admin': {
        'email': 'mahmoud@tanseeq.com', 
        'password': 'mahmoud123'
    },
    'user': {
        'email': 'jihad@tanseeq.com',
        'password': 'jihad123'
    }
}

class InstallmentSchedulingTester:
    def __init__(self):
        self.session = None
        self.tokens = {}
        self.test_results = []
        self.created_advances = []
        self.created_schedules = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, status: str, details: str = "", response_data: Any = None):
        """Log test results"""
        result = {
            'test': test_name,
            'status': status,
            'details': details,
            'timestamp': datetime.now().isoformat(),
            'response_data': response_data
        }
        self.test_results.append(result)
        
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
        if response_data and status == "FAIL":
            print(f"   Response: {response_data}")
        print()

    async def authenticate_user(self, role: str) -> Optional[str]:
        """Authenticate user and return token"""
        try:
            credentials = TEST_CREDENTIALS[role]
            async with self.session.post(
                f"{API_BASE}/auth/login",
                json=credentials
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    token = data.get('access_token')
                    self.tokens[role] = token
                    self.log_test(f"Authentication - {role}", "PASS", f"Successfully authenticated {credentials['email']}")
                    return token
                else:
                    error_text = await response.text()
                    self.log_test(f"Authentication - {role}", "FAIL", f"Status: {response.status}, Error: {error_text}")
                    return None
        except Exception as e:
            self.log_test(f"Authentication - {role}", "FAIL", f"Exception: {str(e)}")
            return None

    async def get_existing_advance(self, token: str) -> Optional[str]:
        """Get an existing approved advance for testing"""
        try:
            async with self.session.get(
                f"{API_BASE}/advances/admin/all-transactions?status=approved&transaction_type=advance&limit=10",
                headers={'Authorization': f'Bearer {token}'}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    transactions = data.get('transactions', [])
                    
                    # Find an advance that doesn't have an installment schedule yet
                    for transaction in transactions:
                        advance_id = transaction.get('id')
                        if advance_id:
                            # Check if this advance already has a schedule
                            async with self.session.get(
                                f"{API_BASE}/advances/{advance_id}/installments",
                                headers={'Authorization': f'Bearer {token}'}
                            ) as schedule_response:
                                if schedule_response.status == 404:  # No existing schedule
                                    self.log_test("Get Existing Advance", "PASS", f"Found existing advance ID: {advance_id} without installment schedule")
                                    return advance_id
                    
                    self.log_test("Get Existing Advance", "WARN", "No suitable existing advances found")
                    return None
                else:
                    self.log_test("Get Existing Advance", "FAIL", f"Status: {response.status}")
                    return None
        except Exception as e:
            self.log_test("Get Existing Advance", "FAIL", f"Exception: {str(e)}")
            return None

    async def create_test_advance(self, token: str) -> Optional[str]:
        """Create a test advance for installment scheduling"""
        try:
            # First try to get an existing advance
            existing_advance = await self.get_existing_advance(token)
            if existing_advance:
                return existing_advance
            
            # Get a test employee (jihad)
            employee_id = None
            async with self.session.get(
                f"{API_BASE}/auth/me",
                headers={'Authorization': f'Bearer {self.tokens["user"]}'}
            ) as response:
                if response.status == 200:
                    user_data = await response.json()
                    employee_id = user_data.get('id')
            
            if not employee_id:
                self.log_test("Create Test Advance", "FAIL", "Could not get employee ID")
                return None
            
            advance_data = {
                "employee_id": employee_id,
                "transaction_type": "advance",
                "amount": 5000.0,
                "description": "Test advance for installment scheduling",
                "category": "other",
                "expense_date": datetime.now().strftime("%Y-%m-%d"),
                "notes": "Created for testing installment scheduling system"
            }
            
            async with self.session.post(
                f"{API_BASE}/advances/create",
                json=advance_data,
                headers={'Authorization': f'Bearer {token}'}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    advance_id = data.get('transaction_id')
                    self.created_advances.append(advance_id)
                    self.log_test("Create Test Advance", "PASS", f"Created advance ID: {advance_id}, Amount: {advance_data['amount']}")
                    return advance_id
                else:
                    error_text = await response.text()
                    self.log_test("Create Test Advance", "FAIL", f"Status: {response.status}, Error: {error_text}")
                    return None
        except Exception as e:
            self.log_test("Create Test Advance", "FAIL", f"Exception: {str(e)}")
            return None

    async def test_create_installment_schedule(self, token: str, advance_id: str):
        """Test POST /api/advances/{advance_id}/installments - Create installment schedule"""
        try:
            schedule_data = {
                "installment_amount": 500.0,
                "number_of_installments": 10,
                "start_date": (date.today() + timedelta(days=30)).strftime("%Y-%m-%d"),
                "respect_ceiling": True
            }
            
            async with self.session.post(
                f"{API_BASE}/advances/{advance_id}/installments",
                json=schedule_data,
                headers={'Authorization': f'Bearer {token}'}
            ) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    schedule_id = response_data.get('schedule_id')
                    if schedule_id:
                        self.created_schedules.append(schedule_id)
                    
                    # Validate response structure
                    required_fields = ['message', 'schedule_id', 'total_amount', 'installment_amount', 'number_of_installments']
                    missing_fields = [field for field in required_fields if field not in response_data]
                    
                    if not missing_fields:
                        self.log_test(
                            "Create Installment Schedule", 
                            "PASS", 
                            f"Schedule created successfully. ID: {schedule_id}, Amount: {response_data.get('installment_amount')}, Installments: {response_data.get('number_of_installments')}"
                        )
                    else:
                        self.log_test(
                            "Create Installment Schedule", 
                            "FAIL", 
                            f"Missing required fields: {missing_fields}",
                            response_data
                        )
                else:
                    self.log_test(
                        "Create Installment Schedule", 
                        "FAIL", 
                        f"Status: {response.status}",
                        response_data
                    )
        except Exception as e:
            self.log_test("Create Installment Schedule", "FAIL", f"Exception: {str(e)}")

    async def test_get_installment_schedule(self, token: str, advance_id: str):
        """Test GET /api/advances/{advance_id}/installments - Get specific installment schedule details"""
        try:
            async with self.session.get(
                f"{API_BASE}/advances/{advance_id}/installments",
                headers={'Authorization': f'Bearer {token}'}
            ) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    # Validate response structure
                    if 'schedule' in response_data and 'installments' in response_data:
                        schedule = response_data['schedule']
                        installments = response_data['installments']
                        
                        # Check schedule fields
                        schedule_fields = ['id', 'advance_transaction_id', 'employee_id', 'total_amount', 'installment_amount', 'number_of_installments']
                        missing_schedule_fields = [field for field in schedule_fields if field not in schedule]
                        
                        # Check installments structure
                        installment_count = len(installments)
                        expected_count = schedule.get('number_of_installments', 0)
                        
                        if not missing_schedule_fields and installment_count == expected_count:
                            self.log_test(
                                "Get Installment Schedule", 
                                "PASS", 
                                f"Retrieved schedule with {installment_count} installments. Total: {schedule.get('total_amount')}"
                            )
                        else:
                            issues = []
                            if missing_schedule_fields:
                                issues.append(f"Missing schedule fields: {missing_schedule_fields}")
                            if installment_count != expected_count:
                                issues.append(f"Installment count mismatch: got {installment_count}, expected {expected_count}")
                            
                            self.log_test(
                                "Get Installment Schedule", 
                                "FAIL", 
                                "; ".join(issues),
                                response_data
                            )
                    else:
                        self.log_test(
                            "Get Installment Schedule", 
                            "FAIL", 
                            "Missing 'schedule' or 'installments' in response",
                            response_data
                        )
                else:
                    self.log_test(
                        "Get Installment Schedule", 
                        "FAIL", 
                        f"Status: {response.status}",
                        response_data
                    )
        except Exception as e:
            self.log_test("Get Installment Schedule", "FAIL", f"Exception: {str(e)}")

    async def test_get_all_installment_schedules(self, token: str):
        """Test GET /api/payroll/installment-schedules - Get all installment schedules (super admin only)"""
        try:
            async with self.session.get(
                f"{API_BASE}/payroll/installment-schedules",
                headers={'Authorization': f'Bearer {token}'}
            ) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    if 'schedules' in response_data:
                        schedules = response_data['schedules']
                        schedule_count = len(schedules)
                        
                        # Validate schedule structure if any exist
                        if schedule_count > 0:
                            first_schedule = schedules[0]
                            required_fields = ['id', 'advance_transaction_id', 'employee_id', 'total_amount', 'installment_amount']
                            missing_fields = [field for field in required_fields if field not in first_schedule]
                            
                            if not missing_fields:
                                self.log_test(
                                    "Get All Installment Schedules", 
                                    "PASS", 
                                    f"Retrieved {schedule_count} installment schedules"
                                )
                            else:
                                self.log_test(
                                    "Get All Installment Schedules", 
                                    "FAIL", 
                                    f"Schedule missing required fields: {missing_fields}",
                                    response_data
                                )
                        else:
                            self.log_test(
                                "Get All Installment Schedules", 
                                "PASS", 
                                "Retrieved 0 installment schedules (empty result is valid)"
                            )
                    else:
                        self.log_test(
                            "Get All Installment Schedules", 
                            "FAIL", 
                            "Missing 'schedules' field in response",
                            response_data
                        )
                else:
                    self.log_test(
                        "Get All Installment Schedules", 
                        "FAIL", 
                        f"Status: {response.status}",
                        response_data
                    )
        except Exception as e:
            self.log_test("Get All Installment Schedules", "FAIL", f"Exception: {str(e)}")

    async def test_data_validation(self, token: str, advance_id: str):
        """Test data validation for installment scheduling"""
        
        # Test 1: Invalid installment amount (negative)
        try:
            invalid_data = {
                "installment_amount": -100.0,
                "number_of_installments": 5,
                "start_date": (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
            }
            
            async with self.session.post(
                f"{API_BASE}/advances/{advance_id}/installments",
                json=invalid_data,
                headers={'Authorization': f'Bearer {token}'}
            ) as response:
                if response.status >= 400:
                    self.log_test("Validation - Negative Amount", "PASS", "Correctly rejected negative installment amount")
                else:
                    self.log_test("Validation - Negative Amount", "FAIL", "Should reject negative installment amount")
        except Exception as e:
            self.log_test("Validation - Negative Amount", "FAIL", f"Exception: {str(e)}")
        
        # Test 2: Invalid number of installments (too high)
        try:
            invalid_data = {
                "installment_amount": 100.0,
                "number_of_installments": 100,  # Should be max 60
                "start_date": (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
            }
            
            async with self.session.post(
                f"{API_BASE}/advances/{advance_id}/installments",
                json=invalid_data,
                headers={'Authorization': f'Bearer {token}'}
            ) as response:
                if response.status >= 400:
                    self.log_test("Validation - Too Many Installments", "PASS", "Correctly rejected >60 installments")
                else:
                    self.log_test("Validation - Too Many Installments", "FAIL", "Should reject >60 installments")
        except Exception as e:
            self.log_test("Validation - Too Many Installments", "FAIL", f"Exception: {str(e)}")
        
        # Test 3: Invalid date format
        try:
            invalid_data = {
                "installment_amount": 100.0,
                "number_of_installments": 5,
                "start_date": "invalid-date"
            }
            
            async with self.session.post(
                f"{API_BASE}/advances/{advance_id}/installments",
                json=invalid_data,
                headers={'Authorization': f'Bearer {token}'}
            ) as response:
                if response.status >= 400:
                    self.log_test("Validation - Invalid Date", "PASS", "Correctly rejected invalid date format")
                else:
                    self.log_test("Validation - Invalid Date", "FAIL", "Should reject invalid date format")
        except Exception as e:
            self.log_test("Validation - Invalid Date", "FAIL", f"Exception: {str(e)}")

    async def test_error_handling(self, token: str):
        """Test error handling scenarios"""
        
        # Test 1: Non-existent advance
        try:
            fake_advance_id = str(uuid.uuid4())
            schedule_data = {
                "installment_amount": 500.0,
                "number_of_installments": 10,
                "start_date": (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
            }
            
            async with self.session.post(
                f"{API_BASE}/advances/{fake_advance_id}/installments",
                json=schedule_data,
                headers={'Authorization': f'Bearer {token}'}
            ) as response:
                if response.status == 404:
                    self.log_test("Error Handling - Non-existent Advance", "PASS", "Correctly returned 404 for non-existent advance")
                else:
                    self.log_test("Error Handling - Non-existent Advance", "FAIL", f"Expected 404, got {response.status}")
        except Exception as e:
            self.log_test("Error Handling - Non-existent Advance", "FAIL", f"Exception: {str(e)}")
        
        # Test 2: Unauthorized access (non-super_admin)
        if 'user' in self.tokens:
            try:
                schedule_data = {
                    "installment_amount": 500.0,
                    "number_of_installments": 10,
                    "start_date": (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
                }
                
                async with self.session.post(
                    f"{API_BASE}/advances/{self.created_advances[0] if self.created_advances else 'test'}/installments",
                    json=schedule_data,
                    headers={'Authorization': f'Bearer {self.tokens["user"]}'}
                ) as response:
                    if response.status == 403:
                        self.log_test("Error Handling - Unauthorized Access", "PASS", "Correctly denied access to regular user")
                    else:
                        self.log_test("Error Handling - Unauthorized Access", "FAIL", f"Expected 403, got {response.status}")
            except Exception as e:
                self.log_test("Error Handling - Unauthorized Access", "FAIL", f"Exception: {str(e)}")

    async def test_duplicate_schedule_prevention(self, token: str, advance_id: str):
        """Test prevention of duplicate schedules for same advance"""
        try:
            schedule_data = {
                "installment_amount": 300.0,
                "number_of_installments": 8,
                "start_date": (date.today() + timedelta(days=60)).strftime("%Y-%m-%d")
            }
            
            async with self.session.post(
                f"{API_BASE}/advances/{advance_id}/installments",
                json=schedule_data,
                headers={'Authorization': f'Bearer {token}'}
            ) as response:
                if response.status >= 400:
                    self.log_test("Duplicate Schedule Prevention", "PASS", "Correctly prevented duplicate schedule creation")
                else:
                    self.log_test("Duplicate Schedule Prevention", "FAIL", "Should prevent duplicate schedule creation")
        except Exception as e:
            self.log_test("Duplicate Schedule Prevention", "FAIL", f"Exception: {str(e)}")

    async def test_integration_workflow(self):
        """Test complete workflow: create advance → approve → create installment schedule"""
        try:
            # Authenticate super admin
            super_admin_token = await self.authenticate_user('super_admin')
            if not super_admin_token:
                self.log_test("Integration Workflow", "FAIL", "Could not authenticate super admin")
                return
            
            # Authenticate regular user
            user_token = await self.authenticate_user('user')
            if not user_token:
                self.log_test("Integration Workflow", "FAIL", "Could not authenticate user")
                return
            
            # Create advance
            advance_id = await self.create_test_advance(super_admin_token)
            if not advance_id:
                self.log_test("Integration Workflow", "FAIL", "Could not create test advance")
                return
            
            # Create installment schedule
            await self.test_create_installment_schedule(super_admin_token, advance_id)
            
            # Get installment schedule details
            await self.test_get_installment_schedule(super_admin_token, advance_id)
            
            # Get all installment schedules
            await self.test_get_all_installment_schedules(super_admin_token)
            
            # Test data validation
            await self.test_data_validation(super_admin_token, advance_id)
            
            # Test error handling
            await self.test_error_handling(super_admin_token)
            
            # Test duplicate prevention
            await self.test_duplicate_schedule_prevention(super_admin_token, advance_id)
            
            self.log_test("Integration Workflow", "PASS", "Completed full integration workflow testing")
            
        except Exception as e:
            self.log_test("Integration Workflow", "FAIL", f"Exception: {str(e)}")

    async def run_all_tests(self):
        """Run all installment scheduling tests"""
        print("🚀 Starting Comprehensive Installment Scheduling System Testing")
        print("=" * 80)
        print()
        
        await self.test_integration_workflow()
        
        # Generate summary
        print("=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%")
        print()
        
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in self.test_results:
                if result['status'] == 'FAIL':
                    print(f"  - {result['test']}: {result['details']}")
            print()
        
        print("🎯 CRITICAL FINDINGS:")
        
        # Check for critical issues
        critical_issues = []
        
        # Check if basic endpoints are working
        endpoint_tests = [r for r in self.test_results if 'Installment Schedule' in r['test']]
        if not any(r['status'] == 'PASS' for r in endpoint_tests):
            critical_issues.append("❌ CRITICAL: No installment scheduling endpoints are working")
        
        # Check authentication
        auth_tests = [r for r in self.test_results if 'Authentication' in r['test']]
        if not any(r['status'] == 'PASS' for r in auth_tests):
            critical_issues.append("❌ CRITICAL: Authentication system not working")
        
        # Check data validation
        validation_tests = [r for r in self.test_results if 'Validation' in r['test']]
        if not any(r['status'] == 'PASS' for r in validation_tests):
            critical_issues.append("⚠️ WARNING: Data validation may not be working properly")
        
        if critical_issues:
            for issue in critical_issues:
                print(f"  {issue}")
        else:
            print("  ✅ No critical issues found - Core installment scheduling functionality is operational")
        
        print()
        print("🔍 DETAILED TEST RESULTS:")
        for result in self.test_results:
            status_emoji = "✅" if result['status'] == "PASS" else "❌"
            print(f"  {status_emoji} {result['test']}")
            if result['details']:
                print(f"      {result['details']}")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': (passed_tests/total_tests*100) if total_tests > 0 else 0,
            'critical_issues': critical_issues,
            'test_results': self.test_results
        }

async def main():
    """Main test execution"""
    async with InstallmentSchedulingTester() as tester:
        results = await tester.run_all_tests()
        return results

if __name__ == "__main__":
    results = asyncio.run(main())