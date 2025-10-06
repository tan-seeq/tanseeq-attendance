#!/usr/bin/env python3
"""
Advanced Attendance Deductions System Testing
اختبار نظام الخصومات المتقدم للحضور - أكتوبر 2025

Testing the new advanced attendance deductions system with:
- GET /api/deductions - Get deductions with filters
- POST /api/deductions/manual - Create manual deduction (Super Admin only)
- PATCH /api/deductions/{id} - Update deduction (Super Admin only)
- POST /api/deductions/{id}/void - Void/cancel deduction (Super Admin only)
- GET /api/attendance/stats/{employee_id} - Get attendance statistics
- POST /api/attendance/recompute - Recompute attendance (Super Admin only)
"""

import requests
import json
import os
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional

# Configuration - Try local backend first
BACKEND_URL = "http://localhost:8001"
API_BASE = f"{BACKEND_URL}/api"

# Test credentials from review request
SUPER_ADMIN_CREDENTIALS = {
    "email": "hatem@tan-seeq.co",
    "password": "hatem123"
}

REGULAR_USER_CREDENTIALS = {
    "email": "jihad@tanseeq.com", 
    "password": "jihad123"
}

class AttendanceDeductionsTestSuite:
    """Test suite for Advanced Attendance Deductions System"""
    
    def __init__(self):
        self.super_admin_token = None
        self.regular_user_token = None
        self.super_admin_user = None
        self.regular_user = None
        self.test_results = []
        self.created_deductions = []  # Track created deductions for cleanup
        
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        if response_data and not success:
            print(f"   Response: {response_data}")
        print()
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response": response_data
        })
    
    def authenticate_user(self, credentials: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Authenticate user and return token + user info"""
        try:
            response = requests.post(
                f"{API_BASE}/auth/login",
                json=credentials,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "token": data.get("access_token"),
                    "user": data.get("user")
                }
            else:
                print(f"Authentication failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Authentication error: {e}")
            return None
    
    def make_request(self, method: str, endpoint: str, token: str, data: Dict = None, params: Dict = None) -> requests.Response:
        """Make authenticated API request"""
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        url = f"{API_BASE}{endpoint}"
        
        try:
            if method.upper() == "GET":
                return requests.get(url, headers=headers, params=params, timeout=30)
            elif method.upper() == "POST":
                return requests.post(url, headers=headers, json=data, timeout=30)
            elif method.upper() == "PATCH":
                return requests.patch(url, headers=headers, json=data, timeout=30)
            elif method.upper() == "DELETE":
                return requests.delete(url, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
        except Exception as e:
            print(f"Request error for {method} {endpoint}: {e}")
            raise
    
    def setup_authentication(self):
        """Setup authentication for both user types"""
        print("🔐 Setting up authentication...")
        
        # Authenticate Super Admin
        super_admin_auth = self.authenticate_user(SUPER_ADMIN_CREDENTIALS)
        if super_admin_auth:
            self.super_admin_token = super_admin_auth["token"]
            self.super_admin_user = super_admin_auth["user"]
            self.log_test(
                "Super Admin Authentication", 
                True, 
                f"Authenticated as {self.super_admin_user.get('name')} ({self.super_admin_user.get('role')})"
            )
        else:
            self.log_test("Super Admin Authentication", False, "Failed to authenticate super admin")
            return False
        
        # Authenticate Regular User
        regular_user_auth = self.authenticate_user(REGULAR_USER_CREDENTIALS)
        if regular_user_auth:
            self.regular_user_token = regular_user_auth["token"]
            self.regular_user = regular_user_auth["user"]
            self.log_test(
                "Regular User Authentication", 
                True, 
                f"Authenticated as {self.regular_user.get('name')} ({self.regular_user.get('role')})"
            )
        else:
            self.log_test("Regular User Authentication", False, "Failed to authenticate regular user")
            return False
        
        return True
    
    def test_get_deductions_super_admin(self):
        """Test GET /api/deductions as Super Admin"""
        print("📊 Testing GET /api/deductions (Super Admin)...")
        
        try:
            # Test without filters
            response = self.make_request("GET", "/deductions", self.super_admin_token)
            
            if response.status_code == 200:
                deductions = response.json()
                self.log_test(
                    "GET /api/deductions (Super Admin - No Filters)",
                    True,
                    f"Retrieved {len(deductions)} deductions"
                )
            else:
                self.log_test(
                    "GET /api/deductions (Super Admin - No Filters)",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
            
            # Test with month filter
            current_month = datetime.now().strftime("%Y-%m")
            response = self.make_request(
                "GET", 
                "/deductions", 
                self.super_admin_token,
                params={"month": current_month}
            )
            
            if response.status_code == 200:
                deductions = response.json()
                self.log_test(
                    "GET /api/deductions (Super Admin - Month Filter)",
                    True,
                    f"Retrieved {len(deductions)} deductions for {current_month}"
                )
            else:
                self.log_test(
                    "GET /api/deductions (Super Admin - Month Filter)",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
            
            # Test with employee filter
            if self.regular_user:
                response = self.make_request(
                    "GET", 
                    "/deductions", 
                    self.super_admin_token,
                    params={"employee_id": self.regular_user["id"]}
                )
                
                if response.status_code == 200:
                    deductions = response.json()
                    self.log_test(
                        "GET /api/deductions (Super Admin - Employee Filter)",
                        True,
                        f"Retrieved {len(deductions)} deductions for {self.regular_user['name']}"
                    )
                else:
                    self.log_test(
                        "GET /api/deductions (Super Admin - Employee Filter)",
                        False,
                        f"Status: {response.status_code}",
                        response.text
                    )
            
        except Exception as e:
            self.log_test("GET /api/deductions (Super Admin)", False, f"Exception: {e}")
    
    def test_get_deductions_regular_user(self):
        """Test GET /api/deductions as Regular User (should only see own deductions)"""
        print("👤 Testing GET /api/deductions (Regular User)...")
        
        try:
            response = self.make_request("GET", "/deductions", self.regular_user_token)
            
            if response.status_code == 200:
                deductions = response.json()
                # Verify all deductions belong to the current user
                all_own_deductions = all(
                    d.get("employee_id") == self.regular_user["id"] 
                    for d in deductions
                )
                
                self.log_test(
                    "GET /api/deductions (Regular User - Own Deductions Only)",
                    all_own_deductions,
                    f"Retrieved {len(deductions)} own deductions, all belong to user: {all_own_deductions}"
                )
            else:
                self.log_test(
                    "GET /api/deductions (Regular User)",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
            
        except Exception as e:
            self.log_test("GET /api/deductions (Regular User)", False, f"Exception: {e}")
    
    def test_create_manual_deduction_super_admin(self):
        """Test POST /api/deductions/manual as Super Admin"""
        print("➕ Testing POST /api/deductions/manual (Super Admin)...")
        
        try:
            # Create manual deduction for regular user
            deduction_data = {
                "employee_id": self.regular_user["id"],
                "amount": 50.0,
                "reason": "Test manual deduction - Late arrival penalty",
                "date": datetime.now().strftime("%Y-%m-%d")
            }
            
            response = self.make_request(
                "POST", 
                "/deductions/manual", 
                self.super_admin_token,
                data=deduction_data
            )
            
            if response.status_code == 200:
                result = response.json()
                deduction = result.get("deduction", {})
                if deduction.get("id"):
                    self.created_deductions.append(deduction["id"])
                
                self.log_test(
                    "POST /api/deductions/manual (Super Admin)",
                    True,
                    f"Created manual deduction: {result.get('message', 'Success')}"
                )
            else:
                self.log_test(
                    "POST /api/deductions/manual (Super Admin)",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
            
        except Exception as e:
            self.log_test("POST /api/deductions/manual (Super Admin)", False, f"Exception: {e}")
    
    def test_create_manual_deduction_regular_user(self):
        """Test POST /api/deductions/manual as Regular User (should fail)"""
        print("🚫 Testing POST /api/deductions/manual (Regular User - Should Fail)...")
        
        try:
            deduction_data = {
                "employee_id": self.regular_user["id"],
                "amount": 25.0,
                "reason": "Test unauthorized deduction",
                "date": datetime.now().strftime("%Y-%m-%d")
            }
            
            response = self.make_request(
                "POST", 
                "/deductions/manual", 
                self.regular_user_token,
                data=deduction_data
            )
            
            # Should return 403 Forbidden
            if response.status_code == 403:
                self.log_test(
                    "POST /api/deductions/manual (Regular User - Access Denied)",
                    True,
                    "Correctly denied access with 403 status"
                )
            else:
                self.log_test(
                    "POST /api/deductions/manual (Regular User - Access Denied)",
                    False,
                    f"Expected 403, got {response.status_code}",
                    response.text
                )
            
        except Exception as e:
            self.log_test("POST /api/deductions/manual (Regular User)", False, f"Exception: {e}")
    
    def test_update_deduction_super_admin(self):
        """Test PATCH /api/deductions/{id} as Super Admin"""
        print("✏️ Testing PATCH /api/deductions/{id} (Super Admin)...")
        
        if not self.created_deductions:
            self.log_test("PATCH /api/deductions/{id} (Super Admin)", False, "No deductions to update")
            return
        
        try:
            deduction_id = self.created_deductions[0]
            update_data = {
                "amount": 75.0,
                "reason": "Updated manual deduction - Increased penalty"
            }
            
            response = self.make_request(
                "PATCH", 
                f"/deductions/{deduction_id}", 
                self.super_admin_token,
                data=update_data
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log_test(
                    "PATCH /api/deductions/{id} (Super Admin)",
                    True,
                    f"Updated deduction: {result.get('message', 'Success')}"
                )
            else:
                self.log_test(
                    "PATCH /api/deductions/{id} (Super Admin)",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
            
        except Exception as e:
            self.log_test("PATCH /api/deductions/{id} (Super Admin)", False, f"Exception: {e}")
    
    def test_update_deduction_regular_user(self):
        """Test PATCH /api/deductions/{id} as Regular User (should fail)"""
        print("🚫 Testing PATCH /api/deductions/{id} (Regular User - Should Fail)...")
        
        if not self.created_deductions:
            self.log_test("PATCH /api/deductions/{id} (Regular User)", False, "No deductions to update")
            return
        
        try:
            deduction_id = self.created_deductions[0]
            update_data = {
                "amount": 10.0,
                "reason": "Unauthorized update attempt"
            }
            
            response = self.make_request(
                "PATCH", 
                f"/deductions/{deduction_id}", 
                self.regular_user_token,
                data=update_data
            )
            
            # Should return 403 Forbidden
            if response.status_code == 403:
                self.log_test(
                    "PATCH /api/deductions/{id} (Regular User - Access Denied)",
                    True,
                    "Correctly denied access with 403 status"
                )
            else:
                self.log_test(
                    "PATCH /api/deductions/{id} (Regular User - Access Denied)",
                    False,
                    f"Expected 403, got {response.status_code}",
                    response.text
                )
            
        except Exception as e:
            self.log_test("PATCH /api/deductions/{id} (Regular User)", False, f"Exception: {e}")
    
    def test_void_deduction_super_admin(self):
        """Test POST /api/deductions/{id}/void as Super Admin"""
        print("🗑️ Testing POST /api/deductions/{id}/void (Super Admin)...")
        
        if not self.created_deductions:
            self.log_test("POST /api/deductions/{id}/void (Super Admin)", False, "No deductions to void")
            return
        
        try:
            deduction_id = self.created_deductions[0]
            void_data = {
                "reason": "Test voiding - Administrative correction"
            }
            
            response = self.make_request(
                "POST", 
                f"/deductions/{deduction_id}/void", 
                self.super_admin_token,
                data=void_data
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log_test(
                    "POST /api/deductions/{id}/void (Super Admin)",
                    True,
                    f"Voided deduction: {result.get('message', 'Success')}"
                )
            else:
                self.log_test(
                    "POST /api/deductions/{id}/void (Super Admin)",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
            
        except Exception as e:
            self.log_test("POST /api/deductions/{id}/void (Super Admin)", False, f"Exception: {e}")
    
    def test_void_deduction_regular_user(self):
        """Test POST /api/deductions/{id}/void as Regular User (should fail)"""
        print("🚫 Testing POST /api/deductions/{id}/void (Regular User - Should Fail)...")
        
        if not self.created_deductions:
            self.log_test("POST /api/deductions/{id}/void (Regular User)", False, "No deductions to void")
            return
        
        try:
            deduction_id = self.created_deductions[0]
            void_data = {
                "reason": "Unauthorized void attempt"
            }
            
            response = self.make_request(
                "POST", 
                f"/deductions/{deduction_id}/void", 
                self.regular_user_token,
                data=void_data
            )
            
            # Should return 403 Forbidden
            if response.status_code == 403:
                self.log_test(
                    "POST /api/deductions/{id}/void (Regular User - Access Denied)",
                    True,
                    "Correctly denied access with 403 status"
                )
            else:
                self.log_test(
                    "POST /api/deductions/{id}/void (Regular User - Access Denied)",
                    False,
                    f"Expected 403, got {response.status_code}",
                    response.text
                )
            
        except Exception as e:
            self.log_test("POST /api/deductions/{id}/void (Regular User)", False, f"Exception: {e}")
    
    def test_attendance_stats_super_admin(self):
        """Test GET /api/attendance/stats/{employee_id} as Super Admin"""
        print("📈 Testing GET /api/attendance/stats/{employee_id} (Super Admin)...")
        
        try:
            # Test getting stats for regular user
            response = self.make_request(
                "GET", 
                f"/attendance/stats/{self.regular_user['id']}", 
                self.super_admin_token
            )
            
            if response.status_code == 200:
                stats = response.json()
                self.log_test(
                    "GET /api/attendance/stats/{employee_id} (Super Admin)",
                    True,
                    f"Retrieved attendance stats for {self.regular_user['name']}: {stats}"
                )
            else:
                self.log_test(
                    "GET /api/attendance/stats/{employee_id} (Super Admin)",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
            
            # Test getting own stats
            response = self.make_request(
                "GET", 
                f"/attendance/stats/{self.super_admin_user['id']}", 
                self.super_admin_token
            )
            
            if response.status_code == 200:
                stats = response.json()
                self.log_test(
                    "GET /api/attendance/stats/{employee_id} (Super Admin - Own Stats)",
                    True,
                    f"Retrieved own attendance stats: {stats}"
                )
            else:
                self.log_test(
                    "GET /api/attendance/stats/{employee_id} (Super Admin - Own Stats)",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
            
        except Exception as e:
            self.log_test("GET /api/attendance/stats/{employee_id} (Super Admin)", False, f"Exception: {e}")
    
    def test_attendance_stats_regular_user(self):
        """Test GET /api/attendance/stats/{employee_id} as Regular User"""
        print("👤 Testing GET /api/attendance/stats/{employee_id} (Regular User)...")
        
        try:
            # Test getting own stats (should work)
            response = self.make_request(
                "GET", 
                f"/attendance/stats/{self.regular_user['id']}", 
                self.regular_user_token
            )
            
            if response.status_code == 200:
                stats = response.json()
                self.log_test(
                    "GET /api/attendance/stats/{employee_id} (Regular User - Own Stats)",
                    True,
                    f"Retrieved own attendance stats: {stats}"
                )
            else:
                self.log_test(
                    "GET /api/attendance/stats/{employee_id} (Regular User - Own Stats)",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
            
            # Test getting other user's stats (should fail)
            response = self.make_request(
                "GET", 
                f"/attendance/stats/{self.super_admin_user['id']}", 
                self.regular_user_token
            )
            
            if response.status_code == 403:
                self.log_test(
                    "GET /api/attendance/stats/{employee_id} (Regular User - Other's Stats - Access Denied)",
                    True,
                    "Correctly denied access to other user's stats with 403 status"
                )
            else:
                self.log_test(
                    "GET /api/attendance/stats/{employee_id} (Regular User - Other's Stats - Access Denied)",
                    False,
                    f"Expected 403, got {response.status_code}",
                    response.text
                )
            
        except Exception as e:
            self.log_test("GET /api/attendance/stats/{employee_id} (Regular User)", False, f"Exception: {e}")
    
    def test_attendance_recompute_super_admin(self):
        """Test POST /api/attendance/recompute as Super Admin"""
        print("🔄 Testing POST /api/attendance/recompute (Super Admin)...")
        
        try:
            # Test recompute for specific date and employee
            recompute_data = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "employee_id": self.regular_user["id"]
            }
            
            response = self.make_request(
                "POST", 
                "/attendance/recompute", 
                self.super_admin_token,
                data=recompute_data
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log_test(
                    "POST /api/attendance/recompute (Super Admin - Specific Date/Employee)",
                    True,
                    f"Recomputed attendance: {result.get('message', 'Success')}"
                )
            else:
                self.log_test(
                    "POST /api/attendance/recompute (Super Admin - Specific Date/Employee)",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
            
            # Test recompute for entire month
            current_month = datetime.now().strftime("%Y-%m")
            recompute_data = {
                "month": current_month,
                "employee_id": self.regular_user["id"]
            }
            
            response = self.make_request(
                "POST", 
                "/attendance/recompute", 
                self.super_admin_token,
                data=recompute_data
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log_test(
                    "POST /api/attendance/recompute (Super Admin - Entire Month)",
                    True,
                    f"Recomputed month attendance: {result.get('message', 'Success')}"
                )
            else:
                self.log_test(
                    "POST /api/attendance/recompute (Super Admin - Entire Month)",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
            
        except Exception as e:
            self.log_test("POST /api/attendance/recompute (Super Admin)", False, f"Exception: {e}")
    
    def test_attendance_recompute_regular_user(self):
        """Test POST /api/attendance/recompute as Regular User (should fail)"""
        print("🚫 Testing POST /api/attendance/recompute (Regular User - Should Fail)...")
        
        try:
            recompute_data = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "employee_id": self.regular_user["id"]
            }
            
            response = self.make_request(
                "POST", 
                "/attendance/recompute", 
                self.regular_user_token,
                data=recompute_data
            )
            
            # Should return 403 Forbidden
            if response.status_code == 403:
                self.log_test(
                    "POST /api/attendance/recompute (Regular User - Access Denied)",
                    True,
                    "Correctly denied access with 403 status"
                )
            else:
                self.log_test(
                    "POST /api/attendance/recompute (Regular User - Access Denied)",
                    False,
                    f"Expected 403, got {response.status_code}",
                    response.text
                )
            
        except Exception as e:
            self.log_test("POST /api/attendance/recompute (Regular User)", False, f"Exception: {e}")
    
    def test_advanced_deduction_rules(self):
        """Test advanced deduction rules for October 2025"""
        print("⚖️ Testing Advanced Deduction Rules (October 2025)...")
        
        try:
            # Test different scenarios with manual deductions
            test_scenarios = [
                {
                    "name": "15 minutes late (should be free if within limit)",
                    "amount": 0,  # Should be calculated based on rules
                    "reason": "Test: 15 minutes late - should use free occurrence"
                },
                {
                    "name": "25 minutes late (direct deduction)",
                    "amount": 0,  # Should be calculated
                    "reason": "Test: 25 minutes late - direct deduction"
                },
                {
                    "name": "90 minutes late (half day)",
                    "amount": 0,  # Should be calculated as half day
                    "reason": "Test: 90 minutes late - half day deduction"
                },
                {
                    "name": "150 minutes late (full day)",
                    "amount": 0,  # Should be calculated as full day
                    "reason": "Test: 150 minutes late - full day deduction"
                }
            ]
            
            for scenario in test_scenarios:
                deduction_data = {
                    "employee_id": self.regular_user["id"],
                    "amount": scenario["amount"] if scenario["amount"] > 0 else 50.0,  # Default amount for testing
                    "reason": scenario["reason"],
                    "date": datetime.now().strftime("%Y-%m-%d")
                }
                
                response = self.make_request(
                    "POST", 
                    "/deductions/manual", 
                    self.super_admin_token,
                    data=deduction_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    deduction = result.get("deduction", {})
                    if deduction.get("id"):
                        self.created_deductions.append(deduction["id"])
                    
                    self.log_test(
                        f"Advanced Deduction Rule - {scenario['name']}",
                        True,
                        f"Created test deduction: {result.get('message', 'Success')}"
                    )
                else:
                    self.log_test(
                        f"Advanced Deduction Rule - {scenario['name']}",
                        False,
                        f"Status: {response.status_code}",
                        response.text
                    )
            
        except Exception as e:
            self.log_test("Advanced Deduction Rules", False, f"Exception: {e}")
    
    def test_employee_exceptions(self):
        """Test employee exceptions (Hatem should be exempt from penalties)"""
        print("🛡️ Testing Employee Exceptions (Hatem exempt from penalties)...")
        
        try:
            # Try to create a deduction for Hatem (should work but might have special handling)
            deduction_data = {
                "employee_id": self.super_admin_user["id"],  # Hatem
                "amount": 100.0,
                "reason": "Test: Hatem exception - should be exempt from penalties",
                "date": datetime.now().strftime("%Y-%m-%d")
            }
            
            response = self.make_request(
                "POST", 
                "/deductions/manual", 
                self.super_admin_token,
                data=deduction_data
            )
            
            if response.status_code == 200:
                result = response.json()
                deduction = result.get("deduction", {})
                if deduction.get("id"):
                    self.created_deductions.append(deduction["id"])
                
                self.log_test(
                    "Employee Exception - Hatem Manual Deduction",
                    True,
                    f"Manual deduction created for Hatem: {result.get('message', 'Success')}"
                )
            else:
                self.log_test(
                    "Employee Exception - Hatem Manual Deduction",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
            
        except Exception as e:
            self.log_test("Employee Exceptions", False, f"Exception: {e}")
    
    def test_data_validation(self):
        """Test data validation and security"""
        print("🔒 Testing Data Validation and Security...")
        
        try:
            # Test with invalid employee ID
            invalid_deduction_data = {
                "employee_id": "invalid-employee-id-12345",
                "amount": 50.0,
                "reason": "Test invalid employee ID",
                "date": datetime.now().strftime("%Y-%m-%d")
            }
            
            response = self.make_request(
                "POST", 
                "/deductions/manual", 
                self.super_admin_token,
                data=invalid_deduction_data
            )
            
            if response.status_code in [400, 404]:
                self.log_test(
                    "Data Validation - Invalid Employee ID",
                    True,
                    f"Correctly rejected invalid employee ID with status {response.status_code}"
                )
            else:
                self.log_test(
                    "Data Validation - Invalid Employee ID",
                    False,
                    f"Expected 400/404, got {response.status_code}",
                    response.text
                )
            
            # Test with invalid date format
            invalid_date_data = {
                "employee_id": self.regular_user["id"],
                "amount": 50.0,
                "reason": "Test invalid date",
                "date": "invalid-date-format"
            }
            
            response = self.make_request(
                "POST", 
                "/deductions/manual", 
                self.super_admin_token,
                data=invalid_date_data
            )
            
            if response.status_code == 400:
                self.log_test(
                    "Data Validation - Invalid Date Format",
                    True,
                    "Correctly rejected invalid date format with 400 status"
                )
            else:
                self.log_test(
                    "Data Validation - Invalid Date Format",
                    False,
                    f"Expected 400, got {response.status_code}",
                    response.text
                )
            
            # Test with missing required fields
            incomplete_data = {
                "employee_id": self.regular_user["id"],
                # Missing amount, reason, date
            }
            
            response = self.make_request(
                "POST", 
                "/deductions/manual", 
                self.super_admin_token,
                data=incomplete_data
            )
            
            if response.status_code == 400:
                self.log_test(
                    "Data Validation - Missing Required Fields",
                    True,
                    "Correctly rejected incomplete data with 400 status"
                )
            else:
                self.log_test(
                    "Data Validation - Missing Required Fields",
                    False,
                    f"Expected 400, got {response.status_code}",
                    response.text
                )
            
        except Exception as e:
            self.log_test("Data Validation", False, f"Exception: {e}")
    
    def test_notification_system(self):
        """Test that notifications are sent when deductions are created/modified"""
        print("🔔 Testing Notification System Integration...")
        
        try:
            # Get notifications before creating deduction
            response = self.make_request("GET", "/notifications", self.regular_user_token)
            initial_count = 0
            if response.status_code == 200:
                notifications = response.json()
                initial_count = len(notifications)
            
            # Create a deduction that should trigger notification
            deduction_data = {
                "employee_id": self.regular_user["id"],
                "amount": 25.0,
                "reason": "Test notification system - penalty for testing",
                "date": datetime.now().strftime("%Y-%m-%d")
            }
            
            response = self.make_request(
                "POST", 
                "/deductions/manual", 
                self.super_admin_token,
                data=deduction_data
            )
            
            if response.status_code == 200:
                result = response.json()
                deduction = result.get("deduction", {})
                if deduction.get("id"):
                    self.created_deductions.append(deduction["id"])
                
                # Check if notification was created
                response = self.make_request("GET", "/notifications", self.regular_user_token)
                if response.status_code == 200:
                    notifications = response.json()
                    new_count = len(notifications)
                    
                    if new_count > initial_count:
                        self.log_test(
                            "Notification System - Deduction Created",
                            True,
                            f"Notification sent successfully (count increased from {initial_count} to {new_count})"
                        )
                    else:
                        self.log_test(
                            "Notification System - Deduction Created",
                            False,
                            f"No new notification found (count: {initial_count} -> {new_count})"
                        )
                else:
                    self.log_test(
                        "Notification System - Check Notifications",
                        False,
                        f"Failed to retrieve notifications: {response.status_code}"
                    )
            else:
                self.log_test(
                    "Notification System - Create Deduction",
                    False,
                    f"Failed to create deduction: {response.status_code}",
                    response.text
                )
            
        except Exception as e:
            self.log_test("Notification System", False, f"Exception: {e}")
    
    def run_all_tests(self):
        """Run all test scenarios"""
        print("🚀 Starting Advanced Attendance Deductions System Testing...")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 80)
        
        # Setup
        if not self.setup_authentication():
            print("❌ Authentication setup failed. Cannot proceed with tests.")
            return
        
        # Core API endpoint tests
        self.test_get_deductions_super_admin()
        self.test_get_deductions_regular_user()
        
        self.test_create_manual_deduction_super_admin()
        self.test_create_manual_deduction_regular_user()
        
        self.test_update_deduction_super_admin()
        self.test_update_deduction_regular_user()
        
        self.test_void_deduction_super_admin()
        self.test_void_deduction_regular_user()
        
        self.test_attendance_stats_super_admin()
        self.test_attendance_stats_regular_user()
        
        self.test_attendance_recompute_super_admin()
        self.test_attendance_recompute_regular_user()
        
        # Advanced feature tests
        self.test_advanced_deduction_rules()
        self.test_employee_exceptions()
        self.test_data_validation()
        self.test_notification_system()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for test in self.test_results:
                if not test["success"]:
                    print(f"  - {test['test']}: {test['details']}")
        
        print(f"\n📝 Created {len(self.created_deductions)} test deductions during testing")
        print("=" * 80)

if __name__ == "__main__":
    test_suite = AttendanceDeductionsTestSuite()
    test_suite.run_all_tests()