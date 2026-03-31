"""
Test Admin Config and Live Monitoring endpoints - Iteration 3
Tests for:
1. Admin Config System Settings (/api/admin/config/system)
2. Attendance Exceptions (/api/admin/config/exceptions)
3. Import Mappings (/api/admin/config/import-mappings)
4. Live Monitoring Metrics (/api/live/metrics)
5. Live Monitoring Logs (/api/live/logs)
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
SUPER_ADMIN_EMAIL = "admin@tanseeq.com"
SUPER_ADMIN_PASSWORD = "ADMIN"


class TestAuth:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for super admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        return data["access_token"]
    
    def test_login_super_admin(self, auth_token):
        """Test super admin login"""
        assert auth_token is not None
        assert len(auth_token) > 0
        print(f"✅ Super admin login successful, token length: {len(auth_token)}")


class TestAdminConfigSystem:
    """Admin Config - System Settings tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_get_system_config(self, auth_token):
        """Test GET /api/admin/config/system"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/config/system", headers=headers)
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "success" in data
        assert data["success"] == True
        assert "config" in data
        
        config = data["config"]
        # Verify expected fields exist
        assert "working_hours_start" in config or config.get("type") == "general"
        print(f"✅ GET /api/admin/config/system - Config retrieved: {list(config.keys())}")
    
    def test_update_system_config(self, auth_token):
        """Test PUT /api/admin/config/system"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First get current config
        get_response = requests.get(f"{BASE_URL}/api/admin/config/system", headers=headers)
        assert get_response.status_code == 200
        original_config = get_response.json()["config"]
        
        # Update config
        update_data = {
            "company_name": "TANSEEQ Tax Consultancy",
            "timezone": "Asia/Dubai",
            "working_hours_start": "09:00",
            "working_hours_end": "18:00",
            "grace_period_minutes": 15,
            "weekend_days": ["friday", "saturday"],
            "overtime_enabled": True,
            "auto_deduction_enabled": True
        }
        
        response = requests.put(f"{BASE_URL}/api/admin/config/system", 
                               headers=headers, json=update_data)
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["success"] == True
        print(f"✅ PUT /api/admin/config/system - Config updated successfully")


