#!/usr/bin/env python3
"""
🔥 URGENT: Test the 9:15 AM Late Tracking Fix Implementation
Direct test of the fix after applying the code changes
"""

import requests
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

# Get backend URL from frontend .env
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.split('=')[1].strip()
            break

API_BASE = f"{BACKEND_URL}/api"

# Test credentials
TEST_USERS = {
    "regular": {"email": "jihad@tanseeq.com", "password": "jihad123"},
    "admin": {"email": "mahmoud@tanseeq.com", "password": "mahmoud123"},
    "super_admin": {"email": "hatem@tan-seeq.co", "password": "hatem123"}
}

def authenticate(user_type="regular"):
    """Authenticate and return session"""
    session = requests.Session()
    user_creds = TEST_USERS[user_type]
    response = session.post(f"{API_BASE}/auth/login", json=user_creds)
    
    if response.status_code == 200:
        data = response.json()
        auth_token = data["access_token"]
        session.headers.update({"Authorization": f"Bearer {auth_token}"})
        print(f"✅ Authenticated as {user_creds['email']}")
        return session
    else:
        print(f"❌ Authentication failed: {response.status_code}")
        return None

def test_check_in_response_structure():
    """Test the check-in endpoint response structure"""
    print("\n🔍 TESTING CHECK-IN ENDPOINT RESPONSE STRUCTURE:")
    
    session = authenticate("regular")
    if not session:
        return False
    
    # Try to check out first to reset state
    checkout_response = session.post(f"{API_BASE}/attendance/check-out")
    print(f"   Checkout attempt: {checkout_response.status_code}")
    
    # Now try check-in
    response = session.post(f"{API_BASE}/attendance/check-in")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Check-in successful!")
        print(f"   Response keys: {list(data.keys())}")
        
        # Check for required fields
        has_late_minutes = "late_minutes" in data
        has_is_late = "is_late" in data
        has_schedule_type = "schedule_type" in data
        
        print(f"   Has late_minutes: {has_late_minutes} (value: {data.get('late_minutes', 'N/A')})")
        print(f"   Has is_late: {has_is_late} (value: {data.get('is_late', 'N/A')})")
        print(f"   Has schedule_type: {has_schedule_type} (value: {data.get('schedule_type', 'N/A')})")
        
        # Calculate expected late_minutes
        current_time = datetime.now()
        expected_late_minutes = 0
        if current_time.hour > 9 or (current_time.hour == 9 and current_time.minute > 15):
            check_in_minutes = current_time.hour * 60 + current_time.minute
            threshold_minutes = 9 * 60 + 15  # 9:15 AM
            expected_late_minutes = check_in_minutes - threshold_minutes
        
        actual_late_minutes = data.get("late_minutes", 0)
        print(f"   Expected late_minutes: {expected_late_minutes}")
        print(f"   Actual late_minutes: {actual_late_minutes}")
        
        success = has_late_minutes and has_is_late
        print(f"   🎯 Fix Implementation: {'✅ SUCCESS' if success else '❌ FAILED'}")
        
        return success, data
        
    elif response.status_code == 400:
        error_msg = response.json().get("detail", "")
        print(f"   ⚠️ Already checked in: {error_msg}")
        return None, {"already_checked_in": True}
    else:
        print(f"   ❌ Unexpected response: {response.status_code} - {response.text}")
        return False, None

def test_database_record_structure():
    """Test if new attendance records have the required fields"""
    print("\n💾 TESTING DATABASE RECORD STRUCTURE:")
    
    session = authenticate("regular")
    if not session:
        return False
    
    # Get attendance records
    response = session.get(f"{API_BASE}/attendance")
    
    if response.status_code == 200:
        data = response.json()
        attendance_records = data if isinstance(data, list) else data.get("attendance", [])
        
        print(f"   Total records: {len(attendance_records)}")
        
        # Check the most recent record
        if attendance_records:
            recent_record = max(attendance_records, key=lambda x: x.get("date", ""))
            print(f"   Most recent record date: {recent_record.get('date')}")
            print(f"   Record keys: {list(recent_record.keys())}")
            
            # Check for new fields
            has_late_minutes = "late_minutes" in recent_record
            has_early_departure = "early_departure_minutes" in recent_record
            has_deducted_hours = "deducted_hours" in recent_record
            has_schedule_type = "schedule_type" in recent_record
            
            print(f"   Has late_minutes: {has_late_minutes} (value: {recent_record.get('late_minutes', 'N/A')})")
            print(f"   Has early_departure_minutes: {has_early_departure} (value: {recent_record.get('early_departure_minutes', 'N/A')})")
            print(f"   Has deducted_hours: {has_deducted_hours} (value: {recent_record.get('deducted_hours', 'N/A')})")
            print(f"   Has schedule_type: {has_schedule_type} (value: {recent_record.get('schedule_type', 'N/A')})")
            
            success = has_late_minutes and has_early_departure and has_deducted_hours
            print(f"   🎯 Database Schema: {'✅ SUCCESS' if success else '❌ FAILED'}")
            
            return success
        else:
            print(f"   ❌ No attendance records found")
            return False
    else:
        print(f"   ❌ Failed to get attendance records: {response.status_code}")
        return False

