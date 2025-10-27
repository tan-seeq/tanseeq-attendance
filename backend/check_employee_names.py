import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'tanseeq_hr')

async def main():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    employees = await db.users.find({"is_active": True}).to_list(None)
    print("📋 Active Employees in Database:")
    for emp in employees:
        print(f"   {emp['name']}")
    
    client.close()

asyncio.run(main())
