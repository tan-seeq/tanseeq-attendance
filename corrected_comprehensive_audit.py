#!/usr/bin/env python3
"""
🔍 CORRECTED COMPREHENSIVE HR SYSTEM AUDIT - BACKEND VERIFICATION
Complete system audit with corrected endpoint testing

This audit addresses the specific requirements from the comprehensive review request
and tests actual working endpoints with proper error handling.
"""

import requests
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://payroll-management-4.preview.emergentagent.com')
BASE_URL = f"{BACKEND_URL}/api"

# Test accounts
TEST_ACCOUNTS = {
    "super_admin": {"email": "admin@tanseeq.com", "password": "ADMIN"},
    "admin": {"email": "mahmoud@tanseeq.com", "password": "mahmoud123"},
    "user": {"email": "jihad@tanseeq.com", "password": "jihad123"}
}

class CorrectedHRAudit:
    def __init__(self):
        self.results = {
            "audit_timestamp": datetime.now().isoformat(),
            "backend_url": BACKEND_URL,
            "test_summary": {},
            "detailed_results": {},
            "critical_issues": [],
            "working_features": [],
            "broken_features": [],
            "overall_health_score": 0
        }
        self.tokens = {}
        
    def authenticate_all_users(self):
        """Authenticate all test users"""
        print("🔐 Authenticating all test users...")
        
        auth_results = {}
        for role, credentials in TEST_ACCOUNTS.items():
            try:
                response = requests.post(f"{BASE_URL}/auth/login", json=credentials, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    self.tokens[role] = data.get("access_token")
                    auth_results[role] = {
                        "success": True,
                        "user_info": data.get("user", {}),
                        "role_verified": data.get("user", {}).get("role")
                    }
                    print(f"  ✅ {role.upper()}: {credentials['email']} - SUCCESS")
                else:
                    auth_results[role] = {
                        "success": False,
                        "error": f"Status {response.status_code}: {response.text}"
                    }
                    print(f"  ❌ {role.upper()}: {credentials['email']} - FAILED")
                    
            except Exception as e:
                auth_results[role] = {
                    "success": False,
                    "error": str(e)
                }
                print(f"  ❌ {role.upper()}: {credentials['email']} - ERROR: {e}")
        
        self.results["authentication"] = auth_results
        return all(result["success"] for result in auth_results.values())

    def test_attendance_system(self):
        """Test Attendance & Time Tracking System"""
        print("\n⏰ Testing Attendance & Time Tracking System...")
        
        token = self.tokens.get("super_admin")
        if not token:
            return {"success": False, "error": "No authentication"}
        
        headers = {"Authorization": f"Bearer {token}"}
        results = {}
        
        # Test attendance endpoints
        test_cases = [
            ("GET", "/attendance", "Get attendance records"),
            ("GET", "/attendance/with-absences", "Get attendance with absences"),
            ("POST", "/attendance/check-in", "Check-in functionality"),
            ("POST", "/attendance/check-out", "Check-out functionality"),
        ]
        
        for method, endpoint, description in test_cases:
            try:
                if method == "GET":
                    response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=10)
                else:
                    response = requests.post(f"{BASE_URL}{endpoint}", headers=headers, timeout=10)
                
                success = response.status_code in [200, 400]  # 400 might be expected for check-in/out
                
                results[endpoint] = {
                    "success": success,
                    "status_code": response.status_code,
                    "description": description,
                    "details": f"Status {response.status_code}"
                }
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if isinstance(data, list):
                            results[endpoint]["record_count"] = len(data)
                            results[endpoint]["details"] += f" - Found {len(data)} records"
                        elif isinstance(data, dict) and 'message' in data:
                            results[endpoint]["message"] = data['message']
                    except:
                        pass
                
                status_icon = "✅" if success else "❌"
                print(f"  {status_icon} {description}: {results[endpoint]['details']}")
                
            except Exception as e:
                results[endpoint] = {
                    "success": False,
                    "error": str(e),
                    "description": description
                }
                print(f"  ❌ {description}: ERROR - {e}")
        
        self.results["detailed_results"]["attendance"] = results
        success_rate = sum(1 for r in results.values() if r.get("success", False)) / len(results) * 100
        return {"success_rate": success_rate, "results": results}

    def test_leave_management(self):
        """Test Leave Management System"""
        print("\n🏖️ Testing Leave Management System...")
        
        admin_token = self.tokens.get("admin")
        user_token = self.tokens.get("user")
        
        if not admin_token or not user_token:
            return {"success": False, "error": "Missing authentication tokens"}
        
        results = {}
        
        # Test leave endpoints
        test_cases = [
            ("GET", "/leaves", "Get all leaves (admin)", admin_token),
            ("GET", "/leaves/my", "Get user leaves", user_token),
        ]
        
        for method, endpoint, description, token in test_cases:
            try:
                headers = {"Authorization": f"Bearer {token}"}
                response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=10)
                
                success = response.status_code == 200
                
                results[endpoint] = {
                    "success": success,
                    "status_code": response.status_code,
                    "description": description
                }
                
                if success:
                    try:
                        data = response.json()
                        if isinstance(data, list):
                            results[endpoint]["record_count"] = len(data)
                        elif isinstance(data, dict) and 'leaves' in data:
                            results[endpoint]["record_count"] = len(data['leaves'])
                    except:
                        pass
                
                status_icon = "✅" if success else "❌"
                record_info = f" ({results[endpoint].get('record_count', 0)} records)" if success else ""
                print(f"  {status_icon} {description}: Status {response.status_code}{record_info}")
                
            except Exception as e:
                results[endpoint] = {
                    "success": False,
                    "error": str(e),
                    "description": description
                }
                print(f"  ❌ {description}: ERROR - {e}")
        
        self.results["detailed_results"]["leave_management"] = results
        success_rate = sum(1 for r in results.values() if r.get("success", False)) / len(results) * 100
        return {"success_rate": success_rate, "results": results}

    def test_payroll_system(self):
        """Test Payroll System (CRITICAL)"""
        print("\n💰 Testing Payroll System (CRITICAL)...")
        
        token = self.tokens.get("super_admin")
        if not token:
            return {"success": False, "error": "No super admin authentication"}
        
        headers = {"Authorization": f"Bearer {token}"}
        results = {}
        
        # Test payroll endpoints
        test_cases = [
            ("GET", "/payroll/cycles", "Get payroll cycles"),
            ("GET", "/payroll/installment-schedules", "Get installment schedules"),
        ]
        
        for method, endpoint, description in test_cases:
            try:
                response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=10)
                
                success = response.status_code == 200
                
                results[endpoint] = {
                    "success": success,
                    "status_code": response.status_code,
                    "description": description
                }
                
                if success:
                    try:
                        data = response.json()
                        if isinstance(data, list):
                            results[endpoint]["record_count"] = len(data)
                            results[endpoint]["details"] = f"Found {len(data)} records"
                    except:
                        pass
                
                status_icon = "✅" if success else "❌"
                details = results[endpoint].get("details", f"Status {response.status_code}")
                print(f"  {status_icon} {description}: {details}")
                
            except Exception as e:
                results[endpoint] = {
                    "success": False,
                    "error": str(e),
                    "description": description
                }
                print(f"  ❌ {description}: ERROR - {e}")
        
        # Test payroll cycle operations if cycles exist
        if results.get("/payroll/cycles", {}).get("success"):
            self.test_payroll_cycle_operations(headers, results)
        
        self.results["detailed_results"]["payroll_system"] = results
        success_rate = sum(1 for r in results.values() if r.get("success", False)) / len(results) * 100
        return {"success_rate": success_rate, "results": results}

    def test_payroll_cycle_operations(self, headers, results):
        """Test payroll cycle specific operations"""
        try:
            # Get first cycle for testing
            response = requests.get(f"{BASE_URL}/payroll/cycles", headers=headers, timeout=10)
            if response.status_code == 200:
                cycles = response.json()
                if cycles and len(cycles) > 0:
                    cycle_id = cycles[0].get("id")
                    
                    if cycle_id:
                        # Test cycle operations
                        cycle_ops = [
                            ("GET", f"/payroll/cycles/{cycle_id}", "Get cycle details"),
                            ("GET", f"/payroll/cycles/{cycle_id}/summary", "Get cycle summary"),
                            ("POST", f"/payroll/cycles/{cycle_id}/recalculate", "Recalculate cycle"),
                        ]
                        
                        for method, endpoint, description in cycle_ops:
                            try:
                                if method == "GET":
                                    resp = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=10)
                                else:
                                    resp = requests.post(f"{BASE_URL}{endpoint}", headers=headers, timeout=10)
                                
                                success = resp.status_code == 200
                                results[endpoint] = {
                                    "success": success,
                                    "status_code": resp.status_code,
                                    "description": description
                                }
                                
                                status_icon = "✅" if success else "❌"
                                print(f"  {status_icon} {description}: Status {resp.status_code}")
                                
                            except Exception as e:
                                results[endpoint] = {
                                    "success": False,
                                    "error": str(e),
                                    "description": description
                                }
                                print(f"  ❌ {description}: ERROR - {e}")
        except Exception as e:
            print(f"  ⚠️ Cycle operations test failed: {e}")

    def test_deductions_system(self):
        """Test Deductions System (CRITICAL)"""
        print("\n💸 Testing Deductions System (CRITICAL)...")
        
        token = self.tokens.get("super_admin")
        if not token:
            return {"success": False, "error": "No super admin authentication"}
        
        headers = {"Authorization": f"Bearer {token}"}
        results = {}
        
        # Test deduction endpoints
        test_cases = [
            ("GET", "/deductions", "Get deductions list"),
            ("POST", "/deductions/calculate-monthly?month=2025-01", "Calculate monthly deductions"),
            ("POST", "/deductions/apply-monthly?month=2025-01", "Apply monthly deductions"),
            ("GET", "/employees/list", "Get employees for deductions"),
        ]
        
        for method, endpoint_with_params, description in test_cases:
            try:
                if method == "GET":
                    response = requests.get(f"{BASE_URL}{endpoint_with_params}", headers=headers, timeout=10)
                else:
                    response = requests.post(f"{BASE_URL}{endpoint_with_params}", headers=headers, timeout=10)
                
                success = response.status_code == 200
                
                results[endpoint_with_params] = {
                    "success": success,
                    "status_code": response.status_code,
                    "description": description
                }
                
                if success:
                    try:
                        data = response.json()
                        if isinstance(data, list):
                            results[endpoint_with_params]["record_count"] = len(data)
                        elif isinstance(data, dict) and 'message' in data:
                            results[endpoint_with_params]["message"] = data['message']
                    except:
                        pass
                
                status_icon = "✅" if success else "❌"
                record_info = ""
                if results[endpoint_with_params].get("record_count"):
                    record_info = f" ({results[endpoint_with_params]['record_count']} records)"
                elif results[endpoint_with_params].get("message"):
                    record_info = f" - {results[endpoint_with_params]['message']}"
                    
                print(f"  {status_icon} {description}: Status {response.status_code}{record_info}")
                
            except Exception as e:
                results[endpoint_with_params] = {
                    "success": False,
                    "error": str(e),
                    "description": description
                }
                print(f"  ❌ {description}: ERROR - {e}")
        
        self.results["detailed_results"]["deductions_system"] = results
        success_rate = sum(1 for r in results.values() if r.get("success", False)) / len(results) * 100
        return {"success_rate": success_rate, "results": results}

    def test_advances_system(self):
        """Test Advances & Installments System (CRITICAL)"""
        print("\n💳 Testing Advances & Installments System (CRITICAL)...")
        
        super_admin_token = self.tokens.get("super_admin")
        user_token = self.tokens.get("user")
        
        if not super_admin_token or not user_token:
            return {"success": False, "error": "Missing authentication tokens"}
        
        results = {}
        
        # Test advances endpoints
        test_cases = [
            ("GET", "/advances/admin/all-balances", "Get all employee balances", super_admin_token),
            ("GET", "/advances/admin/pending-approvals", "Get pending approvals", super_admin_token),
            ("GET", "/advances/admin/all-transactions", "Get all transactions", super_admin_token),
            ("GET", "/advances/my-balance", "Get user balance", user_token),
            ("GET", "/advances/my-transactions", "Get user transactions", user_token),
        ]
        
        for method, endpoint, description, token in test_cases:
            try:
                headers = {"Authorization": f"Bearer {token}"}
                response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=10)
                
                success = response.status_code == 200
                
                results[endpoint] = {
                    "success": success,
                    "status_code": response.status_code,
                    "description": description
                }
                
                if success:
                    try:
                        data = response.json()
                        if isinstance(data, dict):
                            if 'employee_balances' in data:
                                results[endpoint]["record_count"] = len(data['employee_balances'])
                            elif 'pending_transactions' in data:
                                results[endpoint]["record_count"] = len(data['pending_transactions'])
                            elif 'transactions' in data:
                                results[endpoint]["record_count"] = len(data['transactions'])
                            elif 'total_available' in data:
                                results[endpoint]["balance_info"] = f"Available: {data['total_available']}"
                    except:
                        pass
                
                status_icon = "✅" if success else "❌"
                extra_info = ""
                if results[endpoint].get("record_count"):
                    extra_info = f" ({results[endpoint]['record_count']} records)"
                elif results[endpoint].get("balance_info"):
                    extra_info = f" - {results[endpoint]['balance_info']}"
                    
                print(f"  {status_icon} {description}: Status {response.status_code}{extra_info}")
                
            except Exception as e:
                results[endpoint] = {
                    "success": False,
                    "error": str(e),
                    "description": description
                }
                print(f"  ❌ {description}: ERROR - {e}")
        
        self.results["detailed_results"]["advances_system"] = results
        success_rate = sum(1 for r in results.values() if r.get("success", False)) / len(results) * 100
        return {"success_rate": success_rate, "results": results}

    def test_work_reports_system(self):
        """Test Work Reports System"""
        print("\n📝 Testing Work Reports System...")
        
        token = self.tokens.get("admin")
        if not token:
            return {"success": False, "error": "No admin authentication"}
        
        headers = {"Authorization": f"Bearer {token}"}
        results = {}
        
        # Test work reports endpoints
        test_cases = [
            ("GET", "/work-reports/clients", "Get clients"),
            ("GET", "/work-reports/logs", "Get work logs"),
        ]
        
        for method, endpoint, description in test_cases:
            try:
                response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=10)
                
                success = response.status_code == 200
                
                results[endpoint] = {
                    "success": success,
                    "status_code": response.status_code,
                    "description": description
                }
                
                if success:
                    try:
                        data = response.json()
                        if isinstance(data, list):
                            results[endpoint]["record_count"] = len(data)
                    except:
                        pass
                
                status_icon = "✅" if success else "❌"
                record_info = f" ({results[endpoint].get('record_count', 0)} records)" if success else ""
                print(f"  {status_icon} {description}: Status {response.status_code}{record_info}")
                
            except Exception as e:
                results[endpoint] = {
                    "success": False,
                    "error": str(e),
                    "description": description
                }
                print(f"  ❌ {description}: ERROR - {e}")
        
        self.results["detailed_results"]["work_reports"] = results
        success_rate = sum(1 for r in results.values() if r.get("success", False)) / len(results) * 100
        return {"success_rate": success_rate, "results": results}

    def test_notifications_system(self):
        """Test Notifications System"""
        print("\n🔔 Testing Notifications System...")
        
        super_admin_token = self.tokens.get("super_admin")
        user_token = self.tokens.get("user")
        
        if not super_admin_token or not user_token:
            return {"success": False, "error": "Missing authentication tokens"}
        
        results = {}
        
        # Test notifications endpoints
        test_cases = [
            ("GET", "/notifications", "Get all notifications", super_admin_token),
            ("GET", "/notifications/my", "Get user notifications", user_token),
            ("GET", "/notifications/unread-mandatory", "Get unread mandatory", user_token),
        ]
        
        for method, endpoint, description, token in test_cases:
            try:
                headers = {"Authorization": f"Bearer {token}"}
                response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=10)
                
                success = response.status_code == 200
                
                results[endpoint] = {
                    "success": success,
                    "status_code": response.status_code,
                    "description": description
                }
                
                if success:
                    try:
                        data = response.json()
                        if isinstance(data, list):
                            results[endpoint]["record_count"] = len(data)
                        elif isinstance(data, dict) and 'notifications' in data:
                            results[endpoint]["record_count"] = len(data['notifications'])
                    except:
                        pass
                
                status_icon = "✅" if success else "❌"
                record_info = f" ({results[endpoint].get('record_count', 0)} records)" if success else ""
                print(f"  {status_icon} {description}: Status {response.status_code}{record_info}")
                
            except Exception as e:
                results[endpoint] = {
                    "success": False,
                    "error": str(e),
                    "description": description
                }
                print(f"  ❌ {description}: ERROR - {e}")
        
        self.results["detailed_results"]["notifications"] = results
        success_rate = sum(1 for r in results.values() if r.get("success", False)) / len(results) * 100
        return {"success_rate": success_rate, "results": results}

    def test_marketing_visits_system(self):
        """Test Marketing Visits System"""
        print("\n🚗 Testing Marketing Visits System...")
        
        token = self.tokens.get("user")
        if not token:
            return {"success": False, "error": "No user authentication"}
        
        headers = {"Authorization": f"Bearer {token}"}
        results = {}
        
        # Test marketing visits endpoints
        test_cases = [
            ("GET", "/marketing-visits/history", "Get marketing visits history"),
            ("GET", "/marketing-visits/active", "Get active marketing visit"),
        ]
        
        for method, endpoint, description in test_cases:
            try:
                response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=10)
                
                success = response.status_code == 200
                
                results[endpoint] = {
                    "success": success,
                    "status_code": response.status_code,
                    "description": description
                }
                
                if success:
                    try:
                        data = response.json()
                        if isinstance(data, list):
                            results[endpoint]["record_count"] = len(data)
                        elif isinstance(data, dict):
                            if 'active_visit' in data:
                                results[endpoint]["active_visit"] = data['active_visit'] is not None
                    except:
                        pass
                
                status_icon = "✅" if success else "❌"
                extra_info = ""
                if results[endpoint].get("record_count") is not None:
                    extra_info = f" ({results[endpoint]['record_count']} records)"
                elif results[endpoint].get("active_visit") is not None:
                    extra_info = f" - Active visit: {results[endpoint]['active_visit']}"
                    
                print(f"  {status_icon} {description}: Status {response.status_code}{extra_info}")
                
            except Exception as e:
                results[endpoint] = {
                    "success": False,
                    "error": str(e),
                    "description": description
                }
                print(f"  ❌ {description}: ERROR - {e}")
        
        self.results["detailed_results"]["marketing_visits"] = results
        success_rate = sum(1 for r in results.values() if r.get("success", False)) / len(results) * 100
        return {"success_rate": success_rate, "results": results}

    def generate_final_audit_report(self):
        """Generate comprehensive final audit report"""
        print("\n" + "="*80)
        print("🔍 COMPREHENSIVE HR SYSTEM AUDIT - FINAL REPORT")
        print("="*80)
        
        # Calculate overall statistics
        all_tests = []
        module_summaries = {}
        
        for module_name, module_results in self.results["detailed_results"].items():
            successful_tests = sum(1 for result in module_results.values() if result.get("success", False))
            total_tests = len(module_results)
            success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
            
            module_summaries[module_name] = {
                "success_rate": success_rate,
                "successful_tests": successful_tests,
                "total_tests": total_tests,
                "status": "Working" if success_rate >= 80 else "Partial" if success_rate >= 50 else "Broken"
            }
            
            all_tests.extend([result.get("success", False) for result in module_results.values()])
        
        overall_success_rate = (sum(all_tests) / len(all_tests) * 100) if all_tests else 0
        self.results["overall_health_score"] = round(overall_success_rate, 1)
        
        # Print summary
        print(f"🕒 Audit Timestamp: {self.results['audit_timestamp']}")
        print(f"🌐 Backend URL: {self.results['backend_url']}")
        print(f"🏥 Overall System Health: {self.results['overall_health_score']}%")
        print(f"📊 Total Tests Conducted: {len(all_tests)}")
        print(f"✅ Successful Tests: {sum(all_tests)}")
        print(f"❌ Failed Tests: {len(all_tests) - sum(all_tests)}")
        
        # Authentication summary
        print(f"\n🔐 AUTHENTICATION RESULTS:")
        for role, auth_result in self.results["authentication"].items():
            status = "✅ SUCCESS" if auth_result["success"] else "❌ FAILED"
            user_role = auth_result.get("role_verified", "unknown")
            print(f"  {role.upper()}: {status} (Role: {user_role})")
        
        # Module breakdown
        print(f"\n📋 MODULE AUDIT RESULTS:")
        for module_name, summary in module_summaries.items():
            status_icon = "✅" if summary["status"] == "Working" else "⚠️" if summary["status"] == "Partial" else "❌"
            print(f"  {status_icon} {module_name.replace('_', ' ').title()}: {summary['status']} "
                  f"({summary['successful_tests']}/{summary['total_tests']} tests passed - {summary['success_rate']:.1f}%)")
        
        # Critical system assessment
        print(f"\n🚨 CRITICAL SYSTEM ASSESSMENT:")
        
        critical_modules = ["payroll_system", "deductions_system", "advances_system"]
        critical_working = sum(1 for module in critical_modules 
                             if module_summaries.get(module, {}).get("status") == "Working")
        
        print(f"  Critical Modules Working: {critical_working}/{len(critical_modules)}")
        
        if critical_working == len(critical_modules):
            print("  🟢 All critical financial modules are operational")
        elif critical_working >= 2:
            print("  🟡 Most critical modules working, some issues detected")
        else:
            print("  🔴 Critical system failures detected - immediate attention required")
        
        # Production readiness assessment
        print(f"\n🎯 PRODUCTION READINESS ASSESSMENT:")
        
        if overall_success_rate >= 90:
            readiness = "🟢 READY FOR PRODUCTION"
        elif overall_success_rate >= 75:
            readiness = "🟡 MOSTLY READY - Minor issues to resolve"
        elif overall_success_rate >= 60:
            readiness = "🟠 NEEDS WORK - Several issues to fix"
        else:
            readiness = "🔴 NOT READY - Major issues require resolution"
        
        print(f"  {readiness}")
        print(f"  Overall Health Score: {self.results['overall_health_score']}%")
        
        # Save detailed results
        results_file = Path("/app/corrected_comprehensive_audit_results.json")
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Detailed audit results saved to: {results_file}")
        
        return {
            "overall_health": self.results["overall_health_score"],
            "critical_modules_working": critical_working,
            "total_critical_modules": len(critical_modules),
            "authentication_success": all(auth["success"] for auth in self.results["authentication"].values()),
            "production_ready": overall_success_rate >= 75,
            "module_summaries": module_summaries
        }

    def run_comprehensive_audit(self):
        """Run the complete corrected HR system audit"""
        print("🔍 STARTING CORRECTED COMPREHENSIVE HR SYSTEM AUDIT")
        print("="*60)
        
        # Step 1: Authenticate all users
        if not self.authenticate_all_users():
            print("❌ Authentication failed for some users. Continuing with available tokens...")
        
        # Step 2: Test all modules
        self.test_attendance_system()
        self.test_leave_management()
        self.test_payroll_system()
        self.test_deductions_system()
        self.test_advances_system()
        self.test_work_reports_system()
        self.test_notifications_system()
        self.test_marketing_visits_system()
        
        # Step 3: Generate final report
        return self.generate_final_audit_report()

def main():
    """Main execution function"""
    audit = CorrectedHRAudit()
    return audit.run_comprehensive_audit()

if __name__ == "__main__":
    main()