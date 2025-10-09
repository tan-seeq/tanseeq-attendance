"""
MongoDB Database Setup and Models for Daily Work Report + Clients Master Feature
Migrated from SQLite to MongoDB for production Kubernetes compatibility
"""

import os
import uuid
from datetime import datetime
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from cryptography.fernet import Fernet
import base64
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ❌ REMOVED import-time MongoDB connection
# ✅ Lazy initialization - only connect when actually needed
_work_reports_client = None
_work_reports_db = None

def get_work_reports_client():
    """Get or create Work Reports MongoDB client (lazy initialization)"""
    global _work_reports_client
    if _work_reports_client is None:
        mongo_url = os.environ.get('MONGO_URL')
        if not mongo_url:
            raise ValueError(
                "MONGO_URL environment variable is required for Work Reports. "
                "Please set MONGO_URL in your environment configuration."
            )
        
        # Create client with short timeouts to prevent blocking
        _work_reports_client = AsyncIOMotorClient(
            mongo_url,
            serverSelectionTimeoutMS=2000,  # 2 second timeout
            connectTimeoutMS=2000,
            socketTimeoutMS=2000,
            maxPoolSize=10,
            minPoolSize=1,
            retryWrites=True
        )
        print(f"✅ Work Reports MongoDB client initialized (lazy)")
    
    return _work_reports_client

def get_work_reports_db_connection():
    """Get Work Reports database (lazy initialization)"""
    global _work_reports_db
    if _work_reports_db is None:
        client = get_work_reports_client()
        db_name = os.environ.get('DB_NAME', 'tanseeq_hr')
        _work_reports_db = client[f"{db_name}_work_reports"]
        print(f"✅ Work Reports database ready: {db_name}_work_reports")
    
    return _work_reports_db

# Backward compatibility - return None initially, will be set on first access
work_reports_db = None

def _ensure_work_reports_db():
    """Internal helper to ensure work_reports_db is initialized"""
    global work_reports_db
    if work_reports_db is None:
        work_reports_db = get_work_reports_db_connection()
    return work_reports_db

# Encryption key for client credentials 
ENCRYPTION_KEY = os.environ.get('WORK_REPORTS_ENCRYPTION_KEY', 
                               base64.urlsafe_b64encode(os.urandom(32)).decode())

# ============ PYDANTIC MODELS FOR VALIDATION ============

class ClientCreate(BaseModel):
    company_name: str
    company_name_ar: Optional[str] = None
    client_code: Optional[str] = None
    industry: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    tax_number: Optional[str] = None
    commercial_registration: Optional[str] = None
    is_active: bool = True

class ClientUpdate(BaseModel):
    company_name: Optional[str] = None
    company_name_ar: Optional[str] = None
    client_code: Optional[str] = None
    industry: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    tax_number: Optional[str] = None
    commercial_registration: Optional[str] = None
    is_active: Optional[bool] = None

class ClientResponse(BaseModel):
    id: str
    company_name: str
    company_name_ar: Optional[str] = None
    client_code: Optional[str] = None
    industry: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    tax_number: Optional[str] = None
    commercial_registration: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

class ClientCredentialCreate(BaseModel):
    client_id: str
    portal_name: str
    portal_url: Optional[str] = None
    username: str
    password: str
    email: Optional[str] = None
    notes: Optional[str] = None

class ClientCredentialResponse(BaseModel):
    id: str
    client_id: str
    portal_name: str
    portal_url: Optional[str] = None
    username: str
    email: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class ActivityTypeCreate(BaseModel):
    name: str
    name_ar: Optional[str] = None
    description: Optional[str] = None
    hourly_rate: Optional[float] = None
    is_billable: bool = True
    category: Optional[str] = None

class ActivityTypeResponse(BaseModel):
    id: str
    name: str
    name_ar: Optional[str] = None
    description: Optional[str] = None
    hourly_rate: Optional[float] = None
    is_billable: bool = True
    category: Optional[str] = None
    created_at: datetime

class WorkLogCreate(BaseModel):
    client_id: str
    activity_type_id: str
    date: str  # YYYY-MM-DD format
    start_time: str  # HH:MM format
    end_time: str  # HH:MM format
    description: Optional[str] = None
    amount: Optional[float] = None

class WorkLogUpdate(BaseModel):
    client_id: Optional[str] = None
    activity_type_id: Optional[str] = None
    date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None

class WorkLogResponse(BaseModel):
    id: str
    client_id: str
    activity_type_id: str
    date: str
    start_time: str
    end_time: str
    duration_minutes: int
    description: Optional[str] = None
    amount: Optional[float] = None
    created_by: str
    created_at: datetime
    updated_at: datetime

class UserPermissionResponse(BaseModel):
    user_id: str
    permission_level: str
    can_view_credentials: bool = False
    can_create_credentials: bool = False
    can_edit_credentials: bool = False
    can_delete_credentials: bool = False
    can_reveal_passwords: bool = False
    can_manage_permissions: bool = False
    can_audit_logs: bool = False
    can_export_data: bool = False
    can_import_data: bool = False
    can_manage_templates: bool = False

class PermissionUpdateRequest(BaseModel):
    permission_level: str
    can_view_credentials: bool = False
    can_create_credentials: bool = False
    can_edit_credentials: bool = False
    can_delete_credentials: bool = False
    can_reveal_passwords: bool = False
    can_manage_permissions: bool = False
    can_audit_logs: bool = False
    can_export_data: bool = False
    can_import_data: bool = False
    can_manage_templates: bool = False

# ============ PERMISSION TEMPLATES ============

