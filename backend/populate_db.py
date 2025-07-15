import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import bcrypt
import uuid
from datetime import datetime
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

def hash_password(password: str) -> str:
    """Hash a password"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

async def populate_users():
    """Populate the database with TANSEEQ employees"""
    
    # Clear existing users
    await db.users.delete_many({})
    
    users = [
        {
            "id": str(uuid.uuid4()),
            "name": "Hatem Mohamed Ahmed",
            "email": "hatem@tanseeq.com",
            "password": hash_password("hatem123"),
            "role": "super_admin",
            "position": "Managing Director",
            "monthly_salary": 5500.0,
            "daily_rate": 5500.0 / 22,  # Monthly salary / working days
            "working_hours_start": "00:00",  # No time restriction
            "working_hours_end": "23:59",   # No time restriction
            "phone": "+971-50-123-4567",
            "hire_date": datetime(2020, 1, 1),
            "is_active": True,
            "has_custom_schedule": True,
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Jihad",
            "email": "jihad@tanseeq.com",
            "password": hash_password("jihad123"),
            "role": "user",
            "position": "Tax Consultant",
            "monthly_salary": 2700.0,
            "daily_rate": 2700.0 / 22,
            "working_hours_start": "09:00",
            "working_hours_end": "18:00",
            "phone": "+971-50-123-4568",
            "hire_date": datetime(2021, 6, 1),
            "is_active": True,
            "has_custom_schedule": False,
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Tarek Wazzan",
            "email": "tarek.wazzan@tanseeq.com",
            "password": hash_password("tarek123"),
            "role": "user",
            "position": "Senior Tax Consultant",
            "monthly_salary": 4000.0,
            "daily_rate": 4000.0 / 22,
            "working_hours_start": "08:00",  # Tarek can start from 8 AM
            "working_hours_end": "17:00",
            "phone": "+971-50-123-4569",
            "hire_date": datetime(2021, 8, 1),
            "is_active": True,
            "has_custom_schedule": True,
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Tarek Hegazy",
            "email": "tarek.hegazy@tanseeq.com",
            "password": hash_password("tarek123"),
            "role": "user",
            "position": "Senior Tax Advisor",
            "monthly_salary": 5000.0,
            "daily_rate": 5000.0 / 22,
            "working_hours_start": "09:00",
            "working_hours_end": "18:00",
            "phone": "+971-50-123-4570",
            "hire_date": datetime(2021, 9, 1),
            "is_active": True,
            "has_custom_schedule": False,
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Kareem",
            "email": "kareem@tanseeq.com",
            "password": hash_password("kareem123"),
            "role": "user",
            "position": "Tax Specialist",
            "monthly_salary": 2500.0,
            "daily_rate": 2500.0 / 22,
            "working_hours_start": "09:00",
            "working_hours_end": "18:00",
            "phone": "+971-50-123-4571",
            "hire_date": datetime(2022, 1, 1),
            "is_active": True,
            "has_custom_schedule": False,
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Hesham",
            "email": "hesham@tanseeq.com",
            "password": hash_password("hesham123"),
            "role": "user",
            "position": "Tax Specialist",
            "monthly_salary": 2500.0,
            "daily_rate": 2500.0 / 22,
            "working_hours_start": "09:00",
            "working_hours_end": "18:00",
            "phone": "+971-50-123-4572",
            "hire_date": datetime(2022, 2, 1),
            "is_active": True,
            "has_custom_schedule": False,
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Mohamed Mostafa",
            "email": "mohamed.mostafa@tanseeq.com",
            "password": hash_password("mohamed123"),
            "role": "user",
            "position": "Tax Consultant",
            "monthly_salary": 3500.0,
            "daily_rate": 3500.0 / 22,
            "working_hours_start": "09:00",
            "working_hours_end": "18:00",
            "phone": "+971-50-123-4573",
            "hire_date": datetime(2022, 3, 1),
            "is_active": True,
            "has_custom_schedule": False,
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Mahmoud",
            "email": "mahmoud@tanseeq.com",
            "password": hash_password("mahmoud123"),
            "role": "admin",
            "position": "Operations Manager",
            "monthly_salary": 5000.0,
            "daily_rate": 5000.0 / 22,
            "working_hours_start": "09:00",
            "working_hours_end": "18:00",
            "phone": "+971-50-123-4574",
            "hire_date": datetime(2020, 6, 1),
            "is_active": True,
            "has_custom_schedule": False,
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Howaida",
            "email": "howaida@tanseeq.com",
            "password": hash_password("howaida123"),
            "role": "admin",
            "position": "HR Manager",
            "monthly_salary": 5000.0,
            "daily_rate": 5000.0 / 22,
            "working_hours_start": "09:00",
            "working_hours_end": "18:00",
            "phone": "+971-50-123-4575",
            "hire_date": datetime(2020, 8, 1),
            "is_active": True,
            "has_custom_schedule": False,
            "created_at": datetime.utcnow()
        }
    ]
    
    await db.users.insert_many(users)
    print(f"Successfully populated {len(users)} TANSEEQ employees")
    
    # Create indexes
    await db.users.create_index("email", unique=True)
    await db.attendance.create_index([("user_id", 1), ("date", 1)])
    await db.leaves.create_index("user_id")
    await db.field_exits.create_index("user_id")
    await db.activity_logs.create_index("user_id")
    
    print("Database indexes created successfully")
    
    # Print employee list for verification
    print("\n=== TANSEEQ EMPLOYEES ===")
    for user in users:
        print(f"Name: {user['name']}")
        print(f"Email: {user['email']}")
        print(f"Role: {user['role']}")
        print(f"Salary: AED {user['monthly_salary']:,.0f}")
        print(f"Working Hours: {user['working_hours_start']} - {user['working_hours_end']}")
        print("-" * 40)

async def main():
    await populate_users()
    client.close()

if __name__ == "__main__":
    asyncio.run(main())