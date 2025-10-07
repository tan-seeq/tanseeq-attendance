#!/usr/bin/env python3
"""
Backend Payroll Summary/Detail and Exports Testing
Focused test for payroll cycle endpoints as requested in review
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime
from pathlib import Path

# Test Configuration
BASE_URL = "https://payroll-fix-1.preview.emergentagent.com/api"
TEST_CREDENTIALS = {
    "email": "admin@tanseeq.com",
    "password": "ADMIN"
}

# Evidence directory
EVIDENCE_DIR = Path("/app/evidence/backend_exports_ret")
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

class PayrollExportsTest:
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.test_results = []
        
    async def setup_session(self):
        """Setup HTTP session with authentication"""
        self.session = aiohttp.ClientSession()
        
        # Login to get auth token
        login_url = f"{BASE_URL}/auth/login"
        async with self.session.post(login_url, json=TEST_CREDENTIALS) as response:
            if response.status == 200:
                data = await response.json()
                self.auth_token = data.get("access_token")
                print(f"✅ Authentication successful - Token: {self.auth_token[:20]}...")
                return True
            else:
                error_text = await response.text()
                print(f"❌ Authentication failed: {response.status} - {error_text}")
                return False
    
    def get_headers(self):
        """Get headers with authentication"""
        return {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
    
    async def log_test_result(self, test_name, status, details, response_headers=None):
        """Log test result with details"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_headers": dict(response_headers) if response_headers else None
        }
        self.test_results.append(result)
        
        status_icon = "✅" if status == "PASS" else "❌"
        print(f"{status_icon} {test_name}: {details}")
        
        if response_headers:
            print(f"   Response Headers Sample: {dict(list(response_headers.items())[:3])}")
    
    async def test_get_payroll_cycles(self):
        """Test 1: GET /api/payroll/cycles to obtain cycle IDs"""
        try:
            url = f"{BASE_URL}/payroll/cycles"
            async with self.session.get(url, headers=self.get_headers()) as response:
                status_code = response.status
                response_headers = response.headers
                
                if status_code == 200:
                    cycles = await response.json()
                    cycle_count = len(cycles)
                    
                    if cycle_count > 0:
                        # Store first cycle ID for subsequent tests
                        self.test_cycle_id = cycles[0].get("id")
                        await self.log_test_result(
                            "GET /api/payroll/cycles",
                            "PASS",
                            f"Retrieved {cycle_count} payroll cycles. First cycle ID: {self.test_cycle_id}",
                            response_headers
                        )
                        return cycles
                    else:
                        await self.log_test_result(
                            "GET /api/payroll/cycles",
                            "FAIL",
                            "No payroll cycles found in system",
                            response_headers
                        )
                        return []
                else:
                    error_text = await response.text()
                    await self.log_test_result(
                        "GET /api/payroll/cycles",
                        "FAIL",
                        f"HTTP {status_code}: {error_text}",
                        response_headers
                    )
                    return []
                    
        except Exception as e:
            await self.log_test_result(
                "GET /api/payroll/cycles",
                "ERROR",
                f"Exception: {str(e)}"
            )
            return []
    
    async def test_get_payroll_cycle_detail(self, cycle_id):
        """Test 2: GET /api/payroll/cycles/{id} should return 200 with JSON"""
        try:
            url = f"{BASE_URL}/payroll/cycles/{cycle_id}"
            async with self.session.get(url, headers=self.get_headers()) as response:
                status_code = response.status
                response_headers = response.headers
                
                if status_code == 200:
                    cycle_data = await response.json()
                    await self.log_test_result(
                        f"GET /api/payroll/cycles/{cycle_id}",
                        "PASS",
                        f"Retrieved cycle detail. Keys: {list(cycle_data.keys())[:5]}",
                        response_headers
                    )
                    return cycle_data
                else:
                    error_text = await response.text()
                    await self.log_test_result(
                        f"GET /api/payroll/cycles/{cycle_id}",
                        "FAIL",
                        f"HTTP {status_code}: {error_text}",
                        response_headers
                    )
                    return None
                    
        except Exception as e:
            await self.log_test_result(
                f"GET /api/payroll/cycles/{cycle_id}",
                "ERROR",
                f"Exception: {str(e)}"
            )
            return None
    
    async def test_get_payroll_cycle_summary(self, cycle_id):
        """Test 3: GET /api/payroll/cycles/{id}/summary should return 200 with cycle and employee_summaries"""
        try:
            url = f"{BASE_URL}/payroll/cycles/{cycle_id}/summary"
            async with self.session.get(url, headers=self.get_headers()) as response:
                status_code = response.status
                response_headers = response.headers
                
                if status_code == 200:
                    summary_data = await response.json()
                    
                    # Verify required fields
                    has_cycle = "cycle" in summary_data
                    has_employee_summaries = "employee_summaries" in summary_data
                    employee_count = len(summary_data.get("employee_summaries", []))
                    
                    if has_cycle and has_employee_summaries:
                        await self.log_test_result(
                            f"GET /api/payroll/cycles/{cycle_id}/summary",
                            "PASS",
                            f"Retrieved summary with cycle and {employee_count} employee summaries",
                            response_headers
                        )
                        return summary_data
                    else:
                        await self.log_test_result(
                            f"GET /api/payroll/cycles/{cycle_id}/summary",
                            "FAIL",
                            f"Missing required fields. Has cycle: {has_cycle}, Has employee_summaries: {has_employee_summaries}",
                            response_headers
                        )
                        return None
                else:
                    error_text = await response.text()
                    await self.log_test_result(
                        f"GET /api/payroll/cycles/{cycle_id}/summary",
                        "FAIL",
                        f"HTTP {status_code}: {error_text}",
                        response_headers
                    )
                    return None
                    
        except Exception as e:
            await self.log_test_result(
                f"GET /api/payroll/cycles/{cycle_id}/summary",
                "ERROR",
                f"Exception: {str(e)}"
            )
            return None
    
    async def test_export_payroll_pdf(self, cycle_id):
        """Test 4: GET /api/payroll/cycles/{id}/export/pdf should return PDF file"""
        try:
            url = f"{BASE_URL}/payroll/cycles/{cycle_id}/export/pdf"
            async with self.session.get(url, headers=self.get_headers()) as response:
                status_code = response.status
                response_headers = response.headers
                content_type = response_headers.get('content-type', '')
                
                if status_code == 200:
                    # Check content type
                    is_pdf = 'application/pdf' in content_type
                    
                    # Save file
                    pdf_content = await response.read()
                    pdf_file = EVIDENCE_DIR / f"payroll_{cycle_id}.pdf"
                    
                    with open(pdf_file, 'wb') as f:
                        f.write(pdf_content)
                    
                    file_size = len(pdf_content)
                    
                    await self.log_test_result(
                        f"GET /api/payroll/cycles/{cycle_id}/export/pdf",
                        "PASS" if is_pdf else "PARTIAL",
                        f"Downloaded PDF ({file_size} bytes). Content-Type: {content_type}. Saved to: {pdf_file}",
                        response_headers
                    )
                    return True
                else:
                    error_text = await response.text()
                    await self.log_test_result(
                        f"GET /api/payroll/cycles/{cycle_id}/export/pdf",
                        "FAIL",
                        f"HTTP {status_code}: {error_text}",
                        response_headers
                    )
                    return False
                    
        except Exception as e:
            await self.log_test_result(
                f"GET /api/payroll/cycles/{cycle_id}/export/pdf",
                "ERROR",
                f"Exception: {str(e)}"
            )
            return False
    
    async def test_export_payroll_excel(self, cycle_id):
        """Test 5: GET /api/payroll/cycles/{id}/export/excel should return Excel/CSV file"""
        try:
            url = f"{BASE_URL}/payroll/cycles/{cycle_id}/export/excel"
            async with self.session.get(url, headers=self.get_headers()) as response:
                status_code = response.status
                response_headers = response.headers
                content_type = response_headers.get('content-type', '')
                
                if status_code == 200:
                    # Check content type (could be CSV or Excel)
                    is_excel_csv = any(ct in content_type for ct in ['text/csv', 'application/vnd.ms-excel', 'application/vnd.openxmlformats'])
                    
                    # Save file
                    excel_content = await response.read()
                    excel_file = EVIDENCE_DIR / f"payroll_{cycle_id}.csv"
                    
                    with open(excel_file, 'wb') as f:
                        f.write(excel_content)
                    
                    file_size = len(excel_content)
                    
                    await self.log_test_result(
                        f"GET /api/payroll/cycles/{cycle_id}/export/excel",
                        "PASS" if is_excel_csv else "PARTIAL",
                        f"Downloaded Excel/CSV ({file_size} bytes). Content-Type: {content_type}. Saved to: {excel_file}",
                        response_headers
                    )
                    return True
                else:
                    error_text = await response.text()
                    await self.log_test_result(
                        f"GET /api/payroll/cycles/{cycle_id}/export/excel",
                        "FAIL",
                        f"HTTP {status_code}: {error_text}",
                        response_headers
                    )
                    return False
                    
        except Exception as e:
            await self.log_test_result(
                f"GET /api/payroll/cycles/{cycle_id}/export/excel",
                "ERROR",
                f"Exception: {str(e)}"
            )
            return False
    
    async def run_all_tests(self):
        """Run all payroll export tests in sequence"""
        print("🎯 BACKEND PAYROLL EXPORTS TESTING - TARGETED RETEST")
        print("=" * 60)
        
        # Setup authentication
        if not await self.setup_session():
            return False
        
        # Test 1: Get payroll cycles
        cycles = await self.test_get_payroll_cycles()
        if not cycles:
            print("❌ Cannot proceed without payroll cycles")
            return False
        
        # Use first cycle for remaining tests
        cycle_id = cycles[0].get("id")
        if not cycle_id:
            print("❌ No valid cycle ID found")
            return False
        
        print(f"\n🔍 Testing with Cycle ID: {cycle_id}")
        print("-" * 40)
        
        # Test 2: Get cycle detail
        await self.test_get_payroll_cycle_detail(cycle_id)
        
        # Test 3: Get cycle summary
        await self.test_get_payroll_cycle_summary(cycle_id)
        
        # Test 4: Export PDF
        await self.test_export_payroll_pdf(cycle_id)
        
        # Test 5: Export Excel
        await self.test_export_payroll_excel(cycle_id)
        
        return True
    
    async def generate_report(self):
        """Generate final test report"""
        print("\n" + "=" * 60)
        print("📊 PAYROLL EXPORTS TEST RESULTS SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        error_tests = len([r for r in self.test_results if r["status"] == "ERROR"])
        partial_tests = len([r for r in self.test_results if r["status"] == "PARTIAL"])
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"⚠️  Partial: {partial_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"🔥 Errors: {error_tests}")
        print(f"Success Rate: {((passed_tests + partial_tests) / total_tests * 100):.1f}%")
        
        # Save detailed report
        report_file = EVIDENCE_DIR / "payroll_exports_test_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                "test_summary": {
                    "total_tests": total_tests,
                    "passed": passed_tests,
                    "partial": partial_tests,
                    "failed": failed_tests,
                    "errors": error_tests,
                    "success_rate": f"{((passed_tests + partial_tests) / total_tests * 100):.1f}%"
                },
                "test_results": self.test_results,
                "evidence_directory": str(EVIDENCE_DIR),
                "test_timestamp": datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📁 Evidence saved to: {EVIDENCE_DIR}")
        print(f"📄 Detailed report: {report_file}")
        
        return passed_tests + partial_tests == total_tests
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()

async def main():
    """Main test execution"""
    tester = PayrollExportsTest()
    
    try:
        success = await tester.run_all_tests()
        await tester.generate_report()
        
        if success:
            print("\n🎉 All payroll export tests completed successfully!")
            return 0
        else:
            print("\n⚠️  Some tests failed or had issues. Check the report for details.")
            return 1
            
    except Exception as e:
        print(f"\n🔥 Test execution failed: {str(e)}")
        return 1
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)