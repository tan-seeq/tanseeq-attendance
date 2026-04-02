"""
Push Notifications API Tests - Iteration 11
Tests for PWA Push Notification endpoints:
- GET /api/push/vapid-key
- POST /api/push/subscribe
- POST /api/push/unsubscribe
- GET /api/push/settings
- POST /api/push/settings (admin only)
- GET /api/push/stats
- POST /api/push/test
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@tanseeq.com"
ADMIN_PASSWORD = "ADMIN"


class TestHealthCheck:
    """Basic health check to ensure API is running"""
    
    def test_health_endpoint(self):
        response = requests.get(f"{BASE_URL}/api/healthz")
        assert response.status_code == 200, f"Health check failed: {response.text}"
        print("✅ Health check passed")


class TestPushVapidKey:
    """Test GET /api/push/vapid-key endpoint"""
    
    def test_get_vapid_key_returns_public_key(self):
        """VAPID key endpoint should return public_key string"""
        response = requests.get(f"{BASE_URL}/api/push/vapid-key")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "public_key" in data, "Response should contain 'public_key'"
        assert isinstance(data["public_key"], str), "public_key should be a string"
        assert len(data["public_key"]) > 0, "public_key should not be empty"
        print(f"✅ VAPID public key returned: {data['public_key'][:20]}...")


class TestPushSubscription:
    """Test push subscription endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json().get("access_token")
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Return headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_subscribe_with_valid_subscription(self, auth_headers):
        """POST /api/push/subscribe should accept valid subscription object"""
        # Create a fake subscription object (mimics browser push subscription)
        fake_subscription = {
            "subscription": {
                "endpoint": f"https://fake.pushservice.com/test-{uuid.uuid4()}",
                "keys": {
                    "p256dh": "test_p256dh_key_value",
                    "auth": "test_auth_key_value"
                }
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/push/subscribe",
            json=fake_subscription,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "status" in data, "Response should contain 'status'"
        assert data["status"] in ["subscribed", "already_subscribed"], f"Unexpected status: {data['status']}"
        print(f"✅ Subscribe endpoint returned status: {data['status']}")
    
    def test_subscribe_without_endpoint_fails(self, auth_headers):
        """POST /api/push/subscribe should fail without endpoint"""
        invalid_subscription = {
            "subscription": {
                "keys": {"p256dh": "test", "auth": "test"}
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/push/subscribe",
            json=invalid_subscription,
            headers=auth_headers
        )
        assert response.status_code == 400, f"Expected 400 for invalid subscription, got {response.status_code}"
        print("✅ Subscribe correctly rejects invalid subscription")
    
    def test_unsubscribe_with_endpoint(self, auth_headers):
        """POST /api/push/unsubscribe should return status=unsubscribed"""
        response = requests.post(
            f"{BASE_URL}/api/push/unsubscribe",
            json={"endpoint": "https://fake.pushservice.com/test-endpoint"},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("status") == "unsubscribed", f"Expected status=unsubscribed, got {data}"
        print("✅ Unsubscribe endpoint returned status: unsubscribed")


class TestPushSettings:
    """Test push notification settings endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json().get("access_token")
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Return headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_get_settings_returns_defaults(self, auth_headers):
        """GET /api/push/settings should return default settings"""
        response = requests.get(
            f"{BASE_URL}/api/push/settings",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Check all expected fields exist
        expected_fields = ["late_notifications", "absence_notifications", "notify_employee", "notify_admin"]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
            assert isinstance(data[field], bool), f"{field} should be boolean"
        
        print(f"✅ Settings returned: {data}")
    
    def test_save_settings_as_admin(self, auth_headers):
        """POST /api/push/settings should save new settings (admin only)"""
        new_settings = {
            "late_notifications": True,
            "absence_notifications": True,
            "notify_employee": True,
            "notify_admin": True
        }
        
        response = requests.post(
            f"{BASE_URL}/api/push/settings",
            json=new_settings,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("status") == "saved", f"Expected status=saved, got {data}"
        print("✅ Settings saved successfully")
        
        # Verify settings were saved by fetching them
        verify_response = requests.get(
            f"{BASE_URL}/api/push/settings",
            headers=auth_headers
        )
        verify_data = verify_response.json()
        assert verify_data.get("late_notifications") == True
        assert verify_data.get("absence_notifications") == True
        print("✅ Settings verified after save")


class TestPushStats:
    """Test push notification statistics endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json().get("access_token")
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Return headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_get_stats_returns_counts(self, auth_headers):
        """GET /api/push/stats should return total_subscriptions and active_users"""
        response = requests.get(
            f"{BASE_URL}/api/push/stats",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "total_subscriptions" in data, "Response should contain 'total_subscriptions'"
        assert "active_users" in data, "Response should contain 'active_users'"
        assert isinstance(data["total_subscriptions"], int), "total_subscriptions should be int"
        assert isinstance(data["active_users"], int), "active_users should be int"
        
        print(f"✅ Stats returned: {data['total_subscriptions']} subscriptions, {data['active_users']} active users")


class TestPushTestNotification:
    """Test sending test push notification"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json().get("access_token")
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Return headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_send_test_notification(self, auth_headers):
        """POST /api/push/test should return message about notification status"""
        response = requests.post(
            f"{BASE_URL}/api/push/test",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should contain 'message'"
        # Message will indicate either success or no devices registered
        print(f"✅ Test notification response: {data['message']}")


class TestPushSubscriptionCleanup:
    """Cleanup test subscriptions after tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json().get("access_token")
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Return headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_cleanup_test_subscriptions(self, auth_headers):
        """Clean up any test subscriptions created during testing"""
        # Unsubscribe from any test endpoints
        response = requests.post(
            f"{BASE_URL}/api/push/unsubscribe",
            json={"endpoint": "https://fake.pushservice.com/test-endpoint"},
            headers=auth_headers
        )
        assert response.status_code == 200
        print("✅ Test subscriptions cleaned up")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
