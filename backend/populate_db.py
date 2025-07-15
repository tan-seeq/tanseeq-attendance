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
    """Populate the database with initial users"""
    
    # Clear existing users
    await db.users.delete_many({})
    
    users = [
        {
            "id": str(uuid.uuid4()),
            "name": "حاتم",
            "email": "hatem@tan-seeq.co",
            "password": hash_password("5405009"),
            "role": "super_admin",
            "position": "مدير عام",
            "monthly_salary": 10000.0,
            "daily_rate": 400.0,
            "working_hours_start": "09:00",
            "working_hours_end": "18:00",
            "phone": "+971501234567",
            "hire_date": datetime(2020, 1, 1),
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "محمود",
            "email": "mahmoud.admin@tanseeq.com",
            "password": hash_password("123456"),
            "role": "admin",
            "position": "مدير إداري",
            "monthly_salary": 8000.0,
            "daily_rate": 300.0,
            "working_hours_start": "09:00",
            "working_hours_end": "18:00",
            "phone": "+971501234568",
            "hire_date": datetime(2021, 1, 1),
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "حويدا",
            "email": "howaida.admin@tanseeq.com",
            "password": hash_password("123456"),
            "role": "admin",
            "position": "مديرة الموارد البشرية",
            "monthly_salary": 8000.0,
            "daily_rate": 300.0,
            "working_hours_start": "09:00",
            "working_hours_end": "18:00",
            "phone": "+971501234569",
            "hire_date": datetime(2021, 1, 1),
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "طارق",
            "email": "Tarek.wzard@gmail.com",
            "password": hash_password("123456"),
            "role": "user",
            "position": "موظف",
            "monthly_salary": 5000.0,
            "daily_rate": 200.0,
            "working_hours_start": "09:00",
            "working_hours_end": "18:00",
            "phone": "+971501234570",
            "hire_date": datetime(2022, 1, 1),
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "أحمد",
            "email": "ahmed.employee@tanseeq.com",
            "password": hash_password("123456"),
            "role": "user",
            "position": "موظف",
            "monthly_salary": 4500.0,
            "daily_rate": 180.0,
            "working_hours_start": "09:00",
            "working_hours_end": "18:00",
            "phone": "+971501234571",
            "hire_date": datetime(2022, 6, 1),
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "فاطمة",
            "email": "fatima.employee@tanseeq.com",
            "password": hash_password("123456"),
            "role": "user",
            "position": "موظفة",
            "monthly_salary": 4000.0,
            "daily_rate": 160.0,
            "working_hours_start": "09:00",
            "working_hours_end": "18:00",
            "phone": "+971501234572",
            "hire_date": datetime(2022, 8, 1),
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "محمد",
            "email": "mohammed.employee@tanseeq.com",
            "password": hash_password("123456"),
            "role": "user",
            "position": "موظف",
            "monthly_salary": 4200.0,
            "daily_rate": 170.0,
            "working_hours_start": "09:00",
            "working_hours_end": "18:00",
            "phone": "+971501234573",
            "hire_date": datetime(2023, 1, 1),
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "عائشة",
            "email": "aisha.employee@tanseeq.com",
            "password": hash_password("123456"),
            "role": "user",
            "position": "موظفة",
            "monthly_salary": 3800.0,
            "daily_rate": 150.0,
            "working_hours_start": "09:00",
            "working_hours_end": "18:00",
            "phone": "+971501234574",
            "hire_date": datetime(2023, 3, 1),
            "is_active": True,
            "created_at": datetime.utcnow()
        }
    ]
    
    await db.users.insert_many(users)
    print(f"Successfully populated {len(users)} users")
    
    # Create indexes
    await db.users.create_index("email", unique=True)
    await db.attendance.create_index([("user_id", 1), ("date", 1)])
    await db.leaves.create_index("user_id")
    await db.field_exits.create_index("user_id")
    await db.activity_logs.create_index("user_id")
    
    print("Database indexes created successfully")

async def main():
    await populate_users()
    client.close()

if __name__ == "__main__":
    asyncio.run(main())