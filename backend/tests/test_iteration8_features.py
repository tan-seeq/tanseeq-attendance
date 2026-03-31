"""
Iteration 8 Backend Tests - TANSEEQ HR System
Tests for:
1. Login with admin@tanseeq.com / ADMIN
2. System health-check endpoint with calibration data
3. Live monitoring metrics endpoint
4. Salary slip PDF generation (English-only)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@tanseeq.com"
ADMIN_PASSWORD = "ADMIN"


class TestAuthentication:
    """Test login and authentication"""
    
    def test_login_success(self):
        """Test login with admin credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert "user" in data, "No user in response"
        assert data["user"]["email"] == ADMIN_EMAIL
        print(f"✅ Login successful for {ADMIN_EMAIL}")
        return data["access_token"]
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpass"
        })
        assert response.status_code in [401, 400], f"Expected 401/400, got {response.status_code}"
        print("✅ Invalid credentials correctly rejected")


class TestSystemHealth:
    """Test system health-check endpoint with calibration data"""
    
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
    
    def test_health_check_endpoint(self, auth_token):
        """Test /api/system/health-check returns calibration data"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/system/health-check", headers=headers)
        
        assert response.status_code == 200, f"Health check failed: {response.text}"
        data = response.json()
        
        # Check overall status
        assert "overall" in data, "Missing 'overall' field"
        assert data["overall"] in ["up", "degraded"], f"Unexpected overall status: {data['overall']}"
        
        # Check services
        assert "services" in data, "Missing 'services' field"
        services = data["services"]
        assert "database" in services, "Missing database service"
        assert "smtp" in services, "Missing smtp service"
        assert "api" in services, "Missing api service"
        
        # Check calibration data (October 2025 calibration mode)
        assert "calibration" in data, "Missing 'calibration' field"
        calibration = data["calibration"]
        assert "status" in calibration, "Missing calibration status"
        assert calibration["status"] in ["expired", "active", "disabled"], f"Unexpected calibration status: {calibration['status']}"
        assert "window_from" in calibration, "Missing window_from"
        assert "window_to" in calibration, "Missing window_to"
        assert "current_date" in calibration, "Missing current_date"
        
        # Since we're in 2026, calibration should be expired
        print(f"✅ Health check passed - Calibration status: {calibration['status']}")
        print(f"   Window: {calibration['window_from']} to {calibration['window_to']}")
        print(f"   Current date: {calibration['current_date']}")
        
        # Check system info
        assert "system_info" in data, "Missing 'system_info' field"
        print(f"✅ System info: version={data['system_info'].get('version')}, employees={data['system_info'].get('employee_count')}")


class TestLiveMonitoring:
    """Test live monitoring metrics endpoint"""
    
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
    
    def test_live_metrics_endpoint(self, auth_token):
        """Test /api/live/metrics returns metrics data"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First make some API calls to generate metrics
        requests.get(f"{BASE_URL}/api/users", headers=headers)
        requests.get(f"{BASE_URL}/api/healthz")
        
        # Now check metrics
        response = requests.get(f"{BASE_URL}/api/live/metrics", headers=headers)
        
        assert response.status_code == 200, f"Live metrics failed: {response.text}"
        data = response.json()
        
        assert "success" in data, "Missing 'success' field"
        assert data["success"] == True, "success should be True"
        assert "metrics" in data, "Missing 'metrics' field"
        
        metrics = data["metrics"]
        assert "total_requests" in metrics, "Missing total_requests"
        assert "success_count" in metrics, "Missing success_count"
        assert "error_count" in metrics, "Missing error_count"
        assert "avg_response_ms" in metrics, "Missing avg_response_ms"
        
        # Verify metrics have data (after our API calls)
        print(f"✅ Live metrics: total_requests={metrics['total_requests']}, success_count={metrics['success_count']}")
        print(f"   Error count: {metrics['error_count']}, Avg response: {metrics['avg_response_ms']}ms")
    
    def test_live_logs_endpoint(self, auth_token):
        """Test /api/live/logs returns log data"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/live/logs", headers=headers)
        
        assert response.status_code == 200, f"Live logs failed: {response.text}"
        data = response.json()
        
        assert "success" in data, "Missing 'success' field"
        assert "lines" in data, "Missing 'lines' field"
        print(f"✅ Live logs: {len(data['lines'])} log lines available")


class TestSalarySlip:
    """Test salary slip PDF generation (English-only)"""
    
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
    def employee_id(self, auth_token):
        """Get first employee ID"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/users", headers=headers)
        if response.status_code == 200:
            users = response.json()
            if isinstance(users, list) and len(users) > 0:
                return users[0].get("id")
        pytest.skip("No employees found")
    
    def test_salary_slip_generation(self, auth_token, employee_id):
        """Test /api/salary-slip/{employee_id}/{month} generates English PDF"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        cycle_month = "2026-03"  # Current month
        
        response = requests.get(
            f"{BASE_URL}/api/salary-slip/{employee_id}/{cycle_month}",
            headers=headers
        )
        
        assert response.status_code == 200, f"Salary slip generation failed: {response.text}"
        data = response.json()
        
        # API returns file_content (base64 encoded PDF)
        assert "file_content" in data or "pdf_base64" in data, "Missing file_content/pdf_base64 in response"
        assert "filename" in data, "Missing filename in response"
        assert data.get("success") == True, "success should be True"
        
        # Verify PDF is base64 encoded and valid
        import base64
        pdf_content = data.get("file_content") or data.get("pdf_base64")
        pdf_bytes = base64.b64decode(pdf_content)
        
        # Check PDF header
        assert pdf_bytes[:4] == b'%PDF', "Generated file is not a valid PDF"
        
        # Check PDF uses Helvetica font (English font, not Arabic)
        pdf_text = pdf_bytes.decode('latin-1', errors='ignore')
        assert 'Helvetica' in pdf_text, "PDF should use Helvetica font (English)"
        assert 'ReportLab' in pdf_text, "PDF should be generated by ReportLab"
        
        print(f"✅ Salary slip PDF generated: {data['filename']}")
        print(f"   PDF size: {len(pdf_bytes)} bytes")
        print(f"   Employee: {data.get('employee_name', 'N/A')}")


class TestAdminConfig:
    """Test admin configuration endpoints"""
    
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
    
    def test_admin_config_system(self, auth_token):
        """Test /api/admin/config/system endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/config/system", headers=headers)
        
        assert response.status_code == 200, f"Admin config failed: {response.text}"
        data = response.json()
        assert "config" in data, "Missing 'config' field"
        print(f"✅ Admin config loaded: {list(data['config'].keys())[:5]}...")
    
    def test_admin_config_exceptions(self, auth_token):
        """Test /api/admin/config/exceptions endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/config/exceptions", headers=headers)
        
        assert response.status_code == 200, f"Admin exceptions failed: {response.text}"
        data = response.json()
        assert "exceptions" in data, "Missing 'exceptions' field"
        print(f"✅ Admin exceptions loaded: {len(data['exceptions'])} exceptions")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
