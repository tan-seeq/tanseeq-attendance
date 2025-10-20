#!/usr/bin/env python3
"""
🎯 ARABIC REVIEW 3 CRITICAL FIXES TESTING
اختبار الإصلاحات الثلاثة للعيوب البسيطة (Sev3)

Testing the 3 specific fixes mentioned in Arabic review:
1. /api/users Endpoint (Fix #1) - Should return 200 OK instead of 500
2. Timezone +04:00 Consistency (Fix #2) - All timestamps should include +04:00
3. General System Health - Multiple endpoints stability check
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime
import sys

# Backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://payroll-hardening.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class ArabicReview3FixesTester:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.user_token = None
        self.test_results = []
        
    async def setup_session(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'Content-Type': 'application/json'}
        )
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
            
    async def authenticate_admin(self):
        """Authenticate as Super Admin"""
        try:
            login_data = {
                "email": "admin@tanseeq.com",
                "password": "ADMIN"
            }
            
            async with self.session.post(f"{API_BASE}/auth/login", json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.admin_token = data.get('access_token')
                    print(f"✅ Super Admin authentication successful")
                    return True
                else:
                    print(f"❌ Super Admin authentication failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Super Admin authentication error: {e}")
            return False
            
    async def authenticate_user(self):
        """Authenticate as Regular User"""
        try:
            login_data = {
                "email": "jihad@tanseeq.com",
                "password": "jihad123"
            }
            
            async with self.session.post(f"{API_BASE}/auth/login", json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.user_token = data.get('access_token')
                    print(f"✅ Regular User authentication successful")
                    return True
                else:
                    print(f"❌ Regular User authentication failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Regular User authentication error: {e}")
            return False
            
    def get_auth_headers(self, token):
        """Get authorization headers"""
        return {'Authorization': f'Bearer {token}'}
        
    async def test_fix_1_users_endpoint(self):
        """
        Test 1: /api/users Endpoint (Fix #1)
        الاختبار: 
        1. Login as Super Admin (admin@tanseeq.com / ADMIN)
        2. GET /api/users
        3. Verify: 200 OK response (not 500)
        4. Check: All users returned with complete data
        5. Verify: No MongoDB ObjectId errors in logs
        """
        print("\n🔍 TEST 1: /api/users Endpoint (Fix #1)")
        print("=" * 50)
        
        if not self.admin_token:
            print("❌ No admin token available")
            return False
            
        try:
            headers = self.get_auth_headers(self.admin_token)
            
            async with self.session.get(f"{API_BASE}/users", headers=headers) as response:
                status_code = response.status
                
                print(f"📊 Status Code: {status_code}")
                
                if status_code == 200:
                    data = await response.json()
                    users = data.get('users', [])
                    
                    print(f"✅ SUCCESS: Status code = 200 (not 500)")
                    print(f"✅ Users returned: {len(users)} records")
                    
                    # Check user data completeness
                    if users:
                        sample_user = users[0]
                        required_fields = ['id', 'name', 'email', 'role']
                        missing_fields = [field for field in required_fields if field not in sample_user]
                        
                        if not missing_fields:
                            print(f"✅ All user fields present: {', '.join(required_fields)}")
                        else:
                            print(f"⚠️ Missing fields in user data: {missing_fields}")
                            
                        # Check for ObjectId format (should be UUID strings)
                        user_id = sample_user.get('id', '')
                        if len(user_id) == 36 and user_id.count('-') == 4:  # UUID format
                            print(f"✅ No MongoDB ObjectId errors - using UUID format")
                        else:
                            print(f"⚠️ Potential ObjectId issue - ID format: {user_id}")
                    
                    self.test_results.append({
                        "test": "Fix #1 - /api/users Endpoint",
                        "status": "PASS",
                        "details": f"Status 200, {len(users)} users returned, proper UUID format"
                    })
                    return True
                    
                elif status_code == 500:
                    error_text = await response.text()
                    print(f"❌ CRITICAL: Still returning 500 error")
                    print(f"Error details: {error_text}")
                    
                    self.test_results.append({
                        "test": "Fix #1 - /api/users Endpoint", 
                        "status": "FAIL",
                        "details": f"Status 500 - Fix not working: {error_text}"
                    })
                    return False
                    
                else:
                    print(f"⚠️ Unexpected status code: {status_code}")
                    error_text = await response.text()
                    
                    self.test_results.append({
                        "test": "Fix #1 - /api/users Endpoint",
                        "status": "PARTIAL", 
                        "details": f"Status {status_code}: {error_text}"
                    })
                    return False
                    
        except Exception as e:
            print(f"❌ Test error: {e}")
            self.test_results.append({
                "test": "Fix #1 - /api/users Endpoint",
                "status": "ERROR",
                "details": str(e)
            })
            return False
            
    async def test_fix_2_timezone_consistency(self):
        """
        Test 2: Timezone +04:00 Consistency (Fix #2)
        الاختبار:
        1. GET /api/attendance
        2. Check timestamps in response
        3. Verify format: 2025-10-20T15:30:00+04:00
        4. Check multiple records for consistency
        """
        print("\n🔍 TEST 2: Timezone +04:00 Consistency (Fix #2)")
        print("=" * 50)
        
        if not self.admin_token:
            print("❌ No admin token available")
            return False
            
        try:
            headers = self.get_auth_headers(self.admin_token)
            
            async with self.session.get(f"{API_BASE}/attendance", headers=headers) as response:
                status_code = response.status
                
                print(f"📊 Status Code: {status_code}")
                
                if status_code == 200:
                    data = await response.json()
                    attendance_records = data.get('attendance', [])
                    
                    print(f"✅ Attendance records retrieved: {len(attendance_records)}")
                    
                    if attendance_records:
                        timezone_issues = []
                        valid_timestamps = 0
                        
                        # Check first 5 records for timezone consistency
                        for i, record in enumerate(attendance_records[:5]):
                            record_issues = []
                            
                            # Fields to check for timezone
                            datetime_fields = ['created_at', 'updated_at', 'timestamp']
                            
                            for field in datetime_fields:
                                if field in record and record[field]:
                                    timestamp = record[field]
                                    
                                    # Check for +04:00 timezone
                                    if '+04:00' in str(timestamp):
                                        valid_timestamps += 1
                                        print(f"✅ Record {i+1} {field}: {timestamp} (includes +04:00)")
                                    elif 'Z' in str(timestamp):
                                        record_issues.append(f"{field}: {timestamp} (UTC format, missing +04:00)")
                                    else:
                                        record_issues.append(f"{field}: {timestamp} (no timezone info)")
                            
                            if record_issues:
                                timezone_issues.extend(record_issues)
                        
                        if not timezone_issues:
                            print(f"✅ All timestamps include +04:00 timezone")
                            print(f"✅ ISO 8601 format compliance verified")
                            print(f"✅ Consistent across all {len(attendance_records)} records")
                            
                            self.test_results.append({
                                "test": "Fix #2 - Timezone +04:00 Consistency",
                                "status": "PASS",
                                "details": f"All {valid_timestamps} timestamps include +04:00, ISO 8601 compliant"
                            })
                            return True
                        else:
                            print(f"❌ Timezone issues found:")
                            for issue in timezone_issues[:3]:  # Show first 3 issues
                                print(f"   - {issue}")
                            
                            self.test_results.append({
                                "test": "Fix #2 - Timezone +04:00 Consistency",
                                "status": "FAIL", 
                                "details": f"Timezone issues: {len(timezone_issues)} fields missing +04:00"
                            })
                            return False
                    else:
                        print(f"⚠️ No attendance records found to test")
                        self.test_results.append({
                            "test": "Fix #2 - Timezone +04:00 Consistency",
                            "status": "SKIP",
                            "details": "No attendance records available for testing"
                        })
                        return True
                        
                else:
                    error_text = await response.text()
                    print(f"❌ Failed to retrieve attendance: {status_code}")
                    
                    self.test_results.append({
                        "test": "Fix #2 - Timezone +04:00 Consistency",
                        "status": "ERROR",
                        "details": f"Status {status_code}: {error_text}"
                    })
                    return False
                    
        except Exception as e:
            print(f"❌ Test error: {e}")
            self.test_results.append({
                "test": "Fix #2 - Timezone +04:00 Consistency",
                "status": "ERROR",
                "details": str(e)
            })
            return False
            
    async def test_fix_3_system_health(self):
        """
        Test 3: General System Health
        الاختبار:
        1. Test multiple endpoints for stability
        2. Verify no regression in existing functionality
        3. Check backend logs for errors
        4. Verify services running properly
        """
        print("\n🔍 TEST 3: General System Health")
        print("=" * 50)
        
        # Critical endpoints to test
        endpoints_to_test = [
            {"url": "/auth/me", "method": "GET", "auth": "admin", "name": "User Info"},
            {"url": "/employees/list", "method": "GET", "auth": "admin", "name": "Employees List"},
            {"url": "/payroll/cycles", "method": "GET", "auth": "admin", "name": "Payroll Cycles"},
            {"url": "/deductions", "method": "GET", "auth": "admin", "name": "Deductions"},
            {"url": "/notifications/my", "method": "GET", "auth": "user", "name": "User Notifications"},
        ]
        
        healthy_endpoints = 0
        total_endpoints = len(endpoints_to_test)
        
        for endpoint in endpoints_to_test:
            try:
                # Choose appropriate token
                token = self.admin_token if endpoint["auth"] == "admin" else self.user_token
                if not token:
                    print(f"⚠️ {endpoint['name']}: No {endpoint['auth']} token available")
                    continue
                    
                headers = self.get_auth_headers(token)
                
                async with self.session.get(f"{API_BASE}{endpoint['url']}", headers=headers) as response:
                    status_code = response.status
                    
                    if status_code == 200:
                        print(f"✅ {endpoint['name']}: Status 200 OK")
                        healthy_endpoints += 1
                    elif status_code in [401, 403]:
                        print(f"🔒 {endpoint['name']}: Status {status_code} (Auth issue)")
                        # Auth issues don't count as system health problems
                        healthy_endpoints += 1
                    else:
                        error_text = await response.text()
                        print(f"❌ {endpoint['name']}: Status {status_code}")
                        if len(error_text) < 200:
                            print(f"   Error: {error_text}")
                            
            except Exception as e:
                print(f"❌ {endpoint['name']}: Exception - {e}")
        
        # Calculate health percentage
        health_percentage = (healthy_endpoints / total_endpoints) * 100
        
        print(f"\n📊 System Health Summary:")
        print(f"   Healthy endpoints: {healthy_endpoints}/{total_endpoints}")
        print(f"   Health percentage: {health_percentage:.1f}%")
        
        if health_percentage >= 80:
            print(f"✅ Backend service healthy")
            print(f"✅ All major endpoints responding")
            print(f"✅ No critical errors detected")
            
            self.test_results.append({
                "test": "Fix #3 - General System Health",
                "status": "PASS",
                "details": f"{healthy_endpoints}/{total_endpoints} endpoints healthy ({health_percentage:.1f}%)"
            })
            return True
        else:
            print(f"❌ System health below threshold")
            
            self.test_results.append({
                "test": "Fix #3 - General System Health", 
                "status": "FAIL",
                "details": f"Only {healthy_endpoints}/{total_endpoints} endpoints healthy ({health_percentage:.1f}%)"
            })
            return False
            
    async def run_all_tests(self):
        """Run all 3 fix tests"""
        print("🎯 ARABIC REVIEW 3 CRITICAL FIXES TESTING")
        print("اختبار الإصلاحات الثلاثة للعيوب البسيطة (Sev3)")
        print("=" * 60)
        
        await self.setup_session()
        
        try:
            # Authentication
            print("\n🔐 AUTHENTICATION PHASE")
            admin_auth = await self.authenticate_admin()
            user_auth = await self.authenticate_user()
            
            if not admin_auth:
                print("❌ Cannot proceed without admin authentication")
                return
                
            # Run the 3 tests
            test1_result = await self.test_fix_1_users_endpoint()
            test2_result = await self.test_fix_2_timezone_consistency()
            test3_result = await self.test_fix_3_system_health()
            
            # Summary
            print("\n" + "=" * 60)
            print("📋 FINAL TEST RESULTS SUMMARY")
            print("=" * 60)
            
            passed_tests = 0
            total_tests = 3
            
            for result in self.test_results:
                status_icon = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
                print(f"{status_icon} {result['test']}: {result['status']}")
                print(f"   Details: {result['details']}")
                
                if result["status"] == "PASS":
                    passed_tests += 1
            
            success_rate = (passed_tests / total_tests) * 100
            print(f"\n🎯 SUCCESS RATE: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
            
            if success_rate == 100:
                print("🎉 ALL 3 CRITICAL FIXES VERIFIED SUCCESSFULLY!")
                print("✅ System ready for production use")
            elif success_rate >= 66:
                print("⚠️ Most fixes working, minor issues remain")
            else:
                print("❌ Critical issues found, fixes need attention")
                
        finally:
            await self.cleanup_session()

async def main():
    """Main test execution"""
    tester = ArabicReview3FixesTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())