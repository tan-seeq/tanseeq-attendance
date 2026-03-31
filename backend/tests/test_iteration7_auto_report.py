"""
Iteration 7 - Auto Monthly Report System Tests
Tests for:
1. GET /api/payroll/auto-report-config - Get auto-report configuration
2. PUT /api/payroll/auto-report-config - Update auto-report configuration
3. POST /api/payroll/send-monthly-reports - Manual trigger (background task)
4. GET /api/payroll/auto-report-history - Get history of report runs
5. Regression: HR Dashboard, System Health page
"""

import pytest
import requests
import os
import time

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


class TestAutoReportConfig:
    """Test /api/payroll/auto-report-config endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@tanseeq.com",
            "password": "ADMIN"
        })
        return response.json().get("access_token")
    
    def test_get_auto_report_config(self, auth_token):
        """Test GET /api/payroll/auto-report-config returns config with enabled, day_of_month, last_run"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/payroll/auto-report-config", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify required fields
        assert "enabled" in data, "Missing 'enabled' field"
        assert "day_of_month" in data, "Missing 'day_of_month' field"
        assert isinstance(data["enabled"], bool), f"enabled should be bool, got {type(data['enabled'])}"
        assert isinstance(data["day_of_month"], int), f"day_of_month should be int, got {type(data['day_of_month'])}"
        
        # last_run can be null or object
        assert "last_run" in data, "Missing 'last_run' field"
        
        print(f"✅ GET /api/payroll/auto-report-config - enabled={data['enabled']}, day={data['day_of_month']}")
    
    def test_update_auto_report_config_enable(self, auth_token):
        """Test PUT /api/payroll/auto-report-config with enabled=true, day_of_month=28"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Enable auto-report on day 28
        response = requests.put(f"{BASE_URL}/api/payroll/auto-report-config", 
            headers=headers,
            json={"enabled": True, "day_of_month": 28}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data.get("success") == True, f"Expected success=True, got {data}"
        assert data.get("enabled") == True, f"Expected enabled=True, got {data.get('enabled')}"
        assert data.get("day_of_month") == 28, f"Expected day_of_month=28, got {data.get('day_of_month')}"
        
        print(f"✅ PUT /api/payroll/auto-report-config - enabled=True, day=28")
    
    def test_update_auto_report_config_disable(self, auth_token):
        """Test PUT /api/payroll/auto-report-config with enabled=false"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Disable auto-report
        response = requests.put(f"{BASE_URL}/api/payroll/auto-report-config", 
            headers=headers,
            json={"enabled": False, "day_of_month": 15}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data.get("success") == True, f"Expected success=True, got {data}"
        assert data.get("enabled") == False, f"Expected enabled=False, got {data.get('enabled')}"
        
        print(f"✅ PUT /api/payroll/auto-report-config - disabled successfully")
    
    def test_update_auto_report_config_day_clamping(self, auth_token):
        """Test that day_of_month is clamped to 1-28 range"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Try day > 28 (should be clamped to 28)
        response = requests.put(f"{BASE_URL}/api/payroll/auto-report-config", 
            headers=headers,
            json={"enabled": True, "day_of_month": 31}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("day_of_month") == 28, f"Expected day clamped to 28, got {data.get('day_of_month')}"
        
        print(f"✅ Day clamping works - 31 clamped to 28")


class TestSendMonthlyReports:
    """Test /api/payroll/send-monthly-reports endpoint (manual trigger)"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@tanseeq.com",
            "password": "ADMIN"
        })
        return response.json().get("access_token")
    
    def test_send_monthly_reports_returns_immediately(self, auth_token):
        """Test POST /api/payroll/send-monthly-reports returns success immediately (background task)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/api/payroll/send-monthly-reports", 
            headers=headers,
            json={"cycle_month": "2026-03"}
        )
        elapsed = time.time() - start_time
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Should return success immediately (background task)
        assert data.get("success") == True, f"Expected success=True, got {data}"
        assert data.get("cycle_month") == "2026-03", f"Expected cycle_month=2026-03, got {data.get('cycle_month')}"
        assert "message" in data, "Missing message field"
        
        # Should return quickly (< 5 seconds) since it runs in background
        assert elapsed < 5, f"Request took too long ({elapsed:.2f}s) - should return immediately"
        
        print(f"✅ POST /api/payroll/send-monthly-reports - returned in {elapsed:.2f}s (background task)")
    
    def test_send_monthly_reports_default_cycle(self, auth_token):
        """Test POST /api/payroll/send-monthly-reports with empty cycle_month uses current month"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.post(f"{BASE_URL}/api/payroll/send-monthly-reports", 
            headers=headers,
            json={}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data.get("success") == True, f"Expected success=True, got {data}"
        # cycle_month should be set to current month
        assert "cycle_month" in data, "Missing cycle_month in response"
        
        print(f"✅ POST /api/payroll/send-monthly-reports - default cycle_month={data.get('cycle_month')}")


