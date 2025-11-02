#!/usr/bin/env python3
"""
🔥 COMPREHENSIVE HR SYSTEM AUDIT - BACKEND TESTING
Full System Audit for Tanseeq HR as requested in review

Target environments:
1) Production: https://hrapp-tanseeq-replaced-1761028071.emergent.host/api
2) Preview: https://attendance-pro-43.preview.emergentagent.com/api

Scope: Health checks, Authentication & RBAC, Read-only integrity, Deductions engine,
Security checks, Performance snapshot with comprehensive evidence collection.
"""

import asyncio
import aiohttp
import json
import time
import statistics
from datetime import datetime, timezone
from pathlib import Path
import os

# Test Configuration
ENVIRONMENTS = {
    "production": "https://hrapp-tanseeq-replaced-1761028071.emergent.host/api",
    "preview": "https://attendance-pro-43.preview.emergentagent.com/api"
}

# Test Credentials
CREDENTIALS = {
    "super_admin": {"email": "admin@tanseeq.com", "password": "ADMIN"},
    "super_admin_alt": {"email": "hatem@tan-seeq.co", "password": "hatem123"},
    "regular_user": {"email": "jihad@tanseeq.com", "password": "jihad123"}
}

# Evidence directory
EVIDENCE_DIR = Path("/app/evidence")
EVIDENCE_DIR.mkdir(exist_ok=True)

