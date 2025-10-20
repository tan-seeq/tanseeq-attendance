#!/usr/bin/env python3
"""
Debug the attendance record creation to see what's happening
"""

import requests
import json
from datetime import datetime

# Get backend URL from frontend .env
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.split('=')[1].strip()
            break

API_BASE = f"{BACKEND_URL}/api"

def debug_attendance_creation():
    """Debug attendance record creation"""
    print("🔍 Debugging attendance record creation...")
    
    # Authenticate as super admin
    session = requests.Session()
    response = session.post(f"{API_BASE}/auth/login", json={
        "email": "hatem@tan-seeq.co",
        "password": "hatem123"
    })
    
    if response.status_code != 200:
        print(f"❌ Authentication failed")
        return False
    
    data = response.json()
    auth_token = data["access_token"]
    session.headers.update({"Authorization": f"Bearer {auth_token}"})
    print(f"✅ Authenticated as super admin")
    
    # Get all attendance records for today
    response = session.get(f"{API_BASE}/attendance")
    
    if response.status_code == 200:
        data = response.json()
        attendance_records = data if isinstance(data, list) else data.get("attendance", [])
        
        today = datetime.now().strftime("%Y-%m-%d")
        today_records = [r for r in attendance_records if r.get("date") == today]
        
        print(f"\n📊 TODAY'S ATTENDANCE RECORDS ({len(today_records)} found):")
        print("-" * 80)
        
        for i, record in enumerate(today_records):
            print(f"\nRecord {i+1}:")
            print(f"   User: {record.get('user_name', 'N/A')}")
            print(f"   Date: {record.get('date', 'N/A')}")
            print(f"   Check-in: {record.get('check_in', 'N/A')}")
            print(f"   Check-out: {record.get('check_out', 'N/A')}")
            print(f"   Status: {record.get('status', 'N/A')}")
            print(f"   Is Late: {record.get('is_late', 'N/A')}")
            
            # Check for new fields
            has_late_minutes = "late_minutes" in record
            has_early_departure = "early_departure_minutes" in record
            has_deducted_hours = "deducted_hours" in record
            has_schedule_type = "schedule_type" in record
            
            print(f"   🎯 NEW FIELDS:")
            print(f"      late_minutes: {record.get('late_minutes', 'MISSING')} (exists: {has_late_minutes})")
            print(f"      early_departure_minutes: {record.get('early_departure_minutes', 'MISSING')} (exists: {has_early_departure})")
            print(f"      deducted_hours: {record.get('deducted_hours', 'MISSING')} (exists: {has_deducted_hours})")
            print(f"      schedule_type: {record.get('schedule_type', 'MISSING')} (exists: {has_schedule_type})")
            
            print(f"   📋 ALL FIELDS: {list(record.keys())}")
        
        # Check if any records have the new fields
        records_with_new_fields = sum(1 for r in today_records if "late_minutes" in r)
        
        print(f"\n📈 SUMMARY:")
        print(f"   Total today's records: {len(today_records)}")
        print(f"   Records with new fields: {records_with_new_fields}")
        
        if records_with_new_fields > 0:
            print(f"   🟢 SUCCESS: Some records have the new fields")
            return True
        else:
            print(f"   🔴 ISSUE: No records have the new fields")
            return False
    else:
        print(f"❌ Failed to get attendance records: {response.status_code}")
        return False

if __name__ == "__main__":
    debug_attendance_creation()