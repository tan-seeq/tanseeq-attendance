from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Form, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
import pyotp
import qrcode
from io import BytesIO
import base64
from datetime import datetime, timedelta, time
from jose import JWTError, jwt
import os
import logging
import uuid
import bcrypt
import pytz
import shutil
from pathlib import Path
import requests
import openpyxl
from io import BytesIO

# Import Work Reports Database Module
from work_reports_db import (
    get_work_reports_db, create_work_reports_tables, init_default_activity_types,
    Client, ClientCredential, ActivityType, WorkLog, WorkReportsAuditLog,
    UserWorkReportsPermission, PERMISSION_TEMPLATES,
    ClientCreate, ClientUpdate, ClientResponse,
    ClientCredentialCreate, ClientCredentialResponse,
    ActivityTypeCreate, ActivityTypeResponse,
    WorkLogCreate, WorkLogUpdate, WorkLogResponse,
    UserPermissionResponse, PermissionUpdateRequest,
    credential_encryption, log_work_reports_activity
)
from sqlalchemy.orm import Session
from report_generator import report_generator

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Security
security = HTTPBearer()

# Create the main app
app = FastAPI(title="TANSEEQ HR System", version="1.0.0")

# Create uploads directory
uploads_dir = ROOT_DIR / "uploads"
uploads_dir.mkdir(exist_ok=True)

# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

# Create router with /api prefix
api_router = APIRouter(prefix="/api")

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
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
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

