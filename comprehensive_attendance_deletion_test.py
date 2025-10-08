#!/usr/bin/env python3
"""
Comprehensive Attendance Record Deletion Testing
اختبار شامل لوظيفة حذف سجلات الحضور - ديسمبر 2024

Testing deletion of different types of attendance records:
- Present records
- Late records  
- Absent records
"""

import requests
import json
import os
from datetime import datetime

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://salary-processor-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
SUPER_ADMIN_CREDENTIALS = {
    "email": "hatem@tan-seeq.co",
    "password": "hatem123"
}

REGULAR_USER_CREDENTIALS = {
    "email": "jihad@tanseeq.com", 
    "password": "jihad123"
}

def authenticate(credentials):
    """Authenticate and return token"""
    try:
        response = requests.post(
            f"{API_BASE}/auth/login",
            json=credentials,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token"), data.get("user", {})
        else:
            print(f"Authentication failed: {response.status_code}")
            return None, None
            
    except Exception as e:
        print(f"Authentication error: {str(e)}")
        return None, None

def get_attendance_records(token):
    """Get all attendance records"""
    try:
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(
            f"{API_BASE}/attendance/with-absences",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to get records: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"Error getting records: {str(e)}")
        return []

def test_delete_by_status(token, status_type, max_records=2):
    """Test deleting records of a specific status"""
    print(f"\n🗑️ TESTING DELETION OF {status_type.upper()} RECORDS")
    print("=" * 60)
    
    headers = {'Authorization': f'Bearer {token}'}
    records = get_attendance_records(token)
    
    # Filter records by status
    target_records = [r for r in records if r.get('status', '').lower() == status_type.lower()]
    
    if not target_records:
        print(f"❌ No {status_type} records found for testing")
        return 0
    
    print(f"Found {len(target_records)} {status_type} records")
    
    deleted_count = 0
    for i, record in enumerate(target_records[:max_records]):
        record_id = record.get('id')
        user_name = record.get('user_name', 'Unknown')
        date = record.get('date', 'Unknown')
        
        if not record_id:
            continue
            
        try:
            print(f"\n🔄 Deleting {status_type} record {i+1}/{min(max_records, len(target_records))}")
            print(f"   Record ID: {record_id}")
            print(f"   User: {user_name}")
            print(f"   Date: {date}")
            
            # Test general attendance deletion endpoint
            response = requests.delete(
                f"{API_BASE}/attendance/{record_id}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Successfully deleted: {data.get('message', 'No message')}")
                deleted_count += 1
                
                # Verify deletion
                updated_records = get_attendance_records(token)
                still_exists = any(r.get('id') == record_id for r in updated_records)
                
                if not still_exists:
                    print(f"   ✅ Verified: Record removed from database")
                else:
                    print(f"   ❌ Warning: Record still exists in database")
                    
            elif response.status_code == 404:
                print(f"   ⚠️  Record not found (may have been deleted already)")
            else:
                print(f"   ❌ Deletion failed: {response.status_code} - {response.text[:100]}")
                
        except Exception as e:
            print(f"   ❌ Exception during deletion: {str(e)}")
    
    print(f"\n📊 {status_type.upper()} DELETION SUMMARY: {deleted_count}/{min(max_records, len(target_records))} records deleted")
    return deleted_count

def test_absence_deletion_endpoint(token, max_records=2):
    """Test the specific absence deletion endpoint"""
    print(f"\n🗑️ TESTING ABSENCE-SPECIFIC DELETION ENDPOINT")
    print("=" * 60)
    
    headers = {'Authorization': f'Bearer {token}'}
    records = get_attendance_records(token)
    
    # Filter absence records
    absent_records = [r for r in records if r.get('status', '').lower() == 'absent']
    
    if not absent_records:
        print("❌ No absent records found for testing")
        return 0
    
    print(f"Found {len(absent_records)} absent records")
    
    deleted_count = 0
    for i, record in enumerate(absent_records[:max_records]):
        record_id = record.get('id')
        user_name = record.get('user_name', 'Unknown')
        date = record.get('date', 'Unknown')
        
        if not record_id:
            continue
            
        try:
            print(f"\n🔄 Deleting absence record {i+1}/{min(max_records, len(absent_records))}")
            print(f"   Record ID: {record_id}")
            print(f"   User: {user_name}")
            print(f"   Date: {date}")
            
            # Test absence-specific deletion endpoint
            response = requests.delete(
                f"{API_BASE}/attendance/delete-absence/{record_id}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Successfully deleted: {data.get('message', 'No message')}")
                deleted_count += 1
                
                # Verify deletion
                updated_records = get_attendance_records(token)
                still_exists = any(r.get('id') == record_id for r in updated_records)
                
                if not still_exists:
                    print(f"   ✅ Verified: Record removed from database")
                else:
                    print(f"   ❌ Warning: Record still exists in database")
                    
            elif response.status_code == 404:
                print(f"   ⚠️  Record not found (may have been deleted already)")
            else:
                print(f"   ❌ Deletion failed: {response.status_code} - {response.text[:100]}")
                
        except Exception as e:
            print(f"   ❌ Exception during deletion: {str(e)}")
    
    print(f"\n📊 ABSENCE DELETION SUMMARY: {deleted_count}/{min(max_records, len(absent_records))} records deleted")
    return deleted_count

def test_access_control(regular_token):
    """Test that regular users cannot delete records"""
    print(f"\n🚫 TESTING ACCESS CONTROL - REGULAR USER")
    print("=" * 60)
    
    if not regular_token:
        print("❌ No regular user token available")
        return
    
    headers = {'Authorization': f'Bearer {regular_token}'}
    
    # Get any record ID for testing
    records = get_attendance_records(regular_token)
    if not records:
        print("❌ No records available for access control testing")
        return
    
    test_record_id = records[0].get('id')
    if not test_record_id:
        print("❌ No valid record ID found")
        return
    
    print(f"Testing access control with record ID: {test_record_id}")
    
    # Test general deletion endpoint
    try:
        response = requests.delete(
            f"{API_BASE}/attendance/{test_record_id}",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 403:
            print("✅ General deletion endpoint: Correctly denied access (403)")
        elif response.status_code == 200:
            print("❌ SECURITY ISSUE: Regular user was able to delete attendance record!")
        else:
            print(f"✅ General deletion endpoint: Access restricted ({response.status_code})")
            
    except Exception as e:
        print(f"❌ Exception testing general deletion: {str(e)}")
    
    # Test absence deletion endpoint
    try:
        response = requests.delete(
            f"{API_BASE}/attendance/delete-absence/{test_record_id}",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 403:
            print("✅ Absence deletion endpoint: Correctly denied access (403)")
        elif response.status_code == 200:
            print("❌ SECURITY ISSUE: Regular user was able to delete absence record!")
        else:
            print(f"✅ Absence deletion endpoint: Access restricted ({response.status_code})")
            
    except Exception as e:
        print(f"❌ Exception testing absence deletion: {str(e)}")

def main():
    """Run comprehensive attendance deletion tests"""
    print("🚀 COMPREHENSIVE ATTENDANCE DELETION TESTING")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print("=" * 80)
    
    # Authenticate users
    print("🔐 AUTHENTICATION SETUP")
    super_admin_token, super_admin_user = authenticate(SUPER_ADMIN_CREDENTIALS)
    regular_user_token, regular_user = authenticate(REGULAR_USER_CREDENTIALS)
    
    if not super_admin_token:
        print("🚨 CRITICAL: Super Admin authentication failed!")
        return
    
    print(f"✅ Super Admin authenticated: {super_admin_user.get('name', 'Unknown')}")
    if regular_user_token:
        print(f"✅ Regular User authenticated: {regular_user.get('name', 'Unknown')}")
    else:
        print("⚠️  Regular User authentication failed")
    
    # Get initial statistics
    initial_records = get_attendance_records(super_admin_token)
    print(f"\n📊 INITIAL STATISTICS")
    print(f"Total attendance records: {len(initial_records)}")
    
    status_counts = {}
    for record in initial_records:
        status = record.get('status', 'Unknown')
        status_counts[status] = status_counts.get(status, 0) + 1
    
    for status, count in status_counts.items():
        print(f"  {status}: {count} records")
    
    # Test deletion of different record types
    total_deleted = 0
    
    # Test Present records
    total_deleted += test_delete_by_status(super_admin_token, "Present", 2)
    
    # Test Late records
    total_deleted += test_delete_by_status(super_admin_token, "Late", 2)
    
    # Test Absent records with general endpoint
    total_deleted += test_delete_by_status(super_admin_token, "Absent", 1)
    
    # Test Absent records with specific endpoint
    total_deleted += test_absence_deletion_endpoint(super_admin_token, 1)
    
    # Test access control
    test_access_control(regular_user_token)
    
    # Final statistics
    final_records = get_attendance_records(super_admin_token)
    print(f"\n📊 FINAL STATISTICS")
    print(f"Records before testing: {len(initial_records)}")
    print(f"Records after testing: {len(final_records)}")
    print(f"Total records deleted: {len(initial_records) - len(final_records)}")
    print(f"Expected deletions: {total_deleted}")
    
    print("\n" + "=" * 80)
    print("🏁 COMPREHENSIVE TESTING COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    main()