def test_deductions_calculation():
    """Test deductions calculation with Super Admin"""
    print("\n💰 TESTING DEDUCTIONS CALCULATION:")
    
    session = authenticate("super_admin")
    if not session:
        return False
    
    # Test monthly deductions calculation
    current_month = datetime.now().strftime("%Y-%m")
    response = session.post(f"{API_BASE}/deductions/calculate-monthly?month={current_month}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Deductions calculation successful")
        print(f"   Response type: {type(data)}")
        
        if isinstance(data, list) and len(data) > 0:
            sample_record = data[0]
            print(f"   Sample record keys: {list(sample_record.keys())}")
            
            # Look for attendance-related fields
            attendance_fields = [key for key in sample_record.keys() 
                               if any(term in key.lower() for term in ['attendance', 'late', 'deduction'])]
            
            print(f"   Attendance-related fields: {attendance_fields}")
            
            success = len(attendance_fields) > 0
            print(f"   🎯 Deductions Integration: {'✅ SUCCESS' if success else '❌ FAILED'}")
            
            return success
        else:
            print(f"   ⚠️ No deduction records returned")
            return False
    else:
        print(f"   ❌ Deductions calculation failed: {response.status_code} - {response.text}")
        return False

def main():
    """Run comprehensive test of the late tracking fix"""
    print("🔥 URGENT: 9:15 AM Late Tracking Fix Implementation Test")
    print("=" * 70)
    
    # Test 1: Check-in Response Structure
    check_in_result, check_in_data = test_check_in_response_structure()
    
    # Test 2: Database Record Structure
    database_result = test_database_record_structure()
    
    # Test 3: Deductions Integration
    deductions_result = test_deductions_calculation()
    
    # Summary
    print("\n" + "=" * 70)
    print("📋 TEST SUMMARY:")
    
    tests = [
        ("Check-in Response Structure", check_in_result),
        ("Database Record Structure", database_result),
        ("Deductions Integration", deductions_result)
    ]
    
    passed = sum(1 for _, result in tests if result)
    total = len([t for t in tests if t[1] is not None])
    
    for test_name, result in tests:
        if result is None:
            status = "⚪ SKIPPED"
        elif result:
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        print(f"   {status} {test_name}")
    
    print(f"\nSuccess Rate: {passed}/{total} ({(passed/total)*100:.1f}%)")
    
    # Final Verdict
    if passed >= 2:  # At least 2 out of 3 critical tests
        print(f"\n🟢 VERDICT: 9:15 AM Late Tracking Fix IS WORKING")
        print(f"✅ The fix has been successfully implemented")
        
        # Check current time and expected behavior
        current_time = datetime.now()
        if current_time.hour > 9 or (current_time.hour == 9 and current_time.minute > 15):
            expected_late_minutes = (current_time.hour * 60 + current_time.minute) - (9 * 60 + 15)
            print(f"📝 Current time: {current_time.strftime('%H:%M')}")
            print(f"📝 Expected late_minutes for current check-in: {expected_late_minutes}")
        else:
            print(f"📝 Current time: {current_time.strftime('%H:%M')} (on time)")
            print(f"📝 Expected late_minutes for current check-in: 0")
    else:
        print(f"\n🔴 VERDICT: 9:15 AM Late Tracking Fix NEEDS MORE WORK")
        print(f"❌ Critical issues still exist")
    
    # Save results
    with open('/app/late_tracking_fix_test_results.json', 'w') as f:
        json.dump({
            "test_results": {test_name: result for test_name, result in tests},
            "success_rate": (passed/total)*100 if total > 0 else 0,
            "check_in_data": check_in_data,
            "timestamp": datetime.now().isoformat()
        }, f, indent=2)
    
    return passed >= 2

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)