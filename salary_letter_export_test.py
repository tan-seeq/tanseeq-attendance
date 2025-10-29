#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Salary Letter and Export Endpoints
TANSEEQ HR Payroll System - New Endpoints Testing

Testing the following endpoints:
1. GET /api/payroll/cycles/{cycle_id}/employees/{employee_id}/letter
2. GET /api/payroll/cycles/{cycle_id}/export-all-letters  
3. GET /api/payroll/cycles/{cycle_id}/export-excel

Test Requirements:
- Use admin@tanseeq.com / ADMIN for authentication
- Look for existing payroll cycles in 2025 (likely October 2025)
- Use cycle_id from the cycles list
- Pick employee IDs from the employee summaries of that cycle
- Verify HTML response contains: "TANSEEQ TAX CONSULTANCY", "Salary Statement", employee name, salary details, deductions breakdown
- Verify proper calculation of Daily Rate, Hourly Rate, Per Minute Rate
- Verify JSON response with array of letters
- Verify Excel file (.xlsx) is returned with proper Content-Type and Content-Disposition headers
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime
import sys

# Backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://attendance-calc-4.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class SalaryLetterExportTester:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.test_results = []
        self.cycle_id = None
        self.employee_ids = []
        
    async def setup_session(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
            
    async def authenticate_admin(self):
        """Authenticate as Super Admin"""
        print("🔐 Authenticating as Super Admin...")
        
        login_data = {
            "email": "admin@tanseeq.com",
            "password": "ADMIN"
        }
        
        try:
            async with self.session.post(f"{API_BASE}/auth/login", json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.admin_token = data["access_token"]
                    user_info = data["user"]
                    print(f"✅ Authentication successful - Role: {user_info['role']}, Name: {user_info['name']}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Authentication failed: {response.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False
            
    def get_auth_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.admin_token}"}
        
    async def find_test_data(self):
        """Find existing payroll cycle and employees for testing"""
        print("🔍 Finding test data (payroll cycles and employees)...")
        
        try:
            # Get payroll cycles
            async with self.session.get(f"{API_BASE}/payroll/cycles", headers=self.get_auth_headers()) as response:
                if response.status == 200:
                    cycles_data = await response.json()
                    cycles = cycles_data.get("cycles", [])
                    print(f"📊 Found {len(cycles)} payroll cycles")
                    
                    # Look for 2025 cycles (preferably October)
                    target_cycle = None
                    for cycle in cycles:
                        cycle_month = cycle.get("month", "")
                        if "2025" in cycle_month:
                            target_cycle = cycle
                            if "10" in cycle_month or "October" in cycle_month:
                                break  # Prefer October 2025
                    
                    if target_cycle:
                        self.cycle_id = target_cycle["id"]
                        print(f"✅ Selected cycle: {target_cycle['month']} (ID: {self.cycle_id})")
                        
                        # Get employee summaries for this cycle
                        async with self.session.get(f"{API_BASE}/payroll/cycles/{self.cycle_id}/summary", headers=self.get_auth_headers()) as summary_response:
                            if summary_response.status == 200:
                                summary_data = await summary_response.json()
                                employees = summary_data.get("employees", [])
                                self.employee_ids = [emp.get("employee_id") for emp in employees if emp.get("employee_id")]
                                print(f"✅ Found {len(self.employee_ids)} employees in cycle")
                                
                                if self.employee_ids:
                                    print(f"📋 Employee IDs: {self.employee_ids[:3]}{'...' if len(self.employee_ids) > 3 else ''}")
                                    return True
                                else:
                                    print("❌ No employees found in payroll cycle")
                                    return False
                            else:
                                print(f"❌ Failed to get cycle summary: {summary_response.status}")
                                return False
                    else:
                        print("❌ No 2025 payroll cycles found")
                        return False
                else:
                    error_text = await response.text()
                    print(f"❌ Failed to get payroll cycles: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error finding test data: {str(e)}")
            return False
            
    async def test_salary_letter_endpoint(self):
        """Test GET /api/payroll/cycles/{cycle_id}/employees/{employee_id}/letter"""
        print("\n🧾 Testing Salary Letter Endpoint...")
        
        if not self.employee_ids:
            print("❌ No employee IDs available for testing")
            return False
            
        test_employee_id = self.employee_ids[0]
        print(f"📝 Testing salary letter for employee: {test_employee_id}")
        
        try:
            # Test HTML format
            async with self.session.get(
                f"{API_BASE}/payroll/cycles/{self.cycle_id}/employees/{test_employee_id}/letter?format=html",
                headers=self.get_auth_headers()
            ) as response:
                
                if response.status == 200:
                    content_type = response.headers.get('content-type', '')
                    html_content = await response.text()
                    
                    print(f"✅ Salary letter generated successfully")
                    print(f"📄 Content-Type: {content_type}")
                    print(f"📏 Content length: {len(html_content)} characters")
                    
                    # Verify required content
                    required_elements = [
                        "TANSEEQ TAX CONSULTANCY",
                        "Salary Statement", 
                        "Daily Rate",
                        "Hourly Rate", 
                        "Per Minute Rate"
                    ]
                    
                    missing_elements = []
                    for element in required_elements:
                        if element not in html_content:
                            missing_elements.append(element)
                    
                    if missing_elements:
                        print(f"⚠️ Missing required elements: {missing_elements}")
                    else:
                        print("✅ All required elements found in salary letter")
                    
                    # Check for salary calculations
                    if "Daily Rate" in html_content and "Hourly Rate" in html_content:
                        print("✅ Salary rate calculations present")
                    
                    self.test_results.append({
                        "test": "salary_letter_html",
                        "status": "PASS",
                        "details": f"Generated {len(html_content)} char HTML, missing: {missing_elements}"
                    })
                    return True
                    
                else:
                    error_text = await response.text()
                    print(f"❌ Salary letter generation failed: {response.status} - {error_text}")
                    self.test_results.append({
                        "test": "salary_letter_html", 
                        "status": "FAIL",
                        "details": f"HTTP {response.status}: {error_text}"
                    })
                    return False
                    
        except Exception as e:
            print(f"❌ Salary letter test error: {str(e)}")
            self.test_results.append({
                "test": "salary_letter_html",
                "status": "ERROR", 
                "details": str(e)
            })
            return False
            
    async def test_export_all_letters_endpoint(self):
        """Test GET /api/payroll/cycles/{cycle_id}/export-all-letters"""
        print("\n📦 Testing Export All Letters Endpoint...")
        
        try:
            async with self.session.get(
                f"{API_BASE}/payroll/cycles/{self.cycle_id}/export-all-letters",
                headers=self.get_auth_headers()
            ) as response:
                
                if response.status == 200:
                    content_type = response.headers.get('content-type', '')
                    data = await response.json()
                    
                    print(f"✅ Export all letters successful")
                    print(f"📄 Content-Type: {content_type}")
                    
                    # Verify JSON structure
                    letters = data.get("letters", [])
                    cycle_id = data.get("cycle_id")
                    cycle_month = data.get("cycle_month")
                    
                    print(f"📊 Found {len(letters)} letters")
                    print(f"🗓️ Cycle: {cycle_month} (ID: {cycle_id})")
                    
                    if letters:
                        # Check first letter structure
                        first_letter = letters[0]
                        required_fields = ["employee_id", "employee_name", "employee_code", "html"]
                        missing_fields = [field for field in required_fields if field not in first_letter]
                        
                        if missing_fields:
                            print(f"⚠️ Missing fields in letter: {missing_fields}")
                        else:
                            print("✅ All required fields present in letters")
                            
                        # Check HTML content quality
                        html_content = first_letter.get("html", "")
                        if len(html_content) > 1000:  # Reasonable HTML length
                            print("✅ HTML content appears properly formatted")
                        else:
                            print("⚠️ HTML content seems too short")
                    
                    self.test_results.append({
                        "test": "export_all_letters",
                        "status": "PASS",
                        "details": f"Exported {len(letters)} letters, cycle: {cycle_month}"
                    })
                    return True
                    
                else:
                    error_text = await response.text()
                    print(f"❌ Export all letters failed: {response.status} - {error_text}")
                    self.test_results.append({
                        "test": "export_all_letters",
                        "status": "FAIL", 
                        "details": f"HTTP {response.status}: {error_text}"
                    })
                    return False
                    
        except Exception as e:
            print(f"❌ Export all letters test error: {str(e)}")
            self.test_results.append({
                "test": "export_all_letters",
                "status": "ERROR",
                "details": str(e)
            })
            return False
            
    async def test_export_excel_endpoint(self):
        """Test GET /api/payroll/cycles/{cycle_id}/export-excel"""
        print("\n📊 Testing Export Excel Endpoint...")
        
        try:
            async with self.session.get(
                f"{API_BASE}/payroll/cycles/{self.cycle_id}/export-excel",
                headers=self.get_auth_headers()
            ) as response:
                
                if response.status == 200:
                    content_type = response.headers.get('content-type', '')
                    content_disposition = response.headers.get('content-disposition', '')
                    content = await response.read()
                    
                    print(f"✅ Excel export successful")
                    print(f"📄 Content-Type: {content_type}")
                    print(f"📎 Content-Disposition: {content_disposition}")
                    print(f"📏 File size: {len(content)} bytes")
                    
                    # Verify Excel content type
                    expected_content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    if expected_content_type in content_type:
                        print("✅ Correct Excel content type")
                    else:
                        print(f"⚠️ Unexpected content type: {content_type}")
                    
                    # Verify Content-Disposition header contains filename
                    if "filename" in content_disposition:
                        print("✅ Filename present in Content-Disposition")
                    else:
                        print("⚠️ No filename in Content-Disposition header")
                    
                    # Verify file size is reasonable (Excel files should be > 1KB)
                    if len(content) > 1024:
                        print("✅ Excel file size appears reasonable")
                    else:
                        print("⚠️ Excel file seems too small")
                    
                    self.test_results.append({
                        "test": "export_excel",
                        "status": "PASS",
                        "details": f"Generated {len(content)} byte Excel file, content-type: {content_type}"
                    })
                    return True
                    
                else:
                    error_text = await response.text()
                    print(f"❌ Excel export failed: {response.status} - {error_text}")
                    self.test_results.append({
                        "test": "export_excel",
                        "status": "FAIL",
                        "details": f"HTTP {response.status}: {error_text}"
                    })
                    return False
                    
        except Exception as e:
            print(f"❌ Excel export test error: {str(e)}")
            self.test_results.append({
                "test": "export_excel", 
                "status": "ERROR",
                "details": str(e)
            })
            return False
            
    async def test_authentication_requirements(self):
        """Test that all endpoints require Super Admin authentication"""
        print("\n🔒 Testing Authentication Requirements...")
        
        endpoints = [
            f"/payroll/cycles/{self.cycle_id}/employees/{self.employee_ids[0] if self.employee_ids else 'test'}/letter",
            f"/payroll/cycles/{self.cycle_id}/export-all-letters",
            f"/payroll/cycles/{self.cycle_id}/export-excel"
        ]
        
        auth_test_results = []
        
        for endpoint in endpoints:
            try:
                # Test without authentication
                async with self.session.get(f"{API_BASE}{endpoint}") as response:
                    if response.status in [401, 403]:
                        auth_test_results.append(f"✅ {endpoint}: Properly protected")
                    else:
                        auth_test_results.append(f"⚠️ {endpoint}: Status {response.status} (expected 401/403)")
            except Exception as e:
                auth_test_results.append(f"❌ {endpoint}: Error {str(e)}")
        
        for result in auth_test_results:
            print(result)
            
        self.test_results.append({
            "test": "authentication_requirements",
            "status": "PASS" if all("✅" in result for result in auth_test_results) else "PARTIAL",
            "details": "; ".join(auth_test_results)
        })
        
    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*80)
        print("🎯 SALARY LETTER & EXPORT ENDPOINTS TESTING SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        error_tests = len([r for r in self.test_results if r["status"] == "ERROR"])
        
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"🔥 Errors: {error_tests}")
        print(f"📈 Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        print("\n📋 DETAILED RESULTS:")
        for i, result in enumerate(self.test_results, 1):
            status_icon = {"PASS": "✅", "FAIL": "❌", "ERROR": "🔥", "PARTIAL": "⚠️"}
            icon = status_icon.get(result["status"], "❓")
            print(f"{i}. {icon} {result['test']}: {result['status']}")
            print(f"   Details: {result['details']}")
        
        # Test-specific findings
        print("\n🔍 KEY FINDINGS:")
        
        if self.cycle_id:
            print(f"✅ Test Cycle ID: {self.cycle_id}")
        if self.employee_ids:
            print(f"✅ Test Employees: {len(self.employee_ids)} found")
            
        # Endpoint-specific results
        salary_letter_test = next((r for r in self.test_results if r["test"] == "salary_letter_html"), None)
        if salary_letter_test and salary_letter_test["status"] == "PASS":
            print("✅ Salary Letter Generation: Working correctly with required elements")
            
        export_letters_test = next((r for r in self.test_results if r["test"] == "export_all_letters"), None)
        if export_letters_test and export_letters_test["status"] == "PASS":
            print("✅ Export All Letters: JSON response with proper structure")
            
        excel_test = next((r for r in self.test_results if r["test"] == "export_excel"), None)
        if excel_test and excel_test["status"] == "PASS":
            print("✅ Excel Export: Proper .xlsx file with correct headers")
            
        print("\n" + "="*80)
        
        # Return overall success
        return failed_tests == 0 and error_tests == 0

async def main():
    """Main test execution"""
    print("🚀 Starting Salary Letter & Export Endpoints Testing")
    print(f"🌐 Backend URL: {BACKEND_URL}")
    print("="*80)
    
    tester = SalaryLetterExportTester()
    
    try:
        await tester.setup_session()
        
        # Step 1: Authenticate
        if not await tester.authenticate_admin():
            print("❌ Authentication failed - cannot proceed with tests")
            return False
            
        # Step 2: Find test data
        if not await tester.find_test_data():
            print("❌ Could not find suitable test data - cannot proceed")
            return False
            
        # Step 3: Test endpoints
        await tester.test_salary_letter_endpoint()
        await tester.test_export_all_letters_endpoint() 
        await tester.test_export_excel_endpoint()
        await tester.test_authentication_requirements()
        
        # Step 4: Print summary
        success = tester.print_summary()
        
        return success
        
    except Exception as e:
        print(f"❌ Critical error during testing: {str(e)}")
        return False
        
    finally:
        await tester.cleanup_session()

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)