#!/usr/bin/env python3
"""
Specific investigation of October 2025 payroll cycle for Mohamed Mostafa
"""

import requests
import json
from datetime import datetime
import sys

# Configuration
BACKEND_URL = "https://hr-unification.preview.emergentagent.com/api"
SUPER_ADMIN_CREDENTIALS = {
    "email": "admin@tanseeq.com",
    "password": "ADMIN"
}

class October2025Investigator:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.october_cycle_id = "e70625f9-f78e-4be3-b02e-1c51cdf5385e"  # From previous investigation
        self.mohamed_id = "33d2d833-f414-4b0c-920d-35e3ca4f853c"  # From previous investigation
        
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
    
    def investigate_october_cycle(self):
        """Investigate October 2025 payroll cycle in detail"""
        try:
            print(f"📊 Investigating October 2025 cycle: {self.october_cycle_id}")
            
            # Get cycle details
            response = self.session.get(f"{BACKEND_URL}/payroll/cycles/{self.october_cycle_id}", timeout=30)
            
            if response.status_code == 200:
                cycle = response.json()
                print("✅ October 2025 cycle details:")
                print(f"  - ID: {cycle.get('id')}")
                print(f"  - Period: {cycle.get('period')}")
                print(f"  - Month: {cycle.get('month')}")
                print(f"  - Year: {cycle.get('year')}")
                print(f"  - Status: {cycle.get('status')}")
                print(f"  - Created: {cycle.get('created_at')}")
                
                # Get cycle summary
                self.get_cycle_summary()
                
                # Get Mohamed's ledger
                self.get_mohamed_ledger()
                
                return True
                
            else:
                print(f"❌ Failed to get cycle details: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error investigating cycle: {e}")
            return False
    
    def get_cycle_summary(self):
        """Get October 2025 cycle summary"""
        try:
            print(f"📋 Getting cycle summary for October 2025...")
            
            response = self.session.get(f"{BACKEND_URL}/payroll/cycles/{self.october_cycle_id}/summary", timeout=30)
            
            if response.status_code == 200:
                summary = response.json()
                print("✅ October 2025 cycle summary:")
                print(f"  - Total Employees: {summary.get('total_employees', 0)}")
                print(f"  - Total Basic Salary: {summary.get('total_basic_salary', 0)} AED")
                print(f"  - Total Allowances: {summary.get('total_allowances', 0)} AED")
                print(f"  - Total Deductions: {summary.get('total_deductions', 0)} AED")
                print(f"  - Attendance Deductions: {summary.get('attendance_deductions', 0)} AED")
                print(f"  - Manual Deductions: {summary.get('manual_deductions', 0)} AED")
                print(f"  - Advance Deductions: {summary.get('advance_deductions', 0)} AED")
                print(f"  - Total Net Salary: {summary.get('total_net_salary', 0)} AED")
                
                advance_deductions = summary.get('advance_deductions', 0)
                if advance_deductions == 0:
                    print("  🚨 CRITICAL: NO ADVANCE DEDUCTIONS in October 2025 cycle!")
                else:
                    print(f"  ✅ Advance deductions found: {advance_deductions} AED")
                
                return summary
                
            else:
                print(f"❌ Failed to get cycle summary: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting cycle summary: {e}")
            return None
    
    def get_mohamed_ledger(self):
        """Get Mohamed Mostafa's payroll ledger for October 2025"""
        try:
            print(f"📋 Getting Mohamed Mostafa's payroll ledger for October 2025...")
            
            response = self.session.get(
                f"{BACKEND_URL}/payroll/cycles/{self.october_cycle_id}/ledger/employees/{self.mohamed_id}",
                timeout=30
            )
            
            if response.status_code == 200:
                ledger = response.json()
                print("✅ Mohamed Mostafa's payroll ledger retrieved:")
                
                # Check if it's a list or dict
                if isinstance(ledger, list):
                    entries = ledger
                elif isinstance(ledger, dict):
                    entries = ledger.get('entries', [ledger])
                else:
                    entries = []
                
                print(f"  - Total entries: {len(entries)}")
                
                advance_installment_entries = []
                
                for i, entry in enumerate(entries, 1):
                    print(f"  Entry {i}:")
                    print(f"    - Type: {entry.get('type', 'Unknown')}")
                    print(f"    - Description: {entry.get('description', 'No description')}")
                    print(f"    - Amount: {entry.get('amount', 0)} AED")
                    print(f"    - Date: {entry.get('date', 'Unknown')}")
                    
                    entry_type = entry.get('type', '').upper()
                    if 'ADVANCE' in entry_type or 'INSTALLMENT' in entry_type:
                        advance_installment_entries.append(entry)
                        print(f"    🎯 ADVANCE/INSTALLMENT ENTRY FOUND!")
                
                if not advance_installment_entries:
                    print("  🚨 CRITICAL: NO ADVANCE_INSTALLMENT entries found in Mohamed's ledger!")
                else:
                    print(f"  ✅ Found {len(advance_installment_entries)} advance/installment entries")
                
                return ledger
                
            else:
                print(f"❌ Failed to get Mohamed's ledger: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting Mohamed's ledger: {e}")
            return None
    
    def check_installment_schedules_for_october(self):
        """Check if there are any installment schedules with October 2025 due dates"""
        try:
            print("📅 Checking installment schedules for October 2025 due dates...")
            
            response = self.session.get(f"{BACKEND_URL}/payroll/installment-schedules", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                schedules = data.get("schedules", []) if isinstance(data, dict) else data
                
                october_installments = []
                
                for schedule in schedules:
                    installments = schedule.get("installments", [])
                    for installment in installments:
                        due_date = installment.get("due_date", "")
                        if due_date.startswith("2025-10"):
                            october_installments.append({
                                "schedule": schedule,
                                "installment": installment
                            })
                
                print(f"✅ Found {len(october_installments)} installments due in October 2025:")
                
                for i, item in enumerate(october_installments, 1):
                    schedule = item["schedule"]
                    installment = item["installment"]
                    
                    print(f"  {i}. Employee: {schedule.get('employee_name')} (ID: {schedule.get('employee_id')})")
                    print(f"     - Due Date: {installment.get('due_date')}")
                    print(f"     - Amount: {installment.get('amount')} AED")
                    print(f"     - Status: {installment.get('status')}")
                    print(f"     - Schedule ID: {schedule.get('id')}")
                    
                    if schedule.get('employee_id') == self.mohamed_id:
                        print(f"     🎯 THIS IS MOHAMED MOSTAFA'S INSTALLMENT!")
                
                return october_installments
                
            else:
                print(f"❌ Failed to get installment schedules: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ Error checking installment schedules: {e}")
            return []
    
    def create_test_advance_for_mohamed(self):
        """Create a test advance for Mohamed Mostafa with October 2025 installments"""
        try:
            print("🧪 Creating test advance for Mohamed Mostafa with October 2025 installments...")
            
            # Create test advance
            advance_data = {
                "employee_id": self.mohamed_id,
                "transaction_type": "advance",
                "amount": 1000.0,
                "description": "Test advance for October 2025 installment investigation",
                "category": "other",
                "expense_date": "2025-01-15",
                "notes": "Created for testing October 2025 installment deduction flow"
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
                
                # Create installment schedule with October 2025 due date
                schedule_data = {
                    "number_of_installments": 5,
                    "start_date": "2025-10-01"  # Start in October 2025
                }
                
                schedule_response = self.session.post(
                    f"{BACKEND_URL}/advances/{advance_id}/installments",
                    json=schedule_data,
                    timeout=30
                )
                
                if schedule_response.status_code == 200:
                    schedule_result = schedule_response.json()
                    print(f"✅ Test installment schedule created with October 2025 due dates")
                    print(f"    Schedule ID: {schedule_result.get('schedule_id')}")
                    
                    # Now re-check the installment schedules
                    print("\n🔄 Re-checking installment schedules after creating test data...")
                    self.check_installment_schedules_for_october()
                    
                    return True
                else:
                    print(f"❌ Failed to create installment schedule: {schedule_response.status_code} - {schedule_response.text}")
                    return False
                
            else:
                print(f"❌ Failed to create test advance: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error creating test advance: {e}")
            return False

def main():
    """Main investigation function"""
    print("🚀 Starting October 2025 Specific Investigation for Mohamed Mostafa")
    print("=" * 80)
    
    investigator = October2025Investigator()
    
    # Step 1: Authenticate
    if not investigator.authenticate():
        print("❌ Investigation failed: Could not authenticate")
        return False
    
    # Step 2: Investigate October 2025 cycle
    investigator.investigate_october_cycle()
    
    # Step 3: Check installment schedules for October 2025
    october_installments = investigator.check_installment_schedules_for_october()
    
    # Step 4: If no October installments for Mohamed, create test data
    mohamed_october_installments = [
        item for item in october_installments 
        if item["schedule"].get("employee_id") == investigator.mohamed_id
    ]
    
    if not mohamed_october_installments:
        print("\n🧪 No October 2025 installments found for Mohamed Mostafa. Creating test data...")
        investigator.create_test_advance_for_mohamed()
    
    print("\n" + "="*80)
    print("📊 OCTOBER 2025 INVESTIGATION SUMMARY")
    print("="*80)
    print(f"October 2025 Cycle ID: {investigator.october_cycle_id}")
    print(f"Mohamed Mostafa ID: {investigator.mohamed_id}")
    print(f"October 2025 Installments Found: {len(october_installments)}")
    print(f"Mohamed's October Installments: {len(mohamed_october_installments)}")
    
    if not mohamed_october_installments:
        print("\n🚨 ROOT CAUSE IDENTIFIED:")
        print("Mohamed Mostafa has NO installment schedules with October 2025 due dates.")
        print("This explains why no advance deductions appear in the October 2025 payroll cycle summary.")
    else:
        print("\n✅ Mohamed has October 2025 installments - need to check payroll integration.")
    
    print("\n🎉 October 2025 investigation completed!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)