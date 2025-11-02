#!/usr/bin/env python3
"""
Production Authentication Audit Test
Testing employee login failures on production environment
Base URL: https://hrapp-tanseeq-replaced-1761028017.emergent.host/api
"""

import requests
import json
import os
from datetime import datetime
from typing import Dict, Any

# Configuration
BASE_URL = "https://hrapp-tanseeq-replaced-1761028017.emergent.host/api"
EVIDENCE_DIR = "/app/evidence"

# Test credentials from review request
TEST_CREDENTIALS = [
    {"email": "admin@tanseeq.com", "password": "ADMIN", "role": "super_admin", "expected": 200},
    {"email": "mahmoud@tanseeq.com", "password": "mahmoud123", "role": "admin", "expected": 200},
    {"email": "jihad@tanseeq.com", "password": "jihad123", "role": "user", "expected": 200}
]

def create_evidence_dir():
    """Create evidence directory if it doesn't exist"""
    os.makedirs(EVIDENCE_DIR, exist_ok=True)

def test_login(email: str, password: str) -> Dict[str, Any]:
    """Test login for a specific user"""
    url = f"{BASE_URL}/auth/login"
    payload = {
        "email": email,
        "password": password
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        result = {
            "email": email,
            "status_code": response.status_code,
            "success": response.status_code == 200,
            "response_data": None,
            "error": None,
            "token": None
        }
        
        if response.status_code == 200:
            try:
                data = response.json()
                result["response_data"] = data
                result["token"] = data.get("access_token")
                result["user_info"] = data.get("user", {})
            except json.JSONDecodeError:
                result["error"] = "Invalid JSON response"
        else:
            try:
                error_data = response.json()
                result["error"] = error_data.get("detail", f"HTTP {response.status_code}")
            except json.JSONDecodeError:
                result["error"] = f"HTTP {response.status_code} - {response.text[:200]}"
        
        return result
        
    except requests.exceptions.RequestException as e:
        return {
            "email": email,
            "status_code": None,
            "success": False,
            "response_data": None,
            "error": f"Request failed: {str(e)}",
            "token": None
        }

def get_users_list(admin_token: str) -> Dict[str, Any]:
    """Get users list using super admin token"""
    url = f"{BASE_URL}/users"
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        result = {
            "status_code": response.status_code,
            "success": response.status_code == 200,
            "users": [],
            "error": None
        }
        
        if response.status_code == 200:
            try:
                data = response.json()
                result["users"] = data if isinstance(data, list) else data.get("users", [])
            except json.JSONDecodeError:
                result["error"] = "Invalid JSON response"
        else:
            try:
                error_data = response.json()
                result["error"] = error_data.get("detail", f"HTTP {response.status_code}")
            except json.JSONDecodeError:
                result["error"] = f"HTTP {response.status_code} - {response.text[:200]}"
        
        return result
        
    except requests.exceptions.RequestException as e:
        return {
            "status_code": None,
            "success": False,
            "users": [],
            "error": f"Request failed: {str(e)}"
        }

def analyze_user_in_database(users_list: list, target_email: str) -> Dict[str, Any]:
    """Analyze if user exists in database and check their properties"""
    for user in users_list:
        if user.get("email") == target_email:
            return {
                "exists": True,
                "is_active": user.get("is_active", False),
                "has_password": "password" in user and user["password"] is not None,
                "role": user.get("role", "unknown"),
                "name": user.get("name", ""),
                "user_data": user
            }
    
    return {
        "exists": False,
        "is_active": None,
        "has_password": None,
        "role": None,
        "name": None,
        "user_data": None
    }

def determine_root_cause(login_result: Dict[str, Any], db_analysis: Dict[str, Any]) -> str:
    """Determine the likely root cause of login failure"""
    if not db_analysis["exists"]:
        return "EMAIL_MISMATCH - User email does not exist in database"
    
    if not db_analysis["is_active"]:
        return "INACTIVE_FLAG - User account is marked as inactive"
    
    if not db_analysis["has_password"]:
        return "MISSING_PASSWORD - User has no password hash in database"
    
    if login_result["status_code"] == 401:
        return "INVALID_PASSWORD_HASH - Password hash doesn't match or is corrupted"
    
    return f"UNKNOWN - Status: {login_result['status_code']}, Error: {login_result.get('error', 'Unknown')}"

def run_production_auth_audit():
    """Run the complete production authentication audit"""
    print("🔍 Starting Production Authentication Audit...")
    print(f"Base URL: {BASE_URL}")
    print("=" * 80)
    
    create_evidence_dir()
    
    audit_results = {
        "audit_info": {
            "timestamp": datetime.now().isoformat(),
            "base_url": BASE_URL,
            "test_type": "production_auth_audit"
        },
        "login_tests": [],
        "users_database_check": None,
        "summary": {
            "total_tests": len(TEST_CREDENTIALS),
            "passed": 0,
            "failed": 0,
            "pass_fail_per_user": {}
        },
        "root_causes": {}
    }
    
    # Step 1-3: Test each credential
    admin_token = None
    failed_logins = []
    
    for i, cred in enumerate(TEST_CREDENTIALS, 1):
        print(f"\n{i}. Testing {cred['role']} login: {cred['email']}")
        
        login_result = test_login(cred["email"], cred["password"])
        audit_results["login_tests"].append(login_result)
        
        if login_result["success"]:
            print(f"   ✅ SUCCESS - Status: {login_result['status_code']}")
            audit_results["summary"]["passed"] += 1
            audit_results["summary"]["pass_fail_per_user"][cred["email"]] = "PASS"
            
            # Store admin token for database check
            if cred["role"] == "super_admin" and login_result["token"]:
                admin_token = login_result["token"]
        else:
            print(f"   ❌ FAILED - Status: {login_result['status_code']}, Error: {login_result['error']}")
            audit_results["summary"]["failed"] += 1
            audit_results["summary"]["pass_fail_per_user"][cred["email"]] = "FAIL"
            failed_logins.append(cred)
    
    # Step 4: If any failed and we have admin token, check database
    if failed_logins and admin_token:
        print(f"\n4. Checking database for failed logins using super admin token...")
        
        users_result = get_users_list(admin_token)
        audit_results["users_database_check"] = users_result
        
        if users_result["success"]:
            print(f"   ✅ Retrieved {len(users_result['users'])} users from database")
            
            # Analyze each failed login
            for cred in failed_logins:
                print(f"\n   Analyzing {cred['email']}:")
                db_analysis = analyze_user_in_database(users_result["users"], cred["email"])
                
                # Find corresponding login result
                login_result = next((lr for lr in audit_results["login_tests"] if lr["email"] == cred["email"]), {})
                
                # Determine root cause
                root_cause = determine_root_cause(login_result, db_analysis)
                audit_results["root_causes"][cred["email"]] = {
                    "root_cause": root_cause,
                    "database_analysis": db_analysis
                }
                
                print(f"     - Exists in DB: {db_analysis['exists']}")
                if db_analysis["exists"]:
                    print(f"     - Is Active: {db_analysis['is_active']}")
                    print(f"     - Has Password: {db_analysis['has_password']}")
                    print(f"     - Role: {db_analysis['role']}")
                    print(f"     - Name: {db_analysis['name']}")
                print(f"     - Root Cause: {root_cause}")
        else:
            print(f"   ❌ Failed to retrieve users: {users_result['error']}")
    
    elif failed_logins and not admin_token:
        print(f"\n4. ⚠️  Cannot check database - Super admin login failed, no token available")
        audit_results["users_database_check"] = {
            "error": "Super admin login failed - cannot retrieve users list",
            "success": False
        }
    
    # Step 5: Save results to evidence file
    evidence_file = os.path.join(EVIDENCE_DIR, "prod_auth_audit.json")
    with open(evidence_file, "w", encoding="utf-8") as f:
        json.dump(audit_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📁 Results saved to: {evidence_file}")
    
    # Step 6: Summary
    print("\n" + "=" * 80)
    print("📊 PRODUCTION AUTH AUDIT SUMMARY")
    print("=" * 80)
    
    for email, result in audit_results["summary"]["pass_fail_per_user"].items():
        status_icon = "✅" if result == "PASS" else "❌"
        print(f"{status_icon} {email}: {result}")
    
    print(f"\nTotal Tests: {audit_results['summary']['total_tests']}")
    print(f"Passed: {audit_results['summary']['passed']}")
    print(f"Failed: {audit_results['summary']['failed']}")
    
    if audit_results["root_causes"]:
        print(f"\n🔍 ROOT CAUSES FOR FAILURES:")
        for email, analysis in audit_results["root_causes"].items():
            print(f"   {email}: {analysis['root_cause']}")
    
    return audit_results

if __name__ == "__main__":
    try:
        results = run_production_auth_audit()
        
        # Exit with appropriate code
        if results["summary"]["failed"] > 0:
            print(f"\n⚠️  {results['summary']['failed']} authentication test(s) failed")
            exit(1)
        else:
            print(f"\n🎉 All {results['summary']['passed']} authentication tests passed")
            exit(0)
            
    except Exception as e:
        print(f"\n💥 Audit failed with exception: {str(e)}")
        exit(1)