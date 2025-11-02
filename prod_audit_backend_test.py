#!/usr/bin/env python3
"""
Production Deep Audit for TANSEEQ HR System
URL: https://hrapp-tanseeq-replaced-1761028017.emergent.host/api
November Regression Check - READ-ONLY AUDIT

This script performs a comprehensive audit of the production system
focusing on deductions calculation for October and November 2025.
"""

import requests
import json
import time
from datetime import datetime
from pathlib import Path

class ProductionAudit:
    def __init__(self):
        self.base_url = "https://hrapp-tanseeq-replaced-1761028017.emergent.host/api"
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.auth_token = None
        self.user_mapping = {}
        self.audit_results = {
            "audit_timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "health_checks": {},
            "authentication": {},
            "users_mapping": {},
            "october_calculations": {},
            "november_calculations": {},
            "summary": {},
            "issues_found": []
        }
        
    def log_result(self, category, key, result):
        """Log audit result"""
        if category not in self.audit_results:
            self.audit_results[category] = {}
        self.audit_results[category][key] = result
        print(f"✅ {category}.{key}: {result.get('status', 'COMPLETED')}")
        
    def log_issue(self, severity, message, details=None):
        """Log audit issue"""
        issue = {
            "severity": severity,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        self.audit_results["issues_found"].append(issue)
        print(f"🚨 {severity}: {message}")
        
    def test_health_endpoints(self):
        """Step 1: Health checks - GET /healthz and /readyz"""
        print("\n=== STEP 1: HEALTH CHECKS ===")
        
        # Test /healthz
        try:
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/healthz", timeout=10)
            latency = (time.time() - start_time) * 1000
            
            self.log_result("health_checks", "healthz", {
                "status": "PASS" if response.status_code == 200 else "FAIL",
                "status_code": response.status_code,
                "latency_ms": round(latency, 2),
                "response": response.json() if response.status_code == 200 else response.text
            })
            
            if response.status_code != 200:
                self.log_issue("CRITICAL", f"/healthz failed with status {response.status_code}")
                
        except Exception as e:
            self.log_result("health_checks", "healthz", {
                "status": "ERROR",
                "error": str(e)
            })
            self.log_issue("CRITICAL", f"/healthz endpoint error: {str(e)}")
            
        # Test /readyz
        try:
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/readyz", timeout=10)
            latency = (time.time() - start_time) * 1000
            
            self.log_result("health_checks", "readyz", {
                "status": "PASS" if response.status_code == 200 else "FAIL",
                "status_code": response.status_code,
                "latency_ms": round(latency, 2),
                "response": response.json() if response.status_code == 200 else response.text
            })
            
            if response.status_code != 200:
                self.log_issue("CRITICAL", f"/readyz failed with status {response.status_code}")
                
        except Exception as e:
            self.log_result("health_checks", "readyz", {
                "status": "ERROR",
                "error": str(e)
            })
            self.log_issue("CRITICAL", f"/readyz endpoint error: {str(e)}")
            
    def authenticate(self):
        """Step 2: Authentication - POST /auth/login"""
        print("\n=== STEP 2: AUTHENTICATION ===")
        
        # Primary credentials
        credentials = [
            {"email": "admin@tanseeq.com", "password": "ADMIN"},
            {"email": "hatem@tan-seeq.co", "password": "hatem123"}
        ]
        
        for cred in credentials:
            try:
                response = self.session.post(
                    f"{self.base_url}/auth/login",
                    json=cred,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.auth_token = data.get("access_token")
                    self.session.headers.update({
                        'Authorization': f'Bearer {self.auth_token}'
                    })
                    
                    self.log_result("authentication", "login", {
                        "status": "SUCCESS",
                        "credentials": cred["email"],
                        "user_role": data.get("user", {}).get("role"),
                        "user_name": data.get("user", {}).get("name")
                    })
                    return True
                    
                else:
                    self.log_issue("HIGH", f"Authentication failed for {cred['email']}: {response.status_code}")
                    
            except Exception as e:
                self.log_issue("HIGH", f"Authentication error for {cred['email']}: {str(e)}")
                
        self.log_issue("CRITICAL", "All authentication attempts failed")
        return False
        
    def get_users_mapping(self):
        """Step 3: Users - GET /users and fuzzy-map target users"""
        print("\n=== STEP 3: USERS MAPPING ===")
        
        if not self.auth_token:
            self.log_issue("CRITICAL", "Cannot get users - no authentication token")
            return False
            
        try:
            response = self.session.get(f"{self.base_url}/users", timeout=15)
            
            if response.status_code != 200:
                self.log_issue("CRITICAL", f"Users endpoint failed: {response.status_code}")
                return False
                
            users = response.json()
            
            # Target users for fuzzy mapping
            target_names = {
                "hatem": ["hatem", "حاتم"],
                "tarek": ["tarek", "tariq", "طارق", "alwazan", "wazzan"],
                "karim": ["karim", "كريم"],
                "hesham": ["hesham", "هشام"]
            }
            
            for user in users:
                user_name = user.get("name", "").lower()
                user_email = user.get("email", "").lower()
                
                for key, variations in target_names.items():
                    if any(var in user_name or var in user_email for var in variations):
                        self.user_mapping[key] = {
                            "user_id": user.get("id"),
                            "name": user.get("name"),
                            "email": user.get("email"),
                            "role": user.get("role")
                        }
                        break
                        
            self.log_result("users_mapping", "mapping_results", {
                "total_users": len(users),
                "mapped_users": len(self.user_mapping),
                "mapping": self.user_mapping
            })
            
            # Check if we found all target users
            missing_users = set(target_names.keys()) - set(self.user_mapping.keys())
            if missing_users:
                self.log_issue("MEDIUM", f"Could not map users: {list(missing_users)}")
                
            return True
            
        except Exception as e:
            self.log_issue("CRITICAL", f"Users mapping error: {str(e)}")
            return False
            
    def validate_user_deductions(self, user_key, user_data, month_data, month):
        """Validate deductions per user type with business rules"""
        
        # Find user in summaries array by user_id
        user_id = user_data.get("user_id")
        user_calc = None
        
        summaries = month_data.get("summaries", [])
        for summary in summaries:
            if summary.get("employee_id") == user_id:
                user_calc = summary
                break
                
        if not user_calc:
            return {
                "status": "FAIL",
                "reason": "User not found in calculation results"
            }
            
        # Extract key metrics
        total_deduction = user_calc.get("total_deduction", 0)
        late_deduction = user_calc.get("late_deduction", 0)
        absence_deduction = user_calc.get("absence_deduction", 0)
        days_absent = user_calc.get("absence_count", 0)
        total_late_minutes = user_calc.get("total_late_minutes", 0)
        
        issues = []
        
        # Business rule validation based on user type
        if user_key == "hatem":  # Exempt user
            if total_deduction != 0:
                issues.append(f"Hatem (exempt): total_deduction should be 0, got {total_deduction}")
                
        elif user_key == "tarek":  # Flex user
            if late_deduction != 0:
                issues.append(f"Tarek (flex): late_deduction should be 0, got {late_deduction}")
            if days_absent == 0 and total_deduction != absence_deduction:
                issues.append(f"Tarek (flex): when no absence, total_deduction should equal absence_deduction")
                
        elif user_key in ["karim", "hesham"]:  # Partial-flex users
            if days_absent == 0 and absence_deduction != 0:
                issues.append(f"{user_key} (partial-flex): when days_absent=0, absence_deduction should be 0")
            if days_absent == 0 and total_deduction != late_deduction:
                issues.append(f"{user_key} (partial-flex): when no absence, total_deduction should equal late_deduction only")
                
        # Check daily records consistency
        daily_records = user_calc.get("daily_records", [])
        for record in daily_records:
            rule_applied = record.get("rule_applied", "")
            check_in = record.get("check_in")
            check_out = record.get("check_out")
            
            # Check for non-numeric working hours
            working_hours = record.get("working_hours")
            if working_hours and isinstance(working_hours, str) and ":" in working_hours:
                issues.append(f"Working hours in HH:MM format detected: {working_hours}")
                
        return {
            "status": "PASS" if not issues else "FAIL",
            "issues": issues,
            "metrics": {
                "total_deduction": total_deduction,
                "late_deduction": late_deduction,
                "absence_deduction": absence_deduction,
                "days_absent": days_absent,
                "total_late_minutes": total_late_minutes
            }
        }
        
    def calculate_monthly_deductions(self, month):
        """Step 4 & 5: Monthly deductions calculation"""
        print(f"\n=== MONTHLY CALCULATION: {month} ===")
        
        if not self.auth_token:
            self.log_issue("CRITICAL", f"Cannot calculate {month} - no authentication token")
            return False
            
        try:
            response = self.session.post(
                f"{self.base_url}/deductions/calculate-monthly?month={month}",
                timeout=30
            )
            
            if response.status_code != 200:
                self.log_issue("CRITICAL", f"Monthly calculation {month} failed: {response.status_code}")
                self.log_result(f"{month.replace('-', '_')}_calculations", "api_call", {
                    "status": "FAIL",
                    "status_code": response.status_code,
                    "response": response.text[:500]
                })
                return False
                
            calc_data = response.json()
            
            # Process results for each mapped user
            month_results = {}
            for user_key, user_info in self.user_mapping.items():
                validation = self.validate_user_deductions(user_key, user_info, calc_data, month)
                month_results[user_key] = validation
                
            self.log_result(f"{month.replace('-', '_')}_calculations", "results", {
                "status": "COMPLETED",
                "raw_data": calc_data,
                "validations": month_results
            })
            
            return True
            
        except Exception as e:
            self.log_issue("CRITICAL", f"Monthly calculation {month} error: {str(e)}")
            return False
            
    def generate_summary(self):
        """Generate concise PASS/FAIL summary per employee per month"""
        print("\n=== GENERATING SUMMARY ===")
        
        summary = {
            "overall_status": "PASS",
            "employee_results": {}
        }
        
        months = ["2025-10", "2025-11"]
        
        for user_key in self.user_mapping.keys():
            summary["employee_results"][user_key] = {}
            
            for month in months:
                month_key = f"{month.replace('-', '_')}_calculations"
                
                if month_key in self.audit_results and "results" in self.audit_results[month_key]:
                    validations = self.audit_results[month_key]["results"].get("validations", {})
                    
                    if user_key in validations:
                        validation = validations[user_key]
                        summary["employee_results"][user_key][month] = {
                            "status": validation["status"],
                            "metrics": validation.get("metrics", {}),
                            "issues": validation.get("issues", [])
                        }
                        
                        if validation["status"] == "FAIL":
                            summary["overall_status"] = "FAIL"
                    else:
                        summary["employee_results"][user_key][month] = {
                            "status": "NOT_FOUND",
                            "metrics": {},
                            "issues": ["User not found in calculation results"]
                        }
                        summary["overall_status"] = "FAIL"
                else:
                    summary["employee_results"][user_key][month] = {
                        "status": "NO_DATA",
                        "metrics": {},
                        "issues": ["Monthly calculation data not available"]
                    }
                    summary["overall_status"] = "FAIL"
                    
        self.audit_results["summary"] = summary
        
        # Print concise summary
        print("\n" + "="*60)
        print("PRODUCTION AUDIT SUMMARY")
        print("="*60)
        
        for user_key, user_data in summary["employee_results"].items():
            user_info = self.user_mapping.get(user_key, {})
            print(f"\n👤 {user_info.get('name', user_key.upper())} ({user_key}):")
            
            for month in months:
                if month in user_data:
                    result = user_data[month]
                    status_icon = "✅" if result["status"] == "PASS" else "❌"
                    metrics = result.get("metrics", {})
                    
                    print(f"  {status_icon} {month}: {result['status']}")
                    if metrics:
                        print(f"    📊 Deductions: {metrics.get('total_deduction', 'N/A')}")
                        print(f"    ⏰ Late: {metrics.get('late_deduction', 'N/A')}")
                        print(f"    🏠 Absence: {metrics.get('absence_deduction', 'N/A')}")
                        print(f"    📅 Days Absent: {metrics.get('days_absent', 'N/A')}")
                        print(f"    ⏱️ Late Minutes: {metrics.get('total_late_minutes', 'N/A')}")
                        
                    if result.get("issues"):
                        for issue in result["issues"]:
                            print(f"    ⚠️ {issue}")
                            
        print(f"\n🎯 OVERALL STATUS: {summary['overall_status']}")
        print(f"🔍 Total Issues Found: {len(self.audit_results['issues_found'])}")
        
    def save_evidence(self):
        """Save complete evidence to JSON file"""
        print("\n=== SAVING EVIDENCE ===")
        
        evidence_dir = Path("/app/evidence")
        evidence_dir.mkdir(exist_ok=True)
        
        evidence_file = evidence_dir / "prod_1761028017_audit_oct_nov.json"
        
        try:
            with open(evidence_file, 'w', encoding='utf-8') as f:
                json.dump(self.audit_results, f, indent=2, ensure_ascii=False, default=str)
                
            print(f"✅ Evidence saved to: {evidence_file}")
            print(f"📊 File size: {evidence_file.stat().st_size} bytes")
            
        except Exception as e:
            self.log_issue("HIGH", f"Failed to save evidence: {str(e)}")
            
    def run_audit(self):
        """Run complete production audit"""
        print("🔍 STARTING PRODUCTION DEEP AUDIT")
        print(f"🌐 Target URL: {self.base_url}")
        print(f"📅 Audit Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("⚠️ READ-ONLY AUDIT - NO MODIFICATIONS ALLOWED")
        
        # Step 1: Health checks
        self.test_health_endpoints()
        
        # Step 2: Authentication
        if not self.authenticate():
            print("❌ AUDIT FAILED: Authentication required for further testing")
            self.save_evidence()
            return False
            
        # Step 3: Users mapping
        if not self.get_users_mapping():
            print("❌ AUDIT FAILED: User mapping required for deductions validation")
            self.save_evidence()
            return False
            
        # Step 4: October calculations
        self.calculate_monthly_deductions("2025-10")
        
        # Step 5: November calculations (regression check)
        self.calculate_monthly_deductions("2025-11")
        
        # Generate summary
        self.generate_summary()
        
        # Save evidence
        self.save_evidence()
        
        print("\n🎉 PRODUCTION AUDIT COMPLETED")
        return True

def main():
    """Main execution function"""
    audit = ProductionAudit()
    
    try:
        success = audit.run_audit()
        exit_code = 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n⚠️ Audit interrupted by user")
        audit.save_evidence()
        exit_code = 2
        
    except Exception as e:
        print(f"\n💥 Audit failed with error: {str(e)}")
        audit.log_issue("CRITICAL", f"Audit execution error: {str(e)}")
        audit.save_evidence()
        exit_code = 3
        
    return exit_code

if __name__ == "__main__":
    exit(main())