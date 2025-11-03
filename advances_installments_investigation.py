#!/usr/bin/env python3
"""
فحص بيانات السُلف وجدول الأقساط لـ Mohamed Mostafa
Investigation of advances and installment schedules for Mohamed Mostafa
"""

import requests
import json
from datetime import datetime
import sys

# Configuration
BACKEND_URL = "https://attend-deduct-hr.preview.emergentagent.com/api"
SUPER_ADMIN_CREDENTIALS = {
    "email": "admin@tanseeq.com",
    "password": "ADMIN"
}

class AdvancesInstallmentsInvestigator:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.mohamed_id = None
        self.results = {
            "authentication": False,
            "mohamed_found": False,
            "advances_count": 0,
            "advances_data": [],
            "installment_schedules": [],
            "monthly_installments": [],
            "payroll_ledger_entries": [],
            "october_2025_installments": [],
            "findings": []
        }
    
    def authenticate(self):
        """Authenticate as Super Admin"""
        try:
            print("🔐 Authenticating as Super Admin...")
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=SUPER_ADMIN_CREDENTIALS,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.session.headers.update({
                    "Authorization": f"Bearer {self.token}"
                })
                self.results["authentication"] = True
                print("✅ Authentication successful")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def find_mohamed_mostafa(self):
        """Find Mohamed Mostafa's employee ID"""
        try:
            print("🔍 Searching for Mohamed Mostafa...")
            
            # Try different employee endpoints
            endpoints_to_try = [
                "/employees/list",
                "/employees",
                "/users",
                "/advances/admin/all-balances"  # This might have employee data
            ]
            
            employees = []
            
            for endpoint in endpoints_to_try:
                try:
                    response = self.session.get(f"{BACKEND_URL}{endpoint}", timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        print(f"✅ Successfully got data from {endpoint}")
                        
                        # Handle different response formats
                        if isinstance(data, list):
                            employees = data
                        elif isinstance(data, dict):
                            if "employees" in data:
                                employees = data["employees"]
                            elif "employee_balances" in data:
                                employees = data["employee_balances"]
                            elif "users" in data:
                                employees = data["users"]
                            else:
                                employees = [data]  # Single employee object
                        
                        if employees:
                            break
                            
                except Exception as e:
                    print(f"⚠️ Endpoint {endpoint} failed: {e}")
                    continue
            
            if not employees:
                print("❌ Could not retrieve employee data from any endpoint")
                return False
            
            print(f"✅ Retrieved {len(employees)} employee records")
            
            # Search for Mohamed Mostafa (various name variations)
            mohamed_variations = [
                "mohamed mostafa", "محمد مصطفى", "mohamed", "mostafa",
                "Mohamed Mostafa", "MOHAMED MOSTAFA", "محمد", "مصطفى"
            ]
            
            for employee in employees:
                if isinstance(employee, dict):
                    employee_name = employee.get("name", employee.get("employee_name", "")).lower()
                    employee_id = employee.get("id", employee.get("employee_id", ""))
                    
                    for variation in mohamed_variations:
                        if variation.lower() in employee_name:
                            self.mohamed_id = employee_id
                            self.results["mohamed_found"] = True
                            print(f"✅ Found Mohamed Mostafa: ID = {self.mohamed_id}, Name = {employee.get('name', employee.get('employee_name'))}")
                            return True
            
            print("❌ Mohamed Mostafa not found in employee list")
            print("Available employees (first 10):")
            for i, emp in enumerate(employees[:10]):
                if isinstance(emp, dict):
                    name = emp.get("name", emp.get("employee_name", "Unknown"))
                    emp_id = emp.get("id", emp.get("employee_id", "Unknown"))
                    print(f"  {i+1}. {name} (ID: {emp_id})")
            
            return False
                
        except Exception as e:
            print(f"❌ Error finding Mohamed Mostafa: {e}")
            return False
    
    def get_advances_data(self):
        """1. جلب بيانات السُلف لـ Mohamed Mostafa"""
        try:
            print(f"📊 Getting advances data for Mohamed Mostafa (ID: {self.mohamed_id})...")
            
            # Try different endpoints to get advances data
            endpoints_to_try = [
                f"/advances?employee_id={self.mohamed_id}",
                f"/advances/my-transactions",  # If we can impersonate
                f"/advances/admin/all-transactions?employee_id={self.mohamed_id}",
                f"/advances/admin/all-transactions"
            ]
            
            advances = []
            
            for endpoint in endpoints_to_try:
                try:
                    response = self.session.get(f"{BACKEND_URL}{endpoint}", timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        print(f"✅ Successfully got data from {endpoint}")
                        
                        # Handle different response formats
                        if isinstance(data, list):
                            advances = data
                        elif isinstance(data, dict):
                            if "transactions" in data:
                                advances = data["transactions"]
                            elif "advances" in data:
                                advances = data["advances"]
                        
                        # Filter for Mohamed Mostafa if we got all transactions
                        if endpoint.endswith("all-transactions") and not endpoint.endswith(f"employee_id={self.mohamed_id}"):
                            advances = [adv for adv in advances if adv.get("employee_id") == self.mohamed_id]
                        
                        if advances:
                            break
                            
                except Exception as e:
                    print(f"⚠️ Endpoint {endpoint} failed: {e}")
                    continue
            
            self.results["advances_count"] = len(advances)
            self.results["advances_data"] = advances
            
            print(f"✅ Found {len(advances)} advances for Mohamed Mostafa")
            
            if advances:
                for i, advance in enumerate(advances, 1):
                    print(f"  Advance {i}:")
                    print(f"    - ID: {advance.get('id')}")
                    print(f"    - Type: {advance.get('transaction_type')} ({advance.get('transaction_type_ar', '')})")
                    print(f"    - Amount: {advance.get('amount')} AED")
                    print(f"    - Status: {advance.get('status')} ({advance.get('status_ar', '')})")
                    print(f"    - Created: {advance.get('created_at_display', advance.get('created_at'))}")
            else:
                print("⚠️ No advances found for Mohamed Mostafa")
            
            return True
                
        except Exception as e:
            print(f"❌ Error getting advances data: {e}")
            return False
    
    def get_installment_schedules(self):
        """2. جلب جدول الأقساط للسُلف"""
        try:
            print("📅 Getting installment schedules for advances...")
            
            for advance in self.results["advances_data"]:
                advance_id = advance.get("id")
                if not advance_id:
                    continue
                
                print(f"  Checking installments for advance {advance_id}...")
                
                response = self.session.get(
                    f"{BACKEND_URL}/advances/{advance_id}/installments",
                    timeout=30
                )
                
                if response.status_code == 200:
                    installments_data = response.json()
                    
                    if installments_data:
                        self.results["installment_schedules"].append({
                            "advance_id": advance_id,
                            "advance_amount": advance.get("amount"),
                            "installments": installments_data
                        })
                        
                        print(f"    ✅ Found installment schedule")
                        
                        # Check for October 2025 installments
                        installments = installments_data.get("installments", [])
                        for installment in installments:
                            due_date = installment.get("due_date", "")
                            status = installment.get("status", "")
                            amount = installment.get("amount", 0)
                            
                            print(f"      - Due Date: {due_date}, Status: {status}, Amount: {amount} AED")
                            
                            if due_date.startswith("2025-10"):
                                self.results["october_2025_installments"].append({
                                    "advance_id": advance_id,
                                    "installment": installment
                                })
                                print(f"        🎯 OCTOBER 2025 INSTALLMENT FOUND!")
                    else:
                        print(f"    ⚠️ No installment schedule found")
                        
                elif response.status_code == 404:
                    print(f"    ⚠️ No installments found for advance {advance_id}")
                else:
                    print(f"    ❌ Error getting installments: {response.status_code} - {response.text}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error getting installment schedules: {e}")
            return False
    
    def get_monthly_installments(self):
        """3. جلب الأقساط حسب الشهر"""
        try:
            print("📊 Getting monthly installment schedules...")
            
            response = self.session.get(
                f"{BACKEND_URL}/payroll/installment-schedules",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                schedules = data.get("schedules", []) if isinstance(data, dict) else data
                
                self.results["monthly_installments"] = schedules
                
                print(f"✅ Found {len(schedules)} installment schedules")
                
                # Look for Mohamed Mostafa
                mohamed_schedules = []
                for schedule in schedules:
                    if schedule.get("employee_id") == self.mohamed_id:
                        mohamed_schedules.append(schedule)
                
                if mohamed_schedules:
                    print(f"✅ Found {len(mohamed_schedules)} schedules for Mohamed Mostafa:")
                    for schedule in mohamed_schedules:
                        print(f"  - Schedule ID: {schedule.get('id')}")
                        print(f"  - Employee: {schedule.get('employee_name')}")
                        print(f"  - Advance ID: {schedule.get('advance_id')}")
                        print(f"  - Total Amount: {schedule.get('total_amount')} AED")
                        print(f"  - Installments: {schedule.get('number_of_installments')}")
                        
                        # Check dates
                        installments = schedule.get("installments", [])
                        for inst in installments:
                            due_date = inst.get("due_date", "")
                            if due_date.startswith("2025-10"):
                                print(f"    🎯 OCTOBER 2025 INSTALLMENT: {due_date} - {inst.get('amount')} AED - Status: {inst.get('status')}")
                else:
                    print("⚠️ No installment schedules found for Mohamed Mostafa")
                
                return True
                
            else:
                print(f"❌ Failed to get monthly installments: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error getting monthly installments: {e}")
            return False
    
    def check_payroll_ledger(self):
        """4. فحص القيود في Payroll Ledger"""
        try:
            print("📋 Checking Payroll Ledger for October 2025...")
            
            # First, get payroll cycles to find October 2025
            response = self.session.get(f"{BACKEND_URL}/payroll/cycles", timeout=30)
            
            if response.status_code == 200:
                cycles = response.json()
                
                october_cycle = None
                for cycle in cycles:
                    cycle_period = cycle.get("period", "")
                    if "2025-10" in cycle_period or "October 2025" in cycle_period:
                        october_cycle = cycle
                        break
                
                if october_cycle:
                    cycle_id = october_cycle["id"]
                    print(f"✅ Found October 2025 payroll cycle: {cycle_id}")
                    
                    # Get ledger for Mohamed Mostafa
                    ledger_response = self.session.get(
                        f"{BACKEND_URL}/payroll/cycles/{cycle_id}/ledger/employees/{self.mohamed_id}",
                        timeout=30
                    )
                    
                    if ledger_response.status_code == 200:
                        ledger_data = ledger_response.json()
                        self.results["payroll_ledger_entries"] = ledger_data
                        
                        print("✅ Payroll ledger retrieved successfully")
                        
                        # Look for ADVANCE_INSTALLMENT entries
                        entries = ledger_data.get("entries", []) if isinstance(ledger_data, dict) else ledger_data
                        advance_installment_entries = []
                        
                        for entry in entries:
                            entry_type = entry.get("type", "")
                            if "ADVANCE" in entry_type.upper() or "INSTALLMENT" in entry_type.upper():
                                advance_installment_entries.append(entry)
                                print(f"  🎯 ADVANCE/INSTALLMENT ENTRY FOUND:")
                                print(f"    - Type: {entry_type}")
                                print(f"    - Amount: {entry.get('amount', 0)} AED")
                                print(f"    - Description: {entry.get('description', '')}")
                        
                        if not advance_installment_entries:
                            print("⚠️ NO ADVANCE_INSTALLMENT entries found in payroll ledger")
                            self.results["findings"].append("NO ADVANCE_INSTALLMENT entries found in October 2025 payroll ledger")
                        
                        return True
                        
                    else:
                        print(f"❌ Failed to get payroll ledger: {ledger_response.status_code} - {ledger_response.text}")
                        return False
                        
                else:
                    print("⚠️ October 2025 payroll cycle not found")
                    print("Available cycles:")
                    for cycle in cycles[:5]:
                        print(f"  - {cycle.get('period', 'Unknown')} (ID: {cycle.get('id')})")
                    return False
                    
            else:
                print(f"❌ Failed to get payroll cycles: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error checking payroll ledger: {e}")
            return False
    
    def generate_report(self):
        """Generate investigation report"""
        print("\n" + "="*80)
        print("📊 INVESTIGATION REPORT - تقرير التحقيق")
        print("="*80)
        
        print(f"🔍 Investigation Target: Mohamed Mostafa")
        print(f"📅 Focus Period: October 2025")
        print(f"🎯 Issue: Advance installment deductions not showing in payroll cycle summary")
        
        print("\n📋 FINDINGS - النتائج:")
        print("-" * 40)
        
        print(f"1. Mohamed Mostafa Found: {'✅ Yes' if self.results['mohamed_found'] else '❌ No'}")
        if self.results['mohamed_found']:
            print(f"   Employee ID: {self.mohamed_id}")
        
        print(f"2. Number of Advances: {self.results['advances_count']}")
        
        print(f"3. Installment Schedules Found: {len(self.results['installment_schedules'])}")
        
        print(f"4. October 2025 Installments: {len(self.results['october_2025_installments'])}")
        if self.results['october_2025_installments']:
            for oct_inst in self.results['october_2025_installments']:
                installment = oct_inst['installment']
                print(f"   - Due Date: {installment.get('due_date')}")
                print(f"   - Amount: {installment.get('amount')} AED")
                print(f"   - Status: {installment.get('status')}")
        
        print(f"5. Payroll Ledger Entries: {'✅ Retrieved' if self.results['payroll_ledger_entries'] else '❌ Not Retrieved'}")
        
        print("\n🔍 ROOT CAUSE ANALYSIS:")
        print("-" * 40)
        
        if not self.results['mohamed_found']:
            print("❌ CRITICAL: Mohamed Mostafa not found in employee database")
        elif self.results['advances_count'] == 0:
            print("❌ CRITICAL: No advances found for Mohamed Mostafa")
        elif len(self.results['installment_schedules']) == 0:
            print("❌ CRITICAL: No installment schedules created for advances")
        elif len(self.results['october_2025_installments']) == 0:
            print("❌ CRITICAL: No installments scheduled for October 2025")
        elif not self.results['payroll_ledger_entries']:
            print("❌ CRITICAL: Could not retrieve payroll ledger entries")
        else:
            print("✅ All data retrieved successfully - need to check ledger entries for ADVANCE_INSTALLMENT type")
        
        # Save detailed results
        with open('/app/advances_investigation_results.json', 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n💾 Detailed results saved to: /app/advances_investigation_results.json")
        
        return self.results

def main():
    """Main investigation function"""
    print("🚀 Starting Advances Installments Investigation")
    print("=" * 60)
    
    investigator = AdvancesInstallmentsInvestigator()
    
    # Step 1: Authenticate
    if not investigator.authenticate():
        print("❌ Investigation failed: Could not authenticate")
        return False
    
    # Step 2: Find Mohamed Mostafa
    if not investigator.find_mohamed_mostafa():
        print("❌ Investigation failed: Could not find Mohamed Mostafa")
        return False
    
    # Step 3: Get advances data
    if not investigator.get_advances_data():
        print("❌ Investigation failed: Could not get advances data")
        return False
    
    # Step 4: Get installment schedules
    investigator.get_installment_schedules()
    
    # Step 5: Get monthly installments
    investigator.get_monthly_installments()
    
    # Step 6: Check payroll ledger
    investigator.check_payroll_ledger()
    
    # Step 7: Generate report
    results = investigator.generate_report()
    
    print("\n🎉 Investigation completed successfully!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)