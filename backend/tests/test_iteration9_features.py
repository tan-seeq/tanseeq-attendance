"""
Iteration 9 - Testing TANSEEQ HR System Bug Fixes
Tests:
1. Backend API health: GET /api/healthz
2. Login flow: POST /api/auth/login
3. Custom Report API: POST /api/attendance/custom-report
4. Time parsing robustness (via attendance endpoints)
5. Edit/Delete attendance buttons visibility (frontend test)
"""

import pytest
import requests
import os
import base64

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://payroll-management-4.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@tanseeq.com"
ADMIN_PASSWORD = "ADMIN"


class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_healthz_returns_ok(self):
        """GET /api/healthz should return {status: ok}"""
        response = requests.get(f"{BASE_URL}/api/healthz")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("status") == "ok", f"Expected status 'ok', got {data}"
        print(f"✅ Health check passed: {data}")


class TestAuthFlow:
    """Test authentication endpoints"""
    
    def test_login_success(self):
        """POST /api/auth/login with valid credentials should return access_token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed with status {response.status_code}: {response.text}"
        data = response.json()
        assert "access_token" in data, f"No access_token in response: {data}"
        assert data.get("token_type") == "bearer", f"Expected bearer token type"
        assert "user" in data, f"No user in response"
        assert data["user"]["email"] == ADMIN_EMAIL, f"Email mismatch"
        assert data["user"]["role"] == "super_admin", f"Expected super_admin role"
        print(f"✅ Login successful for {ADMIN_EMAIL}")
        return data["access_token"]
    
    def test_login_invalid_credentials(self):
        """POST /api/auth/login with invalid credentials should return 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✅ Invalid credentials correctly rejected")


class TestCustomReportAPI:
    """Test custom report generation endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    @pytest.fixture
    def employee_ids(self, auth_token):
        """Get list of employee IDs"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/users", headers=headers)
        if response.status_code == 200:
            users = response.json()
            return [u["id"] for u in users[:3]]  # Get first 3 employees
        return []
    
    def test_custom_report_excel_format(self, auth_token, employee_ids):
        """POST /api/attendance/custom-report with excel format should return file_content"""
        if not employee_ids:
            pytest.skip("No employees found")
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        payload = {
            "employee_ids": employee_ids,
            "start_date": "2025-01-01",
            "end_date": "2025-01-31",
            "format": "excel"
        }
        
        response = requests.post(f"{BASE_URL}/api/attendance/custom-report", 
                                 json=payload, headers=headers)
        
        assert response.status_code == 200, f"Custom report failed: {response.status_code} - {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "file_content" in data, f"No file_content in response: {data.keys()}"
        assert "filename" in data, f"No filename in response"
        assert "content_type" in data, f"No content_type in response"
        
        # Verify file_content is valid base64
        try:
            decoded = base64.b64decode(data["file_content"])
            assert len(decoded) > 0, "Decoded file is empty"
            print(f"✅ Custom report generated: {data['filename']} ({len(decoded)} bytes)")
        except Exception as e:
            pytest.fail(f"Invalid base64 content: {e}")
        
        # Verify filename has correct extension
        assert data["filename"].endswith(".xlsx"), f"Expected .xlsx file, got {data['filename']}"
        
        return data
    
    def test_custom_report_csv_format(self, auth_token, employee_ids):
        """POST /api/attendance/custom-report with csv format should return file_content"""
        if not employee_ids:
            pytest.skip("No employees found")
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        payload = {
            "employee_ids": employee_ids,
            "start_date": "2025-01-01",
            "end_date": "2025-01-31",
            "format": "csv"
        }
        
        response = requests.post(f"{BASE_URL}/api/attendance/custom-report", 
                                 json=payload, headers=headers)
        
        assert response.status_code == 200, f"Custom report failed: {response.status_code} - {response.text}"
        data = response.json()
        
        assert "file_content" in data, f"No file_content in response"
        assert data["filename"].endswith(".csv"), f"Expected .csv file, got {data['filename']}"
        print(f"✅ CSV report generated: {data['filename']}")
    
    def test_custom_report_no_employees_error(self, auth_token):
        """POST /api/attendance/custom-report with empty employee_ids should fail"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        payload = {
            "employee_ids": [],
            "start_date": "2025-01-01",
            "end_date": "2025-01-31",
            "format": "excel"
        }
        
        response = requests.post(f"{BASE_URL}/api/attendance/custom-report", 
                                 json=payload, headers=headers)
        
        # Should return 400 or similar error
        assert response.status_code in [400, 422], f"Expected error for empty employees, got {response.status_code}"
        print("✅ Empty employee_ids correctly rejected")


class TestTimeParsingRobustness:
    """Test that backend handles various time formats without crashing"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_attendance_endpoint_loads(self, auth_token):
        """GET /api/attendance should load without time parsing errors"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/attendance", headers=headers)
        
        assert response.status_code == 200, f"Attendance endpoint failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"✅ Attendance endpoint loaded successfully ({len(data)} records)")
    
    def test_attendance_with_absences_endpoint(self, auth_token):
        """GET /api/attendance/with-absences should load without errors"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/attendance/with-absences", headers=headers)
        
        assert response.status_code == 200, f"Attendance with absences failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"✅ Attendance with absences loaded ({len(data)} records)")
    
    def test_users_endpoint(self, auth_token):
        """GET /api/users should return list of employees"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/users", headers=headers)
        
        assert response.status_code == 200, f"Users endpoint failed: {response.status_code}"
        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        assert len(data) > 0, "No users found"
        print(f"✅ Users endpoint returned {len(data)} employees")


class TestAttendanceManagement:
    """Test attendance management endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_attendance_list(self, auth_token):
        """GET /api/attendance should return attendance records"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/attendance", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            record = data[0]
            # Verify record structure
            assert "id" in record, "Missing id field"
            assert "user_id" in record or "user_name" in record, "Missing user identifier"
            print(f"✅ Attendance list returned {len(data)} records")
        else:
            print("⚠️ No attendance records found (may be expected)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