@api_router.post("/attendance/check-in")
async def check_in(current_user: User = Depends(get_current_user)):
    """Check in (Normal attendance without QR verification)"""
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
    
    # Determine if late based on user's schedule
    is_late = False
    if current_user.has_flexible_schedule:
        # Flexible schedule - check against flexible start range
        flexible_start = current_user.flexible_start_range or "07:00-11:00"
        _, latest_start = flexible_start.split('-')
        latest_hour, latest_minute = map(int, latest_start.split(':'))
        if current_time.hour > latest_hour or (current_time.hour == latest_hour and current_time.minute > latest_minute):
            is_late = True
    else:
        # Fixed schedule - check against working_hours_start
        start_time = datetime.strptime(current_user.working_hours_start, '%H:%M').time()
        if current_time.time() > start_time:
            is_late = True
    
    # Create or update attendance record
    attendance_data = {
        "user_id": current_user.id,
        "user_name": current_user.name,
        "date": today,
        "check_in": check_in_time,
        "status": "late" if is_late else "present",
        "is_late": is_late
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
        attendance_data["created_at"] = datetime.utcnow()
        await db.attendance.insert_one(attendance_data)
        attendance_id = attendance_record.id
    
    # Log activity
    await log_activity(current_user.id, "check_in", f"Checked in at {check_in_time}")
    
    return {
        "message": "تم تسجيل الحضور بنجاح ✅",
        "check_in_time": check_in_time,
        "status": "متأخر" if is_late else "في الوقت",
        "is_late": is_late
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
    
    # Calculate working hours
    check_in_str = existing_attendance.get("check_in")
    if check_in_str:
        check_in_time = datetime.strptime(f"{today} {check_in_str}", "%Y-%m-%d %H:%M:%S")
        check_out_time_dt = datetime.strptime(f"{today} {check_out_time}", "%Y-%m-%d %H:%M:%S")
        working_hours = (check_out_time_dt - check_in_time).total_seconds() / 3600
    else:
        working_hours = 0
    
    # Update attendance record
    await db.attendance.update_one(
        {"user_id": current_user.id, "date": today},
        {"$set": {
            "check_out": check_out_time,
            "working_hours": round(working_hours, 2)
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
    """User login"""
    user = await db.users.find_one({"email": request.email})
    if not user or not verify_password(request.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive"
        )
    
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
async def reset_password(request: PasswordResetRequest, current_user: User = Depends(get_super_admin_user)):
    """Reset user password (Super admin only)"""
    user = await db.users.find_one({"email": request.email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    hashed_password = hash_password(request.new_password)
    await db.users.update_one(
        {"email": request.email},
        {"$set": {"password": hashed_password}}
    )
    
    await log_activity(current_user.id, "password_reset", f"Reset password for {request.email}")
    
    return {"message": "Password reset successfully"}

# ============ USER ENDPOINTS ============

@api_router.get("/users", response_model=List[UserResponse])
async def get_users(current_user: User = Depends(get_admin_user)):
    """Get all users (Admin only)"""
    users = await db.users.find().to_list(1000)
    return [UserResponse(**user) for user in users]

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
    """Get attendance records"""
    query = {}
    if current_user.role == "user":
        query["user_id"] = current_user.id
    
    attendance_records = await db.attendance.find(query).to_list(1000)
    
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
    
    # Handle time updates
    check_in_updated = "check_in" in update_data
    check_out_updated = "check_out" in update_data
    
    if check_in_updated:
        update_fields["check_in"] = update_data["check_in"]
        changes.append(f"check_in: {update_data['check_in']}")
    
    if check_out_updated:
        update_fields["check_out"] = update_data["check_out"]
        changes.append(f"check_out: {update_data['check_out']}")
    
    # Calculate working hours if both times are available
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
            
            check_in_time = datetime.strptime(check_in_str, "%H:%M:%S")
            check_out_time = datetime.strptime(check_out_str, "%H:%M:%S")
            
            # Handle overnight shifts
            if check_out_time < check_in_time:
                check_out_time += timedelta(days=1)
            
            working_hours = (check_out_time - check_in_time).total_seconds() / 3600
            update_fields["working_hours"] = round(working_hours, 2)
            changes.append(f"working_hours: {working_hours:.2f}")
            
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

@api_router.post("/attendance/check-in")
async def check_in(current_user: User = Depends(get_current_user)):
    """Check in attendance - with enhanced flexibility"""
    uae_time = get_uae_time()
    date_str = uae_time.strftime("%Y-%m-%d")
    time_str = uae_time.strftime("%H:%M:%S")
    
    # Check if it's weekend
    is_weekend = uae_time.weekday() >= 5  # Saturday=5, Sunday=6
    
    # Check if already checked in today
    existing_attendance = await db.attendance.find_one({"user_id": current_user.id, "date": date_str})
    if existing_attendance and existing_attendance.get("check_in"):
        raise HTTPException(status_code=400, detail="Already checked in today")
    
    # Get user details for flexible schedule
    user_details = await db.users.find_one({"id": current_user.id})
    has_flexible_schedule = user_details.get("has_flexible_schedule", False)
    
    # Default status
    status = "present"
    is_late = False
    
    # Check if late based on flexible schedule or fixed rules
    if not is_weekend:
        if has_flexible_schedule:
            # For flexible schedule users - very lenient rules
            flexible_start_range = user_details.get("flexible_start_range", "07:00-11:00")
            start_time, end_time = flexible_start_range.split("-")
            start_hour, start_minute = map(int, start_time.split(":"))
            end_hour, end_minute = map(int, end_time.split(":"))
            
            # Only mark as late if they come after the flexible end time
            if uae_time.hour > end_hour or (uae_time.hour == end_hour and uae_time.minute > end_minute):
                is_late = True
                status = "late"
        else:
            # Fixed schedule rules (legacy)
            if current_user.name == "Hatem Mohamed Ahmed":
                # Hatem has no time restrictions
                pass
            elif current_user.name == "Tarek Wazzan":
                # Tarek can start from 8 AM
                if uae_time.hour > 8 or (uae_time.hour == 8 and uae_time.minute > 0):
                    is_late = True
                    status = "late"
            else:
                # Others should be here by 9 AM
                if uae_time.hour > 9 or (uae_time.hour == 9 and uae_time.minute > 0):
                    is_late = True
                    status = "late"
    
    # Create attendance record
    attendance_data = {
        "id": str(uuid.uuid4()),
        "user_id": current_user.id,
        "user_name": current_user.name,
        "date": date_str,
        "check_in": time_str,
        "check_out": None,
        "working_hours": None,
        "status": status,
        "is_late": is_late,
        "is_weekend": is_weekend,
        "schedule_type": "flexible" if has_flexible_schedule else "fixed",
        "flexible_schedule": has_flexible_schedule,
        "created_at": datetime.utcnow()
    }
    
    if existing_attendance:
        # Update existing record
        await db.attendance.update_one(
            {"user_id": current_user.id, "date": date_str},
            {"$set": attendance_data}
        )
    else:
        # Create new record
        await db.attendance.insert_one(attendance_data)
    
    await log_activity(current_user.id, "check_in", f"Checked in at {time_str} ({'flexible' if has_flexible_schedule else 'fixed'} schedule)")
    
    return {
        "message": "Checked in successfully", 
        "time": time_str, 
        "is_late": is_late, 
        "schedule_type": attendance_data["schedule_type"],
        "flexible_schedule": has_flexible_schedule
    }

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
    """Delete absence record (Super Admin only)"""
    attendance = await db.attendance.find_one({"id": attendance_id})
    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    
    # Only allow deletion of absent records or manually created entries
    if attendance.get("status") != "absent" and not attendance.get("is_manual_entry"):
        raise HTTPException(status_code=400, detail="Can only delete absence records or manually created entries")
    
    # Delete the record
    await db.attendance.delete_one({"id": attendance_id})
    
    await log_activity(
        current_user.id, 
        "absence_deleted", 
        f"Deleted absence record for {attendance.get('user_name')} on {attendance.get('date')}"
    )
    
    return {"message": "Absence record deleted successfully"}

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

@api_router.post("/field-exits/{field_exit_id}/end")
async def end_field_exit(field_exit_id: str, current_user: User = Depends(get_current_user)):
    """Record actual return time"""
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
    
    # Get current UAE time
    uae_time = datetime.now(UAE_TZ)
    actual_end_time = uae_time.strftime("%H:%M:%S")
    
    # Update field exit with actual end time
    await db.field_exits.update_one(
        {"id": field_exit_id},
        {"$set": {
            "actual_end_time": actual_end_time,
            "exit_status": "returned"
        }}
    )
    
    # Log activity
    await log_activity(
        current_user.id, 
        "field_exit_returned", 
        f"Returned from {field_exit.get('visit_type', 'Unknown')} at {actual_end_time}"
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
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=10,
            alignment=1,  # Center alignment
            textColor=colors.Color(0.12, 0.31, 0.47)  # Dark blue
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
    """Calculate payroll for a specific month with automatic deductions (Admin only)"""
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
        
        # Calculate working days and hours
        working_days = len([a for a in attendance_records if a.get("check_in")])
        total_hours = sum([a.get("working_hours", 0) for a in attendance_records if a.get("working_hours")])
        late_days = len([a for a in attendance_records if a.get("is_late")])
        
        # Calculate basic salary based on daily rate
        calculated_salary = working_days * user["daily_rate"]
        basic_salary = min(calculated_salary, user["monthly_salary"])
        
        # Calculate automatic deductions with complex rules
        total_deductions = 0.0
        deduction_details = []
        late_penalty_details = []
        absence_penalty_details = []
        
        # 1. Late arrival penalties with complex rules
        late_records = [a for a in attendance_records if a.get("is_late")]
        
        if late_records:
            # Group late records by minutes
            late_minutes_list = []
            for record in late_records:
                check_in_str = record.get("check_in", "09:00:00")
                try:
                    check_in_time = datetime.strptime(check_in_str, "%H:%M:%S").time()
                    if user.get("has_flexible_schedule"):
                        # For flexible schedule, calculate against 11:00 AM (latest allowed start)
                        standard_start = datetime.strptime("11:00:00", "%H:%M:%S").time()
                    else:
                        # For fixed schedule, use working_hours_start
                        standard_start = datetime.strptime(user.get("working_hours_start", "09:00"), "%H:%M").time()
                    
                    # Calculate late minutes
                    check_in_dt = datetime.combine(datetime.min, check_in_time)
                    standard_dt = datetime.combine(datetime.min, standard_start)
                    
                    if check_in_dt > standard_dt:
                        late_minutes = (check_in_dt - standard_dt).total_seconds() / 60
                        late_minutes_list.append(late_minutes)
                except:
                    continue
            
            if late_minutes_list:
                # Apply complex penalty rules
                total_late_minutes = sum(late_minutes_list)
                free_late_count = 0
                penalty_minutes = 0
                half_day_penalties = 0
                full_day_penalties = 0
                
                for minutes in late_minutes_list:
                    if minutes <= 15:
                        # First 15 minutes x 4 times are free
                        if free_late_count < 4:
                            free_late_count += 1
                        else:
                            penalty_minutes += minutes
                    elif minutes <= 20:
                        # 15-20 minutes: accumulate for deduction
                        penalty_minutes += minutes
                    elif minutes <= 120:  # 20 minutes to 2 hours
                        # More than 20 minutes but less than 2 hours: half day
                        half_day_penalties += 1
                        penalty_minutes += minutes  # Also accumulate the minutes
                    else:  # More than 2 hours
                        # More than 2 hours: full day
                        full_day_penalties += 1
                
                # Calculate penalties
                # 1. Accumulated minutes penalty (convert to daily rate fraction)
                if penalty_minutes > 0:
                    minutes_penalty = (penalty_minutes / (8 * 60)) * user["daily_rate"]  # 8 hours = full day
                    total_deductions += minutes_penalty
                    late_penalty_details.append(f"Late Minutes: {penalty_minutes:.0f} min = AED {minutes_penalty:.2f}")
                
                # 2. Half day penalties
                if half_day_penalties > 0:
                    half_day_penalty = half_day_penalties * (user["daily_rate"] / 2)
                    total_deductions += half_day_penalty
                    late_penalty_details.append(f"Half Day Penalties: {half_day_penalties} × AED {user['daily_rate']/2:.2f} = AED {half_day_penalty:.2f}")
                
                # 3. Full day penalties
                if full_day_penalties > 0:
                    full_day_penalty = full_day_penalties * user["daily_rate"]
                    total_deductions += full_day_penalty
                    late_penalty_details.append(f"Full Day Penalties: {full_day_penalties} × AED {user['daily_rate']:.2f} = AED {full_day_penalty:.2f}")
                
                # Summary for late penalties
                if late_penalty_details:
                    deduction_details.extend(late_penalty_details)
        
        # 2. Absence penalties (2 days salary for each unauthorized absence)
        total_days_in_month = 30  # Simplified
        expected_working_days = total_days_in_month  # Assuming all days are working days
        
        # Get approved leaves for this month
        month_start = f"{month}-01"
        month_end = f"{month}-31"
        leaves = await db.leaves.find({
            "user_id": user["id"],
            "status": "approved",
            "$or": [
                {"start_date": {"$gte": month_start, "$lte": month_end}},
                {"end_date": {"$gte": month_start, "$lte": month_end}},
                {"start_date": {"$lte": month_start}, "end_date": {"$gte": month_end}}
            ]
        }).to_list(100)
        
        # Calculate approved leave days in this month
        approved_leave_days = 0
        for leave in leaves:
            start_date = max(leave.get("start_date", month_start), month_start)
            end_date = min(leave.get("end_date", month_end), month_end)
            
            if start_date <= end_date:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                days_in_month = (end_dt - start_dt).days + 1
                approved_leave_days += days_in_month
        
        # Get approved field exits for this month  
        field_exits = await db.field_exits.find({
            "user_id": user["id"],
            "status": "approved",
            "date": {"$regex": f"^{month}"}
        }).to_list(100)
        
        approved_field_exit_days = len(field_exits)
        
        # Calculate unauthorized absences
        actual_absences = max(0, expected_working_days - working_days - approved_leave_days - approved_field_exit_days)
        
        if actual_absences > 0:
            # Each unauthorized absence = 2 days salary deduction
            absence_penalty = actual_absences * 2 * user["daily_rate"]
            total_deductions += absence_penalty
            absence_penalty_details.append(f"Unauthorized Absences: {actual_absences} days × 2 × AED {user['daily_rate']:.2f} = AED {absence_penalty:.2f}")
            deduction_details.extend(absence_penalty_details)
        
        # 3. Get existing penalty records from late_penalties collection
        existing_penalties = await db.late_penalties.find({
            "user_id": user["id"],
            "month": month,
            "status": "applied"
        }).to_list(100)
        
        existing_penalty_amount = sum(p.get("penalty_amount", 0) for p in existing_penalties)
        if existing_penalty_amount > 0:
            total_deductions += existing_penalty_amount
            deduction_details.append(f"Applied Penalties: AED {existing_penalty_amount:.2f}")
        
        # Calculate final salary after deductions
        final_salary = max(0, basic_salary - total_deductions)  # Cannot be negative
        
        # Separate late and absence deductions for reporting
        late_deductions = 0.0
        absence_deductions = 0.0
        
        # Calculate late deductions total
        for detail in late_penalty_details:
            if "Late Minutes:" in detail or "Half Day Penalties:" in detail or "Full Day Penalties:" in detail:
                try:
                    # Extract AED amount from detail string
                    amount_str = detail.split("AED ")[1].split()[0]
                    late_deductions += float(amount_str)
                except:
                    pass
        
        # Calculate absence deductions total  
        for detail in absence_penalty_details:
            if "Unauthorized Absences:" in detail:
                try:
                    # Extract AED amount from detail string
                    amount_str = detail.split("AED ")[1].split()[0]
                    absence_deductions += float(amount_str)
                except:
                    pass
        
        # Translation for English reports
        english_name = translate_to_english(user["name"])
        english_position = translate_to_english(user["position"])
        
        payroll_data.append({
            "user_id": user["id"],
            "name": english_name,  # English translation
            "arabic_name": user["name"],  # Keep original Arabic
            "position": english_position,  # English translation
            "arabic_position": user["position"],  # Keep original Arabic
            "monthly_salary": user["monthly_salary"],
            "daily_rate": user["daily_rate"],
            "working_days": working_days,
            "total_hours": round(total_hours, 2),
            "late_days": late_days,
            "approved_leaves": approved_leave_days,
            "approved_field_exits": approved_field_exit_days,
            "unauthorized_absences": max(actual_absences, 0),
            "basic_salary": round(basic_salary, 2),
            "late_deductions": round(late_deductions, 2),
            "absence_deductions": round(absence_deductions, 2),
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
            "Employee Name", "Working Days", "Basic Salary", "Late Days", 
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
                f"AED {emp['basic_salary']:.2f}",
                emp["late_days"],
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
        summary_cell.value = f"Total Employees: {len(payroll_data)} | Total Basic Salary: AED {sum(emp['basic_salary'] for emp in payroll_data):.2f} | Total Deductions: AED {sum(emp['total_deductions'] for emp in payroll_data):.2f} | Net Payroll: AED {sum(emp['final_salary'] for emp in payroll_data):.2f}"
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
            "Employee Name", "Monthly Salary", "Working Days", "Total Hours", "Late Days", 
            "Basic Salary", "Late Deductions", "Absence Deductions", "Total Deductions", "Final Salary"
        ]
        headers_ar = [
            "اسم الموظف", "الراتب الشهري", "أيام العمل", "إجمالي الساعات", "الأيام المتأخرة",
            "الراتب الأساسي", "خصومات التأخير", "خصومات الغياب", "إجمالي الخصومات", "الراتب النهائي"
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
                str(employee.get("late_days", 0)),
                f"AED {employee['basic_salary']:.2f}",
                f"AED {employee.get('late_deductions', 0):.2f}",
                f"AED {employee.get('absence_deductions', 0):.2f}",
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
        table_data = [["Employee", "Monthly\nSalary", "Basic\nSalary", "Late\nDeductions", "Absence\nDeductions", "Total\nDeductions", "Final\nSalary"]]
        for employee in payroll_data:
            table_data.append([
                employee["name"][:15],  # Truncate long names for better fit
                f"AED\n{employee['monthly_salary']:.0f}",
                f"AED\n{employee['basic_salary']:.0f}",
                f"AED\n{employee.get('late_deductions', 0):.0f}",
                f"AED\n{employee.get('absence_deductions', 0):.0f}",
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
        total_basic_salary = sum(emp['basic_salary'] for emp in payroll_data)
        total_deductions = sum(emp.get('total_deductions', 0) for emp in payroll_data)
        total_final_salary = sum(emp['final_salary'] for emp in payroll_data)
        
        summary_text = f"""
        <b>Summary | الملخص</b><br/>
        Total Employees: {len(payroll_data)} | إجمالي الموظفين<br/>
        Total Monthly Salaries: AED {total_monthly_salary:.2f} | إجمالي الرواتب الشهرية<br/>
        Total Basic Salaries: AED {total_basic_salary:.2f} | إجمالي الرواتب الأساسية<br/>
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
        
        BACKUP_DIR = "/app/backups"
        Path(BACKUP_DIR).mkdir(exist_ok=True)
        
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
        
        BACKUP_DIR = "/app/backups"
        Path(BACKUP_DIR).mkdir(exist_ok=True)
        
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
                "database": "tanseeq_hr",
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
                except Exception as e:
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

@api_router.on_event("startup")
async def startup_work_reports():
    """Initialize Work Reports database and default data"""
    try:
        # Create tables
        create_work_reports_tables()
        
        # Initialize default activity types
        from sqlalchemy.orm import sessionmaker
        from work_reports_db import engine
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        init_default_activity_types(db)
        db.close()
        
        logger.info("Work Reports module initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Work Reports module: {str(e)}")

# ============ CLIENT MANAGEMENT ENDPOINTS ============

@api_router.get("/work-reports/clients", response_model=List[ClientResponse])
async def get_clients(
    current_user = Depends(get_current_user),
    db = Depends(get_work_reports_db)
):
    """Get all clients"""
    clients = db.query(Client).filter(Client.is_active == True).all()
    
    log_work_reports_activity(
        db, current_user.id, current_user.name, "view_clients"
    )
    
    return clients

@api_router.post("/work-reports/clients", response_model=ClientResponse)
async def create_client(
    client_data: ClientCreate,
    current_user = Depends(get_current_user),
    db = Depends(get_work_reports_db)
):
    """Create new client"""
    # Generate client code if not provided
    if not client_data.client_code:
        company_initials = ''.join([word[0].upper() for word in client_data.company_name.split()[:3]])
        timestamp = datetime.now().strftime("%y%m")
        client_data.client_code = f"{company_initials}{timestamp}"
    
    # Check for duplicate client code
    existing_client = db.query(Client).filter(Client.client_code == client_data.client_code).first()
    if existing_client:
        raise HTTPException(status_code=400, detail="Client code already exists")
    
    # Create client
    client = Client(
        **client_data.dict(),
        created_by=current_user.name
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    
    log_work_reports_activity(
        db, current_user.id, current_user.name, "create_client",
        table_name="clients", record_id=str(client.id),
        after_value=client_data.dict()
    )
    
    return client

@api_router.put("/work-reports/clients/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: str,
    client_update: ClientUpdate,
    current_user = Depends(get_current_user),
    db = Depends(get_work_reports_db)
):
    """Update client information"""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Store original values for audit
    original_data = {
        "company_name": client.company_name,
        "client_code": client.client_code,
        "email": client.email,
        "phone": client.phone
    }
    
    # Update client
    update_data = client_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(client, key, value)
    
    client.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(client)
    
    log_work_reports_activity(
        db, current_user.id, current_user.name, "update_client",
        table_name="clients", record_id=str(client.id),
        before_value=original_data, after_value=update_data
    )
    
    return client

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
    """Create client credential with encrypted password"""
    
    # Check user permissions
    user_permissions = get_user_permissions(db, current_user.id)
    if not user_permissions:
        # Super Admin always has permissions
        if current_user.role != "super_admin":
            raise HTTPException(status_code=403, detail="ليس لديك صلاحية لإدارة بيانات الاعتماد")
    elif not user_permissions.can_create_credentials:
        raise HTTPException(status_code=403, detail="ليس لديك صلاحية لإنشاء بيانات اعتماد")
    
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

@api_router.get("/work-reports/activity-types", response_model=List[ActivityTypeResponse])
async def get_activity_types(
    current_user = Depends(get_current_user),
    db = Depends(get_work_reports_db)
):
    """Get all activity types"""
    activity_types = db.query(ActivityType).filter(ActivityType.is_active == True).all()
    return activity_types

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

# ============ WORK LOG MANAGEMENT ============

@api_router.get("/work-reports/logs", response_model=List[WorkLogResponse])
async def get_work_logs(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    client_id: Optional[str] = None,
    current_user = Depends(get_current_user),
    db = Depends(get_work_reports_db)
):
    """Get work logs with filtering options"""
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
    
    work_logs = query.order_by(WorkLog.date.desc()).all()
    
    # Enhance response with client and activity names
    enhanced_logs = []
    for log in work_logs:
        log_dict = {
            "id": str(log.id),
            "client_id": str(log.client_id),
            "activity_type_id": str(log.activity_type_id),
            "user_id": log.user_id,
            "user_name": log.user_name,
            "date": log.date,
            "start_time": log.start_time,
            "end_time": log.end_time,
            "duration_minutes": log.duration_minutes,
            "description": log.description,
            "notes": log.notes,
            "is_billable": log.is_billable,
            "hourly_rate": log.hourly_rate,
            "total_amount": log.total_amount,
            "status": log.status,
            "created_at": log.created_at,
            "updated_at": log.updated_at,
            "client_name": log.client.company_name if log.client else "",
            "activity_name": log.activity_type.name if log.activity_type else ""
        }
        enhanced_logs.append(log_dict)
    
    return enhanced_logs

@api_router.post("/work-reports/logs", response_model=WorkLogResponse)
async def create_work_log(
    log_data: WorkLogCreate,
    current_user = Depends(get_current_user),
    db = Depends(get_work_reports_db)
):
    """Create new work log entry"""
    # Validate client and activity type exist
    client = db.query(Client).filter(Client.id == log_data.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    activity_type = db.query(ActivityType).filter(ActivityType.id == log_data.activity_type_id).first()
    if not activity_type:
        raise HTTPException(status_code=404, detail="Activity type not found")
    
    # Calculate duration and total amount
    duration_minutes = 0
    if log_data.start_time and log_data.end_time:
        duration = log_data.end_time - log_data.start_time
        duration_minutes = int(duration.total_seconds() / 60)
    
    hourly_rate = log_data.hourly_rate or activity_type.default_rate or 0
    total_amount = (duration_minutes / 60) * hourly_rate if duration_minutes and hourly_rate else 0
    
    # Create work log
    work_log = WorkLog(
        client_id=log_data.client_id,
        activity_type_id=log_data.activity_type_id,
        user_id=current_user.id,
        user_name=current_user.name,
        date=log_data.date,
        start_time=log_data.start_time,
        end_time=log_data.end_time,
        duration_minutes=duration_minutes,
        description=log_data.description,
        notes=log_data.notes,
        is_billable=log_data.is_billable,
        hourly_rate=hourly_rate,
        total_amount=total_amount
    )
    
    db.add(work_log)
    db.commit()
    db.refresh(work_log)
    
    log_work_reports_activity(
        db, current_user.id, current_user.name, "create_work_log",
        table_name="work_logs", record_id=str(work_log.id),
        after_value={
            "client_id": str(log_data.client_id),
            "activity_type_id": str(log_data.activity_type_id),
            "duration_minutes": duration_minutes,
            "total_amount": total_amount
        }
    )
    
    # Return enhanced response
    return {
        "id": str(work_log.id),
        "client_id": str(work_log.client_id),
        "activity_type_id": str(work_log.activity_type_id),
        "user_id": work_log.user_id,
        "user_name": work_log.user_name,
        "date": work_log.date,
        "start_time": work_log.start_time,
        "end_time": work_log.end_time,
        "duration_minutes": work_log.duration_minutes,
        "description": work_log.description,
        "notes": work_log.notes,
        "is_billable": work_log.is_billable,
        "hourly_rate": work_log.hourly_rate,
        "total_amount": work_log.total_amount,
        "status": work_log.status,
        "created_at": work_log.created_at,
        "updated_at": work_log.updated_at,
        "client_name": client.company_name,
        "activity_name": activity_type.name
    }

@api_router.put("/work-reports/logs/{log_id}", response_model=WorkLogResponse)
async def update_work_log(
    log_id: str,
    log_update: WorkLogUpdate,
    current_user = Depends(get_current_user),
    db = Depends(get_work_reports_db)
):
    """Update work log entry"""
    work_log = db.query(WorkLog).filter(WorkLog.id == log_id).first()
    if not work_log:
        raise HTTPException(status_code=404, detail="Work log not found")
    
    # Check permissions - users can only edit their own logs
    if current_user.role == "user" and work_log.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Store original values for audit
    original_data = {
        "duration_minutes": work_log.duration_minutes,
        "total_amount": work_log.total_amount,
        "description": work_log.description
    }
    
    # Update work log
    update_data = log_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(work_log, key, value)
    
    # Recalculate duration and total if times are updated
    if work_log.start_time and work_log.end_time:
        duration = work_log.end_time - work_log.start_time
        work_log.duration_minutes = int(duration.total_seconds() / 60)
    
    if work_log.duration_minutes and work_log.hourly_rate:
        work_log.total_amount = (work_log.duration_minutes / 60) * work_log.hourly_rate
    
    work_log.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(work_log)
    
    log_work_reports_activity(
        db, current_user.id, current_user.name, "update_work_log",
        table_name="work_logs", record_id=str(work_log.id),
        before_value=original_data, after_value=update_data
    )
    
    return {
        "id": str(work_log.id),
        "client_id": str(work_log.client_id),
        "activity_type_id": str(work_log.activity_type_id),
        "user_id": work_log.user_id,
        "user_name": work_log.user_name,
        "date": work_log.date,
        "start_time": work_log.start_time,
        "end_time": work_log.end_time,
        "duration_minutes": work_log.duration_minutes,
        "description": work_log.description,
        "notes": work_log.notes,
        "is_billable": work_log.is_billable,
        "hourly_rate": work_log.hourly_rate,
        "total_amount": work_log.total_amount,
        "status": work_log.status,
        "created_at": work_log.created_at,
        "updated_at": work_log.updated_at,
        "client_name": work_log.client.company_name if work_log.client else "",
        "activity_name": work_log.activity_type.name if work_log.activity_type else ""
    }

@api_router.delete("/work-reports/logs/{log_id}")
async def delete_work_log(
    log_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_work_reports_db)
):
    """Delete work log entry"""
    work_log = db.query(WorkLog).filter(WorkLog.id == log_id).first()
    if not work_log:
        raise HTTPException(status_code=404, detail="Work log not found")
    
    # Check permissions - users can only delete their own logs, admins can delete any
    if current_user.role == "user" and work_log.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    db.delete(work_log)
    db.commit()
    
    log_work_reports_activity(
        db, current_user.id, current_user.name, "delete_work_log",
        table_name="work_logs", record_id=str(log_id)
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
                ).strip() if row_data.get("أميل") or row_data.get("ايميل") else ""
                
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
            "message": f"استيراد مكتمل - Import Status",
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
    current_user = Depends(get_current_user),
    db = Depends(get_work_reports_db)
):
    """Get work reports dashboard statistics"""
    
    # Get total clients
    total_clients = db.query(Client).filter(Client.is_active == True).count()
    
    # Get work logs for current user or all (based on role)
    work_logs_query = db.query(WorkLog)
    if current_user.role == "user":
        work_logs_query = work_logs_query.filter(WorkLog.user_id == current_user.id)
    
    # Get today's work logs
    today = datetime.now().date()
    today_logs = work_logs_query.filter(WorkLog.date >= today).count()
    
    # Get this week's work logs
    week_start = today - timedelta(days=today.weekday())
    week_logs = work_logs_query.filter(WorkLog.date >= week_start).count()
    
    # Get this month's work logs
    month_start = today.replace(day=1)
    month_logs = work_logs_query.filter(WorkLog.date >= month_start).count()
    
    # Get billable hours this month
    month_billable_logs = work_logs_query.filter(
        WorkLog.date >= month_start,
        WorkLog.is_billable == True
    ).all()
    
    total_billable_minutes = sum([log.duration_minutes or 0 for log in month_billable_logs])
    total_billable_hours = round(total_billable_minutes / 60, 2) if total_billable_minutes else 0
    
    # Get total revenue this month
    total_revenue = sum([log.total_amount or 0 for log in month_billable_logs])
    
    # Get recent activity
    recent_logs = work_logs_query.order_by(WorkLog.created_at.desc()).limit(5).all()
    recent_activity = []
    for log in recent_logs:
        recent_activity.append({
            "id": str(log.id),
            "client_name": log.client.company_name if log.client else "Unknown",
            "activity_name": log.activity_type.name if log.activity_type else "Unknown",
            "duration_minutes": log.duration_minutes,
            "date": log.date.isoformat() if log.date else None,
            "created_at": log.created_at.isoformat()
        })
    
    return {
        "total_clients": total_clients,
        "today_logs": today_logs,
        "week_logs": week_logs,
        "month_logs": month_logs,
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
    """Get credential password (for authorized users only) - NO ENCRYPTION"""
    
    # Check user permissions FIRST
    user_permissions = get_user_permissions(db, current_user.id)
    if not user_permissions:
        # Super Admin always has access
        if current_user.role != "super_admin":
            raise HTTPException(
                status_code=403, 
                detail="ليس لديك صلاحية لعرض كلمات المرور - لم يتم العثور على صلاحياتك"
            )
    elif not user_permissions.can_reveal_passwords:
        raise HTTPException(
            status_code=403, 
            detail=f"ليس لديك صلاحية لكشف كلمات المرور - مستواك الحالي: {user_permissions.permission_level}"
        )
    
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
    """Get current user's permissions"""
    permissions = get_user_permissions(db, current_user.id)
    
    # If user has permissions in DB, return them
    if permissions:
        # Update user info if needed (but don't commit if no changes needed)
        update_needed = False
        if permissions.user_name != current_user.name:
            permissions.user_name = current_user.name
            update_needed = True
        if permissions.user_email != getattr(current_user, 'email', ''):
            permissions.user_email = getattr(current_user, 'email', '')
            update_needed = True
            
        if update_needed:
            db.commit()
            
        return permissions
    
    # If no permissions exist, return default based on role (without saving to DB)
    if current_user.role == "super_admin":
        default_template = PERMISSION_TEMPLATES["admin"]
        return UserPermissionResponse(
            user_id=current_user.id,
            user_name=current_user.name,
            user_email=getattr(current_user, 'email', ''),
            permission_level="admin",
            granted_at=datetime.utcnow(),
            last_updated=datetime.utcnow(),
            is_active=True,
            **default_template["permissions"]
        )
    else:
        default_template = PERMISSION_TEMPLATES["user"] 
        return UserPermissionResponse(
            user_id=current_user.id,
            user_name=current_user.name,
            user_email=getattr(current_user, 'email', ''),
            permission_level="user",
            granted_at=datetime.utcnow(),
            last_updated=datetime.utcnow(),
            is_active=True,
            **default_template["permissions"]
        )

@api_router.delete("/work-reports/permissions/{user_id}")
async def revoke_user_permissions(
    user_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_work_reports_db)
):
    """Revoke user permissions (Super Admin only)"""
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Super Admin access required")
    
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
    client.close()

# Root endpoint
@app.get("/")
async def root():
    return {"message": "TANSEEQ HR System API"}