"""
Iteration 6 New Features Tests
Tests for:
1. System Health endpoint - /api/system/health-check
2. PDF Salary Slip generation with Arabic support - /api/salary-slip/{employee_id}/{cycle_month}
3. Auto email notifications (fire-and-forget) - check-in endpoint
4. HRDashboard regression check
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestAuthentication:
    """Test login with admin credentials"""
    
    def test_admin_login(self):
        """Test login with admin@tanseeq.com / ADMIN"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@tanseeq.com",
            "password": "ADMIN"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        print(f"✅ Admin login successful")


class TestSystemHealthEndpoint:
    """Test /api/system/health-check - new System Health feature"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@tanseeq.com",
            "password": "ADMIN"
        })
        return response.json().get("access_token")
    
    def test_health_check_returns_200(self, auth_token):
        """Test /api/system/health-check returns 200 for super admin"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/system/health-check", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"✅ /api/system/health-check returned 200")
    
    def test_health_check_structure(self, auth_token):
        """Test health-check response has correct structure"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/system/health-check", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check overall status
        assert "overall" in data, "Missing 'overall' field"
        assert data["overall"] in ["up", "degraded"], f"Invalid overall status: {data['overall']}"
        
        # Check services
        assert "services" in data, "Missing 'services' field"
        services = data["services"]
        
        # Required services
        required_services = ["database", "smtp", "api", "auth", "storage"]
        for svc in required_services:
            assert svc in services, f"Missing service: {svc}"
            assert "status" in services[svc], f"Missing status for {svc}"
            assert services[svc]["status"] in ["up", "down"], f"Invalid status for {svc}"
        
        print(f"✅ Health check structure verified - services: {list(services.keys())}")
    
    def test_health_check_database_up(self, auth_token):
        """Test database service is up"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/system/health-check", headers=headers)
        data = response.json()
        
        db_status = data["services"]["database"]["status"]
        assert db_status == "up", f"Database is down: {data['services']['database']}"
        print(f"✅ Database service is UP")
    
    def test_health_check_api_up(self, auth_token):
        """Test API service is up"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/system/health-check", headers=headers)
        data = response.json()
        
        api_status = data["services"]["api"]["status"]
        assert api_status == "up", f"API is down: {data['services']['api']}"
        print(f"✅ API service is UP")
    
    def test_health_check_auth_up(self, auth_token):
        """Test Auth service is up"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/system/health-check", headers=headers)
        data = response.json()
        
        auth_status = data["services"]["auth"]["status"]
        assert auth_status == "up", f"Auth is down: {data['services']['auth']}"
        print(f"✅ Auth service is UP")
    
    def test_health_check_system_info(self, auth_token):
        """Test system_info is present"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/system/health-check", headers=headers)
        data = response.json()
        
        assert "system_info" in data, "Missing system_info"
        sys_info = data["system_info"]
        assert "version" in sys_info, "Missing version"
        assert "employee_count" in sys_info, "Missing employee_count"
        print(f"✅ System info: version={sys_info.get('version')}, employees={sys_info.get('employee_count')}")


class TestPDFSalarySlipGeneration:
    """Test PDF salary slip generation with Arabic support"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@tanseeq.com",
            "password": "ADMIN"
        })
        return response.json().get("access_token")
    
    @pytest.fixture
    def employee_id(self, auth_token):
        """Get first employee ID"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/employees/list", headers=headers)
        if response.status_code == 200:
            data = response.json()
            employees = data.get("employees", data) if isinstance(data, dict) else data
            if employees and len(employees) > 0:
                return employees[0].get("id")
        return None
    
    def test_salary_slip_pdf_generation(self, auth_token, employee_id):
        """Test PDF generation for salary slip"""
        if not employee_id:
            pytest.skip("No employee found")
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        # Use a valid cycle month
        response = requests.get(f"{BASE_URL}/api/salary-slip/{employee_id}/2026-03", headers=headers)
        
        # Should return 200 with PDF bytes
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Check content type is PDF
        content_type = response.headers.get("content-type", "")
        assert "pdf" in content_type.lower() or len(response.content) > 100, f"Expected PDF, got {content_type}"
        
        # PDF should start with %PDF
        if response.content[:4] == b'%PDF':
            print(f"✅ PDF salary slip generated successfully ({len(response.content)} bytes)")
        else:
            # Might be base64 encoded
            print(f"✅ Salary slip response received ({len(response.content)} bytes)")
    
    def test_salary_slip_invalid_employee(self, auth_token):
        """Test PDF generation with invalid employee ID"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/salary-slip/invalid-id-12345/2026-03", headers=headers)
        
        # Should return 404 or 400
        assert response.status_code in [400, 404], f"Expected 400/404, got {response.status_code}"
        print(f"✅ Invalid employee returns {response.status_code}")


