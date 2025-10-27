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
    
    # Create simple advance record
    advance = {
        "id": str(uuid.uuid4()),
        "employee_id": emp["id"],
        "employee_name": "Mohamed Mostafa",
        "amount": 500.0,
        "reason": "سلفة شخصية - أكتوبر",
        "request_date": "2025-10-01",
        "status": "approved",
        "created_at": datetime.now().isoformat()
    }
    
    await db.advances.insert_one(advance)
    print("✅ Added 500 AED advance for Mohamed Mostafa")
    
    client.close()

asyncio.run(main())
