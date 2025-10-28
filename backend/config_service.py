# backend/config_service.py
from typing import Dict, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

EXCEPTIONS_COLLECTION = "config_exceptions"
IMPORT_MAP_COLLECTION = "config_import_map"

async def get_exception_type(db: AsyncIOMotorDatabase, user_id: str) -> Optional[str]:
    """
    Return exception type for user_id if configured:
    - 'flex' → no late/early deductions, absence only
    - 'partial-flex' → lateness-only deductions, ignore early leave
    - None → no special exception
    """
    if not user_id:
        return None
    doc = await db[EXCEPTIONS_COLLECTION].find_one({"user_id": user_id})
    if not doc:
        return None
    t = (doc.get("type") or "").strip().lower()
    return t if t in ("flex", "partial-flex") else None

async def get_import_name_mapping(db: AsyncIOMotorDatabase) -> Dict[str, str]:
    """Return a mapping of external names → canonical system names from DB config."""
    mapping = {}
    async for doc in db[IMPORT_MAP_COLLECTION].find({}):
        ext = (doc.get("external_name") or "").strip()
        canon = (doc.get("canonical_name") or "").strip()
        if ext and canon:
            mapping[ext] = canon
    return mapping
