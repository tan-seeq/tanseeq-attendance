#!/usr/bin/env python3
"""
Setup Production Users - TANSEEQ HR
====================================
Creates all required users with correct roles in production database.

ROLES:
- Super Admin: حاتم (hatem@tanseeq.com)
- Admins: محمود (mahmoud@tanseeq.com), هويدة (howayda@tanseeq.com)
- Users: محمد (mohamed@tanseeq.com), جهاد (jihad@tanseeq.com)
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from db_client import get_db
import bcrypt
import uuid
from datetime import datetime

async def setup_users():
    """Setup all production users with correct roles"""
    
    db = get_db()
    
    users_to_create = [
        {
            'email': 'hatem@tanseeq.com',
            'name': 'حاتم',
            'password': 'hatem123',  # يجب تغييرها في الإنتاج
            'role': 'super_admin',
            'position': 'Super Admin',
            'monthly_salary': 0.0,
            'has_flexible_schedule': True,  # مستثنى من الخصومات
        },
        {
            'email': 'mahmoud@tanseeq.com',
            'name': 'محمود',
            'password': 'mahmoud123',
            'role': 'admin',
            'position': 'Admin',
            'monthly_salary': 0.0,
            'has_flexible_schedule': False,
        },
        {
            'email': 'howayda@tanseeq.com',
            'name': 'هويدة',
            'password': 'howayda123',
            'role': 'admin',
            'position': 'Admin',
            'monthly_salary': 0.0,
            'has_flexible_schedule': False,
        },
        {
            'email': 'mohamed@tanseeq.com',
            'name': 'محمد مصطفى',
            'password': 'mohamed123',
            'role': 'user',
            'position': 'Employee',
            'monthly_salary': 8000.0,
            'daily_rate': 320.0,
            'has_flexible_schedule': False,
        },
        {
            'email': 'jihad@tanseeq.com',
            'name': 'جهاد',
            'password': 'jihad123',
            'role': 'user',
            'position': 'Employee',
            'monthly_salary': 8000.0,
            'daily_rate': 320.0,
            'has_flexible_schedule': False,
        }
    ]
    
    print("\n🔧 SETTING UP PRODUCTION USERS")
    print("="*60)
    
    for user_data in users_to_create:
        email = user_data['email']
        
        # Check if user exists
        existing = await db.users.find_one({'email': email})
        
        if existing:
            # Update existing user
            password_hash = bcrypt.hashpw(user_data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            await db.users.update_one(
                {'email': email},
                {'$set': {
                    'name': user_data['name'],
                    'password': password_hash,
                    'role': user_data['role'],
                    'position': user_data['position'],
                    'monthly_salary': user_data['monthly_salary'],
                    'daily_rate': user_data.get('daily_rate', 0.0),
                    'working_hours_start': '09:00',
                    'working_hours_end': '18:00',
                    'phone': '',
                    'is_active': True,
                    'has_flexible_schedule': user_data['has_flexible_schedule'],
                    'updated_at': datetime.now().isoformat()
                }}
            )
            print(f"  ✅ Updated: {user_data['name']} ({email}) - Role: {user_data['role']}")
        else:
            # Create new user
            password_hash = bcrypt.hashpw(user_data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            user = {
                'id': str(uuid.uuid4()),
                'email': email,
                'name': user_data['name'],
                'password': password_hash,
                'role': user_data['role'],
                'position': user_data['position'],
                'monthly_salary': user_data['monthly_salary'],
                'daily_rate': user_data.get('daily_rate', 0.0),
                'working_hours_start': '09:00',
                'working_hours_end': '18:00',
                'phone': '',
                'hire_date': datetime.now().isoformat(),
                'is_active': True,
                'has_flexible_schedule': user_data['has_flexible_schedule'],
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            await db.users.insert_one(user)
            print(f"  ✅ Created: {user_data['name']} ({email}) - Role: {user_data['role']}")
    
    print("\n✅ ALL USERS SETUP COMPLETE")
    print("="*60)
    
    # Verify all users can login
    print("\n🔐 VERIFYING AUTHENTICATION...")
    for user_data in users_to_create:
        user = await db.users.find_one({'email': user_data['email']})
        if user and 'password' in user:
            # Test password
            result = bcrypt.checkpw(user_data['password'].encode('utf-8'), user['password'].encode('utf-8'))
            status = "✅ OK" if result else "❌ FAIL"
            print(f"  {status}: {user['name']} ({user['email']}) - Role: {user['role']}")
        else:
            print(f"  ❌ MISSING: {user_data['email']}")
    
    print("\n" + "="*60)
    print("🎯 CREDENTIALS FOR TESTING:")
    print("  Super Admin: hatem@tanseeq.com / hatem123")
    print("  Admin 1: mahmoud@tanseeq.com / mahmoud123")
    print("  Admin 2: howayda@tanseeq.com / howayda123")
    print("  User 1: mohamed@tanseeq.com / mohamed123")
    print("  User 2: jihad@tanseeq.com / jihad123")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(setup_users())
