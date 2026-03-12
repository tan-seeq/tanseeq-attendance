#!/usr/bin/env python3
"""
اختبار سريع لـ endpoint التقرير المخصص
Quick test for custom attendance report endpoint

Focus: POST /api/attendance/custom-report
Requirements:
1. Super Admin login (admin@tanseeq.com / ADMIN)
2. Test endpoint with specific parameters
3. Verify response contains file_content
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime

# Configuration
BASE_URL = "https://attend-deduct-hr.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"

# Test credentials
SUPER_ADMIN_EMAIL = "admin@tanseeq.com"
SUPER_ADMIN_PASSWORD = "ADMIN"

class CustomReportTester:
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.test_results = []
        
    async def setup_session(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
            
    def log_result(self, test_name, status, details):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{'✅' if status == 'PASS' else '❌'} {test_name}: {details}")
        
    async def authenticate_super_admin(self):
        """Authenticate as Super Admin"""
        try:
            login_data = {
                "email": SUPER_ADMIN_EMAIL,
                "password": SUPER_ADMIN_PASSWORD
            }
            
            async with self.session.post(f"{API_BASE}/auth/login", json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.auth_token = data.get("access_token")
                    user_info = data.get("user", {})
                    
                    self.log_result(
                        "Super Admin Authentication",
                        "PASS",
                        f"Login successful - Role: {user_info.get('role')}, Name: {user_info.get('name')}"
                    )
                    return True
                else:
                    error_text = await response.text()
                    self.log_result(
                        "Super Admin Authentication", 
                        "FAIL",
                        f"Status {response.status}: {error_text}"
                    )
                    return False
                    
        except Exception as e:
            self.log_result("Super Admin Authentication", "FAIL", f"Exception: {str(e)}")
            return False
            
    async def get_employee_ids(self):
        """Get employee IDs for testing"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            async with self.session.get(f"{API_BASE}/users", headers=headers) as response:
                if response.status == 200:
                    users = await response.json()
                    employee_ids = [user["id"] for user in users if user.get("is_active", True)]
                    
                    self.log_result(
                        "Employee IDs Retrieval",
                        "PASS", 
                        f"Found {len(employee_ids)} active employees"
                    )
                    return employee_ids[:3]  # Return first 3 for testing
                else:
                    error_text = await response.text()
                    self.log_result(
                        "Employee IDs Retrieval",
                        "FAIL",
                        f"Status {response.status}: {error_text}"
                    )
                    return []
                    
        except Exception as e:
            self.log_result("Employee IDs Retrieval", "FAIL", f"Exception: {str(e)}")
            return []
            
    async def test_custom_report_endpoint(self, employee_ids):
        """Test the custom attendance report endpoint"""
        try:
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            # Test data as specified in review request
            request_body = {
                "employee_ids": employee_ids,
                "start_date": "2025-01-01",
                "end_date": "2025-01-31", 
                "format": "excel"
            }
            
            print(f"\n🔍 Testing POST /api/attendance/custom-report")
            print(f"Request body: {json.dumps(request_body, indent=2)}")
            
            async with self.session.post(
                f"{API_BASE}/attendance/custom-report", 
                json=request_body,
                headers=headers
            ) as response:
                
                response_text = await response.text()
                
                if response.status == 200:
                    try:
                        response_data = json.loads(response_text)
                        
                        # Check for file_content in response
                        has_file_content = "file_content" in response_data
                        file_content_size = len(response_data.get("file_content", "")) if has_file_content else 0
                        
                        success_criteria = [
                            ("Response Status", response.status == 200),
                            ("JSON Response", isinstance(response_data, dict)),
                            ("Success Field", response_data.get("success") == True),
                            ("File Content Present", has_file_content),
                            ("File Content Not Empty", file_content_size > 0),
                            ("Filename Present", "filename" in response_data),
                            ("Content Type Present", "content_type" in response_data)
                        ]
                        
                        all_passed = all(criteria[1] for criteria in success_criteria)
                        
                        details = {
                            "status_code": response.status,
                            "response_size": len(response_text),
                            "file_content_size": file_content_size,
                            "filename": response_data.get("filename"),
                            "content_type": response_data.get("content_type"),
                            "records_count": response_data.get("records_count"),
                            "employees_count": response_data.get("employees_count"),
                            "success_criteria": {criteria[0]: criteria[1] for criteria in success_criteria}
                        }
                        
                        self.log_result(
                            "Custom Report Endpoint",
                            "PASS" if all_passed else "FAIL",
                            f"All criteria passed: {all_passed}. Details: {json.dumps(details, indent=2)}"
                        )
                        
                        return all_passed
                        
                    except json.JSONDecodeError:
                        self.log_result(
                            "Custom Report Endpoint",
                            "FAIL", 
                            f"Invalid JSON response. Status: {response.status}, Response: {response_text[:500]}"
                        )
                        return False
                        
                else:
                    self.log_result(
                        "Custom Report Endpoint",
                        "FAIL",
                        f"Status {response.status}: {response_text}"
                    )
                    return False
                    
        except Exception as e:
            self.log_result("Custom Report Endpoint", "FAIL", f"Exception: {str(e)}")
            return False
            
    async def run_tests(self):
        """Run all tests"""
        print("🎯 اختبار سريع لـ endpoint التقرير المخصص")
        print("=" * 60)
        
        await self.setup_session()
        
        try:
            # Step 1: Authenticate
            if not await self.authenticate_super_admin():
                return False
                
            # Step 2: Get employee IDs
            employee_ids = await self.get_employee_ids()
            if not employee_ids:
                return False
                
            # Step 3: Test custom report endpoint
            success = await self.test_custom_report_endpoint(employee_ids)
            
            return success
            
        finally:
            await self.cleanup_session()
            
    def save_results(self):
        """Save test results to file"""
        results_file = "/app/custom_report_test_results.json"
        
        summary = {
            "test_name": "Custom Attendance Report Endpoint Test",
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(self.test_results),
            "passed_tests": len([r for r in self.test_results if r["status"] == "PASS"]),
            "failed_tests": len([r for r in self.test_results if r["status"] == "FAIL"]),
            "success_rate": f"{(len([r for r in self.test_results if r['status'] == 'PASS']) / len(self.test_results) * 100):.1f}%" if self.test_results else "0%",
            "test_results": self.test_results
        }
        
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
            
        print(f"\n📊 Test Results Summary:")
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']}")
        print(f"Failed: {summary['failed_tests']}")
        print(f"Success Rate: {summary['success_rate']}")
        print(f"Results saved to: {results_file}")

async def main():
    """Main test function"""
    tester = CustomReportTester()
    
    try:
        success = await tester.run_tests()
        tester.save_results()
        
        if success:
            print("\n🎉 جميع الاختبارات نجحت! All tests passed!")
        else:
            print("\n❌ بعض الاختبارات فشلت. Some tests failed.")
            
    except Exception as e:
        print(f"\n💥 Test execution failed: {str(e)}")
        tester.save_results()

if __name__ == "__main__":
    asyncio.run(main())