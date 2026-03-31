"""
Iteration 5 Bug Fix Tests
Tests for critical fixes:
1. /api/deductions/calculate-monthly - date overflow bug fix
2. /api/payroll/cycles - _id serialization fix
3. /api/payroll/ledger - endpoint fix
4. /api/email/preferences - endpoint fix
5. /api/email/test - try/except wrapper fix
6. /api/work-reports/clients - empty list fallback fix
7. /api/employees/list - employee list endpoint
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
        print(f"✅ Admin login successful, token received")
        return data["access_token"]


class TestDeductionsEndpoint:
    """Test /api/deductions/calculate-monthly - date overflow bug fix"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@tanseeq.com",
            "password": "ADMIN"
        })
        return response.json().get("access_token")
    
    def test_calculate_monthly_deductions_march_2026(self, auth_token):
        """Test calculate-monthly for March 2026 - should not 500"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/deductions/calculate-monthly?month=2026-03",
            headers=headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"✅ /api/deductions/calculate-monthly?month=2026-03 returned 200")
    
    def test_calculate_monthly_deductions_february_2024(self, auth_token):
        """Test calculate-monthly for Feb 2024 (leap year) - date overflow edge case"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/deductions/calculate-monthly?month=2024-02",
            headers=headers
        )
        # Should not crash with 500
        assert response.status_code in [200, 400, 404], f"Unexpected 500 error: {response.text}"
        print(f"✅ /api/deductions/calculate-monthly?month=2024-02 did not crash (status: {response.status_code})")


class TestPayrollEndpoints:
    """Test payroll endpoints - _id serialization and ledger fixes"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@tanseeq.com",
            "password": "ADMIN"
        })
        return response.json().get("access_token")
    
    def test_payroll_cycles_no_500(self, auth_token):
        """Test /api/payroll/cycles returns list without 500"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/payroll/cycles", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"✅ /api/payroll/cycles returned {len(data)} cycles")
    
    def test_payroll_ledger_no_500(self, auth_token):
        """Test /api/payroll/ledger returns success without 500"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/payroll/ledger", headers=headers)
        # Should not be 500
        assert response.status_code != 500, f"Got 500 error: {response.text}"
        print(f"✅ /api/payroll/ledger did not crash (status: {response.status_code})")


class TestEmailEndpoints:
    """Test email endpoints - preferences and test endpoint fixes"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@tanseeq.com",
            "password": "ADMIN"
        })
        return response.json().get("access_token")
    
    def test_email_preferences_no_500(self, auth_token):
        """Test /api/email/preferences returns preferences without 500"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/email/preferences", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"✅ /api/email/preferences returned 200")
    
    def test_email_test_no_500(self, auth_token):
        """Test /api/email/test returns response without 500 (even if SMTP fails)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(f"{BASE_URL}/api/email/test", headers=headers)
        # Should not be 500 - even if SMTP auth fails, should return success:false
        assert response.status_code != 500, f"Got 500 error: {response.text}"
        print(f"✅ /api/email/test did not crash (status: {response.status_code})")


class TestWorkReportsEndpoints:
    """Test work-reports endpoints - clients endpoint fix"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@tanseeq.com",
            "password": "ADMIN"
        })
        return response.json().get("access_token")
    
    def test_work_reports_clients_no_500(self, auth_token):
        """Test /api/work-reports/clients returns list without 500"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/work-reports/clients", headers=headers)
        # Should not be 500 - should return empty list on error
        assert response.status_code != 500, f"Got 500 error: {response.text}"
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list), f"Expected list, got {type(data)}"
            print(f"✅ /api/work-reports/clients returned {len(data)} clients")
        else:
            print(f"✅ /api/work-reports/clients did not crash (status: {response.status_code})")


class TestEmployeesEndpoint:
    """Test employees endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@tanseeq.com",
            "password": "ADMIN"
        })
        return response.json().get("access_token")
    
    def test_employees_list(self, auth_token):
        """Test /api/employees/list returns employees"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/employees/list", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        # API returns dict with 'employees' key
        if isinstance(data, dict) and "employees" in data:
            employees = data["employees"]
            assert isinstance(employees, list), f"Expected list in employees key, got {type(employees)}"
            print(f"✅ /api/employees/list returned {len(employees)} employees")
        else:
            assert isinstance(data, list), f"Expected list or dict with employees key, got {type(data)}"
            print(f"✅ /api/employees/list returned {len(data)} employees")
    
    def test_users_endpoint(self, auth_token):
        """Test /api/users returns users"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/users", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"✅ /api/users returned {len(data)} users")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
