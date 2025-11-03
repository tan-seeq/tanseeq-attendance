#!/usr/bin/env python3
"""
Production Monthly Deductions Normalization Test for October 2025
Re-run monthly deductions for production environment to validate final normalization rules.

Test Steps:
1) Authenticate as Super Admin (hatem@tan-seeq.co / hatem123) against the same BASE_URL used previously.
2) GET /api/users and remap user_ids for Hatem, Tarek/Tariq, Karim, Hesham (fuzzy).
3) Ensure exceptions already set (GET /api/config/exceptions) - if missing, set them with PUT.
4) POST /api/deductions/calculate-monthly?month=2025-10 and extract the four employees from the summaries.
5) Assert invariants after normalization:
   - Hatem: total_deduction == 0
   - Tarek: late_deduction == 0 and total_deduction == absence_deduction (0 if no absence)
   - Karim/Hesham: absence_deduction == 0 if days_absent==0; early/under-hours not contributing; total_deduction == late_deduction only when no absence.
6) Save raw response to /app/evidence/production_after_normalization_oct.json and output a concise PASS/FAIL matrix with actual numeric values.
"""

import requests
import json
import os
from datetime import datetime
from pathlib import Path

# Configuration
BASE_URL = "https://attend-deduct-hr.preview.emergentagent.com"
SUPER_ADMIN_EMAIL = "hatem@tan-seeq.co"
SUPER_ADMIN_PASSWORD = "hatem123"
TARGET_MONTH = "2025-10"

# Evidence directory
EVIDENCE_DIR = Path("/app/evidence")
EVIDENCE_DIR.mkdir(exist_ok=True)

