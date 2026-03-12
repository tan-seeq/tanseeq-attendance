"""
Test Suite for Attendance Features - Custom Report & Admin Functions
Tests for:
1. Login as super_admin
2. Custom Report endpoint
3. Attendance management endpoints
"""

import pytest
import requests
import os
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL')
if not BASE_URL:
    BASE_URL = "https://payroll-management-4.preview.emergentagent.com"

BASE_URL = BASE_URL.rstrip('/')

class TestAuthentication:
    """Authentication and login tests"""
    
    def test_login_super_admin(self):
        """Test login as super_admin with admin@tanseeq.com / ADMIN"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@tanseeq.com",
            "password": "ADMIN"
        })
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert "user" in data, "No user in response"
        assert data["user"]["role"] == "super_admin", f"Expected super_admin, got {data['user']['role']}"
        print(f"✅ Login successful - User: {data['user']['name']}, Role: {data['user']['role']}")
        return data["access_token"]

    def test_auth_me_endpoint(self):
        """Test /auth/me endpoint returns user info"""
        # First login
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@tanseeq.com",
            "password": "ADMIN"
        })
        token = login_response.json()["access_token"]
        
        # Then check /auth/me
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        
        assert response.status_code == 200, f"Auth me failed: {response.text}"
        data = response.json()
        assert data["role"] == "super_admin"
        print(f"✅ Auth/me working - User: {data['name']}, Role: {data['role']}")


class TestAttendanceManagement:
    """Attendance management tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@tanseeq.com",
            "password": "ADMIN"
        })
        return response.json()["access_token"]
    
    def test_attendance_list(self, admin_token):
        """Test fetching attendance records"""
        response = requests.get(f"{BASE_URL}/api/attendance", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code == 200, f"Failed to get attendance: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of attendance records"
        print(f"✅ Got {len(data)} attendance records")
        return data

    def test_users_list(self, admin_token):
        """Test fetching users list for custom report"""
        response = requests.get(f"{BASE_URL}/api/users", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code == 200, f"Failed to get users: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of users"
        assert len(data) > 0, "Expected at least one user"
        print(f"✅ Got {len(data)} users")
        return data


class TestCustomReport:
    """Custom report feature tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@tanseeq.com",
            "password": "ADMIN"
        })
        return response.json()["access_token"]
    
    @pytest.fixture
    def user_ids(self, admin_token):
        """Get first few user IDs for testing"""
        response = requests.get(f"{BASE_URL}/api/users", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        users = response.json()
        # Get first 3 user IDs
        return [user["id"] for user in users[:3]]
    
    def test_custom_report_excel(self, admin_token, user_ids):
        """Test custom report generation in Excel format"""
        payload = {
            "employee_ids": user_ids,
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
            "format": "excel"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/attendance/custom-report", 
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Expect 200 (success with data) or 404 (no records in period)
        assert response.status_code in [200, 404], f"Custom report failed: {response.status_code} - {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") == True, "Expected success: true"
            assert "file_content" in data, "Expected file_content in response"
            assert "filename" in data, "Expected filename in response"
            assert ".xlsx" in data["filename"], "Expected .xlsx extension"
            print(f"✅ Custom report Excel generated: {data['filename']} ({data.get('records_count', 0)} records)")
        else:
            print(f"⚠️ Custom report returned 404 - no records in date range (expected behavior)")
    
    def test_custom_report_csv(self, admin_token, user_ids):
        """Test custom report generation in CSV format"""
        payload = {
            "employee_ids": user_ids,
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
            "format": "csv"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/attendance/custom-report", 
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Expect 200 (success with data) or 404 (no records in period)
        assert response.status_code in [200, 404], f"Custom report CSV failed: {response.status_code} - {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") == True
            assert "file_content" in data
            assert ".csv" in data["filename"]
            print(f"✅ Custom report CSV generated: {data['filename']}")
        else:
            print(f"⚠️ Custom report CSV returned 404 - no records in date range")
    
    def test_custom_report_validation_no_employees(self, admin_token):
        """Test custom report validation - no employees selected"""
        payload = {
            "employee_ids": [],
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
            "format": "excel"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/attendance/custom-report", 
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Should return 400 or validation error
        assert response.status_code == 400, f"Expected 400 for empty employee_ids, got {response.status_code}"
        print("✅ Validation working - empty employee_ids rejected")
    
    def test_custom_report_validation_no_dates(self, admin_token, user_ids):
        """Test custom report validation - missing dates"""
        payload = {
            "employee_ids": user_ids,
            "start_date": "",
            "end_date": "",
            "format": "excel"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/attendance/custom-report", 
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Should return 400 for missing required dates
        assert response.status_code == 400, f"Expected 400 for missing dates, got {response.status_code}"
        print("✅ Validation working - missing dates rejected")


class TestHealthChecks:
    """Health check tests"""
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = requests.get(f"{BASE_URL}/api/healthz")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        print("✅ Health check OK")
    
    def test_readiness_endpoint(self):
        """Test readiness endpoint"""
        response = requests.get(f"{BASE_URL}/api/readyz")
        # Can be 200 or 503 depending on DB status
        assert response.status_code in [200, 503], f"Unexpected status: {response.status_code}"
        print(f"✅ Readiness check returned: {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
