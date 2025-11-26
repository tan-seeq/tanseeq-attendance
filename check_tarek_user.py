#!/usr/bin/env python3
"""
Check if Tarek user exists in database and verify credentials
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from db_client import get_db
import bcrypt

async def check_tarek_user():
    """Check Tarek user in database"""
    try:
        db = get_db()
        
        # Search for Tarek user
        tarek_users = await db.users.find({"email": {"$regex": "tarek", "$options": "i"}}).to_list(10)
        
        print("🔍 Searching for Tarek users...")
        print(f"Found {len(tarek_users)} users with 'tarek' in email:")
        
        for user in tarek_users:
            print(f"\n📧 Email: {user.get('email')}")
            print(f"👤 Name: {user.get('name')}")
            print(f"🔑 Role: {user.get('role')}")
            print(f"✅ Active: {user.get('is_active')}")
            print(f"🔒 Has Password: {'Yes' if user.get('password') else 'No'}")
            
            # Test password verification
            if user.get('password'):
                test_passwords = ["tarek123", "123456", "tarek", "TAREK"]
                for pwd in test_passwords:
                    try:
                        is_valid = bcrypt.checkpw(pwd.encode('utf-8'), user['password'].encode('utf-8'))
                        if is_valid:
                            print(f"✅ Password '{pwd}' is VALID")
                            break
                    except Exception as e:
                        print(f"❌ Error testing password '{pwd}': {e}")
                else:
                    print("❌ None of the test passwords work")
        
        # Also check all users to see available accounts
        print("\n" + "="*50)
        print("📋 All users in database:")
        all_users = await db.users.find({}).to_list(20)
        
        for user in all_users:
            status = "✅" if user.get('is_active') else "❌"
            pwd_status = "🔒" if user.get('password') else "🔓"
            print(f"{status} {pwd_status} {user.get('email')} ({user.get('role')}) - {user.get('name')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_tarek_user())