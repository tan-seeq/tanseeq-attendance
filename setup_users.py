#!/usr/bin/env python3
"""
Setup script to create TANSEEQ HR users with correct passwords
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
import bcrypt
import uuid
from datetime import datetime

async def setup_users():
    load_dotenv('/app/backend/.env')
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # Define users as per the review request
    users_data = [
        {
            'name': 'Hatem Mohamed Ahmed',
            'email': 'hatem@tanseeq.com',
            'password': 'hatem123',
            'role': 'super_admin',
            'position': 'General Manager',
            'monthly_salary': 5500.0,
            'daily_rate': 250.0,
            'working_hours_start': '00:00',  # No time restrictions
            'working_hours_end': '23:59',
            'phone': '+971501234567',
            'is_active': True
        },
        {
            'name': 'Jihad',
            'email': 'jihad@tanseeq.com',
            'password': 'jihad123',
            'role': 'user',
            'position': 'Employee',
            'monthly_salary': 2700.0,
            'daily_rate': 122.73,
            'working_hours_start': '09:00',
            'working_hours_end': '18:00',
            'phone': '+971501234568',
            'is_active': True
        },
        {
            'name': 'Tarek Wazzan',
            'email': 'tarek.wazzan@tanseeq.com',
            'password': 'tarek123',
            'role': 'user',
            'position': 'Employee',
            'monthly_salary': 4000.0,
            'daily_rate': 181.82,
            'working_hours_start': '08:00',  # Can start from 8 AM
            'working_hours_end': '18:00',
            'phone': '+971501234569',
            'is_active': True
        },
        {
            'name': 'Tarek Hegazy',
            'email': 'tarek.hegazy@tanseeq.com',
            'password': 'tarek123',
            'role': 'user',
            'position': 'Employee',
            'monthly_salary': 5000.0,
            'daily_rate': 227.27,
            'working_hours_start': '09:00',
            'working_hours_end': '18:00',
            'phone': '+971501234570',
            'is_active': True
        },
        {
            'name': 'Kareem',
            'email': 'kareem@tanseeq.com',
            'password': 'kareem123',
            'role': 'user',
            'position': 'Employee',
            'monthly_salary': 2500.0,
            'daily_rate': 113.64,
            'working_hours_start': '09:00',
            'working_hours_end': '18:00',
            'phone': '+971501234571',
            'is_active': True
        },
        {
            'name': 'Hesham',
            'email': 'hesham@tanseeq.com',
            'password': 'hesham123',
            'role': 'user',
            'position': 'Employee',
            'monthly_salary': 2500.0,
            'daily_rate': 113.64,
            'working_hours_start': '09:00',
            'working_hours_end': '18:00',
            'phone': '+971501234572',
            'is_active': True
        },
        {
            'name': 'Mohamed Mostafa',
            'email': 'mohamed.mostafa@tanseeq.com',
            'password': 'mohamed123',
            'role': 'user',
            'position': 'Employee',
            'monthly_salary': 3500.0,
            'daily_rate': 159.09,
            'working_hours_start': '09:00',
            'working_hours_end': '18:00',
            'phone': '+971501234573',
            'is_active': True
        },
        {
            'name': 'Mahmoud',
            'email': 'mahmoud@tanseeq.com',
            'password': 'mahmoud123',
            'role': 'admin',
            'position': 'Admin',
            'monthly_salary': 5000.0,
            'daily_rate': 227.27,
            'working_hours_start': '09:00',
            'working_hours_end': '18:00',
            'phone': '+971501234574',
            'is_active': True
        },
        {
            'name': 'Howaida',
            'email': 'howaida@tanseeq.com',
            'password': 'howaida123',
            'role': 'admin',
            'position': 'Admin',
            'monthly_salary': 5000.0,
            'daily_rate': 227.27,
            'working_hours_start': '09:00',
            'working_hours_end': '18:00',
            'phone': '+971501234575',
            'is_active': True
        }
    ]
    
    print("Setting up TANSEEQ HR users...")
    
    # Clear existing users
    await db.users.delete_many({})
    print("Cleared existing users")
    
    # Create users
    for user_data in users_data:
        # Hash password
        hashed_password = bcrypt.hashpw(user_data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        user_doc = {
            'id': str(uuid.uuid4()),
            'name': user_data['name'],
            'email': user_data['email'],
            'password': hashed_password,
            'role': user_data['role'],
            'position': user_data['position'],
            'monthly_salary': user_data['monthly_salary'],
            'daily_rate': user_data['daily_rate'],
            'working_hours_start': user_data['working_hours_start'],
            'working_hours_end': user_data['working_hours_end'],
            'phone': user_data['phone'],
            'hire_date': datetime.utcnow(),
            'is_active': user_data['is_active'],
            'created_at': datetime.utcnow()
        }
        
        await db.users.insert_one(user_doc)
        print(f"✅ Created user: {user_data['name']} ({user_data['email']}) - {user_data['role']}")
    
    print(f"\n🎉 Successfully created {len(users_data)} users!")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(setup_users())