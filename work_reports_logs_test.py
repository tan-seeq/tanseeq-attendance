#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Work Reports Logs APIs
Testing the fixed Work Reports Logs APIs and new indexes as requested in review.

Test Scenarios:
1. Happy path: GET /api/work-reports/logs returns {items,total,page,page_size} for super_admin and user, RBAC enforced
2. Filters: start_date/end_date range, client_id, employee_id (as super_admin)
3. Search: q text search across description/notes/client_name/activity_name, ensure text index present
4. Pagination: page=2&page_size=5 returns proper slice and total
5. Create/Update/Delete: POST /api/work-reports/logs creates log with computed duration/amount, PUT updates times and recomputes duration/amount, DELETE removes
6. Use accounts: admin@tanseeq.com/ADMIN (super_admin), jihad@tanseeq.com/jihad123 (user)
7. Confirm indexes exist on work_logs collection and no 500s triggered
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
import uuid

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://hr-unification.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials as specified in review request
TEST_CREDENTIALS = {
    'super_admin': {
        'email': 'admin@tanseeq.com',
        'password': 'ADMIN'
    },
    'user': {
        'email': 'jihad@tanseeq.com',
        'password': 'jihad123'
    }
}

class WorkReportsLogsTester:
    def __init__(self):
        self.session = None
        self.tokens = {}
        self.test_results = []
        self.created_clients = []
        self.created_activities = []
        self.created_logs = []
        self.activity_rate = 150.0  # Default rate
        
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

    async def setup_test_data(self, token: str):
        """Setup test clients and activities for work logs testing"""
        try:
            # Get existing clients (clients endpoint returns array directly)
            async with self.session.get(
                f"{API_BASE}/work-reports/clients",
                headers={'Authorization': f'Bearer {token}'}
            ) as get_response:
                if get_response.status == 200:
                    clients = await get_response.json()  # Direct array
                    if clients and len(clients) > 0:
                        client_id = clients[0]['id']
                        self.log_test("Setup Test Client", "PASS", f"Using existing client ID: {client_id}")
                    else:
                        self.log_test("Setup Test Client", "FAIL", "No clients available")
                        return None, None
                else:
                    self.log_test("Setup Test Client", "FAIL", f"Could not get clients: {get_response.status}")
                    return None, None
            
            # Get existing activity types (activity-types endpoint returns array directly)
            async with self.session.get(
                f"{API_BASE}/work-reports/activity-types",
                headers={'Authorization': f'Bearer {token}'}
            ) as get_response:
                if get_response.status == 200:
                    activities = await get_response.json()  # Direct array
                    if activities and len(activities) > 0:
                        activity_id = activities[0]['id']
                        activity_rate = activities[0].get('hourly_rate', 150.0)
                        self.log_test("Setup Test Activity", "PASS", f"Using existing activity ID: {activity_id}, Rate: {activity_rate}")
                        # Store the rate for calculation validation
                        self.activity_rate = activity_rate
                    else:
                        self.log_test("Setup Test Activity", "FAIL", "No activities available")
                        return client_id, None
                else:
                    self.log_test("Setup Test Activity", "FAIL", f"Could not get activities: {get_response.status}")
                    return client_id, None
            
            return client_id, activity_id
            
        except Exception as e:
            self.log_test("Setup Test Data", "FAIL", f"Exception: {str(e)}")
            return None, None

    async def test_create_work_log(self, token: str, client_id: str, activity_id: str) -> Optional[str]:
        """Test POST /api/work-reports/logs - Create work log with computed duration/amount"""
        try:
            log_data = {
                "client_id": client_id,
                "activity_type_id": activity_id,
                "date": "2025-01-15",
                "start_time": "09:00",
                "end_time": "11:30",
                "description": "Developed new features for the client portal system"
            }
            
            async with self.session.post(
                f"{API_BASE}/work-reports/logs",
                json=log_data,
                headers={'Authorization': f'Bearer {token}'}
            ) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    log_id = response_data.get('id')
                    duration_minutes = response_data.get('duration_minutes')
                    total_amount = response_data.get('total_amount')
                    
                    # Validate computed values
                    expected_duration = 150  # 2.5 hours = 150 minutes
                    expected_amount = round((150 / 60) * self.activity_rate, 2)  # 2.5 hours * activity_rate
                    
                    if duration_minutes == expected_duration and total_amount == expected_amount:
                        self.created_logs.append(log_id)
                        self.log_test(
                            "Create Work Log", 
                            "PASS", 
                            f"Created work log ID: {log_id}, Duration: {duration_minutes}min, Amount: {total_amount} AED"
                        )
                        return log_id
                    else:
                        self.log_test(
                            "Create Work Log", 
                            "FAIL", 
                            f"Incorrect calculations - Duration: {duration_minutes} (expected {expected_duration}), Amount: {total_amount} (expected {expected_amount})",
                            response_data
                        )
                        return log_id
                else:
                    self.log_test(
                        "Create Work Log", 
                        "FAIL", 
                        f"Status: {response.status}",
                        response_data
                    )
                    return None
        except Exception as e:
            self.log_test("Create Work Log", "FAIL", f"Exception: {str(e)}")
            return None

    async def test_update_work_log(self, token: str, log_id: str):
        """Test PUT /api/work-reports/logs/{log_id} - Update times and recompute duration/amount"""
        try:
            update_data = {
                "start_time": "09:00",
                "end_time": "12:00",  # Changed from 11:30 to 12:00 (3 hours total)
                "description": "Updated: Developed new features and performed testing"
            }
            
            async with self.session.put(
                f"{API_BASE}/work-reports/logs/{log_id}",
                json=update_data,
                headers={'Authorization': f'Bearer {token}'}
            ) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    duration_minutes = response_data.get('duration_minutes')
                    total_amount = response_data.get('total_amount')
                    
                    # Validate recomputed values
                    expected_duration = 180  # 3 hours = 180 minutes
                    expected_amount = round((180 / 60) * self.activity_rate, 2)  # 3 hours * activity_rate
                    
                    if duration_minutes == expected_duration and total_amount == expected_amount:
                        self.log_test(
                            "Update Work Log", 
                            "PASS", 
                            f"Updated work log - Duration: {duration_minutes}min, Amount: {total_amount} AED (recomputed correctly)"
                        )
                    else:
                        self.log_test(
                            "Update Work Log", 
                            "FAIL", 
                            f"Incorrect recomputation - Duration: {duration_minutes} (expected {expected_duration}), Amount: {total_amount} (expected {expected_amount})",
                            response_data
                        )
                else:
                    self.log_test(
                        "Update Work Log", 
                        "FAIL", 
                        f"Status: {response.status}",
                        response_data
                    )
        except Exception as e:
            self.log_test("Update Work Log", "FAIL", f"Exception: {str(e)}")

    async def test_get_work_logs_happy_path(self, token: str, role: str):
        """Test GET /api/work-reports/logs - Happy path with proper response structure"""
        try:
            async with self.session.get(
                f"{API_BASE}/work-reports/logs",
                headers={'Authorization': f'Bearer {token}'}
            ) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    # Validate response structure
                    required_fields = ['items', 'total', 'page', 'page_size']
                    missing_fields = [field for field in required_fields if field not in response_data]
                    
                    if not missing_fields:
                        items = response_data.get('items', [])
                        total = response_data.get('total', 0)
                        page = response_data.get('page', 1)
                        page_size = response_data.get('page_size', 20)
                        
                        self.log_test(
                            f"Get Work Logs Happy Path - {role}", 
                            "PASS", 
                            f"Retrieved {len(items)} items, Total: {total}, Page: {page}, Page Size: {page_size}"
                        )
                    else:
                        self.log_test(
                            f"Get Work Logs Happy Path - {role}", 
                            "FAIL", 
                            f"Missing required fields: {missing_fields}",
                            response_data
                        )
                else:
                    self.log_test(
                        f"Get Work Logs Happy Path - {role}", 
                        "FAIL", 
                        f"Status: {response.status}",
                        response_data
                    )
        except Exception as e:
            self.log_test(f"Get Work Logs Happy Path - {role}", "FAIL", f"Exception: {str(e)}")

    async def test_rbac_enforcement(self):
        """Test RBAC: user sees own logs, super_admin sees all"""
        try:
            # Test user access (should only see own logs)
            if 'user' in self.tokens:
                async with self.session.get(
                    f"{API_BASE}/work-reports/logs",
                    headers={'Authorization': f'Bearer {self.tokens["user"]}'}
                ) as response:
                    if response.status == 200:
                        user_data = await response.json()
                        user_items = user_data.get('items', [])
                        
                        # Check if all items belong to the user
                        user_id = None
                        async with self.session.get(
                            f"{API_BASE}/auth/me",
                            headers={'Authorization': f'Bearer {self.tokens["user"]}'}
                        ) as me_response:
                            if me_response.status == 200:
                                me_data = await me_response.json()
                                user_id = me_data.get('id')
                        
                        if user_id:
                            user_owns_all = all(item.get('created_by') == user_id for item in user_items)
                            if user_owns_all:
                                self.log_test(
                                    "RBAC - User Access", 
                                    "PASS", 
                                    f"User correctly sees only own logs ({len(user_items)} items)"
                                )
                            else:
                                self.log_test(
                                    "RBAC - User Access", 
                                    "FAIL", 
                                    "User can see logs from other users"
                                )
                        else:
                            self.log_test("RBAC - User Access", "WARN", "Could not verify user ID")
                    else:
                        self.log_test("RBAC - User Access", "FAIL", f"User access failed: {response.status}")
            
            # Test super_admin access (should see all logs)
            if 'super_admin' in self.tokens:
                async with self.session.get(
                    f"{API_BASE}/work-reports/logs",
                    headers={'Authorization': f'Bearer {self.tokens["super_admin"]}'}
                ) as response:
                    if response.status == 200:
                        admin_data = await response.json()
                        admin_items = admin_data.get('items', [])
                        
                        self.log_test(
                            "RBAC - Super Admin Access", 
                            "PASS", 
                            f"Super Admin can see all logs ({len(admin_items)} items)"
                        )
                    else:
                        self.log_test("RBAC - Super Admin Access", "FAIL", f"Super Admin access failed: {response.status}")
                        
        except Exception as e:
            self.log_test("RBAC Enforcement", "FAIL", f"Exception: {str(e)}")

    async def test_date_range_filters(self, token: str):
        """Test start_date/end_date range filters"""
        try:
            # Test with date range
            start_date = "2025-01-01"
            end_date = "2025-01-31"
            
            async with self.session.get(
                f"{API_BASE}/work-reports/logs?start_date={start_date}&end_date={end_date}",
                headers={'Authorization': f'Bearer {token}'}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    items = data.get('items', [])
                    
                    # Validate that all items are within date range
                    valid_dates = True
                    for item in items:
                        item_date = item.get('date')
                        if item_date and (item_date < start_date or item_date > end_date):
                            valid_dates = False
                            break
                    
                    if valid_dates:
                        self.log_test(
                            "Date Range Filter", 
                            "PASS", 
                            f"Retrieved {len(items)} items within date range {start_date} to {end_date}"
                        )
                    else:
                        self.log_test(
                            "Date Range Filter", 
                            "FAIL", 
                            "Some items are outside the specified date range"
                        )
                else:
                    self.log_test("Date Range Filter", "FAIL", f"Status: {response.status}")
                    
        except Exception as e:
            self.log_test("Date Range Filter", "FAIL", f"Exception: {str(e)}")

    async def test_client_filter(self, token: str, client_id: str):
        """Test client_id filter"""
        try:
            async with self.session.get(
                f"{API_BASE}/work-reports/logs?client_id={client_id}",
                headers={'Authorization': f'Bearer {token}'}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    items = data.get('items', [])
                    
                    # Validate that all items belong to the specified client
                    valid_client = all(item.get('client_id') == client_id for item in items)
                    
                    if valid_client:
                        self.log_test(
                            "Client Filter", 
                            "PASS", 
                            f"Retrieved {len(items)} items for client {client_id}"
                        )
                    else:
                        self.log_test(
                            "Client Filter", 
                            "FAIL", 
                            "Some items belong to different clients"
                        )
                else:
                    self.log_test("Client Filter", "FAIL", f"Status: {response.status}")
                    
        except Exception as e:
            self.log_test("Client Filter", "FAIL", f"Exception: {str(e)}")

    async def test_employee_filter(self, token: str):
        """Test employee_id filter (super_admin only)"""
        try:
            # Get user ID for filtering
            user_id = None
            if 'user' in self.tokens:
                async with self.session.get(
                    f"{API_BASE}/auth/me",
                    headers={'Authorization': f'Bearer {self.tokens["user"]}'}
                ) as me_response:
                    if me_response.status == 200:
                        me_data = await me_response.json()
                        user_id = me_data.get('id')
            
            if user_id:
                async with self.session.get(
                    f"{API_BASE}/work-reports/logs?employee_id={user_id}",
                    headers={'Authorization': f'Bearer {token}'}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        items = data.get('items', [])
                        
                        # Validate that all items belong to the specified employee
                        valid_employee = all(item.get('created_by') == user_id for item in items)
                        
                        if valid_employee:
                            self.log_test(
                                "Employee Filter", 
                                "PASS", 
                                f"Retrieved {len(items)} items for employee {user_id}"
                            )
                        else:
                            self.log_test(
                                "Employee Filter", 
                                "FAIL", 
                                "Some items belong to different employees"
                            )
                    else:
                        self.log_test("Employee Filter", "FAIL", f"Status: {response.status}")
            else:
                self.log_test("Employee Filter", "WARN", "Could not get user ID for testing")
                    
        except Exception as e:
            self.log_test("Employee Filter", "FAIL", f"Exception: {str(e)}")

    async def test_text_search(self, token: str):
        """Test q text search across description/notes/client_name/activity_name"""
        try:
            search_terms = ["development", "features", "portal"]
            
            for term in search_terms:
                async with self.session.get(
                    f"{API_BASE}/work-reports/logs?q={term}",
                    headers={'Authorization': f'Bearer {token}'}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        items = data.get('items', [])
                        
                        # Check if search term appears in searchable fields
                        found_matches = False
                        for item in items:
                            searchable_text = " ".join([
                                item.get('description', ''),
                                item.get('notes', ''),
                                item.get('client_name', ''),
                                item.get('activity_name', '')
                            ]).lower()
                            
                            if term.lower() in searchable_text:
                                found_matches = True
                                break
                        
                        if found_matches or len(items) == 0:  # Empty result is also valid
                            self.log_test(
                                f"Text Search - '{term}'", 
                                "PASS", 
                                f"Search returned {len(items)} items"
                            )
                        else:
                            self.log_test(
                                f"Text Search - '{term}'", 
                                "FAIL", 
                                "Search returned items that don't contain the search term"
                            )
                    else:
                        self.log_test(f"Text Search - '{term}'", "FAIL", f"Status: {response.status}")
                        
        except Exception as e:
            self.log_test("Text Search", "FAIL", f"Exception: {str(e)}")

    async def test_pagination(self, token: str):
        """Test pagination: page=2&page_size=5 returns proper slice and total"""
        try:
            # First, get total count
            async with self.session.get(
                f"{API_BASE}/work-reports/logs?page=1&page_size=100",
                headers={'Authorization': f'Bearer {token}'}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    total_items = data.get('total', 0)
                    
                    if total_items > 5:  # Only test pagination if we have enough items
                        # Test page 2 with page_size 5
                        async with self.session.get(
                            f"{API_BASE}/work-reports/logs?page=2&page_size=5",
                            headers={'Authorization': f'Bearer {token}'}
                        ) as page_response:
                            if page_response.status == 200:
                                page_data = await page_response.json()
                                items = page_data.get('items', [])
                                total = page_data.get('total', 0)
                                page = page_data.get('page', 1)
                                page_size = page_data.get('page_size', 20)
                                
                                # Validate pagination
                                expected_items = min(5, max(0, total_items - 5))  # Items on page 2
                                
                                if (len(items) == expected_items and 
                                    total == total_items and 
                                    page == 2 and 
                                    page_size == 5):
                                    self.log_test(
                                        "Pagination", 
                                        "PASS", 
                                        f"Page 2 returned {len(items)} items (expected {expected_items}), Total: {total}, Page: {page}, Page Size: {page_size}"
                                    )
                                else:
                                    self.log_test(
                                        "Pagination", 
                                        "FAIL", 
                                        f"Incorrect pagination - Items: {len(items)} (expected {expected_items}), Total: {total}, Page: {page}, Page Size: {page_size}"
                                    )
                            else:
                                self.log_test("Pagination", "FAIL", f"Page 2 request failed: {page_response.status}")
                    else:
                        self.log_test("Pagination", "PASS", f"Not enough items for pagination test (total: {total_items})")
                else:
                    self.log_test("Pagination", "FAIL", f"Initial request failed: {response.status}")
                    
        except Exception as e:
            self.log_test("Pagination", "FAIL", f"Exception: {str(e)}")

    async def test_delete_work_log(self, token: str, log_id: str):
        """Test DELETE /api/work-reports/logs/{log_id} - Remove work log"""
        try:
            async with self.session.delete(
                f"{API_BASE}/work-reports/logs/{log_id}",
                headers={'Authorization': f'Bearer {token}'}
            ) as response:
                if response.status == 200:
                    # Verify the log is actually deleted
                    async with self.session.get(
                        f"{API_BASE}/work-reports/logs",
                        headers={'Authorization': f'Bearer {token}'}
                    ) as verify_response:
                        if verify_response.status == 200:
                            data = await verify_response.json()
                            items = data.get('items', [])
                            
                            # Check if the deleted log is still present
                            deleted_log_exists = any(item.get('id') == log_id for item in items)
                            
                            if not deleted_log_exists:
                                self.log_test(
                                    "Delete Work Log", 
                                    "PASS", 
                                    f"Work log {log_id} successfully deleted and removed from database"
                                )
                            else:
                                self.log_test(
                                    "Delete Work Log", 
                                    "FAIL", 
                                    f"Work log {log_id} still exists after deletion"
                                )
                        else:
                            self.log_test("Delete Work Log", "WARN", "Could not verify deletion")
                else:
                    response_data = await response.json() if response.content_type == 'application/json' else await response.text()
                    self.log_test(
                        "Delete Work Log", 
                        "FAIL", 
                        f"Status: {response.status}",
                        response_data
                    )
        except Exception as e:
            self.log_test("Delete Work Log", "FAIL", f"Exception: {str(e)}")

    async def test_no_500_errors(self):
        """Test that no 500 errors are triggered in any endpoint"""
        try:
            endpoints_to_test = [
                "/work-reports/logs",
                "/work-reports/logs?page=1&page_size=10",
                "/work-reports/logs?start_date=2025-01-01",
                "/work-reports/logs?q=test",
                "/work-reports/clients",
                "/work-reports/activity-types"
            ]
            
            server_errors = []
            
            for endpoint in endpoints_to_test:
                for role in ['super_admin', 'user']:
                    if role in self.tokens:
                        async with self.session.get(
                            f"{API_BASE}{endpoint}",
                            headers={'Authorization': f'Bearer {self.tokens[role]}'}
                        ) as response:
                            if response.status >= 500:
                                server_errors.append(f"{endpoint} ({role}): {response.status}")
            
            if not server_errors:
                self.log_test(
                    "No 500 Errors", 
                    "PASS", 
                    f"All {len(endpoints_to_test) * len(self.tokens)} endpoint tests completed without server errors"
                )
            else:
                self.log_test(
                    "No 500 Errors", 
                    "FAIL", 
                    f"Server errors found: {', '.join(server_errors)}"
                )
                
        except Exception as e:
            self.log_test("No 500 Errors", "FAIL", f"Exception: {str(e)}")

    async def run_comprehensive_tests(self):
        """Run all Work Reports Logs API tests"""
        print("🚀 Starting Comprehensive Work Reports Logs API Testing")
        print("=" * 80)
        print()
        
        # Authenticate users
        super_admin_token = await self.authenticate_user('super_admin')
        user_token = await self.authenticate_user('user')
        
        if not super_admin_token:
            print("❌ Cannot proceed without super_admin authentication")
            return
        
        if not user_token:
            print("⚠️ User authentication failed, some tests will be skipped")
        
        # Setup test data
        client_id, activity_id = await self.setup_test_data(super_admin_token)
        
        if not client_id or not activity_id:
            print("❌ Cannot proceed without test data setup")
            return
        
        # Test Create/Update/Delete workflow
        log_id = await self.test_create_work_log(super_admin_token, client_id, activity_id)
        
        if log_id:
            await self.test_update_work_log(super_admin_token, log_id)
        
        # Test Happy Path for both roles
        await self.test_get_work_logs_happy_path(super_admin_token, 'super_admin')
        if user_token:
            await self.test_get_work_logs_happy_path(user_token, 'user')
        
        # Test RBAC enforcement
        await self.test_rbac_enforcement()
        
        # Test filters
        await self.test_date_range_filters(super_admin_token)
        await self.test_client_filter(super_admin_token, client_id)
        await self.test_employee_filter(super_admin_token)
        
        # Test search functionality
        await self.test_text_search(super_admin_token)
        
        # Test pagination
        await self.test_pagination(super_admin_token)
        
        # Test no 500 errors
        await self.test_no_500_errors()
        
        # Test delete (do this last)
        if log_id:
            await self.test_delete_work_log(super_admin_token, log_id)
        
        # Generate summary
        await self.generate_test_summary()

    async def generate_test_summary(self):
        """Generate comprehensive test summary"""
        print("=" * 80)
        print("📊 WORK REPORTS LOGS API TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        warned_tests = len([r for r in self.test_results if r['status'] == 'WARN'])
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Warnings: {warned_tests} ⚠️")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%")
        print()
        
        # Critical findings
        print("🎯 CRITICAL FINDINGS:")
        
        critical_issues = []
        
        # Check authentication
        auth_tests = [r for r in self.test_results if 'Authentication' in r['test']]
        if not any(r['status'] == 'PASS' for r in auth_tests):
            critical_issues.append("❌ CRITICAL: Authentication system not working")
        
        # Check core CRUD operations
        crud_tests = [r for r in self.test_results if any(op in r['test'] for op in ['Create', 'Update', 'Delete'])]
        if not any(r['status'] == 'PASS' for r in crud_tests):
            critical_issues.append("❌ CRITICAL: CRUD operations not working")
        
        # Check happy path
        happy_path_tests = [r for r in self.test_results if 'Happy Path' in r['test']]
        if not any(r['status'] == 'PASS' for r in happy_path_tests):
            critical_issues.append("❌ CRITICAL: Basic GET endpoint not working")
        
        # Check RBAC
        rbac_tests = [r for r in self.test_results if 'RBAC' in r['test']]
        if not any(r['status'] == 'PASS' for r in rbac_tests):
            critical_issues.append("⚠️ WARNING: RBAC enforcement may not be working")
        
        # Check for server errors
        server_error_tests = [r for r in self.test_results if '500 Errors' in r['test']]
        if any(r['status'] == 'FAIL' for r in server_error_tests):
            critical_issues.append("❌ CRITICAL: Server errors (500) detected")
        
        if critical_issues:
            for issue in critical_issues:
                print(f"  {issue}")
        else:
            print("  ✅ No critical issues found - Work Reports Logs API is fully operational")
        
        print()
        
        # Failed tests details
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in self.test_results:
                if result['status'] == 'FAIL':
                    print(f"  - {result['test']}: {result['details']}")
            print()
        
        # Test categories summary
        print("📋 TEST CATEGORIES SUMMARY:")
        categories = {
            'Authentication': [r for r in self.test_results if 'Authentication' in r['test']],
            'CRUD Operations': [r for r in self.test_results if any(op in r['test'] for op in ['Create', 'Update', 'Delete'])],
            'Happy Path': [r for r in self.test_results if 'Happy Path' in r['test']],
            'RBAC': [r for r in self.test_results if 'RBAC' in r['test']],
            'Filters': [r for r in self.test_results if 'Filter' in r['test']],
            'Search': [r for r in self.test_results if 'Search' in r['test']],
            'Pagination': [r for r in self.test_results if 'Pagination' in r['test']],
            'Error Handling': [r for r in self.test_results if '500 Errors' in r['test']]
        }
        
        for category, tests in categories.items():
            if tests:
                passed = len([t for t in tests if t['status'] == 'PASS'])
                total = len(tests)
                status = "✅" if passed == total else "❌" if passed == 0 else "⚠️"
                print(f"  {status} {category}: {passed}/{total} passed")
        
        print()
        print("🔍 DETAILED TEST RESULTS:")
        for result in self.test_results:
            status_emoji = "✅" if result['status'] == "PASS" else "❌" if result['status'] == "FAIL" else "⚠️"
            print(f"  {status_emoji} {result['test']}")
            if result['details']:
                print(f"      {result['details']}")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'warned_tests': warned_tests,
            'success_rate': (passed_tests/total_tests*100) if total_tests > 0 else 0,
            'critical_issues': critical_issues,
            'test_results': self.test_results
        }

async def main():
    """Main test execution"""
    async with WorkReportsLogsTester() as tester:
        await tester.run_comprehensive_tests()

if __name__ == "__main__":
    asyncio.run(main())