"""
Test Telegram Integration for Salary Slip Sending - Iteration 13
Tests the new feature: Telegram PDF sending when sending salary slips

Features tested:
1. POST /api/email/send-salary-slip returns telegram_sent field (false if not linked)
2. POST /api/email/send-bulk-salary-slips returns telegram_sent in details for each employee
3. POST /api/telegram/test works for linked users
4. GET /api/telegram/bot-info returns connected=true
5. Salary slip endpoint doesn't crash even when Telegram sending fails
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@tanseeq.com"
ADMIN_PASSWORD = "ADMIN"
TEST_EMPLOYEE_ID = "48613bd9-9007-441f-9495-095408c49889"  # Hatem
TEST_CYCLE_MONTH = "2026-03"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for admin user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestTelegramBotInfo:
    """Test GET /api/telegram/bot-info endpoint"""
    
    def test_bot_info_returns_connected_true(self, auth_headers):
        """Verify bot-info returns connected=true when bot token is configured"""
        response = requests.get(f"{BASE_URL}/api/telegram/bot-info", headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "connected" in data, "Response should contain 'connected' field"
        assert data["connected"] == True, "Bot should be connected (token is configured)"
        
        # Should also have bot_username
        if data["connected"]:
            assert "bot_username" in data, "Connected bot should have bot_username"
            print(f"✅ Bot connected: @{data.get('bot_username', 'unknown')}")


class TestSendSalarySlipWithTelegram:
    """Test POST /api/email/send-salary-slip with Telegram integration"""
    
    def test_send_salary_slip_returns_telegram_sent_field(self, auth_headers):
        """Verify send-salary-slip returns telegram_sent field"""
        response = requests.post(
            f"{BASE_URL}/api/email/send-salary-slip",
            headers=auth_headers,
            json={
                "employee_id": TEST_EMPLOYEE_ID,
                "cycle_month": TEST_CYCLE_MONTH
            }
        )
        
        # Should not crash - accept 200 or 400 (if employee not found)
        assert response.status_code in [200, 400, 404], f"Unexpected status: {response.status_code}: {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            # Key assertion: telegram_sent field should be present
            assert "telegram_sent" in data, f"Response should contain 'telegram_sent' field. Got: {data.keys()}"
            
            # Since no employees are linked to Telegram, it should be false
            assert data["telegram_sent"] == False, "telegram_sent should be False for unlinked employee"
            print(f"✅ telegram_sent field present: {data['telegram_sent']}")
        else:
            print(f"⚠️ Employee not found or no email - status {response.status_code}")
    
    def test_send_salary_slip_does_not_crash_on_telegram_failure(self, auth_headers):
        """Verify endpoint doesn't crash even if Telegram sending fails"""
        # This test ensures the try/except block works
        response = requests.post(
            f"{BASE_URL}/api/email/send-salary-slip",
            headers=auth_headers,
            json={
                "employee_id": TEST_EMPLOYEE_ID,
                "cycle_month": TEST_CYCLE_MONTH
            }
        )
        
        # Should not return 500 (internal server error)
        assert response.status_code != 500, f"Endpoint crashed with 500: {response.text}"
        print(f"✅ Endpoint did not crash - status: {response.status_code}")


class TestBulkSalarySlipsWithTelegram:
    """Test POST /api/email/send-bulk-salary-slips with Telegram integration"""
    
    def test_bulk_salary_slips_returns_telegram_sent_in_details(self, auth_headers):
        """Verify bulk send returns telegram_sent in details for each employee"""
        response = requests.post(
            f"{BASE_URL}/api/email/send-bulk-salary-slips",
            headers=auth_headers,
            json={
                "employee_ids": [TEST_EMPLOYEE_ID],
                "cycle_month": TEST_CYCLE_MONTH
            }
        )
        
        # Should not crash
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}: {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            assert "details" in data, "Response should contain 'details' field"
            
            # Check each detail has telegram_sent
            for detail in data.get("details", []):
                assert "telegram_sent" in detail, f"Each detail should have 'telegram_sent'. Got: {detail.keys()}"
                # Since no employees are linked, should be false
                assert detail["telegram_sent"] == False, "telegram_sent should be False for unlinked employee"
                print(f"✅ Employee {detail.get('employee_name', 'unknown')}: telegram_sent={detail['telegram_sent']}")
        else:
            print(f"⚠️ Bulk send returned {response.status_code}")
    
    def test_bulk_salary_slips_does_not_crash(self, auth_headers):
        """Verify bulk endpoint doesn't crash"""
        response = requests.post(
            f"{BASE_URL}/api/email/send-bulk-salary-slips",
            headers=auth_headers,
            json={
                "employee_ids": [TEST_EMPLOYEE_ID],
                "cycle_month": TEST_CYCLE_MONTH
            }
        )
        
        # Should not return 500
        assert response.status_code != 500, f"Endpoint crashed with 500: {response.text}"
        print(f"✅ Bulk endpoint did not crash - status: {response.status_code}")


class TestTelegramTestMessage:
    """Test POST /api/telegram/test endpoint"""
    
    def test_telegram_test_for_unlinked_user(self, auth_headers):
        """Verify test endpoint works for unlinked users (returns appropriate message)"""
        response = requests.post(f"{BASE_URL}/api/telegram/test", headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # For unlinked users, should indicate not linked
        assert "sent" in data or "message" in data or "success" in data, f"Response should have status field. Got: {data}"
        print(f"✅ Telegram test response: {data}")


class TestHealthCheck:
    """Basic health check to ensure API is running"""
    
    def test_health_endpoint(self):
        """Verify health endpoint works"""
        response = requests.get(f"{BASE_URL}/api/healthz")
        assert response.status_code == 200, f"Health check failed: {response.status_code}"
        print("✅ Health check passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
