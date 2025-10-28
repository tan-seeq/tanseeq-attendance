# backend/audit_service.py
from datetime import datetime, timezone
from typing import Any, Dict
from motor.motor_asyncio import AsyncIOMotorDatabase

AUDIT_COLLECTION = "config_audit"

async def add_audit(db: AsyncIOMotorDatabase, action: str, payload: Dict[str, Any], created_by: str = "system"):
    doc = {
        "action": action,
        "payload": payload,
        "created_by": created_by,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db[AUDIT_COLLECTION].insert_one(doc)

async def ensure_calibration_off_logged(db: AsyncIOMotorDatabase, period_key: str, window_from: str, window_to: str):
    existing = await db[AUDIT_COLLECTION].find_one({
        "action": "calibration_off",
        "payload.period": period_key,
    })
    if existing:
        return
    await add_audit(db, "calibration_off", {
        "period": period_key,
        "window": {"from": window_from, "to": window_to},
        "note": "October calibration auto-off"
    })
