import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import uuid
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'tanseeq_hr')

async def main():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Find Mohamed Mostafa
    emp = await db.users.find_one({"name": "Mohamed Mostafa"})
    if not emp:
        print("❌ Mohamed Mostafa not found")
        return
    
    print(f"✅ Found Mohamed Mostafa: {emp['id']}")
    
    # Create advance with scheduled installments
    advance_id = str(uuid.uuid4())
    
    advance = {
        "id": advance_id,
        "employee_id": emp["id"],
        "employee_name": "Mohamed Mostafa",
        "amount": 500.0,
        "reason": "سلفة شخصية",
        "request_date": "2025-10-01",
        "approved_date": "2025-10-01",
        "approved_by": "admin",
        "status": "approved",
        "repayment_plan": {
            "installments": 2,
            "start_month": "2025-10",
            "monthly_amount": 250.0
        },
        "created_at": datetime.now().isoformat()
    }
    
    # Check if already exists
    existing = await db.advances.find_one({"employee_id": emp["id"], "amount": 500.0})
    if existing:
        print("⚠️  Advance already exists, updating...")
        await db.advances.replace_one(
            {"id": existing["id"]},
            advance
        )
    else:
        await db.advances.insert_one(advance)
    
    print("✅ Added advance: 500 AED (250 per month for 2 months)")
    
    # Create installment schedule
    from payroll_integration_engine import PayrollIntegrationEngine
    engine = PayrollIntegrationEngine(db)
    
    # Get October 2025 payroll cycle
    october_cycle = await db.payroll_cycles.find_one({"month": "2025-10"})
    
    if october_cycle:
        # Check if installments already created
        existing_installments = await db.advance_installments.find({
            "advance_id": advance_id
        }).to_list(None)
        
        if not existing_installments:
            schedule = await engine.create_installment_schedule(
                advance_id=advance_id,
                employee_id=emp["id"],
                total_amount=500.0,
                num_installments=2,
                first_cycle_id=october_cycle["id"]
            )
            print(f"✅ Created {len(schedule)} installments")
        else:
            print(f"⚠️  Installments already exist: {len(existing_installments)}")
    else:
        print("⚠️  October 2025 payroll cycle not found")
    
    client.close()
    print("✅ Complete!")

asyncio.run(main())
