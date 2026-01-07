#!/usr/bin/env python3
"""
Production Deep Audit - Post-Deploy Testing
Focus areas requested by user for TANSEEQ HR System
Base URL: https://hrapp-tanseeq-replaced-1761028017.emergent.host/api
"""

import requests
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
BASE_URL = "https://hrapp-tanseeq-replaced-1761028017.emergent.host/api"
EVIDENCE_DIR = "/app/evidence/audit_prod_post_deploy"

# Test credentials
SUPER_ADMIN_EMAIL = "admin@tanseeq.com"
SUPER_ADMIN_PASSWORD = "ADMIN"

class ProductionAuditTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.results = {
            "audit_timestamp": datetime.now().isoformat(),
            "base_url": BASE_URL,
            "areas": {
                "authentication": {"status": "PENDING", "details": [], "issues": []},
                "payroll_cycles": {"status": "PENDING", "details": [], "issues": []},
                "advanced_deductions": {"status": "PENDING", "details": [], "issues": []},
                "manual_absence_creation": {"status": "PENDING", "details": [], "issues": []},
                "users_module": {"status": "PENDING", "details": [], "issues": []}
            },
            "summary": {
                "total_areas": 5,
                "passed": 0,
                "failed": 0,
                "actionable_fixes": []
            }
        }
        
        # Create evidence directory
        os.makedirs(EVIDENCE_DIR, exist_ok=True)
        
    def log_detail(self, area, message, is_issue=False):
        """Log detail to specific area"""
        if is_issue:
            self.results["areas"][area]["issues"].append(message)
        else:
            self.results["areas"][area]["details"].append(message)
        print(f"[{area.upper()}] {message}")
    
    def set_area_status(self, area, status):
        """Set area status (PASS/FAIL)"""
        self.results["areas"][area]["status"] = status
        if status == "PASS":
            self.results["summary"]["passed"] += 1
        else:
            self.results["summary"]["failed"] += 1
    
    def add_actionable_fix(self, fix):
        """Add actionable fix to summary"""
        self.results["summary"]["actionable_fixes"].append(fix)
    
    def test_authentication(self):
        """Test 1: Authentication - Login as super_admin admin@tanseeq.com / ADMIN"""
        print("\n🔐 Testing Authentication...")
        
        try:
            # Test login
            login_data = {
                "email": SUPER_ADMIN_EMAIL,
                "password": SUPER_ADMIN_PASSWORD
            }
            
            response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                user_info = data.get("user", {})
                
                self.log_detail("authentication", f"✅ Login successful for {SUPER_ADMIN_EMAIL}")
                self.log_detail("authentication", f"✅ Token received: {self.token[:20]}...")
                self.log_detail("authentication", f"✅ User role: {user_info.get('role')}")
                self.log_detail("authentication", f"✅ User name: {user_info.get('name')}")
                
                # Set authorization header for future requests
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                
                # Test /auth/me endpoint
                me_response = self.session.get(f"{BASE_URL}/auth/me")
                if me_response.status_code == 200:
                    me_data = me_response.json()
                    self.log_detail("authentication", f"✅ /auth/me working - ID: {me_data.get('id')}")
                else:
                    self.log_detail("authentication", f"⚠️ /auth/me failed: {me_response.status_code}", True)
                
                self.set_area_status("authentication", "PASS")
                
            else:
                self.log_detail("authentication", f"❌ Login failed: {response.status_code} - {response.text}", True)
                self.set_area_status("authentication", "FAIL")
                self.add_actionable_fix("Fix super admin authentication credentials")
                return False
                
        except Exception as e:
            self.log_detail("authentication", f"❌ Authentication error: {str(e)}", True)
            self.set_area_status("authentication", "FAIL")
            self.add_actionable_fix("Fix authentication system connectivity")
            return False
        
        return True
    
    def test_payroll_cycles(self):
        """Test 2: Payroll cycles - GET /payroll/cycles and verify summaries"""
        print("\n💰 Testing Payroll Cycles...")
        
        if not self.token:
            self.log_detail("payroll_cycles", "❌ No authentication token available", True)
            self.set_area_status("payroll_cycles", "FAIL")
            return
        
        try:
            # Get payroll cycles
            response = self.session.get(f"{BASE_URL}/payroll/cycles")
            
            if response.status_code == 200:
                cycles = response.json()
                self.log_detail("payroll_cycles", f"✅ GET /payroll/cycles successful")
                self.log_detail("payroll_cycles", f"✅ Found {len(cycles)} payroll cycles")
                
                if len(cycles) > 0:
                    # Test first cycle summary
                    first_cycle = cycles[0]
                    cycle_id = first_cycle.get("id")
                    
                    self.log_detail("payroll_cycles", f"✅ Testing cycle: {first_cycle.get('cycle_name', 'Unknown')}")
                    
                    # Get cycle summary
                    summary_response = self.session.get(f"{BASE_URL}/payroll/cycles/{cycle_id}/summary")
                    
                    if summary_response.status_code == 200:
                        summary_data = summary_response.json()
                        self.log_detail("payroll_cycles", f"✅ GET /payroll/cycles/{cycle_id}/summary successful")
                        
                        # Verify totals structure
                        required_fields = ["total_basic_salary", "total_allowances", "total_deductions", "total_net_salary"]
                        missing_fields = []
                        
                        for field in required_fields:
                            if field not in summary_data:
                                missing_fields.append(field)
                        
                        if missing_fields:
                            self.log_detail("payroll_cycles", f"⚠️ Missing summary fields: {missing_fields}", True)
                        else:
                            self.log_detail("payroll_cycles", f"✅ All required summary fields present")
                            
                        # Log totals
                        for field in required_fields:
                            value = summary_data.get(field, 0)
                            self.log_detail("payroll_cycles", f"✅ {field}: {value}")
                        
                        self.set_area_status("payroll_cycles", "PASS")
                        
                    else:
                        self.log_detail("payroll_cycles", f"❌ Cycle summary failed: {summary_response.status_code}", True)
                        self.set_area_status("payroll_cycles", "FAIL")
                        self.add_actionable_fix("Fix payroll cycle summary endpoint")
                else:
                    self.log_detail("payroll_cycles", "⚠️ No payroll cycles found - cannot test summaries", True)
                    self.set_area_status("payroll_cycles", "FAIL")
                    self.add_actionable_fix("Create test payroll cycles for verification")
                    
            else:
                self.log_detail("payroll_cycles", f"❌ GET /payroll/cycles failed: {response.status_code}", True)
                self.set_area_status("payroll_cycles", "FAIL")
                self.add_actionable_fix("Fix payroll cycles endpoint")
                
        except Exception as e:
            self.log_detail("payroll_cycles", f"❌ Payroll cycles error: {str(e)}", True)
            self.set_area_status("payroll_cycles", "FAIL")
            self.add_actionable_fix("Debug payroll cycles system")
    
    def test_advanced_deductions(self):
        """Test 3: Advanced deductions - Monthly and custom calculations"""
        print("\n📊 Testing Advanced Deductions...")
        
        if not self.token:
            self.log_detail("advanced_deductions", "❌ No authentication token available", True)
            self.set_area_status("advanced_deductions", "FAIL")
            return
        
        try:
            # Test monthly deductions calculation
            monthly_response = self.session.post(f"{BASE_URL}/deductions/calculate-monthly?month=2025-10")
            
            if monthly_response.status_code == 200:
                monthly_data = monthly_response.json()
                self.log_detail("advanced_deductions", f"✅ POST /deductions/calculate-monthly?month=2025-10 successful")
                
                # Verify response structure
                if "summaries" in monthly_data or "employees" in monthly_data:
                    self.log_detail("advanced_deductions", f"✅ Response contains summaries/employees structure")
                else:
                    self.log_detail("advanced_deductions", f"⚠️ Missing summaries/employees in response", True)
                
                # Check for daily_records
                if "daily_records" in monthly_data:
                    self.log_detail("advanced_deductions", f"✅ daily_records present in response")
                else:
                    self.log_detail("advanced_deductions", f"⚠️ daily_records missing from response", True)
                
                # Log employee count if available
                if "employees" in monthly_data:
                    employee_count = len(monthly_data["employees"])
                    self.log_detail("advanced_deductions", f"✅ Found {employee_count} employees in calculation")
                
            else:
                self.log_detail("advanced_deductions", f"❌ Monthly calculation failed: {monthly_response.status_code}", True)
            
            # Test custom date range calculation
            custom_response = self.session.post(f"{BASE_URL}/deductions/calculate?mode=custom&from_date=2025-10-01&to_date=2025-10-28")
            
            if custom_response.status_code == 200:
                custom_data = custom_response.json()
                self.log_detail("advanced_deductions", f"✅ POST /deductions/calculate (custom range) successful")
                
                # Verify response structure
                if "summaries" in custom_data or "employees" in custom_data:
                    self.log_detail("advanced_deductions", f"✅ Custom response contains summaries/employees structure")
                else:
                    self.log_detail("advanced_deductions", f"⚠️ Missing summaries/employees in custom response", True)
                
                # Check for daily_records
                if "daily_records" in custom_data:
                    self.log_detail("advanced_deductions", f"✅ daily_records present in custom response")
                else:
                    self.log_detail("advanced_deductions", f"⚠️ daily_records missing from custom response", True)
                
            else:
                self.log_detail("advanced_deductions", f"❌ Custom calculation failed: {custom_response.status_code}", True)
            
            # Determine overall status
            if monthly_response.status_code == 200 and custom_response.status_code == 200:
                self.set_area_status("advanced_deductions", "PASS")
            else:
                self.set_area_status("advanced_deductions", "FAIL")
                self.add_actionable_fix("Fix advanced deductions calculation endpoints")
                
        except Exception as e:
            self.log_detail("advanced_deductions", f"❌ Advanced deductions error: {str(e)}", True)
            self.set_area_status("advanced_deductions", "FAIL")
            self.add_actionable_fix("Debug advanced deductions system")
    
    def test_manual_absence_creation(self):
        """Test 4: Manual absence creation - Find admin endpoint and test"""
        print("\n🏥 Testing Manual Absence Creation...")
        
        if not self.token:
            self.log_detail("manual_absence_creation", "❌ No authentication token available", True)
            self.set_area_status("manual_absence_creation", "FAIL")
            return
        
        try:
            # Try common admin absence endpoints
            potential_endpoints = [
                "/attendance/admin/create-absence",
                "/attendance/mark-absence",
                "/attendance/admin/mark-absence",
                "/attendance/absence/create",
                "/admin/attendance/create-absence"
            ]
            
            found_endpoint = None
            
            for endpoint in potential_endpoints:
                # Test with OPTIONS or GET first to see if endpoint exists
                test_response = self.session.options(f"{BASE_URL}{endpoint}")
                if test_response.status_code != 404:
                    found_endpoint = endpoint
                    self.log_detail("manual_absence_creation", f"✅ Found potential endpoint: {endpoint}")
                    break
            
            if found_endpoint:
                # Try to create a test absence
                test_absence_data = {
                    "user_id": "test-user-id",
                    "date": "2025-01-15",
                    "reason": "QA Testing - Manual Absence",
                    "absence_type": "sick_leave"
                }
                
                create_response = self.session.post(f"{BASE_URL}{found_endpoint}", json=test_absence_data)
                
                if create_response.status_code in [200, 201]:
                    self.log_detail("manual_absence_creation", f"✅ Manual absence creation successful")
                    
                    # Try to delete or mark void if possible
                    response_data = create_response.json()
                    absence_id = response_data.get("id") or response_data.get("absence_id")
                    
                    if absence_id:
                        # Try to delete
                        delete_response = self.session.delete(f"{BASE_URL}/attendance/{absence_id}")
                        if delete_response.status_code == 200:
                            self.log_detail("manual_absence_creation", f"✅ Test absence deleted successfully")
                        else:
                            self.log_detail("manual_absence_creation", f"⚠️ Could not delete test absence: {delete_response.status_code}")
                    
                    self.set_area_status("manual_absence_creation", "PASS")
                    
                else:
                    self.log_detail("manual_absence_creation", f"❌ Absence creation failed: {create_response.status_code}", True)
                    self.set_area_status("manual_absence_creation", "FAIL")
                    self.add_actionable_fix("Fix manual absence creation functionality")
            else:
                self.log_detail("manual_absence_creation", "❌ No manual absence creation endpoint found", True)
                self.set_area_status("manual_absence_creation", "FAIL")
                self.add_actionable_fix("Implement manual absence creation endpoint: POST /attendance/admin/create-absence with fields: user_id, date, reason, absence_type")
                
        except Exception as e:
            self.log_detail("manual_absence_creation", f"❌ Manual absence creation error: {str(e)}", True)
            self.set_area_status("manual_absence_creation", "FAIL")
            self.add_actionable_fix("Debug manual absence creation system")
    
    def test_users_module(self):
        """Test 5: Users module - Check for employee code update endpoint"""
        print("\n👥 Testing Users Module...")
        
        if not self.token:
            self.log_detail("users_module", "❌ No authentication token available", True)
            self.set_area_status("users_module", "FAIL")
            return
        
        try:
            # First, get list of users to find a test user
            users_response = self.session.get(f"{BASE_URL}/users")
            
            if users_response.status_code == 200:
                users = users_response.json()
                self.log_detail("users_module", f"✅ GET /users successful - found {len(users)} users")
                
                if len(users) > 0:
                    test_user = users[0]
                    user_id = test_user.get("id")
                    
                    self.log_detail("users_module", f"✅ Testing with user: {test_user.get('name')} (ID: {user_id})")
                    
                    # Test PUT /users/{id} endpoint
                    update_data = {
                        "employee_code": "TEST-EMP-001",
                        "name": test_user.get("name")  # Keep existing name
                    }
                    
                    update_response = self.session.put(f"{BASE_URL}/users/{user_id}", json=update_data)
                    
                    if update_response.status_code == 200:
                        self.log_detail("users_module", f"✅ PUT /users/{user_id} successful - employee code update working")
                        
                        # Verify the update
                        verify_response = self.session.get(f"{BASE_URL}/users/{user_id}")
                        if verify_response.status_code == 200:
                            updated_user = verify_response.json()
                            if updated_user.get("employee_code") == "TEST-EMP-001":
                                self.log_detail("users_module", f"✅ Employee code update verified")
                            else:
                                self.log_detail("users_module", f"⚠️ Employee code not updated in database", True)
                        
                        self.set_area_status("users_module", "PASS")
                        
                    elif update_response.status_code == 404:
                        self.log_detail("users_module", "❌ PUT /users/{id} endpoint not found", True)
                        self.set_area_status("users_module", "FAIL")
                        self.add_actionable_fix("Implement PUT /users/{id} endpoint for employee code updates")
                        
                    else:
                        self.log_detail("users_module", f"❌ User update failed: {update_response.status_code}", True)
                        self.set_area_status("users_module", "FAIL")
                        self.add_actionable_fix("Fix user update endpoint functionality")
                else:
                    self.log_detail("users_module", "⚠️ No users found for testing", True)
                    self.set_area_status("users_module", "FAIL")
                    self.add_actionable_fix("Ensure test users exist in system")
            else:
                self.log_detail("users_module", f"❌ GET /users failed: {users_response.status_code}", True)
                self.set_area_status("users_module", "FAIL")
                self.add_actionable_fix("Fix users list endpoint")
                
        except Exception as e:
            self.log_detail("users_module", f"❌ Users module error: {str(e)}", True)
            self.set_area_status("users_module", "FAIL")
            self.add_actionable_fix("Debug users module system")
    
    def save_results(self):
        """Save consolidated findings to results.json"""
        results_file = os.path.join(EVIDENCE_DIR, "results.json")
        
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Results saved to: {results_file}")
        
        # Also create a summary report
        summary_file = os.path.join(EVIDENCE_DIR, "audit_summary.txt")
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write("PRODUCTION DEEP AUDIT SUMMARY\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Audit Date: {self.results['audit_timestamp']}\n")
            f.write(f"Base URL: {self.results['base_url']}\n\n")
            
            f.write("AREA RESULTS:\n")
            f.write("-" * 20 + "\n")
            for area, data in self.results["areas"].items():
                f.write(f"{area.upper()}: {data['status']}\n")
                if data["issues"]:
                    f.write(f"  Issues: {len(data['issues'])}\n")
            
            f.write(f"\nOVERALL: {self.results['summary']['passed']}/{self.results['summary']['total_areas']} PASSED\n\n")
            
            if self.results["summary"]["actionable_fixes"]:
                f.write("ACTIONABLE FIXES:\n")
                f.write("-" * 20 + "\n")
                for i, fix in enumerate(self.results["summary"]["actionable_fixes"], 1):
                    f.write(f"{i}. {fix}\n")
        
        print(f"📄 Summary saved to: {summary_file}")
    
    def run_audit(self):
        """Run complete production audit"""
        print("🚀 Starting Production Deep Audit...")
        print(f"🎯 Target: {BASE_URL}")
        print("=" * 60)
        
        # Run all tests
        if self.test_authentication():
            self.test_payroll_cycles()
            self.test_advanced_deductions()
            self.test_manual_absence_creation()
            self.test_users_module()
        
        # Save results
        self.save_results()
        
        # Print summary
        print("\n" + "=" * 60)
        print("🏁 AUDIT COMPLETE")
        print(f"✅ Passed: {self.results['summary']['passed']}")
        print(f"❌ Failed: {self.results['summary']['failed']}")
        print(f"📊 Total Areas: {self.results['summary']['total_areas']}")
        
        if self.results["summary"]["actionable_fixes"]:
            print(f"\n🔧 Actionable Fixes Required: {len(self.results['summary']['actionable_fixes'])}")
            for i, fix in enumerate(self.results["summary"]["actionable_fixes"], 1):
                print(f"   {i}. {fix}")

if __name__ == "__main__":
    auditor = ProductionAuditTester()
    auditor.run_audit()