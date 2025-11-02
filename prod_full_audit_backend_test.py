#!/usr/bin/env python3
"""
🔥 PRODUCTION FULL SYSTEM AUDIT - BACKEND TESTING
Comprehensive read-only testing on production environment
Base URL: https://hrapp-tanseeq-replaced-1761028017.emergent.host/api
"""

import requests
import json
import os
from datetime import datetime, timezone
from pathlib import Path

# Test Configuration
BASE_URL = "https://hrapp-tanseeq-replaced-1761028017.emergent.host/api"
EVIDENCE_DIR = Path("/app/evidence")
EVIDENCE_FILE = EVIDENCE_DIR / "prod_full_audit_backend.json"

# Test Credentials
ADMIN_CREDENTIALS = {
    "email": "admin@tanseeq.com",
    "password": "ADMIN"
}

# Test Results Storage
test_results = {
    "audit_info": {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "base_url": BASE_URL,
        "test_type": "production_full_audit",
        "scope": [
            "Health endpoints",
            "Authentication & JWT validation", 
            "Users & RBAC",
            "Attendance & Deductions",
            "Payroll cycles",
            "Advances system",
            "Notifications",
            "Work Reports",
            "Security testing"
        ]
    },
    "test_summary": {
        "total_tests": 0,
        "passed": 0,
        "failed": 0,
        "success_rate": 0.0
    },
    "test_categories": {},
    "critical_issues": [],
    "security_findings": [],
    "evidence": {}
}

