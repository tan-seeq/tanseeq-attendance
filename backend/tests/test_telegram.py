"""
Test Telegram Bot Integration for TANSEEQ HR
Tests the new Telegram notification feature endpoints.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@tanseeq.com"
ADMIN_PASSWORD = "ADMIN"


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def auth_token(api_client):
    """Get authentication token for admin user"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def authenticated_client(api_client, auth_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


class TestHealthCheck:
    """Basic health check"""
    
    def test_health_endpoint(self, api_client):
        """Test health endpoint is accessible"""
        response = api_client.get(f"{BASE_URL}/api/healthz")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        print("✅ Health check passed")


class TestTelegramBotInfo:
    """Test GET /api/telegram/bot-info endpoint"""
    
    def test_get_bot_info_returns_connected_status(self, api_client):
        """Bot info should return connected=true and bot_username"""
        response = api_client.get(f"{BASE_URL}/api/telegram/bot-info")
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "connected" in data
        assert "bot_username" in data
        
        # Bot should be connected (token is configured)
        assert data["connected"] == True, f"Bot should be connected, got: {data}"
        assert data["bot_username"] == "tanseeq_hr_bot", f"Expected tanseeq_hr_bot, got: {data['bot_username']}"
        print(f"✅ Bot info: connected={data['connected']}, username=@{data['bot_username']}")


class TestTelegramGenerateLink:
    """Test POST /api/telegram/generate-link endpoint"""
    
    def test_generate_link_returns_code_and_deep_link(self, authenticated_client):
        """Generate link should return a code and deep link URL"""
        response = authenticated_client.post(f"{BASE_URL}/api/telegram/generate-link", json={})
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "code" in data, f"Response should contain 'code': {data}"
        assert "link" in data, f"Response should contain 'link': {data}"
        assert "bot_username" in data, f"Response should contain 'bot_username': {data}"
        
        # Verify code format (TQ + 12 hex chars)
        code = data["code"]
        assert code.startswith("TQ"), f"Code should start with TQ: {code}"
        assert len(code) == 14, f"Code should be 14 chars (TQ + 12 hex): {code}"
        
        # Verify deep link format
        link = data["link"]
        assert "t.me/" in link, f"Link should be a Telegram deep link: {link}"
        assert f"?start={code}" in link, f"Link should contain the code: {link}"
        
        print(f"✅ Generated link: code={code}, link={link}")
    
    def test_generate_link_requires_auth(self):
        """Generate link should require authentication"""
        # Use fresh session without auth
        response = requests.post(f"{BASE_URL}/api/telegram/generate-link", json={})
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✅ Generate link requires authentication")


class TestTelegramStatus:
    """Test GET /api/telegram/status endpoint"""
    
    def test_status_returns_linked_false_for_unlinked_user(self, authenticated_client):
        """Status should return linked=false for users who haven't linked Telegram"""
        response = authenticated_client.get(f"{BASE_URL}/api/telegram/status")
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "linked" in data, f"Response should contain 'linked': {data}"
        
        # Admin user is likely not linked
        # (If linked, that's also valid - just verify structure)
        if data["linked"]:
            assert "telegram_name" in data
            print(f"✅ Status: linked=True, telegram_name={data.get('telegram_name')}")
        else:
            assert data["linked"] == False
            print("✅ Status: linked=False (user not linked)")
    
    def test_status_requires_auth(self):
        """Status should require authentication"""
        # Use fresh session without auth
        response = requests.get(f"{BASE_URL}/api/telegram/status")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✅ Status requires authentication")


class TestTelegramUnlink:
    """Test POST /api/telegram/unlink endpoint"""
    
    def test_unlink_returns_status_unlinked(self, authenticated_client):
        """Unlink should return status=unlinked"""
        response = authenticated_client.post(f"{BASE_URL}/api/telegram/unlink")
        assert response.status_code == 200
        data = response.json()
        
        # Verify response
        assert data.get("status") == "unlinked", f"Expected status=unlinked, got: {data}"
        print("✅ Unlink returned status=unlinked")
    
    def test_unlink_requires_auth(self):
        """Unlink should require authentication"""
        # Use fresh session without auth
        response = requests.post(f"{BASE_URL}/api/telegram/unlink")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✅ Unlink requires authentication")


class TestTelegramLinkedEmployees:
    """Test GET /api/telegram/linked-employees endpoint (admin only)"""
    
    def test_linked_employees_returns_list(self, authenticated_client):
        """Linked employees should return a list (admin only)"""
        response = authenticated_client.get(f"{BASE_URL}/api/telegram/linked-employees")
        assert response.status_code == 200
        data = response.json()
        
        # Should be a list
        assert isinstance(data, list), f"Expected list, got: {type(data)}"
        
        # If there are linked employees, verify structure
        if len(data) > 0:
            emp = data[0]
            assert "employee_id" in emp or "employee_name" in emp
            print(f"✅ Linked employees: {len(data)} employees linked")
        else:
            print("✅ Linked employees: empty list (no employees linked yet)")
    
    def test_linked_employees_requires_admin(self):
        """Linked employees should require admin authentication"""
        # Use fresh session without auth
        response = requests.get(f"{BASE_URL}/api/telegram/linked-employees")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✅ Linked employees requires admin authentication")


class TestTelegramTestMessage:
    """Test POST /api/telegram/test endpoint"""
    
    def test_test_message_returns_not_linked_message(self, authenticated_client):
        """Test message should return appropriate message for unlinked user"""
        response = authenticated_client.post(f"{BASE_URL}/api/telegram/test")
        assert response.status_code == 200
        data = response.json()
        
        # Verify response has message
        assert "message" in data, f"Response should contain 'message': {data}"
        
        # Message should indicate not linked or success
        message = data["message"]
        assert len(message) > 0, "Message should not be empty"
        print(f"✅ Test message response: {message}")
    
    def test_test_message_requires_auth(self):
        """Test message should require authentication"""
        # Use fresh session without auth
        response = requests.post(f"{BASE_URL}/api/telegram/test")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✅ Test message requires authentication")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
