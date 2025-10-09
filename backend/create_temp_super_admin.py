#!/usr/bin/env python3
"""
Create Temporary Super Admin Account for QA Testing
====================================================
Creates: qa.superadmin@tanseeq.com with strong password and forced reset
"""

import asyncio
import os
import uuid
import secrets
import string
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from dotenv import load_dotenv
import pyotp

# Add parent directory to path for imports
import sys
sys.path.insert(0, '/app/backend')
from uae_datetime_utils import to_iso_string_uae

load_dotenv('/app/backend/.env')

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_strong_password(length=16):
    """Generate a strong random password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password


async def create_temp_super_admin():
    """Create temporary Super Admin account for QA testing"""
    mongo_url = os.environ['MONGO_URL']
    db_name = os.environ['DB_NAME']
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("=" * 70)
    print("🔐 CREATING TEMPORARY SUPER ADMIN ACCOUNT")
    print("=" * 70)
    print()
    
    # Account details
    email = "qa.superadmin@tanseeq.com"
    name = "QA SUPER ADMIN (TEMP)"
    
    # Check if already exists
    existing = await db.users.find_one({"email": email})
    if existing:
        print(f"⚠️  Account already exists: {email}")
        print(f"   Existing ID: {existing.get('id')}")
        
        response = input("\nDelete and recreate? (yes/no): ")
        if response.lower() != "yes":
            print("Aborted.")
            client.close()
            return None
        
        # Delete existing
        await db.users.delete_one({"email": email})
        print(f"✅ Deleted existing account")
    
    # Generate strong one-time password
    temp_password = generate_strong_password(16)
    hashed_password = pwd_context.hash(temp_password)
    
    # Generate TOTP secret for 2FA
    totp_secret = pyotp.random_base32()
    totp_uri = pyotp.totp.TOTP(totp_secret).provisioning_uri(
        name=email,
        issuer_name="TANSEEQ HR"
    )
    
    # Create user document
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "name": name,
        "email": email,
        "password": hashed_password,
        "role": "super_admin",
        "position": "QA Testing - Temporary Account",
        "monthly_salary": 0.0,
        "daily_rate": 0.0,
        "created_at": to_iso_string_uae(),
        "updated_at": to_iso_string_uae(),
        
        # 2FA / TOTP
        "totp_secret": totp_secret,
        "totp_enabled": True,
        
        # Force password reset on first login
        "must_change_password": True,
        "password_changed_at": None,
        
        # Temporary account marker
        "is_temporary": True,
        "temporary_purpose": "QA Testing - Comprehensive Audit Phase",
        "temporary_created_by": "system",
        "temporary_created_at": to_iso_string_uae(),
        
        # Audit metadata
        "metadata": {
            "account_type": "temporary_qa",
            "creation_reason": "Phase 1-4 comprehensive testing",
            "scheduled_deletion": "After project closure",
            "creator_agent": "AI Agent - Phase 2 Implementation"
        }
    }
    
    # Insert into database
    await db.users.insert_one(user_doc)
    
    # Create audit log entry
    audit_entry = {
        "id": str(uuid.uuid4()),
        "timestamp": to_iso_string_uae(),
        "action": "CREATE_TEMP_SUPER_ADMIN",
        "user_id": user_id,
        "user_email": email,
        "user_name": name,
        "performed_by": "system",
        "details": {
            "purpose": "QA Testing - Comprehensive Audit & Fix",
            "2fa_enabled": True,
            "password_reset_required": True,
            "account_temporary": True
        },
        "ip_address": "system",
        "user_agent": "Backend Script"
    }
    
    await db.audit_logs.insert_one(audit_entry)
    
    print("✅ Account Created Successfully!")
    print()
    print("=" * 70)
    print("📋 ACCOUNT DETAILS")
    print("=" * 70)
    print(f"Email:    {email}")
    print(f"Name:     {name}")
    print(f"Role:     super_admin")
    print(f"User ID:  {user_id}")
    print()
    print("=" * 70)
    print("🔑 TEMPORARY CREDENTIALS (ONE-TIME USE)")
    print("=" * 70)
    print(f"Password: {temp_password}")
    print()
    print("⚠️  SECURITY NOTES:")
    print("   1. This password must be changed on first login")
    print("   2. 2FA/TOTP is ENABLED and REQUIRED")
    print("   3. Share credentials via secure channel only (Signal/WhatsApp)")
    print("   4. Account is marked as temporary and will be deleted after closure")
    print()
    print("=" * 70)
    print("📱 2FA / TOTP SETUP")
    print("=" * 70)
    print(f"TOTP Secret: {totp_secret}")
    print()
    print("QR Code URI (for authenticator app):")
    print(totp_uri)
    print()
    print("To generate QR code, run:")
    print(f"  python3 -c \"import pyotp; import qrcode; qrcode.make('{totp_uri}').save('qa_admin_qr.png')\"")
    print()
    print("=" * 70)
    print("📊 AUDIT LOG")
    print("=" * 70)
    print(f"Audit Entry ID: {audit_entry['id']}")
    print(f"Timestamp:      {audit_entry['timestamp']}")
    print(f"Action:         {audit_entry['action']}")
    print()
    print("✅ Account creation logged in audit_logs collection")
    print()
    
    client.close()
    
    return {
        "user_id": user_id,
        "email": email,
        "password": temp_password,
        "totp_secret": totp_secret,
        "totp_uri": totp_uri
    }


if __name__ == "__main__":
    print("\n🔐 Temporary Super Admin Account Creator")
    print("Purpose: QA Testing for TANSEEQ HR Comprehensive Audit\n")
    
    credentials = asyncio.run(create_temp_super_admin())
    
    if credentials:
        print("=" * 70)
        print("✅ SETUP COMPLETE")
        print("=" * 70)
        print()
        print("Next Steps:")
        print("1. Share credentials securely with QA team")
        print("2. User must login and change password immediately")
        print("3. User must setup 2FA authenticator app")
        print("4. After testing complete, delete account via admin panel")
        print()
