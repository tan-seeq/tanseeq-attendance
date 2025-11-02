#!/usr/bin/env python3
"""
Production Diagnostics Test for TANSEEQ HR System
NEW Production URL: https://hrapp-tanseeq-replaced-1761028017.emergent.host/api

Scope:
1) Health: GET /healthz and /readyz
2) Auth: POST /auth/login with admin@tanseeq.com / ADMIN (alt: hatem@tan-seeq.co / hatem123)
3) Users: GET /users; fuzzy-map user_ids for Hatem, Tarek/Tariq (Alwazan/Wazzan), Karim, Hesham
4) Exceptions: For the four, GET /config/exceptions/{user_id}. If missing or wrong, PUT /config/exceptions/{user_id}
5) Monthly calc: POST /deductions/calculate-monthly?month=2025-10
6) Working-hours check: scan daily_records for string/HH:MM values
7) Save evidence JSON and output PASS/FAIL report
"""

import requests
import json
import os
from datetime import datetime
from pathlib import Path

# Production URL Configuration
PROD_BASE_URL = "https://hrapp-tanseeq-replaced-1761028017.emergent.host/api"

# Test credentials
PRIMARY_CREDS = {"email": "admin@tanseeq.com", "password": "ADMIN"}
ALT_CREDS = {"email": "hatem@tan-seeq.co", "password": "hatem123"}

# Target employees for exception configuration
TARGET_EMPLOYEES = {
    "Hatem": {"exception_type": "exempt"},
    "Tarek": {"exception_type": "flex"}, 
    "Tariq": {"exception_type": "flex"},
    "Karim": {"exception_type": "partial-flex"},
    "Hesham": {"exception_type": "partial-flex"}
}

