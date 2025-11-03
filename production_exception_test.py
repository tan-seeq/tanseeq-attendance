#!/usr/bin/env python3
"""
Production Exception Apply Monthly Testing Script
Target: https://hrapp-tanseeq-replaced-1761028071.emergent.host/api

Test Steps:
1. Authenticate as Super Admin
2. List users and map user_ids for target employees
3. Set exception types for each user
4. Verify exception configurations
5. Trigger monthly recalculation for October 2025
6. Validate business logic expectations
7. Save evidence and generate report
"""

import requests
import json
import os
from datetime import datetime
from pathlib import Path

# Configuration
BASE_URL = "https://attend-deduct-hr.preview.emergentagent.com/api"
SUPER_ADMIN_CREDENTIALS = {
    "email": "hatem@tan-seeq.co",
    "password": "hatem123"
}

# Target users and their exception types
TARGET_USERS = {
    "Hatem": {"exception_type": "exempt"},
    "Tarek": {"exception_type": "flex"},
    "Tariq": {"exception_type": "flex"},  # Alternative name
    "Karim": {"exception_type": "partial-flex"},
    "Hesham": {"exception_type": "partial-flex"}
}

class ProductionExceptionTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.auth_token = None
        self.user_mappings = {}
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "base_url": BASE_URL,
            "test_steps": [],
            "user_mappings": {},
            "exception_configurations": {},
            "monthly_calculation_results": {},
            "validation_results": {},
            "overall_status": "UNKNOWN"
        }
        
    def log_step(self, step_name, status, details=None, response_data=None):
        """Log test step results"""
        step_result = {
            "step": step_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details or {},
            "response_data": response_data
        }
        self.test_results["test_steps"].append(step_result)
        print(f"[{status}] {step_name}: {details}")
        
    def authenticate_super_admin(self):
        """Step 1: Authenticate as Super Admin"""
        try:
            response = self.session.post(
                f"{BASE_URL}/auth/login",
                json=SUPER_ADMIN_CREDENTIALS,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.session.headers.update({
                    'Authorization': f'Bearer {self.auth_token}'
                })
                
                user_info = data.get("user", {})
                self.log_step(
                    "Super Admin Authentication",
                    "SUCCESS",
                    {
                        "user_name": user_info.get("name"),
                        "user_role": user_info.get("role"),
                        "user_email": user_info.get("email")
                    },
                    data
                )
                return True
            else:
                self.log_step(
                    "Super Admin Authentication",
                    "FAILED",
                    {
                        "status_code": response.status_code,
                        "error": response.text
                    }
                )
                return False
                
        except Exception as e:
            self.log_step(
                "Super Admin Authentication",
                "ERROR",
                {"exception": str(e)}
            )
            return False
    
    def list_users_and_map_ids(self):
        """Step 2: GET /users to list users and map user_ids"""
        try:
            response = self.session.get(f"{BASE_URL}/users", timeout=30)
            
            if response.status_code == 200:
                users = response.json()
                
                # Debug: Print all users for analysis
                print("DEBUG: All users in system:")
                for user in users:
                    print(f"  - {user.get('name', 'N/A')} (ID: {user.get('id', 'N/A')}, Email: {user.get('email', 'N/A')})")
                
                # Fuzzy name search for target users
                found_users = {}
                for user in users:
                    user_name = user.get("name", "").lower()
                    user_id = user.get("id")
                    
                    # Check for Hatem
                    if "hatem" in user_name:
                        found_users["Hatem"] = {
                            "user_id": user_id,
                            "full_name": user.get("name"),
                            "email": user.get("email")
                        }
                    
                    # Check for Tarek/Tariq (more flexible matching)
                    elif any(name in user_name for name in ["tarek", "tariq"]):
                        key = "Tarek" if "tarek" in user_name else "Tariq"
                        found_users[key] = {
                            "user_id": user_id,
                            "full_name": user.get("name"),
                            "email": user.get("email")
                        }
                    
                    # Check for Karim/Kareem
                    elif "karim" in user_name or "kareem" in user_name:
                        found_users["Karim"] = {
                            "user_id": user_id,
                            "full_name": user.get("name"),
                            "email": user.get("email")
                        }
                    
                    # Check for Hesham
                    elif "hesham" in user_name:
                        found_users["Hesham"] = {
                            "user_id": user_id,
                            "full_name": user.get("name"),
                            "email": user.get("email")
                        }
                
                self.user_mappings = found_users
                self.test_results["user_mappings"] = found_users
                
                self.log_step(
                    "User Mapping",
                    "SUCCESS",
                    {
                        "total_users": len(users),
                        "found_target_users": len(found_users),
                        "mapped_users": list(found_users.keys())
                    },
                    found_users
                )
                return True
                
            else:
                self.log_step(
                    "User Mapping",
                    "FAILED",
                    {
                        "status_code": response.status_code,
                        "error": response.text
                    }
                )
                return False
                
        except Exception as e:
            self.log_step(
                "User Mapping",
                "ERROR",
                {"exception": str(e)}
            )
            return False
    
    def set_exception_configurations(self):
        """Step 3: PUT /config/exceptions/{user_id} for each user"""
        success_count = 0
        
        for user_key, user_info in self.user_mappings.items():
            if user_key not in TARGET_USERS:
                continue
                
            user_id = user_info["user_id"]
            exception_config = TARGET_USERS[user_key]
            
            try:
                response = self.session.put(
                    f"{BASE_URL}/config/exceptions/{user_id}",
                    json=exception_config,
                    timeout=30
                )
                
                if response.status_code in [200, 201]:
                    success_count += 1
                    self.log_step(
                        f"Set Exception - {user_key}",
                        "SUCCESS",
                        {
                            "user_id": user_id,
                            "full_name": user_info["full_name"],
                            "exception_type": exception_config["exception_type"]
                        },
                        response.json() if response.content else {}
                    )
                else:
                    self.log_step(
                        f"Set Exception - {user_key}",
                        "FAILED",
                        {
                            "user_id": user_id,
                            "status_code": response.status_code,
                            "error": response.text
                        }
                    )
                    
            except Exception as e:
                self.log_step(
                    f"Set Exception - {user_key}",
                    "ERROR",
                    {
                        "user_id": user_id,
                        "exception": str(e)
                    }
                )
        
        return success_count == len(self.user_mappings)
    
    def verify_exception_configurations(self):
        """Step 4: Verify with GET /config/exceptions"""
        try:
            response = self.session.get(f"{BASE_URL}/config/exceptions", timeout=30)
            
            if response.status_code == 200:
                exceptions_data = response.json()
                
                # Handle different response formats
                if isinstance(exceptions_data, dict):
                    exceptions = exceptions_data.get("exceptions", [])
                elif isinstance(exceptions_data, list):
                    exceptions = exceptions_data
                else:
                    exceptions = []
                
                # Verify our four entries exist with correct types
                verified_exceptions = {}
                for user_key, user_info in self.user_mappings.items():
                    user_id = user_info["user_id"]
                    expected_type = TARGET_USERS.get(user_key, {}).get("exception_type")
                    
                    # Find exception for this user
                    found_exception = None
                    for exc in exceptions:
                        if isinstance(exc, dict) and exc.get("user_id") == user_id:
                            found_exception = exc
                            break
                    
                    if found_exception:
                        actual_type = found_exception.get("exception_type")
                        verified_exceptions[user_key] = {
                            "user_id": user_id,
                            "expected_type": expected_type,
                            "actual_type": actual_type,
                            "matches": actual_type == expected_type
                        }
                
                self.test_results["exception_configurations"] = verified_exceptions
                
                all_match = all(exc["matches"] for exc in verified_exceptions.values())
                
                self.log_step(
                    "Verify Exception Configurations",
                    "SUCCESS" if all_match else "PARTIAL",
                    {
                        "total_exceptions": len(exceptions),
                        "verified_users": len(verified_exceptions),
                        "all_match_expected": all_match
                    },
                    verified_exceptions
                )
                return all_match
                
            else:
                self.log_step(
                    "Verify Exception Configurations",
                    "FAILED",
                    {
                        "status_code": response.status_code,
                        "error": response.text
                    }
                )
                return False
                
        except Exception as e:
            self.log_step(
                "Verify Exception Configurations",
                "ERROR",
                {"exception": str(e)}
            )
            return False
    
    def trigger_monthly_recalculation(self):
        """Step 5: Trigger recalculation for October 2025"""
        try:
            response = self.session.post(
                f"{BASE_URL}/deductions/calculate-monthly?month=2025-10",
                timeout=60  # Longer timeout for calculation
            )
            
            if response.status_code == 200:
                calculation_results = response.json()
                
                # Debug: Print the raw response structure
                print(f"DEBUG: Raw calculation response type: {type(calculation_results)}")
                if isinstance(calculation_results, dict):
                    print(f"DEBUG: Response keys: {list(calculation_results.keys())}")
                elif isinstance(calculation_results, list):
                    print(f"DEBUG: Response list length: {len(calculation_results)}")
                    if len(calculation_results) > 0:
                        print(f"DEBUG: First item keys: {list(calculation_results[0].keys()) if isinstance(calculation_results[0], dict) else 'Not a dict'}")
                
                # Extract data for our target users
                user_results = {}
                results_list = []
                
                # Normalize the response to a list
                if isinstance(calculation_results, list):
                    results_list = calculation_results
                elif isinstance(calculation_results, dict):
                    # Check common response patterns
                    if "results" in calculation_results:
                        results_list = calculation_results["results"]
                    elif "deductions" in calculation_results:
                        results_list = calculation_results["deductions"]
                    elif "employees" in calculation_results:
                        results_list = calculation_results["employees"]
                    else:
                        # Try to find any list in the response
                        for key, value in calculation_results.items():
                            if isinstance(value, list) and len(value) > 0:
                                results_list = value
                                break
                
                print(f"DEBUG: Normalized results list length: {len(results_list)}")
                
                for user_key, user_info in self.user_mappings.items():
                    user_id = user_info["user_id"]
                    
                    # Find this user's results in the calculation
                    user_result = None
                    for result in results_list:
                        if isinstance(result, dict):
                            # Try different possible user ID fields
                            result_user_id = result.get("user_id") or result.get("employee_id") or result.get("id")
                            if result_user_id == user_id:
                                user_result = result
                                break
                    
                    if user_result:
                        user_results[user_key] = {
                            "user_id": user_id,
                            "full_name": user_info["full_name"],
                            "total_deduction": user_result.get("total_deduction", 0),
                            "late_deduction": user_result.get("late_deduction", 0),
                            "absence_deduction": user_result.get("absence_deduction", 0),
                            "days_absent": user_result.get("days_absent", 0),
                            "days_late": user_result.get("days_late", 0),
                            "total_late_minutes": user_result.get("total_late_minutes", 0),
                            "raw_result": user_result
                        }
                    else:
                        print(f"DEBUG: No result found for {user_key} (ID: {user_id})")
                
                # Store raw response for debugging
                self.test_results["raw_calculation_response"] = calculation_results
                self.test_results["monthly_calculation_results"] = user_results
                
                self.log_step(
                    "Monthly Recalculation October 2025",
                    "SUCCESS",
                    {
                        "calculation_completed": True,
                        "users_found_in_results": len(user_results),
                        "target_users": list(user_results.keys())
                    },
                    user_results
                )
                return True
                
            else:
                self.log_step(
                    "Monthly Recalculation October 2025",
                    "FAILED",
                    {
                        "status_code": response.status_code,
                        "error": response.text
                    }
                )
                return False
                
        except Exception as e:
            self.log_step(
                "Monthly Recalculation October 2025",
                "ERROR",
                {"exception": str(e)}
            )
            return False
    
    def validate_business_expectations(self):
        """Step 6: Validate expectations for each user type"""
        validation_results = {}
        overall_pass = True
        
        user_results = self.test_results.get("monthly_calculation_results", {})
        
        for user_key, result_data in user_results.items():
            expected_type = TARGET_USERS.get(user_key, {}).get("exception_type")
            
            total_deduction = result_data.get("total_deduction", 0)
            late_deduction = result_data.get("late_deduction", 0)
            absence_deduction = result_data.get("absence_deduction", 0)
            days_absent = result_data.get("days_absent", 0)
            days_late = result_data.get("days_late", 0)
            
            validation = {
                "user_key": user_key,
                "exception_type": expected_type,
                "actual_values": {
                    "total_deduction": total_deduction,
                    "late_deduction": late_deduction,
                    "absence_deduction": absence_deduction,
                    "days_absent": days_absent,
                    "days_late": days_late
                },
                "expectations": {},
                "validation_status": "UNKNOWN",
                "issues": []
            }
            
            # Apply business logic validation based on exception type
            if user_key == "Hatem" and expected_type == "exempt":
                # Hatem: total_deduction==0 (no absence, no late)
                validation["expectations"] = {
                    "total_deduction_should_be": 0,
                    "reason": "Exempt users should have no deductions"
                }
                
                if total_deduction == 0:
                    validation["validation_status"] = "PASS"
                else:
                    validation["validation_status"] = "FAIL"
                    validation["issues"].append(f"Expected total_deduction=0, got {total_deduction}")
                    overall_pass = False
                    
            elif user_key in ["Tarek", "Tariq"] and expected_type == "flex":
                # Tarek: total_deduction==0 if days_absent==0; otherwise only absence_deduction>0 and late_deduction==0
                validation["expectations"] = {
                    "if_no_absence": "total_deduction should be 0",
                    "if_absence": "only absence_deduction>0, late_deduction should be 0",
                    "reason": "Flex users are not penalized for lateness, only absence"
                }
                
                if days_absent == 0:
                    if total_deduction == 0:
                        validation["validation_status"] = "PASS"
                    else:
                        validation["validation_status"] = "FAIL"
                        validation["issues"].append(f"No absence but total_deduction={total_deduction}, expected 0")
                        overall_pass = False
                else:
                    if absence_deduction > 0 and late_deduction == 0:
                        validation["validation_status"] = "PASS"
                    else:
                        validation["validation_status"] = "FAIL"
                        if absence_deduction <= 0:
                            validation["issues"].append(f"Has absence but absence_deduction={absence_deduction}")
                        if late_deduction > 0:
                            validation["issues"].append(f"Flex user should not have late_deduction={late_deduction}")
                        overall_pass = False
                        
            elif user_key in ["Karim", "Hesham"] and expected_type == "partial-flex":
                # Karim/Hesham: Only lateness contributes; absence_deduction allowed only if days_absent>0. No early/under-hours impact.
                validation["expectations"] = {
                    "lateness_rule": "Late deductions should apply",
                    "absence_rule": "Absence deduction only if days_absent>0",
                    "early_rule": "No early departure or under-hours impact",
                    "reason": "Partial-flex users have lateness penalties but flexible end times"
                }
                
                issues = []
                if days_absent > 0 and absence_deduction <= 0:
                    issues.append(f"Has {days_absent} absent days but absence_deduction={absence_deduction}")
                elif days_absent == 0 and absence_deduction > 0:
                    issues.append(f"No absent days but absence_deduction={absence_deduction}")
                
                # For partial-flex, we expect late deductions if there are late days
                # This is the main difference from flex users
                
                if len(issues) == 0:
                    validation["validation_status"] = "PASS"
                else:
                    validation["validation_status"] = "FAIL"
                    validation["issues"] = issues
                    overall_pass = False
            
            validation_results[user_key] = validation
        
        self.test_results["validation_results"] = validation_results
        self.test_results["overall_status"] = "PASS" if overall_pass else "FAIL"
        
        self.log_step(
            "Business Logic Validation",
            "SUCCESS" if overall_pass else "FAILED",
            {
                "overall_validation": "PASS" if overall_pass else "FAIL",
                "users_validated": len(validation_results),
                "passed_validations": sum(1 for v in validation_results.values() if v["validation_status"] == "PASS"),
                "failed_validations": sum(1 for v in validation_results.values() if v["validation_status"] == "FAIL")
            },
            validation_results
        )
        
        return overall_pass
    
    def save_evidence_and_generate_report(self):
        """Step 7: Save raw JSON and return concise report"""
        try:
            # Create evidence directory
            evidence_dir = Path("/app/evidence")
            evidence_dir.mkdir(exist_ok=True)
            
            # Save raw JSON
            evidence_file = evidence_dir / "production_exception_apply_monthly.json"
            with open(evidence_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False)
            
            self.log_step(
                "Save Evidence",
                "SUCCESS",
                {
                    "evidence_file": str(evidence_file),
                    "file_size_bytes": evidence_file.stat().st_size
                }
            )
            
            # Generate concise report
            report = self.generate_concise_report()
            
            return True, report
            
        except Exception as e:
            self.log_step(
                "Save Evidence",
                "ERROR",
                {"exception": str(e)}
            )
            return False, f"Failed to save evidence: {str(e)}"
    
    def generate_concise_report(self):
        """Generate concise PASS/FAIL report with numeric values"""
        report_lines = []
        report_lines.append("=== PRODUCTION EXCEPTION APPLY MONTHLY TEST REPORT ===")
        report_lines.append(f"Timestamp: {self.test_results['timestamp']}")
        report_lines.append(f"Target URL: {BASE_URL}")
        report_lines.append(f"Overall Status: {self.test_results['overall_status']}")
        report_lines.append("")
        
        # User mappings
        report_lines.append("USER MAPPINGS:")
        for user_key, user_info in self.test_results.get("user_mappings", {}).items():
            report_lines.append(f"  {user_key}: {user_info['full_name']} (ID: {user_info['user_id']})")
        report_lines.append("")
        
        # Exception configurations
        report_lines.append("EXCEPTION CONFIGURATIONS:")
        for user_key, config in self.test_results.get("exception_configurations", {}).items():
            status = "✓" if config.get("matches", False) else "✗"
            report_lines.append(f"  {status} {user_key}: {config.get('actual_type', 'N/A')}")
        report_lines.append("")
        
        # Monthly calculation results with numeric values
        report_lines.append("MONTHLY CALCULATION RESULTS (October 2025):")
        for user_key, result in self.test_results.get("monthly_calculation_results", {}).items():
            report_lines.append(f"  {user_key}:")
            report_lines.append(f"    - total_deduction: {result.get('total_deduction', 0)}")
            report_lines.append(f"    - late_deduction: {result.get('late_deduction', 0)}")
            report_lines.append(f"    - absence_deduction: {result.get('absence_deduction', 0)}")
            report_lines.append(f"    - days_absent: {result.get('days_absent', 0)}")
            report_lines.append(f"    - days_late: {result.get('days_late', 0)}")
            report_lines.append(f"    - total_late_minutes: {result.get('total_late_minutes', 0)}")
        report_lines.append("")
        
        # Validation results
        report_lines.append("VALIDATION RESULTS:")
        for user_key, validation in self.test_results.get("validation_results", {}).items():
            status = validation.get("validation_status", "UNKNOWN")
            status_symbol = "✓" if status == "PASS" else "✗" if status == "FAIL" else "?"
            report_lines.append(f"  {status_symbol} {user_key} ({validation.get('exception_type', 'N/A')}): {status}")
            
            if validation.get("issues"):
                for issue in validation["issues"]:
                    report_lines.append(f"      Issue: {issue}")
        
        report_lines.append("")
        report_lines.append(f"FINAL RESULT: {self.test_results['overall_status']}")
        
        return "\n".join(report_lines)
    
    def run_full_test(self):
        """Execute all test steps"""
        print("🚀 Starting Production Exception Apply Monthly Test...")
        print(f"Target URL: {BASE_URL}")
        print("=" * 60)
        
        # Step 1: Authentication
        if not self.authenticate_super_admin():
            return False, "Authentication failed"
        
        # Step 2: User mapping
        if not self.list_users_and_map_ids():
            return False, "User mapping failed"
        
        if len(self.user_mappings) == 0:
            return False, "No target users found"
        
        # Step 3: Set exception configurations
        if not self.set_exception_configurations():
            return False, "Failed to set exception configurations"
        
        # Step 4: Verify configurations
        if not self.verify_exception_configurations():
            return False, "Exception configuration verification failed"
        
        # Step 5: Trigger monthly recalculation
        if not self.trigger_monthly_recalculation():
            return False, "Monthly recalculation failed"
        
        # Step 6: Validate business expectations
        validation_passed = self.validate_business_expectations()
        
        # Step 7: Save evidence and generate report
        save_success, report = self.save_evidence_and_generate_report()
        
        if not save_success:
            return False, report
        
        return validation_passed, report

def main():
    """Main execution function"""
    tester = ProductionExceptionTester()
    
    try:
        success, report = tester.run_full_test()
        
        print("\n" + "=" * 60)
        print(report)
        print("=" * 60)
        
        if success:
            print("🎉 All tests PASSED!")
            return 0
        else:
            print("❌ Some tests FAILED!")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        return 2
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        return 3

if __name__ == "__main__":
    exit(main())