class TestAutoReportHistory:
    """Test /api/payroll/auto-report-history endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@tanseeq.com",
            "password": "ADMIN"
        })
        return response.json().get("access_token")
    
    def test_get_auto_report_history(self, auth_token):
        """Test GET /api/payroll/auto-report-history returns runs array"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/payroll/auto-report-history", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Should have runs array
        assert "runs" in data, "Missing 'runs' field"
        assert isinstance(data["runs"], list), f"runs should be list, got {type(data['runs'])}"
        
        print(f"✅ GET /api/payroll/auto-report-history - {len(data['runs'])} runs found")
    
    def test_auto_report_history_structure(self, auth_token):
        """Test that history runs have correct structure (sent/failed/total)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First trigger a send to ensure we have history
        requests.post(f"{BASE_URL}/api/payroll/send-monthly-reports", 
            headers=headers,
            json={"cycle_month": "2026-03"}
        )
        
        # Wait a bit for background task to complete
        time.sleep(3)
        
        response = requests.get(f"{BASE_URL}/api/payroll/auto-report-history", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        if len(data["runs"]) > 0:
            run = data["runs"][0]
            # Verify structure
            assert "sent" in run, "Missing 'sent' field in run"
            assert "failed" in run, "Missing 'failed' field in run"
            assert "total" in run, "Missing 'total' field in run"
            assert "cycle_month" in run, "Missing 'cycle_month' field in run"
            assert "triggered_by" in run, "Missing 'triggered_by' field in run"
            assert "run_at" in run, "Missing 'run_at' field in run"
            
            print(f"✅ History run structure verified - sent={run['sent']}, failed={run['failed']}, total={run['total']}")
        else:
            print(f"⚠️ No history runs found yet")


class TestRegressionHRDashboard:
    """Regression tests for HR Dashboard"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@tanseeq.com",
            "password": "ADMIN"
        })
        return response.json().get("access_token")
    
    def test_employees_list(self, auth_token):
        """Test /api/employees/list still works"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/employees/list", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"✅ /api/employees/list working")
    
    def test_hr_dashboard_stats(self, auth_token):
        """Test HR dashboard stats endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/hr/dashboard-stats", headers=headers)
        
        assert response.status_code != 500, f"Got 500 error: {response.text}"
        print(f"✅ HR dashboard stats endpoint (status: {response.status_code})")


class TestRegressionSystemHealth:
    """Regression tests for System Health page"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@tanseeq.com",
            "password": "ADMIN"
        })
        return response.json().get("access_token")
    
    def test_system_health_check(self, auth_token):
        """Test /api/system/health-check still works"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/system/health-check", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "overall" in data, "Missing 'overall' field"
        assert "services" in data, "Missing 'services' field"
        
        print(f"✅ /api/system/health-check working - overall={data['overall']}")


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
    
    def test_salary_slip_generation(self, auth_token):
        """Test PDF salary slip generation still works"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get first employee
        emp_response = requests.get(f"{BASE_URL}/api/employees/list", headers=headers)
        if emp_response.status_code == 200:
            data = emp_response.json()
            employees = data.get("employees", data) if isinstance(data, dict) else data
            if employees and len(employees) > 0:
                emp_id = employees[0].get("id")
                
                # Generate salary slip
                response = requests.get(f"{BASE_URL}/api/salary-slip/{emp_id}/2026-03", headers=headers)
                assert response.status_code == 200, f"Expected 200, got {response.status_code}"
                print(f"✅ PDF salary slip generation working")
                return
        
        print(f"⚠️ No employees found to test salary slip")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
