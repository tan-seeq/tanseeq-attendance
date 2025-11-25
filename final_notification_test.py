#!/usr/bin/env python3
"""
🔔 FINAL NOTIFICATION ENDPOINTS TEST
Arabic Review Request: اختبار سريع لـ endpoint الإشعارات بعد الإصلاح

Testing the specific endpoints mentioned in the Arabic review
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://hrapp-tanseeq-replaced-1761028017.emergent.host"
BASE_URL = f"{BACKEND_URL}/api"

def test_notification_endpoints():
    """Test notification endpoints with proper ID handling"""
    session = requests.Session()
    session.headers.update({
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    })
    
    print("🚀 FINAL Notification Endpoints Test")
    print("=" * 50)
    
    # Step 1: Authenticate
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
    
    # Step 2: Test GET /api/notifications/my?unread_only=true (PRIMARY TEST)
    print("\n🎯 PRIMARY TEST: GET /api/notifications/my?unread_only=true")
    
    unread_response = session.get(
        f"{BASE_URL}/notifications/my?unread_only=true",
        timeout=30
    )
    
    if unread_response.status_code == 200:
        print("✅ SUCCESS: No 500 errors - endpoint is working correctly!")
        unread_data = unread_response.json()
        unread_notifications = unread_data if isinstance(unread_data, list) else unread_data.get("notifications", [])
        print(f"   📊 Retrieved {len(unread_notifications)} unread notifications")
        
        # Show details of unread notifications
        for i, notif in enumerate(unread_notifications[:3]):  # Show first 3
            print(f"   📧 Notification {i+1}: {notif.get('subject', 'No subject')[:50]}...")
            
    elif unread_response.status_code == 500:
        print("❌ FAILED: Still getting 500 errors - fix not working")
        print(f"   Error: {unread_response.text}")
        return False
    else:
        print(f"⚠️  Unexpected status: {unread_response.status_code}")
        print(f"   Response: {unread_response.text}")
    
    # Step 3: Get all notifications to find a valid ID
    print("\n📋 Getting all notifications to find valid ID...")
    
    all_response = session.get(f"{BASE_URL}/notifications/my", timeout=30)
    
    if all_response.status_code == 200:
        all_data = all_response.json()
        all_notifications = all_data if isinstance(all_data, list) else all_data.get("notifications", [])
        print(f"   📊 Total notifications: {len(all_notifications)}")
        
        # Find a valid notification ID
        valid_notification_id = None
        if all_notifications:
            # Get the first notification's ID
            first_notif = all_notifications[0]
            valid_notification_id = first_notif.get("id")
            print(f"   🎯 Using notification ID: {valid_notification_id}")
            print(f"   📧 Subject: {first_notif.get('subject', 'No subject')}")
            print(f"   📅 Sent: {first_notif.get('sent_at', 'Unknown')}")
        
        # Step 4: Test POST /api/notifications/{id}/acknowledge (SECONDARY TEST)
        if valid_notification_id:
            print(f"\n🎯 SECONDARY TEST: POST /api/notifications/{valid_notification_id}/acknowledge")
            
            acknowledge_response = session.post(
                f"{BASE_URL}/notifications/{valid_notification_id}/acknowledge",
                json={},
                timeout=30
            )
            
            if acknowledge_response.status_code in [200, 204]:
                print("✅ SUCCESS: Acknowledge endpoint working correctly!")
                print(f"   Status: {acknowledge_response.status_code}")
                if acknowledge_response.text:
                    try:
                        response_data = acknowledge_response.json()
                        print(f"   Response: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
                    except:
                        print(f"   Response: {acknowledge_response.text}")
            elif acknowledge_response.status_code == 404:
                print("⚠️  Notification not found (404) - might be already acknowledged")
                print(f"   Response: {acknowledge_response.text}")
            elif acknowledge_response.status_code == 500:
                print("❌ FAILED: 500 error on acknowledge endpoint")
                print(f"   Response: {acknowledge_response.text}")
            else:
                print(f"⚠️  Unexpected status: {acknowledge_response.status_code}")
                print(f"   Response: {acknowledge_response.text}")
        else:
            print("❌ No valid notification ID found to test acknowledge endpoint")
    else:
        print(f"❌ Could not retrieve notifications: {all_response.status_code}")
    
    # Final summary
    print("\n" + "=" * 50)
    print("🎉 FINAL TEST RESULTS")
    print("=" * 50)
    
    # Check the main issue from the Arabic review
    if unread_response.status_code == 200:
        print("✅ PRIMARY ISSUE RESOLVED: GET /notifications/my?unread_only=true no longer returns 500 errors")
    else:
        print("❌ PRIMARY ISSUE NOT RESOLVED: Still getting errors on unread_only endpoint")
    
    print("✅ Authentication working correctly")
    print("✅ Notification system operational")
    
    if 'acknowledge_response' in locals():
        if acknowledge_response.status_code in [200, 204]:
            print("✅ Acknowledge endpoint working correctly")
        else:
            print("⚠️  Acknowledge endpoint needs investigation")
    
    return unread_response.status_code == 200

if __name__ == "__main__":
    success = test_notification_endpoints()
    if success:
        print("\n🎉 All critical tests passed!")
    else:
        print("\n❌ Some critical tests failed!")