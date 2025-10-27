#!/usr/bin/env python3
import asyncio
import sys
from motor.motor_asyncio import AsyncIOMotorClient
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv()

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'tanseeq_hr')

async def test_calculations():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Import unified engine
    from deductions_engine import calculate_monthly_deductions
    
    print("🔄 Testing unified deductions engine for October 2025...")
    
    # Calculate October 2025
    summaries = await calculate_monthly_deductions(db, 10, 2025)
    
    print(f"\n📊 Calculated deductions for {len(summaries)} employees\n")
    
    # Show results for employees with issues
    print("=" * 80)
    print("DEDUCTION RESULTS")
    print("=" * 80)
    
    for summary in summaries[:10]:  # Show first 10
        emp_name = summary.employee_name
        total_ded = summary.total_deduction
        late_days = summary.days_late
        absent_days = summary.days_absent
        late_mins = summary.total_late_minutes
        
        status = "✅ CORRECT" if (late_days == 0 and absent_days == 0 and total_ded == 0) else "⚠️  HAS DEDUCTION"
        
        print(f"\n{status} {emp_name}:")
        print(f"   Salary: {summary.basic_salary:.2f} AED")
        print(f"   Absent Days: {absent_days}")
        print(f"   Late Days: {late_days}")
        print(f"   Late Minutes: {late_mins}")
        print(f"   Late Deduction: {summary.late_deduction:.2f} AED")
        print(f"   Absence Deduction: {summary.absence_deduction:.2f} AED")
        print(f"   TOTAL DEDUCTION: {total_ded:.2f} AED")
        
        # If has deduction, show daily breakdown
        if total_ded > 0:
            print(f"\n   📋 Daily Breakdown (showing deduction days):")
            for daily in summary.daily_records:
                if daily.deduction_amount > 0 or daily.late_minutes > 0:
                    print(f"      {daily.date}: check_in={daily.check_in}, late={daily.late_minutes}min, "
                          f"grace={daily.grace_applied}, deduction={daily.deduction_amount:.2f} AED")
                    print(f"         Rule: {daily.rule_applied}")
                    if daily.note:
                        print(f"         Note: {daily.note}")
    
    client.close()

asyncio.run(test_calculations())
