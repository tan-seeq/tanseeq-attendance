#!/usr/bin/env python3
"""
Exception Application and Monthly Recalculation Test for October 2025
Testing specific workflow from review request:
1. Super Admin authentication
2. Find user IDs for Hatem, Tarek/Tariq, Karim, Hesham
3. Apply exceptions (exempt, flex, partial-flex)
4. Verify exceptions list
5. Monthly recalculation for October 2025
6. Validate deduction expectations
"""

import requests
import json
import os
from datetime import datetime
from pathlib import Path

# Configuration
BASE_URL = "https://attendance-pro-43.preview.emergentagent.com/api"
EVIDENCE_DIR = Path("/app/evidence")
EVIDENCE_DIR.mkdir(exist_ok=True)

class ExceptionTestRunner:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.token = None
        self.test_results = {
            "test_timestamp": datetime.now().isoformat(),
            "base_url": BASE_URL,
            "steps": [],
            "user_mappings": {},
            "exception_applications": {},
            "monthly_calculation_results": {},
            "validation_results": {},
            "summary": {}
        }

    def log_step(self, step_name, success, details, response_data=None):
        """Log test step results"""
        step_result = {
            "step": step_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        if response_data:
            step_result["response_data"] = response_data
        
        self.test_results["steps"].append(step_result)
        print(f"{'✅' if success else '❌'} {step_name}: {details}")

    def authenticate_super_admin(self):
        """Step 1: Authenticate as Super Admin"""
        try:
            auth_data = {
                "email": "hatem@tan-seeq.co",
                "password": "hatem123"
            }
            
            response = self.session.post(f"{BASE_URL}/auth/login", json=auth_data)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.session.headers.update({
                    'Authorization': f'Bearer {self.token}'
                })
                
                user_info = data.get("user", {})
                self.log_step(
                    "Super Admin Authentication",
                    True,
                    f"Successfully authenticated as {user_info.get('name', 'Unknown')} ({user_info.get('role', 'Unknown')})",
                    {"user_role": user_info.get('role'), "user_name": user_info.get('name')}
                )
                return True
            else:
                self.log_step(
                    "Super Admin Authentication",
                    False,
                    f"Authentication failed: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_step(
                "Super Admin Authentication",
                False,
                f"Authentication error: {str(e)}"
            )
            return False

    def find_target_users(self):
        """Step 2: Find user IDs for target employees"""
        try:
            response = self.session.get(f"{BASE_URL}/users")
            
            if response.status_code != 200:
                self.log_step(
                    "User List Retrieval",
                    False,
                    f"Failed to get users: {response.status_code} - {response.text}"
                )
                return False
            
            users = response.json()
            if isinstance(users, dict) and 'users' in users:
                users = users['users']
            
            # Fuzzy mapping logic
            target_mappings = {
                "Hatem": {"keywords": ["hatem"], "exception_type": "exempt"},
                "Tarek/Tariq": {"keywords": ["tarek", "tariq", "wazzan", "alwazan"], "exception_type": "flex"},
                "Karim": {"keywords": ["karim", "kareem"], "exception_type": "partial-flex"},
                "Hesham": {"keywords": ["hesham", "hisham"], "exception_type": "partial-flex"}
            }
            
            found_users = {}
            
            for user in users:
                user_name = user.get('name', '').lower()
                user_email = user.get('email', '').lower()
                user_id = user.get('id')
                
                for target_name, config in target_mappings.items():
                    for keyword in config["keywords"]:
                        if keyword in user_name or keyword in user_email:
                            if target_name not in found_users:
                                found_users[target_name] = {
                                    "user_id": user_id,
                                    "name": user.get('name'),
                                    "email": user.get('email'),
                                    "exception_type": config["exception_type"]
                                }
                                break
            
            self.test_results["user_mappings"] = found_users
            
            self.log_step(
                "User Mapping",
                len(found_users) > 0,
                f"Found {len(found_users)} target users: {list(found_users.keys())}",
                found_users
            )
            
            return len(found_users) > 0
            
        except Exception as e:
            self.log_step(
                "User List Retrieval",
                False,
                f"Error retrieving users: {str(e)}"
            )
            return False

    def apply_exceptions(self):
        """Step 3: Apply exceptions for each found user"""
        if not self.test_results["user_mappings"]:
            self.log_step(
                "Exception Application",
                False,
                "No users found to apply exceptions"
            )
            return False
        
        success_count = 0
        total_count = len(self.test_results["user_mappings"])
        
        for target_name, user_info in self.test_results["user_mappings"].items():
            try:
                user_id = user_info["user_id"]
                exception_type = user_info["exception_type"]
                
                exception_data = {
                    "exception_type": exception_type
                }
                
                response = self.session.put(
                    f"{BASE_URL}/config/exceptions/{user_id}",
                    json=exception_data
                )
                
                if response.status_code in [200, 201]:
                    self.test_results["exception_applications"][target_name] = {
                        "user_id": user_id,
                        "exception_type": exception_type,
                        "success": True,
                        "response": response.json() if response.content else {"status": "success"}
                    }
                    success_count += 1
                    
                    self.log_step(
                        f"Exception Application - {target_name}",
                        True,
                        f"Applied {exception_type} exception for {user_info['name']} ({user_id})"
                    )
                else:
                    self.test_results["exception_applications"][target_name] = {
                        "user_id": user_id,
                        "exception_type": exception_type,
                        "success": False,
                        "error": f"{response.status_code} - {response.text}"
                    }
                    
                    self.log_step(
                        f"Exception Application - {target_name}",
                        False,
                        f"Failed to apply exception: {response.status_code} - {response.text}"
                    )
                    
            except Exception as e:
                self.test_results["exception_applications"][target_name] = {
                    "user_id": user_info.get("user_id"),
                    "exception_type": user_info.get("exception_type"),
                    "success": False,
                    "error": str(e)
                }
                
                self.log_step(
                    f"Exception Application - {target_name}",
                    False,
                    f"Error applying exception: {str(e)}"
                )
        
        return success_count == total_count

    def verify_exceptions_list(self):
        """Step 4: Verify exceptions are properly set"""
        try:
            response = self.session.get(f"{BASE_URL}/config/exceptions")
            
            if response.status_code != 200:
                self.log_step(
                    "Exception Verification",
                    False,
                    f"Failed to get exceptions list: {response.status_code} - {response.text}"
                )
                return False
            
            exceptions_data = response.json()
            if isinstance(exceptions_data, dict) and 'exceptions' in exceptions_data:
                exceptions_list = exceptions_data['exceptions']
            else:
                exceptions_list = exceptions_data
            
            # Verify our 4 target users are present
            found_exceptions = {}
            expected_users = self.test_results["user_mappings"]
            
            for exception in exceptions_list:
                user_id = exception.get('user_id')
                exception_type = exception.get('exception_type')
                
                # Find which target user this matches
                for target_name, user_info in expected_users.items():
                    if user_info["user_id"] == user_id:
                        found_exceptions[target_name] = {
                            "user_id": user_id,
                            "exception_type": exception_type,
                            "expected_type": user_info["exception_type"],
                            "matches": exception_type == user_info["exception_type"]
                        }
                        break
            
            all_found = len(found_exceptions) == len(expected_users)
            all_correct = all(exc["matches"] for exc in found_exceptions.values())
            
            self.test_results["validation_results"]["exceptions_verification"] = {
                "found_exceptions": found_exceptions,
                "all_found": all_found,
                "all_correct": all_correct,
                "total_exceptions": len(exceptions_list)
            }
            
            self.log_step(
                "Exception Verification",
                all_found and all_correct,
                f"Found {len(found_exceptions)}/{len(expected_users)} target users with correct exception types",
                found_exceptions
            )
            
            return all_found and all_correct
            
        except Exception as e:
            self.log_step(
                "Exception Verification",
                False,
                f"Error verifying exceptions: {str(e)}"
            )
            return False

    def run_monthly_recalculation(self):
        """Step 5: Run monthly recalculation for October 2025"""
        try:
            response = self.session.post(f"{BASE_URL}/deductions/calculate-monthly?month=2025-10")
            
            if response.status_code != 200:
                self.log_step(
                    "Monthly Recalculation",
                    False,
                    f"Failed to calculate monthly deductions: {response.status_code} - {response.text}"
                )
                return False
            
            calculation_results = response.json()
            self.test_results["monthly_calculation_results"] = calculation_results
            
            # Extract summaries for our target employees
            summaries = calculation_results.get('summaries', [])
            target_employee_results = {}
            
            for target_name, user_info in self.test_results["user_mappings"].items():
                user_id = user_info["user_id"]
                
                # Find this employee in the summaries
                for summary in summaries:
                    if summary.get('user_id') == user_id:
                        target_employee_results[target_name] = {
                            "user_id": user_id,
                            "name": user_info["name"],
                            "exception_type": user_info["exception_type"],
                            "total_deduction": summary.get('total_deduction', 0),
                            "late_deduction": summary.get('late_deduction', 0),
                            "absence_deduction": summary.get('absence_deduction', 0),
                            "days_absent": summary.get('days_absent', 0),
                            "days_late": summary.get('days_late', 0),
                            "total_late_minutes": summary.get('total_late_minutes', 0)
                        }
                        break
            
            self.test_results["validation_results"]["target_employee_results"] = target_employee_results
            
            self.log_step(
                "Monthly Recalculation",
                True,
                f"Successfully calculated deductions for October 2025. Found results for {len(target_employee_results)} target employees",
                {"total_employees": len(summaries), "target_employees_found": len(target_employee_results)}
            )
            
            return True
            
        except Exception as e:
            self.log_step(
                "Monthly Recalculation",
                False,
                f"Error running monthly recalculation: {str(e)}"
            )
            return False

    def validate_deduction_expectations(self):
        """Step 6: Validate deduction expectations based on exception types"""
        target_results = self.test_results["validation_results"].get("target_employee_results", {})
        
        if not target_results:
            self.log_step(
                "Deduction Validation",
                False,
                "No target employee results found for validation"
            )
            return False
        
        validation_results = {}
        all_passed = True
        
        for target_name, result in target_results.items():
            exception_type = result["exception_type"]
            total_deduction = result["total_deduction"]
            late_deduction = result["late_deduction"]
            absence_deduction = result["absence_deduction"]
            days_absent = result["days_absent"]
            
            validation = {
                "exception_type": exception_type,
                "total_deduction": total_deduction,
                "late_deduction": late_deduction,
                "absence_deduction": absence_deduction,
                "days_absent": days_absent,
                "expectations": {},
                "results": {}
            }
            
            if target_name == "Hatem":
                # Hatem -> exempt: total_deduction should be 0
                expected_total = 0
                validation["expectations"]["total_deduction"] = expected_total
                validation["results"]["total_deduction_pass"] = total_deduction == expected_total
                
            elif target_name == "Tarek/Tariq":
                # Tarek -> flex: total_deduction should be 0 if days_absent == 0, otherwise only absence_deduction > 0 and late_deduction == 0
                if days_absent == 0:
                    expected_total = 0
                    validation["expectations"]["total_deduction"] = expected_total
                    validation["results"]["total_deduction_pass"] = total_deduction == expected_total
                else:
                    validation["expectations"]["absence_only"] = "absence_deduction > 0 and late_deduction == 0"
                    validation["results"]["absence_only_pass"] = absence_deduction > 0 and late_deduction == 0
                
            elif target_name in ["Karim", "Hesham"]:
                # Karim/Hesham -> partial-flex: late_deduction may exist, but absence_deduction should not appear (only lateness)
                validation["expectations"]["lateness_only"] = "late_deduction may exist, absence_deduction should be 0"
                validation["results"]["lateness_only_pass"] = absence_deduction == 0
            
            # Check if all expectations passed for this employee
            employee_passed = all(validation["results"].values())
            validation["overall_pass"] = employee_passed
            
            if not employee_passed:
                all_passed = False
            
            validation_results[target_name] = validation
            
            self.log_step(
                f"Deduction Validation - {target_name}",
                employee_passed,
                f"Exception type: {exception_type}, Total deduction: {total_deduction}, Validation: {'PASS' if employee_passed else 'FAIL'}"
            )
        
        self.test_results["validation_results"]["deduction_expectations"] = validation_results
        
        return all_passed

    def save_evidence(self):
        """Save full JSON results to evidence file"""
        try:
            evidence_file = EVIDENCE_DIR / "exception_apply_and_monthly_oct.json"
            
            with open(evidence_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False, default=str)
            
            self.log_step(
                "Evidence Saving",
                True,
                f"Saved full test results to {evidence_file}"
            )
            
            return True
            
        except Exception as e:
            self.log_step(
                "Evidence Saving",
                False,
                f"Error saving evidence: {str(e)}"
            )
            return False

    def generate_summary_report(self):
        """Generate concise summary report"""
        target_results = self.test_results["validation_results"].get("target_employee_results", {})
        deduction_validations = self.test_results["validation_results"].get("deduction_expectations", {})
        
        summary = {
            "test_completion": datetime.now().isoformat(),
            "total_steps": len(self.test_results["steps"]),
            "successful_steps": len([s for s in self.test_results["steps"] if s["success"]]),
            "users_found": len(self.test_results["user_mappings"]),
            "exceptions_applied": len([e for e in self.test_results["exception_applications"].values() if e.get("success")]),
            "employee_results": {}
        }
        
        for target_name, result in target_results.items():
            validation = deduction_validations.get(target_name, {})
            
            summary["employee_results"][target_name] = {
                "user_id": result["user_id"],
                "name": result["name"],
                "exception_type": result["exception_type"],
                "total_deduction": result["total_deduction"],
                "late_deduction": result["late_deduction"],
                "absence_deduction": result["absence_deduction"],
                "days_absent": result["days_absent"],
                "days_late": result["days_late"],
                "total_late_minutes": result["total_late_minutes"],
                "validation_pass": validation.get("overall_pass", False)
            }
        
        self.test_results["summary"] = summary
        
        print("\n" + "="*80)
        print("EXCEPTION APPLICATION AND MONTHLY RECALCULATION TEST SUMMARY")
        print("="*80)
        print(f"Test Completion: {summary['test_completion']}")
        print(f"Steps Completed: {summary['successful_steps']}/{summary['total_steps']}")
        print(f"Users Found: {summary['users_found']}")
        print(f"Exceptions Applied: {summary['exceptions_applied']}")
        print("\nEmployee Results:")
        
        for target_name, emp_result in summary["employee_results"].items():
            status = "PASS" if emp_result["validation_pass"] else "FAIL"
            print(f"  {target_name} ({emp_result['exception_type']}): {status}")
            print(f"    Total Deduction: {emp_result['total_deduction']}")
            print(f"    Late Deduction: {emp_result['late_deduction']}")
            print(f"    Absence Deduction: {emp_result['absence_deduction']}")
            print(f"    Days Absent: {emp_result['days_absent']}")
            print(f"    Days Late: {emp_result['days_late']}")
            print(f"    Total Late Minutes: {emp_result['total_late_minutes']}")
            print()

    def run_full_test(self):
        """Run the complete test workflow"""
        print("Starting Exception Application and Monthly Recalculation Test...")
        print(f"Base URL: {BASE_URL}")
        print("="*80)
        
        # Step 1: Authenticate
        if not self.authenticate_super_admin():
            return False
        
        # Step 2: Find target users
        if not self.find_target_users():
            return False
        
        # Step 3: Apply exceptions
        if not self.apply_exceptions():
            print("⚠️ Some exceptions failed to apply, continuing with verification...")
        
        # Step 4: Verify exceptions
        if not self.verify_exceptions_list():
            print("⚠️ Exception verification failed, continuing with monthly calculation...")
        
        # Step 5: Run monthly recalculation
        if not self.run_monthly_recalculation():
            return False
        
        # Step 6: Validate expectations
        validation_passed = self.validate_deduction_expectations()
        
        # Step 7: Save evidence
        self.save_evidence()
        
        # Step 8: Generate summary
        self.generate_summary_report()
        
        return validation_passed

def main():
    """Main test execution"""
    test_runner = ExceptionTestRunner()
    
    try:
        success = test_runner.run_full_test()
        
        if success:
            print("✅ All tests completed successfully!")
            return 0
        else:
            print("❌ Some tests failed. Check the detailed results above.")
            return 1
            
    except Exception as e:
        print(f"💥 Test execution failed: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())