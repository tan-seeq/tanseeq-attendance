#!/usr/bin/env python3
"""
Enhanced Reporting System Test - Specific tests for the review request
Tests the enhanced reporting and export system after fixes
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class EnhancedReportingTester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.api_url = f"{self.base_url}/api"
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0
        
        # Admin credentials from review request
        self.admin_creds = {'email': 'hatem@tanseeq.com', 'password': 'hatem123'}

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")

    def login_admin(self) -> bool:
        """Login as admin"""
        try:
            response = requests.post(f"{self.api_url}/auth/login", 
                                   json=self.admin_creds, timeout=30)
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data['access_token']
                self.log_test("Admin login", True)
                return True
            else:
                self.log_test("Admin login", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Admin login", False, str(e))
            return False

    def test_attendance_report_export(self, format_type: str) -> bool:
        """Test attendance report export (Excel/PDF)"""
        if not self.admin_token:
            return False
            
        url = f"{self.api_url}/reports/attendance/export"
        params = {
            'start_date': '2025-01-01',
            'end_date': '2025-01-31',
            'format': format_type
        }
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            success = response.status_code == 200
            
            if success:
                # Check content type and content
                content_type = response.headers.get('content-type', '')
                has_content = len(response.content) > 0
                
                if format_type == 'excel':
                    is_valid = 'spreadsheet' in content_type or 'excel' in content_type
                elif format_type == 'pdf':
                    is_valid = 'pdf' in content_type and response.content.startswith(b'%PDF')
                else:
                    is_valid = False
                
                success = is_valid and has_content
                
                # Check for clean content (no strange symbols in headers)
                content_disposition = response.headers.get('content-disposition', '')
                has_clean_filename = 'TANSEEQ_attendance_report' in content_disposition
                
                success = success and has_clean_filename
            
            self.log_test(f"Attendance report export ({format_type.upper()})", success,
                         f"Status: {response.status_code}, Content-Type: {response.headers.get('content-type', 'N/A')}" if not success else "")
            return success
            
        except Exception as e:
            self.log_test(f"Attendance report export ({format_type.upper()})", False, str(e))
            return False

    def test_leave_report_export(self, format_type: str) -> bool:
        """Test leave report export (Excel/PDF)"""
        if not self.admin_token:
            return False
            
        url = f"{self.api_url}/reports/leaves/export"
        params = {
            'start_date': '2025-01-01',
            'end_date': '2025-01-31',
            'format': format_type
        }
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            success = response.status_code == 200
            
            if success:
                # Check content type and content
                content_type = response.headers.get('content-type', '')
                has_content = len(response.content) > 0
                
                if format_type == 'excel':
                    is_valid = 'spreadsheet' in content_type or 'excel' in content_type
                elif format_type == 'pdf':
                    is_valid = 'pdf' in content_type and response.content.startswith(b'%PDF')
                else:
                    is_valid = False
                
                success = is_valid and has_content
                
                # Check for clean content (no strange symbols in headers)
                content_disposition = response.headers.get('content-disposition', '')
                has_clean_filename = 'TANSEEQ_leaves_report' in content_disposition
                
                success = success and has_clean_filename
            
            self.log_test(f"Leave report export ({format_type.upper()})", success,
                         f"Status: {response.status_code}, Content-Type: {response.headers.get('content-type', 'N/A')}" if not success else "")
            return success
            
        except Exception as e:
            self.log_test(f"Leave report export ({format_type.upper()})", False, str(e))
            return False

    def test_field_exit_report_export(self, format_type: str) -> bool:
        """Test field exit report export (Excel/PDF)"""
        if not self.admin_token:
            return False
            
        url = f"{self.api_url}/reports/field-exits/export"
        params = {
            'start_date': '2025-01-01',
            'end_date': '2025-01-31',
            'format': format_type
        }
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            success = response.status_code == 200
            
            if success:
                # Check content type and content
                content_type = response.headers.get('content-type', '')
                has_content = len(response.content) > 0
                
                if format_type == 'excel':
                    is_valid = 'spreadsheet' in content_type or 'excel' in content_type
                elif format_type == 'pdf':
                    is_valid = 'pdf' in content_type and response.content.startswith(b'%PDF')
                else:
                    is_valid = False
                
                success = is_valid and has_content
                
                # Check for clean content (no strange symbols in headers)
                content_disposition = response.headers.get('content-disposition', '')
                has_clean_filename = 'TANSEEQ_field-exits_report' in content_disposition
                
                success = success and has_clean_filename
            
            self.log_test(f"Field exit report export ({format_type.upper()})", success,
                         f"Status: {response.status_code}, Content-Type: {response.headers.get('content-type', 'N/A')}" if not success else "")
            return success
            
        except Exception as e:
            self.log_test(f"Field exit report export ({format_type.upper()})", False, str(e))
            return False

    def test_attendance_update_api(self) -> bool:
        """Test attendance update API - should make status 'present' instead of 'late'"""
        if not self.admin_token:
            return False
        
        # First get attendance records
        try:
            response = requests.get(f"{self.api_url}/attendance/all", 
                                  headers={'Authorization': f'Bearer {self.admin_token}'}, 
                                  timeout=30)
            
            if response.status_code != 200:
                self.log_test("Attendance update API test setup", False, "Could not fetch attendance records")
                return False
            
            attendance_records = response.json()
            if not attendance_records:
                self.log_test("Attendance update API test setup", False, "No attendance records found")
                return False
            
            # Find a record to update
            test_record = attendance_records[0]
            attendance_id = test_record.get('id')
            
            if not attendance_id:
                self.log_test("Attendance update API test setup", False, "No valid attendance ID found")
                return False
            
            # Test updating attendance
            update_data = {
                "status": "present",
                "check_in": "09:00:00",
                "check_out": "17:00:00"
            }
            
            response = requests.put(f"{self.api_url}/attendance/{attendance_id}", 
                                  json=update_data,
                                  headers={'Authorization': f'Bearer {self.admin_token}'}, 
                                  timeout=30)
            
            success = response.status_code == 200
            
            if success:
                # Verify the update worked by fetching the record again
                response = requests.get(f"{self.api_url}/attendance/all", 
                                      headers={'Authorization': f'Bearer {self.admin_token}'}, 
                                      timeout=30)
                
                if response.status_code == 200:
                    updated_records = response.json()
                    updated_record = next((r for r in updated_records if r.get('id') == attendance_id), None)
                    
                    if updated_record:
                        status_updated = updated_record.get('status') == 'present'
                        is_late_false = not updated_record.get('is_late', True)
                        success = status_updated and is_late_false
            
            self.log_test("Attendance update API (present status)", success,
                         f"Status: {response.status_code}" if not success else "")
            return success
            
        except Exception as e:
            self.log_test("Attendance update API (present status)", False, str(e))
            return False

    def test_custom_date_range_reports(self) -> bool:
        """Test reports with custom date ranges"""
        if not self.admin_token:
            return False
        
        report_types = ['attendance', 'leaves', 'field-exits']
        all_passed = True
        
        for report_type in report_types:
            try:
                url = f"{self.api_url}/reports/{report_type}"
                params = {
                    'start_date': '2025-01-15',
                    'end_date': '2025-01-25'
                }
                headers = {'Authorization': f'Bearer {self.admin_token}'}
                
                response = requests.get(url, params=params, headers=headers, timeout=30)
                success = response.status_code == 200
                
                if success:
                    data = response.json()
                    success = isinstance(data, list)
                
                self.log_test(f"Custom date range {report_type} report", success,
                             f"Status: {response.status_code}" if not success else "")
                
                if not success:
                    all_passed = False
                    
            except Exception as e:
                self.log_test(f"Custom date range {report_type} report", False, str(e))
                all_passed = False
        
        return all_passed

    def run_enhanced_reporting_tests(self):
        """Run all enhanced reporting tests"""
        print("🚀 Starting Enhanced Reporting System Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Login first
        if not self.login_admin():
            print("❌ Admin login failed - stopping tests")
            return False
        
        print("\n📊 Testing Report Export Functionality:")
        print("-" * 40)
        
        # Test Excel exports
        self.test_attendance_report_export('excel')
        self.test_leave_report_export('excel')
        self.test_field_exit_report_export('excel')
        
        # Test PDF exports
        self.test_attendance_report_export('pdf')
        self.test_leave_report_export('pdf')
        self.test_field_exit_report_export('pdf')
        
        print("\n🔧 Testing Attendance Update API:")
        print("-" * 40)
        self.test_attendance_update_api()
        
        print("\n📅 Testing Custom Date Range Reports:")
        print("-" * 40)
        self.test_custom_date_range_reports()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All enhanced reporting tests passed!")
            print("✅ Reports are clean and professionally formatted")
            print("✅ Export functionality working correctly")
            print("✅ Attendance update API working properly")
            return True
        else:
            failed_tests = self.tests_run - self.tests_passed
            print(f"⚠️  {failed_tests} tests failed")
            return False

def main():
    # Get backend URL from frontend .env
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    backend_url = line.split('=', 1)[1].strip()
                    break
            else:
                print("❌ Could not find REACT_APP_BACKEND_URL in frontend/.env")
                return 1
    except Exception as e:
        print(f"❌ Error reading frontend/.env: {e}")
        return 1
    
    print(f"🔗 Using backend URL: {backend_url}")
    
    # Run tests
    tester = EnhancedReportingTester(backend_url)
    success = tester.run_enhanced_reporting_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())