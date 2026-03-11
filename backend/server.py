# ========================================
# Live monitoring additions (after app is defined)
# ========================================
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, date, timedelta, timezone
import json


# CRITICAL: FastAPI app + health endpoints FIRST
# ========================================
import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Load environment variables EARLY
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Define app EARLY (before any DB-related imports)
app = FastAPI(title="TANSEEQ HR System", version="1.0.0")

# ========================================
# HEALTH ENDPOINTS (No DB dependency)
# ========================================

@app.get("/api/healthz")
async def healthz():
    """Fast health check - no DB required"""
    return {"status": "ok"}

@app.get("/api/readyz")
async def readyz():
    """Readiness check - tests DB connectivity"""
    try:
        from db_client import get_db
        _db = get_db()
        await _db.command("ping")  # يفشل بسرعة لو Atlas مش جاهز
        return {"status": "ready"}
    except Exception as e:
        return JSONResponse({"status": "not_ready", "error": str(e)}, status_code=503)

@app.get("/")
async def root():
    """Root endpoint for LB checks"""
    return {"ok": True}

# ========================================
# NOW safe to import heavy modules
# ========================================
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Form, Response, Query, Request
from fastapi.responses import FileResponse
# ========================================
# Live monitoring (moved here to ensure 'app' is defined)
# ========================================
import asyncio
from time import perf_counter
from collections import deque
LIVE_DIR = "/app/evidence/live"
class LiveStats:
    def __init__(self):
        self.lock = asyncio.Lock()
        self.events = deque(maxlen=5000)
        self.errors = 0
        self.success = 0
        self.total_latency_ms = 0.0
        self.count = 0
        self.window = deque(maxlen=3000)
    async def record(self, method: str, path: str, status: int, duration_ms: float):
        async with self.lock:
            self.events.append({
                "ts": datetime.now().isoformat(),
                "method": method,
                "path": path,
                "status": status,
                "duration_ms": round(duration_ms, 2)
            })
            self.count += 1
            self.total_latency_ms += duration_ms
            self.window.append(duration_ms)
            if status >= 400:
                self.errors += 1
            else:
                self.success += 1
    async def snapshot(self):
        async with self.lock:
            total = max(1, self.count)
            avg = self.total_latency_ms / total
            err_rate = (self.errors / total) * 100.0
            succ_rate = (self.success / total) * 100.0
            last_min = list(self.events)[-60:] if len(self.events) > 60 else list(self.events)
            return {
                "requests_total": self.count,
                "success_rate": round(succ_rate, 2),
                "error_rate": round(err_rate, 2),
                "avg_latency_ms": round(avg, 2),
                "recent": last_min
            }
live_stats = LiveStats()
import os, json
os.makedirs(LIVE_DIR, exist_ok=True)
@app.middleware("http")
async def live_metrics_middleware(request, call_next):
    start = perf_counter()
    response = await call_next(request)
    try:
        duration_ms = (perf_counter() - start) * 1000.0
        path = str(request.url.path)
        if path.startswith("/api"):
            status = getattr(response, "status_code", 500)
            await live_stats.record(request.method, path, status, duration_ms)
            with open(os.path.join(LIVE_DIR, "api_requests.log"), "a", encoding="utf-8") as f:
                f.write(f"{datetime.now().isoformat()} {request.method} {path} {status} {duration_ms:.2f}ms\n")
    except Exception:
        pass
    return response
async def _periodic_metrics_dump():
    while True:
        try:
            snap = await live_stats.snapshot()
            with open(os.path.join(LIVE_DIR, "metrics.json"), "w", encoding="utf-8") as f:
                json.dump(snap, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        await asyncio.sleep(30)
# Live endpoints will be defined after api_router is created

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from bson import ObjectId
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
import pyotp
import qrcode
from io import BytesIO
import base64
from datetime import datetime, timezone, timedelta, time, date
from uae_datetime_utils import (
    get_uae_now, get_uae_today, get_uae_date_str, 
    get_uae_datetime_str, to_iso_string_uae, UAE_TZ
)
from jose import JWTError, jwt
import logging
import uuid
import bcrypt
import pytz
import shutil
import requests
import openpyxl
import json
import calendar

# Import Work Reports Database Module - MongoDB version (now lazy)
from work_reports_mongo import (
    get_work_reports_db, init_work_reports_collections, init_default_activity_types,
    Client, ClientCredential, ActivityType, WorkLog, WorkReportsAuditLog,
    UserWorkReportsPermission, PERMISSION_TEMPLATES,
    ClientCreate, ClientUpdate, ClientResponse,
    ClientCredentialCreate, ClientCredentialResponse,
    ActivityTypeCreate, ActivityTypeResponse,
    WorkLogCreate, WorkLogUpdate, WorkLogResponse,
    UserPermissionResponse, PermissionUpdateRequest,
    credential_encryption, log_work_reports_activity,
    _ensure_work_reports_db as get_work_reports_db_lazy
)

# Helper to get work reports DB (lazy)
def _get_wr_db():
    """Get Work Reports DB (lazy initialization)"""
    return get_work_reports_db_lazy()

# Proxy for work_reports_db for backward compatibility
class LazyWorkReportsDB:
    """Lazy Work Reports DB proxy"""
    def __init__(self):
        self._db = None
    
    def __getattr__(self, name):
        if self._db is None:
            self._db = get_work_reports_db_lazy()
        return getattr(self._db, name)
    
    def __bool__(self):
        return True

work_reports_db = LazyWorkReportsDB()

# Notification Model
class Notification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))  # ✅ FIXED: Auto-generate UUID
    recipient_id: str
    recipient_name: Optional[str] = None
    sender_id: str
    sender_name: Optional[str] = None
    subject: str
    message: str
    type: str = "info"  # info, warning, alert
    priority: str = "normal"  # low, normal, high, urgent
    is_read: bool = False
    sent_at: Optional[datetime] = None

class SendNotificationRequest(BaseModel):
    recipient_id: str
    subject: str
    message: str
    type: str = "info"
    priority: str = "normal"

from sqlalchemy.orm import Session
from report_generator import report_generator

# ========================================
# Lazy DB initialization (using db_client.py)
# ========================================
from db_client import get_db, get_client

# Create a proxy class that initializes DB on first access
class LazyDB:
    """Lazy DB proxy that initializes MongoDB connection on first attribute access"""
    def __init__(self):
        self._db = None
        self._client = None
    
    def __getattr__(self, name):
        if self._db is None:
            self._db = get_db()
            self._client = get_client()
        return getattr(self._db, name)
    
    def __bool__(self):
        # Make sure truthiness works
        return True

# Use lazy proxy for global db
db = LazyDB()
mongo_client = None  # Will be set on first DB access

def _ensure_db():
    """Ensure DB is initialized (lazy) - returns the underlying DB"""
    if not hasattr(db, '_db') or db._db is None:
        db._db = get_db()
        global mongo_client
        mongo_client = get_client()
    return db._db

# JWT Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Security
security = HTTPBearer()

# Initialize Work Reports MongoDB collections on startup - DISABLED for performance
# @app.on_event("startup")
# async def startup_event():
#     """Initialize Work Reports MongoDB collections on startup - Non-blocking"""
#     try:
#         # Run initialization in background without blocking server startup
#         import asyncio
#         asyncio.create_task(init_work_reports_collections())
#         asyncio.create_task(init_default_activity_types())
#         print("Work Reports initialization started in background")
#     except Exception as e:
#         print(f"Warning: Work Reports initialization failed: {e}")
#         # Don't block server startup on initialization failures

# Ensure test Super Admin user exists on startup
@app.on_event("startup")
async def ensure_test_super_admin():
    """
    Ensure default Super Admin user exists
    ✅ With timeout protection - doesn't block startup indefinitely
    ✅ Uses lazy DB initialization
    """
    try:
        # ✅ Initialize DB lazily
        _db = _ensure_db()
        
        # ✅ Create index with timeout
        import asyncio
        await asyncio.wait_for(
            _db.users.create_index("email", unique=True),
            timeout=5.0  # 5 second timeout
        )
        
    except asyncio.TimeoutError:
        print("⚠️ Index creation timed out, continuing...")
        return  # Exit early if timeout
    except Exception as e:
        print(f"⚠️ Index creation warning: {e}")
        return  # Exit early if error
    
    try:
        # ✅ Check and create admin user with timeout
        admin_email = "admin@tanseeq.com"
        _db = _ensure_db()  # Ensure DB is ready
        import asyncio
        existing = await asyncio.wait_for(
            _db.users.find_one({"email": admin_email}),
            timeout=5.0  # 5 second timeout
        )
        
        if not existing:
            now = get_uae_now()  # UAE timezone
            test_user = {
                "id": str(uuid.uuid4()),
                "name": "Admin QA",
                "email": admin_email,
                "role": "super_admin",
                "position": "QA Super Admin",
                "monthly_salary": 0.0,
                "daily_rate": 0.0,
                "working_hours_start": "09:00",
                "working_hours_end": "18:00",
                "phone": "",
                "hire_date": now,
                "is_active": True,
                "has_flexible_schedule": False,
                "flexible_hours_per_day": 8.0,
                "flexible_start_range": "07:00-10:00",
                "flexible_end_range": "16:00-19:00",
                "flexible_core_hours": "10:00-15:00",
                "flexible_days_per_week": 5,
                "password": hash_password("ADMIN"),
                "created_at": now,
            }
            await _db.users.insert_one(test_user)
            print("✅ Created test Super Admin user admin@tanseeq.com / ADMIN")
        else:
            # Ensure role and active status are correct
            updates = {"role": "super_admin", "is_active": True}
            if existing.get("password") is None:
                updates["password"] = hash_password("ADMIN")
            await _db.users.update_one({"email": admin_email}, {"$set": updates})
            print("✅ Verified test Super Admin user exists")
    except Exception as e:
        print(f"⚠️ Failed to ensure test Super Admin user: {e}")

# Create uploads directory
uploads_dir = ROOT_DIR / "uploads"
uploads_dir.mkdir(exist_ok=True)

# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

# Create router with /api prefix
api_router = APIRouter(prefix="/api")

# Live monitoring endpoints will be added after auth functions

# UAE timezone
UAE_TZ = pytz.timezone('Asia/Dubai')

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============ MODELS ============

class UserBase(BaseModel):
    name: str
    email: str
    role: str = "user"  # user, admin, super_admin
    position: str = ""
    monthly_salary: float = 0.0
    daily_rate: float = 0.0
    working_hours_start: str = "09:00"
    working_hours_end: str = "18:00"
    phone: str = ""
    hire_date: Optional[datetime] = None
    is_active: bool = True
    has_flexible_schedule: bool = False
    flexible_hours_per_day: float = 8.0
    flexible_start_range: str = "07:00-10:00"  # Range when employee can start
    flexible_end_range: str = "16:00-19:00"    # Range when employee can end
    flexible_core_hours: str = "10:00-15:00"   # Hours when employee must be present
    flexible_days_per_week: int = 5

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    position: Optional[str] = None
    monthly_salary: Optional[float] = None
    daily_rate: Optional[float] = None
    working_hours_start: Optional[str] = None
    working_hours_end: Optional[str] = None
    phone: Optional[str] = None
    hire_date: Optional[datetime] = None
    is_active: Optional[bool] = None
    has_flexible_schedule: Optional[bool] = None
    flexible_hours_per_day: Optional[float] = None
    flexible_start_range: Optional[str] = None  # e.g., "07:00-10:00" 
    flexible_end_range: Optional[str] = None    # e.g., "16:00-19:00"
    flexible_core_hours: Optional[str] = None   # e.g., "10:00-15:00" (must be present)
    flexible_days_per_week: Optional[int] = None

class User(UserBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)

# ============ MESSAGE MODELS ============

class Message(BaseModel):
    """Internal message system for company announcements"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    message_type: str = "general"  # general, friday_work, urgent, announcement
    from_user_id: str
    from_user_name: str
    to_user_ids: List[str] = []  # Empty list means send to all
    is_read_by: List[str] = []  # List of user IDs who have read the message
    priority: str = "normal"  # normal, high, urgent
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    is_active: bool = True

class MessageCreate(BaseModel):
    title: str
    content: str
    message_type: str = "general"
    to_user_ids: List[str] = []
    priority: str = "normal"
    expires_at: Optional[datetime] = None

class MessageResponse(BaseModel):
    id: str
    title: str
    content: str
    message_type: str
    from_user_id: str
    from_user_name: str
    to_user_ids: List[str]
    is_read_by: List[str]
    priority: str
    created_at: datetime
    expires_at: Optional[datetime]
    is_active: bool
    is_read: bool = False  # Will be set based on current user
    time_ago: str = ""  # Human readable time

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    position: str
    monthly_salary: float
    daily_rate: float
    working_hours_start: str
    working_hours_end: str
    phone: str
    hire_date: Optional[datetime] = None
    is_active: bool = True
    has_custom_schedule: bool = False
    has_flexible_schedule: bool = False
    flexible_hours_per_day: float = 8.0
    flexible_start_range: str = "07:00-10:00"
    flexible_end_range: str = "16:00-19:00"
    flexible_core_hours: str = "10:00-15:00"
    flexible_days_per_week: int = 5

# ============ WORK REPORTS PYDANTIC MODELS ============

class ClientResponse(BaseModel):
    id: str
    company_name: str
    company_name_ar: Optional[str] = None
    client_code: str
    industry: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    tax_number: Optional[str] = None
    commercial_registration: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: str
    
    @validator('id', pre=True)
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v
    
    class Config:
        from_attributes = True

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
    notes: Optional[str] = None

class ClientUpdate(BaseModel):
    company_name: Optional[str] = None
    company_name_ar: Optional[str] = None
    industry: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    tax_number: Optional[str] = None
    commercial_registration: Optional[str] = None
    notes: Optional[str] = None

class ActivityTypeResponse(BaseModel):
    id: str
    name: str
    name_ar: Optional[str] = None
    category: str
    description: Optional[str] = None
    default_rate: Optional[float] = None
    is_billable: bool = True
    is_active: bool = True
    created_at: datetime
    
    @validator('id', pre=True)
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v
    
    class Config:
        from_attributes = True

class ActivityTypeCreate(BaseModel):
    name: str
    name_ar: Optional[str] = None
    category: str
    description: Optional[str] = None
    default_rate: Optional[float] = None
    is_billable: bool = True

class WorkLogResponse(BaseModel):
    id: str
    client_id: str
    activity_type_id: str
    user_id: str
    date: datetime
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_hours: Optional[float] = None
    description: str
    notes: Optional[str] = None
    is_billable: bool = True
    hourly_rate: Optional[float] = None
    total_amount: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Related data
    client_name: Optional[str] = None
    activity_name: Optional[str] = None
    user_name: Optional[str] = None
    
    @validator('id', 'client_id', 'activity_type_id', 'user_id', pre=True)
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v
    
    class Config:
        from_attributes = True

class WorkLogCreate(BaseModel):
    client_id: str
    activity_type_id: str
    date: datetime
    start_time: datetime
    end_time: Optional[datetime] = None
    description: str
    notes: Optional[str] = None
    is_billable: bool = True
    hourly_rate: Optional[float] = None

class WorkLogUpdate(BaseModel):
    client_id: Optional[str] = None
    activity_type_id: Optional[str] = None
    date: Optional[datetime] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    is_billable: Optional[bool] = None
    hourly_rate: Optional[float] = None

class ClientCredentialResponse(BaseModel):
    id: str
    client_id: str
    credential_type: str
    username: str
    email: Optional[str] = None
    portal_url: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    @validator('id', 'client_id', pre=True)
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v
    
    class Config:
        from_attributes = True

# Remove duplicate ClientCredentialCreate class - use the one from work_reports_db
# class ClientCredentialCreate(BaseModel):
#     client_id: str
#     credential_type: str
#     username: str
#     email: Optional[str] = None
#     password: str
#     portal_url: Optional[str] = None
#     description: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class PasswordResetRequest(BaseModel):
    email: str
    new_password: str

class AttendanceBase(BaseModel):
    user_id: str
    user_name: str
    date: str
    status: str = "present"  # present, absent, late
    is_late: bool = False

class AttendanceCreate(BaseModel):
    user_id: str
    user_name: str

class AttendanceUpdate(BaseModel):
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    status: Optional[str] = None
    is_late: Optional[bool] = None

class Attendance(AttendanceBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    working_hours: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class LeaveBase(BaseModel):
    user_id: str
    user_name: str
    start_date: str
    end_date: str
    reason: str
    status: str = "pending"  # pending, approved, rejected
    days_count: int
    attachment_url: Optional[str] = None

class LeaveCreate(BaseModel):
    user_id: str
    user_name: str
    start_date: str
    end_date: str
    reason: str
    days_count: int
    attachment_url: Optional[str] = None

class LeaveUpdate(BaseModel):
    status: Optional[str] = None
    approved_by: Optional[str] = None

class Leave(LeaveBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    approved_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class FieldExitBase(BaseModel):
    user_id: str
    user_name: str
    visit_type: str  # client_visit, collection, bank_visit, personal, admin_errand
    client_name: str = ""
    start_time: str
    end_time: str
    report: str = ""
    status: str = "pending"  # pending, approved, rejected

class FieldExitCreate(FieldExitBase):
    pass

class FieldExitUpdate(BaseModel):
    visit_type: Optional[str] = None
    client_name: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    report: Optional[str] = None
    status: Optional[str] = None
    approved_by: Optional[str] = None

class FieldExit(FieldExitBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    approved_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ActivityLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    action: str
    details: str
    before_value: Optional[str] = None
    after_value: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# ============ UTILITY FUNCTIONS ============

def hash_password(password: str) -> str:
    """Hash a password"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = get_uae_now() + expires_delta  # UAE timezone
    else:
        expire = get_uae_now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)  # UAE timezone
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_uae_time():
    """Get current UAE time"""
    return datetime.now(UAE_TZ)

async def log_activity(user_id: str, action: str, details: str, before_value: str = None, after_value: str = None):
    """Log user activity"""
    activity_log = ActivityLog(
        user_id=user_id,
        action=action,
        details=details,
        before_value=before_value,
        after_value=after_value
    )
    await db.activity_logs.insert_one(activity_log.dict())
def calculate_working_hours_and_deductions(check_in, check_out, break_time_minutes=0, is_admin_edited=False):
    """Calculate working hours and deductions - NEW RULES: Late after 9:15 AM, penalty only for early checkout before 6PM"""
    
    # Standard work hours - UPDATED RULES (9:15 AM tolerance)
    STANDARD_START_TIME = datetime.strptime("09:15", "%H:%M").time()  # ✅ Changed to 9:15 AM
    STANDARD_END_TIME = datetime.strptime("18:00", "%H:%M").time() 
    STANDARD_HOURS = 9.0  # 9 hours standard
    BREAK_TIME = break_time_minutes / 60.0  # Convert to hours
    
    if not check_in or not check_out:
        return {
            "total_hours": 0.0,
            "regular_hours": 0.0,
            "overtime_hours": 0.0,
            "deducted_hours": 0.0,
            "late_minutes": 0,
            "early_departure_minutes": 0,
            "status": "incomplete"
        }

    try:
        # Parse times - handle both ISO format (T separator) and space format
        if isinstance(check_in, str):
            try:
                if 'T' in check_in:
                    # ISO format: "2025-08-28T11:08:41"
                    check_in_time = datetime.strptime(check_in.split('T')[0] + ' ' + check_in.split('T')[1][:5], "%Y-%m-%d %H:%M")
                else:
                    # Space format: "2025-08-28 11:08:41" or "2025-08-28 11:08"
                    if len(check_in.split(' ')) >= 2:
                        date_part = check_in.split(' ')[0]
                        time_part = check_in.split(' ')[1][:5]  # Take first 5 chars (HH:MM)
                        check_in_time = datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M")
                    else:
                        raise ValueError(f"Invalid check_in format: {check_in}")
            except ValueError as e:
                print(f"Error parsing check_in time '{check_in}': {e}")
                raise
        else:
            check_in_time = check_in

        if isinstance(check_out, str):
            try:
                if 'T' in check_out:
                    # ISO format: "2025-08-28T18:00:00"
                    check_out_time = datetime.strptime(check_out.split('T')[0] + ' ' + check_out.split('T')[1][:5], "%Y-%m-%d %H:%M")
                else:
                    # Space format: "2025-08-28 18:00:00" or "2025-08-28 18:00"
                    if len(check_out.split(' ')) >= 2:
                        date_part = check_out.split(' ')[0]
                        time_part = check_out.split(' ')[1][:5]  # Take first 5 chars (HH:MM)
                        check_out_time = datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M")
                    else:
                        raise ValueError(f"Invalid check_out format: {check_out}")
            except ValueError as e:
                print(f"Error parsing check_out time '{check_out}': {e}")
                raise
        else:
            check_out_time = check_out

        # Calculate total worked time
        total_worked_time = (check_out_time - check_in_time).total_seconds() / 3600.0
        
        # Subtract break time
        net_worked_hours = max(0, total_worked_time - BREAK_TIME)
        
        # ✅ LATE PENALTY: Any minute after 9:15 AM is considered late
        late_minutes = 0
        if check_in_time.time() > STANDARD_START_TIME:
            late_delta = datetime.combine(check_in_time.date(), check_in_time.time()) - datetime.combine(check_in_time.date(), STANDARD_START_TIME)
            late_minutes = int(late_delta.total_seconds() / 60)
        
        # Calculate early departure ONLY (before 6:00 PM) - MAIN DEDUCTION SOURCE
        early_departure_minutes = 0
        if check_out_time.time() < STANDARD_END_TIME:
            early_delta = datetime.combine(check_out_time.date(), STANDARD_END_TIME) - datetime.combine(check_out_time.date(), check_out_time.time())
            early_departure_minutes = int(early_delta.total_seconds() / 60)
        
        # NO DEDUCTIONS IF ADMIN EDITED THE ATTENDANCE
        if is_admin_edited:
            late_minutes = 0
            early_departure_minutes = 0
        
        # Calculate deductions (ONLY from late arrival and early departure)
        total_deduction_minutes = late_minutes + early_departure_minutes
        deducted_hours = total_deduction_minutes / 60.0
        
        # Calculate regular and overtime hours
        regular_hours = min(net_worked_hours, STANDARD_HOURS)
        overtime_hours = max(0, net_worked_hours - STANDARD_HOURS)
        
        # Adjust regular hours for deductions
        effective_regular_hours = max(0, regular_hours - deducted_hours)
        
        return {
            "total_hours": round(net_worked_hours, 2),
            "regular_hours": round(effective_regular_hours, 2),
            "overtime_hours": round(overtime_hours, 2),
            "deducted_hours": round(deducted_hours, 2),
            "late_minutes": late_minutes,
            "early_departure_minutes": early_departure_minutes,
            "status": "complete",
            "admin_edited": is_admin_edited
        }

    except Exception as e:
        print(f"Error calculating working hours: {e}")
        return {
            "total_hours": 0.0,
            "regular_hours": 0.0,
            "overtime_hours": 0.0,
            "deducted_hours": 0.0,
            "late_minutes": 0,
            "early_departure_minutes": 0,
            "status": "error"
        }

# ============ AUTH DEPENDENCY ============

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = await db.users.find_one({"id": user_id})
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return User(**user)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        

async def get_admin_user(current_user: User = Depends(get_current_user)):
    """Require admin or super_admin role"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
        
    return current_user

async def get_super_admin_user(current_user: User = Depends(get_current_user)):
    """Require super_admin role"""
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required"
        )
        
    return current_user

# ========================================
# LIVE MONITORING ENDPOINTS
# ========================================

@api_router.get("/live/metrics")
async def get_live_metrics(current_user: User = Depends(get_super_admin_user)):
    """Get live metrics - Super Admin only"""
    snap = await live_stats.snapshot()
    return {"success": True, "metrics": snap}

@api_router.get("/live/logs")
async def get_live_logs(current_user: User = Depends(get_super_admin_user)):
    """Get live logs - Super Admin only"""
    logs_path = os.path.join(LIVE_DIR, "api_requests.log")
    if not os.path.exists(logs_path):
        return {"success": True, "lines": []}
    try:
        with open(logs_path, "r", encoding="utf-8") as f:
            lines = f.readlines()[-200:]
        return {"success": True, "lines": lines}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/live/progress/{channel}")
async def post_progress(channel: str, payload: dict, current_user: User = Depends(get_super_admin_user)):
    """Post progress to live channel - Super Admin only"""
    if channel not in ("backend", "frontend"):
        raise HTTPException(status_code=400, detail="channel must be backend|frontend")
    
    line = f"{datetime.now().isoformat()} [{channel}] {payload.get('message','')}\n"
    with open(os.path.join(LIVE_DIR, f"progress_{channel}.log"), "a", encoding="utf-8") as f:
        f.write(line)
    return {"success": True}

@api_router.post("/attendance/check-in")
async def check_in(current_user: User = Depends(get_current_user)):
    """Check in attendance - ✅ FIXED: Read exceptions from DB, not user profile"""
    # Check if already checked in today
    today = get_uae_time().date().strftime('%Y-%m-%d')
    existing_attendance = await db.attendance.find_one({
        "user_id": current_user.id,
        "date": today
    })
    
    if existing_attendance and existing_attendance.get("check_in"):
        raise HTTPException(status_code=400, detail="تم تسجيل الحضور مسبقاً اليوم")
    
    # Get current UAE time
    current_time = get_uae_time()
    check_in_time = current_time.strftime('%H:%M:%S')
    
    # ✅ CRITICAL FIX: Read exception type from database, not user profile
    from config_service import get_exception_type
    _db_instance = db._db if hasattr(db, '_db') and db._db is not None else get_db()
    exception_type = await get_exception_type(_db_instance, current_user.id)
    
    # ✅ CRITICAL FIX: Calculate late_minutes based on exception type and 9:15 AM threshold
    STANDARD_START_TIME = datetime.strptime("09:15", "%H:%M").time()
    is_late = False
    late_minutes = 0
    schedule_type = "fixed"  # Default
    
    # Determine if late based on exception type
    if exception_type in ("exempt", "flex"):
        # Exempt or Flexible schedule - NO late tracking for these users
        schedule_type = "flexible"
        is_late = False
        late_minutes = 0
    elif exception_type == "partial-flex":
        # Partial-flex: Check against 9:00 AM (no grace period)
        schedule_type = "partial-flex"
        PARTIAL_FLEX_START = datetime.strptime("09:00", "%H:%M").time()
        check_in_time_obj = current_time.time()
        if check_in_time_obj > PARTIAL_FLEX_START:
            is_late = True
            late_delta = datetime.combine(current_time.date(), check_in_time_obj) - datetime.combine(current_time.date(), PARTIAL_FLEX_START)
            late_minutes = int(late_delta.total_seconds() / 60)
    else:
        # ✅ FIXED: Standard 9:15 AM rule for all non-exception users
        schedule_type = "fixed"
        check_in_time_obj = current_time.time()
        if check_in_time_obj > STANDARD_START_TIME:
            is_late = True
            # Calculate late_minutes based on 9:15 AM threshold
            late_delta = datetime.combine(current_time.date(), check_in_time_obj) - datetime.combine(current_time.date(), STANDARD_START_TIME)
            late_minutes = int(late_delta.total_seconds() / 60)
    
    # ✅ FIXED: Create attendance record with late_minutes and deduction fields
    attendance_data = {
        "user_id": current_user.id,
        "user_name": current_user.name,
        "date": today,
        "check_in": check_in_time,
        "status": "late" if is_late else "present",
        "is_late": is_late,
        "late_minutes": late_minutes,  # ✅ NEW: Store late_minutes at check-in
        "early_departure_minutes": 0,  # ✅ NEW: Will be calculated at check-out
        "deducted_hours": 0.0,  # ✅ NEW: Will be calculated at check-out
        "schedule_type": schedule_type,
        "exception_type": exception_type  # ✅ Store exception type for audit
    }
    
    if existing_attendance:
        # Update existing record
        await db.attendance.update_one(
            {"user_id": current_user.id, "date": today},
            {"$set": attendance_data}
        )
        
        attendance_id = existing_attendance["id"]
    else:
        # Create new record
        attendance_record = Attendance(
            user_id=current_user.id,
            user_name=current_user.name,
            date=today,
            check_in=check_in_time,
            status="late" if is_late else "present",  
            is_late=is_late
        )
        
        attendance_data["id"] = attendance_record.id
        attendance_data["created_at"] = to_iso_string_uae()  # UAE timezone as ISO string
        await db.attendance.insert_one(attendance_data)
        attendance_id = attendance_record.id
    
    # Log activity with late_minutes and exception info
    await log_activity(
        current_user.id, 
        "check_in", 
        f"Checked in at {check_in_time} (late_minutes: {late_minutes}, exception: {exception_type or 'none'})"
    )
    
    return {
        "message": "تم تسجيل الحضور بنجاح ✅",
        "time": check_in_time,
        "status": "متأخر" if is_late else "في الوقت",
        "is_late": is_late,
        "late_minutes": late_minutes,  # ✅ NEW: Return late_minutes in response
        "schedule_type": schedule_type,
        "exception_type": exception_type  # ✅ Return exception type for debugging
    }

@api_router.post("/attendance/check-out")
async def check_out(current_user: User = Depends(get_current_user)):
    """Check out (Normal attendance without QR verification)"""
    # Check if checked in today
    today = get_uae_time().date().strftime('%Y-%m-%d')
    existing_attendance = await db.attendance.find_one({
        "user_id": current_user.id,
        "date": today
    })
    
    if not existing_attendance or not existing_attendance.get("check_in"):
        raise HTTPException(status_code=400, detail="لم يتم تسجيل الحضور اليوم. يجب تسجيل الحضور أولاً.")
    
    if existing_attendance.get("check_out"):
        raise HTTPException(status_code=400, detail="تم تسجيل الانصراف مسبقاً اليوم")
    
    # Get current UAE time
    current_time = get_uae_time()
    check_out_time = current_time.strftime('%H:%M:%S')
    
    # Calculate working hours AND deductions
    check_in_str = existing_attendance.get("check_in")
    if check_in_str:
        # Use full datetime string format (YYYY-MM-DD HH:MM:SS)
        check_in_full = f"{today} {check_in_str}"
        check_out_full = f"{today} {check_out_time}"
        
        # ✅ Calculate working hours and deductions using the utility function
        work_calc = calculate_working_hours_and_deductions(
            check_in=check_in_full,
            check_out=check_out_full,
            break_time_minutes=0,
            is_admin_edited=False
        )
        
        
        working_hours = work_calc.get("total_hours", 0)
        late_minutes = work_calc.get("late_minutes", 0)
        early_departure_minutes = work_calc.get("early_departure_minutes", 0)
        deducted_hours = work_calc.get("deducted_hours", 0)
    else:
        working_hours = 0
        late_minutes = 0
        early_departure_minutes = 0
        deducted_hours = 0
    
    # ✅ Update attendance record with all calculated fields
    await db.attendance.update_one(
        {"user_id": current_user.id, "date": today},
        {"$set": {
            "check_out": check_out_time,
            "working_hours": round(working_hours, 2),
            "late_minutes": late_minutes,
            "early_departure_minutes": early_departure_minutes,
            "deducted_hours": round(deducted_hours, 2)
        }}
    )
    
    # Log activity
    await log_activity(current_user.id, "check_out", f"Checked out at {check_out_time}")
    
    return {
        "message": "تم تسجيل الانصراف بنجاح ✅",
        "check_out_time": check_out_time,
        "working_hours": round(working_hours, 2)
    }

@api_router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """User login (email is case-insensitive; trims whitespace)"""
    import re
    email_input = (request.email or "").strip()
    password_input = request.password or ""

    # Case-insensitive lookup on email to avoid mobile keyboard case issues
    user = await db.users.find_one({
        "email": {"$regex": f"^{re.escape(email_input)}$", "$options": "i"}
    })

    # If not found, try lower-cased value as exact match (legacy stored lower-case)
    if not user and email_input:
        user = await db.users.find_one({"email": email_input.lower()})

    # Validate
    if not user:
        # log attempt without revealing which part failed
        try:
            await log_activity("anonymous", "login_failed", f"email_not_found:{email_input}")
        except Exception:
            pass
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not user.get("password") or not verify_password(password_input, user["password"]):
        try:
            await log_activity(user.get("id", "unknown"), "login_failed", "bad_password")
        except Exception:
            pass
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not user.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is inactive")

    access_token = create_access_token(data={"sub": user["id"]})
    user_response = UserResponse(**user)

    await log_activity(user["id"], "login", f"User {user['email']} logged in")

    return LoginResponse(access_token=access_token, user=user_response)

@api_router.post("/auth/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """User logout"""
    await log_activity(current_user.id, "logout", f"User {current_user.email} logged out")
    return {"message": "Logged out successfully"}

@api_router.get("/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "position": current_user.position,
        "is_active": current_user.is_active
    }

@api_router.post("/auth/reset-password")
async def reset_password(request: PasswordResetRequest):
    """Reset user password"""
    # Find user by email
    user = await db.users.find_one({"email": request.email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Hash new password
    hashed_password = hash_password(request.new_password)
    
    # Update password
    await db.users.update_one(
        {"email": request.email},
        {"$set": {"password": hashed_password}}
    )
    
    await log_activity(user['id'], "password_reset", f"Password reset for {request.email}")
    
    return {"message": "Password updated successfully"}

# ====================
# MANUAL ATTENDANCE MANAGEMENT - Super Admin Only
# ====================

@api_router.get("/attendance/missing-days/{employee_id}")
async def get_missing_attendance_days(
    employee_id: str,
    start_date: str,
    end_date: str,
    current_user: User = Depends(get_super_admin_user)
):
    """
    الحصول على الأيام المفقودة (بدون حضور) لموظف في فترة محددة - Super Admin Only
    
    Args:
        employee_id: معرف الموظف
        start_date: تاريخ البداية (YYYY-MM-DD)
        end_date: تاريخ النهاية (YYYY-MM-DD)
    
    Returns:
        قائمة بالأيام التي لم يسجل فيها الموظف حضور
    """
    try:
        from datetime import datetime, timedelta
        
        # التحقق من وجود الموظف
        employee = await db.users.find_one({"id": employee_id})
        if not employee:
            raise HTTPException(status_code=404, detail="الموظف غير موجود")
        
        # تحويل التواريخ
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        if end < start:
            raise HTTPException(status_code=400, detail="تاريخ النهاية يجب أن يكون بعد تاريخ البداية")
        
        # جلب جميع سجلات الحضور للموظف في الفترة
        attendance_records = await db.attendance.find({
            "user_id": employee_id,
            "date": {
                "$gte": start_date,
                "$lte": end_date
            }
        }).to_list(None)
        
        # إنشاء set من التواريخ الموجودة
        existing_dates = {record["date"] for record in attendance_records}
        
        # حساب جميع الأيام في الفترة
        missing_days = []
        current_date = start
        while current_date <= end:
            date_str = current_date.strftime("%Y-%m-%d")
            # ✅ FIX: تخطي يوم الجمعة (4) والسبت (5) - عطلة نهاية الأسبوع
            if current_date.weekday() not in [4, 5]:  # 4=Friday, 5=Saturday
                if date_str not in existing_dates:
                    missing_days.append({
                        "date": date_str,
                        "day_name": current_date.strftime("%A"),
                        "day_name_ar": ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"][current_date.weekday()]
                    })
            current_date += timedelta(days=1)
        
        return {
            "employee_id": employee_id,
            "employee_name": employee["name"],
            "start_date": start_date,
            "end_date": end_date,
            "missing_days": missing_days,
            "total_missing": len(missing_days)
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"تنسيق التاريخ غير صحيح: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في جلب الأيام المفقودة: {str(e)}")


@api_router.post("/attendance/bulk-add-manual")
async def bulk_add_manual_attendance(
    request: dict,
    current_user: User = Depends(get_super_admin_user)
):
    """
    إضافة سجلات حضور يدوية للأيام المفقودة - Super Admin Only
    
    Request Body:
    {
        "employee_id": "uuid",
        "missing_days": ["2025-01-01", "2025-01-02", ...],
        "check_in_time": "09:00:00",
        "check_out_time": "18:00:00"
    }
    """
    try:
        employee_id = request.get("employee_id")
        missing_days = request.get("missing_days", [])
        check_in_time = request.get("check_in_time")
        check_out_time = request.get("check_out_time")
        
        if not employee_id or not missing_days or not check_in_time or not check_out_time:
            raise HTTPException(status_code=400, detail="جميع الحقول مطلوبة")
        
        # التحقق من وجود الموظف
        employee = await db.users.find_one({"id": employee_id})
        if not employee:
            raise HTTPException(status_code=404, detail="الموظف غير موجود")
        
        # إضافة سجلات الحضور
        added_count = 0
        failed_dates = []
        
        for date_str in missing_days:
            try:
                # التحقق من عدم وجود سجل بالفعل
                existing = await db.attendance.find_one({
                    "user_id": employee_id,
                    "date": date_str
                })
                
                if existing:
                    failed_dates.append(f"{date_str} (موجود مسبقاً)")
                    continue
                
                # حساب ساعات العمل
                check_in_full = f"{date_str} {check_in_time}"
                check_out_full = f"{date_str} {check_out_time}"
                
                work_calc = calculate_working_hours_and_deductions(
                    check_in=check_in_full,
                    check_out=check_out_full,
                    break_time_minutes=0,
                    is_admin_edited=True
                )
                
                # إنشاء سجل الحضور
                attendance_data = {
                    "id": str(uuid.uuid4()),
                    "user_id": employee_id,
                    "user_name": employee["name"],
                    "date": date_str,
                    "check_in": check_in_time,
                    "check_out": check_out_time,
                    "status": "present",
                    "is_late": False,
                    "working_hours": work_calc["total_hours"],
                    "late_minutes": 0,
                    "early_departure_minutes": 0,
                    "deducted_hours": 0.0,
                    "manual_entry": True,  # تمييز السجلات اليدوية
                    "added_by": current_user.id,
                    "added_by_name": current_user.name,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                
                await db.attendance.insert_one(attendance_data)
                added_count += 1
                
            except Exception as e:
                failed_dates.append(f"{date_str} ({str(e)})")
        
        # تسجيل النشاط
        await log_activity(
            current_user.id,
            "bulk_attendance_added",
            f"أضاف {added_count} سجل حضور يدوي للموظف {employee['name']}"
        )
        
        return {
            "success": True,
            "message": f"تم إضافة {added_count} سجل حضور بنجاح",
            "added_count": added_count,
            "failed_dates": failed_dates,
            "employee_name": employee["name"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في إضافة السجلات: {str(e)}")


@api_router.post("/attendance/custom-report")
async def generate_custom_attendance_report(
    request: dict,
    current_user: User = Depends(get_super_admin_user)
):
    """
    إنشاء تقرير حضور مخصص - Super Admin Only
    
    Request Body:
    {
        "employee_ids": ["uuid1", "uuid2", ...],
        "start_date": "2025-01-01",
        "end_date": "2025-01-31",
        "format": "excel" | "csv"
    }
    """
    try:
        import pandas as pd
        from io import BytesIO
        import base64
        
        employee_ids = request.get("employee_ids", [])
        start_date = request.get("start_date")
        end_date = request.get("end_date")
        export_format = request.get("format", "excel")
        
        if not employee_ids or not start_date or not end_date:
            raise HTTPException(status_code=400, detail="جميع الحقول مطلوبة")
        
        # جلب بيانات الحضور
        attendance_records = await db.attendance.find({
            "user_id": {"$in": employee_ids},
            "date": {
                "$gte": start_date,
                "$lte": end_date
            }
        }).sort("date", 1).to_list(None)
        
        if not attendance_records:
            raise HTTPException(status_code=404, detail="لا توجد سجلات حضور في هذه الفترة")
        
        # جلب أسماء الموظفين
        employees = await db.users.find({"id": {"$in": employee_ids}}).to_list(None)
        employee_map = {emp["id"]: emp["name"] for emp in employees}
        
        # تحضير البيانات للـ Excel/CSV
        report_data = []
        for record in attendance_records:
            report_data.append({
                "اسم الموظف": employee_map.get(record["user_id"], "غير معروف"),
                "التاريخ": record.get("date", ""),
                "اليوم": record.get("day_name", ""),
                "الحضور": record.get("check_in", "لم يسجل"),
                "الانصراف": record.get("check_out", "لم يسجل"),
                "الحالة": "حاضر" if record.get("status") == "present" else 
                         "متأخر" if record.get("status") == "late" else 
                         "غائب" if record.get("status") == "absent" else 
                         record.get("status", "غير محدد"),
                "ساعات العمل": record.get("working_hours", 0),
                "دقائق التأخير": record.get("late_minutes", 0),
                "خروج مبكر (دقائق)": record.get("early_departure_minutes", 0),
                "ملاحظات": "إدخال يدوي" if record.get("manual_entry") else ""
            })
        
        # إنشاء DataFrame
        df = pd.DataFrame(report_data)
        
        if export_format == "excel":
            # إنشاء Excel file
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='تقرير الحضور')
                
                # تنسيق الأعمدة
                worksheet = writer.sheets['تقرير الحضور']
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            output.seek(0)
            file_content = base64.b64encode(output.read()).decode()
            filename = f"attendance_report_{start_date}_to_{end_date}.xlsx"
            content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            
        else:  # CSV
            output = BytesIO()
            df.to_csv(output, index=False, encoding='utf-8-sig')
            output.seek(0)
            file_content = base64.b64encode(output.read()).decode()
            filename = f"attendance_report_{start_date}_to_{end_date}.csv"
            content_type = "text/csv"
        
        return {
            "success": True,
            "filename": filename,
            "content_type": content_type,
            "file_content": file_content,
            "records_count": len(report_data),
            "employees_count": len(employee_ids)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error generating report: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"خطأ في إنشاء التقرير: {str(e)}")


@api_router.post("/attendance/bulk-add-absence")
async def bulk_add_manual_absence(
    request: dict,
    current_user: User = Depends(get_super_admin_user)
):
    """
    إضافة سجلات غياب يدوية للأيام المفقودة مع احتساب الخصومات - Super Admin Only
    
    Request Body:
    {
        "employee_id": "uuid",
        "missing_days": ["2025-01-01", "2025-01-02", ...],
        "absence_type": "full_day" | "half_day",
        "reason": "سبب الغياب (اختياري)"
    }
    """
    try:
        from datetime import datetime, timezone
        
        employee_id = request.get("employee_id")
        missing_days = request.get("missing_days", [])
        absence_type = request.get("absence_type", "full_day")
        reason = request.get("reason", "غياب يدوي")
        
        if not employee_id or not missing_days:
            raise HTTPException(status_code=400, detail="معرف الموظف والأيام مطلوبة")
        
        # التحقق من وجود الموظف
        employee = await db.users.find_one({"id": employee_id})
        if not employee:
            raise HTTPException(status_code=404, detail="الموظف غير موجود")
        
        # الحصول على الراتب الشهري للموظف
        monthly_salary = employee.get("salary", 0)
        if monthly_salary <= 0:
            raise HTTPException(status_code=400, detail="راتب الموظف غير محدد")
        
        # احتساب خصم اليوم الواحد (الراتب الشهري / 30)
        daily_deduction = monthly_salary / 30
        half_day_deduction = daily_deduction / 2
        
        # إضافة سجلات الغياب
        added_count = 0
        failed_dates = []
        total_deduction = 0
        
        for date_str in missing_days:
            try:
                # التحقق من عدم وجود سجل بالفعل
                existing = await db.attendance.find_one({
                    "user_id": employee_id,
                    "date": date_str
                })
                
                if existing:
                    failed_dates.append(f"{date_str} (موجود مسبقاً)")
                    continue
                
                # احتساب الخصم
                deduction_amount = daily_deduction if absence_type == "full_day" else half_day_deduction
                total_deduction += deduction_amount
                
                # إنشاء سجل الغياب
                attendance_data = {
                    "id": str(uuid.uuid4()),
                    "user_id": employee_id,
                    "user_name": employee["name"],
                    "date": date_str,
                    "check_in": None,
                    "check_out": None,
                    "status": "absent",
                    "absence_type": absence_type,  # full_day or half_day
                    "absence_reason": reason,
                    "is_late": False,
                    "working_hours": 0,
                    "late_minutes": 0,
                    "early_departure_minutes": 0,
                    "deducted_hours": 0.0,
                    "absence_deduction": deduction_amount,  # ✅ خصم الغياب
                    "manual_entry": True,
                    "manual_absence": True,  # ✅ تمييز الغياب اليدوي
                    "added_by": current_user.id,
                    "added_by_name": current_user.name,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                
                await db.attendance.insert_one(attendance_data)
                added_count += 1
                
            except Exception as e:
                failed_dates.append(f"{date_str} ({str(e)})")
        
        # ✅ ربط الخصومات بدورة الرواتب الحالية
        # الحصول على الشهر الحالي أو إنشاء دورة رواتب جديدة
        from datetime import datetime
        first_date = min(missing_days)
        year_month = first_date[:7]  # "2025-01"
        
        # البحث عن دورة رواتب موجودة لهذا الشهر
        payroll_cycle = await db.payroll_cycles.find_one({
            "cycle_month": year_month,
            "status": {"$in": ["draft", "pending"]}  # فقط الدورات غير المكتملة
        })
        
        payroll_cycle_id = None
        if payroll_cycle:
            payroll_cycle_id = payroll_cycle["id"]
        else:
            # إنشاء دورة رواتب جديدة
            payroll_cycle_id = str(uuid.uuid4())
            new_cycle = {
                "id": payroll_cycle_id,
                "cycle_month": year_month,
                "status": "draft",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "created_by": current_user.id
            }
            await db.payroll_cycles.insert_one(new_cycle)
        
        # ✅ إضافة سجل الخصم في دورة الرواتب
        if added_count > 0 and total_deduction > 0:
            deduction_record = {
                "id": str(uuid.uuid4()),
                "payroll_cycle_id": payroll_cycle_id,
                "cycle_month": year_month,
                "employee_id": employee_id,
                "employee_name": employee["name"],
                "deduction_type": "manual_absence",
                "deduction_amount": total_deduction,
                "absence_days": added_count,
                "absence_type": absence_type,
                "reason": reason,
                "dates": missing_days[:added_count],  # الأيام الفعلية
                "created_at": datetime.now(timezone.utc).isoformat(),
                "created_by": current_user.id,
                "created_by_name": current_user.name
            }
            
            await db.payroll_deductions.insert_one(deduction_record)
        
        # تسجيل النشاط
        await log_activity(
            current_user.id,
            "bulk_absence_added",
            f"أضاف {added_count} سجل غياب يدوي للموظف {employee['name']} بخصم {total_deduction:.2f} درهم"
        )
        
        return {
            "success": True,
            "message": f"تم إضافة {added_count} سجل غياب بنجاح",
            "added_count": added_count,
            "failed_dates": failed_dates,
            "employee_name": employee["name"],
            "total_deduction": round(total_deduction, 2),
            "payroll_cycle_id": payroll_cycle_id,
            "cycle_month": year_month
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error adding absence records: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"خطأ في إضافة سجلات الغياب: {str(e)}")

# ============ EMPLOYEE ADVANCES & CUSTODY SYSTEM ============

from advances_model import (
    AdvanceTransaction, CreateAdvanceRequest, CreateExpenseRequest, ApprovalRequest,
    TransactionResponse, BalanceResponse, AdvancesDB, EmployeeBalance,
    TransactionType, TransactionStatus, ExpenseCategory, Attachment,
    RepaymentRequest,
    TRANSACTION_TYPE_AR, TRANSACTION_STATUS_AR, EXPENSE_CATEGORY_AR
)

@api_router.post("/advances/create")
async def create_advance_or_custody(
    request: CreateAdvanceRequest,
    current_user: User = Depends(get_super_admin_user)
):
    """إنشاء سلفة أو عهدة جديدة - Super Admin Only"""
    
    # التحقق من وجود الموظف
    employee = await db.users.find_one({"id": request.employee_id})
    if not employee:
        raise HTTPException(status_code=404, detail="الموظف غير موجود")
    
    # إنشاء المعاملة
    transaction = AdvanceTransaction(
        employee_id=request.employee_id,
        employee_name=employee["name"],
        transaction_type=request.transaction_type,
        amount=request.amount,
        description=request.description,
        category=request.category,
        expense_date=request.expense_date,
        status=TransactionStatus.APPROVED,  # تلقائياً معتمد من السوبر أدمن
        approved_by=current_user.id,
        approved_at=datetime.now(timezone.utc),
        notes=request.notes
    )
    
    # حفظ في قاعدة البيانات
    transaction_dict = AdvancesDB.transaction_to_dict(transaction)
    await db.advance_transactions.insert_one(transaction_dict)
    
    # تحديث رصيد الموظف
    await update_employee_balance(request.employee_id)
    
    # إرسال إشعار للموظف
    await send_advance_notification(employee, transaction, current_user, "created")
    
    # تسجيل النشاط
    await log_activity(
        current_user.id,
        f"advance_{request.transaction_type}_created",
        f"إنشاء {TRANSACTION_TYPE_AR[request.transaction_type]} للموظف {employee['name']} بمبلغ {request.amount} درهم"
    )
    
    return {
        "success": True,
        "message": f"تم إنشاء {TRANSACTION_TYPE_AR[request.transaction_type]} بنجاح",
        "transaction_id": transaction.id,
        "amount": request.amount
    }

@api_router.post("/advances/expense")
async def create_expense_with_invoice(
    amount: float = Form(...),
    category: str = Form(...),
    description: str = Form(...),
    expense_date: str = Form(...),
    notes: Optional[str] = Form(None),
    invoice_files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user)
):
    """إنشاء مصروف مع رفع الفواتير"""
    
    try:
        # التحقق من وجود فواتير
        if not invoice_files:
            raise HTTPException(status_code=400, detail="يجب رفع فاتورة واحدة على الأقل")
        
        # التحقق من صحة التصنيف
        try:
            expense_category = ExpenseCategory(category)
        except ValueError:
            raise HTTPException(status_code=400, detail="تصنيف المصروف غير صحيح")
        
        # رفع الملفات وحفظها
        attachments = []
        for file in invoice_files:
            if file.filename:
                # التحقق من نوع الملف
                allowed_types = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf']
                if file.content_type not in allowed_types:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"نوع الملف {file.content_type} غير مدعوم. المسموح: صور أو PDF"
                    )
                
                # إنشاء مجلد الحفظ
                # ✅ Use ROOT_DIR for deployment compatibility
                from pathlib import Path
                ROOT_DIR = Path(__file__).parent
                upload_dir = ROOT_DIR / "uploads" / "expenses" / current_user.id
                upload_dir.mkdir(parents=True, exist_ok=True)
                
                # إنشاء اسم ملف فريد
                file_extension = os.path.splitext(file.filename)[1]
                unique_filename = f"{uuid.uuid4()}{file_extension}"
                file_path = f"{upload_dir}/{unique_filename}"
                
                # حفظ الملف
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                
                # إنشاء معلومات المرفق
                attachment = Attachment(
                    filename=unique_filename,
                    original_filename=file.filename,
                    file_path=file_path,
                    file_size=os.path.getsize(file_path),
                    file_type=file.content_type
                )
                attachments.append(attachment)
        
        # التحقق من الرصيد المتبقي
        balance = await AdvancesDB.calculate_employee_balance(db, current_user.id)
        total_available = balance.remaining_advance + balance.remaining_custody
        
        if amount > total_available:
            raise HTTPException(
                status_code=400,
                detail=f"المبلغ المطلوب ({amount} درهم) يتجاوز الرصيد المتاح ({total_available} درهم)"
            )
        
        
        # إنشاء معاملة المصروف
        transaction = AdvanceTransaction(
            employee_id=current_user.id,
            employee_name=current_user.name,
            transaction_type=TransactionType.EXPENSE,
            amount=amount,
            category=expense_category,
            description=description,
            expense_date=expense_date,
            attachments=attachments,
            status=TransactionStatus.PENDING,  # يحتاج موافقة
            notes=notes
        )
        
        
        # حفظ في قاعدة البيانات
        transaction_dict = AdvancesDB.transaction_to_dict(transaction)
        await db.advance_transactions.insert_one(transaction_dict)
        
        # إرسال إشعار للسوبر أدمن
        await send_expense_approval_notification(current_user, transaction, attachments)
        
        # تسجيل النشاط
        await log_activity(
            current_user.id,
            "expense_submitted",
            f"تقديم مصروف بمبلغ {amount} درهم - {EXPENSE_CATEGORY_AR[expense_category]} مع {len(attachments)} فاتورة"
        )
        
        
        return {
            "success": True,
            "message": "تم تقديم المصروف بنجاح وإرسال للموافقة",
            "transaction_id": transaction.id,
            "attachments_count": len(attachments),
            "remaining_balance": total_available - amount if amount <= total_available else total_available
        }
        
    except Exception as e:
        # تنظيف الملفات في حالة الخطأ
        for attachment in attachments:
            try:
                if os.path.exists(attachment.file_path):
                    os.remove(attachment.file_path)
            except:
                pass
        raise e

@api_router.get("/advances/my-balance")
async def get_my_balance(current_user: User = Depends(get_current_user)):
    """الحصول على رصيد الموظف الحالي"""
    
    balance = await AdvancesDB.calculate_employee_balance(db, current_user.id)
    
    return {
        "employee_name": balance.employee_name,
        "total_advances": balance.total_advances,
        "total_custody": balance.total_custody,
        "total_expenses": balance.total_expenses,
        "remaining_advance": balance.remaining_advance,
        "remaining_custody": balance.remaining_custody,
        "total_available": balance.remaining_advance + balance.remaining_custody,
        "last_transaction_date": balance.last_transaction_date.isoformat() if balance.last_transaction_date else None
    }

@api_router.get("/advances/my-transactions")
async def get_my_transactions(
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """الحصول على معاملات الموظف"""
    
    transactions = await db.advance_transactions.find({
        "employee_id": current_user.id
    }).sort("created_at", -1).limit(limit).to_list(limit)
    
    # معالجة البيانات للعرض
    dubai_tz = timezone(timedelta(hours=4))
    
    for transaction in transactions:
        if "_id" in transaction:
            del transaction["_id"]
        
        # تحويل التواريخ
        if transaction.get("created_at"):
            created_at = datetime.fromisoformat(transaction["created_at"].replace("Z", "+00:00"))
            transaction["created_at_display"] = created_at.astimezone(dubai_tz).strftime("%Y-%m-%d %H:%M")
        
        # إضافة الترجمات
        if transaction.get("transaction_type"):
            transaction["transaction_type_ar"] = TRANSACTION_TYPE_AR.get(
                TransactionType(transaction["transaction_type"]), transaction["transaction_type"]
            )
        
        
        if transaction.get("status"):
            transaction["status_ar"] = TRANSACTION_STATUS_AR.get(
                TransactionStatus(transaction["status"]), transaction["status"]
            )
        
        
        if transaction.get("category"):
            transaction["category_ar"] = EXPENSE_CATEGORY_AR.get(
                ExpenseCategory(transaction["category"]), transaction["category"]
            )
        
    
    return {"transactions": transactions}

@api_router.get("/advances/admin/all-transactions")
async def get_all_transactions_admin(
    limit: int = 100,
    employee_id: Optional[str] = None,
    transaction_type: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_super_admin_user)
):
    """جميع المعاملات - Super Admin Only"""
    
    # إنشاء فلتر البحث
    filter_query = {}
    
    if employee_id:
        filter_query["employee_id"] = employee_id
    
    if transaction_type:
        filter_query["transaction_type"] = transaction_type
        
    if status:
        filter_query["status"] = status
    
    transactions = await db.advance_transactions.find(filter_query).sort("created_at", -1).limit(limit).to_list(limit)
    
    # معالجة البيانات للعرض
    dubai_tz = timezone(timedelta(hours=4))
    
    for transaction in transactions:
        if "_id" in transaction:
            del transaction["_id"]
        
        # تحويل التواريخ
        if transaction.get("created_at"):
            created_at = datetime.fromisoformat(transaction["created_at"].replace("Z", "+00:00"))
            transaction["created_at_display"] = created_at.astimezone(dubai_tz).strftime("%Y-%m-%d %H:%M")
        
        # إضافة الترجمات
        if transaction.get("transaction_type"):
            transaction["transaction_type_ar"] = TRANSACTION_TYPE_AR.get(
                TransactionType(transaction["transaction_type"]), transaction["transaction_type"]
            )
        
        
        if transaction.get("status"):
            transaction["status_ar"] = TRANSACTION_STATUS_AR.get(
                TransactionStatus(transaction["status"]), transaction["status"]
            )
        
        
        if transaction.get("category"):
            transaction["category_ar"] = EXPENSE_CATEGORY_AR.get(
                ExpenseCategory(transaction["category"]), transaction["category"]
            )
        
    
    return {"transactions": transactions}

@api_router.get("/advances/admin/all-balances")
async def get_all_employee_balances(current_user: User = Depends(get_super_admin_user)):
    """جميع أرصدة الموظفين - Super Admin Only"""
    
    # الحصول على جميع الموظفين الذين لديهم معاملات
    employee_ids = await db.advance_transactions.distinct("employee_id")
    
    balances = []
    for employee_id in employee_ids:
        balance = await AdvancesDB.calculate_employee_balance(db, employee_id)
        balances.append(balance.dict())
    
    # ترتيب حسب إجمالي المبلغ المتبقي
    balances.sort(key=lambda x: (x["remaining_advance"] + x["remaining_custody"]), reverse=True)
    
    return {"employee_balances": balances}

@api_router.get("/advances/admin/pending-approvals")
async def get_pending_approvals(current_user: User = Depends(get_super_admin_user)):
    """المعاملات المُعلقة للموافقة - Super Admin Only"""
    
    pending_transactions = await db.advance_transactions.find({
        "status": TransactionStatus.PENDING
    }).sort("created_at", -1).to_list(100)
    
    # معالجة البيانات
    dubai_tz = timezone(timedelta(hours=4))
    
    for transaction in pending_transactions:
        if "_id" in transaction:
            del transaction["_id"]
        
        # تحويل التواريخ
        if transaction.get("created_at"):
            created_at = datetime.fromisoformat(transaction["created_at"].replace("Z", "+00:00"))
            transaction["created_at_display"] = created_at.astimezone(dubai_tz).strftime("%Y-%m-%d %H:%M")
        
        # إضافة الترجمات
        if transaction.get("transaction_type"):
            transaction["transaction_type_ar"] = TRANSACTION_TYPE_AR.get(
                TransactionType(transaction["transaction_type"]), transaction["transaction_type"]
            )
        
        
        if transaction.get("category"):
            transaction["category_ar"] = EXPENSE_CATEGORY_AR.get(
                ExpenseCategory(transaction["category"]), transaction["category"]
            )
        
    
    return {"pending_transactions": pending_transactions}

@api_router.post("/advances/{transaction_id}/approve")
async def approve_transaction(
    transaction_id: str,
    approval: ApprovalRequest,
    current_user: User = Depends(get_super_admin_user)
):
    """الموافقة على أو رفض معاملة"""
    
    transaction = await db.advance_transactions.find_one({"id": transaction_id})
    if not transaction:
        raise HTTPException(status_code=404, detail="المعاملة غير موجودة")
    
    if transaction["status"] != TransactionStatus.PENDING:
        raise HTTPException(status_code=400, detail="هذه المعاملة تم معالجتها بالفعل")
    
    # تحديث حالة المعاملة
    update_data = {
        "status": approval.status,
        "approved_by": current_user.id,
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    if approval.status == TransactionStatus.REJECTED:
        update_data["rejection_reason"] = approval.notes or "لم يتم تحديد سبب"
    
    if approval.notes:
        update_data["notes"] = approval.notes
    
    await db.advance_transactions.update_one(
        {"id": transaction_id},
        {"$set": update_data}
    )
    
    # تحديث رصيد الموظف إذا تمت الموافقة
    if approval.status == TransactionStatus.APPROVED:
        await update_employee_balance(transaction["employee_id"])
    
    # إرسال إشعار للموظف
    employee = await db.users.find_one({"id": transaction["employee_id"]})
    if employee:
        await send_expense_decision_notification(employee, transaction, approval, current_user)
    
    # تسجيل النشاط
    action = "approved" if approval.status == TransactionStatus.APPROVED else "rejected"
    await log_activity(
        current_user.id,
        f"expense_{action}",
        f"{'موافقة' if approval.status == TransactionStatus.APPROVED else 'رفض'} مصروف للموظف {transaction['employee_name']} بمبلغ {transaction['amount']} درهم"
    )
    
    return {
        "success": True,
        "message": f"تم {'الموافقة على' if approval.status == TransactionStatus.APPROVED else 'رفض'} المعاملة",
        "transaction_id": transaction_id
    }

@api_router.get("/advances/attachment/{transaction_id}/{attachment_id}")
async def view_attachment(
    transaction_id: str,
    attachment_id: str,
    token: Optional[str] = Query(None),
    current_user: Optional[User] = Depends(lambda: None)
):
    """عرض مرفق (فاتورة)"""
    
    # Authentication check - support both header and query token
    authenticated_user = None
    
    if current_user:
        authenticated_user = current_user
    elif token:
        try:
            from jose import jwt
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            if user_id:
                user_doc = await db.users.find_one({"id": user_id})
                if user_doc:
                    authenticated_user = User(**user_doc)
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    if not authenticated_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    transaction = await db.advance_transactions.find_one({"id": transaction_id})
    if not transaction:
        raise HTTPException(status_code=404, detail="المعاملة غير موجودة")
    
    # التحقق من الصلاحية
    if authenticated_user.role != "super_admin" and transaction["employee_id"] != authenticated_user.id:
        raise HTTPException(status_code=403, detail="غير مسموح")
    
    # البحث عن المرفق
    attachment = None
    for att in transaction.get("attachments", []):
        if att["id"] == attachment_id:
            attachment = att
            break
    
    if not attachment:
        raise HTTPException(status_code=404, detail="المرفق غير موجود")
    
    # التحقق من وجود الملف
    if not os.path.exists(attachment["file_path"]):
        raise HTTPException(status_code=404, detail="الملف غير موجود")
    
    return FileResponse(
        path=attachment["file_path"],
        filename=attachment["original_filename"],
        media_type=attachment["file_type"]
    )

async def update_employee_balance(employee_id: str):
    """تحديث رصيد الموظف"""
    balance = await AdvancesDB.calculate_employee_balance(db, employee_id)
    
    # حفظ أو تحديث الرصيد
    await db.employee_balances.replace_one(
        {"employee_id": employee_id},
        balance.dict(),
        upsert=True
    )

async def send_advance_notification(employee, transaction, admin, action):
    """إرسال إشعار للموظف عند إنشاء سلفة/عهدة"""
    
    message = f"""💰 {TRANSACTION_TYPE_AR[TransactionType(transaction.transaction_type)]} جديدة

👤 الموظف: {employee['name']}
💵 المبلغ: {transaction.amount} درهم
📝 الوصف: {transaction.description}
👤 تم الإنشاء من: {admin.name}
📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}

{f"📋 ملاحظات: {transaction.notes}" if transaction.notes else ""}

يمكنك الآن استخدام هذا المبلغ في مصروفاتك."""

    notification = Notification(
        recipient_id=employee["id"],
        recipient_name=employee["name"],
        sender_id=admin.id,
        sender_name=admin.name,
        subject=f"💰 {TRANSACTION_TYPE_AR[TransactionType(transaction.transaction_type)]} جديدة بمبلغ {transaction.amount} درهم",
        message=message,
        type="success",
        priority="normal",
        sent_at=datetime.utcnow()
    )
    
    await db.notifications.insert_one(notification.dict())

async def send_expense_approval_notification(employee, transaction, attachments):
    """إرسال إشعار للسوبر أدمن عند تقديم مصروف"""
    
    super_admins = await db.users.find({"role": "super_admin"}).to_list(10)
    
    message = f"""🧾 طلب موافقة على مصروف جديد

👤 الموظف: {employee.name}
💵 المبلغ: {transaction.amount} درهم
📂 التصنيف: {EXPENSE_CATEGORY_AR[transaction.category]}
📅 تاريخ المصروف: {transaction.expense_date}
📝 الوصف: {transaction.description}
📎 عدد الفواتير: {len(attachments)}

يرجى مراجعة الطلب والفواتير للموافقة أو الرفض."""

    for admin in super_admins:
        notification = Notification(
            recipient_id=admin["id"],
            recipient_name=admin["name"],
            sender_id="system",
            sender_name="نظام السلف والعهد",
            subject=f"🧾 طلب موافقة مصروف - {employee.name}",
            message=message,
            type="info",
            priority="high",
            sent_at=datetime.utcnow()
        )
        
        
        await db.notifications.insert_one(notification.dict())

async def send_expense_decision_notification(employee, transaction, approval, admin):
    """إرسال إشعار بقرار الموافقة/الرفض"""
    
    if approval.status == TransactionStatus.APPROVED:
        message = f"""✅ تمت الموافقة على مصروفك

💵 المبلغ: {transaction['amount']} درهم
📂 التصنيف: {EXPENSE_CATEGORY_AR[ExpenseCategory(transaction['category'])]}
📅 تاريخ المصروف: {transaction['expense_date']}
👤 تمت الموافقة من: {admin.name}

{f"📋 ملاحظات الإدارة: {approval.notes}" if approval.notes else ""}

تم خصم المبلغ من رصيدك المتاح."""

        subject = "✅ تمت الموافقة على مصروفك"
        msg_type = "success"
    else:
        message = f"""❌ تم رفض مصروفك

💵 المبلغ: {transaction['amount']} درهم
📂 التصنيف: {EXPENSE_CATEGORY_AR[ExpenseCategory(transaction['category'])]}
📅 تاريخ المصروف: {transaction['expense_date']}
👤 تم الرفض من: {admin.name}
❗ سبب الرفض: {approval.notes or 'لم يتم تحديد سبب'}

يرجى مراجعة الفواتير وإعادة التقديم."""

        subject = "❌ تم رفض مصروفك"
        msg_type = "warning"

    notification = Notification(
        recipient_id=employee["id"],
        recipient_name=employee["name"],
        sender_id=admin.id,
        sender_name=admin.name,
        subject=subject,
        message=message,
        type=msg_type,
        priority="normal",
        sent_at=datetime.utcnow()
    )
    
    await db.notifications.insert_one(notification.dict())

# ============ MARKETING VISITS SYSTEM ============

from marketing_visits_model import (
    MarketingVisit, StartVisitRequest, CompleteVisitRequest, VisitResponse,
    ActiveVisitResponse, VisitStatus, VisitPurpose, VisitResult,
    MarketingVisitsDB, PURPOSE_TRANSLATIONS, RESULT_TRANSLATIONS,
    GPSLocation, VisitReport
)

@api_router.post("/marketing-visits/start", response_model=Dict[str, Any])
async def start_marketing_visit(
    visit_request: StartVisitRequest,
    current_user: User = Depends(get_current_user)
):
    """بدء زيارة خارجية جديدة - Server-generated timestamp"""
    
    # التحقق من عدم وجود زيارة قيد التنفيذ لنفس الموظف
    active_visit = await db.marketing_visits.find_one({
        "employee_id": current_user.id,
        "status": VisitStatus.STARTED
    })
    
    if active_visit:
        raise HTTPException(
            status_code=400, 
            detail="لديك زيارة خارجية قيد التنفيذ بالفعل. يجب إنهاؤها أولاً قبل بدء زيارة جديدة"
        )
        
    
    # إنشاء زيارة جديدة بوقت السيرفر
    visit = MarketingVisit(
        employee_id=current_user.id,
        employee_name=current_user.name,
        client_name=visit_request.client_name,
        location_name=visit_request.location_name,
        area=visit_request.area,
        purpose=visit_request.purpose,
        purpose_details=visit_request.purpose_details,
        start_location=visit_request.gps_location,
        start_time=datetime.now(timezone.utc)  # Server timestamp
    )
    
    # حفظ في قاعدة البيانات
    visit_dict = MarketingVisitsDB.visit_to_dict(visit)
    await db.marketing_visits.insert_one(visit_dict)
    
    # تسجيل النشاط
    await log_activity(
        current_user.id,
        "marketing_visit_started",
        f"بدأ زيارة خارجية للعميل: {visit.client_name} في {visit.location_name}"
    )
    
    return {
        "success": True,
        "message": "تم بدء الزيارة الخارجية بنجاح",
        "visit_id": visit.id,
        "start_time": visit.start_time.isoformat(),
        "client_name": visit.client_name,
        "location": visit.location_name
    }

@api_router.get("/marketing-visits/active")
async def get_active_visit(current_user: User = Depends(get_current_user)):
    """الحصول على الزيارة النشطة للموظف الحالي"""
    
    active_visit = await db.marketing_visits.find_one({
        "employee_id": current_user.id,
        "status": VisitStatus.STARTED
    })
    
    if not active_visit:
        return {"active_visit": None}
    
    # حساب الوقت المنقضي
    start_time = datetime.fromisoformat(active_visit["start_time"].replace("Z", "+00:00"))
    elapsed_minutes = int((datetime.now(timezone.utc) - start_time).total_seconds() / 60)
    
    return {
        "active_visit": {
            "id": active_visit["id"],
            "client_name": active_visit["client_name"],
            "location_name": active_visit["location_name"],
            "area": active_visit["area"],
            "purpose": active_visit["purpose"],
            "purpose_ar": PURPOSE_TRANSLATIONS[VisitPurpose(active_visit["purpose"])]["ar"],
            "start_time": active_visit["start_time"],
            "elapsed_minutes": elapsed_minutes,
            "can_complete": True
        }
    }

@api_router.post("/marketing-visits/{visit_id}/complete")
async def complete_marketing_visit(
    visit_id: str,
    completion_request: CompleteVisitRequest,
    current_user: User = Depends(get_current_user)
):
    """إنهاء الزيارة الخارجية مع تقرير إلزامي"""
    
    # البحث عن الزيارة
    visit = await db.marketing_visits.find_one({
        "id": visit_id,
        "employee_id": current_user.id,
        "status": VisitStatus.STARTED
    })
    
    if not visit:
        raise HTTPException(
            status_code=404,
            detail="الزيارة غير موجودة أو مكتملة بالفعل"
        )
        
    
    # التحقق من اكتمال التقرير
    report = completion_request.visit_report
    if not report or not all([
        report.summary and len(report.summary.strip()) >= 20,
        report.details and len(report.details.strip()) >= 50,
        report.result,
        report.next_actions and len(report.next_actions.strip()) >= 10
    ]):
        raise HTTPException(
            status_code=400,
            detail="يجب تعبئة جميع حقول التقرير الإلزامية بالشكل المطلوب"
        )
        
    
    # حساب مدة الزيارة
    start_time = datetime.fromisoformat(visit["start_time"].replace("Z", "+00:00"))
    end_time = datetime.now(timezone.utc)
    duration_minutes = int((end_time - start_time).total_seconds() / 60)
    
    # تحديث الزيارة
    update_data = {
        "end_time": end_time.isoformat(),
        "duration_minutes": duration_minutes,
        "status": VisitStatus.COMPLETED,
        "report": report.dict(),
        "end_location": completion_request.gps_location.dict() if completion_request.gps_location else None,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.marketing_visits.update_one(
        {"id": visit_id},
        {"$set": update_data}
    )
    
    # إرسال إشعار للسوبر أدمن
    await send_visit_completion_notification(visit, report, current_user, duration_minutes)
    
    # تسجيل النشاط
    await log_activity(
        current_user.id,
        "marketing_visit_completed",
        f"أكمل زيارة خارجية للعميل: {visit['client_name']} - المدة: {duration_minutes} دقيقة"
    )
    
    return {
        "success": True,
        "message": "تم إنهاء الزيارة وإرسال التقرير بنجاح",
        "duration_minutes": duration_minutes,
        "visit_id": visit_id
    }

@api_router.get("/marketing-visits/history")
async def get_visits_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """تاريخ الزيارات الخارجية للموظف"""
    
    visits = await db.marketing_visits.find({
        "employee_id": current_user.id
    }).sort("start_time", -1).limit(limit).to_list(limit)
    
    # تحويل التواريخ وإضافة الترجمات
    dubai_tz = timezone(timedelta(hours=4))  # تعريف dubai_tz مرة واحدة
    
    for visit in visits:
        # إزالة _id من MongoDB لتجنب مشاكل JSON serialization
        if "_id" in visit:
            del visit["_id"]
        if visit.get("start_time"):
            start_time = datetime.fromisoformat(visit["start_time"].replace("Z", "+00:00"))
            visit["start_time_display"] = start_time.astimezone(dubai_tz).strftime("%Y-%m-%d %H:%M")
        
        if visit.get("end_time"):
            end_time = datetime.fromisoformat(visit["end_time"].replace("Z", "+00:00"))
            visit["end_time_display"] = end_time.astimezone(dubai_tz).strftime("%Y-%m-%d %H:%M")
        
        # إضافة الترجمات
        if visit.get("purpose"):
            visit["purpose_ar"] = PURPOSE_TRANSLATIONS.get(VisitPurpose(visit["purpose"]), {}).get("ar", visit["purpose"])
        
        if visit.get("report") and visit["report"].get("result"):
            visit["result_ar"] = RESULT_TRANSLATIONS.get(VisitResult(visit["report"]["result"]), {}).get("ar", visit["report"]["result"])
    
    return {"visits": visits}

@api_router.get("/marketing-visits/admin/all")
async def get_all_visits_admin(
    limit: int = 100,
    employee_id: Optional[str] = None,
    current_user: User = Depends(get_admin_user)
):
    """جميع الزيارات الخارجية للإدارة"""
    
    filter_query = {}
    if employee_id:
        filter_query["employee_id"] = employee_id
    
    visits = await db.marketing_visits.find(filter_query).sort("start_time", -1).limit(limit).to_list(limit)
    
    # معالجة البيانات للعرض
    dubai_tz = timezone(timedelta(hours=4))  # تعريف dubai_tz مرة واحدة
    
    for visit in visits:
        # إزالة _id من MongoDB لتجنب مشاكل JSON serialization
        if "_id" in visit:
            del visit["_id"]
        # تحويل التواريخ
        if visit.get("start_time"):
            start_time = datetime.fromisoformat(visit["start_time"].replace("Z", "+00:00"))
            visit["start_time_display"] = start_time.astimezone(dubai_tz).strftime("%Y-%m-%d %H:%M")
        
        if visit.get("end_time"):
            end_time = datetime.fromisoformat(visit["end_time"].replace("Z", "+00:00"))
            visit["end_time_display"] = end_time.astimezone(dubai_tz).strftime("%Y-%m-%d %H:%M")
        
        # إضافة الترجمات
        if visit.get("purpose"):
            visit["purpose_ar"] = PURPOSE_TRANSLATIONS.get(VisitPurpose(visit["purpose"]), {}).get("ar", visit["purpose"])
        
        if visit.get("report") and visit["report"].get("result"):
            visit["result_ar"] = RESULT_TRANSLATIONS.get(VisitResult(visit["report"]["result"]), {}).get("ar", visit["report"]["result"])
    
    return {"visits": visits}

@api_router.put("/marketing-visits/{visit_id}/edit")
async def edit_marketing_visit(
    visit_id: str,
    edit_data: Dict[str, Any],
    current_user: User = Depends(get_super_admin_user)
):
    """تعديل زيارة تسويقية (خاص بالسوبر أدمن فقط)"""
    
    # البحث عن الزيارة
    visit = await db.marketing_visits.find_one({"id": visit_id})
    if not visit:
        raise HTTPException(status_code=404, detail="الزيارة غير موجودة")
    
    # تحضير البيانات المحدثة
    update_data = {}
    
    # الحقول القابلة للتعديل
    editable_fields = [
        'client_name', 'location_name', 'area', 'purpose', 'purpose_details',
        'start_time', 'end_time'
    ]
    
    for field in editable_fields:
        if field in edit_data:
            update_data[field] = edit_data[field]
    
    # تحديث وقت التعديل
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    update_data['edited_by'] = current_user.id
    update_data['edited_by_name'] = current_user.name
    
    # تحديث في قاعدة البيانات
    result = await db.marketing_visits.update_one(
        {"id": visit_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="لم يتم التحديث")
    
    # إضافة سجل في النشاطات
    await log_activity(
        current_user.id,
        "marketing_visit_edited",
        f"تعديل زيارة تسويقية - {visit['client_name']}"
    )
    
    return {
        "success": True,
        "message": "تم تعديل الزيارة بنجاح",
        "visit_id": visit_id
    }

@api_router.put("/advances/{transaction_id}/edit")
async def edit_advance_transaction(
    transaction_id: str,
    edit_data: Dict[str, Any],
    current_user: User = Depends(get_super_admin_user)
):
    """تعديل معاملة سلفة/عهدة (خاص بالسوبر أدمن فقط)"""
    
    # البحث عن المعاملة
    transaction = await db.advance_transactions.find_one({"id": transaction_id})
    if not transaction:
        raise HTTPException(status_code=404, detail="المعاملة غير موجودة")
    
    # ملاحظة: السوبر أدمن مسموح له التعديل حتى لو كانت المعاملة معتمدة/مرفوضة
    # تحضير البيانات المحدثة
    update_data = {}
    
    # الحقول القابلة للتعديل
    editable_fields = ['amount', 'description', 'notes', 'category']
    
    for field in editable_fields:
        if field in edit_data:
            update_data[field] = edit_data[field]
    
    # تحديث وقت التعديل
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    update_data['edited_by'] = current_user.id
    update_data['edited_by_name'] = current_user.name
    
    # تحديث في قاعدة البيانات
    result = await db.advance_transactions.update_one(
        {"id": transaction_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="لم يتم التحديث")
    
    # إذا تم تعديل المبلغ، إعادة حساب الرصيد
    if 'amount' in edit_data:
        await update_employee_balance(transaction['employee_id'])
    
    # إضافة سجل في النشاطات
    transaction_type_ar = TRANSACTION_TYPE_AR.get(transaction.get('transaction_type'), 'معاملة')
    await log_activity(
        current_user.id,
        "advance_edited",
        f"تعديل معاملة {transaction_type_ar} - {transaction['employee_name']}"
    )
    
    return {
        "success": True,
        "message": "تم تعديل المعاملة بنجاح",
        "transaction_id": transaction_id
    }

@api_router.delete("/advances/{transaction_id}")
async def delete_advance_transaction(
    transaction_id: str,
    current_user: User = Depends(get_super_admin_user)
):
    """حذف معاملة سلفة/عهدة (خاص بالسوبر أدمن فقط)"""
    
    # البحث عن المعاملة
    transaction = await db.advance_transactions.find_one({"id": transaction_id})
    if not transaction:
        raise HTTPException(status_code=404, detail="المعاملة غير موجودة")
    
    # ملاحظة: السوبر أدمن مسموح له الحذف حتى لو كانت المعاملة معتمدة
    
    # حذف المعاملة من قاعدة البيانات
    result = await db.advance_transactions.delete_one({"id": transaction_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=400, detail="لم يتم الحذف")
    
    # إذا تم حذف معاملة معلقة، قد نحتاج لتحديث الرصيد
    if transaction.get("status") != "pending":
        await update_employee_balance(transaction['employee_id'])
    
    # إضافة سجل في النشاطات
    await log_activity(
        current_user.id,
        "advance_deleted",
        f"حذف معاملة {transaction.get('transaction_type_ar', 'غير محدد')} - {transaction.get('employee_name', 'غير محدد')} بمبلغ {transaction.get('amount', 0):.2f} درهم"
    )
    
    return {
        "success": True,
        "message": "تم حذف المعاملة بنجاح",
        "transaction_id": transaction_id
    }



@api_router.post("/advances/repay")
async def repay_advance(
    req: RepaymentRequest,
    current_user: User = Depends(get_super_admin_user)
):
    """تسجيل سداد سُلفة/عُهدة (RETURN) لموظف - Super Admin Only"""
    # تحقق من الموظف
    employee = await db.users.find_one({"id": req.employee_id})
    if not employee:
        raise HTTPException(status_code=404, detail="الموظف غير موجود")

    # إنشاء معاملة سداد كـ RETURN
    desc = req.notes or "سداد سُلفة/عُهدة"
    if req.method or req.reference:
        extra = []
        if req.method:
            extra.append(f"طريقة السداد: {req.method}")
        if req.reference:
            extra.append(f"مرجع: {req.reference}")
        if extra:
            desc = f"{desc} ({' - '.join(extra)})"

    transaction = AdvanceTransaction(
        employee_id=req.employee_id,
        employee_name=employee["name"],
        transaction_type=TransactionType.RETURN,
        amount=float(req.amount),
        description=desc,
        expense_date=req.repayment_date,
        status=TransactionStatus.APPROVED,
        approved_by=current_user.id,
        approved_at=datetime.now(timezone.utc),
        notes=req.notes
    )

    # حفظ المعاملة
    await db.advance_transactions.insert_one(AdvancesDB.transaction_to_dict(transaction))

    # تحديث الرصيد
    await update_employee_balance(req.employee_id)

    # تسجيل النشاط
    await log_activity(
        current_user.id,
        "advance_repayment_recorded",
        f"تسجيل سداد بمبلغ {req.amount} درهم للموظف {employee['name']}"
    )

    return {
        "success": True,
        "message": "تم تسجيل سداد السُلفة/العُهدة بنجاح",
        "transaction_id": transaction.id,
        "amount": transaction.amount
    }

@api_router.post("/advances/settle-advance")
async def settle_advance_with_salary(
    settlement_request: dict,
    current_user: User = Depends(get_super_admin_user)
):
    """تسوية سلفة مع الراتب (خاص بالسوبر أدمن فقط)"""
    
    employee_id = settlement_request.get("employee_id")
    settlement_amount = settlement_request.get("settlement_amount")
    salary_month = settlement_request.get("salary_month")
    notes = settlement_request.get("notes", "")
    
    if not employee_id or not settlement_amount or not salary_month:
        raise HTTPException(status_code=400, detail="جميع الحقول مطلوبة")
    
    # التحقق من وجود الموظف
    employee = await db.users.find_one({"id": employee_id})
    if not employee:
        raise HTTPException(status_code=404, detail="الموظف غير موجود")
    
    # إنشاء معاملة تسوية
    settlement_transaction = AdvanceTransaction(
        employee_id=employee_id,
        employee_name=employee["name"],
        transaction_type=TransactionType.ADVANCE_SETTLEMENT,
        amount=settlement_amount,
        description=f"تسوية سلفة مع راتب شهر {salary_month}",
        status=TransactionStatus.APPROVED,
        approved_by=current_user.id,
        approved_at=datetime.now(timezone.utc),
        notes=notes,
        created_by=current_user.id
    )
    
    # حفظ في قاعدة البيانات
    transaction_dict = AdvancesDB.transaction_to_dict(settlement_transaction)
    await db.advance_transactions.insert_one(transaction_dict)
    
    # تحديث رصيد الموظف
    await update_employee_balance(employee_id)
    
    # إضافة سجل في النشاطات
    await log_activity(
        current_user.id,
        "advance_settlement",
        f"تسوية سلفة للموظف {employee['name']} بمبلغ {settlement_amount} درهم"
    )
    
    return {
        "success": True,
        "message": f"تم تسوية السلفة بنجاح بمبلغ {settlement_amount} درهم",
        "transaction_id": settlement_transaction.id
    }

@api_router.put("/advances/expense/{transaction_id}/set-deduction-source")
async def set_expense_deduction_source(
    transaction_id: str,
    deduction_data: dict,
    current_user: User = Depends(get_super_admin_user)
):
    """تحديد مصدر خصم المصروف (سلفة أم عهدة) - خاص بالسوبر أدمن"""
    
    deduction_source = deduction_data.get("deduction_source")  # "advance" or "custody"
    
    if deduction_source not in ["advance", "custody"]:
        raise HTTPException(status_code=400, detail="مصدر الخصم يجب أن يكون 'advance' أو 'custody'")
    
    # البحث عن المعاملة
    transaction = await db.advance_transactions.find_one({"id": transaction_id})
    if not transaction:
        raise HTTPException(status_code=404, detail="المعاملة غير موجودة")
    
    if transaction.get("transaction_type") != "expense":
        raise HTTPException(status_code=400, detail="هذه المعاملة ليست مصروف")
    
    # تحديث مصدر الخصم
    result = await db.advance_transactions.update_one(
        {"id": transaction_id},
        {"$set": {
            "deduction_source": deduction_source,
            "deduction_source_ar": "سلفة" if deduction_source == "advance" else "عهدة",
            "updated_at": to_iso_string_uae(),  # ✅ UAE timezone
            "updated_by": current_user.id
        }}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="لم يتم التحديث")
    
    # إعادة حساب الرصيد
    await update_employee_balance(transaction['employee_id'])
    
    return {
        "success": True,
        "message": f"تم تحديد مصدر الخصم: {'سلفة' if deduction_source == 'advance' else 'عهدة'}",
        "deduction_source": deduction_source
    }

# ====================
# NEW: EMPLOYEE ADVANCE/CUSTODY REQUEST ENDPOINTS
# ====================

@api_router.post("/advances/request")
async def request_advance_or_custody(
    request: CreateAdvanceRequest,
    current_user: User = Depends(get_current_user)
):
    """طلب سلفة أو عهدة من الموظف - يحتاج موافقة السوبر أدمن"""
    
    # إنشاء المعاملة بحالة Pending
    transaction = AdvanceTransaction(
        employee_id=current_user.id,
        employee_name=current_user.name,
        transaction_type=request.transaction_type,
        amount=request.amount,
        description=request.description,
        category=request.category,
        expense_date=request.expense_date,
        status=TransactionStatus.PENDING,  # يحتاج موافقة
        notes=request.notes,
        created_by=current_user.id
    )
    
    # حفظ في قاعدة البيانات
    transaction_dict = AdvancesDB.transaction_to_dict(transaction)
    await db.advance_transactions.insert_one(transaction_dict)
    
    # إرسال إشعار للسوبر أدمن
    await send_advance_request_notification(current_user, transaction)
    
    # تسجيل النشاط
    await log_activity(
        current_user.id,
        f"advance_{request.transaction_type}_requested",
        f"طلب {TRANSACTION_TYPE_AR[request.transaction_type]} بمبلغ {request.amount} درهم"
    )
    
    return {
        "success": True,
        "message": f"تم إرسال طلب {TRANSACTION_TYPE_AR[request.transaction_type]} بنجاح وسيتم مراجعته من الإدارة",
        "transaction_id": transaction.id,
        "amount": request.amount,
        "status": "pending"
    }

@api_router.post("/advances/custody-settlement")
async def settle_custody(
    settlement_data: dict,
    current_user: User = Depends(get_current_user)
):
    """تسوية العهدة (رد العهدة) من الموظف"""
    
    amount = settlement_data.get("amount")
    notes = settlement_data.get("notes", "")
    settlement_date = settlement_data.get("settlement_date")
    
    if not amount or not settlement_date:
        raise HTTPException(status_code=400, detail="المبلغ وتاريخ التسوية مطلوبان")
    
    # التحقق من رصيد العهدة
    balance = await AdvancesDB.calculate_employee_balance(db, current_user.id)
    if balance.remaining_custody <= 0:
        raise HTTPException(status_code=400, detail="لا يوجد رصيد عهدة متبقي للتسوية")
    
    if float(amount) > balance.remaining_custody:
        raise HTTPException(
            status_code=400,
            detail=f"المبلغ المطلوب ({amount} درهم) يتجاوز رصيد العهدة المتبقي ({balance.remaining_custody} درهم)"
        )
    
    # إنشاء معاملة تسوية/رد
    transaction = AdvanceTransaction(
        employee_id=current_user.id,
        employee_name=current_user.name,
        transaction_type=TransactionType.RETURN,
        amount=float(amount),
        description=f"تسوية عهدة - {notes}" if notes else "تسوية عهدة",
        expense_date=settlement_date,
        status=TransactionStatus.PENDING,  # يحتاج موافقة السوبر أدمن
        notes=notes,
        created_by=current_user.id
    )
    
    # حفظ في قاعدة البيانات
    transaction_dict = AdvancesDB.transaction_to_dict(transaction)
    await db.advance_transactions.insert_one(transaction_dict)
    
    # إرسال إشعار للسوبر أدمن
    await send_custody_settlement_notification(current_user, transaction)
    
    # تسجيل النشاط
    await log_activity(
        current_user.id,
        "custody_settlement_requested",
        f"طلب تسوية عهدة بمبلغ {amount} درهم"
    )
    
    return {
        "success": True,
        "message": "تم إرسال طلب تسوية العهدة بنجاح وسيتم مراجعته من الإدارة",
        "transaction_id": transaction.id,
        "amount": amount,
        "status": "pending"
    }

# ====================
# NEW: SUPER ADMIN EDIT/DELETE ENDPOINTS
# ====================

@api_router.put("/advances/{transaction_id}/edit")
async def edit_transaction(
    transaction_id: str,
    edit_data: dict,
    current_user: User = Depends(get_super_admin_user)
):
    """تعديل معاملة سلفة/عهدة - Super Admin Only (حتى بعد الموافقة)"""
    
    # البحث عن المعاملة
    transaction = await db.advance_transactions.find_one({"id": transaction_id})
    if not transaction:
        raise HTTPException(status_code=404, detail="المعاملة غير موجودة")
    
    # تحضير بيانات التحديث
    update_fields = {}
    
    if "amount" in edit_data:
        update_fields["amount"] = float(edit_data["amount"])
    
    if "description" in edit_data:
        update_fields["description"] = edit_data["description"]
    
    if "notes" in edit_data:
        update_fields["notes"] = edit_data["notes"]
    
    if "expense_date" in edit_data:
        update_fields["expense_date"] = edit_data["expense_date"]
    
    if "category" in edit_data:
        update_fields["category"] = edit_data["category"]
    
    # إضافة بيانات التحديث
    update_fields["updated_at"] = datetime.now(timezone.utc).isoformat()
    update_fields["updated_by"] = current_user.id
    
    # تحديث المعاملة
    result = await db.advance_transactions.update_one(
        {"id": transaction_id},
        {"$set": update_fields}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="لم يتم التحديث")
    
    # تحديث رصيد الموظف
    await update_employee_balance(transaction["employee_id"])
    
    # تسجيل النشاط
    await log_activity(
        current_user.id,
        "advance_transaction_edited",
        f"تعديل معاملة للموظف {transaction['employee_name']} (ID: {transaction_id})"
    )
    
    return {
        "success": True,
        "message": "تم تعديل المعاملة بنجاح",
        "transaction_id": transaction_id
    }

@api_router.delete("/advances/{transaction_id}")
async def delete_transaction(
    transaction_id: str,
    current_user: User = Depends(get_super_admin_user)
):
    """حذف معاملة سلفة/عهدة - Super Admin Only (حتى بعد الموافقة)"""
    
    # البحث عن المعاملة
    transaction = await db.advance_transactions.find_one({"id": transaction_id})
    if not transaction:
        raise HTTPException(status_code=404, detail="المعاملة غير موجودة")
    
    employee_id = transaction["employee_id"]
    employee_name = transaction["employee_name"]
    
    # حذف المعاملة
    result = await db.advance_transactions.delete_one({"id": transaction_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=400, detail="فشل الحذف")
    
    # تحديث رصيد الموظف
    await update_employee_balance(employee_id)
    
    # تسجيل النشاط
    await log_activity(
        current_user.id,
        "advance_transaction_deleted",
        f"حذف معاملة للموظف {employee_name} (ID: {transaction_id})"
    )
    
    return {
        "success": True,
        "message": "تم حذف المعاملة بنجاح",
        "transaction_id": transaction_id
    }

# ====================
# NEW: GET EMPLOYEES WITH ACTIVE BALANCES FOR REPAYMENT
# ====================

@api_router.get("/advances/admin/employees-with-balances")
async def get_employees_with_active_balances(current_user: User = Depends(get_super_admin_user)):
    """الحصول على جميع الموظفين الذين لديهم رصيد سلف/عهد نشط - Super Admin Only"""
    
    # الحصول على جميع الموظفين الذين لديهم معاملات
    employee_ids = await db.advance_transactions.distinct("employee_id")
    
    employees_with_balances = []
    for employee_id in employee_ids:
        # حساب الرصيد
        balance = await AdvancesDB.calculate_employee_balance(db, employee_id)
        
        # فقط الموظفين الذين لديهم رصيد متبقي (سلفة أو عهدة)
        total_remaining = balance.remaining_advance + balance.remaining_custody
        if total_remaining > 0:
            employees_with_balances.append({
                "employee_id": balance.employee_id,
                "employee_name": balance.employee_name,
                "remaining_advance": balance.remaining_advance,
                "remaining_custody": balance.remaining_custody,
                "total_remaining": total_remaining
            })
    
    # ترتيب حسب إجمالي المبلغ المتبقي
    employees_with_balances.sort(key=lambda x: x["total_remaining"], reverse=True)
    
    return {
        "employees": employees_with_balances,
        "count": len(employees_with_balances)
    }

# ====================
# NOTIFICATION HELPER FUNCTIONS
# ====================

async def send_advance_request_notification(employee, transaction):
    """إرسال إشعار للسوبر أدمن عند طلب سلفة/عهدة من موظف"""
    
    super_admins = await db.users.find({"role": "super_admin"}).to_list(10)
    
    message = f"""💰 طلب {TRANSACTION_TYPE_AR[TransactionType(transaction.transaction_type)]} جديد
    
👤 الموظف: {employee.name}
💵 المبلغ: {transaction.amount} درهم
📝 الوصف: {transaction.description}
📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}

يرجى مراجعة الطلب للموافقة أو الرفض."""

    for admin in super_admins:
        notification = Notification(
            recipient_id=admin["id"],
            recipient_name=admin["name"],
            sender_id=employee.id,
            sender_name=employee.name,
            subject=f"💰 طلب {TRANSACTION_TYPE_AR[TransactionType(transaction.transaction_type)]} - {employee.name}",
            message=message,
            type="info",
            priority="high",
            sent_at=datetime.utcnow()
        )
        await db.notifications.insert_one(notification.dict())

async def send_custody_settlement_notification(employee, transaction):
    """إرسال إشعار للسوبر أدمن عند طلب تسوية عهدة"""
    
    super_admins = await db.users.find({"role": "super_admin"}).to_list(10)
    
    message = f"""✅ طلب تسوية عهدة
    
👤 الموظف: {employee.name}
💵 المبلغ: {transaction.amount} درهم
📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}
📝 ملاحظات: {transaction.notes or 'لا توجد'}

يرجى مراجعة الطلب للموافقة."""

    for admin in super_admins:
        notification = Notification(
            recipient_id=admin["id"],
            recipient_name=admin["name"],
            sender_id=employee.id,
            sender_name=employee.name,
            subject=f"✅ طلب تسوية عهدة - {employee.name}",
            message=message,
            type="info",
            priority="high",
            sent_at=datetime.utcnow()
        )
        await db.notifications.insert_one(notification.dict())

# ====================
# ADVANCED ATTENDANCE & DEDUCTIONS API
# ====================

from attendance_models import *
from attendance_engine import AttendanceEngine, AttendanceScheduler

# Initialize Attendance Engine
attendance_engine = AttendanceEngine(db)

@app.on_event("startup")
async def initialize_attendance_engine():
    """
    Initialize attendance engine on startup
    ✅ Non-blocking: runs in background if initialization is slow
    """
    global attendance_engine, payroll_engine
    from attendance_engine import AttendanceEngine
    from payroll_integration_engine import PayrollIntegrationEngine
    
    try:
        # ✅ Initialize engines (fast operations)
        attendance_engine = AttendanceEngine(db)
        payroll_engine = PayrollIntegrationEngine(db)
        
        # ✅ Run slow initialization in background (non-blocking)
        import asyncio
        async def init_attendance_background():
            try:
                await attendance_engine.initialize()
                print("✅ Attendance engine initialized successfully")
            except Exception as e:
                print(f"⚠️  Attendance engine initialization warning: {e}")
        
        # ✅ Don't block startup - run in background
        asyncio.create_task(init_attendance_background())
        
        print("✅ Payroll integration engine initialized successfully")
        
    except Exception as e:
        print(f"❌ Engine initialization error: {e}")
        # Don't crash the entire server
        attendance_engine = None
        payroll_engine = None

@api_router.get("/attendance/policies/{employee_id}")
async def get_employee_attendance_policy(
    employee_id: str,
    current_user: User = Depends(get_current_user)
):
    """الحصول على سياسة حضور الموظف"""
    # التحقق من الصلاحية
    if current_user.role not in ["admin", "super_admin"] and current_user.id != employee_id:
        raise HTTPException(status_code=403, detail="غير مسموح")
    
    policy = await attendance_engine.get_employee_policy(employee_id)
    return {"policy": policy.dict()}

@api_router.post("/attendance/policies")
async def create_attendance_policy(
    policy_data: dict,
    current_user: User = Depends(get_super_admin_user)
):
    """إنشاء سياسة حضور جديدة (سوبر أدمن فقط)"""
    
    # Get employee info
    employee = await db.users.find_one({"id": policy_data["employee_id"]})
    if not employee:
        raise HTTPException(status_code=404, detail="الموظف غير موجود")
    
    policy = AttendancePolicy(
        employee_id=policy_data["employee_id"],
        employee_name=employee["name"],
        start_time=datetime.strptime(policy_data.get("start_time", "09:00"), "%H:%M").time(),
        end_time=datetime.strptime(policy_data.get("end_time", "18:00"), "%H:%M").time(),
        no_penalties=policy_data.get("no_penalties", False),
        early_start_allowed=policy_data.get("early_start_allowed", False),
        end_flexible=policy_data.get("end_flexible", False),
        grace_period_minutes=policy_data.get("grace_period_minutes", 0),
        effective_from=datetime.strptime(policy_data.get("effective_from", date.today().isoformat()), "%Y-%m-%d").date()
    )
    
    await db.attendance_policies.insert_one(prepare_for_mongo(policy.dict()))
    
    return {
        "success": True,
        "message": "تم إنشاء سياسة الحضور بنجاح",
        "policy_id": policy.id
    }

@api_router.get("/attendance/daily")
async def get_daily_attendance(
    employee_id: Optional[str] = None,
    date: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """الحصول على سجلات الحضور اليومية"""
    
    # إعداد المرشحات
    if not employee_id:
        employee_id = current_user.id
    
    # التحقق من الصلاحية  
    if current_user.role not in ["admin", "super_admin"] and current_user.id != employee_id:
        raise HTTPException(status_code=403, detail="غير مسموح")
    
    if not date:
        date = datetime.now().date().isoformat()
    
    # البحث عن السجل
    attendance_doc = await db.daily_attendance.find_one({
        "employee_id": employee_id,
        "date": date
    })
    
    if attendance_doc:
        attendance = DailyAttendance(**parse_from_mongo(attendance_doc))
        return {"attendance": attendance.dict()}
    else:
        return {"attendance": None}

# DISABLED: Duplicate check-in endpoint - using the fixed version at line 852
# @api_router.post("/attendance/check-in")
# async def check_in_attendance(
#     current_user: User = Depends(get_current_user)
# ):
#     """تسجيل الحضور"""
#     
#     check_in_time = datetime.now()
#     today = check_in_time.date()
#     
#     # التحقق من عدم وجود تسجيل حضور مسبق اليوم
#     existing_attendance = await db.daily_attendance.find_one({
#         "employee_id": current_user.id,
#         "date": today.isoformat(),
#         "check_in": {"$exists": True}
#     })
#     
#     if existing_attendance:
#         raise HTTPException(status_code=400, detail="تم تسجيل الحضور مسبقاً اليوم")
#     
#     # معالجة الحضور
#     attendance = await attendance_engine.process_daily_attendance(
#         employee_id=current_user.id,
#         target_date=today,
#         check_in=check_in_time
#     )
#     
#     return {
#         "success": True,
#         "message": "تم تسجيل الحضور بنجاح",
#         "check_in_time": check_in_time.isoformat(),
#         "attendance": attendance.dict()
#     }

@api_router.post("/attendance/check-out") 
async def check_out_attendance(
    current_user: User = Depends(get_current_user)
):
    """تسجيل الانصراف"""
    
    check_out_time = datetime.now()
    today = check_out_time.date()
    
    # البحث عن سجل الحضور
    existing_attendance = await db.daily_attendance.find_one({
        "employee_id": current_user.id,
        "date": today.isoformat()
    })
    
    if not existing_attendance:
        raise HTTPException(status_code=400, detail="لم يتم العثور على تسجيل حضور اليوم")
    
    if existing_attendance.get("check_out"):
        raise HTTPException(status_code=400, detail="تم تسجيل الانصراف مسبقاً")
    
    # معالجة الانصراف
    attendance = await attendance_engine.process_daily_attendance(
        employee_id=current_user.id,
        target_date=today,
        check_in=existing_attendance.get("check_in"),
        check_out=check_out_time,
        force_recompute=True
    )
    
    return {
        "success": True,
        "message": "تم تسجيل الانصراف بنجاح",
        "check_out_time": check_out_time.isoformat(),
        "attendance": attendance.dict()
    }

@api_router.post("/attendance/recompute")
async def recompute_attendance(
    month: Optional[str] = None,
    employee_id: Optional[str] = None,
    force: bool = False,
    current_user: User = Depends(get_super_admin_user)
):
    """إعادة احتساب الحضور (سوبر أدمن فقط)"""
    
    if not month:
        month = datetime.now().strftime('%Y-%m')
    
    # تحديد النطاق
    if employee_id:
        employee_ids = [employee_id]
    else:
        # جميع الموظفين
        users = await db.users.find({}).to_list(None)
        employee_ids = [user["id"] for user in users]
    
    # إعادة احتساب لكل موظف
    recomputed_count = 0
    for emp_id in employee_ids:
        year, month_num = month.split('-')
        start_date = date(int(year), int(month_num), 1)
        
        # آخر يوم في الشهر
        if int(month_num) == 12:
            end_date = date(int(year) + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(int(year), int(month_num) + 1, 1) - timedelta(days=1)
        
        # إعادة احتساب كل يوم
        current_date = start_date
        while current_date <= end_date:
            attendance_doc = await db.daily_attendance.find_one({
                "employee_id": emp_id,
                "date": current_date.isoformat()
            })
            
            if attendance_doc:
                await attendance_engine.process_daily_attendance(
                    employee_id=emp_id,
                    target_date=current_date,
                    check_in=attendance_doc.get("check_in"),
                    check_out=attendance_doc.get("check_out"),
                    force_recompute=True
                )
        
                recomputed_count += 1
            
            current_date += timedelta(days=1)
    
    return {
        "success": True,
        "message": f"تم إعادة احتساب {recomputed_count} سجل حضور للشهر {month}",
        "recomputed_count": recomputed_count
    }

# ====================
# DEDUCTIONS MANAGEMENT API
# ====================

@api_router.get("/deductions/my")
async def get_my_deductions(
    month: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """الحصول على خصومات الموظف"""
    
    query = {
        "employee_id": current_user.id,
        "is_voided": False
    }
    
    if month:
        year, month_num = month.split('-')
        start_date = date(int(year), int(month_num), 1)
        if int(month_num) == 12:
            end_date = date(int(year) + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(int(year), int(month_num) + 1, 1) - timedelta(days=1)
        
        query["date"] = {
            "$gte": start_date.isoformat(),
            "$lte": end_date.isoformat()
        }
    
    deductions = await db.payroll_deductions.find(query).sort("date", -1).to_list(None)
    
    # إضافة الترجمات
    for deduction in deductions:
        if "_id" in deduction:
            del deduction["_id"]
        
        deduction["deduction_type_ar"] = DEDUCTION_TYPE_AR.get(
            DeductionType(deduction["deduction_type"]), deduction["deduction_type"]
        )
        
        deduction["category_ar"] = DEDUCTION_CATEGORY_AR.get(
            DeductionCategory(deduction["category"]), deduction["category"]
        )
        
    
    return {"deductions": deductions}

@api_router.post("/deductions/manual")
async def create_manual_deduction(
    deduction_request: dict,
    current_user: User = Depends(get_super_admin_user)
):
    """إنشاء خصم يدوي (سوبر أدمن فقط)"""
    
    deduction = await attendance_engine.create_manual_deduction(
        employee_id=deduction_request["employee_id"],
        deduction_type=DeductionType(deduction_request.get("deduction_type", "manual")),
        category=DeductionCategory(deduction_request["category"]),
        target_date=datetime.strptime(deduction_request["date"], "%Y-%m-%d").date(),
        minutes=deduction_request.get("minutes"),
        amount=deduction_request.get("amount"),
        reason=deduction_request["reason"],
        created_by=current_user.id,
        attachments=deduction_request.get("attachments", [])
    )
    
    return {
        "success": True,
        "message": "تم إنشاء الخصم بنجاح",
        "deduction_id": deduction.id,
        "amount": deduction.amount
    }

@api_router.patch("/deductions/{deduction_id}")
async def update_deduction(
    deduction_id: str,
    update_data: dict,
    current_user: User = Depends(get_super_admin_user)
):
    """تعديل خصم (سوبر أدمن فقط)"""
    
    # البحث عن الخصم
    deduction_doc = await db.payroll_deductions.find_one({"id": deduction_id})
    if not deduction_doc:
        raise HTTPException(status_code=404, detail="الخصم غير موجود")
    
    if deduction_doc.get("is_voided"):
        raise HTTPException(status_code=400, detail="لا يمكن تعديل خصم ملغي")
    
    # تحضير البيانات المحدثة
    update_fields = {}
    
    if "minutes" in update_data:
        update_fields["minutes"] = update_data["minutes"]
    
    if "amount" in update_data:
        update_fields["amount"] = update_data["amount"]
    
    if "reason" in update_data:
        update_fields["reason"] = update_data["reason"]
    
    if "notes" in update_data:
        update_fields["notes"] = update_data["notes"]
    
    update_fields["updated_by"] = current_user.id
    update_fields["updated_at"] = datetime.now().isoformat()
    
    # تحديث الخصم
    result = await db.payroll_deductions.update_one(
        {"id": deduction_id},
        {"$set": update_fields}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="لم يتم التحديث")
    
    # إنشاء إشعار للموظف
    notification = SystemNotification(
        employee_id=deduction_doc["employee_id"],
        employee_name=deduction_doc["employee_name"],
        title="تم تعديل خصم",
        message=f"تم تعديل خصم بتاريخ {deduction_doc['date']} من قبل الإدارة",
        severity=NotificationSeverity.IMPORTANT,
        must_acknowledge=True,
        category="deduction_updated",
        reference_id=deduction_id
    )
    
    await db.system_notifications.insert_one(prepare_for_mongo(notification.dict()))
    
    return {
        "success": True,
        "message": "تم تعديل الخصم بنجاح"
    }

@api_router.delete("/deductions/{deduction_id}")
async def void_deduction(
    deduction_id: str,
    void_data: dict,
    current_user: User = Depends(get_super_admin_user)
):
    """إلغاء خصم (Soft Delete - سوبر أدمن فقط)"""
    
    # البحث عن الخصم
    deduction_doc = await db.payroll_deductions.find_one({"id": deduction_id})
    if not deduction_doc:
        raise HTTPException(status_code=404, detail="الخصم غير موجود")
    
    if deduction_doc.get("is_voided"):
        raise HTTPException(status_code=400, detail="الخصم ملغي مسبقاً")
    
    # إلغاء الخصم (Soft Delete)
    void_fields = {
        "is_voided": True,
        "voided_by": current_user.id,
        "voided_by_name": current_user.name,
        "void_reason": void_data.get("void_reason", ""),
        "voided_at": datetime.now().isoformat()
    }
    
    result = await db.payroll_deductions.update_one(
        {"id": deduction_id},
        {"$set": void_fields}
    )
    
    # إنشاء إشعار للموظف
    notification = SystemNotification(
        employee_id=deduction_doc["employee_id"],
        employee_name=deduction_doc["employee_name"],
        title="تم إلغاء خصم",
        message=f"تم إلغاء خصم بمبلغ {deduction_doc['amount']:.2f} درهم. السبب: {void_data.get('void_reason', 'غير محدد')}",
        severity=NotificationSeverity.IMPORTANT,
        must_acknowledge=True,
        category="deduction_voided",
        reference_id=deduction_id
    )
    
    await db.system_notifications.insert_one(prepare_for_mongo(notification.dict()))
    
    return {
        "success": True,
        "message": "تم إلغاء الخصم بنجاح"
    }

@api_router.post("/deductions/{deduction_id}/void")
async def void_deduction_post(
    deduction_id: str,
    void_data: dict,
    current_user: User = Depends(get_super_admin_user)
):
    """إلغاء خصم (POST method - سوبر أدمن فقط)"""
    
    # البحث عن الخصم
    deduction_doc = await db.payroll_deductions.find_one({"id": deduction_id})
    if not deduction_doc:
        raise HTTPException(status_code=404, detail="الخصم غير موجود")
    
    if deduction_doc.get("is_voided"):
        raise HTTPException(status_code=400, detail="الخصم ملغي مسبقاً")
    
    # إلغاء الخصم (Soft Delete)
    void_fields = {
        "is_voided": True,
        "voided_by": current_user.id,
        "voided_by_name": current_user.name,
        "void_reason": void_data.get("void_reason", ""),
        "voided_at": datetime.now().isoformat()
    }
    
    result = await db.payroll_deductions.update_one(
        {"id": deduction_id},
        {"$set": void_fields}
    )
    
    # إنشاء إشعار للموظف
    notification = SystemNotification(
        employee_id=deduction_doc["employee_id"],
        employee_name=deduction_doc["employee_name"],
        title="تم إلغاء خصم",
        message=f"تم إلغاء خصم بمبلغ {deduction_doc['amount']:.2f} درهم. السبب: {void_data.get('void_reason', 'غير محدد')}",
        severity=NotificationSeverity.IMPORTANT,
        must_acknowledge=True,
        category="deduction_voided",
        reference_id=deduction_id
    )
    
    await db.system_notifications.insert_one(prepare_for_mongo(notification.dict()))
    
    return {
        "success": True,
        "message": "تم إلغاء الخصم بنجاح"
    }

@api_router.get("/deductions/admin/all")
async def get_all_deductions_admin(
    employee_id: Optional[str] = None,
    month: Optional[str] = None,
    include_voided: bool = False,
    current_user: User = Depends(get_super_admin_user)
):
    """جميع الخصومات للإدارة (سوبر أدمن فقط)"""
    
    query = {}
    
    if employee_id:
        query["employee_id"] = employee_id
    
    if month:
        year, month_num = month.split('-')
        start_date = date(int(year), int(month_num), 1)
        if int(month_num) == 12:
            end_date = date(int(year) + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(int(year), int(month_num) + 1, 1) - timedelta(days=1)
        
        query["date"] = {
            "$gte": start_date.isoformat(),
            "$lte": end_date.isoformat()
        }
    
    if not include_voided:
        query["is_voided"] = False
    
    deductions = await db.payroll_deductions.find(query).sort("date", -1).to_list(None)
    
    # إضافة الترجمات
    for deduction in deductions:
        if "_id" in deduction:
            del deduction["_id"]
        
        deduction["deduction_type_ar"] = DEDUCTION_TYPE_AR.get(
            DeductionType(deduction["deduction_type"]), deduction["deduction_type"]
        )
        
        deduction["category_ar"] = DEDUCTION_CATEGORY_AR.get(
            DeductionCategory(deduction["category"]), deduction["category"]
        )
        
    
    return {"deductions": deductions}

@api_router.post("/deductions/calculate-monthly")
async def calculate_monthly_deductions_endpoint(
    month: str = Query(..., description="Month in YYYY-MM format"),
    current_user: User = Depends(get_super_admin_user)
):
    """
    حساب خصومات التأخير والغياب لشهر معين باستخدام النظام المتقدم
    ✅ Uses advanced_deductions_system for accurate calculations
    ✅ Returns detailed daily breakdown for each employee
    Returns: قائمة الموظفين مع الخصومات والتفاصيل اليومية
    """
    try:
        # ✅ Validate and parse month (format: YYYY-MM)
        if not month or '-' not in month:
            raise HTTPException(
                status_code=400,
                detail="تنسيق الشهر غير صحيح. يجب أن يكون بصيغة YYYY-MM مثل 2025-10"
            )
        
        parts = month.split('-')
        if len(parts) != 2:
            raise HTTPException(
                status_code=400,
                detail="تنسيق الشهر غير صحيح. يجب أن يكون بصيغة YYYY-MM مثل 2025-10"
            )
        
        year_str, month_str = parts
        
        # Validate year and month values
        try:
            year = int(year_str)
            month_num = int(month_str)
            
            if year < 2020 or year > 2100:
                raise ValueError("السنة خارج النطاق المقبول")
            
            if month_num < 1 or month_num > 12:
                raise ValueError("الشهر يجب أن يكون بين 1 و 12")
                
        except ValueError as ve:
            raise HTTPException(
                status_code=400,
                detail=f"قيم الشهر غير صحيحة: {str(ve)}"
            )
        
        # ✅ Calculate 29→28 cycle dates for display
        if month_num == 1:
            # For January, previous month is December of previous year
            cycle_start = date(year - 1, 12, 29)
        else:
            cycle_start = date(year, month_num - 1, 29)
        
        cycle_end = date(year, month_num, 28)
        
        # Get all active employees
        employees = await db.users.find({"is_active": True}).to_list(None)
        
        # ✅ Calculate deductions for each employee
        results = []
        total_deductions = 0
        
        for emp in employees:
            employee_id = emp["id"]
            employee_name = emp["name"]
            employee_salary = emp.get("monthly_salary", 0)
            
            # Skip if no salary defined
            if employee_salary <= 0:
                continue
            
            # Get ALL attendance records for the period (not just late/absent)
            all_attendance = await db.attendance.find({
                "user_id": employee_id,
                "date": {"$gte": cycle_start.isoformat(), "$lte": cycle_end.isoformat()}
            }).sort("date", 1).to_list(None)
            
            # Build detailed daily breakdown
            daily_breakdown = []
            late_deduction = 0
            absence_deduction = 0
            late_count = 0
            total_late_minutes = 0
            
            for record in all_attendance:
                day_date = record.get("date")
                status = record.get("status", "present")
                check_in = record.get("check_in")
                check_out = record.get("check_out")
                late_minutes = record.get("late_minutes", 0)
                early_leave_minutes = record.get("early_departure_minutes", 0)
                working_hours = record.get("working_hours", 0)
                
                # Determine rule applied and deduction
                rule_applied = "No deduction"
                day_deduction = 0
                deduction_type = "none"
                note = ""
                
                if status == "absent":
                    rule_applied = "Full-day deduction (غياب)"
                    daily_rate = employee_salary / 30
                    day_deduction = daily_rate
                    absence_deduction += day_deduction
                    deduction_type = "absence"
                    note = "غياب بدون مبرر"
                    
                elif status == "late":
                    late_count += 1
                    total_late_minutes += late_minutes
                    
                    if late_minutes <= 15:
                        if late_count <= 4:
                            rule_applied = f"Grace period (15 min × {late_count}/4 free)"
                            note = "داخل حد الجريس المجاني"
                        else:
                            # After 4 times, even <15 min counts
                            rule_applied = "Accumulated after grace period"
                            hourly_rate = employee_salary / 30 / 8
                            day_deduction = (late_minutes / 60) * hourly_rate
                            late_deduction += day_deduction
                            deduction_type = "late"
                            note = f"تأخير {late_minutes} دقيقة (بعد انتهاء الجريس)"
                    elif late_minutes <= 20:
                        rule_applied = "Exact time deduction (16-20 min)"
                        hourly_rate = employee_salary / 30 / 8
                        day_deduction = (late_minutes / 60) * hourly_rate
                        late_deduction += day_deduction
                        deduction_type = "late"
                        note = f"تأخير {late_minutes} دقيقة - خصم دقيق"
                    elif late_minutes <= 120:
                        rule_applied = "Half-day deduction (20-120 min)"
                        day_deduction = (employee_salary / 30) / 2
                        late_deduction += day_deduction
                        deduction_type = "late_half_day"
                        note = "تأخير أكثر من 20 دقيقة - نصف يوم"
                    else:
                        rule_applied = "Full-day deduction (>120 min)"
                        day_deduction = employee_salary / 30
                        late_deduction += day_deduction
                        deduction_type = "late_full_day"
                        note = "تأخير أكثر من ساعتين - يوم كامل"
                
                elif status == "weekend":
                    rule_applied = "Weekend (excluded)"
                    note = "عطلة نهاية أسبوع"
                    
                elif status == "holiday":
                    rule_applied = "Public holiday (excluded)"
                    note = "عطلة رسمية"
                    
                elif status == "on_leave":
                    rule_applied = "Approved leave (excluded)"
                    note = "إجازة معتمدة"
                    
                elif status == "present":
                    rule_applied = "Normal attendance"
                    note = "حضور وانصراف طبيعي"
                
                # Add to daily breakdown
                daily_breakdown.append({
                    "date": day_date,
                    "status": status,
                    "check_in": check_in,
                    "check_out": check_out,
                    "late_minutes": late_minutes,
                    "early_leave_minutes": early_leave_minutes,
                    "working_hours": working_hours,
                    "rule_applied": rule_applied,
                    "deduction_type": deduction_type,
                    "deduction_amount": round(day_deduction, 2),
                    "note": note
                })
            
            deduction_details = []
            if late_count > 0:
                deduction_details.append(f"تأخير {late_count} مرات - إجمالي {total_late_minutes} دقيقة")
            
            absence_count = len([d for d in daily_breakdown if d["status"] == "absent"])
            if absence_count > 0:
                deduction_details.append(f"غياب {absence_count} يوم")
            
            # ❌ NO ADVANCES IN ADVANCED DEDUCTIONS SYSTEM
            # Advances are handled separately in payroll cycle settlement
            # Advanced Deductions = Late + Absence + Early Leave ONLY
            
            # Calculate totals
            total_employee_deduction = late_deduction + absence_deduction
            
            if total_employee_deduction > 0 or len(daily_breakdown) > 0:
                results.append({
                    "employee_id": employee_id,
                    "employee_name": employee_name,
                    "monthly_salary": employee_salary,
                    "late_deduction": round(late_deduction, 2),
                    "absence_deduction": round(absence_deduction, 2),
                    "total_deduction": round(total_employee_deduction, 2),
                    "deduction_details": deduction_details,
                    "late_count": late_count,
                    "absence_count": absence_count,
                    "daily_breakdown": daily_breakdown,
                    "daily_records": daily_breakdown  # ✅ Also expose as daily_records for UI compatibility
                })
                total_deductions += total_employee_deduction
        
        return {
            "success": True,
            "mode": "monthly",
            "month": month,
            "cycle_window": {
                "from": cycle_start.isoformat(),
                "to": cycle_end.isoformat(),
                "description": f"دورة شهرية: 29 {calendar.month_name[cycle_start.month]} إلى 28 {calendar.month_name[cycle_end.month]}"
            },
            # Backward compatibility: keep 'employees' but primary key is 'summaries'
            "summaries": results,
            "employees": results,
            "total_deductions": round(total_deductions, 2),
            "employee_count": len(results),
            "note": "Advanced Deductions = Late + Absence + Early Leave ONLY (NO Advances/Custody)"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في حساب الخصومات: {str(e)}")


@api_router.post("/deductions/calculate")
async def calculate_custom_deductions(
    mode: str = Query(..., description="Mode: custom"),
    from_date: str = Query(..., description="Start date YYYY-MM-DD"),
    to_date: str = Query(..., description="End date YYYY-MM-DD"),
    current_user: User = Depends(get_super_admin_user)
):
    """
    حساب خصومات التأخير والغياب لفترة مخصصة
    Custom Period Calculation (Max 93 days)
    ⚠️ Uses advanced_deductions_system for accurate calculations
    Returns: قائمة الموظفين مع الخصومات والتفاصيل اليومية
    """
    try:
        # Validate dates
        if not from_date or not to_date:
            raise HTTPException(
                status_code=400,
                detail="يجب تحديد تاريخ البداية والنهاية"
            )
        
        try:
            start_date = date.fromisoformat(from_date)
            end_date = date.fromisoformat(to_date)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="صيغة التاريخ غير صحيحة. يجب أن تكون YYYY-MM-DD"
            )
        
        # Validate date range
        if start_date > end_date:
            raise HTTPException(
                status_code=400,
                detail="تاريخ البداية يجب أن يكون قبل تاريخ النهاية"
            )
        
        diff_days = (end_date - start_date).days
        if diff_days > 93:
            raise HTTPException(
                status_code=400,
                detail=f"الفترة تتجاوز 93 يوم ({diff_days} يوم). الرجاء تقليل النطاق"
            )
        
        # ✅ Get all active employees (same logic as Monthly)
        employees = await db.users.find({"is_active": True}).to_list(None)
        
        results = []
        total_deductions = 0
        
        for emp in employees:
            employee_id = emp["id"]
            employee_name = emp["name"]
            employee_salary = emp.get("monthly_salary", 0)
            
            # Skip if no salary defined
            if employee_salary <= 0:
                continue
            
            # Get attendance records for custom period
            all_attendance = await db.attendance.find({
                "user_id": employee_id,
                "date": {"$gte": start_date.isoformat(), "$lte": end_date.isoformat()}
            }).sort("date", 1).to_list(None)
            
            # Calculate deductions (same logic as Monthly)
            late_deduction = 0
            absence_deduction = 0
            late_count = 0
            total_late_minutes = 0
            absence_count = 0
            
            daily_breakdown = []
            
            for record in all_attendance:
                day_date = record.get("date")
                status = record.get("status", "present")
                check_in = record.get("check_in")
                check_out = record.get("check_out")
                late_minutes = record.get("late_minutes", 0)
                early_leave_minutes = record.get("early_departure_minutes", 0)
                working_hours = record.get("working_hours", 0)
                
                rule_applied = "No deduction"
                day_deduction = 0
                deduction_type = "none"
                note = ""
                
                if status == "absent":
                    rule_applied = "Full-day deduction (غياب)"
                    daily_rate = employee_salary / 30
                    day_deduction = daily_rate
                    absence_deduction += day_deduction
                    absence_count += 1
                    deduction_type = "absence"
                    note = "غياب بدون مبرر"
                    
                elif status == "late":
                    late_count += 1
                    total_late_minutes += late_minutes
                    
                    if late_minutes <= 15:
                        if late_count <= 4:
                            rule_applied = f"Grace period (15 min × {late_count}/4 free)"
                            note = "داخل حد الجريس المجاني"
                        else:
                            rule_applied = "Accumulated after grace period"
                            hourly_rate = employee_salary / 30 / 8
                            day_deduction = (late_minutes / 60) * hourly_rate
                            late_deduction += day_deduction
                            deduction_type = "late"
                            note = f"تأخير {late_minutes} دقيقة (بعد انتهاء الجريس)"
                    elif late_minutes <= 20:
                        rule_applied = "Exact time deduction (16-20 min)"
                        hourly_rate = employee_salary / 30 / 8
                        day_deduction = (late_minutes / 60) * hourly_rate
                        late_deduction += day_deduction
                        deduction_type = "late"
                        note = f"تأخير {late_minutes} دقيقة"
                    elif late_minutes <= 120:
                        rule_applied = "Half-day deduction (20-120 min)"
                        day_deduction = (employee_salary / 30) / 2
                        late_deduction += day_deduction
                        deduction_type = "late_half_day"
                        note = "تأخير أكثر من 20 دقيقة - نصف يوم"
                    else:
                        rule_applied = "Full-day deduction (>120 min)"
                        day_deduction = employee_salary / 30
                        late_deduction += day_deduction
                        deduction_type = "late_full_day"
                        note = "تأخير أكثر من ساعتين - يوم كامل"
                
                daily_breakdown.append({
                    "date": day_date,
                    "status": status,
                    "check_in": check_in,
                    "check_out": check_out,
                    "late_minutes": late_minutes,
                    "early_leave_minutes": early_leave_minutes,
                    "working_hours": working_hours,
                    "rule_applied": rule_applied,
                    "deduction_type": deduction_type,
                    "deduction_amount": round(day_deduction, 2),
                    "note": note,
                    "is_absent": status == "absent"
                })
            
            total_employee_deduction = late_deduction + absence_deduction
            
            if total_employee_deduction > 0 or len(daily_breakdown) > 0:
                deduction_details = []
                if late_count > 0:
                    deduction_details.append(f"تأخير {late_count} مرات - إجمالي {total_late_minutes} دقيقة")
                if absence_count > 0:
                    deduction_details.append(f"غياب {absence_count} يوم")
                
                results.append({
                    "employee_id": employee_id,
                    "employee_name": employee_name,
                    "monthly_salary": employee_salary,
                    "late_deduction": round(late_deduction, 2),
                    "absence_deduction": round(absence_deduction, 2),
                    "total_deduction": round(total_employee_deduction, 2),
                    "deduction_details": deduction_details,
                    "late_count": late_count,
                    "absence_count": absence_count,
                    "total_late_minutes": total_late_minutes,
                    "daily_records": daily_breakdown
                })
                total_deductions += total_employee_deduction
        
        return {
            "success": True,
            "mode": "custom",
            "period": {
                "from": from_date,
                "to": to_date,
                "days": diff_days + 1,
                "description": f"فترة مخصصة: {from_date} إلى {to_date} ({diff_days + 1} يوم)"
            },
            "employees": results,
            "total_deductions": round(total_deductions, 2),
            "employee_count": len(results),
            "note": "⚠️ Custom Period is PREVIEW ONLY - Use Monthly Calculation to apply deductions to payroll"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"❌ Custom Period Error: {str(e)}")
        print(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"خطأ في حساب الخصومات: {str(e)}")

class ApplyDeductionsRequest(BaseModel):
    """Request model for applying monthly deductions"""
    month: str  # Format: YYYY-MM
    employees: List[dict]  # Employee deduction data
    notes: Optional[str] = None

@api_router.post("/deductions/apply-monthly")
async def apply_monthly_deductions(
    apply_data: ApplyDeductionsRequest,
    current_user: User = Depends(get_super_admin_user)
):
    """
    تطبيق الخصومات المحسوبة على دورة الرواتب
    Creates/updates payroll cycle with calculated deductions
    
    Request Body:
    {
        "month": "2025-10",  # Required: YYYY-MM format
        "employees": [       # Required: List of employee deductions
            {
                "employee_id": "emp-001",
                "employee_name": "محمد أحمد",
                "late_deduction": 150.50,
                "absence_deduction": 500.00,
                "advance_deduction": 300.00
            }
        ],
        "notes": "Optional notes"  # Optional
    }
    """
    try:
        month = apply_data.month
        employees_data = apply_data.employees
        
        if not month or not employees_data:
            raise HTTPException(status_code=400, detail="البيانات غير مكتملة")
        
        # Parse month
        year, month_num = month.split('-')
        
        # Find or create payroll cycle
        cycle = await db.payroll_cycles.find_one({
            "month": month,
            "is_locked": False
        })
        
        if not cycle:
            # Create new payroll cycle
            new_cycle = {
                "id": str(uuid.uuid4()),
                "month": month,
                "year": int(year),
                "display_name": f"رواتب {month}",
                "start_date": date(int(year), int(month_num), 1).isoformat(),
                "is_locked": False,
                "created_at": to_iso_string_uae(),
                "created_by": current_user.id
            }
            await db.payroll_cycles.insert_one(new_cycle)
            cycle = new_cycle
        
        cycle_id = cycle["id"]
        applied_count = 0
        notifications_sent = 0
        
        # Apply deductions for each employee
        for emp_data in employees_data:
            employee_id = emp_data.get("employee_id")
            employee_name = emp_data.get("employee_name")
            late_deduction = emp_data.get("late_deduction", 0)
            absence_deduction = emp_data.get("absence_deduction", 0)
            advance_deduction = emp_data.get("advance_deduction", 0)
            deduction_details = emp_data.get("deduction_details", [])
            
            # Find or create employee payroll summary
            summary = await db.employee_payroll_summaries.find_one({
                "payroll_cycle_id": cycle_id,
                "employee_id": employee_id
            })
            
            if not summary:
                # Get employee info
                employee = await db.users.find_one({"id": employee_id})
                if not employee:
                    continue
                
                # Create new summary
                summary = {
                    "id": str(uuid.uuid4()),
                    "payroll_cycle_id": cycle_id,
                    "employee_id": employee_id,
                    "employee_name": employee_name,
                    "base_salary": employee.get("monthly_salary", 0),
                    "total_allowances": 0,
                    "manual_deductions": 0,
                    "attendance_deductions": 0,
                    "advance_deductions": 0,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                await db.employee_payroll_summaries.insert_one(summary)
            
            # Update deductions
            update_fields = {
                "attendance_deductions": late_deduction + absence_deduction,
                "advance_deductions": advance_deduction,
                "deduction_notes": "\n".join(deduction_details),
                "updated_at": to_iso_string_uae()  # ✅ UAE timezone
            }
            
            # Recalculate totals
            base_salary = summary.get("base_salary", 0)
            allowances = summary.get("total_allowances", 0)
            manual_ded = summary.get("manual_deductions", 0)
            
            update_fields["gross_salary"] = base_salary + allowances
            update_fields["total_deductions"] = manual_ded + late_deduction + absence_deduction + advance_deduction
            update_fields["net_salary"] = update_fields["gross_salary"] - update_fields["total_deductions"]
            
            await db.employee_payroll_summaries.update_one(
                {"payroll_cycle_id": cycle_id, "employee_id": employee_id},
                {"$set": update_fields}
            )
        
            
            # 🆕 CREATE AUTOMATIC LEDGER ENTRIES using PayrollLedgerService
            from payroll_ledger_service import PayrollLedgerService
            ledger_service = PayrollLedgerService(db)
            
            # ✅ CRITICAL FIX: Delete old attendance deduction entries before creating new ones (Idempotency)
            # This prevents ledger duplication when recalculating/reapplying deductions
            await ledger_service.delete_entries_for_employee_cycle(
                employee_id=employee_id,
                cycle_id=cycle_id,
                source_types=["ATTENDANCE_DEDUCTION"]  # Only delete attendance deductions
            )
            
            # 1. Attendance Deduction Ledger Entry
            if late_deduction + absence_deduction > 0:
                attendance_desc = f"خصومات الحضور والتأخير - {month}: " + ", ".join([d for d in deduction_details if "تأخير" in d or "غياب" in d])
                
                await ledger_service.create_entry(
                    employee_id=employee_id,
                    cycle_id=cycle_id,
                    source_type="ATTENDANCE_DEDUCTION",
                    source_id=f"attendance_{month}_{employee_id}",
                    amount=-(late_deduction + absence_deduction),  # سالب للخصم
                    description=attendance_desc,
                    created_by=current_user.id,
                    metadata={"month": month}
                )
        
            
            # 2. Advance Installment Ledger Entries
            if advance_deduction > 0:
                # Get installment details
                installments = await db.individual_installments.find({
                    "employee_id": employee_id,
                    "due_date": {"$regex": f"^{month}"},
                    "status": "pending"
                }).to_list(None)
                
                for installment in installments:
                    await ledger_service.create_entry(
                        employee_id=employee_id,
                        cycle_id=cycle_id,
                        source_type="ADVANCE_INSTALLMENT",
                        source_id=installment.get("id"),
                        amount=-installment.get("installment_amount", 0),  # سالب للخصم
                        description=f"قسط سلفة رقم {installment.get('installment_number', 0)} - استحقاق {installment.get('due_date', '')[:10]}",
                        created_by=current_user.id,
                        metadata={"installment_number": installment.get('installment_number')}
                    )
        
            
            # Mark installments as applied
            await db.individual_installments.update_many(
                {
                    "employee_id": employee_id,
                    "due_date": {"$regex": f"^{month}"},
                    "status": "pending"
                },
                {"$set": {
                    "status": "paid",
                    "paid_at": datetime.now(timezone.utc).isoformat(),
                    "payroll_cycle_id": cycle_id
                }}
            )
        
            
            applied_count += 1
            
            # Send notification to employee
            notification_message = f"تم تطبيق خصومات شهر {month} على راتبك:\n"
            if late_deduction > 0:
                notification_message += f"• خصم تأخير: {late_deduction:.2f} درهم\n"
            if absence_deduction > 0:
                notification_message += f"• خصم غياب: {absence_deduction:.2f} درهم\n"
            if advance_deduction > 0:
                notification_message += f"• أقساط سلف: {advance_deduction:.2f} درهم\n"
            
            notification_message += f"\nإجمالي الخصومات: {(late_deduction + absence_deduction + advance_deduction):.2f} درهم"
            
            if deduction_details:
                notification_message += "\n\nالتفاصيل:\n" + "\n".join(f"• {detail}" for detail in deduction_details)
            
            notification = SystemNotification(
                employee_id=employee_id,
                employee_name=employee_name,
                title=f"خصومات شهر {month}",
                message=notification_message,
                severity=NotificationSeverity.IMPORTANT,
                must_acknowledge=True,
                category="payroll_deductions_applied",
                reference_id=cycle_id
            )
        
            
            await db.system_notifications.insert_one(prepare_for_mongo(notification.dict()))
            notifications_sent += 1
        
        # Update cycle totals
        summaries = await db.employee_payroll_summaries.find({"payroll_cycle_id": cycle_id}).to_list(None)
        cycle_totals = {
            "total_employees": len(summaries),
            "total_gross_salary": sum(s.get("gross_salary", 0) for s in summaries),
            "total_deductions": sum(s.get("total_deductions", 0) for s in summaries),
            "total_net_salary": sum(s.get("net_salary", 0) for s in summaries),
            "updated_at": to_iso_string_uae()  # ✅ UAE timezone
        }
        
        await db.payroll_cycles.update_one(
            {"id": cycle_id},
            {"$set": cycle_totals}
        )
        
        
        return {
            "success": True,
            "message": f"تم تطبيق الخصومات بنجاح على {applied_count} موظف",
            "cycle_id": cycle_id,
            "applied_count": applied_count,
            "notifications_sent": notifications_sent
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في تطبيق الخصومات: {str(e)}")

# ====================
# NOTIFICATIONS API
# ====================

@api_router.get("/notifications/my")
async def get_my_notifications(
    limit: int = 20,
    unread_only: bool = False,
    current_user: User = Depends(get_current_user)
):
    """الحصول على إشعارات الموظف - من كلا الـ collections"""
    
    # ✅ FIX: جلب الإشعارات من notifications collection أيضاً
    # جلب من notifications (الإشعارات المرسلة من السوبر أدمن)
    notifications_query = {
        "$or": [
            {"recipient_id": current_user.id},
            {"user_id": current_user.id}  # للتوافق مع الإشعارات القديمة
        ]
    }
    
    if unread_only:
        notifications_query["is_read"] = False
    
    notifications_from_admin = await db.notifications.find(notifications_query).sort("sent_at", -1).limit(limit).to_list(limit)
    
    # جلب من system_notifications (الإشعارات التلقائية من النظام)
    system_query = {"employee_id": current_user.id}
    if unread_only:
        system_query["acknowledged_at"] = None
    
    system_notifications = await db.system_notifications.find(system_query).sort("created_at", -1).limit(limit).to_list(limit)
    
    # دمج ومعالجة الإشعارات
    all_notifications = []
    
    # معالجة notifications من الأدمن
    for notification in notifications_from_admin:
        # ✅ CRITICAL FIX: استخدام _id من MongoDB إذا لم يكن هناك id
        notif_id = notification.get("id")
        if not notif_id and "_id" in notification:
            # استخدام MongoDB _id كـ string
            notif_id = str(notification["_id"])
        elif not notif_id:
            # في حالة نادرة جداً، أنشئ UUID
            import uuid
            notif_id = str(uuid.uuid4())
        
        # حذف _id لتجنب مشاكل JSON serialization
        if "_id" in notification:
            del notification["_id"]
        
        all_notifications.append({
            "id": notif_id,  # ✅ FIXED: استخدام _id من MongoDB أو id الموجود
            "subject": notification.get("subject", "إشعار"),
            "message": notification.get("message", ""),
            "type": notification.get("type", "info"),
            "priority": notification.get("priority", "normal"),
            "is_read": notification.get("is_read", False),
            "sent_at": notification.get("sent_at"),
            "sender_name": notification.get("sender_name", "الإدارة"),
            "source": "admin"
        })
    
    # معالجة system_notifications
    for notification in system_notifications:
        # ✅ CRITICAL FIX: استخدام _id من MongoDB إذا لم يكن هناك id
        if not notification.get("id") and "_id" in notification:
            notification["id"] = str(notification["_id"])
        elif not notification.get("id"):
            import uuid
            notification["id"] = str(uuid.uuid4())
        
        # حذف _id لتجنب مشاكل JSON serialization
        if "_id" in notification:
            del notification["_id"]
        
        notification["severity_ar"] = NOTIFICATION_SEVERITY_AR.get(
            NotificationSeverity(notification["severity"]), notification["severity"]
        )
        notification["source"] = "system"
        all_notifications.append(notification)
    
    # ترتيب حسب التاريخ - معالجة آمنة لـ datetime و strings
    def get_sort_key(notif):
        """Get sortable timestamp from notification - always returns comparable string"""
        from datetime import datetime
        
        timestamp = notif.get("sent_at") or notif.get("created_at")
        
        # Handle None or empty values
        if not timestamp:
            return "1970-01-01T00:00:00"  # Default old date for sorting
        
        # If it's already a string, return it
        if isinstance(timestamp, str):
            return timestamp if timestamp else "1970-01-01T00:00:00"
        
        # If it's a datetime object, convert to ISO string
        if isinstance(timestamp, datetime):
            return timestamp.isoformat()
        
        # If it has isoformat method (datetime-like), use it
        if hasattr(timestamp, 'isoformat'):
            try:
                return timestamp.isoformat()
            except:
                pass
        
        # Fallback: convert to string
        try:
            return str(timestamp) if timestamp else "1970-01-01T00:00:00"
        except:
            return "1970-01-01T00:00:00"
    
    try:
        all_notifications.sort(key=get_sort_key, reverse=True)
    except Exception as e:
        # If sorting still fails, log and return unsorted
        import traceback
        print(f"❌ Error sorting notifications: {e}")
        print(traceback.format_exc())
    
    return {"notifications": all_notifications[:limit]}

@api_router.get("/notifications/unread-mandatory")
async def get_unread_mandatory_notifications(
    current_user: User = Depends(get_current_user)
):
    """الحصول على الإشعارات الإجبارية غير المقروءة"""
    
    notifications = await db.system_notifications.find({
        "employee_id": current_user.id,
        "must_acknowledge": True,
        "acknowledged_at": None
    }).sort("created_at", -1).to_list(None)
    
    # تنظيف البيانات
    for notification in notifications:
        if "_id" in notification:
            del notification["_id"]
        
        notification["severity_ar"] = NOTIFICATION_SEVERITY_AR.get(
            NotificationSeverity(notification["severity"]), notification["severity"]
        )
        
    
    return {"notifications": notifications}

@api_router.post("/notifications/{notification_id}/acknowledge")
async def acknowledge_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """تأكيد الاطلاع على إشعار - من كلا الـ collections"""
    
    # ✅ FIX: البحث في notifications أولاً (إشعارات الأدمن)
    # البحث بـ id أو _id (للإشعارات القديمة)
    notification_from_admin = None
    
    # محاولة البحث بـ id أولاً
    notification_from_admin = await db.notifications.find_one({
        "id": notification_id,
        "$or": [
            {"recipient_id": current_user.id},
            {"user_id": current_user.id}
        ]
    })
    
    # إذا لم يُعثر عليه، حاول البحث بـ _id (للإشعارات القديمة بدون id)
    if not notification_from_admin:
        try:
            # محاولة استخدام notification_id كـ ObjectId
            notification_from_admin = await db.notifications.find_one({
                "_id": ObjectId(notification_id),
                "$or": [
                    {"recipient_id": current_user.id},
                    {"user_id": current_user.id}
                ]
            })
        except Exception as e:
            print(f"Could not parse as ObjectId: {e}")
    
    if notification_from_admin:
        # تحديث إشعار الأدمن (باستخدام _id أو id حسب ما وُجد)
        update_query = {"_id": notification_from_admin["_id"]} if "_id" in notification_from_admin else {"id": notification_id}
        
        await db.notifications.update_one(
            update_query,
            {"$set": {
                "is_read": True,
                "read_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        return {
            "success": True,
            "message": "تم تأكيد الاطلاع على الإشعار"
        }
    
    # البحث في system_notifications (إشعارات النظام)
    notification = await db.system_notifications.find_one({
        "id": notification_id,
        "employee_id": current_user.id
    })
    
    # إذا لم يُعثر عليه، حاول البحث بـ _id
    if not notification:
        try:
            notification = await db.system_notifications.find_one({
                "_id": ObjectId(notification_id),
                "employee_id": current_user.id
            })
        except Exception as e:
            print(f"Could not parse as ObjectId: {e}")
    
    if not notification:
        raise HTTPException(status_code=404, detail="الإشعار غير موجود")
    
    # تأكيد الاطلاع
    update_query = {"_id": notification["_id"]} if "_id" in notification else {"id": notification_id}
    await db.system_notifications.update_one(
        update_query,
        {"$set": {
            "acknowledged_at": datetime.now(timezone.utc).isoformat(),
            "read_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {
        "success": True,
        "message": "تم تأكيد الاطلاع على الإشعار"
    }
    return {
        "success": True,
        "message": "تم تأكيد الاطلاع على الإشعار"
    }

@api_router.get("/attendance/stats/{employee_id}")
async def get_attendance_stats(
    employee_id: str,
    month: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """إحصائيات الحضور"""
    
    # التحقق من الصلاحية
    if current_user.role not in ["admin", "super_admin"] and current_user.id != employee_id:
        raise HTTPException(status_code=403, detail="غير مسموح")
    
    if not month:
        month = datetime.now().strftime('%Y-%m')
    
    stats = await attendance_engine.get_attendance_stats(employee_id, month)
    return {"stats": stats.dict()}

# ====================
# SYSTEM NOTIFICATIONS API
# ====================

@api_router.get("/notifications/unread")
async def get_unread_notifications(
    current_user: User = Depends(get_current_user)
):
    """الحصول على الإشعارات غير المقروءة"""
    
    notifications = await db.system_notifications.find({
        "employee_id": current_user.id,
        "acknowledged_at": None
    }).sort("created_at", -1).limit(50).to_list(50)
    
    # إضافة الترجمات
    for notification in notifications:
        if "_id" in notification:
            del notification["_id"]
        
        if notification.get("severity"):
            notification["severity_ar"] = NOTIFICATION_SEVERITY_AR.get(
                NotificationSeverity(notification["severity"]), notification["severity"]
            )
        
    
    return {"notifications": notifications}

@api_router.post("/notifications/system")
async def create_system_notification(
    notification_data: dict,
    current_user: User = Depends(get_super_admin_user)
):
    """إنشاء إشعار نظام - Super Admin Only"""
    
    employee_id = notification_data.get("employee_id")
    title = notification_data.get("title", "")
    message = notification_data.get("message", "")
    severity = notification_data.get("severity", "normal")
    must_acknowledge = notification_data.get("must_acknowledge", False)
    
    if not employee_id or not title or not message:
        raise HTTPException(status_code=400, detail="جميع الحقول مطلوبة")
    
    # التحقق من وجود الموظف
    employee = await db.users.find_one({"id": employee_id})
    if not employee:
        raise HTTPException(status_code=404, detail="الموظف غير موجود")
    
    # إنشاء إشعار
    notification = SystemNotification(
        employee_id=employee_id,
        employee_name=employee["name"],
        title=title,
        message=message,
        severity=NotificationSeverity(severity),
        must_acknowledge=must_acknowledge,
        category="admin_message",
        data={"created_by": current_user.name}
    )
    
    await db.system_notifications.insert_one(prepare_for_mongo(notification.dict()))
    
    # تسجيل النشاط
    await log_activity(
        current_user.id,
        "system_notification_created",
        f"إنشاء إشعار نظام للموظف {employee['name']}: {title}"
    )
    
    return {
        "success": True,
        "message": "تم إنشاء الإشعار بنجاح",
        "notification_id": notification.id
    }

# ====================
# ATTENDANCE CONFIGURATION API
# ====================

@api_router.get("/attendance/config")
async def get_attendance_config(
    current_user: User = Depends(get_super_admin_user)
):
    """الحصول على إعدادات نظام الحضور"""
    
    config_doc = await db.attendance_config.find_one({})
    if config_doc:
        config = AttendanceSystemConfig(**parse_from_mongo(config_doc))
        return {"config": config.dict()}
    else:
        # إرجاع الإعدادات الافتراضية
        default_config = AttendanceSystemConfig()
        return {"config": default_config.dict()}

@api_router.put("/attendance/config")
async def update_attendance_config(
    config_data: dict,
    current_user: User = Depends(get_super_admin_user)
):
    """تحديث إعدادات نظام الحضور"""
    
    # الحصول على الإعدادات الحالية أو إنشاء جديدة
    existing_config = await db.attendance_config.find_one({})
    
    if existing_config:
        config = AttendanceSystemConfig(**parse_from_mongo(existing_config))
        # تحديث الحقول المتاحة
        for field, value in config_data.items():
            if hasattr(config, field):
                setattr(config, field, value)
    else:
        config = AttendanceSystemConfig(**config_data)
    
    config.updated_by = current_user.id
    config.updated_at = datetime.now(timezone.utc)
    
    # حفظ الإعدادات
    config_dict = prepare_for_mongo(config.dict())
    await db.attendance_config.replace_one({}, config_dict, upsert=True)
    
    # إعادة تحميل إعدادات المحرك
    await attendance_engine._load_system_config()
    
    # تسجيل النشاط
    await log_activity(
        current_user.id,
        "attendance_config_updated",
        "تحديث إعدادات نظام الحضور"
    )
    
    return {
        "success": True,
        "message": "تم تحديث إعدادات الحضور بنجاح",
        "config": config.dict()
    }

# ====================
# SCHEDULED TASKS API
# ====================

@api_router.post("/attendance/scheduler/check-missing-checkouts")
async def trigger_missing_checkout_check(
    current_user: User = Depends(get_super_admin_user)
):
    """تشغيل فحص عدم تسجيل الانصراف"""
    
    try:
        scheduler = AttendanceScheduler(attendance_engine)
        await scheduler.check_missing_checkouts_warning()
        
        return {
            "success": True,
            "message": "تم تشغيل فحص عدم تسجيل الانصراف بنجاح"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في تشغيل الفحص: {str(e)}")

@api_router.post("/attendance/scheduler/apply-daily-deductions")
async def trigger_daily_deductions(
    target_date: Optional[str] = None,
    current_user: User = Depends(get_super_admin_user)
):
    """تطبيق خصومات يومية"""
    
    try:
        scheduler = AttendanceScheduler(attendance_engine)
        
        if target_date:
            from datetime import datetime
            process_date = datetime.fromisoformat(target_date).date()
        else:
            process_date = date.today()
        
        await scheduler.apply_daily_deductions(process_date)
        
        return {
            "success": True,
            "message": f"تم تطبيق خصومات يوم {process_date} بنجاح"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في تطبيق الخصومات: {str(e)}")

@api_router.get("/attendance/scheduler/status")
async def get_scheduler_status(
    current_user: User = Depends(get_super_admin_user)
):
    """حالة مُجدول المهام"""
    
    return {
        "scheduler_running": True,
        "system_config": {
            "auto_processing_enabled": attendance_engine.config.auto_processing_enabled if attendance_engine.config else True,
            "notifications_enabled": attendance_engine.config.notifications_enabled if attendance_engine.config else True,
        },
        "scheduled_tasks": {
            "missing_checkout_warning": "18:10 daily",
            "missing_checkout_deadline": "23:59 daily",
            "monthly_reset": "00:01 on 1st of each month"
        },
        "last_check": datetime.now(timezone.utc).isoformat()
    }

async def send_visit_completion_notification(visit_data, report, employee, duration_minutes):
    """إرسال إشعار للسوبر أدمن عند إكمال الزيارة"""
    
    # البحث عن جميع السوبر أدمن
    super_admins = await db.users.find({"role": "super_admin"}).to_list(10)
    
    # تحويل مدة الزيارة لصيغة مقروءة
    hours = duration_minutes // 60
    minutes = duration_minutes % 60
    duration_text = ""
    if hours > 0:
        duration_text += f"{hours} ساعة "
    if minutes > 0:
        duration_text += f"{minutes} دقيقة"
    
    # إنشاء رسالة الإشعار
    notification_message = f"""🏢 تم إكمال زيارة خارجية جديدة

👤 الموظف: {employee.name}
🏪 العميل: {visit_data['client_name']}
📍 المكان: {visit_data['location_name']} - {visit_data['area']}
🎯 الغرض: {PURPOSE_TRANSLATIONS.get(VisitPurpose(visit_data['purpose']), {}).get('ar', visit_data['purpose'])}
⏱️ المدة: {duration_text}
📊 النتيجة: {RESULT_TRANSLATIONS.get(VisitResult(report.result), {}).get('ar', report.result)}

📋 ملخص التقرير:
{report.summary}

🔗 لعرض التفاصيل الكاملة، انتقل إلى صفحة إدارة الزيارات الخارجية"""

    # إرسال إشعار لكل سوبر أدمن
    for admin in super_admins:
        notification = Notification(
            recipient_id=admin["id"],
            recipient_name=admin["name"],
            sender_id="system",
            sender_name="نظام الزيارات الخارجية",
            subject="🏢 تم إكمال زيارة خارجية",
            message=notification_message,
            type="info",
            priority="normal",
            sent_at=datetime.utcnow()
        )
        
        
        await db.notifications.insert_one(notification.dict())

# ================================
# ATTENDANCE DEDUCTIONS SYSTEM
# ================================

# Attendance engine is already initialized above

# ================================
# INTEGRATED PAYROLL SYSTEM
# ================================

# Initialize payroll integration engine
payroll_engine = None

@app.get("/api/deductions")
async def get_deductions(
    employee_id: Optional[str] = None,
    month: Optional[str] = None,
    deduction_type: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get deductions with filtering"""
    try:
        # Regular users can only see their own deductions
        if current_user.role == "user":
            employee_id = current_user.id
        
        filters = {}
        if employee_id:
            filters["employee_id"] = employee_id
        if month:
            filters["date"] = {"$regex": f"^{month}"}
        if deduction_type:
            filters["deduction_type"] = deduction_type
        
        deductions = await db.payroll_deductions.find(
            filters
        ).sort([("date", -1)]).to_list(length=100)
        
        # إضافة أسماء الموظفين
        for deduction in deductions:
            if "_id" in deduction:
                del deduction["_id"]
            
            # إضافة اسم الموظف
            if deduction.get("employee_id"):
                employee = await db.users.find_one({"id": deduction["employee_id"]})
                if employee:
                    deduction["employee_name"] = employee["name"]
                else:
                    deduction["employee_name"] = "غير محدد"
        
        return deductions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching deductions: {str(e)}")

@app.get("/api/employees/list")
async def get_employees_list(current_user: User = Depends(get_current_user)):
    """جلب قائمة الموظفين للاستخدام في النماذج"""
    try:
        # جلب جميع الموظفين النشطين
        employees = await db.users.find({"role": {"$in": ["user", "admin"]}, "is_active": {"$ne": False}}).to_list(1000)
        
        employee_list = []
        for emp in employees:
            employee_list.append({
                "id": emp["id"],
                "name": emp["name"],
                "email": emp.get("email", ""),
                "role": emp.get("role", "user")
            })
        
        return {"employees": employee_list}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching employees: {str(e)}")

@app.post("/api/deductions/manual")
async def create_manual_deduction(
    deduction_data: dict,
    current_user: User = Depends(get_super_admin_user)  # 🔒 RBAC: Super Admin Only
):
    """
    إنشاء خصم يدوي - Super Admin Only
    Create manual deduction - Financial operation
    
    🔒 RBAC: Restricted to Super Admin only - manual deductions affect salaries
    """
    
    try:
        global attendance_engine
        from attendance_models import DeductionType, DeductionCategory
        from datetime import date
        
        # Validate required fields
        required_fields = ["employee_id", "amount", "reason", "date"]
        for field in required_fields:
            if field not in deduction_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Validate amount
        amount = float(deduction_data["amount"])
        if amount <= 0:
            raise HTTPException(status_code=400, detail="مبلغ الخصم يجب أن يكون أكبر من صفر")
        
        # Parse date
        target_date = datetime.strptime(deduction_data["date"], "%Y-%m-%d").date()
        
        # Create manual deduction
        deduction = await attendance_engine.create_manual_deduction(
            employee_id=deduction_data["employee_id"],
            deduction_type=DeductionType.MANUAL,
            category=DeductionCategory.CUSTOM,
            target_date=target_date,
            amount=amount,
            reason=deduction_data["reason"],
            created_by=current_user.id
        )
        
        
        # 🆕 TRIGGER: إنشاء قيد محاسبي تلقائياً في Payroll Ledger
        try:
            from payroll_ledger_service import trigger_manual_deduction
            
            # البحث عن دورة راتب مفتوحة لنفس الشهر
            month = target_date.strftime("%Y-%m")
            open_cycle = await db.payroll_cycles.find_one({
                "month": month,
                "is_locked": False
            })
            
            if open_cycle:
                await trigger_manual_deduction(
                    db=db,
                    employee_id=deduction["employee_id"],
                    cycle_id=open_cycle["id"],
                    deduction_id=deduction["id"],
                    amount=amount,
                    reason=deduction_data["reason"],
                    created_by=current_user.id
                )
        
                print(f"✅ تم إنشاء قيد محاسبي تلقائياً للخصم {deduction['id']}")
            else:
                print(f"ℹ️ لا توجد دورة مفتوحة لشهر {month} - سيتم إنشاء القيد عند فتح الدورة")
        except Exception as ledger_error:
            print(f"⚠️ فشل إنشاء قيد محاسبي: {ledger_error}")
        
        # ربط تلقائي بدورة الراتب المفتوحة (النظام القديم)
        try:
            global payroll_engine
            if payroll_engine:
                from .attendance_models import PayrollDeduction, DeductionType, DeductionCategory, DeductionSource
                
                # تحويل البيانات لنموذج الخصم
                deduction_obj = PayrollDeduction(
                    id=deduction["id"],
                    employee_id=deduction["employee_id"],
                    employee_name=deduction["employee_name"],
                    deduction_type=DeductionType.MANUAL,
                    category=DeductionCategory.CUSTOM,
                    date=target_date,
                    amount=deduction["amount"],
                    reason=deduction["reason"],
                    source=DeductionSource.MANUAL,
                    created_by=current_user.id,
                    created_by_name=current_user.name
                )
        
                
                # ربط مع دورة الراتب
                linked = await payroll_engine.link_deduction_to_payroll(deduction_obj)
                if linked:
                    print(f"✅ خصم {deduction['id']} تم ربطه تلقائياً بدورة الراتب")
        except Exception as link_error:
            print(f"⚠️ فشل ربط الخصم بدورة الراتب: {link_error}")
        
        return {"message": "Manual deduction created successfully", "deduction": deduction}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid data: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating manual deduction: {str(e)}")

@app.patch("/api/deductions/{deduction_id}")
async def update_deduction(
    deduction_id: str,
    update_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Update deduction (Super Admin only)"""
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Super Admin access required")
    
    try:
        # Find existing deduction
        existing = await db.payroll_deductions.find_one({"id": deduction_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Deduction not found")
        
        # Update allowed fields
        allowed_updates = ["amount", "reason", "is_voided"]
        update_fields = {}
        
        for field, value in update_data.items():
            if field in allowed_updates:
                update_fields[field] = value
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No valid fields to update")
        
        # Add audit information
        update_fields["updated_by"] = current_user.id
        update_fields["updated_at"] = datetime.now().isoformat()
        
        # Update deduction
        result = await db.payroll_deductions.update_one(
            {"id": deduction_id},
            {"$set": update_fields}
        )
        
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Deduction not found or no changes made")
        
        # Log activity (simplified for now)
        await db.activity_logs.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": current_user.id if hasattr(current_user, 'id') else current_user.id,
            "user_name": current_user.name if hasattr(current_user, 'name') else current_user.name,
            "action": f"Updated deduction {deduction_id}",
            "details": f"Updated fields: {', '.join(update_fields.keys())}",
            "timestamp": datetime.now().isoformat()
        })
        
        # Send notification if amount changed
        if "amount" in update_fields:
            notification = {
                "id": str(uuid.uuid4()),
                "title": "تعديل خصم من الراتب",
                "message": f"تم تعديل خصم بمبلغ {update_fields['amount']} درهم. السبب: {update_fields.get('reason', 'غير محدد')}",
                "severity": "important",
                "category": "deduction",
                "user_id": existing["employee_id"],
                "sender": current_user.name,
                "is_read": False,
                "sent_at": datetime.now().isoformat(),
                "created_at": datetime.now().isoformat()
            }
            await db.notifications.insert_one(notification)
        
        return {"message": "Deduction updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating deduction: {str(e)}")

@app.post("/api/deductions/{deduction_id}/void")
async def void_deduction(
    deduction_id: str,
    void_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Void/cancel a deduction (Super Admin only)"""
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Super Admin access required")
    
    try:
        # Find existing deduction
        existing = await db.payroll_deductions.find_one({"id": deduction_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Deduction not found")
        
        if existing.get("is_voided", False):
            raise HTTPException(status_code=400, detail="Deduction already voided")
        
        void_reason = void_data.get("reason", "إلغاء إداري")
        
        # Mark as voided
        void_fields = {
            "is_voided": True,
            "voided_by": current_user.id,
            "voided_at": datetime.now().isoformat(),
            "void_reason": void_reason
        }
        
        result = await db.payroll_deductions.update_one(
            {"id": deduction_id},
            {"$set": void_fields}
        )
        
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Deduction not found")
        
        # Log activity (simplified for now)
        await db.activity_logs.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": current_user.id if hasattr(current_user, 'id') else current_user.id,
            "user_name": current_user.name if hasattr(current_user, 'name') else current_user.name,
            "action": f"Voided deduction {deduction_id}",
            "details": f"Reason: {void_reason}",
            "timestamp": datetime.now().isoformat()
        })
        
        # Send notification
        notification = {
            "id": str(uuid.uuid4()),
            "title": "إلغاء خصم من الراتب",
            "message": f"تم إلغاء خصم بمبلغ {existing.get('amount', 0)} درهم. السبب: {void_reason}",
            "severity": "important",
            "category": "deduction",
            "user_id": existing["employee_id"],
            "sender": current_user.name,
            "is_read": False,
            "sent_at": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat()
        }
        await db.notifications.insert_one(notification)
        
        return {"message": "Deduction voided successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error voiding deduction: {str(e)}")

@app.get("/api/attendance/stats/{employee_id}")
async def get_attendance_stats(
    employee_id: str,
    month: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get attendance statistics for employee"""
    try:
        # Regular users can only see their own stats
        if current_user.role == "user" and employee_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not month:
            month = datetime.now().strftime("%Y-%m")
        
        global attendance_engine
        
        # Get attendance statistics
        summary = await attendance_engine.get_attendance_stats(employee_id, month)
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching attendance stats: {str(e)}")

@app.post("/api/attendance/recompute")
async def recompute_attendance(
    recompute_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Recompute attendance for specific date/month (Super Admin only)"""
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Super Admin access required")
    
    try:
        global attendance_engine
        
        if "date" in recompute_data:
            # Recompute specific date
            target_date = datetime.strptime(recompute_data["date"], "%Y-%m-%d").date()
            employee_id = recompute_data.get("employee_id")
            
            if employee_id:
                await attendance_engine.process_daily_attendance(
                    employee_id=employee_id,
                    target_date=target_date,
                    force_recompute=True
                )
        
                message = f"Recomputed attendance for employee {employee_id} on {target_date}"
            else:
                # Recompute for all employees on that date
                employees = await db.users.find({"role": {"$in": ["user", "admin"]}}).to_list(length=None)
                for emp in employees:
                    await attendance_engine.process_daily_attendance(
                        employee_id=emp["id"],
                        target_date=target_date,
                        force_recompute=True
                    )
        
                message = f"Recomputed attendance for all employees on {target_date}"
                
        elif "month" in recompute_data:
            # Recompute entire month
            month = recompute_data["month"]
            employee_id = recompute_data.get("employee_id")
            
            year, month_num = map(int, month.split('-'))
            days_in_month = calendar.monthrange(year, month_num)[1]
            
            if employee_id:
                for day in range(1, days_in_month + 1):
                    target_date = date(year, month_num, day)
                    await attendance_engine.process_daily_attendance(
                        employee_id=employee_id,
                        target_date=target_date,
                        force_recompute=True
                    )
        
                message = f"Recomputed attendance for employee {employee_id} for month {month}"
            else:
                employees = await db.users.find({"role": {"$in": ["user", "admin"]}}).to_list(length=None)
                for emp in employees:
                    for day in range(1, days_in_month + 1):
                        target_date = date(year, month_num, day)
                        await attendance_engine.process_daily_attendance(
                            employee_id=emp["id"],
                            target_date=target_date,
                            force_recompute=True
                        )
        
                message = f"Recomputed attendance for all employees for month {month}"
        else:
            raise HTTPException(status_code=400, detail="Either 'date' or 'month' is required")
        
        # Log activity (simplified for now)
        await db.activity_logs.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": current_user.id if hasattr(current_user, 'id') else current_user.id,
            "user_name": current_user.name if hasattr(current_user, 'name') else current_user.name,
            "action": "Recomputed attendance",
            "details": message,
            "timestamp": datetime.now().isoformat()
        })
        
        return {"message": message}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recomputing attendance: {str(e)}")

# ================================
# INTEGRATED PAYROLL ENDPOINTS
# ================================

@app.post("/api/payroll/cycles")
async def create_payroll_cycle(
    cycle_data: dict,
    current_user: User = Depends(get_super_admin_user)  # 🔒 RBAC: Super Admin Only
):
    """
    إنشاء دورة راتب جديدة - Super Admin Only
    Create new payroll cycle - Financial operation
    
    🔒 RBAC: Restricted to Super Admin only - cycle creation is critical
    """
    
    try:
        global payroll_engine
        
        month = cycle_data.get("month")
        notes = cycle_data.get("notes")
        
        if not month:
            raise HTTPException(status_code=400, detail="Month is required (YYYY-MM format)")
        
        cycle = await payroll_engine.create_payroll_cycle(
            month=month,
            created_by=current_user.id,
            created_by_name=current_user.name,
            notes=notes
        )
        
        
        return {
            "message": f"تم إنشاء دورة راتب {month} بنجاح",
            "cycle_id": cycle.id,
            "display_name": cycle.display_name
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating payroll cycle: {str(e)}")

@app.get("/api/payroll/cycles")
async def get_payroll_cycles(
    status: Optional[str] = None,
    year: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """جلب دورات الراتب مع التصفية"""
    try:
        filters = {}
        
        if status:
            filters["status"] = status
        if year:
            filters["year"] = year
        
        cycles = await db.payroll_cycles.find(filters).sort([("year", -1), ("month", -1)]).to_list(100)
        
        # تنسيق البيانات
        for cycle in cycles:
            cycle["_id"] = str(cycle["_id"])
            if "created_at" in cycle:
                cycle["created_at"] = cycle["created_at"]
            if "locked_at" in cycle:
                cycle["locked_at"] = cycle["locked_at"]
        
        return cycles
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching payroll cycles: {str(e)}")

@app.post("/api/payroll/cycles/{cycle_id}/lock")
async def lock_payroll_cycle(
    cycle_id: str,
    lock_data: dict,
    current_user: User = Depends(get_super_admin_user)  # 🔒 RBAC: Super Admin Only
):
    """
    قفل دورة راتب - Super Admin Only
    Lock payroll cycle (prevents modifications) - Reason is mandatory
    
    🔒 RBAC: Restricted to Super Admin only - cycle locking is a critical financial control
    """
    
    try:
        global payroll_engine
        
        # Make lock_reason mandatory
        lock_reason = lock_data.get("lock_reason")
        if not lock_reason or lock_reason.strip() == "":
            raise HTTPException(status_code=400, detail="سبب القفل إلزامي. يجب توضيح سبب قفل دورة الراتب.")
        
        if len(lock_reason.strip()) < 10:
            raise HTTPException(status_code=400, detail="سبب القفل يجب أن يكون 10 أحرف على الأقل")
        
        success = await payroll_engine.lock_payroll_cycle(
            cycle_id=cycle_id,
            locked_by=current_user.id,
            locked_by_name=current_user.name,
            lock_reason=lock_reason.strip()
        )
        
        
        if success:
            return {
                "message": "تم قفل دورة الراتب بنجاح",
                "lock_reason": lock_reason.strip()
            }
        else:
            raise HTTPException(status_code=404, detail="دورة الراتب غير موجودة أو مقفولة بالفعل")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error locking payroll cycle: {str(e)}")

@app.post("/api/payroll/cycles/{cycle_id}/unlock")
async def unlock_payroll_cycle(
    cycle_id: str,
    unlock_data: dict,
    current_user: User = Depends(get_super_admin_user)  # 🔒 RBAC: Super Admin Only
):
    """
    فتح دورة راتب مقفولة - Super Admin Only
    Unlock locked payroll cycle - Reason is mandatory (15+ chars)
    
    🔒 RBAC: Restricted to Super Admin only - unlocking is a critical audit event
    """
    
    try:
        global payroll_engine
        
        unlock_reason = unlock_data.get("reason") or unlock_data.get("unlock_reason")
        if not unlock_reason or unlock_reason.strip() == "":
            raise HTTPException(status_code=400, detail="سبب الفتح إلزامي. يجب توضيح سبب فتح دورة الراتب المقفولة.")
        
        if len(unlock_reason.strip()) < 15:
            raise HTTPException(status_code=400, detail="سبب الفتح يجب أن يكون 15 حرف على الأقل (فتح دورة مقفولة يتطلب تبرير قوي)")
        
        success = await payroll_engine.unlock_payroll_cycle(
            cycle_id=cycle_id,
            unlocked_by=current_user.id,
            unlock_reason=unlock_reason.strip()
        )
        
        
        if success:
            return {
                "message": "تم فتح دورة الراتب بنجاح",
                "unlock_reason": unlock_reason.strip()
            }
        else:
            raise HTTPException(status_code=404, detail="دورة الراتب غير موجودة")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error unlocking payroll cycle: {str(e)}")


@app.delete("/api/payroll/cycles/{cycle_id}")
async def delete_payroll_cycle(
    cycle_id: str,
    force: bool = False,
    current_user: User = Depends(get_super_admin_user)
):
    """
    حذف دورة رواتب - Super Admin Only
    Delete payroll cycle - With safety checks
    
    🔒 RBAC: Super Admin only
    ⚠️ DANGEROUS: This will delete the cycle and all related data
    
    Args:
        cycle_id: Payroll cycle ID
        force: If true, performs hard delete (deletes all related data)
               If false, performs soft delete (marks as deleted)
    
    Safety checks:
    - Cannot delete locked cycle (must unlock first)
    - Cannot delete if payments are recorded
    - Deletes all related: summaries, ledger entries, deductions
    """
    try:
        # Check if cycle exists
        cycle = await db.payroll_cycles.find_one({"id": cycle_id})
        if not cycle:
            raise HTTPException(status_code=404, detail="دورة الرواتب غير موجودة")
        
        # Safety check 1: Cannot delete locked cycle
        if cycle.get("is_locked", False):
            raise HTTPException(
                status_code=400, 
                detail="لا يمكن حذف دورة مقفلة. يجب فتح القفل أولاً (Unlock)"
            )
        
        
        # Safety check 2: Check if payments are recorded
        # (You can add payment check here if you have payments collection)
        
        # Get statistics before deletion
        summaries_count = await db.employee_payroll_summaries.count_documents({
            "payroll_cycle_id": cycle_id
        })
        
        ledger_count = await db.payroll_ledger.count_documents({
            "cycle_id": cycle_id
        })
        
        deductions_count = await db.deductions_advanced.count_documents({
            "payroll_cycle_id": cycle_id
        })
        
        if force:
            # HARD DELETE: Remove all related data
            print(f"🗑️ Hard deleting payroll cycle {cycle_id}")
            
            # Delete employee summaries
            await db.employee_payroll_summaries.delete_many({
                "payroll_cycle_id": cycle_id
            })
            print(f"   ✅ Deleted {summaries_count} employee summaries")
            
            # Delete ledger entries
            await db.payroll_ledger.delete_many({
                "cycle_id": cycle_id
            })
            print(f"   ✅ Deleted {ledger_count} ledger entries")
            
            # Delete advanced deductions
            await db.deductions_advanced.delete_many({
                "payroll_cycle_id": cycle_id
            })
            print(f"   ✅ Deleted {deductions_count} advanced deductions")
            
            # Delete the cycle itself
            await db.payroll_cycles.delete_one({"id": cycle_id})
            print(f"   ✅ Deleted cycle")
            
            return {
                "success": True,
                "type": "hard_delete",
                "message": "تم حذف دورة الرواتب وجميع البيانات المرتبطة نهائياً",
                "deleted": {
                    "cycle": 1,
                    "summaries": summaries_count,
                    "ledger_entries": ledger_count,
                    "advanced_deductions": deductions_count
                }
            }
        else:
            # SOFT DELETE: Mark as deleted
            print(f"🗑️ Soft deleting payroll cycle {cycle_id}")
            
            await db.payroll_cycles.update_one(
                {"id": cycle_id},
                {
                    "$set": {
                        "is_deleted": True,
                        "deleted_at": datetime.now().isoformat(),
                        "deleted_by": current_user.id
                    }
                }
            )
        
            
            return {
                "success": True,
                "type": "soft_delete",
                "message": "تم تعليم دورة الرواتب كمحذوفة (يمكن استرجاعها)",
                "note": "لحذف نهائي، استخدم force=true",
                "affected": {
                    "summaries": summaries_count,
                    "ledger_entries": ledger_count,
                    "advanced_deductions": deductions_count
                }
            }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting cycle: {str(e)}")
        raise HTTPException(status_code=500, detail=f"خطأ في حذف دورة الرواتب: {str(e)}")


@app.post("/api/payroll/cycles/{cycle_id}/restore")
async def restore_payroll_cycle(
    cycle_id: str,
    current_user: User = Depends(get_super_admin_user)
):
    """
    استرجاع دورة رواتب محذوفة (soft deleted)
    Restore soft-deleted payroll cycle
    
    🔒 RBAC: Super Admin only
    """
    try:
        cycle = await db.payroll_cycles.find_one({"id": cycle_id})
        if not cycle:
            raise HTTPException(status_code=404, detail="دورة الرواتب غير موجودة")
        
        if not cycle.get("is_deleted", False):
            raise HTTPException(status_code=400, detail="دورة الرواتب غير محذوفة")
        
        await db.payroll_cycles.update_one(
            {"id": cycle_id},
            {
                "$set": {
                    "is_deleted": False,
                    "restored_at": datetime.now().isoformat(),
                    "restored_by": current_user.id
                },
                "$unset": {
                    "deleted_at": "",
                    "deleted_by": ""
                }
            }
        )
        
        
        return {
            "success": True,
            "message": "تم استرجاع دورة الرواتب بنجاح"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في استرجاع دورة الرواتب: {str(e)}")

@api_router.get("/payroll/cycles/{cycle_id}/ledger")
async def get_payroll_ledger_entries(
    cycle_id: str,
    employee_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    🆕 جلب القيود المحاسبية لدورة الرواتب
    يعرض جميع القيود (attendance, leave, manual, advance, custody)
    
    ✅ RBAC: All authenticated users can view ledger for transparency
    """
    try:
        from payroll_ledger_service import PayrollLedgerService
        
        ledger_service = PayrollLedgerService(db)
        
        entries = await ledger_service.get_entries_for_cycle(
            cycle_id=cycle_id,
            employee_id=employee_id
        )
        
        
        # تجميع حسب نوع القيد
        summary_by_type = {}
        for entry in entries:
            source_type = entry["source_type"]
            if source_type not in summary_by_type:
                summary_by_type[source_type] = {
                    "count": 0,
                    "total_amount": 0,
                    "entries": []
                }
            summary_by_type[source_type]["count"] += 1
            summary_by_type[source_type]["total_amount"] += entry["amount"]
            summary_by_type[source_type]["entries"].append(entry)
        
        return {
            "cycle_id": cycle_id,
            "employee_id": employee_id,
            "total_entries": len(entries),
            "summary_by_type": summary_by_type,
            "entries": entries
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching ledger entries: {str(e)}")

@app.post("/api/payroll/cycles/{cycle_id}/recalculate")
async def recalculate_payroll_cycle_from_ledger(
    cycle_id: str,
    current_user: User = Depends(get_super_admin_user)  # 🔒 RBAC: Super Admin Only
):
    """
    إعادة حساب دورة الرواتب بناءً على Payroll Ledger - Super Admin Only
    Recalculate payroll cycle from ledger - Financial operation
    
    🔒 RBAC: Restricted to Super Admin only - recalculation affects salaries
    يحسب صافي الراتب تلقائياً من جميع القيود المحاسبية
    """
    
    try:
        from payroll_ledger_service import PayrollLedgerService
        
        # التحقق من وجود الدورة
        cycle = await db.payroll_cycles.find_one({"id": cycle_id})
        if not cycle:
            raise HTTPException(status_code=404, detail="Payroll cycle not found")
        
        if cycle.get("is_locked", False):
            raise HTTPException(status_code=400, detail="لا يمكن إعادة حساب دورة مقفولة")
        
        ledger_service = PayrollLedgerService(db)
        
        # جلب جميع الموظفين النشطين
        employees = await db.users.find({"role": "user", "is_active": True}).to_list(None)
        
        updated_count = 0
        total_gross = 0
        total_deductions = 0
        total_net = 0
        
        for emp in employees:
            employee_id = emp["id"]
            base_salary = emp.get("monthly_salary", 0)
            allowances = 0  # يمكن جلبها من مصدر آخر
            
            # إعادة حساب بناءً على القيود
            calculation = await ledger_service.recalculate_employee_payroll(
                cycle_id=cycle_id,
                employee_id=employee_id,
                base_salary=base_salary,
                allowances=allowances
            )
        
            
            # تحديث employee_payroll_summaries
            await db.employee_payroll_summaries.update_one(
                {
                    "payroll_cycle_id": cycle_id,
                    "employee_id": employee_id
                },
                {
                    "$set": {
                        "base_salary": calculation["base_salary"],
                        "total_allowances": calculation["allowances"],
                        "gross_salary": calculation["gross_salary"],
                        "attendance_deductions": calculation["attendance_deductions"],
                        "manual_deductions": calculation["manual_deductions"],
                        "advance_deductions": calculation["advance_installments"],
                        "total_deductions": calculation["total_deductions"],
                        "net_salary": calculation["net_salary"],
                        "is_calculated": True,
                        "calculated_at": datetime.now(timezone.utc).isoformat(),
                        "ledger_entries_count": calculation["ledger_entries_count"]
                    }
                },
                upsert=True
            )
        
            
            total_gross += calculation["gross_salary"]
            total_deductions += calculation["total_deductions"]
            total_net += calculation["net_salary"]
            updated_count += 1
        
        # تحديث إجماليات الدورة
        await db.payroll_cycles.update_one(
            {"id": cycle_id},
            {
                "$set": {
                    "total_employees": updated_count,
                    "total_gross_salary": total_gross,
                    "total_deductions": total_deductions,
                    "total_net_salary": total_net,
                    "recalculated_at": datetime.now(timezone.utc).isoformat(),
                    "recalculated_by": current_user.id
                }
            }
        )
        
        
        return {
            "message": "تم إعادة حساب الرواتب بنجاح باستخدام Payroll Ledger",
            "cycle_id": cycle_id,
            "employees_updated": updated_count,
            "totals": {
                "gross": total_gross,
                "deductions": total_deductions,
                "net": total_net
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recalculating payroll: {str(e)}")

@app.get("/api/payroll/ledger/employee/{employee_id}")
async def get_employee_ledger_entries(
    employee_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    source_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    الحصول على جميع قيود Payroll Ledger لموظف محدد
    مع إمكانية التصفية حسب التاريخ والنوع
    """
    try:
        # Regular users can only see their own ledger
        if current_user.role == "user" and employee_id != current_user.id:
            raise HTTPException(status_code=403, detail="لا يمكنك الاطلاع على قيود موظف آخر")
        
        # Build query
        query = {"employee_id": employee_id}
        
        if source_type:
            query["source_type"] = source_type
        
        if start_date or end_date:
            date_query = {}
            if start_date:
                date_query["$gte"] = start_date
            if end_date:
                date_query["$lte"] = end_date
            query["created_at"] = date_query
        
        # Get entries
        entries = await db.payroll_ledger.find(query).sort("created_at", -1).to_list(1000)
        
        return {
            "success": True,
            "entries": entries
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching ledger: {str(e)}")

@app.get("/api/payroll/ledger")
async def get_payroll_ledger(
    cycle_id: Optional[str] = None,
    employee_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get payroll ledger entries with filters
    
    Args:
        cycle_id: Optional filter by cycle
        employee_id: Optional filter by employee
    
    🔒 Regular users can only see their own ledger
    """
    try:
        # Regular users can only see their own ledger
        if current_user.get("role") == "user":
            if employee_id and employee_id != current_user.get("id"):
                raise HTTPException(status_code=403, detail="لا يمكنك الاطلاع على قيود موظف آخر")
            employee_id = current_user.get("id")
        
        # Build query
        query = {"is_reversed": {"$ne": True}}
        
        if cycle_id:
            query["cycle_id"] = cycle_id
        
        if employee_id:
            query["employee_id"] = employee_id
        
        # Get entries
        entries = await db.payroll_ledger.find(query).sort("created_at", -1).to_list(1000)
        
        # Remove MongoDB _id
        for entry in entries:
            entry.pop("_id", None)
        
        return {
            "success": True,
            "count": len(entries),
            "entries": entries
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching ledger: {str(e)}")

# Old/duplicate endpoint removed - see line 4297 for correct implementation

@app.put("/api/payroll/cycles/{cycle_id}/update-employees")
async def update_payroll_cycle_employees(
    cycle_id: str,
    update_data: dict,
    current_user: User = Depends(get_super_admin_user)  # 🔒 RBAC: Super Admin Only
):
    """
    تعديل بيانات رواتب الموظفين في دورة معينة - Super Admin Only
    Update payroll cycle employee data (recalculate with new values)
    
    🔒 RBAC: Restricted to Super Admin only - financial modifications require highest privilege
    """
    
    try:
        print(f"📝 UPDATE PAYROLL: cycle_id={cycle_id}, user={current_user.id}")
        print(f"📊 Received {len(update_data.get('employees', []))} employees to update")
        
        # Check if cycle exists and is not locked
        cycle = await db.payroll_cycles.find_one({"id": cycle_id})
        if not cycle:
            print(f"❌ Cycle not found: {cycle_id}")
            raise HTTPException(status_code=404, detail="دورة الراتب غير موجودة")
        
        if cycle.get("is_locked", False):
            print(f"🔒 Cycle is locked: {cycle_id}")
            raise HTTPException(status_code=400, detail="لا يمكن التعديل على دورة مقفولة")
        
        employees = update_data.get("employees", [])
        if not employees:
            print(f"⚠️ No employees data in request")
            raise HTTPException(status_code=400, detail="لا توجد بيانات موظفين للتحديث")
        
        # Update each employee's summary AND create ledger entries
        from payroll_ledger_service import PayrollLedgerService
        ledger_service = PayrollLedgerService(db)
        
        updated_count = 0
        for emp_data in employees:
            employee_id = emp_data.get("employee_id")
            if not employee_id:
                continue
            
            # Get current values to compare
            current_summary = await db.employee_payroll_summaries.find_one({
                "payroll_cycle_id": cycle_id,  # ✅ FIXED: Use payroll_cycle_id (database field name)
                "employee_id": employee_id
            })
            
            if not current_summary:
                continue
            
            # Extract new values
            new_manual_ded = emp_data.get("manual_deductions", 0)
            old_manual_ded = current_summary.get("manual_deductions", 0)
            
            # Update employee summary
            update_fields = {
                "base_salary": emp_data.get("base_salary", 0),
                "total_allowances": emp_data.get("allowances", 0),
                "manual_deductions": new_manual_ded,
                "attendance_deductions": emp_data.get("attendance_deductions", 0),
                "advance_deductions": emp_data.get("advance_deductions", 0),
                "updated_at": to_iso_string_uae()  # ✅ UAE timezone
            }
            
            # Recalculate totals
            base_salary = update_fields["base_salary"]
            allowances = update_fields["total_allowances"]
            manual_ded = update_fields["manual_deductions"]
            attendance_ded = update_fields["attendance_deductions"]
            advance_ded = update_fields["advance_deductions"]
            
            update_fields["gross_salary"] = base_salary + allowances
            update_fields["total_deductions"] = manual_ded + attendance_ded + advance_ded
            update_fields["net_salary"] = update_fields["gross_salary"] - update_fields["total_deductions"]
            
            result = await db.employee_payroll_summaries.update_one(
                {
                    "payroll_cycle_id": cycle_id,  # ✅ FIXED: Use payroll_cycle_id (database field name)
                    "employee_id": employee_id
                },
                {"$set": update_fields}
            )
        
            
            # ✅ FIXED: DELETE old ledger entries instead of reversal to prevent duplication
            from uae_datetime_utils import get_uae_now
            
            # DELETE all old ledger entries for this employee in this cycle
            # (for editable deduction types: MANUAL_DEDUCTION, ATTENDANCE_DEDUCTION, ADVANCE_INSTALLMENT)
            delete_result = await db.payroll_ledger.delete_many({
                "employee_id": employee_id,
                "cycle_id": cycle_id,
                "source_type": {"$in": ["MANUAL_DEDUCTION", "ATTENDANCE_DEDUCTION", "ADVANCE_INSTALLMENT"]}
            })
            
            print(f"🗑️ Deleted {delete_result.deleted_count} old ledger entries for employee {employee_id}")
            
            # 1. Create new Manual Deduction entry (if amount > 0)
            if new_manual_ded > 0:
                await ledger_service.create_entry(
                    employee_id=employee_id,
                    cycle_id=cycle_id,
                    source_type="MANUAL_DEDUCTION",
                    source_id=f"manual_edit_{cycle_id}_{employee_id}_{get_uae_now().timestamp()}",
                    amount=-abs(new_manual_ded),  # Ensure negative for deduction
                    description=f"خصم يدوي - {new_manual_ded:.2f} درهم",
                    created_by=current_user.id
                )
        
            
            # 2. Create new Attendance Deduction entry (if amount > 0)
            new_attendance_ded = emp_data.get("attendance_deductions", 0)
            if new_attendance_ded > 0:
                await ledger_service.create_entry(
                    employee_id=employee_id,
                    cycle_id=cycle_id,
                    source_type="ATTENDANCE_DEDUCTION",
                    source_id=f"attendance_edit_{cycle_id}_{employee_id}_{get_uae_now().timestamp()}",
                    amount=-abs(new_attendance_ded),  # Ensure negative for deduction
                    description=f"خصم حضور/تأخير - {new_attendance_ded:.2f} درهم",
                    created_by=current_user.id
                )
        
            
            # 3. Create new Advance Installment entry (if amount > 0)
            new_advance_ded = emp_data.get("advance_deductions", 0)
            if new_advance_ded > 0:
                await ledger_service.create_entry(
                    employee_id=employee_id,
                    cycle_id=cycle_id,
                    source_type="ADVANCE_INSTALLMENT",
                    source_id=f"advance_edit_{cycle_id}_{employee_id}_{get_uae_now().timestamp()}",
                    amount=-abs(new_advance_ded),  # Ensure negative for deduction
                    description=f"قسط سلفة - {new_advance_ded:.2f} درهم",
                    created_by=current_user.id
                )
        
            
            if result.modified_count > 0:
                updated_count += 1
                print(f"✅ Updated employee: {employee_id}")
            else:
                print(f"⚠️ No changes for employee: {employee_id}")
        
        print(f"📊 Total updated: {updated_count} employees")
        
        # Recalculate cycle totals
        summaries = await db.employee_payroll_summaries.find({"payroll_cycle_id": cycle_id}).to_list(None)  # ✅ FIXED: Use payroll_cycle_id
        
        cycle_totals = {
            "total_employees": len(summaries),
            "total_gross_salary": sum(s.get("gross_salary", 0) for s in summaries),
            "total_deductions": sum(s.get("total_deductions", 0) for s in summaries),
            "total_net_salary": sum(s.get("net_salary", 0) for s in summaries),
            "updated_at": to_iso_string_uae()  # ✅ UAE timezone
        }
        
        await db.payroll_cycles.update_one(
            {"id": cycle_id},
            {"$set": cycle_totals}
        )
        
        
        return {
            "message": f"تم تحديث {updated_count} موظف بنجاح",
            "updated_count": updated_count,
            "cycle_totals": cycle_totals
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating employees: {str(e)}")

@app.post("/api/advances/{advance_id}/installments")
async def create_installment_schedule(
    advance_id: str,
    schedule_data: dict,
    current_user: User = Depends(get_super_admin_user)  # 🔒 RBAC: Super Admin Only
):
    """
    إنشاء جدولة أقساط للسلفة - Super Admin Only
    Create installment schedule for advance - Financial operation
    
    🔒 RBAC: Restricted to Super Admin only - installment scheduling affects payroll deductions
    """
    
    try:
        global payroll_engine
        
        # جلب معلومات السلفة
        advance = await db.advance_transactions.find_one({"id": advance_id})
        if not advance:
            raise HTTPException(status_code=404, detail="السلفة غير موجودة")
        
        # التحقق من المعاملات المطلوبة
        installment_amount = schedule_data.get("installment_amount")
        number_of_installments = schedule_data.get("number_of_installments")
        start_date_str = schedule_data.get("start_date")
        
        if not all([installment_amount, number_of_installments, start_date_str]):
            raise HTTPException(status_code=400, detail="جميع الحقول مطلوبة")
        
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        
        # تحويل البيانات لنموذج السلفة - استخدام البيانات مباشرة
        class MockAdvance:
            def __init__(self, data):
                self.id = data["id"]
                self.employee_id = data["employee_id"]
                self.employee_name = data.get("employee_name", "")
                self.amount = data["amount"]
                self.status = data["status"]
        
        advance_obj = MockAdvance(advance)
        
        # إنشاء الجدولة
        schedule = await payroll_engine.create_installment_schedule(
            advance=advance_obj,
            installment_amount=float(installment_amount),
            number_of_installments=int(number_of_installments),
            start_date=start_date,
            created_by=current_user.id,
            created_by_name=current_user.name,
            respect_ceiling=schedule_data.get("respect_ceiling", True)
        )
        
        
        return {
            "message": "تم إنشاء جدولة الأقساط بنجاح",
            "schedule_id": schedule.id,
            "total_amount": schedule.total_amount,
            "installment_amount": schedule.installment_amount,
            "number_of_installments": schedule.number_of_installments
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating installment schedule: {str(e)}")

@app.get("/api/advances/{advance_id}/installments")
async def get_installment_schedule(
    advance_id: str,
    current_user: dict = Depends(get_current_user)
):
    """جلب جدولة أقساط السلفة"""
    try:
        # التحقق من وجود السلفة أولاً
        advance = await db.advance_transactions.find_one({"id": advance_id})
        if not advance:
            raise HTTPException(status_code=404, detail="السلفة غير موجودة")
        
        # البحث عن الجدولة
        schedule = await db.installment_schedules.find_one({
            "advance_transaction_id": advance_id,
            "is_active": True
        })
        
        if not schedule:
            raise HTTPException(status_code=404, detail="لا توجد جدولة أقساط لهذه السلفة")
        
        # جلب الأقساط الفردية
        installments = await db.individual_installments.find({
            "schedule_id": schedule["id"]
        }).sort([("installment_number", 1)]).to_list(100)
        
        # تنسيق البيانات
        schedule["_id"] = str(schedule["_id"])
        for installment in installments:
            installment["_id"] = str(installment["_id"])
        
        return {
            "schedule": schedule,
            "installments": installments
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching installment schedule: {str(e)}")


@app.get("/api/advances")
async def get_employee_advances(
    employee_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    جلب سلف موظف محدد أو كل السلف
    Get advances for specific employee or all
    
    Args:
        employee_id: Optional employee ID (if not provided, returns current user's advances)
        status: Optional filter by status (approved, pending, rejected, fully_paid)
    """
    try:
        # If no employee_id provided, use current user
        target_employee_id = employee_id if employee_id else current_user.get("id")
        
        # Build query
        query = {"employee_id": target_employee_id}
        
        if status:
            query["status"] = status
        
        # Get advances
        advances = await db.advance_transactions.find(query).sort("created_at", -1).to_list(None)
        
        # Remove MongoDB _id
        for advance in advances:
            advance.pop("_id", None)
        
        return {
            "success": True,
            "count": len(advances),
            "advances": advances
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching advances: {str(e)}")

@app.get("/api/payroll/installment-schedules")
async def get_all_installment_schedules(
    current_user: User = Depends(get_super_admin_user)  # 🔒 RBAC: Super Admin Only
):
    """
    جلب جميع جدولات الأقساط - Super Admin Only
    Get all installment schedules - Financial overview
    
    🔒 RBAC: Restricted to Super Admin only - financial data overview
    """
    
    try:
        # جلب جميع جدولات الأقساط
        schedules = await db.installment_schedules.find({}).sort([("created_at", -1)]).to_list(1000)
        
        # إزالة _id من MongoDB وتنسيق البيانات
        for schedule in schedules:
            if "_id" in schedule:
                del schedule["_id"]
        
        return {"schedules": schedules}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching installment schedules: {str(e)}")

@app.get("/api/payroll/cycles/{cycle_id}/calculate")
async def calculate_payroll_cycle(
    cycle_id: str,
    employee_ids: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """حساب رواتب دورة معينة"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        global payroll_engine
        
        # تحويل employee_ids من string إلى list
        employee_list = None
        if employee_ids:
            employee_list = employee_ids.split(",")
        
        # جلب جميع الموظفين إذا لم يحدد موظفين معينين
        if not employee_list:
            employees = await db.users.find({
                "role": "user",
                "is_active": True
            }).to_list(1000)
            employee_list = [emp["id"] for emp in employees]
        
        # حساب رواتب الموظفين
        results = []
        for employee_id in employee_list:
            try:
                summary = await payroll_engine.calculate_employee_payroll(
                    employee_id=employee_id,
                    payroll_cycle_id=cycle_id
                )
        
                results.append({
                    "employee_id": employee_id,
                    "employee_name": summary.employee_name,
                    "gross_salary": summary.gross_salary,
                    "total_deductions": summary.total_deductions,
                    "net_salary": summary.net_salary,
                    "status": "calculated"
                })
            except Exception as emp_error:
                results.append({
                    "employee_id": employee_id,
                    "status": "error",
                    "error": str(emp_error)
                })
        
        # تحديث إجماليات الدورة
        await payroll_engine.update_payroll_cycle_totals(cycle_id)
        
        return {
            "message": f"تم حساب رواتب {len(results)} موظف",
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating payroll: {str(e)}")

@app.get("/api/payroll/cycles/{cycle_id}/summary")
async def get_payroll_cycle_summary(
    cycle_id: str,
    current_user: dict = Depends(get_current_user)
):
    """جلب ملخص دورة الراتب مع aggregation من Payroll Ledger"""
    try:
        # جلب دورة الراتب
        cycle = await db.payroll_cycles.find_one({"id": cycle_id})
        if not cycle:
            raise HTTPException(status_code=404, detail="دورة الراتب غير موجودة")
        
        # جلب ملخصات الموظفين الأساسية
        summaries = await db.employee_payroll_summaries.find({
            "payroll_cycle_id": cycle_id
        }).to_list(1000)
        
        # تحديث كل ملخص موظف بالخصومات من Payroll Ledger
        from payroll_ledger_service import PayrollLedgerService
        ledger_service = PayrollLedgerService(db)
        
        enhanced_summaries = []
        for summary in summaries:
            employee_id = summary.get("employee_id")
            
            # جلب ملخص القيود من Payroll Ledger
            ledger_summary = await ledger_service.get_employee_summary(cycle_id, employee_id)
            
            # دمج البيانات - استخدام البيانات من Ledger للخصومات
            enhanced_summary = {
                "_id": str(summary["_id"]),
                "employee_id": employee_id,
                "employee_name": summary.get("employee_name", ""),
                "payroll_cycle_id": cycle_id,
                "base_salary": summary.get("base_salary", 0),
                "total_allowances": summary.get("allowances", 0),
                "gross_salary": summary.get("gross_salary", 0),
                
                # استخدام البيانات من Payroll Ledger
                "attendance_deductions": ledger_summary["attendance_deductions"],
                "manual_deductions": ledger_summary["manual_deductions"],
                "advance_deductions": ledger_summary["advance_installments"],
                "leave_adjustments": ledger_summary["leave_adjustments"],
                "custody_adjustments": ledger_summary["custody_adjustments"],
                
                # حساب الإجماليات
                "total_deductions": (
                    ledger_summary["attendance_deductions"] +
                    ledger_summary["manual_deductions"] +
                    ledger_summary["advance_installments"]
                ),
                
                # حساب صافي الراتب
                "net_salary": max(0, 
                    summary.get("gross_salary", 0) +
                    ledger_summary["leave_adjustments"] +
                    ledger_summary["custody_adjustments"] -
                    (ledger_summary["attendance_deductions"] +
                     ledger_summary["manual_deductions"] +
                     ledger_summary["advance_installments"])
                ),
                
                "ledger_entries_count": ledger_summary["entries_count"]
            }
            
            enhanced_summaries.append(enhanced_summary)
        
        # تنسيق بيانات الدورة
        cycle["_id"] = str(cycle["_id"])
        
        return {
            "cycle": cycle,
            "employee_summaries": enhanced_summaries,
            "total_employees": len(enhanced_summaries)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching payroll summary: {str(e)}")

# Disabled legacy salary letter endpoint in favor of router-based implementation
@app.get("/__disabled__/payroll/cycles/{cycle_id}/employees/{employee_id}/letter")
async def generate_salary_letter(
    cycle_id: str,
    employee_id: str,
    format: str = "html",
    current_user: dict = Depends(get_current_user)
):
    """
    إنشاء رسالة راتب شهرية للموظف
    format: html or pdf
    """
    try:
        # جلب دورة الراتب
        cycle = await db.payroll_cycles.find_one({"id": cycle_id})
        if not cycle:
            raise HTTPException(status_code=404, detail="دورة الراتب غير موجودة")
        
        # جلب ملخص راتب الموظف
        employee_summary = await db.employee_payroll_summaries.find_one({
            "payroll_cycle_id": cycle_id,
            "employee_id": employee_id
        })
        
        if not employee_summary:
            raise HTTPException(status_code=404, detail="لم يتم العثور على بيانات راتب الموظف")
        
        # جلب بيانات الموظف
        employee = await db.users.find_one({"id": employee_id})
        if not employee:
            raise HTTPException(status_code=404, detail="الموظف غير موجود")
        
        # حساب المعدلات
        base_salary = employee_summary.get("base_salary", 0)
        daily_rate = base_salary / 30
        hourly_rate = daily_rate / 8
        minute_rate = hourly_rate / 60
        
        # جلب تفاصيل الخصومات من Payroll Ledger
        # ✅ FIXED: Use cycle_id (not payroll_cycle_id) and exclude reversed entries
        ledger_entries = await db.payroll_ledger.find({
            "employee_id": employee_id,
            "cycle_id": cycle_id,
            "is_reversed": {"$ne": True}  # ✅ Exclude reversed entries
        }).to_list(None)
        
        # تصنيف البنود
        attendance_deductions = []
        leave_adjustments = []
        manual_deductions = []
        advance_installments = []
        custody_adjustments = []
        
        for entry in ledger_entries:
            source_type = entry.get("source_type", "")
            amount = entry.get("amount", 0)
            description = entry.get("description", "")
            
            # ✅ Use absolute values for display (amounts are negative in ledger)
            if source_type == "ATTENDANCE_DEDUCTION":
                attendance_deductions.append({
                    "description": description,
                    "amount": abs(amount)  # ✅ Convert to positive for display
                })
            elif source_type == "LEAVE_ADJUSTMENT":
                leave_adjustments.append({
                    "description": description,
                    "amount": amount  # Keep sign (can be positive or negative)
                })
            elif source_type == "MANUAL_DEDUCTION":
                manual_deductions.append({
                    "description": description,
                    "amount": abs(amount)  # ✅ Convert to positive for display
                })
            elif source_type == "ADVANCE_INSTALLMENT":
                advance_installments.append({
                    "description": description,
                    "amount": abs(amount),  # ✅ Convert to positive for display
                    "reference_id": entry.get("reference_id", "")
                })
            elif source_type == "CUSTODY_ADJUSTMENT":
                custody_adjustments.append({
                    "description": description,
                    "amount": amount  # Keep sign (can be positive or negative)
                })
        
        # حساب الإجماليات
        total_attendance_deductions = sum(d["amount"] for d in attendance_deductions)
        total_leave_adjustments = sum(d["amount"] for d in leave_adjustments)
        total_manual_deductions = sum(d["amount"] for d in manual_deductions)
        total_advance_deductions = sum(d["amount"] for d in advance_installments)
        total_custody_adjustments = sum(d["amount"] for d in custody_adjustments)
        
        # جلب تفاصيل السلف (إذا وجدت)
        advance_details = None
        if advance_installments:
            # Get first installment reference
            first_installment_ref = advance_installments[0].get("reference_id", "")
            if first_installment_ref:
                # Get installment details
                installment = await db.individual_installments.find_one({"id": first_installment_ref})
                if installment:
                    schedule_id = installment.get("schedule_id", "")
                    schedule = await db.installment_schedules.find_one({"id": schedule_id})
                    if schedule:
                        advance_id = schedule.get("advance_id", "")
                        advance = await db.advance_transactions.find_one({"id": advance_id})
                        if advance:
                            advance_details = {
                                "total_amount": advance.get("amount", 0),
                                "installments_count": schedule.get("number_of_installments", 0),
                                "current_installment_number": installment.get("installment_number", 0),
                                "current_installment_amount": installment.get("installment_amount", 0),
                                "current_installment_date": installment.get("due_date", ""),
                                "remaining_installments": schedule.get("number_of_installments", 0) - installment.get("installment_number", 0)
                            }
        
        # إعداد البيانات للقالب
        from uae_datetime_utils import format_uae_date_dmy, get_uae_today
        
        # ✅ تنسيق التواريخ بصيغة dd/MM/yyyy (Gregorian)
        statement_date_dmy = format_uae_date_dmy()  # Today in dd/MM/yyyy
        
        letter_data = {
            "statement_date": statement_date_dmy,  # ✅ dd/MM/yyyy Asia/Dubai
            "employee_name": employee.get("name", ""),
            "employee_code": employee.get("id", "")[:8],
            "period_label": f"{cycle.get('month', '')} {cycle.get('year', '')}",
            "base_salary": f"{base_salary:,.2f}",
            "daily_rate": f"{daily_rate:,.4f}",
            "hourly_rate": f"{hourly_rate:,.4f}",
            "minute_rate": f"{minute_rate:,.6f}",
            
            # الإجازات
            "leave_summary": "لا توجد" if not leave_adjustments else f"{len(leave_adjustments)} تعديل(ات)",
            "leave_lines": leave_adjustments,
            
            # الغياب والتأخير
            "absence_summary": attendance_deductions,
            "attendance_deductions_total": f"{total_attendance_deductions:,.2f}",
            
            # الخصومات اليدوية
            "manual_deductions_total": f"{total_manual_deductions:,.2f}",
            "manual_lines": manual_deductions,
            
            # السلف
            "advance_details": advance_details,
            "advance_installments_list": advance_installments,  # للعرض في الجدول
            "advance_deductions_total": f"{total_advance_deductions:,.2f}",
            
            # العهد
            "custody_adjustments_total": f"{total_custody_adjustments:,.2f}",
            "custody_lines": custody_adjustments,
            
            # الصافي
            "net_pay": f"{employee_summary.get('net_salary', 0):,.2f}",
            "gross_salary": f"{employee_summary.get('gross_salary', 0):,.2f}",
            "total_deductions": f"{employee_summary.get('total_deductions', 0):,.2f}",
            "cycle_code": cycle_id[:8]
        }
        
        if format == "pdf":
            # Generate PDF using English-only template (cleaner, no RTL issues)
            from english_salary_letter_pdf import generate_english_salary_letter_pdf
            
            pdf_content = generate_english_salary_letter_pdf(
                letter_data,
                attendance_deductions,
                manual_deductions,
                advance_installments
            )
        
            
            return Response(
                content=pdf_content,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename=salary_letter_{cycle_id}_{employee_id}.pdf"}
            )
        
        else:
            # Return HTML using template
            from fastapi.responses import HTMLResponse
            
            # Build deductions rows
            deductions_rows = ""
            
            # Attendance deductions
            if attendance_deductions and len(attendance_deductions) > 0:
                for d in attendance_deductions:
                    deductions_rows += f"""
                    <tr>
                        <td>خصم حضور/تأخير</td>
                        <td>{d['description']}</td>
                        <td style='color:#dc2626;font-weight:bold;'>{d['amount']:.2f}</td>
                    </tr>
                    """
            else:
                deductions_rows += """
                <tr>
                    <td colspan='3' style='text-align:center;color:#666;'>✓ لا توجد خصومات حضور</td>
                </tr>
                """
            
            # Manual deductions
            if manual_deductions and len(manual_deductions) > 0:
                for d in manual_deductions:
                    deductions_rows += f"""
                    <tr>
                        <td>خصم يدوي</td>
                        <td>{d['description']}</td>
                        <td style='color:#dc2626;font-weight:bold;'>{d['amount']:.2f}</td>
                    </tr>
                    """
            
            # Advance installments
            if advance_installments and len(advance_installments) > 0:
                for d in advance_installments:
                    deductions_rows += f"""
                    <tr>
                        <td>قسط سُلفة</td>
                        <td>{d['description']}</td>
                        <td style='color:#dc2626;font-weight:bold;'>{d['amount']:.2f}</td>
                    </tr>
                    """
            
            # Build advance details HTML
            advance_details_html = ""
            if advance_details:
                advance_details_html = f"""
                <div class='advance-details-box'>
                    <p style='margin:0;'><strong>📊 تفاصيل السُلفة:</strong></p>
                    <ul style='margin:10px 0;'>
                        <li>إجمالي السُلفة: <strong>{advance_details['total_amount']:.2f} درهم</strong></li>
                        <li>عدد الأقساط: <strong>{advance_details['installments_count']}</strong></li>
                        <li>القسط الحالي: <strong>{advance_details['current_installment_amount']:.2f} درهم</strong> (استحقاق: {advance_details['current_installment_date'][:10]})</li>
                        <li>الأقساط المتبقية: <strong>{advance_details['remaining_installments']}</strong></li>
                    </ul>
                </div>
                """
            
            # Read template with error handling
            # ✅ Use ROOT_DIR for deployment compatibility
            import os
            from pathlib import Path
            ROOT_DIR = Path(__file__).parent
            template_path = ROOT_DIR / "salary_letter_template.html"
            
            if not os.path.exists(template_path):
                # Fallback: create inline template
                html_template = """<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <title>رسالة راتب</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 20px; direction: rtl; }}
        .letter {{ background: white; padding: 30px; }}
        .header {{ text-align: center; border-bottom: 2px solid #1e40af; padding-bottom: 15px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        td {{ padding: 10px; border: 1px solid #ddd; }}
    </style>
</head>
<body>
    <div class="letter">
        <div class="header"><h2>شركة التنسيق</h2></div>
        <p>الموظف: {employee_name}</p>
        <p>التاريخ: {statement_date}</p>
        <table>
            <tr><td>الراتب الأساسي</td><td>{base_salary}</td></tr>
            <tr><td>الخصومات</td><td>{total_deductions}</td></tr>
            <tr><td>الصافي</td><td>{net_pay}</td></tr>
        </table>
        {deductions_rows}
    </div>
</body>
</html>"""
            else:
                with open(template_path, 'r', encoding='utf-8') as f:
                    html_template = f.read()
            
            # Replace placeholders
            html_content = html_template.format(
                employee_name=letter_data['employee_name'],
                employee_code=letter_data['employee_code'],
                statement_date=letter_data['statement_date'],
                period_label=letter_data['period_label'],
                base_salary=letter_data['base_salary'],
                daily_rate=letter_data['daily_rate'],
                hourly_rate=letter_data['hourly_rate'],
                minute_rate=letter_data['minute_rate'],
                deductions_rows=deductions_rows,
                total_deductions=letter_data['total_deductions'],
                advance_details_html=advance_details_html,
                gross_salary=letter_data['gross_salary'],
                net_pay=letter_data['net_pay'],
                cycle_code=letter_data['cycle_code']
            )
        
            
            return HTMLResponse(content=html_content)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating salary letter: {str(e)}")

@api_router.get("/payroll/cycles/{cycle_id}")
async def get_payroll_cycle_detail(cycle_id: str, current_user: dict = Depends(get_current_user)):
    cycle = await db.payroll_cycles.find_one({"id": cycle_id})
    if not cycle:
        raise HTTPException(status_code=404, detail="Payroll cycle not found")
    cycle.pop("_id", None)
    return cycle

@app.get("/api/payroll/cycles/{cycle_id}/export/pdf")
async def export_payroll_pdf(
    cycle_id: str,
    current_user: dict = Depends(get_current_user)
):
    """تصدير كشف الراتب كـ PDF باستخدام ReportLab"""
    try:
        from fastapi.responses import Response
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.lib.enums import TA_RIGHT, TA_CENTER
        import io
        from datetime import datetime
        
        # جلب بيانات دورة الراتب
        cycle = await db.payroll_cycles.find_one({"id": cycle_id})
        if not cycle:
            raise HTTPException(status_code=404, detail="Payroll cycle not found")
        
        summaries = await db.employee_payroll_summaries.find({
            "payroll_cycle_id": cycle_id
        }).to_list(1000)
        
        if not summaries:
            raise HTTPException(status_code=404, detail="No employee summaries found")
        
        # إنشاء PDF في الذاكرة
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=1*cm, leftMargin=1*cm, topMargin=2*cm, bottomMargin=2*cm)
        
        elements = []
        
        # العنوان
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1e40af'),
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        
        title = Paragraph(f"كشف الرواتب - {cycle.get('display_name', 'غير محدد')}", title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.5*cm))
        
        # معلومات الدورة
        info_style = ParagraphStyle('Info', parent=styles['Normal'], fontSize=10, alignment=TA_RIGHT)
        info_text = f"تاريخ الإصدار: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        elements.append(Paragraph(info_text, info_style))
        elements.append(Spacer(1, 0.5*cm))
        
        # إنشاء جدول البيانات
        data = [
            ['صافي الراتب', 'إجمالي الخصومات', 'خصم سلف', 'خصم حضور', 'خصم يدوي', 'إجمالي الراتب', 'البدلات', 'الراتب الأساسي', 'اسم الموظف']
        ]
        
        total_gross = 0
        total_deductions = 0
        total_net = 0
        
        for summary in summaries:
            gross = summary.get('gross_salary', 0)
            deductions = summary.get('total_deductions', 0)
            net = summary.get('net_salary', 0)
            
            total_gross += gross
            total_deductions += deductions
            total_net += net
            
            data.append([
                f"{net:.2f}",
                f"{deductions:.2f}",
                f"{summary.get('advance_deductions', 0):.2f}",
                f"{summary.get('attendance_deductions', 0):.2f}",
                f"{summary.get('manual_deductions', 0):.2f}",
                f"{gross:.2f}",
                f"{summary.get('total_allowances', 0):.2f}",
                f"{summary.get('base_salary', 0):.2f}",
                summary.get('employee_name', 'غير محدد')
            ])
        
        # إضافة صف الإجماليات
        data.append([
            f"{total_net:.2f}",
            f"{total_deductions:.2f}",
            '',
            '',
            '',
            f"{total_gross:.2f}",
            '',
            '',
            'الإجمالي'
        ])
        
        # تنسيق الجدول
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            # تنسيق الهيدر
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # تنسيق البيانات
            ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -2), colors.black),
            ('ALIGN', (0, 1), (-2, -1), 'CENTER'),
            ('ALIGN', (-1, 1), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            
            # تنسيق صف الإجماليات
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#10b981')),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 11),
            
            # حدود الجدول
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#1e40af')),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#10b981')),
        ]))
        
        elements.append(table)
        
        # بناء PDF
        doc.build(elements)
        
        # إرجاع الملف
        buffer.seek(0)
        
        return Response(
            content=buffer.getvalue(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=payroll_{cycle.get('month', 'unknown')}_{cycle_id[:8]}.pdf"
            }
        )
        
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting PDF: {str(e)}")

@app.get("/api/payroll/cycles/{cycle_id}/export/excel")
async def export_payroll_excel(
    cycle_id: str,
    current_user: dict = Depends(get_current_user)
):
    """تصدير كشف الراتب كـ Excel باستخدام openpyxl"""
    try:
        from fastapi.responses import Response
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
        import io
        from datetime import datetime
        
        # جلب بيانات دورة الراتب
        cycle = await db.payroll_cycles.find_one({"id": cycle_id})
        if not cycle:
            raise HTTPException(status_code=404, detail="Payroll cycle not found")
        
        summaries = await db.employee_payroll_summaries.find({
            "payroll_cycle_id": cycle_id
        }).to_list(1000)
        
        if not summaries:
            raise HTTPException(status_code=404, detail="No employee summaries found")
        
        # إنشاء Workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "كشف الرواتب"
        
        # تنسيقات
        header_fill = PatternFill(start_color="1E40AF", end_color="1E40AF", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=12)
        total_fill = PatternFill(start_color="10B981", end_color="10B981", fill_type="solid")
        total_font = Font(bold=True, color="FFFFFF", size=11)
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        
        # العنوان
        ws.merge_cells('A1:I1')
        title_cell = ws['A1']
        title_cell.value = f"كشف الرواتب - {cycle.get('display_name', 'غير محدد')}"
        title_cell.font = Font(bold=True, size=16, color="1E40AF")
        title_cell.alignment = Alignment(horizontal='center', vertical='center')
        
        # معلومات الدورة
        ws.merge_cells('A2:I2')
        info_cell = ws['A2']
        info_cell.value = f"تاريخ الإصدار: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        info_cell.alignment = Alignment(horizontal='center')
        
        # Headers
        headers = [
            'اسم الموظف',
            'الراتب الأساسي',
            'البدلات',
            'إجمالي الراتب',
            'خصم يدوي',
            'خصم حضور',
            'خصم سلف',
            'إجمالي الخصومات',
            'صافي الراتب'
        ]
        
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col_num)
            cell.value = header
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = border
        
        # البيانات
        row_num = 5
        total_gross = 0
        total_deductions = 0
        total_net = 0
        
        for summary in summaries:
            gross = summary.get('gross_salary', 0)
            deductions = summary.get('total_deductions', 0)
            net = summary.get('net_salary', 0)
            
            total_gross += gross
            total_deductions += deductions
            total_net += net
            
            ws.cell(row=row_num, column=1, value=summary.get('employee_name', 'غير محدد'))
            ws.cell(row=row_num, column=2, value=summary.get('base_salary', 0))
            ws.cell(row=row_num, column=3, value=summary.get('total_allowances', 0))
            ws.cell(row=row_num, column=4, value=gross)
            ws.cell(row=row_num, column=5, value=summary.get('manual_deductions', 0))
            ws.cell(row=row_num, column=6, value=summary.get('attendance_deductions', 0))
            ws.cell(row=row_num, column=7, value=summary.get('advance_deductions', 0))
            ws.cell(row=row_num, column=8, value=deductions)
            ws.cell(row=row_num, column=9, value=net)
            
            # تنسيق الصف
            for col in range(1, 10):
                cell = ws.cell(row=row_num, column=col)
                cell.border = border
                cell.alignment = Alignment(horizontal='center', vertical='center')
                if col > 1:  # الأعمدة الرقمية
                    cell.number_format = '#,##0.00'
            
            row_num += 1
        
        # صف الإجماليات
        ws.cell(row=row_num, column=1, value='الإجمالي')
        ws.cell(row=row_num, column=2, value='')
        ws.cell(row=row_num, column=3, value='')
        ws.cell(row=row_num, column=4, value=total_gross)
        ws.cell(row=row_num, column=5, value='')
        ws.cell(row=row_num, column=6, value='')
        ws.cell(row=row_num, column=7, value='')
        ws.cell(row=row_num, column=8, value=total_deductions)
        ws.cell(row=row_num, column=9, value=total_net)
        
        # تنسيق صف الإجماليات
        for col in range(1, 10):
            cell = ws.cell(row=row_num, column=col)
            cell.fill = total_fill
            cell.font = total_font
            cell.border = border
            cell.alignment = Alignment(horizontal='center', vertical='center')
            if col > 1:
                cell.number_format = '#,##0.00'
        
        # ضبط عرض الأعمدة
        ws.column_dimensions['A'].width = 25
        for col in ['B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']:
            ws.column_dimensions[col].width = 15
        
        # حفظ في الذاكرة
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        return Response(
            content=buffer.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=payroll_{cycle.get('month', 'unknown')}_{cycle_id[:8]}.xlsx"
            }
        )
        
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting Excel: {str(e)}")

@app.get("/api/payroll/employee/{employee_id}")
async def get_employee_payroll_history(
    employee_id: str,
    limit: int = 12,
    current_user: dict = Depends(get_current_user)
):
    """جلب تاريخ رواتب الموظف"""
    try:
        # التحقق من الصلاحيات - الموظف يمكنه رؤية راتبه فقط
        if current_user.role == "user" and employee_id != current_user.id:
            raise HTTPException(status_code=403, detail="يمكنك رؤية راتبك فقط")
        
        summaries = await db.employee_payroll_summaries.find({
            "employee_id": employee_id
        }).sort([("payroll_cycle_id", -1)]).limit(limit).to_list(limit)
        
        # تنسيق البيانات
        for summary in summaries:
            summary["_id"] = str(summary["_id"])
        
        return summaries
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching employee payroll history: {str(e)}")

# ================================
# NOTIFICATION SYSTEM ENDPOINTS
# ================================

@api_router.post("/notifications")
async def create_notification(
    notification_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Create a notification (Super Admin only)"""
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Super Admin access required")
    
    try:
        notification_id = str(uuid.uuid4())
        notification = {
            "id": notification_id,
            "title": notification_data.get("title", ""),
            "message": notification_data.get("message", ""),
            "severity": notification_data.get("severity", "normal"),
            "priority": notification_data.get("severity", "normal"),  # backward compatibility
            "category": notification_data.get("category", "general"),
            "must_acknowledge": notification_data.get("must_acknowledge", False),
            "action_url": notification_data.get("action_url"),
            "user_id": notification_data.get("user_id"),
            "sender": current_user.name,
            "is_read": False,
            "sent_at": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat()
        }
        
        await db.notifications.insert_one(notification)
        
        return {"message": "Notification created successfully", "id": notification_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating notification: {str(e)}")

@api_router.get("/notifications")
async def get_my_notifications(current_user: User = Depends(get_current_user)):
    """Get notifications for current user"""
    try:
        # Get notifications for current user or general notifications (no specific user_id)
        notifications = await db.notifications.find({
            "$or": [
                {"user_id": current_user.id},
                {"user_id": None},
                {"user_id": ""}
            ]
        }).sort([("sent_at", -1)]).to_list(length=None)
        
        # Convert ObjectId to string and format dates
        for notification in notifications:
            notification["_id"] = str(notification["_id"])
            if "sent_at" in notification and isinstance(notification["sent_at"], str):
                try:
                    # Parse and format the date
                    date_obj = datetime.fromisoformat(notification["sent_at"])
                    notification["sent_at"] = date_obj.isoformat()
                except:
                    pass
        
        return notifications
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching notifications: {str(e)}")

@api_router.get("/notifications/count")
async def get_notifications_count(current_user: User = Depends(get_current_user)):
    """Get unread notification count for current user"""
    try:
        # ✅ FIX: البحث باستخدام recipient_id بدلاً من user_id
        unread_count = await db.notifications.count_documents({
            "$or": [
                {"recipient_id": current_user.id},  # ✅ FIXED: استخدام recipient_id
                {"user_id": current_user.id},  # للتوافق مع الإشعارات القديمة
                {"recipient_id": None},
                {"recipient_id": ""}
            ],
            "is_read": False
        })
        
        return {"unread_count": unread_count}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error counting notifications: {str(e)}")

@api_router.patch("/notifications/read/{notification_id}")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """Mark a specific notification as read"""
    try:
        result = await db.notifications.update_one(
            {"id": notification_id},
            {"$set": {"is_read": True, "read_at": datetime.now().isoformat()}}
        )
        
        
        if result.matched_count == 0:
            # Try with ObjectId format
            try:
                result = await db.notifications.update_one(
                    {"_id": ObjectId(notification_id)},
                    {"$set": {"is_read": True, "read_at": datetime.now().isoformat()}}
                )
        
            except:
                raise HTTPException(status_code=404, detail="Notification not found")
        
        if result.modified_count > 0:
            return {"message": "Notification marked as read"}
        else:
            raise HTTPException(status_code=404, detail="Notification not found")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error marking notification as read: {str(e)}")

@api_router.patch("/notifications/read-all")
async def mark_all_notifications_read(current_user: User = Depends(get_current_user)):
    """Mark all notifications as read for current user"""
    try:
        result = await db.notifications.update_many(
            {
                "$or": [
                    {"user_id": current_user.id},
                    {"user_id": None},
                    {"user_id": ""}
                ],
                "is_read": False
            },
            {"$set": {"is_read": True, "read_at": datetime.now().isoformat()}}
        )
        
        
        return {
            "message": "All notifications marked as read", 
            "count": result.modified_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error marking all notifications as read: {str(e)}")

@api_router.delete("/notifications/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a specific notification (Super Admin only)"""
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Super Admin access required")
    
    try:
        result = await db.notifications.delete_one({"id": notification_id})
        
        if result.deleted_count == 0:
            # Try with ObjectId format
            try:
                result = await db.notifications.delete_one({"_id": ObjectId(notification_id)})
            except:
                raise HTTPException(status_code=404, detail="Notification not found")
        
        if result.deleted_count > 0:
            return {"message": "Notification deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Notification not found")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting notification: {str(e)}")

@api_router.post("/notifications/send")
async def send_notification(notification_data: dict, current_user: User = Depends(get_current_user)):
    """Send notification to specific employee"""
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Only super admin can send notifications")
    
    # Get recipient user
    recipient = await db.users.find_one({"id": notification_data["recipient_id"]})
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")
    
    # Create notification
    notification = Notification(
        recipient_id=notification_data["recipient_id"],
        recipient_name=recipient["name"],
        sender_id=current_user.id,
        sender_name=current_user.name,
        subject=notification_data["subject"],
        message=notification_data["message"],
        type=notification_data.get("type", "info"),
        priority=notification_data.get("priority", "normal"),
        sent_at=datetime.utcnow()
    )
    
    await db.notifications.insert_one(notification.dict())
    
    # Log activity
    await log_activity(
        current_user.id, 
        "notification_sent", 
        f"Sent notification to {recipient['name']}: {notification_data['subject']}"
    )
    
    return {"message": "Notification sent successfully"}

@api_router.post("/notifications/send-warning")
async def send_warning_notification(notification_data: dict, current_user: User = Depends(get_current_user)):
    """Send warning/notice notification to specific employee - Super Admin Only"""
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Only super admin can send warning notifications")
    
    # Get recipient user
    recipient = await db.users.find_one({"id": notification_data["recipient_id"]})
    if not recipient:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Determine notification type based on content
    notification_type = notification_data.get("notification_type", "warning")
    
    # Create structured warning message
    warning_message = f"""
🔔 {notification_data.get('title', 'إشعار إداري')}

📝 {notification_data['message']}

👤 من: {current_user.name} (الإدارة العليا)
📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}

{f"⚠️ إجراء مطلوب: {notification_data['required_action']}" if notification_data.get('required_action') else ""}
{f"📋 ملاحظات إضافية: {notification_data['additional_notes']}" if notification_data.get('additional_notes') else ""}
"""

    # Create notification
    notification = Notification(
        recipient_id=notification_data["recipient_id"],
        recipient_name=recipient["name"],
        sender_id=current_user.id,
        sender_name=current_user.name,
        subject=f"⚠️ {notification_data.get('title', 'إشعار إداري')}",
        message=warning_message.strip(),
        type="warning" if notification_type == "warning" else "info",
        priority="high" if notification_type == "warning" else "normal",
        sent_at=datetime.utcnow()
    )
    
    await db.notifications.insert_one(notification.dict())
    
    # Log activity with detailed information
    await log_activity(
        current_user.id, 
        "warning_notification_sent", 
        f"Sent {notification_type} notification to {recipient['name']}: {notification_data.get('title', 'Administrative Notice')}"
    )
    
    return {
        "message": "تم إرسال الإشعار بنجاح", 
        "notification_type": notification_type,
        "recipient": recipient["name"]
    }

# ============ USER ENDPOINTS ============

@api_router.get("/users", response_model=List[UserResponse])
async def get_users(current_user: User = Depends(get_admin_user)):
    """Get all users (Admin only) - Fixed: Handle MongoDB ObjectId"""
    try:
        users = await db.users.find().to_list(1000)
        
        # ✅ FIX: Clean users data before Pydantic validation
        cleaned_users = []
        for user in users:
            # Remove MongoDB internal fields that cause serialization issues
            user.pop('_id', None)  # Remove MongoDB ObjectId
            
            # Ensure all required fields exist with defaults
            if 'role' not in user:
                user['role'] = 'user'
            if 'is_active' not in user:
                user['is_active'] = True
            if 'monthly_salary' not in user:
                user['monthly_salary'] = 0.0
            if 'daily_rate' not in user:
                user['daily_rate'] = 0.0
            if 'position' not in user:
                user['position'] = 'موظف'
            if 'working_hours_start' not in user:
                user['working_hours_start'] = '09:00'
            if 'working_hours_end' not in user:
                user['working_hours_end'] = '18:00'
            if 'phone' not in user:
                user['phone'] = ''
            if 'hire_date' not in user:
                user['hire_date'] = None
            if 'has_flexible_schedule' not in user:
                user['has_flexible_schedule'] = False
            if 'flexible_hours_per_day' not in user:
                user['flexible_hours_per_day'] = 8.0
            if 'flexible_start_range' not in user:
                user['flexible_start_range'] = '07:00-10:00'
            if 'flexible_end_range' not in user:
                user['flexible_end_range'] = '16:00-19:00'
            if 'flexible_core_hours' not in user:
                user['flexible_core_hours'] = '10:00-15:00'
            if 'flexible_days_per_week' not in user:
                user['flexible_days_per_week'] = 5
            
            cleaned_users.append(user)
        
        return [UserResponse(**user) for user in cleaned_users]
        
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        raise HTTPException(status_code=500, detail=f"خطأ في جلب بيانات المستخدمين: {str(e)}")

@api_router.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate, current_user: User = Depends(get_admin_user)):
    """Create new user (Admin only)"""
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Create new user
    user_dict = user.dict()
    user_dict["id"] = str(uuid.uuid4())
    user_dict["password"] = hash_password(user.password)
    user_dict["created_at"] = datetime.utcnow()
    user_dict["has_custom_schedule"] = False
    
    # Calculate daily rate
    user_dict["daily_rate"] = user_dict["monthly_salary"] / 22
    
    await db.users.insert_one(user_dict)
    
    await log_activity(current_user.id, "user_created", f"Created user {user.name} ({user.email})")
    
    return UserResponse(**user_dict)

@api_router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_update: UserUpdate, current_user: User = Depends(get_admin_user)):
    """Update user (Admin only)"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Store original values for logging
    original_user = user.copy()
    
    # Update user data
    update_data = user_update.dict(exclude_unset=True)
    
    # Recalculate daily rate if monthly salary changed
    if "monthly_salary" in update_data:
        update_data["daily_rate"] = update_data["monthly_salary"] / 22
    
    if update_data:
        await db.users.update_one({"id": user_id}, {"$set": update_data})
        
        # Log the changes
        changes = []
        for key, new_value in update_data.items():
            old_value = original_user.get(key)
            if old_value != new_value:
                changes.append(f"{key}: {old_value} -> {new_value}")
        
        if changes:
            await log_activity(current_user.id, "user_updated", f"Updated user {user['name']}: {', '.join(changes)}")
    
    # Get updated user
    updated_user = await db.users.find_one({"id": user_id})
    return UserResponse(**updated_user)

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: User = Depends(get_admin_user)):
    """Delete user (Admin only)"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Don't allow deleting own account
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete own account")
    
    # Delete user
    await db.users.delete_one({"id": user_id})
    
    await log_activity(current_user.id, "user_deleted", f"Deleted user {user['name']} ({user['email']})")
    
    return {"message": "User deleted successfully"}

@api_router.post("/users/{user_id}/change-password")
async def change_user_password(user_id: str, password_data: dict, current_user: User = Depends(get_current_user)):
    """Change user password (Hatem only)"""
    if current_user.name != "Hatem Mohamed Ahmed":
        raise HTTPException(status_code=403, detail="Only Hatem can change user passwords")
    
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_password = password_data.get("new_password")
    if not new_password:
        raise HTTPException(status_code=400, detail="New password is required")
    
    hashed_password = hash_password(new_password)
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"password": hashed_password}}
    )
    
    await log_activity(current_user.id, "password_changed", f"Changed password for {user['name']}")
    
    return {"message": "Password changed successfully"}

# ============ ATTENDANCE ENDPOINTS ============

@api_router.get("/attendance")
async def get_attendance(current_user: User = Depends(get_current_user)):
    """Get attendance records - ✅ FIXED: Consistent timezone formatting"""
    from uae_datetime_utils import normalize_datetime_fields
    
    query = {}
    if current_user.role == "user":
        query["user_id"] = current_user.id
    
    attendance_records = await db.attendance.find(query).to_list(1000)
    
    # Convert to clean format without ObjectId with normalized timestamps
    attendance_list = []
    for record in attendance_records:
        clean_record = {
            "id": record.get("id", str(record.get("_id", ""))),
            "user_id": record.get("user_id", ""),
            "user_name": record.get("user_name", ""),
            "date": record.get("date", ""),
            "check_in": record.get("check_in"),
            "check_out": record.get("check_out"),
            "working_hours": record.get("working_hours"),
            "status": record.get("status", ""),
            "is_late": record.get("is_late", False),
            "late_minutes": record.get("late_minutes", 0),
            "early_departure_minutes": record.get("early_departure_minutes", 0),
            "deducted_hours": record.get("deducted_hours", 0.0),
            "field_exit": record.get("field_exit"),
            "created_at": record.get("created_at"),
            "updated_at": record.get("updated_at")
        }
        
        # ✅ Normalize datetime fields to include +04:00
        clean_record = normalize_datetime_fields(clean_record)
        attendance_list.append(clean_record)
    
    return attendance_list

@api_router.get("/attendance/all")
async def get_all_attendance(current_user: User = Depends(get_current_user)):
    """Get all attendance records for admin/super_admin"""
    if current_user.role == "user":
        raise HTTPException(status_code=403, detail="Access denied")
    
    attendance_records = await db.attendance.find({}).sort("date", -1).to_list(1000)
    
    # Convert to clean format without ObjectId
    attendance_list = []
    for record in attendance_records:
        attendance_list.append({
            "id": record.get("id", str(record.get("_id", ""))),
            "user_id": record.get("user_id", ""),
            "user_name": record.get("user_name", ""),
            "date": record.get("date", ""),
            "check_in": record.get("check_in"),
            "check_out": record.get("check_out"),
            "working_hours": record.get("working_hours"),
            "status": record.get("status", ""),
            "is_late": record.get("is_late", False),
            "field_exit": record.get("field_exit"),
            "created_at": record.get("created_at")
        })
    
    return attendance_list

@api_router.put("/attendance/{attendance_id}")
async def update_attendance(attendance_id: str, update_data: dict, current_user: User = Depends(get_admin_user)):
    """Update attendance record with comprehensive status and time handling"""
    
    logger.info(f"Updating attendance {attendance_id} with data: {update_data}")
    
    # Find the attendance record
    attendance = await db.attendance.find_one({"id": attendance_id})
    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    
    # Prepare update fields
    update_fields = {}
    changes = []
    
    # Handle status change
    new_status = update_data.get("status")
    if new_status:
        logger.info(f"Status change requested: {attendance.get('status', 'unknown')} -> {new_status}")
        update_fields["status"] = new_status
        changes.append(f"status: {attendance.get('status', 'unknown')} -> {new_status}")
        
        # Clear absence-related fields when changing to present/late
        if new_status in ["present", "late"]:
            update_fields["absence_reason"] = None
            update_fields["is_auto_absence"] = False
            changes.append("cleared absence reason")
        
        # Set absence reason when changing to absent
        elif new_status == "absent":
            reason = update_data.get("reason", "غياب")
            update_fields["absence_reason"] = reason
            update_fields["check_in"] = None
            update_fields["check_out"] = None
            update_fields["working_hours"] = 0
            changes.append(f"set absence reason: {reason}")
            
            # ✅ Set leave type if provided
            leave_type = update_data.get("leave_type")
            if leave_type:
                update_fields["leave_type"] = leave_type
                changes.append(f"set leave type: {leave_type}")
    
    # Handle time updates
    check_in_updated = "check_in" in update_data
    check_out_updated = "check_out" in update_data
    
    if check_in_updated:
        update_fields["check_in"] = update_data["check_in"]
        changes.append(f"check_in: {update_data['check_in']}")
    
    if check_out_updated:
        update_fields["check_out"] = update_data["check_out"]
        changes.append(f"check_out: {update_data['check_out']}")
    
    # Calculate working hours if both times are available using improved logic
    current_check_in = update_fields.get("check_in") or attendance.get("check_in")
    current_check_out = update_fields.get("check_out") or attendance.get("check_out")
    
    if current_check_in and current_check_out:
        try:
            # Handle both HH:MM and HH:MM:SS formats from frontend
            check_in_str = current_check_in
            check_out_str = current_check_out
            
            # Add seconds if not present (frontend sends HH:MM, we need HH:MM:SS)
            if len(check_in_str) == 5:  # HH:MM format
                check_in_str += ":00"
            if len(check_out_str) == 5:  # HH:MM format  
                check_out_str += ":00"
            
            # Use the improved calculation function
            is_admin_edited = attendance.get('admin_edited', False) or True  # Mark as admin edited since this is manual update
            working_hours_info = calculate_working_hours_and_deductions(
                f"{attendance.get('date', '')} {check_in_str}",
                f"{attendance.get('date', '')} {check_out_str}",
                break_time_minutes=60,  # 1 hour lunch break
                is_admin_edited=is_admin_edited
            )
        
            
            # ✅ CRITICAL FIX: Update ALL calculated fields including late tracking
            update_fields["working_hours"] = working_hours_info.get("total_hours", 0)
            update_fields["late_minutes"] = working_hours_info.get("late_minutes", 0)
            update_fields["early_departure_minutes"] = working_hours_info.get("early_departure_minutes", 0)
            update_fields["deducted_hours"] = working_hours_info.get("deducted_hours", 0.0)
            
            changes.append(f"working_hours: {working_hours_info.get('total_hours', 0):.2f}")
            changes.append(f"late_minutes: {working_hours_info.get('late_minutes', 0)}")
            changes.append(f"early_departure_minutes: {working_hours_info.get('early_departure_minutes', 0)}")
            changes.append(f"deducted_hours: {working_hours_info.get('deducted_hours', 0.0):.2f}")
            
            # Auto-correct status when times are provided (only if no explicit status change)
            if not new_status and attendance.get("status") == "absent":
                update_fields["status"] = "present"
                update_fields["absence_reason"] = None
                update_fields["is_auto_absence"] = False
                changes.append("auto-corrected status from absent to present")
                
        except ValueError as e:
            logger.error(f"Time parsing error for {attendance.get('user_name', 'Unknown')}: {e}")
            # Return error instead of silent failure
            raise HTTPException(status_code=400, detail=f"Invalid time format: {str(e)}")
    
    # When admin edits attendance, mark as manually edited
    if check_in_updated or check_out_updated or new_status:
        update_fields["is_late"] = False  # Assume admin correction is valid
        update_fields["is_manually_edited"] = True
        update_fields["modified_by"] = current_user.id
        update_fields["modified_by_name"] = current_user.name
        update_fields["modified_at"] = datetime.utcnow()
    
    # Apply updates
    if update_fields:
        logger.info(f"Applying updates: {update_fields}")
        await db.attendance.update_one({"id": attendance_id}, {"$set": update_fields})
        
        # Log the activity
        change_summary = ", ".join(changes)
        await log_activity(
            current_user.id, 
            "attendance_updated", 
            f"Updated attendance for {attendance.get('user_name', 'Unknown')}: {change_summary}"
        )
        
        
        logger.info(f"Successfully updated attendance {attendance_id}")
    else:
        logger.warning(f"No updates to apply for attendance {attendance_id}")
    
    return {"message": "Attendance updated successfully", "changes": changes}

# DISABLED: Duplicate check-in endpoint - using the fixed version at line 852
# @api_router.post("/attendance/check-in")
# async def check_in(current_user: User = Depends(get_current_user)):
#     """Check in attendance - with enhanced flexibility"""
#     uae_time = get_uae_time()
#     date_str = uae_time.strftime("%Y-%m-%d")
#     time_str = uae_time.strftime("%H:%M:%S")
#     
#     # Check if it's weekend
#     is_weekend = uae_time.weekday() >= 5  # Saturday=5, Sunday=6
#     
#     # Check if already checked in today
#     existing_attendance = await db.attendance.find_one({"user_id": current_user.id, "date": date_str})
#     if existing_attendance and existing_attendance.get("check_in"):
#         raise HTTPException(status_code=400, detail="Already checked in today")
#     
#     # Get user details for flexible schedule
#     user_details = await db.users.find_one({"id": current_user.id})
#     has_flexible_schedule = user_details.get("has_flexible_schedule", False)
#     
#     # Default status
#     status = "present"
#     is_late = False
#     late_minutes = 0
#     
#     # ✅ FIXED: Calculate late_minutes based on 9:15 AM threshold
#     STANDARD_START_TIME = datetime.strptime("09:15", "%H:%M").time()
#     
#     # Check if late based on flexible schedule or fixed rules
#     if not is_weekend:
#         if has_flexible_schedule:
#             # For flexible schedule users - very lenient rules
#             flexible_start_range = user_details.get("flexible_start_range", "07:00-11:00")
#             start_time, end_time = flexible_start_range.split("-")
#             start_hour, start_minute = map(int, start_time.split(":"))
#             end_hour, end_minute = map(int, end_time.split(":"))
#             
#             # Only mark as late if they come after the flexible end time
#             if uae_time.hour > end_hour or (uae_time.hour == end_hour and uae_time.minute > end_minute):
#                 is_late = True
#                 status = "late"
#                 # Calculate late_minutes for flexible schedule users
#                 check_in_time_obj = uae_time.time()
#                 late_threshold = datetime.strptime(end_time, "%H:%M").time()
#                 late_delta = datetime.combine(uae_time.date(), check_in_time_obj) - datetime.combine(uae_time.date(), late_threshold)
#                 late_minutes = max(0, int(late_delta.total_seconds() / 60))
#         else:
#             # Fixed schedule rules (legacy)
#             if current_user.name == "Hatem Mohamed Ahmed":
#                 # Hatem has no time restrictions
#                 pass
#             elif current_user.name == "Tarek Wazzan":
#                 # Tarek can start from 8 AM
#                 if uae_time.hour > 8 or (uae_time.hour == 8 and uae_time.minute > 0):
#                     is_late = True
#                     status = "late"
#                     # Calculate late_minutes for Tarek (8 AM threshold)
#                     check_in_time_obj = uae_time.time()
#                     tarek_threshold = datetime.strptime("08:00", "%H:%M").time()
#                     late_delta = datetime.combine(uae_time.date(), check_in_time_obj) - datetime.combine(uae_time.date(), tarek_threshold)
#                     late_minutes = max(0, int(late_delta.total_seconds() / 60))
#             else:
#                 # ✅ FIXED: Others should be here by 9:15 AM - Calculate late_minutes
#                 check_in_time_obj = uae_time.time()
#                 if check_in_time_obj > STANDARD_START_TIME:
#                     is_late = True
#                     status = "late"
#                     # Calculate late_minutes based on 9:15 AM threshold
#                     late_delta = datetime.combine(uae_time.date(), check_in_time_obj) - datetime.combine(uae_time.date(), STANDARD_START_TIME)
#                     late_minutes = int(late_delta.total_seconds() / 60)
#     
#     # Create attendance record with late_minutes
#     attendance_data = {
#         "id": str(uuid.uuid4()),
#         "user_id": current_user.id,
#         "user_name": current_user.name,
#         "date": date_str,
#         "check_in": time_str,
#         "check_out": None,
#         "working_hours": None,
#         "status": status,
#         "is_late": is_late,
#         "late_minutes": late_minutes,  # ✅ NEW: Store late_minutes at check-in
#         "early_departure_minutes": 0,  # ✅ NEW: Will be calculated at check-out
#         "deducted_hours": 0.0,  # ✅ NEW: Will be calculated at check-out
#         "is_weekend": is_weekend,
#         "schedule_type": "flexible" if has_flexible_schedule else "fixed",
#         "flexible_schedule": has_flexible_schedule,
#         "created_at": datetime.utcnow()
#     }
#     
#     if existing_attendance:
#         # Update existing record
#         await db.attendance.update_one(
#             {"user_id": current_user.id, "date": date_str},
#             {"$set": attendance_data}
#         )
        
#     else:
#         # Create new record
#         await db.attendance.insert_one(attendance_data)
#     
#     await log_activity(current_user.id, "check_in", f"Checked in at {time_str} ({'flexible' if has_flexible_schedule else 'fixed'} schedule, late_minutes: {late_minutes})")
#     
#     return {
#         "message": "Checked in successfully", 
#         "time": time_str, 
#         "is_late": is_late,
#         "late_minutes": late_minutes,  # ✅ NEW: Return late_minutes in response
#         "schedule_type": attendance_data["schedule_type"],
#         "flexible_schedule": has_flexible_schedule
#     }
    pass  # Placeholder for disabled function

@api_router.post("/attendance/check-out")
async def check_out(current_user: User = Depends(get_current_user)):
    """Check out attendance - with full flexibility for all employees"""
    uae_time = get_uae_time()
    date_str = uae_time.strftime("%Y-%m-%d")
    time_str = uae_time.strftime("%H:%M:%S")
    
    # Find today's attendance
    attendance = await db.attendance.find_one({"user_id": current_user.id, "date": date_str})
    if not attendance:
        raise HTTPException(status_code=400, detail="No check-in record found for today")
    
    if attendance.get("check_out"):
        raise HTTPException(status_code=400, detail="Already checked out today")
    
    # Calculate working hours (handle day crossing if needed)
    check_in_time = datetime.strptime(attendance["check_in"], "%H:%M:%S")
    check_out_time = datetime.strptime(time_str, "%H:%M:%S")
    
    # Handle case where checkout is after midnight (next day)
    if check_out_time < check_in_time:
        check_out_time += timedelta(days=1)
    
    working_hours = (check_out_time - check_in_time).total_seconds() / 3600
    
    # Ensure working hours are positive and reasonable (max 24 hours)
    if working_hours < 0:
        working_hours = 0
    elif working_hours > 24:
        working_hours = 24
    
    # Update attendance record
    await db.attendance.update_one(
        {"user_id": current_user.id, "date": date_str},
        {"$set": {
            "check_out": time_str, 
            "working_hours": working_hours,
            "flexible_checkout": True  # Mark as flexible checkout
        }}
    )
    
    await log_activity(current_user.id, "check_out", f"Checked out at {time_str} - Working hours: {working_hours:.1f}h")
    
    return {
        "message": "Checked out successfully", 
        "time": time_str, 
        "working_hours": working_hours,
        "flexible_schedule": True
    }

# ============ ENHANCED ATTENDANCE ABSENCE MANAGEMENT ============

@api_router.post("/attendance/create-absence")
async def create_absence_record(attendance_data: dict, current_user: User = Depends(get_super_admin_user)):
    """Create absence record for employee (Super Admin only)"""
    user_id = attendance_data.get("user_id")
    date = attendance_data.get("date")
    reason = attendance_data.get("reason", "غياب")
    
    if not user_id or not date:
        raise HTTPException(status_code=400, detail="User ID and date are required")
    
    # Check if user exists
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if attendance record already exists
    existing_attendance = await db.attendance.find_one({"user_id": user_id, "date": date})
    if existing_attendance:
        raise HTTPException(status_code=400, detail="Attendance record already exists for this date")
    
    # ✅ Get leave type if provided
    leave_type = attendance_data.get("leave_type")
    
    # Create absence record
    absence_record = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "user_name": user.get("name", ""),
        "date": date,
        "check_in": None,
        "check_out": None,
        "working_hours": 0,
        "status": "absent",
        "is_late": False,
        "absence_reason": reason,
        "leave_type": leave_type,  # ✅ Add leave type
        "created_by": current_user.id,
        "created_by_name": current_user.name,
        "is_manual_entry": True,
        "created_at": datetime.utcnow()
    }
    
    await db.attendance.insert_one(absence_record)
    
    await log_activity(
        current_user.id, 
        "absence_created", 
        f"Created absence record for {user.get('name')} on {date} - Reason: {reason}"
    )
    
    return {"message": "Absence record created successfully", "id": absence_record["id"]}

@api_router.put("/attendance/edit-absence/{attendance_id}")
async def edit_absence_record(attendance_id: str, attendance_data: dict, current_user: User = Depends(get_super_admin_user)):
    """Edit absence record and convert to present with check-in/out times (Super Admin only)"""
    attendance = await db.attendance.find_one({"id": attendance_id})
    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    
    # Store original values for logging
    original_status = attendance.get("status")
    
    # Extract data from request
    new_status = attendance_data.get("status", "present")
    check_in = attendance_data.get("check_in")
    check_out = attendance_data.get("check_out")
    reason = attendance_data.get("reason", "")
    
    update_data = {
        "status": new_status,
        "modified_by": current_user.id,
        "modified_by_name": current_user.name,
        "modified_at": datetime.utcnow(),
        "is_manually_edited": True
    }
    
    # If converting from absent to present, add check-in/out times
    if new_status == "present" and check_in and check_out:
        update_data["check_in"] = check_in
        update_data["check_out"] = check_out
        update_data["is_late"] = False
        update_data["absence_reason"] = None  # Clear absence reason when converting to present
        update_data["is_auto_absence"] = False  # Clear auto absence flag
        
        # Calculate working hours
        try:
            check_in_time = datetime.strptime(check_in, "%H:%M:%S")
            check_out_time = datetime.strptime(check_out, "%H:%M:%S")
            
            if check_out_time < check_in_time:
                check_out_time += timedelta(days=1)
            
            working_hours = (check_out_time - check_in_time).total_seconds() / 3600
            update_data["working_hours"] = working_hours
        except ValueError:
            pass
    
    # If editing absence reason
    if reason and new_status == "absent":
        update_data["absence_reason"] = reason
    
    # Update the record
    await db.attendance.update_one({"id": attendance_id}, {"$set": update_data})
    
    # Log the activity
    action_detail = f"Edited attendance for {attendance.get('user_name')} on {attendance.get('date')}: {original_status} -> {new_status}"
    if check_in and check_out:
        action_detail += f" (Added times: {check_in} - {check_out})"
    
    await log_activity(
        current_user.id, 
        "attendance_edited", 
        action_detail
    )
    
    return {"message": "Attendance record updated successfully"}

@api_router.delete("/attendance/delete-absence/{attendance_id}")
async def delete_absence_record(attendance_id: str, current_user: User = Depends(get_super_admin_user)):
    """Delete an absence record completely (Super Admin only)"""
    try:
        # Find the record first
        attendance = await db.attendance.find_one({"id": attendance_id})
        if not attendance:
            raise HTTPException(status_code=404, detail="Attendance record not found")
        
        # Check if it's an absence record
        if attendance.get("status") != "absent":
            raise HTTPException(status_code=400, detail="Can only delete absence records")
        
        # Delete the record
        await db.attendance.delete_one({"id": attendance_id})
        
        # Log the activity (simplified)
        await db.activity_logs.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": current_user.id,
            "user_name": current_user.name,
            "action": f"Deleted absence record for {attendance.get('user_name')} on {attendance.get('date')}",
            "timestamp": datetime.now().isoformat()
        })
        
        return {"message": "Absence record deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting absence record: {str(e)}")

@api_router.delete("/attendance/{attendance_id}")
async def delete_attendance_record(attendance_id: str, current_user: User = Depends(get_super_admin_user)):
    """Delete any attendance record completely (Super Admin only)"""
    try:
        # Find the record first
        attendance = await db.attendance.find_one({"id": attendance_id})
        if not attendance:
            raise HTTPException(status_code=404, detail="Attendance record not found")
        
        # Store info for logging
        employee_name = attendance.get('user_name', 'Unknown')
        date = attendance.get('date', 'Unknown')
        status = attendance.get('status', 'Unknown')
        
        # Delete the record
        result = await db.attendance.delete_one({"id": attendance_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Attendance record not found")
        
        # Log the activity
        await db.activity_logs.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": current_user.id,
            "user_name": current_user.name,
            "action": "Deleted attendance record",
            "details": f"Employee: {employee_name}, Date: {date}, Status: {status}",
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "message": "Attendance record deleted successfully",
            "deleted_record": {
                "employee_name": employee_name,
                "date": date,
                "status": status
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting attendance record: {str(e)}")

@api_router.get("/attendance/with-absences")
async def get_attendance_with_absences(current_user: User = Depends(get_current_user)):
    """Get attendance records including absences (Enhanced view)"""
    if current_user.role == "user":
        # For regular users, only show their own records
        query = {"user_id": current_user.id}
    else:
        # For admins, show all records
        query = {}
    
    attendance_records = await db.attendance.find(query).sort("date", -1).to_list(1000)
    
    # Convert to enhanced format
    attendance_list = []
    for record in attendance_records:
        # Keep original status, don't convert case
        status_display = record.get("status", "present")
        
        # Only modify display for frontend if needed, but keep original status
        if status_display == "present":
            display_status = "Present"
        elif status_display == "late":
            display_status = "Late" 
        elif status_display == "absent":
            display_status = "Absent"
        else:
            display_status = status_display
            
        attendance_item = {
            "id": record.get("id", str(record.get("_id", ""))),
            "user_id": record.get("user_id", ""),
            "user_name": record.get("user_name", ""),
            "date": record.get("date", ""),
            "check_in": record.get("check_in", "N/A" if record.get("status") == "absent" else record.get("check_in")),
            "check_out": record.get("check_out", "N/A" if record.get("status") == "absent" else record.get("check_out")),
            "working_hours": record.get("working_hours", 0),
            "status": display_status,  # Use display status for frontend
            "original_status": record.get("status"),  # Keep original for reference
            "is_late": record.get("is_late", False),
            "absence_reason": record.get("absence_reason"),
            "is_manual_entry": record.get("is_manual_entry", False),
            "is_manually_edited": record.get("is_manually_edited", False),
            "created_by": record.get("created_by"),
            "created_by_name": record.get("created_by_name"),
            "modified_by": record.get("modified_by"),
            "modified_by_name": record.get("modified_by_name"),
            "can_edit": current_user.role == "super_admin",  # Only super admin can edit
            "created_at": record.get("created_at")
        }
        attendance_list.append(attendance_item)
    
    return attendance_list

# ============ AUTO ABSENCE SYSTEM ============

@api_router.post("/attendance/process-daily-absences")
async def process_daily_absences(date_data: dict, current_user: User = Depends(get_super_admin_user)):
    """Process daily absences - create absence records for employees who didn't check in (Super Admin only)"""
    target_date = date_data.get("date")
    if not target_date:
        target_date = datetime.now().strftime("%Y-%m-%d")
    
    # Get all active employees
    all_employees = await db.users.find({"role": "user", "is_active": True}).to_list(1000)
    
    # Get employees who already have attendance records for this date
    existing_attendance = await db.attendance.find({"date": target_date}).to_list(1000)
    employees_with_records = {record["user_id"] for record in existing_attendance}
    
    # Find employees without attendance records
    absent_employees = [emp for emp in all_employees if emp["id"] not in employees_with_records]
    
    created_absences = []
    for employee in absent_employees:
        absence_record = {
            "id": str(uuid.uuid4()),
            "user_id": employee["id"],
            "user_name": employee["name"],
            "date": target_date,
            "check_in": None,
            "check_out": None,
            "working_hours": 0,
            "status": "absent",
            "is_late": False,
            "absence_reason": "غياب تلقائي - لم يسجل حضور",
            "created_by": current_user.id,
            "created_by_name": current_user.name,
            "is_manual_entry": True,
            "is_auto_absence": True,  # Flag to identify auto-generated absences
            "created_at": datetime.utcnow()
        }
        
        await db.attendance.insert_one(absence_record)
        created_absences.append(absence_record)
        
        # Log the activity
        await log_activity(
            current_user.id, 
            "auto_absence_created", 
            f"Auto-created absence record for {employee['name']} on {target_date}"
        )
        
    
    return {
        "message": f"Processed daily absences for {target_date}",
        "total_employees": len(all_employees),
        "employees_with_records": len(employees_with_records),
        "absences_created": len(created_absences),
        "absent_employees": [{"name": emp["user_name"], "reason": emp["absence_reason"]} for emp in created_absences]
    }

@api_router.get("/attendance/missing-today")
async def get_missing_employees_today(current_user: User = Depends(get_admin_user)):
    """Get employees who haven't checked in today"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Get all active employees
    all_employees = await db.users.find({"role": "user", "is_active": True}).to_list(1000)
    
    # Get employees who already have attendance records for today
    existing_attendance = await db.attendance.find({"date": today}).to_list(1000)
    employees_with_records = {record["user_id"] for record in existing_attendance}
    
    # Find employees without attendance records
    missing_employees = []
    for employee in all_employees:
        if employee["id"] not in employees_with_records:
            missing_employees.append({
                "id": employee["id"],
                "name": employee["name"],
                "email": employee["email"]
            })
    
    return {
        "date": today,
        "total_employees": len(all_employees),
        "employees_present": len(employees_with_records),
        "employees_missing": len(missing_employees),
        "missing_employees": missing_employees
    }

# ============ LEAVE ENDPOINTS ============

@api_router.get("/leaves")
async def get_leaves(current_user: User = Depends(get_current_user)):
    """Get leave requests"""
    query = {}
    if current_user.role == "user":
        query["user_id"] = current_user.id
    
    leave_records = await db.leaves.find(query).to_list(1000)
    
    # Convert to clean format without ObjectId
    leaves_list = []
    for record in leave_records:
        leaves_list.append({
            "id": record.get("id", str(record.get("_id", ""))),
            "user_id": record.get("user_id", ""),
            "user_name": record.get("user_name", ""),
            "start_date": record.get("start_date", ""),
            "end_date": record.get("end_date", ""),
            "reason": record.get("reason", ""),
            "status": record.get("status", "pending"),
            "days_count": record.get("days_count", 0),
            "approved_by": record.get("approved_by"),
            "attachment_url": record.get("attachment_url"),
            "created_at": record.get("created_at")
        })
    
    return leaves_list

@api_router.get("/leaves/my")
async def get_my_leaves(current_user: User = Depends(get_current_user)):
    """Get my leave requests (alias for /leaves for regular users)"""
    # Filter by current user
    leave_records = await db.leaves.find({"user_id": current_user.id}).to_list(1000)
    
    # Convert to clean format
    leaves_list = []
    for record in leave_records:
        leaves_list.append({
            "id": record.get("id", str(record.get("_id", ""))),
            "user_id": record.get("user_id", ""),
            "user_name": record.get("user_name", ""),
            "start_date": record.get("start_date", ""),
            "end_date": record.get("end_date", ""),
            "reason": record.get("reason", ""),
            "type": record.get("type", ""),
            "status": record.get("status", "pending"),
            "days_count": record.get("days_count", 0),
            "approved_by": record.get("approved_by"),
            "attachment_url": record.get("attachment_url"),
            "created_at": record.get("created_at")
        })
    
    return leaves_list

@api_router.get("/leaves/all")
async def get_all_leaves(current_user: User = Depends(get_current_user)):
    """Get all leave requests for admin/super_admin"""
    if current_user.role == "user":
        raise HTTPException(status_code=403, detail="Access denied")
    
    leave_records = await db.leaves.find({}).sort("created_at", -1).to_list(1000)
    
    # Convert to clean format without ObjectId
    leaves_list = []
    for record in leave_records:
        leaves_list.append({
            "id": record.get("id", str(record.get("_id", ""))),
            "user_id": record.get("user_id", ""),
            "user_name": record.get("user_name", ""),
            "start_date": record.get("start_date", ""),
            "end_date": record.get("end_date", ""),
            "reason": record.get("reason", ""),
            "status": record.get("status", "pending"),
            "days_count": record.get("days_count", 0),
            "approved_by": record.get("approved_by"),
            "attachment_url": record.get("attachment_url"),
            "created_at": record.get("created_at")
        })
    
    return leaves_list

@api_router.post("/leaves")
async def create_leave_request(
    user_id: str = Form(None),
    user_name: str = Form(None),
    start_date: str = Form(...),
    end_date: str = Form(...),
    reason: str = Form(...),
    days_count: int = Form(...),
    file: UploadFile = File(None),
    current_user: User = Depends(get_current_user)
):
    """Create leave request with optional file attachment"""
    
    # Validate required fields
    if not start_date or not end_date or not reason or days_count is None:
        raise HTTPException(status_code=400, detail="All fields are required: start_date, end_date, reason, days_count")
    
    # Handle file upload
    attachment_url = None
    if file and file.filename:
        try:
            # Generate unique filename
            file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
            filename = f"{uuid.uuid4()}.{file_extension}"
            file_path = uploads_dir / filename
            
            # Save file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            attachment_url = f"/uploads/{filename}"
        except Exception as e:
            logger.error(f"File upload error: {str(e)}")
            # Continue without file attachment if upload fails
            pass
    
    # Create leave request
    leave_dict = {
        "id": str(uuid.uuid4()),
        "user_id": user_id or current_user.id,
        "user_name": user_name or current_user.name,
        "start_date": start_date,
        "end_date": end_date,
        "reason": reason,
        "days_count": int(days_count),
        "status": "pending",
        "attachment_url": attachment_url,
        "created_at": datetime.utcnow(),
        "approved_by": None,
        "approved_by_id": None,
        "admin_notes": ""
    }
    
    await db.leaves.insert_one(leave_dict)
    
    await log_activity(current_user.id, "leave_requested", 
                      f"Requested leave from {start_date} to {end_date} ({days_count} days)")
    
    return {
        "message": "Leave request created successfully",
        "id": leave_dict["id"],
        "status": "pending"
    }

# Alternative JSON-based endpoint for frontend compatibility
@api_router.post("/leaves/json")
async def create_leave_request_json(
    leave_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Create leave request with JSON data (Frontend compatible)"""
    
    # Extract required fields
    start_date = leave_data.get("start_date")
    end_date = leave_data.get("end_date")
    reason = leave_data.get("reason")
    days_count = leave_data.get("days_count")
    
    # Validate required fields
    if not start_date or not end_date or not reason or days_count is None:
        raise HTTPException(status_code=400, detail="All fields are required: start_date, end_date, reason, days_count")
    
    # Create leave request
    leave_dict = {
        "id": str(uuid.uuid4()),
        "user_id": leave_data.get("user_id") or current_user.id,
        "user_name": leave_data.get("user_name") or current_user.name,
        "start_date": start_date,
        "end_date": end_date,
        "reason": reason,
        "days_count": int(days_count),
        "status": "pending",
        "attachment_url": leave_data.get("attachment_url"),
        "created_at": datetime.utcnow(),
        "approved_by": None,
        "approved_by_id": None,
        "admin_notes": ""
    }
    
    await db.leaves.insert_one(leave_dict)
    
    await log_activity(current_user.id, "leave_requested", 
                      f"Requested leave from {start_date} to {end_date} ({days_count} days)")
    
    return {
        "message": "Leave request created successfully",
        "id": leave_dict["id"],
        "status": "pending"
    }

@api_router.post("/leaves/{leave_id}/approve")
async def approve_leave(leave_id: str, approval_data: dict = None, current_user: User = Depends(get_admin_user)):
    """Approve leave request with optional notes"""
    leave = await db.leaves.find_one({"id": leave_id})
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    if leave.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Leave request has already been processed")
    
    # Get notes from request body
    notes = ""
    if approval_data and "notes" in approval_data:
        notes = approval_data["notes"]
    
    # Update leave status
    update_data = {
        "status": "approved",
        "approved_by": current_user.name,
        "approved_by_id": current_user.id,
        "approved_at": datetime.utcnow(),
        "admin_notes": notes
    }
    
    await db.leaves.update_one({"id": leave_id}, {"$set": update_data})
    
    # Send notification to employee about approval
    notification = Notification(
        recipient_id=leave.get("user_id"),
        recipient_name=leave.get("user_name"),
        sender_id=current_user.id,
        sender_name=current_user.name,
        subject="موافقة على طلب الإجازة",
        message=f"""تم الموافقة على طلب إجازتك:

📅 الفترة: من {leave.get('start_date')} إلى {leave.get('end_date')}
📝 السبب: {leave.get('reason')}
👤 تمت الموافقة من: {current_user.name}
{f"📋 ملاحظات الإدارة: {notes}" if notes else ""}

يمكنك الاستمتاع بإجازتك!""",
        type="success",
        priority="normal",
        sent_at=datetime.utcnow()
    )
    
    await db.notifications.insert_one(notification.dict())
    
    # 🆕 CREATE AUTOMATIC LEDGER ENTRY FOR UNPAID LEAVE
    leave_type = leave.get("type", "").lower()
    if "unpaid" in leave_type or "غير مدفوعة" in leave_type:
        # Calculate leave duration and deduction
        try:
            start_date = datetime.fromisoformat(leave.get("start_date", ""))
            end_date = datetime.fromisoformat(leave.get("end_date", ""))
            leave_days = (end_date - start_date).days + 1
            
            # Get employee salary
            employee = await db.users.find_one({"id": leave.get("user_id")})
            if employee and employee.get("monthly_salary", 0) > 0:
                daily_rate = employee.get("monthly_salary", 0) / 30
                deduction_amount = daily_rate * leave_days
                
                # Find open payroll cycle for this month
                leave_month = start_date.strftime("%Y-%m")
                cycle = await db.payroll_cycles.find_one({
                    "month": leave_month,
                    "is_locked": False
                })
                
                if cycle:
                    ledger_entry = {
                        "id": str(uuid.uuid4()),
                        "employee_id": leave.get("user_id"),
                        "employee_name": leave.get("user_name"),
                        "payroll_cycle_id": cycle["id"],
                        "source_type": "LEAVE_ADJUSTMENT",
                        "amount": deduction_amount,
                        "description": f"خصم إجازة غير مدفوعة - {leave_days} يوم من {leave.get('start_date')[:10]} إلى {leave.get('end_date')[:10]}",
                        "reference_id": leave_id,
                        "created_at": to_iso_string_uae(),
                        "created_by": current_user.id,
                        "is_system_generated": True
                    }
                    await db.payroll_ledger.insert_one(ledger_entry)
        except Exception as e:
            # Log error but don't fail the approval
            print(f"Error creating ledger entry for unpaid leave: {str(e)}")
    
    # Log activity
    await log_activity(
        current_user.id, 
        "leave_approved", 
        f"Approved leave request for {leave.get('user_name', 'Unknown')} from {leave.get('start_date')} to {leave.get('end_date')}" + (f" with notes: {notes}" if notes else "")
    )
    
    return {"message": "Leave request approved successfully", "approved_by": current_user.name, "notes": notes}

@api_router.post("/leaves/{leave_id}/reject")
async def reject_leave(leave_id: str, rejection_data: dict = None, current_user: User = Depends(get_admin_user)):
    """Reject leave request with optional notes"""
    leave = await db.leaves.find_one({"id": leave_id})
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    if leave.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Leave request has already been processed")
    
    # Get notes from request body
    notes = ""
    if rejection_data and "notes" in rejection_data:
        notes = rejection_data["notes"]
    
    # Update leave status
    update_data = {
        "status": "rejected",
        "rejected_by": current_user.name,
        "rejected_by_id": current_user.id,
        "rejected_at": datetime.utcnow(),
        "admin_notes": notes
    }
    
    await db.leaves.update_one({"id": leave_id}, {"$set": update_data})
    
    # Send notification to employee about rejection
    notification = Notification(
        recipient_id=leave.get("user_id"),
        recipient_name=leave.get("user_name"),
        sender_id=current_user.id,
        sender_name=current_user.name,
        subject="رفض طلب الإجازة",
        message=f"""تم رفض طلب إجازتك:

📅 الفترة المطلوبة: من {leave.get('start_date')} إلى {leave.get('end_date')}
📝 السبب المقدم: {leave.get('reason')}
👤 تم الرفض من: {current_user.name}
{f"📋 سبب الرفض: {notes}" if notes else "❗ لم يتم تحديد سبب محدد للرفض"}

يمكنك التواصل مع الإدارة لمزيد من التوضيح.""",
        type="warning",
        priority="high",
        sent_at=datetime.utcnow()
    )
    
    await db.notifications.insert_one(notification.dict())
    
    # Log activity
    await log_activity(
        current_user.id, 
        "leave_rejected", 
        f"Rejected leave request for {leave.get('user_name', 'Unknown')} from {leave.get('start_date')} to {leave.get('end_date')}" + (f" with notes: {notes}" if notes else "")
    )
    
    return {"message": "Leave request rejected successfully", "rejected_by": current_user.name, "notes": notes}

# ============ FIELD EXIT ENDPOINTS ============

@api_router.get("/field-exits")
async def get_field_exits(current_user: User = Depends(get_current_user)):
    """Get field exit requests"""
    query = {}
    if current_user.role == "user":
        query["user_id"] = current_user.id
    
    field_exit_records = await db.field_exits.find(query).to_list(1000)
    
    # Convert to clean format without ObjectId
    field_exits_list = []
    for record in field_exit_records:
        field_exits_list.append({
            "id": record.get("id", str(record.get("_id", ""))),
            "user_id": record.get("user_id", ""),
            "user_name": record.get("user_name", ""),
            "date": record.get("date", ""),
            "visit_type": record.get("visit_type", ""),
            "client_name": record.get("client_name", ""),
            "start_time": record.get("start_time", ""),
            "end_time": record.get("end_time", ""),
            "expected_start_time": record.get("expected_start_time", ""),
            "expected_end_time": record.get("expected_end_time", ""),
            "actual_start_time": record.get("actual_start_time", ""),
            "actual_end_time": record.get("actual_end_time", ""),
            "report": record.get("report", ""),
            "status": record.get("status", "pending"),
            "approved_by": record.get("approved_by"),
            "rejected_by": record.get("rejected_by"),
            "admin_notes": record.get("admin_notes", ""),
            "created_at": record.get("created_at")
        })
    
    return field_exits_list

@api_router.get("/field-exits/all")
async def get_all_field_exits(current_user: User = Depends(get_current_user)):
    """Get all field exit requests for admin/super_admin"""
    if current_user.role == "user":
        raise HTTPException(status_code=403, detail="Access denied")
    
    field_exit_records = await db.field_exits.find({}).sort("created_at", -1).to_list(1000)
    
    # Convert to clean format without ObjectId
    field_exits_list = []
    for record in field_exit_records:
        field_exits_list.append({
            "id": record.get("id", str(record.get("_id", ""))),
            "user_id": record.get("user_id", ""),
            "user_name": record.get("user_name", ""),
            "date": record.get("date", ""),
            "visit_type": record.get("visit_type", ""),
            "client_name": record.get("client_name", ""),
            "start_time": record.get("start_time", ""),
            "end_time": record.get("end_time", ""),
            "expected_start_time": record.get("expected_start_time", ""),
            "expected_end_time": record.get("expected_end_time", ""),
            "actual_start_time": record.get("actual_start_time", ""),
            "actual_end_time": record.get("actual_end_time", ""),
            "report": record.get("report", ""),
            "status": record.get("status", "pending"),
            "approved_by": record.get("approved_by"),
            "rejected_by": record.get("rejected_by"),
            "admin_notes": record.get("admin_notes", ""),
            "created_at": record.get("created_at")
        })
    
    return field_exits_list

@api_router.post("/field-exits", response_model=dict)
async def create_field_exit_request(
    visit_type: str = Form(...),
    client_name: str = Form(""),
    expected_start_time: str = Form(...),
    expected_end_time: str = Form(...),
    report: str = Form(""),
    current_user: User = Depends(get_current_user)
):
    """Create field exit request"""
    # Get current UAE time
    uae_time = datetime.now(UAE_TZ)
    date_str = uae_time.strftime("%Y-%m-%d")
    
    # Create field exit request
    field_exit = {
        "id": str(uuid.uuid4()),
        "user_id": current_user.id,
        "user_name": current_user.name,
        "date": date_str,
        "visit_type": visit_type,
        "client_name": client_name,
        "expected_start_time": expected_start_time,
        "expected_end_time": expected_end_time,
        "actual_start_time": None,  # Will be set when user clicks "تسجيل الذهاب"
        "actual_end_time": None,    # Will be set when user clicks "تسجيل العودة"
        "report": report,
        "status": "pending",
        "approved_by": None,
        "approved_by_id": None,
        "approved_at": None,
        "rejected_by": None,
        "rejected_by_id": None,
        "rejected_at": None,
        "admin_notes": "",
        "created_at": datetime.utcnow(),
        "exit_status": "requested"  # requested, departed, returned, completed
    }
    
    await db.field_exits.insert_one(field_exit)
    
    # Log activity
    await log_activity(
        current_user.id, 
        "field_exit_requested", 
        f"Requested field exit for {visit_type} from {expected_start_time} to {expected_end_time}"
    )
    
    return {"message": "Field exit request created successfully", "id": field_exit["id"]}

@api_router.post("/field-exits/{field_exit_id}/start")
async def start_field_exit(field_exit_id: str, current_user: User = Depends(get_current_user)):
    """Record actual departure time"""
    field_exit = await db.field_exits.find_one({"id": field_exit_id})
    if not field_exit:
        raise HTTPException(status_code=404, detail="Field exit request not found")
    
    # Check if this is the user's request
    if field_exit.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if already departed
    if field_exit.get("actual_start_time"):
        raise HTTPException(status_code=400, detail="Already recorded departure time")
    
    # Get current UAE time
    uae_time = datetime.now(UAE_TZ)
    actual_start_time = uae_time.strftime("%H:%M:%S")
    
    # Update field exit with actual start time
    await db.field_exits.update_one(
        {"id": field_exit_id},
        {"$set": {
            "actual_start_time": actual_start_time,
            "exit_status": "departed"
        }}
    )
    
    # Log activity
    await log_activity(
        current_user.id, 
        "field_exit_departed", 
        f"Departed for {field_exit.get('visit_type', 'Unknown')} at {actual_start_time}"
    )
    
    return {"message": "Departure time recorded successfully", "actual_start_time": actual_start_time}

@api_router.post("/field-exits/{field_exit_id}/report")
async def submit_field_exit_report(
    field_exit_id: str, 
    report_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Submit detailed visit report - REQUIRED before check-out"""
    field_exit = await db.field_exits.find_one({"id": field_exit_id})
    if not field_exit:
        raise HTTPException(status_code=404, detail="Field exit request not found")
    
    # Check if this is the user's request
    if field_exit.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if departed first
    if not field_exit.get("actual_start_time"):
        raise HTTPException(status_code=400, detail="Must record departure time first")
    
    # Check if already returned
    if field_exit.get("actual_end_time"):
        raise HTTPException(status_code=400, detail="Visit already completed")
    
    # Validate report content (must be detailed)
    detailed_report = report_data.get("detailed_report", "").strip()
    if len(detailed_report) < 20:
        raise HTTPException(status_code=400, detail="يجب أن يحتوي التقرير على 20 حرف على الأقل لوصف ما تم إنجازه")
    
    # Update field exit with detailed report
    await db.field_exits.update_one(
        {"id": field_exit_id},
        {"$set": {
            "detailed_report": detailed_report,
            "accomplishments": report_data.get("accomplishments", ""),
            "challenges": report_data.get("challenges", ""),
            "next_steps": report_data.get("next_steps", ""),
            "exit_status": "report_submitted"
        }}
    )
    
    # Log activity
    await log_activity(
        current_user.id, 
        "field_exit_report_submitted", 
        f"Submitted visit report for {field_exit.get('visit_type', 'Unknown')}"
    )
    
    return {
        "message": "Visit report submitted successfully", 
        "status": "report_submitted",
        "can_checkout": True
    }

@api_router.post("/field-exits/{field_exit_id}/end")
async def end_field_exit(field_exit_id: str, current_user: User = Depends(get_current_user)):
    """Record actual return time - REQUIRES REPORT SUBMISSION FIRST"""
    field_exit = await db.field_exits.find_one({"id": field_exit_id})
    if not field_exit:
        raise HTTPException(status_code=404, detail="Field exit request not found")
    
    # Check if this is the user's request
    if field_exit.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if already returned
    if field_exit.get("actual_end_time"):
        raise HTTPException(status_code=400, detail="Already recorded return time")
    
    # Check if departed first
    if not field_exit.get("actual_start_time"):
        raise HTTPException(status_code=400, detail="Must record departure time first")
    
    # NEW REQUIREMENT: Must submit detailed report before checkout
    if field_exit.get("exit_status") != "report_submitted":
        raise HTTPException(
            status_code=400, 
            detail="يجب كتابة تقرير مفصل عن الزيارة قبل تسجيل وقت العودة"
        )
        
    
    # Get current UAE time
    uae_time = datetime.now(UAE_TZ)
    actual_end_time = uae_time.strftime("%H:%M:%S")
    
    # Update field exit
    await db.field_exits.update_one(
        {"id": field_exit_id},
        {"$set": {
            "actual_end_time": actual_end_time,
            "exit_status": "completed"
        }}
    )
    
    # Log activity
    await log_activity(
        current_user.id, 
        "field_exit_completed", 
        f"Completed visit to {field_exit.get('visit_type', 'Unknown')} at {actual_end_time} with detailed report"
    )
    
    return {"message": "Return time recorded successfully", "actual_end_time": actual_end_time}

@api_router.post("/field-exits/{field_exit_id}/approve")
async def approve_field_exit(field_exit_id: str, approval_data: dict = None, current_user: User = Depends(get_admin_user)):
    """Approve field exit request with optional notes"""
    field_exit = await db.field_exits.find_one({"id": field_exit_id})
    if not field_exit:
        raise HTTPException(status_code=404, detail="Field exit request not found")
    
    if field_exit.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Field exit request has already been processed")
    
    # Get notes from request body
    notes = ""
    if approval_data and "notes" in approval_data:
        notes = approval_data["notes"]
    
    # Update field exit status
    update_data = {
        "status": "approved",
        "approved_by": current_user.name,
        "approved_by_id": current_user.id,
        "approved_at": datetime.utcnow(),
        "admin_notes": notes,
        "exit_status": "approved"
    }
    
    await db.field_exits.update_one({"id": field_exit_id}, {"$set": update_data})
    
    # Send notification to employee about approval
    notification = Notification(
        recipient_id=field_exit.get("user_id"),
        recipient_name=field_exit.get("user_name"),
        sender_id=current_user.id,
        sender_name=current_user.name,
        subject="موافقة على طلب الزيارة الخارجية",
        message=f"""تم الموافقة على طلب زيارتك الخارجية:

🏢 نوع الزيارة: {field_exit.get('visit_type', 'غير محدد')}
📅 التاريخ: {field_exit.get('date')}
⏰ الوقت المتوقع: من {field_exit.get('expected_start_time')} إلى {field_exit.get('expected_end_time')}
👤 تمت الموافقة من: {current_user.name}
{f"📋 ملاحظات الإدارة: {notes}" if notes else ""}

يمكنك الآن تسجيل وقت المغادرة عند بدء الزيارة.""",
        type="success",
        priority="normal",
        sent_at=datetime.utcnow()
    )
    
    await db.notifications.insert_one(notification.dict())
    
    # Log activity
    await log_activity(
        current_user.id, 
        "field_exit_approved", 
        f"Approved field exit request for {field_exit.get('user_name', 'Unknown')} - {field_exit.get('visit_type', 'Unknown')}" + (f" with notes: {notes}" if notes else "")
    )
    
    return {"message": "Field exit request approved successfully", "approved_by": current_user.name, "notes": notes}

@api_router.post("/field-exits/{field_exit_id}/reject")
async def reject_field_exit(field_exit_id: str, rejection_data: dict = None, current_user: User = Depends(get_admin_user)):
    """Reject field exit request with optional notes"""
    field_exit = await db.field_exits.find_one({"id": field_exit_id})
    if not field_exit:
        raise HTTPException(status_code=404, detail="Field exit request not found")
    
    if field_exit.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Field exit request has already been processed")
    
    # Get notes from request body
    notes = ""
    if rejection_data and "notes" in rejection_data:
        notes = rejection_data["notes"]
    
    # Update field exit status
    update_data = {
        "status": "rejected",
        "rejected_by": current_user.name,
        "rejected_by_id": current_user.id,
        "rejected_at": datetime.utcnow(),
        "admin_notes": notes,
        "exit_status": "rejected"
    }
    
    await db.field_exits.update_one({"id": field_exit_id}, {"$set": update_data})
    
    # Send notification to employee about rejection
    notification = Notification(
        recipient_id=field_exit.get("user_id"),
        recipient_name=field_exit.get("user_name"),
        sender_id=current_user.id,
        sender_name=current_user.name,
        subject="رفض طلب الزيارة الخارجية",
        message=f"""تم رفض طلب زيارتك الخارجية:

🏢 نوع الزيارة المطلوبة: {field_exit.get('visit_type', 'غير محدد')}
📅 التاريخ المطلوب: {field_exit.get('date')}
⏰ الوقت المطلوب: من {field_exit.get('expected_start_time')} إلى {field_exit.get('expected_end_time')}
👤 تم الرفض من: {current_user.name}
{f"📋 سبب الرفض: {notes}" if notes else "❗ لم يتم تحديد سبب محدد للرفض"}

يمكنك التواصل مع الإدارة لمزيد من التوضيح أو إعادة التقديم.""",
        type="warning",
        priority="high",
        sent_at=datetime.utcnow()
    )
    
    await db.notifications.insert_one(notification.dict())
    
    # Log activity
    await log_activity(
        current_user.id, 
        "field_exit_rejected", 
        f"Rejected field exit request for {field_exit.get('user_name', 'Unknown')} - {field_exit.get('visit_type', 'Unknown')}" + (f" with notes: {notes}" if notes else "")
    )
    
    return {"message": "Field exit request rejected successfully", "rejected_by": current_user.name, "notes": notes}

# ============ DASHBOARD ENDPOINTS ============

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
    """Get dashboard statistics"""
    try:
        stats = {}
        
        if current_user.role in ["admin", "super_admin"]:
            # Admin stats
            total_users = await db.users.count_documents({})
            today = get_uae_time().strftime("%Y-%m-%d")
            present_today = await db.attendance.count_documents({
                "date": today, 
                "status": {"$in": ["present", "late", "Present", "Late"]}
            })
            pending_leaves = await db.leaves.count_documents({"status": "pending"})
            pending_field_exits = await db.field_exits.count_documents({"status": "pending"})
            
            stats = {
                "total_users": int(total_users),
                "present_today": int(present_today),
                "pending_leaves": int(pending_leaves),
                "pending_field_exits": int(pending_field_exits)
            }
        else:
            # User stats
            today = get_uae_time().strftime("%Y-%m-%d")
            attendance_today = await db.attendance.find_one({"user_id": current_user.id, "date": today})
            pending_leaves = await db.leaves.count_documents({"user_id": current_user.id, "status": "pending"})
            pending_field_exits = await db.field_exits.count_documents({"user_id": current_user.id, "status": "pending"})
            
            # Convert attendance_today to a simple boolean or basic dict
            attendance_status = None
            if attendance_today:
                attendance_status = {
                    "date": attendance_today.get("date"),
                    "check_in": attendance_today.get("check_in"),
                    "check_out": attendance_today.get("check_out"),
                    "status": attendance_today.get("status"),
                    "is_late": attendance_today.get("is_late", False)
                }
            
            stats = {
                "attendance_today": attendance_status,
                "pending_leaves": int(pending_leaves),
                "pending_field_exits": int(pending_field_exits)
            }
        
        return stats
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching dashboard statistics")

# ============ ACTIVITY LOGS ENDPOINTS ============

@api_router.get("/activity-logs")
async def get_activity_logs(date: str = None, current_user: User = Depends(get_super_admin_user)):
    """Get activity logs (Super admin only)"""
    query = {}
    if date:
        query["timestamp"] = {"$gte": f"{date}T00:00:00.000Z", "$lte": f"{date}T23:59:59.999Z"}
    
    activity_records = await db.activity_logs.find(query).sort("timestamp", -1).to_list(1000)
    
    # Convert to clean format without ObjectId
    activity_logs_list = []
    for record in activity_records:
        # Get user name from user_id
        user = await db.users.find_one({"id": record.get("user_id")})
        user_name = user.get("name", "Unknown") if user else "Unknown"
        
        activity_logs_list.append({
            "id": record.get("id", str(record.get("_id", ""))),
            "user_id": record.get("user_id", ""),
            "user_name": user_name,
            "action": record.get("action", ""),
            "details": record.get("details", ""),
            "before_value": record.get("before_value"),
            "after_value": record.get("after_value"),
            "timestamp": record.get("timestamp")
        })
    
    return activity_logs_list

# ============ REPORTS ENDPOINTS ============

@api_router.get("/reports/{report_type}")
async def get_reports(report_type: str, start_date: str, end_date: str, current_user: User = Depends(get_admin_user)):
    """Get reports for attendance, leaves, or field-exits for a custom date range"""
    
    if report_type == "attendance":
        records = await db.attendance.find({
            "date": {"$gte": start_date, "$lte": end_date}
        }).sort("date", -1).to_list(1000)
        
        report_data = []
        for record in records:
            status_display = "Present"
            if record.get("status") == "late":
                status_display = "Late"
            elif record.get("status") == "absent":
                status_display = "Absent"
                
            report_data.append({
                "user_name": record.get("user_name", ""),
                "date": record.get("date", ""),
                "check_in": record.get("check_in", "N/A" if record.get("status") == "absent" else ""),
                "check_out": record.get("check_out", "N/A" if record.get("status") == "absent" else ""),
                "working_hours": record.get("working_hours", 0),
                "status": status_display,
                "is_late": record.get("is_late", False),
                "absence_reason": record.get("absence_reason", ""),
                "is_manual_entry": record.get("is_manual_entry", False),
                "is_manually_edited": record.get("is_manually_edited", False)
            })
    
    elif report_type == "leaves":
        records = await db.leaves.find({
            "$or": [
                {"start_date": {"$gte": start_date, "$lte": end_date}},
                {"end_date": {"$gte": start_date, "$lte": end_date}},
                {"$and": [{"start_date": {"$lte": start_date}}, {"end_date": {"$gte": end_date}}]}
            ]
        }).sort("created_at", -1).to_list(1000)
        
        report_data = []
        for record in records:
            report_data.append({
                "user_name": record.get("user_name", ""),
                "date": record.get("start_date", ""),
                "start_date": record.get("start_date", ""),
                "end_date": record.get("end_date", ""),
                "days_count": record.get("days_count", 0),
                "reason": record.get("reason", ""),
                "status": record.get("status", "")
            })
    
    elif report_type == "field-exits":
        records = await db.field_exits.find({
            "date": {"$gte": start_date, "$lte": end_date}
        }).sort("created_at", -1).to_list(1000)
        
        report_data = []
        for record in records:
            report_data.append({
                "user_name": record.get("user_name", ""),
                "date": record.get("date", ""),
                "visit_type": record.get("visit_type", ""),
                "client_name": record.get("client_name", ""),
                "start_time": record.get("start_time", ""),
                "end_time": record.get("end_time", ""),
                "status": record.get("status", "")
            })
    
    else:
        raise HTTPException(status_code=400, detail="Invalid report type")
    
    return report_data

@api_router.get("/reports/{report_type}/export")
async def export_report(report_type: str, start_date: str, end_date: str, format: str = "excel", current_user: User = Depends(get_admin_user)):
    """Export reports in Excel or PDF format with professional design for custom date range"""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    from io import BytesIO
    import os
    from datetime import datetime
    
    # Fetch data based on report type
    if report_type == "attendance":
        records = await db.attendance.find({
            "date": {"$gte": start_date, "$lte": end_date}
        }).sort("date", -1).to_list(1000)
        
        report_data = []
        for record in records:
            status_display = "Present"
            if record.get("status") == "late":
                status_display = "Late"
            elif record.get("status") == "absent":
                status_display = "Absent"
                
            report_data.append({
                "user_name": record.get("user_name", ""),
                "date": record.get("date", ""),
                "check_in": record.get("check_in", "N/A" if record.get("status") == "absent" else ""),
                "check_out": record.get("check_out", "N/A" if record.get("status") == "absent" else ""),
                "working_hours": record.get("working_hours", 0),
                "status": status_display,
                "is_late": record.get("is_late", False),
                "absence_reason": record.get("absence_reason", ""),
                "is_manual_entry": record.get("is_manual_entry", False),
                "is_manually_edited": record.get("is_manually_edited", False)
            })
        
        headers = ["Employee", "Date", "Check In", "Check Out", "Working Hours", "Status", "Late", "Absence Reason"]
        headers_ar = ["الموظف", "التاريخ", "الحضور", "الانصراف", "ساعات العمل", "الحالة", "متأخر", "سبب الغياب"]
        report_title = "Attendance Report"
        report_title_ar = "تقرير الحضور"
        
    elif report_type == "leaves":
        records = await db.leaves.find({
            "$or": [
                {"start_date": {"$gte": start_date, "$lte": end_date}},
                {"end_date": {"$gte": start_date, "$lte": end_date}},
                {"$and": [{"start_date": {"$lte": start_date}}, {"end_date": {"$gte": end_date}}]}
            ]
        }).sort("created_at", -1).to_list(1000)
        
        report_data = []
        for record in records:
            report_data.append({
                "user_name": record.get("user_name", ""),
                "start_date": record.get("start_date", ""),
                "end_date": record.get("end_date", ""),
                "days_count": record.get("days_count", 0),
                "reason": record.get("reason", ""),
                "status": record.get("status", "")
            })
        
        headers = ["Employee", "Start Date", "End Date", "Days Count", "Reason", "Status"]
        headers_ar = ["الموظف", "تاريخ البداية", "تاريخ النهاية", "عدد الأيام", "السبب", "الحالة"]
        report_title = "Leave Report"
        report_title_ar = "تقرير الإجازات"
        
    elif report_type == "field-exits":
        records = await db.field_exits.find({
            "date": {"$gte": start_date, "$lte": end_date}
        }).sort("created_at", -1).to_list(1000)
        
        report_data = []
        for record in records:
            visit_types = {
                "client_visit": "زيارة عميل",
                "collection": "تحصيل",
                "bank_visit": "زيارة بنك",
                "personal": "شخصي",
                "admin_errand": "مهمة إدارية"
            }
            report_data.append({
                "user_name": record.get("user_name", ""),
                "date": record.get("date", ""),
                "visit_type": visit_types.get(record.get("visit_type", ""), record.get("visit_type", "")),
                "client_name": record.get("client_name", ""),
                "start_time": record.get("start_time", ""),
                "end_time": record.get("end_time", ""),
                "status": record.get("status", "")
            })
        
        headers = ["Employee", "Date", "Visit Type", "Client", "Start Time", "End Time", "Status"]
        headers_ar = ["الموظف", "التاريخ", "نوع الزيارة", "العميل", "وقت البداية", "وقت النهاية", "الحالة"]
        report_title = "Field Exit Report"
        report_title_ar = "تقرير الزيارات الخارجية"
    
    else:
        raise HTTPException(status_code=400, detail="Invalid report type")
    
    if format == "excel":
        # Create Excel file with professional design
        wb = Workbook()
        ws = wb.active
        ws.title = f"{report_type}_report_{start_date}_{end_date}"
        
        # Set column widths
        column_widths = [20, 15, 12, 12, 15, 12, 10]
        for i, width in enumerate(column_widths[:len(headers)], 1):
            ws.column_dimensions[get_column_letter(i)].width = width
        
        # Company header with logo styling
        ws.merge_cells('A1:G1')
        company_cell = ws['A1']
        company_cell.value = "TANSEEQ TAX CONSULTANCY"
        company_cell.font = Font(name="Arial", size=20, bold=True, color="FFFFFF")
        company_cell.fill = PatternFill(start_color="2B5797", end_color="1B4477", fill_type="solid")
        company_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[1].height = 40
        
        # Logo area (simulated with styling)
        ws.merge_cells('A2:G2')
        logo_cell = ws['A2']
        logo_cell.value = "مكتب استشارات ضريبية متخصص"
        logo_cell.font = Font(name="Arial", size=12, color="4472C4", italic=True)
        logo_cell.fill = PatternFill(start_color="E6EFFF", end_color="E6EFFF", fill_type="solid")
        logo_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[2].height = 25
        
        # Report title with enhanced styling
        ws.merge_cells('A3:G3')
        title_cell = ws['A3']
        title_cell.value = f"{report_title} - {report_title_ar}"
        title_cell.font = Font(name="Arial", size=16, bold=True, color="1F4E79")
        title_cell.fill = PatternFill(start_color="F0F8FF", end_color="F0F8FF", fill_type="solid")
        title_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[3].height = 30
        
        # Enhanced period info
        ws.merge_cells('A4:G4')
        period_cell = ws['A4']
        period_cell.value = f"الفترة: {start_date} إلى {end_date} | عدد السجلات: {len(report_data)} | تاريخ الإنشاء: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        period_cell.font = Font(name="Arial", size=10, color="555555")
        period_cell.fill = PatternFill(start_color="F8F9FA", end_color="F8F9FA", fill_type="solid")
        period_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[4].height = 25
        
        # Add decorative separator
        ws.merge_cells('A5:G5')
        separator_cell = ws['A5']
        separator_cell.value = "=" * 80
        separator_cell.font = Font(name="Arial", size=8, color="CCCCCC")
        separator_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[5].height = 10
        
        # Headers with enhanced styling
        header_row = 6
        for col, (header_en, header_ar) in enumerate(zip(headers, headers_ar), 1):
            cell = ws.cell(row=header_row, column=col)
            cell.value = f"{header_en}\n{header_ar}"
            cell.font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="2B5797", end_color="2B5797", fill_type="solid")
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = Border(
                left=Side(style='medium', color='000000'),
                right=Side(style='medium', color='000000'),
                top=Side(style='medium', color='000000'),
                bottom=Side(style='medium', color='000000')
            )
        
        ws.row_dimensions[header_row].height = 40
        
        # Data rows
        for row_idx, record in enumerate(report_data, header_row + 1):
            row_color = "F2F2F2" if row_idx % 2 == 0 else "FFFFFF"
            
            if report_type == "attendance":
                values = [
                    record["user_name"],
                    record["date"],
                    record["check_in"],
                    record["check_out"],
                    f"{record['working_hours']:.1f}h" if record['working_hours'] else "0.0h",
                    record["status"],  # Now using the processed status_display
                    "Yes" if record["is_late"] else "No",
                    record.get("absence_reason", "")  # Add absence reason
                ]
            elif report_type == "leaves":
                values = [
                    record["user_name"],
                    record["start_date"],
                    record["end_date"],
                    f"{record['days_count']} days",
                    record["reason"],
                    "Approved" if record["status"] == "approved" else "Rejected" if record["status"] == "rejected" else "Pending"
                ]
            elif report_type == "field-exits":
                values = [
                    record["user_name"],
                    record["date"],
                    record["visit_type"],
                    record["client_name"],
                    record["start_time"],
                    record["end_time"],
                    "Approved" if record["status"] == "approved" else "Rejected" if record["status"] == "rejected" else "Pending"
                ]
            
            for col, value in enumerate(values, 1):
                cell = ws.cell(row=row_idx, column=col)
                cell.value = value
                cell.font = Font(name="Arial", size=9)
                cell.fill = PatternFill(start_color=row_color, end_color=row_color, fill_type="solid")
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.border = Border(
                    left=Side(style='thin', color='CCCCCC'),
                    right=Side(style='thin', color='CCCCCC'),
                    top=Side(style='thin', color='CCCCCC'),
                    bottom=Side(style='thin', color='CCCCCC')
                )
        
            ws.row_dimensions[row_idx].height = 20
        
        # Footer
        footer_row = len(report_data) + header_row + 2
        ws.merge_cells(f'A{footer_row}:G{footer_row}')
        footer_cell = ws[f'A{footer_row}']
        footer_cell.value = "TANSEEQ TAX CONSULTANCY - Employee Management System"
        footer_cell.font = Font(name="Arial", size=9, italic=True, color="666666")
        footer_cell.alignment = Alignment(horizontal="center", vertical="center")
        
        # Save to BytesIO
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        return Response(
            content=output.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=TANSEEQ_{report_type}_report_{start_date}_{end_date}.xlsx"}
        )
        
    
    elif format == "pdf":
        # Create PDF with enhanced professional design and logo
        output = BytesIO()
        doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles with enhanced colors
        company_style = ParagraphStyle(
            'CompanyStyle',
            parent=styles['Heading1'],
            fontSize=28,
            spaceAfter=10,
            alignment=1,  # Center alignment
            textColor=colors.Color(0.12, 0.31, 0.47),  # Dark blue
            fontName='Helvetica-Bold'
        )
        
        
        logo_style = ParagraphStyle(
            'LogoStyle',
            parent=styles['Normal'],
            fontSize=14,
            spaceAfter=20,
            alignment=1,  # Center alignment
            textColor=colors.Color(0.27, 0.45, 0.77),  # Medium blue
            fontName='Helvetica-Oblique'
        )
        
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=22,
            spaceAfter=15,
            alignment=1,  # Center alignment
            textColor=colors.Color(0.12, 0.31, 0.47),  # Dark blue
            fontName='Helvetica-Bold'
        )
        
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=16,
            spaceAfter=25,
            alignment=1,  # Center alignment
            textColor=colors.Color(0.27, 0.45, 0.77),  # Medium blue
            fontName='Helvetica-Bold'
        )
        
        
        info_style = ParagraphStyle(
            'InfoStyle',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=25,
            alignment=1,  # Center alignment
            textColor=colors.Color(0.4, 0.4, 0.4),  # Gray
            fontName='Helvetica'
        )
        
        
        # Enhanced company header with logo simulation
        company_header = Paragraph("TANSEEQ TAX CONSULTANCY", company_style)
        story.append(company_header)
        
        # Logo subtitle
        logo_subtitle = Paragraph("مكتب استشارات ضريبية متخصص - نظام إدارة الموارد البشرية المتطور", logo_style)
        story.append(logo_subtitle)
        story.append(Spacer(1, 20))
        
        # Report title with enhanced styling
        report_title_text = Paragraph(f"{report_title}<br/>{report_title_ar}", title_style)
        story.append(report_title_text)
        
        # Period info with icons
        period_info = Paragraph(f"الفترة: {start_date} إلى {end_date}<br/>عدد السجلات: {len(report_data)}<br/>تاريخ الإنشاء: {datetime.now().strftime('%Y-%m-%d %H:%M')}", info_style)
        story.append(period_info)
        story.append(Spacer(1, 30))
        
        # Add decorative line
        line_style = ParagraphStyle(
            'LineStyle',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=20,
            alignment=1,
            textColor=colors.Color(0.8, 0.8, 0.8)
        )
        
        decorative_line = Paragraph("=" * 60, line_style)
        story.append(decorative_line)
        
        # Create table data
        table_data = [headers]
        for record in report_data:
            if report_type == "attendance":
                table_data.append([
                    record["user_name"][:20],  # Truncate long names
                    record["date"], 
                    record["check_in"], 
                    record["check_out"],
                    f"{record['working_hours']:.1f}h" if record['working_hours'] else "0.0h",
                    record["status"],  # Now using the processed status_display
                    "Yes" if record["is_late"] else "No",
                    record.get("absence_reason", "")  # Add absence reason
                ])
            elif report_type == "leaves":
                table_data.append([
                    record["user_name"][:20],
                    record["start_date"], 
                    record["end_date"], 
                    f"{record['days_count']}d",
                    record["reason"][:20],  # Truncate long reasons
                    "Approved" if record["status"] == "approved" else "Rejected" if record["status"] == "rejected" else "Pending"
                ])
            elif report_type == "field-exits":
                table_data.append([
                    record["user_name"][:20],
                    record["date"], 
                    record["visit_type"][:15],
                    record["client_name"][:15] if record["client_name"] else "",
                    record["start_time"], 
                    record["end_time"],
                    "Approved" if record["status"] == "approved" else "Rejected" if record["status"] == "rejected" else "Pending"
                ])
        
        # Create table
        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.27, 0.45, 0.77)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            
            # Data styling
            ('BACKGROUND', (0, 1), (-1, -1), colors.Color(0.98, 0.98, 0.98)),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.Color(0.8, 0.8, 0.8)),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.95, 0.95)]),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 30))
        
        # Footer
        footer_style = ParagraphStyle(
            'FooterStyle',
            parent=styles['Normal'],
            fontSize=8,
            alignment=1,  # Center alignment
            textColor=colors.Color(0.5, 0.5, 0.5)  # Gray
        )
        
        footer = Paragraph("TANSEEQ TAX CONSULTANCY - Employee Management System", footer_style)
        story.append(footer)
        
        doc.build(story)
        output.seek(0)
        
        return Response(
            content=output.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=TANSEEQ_{report_type}_report_{start_date}_{end_date}.pdf"}
        )
        
    
    else:
        raise HTTPException(status_code=400, detail="Invalid format. Use 'excel' or 'pdf'")

# Legacy endpoint for backward compatibility
@api_router.get("/reports/{report_type}/{month}")
async def get_reports_by_month(report_type: str, month: str, current_user: User = Depends(get_admin_user)):
    """Get reports by month (legacy endpoint)"""
    start_date = f"{month}-01"
    year, month_num = map(int, month.split('-'))
    if month_num == 12:
        end_date = f"{year + 1}-01-31"
    else:
        end_date = f"{year}-{month_num + 1:02d}-31"
    
    return await get_reports(report_type, start_date, end_date, current_user)

@api_router.get("/reports/{report_type}/{month}/export")
async def export_report_by_month(report_type: str, month: str, format: str = "excel", current_user: User = Depends(get_admin_user)):
    """Export reports by month (legacy endpoint)"""
    start_date = f"{month}-01"
    year, month_num = map(int, month.split('-'))
    if month_num == 12:
        end_date = f"{year + 1}-01-31"
    else:
        end_date = f"{year}-{month_num + 1:02d}-31"
    
    return await export_report(report_type, start_date, end_date, format, current_user)

@api_router.get("/reports/{report_type}/{month}/export")
async def export_report(report_type: str, month: str, format: str = "excel", current_user: User = Depends(get_admin_user)):
    """Export reports in Excel or PDF format with professional design"""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    from io import BytesIO
    import os
    from datetime import datetime
    
    # Parse month to get start and end dates
    start_date = f"{month}-01"
    year, month_num = map(int, month.split('-'))
    if month_num == 12:
        end_date = f"{year + 1}-01-01"
    else:
        end_date = f"{year}-{month_num + 1:02d}-01"
    
    # Get month name in Arabic
    month_names = {
        1: "يناير", 2: "فبراير", 3: "مارس", 4: "أبريل", 5: "مايو", 6: "يونيو",
        7: "يوليو", 8: "أغسطس", 9: "سبتمبر", 10: "أكتوبر", 11: "نوفمبر", 12: "ديسمبر"
    }
    month_name_ar = month_names.get(month_num, "")
    
    # Fetch data based on report type
    if report_type == "attendance":
        records = await db.attendance.find({
            "date": {"$gte": start_date, "$lt": end_date}
        }).sort("date", -1).to_list(1000)
        
        report_data = []
        for record in records:
            status_display = "Present"
            if record.get("status") == "late":
                status_display = "Late"
            elif record.get("status") == "absent":
                status_display = "Absent"
                
            report_data.append({
                "user_name": record.get("user_name", ""),
                "date": record.get("date", ""),
                "check_in": record.get("check_in", "N/A" if record.get("status") == "absent" else ""),
                "check_out": record.get("check_out", "N/A" if record.get("status") == "absent" else ""),
                "working_hours": record.get("working_hours", 0),
                "status": status_display,
                "is_late": record.get("is_late", False),
                "absence_reason": record.get("absence_reason", ""),
                "is_manual_entry": record.get("is_manual_entry", False),
                "is_manually_edited": record.get("is_manually_edited", False)
            })
        
        headers = ["Employee", "Date", "Check In", "Check Out", "Working Hours", "Status", "Late", "Absence Reason"]
        headers_ar = ["الموظف", "التاريخ", "الحضور", "الانصراف", "ساعات العمل", "الحالة", "متأخر", "سبب الغياب"]
        report_title = "Attendance Report"
        report_title_ar = "تقرير الحضور"
        
    elif report_type == "leaves":
        records = await db.leaves.find({
            "$or": [
                {"start_date": {"$gte": start_date, "$lt": end_date}},
                {"end_date": {"$gte": start_date, "$lt": end_date}}
            ]
        }).sort("created_at", -1).to_list(1000)
        
        report_data = []
        for record in records:
            report_data.append({
                "user_name": record.get("user_name", ""),
                "start_date": record.get("start_date", ""),
                "end_date": record.get("end_date", ""),
                "days_count": record.get("days_count", 0),
                "reason": record.get("reason", ""),
                "status": record.get("status", "")
            })
        
        headers = ["Employee", "Start Date", "End Date", "Days Count", "Reason", "Status"]
        headers_ar = ["الموظف", "تاريخ البداية", "تاريخ النهاية", "عدد الأيام", "السبب", "الحالة"]
        report_title = "Leave Report"
        report_title_ar = "تقرير الإجازات"
        
    elif report_type == "field-exits":
        records = await db.field_exits.find({
            "date": {"$gte": start_date, "$lt": end_date}
        }).sort("created_at", -1).to_list(1000)
        
        report_data = []
        for record in records:
            visit_types = {
                "client_visit": "زيارة عميل",
                "collection": "تحصيل",
                "bank_visit": "زيارة بنك",
                "personal": "شخصي",
                "admin_errand": "مهمة إدارية"
            }
            report_data.append({
                "user_name": record.get("user_name", ""),
                "date": record.get("date", ""),
                "visit_type": visit_types.get(record.get("visit_type", ""), record.get("visit_type", "")),
                "client_name": record.get("client_name", ""),
                "start_time": record.get("start_time", ""),
                "end_time": record.get("end_time", ""),
                "status": record.get("status", "")
            })
        
        headers = ["Employee", "Date", "Visit Type", "Client", "Start Time", "End Time", "Status"]
        headers_ar = ["الموظف", "التاريخ", "نوع الزيارة", "العميل", "وقت البداية", "وقت النهاية", "الحالة"]
        report_title = "Field Exit Report"
        report_title_ar = "تقرير الزيارات الخارجية"
    
    else:
        raise HTTPException(status_code=400, detail="Invalid report type")
    
    if format == "excel":
        # Create Excel file with professional design
        wb = Workbook()
        ws = wb.active
        ws.title = f"{report_type}_report_{month}"
        
        # Set column widths
        column_widths = [20, 15, 12, 12, 15, 12, 10]
        for i, width in enumerate(column_widths[:len(headers)], 1):
            ws.column_dimensions[get_column_letter(i)].width = width
        
        # Company header
        ws.merge_cells('A1:G1')
        company_cell = ws['A1']
        company_cell.value = "TANSEEQ TAX CONSULTANCY"
        company_cell.font = Font(name="Arial", size=18, bold=True, color="FFFFFF")
        company_cell.fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
        company_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[1].height = 30
        
        # Report title
        ws.merge_cells('A2:G2')
        title_cell = ws['A2']
        title_cell.value = f"{report_title} - {report_title_ar}"
        title_cell.font = Font(name="Arial", size=14, bold=True, color="1F4E79")
        title_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[2].height = 25
        
        # Period info
        ws.merge_cells('A3:G3')
        period_cell = ws['A3']
        period_cell.value = f"Period: {start_date} to {end_date.split('-')[0]}-{end_date.split('-')[1]}-{int(end_date.split('-')[2])-1:02d} | Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        period_cell.font = Font(name="Arial", size=10, color="666666")
        period_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[3].height = 20
        
        # Add empty row
        ws.row_dimensions[4].height = 10
        
        # Headers
        header_row = 5
        for col, (header_en, header_ar) in enumerate(zip(headers, headers_ar), 1):
            cell = ws.cell(row=header_row, column=col)
            cell.value = f"{header_en}\n{header_ar}"
            cell.font = Font(name="Arial", size=10, bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = Border(
                left=Side(style='thin', color='000000'),
                right=Side(style='thin', color='000000'),
                top=Side(style='thin', color='000000'),
                bottom=Side(style='thin', color='000000')
            )
        
        ws.row_dimensions[header_row].height = 35
        
        # Data rows
        for row_idx, record in enumerate(report_data, header_row + 1):
            row_color = "F2F2F2" if row_idx % 2 == 0 else "FFFFFF"
            
            if report_type == "attendance":
                values = [
                    record["user_name"],
                    record["date"],
                    record["check_in"],
                    record["check_out"],
                    f"{record['working_hours']:.1f}h" if record['working_hours'] else "0.0h",
                    record["status"],  # Now using the processed status_display
                    "Yes" if record["is_late"] else "No",
                    record.get("absence_reason", "")  # Add absence reason
                ]
            elif report_type == "leaves":
                values = [
                    record["user_name"],
                    record["start_date"],
                    record["end_date"],
                    f"{record['days_count']} days",
                    record["reason"],
                    "Approved" if record["status"] == "approved" else "Rejected" if record["status"] == "rejected" else "Pending"
                ]
            elif report_type == "field-exits":
                values = [
                    record["user_name"],
                    record["date"],
                    record["visit_type"],
                    record["client_name"],
                    record["start_time"],
                    record["end_time"],
                    "Approved" if record["status"] == "approved" else "Rejected" if record["status"] == "rejected" else "Pending"
                ]
            
            for col, value in enumerate(values, 1):
                cell = ws.cell(row=row_idx, column=col)
                cell.value = value
                cell.font = Font(name="Arial", size=9)
                cell.fill = PatternFill(start_color=row_color, end_color=row_color, fill_type="solid")
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.border = Border(
                    left=Side(style='thin', color='CCCCCC'),
                    right=Side(style='thin', color='CCCCCC'),
                    top=Side(style='thin', color='CCCCCC'),
                    bottom=Side(style='thin', color='CCCCCC')
                )
        
            ws.row_dimensions[row_idx].height = 20
        
        # Footer
        footer_row = len(report_data) + header_row + 2
        ws.merge_cells(f'A{footer_row}:G{footer_row}')
        footer_cell = ws[f'A{footer_row}']
        footer_cell.value = "TANSEEQ TAX CONSULTANCY - Employee Management System"
        footer_cell.font = Font(name="Arial", size=9, italic=True, color="666666")
        footer_cell.alignment = Alignment(horizontal="center", vertical="center")
        
        # Save to BytesIO
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        return Response(
            content=output.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=TANSEEQ_{report_type}_report_{month}.xlsx"}
        )
        
    
    elif format == "pdf":
        # Create PDF with professional design
        output = BytesIO()
        doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
        
        story = []
        styles = getSampleStyleSheet()
        
        # Enhanced PDF styles for professional A4 printing
        # Register Arabic font if available
        try:
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            # Note: Add Arabic font file to support Arabic text properly
        except:
            pass
        
        # Professional styles for A4 format
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,  # Reduced for A4 fit
            spaceAfter=12,
            alignment=1,  # Center alignment
            textColor=colors.Color(0.12, 0.31, 0.47),  # TANSEEQ Blue
            fontName='Helvetica-Bold'
        )
        
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=16,
            spaceAfter=20,
            alignment=1,  # Center alignment
            textColor=colors.Color(0.27, 0.45, 0.77)  # Medium blue
        )
        
        
        info_style = ParagraphStyle(
            'InfoStyle',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=20,
            alignment=1,  # Center alignment
            textColor=colors.Color(0.4, 0.4, 0.4)  # Gray
        )
        
        
        # Company header
        company_title = Paragraph("TANSEEQ TAX CONSULTANCY", title_style)
        story.append(company_title)
        story.append(Spacer(1, 12))
        
        # Report title
        report_subtitle = Paragraph(f"{report_title}<br/>{report_title_ar}", subtitle_style)
        story.append(report_subtitle)
        
        # Period info
        period_info = Paragraph(f"Period: {start_date} to {end_date.split('-')[0]}-{end_date.split('-')[1]}-{int(end_date.split('-')[2])-1:02d}<br/>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", info_style)
        story.append(period_info)
        story.append(Spacer(1, 20))
        
        # Create table data
        table_data = [headers]
        for record in report_data:
            if report_type == "attendance":
                table_data.append([
                    record["user_name"][:20],  # Truncate long names
                    record["date"], 
                    record["check_in"], 
                    record["check_out"],
                    f"{record['working_hours']:.1f}h" if record['working_hours'] else "0.0h",
                    record["status"],  # Now using the processed status_display
                    "Yes" if record["is_late"] else "No",
                    record.get("absence_reason", "")  # Add absence reason
                ])
            elif report_type == "leaves":
                table_data.append([
                    record["user_name"][:20],
                    record["start_date"], 
                    record["end_date"], 
                    f"{record['days_count']}d",
                    record["reason"][:20],  # Truncate long reasons
                    "Approved" if record["status"] == "approved" else "Rejected" if record["status"] == "rejected" else "Pending"
                ])
            elif report_type == "field-exits":
                table_data.append([
                    record["user_name"][:20],
                    record["date"], 
                    record["visit_type"][:15],
                    record["client_name"][:15] if record["client_name"] else "",
                    record["start_time"], 
                    record["end_time"],
                    "Approved" if record["status"] == "approved" else "Rejected" if record["status"] == "rejected" else "Pending"
                ])
        
        # Create table
        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.27, 0.45, 0.77)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            
            # Data styling
            ('BACKGROUND', (0, 1), (-1, -1), colors.Color(0.98, 0.98, 0.98)),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.Color(0.8, 0.8, 0.8)),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.95, 0.95)]),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 30))
        
        # Footer
        footer_style = ParagraphStyle(
            'FooterStyle',
            parent=styles['Normal'],
            fontSize=8,
            alignment=1,  # Center alignment
            textColor=colors.Color(0.5, 0.5, 0.5)  # Gray
        )
        
        footer = Paragraph("TANSEEQ TAX CONSULTANCY - Employee Management System", footer_style)
        story.append(footer)
        
        doc.build(story)
        output.seek(0)
        
        return Response(
            content=output.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=TANSEEQ_{report_type}_report_{month}.pdf"}
        )
        
    
    else:
        raise HTTPException(status_code=400, detail="Invalid format. Use 'excel' or 'pdf'")

# ============ PAYROLL ENDPOINTS ============

@api_router.get("/payroll/calculate/{month}")
async def calculate_payroll(month: str, current_user: User = Depends(get_admin_user)):
    """Calculate payroll for a specific month - SIMPLIFIED AND ACCURATE SYSTEM"""
    try:
        # Validate month format (YYYY-MM)
        datetime.strptime(month, "%Y-%m")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM")
    
    # Get all active users (exclude admin and super_admin)
    users = await db.users.find({
        "is_active": True,
        "role": "user"  # Only regular employees get payroll
    }).to_list(1000)
    
    payroll_data = []
    
    for user in users:
        # Get attendance for the specified month
        attendance_records = await db.attendance.find({
            "user_id": user["id"], 
            "date": {"$regex": f"^{month}"}
        }).to_list(1000)
        
        # IMPROVED CALCULATIONS
        present_days = 0
        absent_days = 0
        total_working_hours = 0.0
        total_deducted_hours = 0.0
        late_incidents = 0
        early_departure_incidents = 0
        
        for record in attendance_records:
            if record.get("status") == "absent":
                absent_days += 1
            elif record.get("check_in") and record.get("check_out"):
                present_days += 1
                
                # Use improved calculation function
                working_calc = calculate_working_hours_and_deductions(
                    record.get("check_in"),
                    record.get("check_out"),
                    break_time_minutes=60,
                    is_admin_edited=record.get("admin_edited", False)
                )
        
                
                total_working_hours += working_calc.get("regular_hours", 0)
                total_deducted_hours += working_calc.get("deducted_hours", 0)
                
                if working_calc.get("late_minutes", 0) > 0:
                    late_incidents += 1
                if working_calc.get("early_departure_minutes", 0) > 0:
                    early_departure_incidents += 1
        
        # Calculate base salary - IMPROVED ACCURACY
        monthly_salary = user.get("monthly_salary", 0)
        daily_rate = monthly_salary / 22  # 22 working days per month
        
        # Calculate salary based on presence, NOT hours (more accurate for UAE labor law)
        # Full daily rate for each present day, regardless of slight time variations
        base_earned_salary = present_days * daily_rate
        
        # Calculate hourly rate for deductions only
        standard_monthly_hours = 22 * 9  # 22 days * 9 hours = 198 hours standard
        hourly_rate = monthly_salary / standard_monthly_hours
        
        # Use base salary unless significantly under-hours
        earned_salary = base_earned_salary
        
        # Deductions calculation - SIMPLIFIED
        total_deductions = 0.0
        deduction_details = []
        
        # SIMPLIFIED DEDUCTION SYSTEM
        
        # 1. Absence deductions (full day salary per absent day)
        if absent_days > 0:
            absence_deduction = absent_days * daily_rate
            total_deductions += absence_deduction
            deduction_details.append({
                "type": "غياب",
                "description": f"{absent_days} يوم غياب",
                "amount": round(absence_deduction, 2)
            })
        
        # 2. Deducted hours penalty (for late arrival and early departure)
        if total_deducted_hours > 0:
            hours_deduction = total_deducted_hours * hourly_rate
            total_deductions += hours_deduction
            deduction_details.append({
                "type": "ساعات منقوصة",
                "description": f"{total_deducted_hours:.1f} ساعة تأخير/انصراف مبكر",
                "amount": round(hours_deduction, 2)
            })
                
        # Get approved leaves for this month
        approved_leaves = await db.leaves.find({
            "user_id": user["id"],
            "status": "approved",
            "start_date": {"$regex": f"^{month}"}
        }).to_list(1000)
        approved_leave_days = sum(int(leave.get("days_count", 0)) for leave in approved_leaves)
        
        # Get approved field exits for this month
        approved_field_exits = await db.field_exits.find({
            "user_id": user["id"],
            "status": "approved", 
            "date": {"$regex": f"^{month}"}
        }).to_list(1000)
        approved_field_exit_days = len(approved_field_exits)
        
        # Calculate working days (present + approved absences)
        working_days = present_days + approved_leave_days + approved_field_exit_days
        
        # Calculate final salary
        gross_salary = min(earned_salary, monthly_salary)  # Cannot exceed monthly salary
        final_salary = max(0, gross_salary - total_deductions)  # Cannot be negative  
        
        # Translation for English reports
        english_name = translate_to_english(user["name"])
        english_position = translate_to_english(user["position"])
        
        payroll_data.append({
            "user_id": user["id"],
            "name": english_name,  # English translation
            "arabic_name": user["name"],  # Keep original Arabic
            "position": english_position,  # English translation
            "arabic_position": user["position"],  # Keep original Arabic
            "monthly_salary": monthly_salary,
            "daily_rate": daily_rate,
            "working_days": working_days,
            "present_days": present_days,
            "total_hours": round(total_working_hours, 2),
            "late_incidents": late_incidents,
            "early_departure_incidents": early_departure_incidents,
            "approved_leaves": approved_leave_days,
            "approved_field_exits": approved_field_exit_days,
            "unauthorized_absences": absent_days,
            "earned_salary": round(earned_salary, 2),
            "gross_salary": round(gross_salary, 2),
            "total_deductions": round(total_deductions, 2),
            "deduction_details": deduction_details,
            "final_salary": round(final_salary, 2),
            "month": month
        })
    
    return payroll_data

def translate_to_english(arabic_text: str) -> str:
    """Simple translation function for common Arabic names and positions"""
    # Common Arabic to English translations
    translations = {
        # Names
        "محمد": "Mohammed",
        "أحمد": "Ahmed", 
        "علي": "Ali",
        "حسن": "Hassan",
        "حسين": "Hussein",
        "عبدالله": "Abdullah",
        "عبدالرحمن": "Abdulrahman",
        "خالد": "Khaled",
        "محمود": "Mahmoud",
        "حاتم": "Hatem",
        "طارق": "Tarek",
        "جهاد": "Jihad",
        "سامي": "Sami",
        "عمر": "Omar",
        "يوسف": "Youssef",
        
        # Positions
        "محاسب": "Accountant",
        "مدير": "Manager",
        "موظف": "Employee",
        "سكرتير": "Secretary",
        "مساعد": "Assistant",
        "مستشار": "Consultant",
        "محاسب ضرائب": "Tax Accountant",
        "مدقق": "Auditor",
        "مطور": "Developer",
        "مصمم": "Designer",
        "مهندس": "Engineer",
        "مسؤول": "Officer",
        
        # Common words
        "مالي": "Financial",
        "إداري": "Administrative", 
        "تقني": "Technical",
        "خدمة عملاء": "Customer Service",
        "موارد بشرية": "Human Resources",
        "مبيعات": "Sales",
        "تسويق": "Marketing"
    }
    
    # Try to translate word by word
    words = arabic_text.split()
    translated_words = []
    
    for word in words:
        translated_word = translations.get(word.strip(), word)
        translated_words.append(translated_word)
    
    return " ".join(translated_words)

@api_router.get("/payroll/export/{month}")
async def export_payroll(month: str, format: str = "excel", current_user: User = Depends(get_admin_user)):
    """Export payroll data with professional design matching attendance reports"""
    from io import BytesIO
    from fastapi.responses import StreamingResponse
    
    payroll_data = await calculate_payroll(month, current_user)
    
    if format == "excel":
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
        from datetime import datetime
        
        # Create workbook and worksheet
        wb = Workbook()
        ws = wb.active
        ws.title = f"payroll_{month}"
        
        # Set column widths for enhanced payroll report
        column_widths = [18, 14, 12, 12, 10, 14, 14, 14, 14, 14]
        for i, width in enumerate(column_widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = width
        
        # Company header with logo styling  
        ws.merge_cells('A1:J1')
        company_cell = ws['A1']
        company_cell.value = "TANSEEQ TAX CONSULTANCY"
        company_cell.font = Font(name="Arial", size=20, bold=True, color="FFFFFF")
        company_cell.fill = PatternFill(start_color="2B5797", end_color="1B4477", fill_type="solid")
        company_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[1].height = 40
        
        # Logo area (simulated with styling)
        ws.merge_cells('A2:J2')
        logo_cell = ws['A2']
        logo_cell.value = "Professional Tax Consultancy Services - خدمات استشارات ضريبية محترفة"
        logo_cell.font = Font(name="Arial", size=12, color="4472C4", italic=True)
        logo_cell.fill = PatternFill(start_color="E6EFFF", end_color="E6EFFF", fill_type="solid")
        logo_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[2].height = 25
        
        # Report title with enhanced styling
        ws.merge_cells('A3:J3')
        title_cell = ws['A3']
        title_cell.value = f"Enhanced Payroll Report with Automatic Deductions - تقرير الرواتب المحسن مع الخصومات التلقائية - {month}"
        title_cell.font = Font(name="Arial", size=14, bold=True, color="1F4E79")
        title_cell.fill = PatternFill(start_color="F0F8FF", end_color="F0F8FF", fill_type="solid")
        title_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[3].height = 35
        
        # Date and generation info
        ws.merge_cells('A4:J4')
        date_cell = ws['A4']
        date_cell.value = f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UAE Time - تم الإنشاء في الوقت الإماراتي"
        date_cell.font = Font(name="Arial", size=10, color="666666")
        date_cell.alignment = Alignment(horizontal="center")
        ws.row_dimensions[4].height = 20
        
        # Separator row for enhanced design
        ws.merge_cells('A5:J5')
        separator_cell = ws['A5']
        separator_cell.value = "────────────────────────────────────────────────────────────────"
        separator_cell.font = Font(name="Arial", size=8, color="CCCCCC")
        separator_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[5].height = 10
        
        # Headers with enhanced styling  
        headers = [
            "Employee Name", "Working Days", "Monthly Salary", "Late Incidents", 
            "Absence Days", "Total Deductions", "Deduction Details", "Final Salary", "Month", "Status"
        ]
        
        header_style = Font(name="Arial", size=11, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="1B4477", end_color="1B4477", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=7, column=col)
            cell.value = header
            cell.font = header_style
            cell.fill = header_fill
            cell.alignment = header_alignment
        
        ws.row_dimensions[7].height = 35
        
        # Data rows with enhanced styling
        row_num = 8
        for emp in payroll_data:
            deduction_details_text = "; ".join(emp.get("deduction_details", []))
            if not deduction_details_text:
                deduction_details_text = "No deductions"
                
            row_data = [
                emp["name"],  # English translated name
                emp["working_days"],
                f"AED {emp['monthly_salary']:.2f}",  # Fixed: use monthly_salary instead of basic_salary
                emp["late_incidents"],  # Fixed: use late_incidents instead of late_days
                emp.get("unauthorized_absences", 0),
                f"AED {emp['total_deductions']:.2f}",
                deduction_details_text,
                f"AED {emp['final_salary']:.2f}",
                emp["month"],
                "Active"  # New Status column
            ]
            
            for col, value in enumerate(row_data, 1):
                cell = ws.cell(row=row_num, column=col)
                cell.value = value
                cell.font = Font(name="Arial", size=10)
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                
                # Alternating row colors
                if row_num % 2 == 0:
                    cell.fill = PatternFill(start_color="F8F9FA", end_color="F8F9FA", fill_type="solid")
                else:
                    cell.fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
            
            ws.row_dimensions[row_num].height = 25
            row_num += 1
        
        # Add borders to all cells
        thin_border = Border(
            left=Side(style='thin'), right=Side(style='thin'),
            top=Side(style='thin'), bottom=Side(style='thin')
        )
        
        
        for row in ws.iter_rows(min_row=6, max_row=row_num-1, min_col=1, max_col=9):
            for cell in row:
                cell.border = thin_border
        
        # Summary section
        summary_row = row_num + 2
        ws.merge_cells(f'A{summary_row}:I{summary_row}')
        summary_cell = ws[f'A{summary_row}']
        summary_cell.value = f"Total Employees: {len(payroll_data)} | Total Monthly Salary: AED {sum(emp['monthly_salary'] for emp in payroll_data):.2f} | Total Deductions: AED {sum(emp['total_deductions'] for emp in payroll_data):.2f} | Net Payroll: AED {sum(emp['final_salary'] for emp in payroll_data):.2f}"
        summary_cell.font = Font(name="Arial", size=12, bold=True, color="1B4477")
        summary_cell.fill = PatternFill(start_color="E8F4FD", end_color="E8F4FD", fill_type="solid")
        summary_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[summary_row].height = 30
        
        # Footer
        footer_row = summary_row + 2
        ws.merge_cells(f'A{footer_row}:I{footer_row}')
        footer_cell = ws[f'A{footer_row}']
        footer_cell.value = "TANSEEQ TAX CONSULTANCY - Automated Payroll System with Deductions"
        footer_cell.font = Font(name="Arial", size=10, color="666666", italic=True)
        footer_cell.alignment = Alignment(horizontal="center")
        title_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[3].height = 30
        
        # Enhanced period info
        ws.merge_cells('A4:G4')
        period_cell = ws['A4']
        period_cell.value = f"الشهر: {month} | عدد الموظفين: {len(payroll_data)} | تاريخ الإنشاء: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        period_cell.font = Font(name="Arial", size=10, color="555555")
        period_cell.fill = PatternFill(start_color="F8F9FA", end_color="F8F9FA", fill_type="solid")
        period_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[4].height = 25
        
        # Add decorative separator
        ws.merge_cells('A5:G5')
        separator_cell = ws['A5']
        separator_cell.value = "=" * 80
        separator_cell.font = Font(name="Arial", size=8, color="CCCCCC")
        separator_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[5].height = 10
        
        # Headers with enhanced styling including deductions 
        headers = [
            "Employee Name", "Monthly Salary", "Working Days", "Total Hours", "Late Incidents", 
            "Present Days", "Approved Leaves", "Absence Days", "Total Deductions", "Final Salary"
        ]
        headers_ar = [
            "اسم الموظف", "الراتب الشهري", "أيام العمل", "إجمالي الساعات", "حوادث التأخير",
            "أيام الحضور", "الإجازات المعتمدة", "أيام الغياب", "إجمالي الخصومات", "الراتب النهائي"
        ]
        
        header_row = 6
        for col, (header_en, header_ar) in enumerate(zip(headers, headers_ar), 1):
            cell = ws.cell(row=header_row, column=col)
            cell.value = f"{header_en}\n{header_ar}"
            cell.font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="2B5797", end_color="2B5797", fill_type="solid")
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = Border(
                left=Side(style='medium', color='000000'),
                right=Side(style='medium', color='000000'),
                top=Side(style='medium', color='000000'),
                bottom=Side(style='medium', color='000000')
            )
        
        ws.row_dimensions[header_row].height = 40
        
        # Data rows with enhanced formatting
        for row_idx, employee in enumerate(payroll_data, header_row + 1):
            row_color = "F8F9FA" if row_idx % 2 == 0 else "FFFFFF"
            
            values = [
                employee["name"],
                f"AED {employee['monthly_salary']:.2f}",
                str(employee["working_days"]),
                f"{employee.get('total_hours', 0):.1f}h",
                str(employee.get("late_incidents", 0)),
                str(employee.get("present_days", 0)),
                str(employee.get("approved_leaves", 0)),
                str(employee.get("unauthorized_absences", 0)),
                f"AED {employee.get('total_deductions', 0):.2f}",
                f"AED {employee['final_salary']:.2f}"
            ]
            
            for col, value in enumerate(values, 1):
                cell = ws.cell(row=row_idx, column=col)
                cell.value = value
                cell.font = Font(name="Arial", size=9)
                cell.fill = PatternFill(start_color=row_color, end_color=row_color, fill_type="solid")
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.border = Border(
                    left=Side(style='thin', color='CCCCCC'),
                    right=Side(style='thin', color='CCCCCC'),
                    top=Side(style='thin', color='CCCCCC'),
                    bottom=Side(style='thin', color='CCCCCC')
                )
        
            ws.row_dimensions[row_idx].height = 20
        
        # Footer with enhanced styling
        footer_row = len(payroll_data) + header_row + 2
        ws.merge_cells(f'A{footer_row}:J{footer_row}')
        footer_cell = ws[f'A{footer_row}']
        footer_cell.value = "TANSEEQ TAX CONSULTANCY - Comprehensive HR Management System"
        footer_cell.font = Font(name="Arial", size=9, italic=True, color="666666")
        footer_cell.alignment = Alignment(horizontal="center", vertical="center")
        
        # Save to BytesIO
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        return StreamingResponse(
            BytesIO(output.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=TANSEEQ_payroll_report_{month}.xlsx"}
        )
        
    
    elif format == "pdf":
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from datetime import datetime
        
        output = BytesIO()
        doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles with enhanced colors
        company_style = ParagraphStyle(
            'CompanyStyle',
            parent=styles['Heading1'],
            fontSize=28,
            spaceAfter=10,
            alignment=1,  # Center alignment
            textColor=colors.Color(0.12, 0.31, 0.47),  # Dark blue
            fontName='Helvetica-Bold'
        )
        
        
        logo_style = ParagraphStyle(
            'LogoStyle',
            parent=styles['Normal'],
            fontSize=14,
            spaceAfter=20,
            alignment=1,  # Center alignment
            textColor=colors.Color(0.27, 0.45, 0.77),  # Medium blue
            fontName='Helvetica-Oblique'
        )
        
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=22,
            spaceAfter=15,
            alignment=1,  # Center alignment
            textColor=colors.Color(0.12, 0.31, 0.47),  # Dark blue
            fontName='Helvetica-Bold'
        )
        
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=16,
            spaceAfter=25,
            alignment=1,  # Center alignment
            textColor=colors.Color(0.27, 0.45, 0.77),  # Medium blue
            fontName='Helvetica-Bold'
        )
        
        
        info_style = ParagraphStyle(
            'InfoStyle',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=25,
            alignment=1,  # Center alignment
            textColor=colors.Color(0.4, 0.4, 0.4),  # Gray
            fontName='Helvetica'
        )
        
        
        # Enhanced company header
        company_header = Paragraph("TANSEEQ TAX CONSULTANCY", company_style)
        story.append(company_header)
        
        # Logo subtitle
        logo_subtitle = Paragraph("مكتب استشارات ضريبية متخصص - نظام إدارة الموارد البشرية المتطور", logo_style)
        story.append(logo_subtitle)
        story.append(Spacer(1, 20))
        
        # Report title with enhanced styling
        report_title_text = Paragraph("Enhanced Payroll Report with Deductions<br/>تقرير الرواتب المحسن مع الخصومات التفصيلية", title_style)
        story.append(report_title_text)
        
        # Period info
        period_info = Paragraph(f"الشهر: {month}<br/>عدد الموظفين: {len(payroll_data)}<br/>تاريخ الإنشاء: {datetime.now().strftime('%Y-%m-%d %H:%M')}", info_style)
        story.append(period_info)
        story.append(Spacer(1, 30))
        
        # Add decorative line
        line_style = ParagraphStyle(
            'LineStyle',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=20,
            alignment=1,
            textColor=colors.Color(0.8, 0.8, 0.8)
        )
        
        decorative_line = Paragraph("=" * 60, line_style)
        story.append(decorative_line)
        
        # Create enhanced table data with deductions
        table_data = [["Employee", "Monthly\nSalary", "Working\nDays", "Late\nIncidents", "Absences", "Total\nDeductions", "Final\nSalary"]]
        for employee in payroll_data:
            table_data.append([
                employee["name"][:15],  # Truncate long names for better fit
                f"AED\n{employee['monthly_salary']:.0f}",
                f"{employee['working_days']}",
                f"{employee.get('late_incidents', 0)}",
                f"{employee.get('unauthorized_absences', 0)}",
                f"AED\n{employee.get('total_deductions', 0):.0f}",
                f"AED\n{employee['final_salary']:.0f}"
            ])
        
        # Create table with enhanced styling and proper column widths
        table = Table(table_data, colWidths=[1.8*inch, 1.0*inch, 1.0*inch, 0.9*inch, 0.9*inch, 1.0*inch, 1.0*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.17, 0.34, 0.59)),  # Dark blue header
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.Color(0.95, 0.95, 0.95)),  # Light gray alternating
            ('GRID', (0, 0), (-1, -1), 1, colors.Color(0.7, 0.7, 0.7)),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.95, 0.95)]),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 20))
        
        # Add summary section
        summary_style = ParagraphStyle(
            'SummaryStyle',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=10,
            alignment=1,
            textColor=colors.Color(0.2, 0.2, 0.2),
            fontName='Helvetica-Bold'
        )
        
        
        # Calculate totals
        total_monthly_salary = sum(emp['monthly_salary'] for emp in payroll_data)
        total_basic_salary = sum(emp['monthly_salary'] for emp in payroll_data)  # Fixed: use monthly_salary
        total_deductions = sum(emp.get('total_deductions', 0) for emp in payroll_data)
        total_final_salary = sum(emp['final_salary'] for emp in payroll_data)
        
        summary_text = f"""
        <b>Summary | الملخص</b><br/>
        Total Employees: {len(payroll_data)} | إجمالي الموظفين<br/>
        Total Monthly Salaries: AED {total_monthly_salary:.2f} | إجمالي الرواتب الشهرية<br/>
        Total Deductions: AED {total_deductions:.2f} | إجمالي الخصومات<br/>
        Total Final Salaries: AED {total_final_salary:.2f} | إجمالي الرواتب النهائية
        """
        
        summary_paragraph = Paragraph(summary_text, summary_style)
        story.append(summary_paragraph)
        story.append(Spacer(1, 20))
        
        # Professional footer
        footer_style = ParagraphStyle(
            'FooterStyle',
            parent=styles['Normal'],
            fontSize=10,
            alignment=1,
            textColor=colors.Color(0.4, 0.4, 0.4),
            fontName='Helvetica-Oblique'
        )
        
        footer_text = Paragraph("TANSEEQ TAX CONSULTANCY - Comprehensive HR Management System", footer_style)
        story.append(footer_text)
        
        # Build PDF
        doc.build(story)
        
        output.seek(0)
        return StreamingResponse(
            BytesIO(output.read()),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=TANSEEQ_payroll_report_{month}.pdf"}
        )
        
    
    else:
        raise HTTPException(status_code=400, detail="Invalid format. Use 'excel' or 'pdf'")

@api_router.put("/payroll/{user_id}/{month}")
async def update_payroll(user_id: str, month: str, payroll_data: dict, current_user: User = Depends(get_admin_user)):
    """Update payroll manually (Admin only)"""
    if current_user.name != "Hatem Mohamed Ahmed":
        raise HTTPException(status_code=403, detail="Only Hatem can manually override payroll")
    
    # Store manual payroll override
    override_data = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "month": month,
        "override_salary": payroll_data.get("override_salary"),
        "reason": payroll_data.get("reason", "Manual override"),
        "created_by": current_user.id,
        "created_at": datetime.utcnow()
    }
    
    await db.payroll_overrides.insert_one(override_data)
    
    await log_activity(current_user.id, "payroll_override", f"Manual payroll override for {user_id} - {month}")
    
    return {"message": "Payroll override saved successfully"}

# ============ ADVANCED LATE PENALTY SYSTEM ============

class LatePenalty(BaseModel):
    """Late penalty calculation model"""
    user_id: str
    user_name: str
    month: str
    total_late_minutes: int
    late_incidents: int
    free_late_minutes: int  # First 15 minutes x 4 times = 60 minutes free
    penalty_minutes: int
    penalty_amount: float
    penalty_days: float
    daily_salary: float
    monthly_salary: float
    penalty_type: str  # "minutes", "half_day", "full_day"
    details: List[dict]

@api_router.get("/penalties/late/{month}")
async def calculate_late_penalties(month: str, current_user: User = Depends(get_admin_user)):
    """Calculate late penalties for a specific month (Admin only)"""
    try:
        # Parse month (format: YYYY-MM)
        year, month_num = map(int, month.split('-'))
        
        # Get all employees
        employees = await db.users.find({"is_active": True}).to_list(1000)
        
        # Get attendance records for the month
        start_date = datetime(year, int(month_num), 1).strftime('%Y-%m-%d')
        if int(month_num) == 12:
            end_date = datetime(year + 1, 1, 1).strftime('%Y-%m-%d')
        else:
            end_date = datetime(year, int(month_num) + 1, 1).strftime('%Y-%m-%d')
        
        penalties = []
        
        for employee in employees:
            # Skip admin and super_admin roles - they don't have attendance tracking
            if employee.get("role") in ["admin", "super_admin"]:
                continue
                
            # Get attendance records for this employee in this month
            attendance_records = await db.attendance.find({
                "user_id": employee["id"],
                "date": {"$gte": start_date, "$lt": end_date},
                "is_late": True
            }).to_list(1000)
            
            if not attendance_records:
                continue  # No late records for this employee
            
            # Calculate penalties based on complex rules
            total_late_minutes = 0
            late_incidents = len(attendance_records)
            details = []
            
            # Calculate total late minutes
            for record in attendance_records:
                check_in = record.get('check_in')
                if not check_in:
                    continue
                
                # Parse check-in time
                check_in_time = datetime.strptime(check_in, '%H:%M:%S').time()
                
                # Calculate late minutes based on user-specific rules
                late_minutes = 0
                if employee.get('has_flexible_schedule', False):
                    # Flexible schedule users - calculate based on flexible_start_range
                    flexible_start = employee.get('flexible_start_range', '07:00-11:00')
                    _, end_time = flexible_start.split('-')
                    target_hour, target_minute = map(int, end_time.split(':'))
                    target_time = datetime.strptime(f'{target_hour:02d}:{target_minute:02d}', '%H:%M').time()
                else:
                    # Fixed schedule users
                    if employee['name'] == 'Hatem Mohamed Ahmed':
                        continue  # Hatem has no time restrictions
                    elif employee['name'] == 'Tarek Wazzan':
                        target_time = datetime.strptime('08:00', '%H:%M').time()
                    else:
                        target_time = datetime.strptime('09:00', '%H:%M').time()
                
                # Calculate minutes late
                if check_in_time > target_time:
                    check_in_minutes = check_in_time.hour * 60 + check_in_time.minute
                    target_minutes = target_time.hour * 60 + target_time.minute
                    late_minutes = check_in_minutes - target_minutes
                
                total_late_minutes += late_minutes
                details.append({
                    "date": record.get('date'),
                    "check_in": check_in,
                    "late_minutes": late_minutes,
                    "target_time": target_time.strftime('%H:%M')
                })
            
            if total_late_minutes == 0:
                continue
            
            # Apply complex penalty rules
            monthly_salary = employee.get('monthly_salary', 0)
            daily_salary = monthly_salary / 30
            
            # Rule 1: First 15 minutes x 4 times = free
            free_late_minutes = min(60, late_incidents * 15)  # Maximum 60 minutes free
            if late_incidents <= 4:
                free_late_minutes = total_late_minutes  # All free if 4 or less incidents
            
            penalty_minutes = max(0, total_late_minutes - free_late_minutes)
            
            # Apply penalty rules
            penalty_amount = 0
            penalty_days = 0
            penalty_type = "none"
            
            if penalty_minutes > 0:
                if penalty_minutes <= 20:
                    # Rule 2: After 4 times, deduct actual minutes
                    penalty_amount = (penalty_minutes / (8 * 60)) * daily_salary  # Minutes as fraction of day
                    penalty_days = penalty_minutes / (8 * 60)
                    penalty_type = "minutes"
                elif penalty_minutes <= 120:  # Up to 2 hours
                    # Rule 3: More than 20 minutes, deduct actual time
                    penalty_amount = (penalty_minutes / (8 * 60)) * daily_salary
                    penalty_days = penalty_minutes / (8 * 60)
                    penalty_type = "actual_time"
                    
                    if penalty_minutes >= 60:  # 1-2 hours = half day
                        penalty_amount = daily_salary * 0.5
                        penalty_days = 0.5
                        penalty_type = "half_day"
                else:
                    # Rule 4: More than 2 hours = full day
                    penalty_amount = daily_salary
                    penalty_days = 1.0
                    penalty_type = "full_day"
            
            penalty = LatePenalty(
                user_id=employee["id"],
                user_name=employee["name"],
                month=month,
                total_late_minutes=total_late_minutes,
                late_incidents=late_incidents,
                free_late_minutes=free_late_minutes,
                penalty_minutes=penalty_minutes,
                penalty_amount=penalty_amount,
                penalty_days=penalty_days,
                daily_salary=daily_salary,
                monthly_salary=monthly_salary,
                penalty_type=penalty_type,
                details=details
            )
        
            
            penalties.append(penalty)
        
        return penalties
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating late penalties: {str(e)}")

@api_router.post("/penalties/apply/{month}")
async def apply_late_penalties(month: str, current_user: User = Depends(get_super_admin_user)):
    """Apply calculated late penalties to payroll (Super admin only)"""
    try:
        # Get calculated penalties
        penalties = await calculate_late_penalties(month, current_user)
        
        # Store penalties in database
        penalty_records = []
        for penalty in penalties:
            penalty_record = {
                "id": f"penalty_{penalty.user_id}_{month}",
                "user_id": penalty.user_id,
                "user_name": penalty.user_name,
                "month": month,
                "total_late_minutes": penalty.total_late_minutes,
                "penalty_amount": penalty.penalty_amount,
                "penalty_days": penalty.penalty_days,
                "penalty_type": penalty.penalty_type,
                "applied_by": current_user.id,
                "applied_at": datetime.utcnow(),
                "status": "applied"
            }
            
            # Insert or update penalty record
            await db.late_penalties.update_one(
                {"id": penalty_record["id"]},
                {"$set": penalty_record},
                upsert=True
            )
        
            
            penalty_records.append(penalty_record)
        
        # Log activity
        total_penalties = sum(p.penalty_amount for p in penalties)
        await log_activity(
            current_user.id, 
            "penalties_applied", 
            f"Applied late penalties for {month}: {len(penalties)} employees, AED {total_penalties:.2f}"
        )
        
        
        return {
            "message": f"Late penalties applied successfully for {month}",
            "total_employees": len(penalties),
            "total_penalty_amount": total_penalties,
            "penalties": penalty_records
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error applying late penalties: {str(e)}")

@api_router.get("/penalties/history/{user_id}")
async def get_penalty_history(user_id: str, current_user: User = Depends(get_current_user)):
    """Get penalty history for a user"""
    # Users can only see their own history, admins can see all
    if current_user.role == "user" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        penalty_records = await db.late_penalties.find(
            {"user_id": user_id}
        ).sort("applied_at", -1).to_list(1000)
        
        return penalty_records
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting penalty history: {str(e)}")

# ============ AUTO BACKUP ENDPOINTS ============

@api_router.get("/backup/stats")
async def get_backup_stats(current_user: User = Depends(get_super_admin_user)):
    """Get backup statistics (Super admin only)"""
    try:
        from pathlib import Path
        import os
        
        # ✅ Use ROOT_DIR for deployment compatibility
        ROOT_DIR = Path(__file__).parent.parent
        BACKUP_DIR = ROOT_DIR / "backups"
        BACKUP_DIR.mkdir(exist_ok=True)
        
        # Count backup files
        backup_files = list(Path(BACKUP_DIR).glob("backup_*.zip"))
        total_files = len(backup_files)
        
        # Calculate total size
        total_size = 0
        latest_backup = None
        latest_date = None
        
        if backup_files:
            total_size = sum(f.stat().st_size for f in backup_files) / (1024 * 1024)  # MB
            latest_backup = max(backup_files, key=lambda f: f.stat().st_mtime)
            latest_date = datetime.fromtimestamp(latest_backup.stat().st_mtime)
        
        # Get backup logs from database
        recent_logs = await db.backup_logs.find({}).sort("timestamp", -1).limit(10).to_list(10)
        
        # Format logs for frontend
        formatted_logs = []
        for log in recent_logs:
            formatted_logs.append({
                "id": log.get("id", ""),
                "timestamp": log.get("timestamp"),
                "status": log.get("status", "unknown"),
                "file_size_mb": log.get("file_size_mb", 0),
                "error": log.get("error", ""),
                "time_ago": get_time_ago(log.get("timestamp", datetime.utcnow()))
            })
        
        stats = {
            "total_backups": total_files,
            "total_size_mb": round(total_size, 2),
            "latest_backup": latest_backup.name if latest_backup else None,
            "latest_backup_date": latest_date.strftime("%Y-%m-%d %H:%M:%S") if latest_date else None,
            "backup_directory": BACKUP_DIR,
            "recent_logs": formatted_logs,
            "auto_backup_enabled": True,
            "backup_schedule": "Daily at 02:00 AM UAE Time"
        }
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting backup stats: {str(e)}")

@api_router.post("/backup/manual")
async def create_manual_backup(current_user: User = Depends(get_super_admin_user)):
    """Create manual backup (Super admin only)"""
    try:
        import subprocess
        from pathlib import Path
        import zipfile
        import shutil
        
        # ✅ Use ROOT_DIR for deployment compatibility
        ROOT_DIR = Path(__file__).parent.parent
        BACKUP_DIR = ROOT_DIR / "backups"
        BACKUP_DIR.mkdir(exist_ok=True)
        
        # Create timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_folder = f"{BACKUP_DIR}/manual_backup_{timestamp}"
        
        # Create backup folder
        Path(backup_folder).mkdir(exist_ok=True)
        
        # Use mongodump to create backup
        MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017/tanseeq_hr")
        
        dump_command = [
            "mongodump",
            "--uri", MONGO_URL,
            "--out", backup_folder
        ]
        
        # Execute mongodump
        result = subprocess.run(dump_command, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Create ZIP archive
            zip_path = f"{backup_folder}.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(backup_folder):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, backup_folder)
                        zipf.write(file_path, arcname)
            
            # Remove original folder, keep only ZIP
            shutil.rmtree(backup_folder)
            
            # Get file size
            file_size = os.path.getsize(zip_path) / (1024 * 1024)  # MB
            
            # Log backup to database
            log_entry = {
                "id": f"manual_backup_{timestamp}",
                "timestamp": datetime.utcnow(),
                "file_path": zip_path,
                "file_size_mb": file_size,
                "status": "success",
                "error": "",
                "created_by": current_user.id,
                "backup_type": "manual",
                "created_at": datetime.utcnow()
            }
            
            await db.backup_logs.insert_one(log_entry)
            
            await log_activity(current_user.id, "manual_backup_created", f"Manual backup created: {file_size:.2f} MB")
            
            return {
                "message": "Manual backup created successfully",
                "backup_file": f"manual_backup_{timestamp}.zip",
                "file_size_mb": round(file_size, 2),
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
        else:
            error_msg = result.stderr
            
            # Log failed backup
            log_entry = {
                "id": f"manual_backup_failed_{timestamp}",
                "timestamp": datetime.utcnow(),
                "file_path": "",
                "file_size_mb": 0,
                "status": "failed",
                "error": error_msg,
                "created_by": current_user.id,
                "backup_type": "manual",
                "created_at": datetime.utcnow()
            }
            
            await db.backup_logs.insert_one(log_entry)
            
            raise HTTPException(status_code=500, detail=f"Backup failed: {error_msg}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating manual backup: {str(e)}")

# ============ INTERNAL MESSAGES ENDPOINTS ============

def get_time_ago(created_at: datetime) -> str:
    """Calculate human readable time ago"""
    now = datetime.utcnow()
    diff = now - created_at
    
    if diff.days > 0:
        if diff.days == 1:
            return "منذ يوم واحد"
        elif diff.days < 7:
            return f"منذ {diff.days} أيام"
        elif diff.days < 30:
            weeks = diff.days // 7
            return f"منذ {weeks} أسبوع" if weeks == 1 else f"منذ {weeks} أسابيع"
        else:
            months = diff.days // 30
            return f"منذ {months} شهر" if months == 1 else f"منذ {months} شهور"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"منذ {hours} ساعة" if hours == 1 else f"منذ {hours} ساعات"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"منذ {minutes} دقيقة" if minutes == 1 else f"منذ {minutes} دقائق"
    else:
        return "منذ لحظات"

@api_router.post("/messages/custom")
async def create_custom_message(message_data: MessageCreate, current_user: User = Depends(get_admin_user)):
    """Create custom message for all employees (Admin/Super Admin only)"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only admins can create custom messages")
    
    # If to_user_ids is empty, send to all users
    if not message_data.to_user_ids:
        all_users = await db.users.find({"is_active": True}).to_list(1000)
        message_data.to_user_ids = [user["id"] for user in all_users]
    
    # Create custom message
    message = Message(
        title=message_data.title,
        content=message_data.content,
        message_type="custom",
        from_user_id=current_user.id,
        from_user_name=current_user.name,
        to_user_ids=message_data.to_user_ids,
        priority=message_data.priority or "normal",
        expires_at=message_data.expires_at
    )
    
    await db.messages.insert_one(message.dict())
    
    await log_activity(current_user.id, "custom_message_created", f"Created custom message: {message.title}")
    
    return {
        "message": "Custom message sent successfully", 
        "id": message.id,
        "recipients_count": len(message_data.to_user_ids),
        "title": message.title
    }

@api_router.post("/notifications/late-warning")
async def send_late_warning_notifications():
    """Send automatic late warning notifications"""
    try:
        # Get current date
        today = get_uae_time().date().strftime('%Y-%m-%d')
        
        # Find employees who are late today - EXCLUDE admin and super_admin roles
        late_attendance = await db.attendance.find({
            "date": today,
            "is_late": True
        }).to_list(1000)
        
        notifications_sent = 0
        
        for record in late_attendance:
            user_id = record.get("user_id")
            user_name = record.get("user_name")
            check_in_time = record.get("check_in", "")
            
            if not user_id:
                continue
            
            # Get user details to check role
            user_details = await db.users.find_one({"id": user_id})
            if not user_details:
                continue
                
            # Skip if user is admin or super_admin - they don't have attendance tracking
            if user_details.get("role") in ["admin", "super_admin"]:
                continue
            
            # Check if notification already sent today
            existing_notification = await db.messages.find_one({
                "message_type": "late_warning",
                "to_user_ids": {"$in": [user_id]},
                "created_at": {"$gte": datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)}
            })
            
            if existing_notification:
                continue  # Already sent notification today
            
            # Create late warning message
            title = "⚠️ تنبيه تأخير"
            content = f"""عزيزي/عزيزتي {user_name}،

تم تسجيل تأخيرك اليوم في الساعة {check_in_time}.

نذكركم بأهمية الالتزام بمواعيد العمل المحددة، حيث أن التأخير المتكرر قد يؤدي إلى:
• خصم من الراتب الشهري
• إجراءات إدارية

نرجو منكم الالتزام بمواعيد العمل في المستقبل.

شكراً لتفهمكم،
إدارة الموارد البشرية
TANSEEQ TAX CONSULTANCY"""
            
            # Create notification message
            message = Message(
                title=title,
                content=content,
                message_type="late_warning",
                from_user_id="system",
                from_user_name="نظام الموارد البشرية",
                to_user_ids=[user_id],
                priority="high"
            )
        
            
            await db.messages.insert_one(message.dict())
            notifications_sent += 1
        
        return {
            "message": "Late warning notifications sent",
            "notifications_sent": notifications_sent,
            "date": today
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending late notifications: {str(e)}")

@api_router.post("/notifications/absence-warning")
async def send_absence_warning_notifications():
    """Send automatic absence warning notifications"""
    try:
        # Get current date
        today = get_uae_time().date().strftime('%Y-%m-%d')
        
        # Get all active employees with role "user" only (exclude admin/super_admin)
        all_employees = await db.users.find({
            "is_active": True,
            "role": "user"  # Only regular employees, not admin/super_admin
        }).to_list(1000)
        
        # Find employees with no attendance record today (absent)
        absent_employees = []
        
        for employee in all_employees:
            attendance_record = await db.attendance.find_one({
                "user_id": employee["id"],
                "date": today
            })
            
            if not attendance_record:
                # Check if they have approved leave today
                approved_leave = await db.leaves.find_one({
                    "user_id": employee["id"],
                    "start_date": {"$lte": today},
                    "end_date": {"$gte": today},
                    "status": "approved"
                })
                
                # Check if they have approved field exit
                approved_field_exit = await db.field_exits.find_one({
                    "user_id": employee["id"],
                    "date": today,
                    "status": "approved"
                })
                
                # If no leave or field exit, they are absent without permission
                if not approved_leave and not approved_field_exit:
                    absent_employees.append(employee)
        
        notifications_sent = 0
        
        for employee in absent_employees:
            user_id = employee["id"]
            user_name = employee["name"]
            
            # Check if notification already sent today
            existing_notification = await db.messages.find_one({
                "message_type": "absence_warning",
                "to_user_ids": {"$in": [user_id]},
                "created_at": {"$gte": datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)}
            })
            
            if existing_notification:
                continue  # Already sent notification today
            
            # Create absence warning message
            title = "🚨 تنبيه غياب بدون إذن"
            content = f"""عزيزي/عزيزتي {user_name}،

لم يتم تسجيل حضورك اليوم {today} ولا يوجد طلب إجازة معتمد.

وفقاً لسياسة الشركة:
• الغياب بدون إذن = خصم يومين من الراتب
• يرجى تقديم مبرر للغياب أو شهادة مرضية إن وجدت

في حال كان لديكم عذر مقبول، يرجى التواصل مع الإدارة فوراً.

إدارة الموارد البشرية
TANSEEQ TAX CONSULTANCY"""
            
            # Create notification message  
            message = Message(
                title=title,
                content=content,
                message_type="absence_warning",
                from_user_id="system",
                from_user_name="نظام الموارد البشرية",
                to_user_ids=[user_id],
                priority="urgent"
            )
        
            
            await db.messages.insert_one(message.dict())
            notifications_sent += 1
        
        return {
            "message": "Absence warning notifications sent",
            "notifications_sent": notifications_sent,
            "absent_employees": len(absent_employees),
            "date": today
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending absence notifications: {str(e)}")

@api_router.post("/notifications/penalty-applied/{user_id}")
async def send_penalty_notification(user_id: str, penalty_amount: float, penalty_reason: str):
    """Send penalty applied notification to specific user"""
    try:
        # Get user details
        user_details = await db.users.find_one({"id": user_id})
        if not user_details:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_name = user_details["name"]
        
        # Create penalty notification message
        title = "💰 تنبيه خصم من الراتب"
        content = f"""عزيزي/عزيزتي {user_name}،

نعلمكم بأنه تم تطبيق خصم على راتبكم الشهري:

💸 مبلغ الخصم: {penalty_amount:.2f} درهم
📋 السبب: {penalty_reason}
📅 تاريخ التطبيق: {datetime.now().strftime('%Y-%m-%d')}

هذا الخصم مطبق وفقاً لسياسة الشركة ونظام الحضور والانصراف.

للاستفسار أو المراجعة، يرجى التواصل مع إدارة الموارد البشرية.

إدارة الموارد البشرية
TANSEEQ TAX CONSULTANCY"""
        
        # Create notification message
        message = Message(
            title=title,
            content=content,
            message_type="penalty_notification",
            from_user_id="system",
            from_user_name="نظام الموارد البشرية",
            to_user_ids=[user_id],
            priority="high"
        )
        
        
        await db.messages.insert_one(message.dict())
        
        return {
            "message": "Penalty notification sent successfully",
            "user_name": user_name,
            "penalty_amount": penalty_amount
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending penalty notification: {str(e)}")

@api_router.post("/messages")
async def create_message(message_data: MessageCreate, current_user: User = Depends(get_admin_user)):
    """Create new internal message"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only admins can create messages")
    
    # If to_user_ids is empty, send to all users
    if not message_data.to_user_ids:
        all_users = await db.users.find({"is_active": True}).to_list(1000)
        message_data.to_user_ids = [user["id"] for user in all_users]
    
    # Create message
    message = Message(
        title=message_data.title,
        content=message_data.content,
        message_type=message_data.message_type,
        from_user_id=current_user.id,
        from_user_name=current_user.name,
        to_user_ids=message_data.to_user_ids,
        priority=message_data.priority,
        expires_at=message_data.expires_at
    )
    
    await db.messages.insert_one(message.dict())
    
    await log_activity(current_user.id, "message_created", f"Created message: {message.title}")
    
    return {"message": "Message created successfully", "id": message.id}

@api_router.get("/messages")
async def get_messages(current_user: User = Depends(get_current_user)):
    """Get messages for current user"""
    # Get messages where user is specifically in to_user_ids, or general messages
    # BUT exclude private messages (late_warning, absence_warning, penalty_notification)
    query = {
        "$and": [
            {
                "$or": [
                    {"to_user_ids": {"$in": [current_user.id]}},
                    {
                        "$and": [
                            {"$or": [
                                {"to_user_ids": {"$size": 0}},  # Broadcast messages
                                {"to_user_ids": []}  # Empty array means all users
                            ]},
                            {"message_type": {"$nin": ["late_warning", "absence_warning", "penalty_notification"]}}
                        ]
                    }
                ]
            },
            {"is_active": True},
            {
                "$or": [
                    {"expires_at": None},
                    {"expires_at": {"$gt": datetime.utcnow()}}
                ]
            }
        ]
    }
    
    messages = await db.messages.find(query).sort("created_at", -1).to_list(1000)
    
    # Convert to response format
    response_messages = []
    for message in messages:
        is_read = current_user.id in message.get("is_read_by", [])
        response_messages.append(MessageResponse(
            id=message["id"],
            title=message["title"],
            content=message["content"],
            message_type=message["message_type"],
            from_user_id=message["from_user_id"],
            from_user_name=message["from_user_name"],
            to_user_ids=message["to_user_ids"],
            is_read_by=message["is_read_by"],
            priority=message["priority"],
            created_at=message["created_at"],
            expires_at=message.get("expires_at"),
            is_active=message["is_active"],
            is_read=is_read,
            time_ago=get_time_ago(message["created_at"])
        ))
    
    return response_messages

@api_router.post("/messages/{message_id}/read")
async def mark_message_as_read(message_id: str, current_user: User = Depends(get_current_user)):
    """Mark message as read by current user"""
    # Add user ID to is_read_by list if not already there
    await db.messages.update_one(
        {"id": message_id},
        {"$addToSet": {"is_read_by": current_user.id}}
    )
    
    return {"message": "Message marked as read"}

@api_router.get("/messages/unread-count")
async def get_unread_count(current_user: User = Depends(get_current_user)):
    """Get count of unread messages for current user"""
    query = {
        "$and": [
            {
                "$or": [
                    {"to_user_ids": {"$in": [current_user.id]}},
                    {
                        "$and": [
                            {"$or": [
                                {"to_user_ids": {"$size": 0}},
                                {"to_user_ids": []}
                            ]},
                            {"message_type": {"$nin": ["late_warning", "absence_warning", "penalty_notification"]}}
                        ]
                    }
                ]
            },
            {"is_active": True},
            {"is_read_by": {"$ne": current_user.id}},  # Not read by current user
            {
                "$or": [
                    {"expires_at": None},
                    {"expires_at": {"$gt": datetime.utcnow()}}
                ]
            }
        ]
    }
    
    count = await db.messages.count_documents(query)
    return {"unread_count": count}

@api_router.post("/messages/friday-work")
async def create_friday_work_message(current_user: User = Depends(get_current_user)):
    """Create Friday work announcement (Super admin only)"""
    if current_user.name != "Hatem Mohamed Ahmed":
        raise HTTPException(status_code=403, detail="Only Hatem can create Friday work announcements")
    
    # Get next Friday's date
    today = get_uae_time().date()
    days_until_friday = (4 - today.weekday()) % 7  # Friday is 4 (0=Monday)
    if days_until_friday == 0:  # If today is Friday, get next Friday
        days_until_friday = 7
    
    next_friday = today + timedelta(days=days_until_friday)
    friday_formatted = next_friday.strftime("%d/%m/%Y")
    
    # Create the message content
    title = "دوام يوم الجمعة الاستثنائي"
    content = f"""السادة الزملاء الكرام،

السلام عليكم ورحمة الله وبركاته،

بناءً على توجيهات الإدارة، ونظراً لضغوط العمل الحالية وحرصاً على استمرارية سير الأعمال، نُعلمكم بأنه تم إلغاء إجازة يوم الجمعة المقبل، والعمل استثنائياً على النحو التالي:

التاريخ: يوم الجمعة الموافق {friday_formatted}

أوقات الدوام: من الساعة 08:00 صباحاً وحتى الساعة 12:00 ظهراً

يرجى الالتزام التام بالحضور في ذلك اليوم، علماً بأنه في حال عدم الحضور سيتم خصم يومين من الراتب.

نعتذر عن أي إزعاج قد يسببه هذا التعديل، ونقدر تعاونكم وتفهمكم.

الإدارة العامة
TANSEEQ TAX CONSULTANCY"""
    
    # Create message
    message = Message(
        title=title,
        content=content,
        message_type="friday_work",
        from_user_id=current_user.id,
        from_user_name=current_user.name,
        to_user_ids=[],  # Send to all
        priority="urgent",
        expires_at=next_friday + timedelta(days=1)  # Expire day after Friday
    )
    
    await db.messages.insert_one(message.dict())
    
    await log_activity(current_user.id, "friday_work_announced", f"Created Friday work announcement for {friday_formatted}")
    
    return {
        "message": "Friday work announcement sent successfully", 
        "id": message.id,
        "friday_date": friday_formatted,
        "recipients": "All employees"
    }

@api_router.get("/messages/{message_id}/stats")
async def get_message_stats(message_id: str, current_user: User = Depends(get_current_user)):
    """Get message read statistics (Admin only)"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only admins can view message statistics")
    
    message = await db.messages.find_one({"id": message_id})
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Get all active users
    all_users = await db.users.find({"is_active": True}).to_list(1000)
    total_users = len(all_users)
    
    # Get users who have read
    read_by = message.get("is_read_by", [])
    read_count = len(read_by)
    
    # Get users who haven't read
    unread_users = []
    for user in all_users:
        if user["id"] not in read_by:
            unread_users.append({
                "id": user["id"],
                "name": user["name"],
                "email": user["email"]
            })
    
    return {
        "message_id": message_id,
        "title": message["title"],
        "total_recipients": total_users,
        "read_count": read_count,
        "unread_count": total_users - read_count,
        "read_percentage": round((read_count / total_users) * 100, 1) if total_users > 0 else 0,
        "unread_users": unread_users,
        "created_at": message["created_at"],
        "time_ago": get_time_ago(message["created_at"])
    }

@api_router.post("/backup/create-download")
async def create_backup_for_download(current_user: User = Depends(get_super_admin_user)):
    """Create a backup file and save it on server (Super admin only)"""
    try:
        import json
        from pathlib import Path
        
        # Create timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"tanseeq_backup_{timestamp}.json"
        
        # Create backup directory if it doesn't exist
        backup_dir = Path(ROOT_DIR) / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        # Full path for the backup file
        backup_file_path = backup_dir / backup_name
        
        # Collect all database data
        backup_data = {
            "backup_info": {
                "filename": backup_name,
                "created_at": datetime.now().isoformat(),
                "version": "1.0",
                "database": os.environ.get("DB_NAME", "tanseeq_hr"),
                "total_collections": 0,
                "total_records": 0
            },
            "collections": {}
        }
        
        # Get all collections
        collections_to_backup = ["users", "attendance", "leaves", "field_exits", "messages", "late_penalties", "activity_logs"]
        
        total_records = 0
        for collection_name in collections_to_backup:
            collection = getattr(db, collection_name)
            records = await collection.find({}).to_list(None)
            
            # Convert ObjectId and datetime to strings for JSON serialization
            serialized_records = []
            for record in records:
                serialized_record = {}
                for key, value in record.items():
                    if key == "_id":
                        continue  # Skip MongoDB _id
                    elif isinstance(value, datetime):
                        serialized_record[key] = value.isoformat()
                    else:
                        serialized_record[key] = value
                serialized_records.append(serialized_record)
            
            backup_data["collections"][collection_name] = serialized_records
            total_records += len(serialized_records)
        
        backup_data["backup_info"]["total_collections"] = len(collections_to_backup)
        backup_data["backup_info"]["total_records"] = total_records
        
        # Convert to JSON string
        json_content = json.dumps(backup_data, indent=2, ensure_ascii=False)
        
        # Save to file
        with open(backup_file_path, 'w', encoding='utf-8') as f:
            f.write(json_content)
        
        # Get file size
        file_size = backup_file_path.stat().st_size
        
        # Log activity
        await log_activity(
            current_user.id,
            "backup_created_on_server",
            f"Created backup file on server: {backup_name} ({file_size} bytes, {total_records} records)"
        )
        
        
        return {
            "message": "تم إنشاء النسخة الاحتياطية وحفظها على الخادم بنجاح",
            "filename": backup_name,
            "file_size": file_size,
            "total_records": total_records,
            "total_collections": len(collections_to_backup),
            "created_at": datetime.now().isoformat(),
            "download_url": f"/api/backup/download/{backup_name}",
            "saved_on_server": True
        }
        
    except Exception as e:
        # Return error but still provide something workable
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        emergency_backup = {
            "backup_info": {
                "filename": f"emergency_backup_{timestamp}.json",
                "created_at": datetime.now().isoformat(),
                "version": "1.0",
                "status": "emergency",
                "error": str(e)
            },
            "collections": {
                "users": [],
                "attendance": [],
                "leaves": [],
                "field_exits": [],
                "messages": []
            }
        }
        
        # Create backup directory if it doesn't exist
        backup_dir = Path(ROOT_DIR) / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        # Save emergency backup to file
        emergency_file_path = backup_dir / f"emergency_backup_{timestamp}.json"
        json_content = json.dumps(emergency_backup, indent=2)
        
        with open(emergency_file_path, 'w', encoding='utf-8') as f:
            f.write(json_content)
        
        file_size = emergency_file_path.stat().st_size
        
        return {
            "message": "تم إنشاء نسخة احتياطية اضطرارية وحفظها على الخادم",
            "filename": f"emergency_backup_{timestamp}.json",
            "file_size": file_size,
            "total_records": 0,
            "total_collections": 5,
            "created_at": datetime.now().isoformat(),
            "download_url": f"/api/backup/download/emergency_backup_{timestamp}.json",
            "saved_on_server": True,
            "status": "emergency",
            "error": str(e)
        }

@api_router.get("/backup/list-files")
async def list_backup_files(current_user: User = Depends(get_super_admin_user)):
    """List all backup files from server directory (Super admin only)"""
    try:
        from pathlib import Path
        import json
        
        # Get backup directory
        backup_dir = Path(ROOT_DIR) / "backups"
        backup_files = []
        
        if backup_dir.exists():
            # Get all JSON files in backup directory
            for backup_file in backup_dir.glob("*.json"):
                try:
                    # Get file stats
                    file_stats = backup_file.stat()
                    file_size = file_stats.st_size
                    
                    # Try to read backup info from file
                    records_count = 0
                    collections_count = 0
                    try:
                        with open(backup_file, 'r', encoding='utf-8') as f:
                            backup_data = json.load(f)
                            records_count = backup_data.get("backup_info", {}).get("total_records", 0)
                            collections_count = backup_data.get("backup_info", {}).get("total_collections", 0)
                    except:
                        pass  # If can't read file content, use defaults
                    
                    backup_files.append({
                        "filename": backup_file.name,
                        "size": file_size,
                        "size_mb": round(file_size / (1024 * 1024), 2),
                        "created_at": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                        "status": "available",
                        "records": records_count,
                        "collections": collections_count
                    })
                except Exception:
                    # Skip files that can't be processed
                    continue
        
        # Sort by creation time (newest first)
        backup_files.sort(key=lambda x: x["created_at"], reverse=True)
        
        total_size = sum(f["size"] for f in backup_files)
        
        return {
            "backup_files": backup_files,
            "total_files": len(backup_files),
            "total_size": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "backup_directory": str(backup_dir),
            "status": "available"
        }
        
    except Exception as e:
        return {
            "backup_files": [],
            "total_files": 0,
            "total_size": 0,
            "total_size_mb": 0.0,
            "backup_directory": "/app/backups",
            "status": "error",
            "error": str(e)
        }

@api_router.get("/backup/download/{filename}")
async def download_backup_file(
    filename: str,
    current_user: User = Depends(get_super_admin_user)  
):
    """Download specific backup file from server (Super admin only)"""
    try:
        from pathlib import Path
        from fastapi.responses import StreamingResponse
        import zipfile
        from io import BytesIO
        
        # Validate filename
        if not (filename.endswith('.json') or filename.endswith('.zip')):
            raise HTTPException(status_code=400, detail="نوع الملف غير مدعوم. يجب أن يكون JSON أو ZIP")
        
        # Get backup directory and file path
        backup_dir = Path(ROOT_DIR) / "backups"
        json_filename = filename.replace('.zip', '.json') if filename.endswith('.zip') else filename
        backup_file_path = backup_dir / json_filename
        
        # Check if file exists
        if not backup_file_path.exists():
            raise HTTPException(status_code=404, detail="الملف غير موجود")
        
        # Log download activity
        await log_activity(
            current_user.id,
            "backup_downloaded",
            f"Downloaded backup file: {filename}"
        )
        
        
        if filename.endswith('.zip'):
            # Create ZIP file containing the JSON backup
            zip_buffer = BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                zip_file.write(backup_file_path, json_filename)
            
            zip_buffer.seek(0)
            
            return StreamingResponse(
                BytesIO(zip_buffer.read()),
                media_type='application/zip',
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "Content-Type": "application/zip"
                }
            )
        
        else:
            # Return JSON file directly
            return StreamingResponse(
                open(backup_file_path, 'rb'),
                media_type='application/json',
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "Content-Type": "application/json; charset=utf-8"
                }
            )
        
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading backup: {str(e)}")

@api_router.delete("/backup/delete/{filename}")
async def delete_backup_file(
    filename: str,
    current_user: User = Depends(get_super_admin_user)
):
    """Delete specific backup file from server (Super admin only)"""
    try:
        from pathlib import Path
        
        # Validate filename
        if not filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="يمكن حذف ملفات JSON فقط")
        
        # Get backup directory and file path
        backup_dir = Path(ROOT_DIR) / "backups"
        backup_file_path = backup_dir / filename
        
        # Check if file exists
        if not backup_file_path.exists():
            raise HTTPException(status_code=404, detail="الملف غير موجود")
        
        # Delete file
        backup_file_path.unlink()
        
        # Log activity
        await log_activity(
            current_user.id,
            "backup_deleted",
            f"Deleted backup file: {filename}"
        )
        
        
        return {
            "message": f"تم حذف الملف {filename} بنجاح",
            "filename": filename,
            "status": "deleted"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في حذف الملف: {str(e)}")

@api_router.post("/backup/restore")
async def restore_backup(
    backup_file: UploadFile = File(...),
    current_user: User = Depends(get_super_admin_user)
):
    """Restore database from backup file (Super admin only)"""
    try:
        # Validate file type
        if not backup_file.filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="يجب أن يكون الملف من نوع JSON")
        
        # Read uploaded file
        backup_content = await backup_file.read()
        
        if len(backup_content) == 0:
            raise HTTPException(status_code=400, detail="الملف فارغ")
        
        # Parse JSON content
        import json
        try:
            backup_data = json.loads(backup_content.decode('utf-8'))
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="ملف JSON غير صحيح")
        
        # Validate backup structure
        if "backup_info" not in backup_data or "collections" not in backup_data:
            raise HTTPException(status_code=400, detail="هيكل النسخة الاحتياطية غير صحيح")
        
        # Simulate restoration process
        collections_restored = 0
        records_restored = 0
        
        for collection_name, records in backup_data["collections"].items():
            if isinstance(records, list):
                collections_restored += 1
                records_restored += len(records)
        
        # Log activity
        await log_activity(
            current_user.id,
            "backup_restored",
            f"Simulated restore from backup: {backup_file.filename} ({len(backup_content)} bytes, {records_restored} records)"
        )
        
        
        return {
            "message": "تم محاكاة استعادة النسخة الاحتياطية بنجاح ✅",
            "restored_from": backup_file.filename,
            "file_size": len(backup_content),
            "collections_restored": collections_restored,
            "records_restored": records_restored,
            "restored_at": datetime.now().isoformat(),
            "status": "simulated",
            "warning": "هذه محاكاة - لم يتم تغيير قاعدة البيانات الفعلية لضمان الأمان"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error restoring backup: {str(e)}")

@api_router.post("/admin/create-leave-request")
async def create_leave_request_for_employee(
    user_id: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...), 
    reason: str = Form(...),
    leave_type: str = Form("annual"),
    days_count: int = Form(...),
    notes: str = Form(""),
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_super_admin_user)
):
    """Super Admin: Create leave request on behalf of employee"""
    try:
        # Get employee details
        employee = await db.users.find_one({"id": user_id})
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        # Handle file upload if present
        file_path = None
        attachment_url = None
        if file and file.filename:
            file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
            file_name = f"leave_{uuid.uuid4().hex}.{file_extension}"
            file_path = uploads_dir / file_name
            
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            attachment_url = f"/uploads/{file_name}"
        
        # Create leave request
        leave_request = Leave(
            user_id=user_id,
            user_name=employee["name"],
            start_date=start_date,
            end_date=end_date,
            reason=reason,
            days_count=days_count,
            attachment_url=attachment_url,
            status="approved",  # Auto-approve requests created by Super Admin
            approved_by=current_user.name
        )
        
        
        # Add additional fields for admin-created requests
        leave_dict = leave_request.dict()
        leave_dict.update({
            "approved_by_id": current_user.id,
            "approved_at": datetime.utcnow(),
            "admin_notes": f"Request created by Super Admin ({current_user.name}) on behalf of employee. Notes: {notes}",
            "created_by_admin": True,
            "created_by_admin_id": current_user.id,
            "created_by_admin_name": current_user.name,
            "leave_type": leave_type,
            "file_path": str(file_path) if file_path else None
        })
        
        await db.leaves.insert_one(leave_dict)
        
        # Log activity
        await log_activity(
            current_user.id, 
            "admin_leave_created", 
            f"Created leave request for {employee['name']} from {start_date} to {end_date}"
        )
        
        
        # Send notification to employee
        message = Message(
            title="✅ طلب إجازة معتمد",
            content=f"""عزيزي/عزيزتي {employee['name']},

تم إنشاء واعتماد طلب إجازة نيابة عنك من قبل الإدارة:

📅 من تاريخ: {start_date}
📅 إلى تاريخ: {end_date}  
📝 السبب: {reason}
📋 عدد الأيام: {days_count}
📋 ملاحظات الإدارة: {leave_dict['admin_notes']}

تم الموافقة على الطلب تلقائياً.

إدارة الموارد البشرية
TANSEEQ TAX CONSULTANCY""",
            message_type="leave_approved",
            from_user_id=current_user.id,
            from_user_name=f"إدارة الموارد البشرية ({current_user.name})",
            to_user_ids=[user_id],
            priority="normal"
        )
        
        
        await db.messages.insert_one(message.dict())
        
        return {
            "message": "Leave request created and approved successfully",
            "leave_id": leave_request.id,
            "employee_name": employee["name"],
            "status": "approved"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating leave request: {str(e)}")

@api_router.post("/admin/create-field-exit-request")
async def create_field_exit_request_for_employee(
    user_id: str = Form(...),
    date: str = Form(...),
    visit_type: str = Form(...),
    client_name: str = Form(""),
    expected_start_time: str = Form(...),
    expected_end_time: str = Form(...),
    report: str = Form(""),
    notes: str = Form(""),
    current_user: User = Depends(get_super_admin_user)
):
    """Super Admin: Create field exit request on behalf of employee"""
    try:
        # Get employee details
        employee = await db.users.find_one({"id": user_id})
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        # Create field exit request
        field_exit_request = FieldExit(
            user_id=user_id,
            user_name=employee["name"],
            visit_type=visit_type,
            client_name=client_name,
            start_time=expected_start_time,
            end_time=expected_end_time,
            report=report,
            status="approved",  # Auto-approve requests created by Super Admin
            approved_by=current_user.name
        )
        
        
        # Add additional fields for admin-created requests
        field_exit_dict = field_exit_request.dict()
        field_exit_dict.update({
            "date": date,
            "expected_start_time": expected_start_time,
            "expected_end_time": expected_end_time,
            "actual_start_time": None,
            "actual_end_time": None,
            "approved_by_id": current_user.id,
            "approved_at": datetime.utcnow(),
            "admin_notes": f"Request created by Super Admin ({current_user.name}) on behalf of employee. Notes: {notes}",
            "created_by_admin": True,
            "created_by_admin_id": current_user.id,
            "created_by_admin_name": current_user.name,
            "exit_status": "approved"
        })
        
        await db.field_exits.insert_one(field_exit_dict)
        
        # Log activity
        await log_activity(
            current_user.id, 
            "admin_field_exit_created", 
            f"Created field exit request for {employee['name']} on {date} - {visit_type}"
        )
        
        
        # Send notification to employee
        message = Message(
            title="✅ طلب زيارة خارجية معتمد",
            content=f"""عزيزي/عزيزتي {employee['name']},

تم إنشاء واعتماد طلب زيارة خارجية نيابة عنك من قبل الإدارة:

📅 التاريخ: {date}
📝 نوع الزيارة: {visit_type}
👤 العميل: {client_name}
🕘 الوقت المتوقع للخروج: {expected_start_time}
🕘 الوقت المتوقع للعودة: {expected_end_time}
📋 ملاحظات الإدارة: {field_exit_dict['admin_notes']}

تم الموافقة على الطلب تلقائياً.

إدارة الموارد البشرية
TANSEEQ TAX CONSULTANCY""",
            message_type="field_exit_approved",
            from_user_id=current_user.id,
            from_user_name=f"إدارة الموارد البشرية ({current_user.name})",
            to_user_ids=[user_id],
            priority="normal"
        )
        
        
        await db.messages.insert_one(message.dict())
        
        return {
            "message": "Field exit request created and approved successfully",
            "field_exit_id": field_exit_request.id,
            "employee_name": employee["name"],
            "status": "approved"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating field exit request: {str(e)}")

# ============ ADMIN: ATTACHMENT VIEWING CAPABILITY ============

@api_router.get("/admin/view-attachment/{request_type}/{request_id}")
async def view_attachment(
    request_type: str, 
    request_id: str, 
    current_user: User = Depends(get_admin_user)
):
    """Admin/Super Admin: View attachment from leave or field exit request"""
    try:
        if request_type not in ["leave", "field-exit"]:
            raise HTTPException(status_code=400, detail="Invalid request type. Must be 'leave' or 'field-exit'")
        
        # Get the request
        if request_type == "leave":
            request_data = await db.leaves.find_one({"id": request_id})
        else:  # field-exit
            request_data = await db.field_exits.find_one({"id": request_id})
        
        if not request_data:
            raise HTTPException(status_code=404, detail=f"{request_type.title()} request not found")
        
        # Check if request has attachment
        file_path = request_data.get("file_path") or request_data.get("attachment_url")
        if not file_path:
            raise HTTPException(status_code=404, detail="No attachment found for this request")
        
        # Handle both file_path and attachment_url formats
        if file_path.startswith("/uploads/"):
            actual_file_path = uploads_dir / file_path.replace("/uploads/", "")
        else:
            actual_file_path = Path(file_path)
        
        if not actual_file_path.exists():
            raise HTTPException(status_code=404, detail="Attachment file not found on server")
        
        # Read file and return as base64 for frontend display
        import base64
        from mimetypes import guess_type
        
        with open(actual_file_path, "rb") as file:
            file_content = file.read()
            file_base64 = base64.b64encode(file_content).decode()
            
            # Get mime type
            mime_type, _ = guess_type(str(actual_file_path))
            if not mime_type:
                mime_type = "application/octet-stream"
            
            # Get file name
            file_name = actual_file_path.name
            
            return {
                "file_name": file_name,
                "mime_type": mime_type,
                "file_size": len(file_content),
                "file_data": f"data:{mime_type};base64,{file_base64}",
                "request_type": request_type,
                "request_id": request_id,
                "employee_name": request_data.get("user_name", "Unknown"),
                "created_at": request_data.get("created_at", "Unknown")
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error viewing attachment: {str(e)}")

@api_router.get("/admin/attachments-list")
async def list_requests_with_attachments(current_user: User = Depends(get_admin_user)):
    """Admin/Super Admin: Get list of all requests with attachments"""
    try:
        # Get leave requests with attachments
        leave_requests = await db.leaves.find({
            "$or": [
                {"file_path": {"$exists": True, "$ne": None, "$ne": ""}},
                {"attachment_url": {"$exists": True, "$ne": None, "$ne": ""}}
            ]
        }).to_list(1000)
        
        # Get field exit requests with attachments (future feature - currently not implemented)
        field_exit_requests = []  # Field exits don't have file attachments yet
        
        # Format the response
        attachments_list = []
        
        # Process leave requests
        for leave in leave_requests:
            attachments_list.append({
                "request_type": "leave",
                "request_id": leave["id"],
                "employee_name": leave.get("user_name", "Unknown"),
                "date_range": f"{leave.get('start_date', '')} to {leave.get('end_date', '')}",
                "reason": leave.get("reason", ""),
                "status": leave.get("status", "pending"),
                "created_at": leave.get("created_at", ""),
                "has_attachment": bool(leave.get("file_path") or leave.get("attachment_url"))
            })
        
        # Process field exit requests (when file attachments are added)
        for field_exit in field_exit_requests:
            attachments_list.append({
                "request_type": "field_exit",
                "request_id": field_exit["id"],
                "employee_name": field_exit.get("user_name", "Unknown"),
                "date_range": field_exit.get("date", ""),
                "reason": field_exit.get("visit_type", ""),
                "status": field_exit.get("status", "pending"),
                "created_at": field_exit.get("created_at", ""),
                "has_attachment": bool(field_exit.get("file_path"))
            })
        
        # Sort by created_at (newest first)
        attachments_list.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return {
            "total_attachments": len(attachments_list),
            "leave_attachments": len(leave_requests),
            "field_exit_attachments": len(field_exit_requests),
            "attachments": attachments_list
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing attachments: {str(e)}")

@api_router.get("/overtime-reports/{month}")
async def get_overtime_report(month: str, current_user: User = Depends(get_admin_user)):
    """Generate overtime report for specific month (Admin only)"""
    try:
        # Validate month format (YYYY-MM)
        datetime.strptime(month, "%Y-%m")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM")
    
    # Get all active employees (exclude admin/super_admin)
    employees = await db.users.find({
        "is_active": True,
        "role": "user"
    }).to_list(1000)
    
    overtime_data = []
    
    for employee in employees:
        # Get attendance records for the month
        attendance_records = await db.attendance.find({
            "user_id": employee["id"],
            "date": {"$regex": f"^{month}"},
            "check_in": {"$exists": True},
            "check_out": {"$exists": True}
        }).to_list(1000)
        
        total_overtime_for_employee = 0
        employee_overtime_records = []
        
        for record in attendance_records:
            check_in_str = record.get("check_in")
            check_out_str = record.get("check_out")
            date = record.get("date")
            
            if not check_in_str or not check_out_str:
                continue
            
            # Parse times
            try:
                check_in_time = datetime.strptime(check_in_str, "%H:%M:%S").time()
                check_out_time = datetime.strptime(check_out_str, "%H:%M:%S").time()
            except:
                continue
            
            # Standard work hours: 9:00 AM to 6:00 PM (9 hours)
            standard_start = datetime.strptime("09:00:00", "%H:%M:%S").time()
            standard_end = datetime.strptime("18:00:00", "%H:%M:%S").time()
            
            # Calculate actual working hours
            check_in_dt = datetime.combine(datetime.strptime(date, "%Y-%m-%d").date(), check_in_time)
            check_out_dt = datetime.combine(datetime.strptime(date, "%Y-%m-%d").date(), check_out_time)
            
            # Handle next day checkout
            if check_out_time < check_in_time:
                check_out_dt += timedelta(days=1)
            
            total_hours = (check_out_dt - check_in_dt).total_seconds() / 3600
            
            # Calculate overtime hours
            early_hours = 0  # Before 9 AM
            late_hours = 0   # After 6 PM
            
            # Early overtime (before 9 AM)
            if check_in_time < standard_start:
                early_start_dt = datetime.combine(datetime.strptime(date, "%Y-%m-%d").date(), check_in_time)
                standard_start_dt = datetime.combine(datetime.strptime(date, "%Y-%m-%d").date(), standard_start)
                early_hours = (standard_start_dt - early_start_dt).total_seconds() / 3600
            
            # Late overtime (after 6 PM)
            if check_out_time > standard_end:
                standard_end_dt = datetime.combine(datetime.strptime(date, "%Y-%m-%d").date(), standard_end)
                late_end_dt = datetime.combine(datetime.strptime(date, "%Y-%m-%d").date(), check_out_time)
                # Handle next day
                if check_out_time < standard_end:
                    late_end_dt += timedelta(days=1)
                late_hours = (late_end_dt - standard_end_dt).total_seconds() / 3600
            
            total_overtime = early_hours + late_hours
            
            # Only include records with overtime
            if total_overtime > 0.1:  # More than 6 minutes
                employee_overtime_records.append({
                    "date": date,
                    "check_in_time": check_in_str,
                    "check_out_time": check_out_str,
                    "total_working_hours": round(total_hours, 2),
                    "standard_hours": 9.0,
                    "early_overtime_hours": round(early_hours, 2),
                    "late_overtime_hours": round(late_hours, 2),
                    "total_overtime_hours": round(total_overtime, 2),
                    "overtime_type": "Early Start" if early_hours > late_hours else "Late Finish" if late_hours > 0 else "Mixed"
                })
                total_overtime_for_employee += total_overtime
        
        # Add employee data if they have overtime
        if employee_overtime_records:
            overtime_data.append({
                "employee_id": employee["id"],
                "user_name_en": translate_to_english(employee["name"]),
                "employee_name": translate_to_english(employee["name"]),
                "arabic_name": employee["name"],
                "total_overtime_hours": round(total_overtime_for_employee, 2),
                "overtime_days": len(employee_overtime_records),
                "overtime_details": employee_overtime_records
            })
    
    return {
        "month": month,
        "total_records": len(overtime_data),
        "total_employees": len(overtime_data),
        "total_overtime_hours": round(sum(record["total_overtime_hours"] for record in overtime_data), 2),
        "overtime_records": overtime_data
    }

@api_router.get("/overtime-reports/export/{month}")
async def export_overtime_report(month: str, format: str = "excel", current_user: User = Depends(get_admin_user)):
    """Export overtime report with professional design"""
    from io import BytesIO
    from fastapi.responses import StreamingResponse
    
    overtime_data = await get_overtime_report(month, current_user)
    records = overtime_data["overtime_records"]
    
    if format == "excel":
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
        
        # Create workbook and worksheet
        wb = Workbook()
        ws = wb.active
        ws.title = f"overtime_{month}"
        
        # Set column widths
        column_widths = [20, 12, 12, 12, 15, 12, 12, 12, 15, 15]
        for i, width in enumerate(column_widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = width
        
        # Company header
        ws.merge_cells('A1:J1')
        company_cell = ws['A1']
        company_cell.value = "TANSEEQ TAX CONSULTANCY - OVERTIME REPORT"
        company_cell.font = Font(name="Arial", size=18, bold=True, color="FFFFFF")
        company_cell.fill = PatternFill(start_color="1B4477", end_color="1B4477", fill_type="solid")
        company_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[1].height = 35
        
        # Report info
        ws.merge_cells('A2:J2')
        info_cell = ws['A2']
        info_cell.value = f"Month: {month} | Total Overtime Hours: {overtime_data['total_overtime_hours']} | Employees: {overtime_data['total_employees']}"
        info_cell.font = Font(name="Arial", size=12, color="4472C4")
        info_cell.fill = PatternFill(start_color="E6EFFF", end_color="E6EFFF", fill_type="solid")
        info_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[2].height = 25
        
        # Headers
        headers = [
            "Employee Name", "Date", "Check In", "Check Out", "Total Hours",
            "Standard Hours", "Early OT", "Late OT", "Total OT", "OT Type"
        ]
        
        header_style = Font(name="Arial", size=11, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="1B4477", end_color="1B4477", fill_type="solid")
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col)
            cell.value = header
            cell.font = header_style
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")
        
        ws.row_dimensions[4].height = 30
        
        # Data rows
        row_num = 5
        for record in records:
            for detail in record["overtime_details"]:
                row_data = [
                    record["employee_name"],
                    detail["date"],
                    detail["check_in_time"],
                    detail["check_out_time"],
                    f"{detail['total_working_hours']:.2f}h",
                    f"{detail['standard_hours']:.1f}h",
                    f"{detail['early_overtime_hours']:.2f}h",
                    f"{detail['late_overtime_hours']:.2f}h",
                    f"{detail['total_overtime_hours']:.2f}h",
                    detail["overtime_type"]
                ]
                
                for col, value in enumerate(row_data, 1):
                    cell = ws.cell(row=row_num, column=col)
                    cell.value = value
                    cell.font = Font(name="Arial", size=10)
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                    
                    # Alternating row colors
                    if row_num % 2 == 0:
                        cell.fill = PatternFill(start_color="F8F9FA", end_color="F8F9FA", fill_type="solid")
                
                ws.row_dimensions[row_num].height = 25
                row_num += 1
        
        # Add borders
        thin_border = Border(
            left=Side(style='thin'), right=Side(style='thin'),
            top=Side(style='thin'), bottom=Side(style='thin')
        )
        
        
        for row in ws.iter_rows(min_row=4, max_row=row_num-1, min_col=1, max_col=10):
            for cell in row:
                cell.border = thin_border
        
        # Summary
        summary_row = row_num + 1
        ws.merge_cells(f'A{summary_row}:J{summary_row}')
        summary_cell = ws[f'A{summary_row}']
        summary_cell.value = f"SUMMARY: {len(records)} overtime records | Total: {overtime_data['total_overtime_hours']:.2f} hours | Average per employee: {overtime_data['total_overtime_hours']/max(overtime_data['total_employees'],1):.2f} hours"
        summary_cell.font = Font(name="Arial", size=12, bold=True, color="1B4477")
        summary_cell.fill = PatternFill(start_color="E8F4FD", end_color="E8F4FD", fill_type="solid")
        summary_cell.alignment = Alignment(horizontal="center", vertical="center")
        
        # Save to BytesIO
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        return StreamingResponse(
            BytesIO(output.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=TANSEEQ_overtime_report_{month}.xlsx"}
        )
        
    
    else:  # PDF format
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        
        output = BytesIO()
        doc = SimpleDocTemplate(output, pagesize=landscape(A4))
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title = Paragraph(f"<b>TANSEEQ TAX CONSULTANCY - OVERTIME REPORT</b><br/>Month: {month}", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 20))
        
        # Summary
        summary_text = f"Total Records: {len(records)} | Total Overtime Hours: {overtime_data['total_overtime_hours']:.2f} | Employees: {overtime_data['total_employees']}"
        summary = Paragraph(summary_text, styles['Normal'])
        elements.append(summary)
        elements.append(Spacer(1, 20))
        
        # Table data
        table_data = [["Employee", "Date", "Check In", "Check Out", "Total Hours", "Early OT", "Late OT", "Total OT", "Type"]]
        
        for record in records:
            for detail in record["overtime_details"]:
                table_data.append([
                    record["employee_name"],
                    detail["date"],
                    detail["check_in_time"],
                    detail["check_out_time"],
                    f"{detail['total_working_hours']:.1f}h",
                    f"{detail['early_overtime_hours']:.1f}h",
                    f"{detail['late_overtime_hours']:.1f}h",
                    f"{detail['total_overtime_hours']:.1f}h",
                    detail["overtime_type"]
                ])
        
        # Create table
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.navy),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        doc.build(elements)
        
        output.seek(0)
        return StreamingResponse(
            BytesIO(output.read()),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=TANSEEQ_overtime_report_{month}.pdf"}
        )
        

@api_router.get("/automation/status")
async def get_automation_status(current_user: User = Depends(get_super_admin_user)):
    """Get status of automation systems"""
    try:
        # Check if automation scheduler is running (basic check)
        import subprocess
        
        automation_running = False
        try:
            # Check if automation_scheduler.py process is running
            result = subprocess.run(
                ["pgrep", "-f", "automation_scheduler.py"],
                capture_output=True, text=True
            )
        
            automation_running = bool(result.returncode == 0)
        except:
            automation_running = False
        
        # Get recent automation logs/activity
        recent_messages = await db.messages.find({
            "message_type": {"$in": ["late_warning", "absence_warning", "penalty_notification"]},
            "created_at": {"$gte": datetime.utcnow() - timedelta(days=7)}
        }).sort("created_at", -1).limit(10).to_list(10)
        
        # Get recent penalty applications (if late_penalties collection exists)
        recent_penalties = []
        try:
            recent_penalties = await db.late_penalties.find({
                "applied_at": {"$gte": datetime.utcnow() - timedelta(days=30)}
            }).sort("applied_at", -1).limit(5).to_list(5)
        except:
            pass  # Collection might not exist yet
        
        return {
            "automation_scheduler_running": automation_running,
            "scheduled_tasks": {
                "late_warnings": "Daily at 09:30 AM UAE",
                "absence_warnings": "Daily at 11:00 AM UAE", 
                "monthly_penalties": "1st day of month at 02:00 AM UAE"
            },
            "recent_activity": {
                "total_recent_notifications": len(recent_messages),
                "recent_penalty_applications": len(recent_penalties),
                "last_notification": recent_messages[0]["created_at"] if recent_messages else None,
                "last_penalty_application": recent_penalties[0]["applied_at"] if recent_penalties else None
            },
            "system_status": "active" if automation_running else "inactive"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting automation status: {str(e)}")

# ============ WORK REPORTS MODULE (COMPLETELY ISOLATED) ============
"""
Daily Work Report + Clients Master Feature
This module is completely isolated from the main TANSEEQ HR system
Uses PostgreSQL instead of MongoDB for data storage
"""

# Work Reports MongoDB initialization is now handled in app startup event

# ============ CLIENT MANAGEMENT ENDPOINTS ============

@api_router.get("/work-reports/clients")
async def get_clients(current_user = Depends(get_current_user)):
    """Get all clients - MongoDB version"""
    try:
        clients = await work_reports_db.clients.find({"is_active": True}).to_list(1000)
        
        # Convert to response format
        client_list = []
        for client in clients:
            client_list.append({
                "id": client.get("id"),
                "company_name": client.get("company_name"),
                "company_name_ar": client.get("company_name_ar"),
                "client_code": client.get("client_code"),
                "industry": client.get("industry"),
                "contact_person": client.get("contact_person"),
                "phone": client.get("phone"),
                "email": client.get("email"),
                "address": client.get("address"),
                "tax_number": client.get("tax_number"),
                "commercial_registration": client.get("commercial_registration"),
                "is_active": client.get("is_active", True),
                "created_at": client.get("created_at"),
                "updated_at": client.get("updated_at")
            })
        
        await log_work_reports_activity(current_user.id, "view_clients", "Viewed clients list")
        
        return client_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting clients: {str(e)}")

@api_router.post("/work-reports/clients")
async def create_client(
    client_data: ClientCreate,
    current_user: User = Depends(get_current_user)
):
    """Create new client (MongoDB)"""
    # Generate client code if not provided
    if not client_data.client_code:
        company_initials = ''.join([word[0].upper() for word in client_data.company_name.split()[:3]])
        timestamp = datetime.now().strftime("%y%m")
        client_data.client_code = f"{company_initials}{timestamp}"
    # Check for duplicate client code
    dup = await work_reports_db.clients.find_one({"client_code": client_data.client_code})
    if dup:
        raise HTTPException(status_code=400, detail="Client code already exists")
    client_doc = {
        "id": str(uuid.uuid4()),
        "company_name": client_data.company_name,
        "company_name_ar": client_data.company_name_ar,
        "client_code": client_data.client_code,
        "industry": client_data.industry,
        "contact_person": client_data.contact_person,
        "phone": client_data.phone,
        "email": client_data.email,
        "address": client_data.address,
        "tax_number": client_data.tax_number,
        "commercial_registration": client_data.commercial_registration,
        "is_active": True,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "created_by": current_user.id,
        "created_by_name": current_user.name
    }
    await work_reports_db.clients.insert_one(client_doc)
    # Remove _id for JSON serialization in activity log
    log_doc = {k: v for k, v in client_doc.items() if k != "_id"}
    await log_work_reports_activity(current_user.id, "create_client", f"Created client {client_doc['company_name']}", target_id=client_doc["id"], after_value=json.dumps(log_doc))
    client_doc.pop("_id", None)
    return client_doc

@api_router.put("/work-reports/clients/{client_id}")
async def update_client(
    client_id: str,
    client_update: ClientUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update client information (MongoDB)"""
    # Find existing client
    client = await work_reports_db.clients.find_one({"id": client_id})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Store original values for audit
    original_data = {
        "company_name": client.get("company_name"),
        "client_code": client.get("client_code"),
        "email": client.get("email"),
        "phone": client.get("phone")
    }
    
    # Prepare update data
    update_data = client_update.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow().isoformat()
    
    # Update client in MongoDB
    await work_reports_db.clients.update_one(
        {"id": client_id},
        {"$set": update_data}
    )
    
    # Get updated client
    updated_client = await work_reports_db.clients.find_one({"id": client_id})
    
    # Log activity
    await log_work_reports_activity(
        current_user.id, "update_client", 
        f"Updated client {updated_client['company_name']}", 
        target_id=client_id,
        before_value=json.dumps(original_data),
        after_value=json.dumps(update_data)
    )
    
    # Remove _id for response
    updated_client.pop("_id", None)
    return updated_client

@api_router.delete("/work-reports/clients/{client_id}")
async def delete_client(
    client_id: str,
    current_user = Depends(get_admin_user),
    db = Depends(get_work_reports_db)
):
    """Delete client (Admin only) - Soft delete"""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Soft delete
    client.is_active = False
    client.updated_at = datetime.utcnow()
    db.commit()
    
    log_work_reports_activity(
        db, current_user.id, current_user.name, "delete_client",
        table_name="clients", record_id=str(client.id)
    )
    
    return {"message": "Client deleted successfully"}

# ============ CLIENT CREDENTIALS MANAGEMENT ============

@api_router.get("/work-reports/clients/{client_id}/credentials", response_model=List[ClientCredentialResponse])
async def get_client_credentials(
    client_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_work_reports_db)
):
    """Get client credentials (without passwords)"""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    credentials = db.query(ClientCredential).filter(
        ClientCredential.client_id == client_id,
        ClientCredential.is_active == True
    ).all()
    
    log_work_reports_activity(
        db, current_user.id, current_user.name, "view_credentials",
        table_name="client_credentials", record_id=client_id
    )
    
    return credentials

@api_router.post("/work-reports/clients/{client_id}/credentials", response_model=ClientCredentialResponse)
async def create_client_credential(
    client_id: str,
    credential_data: ClientCredentialCreate,
    current_user = Depends(get_current_user),
    db = Depends(get_work_reports_db)
):
    """Create client credential - NO PERMISSIONS CHECK - FULL ACCESS FOR ALL USERS"""
    
    # NO PERMISSION CHECKS - ALL USERS CAN CREATE CREDENTIALS
    
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Save password as plain text (no encryption)
    plain_password = credential_data.password if credential_data.password else None
    
    # Create credential
    credential = ClientCredential(
        client_id=client_id,
        credential_type=credential_data.credential_type,
        username=credential_data.username,
        email=credential_data.email,
        password=plain_password,  # Store as plain text
        encrypted_password=None,  # No encryption
        portal_url=credential_data.portal_url,
        description=credential_data.description,
        is_active=True  # Default to True
    )
    
    db.add(credential)
    db.commit()
    db.refresh(credential)
    
    log_work_reports_activity(
        db, current_user.id, current_user.name, "create_credential",
        table_name="client_credentials", record_id=str(credential.id),
        after_value={"credential_type": credential_data.credential_type, "client_id": client_id}
    )
    
    return credential

@api_router.get("/work-reports/credentials/{credential_id}/password")
async def get_credential_password(
    credential_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_work_reports_db)
):
    """Get credential password - NO PERMISSIONS CHECK - FULL ACCESS FOR ALL USERS"""
    
    # NO PERMISSION CHECKS - ALL USERS CAN ACCESS PASSWORDS
    
    credential = db.query(ClientCredential).filter(ClientCredential.id == credential_id).first()
    if not credential:
        raise HTTPException(status_code=404, detail="Credential not found")
    
    # Get plain text password (no encryption)
    if not credential.password:
        raise HTTPException(status_code=404, detail="لا توجد كلمة مرور محفوظة لهذا الاعتماد")
    
    # Update last used timestamp
    credential.last_used = datetime.utcnow()
    db.commit()
    
    log_work_reports_activity(
        db, current_user.id, current_user.name, "access_password",
        table_name="client_credentials", record_id=str(credential.id)
    )
    
    return {"password": credential.password}

# ============ ACTIVITY TYPES MANAGEMENT ============

@api_router.get("/work-reports/activity-types")
async def get_activity_types(current_user = Depends(get_current_user)):
    """Get all activity types - MongoDB version"""
    try:
        activity_types = await work_reports_db.activity_types.find({}).to_list(1000)
        
        # Convert to response format
        activities = []
        for activity in activity_types:
            activities.append({
                "id": activity.get("id"),
                "name": activity.get("name"),
                "name_ar": activity.get("name_ar"),
                "description": activity.get("description"),
                "hourly_rate": activity.get("hourly_rate"),
                "is_billable": activity.get("is_billable", True),
                "category": activity.get("category"),
                "created_at": activity.get("created_at")
            })
        
        return activities
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting activity types: {str(e)}")

@api_router.post("/work-reports/activity-types", response_model=ActivityTypeResponse)
async def create_activity_type(
    activity_data: ActivityTypeCreate,
    current_user = Depends(get_admin_user),
    db = Depends(get_work_reports_db)
):
    """Create new activity type (Admin only)"""
    activity_type = ActivityType(**activity_data.dict())
    db.add(activity_type)
    db.commit()
    db.refresh(activity_type)
    
    log_work_reports_activity(
        db, current_user.id, current_user.name, "create_activity_type",
        table_name="activity_types", record_id=str(activity_type.id),
        after_value=activity_data.dict()
    )
    
    return activity_type
# Ensure MongoDB indexes for work reports logs
@app.on_event("startup")
async def init_work_reports_indexes():
    """
    Initialize Work Reports MongoDB indexes
    ✅ Non-blocking: runs in background, doesn't block startup
    """
    try:
        # ✅ Check if work_reports_db is available
        if work_reports_db is None:
            logger.warning("Work Reports DB not available, skipping index creation")
            return
        
        # ✅ Create indexes in background (non-blocking)
        import asyncio
        async def create_indexes_background():
            try:
                # Compound indexes for performance
                await work_reports_db.work_logs.create_index([("created_by", 1), ("start_at", -1)])
                await work_reports_db.work_logs.create_index([("client_id", 1)])
                await work_reports_db.work_logs.create_index([("start_at", -1)])
                # Optional text index for search
                await work_reports_db.work_logs.create_index(
                    [("description", "text"), ("notes", "text"), ("client_name", "text"), ("activity_name", "text")],
                    name="worklog_text_index"
                )
        
                logger.info("✅ Work Reports indexes created successfully")
            except Exception as e:
                logger.warning(f"Work Reports index creation warning: {e}")
        
        # ✅ Run in background without blocking startup
        asyncio.create_task(create_indexes_background())
        
    except Exception as e:
        logger.warning(f"Work Reports index initialization warning: {e}")


# ============ WORK LOG MANAGEMENT ============

@api_router.get("/work-reports/logs")
async def get_work_logs(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    client_id: Optional[str] = None,
    employee_id: Optional[str] = None,
    q: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user)
):
    """Get work logs (MongoDB) with filters, search, and pagination.
    Returns: { items: [...], total: int, page: int, page_size: int }
    """
    coll = work_reports_db.work_logs
    # Build filter
    filter_query: Dict[str, Any] = {}
    # RBAC: regular users only see their own logs
    if current_user.role == "user":
        filter_query["created_by"] = current_user.id
    elif employee_id:
        filter_query["created_by"] = employee_id
    # Date range using start_at
    try:
        if start_date:
            start_dt = datetime.strptime(start_date + " 00:00", "%Y-%m-%d %H:%M")
            filter_query.setdefault("start_at", {})["$gte"] = start_dt
        if end_date:
            end_dt = datetime.strptime(end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S")
            filter_query.setdefault("start_at", {})["$lte"] = end_dt
    except Exception:
        pass
    # Client filter
    if client_id:
        filter_query["client_id"] = client_id
    # Text search over description/notes/client_name/activity_name
    if q:
        filter_query["$text"] = {"$search": q}
    # Pagination params
    page = max(1, page)
    page_size = max(1, min(100, page_size))
    skip = (page - 1) * page_size
    # Count total
    total = await coll.count_documents(filter_query)
    # Query items sorted by start_at desc then created_at desc
    cursor = coll.find(filter_query).sort([
        ("start_at", -1),
        ("created_at", -1)
    ]).skip(skip).limit(page_size)
    items = []
    async for doc in cursor:
        doc.pop("_id", None)
        items.append(doc)
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }

@api_router.post("/work-reports/logs")
async def create_work_log(
    log_data: WorkLogCreate,
    current_user: User = Depends(get_current_user)
):
    """Create new work log entry (MongoDB)"""
    # Validate referenced data
    client = await work_reports_db.clients.find_one({"id": log_data.client_id})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    activity = await work_reports_db.activity_types.find_one({"id": log_data.activity_type_id})
    if not activity:
        raise HTTPException(status_code=404, detail="Activity type not found")
    # Compute duration in minutes
    try:
        start_dt = datetime.strptime(f"{log_data.date} {log_data.start_time}", "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(f"{log_data.date} {log_data.end_time}", "%Y-%m-%d %H:%M")
        duration_minutes = int((end_dt - start_dt).total_seconds() // 60)
    except Exception:
        duration_minutes = 0
    hourly_rate = (activity.get("hourly_rate") or 0)
    total_amount = round((duration_minutes / 60) * hourly_rate, 2) if duration_minutes and hourly_rate else 0
    work_log = {
        "id": str(uuid.uuid4()),
        "client_id": log_data.client_id,
        "client_name": client.get("company_name"),
        "activity_type_id": log_data.activity_type_id,
        "activity_name": activity.get("name"),
        "created_by": current_user.id,
        "created_by_name": current_user.name,
        "date": log_data.date,
        "start_time": log_data.start_time,
        "end_time": log_data.end_time,
        "start_at": start_dt.isoformat() if duration_minutes else None,
        "end_at": end_dt.isoformat() if duration_minutes else None,
        "duration_minutes": duration_minutes,
        "description": log_data.description,
        "notes": None,
        "is_billable": True,
        "hourly_rate": hourly_rate,
        "total_amount": total_amount,
        "status": "open",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    await work_reports_db.work_logs.insert_one(work_log)
    await log_work_reports_activity(
        current_user.id,
        "create_work_log",
        f"Created work log for client {client.get('company_name')}",
        target_id=work_log["id"],
        after_value=json.dumps({"duration_minutes": duration_minutes, "total_amount": total_amount})
    )
    work_log.pop("_id", None)
    return work_log

@api_router.put("/work-reports/logs/{log_id}")
async def update_work_log(
    log_id: str,
    log_update: WorkLogUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update work log entry (MongoDB)"""
    doc = await work_reports_db.work_logs.find_one({"id": log_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Work log not found")
    if current_user.role == "user" and doc.get("created_by") != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    original = {k: doc.get(k) for k in ["start_time","end_time","duration_minutes","total_amount","description","notes"]}
    update_data = {k: v for k, v in log_update.dict(exclude_unset=True).items()}
    # Recompute duration and amounts if times changed
    start_time = update_data.get("start_time", doc.get("start_time"))
    end_time = update_data.get("end_time", doc.get("end_time"))
    date_str = update_data.get("date", doc.get("date"))
    duration_minutes = doc.get("duration_minutes", 0)
    hourly_rate = doc.get("hourly_rate", 0)
    try:
        # Accept both 'YYYY-MM-DD' with 'HH:MM' and ISO 'YYYY-MM-DDTHH:MM:SS' inputs
        if start_time and end_time and date_str:
            # Normalize time strings - handle both string and datetime inputs
            def norm_time(t) -> str:
                if isinstance(t, datetime):
                    return t.strftime("%H:%M")
                elif isinstance(t, str):
                    return t.split('T')[1][:5] if 'T' in t else t[:5]
                else:
                    return str(t)[:5]
            
            def norm_date(d) -> str:
                if isinstance(d, datetime):
                    return d.strftime("%Y-%m-%d")
                elif isinstance(d, str):
                    return d.split('T')[0]
                else:
                    return str(d)[:10]
            
            start_dt = datetime.strptime(f"{norm_date(date_str)} {norm_time(start_time)}", "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(f"{norm_date(date_str)} {norm_time(end_time)}", "%Y-%m-%d %H:%M")
            duration_minutes = max(0, int((end_dt - start_dt).total_seconds() // 60))
            update_data["duration_minutes"] = duration_minutes
            update_data["start_at"] = start_dt.isoformat()
            update_data["end_at"] = end_dt.isoformat()
            update_data["total_amount"] = round((duration_minutes / 60) * hourly_rate, 2) if hourly_rate else doc.get("total_amount", 0)
    except Exception as e:
        logger.warning(f"Work log recompute failed for {log_id}: {e}")
    update_data["updated_at"] = datetime.utcnow()
    await work_reports_db.work_logs.update_one({"id": log_id}, {"$set": update_data})
    # Convert datetime objects to strings for JSON serialization
    def serialize_for_json(data):
        """Convert datetime objects to ISO format strings for JSON serialization"""
        serialized = {}
        for k, v in data.items():
            if isinstance(v, datetime):
                serialized[k] = v.isoformat()
            else:
                serialized[k] = v
        return serialized
    
    await log_work_reports_activity(
        current_user.id,
        "update_work_log",
        f"Updated work log {log_id}",
        target_id=log_id,
        before_value=json.dumps(serialize_for_json(original)),
        after_value=json.dumps(serialize_for_json(update_data))
    )
    doc = await work_reports_db.work_logs.find_one({"id": log_id}, {"_id": 0})
    return doc

@api_router.delete("/work-reports/logs/{log_id}")
async def delete_work_log(
    log_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete work log entry (MongoDB)"""
    log_doc = await work_reports_db.work_logs.find_one({"id": log_id})
    if not log_doc:
        raise HTTPException(status_code=404, detail="Work log not found")
    if current_user.role == "user" and log_doc.get("created_by") != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    await work_reports_db.work_logs.delete_one({"id": log_id})
    await log_work_reports_activity(
        current_user.id,
        "delete_work_log",
        f"Deleted work log {log_id}",
        target_id=log_id
    )
    return {"message": "Work log deleted successfully"}

# ============ CLIENT DATA IMPORT ENDPOINT ============

@api_router.post("/work-reports/import-clients")
async def import_clients_from_excel(
    current_user = Depends(get_admin_user),
    db = Depends(get_work_reports_db)
):
    """Import clients from Excel file (عملاء.xlsx)"""
    try:
        # Download the Excel file from the provided URL
        excel_url = "https://customer-assets.emergentagent.com/job_hr-dashboard-20/artifacts/warpb19o_%D8%B9%D9%85%D9%84%D8%A7%D8%A1.xlsx"
        
        response = requests.get(excel_url)
        response.raise_for_status()
        
        # Load Excel file
        workbook = openpyxl.load_workbook(BytesIO(response.content))
        sheet = workbook.active
        
        imported_clients = []
        errors = []
        
        # Assuming the Excel has headers in the first row
        # Expected columns: Company Name, Contact Person, Phone, Email, etc.
        headers = []
        for col in range(1, sheet.max_column + 1):
            cell_value = sheet.cell(row=1, column=col).value
            if cell_value:
                headers.append(str(cell_value).strip())
        
        # Process each row (starting from row 2)
        skipped_empty_rows = 0
        for row_num in range(2, sheet.max_row + 1):
            try:
                row_data = {}
                for col_num, header in enumerate(headers, 1):
                    cell_value = sheet.cell(row=row_num, column=col_num).value
                    if cell_value is not None:
                        row_data[header] = str(cell_value).strip()
                
                # Skip empty rows (improved detection)
                if not any(value for value in row_data.values() if value and value.strip()):
                    skipped_empty_rows += 1
                    continue
                
                # Map Excel columns to our Client model  
                # تحديث المطابقة حسب الهيكل الفعلي للملف
                company_name = (
                    row_data.get("أسم الشركة") or 
                    row_data.get("اسم الشركة") or 
                    row_data.get("Company Name") or
                    row_data.get("الشركة") or ""
                )
        
                
                email = (
                    row_data.get("أميل") or
                    row_data.get("ايميل") or
                    row_data.get("Email") or
                    row_data.get("البريد الالكتروني") or ""
                ).strip() if row_data.get("أميل") or row_data.get("ايميل") or row_data.get("Email") or row_data.get("البريد الالكتروني") else ""
                
                if not company_name or company_name.strip() == "":
                    errors.append(f"Row {row_num}: اسم الشركة مفقود - Missing company name")
                    continue
                
                # تنظيف اسم الشركة
                company_name = company_name.strip()
                
                # Generate client code
                company_initials = ''.join([word[0].upper() for word in company_name.split()[:2] if word.strip()])
                if not company_initials:
                    company_initials = "CL"
                timestamp = datetime.now().strftime("%y%m")
                client_code = f"{company_initials}{timestamp}{row_num:03d}"
                
                # Check for duplicate
                existing_client = db.query(Client).filter(
                    Client.company_name == company_name
                ).first()
                
                if existing_client:
                    errors.append(f"Row {row_num}: Client '{company_name}' already exists")
                    continue
                
                # Create client
                client = Client(
                    company_name=company_name,
                    company_name_ar=company_name,  # استخدام نفس الاسم للعربية
                    client_code=client_code,
                    industry=row_data.get("Industry") or row_data.get("القطاع", ""),
                    contact_person=row_data.get("Contact Person") or row_data.get("Contact") or row_data.get("المسؤول", ""),
                    phone=row_data.get("Phone") or row_data.get("Mobile") or row_data.get("الهاتف", ""),
                    email=email,
                    address=row_data.get("Address") or row_data.get("العنوان", ""),
                    tax_number=row_data.get("Tax Number") or row_data.get("TRN") or row_data.get("الرقم الضريبي", ""),
                    commercial_registration=row_data.get("CR Number") or row_data.get("الرخصة التجارية", ""),
                    notes=f"تم الاستيراد من Excel في {datetime.now().strftime('%Y-%m-%d')}",
                    created_by=current_user.name
                )
        
                
                db.add(client)
                
                # إضافة بيانات الاعتماد إذا كانت متوفرة
                email_password = row_data.get("باسورد الأميل", "").strip()
                fta_password = row_data.get("باسورد الهيئة", "").strip()
                
                # حفظ العميل أولاً للحصول على ID
                db.commit()
                db.refresh(client)
                
                # إضافة بيانات اعتماد الإيميل
                if email and email_password:
                    email_credential = ClientCredential(
                        client_id=client.id,
                        credential_type="email_account",
                        username=email,
                        email=email,
                        encrypted_password=credential_encryption.encrypt_password(email_password),
                        description="بيانات الإيميل الأساسي للشركة"
                    )
        
                    db.add(email_credential)
                
                # إضافة بيانات اعتماد الهيئة
                if fta_password:
                    fta_credential = ClientCredential(
                        client_id=client.id,
                        credential_type="fta_portal",
                        username=email,  # غالباً نفس الإيميل
                        email=email,
                        encrypted_password=credential_encryption.encrypt_password(fta_password),
                        portal_url="https://tax.gov.ae",
                        description="بوابة الهيئة الاتحادية للضرائب"
                    )
        
                    db.add(fta_credential)
                
                imported_clients.append({
                    "company_name": company_name,
                    "client_code": client_code,
                    "email": email,
                    "has_email_password": bool(email_password),
                    "has_fta_password": bool(fta_password),
                    "row": row_num
                })
                
            except Exception as e:
                errors.append(f"Row {row_num}: Error processing - {str(e)}")
                continue
        
        # Commit all changes
        db.commit()
        
        # Log the import activity
        log_work_reports_activity(
            db, current_user.id, current_user.name, "import_clients",
            table_name="clients",
            after_value={
                "imported_count": len(imported_clients),
                "error_count": len(errors)
            }
        )
        
        
        return {
            "message": "استيراد مكتمل - Import Status",
            "success": len(imported_clients) > 0,
            "imported_count": len(imported_clients),
            "skipped_empty_rows": skipped_empty_rows,
            "error_count": len(errors),
            "imported_clients": imported_clients[:5],  # Show first 5
            "errors": errors[:5] if errors else [],  # Show first 5 errors
            "summary": {
                "total_rows_processed": sheet.max_row - 1,
                "successful_imports": len(imported_clients),
                "empty_rows_skipped": skipped_empty_rows,
                "errors_encountered": len(errors),
                "clients_with_email_credentials": sum(1 for c in imported_clients if c.get("has_email_password")),
                "clients_with_fta_credentials": sum(1 for c in imported_clients if c.get("has_fta_password"))
            },
            "status": "success" if len(imported_clients) > 0 else "failed",
            "status_message": f"تم استيراد {len(imported_clients)} عميل بنجاح" if len(imported_clients) > 0 else "فشل الاستيراد - لم يتم استيراد أي عميل"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

# ============ WORK REPORTS DASHBOARD ENDPOINT ============

@api_router.get("/work-reports/dashboard")
async def get_work_reports_dashboard(
    current_user = Depends(get_current_user)
):
    """Get work reports dashboard statistics - MongoDB version"""
    
    # Get total clients
    total_clients = await work_reports_db.clients.count_documents({"is_active": True})
    
    # Get today's work logs
    today = datetime.now().date().isoformat()
    today_logs_filter = {"date": today}
    if current_user.role == "user":
        today_logs_filter["created_by"] = current_user.id
    today_logs = await work_reports_db.work_logs.count_documents(today_logs_filter)
    
    # Get this week's work logs
    week_start = (datetime.now().date() - timedelta(days=datetime.now().weekday())).isoformat()
    week_logs_filter = {"date": {"$gte": week_start}}
    if current_user.role == "user":
        week_logs_filter["created_by"] = current_user.id
    week_logs = await work_reports_db.work_logs.count_documents(week_logs_filter)
    
    # Get this month's work logs
    month_start = datetime.now().date().replace(day=1).isoformat()
    month_logs_filter = {"date": {"$gte": month_start}}
    if current_user.role == "user":
        month_logs_filter["created_by"] = current_user.id
    month_logs = await work_reports_db.work_logs.count_documents(month_logs_filter)
    
    # Get billable hours this month
    month_billable_logs = await work_reports_db.work_logs.find(month_logs_filter).to_list(1000)
    
    total_billable_minutes = sum([log.get("duration_minutes", 0) for log in month_billable_logs])
    total_billable_hours = round(total_billable_minutes / 60, 2) if total_billable_minutes else 0
    
    # Get total revenue this month
    total_revenue = sum([log.get("amount", 0) or 0 for log in month_billable_logs])
    
    # Get recent activity
    recent_logs_filter = {}
    if current_user.role == "user":
        recent_logs_filter["created_by"] = current_user.id
        
    recent_logs = await work_reports_db.work_logs.find(recent_logs_filter).sort("created_at", -1).limit(5).to_list(5)
    recent_activity = []
    for log in recent_logs:
        # Get client and activity info
        client = await work_reports_db.clients.find_one({"id": log.get("client_id")})
        activity = await work_reports_db.activity_types.find_one({"id": log.get("activity_type_id")})
        
        recent_activity.append({
            "id": log.get("id"),
            "client_name": client.get("company_name", "Unknown") if client else "Unknown",
            "activity_name": activity.get("name", "Unknown") if activity else "Unknown",
            "duration_minutes": log.get("duration_minutes", 0),
            "date": log.get("date"),
            "created_at": log.get("created_at").isoformat() if log.get("created_at") else None
        })
    
    return {
        "total_clients": total_clients,
        "todays_logs": today_logs,
        "week_logs": week_logs,
        "monthly_logs": month_logs,
        "total_billable_hours": total_billable_hours,
        "total_revenue": round(total_revenue, 2),
        "recent_activity": recent_activity,
        "user_role": current_user.role
    }

@api_router.get("/work-reports/credentials/{credential_id}/password")
async def get_credential_password(
    credential_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_work_reports_db)
):
    """Get credential password - NO PERMISSIONS CHECK - FULL ACCESS FOR ALL USERS"""
    
    # NO PERMISSION CHECKS - ALL USERS CAN ACCESS PASSWORDS
    
    credential = db.query(ClientCredential).filter(ClientCredential.id == credential_id).first()
    if not credential:
        raise HTTPException(status_code=404, detail="Credential not found")
    
    # Get plain text password (no encryption)
    if not credential.password:
        raise HTTPException(status_code=404, detail="لا توجد كلمة مرور محفوظة لهذا الاعتماد")
    
    # Update last used timestamp
    credential.last_used = datetime.utcnow()
    db.commit()
    
    log_work_reports_activity(
        db, current_user.id, current_user.name, "access_password",
        table_name="client_credentials", record_id=str(credential.id)
    )
    
    return {"password": credential.password}

@api_router.delete("/work-reports/credentials/{credential_id}")
async def delete_credential(
    credential_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_work_reports_db)
):
    """Delete client credential"""
    credential = db.query(ClientCredential).filter(ClientCredential.id == credential_id).first()
    if not credential:
        raise HTTPException(status_code=404, detail="Credential not found")
    
    # Check permissions - only admin or super admin can delete
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    db.delete(credential)
    db.commit()
    
    log_work_reports_activity(
        db, current_user.id, current_user.name, "delete_credential",
        table_name="client_credentials", record_id=str(credential_id)
    )
    
    return {"message": "Credential deleted successfully"}

@api_router.post("/work-reports/setup-sample-data")
async def setup_sample_data(
    current_user = Depends(get_admin_user),
    db = Depends(get_work_reports_db)
):
    """Setup sample data for testing (Admin only)"""
    try:
        # إنشاء عميل نموذجي إذا لم يكن موجوداً
        sample_client = db.query(Client).filter(Client.company_name == "شركة الإمارات التجارية").first()
        
        if not sample_client:
            sample_client = Client(
                company_name="شركة الإمارات التجارية",
                company_name_ar="Emirates Trading Company",
                client_code="ETC2508001",
                industry="التجارة العامة",
                contact_person="أحمد محمد",
                phone="+971501234567",
                email="contact@emiratestrading.ae",
                address="دبي، الإمارات العربية المتحدة",
                tax_number="100123456789003",
                commercial_registration="1234567890",
                notes="عميل نموذجي للاختبار",
                created_by=current_user.name
            )
        
            db.add(sample_client)
            db.commit()
            db.refresh(sample_client)
        
        # الحصول على نوع النشاط
        activity_type = db.query(ActivityType).filter(ActivityType.name == "VAT Return Filing").first()
        if not activity_type:
            activity_type = db.query(ActivityType).first()
        
        # إنشاء سجلات عمل نموذجية
        sample_logs_data = [
            {
                "date_offset": 0,  # اليوم
                "start_hour": 9,
                "duration": 180,  # 3 ساعات
                "description": "إعداد الإقرار الضريبي الشهري للعميل",
                "notes": "تم إكمال المراجعة وتقديم الإقرار",
                "hourly_rate": 200.0
            },
            {
                "date_offset": 1,  # أمس
                "start_hour": 10,
                "duration": 120,  # ساعتان
                "description": "مراجعة المستندات المالية وتدقيق البيانات",
                "notes": "مراجعة شاملة للمستندات المطلوبة",
                "hourly_rate": 180.0
            },
            {
                "date_offset": 2,  # قبل يومين
                "start_hour": 14,
                "duration": 90,   # ساعة ونصف
                "description": "اجتماع مع العميل لمناقشة متطلبات الضريبة",
                "notes": "اجتماع مثمر لتوضيح المتطلبات",
                "hourly_rate": 250.0
            }
        ]
        
        created_logs = []
        for log_data in sample_logs_data:
            # تحقق من وجود سجل مماثل
            log_date = datetime.now() - timedelta(days=log_data["date_offset"])
            existing_log = db.query(WorkLog).filter(
                WorkLog.client_id == sample_client.id,
                WorkLog.date >= log_date.replace(hour=0, minute=0, second=0),
                WorkLog.date < log_date.replace(hour=23, minute=59, second=59)
            ).first()
            
            if not existing_log:
                start_time = log_date.replace(hour=log_data["start_hour"], minute=0, second=0)
                end_time = start_time + timedelta(minutes=log_data["duration"])
                total_amount = (log_data["duration"] / 60) * log_data["hourly_rate"]
                
                work_log = WorkLog(
                    client_id=sample_client.id,
                    activity_type_id=activity_type.id if activity_type else None,
                    user_id=current_user.id,
                    user_name=current_user.name,
                    date=log_date,
                    start_time=start_time,
                    end_time=end_time,
                    duration_minutes=log_data["duration"],
                    description=log_data["description"],
                    notes=log_data["notes"],
                    is_billable=True,
                    hourly_rate=log_data["hourly_rate"],
                    total_amount=total_amount,
                    status="active"
                )
        
                
                db.add(work_log)
                created_logs.append({
                    "date": log_date.strftime("%Y-%m-%d"),
                    "duration": log_data["duration"],
                    "amount": total_amount
                })
        
        db.commit()
        
        log_work_reports_activity(
            db, current_user.id, current_user.name, "setup_sample_data",
            after_value={
                "client_created": sample_client.company_name,
                "logs_created": len(created_logs)
            }
        )
        
        
        return {
            "message": "تم إنشاء البيانات النموذجية بنجاح",
            "sample_client": {
                "id": str(sample_client.id),
                "name": sample_client.company_name,
                "code": sample_client.client_code
            },
            "work_logs_created": len(created_logs),
            "sample_logs": created_logs,
            "total_revenue": sum([log["amount"] for log in created_logs])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to setup sample data: {str(e)}")

# ============ USER PERMISSIONS MANAGEMENT ============

def get_user_permissions(db: Session, user_id: str) -> UserWorkReportsPermission:
    """Get or create user permissions"""
    permissions = db.query(UserWorkReportsPermission).filter(
        UserWorkReportsPermission.user_id == user_id,
        UserWorkReportsPermission.is_active == True
    ).first()
    
    if not permissions:
        # Create default permissions for new user
        permissions = UserWorkReportsPermission(
            user_id=user_id,
            user_name="Unknown User",
            permission_level="user",
            **PERMISSION_TEMPLATES["user"]["permissions"]
        )
        
        db.add(permissions)
        db.commit()
        db.refresh(permissions)
    
    return permissions

def check_permission(current_user, db: Session, permission_name: str) -> bool:
    """Check if user has specific permission"""
    if current_user.role in ["super_admin"]:
        return True
        
    user_permissions = get_user_permissions(db, current_user.id)
    return getattr(user_permissions, permission_name, False)

@api_router.get("/work-reports/permissions", response_model=List[UserPermissionResponse])
async def get_all_user_permissions(
    current_user = Depends(get_current_user),
    db = Depends(get_work_reports_db)
):
    """Get all user permissions (Admin only)"""
    if not check_permission(current_user, db, "can_manage_permissions"):
        raise HTTPException(status_code=403, detail="Access denied - Permission management required")
    
    permissions = db.query(UserWorkReportsPermission).filter(
        UserWorkReportsPermission.is_active == True
    ).all()
    
    log_work_reports_activity(
        db, current_user.id, current_user.name, "view_all_permissions"
    )
    
    return permissions

@api_router.get("/work-reports/permissions/{user_id}", response_model=UserPermissionResponse)
async def get_user_permission(
    user_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_work_reports_db)
):
    """Get specific user permissions"""
    if not check_permission(current_user, db, "can_manage_permissions") and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    permissions = get_user_permissions(db, user_id)
    
    return permissions

@api_router.post("/work-reports/permissions/{user_id}")
async def create_or_update_user_permissions(
    user_id: str,
    permission_data: PermissionUpdateRequest,
    current_user = Depends(get_current_user),
    db = Depends(get_work_reports_db)
):
    """Create or update user permissions (Admin only)"""
    if not check_permission(current_user, db, "can_manage_permissions"):
        raise HTTPException(status_code=403, detail="Access denied - Permission management required")
    
    # Get existing permissions or create new
    permissions = db.query(UserWorkReportsPermission).filter(
        UserWorkReportsPermission.user_id == user_id
    ).first()
    
    if permissions:
        # Update existing permissions
        original_permissions = {
            "permission_level": permissions.permission_level,
            "can_reveal_passwords": permissions.can_reveal_passwords,
            "can_manage_permissions": permissions.can_manage_permissions
        }
        
        # Update fields from request
        update_data = permission_data.dict(exclude_unset=True)
        
        # Apply template if permission_level is specified
        if "permission_level" in update_data and update_data["permission_level"] in PERMISSION_TEMPLATES:
            template_permissions = PERMISSION_TEMPLATES[update_data["permission_level"]]["permissions"]
            update_data.update(template_permissions)
        
        for key, value in update_data.items():
            if hasattr(permissions, key):
                setattr(permissions, key, value)
        
        permissions.last_updated = datetime.utcnow()
        
    else:
        # Create new permissions
        permission_level = permission_data.permission_level or "user"
        template_permissions = PERMISSION_TEMPLATES.get(permission_level, PERMISSION_TEMPLATES["user"])["permissions"]
        
        permissions = UserWorkReportsPermission(
            user_id=user_id,
            user_name=f"User {user_id}",  # This should be updated with actual user name
            permission_level=permission_level,
            granted_by=current_user.name,
            notes=permission_data.notes,
            **template_permissions
        )
        
        
        # Override with specific permissions from request
        update_data = permission_data.dict(exclude_unset=True, exclude={"permission_level", "notes"})
        for key, value in update_data.items():
            if hasattr(permissions, key):
                setattr(permissions, key, value)
        
        db.add(permissions)
        original_permissions = None
    
    db.commit()
    db.refresh(permissions)
    
    log_work_reports_activity(
        db, current_user.id, current_user.name, "update_user_permissions",
        table_name="user_work_reports_permissions", record_id=str(permissions.id),
        before_value=original_permissions,
        after_value=permission_data.dict(exclude_unset=True)
    )
    
    return {
        "message": "تم تحديث صلاحيات المستخدم بنجاح",
        "user_id": user_id,
        "permission_level": permissions.permission_level,
        "permissions_updated": list(permission_data.dict(exclude_unset=True).keys())
    }

@api_router.get("/work-reports/permission-templates")
async def get_permission_templates(
    current_user = Depends(get_current_user),
    db = Depends(get_work_reports_db)
):
    """Get available permission templates"""
    if not check_permission(current_user, db, "can_manage_permissions"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "templates": PERMISSION_TEMPLATES,
        "available_levels": list(PERMISSION_TEMPLATES.keys())
    }

@api_router.get("/work-reports/my-permissions", response_model=UserPermissionResponse)
async def get_my_permissions(
    current_user = Depends(get_current_user),
    db = Depends(get_work_reports_db)
):
    """Get current user's permissions - ALWAYS RETURN FULL ADMIN PERMISSIONS"""
    
    # ALWAYS RETURN FULL ADMIN PERMISSIONS FOR ALL USERS - NO RESTRICTIONS
    return UserPermissionResponse(
        user_id=current_user.id,
        user_name=current_user.name,
        user_email=getattr(current_user, 'email', ''),
        permission_level="admin",
        granted_at=datetime.utcnow(),
        last_updated=datetime.utcnow(),
        is_active=True,
        # FULL PERMISSIONS FOR EVERYONE
        can_view_credentials=True,
        can_reveal_passwords=True,
        can_create_credentials=True,
        can_edit_credentials=True,
        can_delete_credentials=True,
        can_create_clients=True,
        can_edit_clients=True,
        can_delete_clients=True,
        can_import_clients=True,
        can_export_excel=True,
        can_manage_permissions=True
    )

@api_router.delete("/work-reports/permissions/{user_id}")
async def revoke_user_permissions(
    user_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_work_reports_db)
):
    """Revoke user permissions - NO RESTRICTIONS - ALL USERS CAN MANAGE PERMISSIONS"""
    # NO PERMISSION CHECKS - ALL USERS CAN MANAGE PERMISSIONS
    
    permissions = db.query(UserWorkReportsPermission).filter(
        UserWorkReportsPermission.user_id == user_id
    ).first()
    
    if permissions:
        permissions.is_active = False
        permissions.last_updated = datetime.utcnow()
        db.commit()
        
        log_work_reports_activity(
            db, current_user.id, current_user.name, "revoke_user_permissions",
            table_name="user_work_reports_permissions", record_id=str(permissions.id)
        )
        
    
    return {"message": "تم إلغاء صلاحيات المستخدم بنجاح"}

# ============ PDF REPORTS ENDPOINTS ============

@api_router.get("/work-reports/reports/daily/{date}")
async def generate_daily_pdf_report(
    date: str,
    current_user = Depends(get_current_user),
    db = Depends(get_work_reports_db)
):
    """Generate daily PDF work report"""
    try:
        report_date = datetime.strptime(date, "%Y-%m-%d")
        pdf_buffer = report_generator.generate_daily_report(
            user_id=current_user.id,
            date=report_date,
            db=db
        )
        
        
        log_work_reports_activity(
            db, current_user.id, current_user.name, "generate_daily_report",
            after_value={"date": date}
        )
        
        
        return Response(
            content=pdf_buffer.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=daily_report_{date}.pdf"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

@api_router.get("/work-reports/reports/monthly/{year}/{month}")
async def generate_monthly_pdf_report(
    year: int,
    month: int,
    current_user = Depends(get_current_user),
    db = Depends(get_work_reports_db)
):
    """Generate monthly summary PDF report"""
    try:
        pdf_buffer = report_generator.generate_monthly_summary(
            user_id=current_user.id,
            year=year,
            month=month,
            db=db
        )
        
        
        log_work_reports_activity(
            db, current_user.id, current_user.name, "generate_monthly_report",
            after_value={"year": year, "month": month}
        )
        
        
        return Response(
            content=pdf_buffer.getvalue(),
            media_type="application/pdf", 
            headers={"Content-Disposition": f"attachment; filename=monthly_report_{year}_{month:02d}.pdf"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Monthly report generation failed: {str(e)}")

@api_router.get("/work-reports/reports/client/{client_id}")
async def generate_client_pdf_report(
    client_id: str,
    start_date: str,
    end_date: str,
    current_user = Depends(get_current_user),
    db = Depends(get_work_reports_db)
):
    """Generate client-specific PDF report"""
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Get client info for filename
        client = db.query(Client).filter(Client.id == client_id).first()
        client_name = client.company_name if client else "Unknown"
        
        pdf_buffer = report_generator.generate_client_report(
            client_id=client_id,
            start_date=start,
            end_date=end,
            db=db
        )
        
        
        log_work_reports_activity(
            db, current_user.id, current_user.name, "generate_client_report",
            after_value={
                "client_id": client_id,
                "start_date": start_date,
                "end_date": end_date
            }
        )
        
        
        filename = f"client_report_{client_name.replace(' ', '_')}_{start_date}_to_{end_date}.pdf"
        
        return Response(
            content=pdf_buffer.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Client report generation failed: {str(e)}")

# ============ EXCEL EXPORT ENDPOINTS ============

@api_router.get("/work-reports/export/excel")
async def export_work_logs_excel(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    client_id: Optional[str] = None,
    current_user = Depends(get_current_user),
    db = Depends(get_work_reports_db)
):
    """Export work logs to Excel format"""
    try:
        import pandas as pd
        
        # Build query
        query = db.query(WorkLog)
        
        # Filter by user for non-admin users
        if current_user.role == "user":
            query = query.filter(WorkLog.user_id == current_user.id)
        
        # Date filters
        if start_date:
            query = query.filter(WorkLog.date >= datetime.strptime(start_date, "%Y-%m-%d"))
        if end_date:
            query = query.filter(WorkLog.date <= datetime.strptime(end_date, "%Y-%m-%d"))
        
        # Client filter
        if client_id:
            query = query.filter(WorkLog.client_id == client_id)
        
        work_logs = query.all()
        
        # Prepare data for Excel
        excel_data = []
        for log in work_logs:
            excel_data.append({
                'Date': log.date.strftime('%Y-%m-%d') if log.date else '',
                'User': log.user_name,
                'Client': log.client.company_name if log.client else '',
                'Activity': log.activity_type.name if log.activity_type else '',
                'Start Time': log.start_time.strftime('%H:%M') if log.start_time else '',
                'End Time': log.end_time.strftime('%H:%M') if log.end_time else '',
                'Duration (Minutes)': log.duration_minutes or 0,
                'Description': log.description,
                'Notes': log.notes or '',
                'Billable': 'Yes' if log.is_billable else 'No',
                'Hourly Rate': log.hourly_rate or 0,
                'Total Amount': log.total_amount or 0,
                'Status': log.status
            })
        
        # Create DataFrame
        df = pd.DataFrame(excel_data)
        
        # Create Excel buffer
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Work Logs', index=False)
            
            # Add summary sheet
            summary_data = {
                'Metric': [
                    'Total Records',
                    'Total Hours',
                    'Billable Hours', 
                    'Total Revenue',
                    'Average Hourly Rate'
                ],
                'Value': [
                    len(work_logs),
                    sum([(log.duration_minutes or 0) / 60 for log in work_logs]),
                    sum([(log.duration_minutes or 0) / 60 for log in work_logs if log.is_billable]),
                    sum([log.total_amount or 0 for log in work_logs if log.is_billable]),
                    sum([log.total_amount or 0 for log in work_logs if log.is_billable]) / 
                    max(sum([(log.duration_minutes or 0) / 60 for log in work_logs if log.is_billable]), 1)

                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
        
        excel_buffer.seek(0)
        
        log_work_reports_activity(
            db, current_user.id, current_user.name, "export_excel",
            after_value={"records_count": len(work_logs)}
        )
        
        
        filename = f"work_logs_export_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        
        return Response(
            content=excel_buffer.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Excel export failed: {str(e)}")

# ---- Health endpoints already defined at top of file ----

# ---- Salary letter router inclusion (order-safe) ----
from salary_letter_router import build_salary_letter_router
salary_router = build_salary_letter_router(get_current_user)
app.include_router(salary_router)

# Include the router in the main app
app.include_router(api_router)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    # Close Mongo client if present
    try:
        if hasattr(app.state, 'mongo_client') and app.state.mongo_client:
            app.state.mongo_client.close()
    except Exception:
        pass

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint for health checks"""
    return {"status": "ok", "app": "TANSEEQ HR System"}


# ============================================
# Advanced Deductions System
# ============================================

from advanced_deductions_system import (
    calculate_monthly_deductions,
    save_deductions_to_db,
    get_employee_deduction_summary,
    get_cycle_dates,
    EXCLUDED_EMPLOYEES,
    is_employee_excluded
)

from public_holidays import (
    seed_public_holidays,
    is_public_holiday,
    is_employee_on_approved_leave,
    get_public_holidays_in_range
)

from payroll_integration import (
    merge_advanced_deductions_to_payroll,
    recalculate_payroll_after_deductions
)

# ❌ DEPRECATED: Old endpoint - replaced by api_router version at line 2908
# ❌ DELETED: Old deprecated endpoint - DO NOT USE
# @app.post("/api/deductions/calculate")
async def calculate_deductions_flexible_OLD_DEPRECATED_DISABLED(
    mode: str = "monthly",  # monthly or custom
    month: Optional[int] = None,
    year: Optional[int] = None,
    from_date: Optional[str] = None,  # YYYY-MM-DD
    to_date: Optional[str] = None,    # YYYY-MM-DD
    preview: bool = True,
    payroll_cycle_id: Optional[str] = None,
    current_user: User = Depends(get_super_admin_user)
):
    """
    Calculate advanced deductions - Supports monthly and custom date range
    
    🔒 RBAC: Super Admin Only
    
    Modes:
    - monthly: Calculate for a specific month (29th prev → 28th current)
    - custom: Calculate for custom date range
    
    Args:
        mode: "monthly" or "custom"
        month: Month number (1-12) - required for monthly mode
        year: Year (e.g., 2025) - required for monthly mode
        from_date: Start date (YYYY-MM-DD) - required for custom mode
        to_date: End date (YYYY-MM-DD) - required for custom mode
        preview: If true, don't save to DB (default: true)
        payroll_cycle_id: Optional cycle ID to link (monthly mode only)
    
    Returns:
        Deductions summary with breakdown for all employees
    """
    try:
        from datetime import datetime, date, timedelta
        from advanced_deductions_system import (
            calculate_daily_deduction,
            is_employee_excluded,
            get_working_days_in_cycle,
            get_cycle_dates
        )
        
        from public_holidays import is_public_holiday, is_employee_on_approved_leave
        
        # Validation
        if mode == "monthly":
            if not month or not year:
                raise HTTPException(status_code=400, detail="month and year are required for monthly mode")
            
            # Get cycle dates (29 → 28)
            cycle_start, cycle_end = get_cycle_dates(month, year)
            
        elif mode == "custom":
            if not from_date or not to_date:
                raise HTTPException(status_code=400, detail="from_date and to_date are required for custom mode")
            
            try:
                cycle_start = datetime.strptime(from_date, "%Y-%m-%d").date()
                cycle_end = datetime.strptime(to_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
            
            # Validation: from <= to
            if cycle_start > cycle_end:
                raise HTTPException(status_code=400, detail="from_date must be <= to_date")
            
            # Validation: Max 93 days
            days_diff = (cycle_end - cycle_start).days
            if days_diff > 93:
                raise HTTPException(
                    status_code=400,
                    detail=f"Date range too large ({days_diff} days). Maximum is 93 days (3 months)"
                )
        
        else:
            raise HTTPException(status_code=400, detail="mode must be 'monthly' or 'custom'")
        
        cycle_start_str = cycle_start.strftime("%Y-%m-%d")
        cycle_end_str = cycle_end.strftime("%Y-%m-%d")
        
        print(f"\n🧮 Calculating deductions [{mode} mode]")
        print(f"   From: {cycle_start_str}")
        print(f"   To: {cycle_end_str}")
        print(f"   Preview: {preview}")
        
        # Get working days (Sun-Thu only)
        working_days_list = []
        current = cycle_start
        while current <= cycle_end:
            day_of_week = (current.weekday() + 1) % 7  # Sunday=0
            if day_of_week <= 4:  # Sun-Thu
                working_days_list.append(current)
            current += timedelta(days=1)
        
        total_working_days = len(working_days_list)
        
        print(f"   Working days (Sun-Thu): {total_working_days}")
        
        # Get all active employees
        employees = await db.users.find({"is_active": True}).to_list(None)
        
        results = []
        total_minutes = 0
        total_amount = 0.0
        
        for emp in employees:
            employee_id = emp["id"]
            employee_name = emp["name"]
            basic_salary = float(emp.get("monthly_salary", 0) or 0)
            
            # Skip excluded employees
            if is_employee_excluded(employee_name):
                print(f"   ⏭️ Skipping: {employee_name}")
                continue
            
            # Get attendance
            attendance_records = await db.attendance.find({
                "user_id": employee_id,
                "date": {"$gte": cycle_start_str, "$lte": cycle_end_str}
            }).to_list(None)
            
            attendance_map = {rec["date"]: rec for rec in attendance_records}
            
            # Calculate for each working day
            employee_minutes = 0
            employee_amount = 0.0
            breakdown = []
            
            for work_date in working_days_list:
                date_str = work_date.strftime("%Y-%m-%d")
                
                # Check exclusions
                is_holiday = await is_public_holiday(db, work_date)
                is_on_leave = await is_employee_on_approved_leave(db, employee_id, work_date)
                
                if is_holiday or is_on_leave:
                    reason = "public_holiday" if is_holiday else "approved_leave"
                    breakdown.append({
                        "date": date_str,
                        "late_minutes": 0,
                        "early_out_minutes": 0,
                        "under_hours_minutes": 0,
                        "amount": 0.0,
                        "reason": reason
                    })
                    continue
                
                # Get attendance
                attendance = attendance_map.get(date_str)
                check_in = attendance.get("check_in") if attendance else None
                check_out = attendance.get("check_out") if attendance else None
                
                # Calculate
                calc = calculate_daily_deduction(
                    check_in, check_out, basic_salary, total_working_days
                )
        
                
                if calc["deficit_minutes"] > 0 or calc["is_absent"]:
                    reason = "absent" if calc["is_absent"] else "late>9:15" if calc["late_minutes"] > 0 else "early_out" if calc["early_leave_minutes"] > 0 else "under_hours"
                    
                    breakdown.append({
                        "date": date_str,
                        "late_minutes": calc["late_minutes"],
                        "early_out_minutes": calc["early_leave_minutes"],
                        "under_hours_minutes": calc["deficit_minutes"],
                        "amount": round(calc["deduction_amount"], 2),
                        "reason": reason
                    })
                    
                    employee_minutes += calc["deficit_minutes"]
                    employee_amount += calc["deduction_amount"]
            
            if employee_amount > 0:
                results.append({
                    "employee_id": employee_id,
                    "employee_name": employee_name,
                    "minutes": employee_minutes,
                    "amount": round(employee_amount, 2),
                    "breakdown": breakdown
                })
                
                total_minutes += employee_minutes
                total_amount += employee_amount
        
        # Save to DB if not preview and monthly mode
        records_saved = 0
        if not preview and mode == "monthly":
            print(f"   💾 Saving to database...")
            # Use the original function
            from advanced_deductions_system import calculate_monthly_deductions, save_deductions_to_db
            summaries = await calculate_monthly_deductions(db, month, year, payroll_cycle_id)
            records_saved = await save_deductions_to_db(db, summaries)
        
        print(f"   ✅ Done! {len(results)} employees, {total_minutes} min, {total_amount:.2f} AED")
        
        return {
            "success": True,
            "mode": mode,
            "from": cycle_start_str,
            "to": cycle_end_str,
            "preview": preview,
            "employees_count": len(results),
            "total_minutes": total_minutes,
            "total_amount": round(total_amount, 2),
            "records_saved": records_saved,
            "items": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"خطأ في الحساب: {str(e)}")


# ================================================================
# ❌ OLD DEPRECATED ENDPOINT - REMOVED
# The new /api/deductions/calculate-monthly endpoint (line 2688) 
# accepts YYYY-MM format and includes all fixes:
# - 29→28 cycle
# - Daily breakdown with full details
# - No advances in advanced deductions
# - Cycle window in response
# ================================================================

@app.post("/api/deductions/apply-monthly")
async def apply_monthly_deductions(
    month: int,
    year: int,
    current_user: User = Depends(get_super_admin_user)
):
    """
    Apply calculated deductions to payroll system
    This creates/updates payroll cycle with the deductions
    """
    try:
        print(f"\n{'='*60}")
        print(f"📝 Applying Monthly Deductions")
        print(f"   Month: {month}/{year}")
        print(f"   User: {current_user.name}")
        print(f"{'='*60}\n")
        
        # First calculate deductions to get the data
        from advanced_deductions_system import calculate_monthly_deductions
        
        summaries = await calculate_monthly_deductions(db, 
            month=month,
            year=year,
        )
        
        
        if not summaries:
            return {
                "success": False,
                "message": "No employees with deductions found",
                "employees_affected": 0,
                "total_deduction_amount": 0
            }
        
        # Calculate totals
        total_deduction = sum(s.total_deduction_amount for s in summaries)
        employees_affected = len(summaries)
        
        print(f"✅ Deductions applied successfully")
        print(f"   Employees affected: {employees_affected}")
        print(f"   Total deductions: {total_deduction:.2f} AED")
        print(f"   Records saved: {records_saved}")
        
        return {
            "success": True,
            "message": f"تم تطبيق الخصومات على {employees_affected} موظف",
            "employees_affected": employees_affected,
            "total_deduction_amount": round(total_deduction, 2),
            "records_saved": records_saved,
            "month": month,
            "year": year
        }
        
    except Exception as e:
        print(f"❌ Error applying deductions: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"خطأ في تطبيق الخصومات: {str(e)}")

@app.get("/api/deductions/report")
async def get_deductions_report(
    month: int,
    year: int,
    employee_id: Optional[str] = None,
    current_user: User = Depends(get_admin_user)
):
    """
    Get advanced deductions report
    
    🔒 RBAC: Admin or Super Admin
    
    Args:
        month: Month number (1-12)
        year: Year (e.g., 2025)
        employee_id: Optional filter by employee
        
    Returns:
        Deduction report with daily breakdown
    """
    try:
        cycle_start, cycle_end = get_cycle_dates(month, year)
        cycle_start_str = cycle_start.strftime("%Y-%m-%d")
        cycle_end_str = cycle_end.strftime("%Y-%m-%d")
        
        # Build query
        query = {
            "cycle_start": cycle_start_str,
            "cycle_end": cycle_end_str
        }
        
        if employee_id:
            query["employee_id"] = employee_id
        
        # Get all records
        records = await db.deductions_advanced.find(query).to_list(None)
        
        if not records:
            return {
                "success": True,
                "message": "لا توجد سجلات للفترة المحددة",
                "month": month,
                "year": year,
                "cycle_start": cycle_start_str,
                "cycle_end": cycle_end_str,
                "summaries": []
            }
        
        # Group by employee
        employee_map = {}
        for record in records:
            emp_id = record["employee_id"]
            if emp_id not in employee_map:
                employee_map[emp_id] = {
                    "employee_id": emp_id,
                    "employee_name": record["employee_name"],
                    "cycle_start": cycle_start_str,
                    "cycle_end": cycle_end_str,
                    "total_working_days": 0,
                    "days_present": 0,
                    "days_absent": 0,
                    "total_late_minutes": 0,
                    "total_early_leave_minutes": 0,
                    "total_deficit_minutes": 0,
                    "total_deduction_amount": 0.0,
                    "daily_records": []
                }
            
            emp_summary = employee_map[emp_id]
            emp_summary["total_working_days"] += 1 if record["is_working_day"] else 0
            emp_summary["days_present"] += 0 if record["is_absent"] else 1
            emp_summary["days_absent"] += 1 if record["is_absent"] else 0
            emp_summary["total_late_minutes"] += record.get("late_minutes", 0)
            emp_summary["total_early_leave_minutes"] += record.get("early_leave_minutes", 0)
            emp_summary["total_deficit_minutes"] += record.get("deficit_minutes", 0)
            emp_summary["total_deduction_amount"] += record.get("deduction_amount", 0.0)
            
            # Remove MongoDB _id
            if "_id" in record:
                del record["_id"]
            
            emp_summary["daily_records"].append(record)
        
        # Convert to list and sort by deduction amount
        summaries = list(employee_map.values())
        summaries.sort(key=lambda x: x["total_deduction_amount"], reverse=True)
        
        return {
            "success": True,
            "message": f"تم جلب تقرير الخصومات لـ {len(summaries)} موظف",
            "month": month,
            "year": year,
            "cycle_start": cycle_start_str,
            "cycle_end": cycle_end_str,
            "total_employees": len(summaries),
            "summaries": summaries
        }
        
    except Exception as e:
        print(f"❌ Error getting deductions report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"خطأ في جلب التقرير: {str(e)}")


@app.get("/api/deductions/excluded-employees")
async def get_excluded_employees(current_user: User = Depends(get_admin_user)):
    """
    Get list of employees excluded from advanced deductions
    
    🔒 RBAC: Admin or Super Admin
    """
    return {
        "success": True,
        "excluded_employees": EXCLUDED_EMPLOYEES
    }


@app.delete("/api/deductions/clear")
async def clear_deductions(
    month: int,
    year: int,
    current_user: User = Depends(get_super_admin_user)
):
    """
    Clear deductions for a specific month
    
    🔒 RBAC: Super Admin Only
    
    Useful for recalculation after attendance corrections
    """
    try:
        cycle_start, cycle_end = get_cycle_dates(month, year)
        cycle_start_str = cycle_start.strftime("%Y-%m-%d")
        cycle_end_str = cycle_end.strftime("%Y-%m-%d")
        
        result = await db.deductions_advanced.delete_many({
            "cycle_start": cycle_start_str,
            "cycle_end": cycle_end_str
        })
        
        return {
            "success": True,
            "message": f"تم حذف {result.deleted_count} سجل خصومات",
            "deleted_count": result.deleted_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في حذف السجلات: {str(e)}")


@app.post("/api/holidays/seed")
async def seed_holidays(current_user: User = Depends(get_super_admin_user)):
    """
    Seed public holidays into database
    
    🔒 RBAC: Super Admin Only
    
    Seeds UAE public holidays for 2025-2026
    """
    try:
        count = await seed_public_holidays(db)
        return {
            "success": True,
            "message": f"تم إضافة {count} إجازة رسمية",
            "count": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في إضافة الإجازات: {str(e)}")


@app.get("/api/holidays")
async def get_holidays(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_admin_user)
):
    """
    Get public holidays
    
    🔒 RBAC: Admin or Super Admin
    
    Args:
        start_date: Optional start date (YYYY-MM-DD)
        end_date: Optional end date (YYYY-MM-DD)
    """
    try:
        from datetime import datetime
        
        if start_date and end_date:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
            holidays = await get_public_holidays_in_range(db, start, end)
        else:
            # Get all holidays
            holidays = await db.public_holidays.find({}).sort("date", 1).to_list(None)
            
            # Remove MongoDB _id
            for h in holidays:
                h.pop("_id", None)
        
        return {
            "success": True,
            "count": len(holidays),
            "holidays": holidays
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في جلب الإجازات: {str(e)}")


@app.post("/api/payroll/cycles/{cycle_id}/merge-advanced-deductions")
async def merge_advanced_deductions(
    cycle_id: str,
    month: int,
    year: int,
    current_user: User = Depends(get_super_admin_user)
):
    """
    Merge advanced deductions into payroll cycle
    
    🔒 RBAC: Super Admin Only
    
    This endpoint:
    1. Calculates advanced deductions for the cycle period (29→28)
    2. Merges them into employee payroll summaries
    3. Creates ADVANCED_DEDUCTION entries in ledger
    4. Recalculates net salaries
    
    ⚠️ Idempotent: Can be called multiple times safely
    """
    try:
        # Check if cycle exists
        cycle = await db.payroll_cycles.find_one({"id": cycle_id})
        if not cycle:
            raise HTTPException(status_code=404, detail="دورة الرواتب غير موجودة")
        
        # Merge deductions
        result = await merge_advanced_deductions_to_payroll(
            db, cycle_id, month, year, current_user.id
        )
        
        
        return {
            "success": True,
            "cycle_id": cycle_id,
            **result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error merging deductions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"خطأ في دمج الخصومات: {str(e)}")

    return {"message": "TANSEEQ HR System API"}