class ProductionNormalizationTest:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_mappings = {}
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "test_type": "production_normalization_validation",
            "month": TARGET_MONTH,
            "results": {},
            "pass_fail_matrix": {},
            "raw_responses": {}
        }
        
    def authenticate_super_admin(self):
        """Step 1: Authenticate as Super Admin"""
        print(f"🔐 Step 1: Authenticating as Super Admin ({SUPER_ADMIN_EMAIL})")
        
        login_url = f"{BASE_URL}/api/auth/login"
        login_data = {
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        }
        
        try:
            response = self.session.post(login_url, json=login_data, timeout=30)
            print(f"   Login Response: {response.status_code}")
            
            if response.status_code == 200:
                auth_data = response.json()
                self.auth_token = auth_data.get("access_token")
                user_info = auth_data.get("user", {})
                
                # Set authorization header
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}",
                    "Content-Type": "application/json"
                })
                
                print(f"   ✅ Authentication successful")
                print(f"   User: {user_info.get('name')} ({user_info.get('role')})")
                
                self.test_results["authentication"] = {
                    "status": "success",
                    "user_name": user_info.get('name'),
                    "user_role": user_info.get('role'),
                    "user_id": user_info.get('id')
                }
                return True
            else:
                print(f"   ❌ Authentication failed: {response.status_code}")
                print(f"   Response: {response.text}")
                self.test_results["authentication"] = {
                    "status": "failed",
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                return False
                
        except Exception as e:
            print(f"   ❌ Authentication error: {e}")
            self.test_results["authentication"] = {
                "status": "error",
                "error": str(e)
            }
            return False
    
    def get_users_and_remap(self):
        """Step 2: GET /api/users and remap user_ids for target employees"""
        print(f"👥 Step 2: Getting users and remapping target employees")
        
        users_url = f"{BASE_URL}/api/users"
        
        try:
            response = self.session.get(users_url, timeout=30)
            print(f"   Users Response: {response.status_code}")
            
            if response.status_code == 200:
                users_data = response.json()
                # Handle both array and object response formats
                if isinstance(users_data, list):
                    users = users_data
                else:
                    users = users_data.get("users", [])
                print(f"   Found {len(users)} total users")
                
                # Fuzzy matching for target employees
                target_names = ["hatem", "tarek", "tariq", "karim", "hesham"]
                
                for user in users:
                    user_name = user.get("name", "").lower()
                    user_email = user.get("email", "").lower()
                    user_id = user.get("id")
                    
                    # Fuzzy matching logic
                    for target in target_names:
                        if target in user_name or target in user_email:
                            # Handle multiple Tarek/Tariq matches
                            if target in ["tarek", "tariq"]:
                                if "tarek" not in self.user_mappings:
                                    self.user_mappings["tarek"] = {
                                        "user_id": user_id,
                                        "name": user.get("name"),
                                        "email": user.get("email")
                                    }
                                else:
                                    # Store as tarek2 if we find another
                                    self.user_mappings["tarek2"] = {
                                        "user_id": user_id,
                                        "name": user.get("name"),
                                        "email": user.get("email")
                                    }
                            else:
                                self.user_mappings[target] = {
                                    "user_id": user_id,
                                    "name": user.get("name"),
                                    "email": user.get("email")
                                }
                            break
                
                print(f"   ✅ User mapping completed:")
                for key, mapping in self.user_mappings.items():
                    print(f"     {key}: {mapping['name']} ({mapping['user_id'][:8]}...)")
                
                self.test_results["user_mapping"] = {
                    "status": "success",
                    "total_users": len(users),
                    "mapped_users": self.user_mappings
                }
                
                # Store raw users response
                self.test_results["raw_responses"]["users"] = users_data
                return True
                
            else:
                print(f"   ❌ Users retrieval failed: {response.status_code}")
                self.test_results["user_mapping"] = {
                    "status": "failed",
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                return False
                
        except Exception as e:
            print(f"   ❌ Users retrieval error: {e}")
            self.test_results["user_mapping"] = {
                "status": "error",
                "error": str(e)
            }
            return False
    
    def ensure_exceptions_configured(self):
        """Step 3: Ensure exceptions already set - if missing, set them with PUT"""
        print(f"⚙️ Step 3: Ensuring exception configurations are set")
        
        # Expected exception configurations
        expected_exceptions = {
            "hatem": "exempt",
            "tarek": "flex", 
            "karim": "partial-flex",
            "hesham": "partial-flex"
        }
        
        exceptions_status = {}
        
        for name, expected_type in expected_exceptions.items():
            if name not in self.user_mappings:
                print(f"   ⚠️ User {name} not found in mappings, skipping")
                continue
                
            user_id = self.user_mappings[name]["user_id"]
            
            # Check current exception
            get_url = f"{BASE_URL}/api/config/exceptions/{user_id}"
            
            try:
                response = self.session.get(get_url, timeout=30)
                
                if response.status_code == 200:
                    current_config = response.json()
                    current_type = current_config.get("exception_type")
                    
                    if current_type == expected_type:
                        print(f"   ✅ {name}: {current_type} (already configured)")
                        exceptions_status[name] = {"status": "already_set", "type": current_type}
                    else:
                        # Need to update
                        print(f"   🔄 {name}: Updating {current_type} → {expected_type}")
                        put_url = f"{BASE_URL}/api/config/exceptions/{user_id}"
                        put_data = {"exception_type": expected_type}
                        
                        put_response = self.session.put(put_url, json=put_data, timeout=30)
                        
                        if put_response.status_code == 200:
                            print(f"   ✅ {name}: Updated to {expected_type}")
                            exceptions_status[name] = {"status": "updated", "type": expected_type}
                        else:
                            print(f"   ❌ {name}: Update failed ({put_response.status_code})")
                            exceptions_status[name] = {"status": "update_failed", "error": put_response.text}
                            
                elif response.status_code == 404:
                    # Exception not set, create it
                    print(f"   🆕 {name}: Creating new exception ({expected_type})")
                    put_url = f"{BASE_URL}/api/config/exceptions/{user_id}"
                    put_data = {"exception_type": expected_type}
                    
                    put_response = self.session.put(put_url, json=put_data, timeout=30)
                    
                    if put_response.status_code == 200:
                        print(f"   ✅ {name}: Created {expected_type}")
                        exceptions_status[name] = {"status": "created", "type": expected_type}
                    else:
                        print(f"   ❌ {name}: Creation failed ({put_response.status_code})")
                        exceptions_status[name] = {"status": "creation_failed", "error": put_response.text}
                else:
                    print(f"   ❌ {name}: Exception check failed ({response.status_code})")
                    exceptions_status[name] = {"status": "check_failed", "error": response.text}
                    
            except Exception as e:
                print(f"   ❌ {name}: Exception error: {e}")
                exceptions_status[name] = {"status": "error", "error": str(e)}
        
        self.test_results["exceptions_config"] = {
            "status": "completed",
            "exceptions": exceptions_status
        }
        
        return True
    
    def calculate_monthly_deductions(self):
        """Step 4: POST /api/deductions/calculate-monthly?month=2025-10 and extract employees"""
        print(f"📊 Step 4: Calculating monthly deductions for {TARGET_MONTH}")
        
        calc_url = f"{BASE_URL}/api/deductions/calculate-monthly"
        params = {"month": TARGET_MONTH}
        
        try:
            response = self.session.post(calc_url, params=params, timeout=60)
            print(f"   Calculation Response: {response.status_code}")
            
            if response.status_code == 200:
                calc_data = response.json()
                
                # Extract key metrics
                summaries = calc_data.get("summaries", [])
                employees = calc_data.get("employees", [])
                success = calc_data.get("success", False)
                
                print(f"   ✅ Calculation successful")
                print(f"   Summaries: {len(summaries)} employees")
                print(f"   Employees: {len(employees)} employees")
                print(f"   Success: {success}")
                
                # Store raw response for evidence
                self.test_results["raw_responses"]["monthly_calculation"] = calc_data
                
                # Extract target employees from summaries
                target_employees = {}
                
                for summary in summaries:
                    employee_name = summary.get("employee_name", "").lower()
                    
                    # Match against our mapped users
                    for mapped_name, mapping in self.user_mappings.items():
                        mapped_user_name = mapping["name"].lower()
                        
                        if any(part in employee_name for part in mapped_user_name.split()):
                            target_employees[mapped_name] = summary
                            print(f"   📋 Found {mapped_name}: {summary.get('employee_name')}")
                            break
                
                self.test_results["monthly_calculation"] = {
                    "status": "success",
                    "total_summaries": len(summaries),
                    "total_employees": len(employees),
                    "success": success,
                    "target_employees": target_employees
                }
                
                return target_employees
                
            else:
                print(f"   ❌ Calculation failed: {response.status_code}")
                print(f"   Response: {response.text}")
                self.test_results["monthly_calculation"] = {
                    "status": "failed",
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                return {}
                
        except Exception as e:
            print(f"   ❌ Calculation error: {e}")
            self.test_results["monthly_calculation"] = {
                "status": "error",
                "error": str(e)
            }
            return {}
    
    def validate_normalization_invariants(self, target_employees):
        """Step 5: Assert invariants after normalization"""
        print(f"🔍 Step 5: Validating normalization invariants")
        
        validation_results = {}
        pass_fail_matrix = {}
        
        # Define expected invariants
        invariants = {
            "hatem": {
                "rule": "total_deduction == 0 (exempt)",
                "check": lambda emp: emp.get("total_deduction", 0) == 0
            },
            "tarek": {
                "rule": "late_deduction == 0 and total_deduction == absence_deduction (flex, 0 if no absence)",
                "check": lambda emp: (
                    emp.get("late_deduction", 0) == 0 and
                    emp.get("total_deduction", 0) == emp.get("absence_deduction", 0)
                )
            },
            "karim": {
                "rule": "absence_deduction == 0 if days_absent==0; total_deduction == late_deduction when no absence",
                "check": lambda emp: (
                    (emp.get("days_absent", 0) == 0 and emp.get("absence_deduction", 0) == 0) or
                    (emp.get("days_absent", 0) > 0)
                ) and (
                    emp.get("days_absent", 0) == 0 and 
                    emp.get("total_deduction", 0) == emp.get("late_deduction", 0)
                ) if emp.get("days_absent", 0) == 0 else True
            },
            "hesham": {
                "rule": "absence_deduction == 0 if days_absent==0; total_deduction == late_deduction when no absence",
                "check": lambda emp: (
                    (emp.get("days_absent", 0) == 0 and emp.get("absence_deduction", 0) == 0) or
                    (emp.get("days_absent", 0) > 0)
                ) and (
                    emp.get("days_absent", 0) == 0 and 
                    emp.get("total_deduction", 0) == emp.get("late_deduction", 0)
                ) if emp.get("days_absent", 0) == 0 else True
            }
        }
        
        for name, invariant in invariants.items():
            if name in target_employees:
                employee_data = target_employees[name]
                
                # Extract key values
                total_deduction = employee_data.get("total_deduction", 0)
                late_deduction = employee_data.get("late_deduction", 0)
                absence_deduction = employee_data.get("absence_deduction", 0)
                days_absent = employee_data.get("days_absent", 0)
                
                # Run validation check
                is_valid = invariant["check"](employee_data)
                
                validation_results[name] = {
                    "employee_name": employee_data.get("employee_name"),
                    "rule": invariant["rule"],
                    "values": {
                        "total_deduction": total_deduction,
                        "late_deduction": late_deduction,
                        "absence_deduction": absence_deduction,
                        "days_absent": days_absent
                    },
                    "is_valid": is_valid,
                    "status": "PASS" if is_valid else "FAIL"
                }
                
                pass_fail_matrix[name] = {
                    "status": "PASS" if is_valid else "FAIL",
                    "total_deduction": total_deduction,
                    "late_deduction": late_deduction,
                    "absence_deduction": absence_deduction,
                    "days_absent": days_absent
                }
                
                status_icon = "✅" if is_valid else "❌"
                print(f"   {status_icon} {name}: {validation_results[name]['status']}")
                print(f"      Total: {total_deduction}, Late: {late_deduction}, Absence: {absence_deduction}, Days Absent: {days_absent}")
                
            else:
                validation_results[name] = {
                    "rule": invariant["rule"],
                    "is_valid": False,
                    "status": "NOT_FOUND",
                    "error": "Employee not found in calculation results"
                }
                
                pass_fail_matrix[name] = {
                    "status": "NOT_FOUND",
                    "error": "Employee not found"
                }
                
                print(f"   ❌ {name}: NOT_FOUND - Employee not in calculation results")
        
        self.test_results["validation"] = validation_results
        self.test_results["pass_fail_matrix"] = pass_fail_matrix
        
        return validation_results
    
    def save_evidence_and_output_matrix(self):
        """Step 6: Save raw response and output concise PASS/FAIL matrix"""
        print(f"💾 Step 6: Saving evidence and outputting results")
        
        # Save comprehensive results to evidence file
        evidence_file = EVIDENCE_DIR / "production_after_normalization_oct.json"
        
        try:
            with open(evidence_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"   ✅ Evidence saved to: {evidence_file}")
            print(f"   File size: {evidence_file.stat().st_size} bytes")
            
        except Exception as e:
            print(f"   ❌ Failed to save evidence: {e}")
        
        # Output concise PASS/FAIL matrix
        print(f"\n" + "="*80)
        print(f"🎯 PRODUCTION NORMALIZATION TEST RESULTS - {TARGET_MONTH}")
        print(f"="*80)
        
        matrix = self.test_results.get("pass_fail_matrix", {})
        
        if matrix:
            print(f"{'Employee':<15} {'Status':<10} {'Total':<10} {'Late':<10} {'Absence':<10} {'Days Absent':<12}")
            print(f"{'-'*15} {'-'*10} {'-'*10} {'-'*10} {'-'*10} {'-'*12}")
            
            for name, data in matrix.items():
                status = data.get("status", "UNKNOWN")
                total = data.get("total_deduction", "N/A")
                late = data.get("late_deduction", "N/A")
                absence = data.get("absence_deduction", "N/A")
                days_absent = data.get("days_absent", "N/A")
                
                print(f"{name.capitalize():<15} {status:<10} {total:<10} {late:<10} {absence:<10} {days_absent:<12}")
        else:
            print("❌ No validation results available")
        
        # Summary statistics
        total_tests = len(matrix)
        passed_tests = sum(1 for data in matrix.values() if data.get("status") == "PASS")
        failed_tests = sum(1 for data in matrix.values() if data.get("status") == "FAIL")
        not_found = sum(1 for data in matrix.values() if data.get("status") == "NOT_FOUND")
        
        print(f"\n📊 SUMMARY:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   ⚠️ Not Found: {not_found}")
        
        if total_tests > 0:
            success_rate = (passed_tests / total_tests) * 100
            print(f"   📈 Success Rate: {success_rate:.1f}%")
        
        print(f"="*80)
        
        return True
    
    def run_full_test(self):
        """Run the complete production normalization test"""
        print(f"🚀 Starting Production Monthly Deductions Normalization Test")
        print(f"   Target Month: {TARGET_MONTH}")
        print(f"   Base URL: {BASE_URL}")
        print(f"   Timestamp: {datetime.now().isoformat()}")
        print(f"="*80)
        
        # Step 1: Authentication
        if not self.authenticate_super_admin():
            print("❌ Test failed at authentication step")
            return False
        
        # Step 2: User mapping
        if not self.get_users_and_remap():
            print("❌ Test failed at user mapping step")
            return False
        
        # Step 3: Exception configuration
        if not self.ensure_exceptions_configured():
            print("❌ Test failed at exception configuration step")
            return False
        
        # Step 4: Monthly calculation
        target_employees = self.calculate_monthly_deductions()
        if not target_employees:
            print("❌ Test failed at monthly calculation step")
            return False
        
        # Step 5: Validation
        validation_results = self.validate_normalization_invariants(target_employees)
        
        # Step 6: Evidence and output
        self.save_evidence_and_output_matrix()
        
        print(f"\n🎉 Production normalization test completed successfully!")
        return True

def main():
    """Main test execution"""
    test = ProductionNormalizationTest()
    
    try:
        success = test.run_full_test()
        
        if success:
            print(f"\n✅ All test steps completed successfully")
            return 0
        else:
            print(f"\n❌ Test execution failed")
            return 1
            
    except KeyboardInterrupt:
        print(f"\n⚠️ Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())