PERMISSION_TEMPLATES = {
    "user": {
        "name": "مستخدم عادي",
        "name_en": "Regular User",
        "description": "صلاحيات أساسية للمستخدمين العاديين",
        "description_en": "Basic permissions for regular users",
        "permissions": {
            "can_view_credentials": False,
            "can_create_credentials": False,
            "can_edit_credentials": False,
            "can_delete_credentials": False,
            "can_reveal_passwords": False,
            "can_manage_permissions": False,
            "can_audit_logs": False,
            "can_export_data": False,
            "can_import_data": False,
            "can_manage_templates": False
        }
    },
    "supervisor": {
        "name": "مشرف",
        "name_en": "Supervisor",
        "description": "صلاحيات متوسطة للمشرفين",
        "description_en": "Intermediate permissions for supervisors",
        "permissions": {
            "can_view_credentials": True,
            "can_create_credentials": True,
            "can_edit_credentials": True,
            "can_delete_credentials": False,
            "can_reveal_passwords": True,
            "can_manage_permissions": False,
            "can_audit_logs": True,
            "can_export_data": True,
            "can_import_data": False,
            "can_manage_templates": False
        }
    },
    "admin": {
        "name": "مدير",
        "name_en": "Administrator",
        "description": "صلاحيات كاملة للمدراء",
        "description_en": "Full permissions for administrators",
        "permissions": {
            "can_view_credentials": True,
            "can_create_credentials": True,
            "can_edit_credentials": True,
            "can_delete_credentials": True,
            "can_reveal_passwords": True,
            "can_manage_permissions": True,
            "can_audit_logs": True,
            "can_export_data": True,
            "can_import_data": True,
            "can_manage_templates": True
        }
    }
}

# ============ ENCRYPTION UTILITIES ============

class CredentialEncryption:
    def __init__(self, key: str = ENCRYPTION_KEY):
        self.key = key.encode() if isinstance(key, str) else key
        self.fernet = Fernet(base64.urlsafe_b64encode(self.key[:32]))
    
    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data"""
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        return self.fernet.decrypt(encrypted_data.encode()).decode()

credential_encryption = CredentialEncryption()

# ============ MONGODB UTILITIES ============

async def get_work_reports_db():
    """Get work reports MongoDB database (lazy initialization)"""
    return _ensure_work_reports_db()

async def init_work_reports_collections():
    """Initialize MongoDB collections and indexes for work reports - Fast & Non-blocking"""
    try:
        # ✅ Use lazy initialization
        db = _ensure_work_reports_db()
            
        # Create essential indexes only, avoid blocking operations
        import asyncio
        
        # Test connection first with quick timeout
        await asyncio.wait_for(
            db.command("ping"),
            timeout=2.0
        )
        
        # Use background: True for non-blocking index creation
        index_tasks = [
            work_reports_db.clients.create_index("is_active", background=True),
            work_reports_db.work_logs.create_index("date", background=True),
            work_reports_db.user_permissions.create_index("user_id", background=True),
        ]
        
        # Wait only for essential indexes with short timeout
        await asyncio.wait_for(
            asyncio.gather(*index_tasks, return_exceptions=True),
            timeout=3.0  # 3 second timeout
        )
        
        print("Work Reports MongoDB essential indexes created successfully")
        return True
    except asyncio.TimeoutError:
        print("Work Reports index creation timed out - continuing with server startup")
        return True  # Don't fail startup on timeout
    except Exception as e:
        print(f"Warning: Work Reports collections initialization failed: {e}")
        return True  # Don't fail startup on errors

async def init_default_activity_types():
    """Initialize default activity types - Fast & Non-blocking"""
    try:
        if work_reports_db is None:
            print("Work Reports database not available, skipping activity types initialization")
            return 0
            
        # Quick check with timeout
        import asyncio
        existing_count = await asyncio.wait_for(
            work_reports_db.activity_types.count_documents({}, limit=1),
            timeout=2.0
        )
        
        if existing_count > 0:
            print("Activity types already exist, skipping initialization")
            return existing_count
        
        # Only create if none exist - minimal set for faster startup
        default_activities = [
            {
                "id": str(uuid.uuid4()),
                "name": "Tax Consultation",
                "name_ar": "استشارة ضريبية",
                "description": "General tax consultation services",
                "hourly_rate": 300.0,
                "is_billable": True,
                "category": "Consultation",
                "created_at": datetime.utcnow()
            }
        ]
        
        # Fast insert with timeout
        await asyncio.wait_for(
            work_reports_db.activity_types.insert_many(default_activities),
            timeout=2.0
        )
        
        print(f"Initialized {len(default_activities)} default activity types")
        return len(default_activities)
        
    except asyncio.TimeoutError:
        print("Activity types initialization timed out - continuing")
        return 0
    except Exception as e:
        print(f"Warning: Activity types initialization failed: {e}")
        return 0

async def log_work_reports_activity(user_id: str, action_type: str, details: str, 
                                  target_id: Optional[str] = None, before_value: Optional[str] = None, 
                                  after_value: Optional[str] = None):
    """Log work reports audit activity"""
    audit_log = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "action_type": action_type,
        "details": details,
        "target_id": target_id,
        "before_value": before_value,
        "after_value": after_value,
        "timestamp": datetime.utcnow(),
        "ip_address": None  # Can be enhanced later
    }
    
    await work_reports_db.audit_logs.insert_one(audit_log)
    return audit_log["id"]

# Backward compatibility - keep old function names
Client = ClientResponse
ClientCredential = ClientCredentialResponse  
ActivityType = ActivityTypeResponse
WorkLog = WorkLogResponse
WorkReportsAuditLog = dict  # Simple dict for audit logs
UserWorkReportsPermission = UserPermissionResponse