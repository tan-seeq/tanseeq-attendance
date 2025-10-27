#!/usr/bin/env python3
import asyncio
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'tanseeq_hr')

TARGET_NAME_OPTIONS = [
    'Mohamed Mostafa',
    'MOHAMED AHMED MOHAMED MOSTAFA',
    'Mohamed AHMED MOHAMED MOSTAFA',
]

async def main():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    count = 0
    for name in TARGET_NAME_OPTIONS:
        res = await db.users.update_many({'name': name}, {'$set': {'monthly_salary': 2500.0}})
        count += res.modified_count
    # Also try case-insensitive
    res = await db.users.update_many({'name': {'$regex': '^mohamed.*mostafa$', '$options': 'i'}}, {'$set': {'monthly_salary': 2500.0}})
    count += res.modified_count
    print(f"✅ Updated salary to 2500.0 for {count} user(s) matching Mohamed Mostafa")
    client.close()

if __name__ == '__main__':
    asyncio.run(main())