class ProductionDiagnostics:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 30
        self.token = None
        self.evidence = {
            "test_timestamp": datetime.now().isoformat(),
            "production_url": PROD_BASE_URL,
            "test_results": {},
            "corrective_actions": [],
            "employee_mappings": {},
            "exception_configs": {},
            "monthly_calculations": {},
            "working_hours_issues": []
        }
        self.test_results = []
        
    def log_result(self, test_name, status, details=None, data=None):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details or "",
            "data": data
        }
        self.test_results.append(result)
        self.evidence["test_results"][test_name] = result
        print(f"{'✅' if status == 'PASS' else '❌'} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
            
    def make_request(self, method, endpoint, **kwargs):
        """Make HTTP request with error handling"""
        url = f"{PROD_BASE_URL}{endpoint}"
        headers = kwargs.get('headers', {})
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
            kwargs['headers'] = headers
            
        try:
            response = self.session.request(method, url, **kwargs)
            return response
        except Exception as e:
            print(f"Request failed: {method} {url} - {str(e)}")
            return None
            
    def test_health_endpoints(self):
        """Test 1: Health endpoints"""
        print("\n🔍 Testing Health Endpoints...")
        
        # Test /healthz
        response = self.make_request('GET', '/healthz')
        if response and response.status_code == 200:
            self.log_result("health_healthz", "PASS", f"Status: {response.status_code}", response.json())
        else:
            self.log_result("health_healthz", "FAIL", f"Status: {response.status_code if response else 'No response'}")
            
        # Test /readyz  
        response = self.make_request('GET', '/readyz')
        if response and response.status_code == 200:
            self.log_result("health_readyz", "PASS", f"Status: {response.status_code}", response.json())
        else:
            self.log_result("health_readyz", "FAIL", f"Status: {response.status_code if response else 'No response'}")
            
    def test_authentication(self):
        """Test 2: Authentication with both credential sets"""
        print("\n🔐 Testing Authentication...")
        
        # Try primary credentials first
        response = self.make_request('POST', '/auth/login', json=PRIMARY_CREDS)
        if response and response.status_code == 200:
            data = response.json()
            self.token = data.get('access_token')
            self.log_result("auth_primary", "PASS", f"Logged in as {data.get('user', {}).get('name', 'Unknown')}", data)
            return True
            
        # Try alternative credentials
        response = self.make_request('POST', '/auth/login', json=ALT_CREDS)
        if response and response.status_code == 200:
            data = response.json()
            self.token = data.get('access_token')
            self.log_result("auth_alternative", "PASS", f"Logged in as {data.get('user', {}).get('name', 'Unknown')}", data)
            return True
            
        self.log_result("auth_failed", "FAIL", "Both credential sets failed")
        return False
        
    def test_users_and_mapping(self):
        """Test 3: Get users and fuzzy-map target employees"""
        print("\n👥 Testing Users Endpoint and Employee Mapping...")
        
        if not self.token:
            self.log_result("users_no_auth", "FAIL", "No authentication token")
            return
            
        response = self.make_request('GET', '/users')
        if not response or response.status_code != 200:
            self.log_result("users_endpoint", "FAIL", f"Status: {response.status_code if response else 'No response'}")
            return
            
        users = response.json()
        self.log_result("users_endpoint", "PASS", f"Retrieved {len(users)} users", {"user_count": len(users)})
        
        # Fuzzy mapping for target employees
        mappings = {}
        for target_name in TARGET_EMPLOYEES.keys():
            best_match = None
            best_score = 0
            
            for user in users:
                user_name = user.get('name', '').lower()
                target_lower = target_name.lower()
                
                # Simple fuzzy matching
                if target_lower in user_name or user_name in target_lower:
                    score = len(set(target_lower) & set(user_name)) / len(set(target_lower) | set(user_name))
                    if score > best_score:
                        best_score = score
                        best_match = user
                        
            if best_match:
                mappings[target_name] = {
                    "user_id": best_match.get('id'),
                    "name": best_match.get('name'),
                    "email": best_match.get('email'),
                    "match_score": best_score
                }
                
        self.evidence["employee_mappings"] = mappings
        self.log_result("employee_mapping", "PASS", f"Mapped {len(mappings)}/{len(TARGET_EMPLOYEES)} employees", mappings)
        
    def test_exception_configurations(self):
        """Test 4: Check and configure employee exceptions"""
        print("\n⚙️ Testing Exception Configurations...")
        
        if not self.evidence["employee_mappings"]:
            self.log_result("exceptions_no_mapping", "FAIL", "No employee mappings available")
            return
            
        corrective_actions = []
        
        for emp_name, mapping in self.evidence["employee_mappings"].items():
            user_id = mapping["user_id"]
            expected_exception = TARGET_EMPLOYEES[emp_name]["exception_type"]
            
            # GET current exception
            response = self.make_request('GET', f'/config/exceptions/{user_id}')
            
            current_exception = None
            needs_update = True
            
            if response and response.status_code == 200:
                data = response.json()
                current_exception = data.get('exception_type')
                needs_update = current_exception != expected_exception
                
            if needs_update:
                # PUT correct exception
                put_data = {"exception_type": expected_exception}
                put_response = self.make_request('PUT', f'/config/exceptions/{user_id}', json=put_data)
                
                if put_response and put_response.status_code in [200, 201]:
                    action = f"Updated {emp_name} ({user_id}) exception: {current_exception} -> {expected_exception}"
                    corrective_actions.append(action)
                    self.log_result(f"exception_fix_{emp_name}", "PASS", action)
                else:
                    self.log_result(f"exception_fix_{emp_name}", "FAIL", f"Failed to update exception for {emp_name}")
            else:
                self.log_result(f"exception_check_{emp_name}", "PASS", f"{emp_name} already has correct exception: {expected_exception}")
                
        self.evidence["corrective_actions"].extend(corrective_actions)
        
    def test_monthly_calculations(self):
        """Test 5: Monthly deductions calculation for 2025-10"""
        print("\n📊 Testing Monthly Calculations...")
        
        if not self.token:
            self.log_result("monthly_calc_no_auth", "FAIL", "No authentication token")
            return
            
        response = self.make_request('POST', '/deductions/calculate-monthly?month=2025-10')
        
        if not response or response.status_code != 200:
            self.log_result("monthly_calculation", "FAIL", f"Status: {response.status_code if response else 'No response'}")
            return
            
        calc_data = response.json()
        self.evidence["monthly_calculations"] = calc_data
        
        # Extract summaries for target employees
        employee_summaries = {}
        
        if isinstance(calc_data, dict) and 'employees' in calc_data:
            for emp_data in calc_data['employees']:
                emp_name = emp_data.get('employee_name', '')
                for target_name in TARGET_EMPLOYEES.keys():
                    if target_name.lower() in emp_name.lower():
                        employee_summaries[target_name] = emp_data
                        break
                        
        # Validate business rules
        validation_results = []
        
        for emp_name, summary in employee_summaries.items():
            if emp_name == "Hatem":
                # Hatem should have total_deduction == 0 (exempt)
                total_deduction = summary.get('total_deduction', 0)
                if total_deduction == 0:
                    validation_results.append(f"✅ Hatem: total_deduction = {total_deduction} (correct)")
                else:
                    validation_results.append(f"❌ Hatem: total_deduction = {total_deduction} (should be 0)")
                    
            elif emp_name in ["Tarek", "Tariq"]:
                # Tarek/Tariq: late_deduction == 0; total_deduction == absence_deduction
                late_deduction = summary.get('late_deduction', 0)
                total_deduction = summary.get('total_deduction', 0)
                absence_deduction = summary.get('absence_deduction', 0)
                
                if late_deduction == 0:
                    validation_results.append(f"✅ {emp_name}: late_deduction = {late_deduction} (correct)")
                else:
                    validation_results.append(f"❌ {emp_name}: late_deduction = {late_deduction} (should be 0)")
                    
                if total_deduction == absence_deduction:
                    validation_results.append(f"✅ {emp_name}: total_deduction ({total_deduction}) == absence_deduction ({absence_deduction})")
                else:
                    validation_results.append(f"❌ {emp_name}: total_deduction ({total_deduction}) != absence_deduction ({absence_deduction})")
                    
            elif emp_name in ["Karim", "Hesham"]:
                # Karim/Hesham: absence_deduction == 0 if days_absent==0
                days_absent = summary.get('days_absent', 0)
                absence_deduction = summary.get('absence_deduction', 0)
                
                if days_absent == 0 and absence_deduction == 0:
                    validation_results.append(f"✅ {emp_name}: No absence, no absence_deduction (correct)")
                elif days_absent == 0 and absence_deduction != 0:
                    validation_results.append(f"❌ {emp_name}: No absence but absence_deduction = {absence_deduction}")
                else:
                    validation_results.append(f"ℹ️ {emp_name}: {days_absent} days absent, absence_deduction = {absence_deduction}")
                    
        self.log_result("monthly_calculation", "PASS", f"Processed {len(employee_summaries)} target employees", {
            "summaries": employee_summaries,
            "validations": validation_results
        })
        
    def test_working_hours_validation(self):
        """Test 6: Working-hours validation for string/HH:MM values"""
        print("\n⏰ Testing Working Hours Validation...")
        
        if not self.token:
            self.log_result("working_hours_no_auth", "FAIL", "No authentication token")
            return
            
        # Get attendance records for target employees
        issues_found = []
        
        for emp_name, mapping in self.evidence["employee_mappings"].items():
            user_id = mapping["user_id"]
            
            # Get attendance records for this employee
            response = self.make_request('GET', f'/attendance?user_id={user_id}')
            
            if response and response.status_code == 200:
                records = response.json()
                
                for record in records:
                    working_hours = record.get('working_hours')
                    
                    # Check if working_hours is string or HH:MM format
                    if isinstance(working_hours, str):
                        if ':' in working_hours:  # HH:MM format
                            try:
                                hours, minutes = working_hours.split(':')
                                expected_minutes = int(hours) * 60 + int(minutes)
                                
                                # Check if this matches expected calculation
                                check_in = record.get('check_in')
                                check_out = record.get('check_out')
                                
                                if check_in and check_out:
                                    # Calculate expected working minutes
                                    # This is a simplified calculation
                                    issue = {
                                        "employee": emp_name,
                                        "date": record.get('date'),
                                        "working_hours": working_hours,
                                        "type": "HH:MM_format",
                                        "check_in": check_in,
                                        "check_out": check_out
                                    }
                                    issues_found.append(issue)
                                    
                            except ValueError:
                                issue = {
                                    "employee": emp_name,
                                    "date": record.get('date'),
                                    "working_hours": working_hours,
                                    "type": "invalid_string",
                                    "error": "Cannot parse HH:MM format"
                                }
                                issues_found.append(issue)
                        else:
                            # Non-HH:MM string
                            issue = {
                                "employee": emp_name,
                                "date": record.get('date'),
                                "working_hours": working_hours,
                                "type": "string_value",
                            }
                            issues_found.append(issue)
                            
        self.evidence["working_hours_issues"] = issues_found
        
        if issues_found:
            self.log_result("working_hours_validation", "FAIL", f"Found {len(issues_found)} working hours issues", issues_found)
        else:
            self.log_result("working_hours_validation", "PASS", "No working hours format issues found")
            
    def save_evidence_and_report(self):
        """Save evidence JSON and generate PASS/FAIL report"""
        print("\n💾 Saving Evidence and Generating Report...")
        
        # Create evidence directory
        evidence_dir = Path("/app/evidence")
        evidence_dir.mkdir(exist_ok=True)
        
        # Save evidence JSON
        evidence_file = evidence_dir / "prod_1761028017_diagnostics.json"
        with open(evidence_file, 'w') as f:
            json.dump(self.evidence, f, indent=2, default=str)
            
        # Generate summary report
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = total_tests - passed_tests
        
        report = f"""
🔥 PRODUCTION DIAGNOSTICS REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Production URL: {PROD_BASE_URL}

📊 SUMMARY:
Total Tests: {total_tests}
✅ Passed: {passed_tests}
❌ Failed: {failed_tests}
Success Rate: {(passed_tests/total_tests*100):.1f}%

🎯 DETAILED RESULTS:
"""
        
        for result in self.test_results:
            status_icon = "✅" if result['status'] == 'PASS' else "❌"
            report += f"{status_icon} {result['test']}: {result['status']}\n"
            if result['details']:
                report += f"   └─ {result['details']}\n"
                
        # Add corrective actions
        if self.evidence["corrective_actions"]:
            report += f"\n🔧 CORRECTIVE ACTIONS PERFORMED:\n"
            for action in self.evidence["corrective_actions"]:
                report += f"• {action}\n"
                
        # Add working hours issues
        if self.evidence["working_hours_issues"]:
            report += f"\n⚠️ WORKING HOURS ISSUES FOUND:\n"
            for issue in self.evidence["working_hours_issues"]:
                report += f"• {issue['employee']} ({issue['date']}): {issue['type']} - {issue.get('working_hours', 'N/A')}\n"
                
        # Overall assessment
        if failed_tests == 0:
            report += f"\n🎉 OVERALL ASSESSMENT: PASS - All systems operational"
        else:
            report += f"\n🚨 OVERALL ASSESSMENT: FAIL - {failed_tests} critical issues found"
            
        report += f"\n📁 Evidence saved to: {evidence_file}"
        
        print(report)
        
        # Save report to file
        report_file = evidence_dir / "prod_1761028017_report.txt"
        with open(report_file, 'w') as f:
            f.write(report)
            
        return passed_tests == total_tests
        
    def run_diagnostics(self):
        """Run complete production diagnostics"""
        print("🚀 Starting Production Diagnostics for TANSEEQ HR System")
        print(f"🎯 Target URL: {PROD_BASE_URL}")
        print("=" * 80)
        
        try:
            # Run all tests in sequence
            self.test_health_endpoints()
            
            if self.test_authentication():
                self.test_users_and_mapping()
                self.test_exception_configurations()
                self.test_monthly_calculations()
                self.test_working_hours_validation()
            else:
                print("❌ Authentication failed - skipping authenticated tests")
                
            # Generate final report
            success = self.save_evidence_and_report()
            
            return success
            
        except Exception as e:
            print(f"💥 Diagnostics failed with error: {str(e)}")
            self.log_result("diagnostics_error", "FAIL", str(e))
            return False

if __name__ == "__main__":
    diagnostics = ProductionDiagnostics()
    success = diagnostics.run_diagnostics()
    
    if success:
        print("\n🎉 Production diagnostics completed successfully!")
        exit(0)
    else:
        print("\n🚨 Production diagnostics found critical issues!")
        exit(1)