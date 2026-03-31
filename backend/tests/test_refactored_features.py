"""
Test Suite for Refactored TANSEEQ HR App - Iteration 2
Tests for:
1. Login as super admin
2. Dashboard loads correctly
3. Attendance Management page
4. Advances & Loans - POST /api/advances/request
5. Payroll - GET /api/payroll/cycles
6. Payroll Export - GET /api/payroll/cycles/{id}/export/excel
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
    """Authentication tests - Login as super admin"""
    
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
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@tanseeq.com",
            "password": "ADMIN"
        })
        token = login_response.json()["access_token"]
        
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        
        assert response.status_code == 200, f"Auth me failed: {response.text}"
        data = response.json()
        assert data["role"] == "super_admin"
        print(f"✅ Auth/me working - User: {data['name']}, Role: {data['role']}")


class TestDashboard:
    """Dashboard tests - verify dashboard data loads"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@tanseeq.com",
            "password": "ADMIN"
        })
        return response.json()["access_token"]
    
    def test_users_list(self, admin_token):
        """Test fetching users list for dashboard stats"""
        response = requests.get(f"{BASE_URL}/api/users", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code == 200, f"Failed to get users: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of users"
        assert len(data) > 0, "Expected at least one user"
        print(f"✅ Got {len(data)} users for dashboard")
    
    def test_attendance_list(self, admin_token):
        """Test fetching attendance records for dashboard"""
        response = requests.get(f"{BASE_URL}/api/attendance", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code == 200, f"Failed to get attendance: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of attendance records"
        print(f"✅ Got {len(data)} attendance records")
    
    def test_leaves_list(self, admin_token):
        """Test fetching leaves for dashboard"""
        response = requests.get(f"{BASE_URL}/api/leaves", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code == 200, f"Failed to get leaves: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of leaves"
        print(f"✅ Got {len(data)} leave records")
    
    def test_field_exits_list(self, admin_token):
        """Test fetching field exits for dashboard"""
        response = requests.get(f"{BASE_URL}/api/field-exits", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code == 200, f"Failed to get field exits: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of field exits"
        print(f"✅ Got {len(data)} field exit records")


class TestAttendanceManagement:
    """Attendance Management tests - verify the refactored component works"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@tanseeq.com",
            "password": "ADMIN"
        })
        return response.json()["access_token"]
    
    def test_attendance_with_absences(self, admin_token):
        """Test fetching attendance with absences (used by AttendanceManagement component)"""
        response = requests.get(f"{BASE_URL}/api/attendance/with-absences", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code == 200, f"Failed to get attendance with absences: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of attendance records"
        print(f"✅ Got {len(data)} attendance records with absences")
    
    def test_missing_today(self, admin_token):
        """Test fetching missing employees today"""
        response = requests.get(f"{BASE_URL}/api/attendance/missing-today", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code == 200, f"Failed to get missing today: {response.text}"
        data = response.json()
        assert "missing_employees" in data, "Expected missing_employees in response"
        print(f"✅ Got {len(data['missing_employees'])} missing employees today")


class TestAdvancesLoans:
    """Advances & Loans tests - POST /api/advances/request"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@tanseeq.com",
            "password": "ADMIN"
        })
        return response.json()["access_token"]
    
    def test_my_balance(self, admin_token):
        """Test fetching user's advance balance"""
        response = requests.get(f"{BASE_URL}/api/advances/my-balance", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code == 200, f"Failed to get balance: {response.text}"
        data = response.json()
        # Check expected fields
        assert "total_advances" in data or "employee_id" in data, "Expected balance data"
        print(f"✅ Got advance balance data")
    
    def test_my_transactions(self, admin_token):
        """Test fetching user's transactions"""
        response = requests.get(f"{BASE_URL}/api/advances/my-transactions?limit=5", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code == 200, f"Failed to get transactions: {response.text}"
        data = response.json()
        assert "transactions" in data, "Expected transactions in response"
        print(f"✅ Got {len(data['transactions'])} transactions")
    
    def test_advance_request_endpoint(self, admin_token):
        """Test POST /api/advances/request endpoint - create advance request"""
        payload = {
            "transaction_type": "advance",
            "amount": 100.00,
            "description": "TEST_advance_request_for_testing",
            "notes": "This is a test advance request",
            "expense_date": "2025-01-15"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/advances/request",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Should return 200 or 201 for success
        assert response.status_code in [200, 201], f"Advance request failed: {response.status_code} - {response.text}"
        data = response.json()
        assert data.get("success") == True or "transaction" in data or "id" in data, f"Expected success response, got: {data}"
        print(f"✅ Advance request endpoint working - Response: {data.get('message', 'OK')}")
    
    def test_custody_request_endpoint(self, admin_token):
        """Test POST /api/advances/request endpoint - create custody request"""
        payload = {
            "transaction_type": "custody",
            "amount": 50.00,
            "description": "TEST_custody_request_for_testing",
            "notes": "This is a test custody request",
            "expense_date": "2025-01-15"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/advances/request",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Should return 200 or 201 for success
        assert response.status_code in [200, 201], f"Custody request failed: {response.status_code} - {response.text}"
        data = response.json()
        assert data.get("success") == True or "transaction" in data or "id" in data, f"Expected success response, got: {data}"
        print(f"✅ Custody request endpoint working - Response: {data.get('message', 'OK')}")


class TestPayrollCycles:
    """Payroll Cycles tests - GET /api/payroll/cycles and export"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@tanseeq.com",
            "password": "ADMIN"
        })
        return response.json()["access_token"]
    
    def test_payroll_cycles_list(self, admin_token):
        """Test GET /api/payroll/cycles - list all payroll cycles"""
        response = requests.get(f"{BASE_URL}/api/payroll/cycles", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code == 200, f"Failed to get payroll cycles: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of payroll cycles"
        print(f"✅ Got {len(data)} payroll cycles")
        return data
    
    def test_payroll_cycle_detail(self, admin_token):
        """Test GET /api/payroll/cycles/{id} - get single cycle detail"""
        # First get list of cycles
        cycles_response = requests.get(f"{BASE_URL}/api/payroll/cycles", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        cycles = cycles_response.json()
        
        if len(cycles) == 0:
            pytest.skip("No payroll cycles available to test")
        
        cycle_id = cycles[0]["id"]
        
        response = requests.get(f"{BASE_URL}/api/payroll/cycles/{cycle_id}", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code == 200, f"Failed to get cycle detail: {response.text}"
        data = response.json()
        assert "id" in data, "Expected id in cycle detail"
        print(f"✅ Got payroll cycle detail: {data.get('display_name', data.get('month', 'N/A'))}")
    
    def test_payroll_cycle_export_excel(self, admin_token):
        """Test GET /api/payroll/cycles/{id}/export/excel - export cycle to Excel"""
        # First get list of cycles
        cycles_response = requests.get(f"{BASE_URL}/api/payroll/cycles", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        cycles = cycles_response.json()
        
        if len(cycles) == 0:
            pytest.skip("No payroll cycles available to test export")
        
        cycle_id = cycles[0]["id"]
        
        response = requests.get(
            f"{BASE_URL}/api/payroll/cycles/{cycle_id}/export/excel",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Should return 200 with Excel file or 404 if no data
        assert response.status_code in [200, 404], f"Export failed: {response.status_code} - {response.text}"
        
        if response.status_code == 200:
            # Check content type for Excel
            content_type = response.headers.get('content-type', '')
            assert 'spreadsheet' in content_type or 'octet-stream' in content_type or len(response.content) > 0, \
                f"Expected Excel file, got content-type: {content_type}"
            print(f"✅ Payroll Excel export working - Size: {len(response.content)} bytes")
        else:
            print(f"⚠️ Payroll export returned 404 - no data for this cycle")
    
    def test_payroll_cycle_summary(self, admin_token):
        """Test GET /api/payroll/cycles/{id}/summary - get cycle summary"""
        # First get list of cycles
        cycles_response = requests.get(f"{BASE_URL}/api/payroll/cycles", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        cycles = cycles_response.json()
        
        if len(cycles) == 0:
            pytest.skip("No payroll cycles available to test summary")
        
        cycle_id = cycles[0]["id"]
        
        response = requests.get(
            f"{BASE_URL}/api/payroll/cycles/{cycle_id}/summary",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Should return 200 or 404 if no employee summaries
        assert response.status_code in [200, 404], f"Summary failed: {response.status_code} - {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Payroll cycle summary working - Employees: {len(data.get('employee_summaries', []))}")
        else:
            print(f"⚠️ Payroll summary returned 404 - no employee data for this cycle")


class TestNotifications:
    """Notification system tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@tanseeq.com",
            "password": "ADMIN"
        })
        return response.json()["access_token"]
    
    def test_notifications_count(self, admin_token):
        """Test GET /api/notifications/count - get unread count"""
        response = requests.get(f"{BASE_URL}/api/notifications/count", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code == 200, f"Failed to get notification count: {response.text}"
        data = response.json()
        assert "unread_count" in data, "Expected unread_count in response"
        print(f"✅ Notification count: {data['unread_count']}")
    
    def test_my_notifications(self, admin_token):
        """Test GET /api/notifications/my - get user's notifications"""
        response = requests.get(f"{BASE_URL}/api/notifications/my", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code == 200, f"Failed to get notifications: {response.text}"
        data = response.json()
        # API returns either a list or a dict with 'notifications' key
        if isinstance(data, dict):
            notifications = data.get("notifications", [])
        else:
            notifications = data
        assert isinstance(notifications, list), "Expected list of notifications"
        print(f"✅ Got {len(notifications)} notifications")


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
        assert response.status_code in [200, 503], f"Unexpected status: {response.status_code}"
        print(f"✅ Readiness check returned: {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