def log_test_result(category, test_name, success, details, response_data=None):
    """Log individual test result"""
    global test_results
    
    if category not in test_results["test_categories"]:
        test_results["test_categories"][category] = {
            "tests": [],
            "passed": 0,
            "failed": 0
        }
    
    test_entry = {
        "test_name": test_name,
        "success": success,
        "details": details,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    if response_data:
        test_entry["response_data"] = response_data
    
    test_results["test_categories"][category]["tests"].append(test_entry)
    
    if success:
        test_results["test_categories"][category]["passed"] += 1
        test_results["test_summary"]["passed"] += 1
    else:
        test_results["test_categories"][category]["failed"] += 1
        test_results["test_summary"]["failed"] += 1
        
    test_results["test_summary"]["total_tests"] += 1
    
    # Calculate success rate
    total = test_results["test_summary"]["total_tests"]
    passed = test_results["test_summary"]["passed"]
    test_results["test_summary"]["success_rate"] = round((passed / total) * 100, 1) if total > 0 else 0.0
    
    print(f"{'✅' if success else '❌'} [{category}] {test_name}: {details}")

def add_critical_issue(severity, component, issue, root_cause, recommended_fix):
    """Add critical issue to findings"""
    test_results["critical_issues"].append({
        "severity": severity,
        "component": component,
        "issue": issue,
        "root_cause": root_cause,
        "recommended_fix": recommended_fix,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

def add_security_finding(finding_type, description, risk_level, evidence):
    """Add security finding"""
    test_results["security_findings"].append({
        "type": finding_type,
        "description": description,
        "risk_level": risk_level,
        "evidence": evidence,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

def test_health_endpoints():
    """Test health and readiness endpoints"""
    print("\n🏥 TESTING HEALTH ENDPOINTS")
    
    # Test /healthz
    try:
        response = requests.get(f"{BASE_URL}/healthz", timeout=10)
        if response.status_code == 200:
            data = response.json()
            log_test_result("Health", "GET /healthz", True, 
                          f"Status: {response.status_code}, Response: {data}")
        else:
            log_test_result("Health", "GET /healthz", False, 
                          f"Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        log_test_result("Health", "GET /healthz", False, f"Exception: {str(e)}")
    
    # Test /readyz
    try:
        response = requests.get(f"{BASE_URL}/readyz", timeout=10)
        if response.status_code == 200:
            data = response.json()
            log_test_result("Health", "GET /readyz", True, 
                          f"Status: {response.status_code}, Response: {data}")
        else:
            log_test_result("Health", "GET /readyz", False, 
                          f"Status: {response.status_code}, Response: {response.text}")
            add_critical_issue("HIGH", "Database", "Readiness check failing", 
                             "Database connectivity issues", "Check MongoDB connection")
    except Exception as e:
        log_test_result("Health", "GET /readyz", False, f"Exception: {str(e)}")
        add_critical_issue("CRITICAL", "Infrastructure", "Readiness endpoint unreachable", 
                         "Network or service issues", "Check service availability")

def test_authentication_and_jwt():
    """Test authentication system and JWT validation"""
    print("\n🔐 TESTING AUTHENTICATION & JWT")
    
    # Test login with admin credentials
    try:
        response = requests.post(f"{BASE_URL}/auth/login", 
                               json=ADMIN_CREDENTIALS, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            user_info = data.get("user", {})
            
            log_test_result("Authentication", "POST /auth/login (admin)", True,
                          f"Login successful, Role: {user_info.get('role')}")
            
            # Store token for subsequent tests
            test_results["evidence"]["admin_token"] = token
            test_results["evidence"]["admin_user"] = user_info
            
            # Test /auth/me with valid token
            headers = {"Authorization": f"Bearer {token}"}
            me_response = requests.get(f"{BASE_URL}/auth/me", headers=headers, timeout=10)
            
            if me_response.status_code == 200:
                me_data = me_response.json()
                log_test_result("Authentication", "GET /auth/me (valid token)", True,
                              f"User ID: {me_data.get('id')}, Role: {me_data.get('role')}")
            else:
                log_test_result("Authentication", "GET /auth/me (valid token)", False,
                              f"Status: {me_response.status_code}")
                
        else:
            log_test_result("Authentication", "POST /auth/login (admin)", False,
                          f"Status: {response.status_code}, Response: {response.text}")
            add_critical_issue("CRITICAL", "Authentication", "Admin login failing",
                             "Invalid credentials or authentication system down",
                             "Verify admin credentials and auth service")
            
    except Exception as e:
        log_test_result("Authentication", "POST /auth/login (admin)", False, f"Exception: {str(e)}")
        add_critical_issue("CRITICAL", "Authentication", "Login endpoint unreachable",
                         "Network or service issues", "Check authentication service")

def test_security_features():
    """Test security features"""
    print("\n🛡️ TESTING SECURITY FEATURES")
    
    # Test invalid token
    try:
        invalid_headers = {"Authorization": "Bearer invalid_token_12345"}
        response = requests.get(f"{BASE_URL}/auth/me", headers=invalid_headers, timeout=10)
        
        if response.status_code == 401:
            log_test_result("Security", "Invalid JWT rejection", True,
                          "Invalid token correctly rejected with 401")
        else:
            log_test_result("Security", "Invalid JWT rejection", False,
                          f"Expected 401, got {response.status_code}")
            add_security_finding("AUTHENTICATION", "Invalid token not rejected properly",
                               "HIGH", f"Status: {response.status_code}")
    except Exception as e:
        log_test_result("Security", "Invalid JWT rejection", False, f"Exception: {str(e)}")
    
    # Test CORS headers on OPTIONS request
    try:
        response = requests.options(f"{BASE_URL}/auth/login", timeout=10)
        cors_headers = {
            "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
            "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
            "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers")
        }
        
        if any(cors_headers.values()):
            log_test_result("Security", "CORS headers present", True,
                          f"CORS headers found: {cors_headers}")
        else:
            log_test_result("Security", "CORS headers present", False,
                          "No CORS headers found")
            
    except Exception as e:
        log_test_result("Security", "CORS headers test", False, f"Exception: {str(e)}")

def test_users_and_rbac():
    """Test users endpoint and RBAC"""
    print("\n👥 TESTING USERS & RBAC")
    
    token = test_results["evidence"].get("admin_token")
    if not token:
        log_test_result("RBAC", "Users endpoint test", False, "No admin token available")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test GET /users with admin token
    try:
        response = requests.get(f"{BASE_URL}/users", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            users_count = len(data) if isinstance(data, list) else len(data.get("users", []))
            log_test_result("RBAC", "GET /users (admin access)", True,
                          f"Retrieved {users_count} users")
            test_results["evidence"]["users_data"] = data
        else:
            log_test_result("RBAC", "GET /users (admin access)", False,
                          f"Status: {response.status_code}")
            
    except Exception as e:
        log_test_result("RBAC", "GET /users (admin access)", False, f"Exception: {str(e)}")

def test_attendance_and_deductions():
    """Test attendance and deductions endpoints"""
    print("\n📅 TESTING ATTENDANCE & DEDUCTIONS")
    
    token = test_results["evidence"].get("admin_token")
    if not token:
        log_test_result("Attendance", "Attendance tests", False, "No admin token available")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test GET /attendance
    try:
        response = requests.get(f"{BASE_URL}/attendance", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            records_count = len(data) if isinstance(data, list) else len(data.get("attendance", []))
            log_test_result("Attendance", "GET /attendance", True,
                          f"Retrieved {records_count} attendance records")
        else:
            log_test_result("Attendance", "GET /attendance", False,
                          f"Status: {response.status_code}")
            
    except Exception as e:
        log_test_result("Attendance", "GET /attendance", False, f"Exception: {str(e)}")
    
    # Test GET /attendance/with-absences
    try:
        response = requests.get(f"{BASE_URL}/attendance/with-absences", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            records_count = len(data) if isinstance(data, list) else len(data.get("attendance", []))
            log_test_result("Attendance", "GET /attendance/with-absences", True,
                          f"Retrieved {records_count} records with absences")
        else:
            log_test_result("Attendance", "GET /attendance/with-absences", False,
                          f"Status: {response.status_code}")
            
    except Exception as e:
        log_test_result("Attendance", "GET /attendance/with-absences", False, f"Exception: {str(e)}")
    
    # Test monthly deductions calculation for 2025-10
    try:
        response = requests.post(f"{BASE_URL}/deductions/calculate-monthly?month=2025-10", 
                               headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            log_test_result("Deductions", "POST /deductions/calculate-monthly (2025-10)", True,
                          f"Monthly calculation successful: {len(data.get('employees', []))} employees")
        else:
            log_test_result("Deductions", "POST /deductions/calculate-monthly (2025-10)", False,
                          f"Status: {response.status_code}")
            
    except Exception as e:
        log_test_result("Deductions", "POST /deductions/calculate-monthly (2025-10)", False, f"Exception: {str(e)}")
    
    # Test monthly deductions calculation for 2025-11
    try:
        response = requests.post(f"{BASE_URL}/deductions/calculate-monthly?month=2025-11", 
                               headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            log_test_result("Deductions", "POST /deductions/calculate-monthly (2025-11)", True,
                          f"Monthly calculation successful: {len(data.get('employees', []))} employees")
        else:
            log_test_result("Deductions", "POST /deductions/calculate-monthly (2025-11)", False,
                          f"Status: {response.status_code}")
            
    except Exception as e:
        log_test_result("Deductions", "POST /deductions/calculate-monthly (2025-11)", False, f"Exception: {str(e)}")

def test_payroll_system():
    """Test payroll endpoints"""
    print("\n💰 TESTING PAYROLL SYSTEM")
    
    token = test_results["evidence"].get("admin_token")
    if not token:
        log_test_result("Payroll", "Payroll tests", False, "No admin token available")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test GET /payroll/cycles
    try:
        response = requests.get(f"{BASE_URL}/payroll/cycles", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            cycles = data if isinstance(data, list) else data.get("cycles", [])
            log_test_result("Payroll", "GET /payroll/cycles", True,
                          f"Retrieved {len(cycles)} payroll cycles")
            
            # Test cycle summary for first cycle if available
            if cycles:
                cycle_id = cycles[0].get("id")
                if cycle_id:
                    summary_response = requests.get(f"{BASE_URL}/payroll/cycles/{cycle_id}/summary", 
                                                  headers=headers, timeout=10)
                    
                    if summary_response.status_code == 200:
                        summary_data = summary_response.json()
                        log_test_result("Payroll", f"GET /payroll/cycles/{cycle_id}/summary", True,
                                      f"Cycle summary retrieved successfully")
                    else:
                        log_test_result("Payroll", f"GET /payroll/cycles/{cycle_id}/summary", False,
                                      f"Status: {summary_response.status_code}")
        else:
            log_test_result("Payroll", "GET /payroll/cycles", False,
                          f"Status: {response.status_code}")
            
    except Exception as e:
        log_test_result("Payroll", "GET /payroll/cycles", False, f"Exception: {str(e)}")

def test_advances_system():
    """Test advances and loans system"""
    print("\n💳 TESTING ADVANCES SYSTEM")
    
    token = test_results["evidence"].get("admin_token")
    if not token:
        log_test_result("Advances", "Advances tests", False, "No admin token available")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test GET /advances/admin/all-balances
    try:
        response = requests.get(f"{BASE_URL}/advances/admin/all-balances", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            balances = data.get("employee_balances", [])
            log_test_result("Advances", "GET /advances/admin/all-balances", True,
                          f"Retrieved {len(balances)} employee balances")
        else:
            log_test_result("Advances", "GET /advances/admin/all-balances", False,
                          f"Status: {response.status_code}")
            
    except Exception as e:
        log_test_result("Advances", "GET /advances/admin/all-balances", False, f"Exception: {str(e)}")
    
    # Test GET /advances/admin/all-transactions
    try:
        response = requests.get(f"{BASE_URL}/advances/admin/all-transactions", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            transactions = data.get("transactions", [])
            log_test_result("Advances", "GET /advances/admin/all-transactions", True,
                          f"Retrieved {len(transactions)} transactions")
        else:
            log_test_result("Advances", "GET /advances/admin/all-transactions", False,
                          f"Status: {response.status_code}")
            
    except Exception as e:
        log_test_result("Advances", "GET /advances/admin/all-transactions", False, f"Exception: {str(e)}")

def test_notifications_system():
    """Test notifications system"""
    print("\n🔔 TESTING NOTIFICATIONS SYSTEM")
    
    token = test_results["evidence"].get("admin_token")
    if not token:
        log_test_result("Notifications", "Notifications tests", False, "No admin token available")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test GET /notifications
    try:
        response = requests.get(f"{BASE_URL}/notifications", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            notifications = data if isinstance(data, list) else data.get("notifications", [])
            log_test_result("Notifications", "GET /notifications", True,
                          f"Retrieved {len(notifications)} notifications")
        else:
            log_test_result("Notifications", "GET /notifications", False,
                          f"Status: {response.status_code}")
            
    except Exception as e:
        log_test_result("Notifications", "GET /notifications", False, f"Exception: {str(e)}")
    
    # Test GET /notifications/my
    try:
        response = requests.get(f"{BASE_URL}/notifications/my", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            my_notifications = data if isinstance(data, list) else data.get("notifications", [])
            log_test_result("Notifications", "GET /notifications/my", True,
                          f"Retrieved {len(my_notifications)} personal notifications")
        else:
            log_test_result("Notifications", "GET /notifications/my", False,
                          f"Status: {response.status_code}")
            
    except Exception as e:
        log_test_result("Notifications", "GET /notifications/my", False, f"Exception: {str(e)}")

def test_work_reports_system():
    """Test work reports MongoDB system"""
    print("\n📊 TESTING WORK REPORTS SYSTEM")
    
    token = test_results["evidence"].get("admin_token")
    if not token:
        log_test_result("Work Reports", "Work Reports tests", False, "No admin token available")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test GET /work-reports/clients
    try:
        response = requests.get(f"{BASE_URL}/work-reports/clients", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            clients = data if isinstance(data, list) else data.get("clients", [])
            log_test_result("Work Reports", "GET /work-reports/clients", True,
                          f"Retrieved {len(clients)} clients")
        else:
            log_test_result("Work Reports", "GET /work-reports/clients", False,
                          f"Status: {response.status_code}")
            
    except Exception as e:
        log_test_result("Work Reports", "GET /work-reports/clients", False, f"Exception: {str(e)}")
    
    # Test GET /work-reports/logs
    try:
        response = requests.get(f"{BASE_URL}/work-reports/logs", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            logs = data if isinstance(data, list) else data.get("logs", [])
            log_test_result("Work Reports", "GET /work-reports/logs", True,
                          f"Retrieved {len(logs)} work logs")
        else:
            log_test_result("Work Reports", "GET /work-reports/logs", False,
                          f"Status: {response.status_code}")
            
    except Exception as e:
        log_test_result("Work Reports", "GET /work-reports/logs", False, f"Exception: {str(e)}")

def verify_exception_invariants():
    """Verify attendance policy exceptions for specific employees"""
    print("\n🔍 VERIFYING EXCEPTION INVARIANTS")
    
    # Check for specific employees mentioned: Hatem/Tarek/Karim/Hesham
    target_employees = ["Hatem", "Tarek", "Karim", "Hesham"]
    users_data = test_results["evidence"].get("users_data", [])
    
    if isinstance(users_data, dict):
        users_data = users_data.get("users", [])
    
    found_employees = []
    for user in users_data:
        user_name = user.get("name", "")
        for target in target_employees:
            if target.lower() in user_name.lower():
                found_employees.append({
                    "name": user_name,
                    "has_flexible_schedule": user.get("has_flexible_schedule", False),
                    "role": user.get("role", ""),
                    "schedule_type": "flexible" if user.get("has_flexible_schedule") else "fixed"
                })
                break
    
    if found_employees:
        log_test_result("Policy Exceptions", "Employee exception verification", True,
                      f"Found {len(found_employees)} target employees with schedule policies")
        test_results["evidence"]["exception_employees"] = found_employees
    else:
        log_test_result("Policy Exceptions", "Employee exception verification", False,
                      "No target employees found in user data")

def save_evidence():
    """Save all evidence to JSON file"""
    print(f"\n💾 SAVING EVIDENCE TO {EVIDENCE_FILE}")
    
    # Ensure evidence directory exists
    EVIDENCE_DIR.mkdir(exist_ok=True)
    
    # Add final summary
    test_results["final_summary"] = {
        "audit_completed": True,
        "total_categories": len(test_results["test_categories"]),
        "critical_issues_count": len(test_results["critical_issues"]),
        "security_findings_count": len(test_results["security_findings"]),
        "overall_health": "GOOD" if test_results["test_summary"]["success_rate"] >= 80 else 
                         "FAIR" if test_results["test_summary"]["success_rate"] >= 60 else "POOR"
    }
    
    # Save to file
    with open(EVIDENCE_FILE, 'w', encoding='utf-8') as f:
        json.dump(test_results, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Evidence saved successfully to {EVIDENCE_FILE}")

def print_final_summary():
    """Print comprehensive test summary"""
    print("\n" + "="*80)
    print("🔥 PRODUCTION FULL SYSTEM AUDIT - FINAL SUMMARY")
    print("="*80)
    
    summary = test_results["test_summary"]
    print(f"📊 OVERALL RESULTS:")
    print(f"   Total Tests: {summary['total_tests']}")
    print(f"   Passed: {summary['passed']} ✅")
    print(f"   Failed: {summary['failed']} ❌")
    print(f"   Success Rate: {summary['success_rate']}%")
    
    print(f"\n📋 TEST CATEGORIES:")
    for category, data in test_results["test_categories"].items():
        success_rate = round((data['passed'] / (data['passed'] + data['failed'])) * 100, 1) if (data['passed'] + data['failed']) > 0 else 0
        print(f"   {category}: {data['passed']}/{data['passed'] + data['failed']} ({success_rate}%)")
    
    if test_results["critical_issues"]:
        print(f"\n🚨 CRITICAL ISSUES ({len(test_results['critical_issues'])}):")
        for issue in test_results["critical_issues"]:
            print(f"   [{issue['severity']}] {issue['component']}: {issue['issue']}")
    
    if test_results["security_findings"]:
        print(f"\n🛡️ SECURITY FINDINGS ({len(test_results['security_findings'])}):")
        for finding in test_results["security_findings"]:
            print(f"   [{finding['risk_level']}] {finding['type']}: {finding['description']}")
    
    print(f"\n📁 Evidence saved to: {EVIDENCE_FILE}")
    print("="*80)

def main():
    """Main test execution"""
    print("🚀 STARTING PRODUCTION FULL SYSTEM AUDIT")
    print(f"🎯 Target: {BASE_URL}")
    print(f"📅 Timestamp: {datetime.now(timezone.utc).isoformat()}")
    
    # Execute all test categories
    test_health_endpoints()
    test_authentication_and_jwt()
    test_security_features()
    test_users_and_rbac()
    test_attendance_and_deductions()
    test_payroll_system()
    test_advances_system()
    test_notifications_system()
    test_work_reports_system()
    verify_exception_invariants()
    
    # Save evidence and print summary
    save_evidence()
    print_final_summary()

if __name__ == "__main__":
    main()