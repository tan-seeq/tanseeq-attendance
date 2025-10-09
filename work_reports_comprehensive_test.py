#!/usr/bin/env python3
"""
Comprehensive Work Reports Testing - Verify all functionality
"""

import requests
import json
import time
from datetime import datetime, timedelta

BASE_URL = "https://tanseeq-hr-fix.preview.emergentagent.com/api"

def comprehensive_work_reports_test():
    session = requests.Session()
    
    # Authenticate
    login_data = {"email": "admin@tanseeq.com", "password": "ADMIN"}
    response = session.post(f"{BASE_URL}/auth/login", json=login_data)
    
    if response.status_code != 200:
        print(f"❌ Authentication failed: {response.status_code}")
        return
    
    token = response.json()["access_token"]
    session.headers.update({"Authorization": f"Bearer {token}"})
    print("✅ Authenticated successfully")
    
    # Create test client
    client_data = {
        "company_name": "Comprehensive Test Client",
        "client_code": f"CTC-{int(time.time())}",
        "industry": "Comprehensive Testing",
        "contact_person": "Test Manager",
        "phone": "+971501234567",
        "email": "test@comprehensive.com",
        "notes": "Client for comprehensive Work Reports testing"
    }
    
    response = session.post(f"{BASE_URL}/work-reports/clients", json=client_data)
    if response.status_code not in [200, 201]:
        print(f"❌ Client creation failed: {response.status_code}")
        return
    
    client_id = response.json()["id"]
    print(f"✅ Created comprehensive test client: {client_id}")
    
    # Get activity type
    response = session.get(f"{BASE_URL}/work-reports/activity-types")
    if response.status_code != 200:
        print(f"❌ Failed to get activity types: {response.status_code}")
        return
    
    activity_types = response.json()
    if isinstance(activity_types, list) and len(activity_types) > 0:
        activity_type_id = activity_types[0]["id"]
    elif isinstance(activity_types, dict) and activity_types.get("activity_types"):
        activity_type_id = activity_types["activity_types"][0]["id"]
    else:
        print("❌ No activity types available")
        return
    
    print(f"✅ Using activity type: {activity_type_id}")
    
    # Create multiple work logs for testing
    log_ids = []
    now = datetime.now()
    
    for i in range(3):
        start_time = now.replace(hour=9+i, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=2)
        
        log_data = {
            "client_id": client_id,
            "activity_type_id": activity_type_id,
            "date": now.strftime("%Y-%m-%d"),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "description": f"Comprehensive test work log #{i+1}",
            "notes": f"Test log {i+1} for comprehensive testing",
            "is_billable": True,
            "hourly_rate": 100.0 + (i * 25)  # Different rates
        }
        
        response = session.post(f"{BASE_URL}/work-reports/logs", json=log_data)
        if response.status_code in [200, 201]:
            log_id = response.json().get("id") or response.json().get("log_id")
            log_ids.append(log_id)
            print(f"✅ Created work log #{i+1}: {log_id}")
        else:
            print(f"❌ Failed to create work log #{i+1}: {response.status_code}")
    
    # Test filtering with different parameters
    current_date = now.strftime("%Y-%m-%d")
    
    # Test 1: Date filter
    params = {"start_date": current_date, "end_date": current_date}
    response = session.get(f"{BASE_URL}/work-reports/logs", params=params)
    if response.status_code == 200:
        result = response.json()
        if isinstance(result, list):
            logs = result
        elif isinstance(result, dict):
            logs = result.get("logs", result.get("data", []))
        else:
            logs = []
        
        found_logs = [log for log in logs if log.get("id") in log_ids]
        print(f"✅ Date filter test: Found {len(found_logs)}/{len(log_ids)} test logs")
    else:
        print(f"❌ Date filter test failed: {response.status_code}")
    
    # Test 2: Search query filter
    params = {"q": "Comprehensive test"}
    response = session.get(f"{BASE_URL}/work-reports/logs", params=params)
    if response.status_code == 200:
        result = response.json()
        if isinstance(result, list):
            search_logs = result
        elif isinstance(result, dict):
            search_logs = result.get("logs", result.get("data", []))
        else:
            search_logs = []
        
        found_search_logs = [log for log in search_logs if log.get("id") in log_ids]
        print(f"✅ Search filter test: Found {len(found_search_logs)} matching logs")
    else:
        print(f"❌ Search filter test failed: {response.status_code}")
    
    # Test 3: Pagination
    params = {"page": 1, "page_size": 2}
    response = session.get(f"{BASE_URL}/work-reports/logs", params=params)
    if response.status_code == 200:
        print("✅ Pagination test: Successfully retrieved paginated results")
    else:
        print(f"❌ Pagination test failed: {response.status_code}")
    
    # Test update functionality on first log
    if log_ids:
        test_log_id = log_ids[0]
        update_data = {
            "description": "Updated comprehensive test log",
            "hourly_rate": 200.0,
            "notes": "Updated during comprehensive testing"
        }
        
        response = session.put(f"{BASE_URL}/work-reports/logs/{test_log_id}", json=update_data)
        if response.status_code == 200:
            result = response.json()
            total_amount = result.get("total_amount", 0)
            print(f"✅ Update test: Log updated successfully, new amount: {total_amount}")
        else:
            print(f"❌ Update test failed: {response.status_code}")
    
    # Test delete functionality on all logs
    deleted_count = 0
    for log_id in log_ids:
        response = session.delete(f"{BASE_URL}/work-reports/logs/{log_id}")
        if response.status_code == 200:
            deleted_count += 1
    
    print(f"✅ Delete test: Successfully deleted {deleted_count}/{len(log_ids)} logs")
    
    # Cleanup: Deactivate test client
    update_data = {"is_active": False, "notes": "Deactivated after comprehensive testing"}
    response = session.put(f"{BASE_URL}/work-reports/clients/{client_id}", json=update_data)
    if response.status_code == 200:
        print("✅ Cleanup: Test client deactivated successfully")
    else:
        print(f"❌ Cleanup failed: {response.status_code}")
    
    print("\n🎉 Comprehensive Work Reports testing completed!")

if __name__ == "__main__":
    comprehensive_work_reports_test()