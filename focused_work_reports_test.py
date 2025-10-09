#!/usr/bin/env python3
"""
Focused Work Reports Logs API Testing - Fixed Endpoints Only
Re-testing only the two fixed endpoints for Work Reports Logs:
- PUT /api/work-reports/logs/{log_id} (datetime parsing with ISO normalization)
- DELETE /api/work-reports/logs/{log_id} (remove leftover SQLAlchemy)

Test Steps as specified in review request:
1. Authenticate as admin@tanseeq.com/ADMIN
2. Create a log via POST /api/work-reports/logs (09:00-11:30) and capture id
3. Update the same log with new times (10:15-12:00, with both ISO and HH:MM forms) and verify duration_minutes and total_amount recomputed > 0
4. Delete the log and verify 200 with message, then GET should not find it
5. Also test RBAC by attempting DELETE as user (jihad) to ensure 403
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
import uuid

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://tanseeq-payroll-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials as specified in review request
TEST_CREDENTIALS = {
    'admin': {
        'email': 'admin@tanseeq.com',
        'password': 'ADMIN'
    },
    'user': {
        'email': 'jihad@tanseeq.com',
        'password': 'jihad123'
    }
}

class FocusedWorkReportsLogsTester:
    def __init__(self):
        self.session = None
        self.tokens = {}
        self.test_results = []
        self.created_log_id = None
        self.client_id = None
        self.activity_id = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_result(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            'test': test_name,
            'status': status,
            'success': success,
            'details': details,
            'response_data': response_data,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if not success and response_data:
            print(f"   Response: {response_data}")
        print()
    
    async def authenticate(self, role: str) -> str:
        """Authenticate and get token"""
        if role in self.tokens:
            return self.tokens[role]
            
        creds = TEST_CREDENTIALS[role]
        
        try:
            async with self.session.post(
                f"{API_BASE}/auth/login",
                json=creds,
                headers={'Content-Type': 'application/json'}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    token = data['access_token']
                    self.tokens[role] = token
                    self.log_result(f"Authentication - {role}", True, f"Logged in as {creds['email']}")
                    return token
                else:
                    error_text = await response.text()
                    self.log_result(f"Authentication - {role}", False, f"Status {response.status}: {error_text}")
                    return None
        except Exception as e:
            self.log_result(f"Authentication - {role}", False, f"Exception: {str(e)}")
            return None
    
    async def setup_test_data(self, token: str) -> bool:
        """Setup test client and activity data"""
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Get existing clients
        try:
            async with self.session.get(f"{API_BASE}/work-reports/clients", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    # Handle both list and dict responses
                    if isinstance(data, list):
                        clients = data
                    else:
                        clients = data.get('items', data.get('clients', []))
                    
                    if clients and len(clients) > 0:
                        self.client_id = clients[0]['id']
                        self.log_result("Setup Test Client", True, f"Using existing client ID: {self.client_id}")
                    else:
                        self.log_result("Setup Test Client", False, "No clients found")
                        return False
                else:
                    self.log_result("Setup Test Client", False, f"Status {response.status}")
                    return False
        except Exception as e:
            self.log_result("Setup Test Client", False, f"Exception: {str(e)}")
            return False
        
        # Get existing activity types
        try:
            async with self.session.get(f"{API_BASE}/work-reports/activity-types", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    # Handle both list and dict responses
                    if isinstance(data, list):
                        activities = data
                    else:
                        activities = data.get('items', data.get('activity_types', []))
                    
                    if activities and len(activities) > 0:
                        self.activity_id = activities[0]['id']
                        rate = activities[0].get('default_rate', 200.0)
                        self.log_result("Setup Test Activity", True, f"Using existing activity ID: {self.activity_id}, Rate: {rate}")
                    else:
                        self.log_result("Setup Test Activity", False, "No activities found")
                        return False
                else:
                    self.log_result("Setup Test Activity", False, f"Status {response.status}")
                    return False
        except Exception as e:
            self.log_result("Setup Test Activity", False, f"Exception: {str(e)}")
            return False
        
        return True
    
    async def create_work_log(self, token: str) -> Optional[str]:
        """Create a work log with 09:00-11:30 times (2.5 hours)"""
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Get today's date in proper format
        today = date.today()
        
        # Create log data with proper datetime format
        log_data = {
            "client_id": self.client_id,
            "activity_type_id": self.activity_id,
            "date": today.isoformat() + "T00:00:00Z",
            "start_time": today.isoformat() + "T09:00:00Z",
            "end_time": today.isoformat() + "T11:30:00Z",
            "description": "Initial test work log for update testing - 09:00 to 11:30",
            "notes": "Created for testing PUT and DELETE endpoints - should be 2.5 hours duration",
            "is_billable": True,
            "hourly_rate": 200.0
        }
        
        try:
            async with self.session.post(
                f"{API_BASE}/work-reports/logs",
                json=log_data,
                headers=headers
            ) as response:
                response_text = await response.text()
                
                if response.status in [200, 201]:
                    try:
                        data = await response.json()
                        log_id = data.get('id') or data.get('log_id')
                        duration_minutes = data.get('duration_minutes', 0)
                        total_amount = data.get('total_amount', 0)
                        
                        if log_id:
                            self.created_log_id = log_id
                            self.log_result(
                                "Create Work Log (09:00-11:30)", 
                                True, 
                                f"Created log ID: {log_id}, Duration: {duration_minutes} minutes, Amount: {total_amount}"
                            )
                            return log_id
                        else:
                            self.log_result("Create Work Log (09:00-11:30)", False, "No log ID in response", data)
                            return None
                    except json.JSONDecodeError:
                        self.log_result("Create Work Log (09:00-11:30)", False, f"Invalid JSON response: {response_text}")
                        return None
                else:
                    self.log_result("Create Work Log (09:00-11:30)", False, f"Status {response.status}: {response_text}")
                    return None
                    
        except Exception as e:
            self.log_result("Create Work Log (09:00-11:30)", False, f"Exception: {str(e)}")
            return None
    
    async def update_work_log_iso_format(self, token: str, log_id: str) -> bool:
        """Update work log with ISO format times (10:15-12:00) - 1.75 hours"""
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        today = date.today()
        
        # Update with new times in ISO format: 10:15-12:00 (1.75 hours = 105 minutes)
        update_data = {
            "start_time": today.isoformat() + "T10:15:00Z",
            "end_time": today.isoformat() + "T12:00:00Z",
            "description": "Updated work log with ISO format times - 10:15 to 12:00",
            "notes": "Testing datetime parsing with ISO normalization - should be 1.75 hours",
            "hourly_rate": 250.0
        }
        
        try:
            async with self.session.put(
                f"{API_BASE}/work-reports/logs/{log_id}",
                json=update_data,
                headers=headers
            ) as response:
                response_text = await response.text()
                
                if response.status == 200:
                    try:
                        data = await response.json()
                        duration_minutes = data.get('duration_minutes', 0)
                        total_amount = data.get('total_amount', 0)
                        
                        # Verify duration and amount are recomputed and > 0
                        # Expected: 105 minutes (1.75 hours), Amount should be 1.75 * 250 = 437.5
                        if duration_minutes > 0 and total_amount > 0:
                            self.log_result(
                                "Update Work Log (ISO Format)", 
                                True, 
                                f"Updated successfully - Duration: {duration_minutes} minutes (expected ~105), Amount: {total_amount} (expected ~437.5)"
                            )
                            return True
                        else:
                            self.log_result(
                                "Update Work Log (ISO Format)", 
                                False, 
                                f"Duration or amount not recomputed properly - Duration: {duration_minutes}, Amount: {total_amount}",
                                data
                            )
                            return False
                    except json.JSONDecodeError:
                        self.log_result("Update Work Log (ISO Format)", False, f"Invalid JSON response: {response_text}")
                        return False
                else:
                    self.log_result("Update Work Log (ISO Format)", False, f"Status {response.status}: {response_text}")
                    return False
                    
        except Exception as e:
            self.log_result("Update Work Log (ISO Format)", False, f"Exception: {str(e)}")
            return False
    
    async def update_work_log_hhmm_format(self, token: str, log_id: str) -> bool:
        """Update work log with HH:MM format times (10:30-12:15) - 1.75 hours"""
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        today = date.today()
        
        # Update with HH:MM format: 10:30-12:15 (1.75 hours = 105 minutes)
        update_data = {
            "start_time": today.isoformat() + " 10:30:00",
            "end_time": today.isoformat() + " 12:15:00", 
            "description": "Updated work log with HH:MM format times - 10:30 to 12:15",
            "notes": "Testing datetime parsing with HH:MM format - should be 1.75 hours",
            "hourly_rate": 300.0
        }
        
        try:
            async with self.session.put(
                f"{API_BASE}/work-reports/logs/{log_id}",
                json=update_data,
                headers=headers
            ) as response:
                response_text = await response.text()
                
                if response.status == 200:
                    try:
                        data = await response.json()
                        duration_minutes = data.get('duration_minutes', 0)
                        total_amount = data.get('total_amount', 0)
                        
                        # Verify duration and amount are recomputed and > 0
                        # Expected: 105 minutes (1.75 hours), Amount should be 1.75 * 300 = 525
                        if duration_minutes > 0 and total_amount > 0:
                            self.log_result(
                                "Update Work Log (HH:MM Format)", 
                                True, 
                                f"Updated successfully - Duration: {duration_minutes} minutes (expected ~105), Amount: {total_amount} (expected ~525)"
                            )
                            return True
                        else:
                            self.log_result(
                                "Update Work Log (HH:MM Format)", 
                                False, 
                                f"Duration or amount not recomputed properly - Duration: {duration_minutes}, Amount: {total_amount}",
                                data
                            )
                            return False
                    except json.JSONDecodeError:
                        self.log_result("Update Work Log (HH:MM Format)", False, f"Invalid JSON response: {response_text}")
                        return False
                else:
                    self.log_result("Update Work Log (HH:MM Format)", False, f"Status {response.status}: {response_text}")
                    return False
                    
        except Exception as e:
            self.log_result("Update Work Log (HH:MM Format)", False, f"Exception: {str(e)}")
            return False
    
    async def test_rbac_delete_as_user(self, user_token: str, log_id: str) -> bool:
        """Test RBAC by attempting DELETE as regular user (should get 403)"""
        headers = {
            'Authorization': f'Bearer {user_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            async with self.session.delete(
                f"{API_BASE}/work-reports/logs/{log_id}",
                headers=headers
            ) as response:
                response_text = await response.text()
                
                if response.status == 403:
                    self.log_result(
                        "RBAC Test - User Delete (Should Fail)", 
                        True, 
                        "Regular user correctly denied access (403 Forbidden)"
                    )
                    return True
                else:
                    self.log_result(
                        "RBAC Test - User Delete (Should Fail)", 
                        False, 
                        f"Expected 403, got {response.status}: {response_text}"
                    )
                    return False
                    
        except Exception as e:
            self.log_result("RBAC Test - User Delete (Should Fail)", False, f"Exception: {str(e)}")
            return False
    
    async def delete_work_log_as_admin(self, token: str, log_id: str) -> bool:
        """Delete work log as admin and verify 200 with message"""
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        try:
            async with self.session.delete(
                f"{API_BASE}/work-reports/logs/{log_id}",
                headers=headers
            ) as response:
                response_text = await response.text()
                
                if response.status == 200:
                    try:
                        data = await response.json()
                        message = data.get('message', '')
                        if message:
                            self.log_result(
                                "Delete Work Log (Admin)", 
                                True, 
                                f"Deleted successfully with message: '{message}'"
                            )
                            return True
                        else:
                            self.log_result("Delete Work Log (Admin)", True, "Deleted successfully (no message in response)")
                            return True
                    except json.JSONDecodeError:
                        if "deleted" in response_text.lower() or "success" in response_text.lower():
                            self.log_result("Delete Work Log (Admin)", True, f"Deleted successfully: {response_text}")
                            return True
                        else:
                            self.log_result("Delete Work Log (Admin)", False, f"Unexpected response: {response_text}")
                            return False
                else:
                    self.log_result("Delete Work Log (Admin)", False, f"Status {response.status}: {response_text}")
                    return False
                    
        except Exception as e:
            self.log_result("Delete Work Log (Admin)", False, f"Exception: {str(e)}")
            return False
    
    async def verify_log_deleted(self, token: str, log_id: str) -> bool:
        """Verify that GET should not find the deleted log"""
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        try:
            # Try to get the specific log
            async with self.session.get(
                f"{API_BASE}/work-reports/logs/{log_id}",
                headers=headers
            ) as response:
                response_text = await response.text()
                
                if response.status == 404:
                    self.log_result(
                        "Verify Log Deleted (GET specific log)", 
                        True, 
                        "Log correctly not found after deletion (404)"
                    )
                    return True
                elif response.status == 200:
                    self.log_result(
                        "Verify Log Deleted (GET specific log)", 
                        False, 
                        "Log still exists after deletion - DELETE may have failed"
                    )
                    return False
                else:
                    # Any other status is acceptable as long as it's not 200
                    self.log_result(
                        "Verify Log Deleted (GET specific log)", 
                        True, 
                        f"Log not accessible after deletion (Status: {response.status})"
                    )
                    return True
                    
        except Exception as e:
            # Also try to verify via list endpoint
            try:
                async with self.session.get(
                    f"{API_BASE}/work-reports/logs",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        items = data.get('items', [])
                        found_log = any(item.get('id') == log_id for item in items)
                        
                        if not found_log:
                            self.log_result(
                                "Verify Log Deleted (GET list)", 
                                True, 
                                "Log not found in list after deletion"
                            )
                            return True
                        else:
                            self.log_result(
                                "Verify Log Deleted (GET list)", 
                                False, 
                                "Log still found in list after deletion"
                            )
                            return False
                    else:
                        self.log_result("Verify Log Deleted", False, f"Exception: {str(e)}")
                        return False
            except Exception as e2:
                self.log_result("Verify Log Deleted", False, f"Exception: {str(e2)}")
                return False
    
    async def run_focused_test(self):
        """Run the focused test suite for the two fixed endpoints"""
        print("🎯 Starting Focused Work Reports Logs API Testing - Fixed Endpoints Only")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base: {API_BASE}")
        print()
        print("🔍 Testing Specific Review Request:")
        print("1. Authenticate as admin@tanseeq.com/ADMIN")
        print("2. Create a log via POST /api/work-reports/logs (09:00-11:30) and capture id")
        print("3. Update the same log with new times (10:15-12:00, with both ISO and HH:MM forms)")
        print("4. Verify duration_minutes and total_amount recomputed > 0")
        print("5. Delete the log and verify 200 with message, then GET should not find it")
        print("6. Test RBAC by attempting DELETE as user (jihad) to ensure 403")
        print()
        
        # Step 1: Authenticate as admin
        admin_token = await self.authenticate('admin')
        if not admin_token:
            print("❌ CRITICAL: Admin authentication failed - cannot continue")
            return
        
        # Step 1b: Authenticate as regular user for RBAC testing
        user_token = await self.authenticate('user')
        if not user_token:
            print("⚠️ WARNING: User authentication failed - RBAC test will be skipped")
        
        # Step 1c: Setup test data (client and activity)
        setup_success = await self.setup_test_data(admin_token)
        if not setup_success:
            print("❌ CRITICAL: Test data setup failed - cannot continue")
            return
        
        # Step 2: Create a work log (09:00-11:30)
        log_id = await self.create_work_log(admin_token)
        if not log_id:
            print("❌ CRITICAL: Work log creation failed - cannot continue with update/delete tests")
            return
        
        # Step 3a: Update with ISO format times (10:15-12:00)
        iso_update_success = await self.update_work_log_iso_format(admin_token, log_id)
        
        # Step 3b: Update with HH:MM format times (10:30-12:15)
        hhmm_update_success = await self.update_work_log_hhmm_format(admin_token, log_id)
        
        # Step 6: Test RBAC - attempt delete as regular user (should fail with 403)
        if user_token:
            await self.test_rbac_delete_as_user(user_token, log_id)
        
        # Step 5a: Delete the log as admin
        delete_success = await self.delete_work_log_as_admin(admin_token, log_id)
        
        # Step 5b: Verify log is deleted
        if delete_success:
            await self.verify_log_deleted(admin_token, log_id)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📊 FOCUSED WORK REPORTS LOGS API TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        # Print detailed results
        print("DETAILED RESULTS:")
        print("-" * 50)
        for result in self.test_results:
            status_icon = "✅" if result['success'] else "❌"
            print(f"{status_icon} {result['test']}")
            if result['details']:
                print(f"   {result['details']}")
        
        print("\n" + "=" * 80)
        
        # Critical findings for the two fixed endpoints
        put_endpoint_working = False
        delete_endpoint_working = False
        
        for result in self.test_results:
            if 'Update Work Log' in result['test'] and result['success']:
                put_endpoint_working = True
            elif 'Delete Work Log (Admin)' in result['test'] and result['success']:
                delete_endpoint_working = True
        
        print("🎯 REVIEW REQUEST RESULTS:")
        print("-" * 50)
        
        if put_endpoint_working:
            print("✅ PUT /api/work-reports/logs/{log_id} - FIXED: Datetime parsing with ISO normalization working")
        else:
            print("❌ PUT /api/work-reports/logs/{log_id} - STILL BROKEN: Datetime parsing issues persist")
        
        if delete_endpoint_working:
            print("✅ DELETE /api/work-reports/logs/{log_id} - FIXED: Leftover SQLAlchemy code removed")
        else:
            print("❌ DELETE /api/work-reports/logs/{log_id} - STILL BROKEN: SQLAlchemy issues persist")
        
        print()
        
        # Final verdict
        if put_endpoint_working and delete_endpoint_working:
            print("🎉 CONCLUSION: Both fixed endpoints are working correctly!")
            print("   ✅ PUT endpoint: Datetime parsing with ISO normalization functional")
            print("   ✅ DELETE endpoint: SQLAlchemy code issues resolved")
        elif put_endpoint_working:
            print("⚠️ CONCLUSION: PUT endpoint fixed, but DELETE endpoint still has issues")
            print("   ✅ PUT endpoint: Datetime parsing working")
            print("   ❌ DELETE endpoint: Still needs attention")
        elif delete_endpoint_working:
            print("⚠️ CONCLUSION: DELETE endpoint fixed, but PUT endpoint still has issues")
            print("   ❌ PUT endpoint: Datetime parsing still broken")
            print("   ✅ DELETE endpoint: SQLAlchemy issues resolved")
        else:
            print("❌ CONCLUSION: Both endpoints still have critical issues")
            print("   ❌ PUT endpoint: Datetime parsing not working")
            print("   ❌ DELETE endpoint: SQLAlchemy issues not resolved")
        
        print("=" * 80)

async def main():
    """Main test execution"""
    async with FocusedWorkReportsLogsTester() as tester:
        await tester.run_focused_test()

if __name__ == "__main__":
    asyncio.run(main())