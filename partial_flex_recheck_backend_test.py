#!/usr/bin/env python3
"""
Partial-Flex Behavior Production Check for Hesham User
Testing specific partial-flex exception behavior as requested in review
"""

import requests
import json
import os
from datetime import datetime

# Production Configuration
BASE_URL = "https://attend-deduct-hr.preview.emergentagent.com"
SUPER_ADMIN_CREDENTIALS = {
    "email": "admin@tanseeq.com",
    "password": "ADMIN"
}

class PartialFlexTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "base_url": BASE_URL,
            "test_type": "partial_flex_recheck_hesham",
            "results": {}
        }
        
    def authenticate_super_admin(self):
        """Step 1: Authenticate as Super Admin on production BASE_URL"""
        print("🔐 Step 1: Authenticating as Super Admin...")
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                json=SUPER_ADMIN_CREDENTIALS,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                user_info = data.get("user", {})
                print(f"✅ Authentication successful: {user_info.get('name')} ({user_info.get('role')})")
                
                self.test_results["results"]["authentication"] = {
                    "status": "success",
                    "user_name": user_info.get('name'),
                    "user_role": user_info.get('role'),
                    "user_email": user_info.get('email')
                }
                return True
                
            else:
                print(f"❌ Authentication failed: {response.status_code} - {response.text}")
                self.test_results["results"]["authentication"] = {
                    "status": "failed",
                    "error": f"{response.status_code} - {response.text}"
                }
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            self.test_results["results"]["authentication"] = {
                "status": "error",
                "error": str(e)
            }
            return False
    
    def find_hesham_user_id(self):
        """Find Hesham user_id from users list"""
        print("🔍 Step 2: Finding Hesham user_id...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/users", timeout=30)
            
            if response.status_code == 200:
                users = response.json()
                
                # Look for Hesham user (case-insensitive search)
                hesham_user = None
                for user in users:
                    if "hesham" in user.get("name", "").lower():
                        hesham_user = user
                        break
                
                if hesham_user:
                    user_id = hesham_user.get("id")
                    print(f"✅ Found Hesham user: {hesham_user.get('name')} (ID: {user_id})")
                    
                    self.test_results["results"]["user_discovery"] = {
                        "status": "success",
                        "hesham_user_id": user_id,
                        "hesham_name": hesham_user.get("name"),
                        "hesham_email": hesham_user.get("email")
                    }
                    return user_id
                else:
                    print("❌ Hesham user not found in users list")
                    self.test_results["results"]["user_discovery"] = {
                        "status": "failed",
                        "error": "Hesham user not found",
                        "total_users": len(users)
                    }
                    return None
                    
            else:
                print(f"❌ Failed to get users: {response.status_code}")
                self.test_results["results"]["user_discovery"] = {
                    "status": "failed",
                    "error": f"API error: {response.status_code}"
                }
                return None
                
        except Exception as e:
            print(f"❌ User discovery error: {str(e)}")
            self.test_results["results"]["user_discovery"] = {
                "status": "error",
                "error": str(e)
            }
            return None
    
    def set_partial_flex_exception(self, user_id):
        """Step 3: Set exception partial-flex for Hesham user"""
        print(f"⚙️ Step 3: Setting partial-flex exception for user {user_id}...")
        
        try:
            response = self.session.put(
                f"{self.base_url}/api/config/exceptions/{user_id}",
                json={"exception_type": "partial-flex"},
                timeout=30
            )
            
            if response.status_code == 200:
                print("✅ Partial-flex exception set successfully")
                self.test_results["results"]["exception_config"] = {
                    "status": "success",
                    "exception_type": "partial-flex",
                    "user_id": user_id
                }
                return True
            else:
                print(f"❌ Failed to set exception: {response.status_code} - {response.text}")
                self.test_results["results"]["exception_config"] = {
                    "status": "failed",
                    "error": f"{response.status_code} - {response.text}"
                }
                return False
                
        except Exception as e:
            print(f"❌ Exception config error: {str(e)}")
            self.test_results["results"]["exception_config"] = {
                "status": "error",
                "error": str(e)
            }
            return False
    
    def calculate_monthly_deductions(self):
        """Step 4: Calculate monthly deductions for October 2025 and extract Hesham summary"""
        print("📊 Step 4: Calculating monthly deductions for October 2025...")
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/deductions/calculate-monthly?month=2025-10",
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract Hesham summary
                hesham_summary = None
                summaries = data.get("summaries", [])
                
                for summary in summaries:
                    if "hesham" in summary.get("employee_name", "").lower():
                        hesham_summary = summary
                        break
                
                if hesham_summary:
                    print(f"✅ Found Hesham summary:")
                    print(f"   Employee: {hesham_summary.get('employee_name')}")
                    print(f"   Days Absent: {hesham_summary.get('days_absent', 'N/A')}")
                    print(f"   Absence Deduction: {hesham_summary.get('absence_deduction', 'N/A')} AED")
                    print(f"   Total Deduction: {hesham_summary.get('total_deduction', 'N/A')} AED")
                    
                    self.test_results["results"]["monthly_calculation"] = {
                        "status": "success",
                        "hesham_summary": hesham_summary,
                        "total_employees": len(summaries),
                        "api_response_size": len(str(data))
                    }
                    
                    return hesham_summary
                else:
                    print("❌ Hesham not found in monthly calculation results")
                    self.test_results["results"]["monthly_calculation"] = {
                        "status": "failed",
                        "error": "Hesham not found in results",
                        "total_employees": len(summaries),
                        "available_employees": [s.get("employee_name") for s in summaries[:5]]
                    }
                    return None
                    
            else:
                print(f"❌ Monthly calculation failed: {response.status_code} - {response.text}")
                self.test_results["results"]["monthly_calculation"] = {
                    "status": "failed",
                    "error": f"{response.status_code} - {response.text}"
                }
                return None
                
        except Exception as e:
            print(f"❌ Monthly calculation error: {str(e)}")
            self.test_results["results"]["monthly_calculation"] = {
                "status": "error",
                "error": str(e)
            }
            return None
    
    def validate_partial_flex_behavior(self, hesham_summary):
        """Step 5: Validate partial-flex behavior rules"""
        print("🔍 Step 5: Validating partial-flex behavior...")
        
        validation_results = {
            "days_absent_check": False,
            "absence_deduction_check": False,
            "daily_records_check": False,
            "rule_applied_check": False
        }
        
        try:
            days_absent = hesham_summary.get("days_absent", 0)
            absence_deduction = hesham_summary.get("absence_deduction", 0)
            daily_records = hesham_summary.get("daily_records", [])
            
            # Validation 1: days_absent == 0 -> absence_deduction must be 0
            if days_absent == 0:
                validation_results["days_absent_check"] = True
                print(f"✅ Days absent check: {days_absent} (correct)")
                
                if absence_deduction == 0:
                    validation_results["absence_deduction_check"] = True
                    print(f"✅ Absence deduction check: {absence_deduction} AED (correct)")
                else:
                    print(f"❌ Absence deduction check: {absence_deduction} AED (should be 0)")
            else:
                print(f"❌ Days absent check: {days_absent} (should be 0 for partial-flex)")
            
            # Validation 2: Check daily_records for rule_applied indicating half/full day
            rule_applied_found = False
            for record in daily_records:
                rule_applied = record.get("rule_applied")
                if rule_applied and ("half" in str(rule_applied).lower() or "full" in str(rule_applied).lower()):
                    rule_applied_found = True
                    print(f"⚠️ Found rule_applied indicating half/full day: {rule_applied}")
                    break
            
            if not rule_applied_found:
                validation_results["rule_applied_check"] = True
                print("✅ No half/full day rule_applied found (correct for partial-flex)")
            
            validation_results["daily_records_check"] = len(daily_records) > 0
            print(f"📊 Daily records count: {len(daily_records)}")
            
            self.test_results["results"]["validation"] = {
                "status": "completed",
                "validation_results": validation_results,
                "days_absent": days_absent,
                "absence_deduction": absence_deduction,
                "daily_records_count": len(daily_records),
                "rule_applied_found": rule_applied_found
            }
            
            return validation_results
            
        except Exception as e:
            print(f"❌ Validation error: {str(e)}")
            self.test_results["results"]["validation"] = {
                "status": "error",
                "error": str(e)
            }
            return validation_results
    
    def save_evidence(self):
        """Step 6: Save JSON evidence to /app/evidence/partial_flex_recheck_hesham.json"""
        print("💾 Step 6: Saving evidence...")
        
        try:
            # Create evidence directory if it doesn't exist
            evidence_dir = "/app/evidence"
            os.makedirs(evidence_dir, exist_ok=True)
            
            # Save comprehensive test results
            evidence_file = f"{evidence_dir}/partial_flex_recheck_hesham.json"
            with open(evidence_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Evidence saved to {evidence_file}")
            
            # Calculate file size
            file_size = os.path.getsize(evidence_file)
            print(f"📁 Evidence file size: {file_size} bytes")
            
            return evidence_file
            
        except Exception as e:
            print(f"❌ Failed to save evidence: {str(e)}")
            return None
    
    def output_concise_results(self):
        """Output concise numeric results"""
        print("\n" + "="*60)
        print("📊 CONCISE NUMERIC RESULTS")
        print("="*60)
        
        # Authentication
        auth_status = self.test_results["results"].get("authentication", {}).get("status")
        print(f"Authentication: {'✅ SUCCESS' if auth_status == 'success' else '❌ FAILED'}")
        
        # User Discovery
        user_discovery = self.test_results["results"].get("user_discovery", {})
        hesham_id = user_discovery.get("hesham_user_id", "NOT_FOUND")
        print(f"Hesham User ID: {hesham_id}")
        
        # Exception Config
        exception_status = self.test_results["results"].get("exception_config", {}).get("status")
        print(f"Partial-Flex Config: {'✅ SET' if exception_status == 'success' else '❌ FAILED'}")
        
        # Monthly Calculation
        monthly_calc = self.test_results["results"].get("monthly_calculation", {})
        hesham_summary = monthly_calc.get("hesham_summary", {})
        
        if hesham_summary:
            days_absent = hesham_summary.get("days_absent", "N/A")
            absence_deduction = hesham_summary.get("absence_deduction", "N/A")
            total_deduction = hesham_summary.get("total_deduction", "N/A")
            
            print(f"Days Absent: {days_absent}")
            print(f"Absence Deduction: {absence_deduction} AED")
            print(f"Total Deduction: {total_deduction} AED")
            
            # Validation Results
            validation = self.test_results["results"].get("validation", {})
            validation_results = validation.get("validation_results", {})
            
            days_absent_ok = validation_results.get("days_absent_check", False)
            absence_deduction_ok = validation_results.get("absence_deduction_check", False)
            rule_applied_ok = validation_results.get("rule_applied_check", False)
            
            print(f"Days Absent == 0: {'✅ PASS' if days_absent_ok else '❌ FAIL'}")
            print(f"Absence Deduction == 0: {'✅ PASS' if absence_deduction_ok else '❌ FAIL'}")
            print(f"No Half/Full Day Rules: {'✅ PASS' if rule_applied_ok else '❌ FAIL'}")
            
            # Overall validation
            all_checks_pass = days_absent_ok and absence_deduction_ok and rule_applied_ok
            print(f"\n🎯 OVERALL VALIDATION: {'✅ PASS' if all_checks_pass else '❌ FAIL'}")
            
        else:
            print("❌ No Hesham summary data available")
        
        print("="*60)
    
    def run_complete_test(self):
        """Run the complete partial-flex behavior test"""
        print("🚀 Starting Partial-Flex Behavior Production Check for Hesham User")
        print(f"🌐 Base URL: {self.base_url}")
        print("="*80)
        
        # Step 1: Authenticate
        if not self.authenticate_super_admin():
            print("❌ Test aborted: Authentication failed")
            return False
        
        # Step 2: Find Hesham user
        hesham_user_id = self.find_hesham_user_id()
        if not hesham_user_id:
            print("❌ Test aborted: Hesham user not found")
            return False
        
        # Step 3: Set partial-flex exception
        if not self.set_partial_flex_exception(hesham_user_id):
            print("❌ Test aborted: Failed to set partial-flex exception")
            return False
        
        # Step 4: Calculate monthly deductions
        hesham_summary = self.calculate_monthly_deductions()
        if not hesham_summary:
            print("❌ Test aborted: Failed to get Hesham summary")
            return False
        
        # Step 5: Validate behavior
        validation_results = self.validate_partial_flex_behavior(hesham_summary)
        
        # Step 6: Save evidence
        evidence_file = self.save_evidence()
        
        # Output results
        self.output_concise_results()
        
        print(f"\n📁 Evidence saved to: {evidence_file}")
        print("🏁 Partial-Flex Behavior Test Completed")
        
        return True

def main():
    """Main test execution"""
    tester = PartialFlexTester()
    success = tester.run_complete_test()
    
    if success:
        print("\n✅ Test execution completed successfully")
        return 0
    else:
        print("\n❌ Test execution failed")
        return 1

if __name__ == "__main__":
    exit(main())