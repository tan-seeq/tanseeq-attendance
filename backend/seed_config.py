#!/usr/bin/env python3
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'tanseeq_hr')

USERS = [
    {"name_variants": ["Tariq", "Tarek", "TAREK ABDELMONEM ZAKI ALWAZAN", "Tarek Wazzan"], "type": "flex", "email": None},
    {"name_variants": ["Hatem", "Hatem Mohamed Ahmed", "حاتم"], "type": "flex", "email": None},
    {"name_variants": ["Karim", "Kareem", "KARIM MOHAMED MOUSTAFA ABDELMEGEUID"], "type": "partial-flex", "email": None},
    {"name_variants": ["Hesham", "Hisham", "HESHAM AHMED MOHAMED MOSTAFA"], "type": "partial-flex", "email": None},
]

IMPORT_MAP = {
    "Tariq": "Tariq",
    "Tarek": "Tariq",
    "Hatem": "Hatem",
    "Hatim": "Hatem",
    "Karim": "Karim",
    "Kareem": "Karim",
    "Hesham": "Hesham",
    "Hisham": "Hesham",
    "Mohamed Mostafa": "Mohamed Mostafa",
    "Mohammad Moustafa": "Mohamed Mostafa",
    "Mohammed Mostafa": "Mohamed Mostafa",
}

async def seed():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    # Seed config_import_map
    for ext, canon in IMPORT_MAP.items():
        await db["config_import_map"].update_one(
            {"external_name": ext},
            {"$set": {"external_name": ext, "canonical_name": canon, "created_by": "system"}},
            upsert=True
        )

    # Seed exceptions by user_id using name/email resolving
    users = await db["users"].find({}).to_list(None)
    for cfg in USERS:
        target_user = None
        # Resolve by email first if provided
        if cfg.get("email"):
            for u in users:
                if (u.get("email") or "").lower() == cfg["email"].lower():
                    target_user = u
                    break
        # Otherwise by name variants
        if not target_user:
            for u in users:
                uname = (u.get("name") or "").strip().lower()
                for v in cfg["name_variants"]:
                    if v.lower() in uname or uname in v.lower():
                        target_user = u
                        break
                if target_user:
                    break
        if target_user:
            await db["config_exceptions"].update_one(
                {"user_id": target_user["id"]},
                {"$set": {"user_id": target_user["id"], "type": cfg["type"], "name": target_user.get("name"), "created_by": "system"}},
                upsert=True
            )
        else:
            print("⚠️ Could not resolve user for config:", cfg)

    print("✅ Seeding complete")
    client.close()

if __name__ == '__main__':
    asyncio.run(seed())
