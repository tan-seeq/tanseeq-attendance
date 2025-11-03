#!/usr/bin/env python3
"""
Debug October 2025 Deductions - Investigate why no records returned
"""

import requests
import json
from datetime import datetime

# Configuration
BACKEND_URL = "https://attend-deduct-hr.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@tanseeq.com"
ADMIN_PASSWORD = "ADMIN"

class DeductionsDebugger:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        
    def authenticate(self):
        """Authenticate as Super Admin"""
        print("🔐 Authenticating...")
        
        response = self.session.post(
            f"{BACKEND_URL}/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            self.auth_token = data.get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
            print(f"✅ Authentication successful")
            return True
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return False
    
    def check_employees(self):
        """Check available employees"""
        print("\n👥 Checking employees...")
        
        response = self.session.get(f"{BACKEND_URL}/employees/list", timeout=30)
        if response.status_code == 200:
            employees = response.json()
            if isinstance(employees, list):
                print(f"✅ Found {len(employees)} employees:")
                for emp in employees[:10]:  # Show first 10
                    print(f"  - {emp.get('name', 'N/A')} (ID: {emp.get('id', 'N/A')})")
            else:
                print(f"✅ Employees response: {employees}")
            return employees
        else:
            print(f"❌ Failed to get employees: {response.status_code}")
            return []
    
    def check_attendance_data(self):
        """Check attendance data for October 2025"""
        print("\n📅 Checking attendance data...")
        
        response = self.session.get(f"{BACKEND_URL}/attendance", timeout=30)
        if response.status_code == 200:
            attendance = response.json()
            print(f"✅ Found {len(attendance)} attendance records")
            
            # Filter for October 2025
            october_records = [a for a in attendance if a.get('date', '').startswith('2025-10')]
            print(f"📊 October 2025 records: {len(october_records)}")
            
            if october_records:
                print("Sample October records:")
                for record in october_records[:5]:
                    print(f"  - {record.get('user_name', 'N/A')}: {record.get('date')} - {record.get('status', 'N/A')}")
            
            return october_records
        else:
            print(f"❌ Failed to get attendance: {response.status_code}")
            return []
    
    def check_existing_deductions(self):
        """Check existing deductions"""
        print("\n💰 Checking existing deductions...")
        
        response = self.session.get(f"{BACKEND_URL}/deductions", timeout=30)
        if response.status_code == 200:
            deductions = response.json()
            print(f"✅ Found {len(deductions)} existing deduction records")
            
            # Show sample
            for ded in deductions[:5]:
                print(f"  - {ded.get('employee_name', 'N/A')}: {ded.get('month', 'N/A')} - {ded.get('total_deduction', 0)} AED")
            
            return deductions
        else:
            print(f"❌ Failed to get deductions: {response.status_code}")
            return []
    
    def test_different_months(self):
        """Test calculation for different months"""
        print("\n🗓️ Testing different months...")
        
        months_to_test = ["2025-10", "2025-09", "2025-11", "2024-10"]
        
        for month in months_to_test:
            print(f"\n📊 Testing month: {month}")
            response = self.session.post(
                f"{BACKEND_URL}/deductions/calculate-monthly?month={month}",
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                deductions = data.get('deductions', [])
                print(f"  ✅ {len(deductions)} records returned")
                
                if deductions:
                    print("  Sample employees:")
                    for ded in deductions[:3]:
                        print(f"    - {ded.get('employee_name', 'N/A')}: {ded.get('total_deduction', 0)} AED")
            else:
                print(f"  ❌ Failed: {response.status_code} - {response.text[:100]}")
    
    def check_payroll_cycles(self):
        """Check payroll cycles"""
        print("\n💼 Checking payroll cycles...")
        
        response = self.session.get(f"{BACKEND_URL}/payroll/cycles", timeout=30)
        if response.status_code == 200:
            cycles = response.json()
            print(f"✅ Found {len(cycles)} payroll cycles:")
            
            for cycle in cycles:
                print(f"  - {cycle.get('cycle_name', 'N/A')}: {cycle.get('start_date')} to {cycle.get('end_date')} (Status: {cycle.get('status', 'N/A')})")
            
            return cycles
        else:
            print(f"❌ Failed to get payroll cycles: {response.status_code}")
            return []
    
    def run_debug(self):
        """Run complete debug sequence"""
        print("🔍 Starting Deductions Debug Investigation")
        print("=" * 50)
        
        if not self.authenticate():
            return
        
        employees = self.check_employees()
        attendance = self.check_attendance_data()
        deductions = self.check_existing_deductions()
        cycles = self.check_payroll_cycles()
        
        self.test_different_months()
        
        print("\n" + "=" * 50)
        print("📋 DEBUG SUMMARY")
        print("=" * 50)
        print(f"👥 Employees: {len(employees)}")
        print(f"📅 October 2025 Attendance: {len(attendance)}")
        print(f"💰 Existing Deductions: {len(deductions)}")
        print(f"💼 Payroll Cycles: {len(cycles)}")

if __name__ == "__main__":
    debugger = DeductionsDebugger()
    debugger.run_debug()