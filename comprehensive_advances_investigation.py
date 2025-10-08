#!/usr/bin/env python3
"""
Comprehensive investigation of advances system and payroll cycles
"""

import requests
import json
from datetime import datetime
import sys

# Configuration
BACKEND_URL = "https://salary-processor-1.preview.emergentagent.com/api"
SUPER_ADMIN_CREDENTIALS = {
    "email": "admin@tanseeq.com",
    "password": "ADMIN"
}

class ComprehensiveAdvancesInvestigator:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        
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
                print("✅ Authentication successful")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def investigate_all_advances(self):
        """Get all advances in the system"""
        try:
            print("📊 Getting ALL advances in the system...")
            
            response = self.session.get(f"{BACKEND_URL}/advances/admin/all-transactions", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                advances = data.get("transactions", []) if isinstance(data, dict) else data
                
                print(f"✅ Found {len(advances)} total advances in system")
                
                if advances:
                    print("\n📋 ALL ADVANCES:")
                    for i, advance in enumerate(advances, 1):
                        print(f"  {i}. Employee: {advance.get('employee_name')} (ID: {advance.get('employee_id')})")
                        print(f"     - Advance ID: {advance.get('id')}")
                        print(f"     - Type: {advance.get('transaction_type')} ({advance.get('transaction_type_ar', '')})")
                        print(f"     - Amount: {advance.get('amount')} AED")
                        print(f"     - Status: {advance.get('status')} ({advance.get('status_ar', '')})")
                        print(f"     - Created: {advance.get('created_at_display', advance.get('created_at'))}")
                        print()
                
                return advances
                
            else:
                print(f"❌ Failed to get advances: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ Error getting advances: {e}")
            return []
    
    def investigate_payroll_cycles(self):
        """Get detailed payroll cycle information"""
        try:
            print("📅 Getting detailed payroll cycle information...")
            
            response = self.session.get(f"{BACKEND_URL}/payroll/cycles", timeout=30)
            
            if response.status_code == 200:
                cycles = response.json()
                
                print(f"✅ Found {len(cycles)} payroll cycles")
                
                print("\n📋 ALL PAYROLL CYCLES:")
                for i, cycle in enumerate(cycles, 1):
                    print(f"  {i}. Cycle ID: {cycle.get('id')}")
                    print(f"     - Period: {cycle.get('period', 'Unknown')}")
                    print(f"     - Month: {cycle.get('month', 'Unknown')}")
                    print(f"     - Year: {cycle.get('year', 'Unknown')}")
                    print(f"     - Status: {cycle.get('status', 'Unknown')}")
                    print(f"     - Created: {cycle.get('created_at', 'Unknown')}")
                    
                    # Check if this is October 2025
                    period = cycle.get('period', '')
                    month = cycle.get('month', '')
                    year = cycle.get('year', '')
                    
                    if ('2025-10' in period or 
                        (month == '10' and str(year) == '2025') or
                        ('October' in period and '2025' in period)):
                        print(f"     🎯 THIS IS OCTOBER 2025 CYCLE!")
                        
                        # Get cycle summary
                        self.get_cycle_summary(cycle.get('id'))
                    
                    print()
                
                return cycles
                
            else:
                print(f"❌ Failed to get payroll cycles: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ Error getting payroll cycles: {e}")
            return []
    
    def get_cycle_summary(self, cycle_id):
        """Get detailed cycle summary"""
        try:
            print(f"    📊 Getting summary for cycle {cycle_id}...")
            
            response = self.session.get(f"{BACKEND_URL}/payroll/cycles/{cycle_id}/summary", timeout=30)
            
            if response.status_code == 200:
                summary = response.json()
                
                print(f"    ✅ Cycle summary retrieved")
                print(f"    - Total Employees: {summary.get('total_employees', 0)}")
                print(f"    - Total Basic Salary: {summary.get('total_basic_salary', 0)} AED")
                print(f"    - Total Deductions: {summary.get('total_deductions', 0)} AED")
                print(f"    - Total Net Salary: {summary.get('total_net_salary', 0)} AED")
                
                # Check for advance deductions specifically
                advance_deductions = summary.get('advance_deductions', 0)
                print(f"    - Advance Deductions: {advance_deductions} AED")
                
                if advance_deductions == 0:
                    print(f"    ⚠️ NO ADVANCE DEDUCTIONS in this cycle!")
                
                return summary
                
            else:
                print(f"    ❌ Failed to get cycle summary: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"    ❌ Error getting cycle summary: {e}")
            return None
    
    def investigate_installment_schedules(self):
        """Get all installment schedules"""
        try:
            print("📅 Getting ALL installment schedules...")
            
            response = self.session.get(f"{BACKEND_URL}/payroll/installment-schedules", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                schedules = data.get("schedules", []) if isinstance(data, dict) else data
                
                print(f"✅ Found {len(schedules)} installment schedules")
                
                if schedules:
                    print("\n📋 ALL INSTALLMENT SCHEDULES:")
                    for i, schedule in enumerate(schedules, 1):
                        print(f"  {i}. Employee: {schedule.get('employee_name')} (ID: {schedule.get('employee_id')})")
                        print(f"     - Schedule ID: {schedule.get('id')}")
                        print(f"     - Advance ID: {schedule.get('advance_id')}")
                        print(f"     - Total Amount: {schedule.get('total_amount')} AED")
                        print(f"     - Installments: {schedule.get('number_of_installments')}")
                        print(f"     - Created: {schedule.get('created_at')}")
                        
                        # Check for October 2025 installments
                        installments = schedule.get("installments", [])
                        october_installments = []
                        for inst in installments:
                            due_date = inst.get("due_date", "")
                            if due_date.startswith("2025-10"):
                                october_installments.append(inst)
                        
                        if october_installments:
                            print(f"     🎯 OCTOBER 2025 INSTALLMENTS:")
                            for oct_inst in october_installments:
                                print(f"       - Due: {oct_inst.get('due_date')}, Amount: {oct_inst.get('amount')} AED, Status: {oct_inst.get('status')}")
                        
                        print()
                
                return schedules
                
            else:
                print(f"❌ Failed to get installment schedules: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ Error getting installment schedules: {e}")
            return []
    
    def create_test_advance_for_mohamed(self):
        """Create a test advance for Mohamed Mostafa to investigate the flow"""
        try:
            print("🧪 Creating test advance for Mohamed Mostafa...")
            
            # First find Mohamed's ID
            response = self.session.get(f"{BACKEND_URL}/employees/list", timeout=30)
            if response.status_code != 200:
                print("❌ Could not get employee list")
                return False
            
            employees = response.json()
            mohamed_id = None
            
            for emp in employees:
                if "mohamed" in emp.get("name", "").lower():
                    mohamed_id = emp["id"]
                    break
            
            if not mohamed_id:
                print("❌ Mohamed Mostafa not found")
                return False
            
            # Create test advance
            advance_data = {
                "employee_id": mohamed_id,
                "transaction_type": "advance",
                "amount": 1000.0,
                "description": "Test advance for investigation",
                "category": "personal",
                "expense_date": "2025-01-15",
                "notes": "Created for testing installment deduction flow"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/advances/create",
                json=advance_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                advance_id = result.get("transaction_id")
                print(f"✅ Test advance created: {advance_id}")
                
                # Now create installment schedule
                self.create_test_installment_schedule(advance_id)
                
                return True
            else:
                print(f"❌ Failed to create test advance: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error creating test advance: {e}")
            return False
    
    def create_test_installment_schedule(self, advance_id):
        """Create test installment schedule"""
        try:
            print(f"📅 Creating test installment schedule for advance {advance_id}...")
            
            schedule_data = {
                "number_of_installments": 5,
                "start_date": "2025-10-01"  # Start in October 2025
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/advances/{advance_id}/installments",
                json=schedule_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Test installment schedule created")
                print(f"    Schedule ID: {result.get('schedule_id')}")
                return True
            else:
                print(f"❌ Failed to create installment schedule: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error creating installment schedule: {e}")
            return False

def main():
    """Main investigation function"""
    print("🚀 Starting Comprehensive Advances Investigation")
    print("=" * 70)
    
    investigator = ComprehensiveAdvancesInvestigator()
    
    # Step 1: Authenticate
    if not investigator.authenticate():
        print("❌ Investigation failed: Could not authenticate")
        return False
    
    # Step 2: Investigate all advances
    advances = investigator.investigate_all_advances()
    
    # Step 3: Investigate payroll cycles
    cycles = investigator.investigate_payroll_cycles()
    
    # Step 4: Investigate installment schedules
    schedules = investigator.investigate_installment_schedules()
    
    # Step 5: If no advances for Mohamed, create test data
    if not any(adv.get("employee_name", "").lower().find("mohamed") != -1 for adv in advances):
        print("\n🧪 No advances found for Mohamed Mostafa. Creating test data...")
        investigator.create_test_advance_for_mohamed()
    
    print("\n" + "="*80)
    print("📊 COMPREHENSIVE INVESTIGATION SUMMARY")
    print("="*80)
    print(f"Total Advances in System: {len(advances)}")
    print(f"Total Payroll Cycles: {len(cycles)}")
    print(f"Total Installment Schedules: {len(schedules)}")
    
    # Check for October 2025 data
    october_cycles = [c for c in cycles if '2025-10' in str(c.get('period', '')) or 
                     (c.get('month') == '10' and str(c.get('year')) == '2025')]
    
    print(f"October 2025 Cycles Found: {len(october_cycles)}")
    
    if october_cycles:
        for cycle in october_cycles:
            print(f"  - Cycle ID: {cycle.get('id')}")
            print(f"  - Period: {cycle.get('period')}")
    
    print("\n🎉 Comprehensive investigation completed!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)