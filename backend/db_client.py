# backend/db_client.py
import os
from motor.motor_asyncio import AsyncIOMotorClient

_MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
_DB_NAME   = os.getenv("DB_NAME", "tanseeq_hr")

_client = None
_db = None

def _client_kwargs():
    # timeouts قصيرة لمنع التعليق
    kw = dict(serverSelectionTimeoutMS=2000, connectTimeoutMS=2000, retryWrites=True)
    if _MONGO_URL.startswith("mongodb+srv://"):
        kw["tls"] = True  # Atlas/SRV
    return kw

def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(_MONGO_URL, **_client_kwargs())
    return _client

def get_db():
    global _db
    if _db is None:
        _db = get_client()[_DB_NAME]
    return _db
