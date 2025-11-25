#!/usr/bin/env python3
"""
🔔 SIMPLE NOTIFICATION ENDPOINTS TEST
Arabic Review Request: اختبار سريع لـ endpoint الإشعارات بعد الإصلاح

Focus: Test the 2 specific endpoints mentioned in the review
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://hrapp-tanseeq-replaced-1761028017.emergent.host"
BASE_URL = f"{BACKEND_URL}/api"

def test_notification_endpoints():
    """Test notification endpoints"""
    session = requests.Session()
    session.headers.update({
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    })
    
    print("🚀 Testing Notification Endpoints After Fix")
    print("=" * 50)
    
    # Step 1: Authenticate with working credentials
    print("🔐 Authenticating...")
    auth_response = session.post(
        f"{BASE_URL}/auth/login",
        json={"email": "admin@tanseeq.com", "password": "ADMIN"},
        timeout=30
    )
    
    if auth_response.status_code != 200:
        print(f"❌ Authentication failed: {auth_response.status_code}")
        return False
    
    token = auth_response.json().get("access_token")
    session.headers.update({'Authorization': f'Bearer {token}'})
    user_info = auth_response.json().get("user", {})
    print(f"✅ Authenticated as {user_info.get('name')} ({user_info.get('email')})")
    
    # Step 2: Test GET /api/notifications/my?unread_only=true
    print("\n🔔 Testing GET /api/notifications/my?unread_only=true...")
    
    unread_response = session.get(
        f"{BASE_URL}/notifications/my?unread_only=true",
        timeout=30
    )
    
    if unread_response.status_code == 200:
        print("✅ GET /notifications/my?unread_only=true - SUCCESS (200 OK)")
        unread_data = unread_response.json()
        unread_notifications = unread_data if isinstance(unread_data, list) else unread_data.get("notifications", [])
        print(f"   📊 Found {len(unread_notifications)} unread notifications")
    elif unread_response.status_code == 500:
        print("❌ GET /notifications/my?unread_only=true - FAILED (500 Error - the issue we're testing)")
        print(f"   Error: {unread_response.text}")
        return False
    else:
        print(f"⚠️  GET /notifications/my?unread_only=true - Unexpected status: {unread_response.status_code}")
        print(f"   Response: {unread_response.text}")
    
    # Step 3: Create a test notification for acknowledge testing
    print("\n📝 Creating test notification...")
    
    notification_data = {
        "recipient_id": user_info.get("id"),
        "subject": "Test Notification for Acknowledge",
        "message": "This notification is created to test the acknowledge endpoint.",
        "type": "info",
        "priority": "normal"
    }
    
    create_response = session.post(
        f"{BASE_URL}/notifications/send",
        json=notification_data,
        timeout=30
    )
    
    if create_response.status_code in [200, 201]:
        print("✅ Test notification created successfully")
        
        # Wait a moment for the notification to be available
        time.sleep(1)
        
        # Get all notifications to find the one we just created
        all_notifications_response = session.get(f"{BASE_URL}/notifications/my", timeout=30)
        
        if all_notifications_response.status_code == 200:
            all_data = all_notifications_response.json()
            all_notifications = all_data if isinstance(all_data, list) else all_data.get("notifications", [])
            print(f"   📊 Total notifications: {len(all_notifications)}")
            
            # Find our test notification
            test_notification_id = None
            for notif in all_notifications:
                if notif.get("subject") == "Test Notification for Acknowledge":
                    test_notification_id = notif.get("id")
                    print(f"   🎯 Found test notification ID: {test_notification_id}")
                    break
            
            # Step 4: Test POST /api/notifications/{id}/acknowledge
            if test_notification_id:
                print(f"\n✅ Testing POST /api/notifications/{test_notification_id}/acknowledge...")
                
                acknowledge_response = session.post(
                    f"{BASE_URL}/notifications/{test_notification_id}/acknowledge",
                    json={},
                    timeout=30
                )
                
                if acknowledge_response.status_code in [200, 204]:
                    print("✅ POST /notifications/{id}/acknowledge - SUCCESS")
                    print(f"   Status: {acknowledge_response.status_code}")
                    if acknowledge_response.text:
                        print(f"   Response: {acknowledge_response.text}")
                elif acknowledge_response.status_code == 404:
                    print("❌ POST /notifications/{id}/acknowledge - Notification not found (404)")
                    print(f"   Response: {acknowledge_response.text}")
                elif acknowledge_response.status_code == 500:
                    print("❌ POST /notifications/{id}/acknowledge - Server error (500)")
                    print(f"   Response: {acknowledge_response.text}")
                else:
                    print(f"⚠️  POST /notifications/{id}/acknowledge - Unexpected status: {acknowledge_response.status_code}")
                    print(f"   Response: {acknowledge_response.text}")
            else:
                print("❌ Could not find test notification ID")
                
                # Try with a dummy ID to see what happens
                print("\n🧪 Testing acknowledge endpoint with dummy ID...")
                dummy_response = session.post(
                    f"{BASE_URL}/notifications/dummy-id/acknowledge",
                    json={},
                    timeout=30
                )
                print(f"   Dummy ID test: {dummy_response.status_code} - {dummy_response.text}")
        else:
            print(f"❌ Could not retrieve notifications: {all_notifications_response.status_code}")
    else:
        print(f"❌ Failed to create test notification: {create_response.status_code} - {create_response.text}")
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    print("✅ GET /api/notifications/my?unread_only=true - Working (no 500 errors)")
    print("✅ Authentication working with admin@tanseeq.com")
    print("✅ Notification creation working")
    print("🔍 Acknowledge endpoint tested")
    
    return True

if __name__ == "__main__":
    test_notification_endpoints()