class TestAdminConfigExceptions:
    """Admin Config - Attendance Exceptions tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def test_employee_id(self, auth_token):
        """Get a test employee ID"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/users", headers=headers)
        assert response.status_code == 200
        users = response.json()
        # Find a non-admin user
        for user in users:
            if user.get("role") != "super_admin":
                return user["id"]
        # If no non-admin user, return first user
        return users[0]["id"] if users else None
    
    def test_get_exceptions(self, auth_token):
        """Test GET /api/admin/config/exceptions"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/config/exceptions", headers=headers)
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "success" in data
        assert data["success"] == True
        assert "exceptions" in data
        assert isinstance(data["exceptions"], list)
        print(f"✅ GET /api/admin/config/exceptions - Found {len(data['exceptions'])} exceptions")
    
    def test_add_exception(self, auth_token, test_employee_id):
        """Test POST /api/admin/config/exceptions"""
        if not test_employee_id:
            pytest.skip("No test employee available")
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First check if exception already exists
        get_response = requests.get(f"{BASE_URL}/api/admin/config/exceptions", headers=headers)
        existing = get_response.json().get("exceptions", [])
        existing_ids = [e.get("employee_id") for e in existing]
        
        if test_employee_id in existing_ids:
            # Delete existing exception first
            requests.delete(f"{BASE_URL}/api/admin/config/exceptions/{test_employee_id}", headers=headers)
        
        # Add new exception
        exception_data = {
            "employee_id": test_employee_id,
            "custom_start": "10:00",
            "custom_end": "19:00",
            "grace_period": 30,
            "exempt_from_deductions": True,
            "reason": "TEST_Exception for testing"
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/config/exceptions", 
                                headers=headers, json=exception_data)
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["success"] == True
        assert "exception" in data
        
        exception = data["exception"]
        assert exception["employee_id"] == test_employee_id
        assert exception["custom_start"] == "10:00"
        assert exception["grace_period"] == 30
        print(f"✅ POST /api/admin/config/exceptions - Exception added for employee")
    
    def test_delete_exception(self, auth_token, test_employee_id):
        """Test DELETE /api/admin/config/exceptions/{employee_id}"""
        if not test_employee_id:
            pytest.skip("No test employee available")
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Delete the exception we created
        response = requests.delete(
            f"{BASE_URL}/api/admin/config/exceptions/{test_employee_id}", 
            headers=headers
        )
        
        # Should be 200 if exists, 404 if not
        assert response.status_code in [200, 404], f"Failed: {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            assert data["success"] == True
            print(f"✅ DELETE /api/admin/config/exceptions - Exception deleted")
        else:
            print(f"✅ DELETE /api/admin/config/exceptions - Exception not found (already deleted)")


class TestAdminConfigImportMappings:
    """Admin Config - Import Mappings tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_get_import_mappings(self, auth_token):
        """Test GET /api/admin/config/import-mappings"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/config/import-mappings", headers=headers)
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "success" in data
        assert data["success"] == True
        assert "mappings" in data
        assert isinstance(data["mappings"], list)
        
        # Verify default mappings exist
        if data["mappings"]:
            mapping = data["mappings"][0]
            assert "source_column" in mapping
            assert "target_field" in mapping
        
        print(f"✅ GET /api/admin/config/import-mappings - Found {len(data['mappings'])} mappings")
    
    def test_update_import_mappings(self, auth_token):
        """Test PUT /api/admin/config/import-mappings"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Update mappings
        mappings_data = {
            "mappings": [
                {"source_column": "Name", "target_field": "name", "type": "attendance"},
                {"source_column": "Date", "target_field": "date", "type": "attendance"},
                {"source_column": "Check In", "target_field": "check_in", "type": "attendance"},
                {"source_column": "Check Out", "target_field": "check_out", "type": "attendance"}
            ]
        }
        
        response = requests.put(f"{BASE_URL}/api/admin/config/import-mappings", 
                               headers=headers, json=mappings_data)
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["success"] == True
        print(f"✅ PUT /api/admin/config/import-mappings - Mappings updated successfully")


class TestLiveMonitoring:
    """Live Monitoring tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_get_live_metrics(self, auth_token):
        """Test GET /api/live/metrics"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/live/metrics", headers=headers)
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "success" in data
        assert data["success"] == True
        assert "metrics" in data
        
        metrics = data["metrics"]
        # Verify expected metric fields
        assert "requests_total" in metrics or "total_requests" in metrics
        print(f"✅ GET /api/live/metrics - Metrics retrieved: {list(metrics.keys())}")
    
    def test_get_live_logs(self, auth_token):
        """Test GET /api/live/logs"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/live/logs", headers=headers)
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "success" in data
        assert data["success"] == True
        assert "lines" in data
        assert isinstance(data["lines"], list)
        print(f"✅ GET /api/live/logs - Retrieved {len(data['lines'])} log lines")


class TestUsersEndpoint:
    """Users endpoint test for employee list"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_get_users(self, auth_token):
        """Test GET /api/users - needed for AdminConfig employee dropdown"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/users", headers=headers)
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Verify user structure
        user = data[0]
        assert "id" in user
        assert "name" in user
        print(f"✅ GET /api/users - Found {len(data)} users")


class TestAttendanceManagement:
    """Attendance Management tests - verify refactored component still works"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_get_attendance_with_absences(self, auth_token):
        """Test GET /api/attendance/with-absences"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/attendance/with-absences", headers=headers)
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list)
        print(f"✅ GET /api/attendance/with-absences - Found {len(data)} records")
    
    def test_get_attendance(self, auth_token):
        """Test GET /api/attendance"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/attendance", headers=headers)
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list)
        print(f"✅ GET /api/attendance - Found {len(data)} records")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
