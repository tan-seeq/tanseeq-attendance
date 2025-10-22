#!/usr/bin/env python3
"""
URGENT FORENSIC-LEVEL DATA INTEGRITY AUDIT - PHASE 2
=====================================================

OBJECTIVE: Conduct deep database integrity check and fix critical data issues

TESTING SCOPE:
1. ATTENDANCE RECORDS INTEGRITY (CRITICAL)
2. PAYROLL LEDGER DUPLICATION CHECK (CRITICAL - PRODUCTION BLOCKER)  
3. SALARY CALCULATION RECONCILIATION
4. EMPLOYEE DATA CONSISTENCY
5. ADVANCES/CUSTODY LOGIC VERIFICATION

Authentication:
- Super Admin: admin@tanseeq.com / ADMIN
- Regular User: jihad@tanseeq.com / jihad123
"""

import requests
import json
import sys
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import os

# Configuration
BASE_URL = "https://hr-tanseeq-app.preview.emergentagent.com/api"

# Test credentials
SUPER_ADMIN_CREDS = {"email": "admin@tanseeq.com", "password": "ADMIN"}
USER_CREDS = {"email": "jihad@tanseeq.com", "password": "jihad123"}

class ForensicAudit:
    def __init__(self):
        self.session = requests.Session()
        self.findings = {
            "attendance_integrity": {},
            "payroll_ledger_duplication": {},
            "salary_calculation_reconciliation": {},
            "employee_data_consistency": {},
            "advances_custody_logic": {},
            "summary": {
                "total_issues": 0,
                "critical_issues": 0,
                "affected_employees": set(),
                "affected_records": []
            }
        }
        self.tokens = {}
        
    def authenticate(self, credentials, role_name):
        """Authenticate and get JWT token"""
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", json=credentials)
            if response.status_code == 200:
                data = response.json()
                self.tokens[role_name] = data["access_token"]
                print(f"✅ {role_name} authentication successful")
                return True
            else:
                print(f"❌ {role_name} authentication failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ {role_name} authentication error: {e}")
            return False
    
    def get_headers(self, role="super_admin"):
        """Get authorization headers"""
        token = self.tokens.get(role)
        if not token:
            raise Exception(f"No token for role: {role}")
        return {"Authorization": f"Bearer {token}"}
    
    def make_request(self, method, endpoint, role="super_admin", **kwargs):
        """Make authenticated request"""
        try:
            headers = self.get_headers(role)
            if 'headers' in kwargs:
                kwargs['headers'].update(headers)
            else:
                kwargs['headers'] = headers
                
            response = self.session.request(method, f"{BASE_URL}{endpoint}", **kwargs)
            return response
        except Exception as e:
            print(f"❌ Request error for {endpoint}: {e}")
            return None
    
    def audit_attendance_integrity(self):
        """
        1. ATTENDANCE RECORDS INTEGRITY (CRITICAL):
        - Find ALL attendance records with duplicate IN punches within ≤10 minutes
        - Find ALL attendance records with IN but no OUT on same day
        - Verify late_minutes field calculation for records with check_in > 09:15
        - Check timezone consistency (Asia/Dubai +04:00)
        """
        print("\n🔍 AUDITING ATTENDANCE RECORDS INTEGRITY...")
        
        # Get all attendance records
        response = self.make_request("GET", "/attendance")
        if not response or response.status_code != 200:
            print(f"❌ Failed to get attendance records: {response.status_code if response else 'No response'}")
            return
            
        attendance_records = response.json()
        print(f"📊 Found {len(attendance_records)} attendance records")
        
        findings = {
            "duplicate_checkins": [],
            "incomplete_records": [],
            "late_calculation_errors": [],
            "timezone_inconsistencies": [],
            "missing_fields": []
        }
        
        # Group by employee and date for duplicate detection
        employee_date_checkins = defaultdict(list)
        
        for record in attendance_records:
            employee_id = record.get("user_id")
            date = record.get("date")
            check_in = record.get("check_in")
            check_out = record.get("check_out")
            late_minutes = record.get("late_minutes")
            
            # Check for missing critical fields
            if not all([employee_id, date, check_in]):
                findings["missing_fields"].append({
                    "record_id": record.get("id"),
                    "employee_id": employee_id,
                    "date": date,
                    "missing": [k for k in ["user_id", "date", "check_in"] if not record.get(k)]
                })
                continue
            
            # Group for duplicate detection
            if check_in:
                employee_date_checkins[(employee_id, date)].append({
                    "record_id": record.get("id"),
                    "check_in": check_in,
                    "check_out": check_out,
                    "late_minutes": late_minutes
                })
            
            # Check for incomplete records (IN but no OUT)
            if check_in and not check_out:
                findings["incomplete_records"].append({
                    "record_id": record.get("id"),
                    "employee_id": employee_id,
                    "date": date,
                    "check_in": check_in
                })
            
            # Check late_minutes calculation for check_in > 09:15
            if check_in:
                try:
                    # Handle different time formats
                    check_in_clean = check_in.strip()
                    
                    # Try different time formats
                    time_formats = ["%H:%M:%S", "%H:%M", "%H%M"]
                    check_in_time = None
                    
                    for fmt in time_formats:
                        try:
                            check_in_time = datetime.strptime(check_in_clean, fmt).time()
                            break
                        except ValueError:
                            continue
                    
                    if check_in_time is None:
                        # Skip malformed times
                        continue
                        
                    late_threshold = datetime.strptime("09:15:00", "%H:%M:%S").time()
                    
                    if check_in_time > late_threshold:
                        # Calculate expected late minutes
                        check_in_dt = datetime.combine(datetime.today(), check_in_time)
                        threshold_dt = datetime.combine(datetime.today(), late_threshold)
                        expected_late_minutes = int((check_in_dt - threshold_dt).total_seconds() / 60)
                        
                        actual_late_minutes = late_minutes or 0
                        
                        if actual_late_minutes != expected_late_minutes:
                            findings["late_calculation_errors"].append({
                                "record_id": record.get("id"),
                                "employee_id": employee_id,
                                "date": date,
                                "check_in": check_in,
                                "expected_late_minutes": expected_late_minutes,
                                "actual_late_minutes": actual_late_minutes,
                                "discrepancy": expected_late_minutes - actual_late_minutes
                            })
                except Exception as e:
                    print(f"⚠️ Error parsing check_in time for record {record.get('id')}: {e}")
            
            # Check timezone consistency (should include +04:00)
            for field in ["created_at", "updated_at"]:
                if field in record and record[field]:
                    if "+04:00" not in str(record[field]) and "Z" not in str(record[field]):
                        findings["timezone_inconsistencies"].append({
                            "record_id": record.get("id"),
                            "field": field,
                            "value": record[field],
                            "issue": "Missing timezone info"
                        })
        
        # Check for duplicate check-ins within 10 minutes
        for (employee_id, date), checkins in employee_date_checkins.items():
            if len(checkins) > 1:
                # Sort by check_in time
                checkins.sort(key=lambda x: x["check_in"])
                
                for i in range(len(checkins) - 1):
                    try:
                        # Parse times with multiple format support
                        time1_str = checkins[i]["check_in"].strip()
                        time2_str = checkins[i+1]["check_in"].strip()
                        
                        time_formats = ["%H:%M:%S", "%H:%M"]
                        time1 = time2 = None
                        
                        for fmt in time_formats:
                            try:
                                time1 = datetime.strptime(time1_str, fmt)
                                time2 = datetime.strptime(time2_str, fmt)
                                break
                            except ValueError:
                                continue
                        
                        if time1 and time2:
                            time_diff = abs((time2 - time1).total_seconds() / 60)
                            
                            if time_diff <= 10:
                                findings["duplicate_checkins"].append({
                                    "employee_id": employee_id,
                                    "date": date,
                                    "record1_id": checkins[i]["record_id"],
                                    "record2_id": checkins[i+1]["record_id"],
                                    "check_in1": checkins[i]["check_in"],
                                    "check_in2": checkins[i+1]["check_in"],
                                    "time_difference_minutes": time_diff
                                })
                    except Exception as e:
                        print(f"⚠️ Error comparing check-in times: {e}")
        
        # Store findings
        self.findings["attendance_integrity"] = findings
        
        # Print summary
        print(f"🔍 ATTENDANCE INTEGRITY AUDIT RESULTS:")
        print(f"   📋 Duplicate check-ins (≤10 min): {len(findings['duplicate_checkins'])}")
        print(f"   📋 Incomplete records (IN but no OUT): {len(findings['incomplete_records'])}")
        print(f"   📋 Late calculation errors: {len(findings['late_calculation_errors'])}")
        print(f"   📋 Timezone inconsistencies: {len(findings['timezone_inconsistencies'])}")
        print(f"   📋 Missing critical fields: {len(findings['missing_fields'])}")
        
        # Update summary
        total_issues = sum(len(v) for v in findings.values())
        self.findings["summary"]["total_issues"] += total_issues
        if total_issues > 0:
            self.findings["summary"]["critical_issues"] += 1
    
    def audit_payroll_ledger_duplication(self):
        """
        2. PAYROLL LEDGER DUPLICATION CHECK (CRITICAL - PRODUCTION BLOCKER):
        Test payroll cycle EDIT scenario for ledger entry duplication
        """
        print("\n🔍 AUDITING PAYROLL LEDGER DUPLICATION...")
        
        # Get payroll cycles
        response = self.make_request("GET", "/payroll/cycles")
        if not response or response.status_code != 200:
            print(f"❌ Failed to get payroll cycles: {response.status_code if response else 'No response'}")
            return
            
        cycles = response.json()
        print(f"📊 Found {len(cycles)} payroll cycles")
        
        findings = {
            "duplicate_ledger_entries": [],
            "summary_ledger_mismatches": [],
            "recalculation_issues": []
        }
        
        # Test with existing cycle (e.g., 2025-11)
        target_cycle = None
        for cycle in cycles:
            if "2025-11" in cycle.get("cycle_id", "") or "2025-11" in cycle.get("id", ""):
                target_cycle = cycle
                break
        
        if not target_cycle:
            # Use the first available cycle
            target_cycle = cycles[0] if cycles else None
            
        if not target_cycle:
            print("❌ No payroll cycles found for testing")
            return
            
        cycle_id = target_cycle.get("id")
        print(f"🎯 Testing cycle: {cycle_id}")
        
        # Get initial ledger state
        ledger_response = self.make_request("GET", f"/payroll/cycles/{cycle_id}/ledger")
        if ledger_response and ledger_response.status_code == 200:
            ledger_data = ledger_response.json()
            
            # Handle different response formats
            if isinstance(ledger_data, list):
                initial_ledger = ledger_data
            elif isinstance(ledger_data, dict) and 'entries' in ledger_data:
                initial_ledger = ledger_data['entries']
            elif isinstance(ledger_data, dict) and 'ledger_entries' in ledger_data:
                initial_ledger = ledger_data['ledger_entries']
            else:
                initial_ledger = []
                
            print(f"📊 Initial ledger entries: {len(initial_ledger)}")
            
            # Create a signature for each ledger entry to detect duplicates
            initial_signatures = []
            for entry in initial_ledger:
                if isinstance(entry, dict):
                    signature = f"{entry.get('employee_id')}_{cycle_id}_{entry.get('source_type')}_{entry.get('source_id', 'none')}"
                    initial_signatures.append(signature)
            
            # Count duplicates in initial state
            signature_counts = Counter(initial_signatures)
            for signature, count in signature_counts.items():
                if count > 1:
                    findings["duplicate_ledger_entries"].append({
                        "signature": signature,
                        "count": count,
                        "stage": "initial"
                    })
        else:
            print(f"⚠️ Could not get initial ledger state: {ledger_response.status_code if ledger_response else 'No response'}")
            initial_ledger = []
        
        # Perform recalculation
        recalc_response = self.make_request("POST", f"/payroll/cycles/{cycle_id}/recalculate")
        if recalc_response and recalc_response.status_code == 200:
            print("✅ Payroll recalculation completed")
            
            # Get ledger state after recalculation
            post_ledger_response = self.make_request("GET", f"/payroll/cycles/{cycle_id}/ledger")
            if post_ledger_response and post_ledger_response.status_code == 200:
                post_ledger_data = post_ledger_response.json()
                
                # Handle different response formats
                if isinstance(post_ledger_data, list):
                    post_ledger = post_ledger_data
                elif isinstance(post_ledger_data, dict) and 'entries' in post_ledger_data:
                    post_ledger = post_ledger_data['entries']
                elif isinstance(post_ledger_data, dict) and 'ledger_entries' in post_ledger_data:
                    post_ledger = post_ledger_data['ledger_entries']
                else:
                    post_ledger = []
                    
                print(f"📊 Post-recalc ledger entries: {len(post_ledger)}")
                
                # Check for new duplicates
                post_signatures = []
                for entry in post_ledger:
                    if isinstance(entry, dict):
                        signature = f"{entry.get('employee_id')}_{cycle_id}_{entry.get('source_type')}_{entry.get('source_id', 'none')}"
                        post_signatures.append(signature)
                
                post_signature_counts = Counter(post_signatures)
                for signature, count in post_signature_counts.items():
                    if count > 1:
                        findings["duplicate_ledger_entries"].append({
                            "signature": signature,
                            "count": count,
                            "stage": "post_recalculation"
                        })
                
                # Check if ledger grew unexpectedly (indicating duplication)
                if len(post_ledger) > len(initial_ledger) * 1.5:  # 50% growth threshold
                    findings["recalculation_issues"].append({
                        "cycle_id": cycle_id,
                        "initial_count": len(initial_ledger),
                        "post_count": len(post_ledger),
                        "growth_ratio": len(post_ledger) / len(initial_ledger) if initial_ledger else float('inf'),
                        "issue": "Unexpected ledger growth after recalculation"
                    })
            else:
                print(f"⚠️ Could not get post-recalc ledger state: {post_ledger_response.status_code if post_ledger_response else 'No response'}")
        else:
            print(f"⚠️ Payroll recalculation failed: {recalc_response.status_code if recalc_response else 'No response'}")
            findings["recalculation_issues"].append({
                "cycle_id": cycle_id,
                "issue": "Recalculation endpoint failed",
                "status_code": recalc_response.status_code if recalc_response else None
            })
        
        # Verify payroll summary consistency
        summary_response = self.make_request("GET", f"/payroll/cycles/{cycle_id}/summary")
        if summary_response and summary_response.status_code == 200:
            summary_data = summary_response.json()
            
            # Compare summary totals with ledger aggregations
            if initial_ledger:
                ledger_totals = defaultdict(float)
                for entry in initial_ledger:
                    if isinstance(entry, dict):
                        employee_id = entry.get("employee_id")
                        amount = entry.get("amount", 0)
                        if employee_id and isinstance(amount, (int, float)):
                            ledger_totals[employee_id] += amount
                
                # Check if summary matches ledger
                for employee_summary in summary_data.get("employee_summaries", []):
                    employee_id = employee_summary.get("employee_id")
                    summary_deductions = employee_summary.get("total_deductions", 0)
                    ledger_total = ledger_totals.get(employee_id, 0)
                    
                    if abs(summary_deductions - ledger_total) > 0.01:  # Allow for small rounding differences
                        findings["summary_ledger_mismatches"].append({
                            "employee_id": employee_id,
                            "summary_deductions": summary_deductions,
                            "ledger_total": ledger_total,
                            "discrepancy": summary_deductions - ledger_total
                        })
        
        # Store findings
        self.findings["payroll_ledger_duplication"] = findings
        
        # Print summary
        print(f"🔍 PAYROLL LEDGER DUPLICATION AUDIT RESULTS:")
        print(f"   📋 Duplicate ledger entries: {len(findings['duplicate_ledger_entries'])}")
        print(f"   📋 Summary-ledger mismatches: {len(findings['summary_ledger_mismatches'])}")
        print(f"   📋 Recalculation issues: {len(findings['recalculation_issues'])}")
        
        # Update summary
        total_issues = sum(len(v) for v in findings.values())
        self.findings["summary"]["total_issues"] += total_issues
        if total_issues > 0:
            self.findings["summary"]["critical_issues"] += 1
    
    def audit_salary_calculation_reconciliation(self):
        """
        3. SALARY CALCULATION RECONCILIATION:
        For each employee in payroll: verify Days × Daily Rate = Total Salary
        """
        print("\n🔍 AUDITING SALARY CALCULATION RECONCILIATION...")
        
        # Get employees
        response = self.make_request("GET", "/employees/list")
        if not response or response.status_code != 200:
            print(f"❌ Failed to get employees: {response.status_code if response else 'No response'}")
            return
            
        employees_data = response.json()
        
        # Handle different response formats
        if isinstance(employees_data, list):
            employees = employees_data
        elif isinstance(employees_data, dict) and 'employees' in employees_data:
            employees = employees_data['employees']
        else:
            employees = []
            
        print(f"📊 Found {len(employees)} employees")
        
        # Get payroll cycles
        cycles_response = self.make_request("GET", "/payroll/cycles")
        if not cycles_response or cycles_response.status_code != 200:
            print(f"❌ Failed to get payroll cycles")
            return
            
        cycles = cycles_response.json()
        
        findings = {
            "salary_calculation_errors": [],
            "missing_employee_data": [],
            "payroll_data_issues": []
        }
        
        # Create employee lookup
        employee_lookup = {}
        for emp in employees:
            if isinstance(emp, dict) and emp.get("id"):
                employee_lookup[emp.get("id")] = emp
        
        for cycle in cycles[:3]:  # Test first 3 cycles to avoid too much data
            cycle_id = cycle.get("id")
            
            # Get cycle summary
            summary_response = self.make_request("GET", f"/payroll/cycles/{cycle_id}/summary")
            if not summary_response or summary_response.status_code != 200:
                continue
                
            summary_data = summary_response.json()
            
            for emp_summary in summary_data.get("employee_summaries", []):
                employee_id = emp_summary.get("employee_id")
                employee = employee_lookup.get(employee_id)
                
                if not employee:
                    findings["missing_employee_data"].append({
                        "employee_id": employee_id,
                        "cycle_id": cycle_id,
                        "issue": "Employee not found in employees list"
                    })
                    continue
                
                # Get employee salary data
                daily_rate = employee.get("daily_rate", 0)
                monthly_salary = employee.get("monthly_salary", 0)
                
                # Get payroll calculation data
                basic_salary = emp_summary.get("basic_salary", 0)
                working_days = emp_summary.get("working_days", 0)
                
                # Verify calculation: Days × Daily Rate = Basic Salary
                if daily_rate > 0 and working_days > 0:
                    expected_salary = working_days * daily_rate
                    
                    if abs(basic_salary - expected_salary) > 0.01:  # Allow small rounding differences
                        findings["salary_calculation_errors"].append({
                            "employee_id": employee_id,
                            "employee_name": employee.get("name"),
                            "cycle_id": cycle_id,
                            "daily_rate": daily_rate,
                            "working_days": working_days,
                            "expected_salary": expected_salary,
                            "actual_salary": basic_salary,
                            "discrepancy": basic_salary - expected_salary
                        })
                
                # Also check if monthly salary is reasonable
                if monthly_salary > 0 and daily_rate > 0:
                    expected_daily_rate = monthly_salary / 30  # Approximate
                    if abs(daily_rate - expected_daily_rate) > (expected_daily_rate * 0.2):  # 20% tolerance
                        findings["payroll_data_issues"].append({
                            "employee_id": employee_id,
                            "employee_name": employee.get("name"),
                            "monthly_salary": monthly_salary,
                            "daily_rate": daily_rate,
                            "expected_daily_rate": expected_daily_rate,
                            "issue": "Daily rate inconsistent with monthly salary"
                        })
        
        # Store findings
        self.findings["salary_calculation_reconciliation"] = findings
        
        # Print summary
        print(f"🔍 SALARY CALCULATION RECONCILIATION AUDIT RESULTS:")
        print(f"   📋 Salary calculation errors: {len(findings['salary_calculation_errors'])}")
        print(f"   📋 Missing employee data: {len(findings['missing_employee_data'])}")
        print(f"   📋 Payroll data issues: {len(findings['payroll_data_issues'])}")
        
        # Update summary
        total_issues = sum(len(v) for v in findings.values())
        self.findings["summary"]["total_issues"] += total_issues
        if total_issues > 0:
            self.findings["summary"]["critical_issues"] += 1
    
    def audit_employee_data_consistency(self):
        """
        4. EMPLOYEE DATA CONSISTENCY:
        Check email/name/role consistency across collections
        """
        print("\n🔍 AUDITING EMPLOYEE DATA CONSISTENCY...")
        
        findings = {
            "email_mismatches": [],
            "name_mismatches": [],
            "role_mismatches": [],
            "missing_references": []
        }
        
        # Get data from different collections
        employees_response = self.make_request("GET", "/employees/list")
        users_response = self.make_request("GET", "/users")
        attendance_response = self.make_request("GET", "/attendance")
        
        # Handle employees data
        if employees_response and employees_response.status_code == 200:
            emp_data = employees_response.json()
            employees = emp_data if isinstance(emp_data, list) else emp_data.get('employees', [])
        else:
            employees = []
            
        # Handle users data  
        if users_response and users_response.status_code == 200:
            users_data = users_response.json()
            users = users_data if isinstance(users_data, list) else users_data.get('users', [])
        else:
            users = []
            
        # Handle attendance data
        if attendance_response and attendance_response.status_code == 200:
            att_data = attendance_response.json()
            attendance_records = att_data if isinstance(att_data, list) else att_data.get('attendance', [])
        else:
            attendance_records = []
        
        print(f"📊 Data sources: {len(employees)} employees, {len(users)} users, {len(attendance_records)} attendance records")
        
        # Create lookups
        employee_lookup = {}
        for emp in employees:
            if isinstance(emp, dict) and emp.get("id"):
                employee_lookup[emp.get("id")] = emp
                
        user_lookup = {}
        for user in users:
            if isinstance(user, dict) and user.get("id"):
                user_lookup[user.get("id")] = user
        
        # Check employees vs users consistency
        for employee in employees:
            emp_id = employee.get("id")
            user = user_lookup.get(emp_id)
            
            if not user:
                findings["missing_references"].append({
                    "type": "employee_without_user",
                    "employee_id": emp_id,
                    "employee_name": employee.get("name"),
                    "employee_email": employee.get("email")
                })
                continue
            
            # Check email consistency
            if employee.get("email") != user.get("email"):
                findings["email_mismatches"].append({
                    "employee_id": emp_id,
                    "employee_email": employee.get("email"),
                    "user_email": user.get("email")
                })
            
            # Check name consistency
            if employee.get("name") != user.get("name"):
                findings["name_mismatches"].append({
                    "employee_id": emp_id,
                    "employee_name": employee.get("name"),
                    "user_name": user.get("name")
                })
            
            # Check role consistency
            if employee.get("role") != user.get("role"):
                findings["role_mismatches"].append({
                    "employee_id": emp_id,
                    "employee_role": employee.get("role"),
                    "user_role": user.get("role")
                })
        
        # Check attendance records for orphaned references
        attendance_employee_ids = set()
        for record in attendance_records:
            emp_id = record.get("user_id")
            if emp_id:
                attendance_employee_ids.add(emp_id)
                
                if emp_id not in employee_lookup and emp_id not in user_lookup:
                    findings["missing_references"].append({
                        "type": "attendance_orphaned_employee",
                        "employee_id": emp_id,
                        "attendance_record_id": record.get("id"),
                        "date": record.get("date")
                    })
        
        # Store findings
        self.findings["employee_data_consistency"] = findings
        
        # Print summary
        print(f"🔍 EMPLOYEE DATA CONSISTENCY AUDIT RESULTS:")
        print(f"   📋 Email mismatches: {len(findings['email_mismatches'])}")
        print(f"   📋 Name mismatches: {len(findings['name_mismatches'])}")
        print(f"   📋 Role mismatches: {len(findings['role_mismatches'])}")
        print(f"   📋 Missing references: {len(findings['missing_references'])}")
        
        # Update summary
        total_issues = sum(len(v) for v in findings.values())
        self.findings["summary"]["total_issues"] += total_issues
        if total_issues > 0:
            self.findings["summary"]["critical_issues"] += 1
    
    def audit_advances_custody_logic(self):
        """
        5. ADVANCES/CUSTODY LOGIC VERIFICATION:
        - Verify custody can be deducted by expenses
        - Verify advances are NOT deducted by expenses (only by salary settlement)
        - Check for any overspending scenarios
        """
        print("\n🔍 AUDITING ADVANCES/CUSTODY LOGIC...")
        
        findings = {
            "custody_deduction_errors": [],
            "advance_deduction_errors": [],
            "overspending_scenarios": [],
            "balance_calculation_errors": []
        }
        
        # Get all employee balances
        balances_response = self.make_request("GET", "/advances/admin/all-balances")
        if not balances_response or balances_response.status_code != 200:
            print(f"❌ Failed to get employee balances: {balances_response.status_code if balances_response else 'No response'}")
            return
            
        balances = balances_response.json().get("employee_balances", [])
        print(f"📊 Found {len(balances)} employee balances")
        
        # Get all transactions for detailed analysis
        transactions_response = self.make_request("GET", "/advances/admin/all-transactions", params={"limit": 1000})
        if not transactions_response or transactions_response.status_code != 200:
            print(f"❌ Failed to get transactions")
            return
            
        all_transactions = transactions_response.json().get("transactions", [])
        print(f"📊 Found {len(all_transactions)} transactions")
        
        # Group transactions by employee
        employee_transactions = defaultdict(list)
        for txn in all_transactions:
            employee_id = txn.get("employee_id")
            if employee_id:
                employee_transactions[employee_id].append(txn)
        
        # Analyze each employee's transaction logic
        for balance in balances:
            employee_id = balance.get("employee_id")
            employee_name = balance.get("employee_name")
            
            total_advances = balance.get("total_advances", 0)
            total_custody = balance.get("total_custody", 0)
            total_expenses = balance.get("total_expenses", 0)
            remaining_advance = balance.get("remaining_advance", 0)
            remaining_custody = balance.get("remaining_custody", 0)
            
            transactions = employee_transactions.get(employee_id, [])
            
            # Calculate expected balances based on business rules
            calculated_advances = 0
            calculated_custody = 0
            calculated_expenses = 0
            
            for txn in transactions:
                txn_type = txn.get("transaction_type")
                amount = txn.get("amount", 0)
                status = txn.get("status")
                
                if status == "approved":
                    if txn_type == "advance":
                        calculated_advances += amount
                    elif txn_type == "custody":
                        calculated_custody += amount
                    elif txn_type == "expense":
                        calculated_expenses += amount
            
            # Verify totals match
            if abs(total_advances - calculated_advances) > 0.01:
                findings["balance_calculation_errors"].append({
                    "employee_id": employee_id,
                    "employee_name": employee_name,
                    "field": "total_advances",
                    "expected": calculated_advances,
                    "actual": total_advances,
                    "discrepancy": total_advances - calculated_advances
                })
            
            if abs(total_custody - calculated_custody) > 0.01:
                findings["balance_calculation_errors"].append({
                    "employee_id": employee_id,
                    "employee_name": employee_name,
                    "field": "total_custody",
                    "expected": calculated_custody,
                    "actual": total_custody,
                    "discrepancy": total_custody - calculated_custody
                })
            
            if abs(total_expenses - calculated_expenses) > 0.01:
                findings["balance_calculation_errors"].append({
                    "employee_id": employee_id,
                    "employee_name": employee_name,
                    "field": "total_expenses",
                    "expected": calculated_expenses,
                    "actual": total_expenses,
                    "discrepancy": total_expenses - calculated_expenses
                })
            
            # Check business logic: Advances should NOT be deducted by expenses
            expected_remaining_advance = calculated_advances  # Should remain full
            if abs(remaining_advance - expected_remaining_advance) > 0.01:
                findings["advance_deduction_errors"].append({
                    "employee_id": employee_id,
                    "employee_name": employee_name,
                    "expected_remaining": expected_remaining_advance,
                    "actual_remaining": remaining_advance,
                    "issue": "Advances incorrectly deducted by expenses"
                })
            
            # Check business logic: Custody should be deducted by expenses
            expected_remaining_custody = max(0, calculated_custody - calculated_expenses)
            if abs(remaining_custody - expected_remaining_custody) > 0.01:
                findings["custody_deduction_errors"].append({
                    "employee_id": employee_id,
                    "employee_name": employee_name,
                    "expected_remaining": expected_remaining_custody,
                    "actual_remaining": remaining_custody,
                    "total_custody": calculated_custody,
                    "total_expenses": calculated_expenses,
                    "issue": "Custody deduction calculation error"
                })
            
            # Check for overspending (expenses > available balance)
            total_available = calculated_advances + calculated_custody
            if calculated_expenses > total_available:
                findings["overspending_scenarios"].append({
                    "employee_id": employee_id,
                    "employee_name": employee_name,
                    "total_available": total_available,
                    "total_expenses": calculated_expenses,
                    "overspend_amount": calculated_expenses - total_available
                })
        
        # Store findings
        self.findings["advances_custody_logic"] = findings
        
        # Print summary
        print(f"🔍 ADVANCES/CUSTODY LOGIC AUDIT RESULTS:")
        print(f"   📋 Custody deduction errors: {len(findings['custody_deduction_errors'])}")
        print(f"   📋 Advance deduction errors: {len(findings['advance_deduction_errors'])}")
        print(f"   📋 Overspending scenarios: {len(findings['overspending_scenarios'])}")
        print(f"   📋 Balance calculation errors: {len(findings['balance_calculation_errors'])}")
        
        # Update summary
        total_issues = sum(len(v) for v in findings.values())
        self.findings["summary"]["total_issues"] += total_issues
        if total_issues > 0:
            self.findings["summary"]["critical_issues"] += 1
    
    def generate_evidence_report(self):
        """Generate comprehensive evidence report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Calculate affected employees and records
        affected_employees = set()
        affected_records = []
        
        for category, findings in self.findings.items():
            if category == "summary":
                continue
                
            for finding_type, issues in findings.items():
                for issue in issues:
                    if "employee_id" in issue:
                        affected_employees.add(issue["employee_id"])
                    if "record_id" in issue:
                        affected_records.append(issue["record_id"])
        
        self.findings["summary"]["affected_employees"] = list(affected_employees)
        self.findings["summary"]["affected_records"] = affected_records
        
        # Generate report
        report = {
            "audit_metadata": {
                "timestamp": timestamp,
                "audit_type": "FORENSIC_DATA_INTEGRITY_AUDIT_PHASE_2",
                "base_url": BASE_URL,
                "total_issues_found": self.findings["summary"]["total_issues"],
                "critical_categories_affected": self.findings["summary"]["critical_issues"],
                "affected_employees_count": len(affected_employees),
                "affected_records_count": len(affected_records)
            },
            "executive_summary": {
                "status": "CRITICAL" if self.findings["summary"]["critical_issues"] > 2 else "WARNING" if self.findings["summary"]["total_issues"] > 0 else "CLEAN",
                "production_readiness": "BLOCKED" if self.findings["summary"]["critical_issues"] > 2 else "CONDITIONAL" if self.findings["summary"]["total_issues"] > 0 else "READY",
                "immediate_action_required": self.findings["summary"]["critical_issues"] > 0
            },
            "detailed_findings": self.findings
        }
        
        # Save to file
        filename = f"forensic_audit_evidence_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📄 EVIDENCE REPORT GENERATED: {filename}")
        return filename, report
    
    def run_full_audit(self):
        """Run complete forensic audit"""
        print("🚨 STARTING URGENT FORENSIC-LEVEL DATA INTEGRITY AUDIT - PHASE 2")
        print("=" * 70)
        
        # Authenticate
        if not self.authenticate(SUPER_ADMIN_CREDS, "super_admin"):
            print("❌ Super Admin authentication failed - cannot proceed")
            return False
            
        if not self.authenticate(USER_CREDS, "user"):
            print("⚠️ User authentication failed - limited testing")
        
        # Run all audit modules
        try:
            self.audit_attendance_integrity()
            self.audit_payroll_ledger_duplication()
            self.audit_salary_calculation_reconciliation()
            self.audit_employee_data_consistency()
            self.audit_advances_custody_logic()
            
            # Generate evidence report
            filename, report = self.generate_evidence_report()
            
            # Print final summary
            print("\n" + "=" * 70)
            print("🚨 FORENSIC AUDIT COMPLETE - EXECUTIVE SUMMARY")
            print("=" * 70)
            print(f"📊 TOTAL ISSUES FOUND: {report['audit_metadata']['total_issues_found']}")
            print(f"🔥 CRITICAL CATEGORIES: {report['audit_metadata']['critical_categories_affected']}")
            print(f"👥 AFFECTED EMPLOYEES: {report['audit_metadata']['affected_employees_count']}")
            print(f"📋 AFFECTED RECORDS: {report['audit_metadata']['affected_records_count']}")
            print(f"🚦 PRODUCTION STATUS: {report['executive_summary']['production_readiness']}")
            print(f"⚡ IMMEDIATE ACTION: {'YES' if report['executive_summary']['immediate_action_required'] else 'NO'}")
            
            return True
            
        except Exception as e:
            print(f"❌ AUDIT FAILED: {e}")
            return False

if __name__ == "__main__":
    audit = ForensicAudit()
    success = audit.run_full_audit()
    sys.exit(0 if success else 1)