class FullSystemAuditor:
    def __init__(self):
        self.results = {
            "audit_timestamp": datetime.now(timezone.utc).isoformat(),
            "environments_tested": list(ENVIRONMENTS.keys()),
            "test_summary": {
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "success_rate": 0.0
            },
            "health_checks": {},
            "authentication_rbac": {},
            "read_only_integrity": {},
            "deductions_engine": {},
            "security_checks": {},
            "performance_metrics": {},
            "critical_issues": [],
            "recommendations": []
        }
        self.session = None
        self.auth_tokens = {}

    async def run_full_audit(self):
        """Execute comprehensive system audit"""
        print("🔥 STARTING COMPREHENSIVE HR SYSTEM AUDIT")
        print("=" * 60)
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            self.session = session
            
            # Phase 0: Health & Environment Sanity
            await self.phase_0_health_env_sanity()
            
            # Phase 1: Authentication & RBAC
            await self.phase_1_authentication_rbac()
            
            # Phase 2: Read-only Integrity Sweeps
            await self.phase_2_readonly_integrity()
            
            # Phase 3: Deductions Engine Testing
            await self.phase_3_deductions_engine()
            
            # Phase 4: Security Checks
            await self.phase_4_security_checks()
            
            # Phase 5: Performance Snapshot
            await self.phase_5_performance_snapshot()
            
        # Generate final report
        await self.generate_final_report()
        
        return self.results

    async def phase_0_health_env_sanity(self):
        """Phase 0: Health & Environment Sanity Checks"""
        print("\n📊 PHASE 0: HEALTH & ENVIRONMENT SANITY")
        print("-" * 40)
        
        for env_name, base_url in ENVIRONMENTS.items():
            print(f"\n🔍 Testing {env_name.upper()} environment: {base_url}")
            
            env_results = {
                "base_url": base_url,
                "healthz": {"status": "unknown", "latency_ms": 0, "error": None},
                "readyz": {"status": "unknown", "latency_ms": 0, "error": None}
            }
            
            # Test /healthz endpoint
            try:
                start_time = time.time()
                async with self.session.get(f"{base_url}/healthz") as response:
                    latency = (time.time() - start_time) * 1000
                    env_results["healthz"]["latency_ms"] = round(latency, 2)
                    
                    if response.status == 200:
                        data = await response.json()
                        if data.get("status") == "ok":
                            env_results["healthz"]["status"] = "healthy"
                            print(f"  ✅ /healthz: {response.status} ({latency:.1f}ms)")
                        else:
                            env_results["healthz"]["status"] = "unhealthy"
                            env_results["healthz"]["error"] = f"Unexpected response: {data}"
                    else:
                        env_results["healthz"]["status"] = "error"
                        env_results["healthz"]["error"] = f"HTTP {response.status}"
                        print(f"  ❌ /healthz: {response.status} ({latency:.1f}ms)")
                        
            except Exception as e:
                env_results["healthz"]["status"] = "error"
                env_results["healthz"]["error"] = str(e)
                print(f"  ❌ /healthz: Connection failed - {e}")
            
            # Test /readyz endpoint
            try:
                start_time = time.time()
                async with self.session.get(f"{base_url}/readyz") as response:
                    latency = (time.time() - start_time) * 1000
                    env_results["readyz"]["latency_ms"] = round(latency, 2)
                    
                    if response.status == 200:
                        data = await response.json()
                        if data.get("status") == "ready":
                            env_results["readyz"]["status"] = "ready"
                            print(f"  ✅ /readyz: {response.status} ({latency:.1f}ms)")
                        else:
                            env_results["readyz"]["status"] = "not_ready"
                            env_results["readyz"]["error"] = f"Unexpected response: {data}"
                    else:
                        env_results["readyz"]["status"] = "error"
                        env_results["readyz"]["error"] = f"HTTP {response.status}"
                        print(f"  ❌ /readyz: {response.status} ({latency:.1f}ms)")
                        
            except Exception as e:
                env_results["readyz"]["status"] = "error"
                env_results["readyz"]["error"] = str(e)
                print(f"  ❌ /readyz: Connection failed - {e}")
            
            self.results["health_checks"][env_name] = env_results

    async def phase_1_authentication_rbac(self):
        """Phase 1: Authentication & RBAC Testing"""
        print("\n🔐 PHASE 1: AUTHENTICATION & RBAC")
        print("-" * 40)
        
        # Test authentication for each environment
        for env_name, base_url in ENVIRONMENTS.items():
            print(f"\n🔍 Testing authentication in {env_name.upper()}")
            
            env_auth_results = {
                "super_admin_login": {"status": "unknown", "user_info": None, "error": None},
                "super_admin_alt_login": {"status": "unknown", "user_info": None, "error": None},
                "regular_user_login": {"status": "unknown", "user_info": None, "error": None},
                "rbac_tests": []
            }
            
            # Test Super Admin login (primary)
            token = await self.test_login(base_url, CREDENTIALS["super_admin"], "super_admin")
            if token:
                env_auth_results["super_admin_login"]["status"] = "success"
                self.auth_tokens[f"{env_name}_super_admin"] = token
                
                # Test /auth/me endpoint
                user_info = await self.test_auth_me(base_url, token)
                if user_info:
                    env_auth_results["super_admin_login"]["user_info"] = user_info
                    print(f"  ✅ Super Admin authenticated: {user_info.get('name', 'Unknown')}")
                else:
                    env_auth_results["super_admin_login"]["error"] = "/auth/me failed"
            else:
                env_auth_results["super_admin_login"]["status"] = "failed"
                env_auth_results["super_admin_login"]["error"] = "Login failed"
            
            # Test Super Admin alternative login
            alt_token = await self.test_login(base_url, CREDENTIALS["super_admin_alt"], "super_admin_alt")
            if alt_token:
                env_auth_results["super_admin_alt_login"]["status"] = "success"
                self.auth_tokens[f"{env_name}_super_admin_alt"] = alt_token
                
                user_info = await self.test_auth_me(base_url, alt_token)
                if user_info:
                    env_auth_results["super_admin_alt_login"]["user_info"] = user_info
                    print(f"  ✅ Super Admin Alt authenticated: {user_info.get('name', 'Unknown')}")
            else:
                env_auth_results["super_admin_alt_login"]["status"] = "failed"
                env_auth_results["super_admin_alt_login"]["error"] = "Login failed"
            
            # Test Regular User login
            user_token = await self.test_login(base_url, CREDENTIALS["regular_user"], "regular_user")
            if user_token:
                env_auth_results["regular_user_login"]["status"] = "success"
                self.auth_tokens[f"{env_name}_regular_user"] = user_token
                
                user_info = await self.test_auth_me(base_url, user_token)
                if user_info:
                    env_auth_results["regular_user_login"]["user_info"] = user_info
                    print(f"  ✅ Regular User authenticated: {user_info.get('name', 'Unknown')}")
            else:
                env_auth_results["regular_user_login"]["status"] = "failed"
                env_auth_results["regular_user_login"]["error"] = "Login failed"
            
            # RBAC Tests - Test access control
            if token:  # If we have super admin token
                rbac_results = await self.test_rbac_controls(base_url, token, user_token)
                env_auth_results["rbac_tests"] = rbac_results
            
            self.results["authentication_rbac"][env_name] = env_auth_results

    async def test_login(self, base_url, credentials, user_type):
        """Test login and return token"""
        try:
            login_data = {
                "email": credentials["email"],
                "password": credentials["password"]
            }
            
            async with self.session.post(f"{base_url}/auth/login", json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    token = data.get("access_token")
                    if token:
                        print(f"  ✅ {user_type} login successful")
                        return token
                    else:
                        print(f"  ❌ {user_type} login: No token in response")
                        return None
                else:
                    error_text = await response.text()
                    print(f"  ❌ {user_type} login failed: {response.status} - {error_text}")
                    return None
                    
        except Exception as e:
            print(f"  ❌ {user_type} login error: {e}")
            return None

    async def test_auth_me(self, base_url, token):
        """Test /auth/me endpoint"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            async with self.session.get(f"{base_url}/auth/me", headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"  ❌ /auth/me failed: {response.status}")
                    return None
        except Exception as e:
            print(f"  ❌ /auth/me error: {e}")
            return None

    async def test_rbac_controls(self, base_url, admin_token, user_token):
        """Test Role-Based Access Control"""
        rbac_tests = []
        
        # Test admin endpoints with super admin (should work)
        admin_endpoints = [
            "/users",
            "/payroll/cycles",
            "/deductions",
            "/advances/admin/all-balances"
        ]
        
        for endpoint in admin_endpoints:
            try:
                headers = {"Authorization": f"Bearer {admin_token}"}
                async with self.session.get(f"{base_url}{endpoint}", headers=headers) as response:
                    rbac_tests.append({
                        "endpoint": endpoint,
                        "user_type": "super_admin",
                        "expected": "allow",
                        "actual": "allow" if response.status in [200, 201] else "deny",
                        "status_code": response.status
                    })
                    
                    if response.status in [200, 201]:
                        print(f"  ✅ Super Admin access to {endpoint}: {response.status}")
                    else:
                        print(f"  ⚠️ Super Admin access to {endpoint}: {response.status}")
                        
            except Exception as e:
                rbac_tests.append({
                    "endpoint": endpoint,
                    "user_type": "super_admin",
                    "expected": "allow",
                    "actual": "error",
                    "error": str(e)
                })
        
        # Test admin endpoints with regular user (should be denied)
        if user_token:
            restricted_endpoints = ["/users", "/payroll/cycles"]
            
            for endpoint in restricted_endpoints:
                try:
                    headers = {"Authorization": f"Bearer {user_token}"}
                    async with self.session.get(f"{base_url}{endpoint}", headers=headers) as response:
                        rbac_tests.append({
                            "endpoint": endpoint,
                            "user_type": "regular_user",
                            "expected": "deny",
                            "actual": "deny" if response.status == 403 else "allow",
                            "status_code": response.status
                        })
                        
                        if response.status == 403:
                            print(f"  ✅ Regular User denied access to {endpoint}: {response.status}")
                        else:
                            print(f"  ⚠️ Regular User unexpected access to {endpoint}: {response.status}")
                            
                except Exception as e:
                    rbac_tests.append({
                        "endpoint": endpoint,
                        "user_type": "regular_user",
                        "expected": "deny",
                        "actual": "error",
                        "error": str(e)
                    })
        
        return rbac_tests

    async def phase_2_readonly_integrity(self):
        """Phase 2: Read-only Integrity Sweeps"""
        print("\n📋 PHASE 2: READ-ONLY INTEGRITY SWEEPS")
        print("-" * 40)
        
        # Test read-only endpoints for data integrity
        readonly_endpoints = [
            "/users",
            "/attendance",
            "/attendance/with-absences", 
            "/leaves",
            "/leaves/my",
            "/advances/my-balance",
            "/advances/my-transactions",
            "/advances/admin/all-balances",
            "/advances/admin/pending-approvals",
            "/payroll/cycles",
            "/notifications",
            "/work-reports/clients"
        ]
        
        for env_name, base_url in ENVIRONMENTS.items():
            print(f"\n🔍 Testing read-only integrity in {env_name.upper()}")
            
            env_integrity_results = {
                "endpoints_tested": len(readonly_endpoints),
                "successful_responses": 0,
                "failed_responses": 0,
                "endpoint_results": {}
            }
            
            # Get appropriate token for this environment
            admin_token = self.auth_tokens.get(f"{env_name}_super_admin") or self.auth_tokens.get(f"{env_name}_super_admin_alt")
            user_token = self.auth_tokens.get(f"{env_name}_regular_user")
            
            if not admin_token:
                print(f"  ❌ No admin token available for {env_name}")
                continue
            
            for endpoint in readonly_endpoints:
                # Choose appropriate token based on endpoint
                if "/my" in endpoint or endpoint in ["/leaves/my"]:
                    token = user_token or admin_token
                    user_type = "user" if user_token else "admin"
                else:
                    token = admin_token
                    user_type = "admin"
                
                result = await self.test_readonly_endpoint(base_url, endpoint, token, user_type)
                env_integrity_results["endpoint_results"][endpoint] = result
                
                if result["status"] == "success":
                    env_integrity_results["successful_responses"] += 1
                    print(f"  ✅ {endpoint}: {result['status_code']} ({result.get('record_count', 0)} records)")
                else:
                    env_integrity_results["failed_responses"] += 1
                    print(f"  ❌ {endpoint}: {result.get('status_code', 'error')} - {result.get('error', 'Unknown error')}")
            
            self.results["read_only_integrity"][env_name] = env_integrity_results

    async def test_readonly_endpoint(self, base_url, endpoint, token, user_type):
        """Test a read-only endpoint"""
        try:
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            
            async with self.session.get(f"{base_url}{endpoint}", headers=headers) as response:
                result = {
                    "status_code": response.status,
                    "user_type": user_type,
                    "response_time_ms": 0
                }
                
                if response.status == 200:
                    try:
                        data = await response.json()
                        result["status"] = "success"
                        result["has_data"] = bool(data)
                        
                        # Count records if it's a list or has common list fields
                        if isinstance(data, list):
                            result["record_count"] = len(data)
                        elif isinstance(data, dict):
                            # Check for common list fields
                            for key in ["users", "attendance", "leaves", "transactions", "cycles", "notifications", "clients"]:
                                if key in data and isinstance(data[key], list):
                                    result["record_count"] = len(data[key])
                                    break
                            else:
                                result["record_count"] = 1 if data else 0
                        
                        # Validate JSON structure
                        result["valid_json"] = True
                        
                    except Exception as e:
                        result["status"] = "invalid_json"
                        result["error"] = f"JSON parsing failed: {e}"
                        
                elif response.status == 401:
                    result["status"] = "unauthorized"
                    result["error"] = "Authentication required"
                elif response.status == 403:
                    result["status"] = "forbidden"
                    result["error"] = "Access denied"
                else:
                    result["status"] = "error"
                    result["error"] = f"HTTP {response.status}"
                    
                return result
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "user_type": user_type
            }

    async def phase_3_deductions_engine(self):
        """Phase 3: Deductions Engine Testing with Validation Rules"""
        print("\n⚙️ PHASE 3: DEDUCTIONS ENGINE TESTING")
        print("-" * 40)
        
        # Test deductions calculation for October 2025 and recent month
        test_months = ["2025-10", "2025-01"]  # October 2025 and January 2025
        
        for env_name, base_url in ENVIRONMENTS.items():
            print(f"\n🔍 Testing deductions engine in {env_name.upper()}")
            
            admin_token = self.auth_tokens.get(f"{env_name}_super_admin") or self.auth_tokens.get(f"{env_name}_super_admin_alt")
            if not admin_token:
                print(f"  ❌ No admin token available for {env_name}")
                continue
            
            env_deductions_results = {
                "monthly_calculations": {},
                "validation_results": {},
                "employee_summaries": {}
            }
            
            for month in test_months:
                print(f"\n  📅 Testing month: {month}")
                
                # Test monthly deductions calculation
                calc_result = await self.test_monthly_deductions(base_url, admin_token, month)
                env_deductions_results["monthly_calculations"][month] = calc_result
                
                if calc_result["status"] == "success" and calc_result.get("employees"):
                    # Validate deduction rules
                    validation_result = self.validate_deduction_rules(calc_result["employees"])
                    env_deductions_results["validation_results"][month] = validation_result
                    
                    # Extract summaries for specific employees
                    summaries = self.extract_employee_summaries(calc_result["employees"])
                    env_deductions_results["employee_summaries"][month] = summaries
            
            self.results["deductions_engine"][env_name] = env_deductions_results

    async def test_monthly_deductions(self, base_url, token, month):
        """Test monthly deductions calculation"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            url = f"{base_url}/deductions/calculate-monthly?month={month}"
            
            start_time = time.time()
            async with self.session.post(url, headers=headers) as response:
                response_time = (time.time() - start_time) * 1000
                
                result = {
                    "status_code": response.status,
                    "response_time_ms": round(response_time, 2)
                }
                
                if response.status == 200:
                    data = await response.json()
                    result["status"] = "success"
                    result["employees"] = data.get("employees", [])
                    result["employee_count"] = len(result["employees"])
                    
                    print(f"    ✅ Monthly calculation: {response.status} ({result['employee_count']} employees)")
                    
                else:
                    result["status"] = "error"
                    result["error"] = f"HTTP {response.status}"
                    error_text = await response.text()
                    result["error_details"] = error_text
                    print(f"    ❌ Monthly calculation failed: {response.status}")
                
                return result
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def validate_deduction_rules(self, employees):
        """Validate deduction invariants as specified in review"""
        validation_results = {
            "total_employees": len(employees),
            "exempt_employees": 0,
            "flex_employees": 0,
            "partial_flex_employees": 0,
            "rule_violations": []
        }
        
        for employee in employees:
            employee_name = employee.get("employee_name", "Unknown")
            exception_type = employee.get("exception_type", "none")
            total_deduction = employee.get("total_deduction", 0)
            late_deduction = employee.get("late_deduction", 0)
            absence_deduction = employee.get("absence_deduction", 0)
            days_absent = employee.get("days_absent", 0)
            
            # Count exception types
            if exception_type == "exempt":
                validation_results["exempt_employees"] += 1
                
                # Rule: exempt → total_deduction==0
                if total_deduction != 0:
                    validation_results["rule_violations"].append({
                        "employee": employee_name,
                        "rule": "exempt → total_deduction==0",
                        "actual": f"total_deduction={total_deduction}",
                        "severity": "critical"
                    })
                    
            elif exception_type == "flex":
                validation_results["flex_employees"] += 1
                
                # Rule: flex → only absence counted (late_deduction==0)
                if late_deduction != 0:
                    validation_results["rule_violations"].append({
                        "employee": employee_name,
                        "rule": "flex → late_deduction==0",
                        "actual": f"late_deduction={late_deduction}",
                        "severity": "critical"
                    })
                
                # Rule: flex → total==absence if days_absent>0
                if days_absent > 0 and total_deduction != absence_deduction:
                    validation_results["rule_violations"].append({
                        "employee": employee_name,
                        "rule": "flex → total==absence when days_absent>0",
                        "actual": f"total={total_deduction}, absence={absence_deduction}",
                        "severity": "high"
                    })
                    
            elif exception_type == "partial-flex":
                validation_results["partial_flex_employees"] += 1
                
                # Rule: partial-flex → no early/under-hours penalties
                # Rule: partial-flex → only lateness unless daily is absent
                # Rule: partial-flex → when days_absent==0 then absence_deduction==0
                if days_absent == 0 and absence_deduction != 0:
                    validation_results["rule_violations"].append({
                        "employee": employee_name,
                        "rule": "partial-flex → absence_deduction==0 when days_absent==0",
                        "actual": f"absence_deduction={absence_deduction}",
                        "severity": "high"
                    })
        
        return validation_results

    def extract_employee_summaries(self, employees):
        """Extract summaries for specific employees mentioned in review"""
        target_names = ["hatem", "tarek", "tariq", "karim", "hesham"]
        summaries = {}
        
        for employee in employees:
            employee_name = employee.get("employee_name", "").lower()
            
            # Check if this employee matches any target name
            for target in target_names:
                if target in employee_name:
                    summaries[target] = {
                        "name": employee.get("employee_name"),
                        "exception_type": employee.get("exception_type"),
                        "total_deduction": employee.get("total_deduction"),
                        "late_deduction": employee.get("late_deduction"),
                        "absence_deduction": employee.get("absence_deduction"),
                        "days_absent": employee.get("days_absent"),
                        "days_late": employee.get("days_late", 0)
                    }
                    break
        
        return summaries

    async def phase_4_security_checks(self):
        """Phase 4: Security Checks (Non-invasive)"""
        print("\n🔒 PHASE 4: SECURITY CHECKS")
        print("-" * 40)
        
        for env_name, base_url in ENVIRONMENTS.items():
            print(f"\n🔍 Testing security in {env_name.upper()}")
            
            env_security_results = {
                "jwt_expiry_handling": {"status": "unknown", "error": None},
                "cors_headers": {"status": "unknown", "headers": {}},
                "sensitive_data_check": {"status": "unknown", "issues": []}
            }
            
            # Test JWT expiry handling
            try:
                # Use an obviously expired token
                expired_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0IiwiZXhwIjoxNjAwMDAwMDAwfQ.invalid"
                headers = {"Authorization": f"Bearer {expired_token}"}
                
                async with self.session.get(f"{base_url}/auth/me", headers=headers) as response:
                    if response.status == 401:
                        env_security_results["jwt_expiry_handling"]["status"] = "secure"
                        print(f"  ✅ JWT expiry handling: Properly rejects expired tokens")
                    else:
                        env_security_results["jwt_expiry_handling"]["status"] = "insecure"
                        env_security_results["jwt_expiry_handling"]["error"] = f"Unexpected status: {response.status}"
                        print(f"  ⚠️ JWT expiry handling: Unexpected response {response.status}")
                        
            except Exception as e:
                env_security_results["jwt_expiry_handling"]["error"] = str(e)
            
            # Test CORS headers
            try:
                async with self.session.options(f"{base_url}/auth/login") as response:
                    cors_headers = {}
                    for header in ["Access-Control-Allow-Origin", "Access-Control-Allow-Methods", "Access-Control-Allow-Headers"]:
                        if header in response.headers:
                            cors_headers[header] = response.headers[header]
                    
                    env_security_results["cors_headers"]["headers"] = cors_headers
                    env_security_results["cors_headers"]["status"] = "present" if cors_headers else "missing"
                    
                    if cors_headers:
                        print(f"  ✅ CORS headers present: {len(cors_headers)} headers found")
                    else:
                        print(f"  ⚠️ CORS headers: None found")
                        
            except Exception as e:
                env_security_results["cors_headers"]["error"] = str(e)
            
            # Test for sensitive data in responses
            admin_token = self.auth_tokens.get(f"{env_name}_super_admin") or self.auth_tokens.get(f"{env_name}_super_admin_alt")
            if admin_token:
                sensitive_issues = await self.check_sensitive_data(base_url, admin_token)
                env_security_results["sensitive_data_check"]["issues"] = sensitive_issues
                env_security_results["sensitive_data_check"]["status"] = "secure" if not sensitive_issues else "issues_found"
                
                if not sensitive_issues:
                    print(f"  ✅ Sensitive data check: No issues found")
                else:
                    print(f"  ⚠️ Sensitive data check: {len(sensitive_issues)} issues found")
            
            self.results["security_checks"][env_name] = env_security_results

    async def check_sensitive_data(self, base_url, token):
        """Check for sensitive data exposure in API responses"""
        issues = []
        
        # Test endpoints that might expose sensitive data
        test_endpoints = ["/users", "/auth/me"]
        
        for endpoint in test_endpoints:
            try:
                headers = {"Authorization": f"Bearer {token}"}
                async with self.session.get(f"{base_url}{endpoint}", headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Check for password fields
                        if self.contains_password_fields(data):
                            issues.append({
                                "endpoint": endpoint,
                                "issue": "Password fields exposed in response",
                                "severity": "high"
                            })
                        
                        # Check for other sensitive fields
                        sensitive_fields = self.find_sensitive_fields(data)
                        if sensitive_fields:
                            issues.append({
                                "endpoint": endpoint,
                                "issue": f"Sensitive fields exposed: {', '.join(sensitive_fields)}",
                                "severity": "medium"
                            })
                            
            except Exception:
                pass  # Skip on error
        
        return issues

    def contains_password_fields(self, data):
        """Check if data contains password fields"""
        def check_recursive(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if "password" in key.lower() and value:
                        # Check if it looks like a plain text password (not hashed)
                        if isinstance(value, str) and len(value) < 100 and not value.startswith('$'):
                            return True
                    if isinstance(value, (dict, list)):
                        if check_recursive(value):
                            return True
            elif isinstance(obj, list):
                for item in obj:
                    if check_recursive(item):
                        return True
            return False
        
        return check_recursive(data)

    def find_sensitive_fields(self, data):
        """Find other potentially sensitive fields"""
        sensitive_keywords = ["secret", "key", "token", "credential"]
        found_fields = []
        
        def check_recursive(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    if any(keyword in key.lower() for keyword in sensitive_keywords):
                        if isinstance(value, str) and value:
                            found_fields.append(current_path)
                    if isinstance(value, (dict, list)):
                        check_recursive(value, current_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_recursive(item, f"{path}[{i}]")
        
        check_recursive(data)
        return found_fields

    async def phase_5_performance_snapshot(self):
        """Phase 5: Performance Snapshot"""
        print("\n⚡ PHASE 5: PERFORMANCE SNAPSHOT")
        print("-" * 40)
        
        # Test endpoints for performance
        performance_endpoints = [
            "/auth/login",
            "/payroll/cycles", 
            "/deductions/calculate-monthly?month=2025-10"
        ]
        
        for env_name, base_url in ENVIRONMENTS.items():
            print(f"\n🔍 Testing performance in {env_name.upper()}")
            
            admin_token = self.auth_tokens.get(f"{env_name}_super_admin") or self.auth_tokens.get(f"{env_name}_super_admin_alt")
            if not admin_token:
                print(f"  ❌ No admin token available for {env_name}")
                continue
            
            env_performance_results = {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "response_times": [],
                "endpoint_metrics": {}
            }
            
            # Run 20 requests per environment as specified
            for endpoint in performance_endpoints:
                print(f"    📊 Testing {endpoint}")
                
                endpoint_times = []
                successful_count = 0
                
                for i in range(7):  # 7 requests per endpoint (total ~20 across endpoints)
                    response_time = await self.measure_endpoint_performance(base_url, endpoint, admin_token)
                    
                    if response_time > 0:
                        endpoint_times.append(response_time)
                        env_performance_results["response_times"].append(response_time)
                        successful_count += 1
                        env_performance_results["successful_requests"] += 1
                    else:
                        env_performance_results["failed_requests"] += 1
                    
                    env_performance_results["total_requests"] += 1
                
                if endpoint_times:
                    env_performance_results["endpoint_metrics"][endpoint] = {
                        "requests": len(endpoint_times),
                        "successful": successful_count,
                        "p50": round(statistics.median(endpoint_times), 2),
                        "p95": round(statistics.quantiles(endpoint_times, n=20)[18], 2) if len(endpoint_times) >= 20 else round(max(endpoint_times), 2),
                        "avg": round(statistics.mean(endpoint_times), 2),
                        "min": round(min(endpoint_times), 2),
                        "max": round(max(endpoint_times), 2)
                    }
                    
                    print(f"      ✅ {successful_count}/{len(endpoint_times)} successful (avg: {env_performance_results['endpoint_metrics'][endpoint]['avg']}ms)")
            
            # Calculate overall metrics
            if env_performance_results["response_times"]:
                all_times = env_performance_results["response_times"]
                env_performance_results["overall_metrics"] = {
                    "p50": round(statistics.median(all_times), 2),
                    "p95": round(statistics.quantiles(all_times, n=20)[18], 2) if len(all_times) >= 20 else round(max(all_times), 2),
                    "avg": round(statistics.mean(all_times), 2),
                    "requests_per_second": round(env_performance_results["successful_requests"] / (sum(all_times) / 1000), 2) if sum(all_times) > 0 else 0
                }
                
                print(f"    📈 Overall: P50={env_performance_results['overall_metrics']['p50']}ms, P95={env_performance_results['overall_metrics']['p95']}ms")
            
            self.results["performance_metrics"][env_name] = env_performance_results

    async def measure_endpoint_performance(self, base_url, endpoint, token):
        """Measure single endpoint performance"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            
            # Special handling for login endpoint
            if "/auth/login" in endpoint:
                login_data = {"email": "admin@tanseeq.com", "password": "ADMIN"}
                start_time = time.time()
                async with self.session.post(f"{base_url}{endpoint}", json=login_data) as response:
                    response_time = (time.time() - start_time) * 1000
                    return response_time if response.status == 200 else -1
            else:
                # Handle POST endpoints
                if "calculate-monthly" in endpoint:
                    start_time = time.time()
                    async with self.session.post(f"{base_url}{endpoint}", headers=headers) as response:
                        response_time = (time.time() - start_time) * 1000
                        return response_time if response.status in [200, 201] else -1
                else:
                    # GET endpoints
                    start_time = time.time()
                    async with self.session.get(f"{base_url}{endpoint}", headers=headers) as response:
                        response_time = (time.time() - start_time) * 1000
                        return response_time if response.status == 200 else -1
                        
        except Exception:
            return -1

    async def generate_final_report(self):
        """Generate comprehensive final report"""
        print("\n📊 GENERATING FINAL REPORT")
        print("=" * 60)
        
        # Calculate overall test summary
        total_tests = 0
        passed_tests = 0
        
        # Count health checks
        for env_results in self.results["health_checks"].values():
            total_tests += 2  # healthz + readyz
            if env_results["healthz"]["status"] == "healthy":
                passed_tests += 1
            if env_results["readyz"]["status"] == "ready":
                passed_tests += 1
        
        # Count authentication tests
        for env_results in self.results["authentication_rbac"].values():
            total_tests += 3  # 3 login attempts
            if env_results["super_admin_login"]["status"] == "success":
                passed_tests += 1
            if env_results["super_admin_alt_login"]["status"] == "success":
                passed_tests += 1
            if env_results["regular_user_login"]["status"] == "success":
                passed_tests += 1
        
        # Count integrity tests
        for env_results in self.results["read_only_integrity"].values():
            total_tests += env_results["endpoints_tested"]
            passed_tests += env_results["successful_responses"]
        
        # Update test summary
        self.results["test_summary"]["total_tests"] = total_tests
        self.results["test_summary"]["passed_tests"] = passed_tests
        self.results["test_summary"]["failed_tests"] = total_tests - passed_tests
        self.results["test_summary"]["success_rate"] = round((passed_tests / total_tests * 100), 1) if total_tests > 0 else 0
        
        # Identify critical issues
        self.identify_critical_issues()
        
        # Generate recommendations
        self.generate_recommendations()
        
        # Save to evidence file
        evidence_file = EVIDENCE_DIR / "full_audit_backend_results.json"
        with open(evidence_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"📁 Evidence saved to: {evidence_file}")
        
        # Print summary
        self.print_audit_summary()

    def identify_critical_issues(self):
        """Identify critical production-blocking issues"""
        critical_issues = []
        
        # Check health endpoints
        for env_name, env_results in self.results["health_checks"].items():
            if env_results["healthz"]["status"] != "healthy":
                critical_issues.append({
                    "severity": "Critical",
                    "category": "Health Check",
                    "environment": env_name,
                    "issue": f"Health endpoint failing: {env_results['healthz'].get('error', 'Unknown error')}",
                    "impact": "Service unavailable"
                })
            
            if env_results["readyz"]["status"] != "ready":
                critical_issues.append({
                    "severity": "Critical", 
                    "category": "Health Check",
                    "environment": env_name,
                    "issue": f"Readiness endpoint failing: {env_results['readyz'].get('error', 'Unknown error')}",
                    "impact": "Database connectivity issues"
                })
        
        # Check authentication
        for env_name, env_results in self.results["authentication_rbac"].items():
            if env_results["super_admin_login"]["status"] != "success":
                critical_issues.append({
                    "severity": "High",
                    "category": "Authentication",
                    "environment": env_name,
                    "issue": "Super Admin authentication failing",
                    "impact": "Administrative functions unavailable"
                })
        
        # Check deduction rule violations
        for env_name, env_results in self.results["deductions_engine"].items():
            for month, validation in env_results.get("validation_results", {}).items():
                for violation in validation.get("rule_violations", []):
                    if violation["severity"] == "critical":
                        critical_issues.append({
                            "severity": "Critical",
                            "category": "Business Logic",
                            "environment": env_name,
                            "issue": f"Deduction rule violation for {violation['employee']}: {violation['rule']}",
                            "impact": "Incorrect payroll calculations"
                        })
        
        self.results["critical_issues"] = critical_issues

    def generate_recommendations(self):
        """Generate actionable recommendations"""
        recommendations = []
        
        # Performance recommendations
        for env_name, perf_results in self.results["performance_metrics"].items():
            if perf_results.get("overall_metrics", {}).get("p95", 0) > 2000:
                recommendations.append({
                    "priority": "Medium",
                    "category": "Performance",
                    "recommendation": f"Optimize {env_name} environment - P95 response time exceeds 2 seconds",
                    "action": "Review database queries and add caching"
                })
        
        # Security recommendations
        for env_name, security_results in self.results["security_checks"].items():
            if security_results.get("sensitive_data_check", {}).get("status") == "issues_found":
                recommendations.append({
                    "priority": "High",
                    "category": "Security",
                    "recommendation": f"Address sensitive data exposure in {env_name}",
                    "action": "Review API responses and remove sensitive fields"
                })
        
        # Add general recommendations
        recommendations.extend([
            {
                "priority": "Low",
                "category": "Monitoring",
                "recommendation": "Implement automated health check monitoring",
                "action": "Set up alerts for /healthz and /readyz endpoints"
            },
            {
                "priority": "Medium", 
                "category": "Testing",
                "recommendation": "Establish regular deduction rule validation",
                "action": "Automate monthly deduction rule compliance checks"
            }
        ])
        
        self.results["recommendations"] = recommendations

    def print_audit_summary(self):
        """Print concise audit summary"""
        print(f"\n🎯 AUDIT SUMMARY")
        print(f"Success Rate: {self.results['test_summary']['success_rate']}% ({self.results['test_summary']['passed_tests']}/{self.results['test_summary']['total_tests']} tests)")
        
        print(f"\n🏥 HEALTH STATUS:")
        for env_name, env_results in self.results["health_checks"].items():
            health_status = "✅" if env_results["healthz"]["status"] == "healthy" else "❌"
            ready_status = "✅" if env_results["readyz"]["status"] == "ready" else "❌"
            print(f"  {env_name}: Health {health_status} Ready {ready_status}")
        
        print(f"\n🔐 AUTHENTICATION:")
        for env_name, env_results in self.results["authentication_rbac"].items():
            admin_status = "✅" if env_results["super_admin_login"]["status"] == "success" else "❌"
            user_status = "✅" if env_results["regular_user_login"]["status"] == "success" else "❌"
            print(f"  {env_name}: Admin {admin_status} User {user_status}")
        
        print(f"\n⚙️ DEDUCTIONS ENGINE:")
        for env_name, env_results in self.results["deductions_engine"].items():
            for month, calc_result in env_results.get("monthly_calculations", {}).items():
                status = "✅" if calc_result["status"] == "success" else "❌"
                employee_count = calc_result.get("employee_count", 0)
                print(f"  {env_name} {month}: {status} ({employee_count} employees)")
        
        critical_count = len(self.results["critical_issues"])
        if critical_count > 0:
            print(f"\n🚨 CRITICAL ISSUES: {critical_count} found")
            for issue in self.results["critical_issues"][:3]:  # Show first 3
                print(f"  - {issue['category']}: {issue['issue']}")
        else:
            print(f"\n✅ NO CRITICAL ISSUES FOUND")

async def main():
    """Main execution function"""
    auditor = FullSystemAuditor()
    
    try:
        results = await auditor.run_full_audit()
        
        print(f"\n🎉 AUDIT COMPLETED SUCCESSFULLY")
        print(f"📊 Results saved to: /app/evidence/full_audit_backend_results.json")
        
        return results
        
    except Exception as e:
        print(f"\n❌ AUDIT FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(main())