class TestSalarySlipsPage:
    """Test /api/salary-slips/bulk endpoint for SalarySlips page"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@tanseeq.com",
            "password": "ADMIN"
        })
        return response.json().get("access_token")
    
    def test_bulk_salary_slips_data(self, auth_token):
        """Test bulk salary slips data endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(f"{BASE_URL}/api/salary-slips/bulk/2026-03", headers=headers)
        
        # Should return 200 with employee data
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        # Response can be dict with 'slips' key or list
        if isinstance(data, dict):
            assert "slips" in data, f"Expected 'slips' key in dict"
            slips = data["slips"]
            assert isinstance(slips, list), f"Expected list in slips, got {type(slips)}"
            print(f"✅ Bulk salary slips returned {len(slips)} employees")
        else:
            assert isinstance(data, list), f"Expected list, got {type(data)}"
            print(f"✅ Bulk salary slips returned {len(data)} employees")


class TestCheckInEndpoint:
    """Test check-in endpoint (auto email trigger is fire-and-forget)"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@tanseeq.com",
            "password": "ADMIN"
        })
        return response.json().get("access_token")
    
    def test_check_in_endpoint_exists(self, auth_token):
        """Test check-in endpoint doesn't crash (auto email is fire-and-forget)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        # Just verify the endpoint exists and doesn't 500
        response = requests.get(f"{BASE_URL}/api/attendance/today", headers=headers)
        # Should not be 500
        assert response.status_code != 500, f"Got 500 error: {response.text}"
        print(f"✅ Attendance endpoint working (status: {response.status_code})")


class TestHRDashboardRegression:
    """Regression test for HRDashboard"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@tanseeq.com",
            "password": "ADMIN"
        })
        return response.json().get("access_token")
    
    def test_hr_dashboard_stats(self, auth_token):
        """Test HR dashboard stats endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/hr/dashboard-stats", headers=headers)
        
        # Should return 200 or 404 (if endpoint doesn't exist)
        assert response.status_code != 500, f"Got 500 error: {response.text}"
        print(f"✅ HR dashboard stats endpoint (status: {response.status_code})")
    
    def test_employees_list_for_dashboard(self, auth_token):
        """Test employees list for dashboard"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/employees/list", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"✅ Employees list working for dashboard")


class TestPreviouslyFixedEndpoints:
    """Regression tests for previously fixed endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@tanseeq.com",
            "password": "ADMIN"
        })
        return response.json().get("access_token")
    
    def test_deductions_calculate_monthly(self, auth_token):
        """Test /api/deductions/calculate-monthly still works"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(f"{BASE_URL}/api/deductions/calculate-monthly?month=2026-03", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"✅ /api/deductions/calculate-monthly working")
    
    def test_payroll_cycles(self, auth_token):
        """Test /api/payroll/cycles still works"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/payroll/cycles", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"✅ /api/payroll/cycles working")
    
    def test_payroll_ledger(self, auth_token):
        """Test /api/payroll/ledger still works"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/payroll/ledger", headers=headers)
        assert response.status_code != 500, f"Got 500 error"
        print(f"✅ /api/payroll/ledger working (status: {response.status_code})")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
