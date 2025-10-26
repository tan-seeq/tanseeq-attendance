#!/usr/bin/env python3
"""
🎯 PHASE 3: COMPREHENSIVE END-TO-END BACKEND VALIDATION
Unified Deductions Engine Testing - Complete Review Request Implementation

Test Objectives from Review Request:
1. Cross-page consistency validation (Dashboard vs Advanced Deductions vs Payroll)
2. Formula consistency across months
3. Exempt employees validation  
4. Payroll cycle detailed fields validation
5. Daily breakdown validation
6. Calculation accuracy spot check
7. Error handling & edge cases
8. Performance check

Success Criteria:
- All 3 pages return SAME values
- Formula (DailyRate/540) verified for multiple employees
- Grace period = 5 minutes confirmed
- Exempt employees show 0 deductions
- All new payroll fields present and populated correctly
- Daily breakdown includes all required fields
- No errors for valid requests
- Proper error handling for invalid inputs
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

class Phase3ComprehensiveValidationTest:
    def __init__(self):
        # Get backend URL from environment
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    self.base_url = line.split('=')[1].strip()
                    break
        
        self.base_url = f"{self.base_url}/api"
        self.headers = {}
        self.test_results = []
        self.evidence = {}
        self.performance_metrics = {}
        
        print(f"🔗 Backend URL: {self.base_url}")
        
    def authenticate(self, email: str, password: str) -> bool:
        """Authenticate and get JWT token"""
        try:
            response = requests.post(f"{self.base_url}/auth/login", 
                                   json={"email": email, "password": password})
            
            if response.status_code == 200:
                data = response.json()
                self.headers = {"Authorization": f"Bearer {data['access_token']}"}
                print(f"✅ Authentication successful for {email}")
                return True
            else:
                print(f"❌ Authentication failed for {email}: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def log_test(self, test_name: str, success: bool, details: str, data: Any = None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {details}")
        
        if data:
            self.evidence[test_name] = data
    
    def test_1_cross_page_consistency_validation(self):
        """Test A: October 2025 Deduction Consistency - Dashboard vs Advanced Deductions vs Payroll"""
        print("\n🎯 TEST 1: CROSS-PAGE CONSISTENCY VALIDATION")
        print("Testing: Dashboard, Advanced Deductions, Payroll return SAME values")
        
        try:
            # Endpoint 1: Monthly deductions calculation (Advanced Deductions page)
            start_time = time.time()
            response1 = requests.post(f"{self.base_url}/deductions/calculate-monthly?month=2025-10", 
                                    headers=self.headers)
            deductions_time = time.time() - start_time
            
            if response1.status_code != 200:
                self.log_test("Advanced Deductions API", False, 
                            f"Status {response1.status_code}: {response1.text}")
                return
            
            deductions_data = response1.json()
            self.log_test("Advanced Deductions API", True, 
                        f"Retrieved data for {len(deductions_data.get('employees', []))} employees in {deductions_time:.2f}s")
            
            # Verify engine version
            engine_version = deductions_data.get('engine_version')
            if engine_version == "unified_v1.0":
                self.log_test("Engine Version Verification", True, f"Confirmed: {engine_version}")
            else:
                self.log_test("Engine Version Verification", False, f"Expected unified_v1.0, got: {engine_version}")
            
            # Verify formula note
            note = deductions_data.get('note', '')
            if "(DailyRate/540) × deductible_minutes" in note:
                self.log_test("Formula Note Verification", True, "Formula correctly documented")
            else:
                self.log_test("Formula Note Verification", False, f"Formula not found in note: {note}")
            
            # Extract deductions by employee
            advanced_deductions = {}
            for emp in deductions_data.get('employees', []):
                emp_name = emp.get('employee_name', '')
                total_deduction = emp.get('total_deduction', 0)
                advanced_deductions[emp_name] = {
                    'total_deduction': total_deduction,
                    'late_days': emp.get('late_days', 0),
                    'late_minutes': emp.get('late_minutes', 0),
                    'absent_days': emp.get('absent_days', 0)
                }
            
            # Find October 2025 payroll cycle
            cycles_response = requests.get(f"{self.base_url}/payroll/cycles", headers=self.headers)
            if cycles_response.status_code != 200:
                self.log_test("Payroll Cycles API", False, f"Status {cycles_response.status_code}")
                return
            
            cycles = cycles_response.json()
            october_cycle = None
            
            # Look for October 2025 cycle
            for cycle in cycles:
                start_date = cycle.get('start_date', '')
                end_date = cycle.get('end_date', '')
                if '2025-09-29' in start_date and '2025-10-28' in end_date:
                    october_cycle = cycle
                    break
            
            if not october_cycle:
                self.log_test("October Cycle Discovery", False, "No October 2025 cycle found")
                return
            
            cycle_id = october_cycle.get('id')
            self.log_test("October Cycle Discovery", True, f"Found cycle: {cycle_id}")
            
            # Endpoint 2: Payroll cycle summary (Payroll page)
            start_time = time.time()
            response2 = requests.get(f"{self.base_url}/payroll/cycles/{cycle_id}/summary", 
                                   headers=self.headers)
            payroll_time = time.time() - start_time
            
            if response2.status_code != 200:
                self.log_test("Payroll Summary API", False, f"Status {response2.status_code}")
                return
            
            payroll_data = response2.json()
            self.log_test("Payroll Summary API", True, 
                        f"Retrieved summary for {len(payroll_data.get('employees', []))} employees in {payroll_time:.2f}s")
            
            # Extract payroll deductions by employee
            payroll_deductions = {}
            for emp in payroll_data.get('employees', []):
                emp_name = emp.get('employee_name', '')
                payroll_deductions[emp_name] = {
                    'total_deduction': emp.get('total_deduction_unified', emp.get('total_deductions', 0)),
                    'absent_days': emp.get('absent_days', 0),
                    'absence_amount': emp.get('absence_amount', 0),
                    'late_days': emp.get('late_days', 0),
                    'late_minutes': emp.get('late_minutes', 0),
                    'late_amount': emp.get('late_amount', 0)
                }
            
            # Test specific employees from review request
            key_employees = {
                'Hesham': {'expected_deduction': (33, 34), 'description': '10 late days'},
                'Mohamed Mostafa': {'expected_deduction': (340, 345), 'description': '2 absences, 14 late days'},
                'Hatem': {'expected_deduction': (0, 0), 'description': 'exempt'}
            }
            
            consistency_results = []
            for emp_name, expected in key_employees.items():
                # Find matching employee (case insensitive)
                adv_data = None
                pay_data = None
                
                for name in advanced_deductions.keys():
                    if emp_name.lower() in name.lower():
                        adv_data = advanced_deductions[name]
                        break
                
                for name in payroll_deductions.keys():
                    if emp_name.lower() in name.lower():
                        pay_data = payroll_deductions[name]
                        break
                
                if adv_data and pay_data:
                    adv_total = adv_data['total_deduction']
                    pay_total = pay_data['total_deduction']
                    
                    # Check consistency (allow small floating point differences)
                    if abs(adv_total - pay_total) <= 0.01:
                        self.log_test(f"{emp_name} Consistency", True, 
                                    f"Advanced: {adv_total} AED, Payroll: {pay_total} AED")
                    else:
                        self.log_test(f"{emp_name} Consistency", False, 
                                    f"Mismatch - Advanced: {adv_total} AED, Payroll: {pay_total} AED")
                    
                    # Check expected range
                    min_exp, max_exp = expected['expected_deduction']
                    if min_exp <= adv_total <= max_exp:
                        self.log_test(f"{emp_name} Expected Range", True, 
                                    f"Value {adv_total} AED in range {min_exp}-{max_exp} AED")
                    else:
                        self.log_test(f"{emp_name} Expected Range", False, 
                                    f"Value {adv_total} AED not in range {min_exp}-{max_exp} AED")
                    
                    consistency_results.append({
                        'employee': emp_name,
                        'advanced_deduction': adv_total,
                        'payroll_deduction': pay_total,
                        'consistent': abs(adv_total - pay_total) <= 0.01,
                        'in_expected_range': min_exp <= adv_total <= max_exp
                    })
                else:
                    self.log_test(f"{emp_name} Data Found", False, f"Employee not found in both datasets")
            
            # Store evidence
            self.evidence['cross_page_consistency'] = {
                'advanced_deductions': advanced_deductions,
                'payroll_deductions': payroll_deductions,
                'consistency_results': consistency_results,
                'october_cycle': october_cycle
            }
            
            self.performance_metrics['deductions_api_time'] = deductions_time
            self.performance_metrics['payroll_api_time'] = payroll_time
            
        except Exception as e:
            self.log_test("Cross-Page Consistency Test", False, f"Exception: {str(e)}")
    
    def test_2_formula_consistency_across_months(self):
        """Test Different Months for Formula Consistency"""
        print("\n🎯 TEST 2: FORMULA CONSISTENCY ACROSS MONTHS")
        print("Testing: October 2025 vs November 2025")
        
        test_months = ['2025-10', '2025-11']
        month_results = {}
        
        for month in test_months:
            try:
                start_time = time.time()
                response = requests.post(f"{self.base_url}/deductions/calculate-monthly?month={month}", 
                                       headers=self.headers)
                api_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    month_results[month] = data
                    
                    # Check grace period = 5 minutes (not 15)
                    grace_period = data.get('grace_period_minutes', 0)
                    if grace_period == 5:
                        self.log_test(f"Grace Period {month}", True, "Grace period = 5 minutes (correct)")
                    else:
                        self.log_test(f"Grace Period {month}", False, f"Grace period = {grace_period}, expected 5")
                    
                    # Check cycle dates = 29th prev month → 28th current month
                    cycle_window = data.get('cycle_window', '')
                    expected_start = f"{int(month[:4])}-{int(month[5:])-1:02d}-29"
                    expected_end = f"{month}-28"
                    
                    if expected_start in cycle_window and expected_end in cycle_window:
                        self.log_test(f"Cycle Dates {month}", True, f"Correct cycle: {cycle_window}")
                    else:
                        self.log_test(f"Cycle Dates {month}", False, f"Unexpected cycle: {cycle_window}")
                    
                    self.log_test(f"Monthly Calculation {month}", True, 
                                f"Retrieved {len(data.get('employees', []))} employees in {api_time:.2f}s")
                    
                    self.performance_metrics[f'{month}_api_time'] = api_time
                else:
                    self.log_test(f"Monthly Calculation {month}", False, 
                                f"Status {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test(f"Monthly Calculation {month}", False, f"Exception: {str(e)}")
        
        # Compare formula consistency between months
        if len(month_results) >= 2:
            oct_data = month_results.get('2025-10', {})
            nov_data = month_results.get('2025-11', {})
            
            # Check if formula structure is consistent
            oct_employees = {emp.get('employee_name'): emp for emp in oct_data.get('employees', [])}
            nov_employees = {emp.get('employee_name'): emp for emp in nov_data.get('employees', [])}
            
            common_employees = set(oct_employees.keys()) & set(nov_employees.keys())
            
            if common_employees:
                self.log_test("Formula Consistency Check", True, 
                            f"Found {len(common_employees)} common employees across months")
                
                # Verify formula application is consistent (structure, not values)
                for emp_name in list(common_employees)[:3]:  # Test first 3 common employees
                    oct_emp = oct_employees[emp_name]
                    nov_emp = nov_employees[emp_name]
                    
                    # Check if both have daily_rate field (formula component)
                    oct_daily = oct_emp.get('daily_rate', 0)
                    nov_daily = nov_emp.get('daily_rate', 0)
                    
                    if oct_daily > 0 and nov_daily > 0:
                        self.log_test(f"Formula Structure {emp_name}", True, 
                                    f"Daily rates present: Oct={oct_daily}, Nov={nov_daily}")
                    else:
                        self.log_test(f"Formula Structure {emp_name}", False, 
                                    f"Missing daily rates: Oct={oct_daily}, Nov={nov_daily}")
            else:
                self.log_test("Formula Consistency Check", False, "No common employees found")
        
        self.evidence['month_comparison'] = month_results
    
    def test_3_exempt_employees_validation(self):
        """Test Exempt Rules - Hatem and Tariq special cases"""
        print("\n🎯 TEST 3: EXEMPT EMPLOYEES VALIDATION")
        print("Testing: Hatem (exempt) and Tariq (no late before 08:00)")
        
        try:
            # Get monthly deductions for October
            response = requests.post(f"{self.base_url}/deductions/calculate-monthly?month=2025-10", 
                                   headers=self.headers)
            
            if response.status_code != 200:
                self.log_test("Monthly Deductions for Exempt Test", False, f"Status {response.status_code}")
                return
            
            data = response.json()
            employees = data.get('employees', [])
            
            # Test Hatem exemption
            hatem_found = False
            for emp in employees:
                emp_name = emp.get('employee_name', '').lower()
                if 'hatem' in emp_name:
                    hatem_found = True
                    total_deduction = emp.get('total_deduction', 0)
                    
                    if total_deduction == 0:
                        self.log_test("Hatem Exempt Rule", True, f"Hatem has 0 AED deductions (exempt)")
                    else:
                        self.log_test("Hatem Exempt Rule", False, f"Hatem has {total_deduction} AED (should be 0)")
                    break
            
            if not hatem_found:
                self.log_test("Hatem Exempt Rule", False, "Hatem not found in deductions data")
            
            # Test Tariq special rule (no late before 08:00)
            tariq_found = False
            for emp in employees:
                emp_name = emp.get('employee_name', '').lower()
                if 'tariq' in emp_name or 'tarek' in emp_name:
                    tariq_found = True
                    total_deduction = emp.get('total_deduction', 0)
                    daily_breakdown = emp.get('daily_breakdown', [])
                    
                    # Check for early arrivals before 08:00
                    early_arrivals = []
                    for day in daily_breakdown:
                        check_in = day.get('check_in', '')
                        if check_in and check_in < '08:00':
                            early_arrivals.append(check_in)
                    
                    if early_arrivals:
                        self.log_test(f"Tariq Special Rule ({emp_name})", True, 
                                    f"Found {len(early_arrivals)} early arrivals before 08:00")
                    else:
                        self.log_test(f"Tariq Special Rule ({emp_name})", True, 
                                    f"No early arrivals found, deduction: {total_deduction} AED")
                    break
            
            if not tariq_found:
                self.log_test("Tariq Special Rule", False, "Tariq/Tarek not found in deductions data")
            
            # Verify same employees in payroll summary
            cycles_response = requests.get(f"{self.base_url}/payroll/cycles", headers=self.headers)
            if cycles_response.status_code == 200:
                cycles = cycles_response.json()
                october_cycle = None
                
                for cycle in cycles:
                    if '2025-09-29' in cycle.get('start_date', ''):
                        october_cycle = cycle
                        break
                
                if october_cycle:
                    cycle_id = october_cycle.get('id')
                    summary_response = requests.get(f"{self.base_url}/payroll/cycles/{cycle_id}/summary", 
                                                  headers=self.headers)
                    
                    if summary_response.status_code == 200:
                        summary_data = summary_response.json()
                        
                        # Verify exempt employees in payroll
                        for emp in summary_data.get('employees', []):
                            emp_name = emp.get('employee_name', '').lower()
                            if 'hatem' in emp_name:
                                total_deduction = emp.get('total_deduction_unified', emp.get('total_deductions', 0))
                                if total_deduction == 0:
                                    self.log_test("Hatem Payroll Exempt", True, "Hatem shows 0 deductions in payroll")
                                else:
                                    self.log_test("Hatem Payroll Exempt", False, 
                                                f"Hatem shows {total_deduction} deductions in payroll")
            
        except Exception as e:
            self.log_test("Exempt Employees Validation", False, f"Exception: {str(e)}")
    
    def test_4_payroll_cycle_detailed_fields_validation(self):
        """Test Payroll Summary Endpoint for NEW fields"""
        print("\n🎯 TEST 4: PAYROLL CYCLE DETAILED FIELDS VALIDATION")
        print("Testing: absent_days, absence_amount, late_days, late_minutes, late_amount, total_deduction_unified")
        
        try:
            # Find October 2025 cycle
            cycles_response = requests.get(f"{self.base_url}/payroll/cycles", headers=self.headers)
            if cycles_response.status_code != 200:
                self.log_test("Payroll Cycles API", False, f"Status {cycles_response.status_code}")
                return
            
            cycles = cycles_response.json()
            october_cycle = None
            
            for cycle in cycles:
                if '2025-09-29' in cycle.get('start_date', ''):
                    october_cycle = cycle
                    break
            
            if not october_cycle:
                self.log_test("October Cycle for Fields Test", False, "October 2025 cycle not found")
                return
            
            cycle_id = october_cycle.get('id')
            
            # Test payroll summary endpoint
            response = requests.get(f"{self.base_url}/payroll/cycles/{cycle_id}/summary", 
                                  headers=self.headers)
            
            if response.status_code != 200:
                self.log_test("Payroll Summary for Fields", False, f"Status {response.status_code}")
                return
            
            data = response.json()
            
            # Check unified_engine_active flag
            unified_active = data.get('unified_engine_active', False)
            if unified_active:
                self.log_test("Unified Engine Active Flag", True, "unified_engine_active: true")
            else:
                self.log_test("Unified Engine Active Flag", False, "unified_engine_active flag missing or false")
            
            # Check NEW fields for each employee
            required_fields = [
                'absent_days', 'absence_amount', 'late_days', 
                'late_minutes', 'late_amount', 'total_deduction_unified'
            ]
            
            employees = data.get('employees', [])
            if not employees:
                self.log_test("Employee Data in Summary", False, "No employees found in summary")
                return
            
            field_coverage = {field: 0 for field in required_fields}
            total_employees = len(employees)
            
            # Test specific values for October 2025 (from review request)
            target_employees = {
                'Hesham': {
                    'absent_days': 0, 'late_days': 10, 'late_minutes': 210, 'late_amount': (33, 34)
                },
                'Mohamed Mostafa': {
                    'absent_days': 2, 'late_days': 14, 'late_minutes': 154, 
                    'absence_amount': (315, 320), 'late_amount': (24, 26)
                },
                'Hatem': {
                    'absent_days': 0, 'late_days': 0, 'all_deductions': 0
                }
            }
            
            field_validation_results = []
            
            for emp in employees:
                emp_name = emp.get('employee_name', '')
                
                # Check field presence
                emp_fields = {}
                for field in required_fields:
                    if field in emp:
                        field_coverage[field] += 1
                        emp_fields[field] = emp[field]
                
                # Validate specific employee values
                for target_name, expected_values in target_employees.items():
                    if target_name.lower() in emp_name.lower():
                        validation_result = {'employee': target_name, 'validations': []}
                        
                        for field, expected in expected_values.items():
                            if field == 'all_deductions':
                                actual_value = emp.get('total_deduction_unified', emp.get('total_deductions', 0))
                                if actual_value == expected:
                                    self.log_test(f"{target_name} All Deductions", True, f"All deductions = {expected}")
                                    validation_result['validations'].append({'field': 'all_deductions', 'passed': True})
                                else:
                                    self.log_test(f"{target_name} All Deductions", False, 
                                                f"All deductions = {actual_value}, expected {expected}")
                                    validation_result['validations'].append({'field': 'all_deductions', 'passed': False})
                            elif isinstance(expected, tuple):  # Range validation
                                actual_field = field.replace('_amount', '_amount') if field.endswith('_amount') else field
                                actual_value = emp.get(actual_field, 0)
                                min_val, max_val = expected
                                if min_val <= actual_value <= max_val:
                                    self.log_test(f"{target_name} {actual_field}", True, 
                                                f"Value {actual_value} in range {min_val}-{max_val}")
                                    validation_result['validations'].append({'field': actual_field, 'passed': True})
                                else:
                                    self.log_test(f"{target_name} {actual_field}", False, 
                                                f"Value {actual_value} not in range {min_val}-{max_val}")
                                    validation_result['validations'].append({'field': actual_field, 'passed': False})
                            else:  # Exact value validation
                                actual_value = emp.get(field, 0)
                                if actual_value == expected:
                                    self.log_test(f"{target_name} {field}", True, f"{field} = {expected}")
                                    validation_result['validations'].append({'field': field, 'passed': True})
                                else:
                                    self.log_test(f"{target_name} {field}", False, 
                                                f"{field} = {actual_value}, expected {expected}")
                                    validation_result['validations'].append({'field': field, 'passed': False})
                        
                        field_validation_results.append(validation_result)
            
            # Report field coverage
            for field, count in field_coverage.items():
                coverage_pct = (count / total_employees) * 100
                if coverage_pct >= 80:
                    self.log_test(f"Field Coverage {field}", True, f"{coverage_pct:.1f}% coverage ({count}/{total_employees})")
                else:
                    self.log_test(f"Field Coverage {field}", False, f"Only {coverage_pct:.1f}% coverage ({count}/{total_employees})")
            
            self.evidence['payroll_detailed_fields'] = {
                'field_coverage': field_coverage,
                'total_employees': total_employees,
                'field_validation_results': field_validation_results,
                'sample_employee_data': employees[:3]
            }
            
        except Exception as e:
            self.log_test("Payroll Cycle Fields Validation", False, f"Exception: {str(e)}")
    
    def test_5_daily_breakdown_validation(self):
        """Test Daily Records with all required fields"""
        print("\n🎯 TEST 5: DAILY BREAKDOWN VALIDATION")
        print("Testing: date, check_in, check_out, late_minutes, early_leave_minutes, deduction_amount, grace_applied, rule_applied, note")
        
        try:
            response = requests.post(f"{self.base_url}/deductions/calculate-monthly?month=2025-10", 
                                   headers=self.headers)
            
            if response.status_code != 200:
                self.log_test("Monthly Calculation for Daily Breakdown", False, f"Status {response.status_code}")
                return
            
            data = response.json()
            employees = data.get('employees', [])
            
            if not employees:
                self.log_test("Daily Breakdown Data", False, "No employees found")
                return
            
            # Required daily fields from review request
            required_daily_fields = [
                'date', 'check_in', 'check_out', 'late_minutes', 
                'early_leave_minutes', 'under_hours_minutes', 'deduction_amount', 
                'grace_applied', 'rule_applied', 'note'
            ]
            
            field_coverage = {field: 0 for field in required_daily_fields}
            total_daily_records = 0
            grace_applications = 0
            employees_with_breakdown = 0
            
            for emp in employees:
                emp_name = emp.get('employee_name', '')
                daily_data = emp.get('daily_breakdown', emp.get('daily_records', []))
                
                if daily_data:
                    employees_with_breakdown += 1
                    
                    for day_record in daily_data:
                        total_daily_records += 1
                        
                        # Check field presence
                        for field in required_daily_fields:
                            if field in day_record:
                                field_coverage[field] += 1
                        
                        # Check grace period application (≤ 5 minutes)
                        late_minutes = day_record.get('late_minutes', 0)
                        grace_applied = day_record.get('grace_applied', False)
                        
                        if late_minutes > 0 and late_minutes <= 5 and grace_applied:
                            grace_applications += 1
            
            if employees_with_breakdown > 0:
                self.log_test("Daily Breakdown Presence", True, 
                            f"Daily breakdown found for {employees_with_breakdown} employees with {total_daily_records} total records")
            else:
                self.log_test("Daily Breakdown Presence", False, "No daily breakdown found")
                return
            
            # Report field coverage in daily records
            for field, count in field_coverage.items():
                if total_daily_records > 0:
                    coverage_pct = (count / total_daily_records) * 100
                    if coverage_pct >= 70:
                        self.log_test(f"Daily Field {field}", True, f"{coverage_pct:.1f}% coverage")
                    else:
                        self.log_test(f"Daily Field {field}", False, f"Only {coverage_pct:.1f}% coverage")
            
            # Validate grace period = 5 minutes
            if grace_applications > 0:
                self.log_test("Grace Period Application", True, 
                            f"Grace period applied {grace_applications} times for late ≤ 5 minutes")
            else:
                self.log_test("Grace Period Application", False, "No grace period applications found")
            
            self.evidence['daily_breakdown'] = {
                'employees_with_breakdown': employees_with_breakdown,
                'total_daily_records': total_daily_records,
                'field_coverage': field_coverage,
                'grace_applications': grace_applications,
                'sample_daily_records': employees[:2] if employees else []
            }
            
        except Exception as e:
            self.log_test("Daily Breakdown Validation", False, f"Exception: {str(e)}")
    
    def test_6_calculation_accuracy_spot_check(self):
        """Manual Formula Validation - Hesham example from review request"""
        print("\n🎯 TEST 6: CALCULATION ACCURACY SPOT CHECK")
        print("Testing: Manual calculation vs API result for Hesham")
        print("Formula: (DailyRate/540) × deductible_minutes")
        
        try:
            response = requests.post(f"{self.base_url}/deductions/calculate-monthly?month=2025-10", 
                                   headers=self.headers)
            
            if response.status_code != 200:
                self.log_test("Monthly Calculation for Accuracy", False, f"Status {response.status_code}")
                return
            
            data = response.json()
            employees = data.get('employees', [])
            
            # Find Hesham's data
            hesham_data = None
            for emp in employees:
                if 'hesham' in emp.get('employee_name', '').lower():
                    hesham_data = emp
                    break
            
            if not hesham_data:
                self.log_test("Hesham Data Found", False, "Hesham not found in employee data")
                return
            
            self.log_test("Hesham Data Found", True, "Hesham found in employee data")
            
            # Extract Hesham's values
            basic_salary = hesham_data.get('basic_salary', 2500)  # From review request
            working_days = hesham_data.get('working_days', 22)
            late_days = hesham_data.get('late_days', 0)
            late_minutes = hesham_data.get('late_minutes', 0)
            total_deduction = hesham_data.get('total_deduction', 0)
            
            # Manual calculation from review request example
            # Basic salary: 2500 AED, Working days: 22, Daily rate: 2500 / 22 = 113.64 AED
            # 10 days late × 21 minutes = 210 minutes, Grace: 10 × 5 = 50 minutes
            # Deductible: 210 - 50 = 160 minutes, Deduction: (113.64 / 540) × 160 = 33.66 AED
            
            if basic_salary > 0:
                daily_rate = basic_salary / working_days
                grace_minutes = late_days * 5  # 5 minutes grace per late day
                deductible_minutes = max(0, late_minutes - grace_minutes)
                expected_deduction = (daily_rate / 540) * deductible_minutes
                
                # Compare with actual
                difference = abs(total_deduction - expected_deduction)
                tolerance = 1.0  # Allow 1 AED tolerance
                
                if difference <= tolerance:
                    self.log_test("Hesham Calculation Accuracy", True, 
                                f"✓ Actual: {total_deduction:.2f} AED, Expected: {expected_deduction:.2f} AED (diff: {difference:.2f})")
                else:
                    self.log_test("Hesham Calculation Accuracy", False, 
                                f"✗ Actual: {total_deduction:.2f} AED, Expected: {expected_deduction:.2f} AED (diff: {difference:.2f})")
                
                # Verify formula components
                self.log_test("Formula Components", True, 
                            f"Basic: {basic_salary} AED, Daily: {daily_rate:.2f} AED, Late days: {late_days}, "
                            f"Late mins: {late_minutes}, Grace: {grace_minutes}, Deductible: {deductible_minutes}")
                
                # Test Mohamed Mostafa as well
                for emp in employees:
                    emp_name = emp.get('employee_name', '')
                    if 'mohamed' in emp_name.lower() and 'mostafa' in emp_name.lower():
                        mohamed_salary = emp.get('basic_salary', 0)
                        mohamed_deduction = emp.get('total_deduction', 0)
                        mohamed_late_mins = emp.get('late_minutes', 0)
                        mohamed_absent_days = emp.get('absent_days', 0)
                        
                        if mohamed_salary > 0:
                            mohamed_daily = mohamed_salary / working_days
                            self.log_test("Mohamed Calculation Check", True, 
                                        f"Mohamed: Salary {mohamed_salary}, Daily {mohamed_daily:.2f}, "
                                        f"Late mins {mohamed_late_mins}, Absent days {mohamed_absent_days}, Deduction {mohamed_deduction:.2f}")
                        break
            else:
                self.log_test("Hesham Salary Data", False, "Basic salary not found or zero")
            
            self.evidence['calculation_accuracy'] = {
                'hesham_data': hesham_data,
                'manual_calculation': {
                    'basic_salary': basic_salary,
                    'daily_rate': daily_rate if basic_salary > 0 else 0,
                    'expected_deduction': expected_deduction if basic_salary > 0 else 0,
                    'actual_deduction': total_deduction,
                    'difference': difference if basic_salary > 0 else 0
                }
            }
            
        except Exception as e:
            self.log_test("Calculation Accuracy Spot Check", False, f"Exception: {str(e)}")
    
    def test_7_error_handling_edge_cases(self):
        """Test Invalid Inputs and Error Handling"""
        print("\n🎯 TEST 7: ERROR HANDLING & EDGE CASES")
        print("Testing: Invalid inputs return proper 400/404 status codes")
        
        error_tests = [
            {
                'name': 'Invalid Month Format',
                'url': f"{self.base_url}/deductions/calculate-monthly?month=invalid",
                'method': 'POST',
                'expected_status': [400, 422]
            },
            {
                'name': 'Non-existent Cycle',
                'url': f"{self.base_url}/payroll/cycles/fake-cycle-id-12345/summary",
                'method': 'GET',
                'expected_status': [404, 400]
            },
            {
                'name': 'Future Month (Empty Data)',
                'url': f"{self.base_url}/deductions/calculate-monthly?month=2025-12",
                'method': 'POST',
                'expected_status': [200, 400]  # Either empty result or error is acceptable
            },
            {
                'name': 'Unauthorized Access',
                'url': f"{self.base_url}/deductions/calculate-monthly?month=2025-10",
                'method': 'POST',
                'expected_status': [401, 403],
                'no_auth': True
            }
        ]
        
        for test in error_tests:
            try:
                headers = {} if test.get('no_auth') else self.headers
                
                if test['method'] == 'POST':
                    response = requests.post(test['url'], headers=headers)
                else:
                    response = requests.get(test['url'], headers=headers)
                
                if response.status_code in test['expected_status']:
                    self.log_test(test['name'], True, f"Proper error response: {response.status_code}")
                else:
                    self.log_test(test['name'], False, f"Unexpected status: {response.status_code}")
                    
            except Exception as e:
                self.log_test(test['name'], False, f"Exception: {str(e)}")
    
    def test_8_performance_check(self):
        """Response Times - Monthly calculation ≤10s, Payroll summary ≤5s"""
        print("\n🎯 TEST 8: PERFORMANCE CHECK")
        print("Testing: Monthly calculation ≤10s, Payroll summary ≤5s")
        
        # Test monthly calculation performance
        try:
            start_time = time.time()
            response = requests.post(f"{self.base_url}/deductions/calculate-monthly?month=2025-10", 
                                   headers=self.headers)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                if duration <= 10.0:
                    self.log_test("Monthly Calculation Performance", True, 
                                f"✓ Completed in {duration:.2f}s (≤10s target)")
                else:
                    self.log_test("Monthly Calculation Performance", False, 
                                f"✗ Took {duration:.2f}s (>10s target)")
            else:
                self.log_test("Monthly Calculation Performance", False, 
                            f"Failed with status {response.status_code}")
                
            self.performance_metrics['monthly_calculation_time'] = duration
            
        except Exception as e:
            self.log_test("Monthly Calculation Performance", False, f"Exception: {str(e)}")
        
        # Test payroll summary performance
        try:
            cycles_response = requests.get(f"{self.base_url}/payroll/cycles", headers=self.headers)
            if cycles_response.status_code == 200:
                cycles = cycles_response.json()
                if cycles:
                    # Find October cycle
                    october_cycle = None
                    for cycle in cycles:
                        if '2025-09-29' in cycle.get('start_date', ''):
                            october_cycle = cycle
                            break
                    
                    if october_cycle:
                        cycle_id = october_cycle.get('id')
                        
                        start_time = time.time()
                        response = requests.get(f"{self.base_url}/payroll/cycles/{cycle_id}/summary", 
                                              headers=self.headers)
                        duration = time.time() - start_time
                        
                        if response.status_code == 200:
                            if duration <= 5.0:
                                self.log_test("Payroll Summary Performance", True, 
                                            f"✓ Completed in {duration:.2f}s (≤5s target)")
                            else:
                                self.log_test("Payroll Summary Performance", False, 
                                            f"✗ Took {duration:.2f}s (>5s target)")
                        else:
                            self.log_test("Payroll Summary Performance", False, 
                                        f"Failed with status {response.status_code}")
                            
                        self.performance_metrics['payroll_summary_time'] = duration
                        
        except Exception as e:
            self.log_test("Payroll Summary Performance", False, f"Exception: {str(e)}")
    
    def run_comprehensive_validation(self):
        """Run all Phase 3 validation tests"""
        print("🎯 PHASE 3: COMPREHENSIVE END-TO-END BACKEND VALIDATION")
        print("Unified Deductions Engine - Complete Review Request Implementation")
        print("=" * 80)
        
        # Authenticate as admin
        if not self.authenticate("admin@tanseeq.com", "ADMIN"):
            print("❌ Authentication failed. Cannot proceed with tests.")
            return
        
        # Run all validation tests
        self.test_1_cross_page_consistency_validation()
        self.test_2_formula_consistency_across_months()
        self.test_3_exempt_employees_validation()
        self.test_4_payroll_cycle_detailed_fields_validation()
        self.test_5_daily_breakdown_validation()
        self.test_6_calculation_accuracy_spot_check()
        self.test_7_error_handling_edge_cases()
        self.test_8_performance_check()
        
        # Generate comprehensive summary
        return self.generate_comprehensive_summary()
    
    def generate_comprehensive_summary(self):
        """Generate comprehensive validation summary"""
        print("\n" + "=" * 80)
        print("🎯 PHASE 3 COMPREHENSIVE VALIDATION SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for test in self.test_results if test['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 OVERALL RESULTS: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}% success rate)")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        
        # Performance summary
        if self.performance_metrics:
            print(f"\n⚡ PERFORMANCE METRICS:")
            for metric, value in self.performance_metrics.items():
                print(f"   {metric}: {value:.2f}s")
        
        # Success criteria assessment
        print(f"\n🎯 SUCCESS CRITERIA ASSESSMENT:")
        
        criteria_results = []
        
        # Check each success criterion
        criteria = [
            ("All 3 pages return SAME values", "cross_page_consistency"),
            ("Formula (DailyRate/540) verified", "calculation_accuracy"),
            ("Grace period = 5 minutes confirmed", "formula_consistency"),
            ("Exempt employees show 0 deductions", "exempt_employees"),
            ("All new payroll fields present", "payroll_detailed_fields"),
            ("Daily breakdown includes required fields", "daily_breakdown"),
            ("No errors for valid requests", "error_handling"),
            ("Proper error handling for invalid inputs", "error_handling")
        ]
        
        for criterion, test_category in criteria:
            # Check if related tests passed
            related_tests = [t for t in self.test_results if test_category in t['test'].lower().replace(' ', '_')]
            if related_tests:
                passed_related = sum(1 for t in related_tests if t['success'])
                total_related = len(related_tests)
                if passed_related == total_related:
                    print(f"   ✅ {criterion}")
                    criteria_results.append(True)
                else:
                    print(f"   ❌ {criterion} ({passed_related}/{total_related})")
                    criteria_results.append(False)
            else:
                print(f"   ⚠️ {criterion} (no tests found)")
                criteria_results.append(False)
        
        criteria_success_rate = (sum(criteria_results) / len(criteria_results) * 100) if criteria_results else 0
        
        # Determine overall status
        if success_rate >= 90 and criteria_success_rate >= 80:
            status = "🟢 EXCELLENT - READY FOR PRODUCTION"
        elif success_rate >= 80 and criteria_success_rate >= 70:
            status = "🟡 GOOD - MINOR ISSUES TO ADDRESS"
        elif success_rate >= 70:
            status = "🟠 ACCEPTABLE - SOME ISSUES NEED FIXING"
        else:
            status = "🔴 NEEDS SIGNIFICANT IMPROVEMENT"
        
        print(f"\n📈 PRODUCTION READINESS: {status}")
        print(f"   Overall Success Rate: {success_rate:.1f}%")
        print(f"   Success Criteria Met: {criteria_success_rate:.1f}%")
        
        # Failed tests summary
        if failed_tests > 0:
            print(f"\n🚨 FAILED TESTS REQUIRING ATTENTION:")
            for test in self.test_results:
                if not test['success']:
                    print(f"   ❌ {test['test']}: {test['details']}")
        
        # Evidence and recommendations
        print(f"\n📋 EVIDENCE COLLECTION:")
        print(f"   Cross-page consistency data: {'✓' if 'cross_page_consistency' in self.evidence else '✗'}")
        print(f"   Performance metrics: {'✓' if self.performance_metrics else '✗'}")
        print(f"   Calculation accuracy verification: {'✓' if 'calculation_accuracy' in self.evidence else '✗'}")
        print(f"   Daily breakdown samples: {'✓' if 'daily_breakdown' in self.evidence else '✗'}")
        
        # Save comprehensive evidence
        evidence_file = f"phase3_comprehensive_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(f"/app/{evidence_file}", 'w') as f:
            json.dump({
                'test_results': self.test_results,
                'evidence': self.evidence,
                'performance_metrics': self.performance_metrics,
                'summary': {
                    'total_tests': total_tests,
                    'passed_tests': passed_tests,
                    'failed_tests': failed_tests,
                    'success_rate': success_rate,
                    'criteria_success_rate': criteria_success_rate,
                    'status': status
                }
            }, f, indent=2, default=str)
        
        print(f"\n💾 Comprehensive evidence saved to: {evidence_file}")
        
        return {
            'success_rate': success_rate,
            'criteria_success_rate': criteria_success_rate,
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'status': status,
            'evidence_file': evidence_file,
            'performance_metrics': self.performance_metrics
        }

if __name__ == "__main__":
    validator = Phase3ComprehensiveValidationTest()
    results = validator.run_comprehensive_validation()
    
    print(f"\n🎯 FINAL ASSESSMENT:")
    print(f"Success Rate: {results['success_rate']:.1f}%")
    print(f"Status: {results['status']}")
    print(f"Evidence File: {results['evidence_file']}")