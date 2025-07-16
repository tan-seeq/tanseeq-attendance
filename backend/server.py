from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Form, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, time
from jose import JWTError, jwt
import os
import logging
import uuid
import bcrypt
import pytz
import shutil
from pathlib import Path

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

# ============ AUTH ENDPOINTS ============

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
async def update_attendance(attendance_id: str, attendance_data: dict, current_user: User = Depends(get_super_admin_user)):
    """Update attendance record (Super admin only)"""
    attendance = await db.attendance.find_one({"id": attendance_id})
    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    
    # Store original values for logging
    original_values = {
        "check_in": attendance.get("check_in"),
        "check_out": attendance.get("check_out"),
        "status": attendance.get("status"),
        "is_late": attendance.get("is_late")
    }
    
    # Update values
    update_data = {}
    if "check_in" in attendance_data:
        update_data["check_in"] = attendance_data["check_in"]
    if "check_out" in attendance_data:
        update_data["check_out"] = attendance_data["check_out"]
    if "status" in attendance_data:
        update_data["status"] = attendance_data["status"]
        # If status is manually set to present, remove late flag
        if attendance_data["status"] == "present":
            update_data["is_late"] = False
    
    # Calculate working hours if both check_in and check_out are available
    if update_data.get("check_in") and update_data.get("check_out"):
        try:
            check_in_time = datetime.strptime(update_data["check_in"], "%H:%M:%S")
            check_out_time = datetime.strptime(update_data["check_out"], "%H:%M:%S")
            
            # Handle overnight shifts
            if check_out_time < check_in_time:
                check_out_time += timedelta(days=1)
            
            working_hours = (check_out_time - check_in_time).total_seconds() / 3600
            update_data["working_hours"] = working_hours
        except ValueError:
            pass  # Invalid time format, skip calculation
    
    # When admin edits the attendance, assume it's correct and not late
    if "check_in" in update_data or "check_out" in update_data:
        update_data["is_late"] = False
        if "status" not in update_data:
            update_data["status"] = "present"
    
    # Update the record
    await db.attendance.update_one({"id": attendance_id}, {"$set": update_data})
    
    # Log the activity
    changes = []
    for key, new_value in update_data.items():
        old_value = original_values.get(key, attendance.get(key))
        if old_value != new_value:
            changes.append(f"{key}: {old_value} -> {new_value}")
    
    if changes:
        await log_activity(
            current_user.id, 
            "attendance_updated", 
            f"Updated attendance for {attendance.get('user_name', 'Unknown')}: {', '.join(changes)}"
        )
    
    return {"message": "Attendance updated successfully"}

@api_router.post("/attendance/check-in")
async def check_in(current_user: User = Depends(get_current_user)):
    """Check in attendance"""
    # Get current UAE time
    uae_time = datetime.now(UAE_TZ)
    date_str = uae_time.strftime("%Y-%m-%d")
    time_str = uae_time.strftime("%H:%M:%S")
    
    # Check if user already checked in today
    existing_attendance = await db.attendance.find_one({"user_id": current_user.id, "date": date_str})
    if existing_attendance and existing_attendance.get("check_in"):
        raise HTTPException(status_code=400, detail="Already checked in today")
    
    # Check if it's Friday or Saturday (weekend)
    weekday = uae_time.weekday()  # 0=Monday, 6=Sunday
    if weekday == 4 or weekday == 5:  # Friday=4, Saturday=5
        is_weekend = True
    else:
        is_weekend = False
    
    # Get user details for schedule checking
    user_details = await db.users.find_one({"id": current_user.id})
    
    # Determine if user is late based on their schedule type
    is_late = False
    status = "present"
    
    if user_details.get("has_flexible_schedule", False):
        # Flexible schedule logic
        start_range = user_details.get("flexible_start_range", "07:00-10:00")
        core_hours = user_details.get("flexible_core_hours", "10:00-15:00")
        
        # Parse flexible start range
        start_earliest, start_latest = start_range.split("-")
        core_start, core_end = core_hours.split("-")
        
        current_time = datetime.strptime(time_str, "%H:%M:%S").time()
        start_latest_time = datetime.strptime(start_latest, "%H:%M").time()
        core_start_time = datetime.strptime(core_start, "%H:%M").time()
        
        # For flexible schedule, they're late if they miss core hours start
        if current_time > core_start_time:
            is_late = True
            status = "late"
    else:
        # Fixed schedule logic
        if current_user.name == "Hatem Mohamed Ahmed":
            # Hatem has no restrictions
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
        "schedule_type": "flexible" if user_details.get("has_flexible_schedule", False) else "fixed",
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
    
    await log_activity(current_user.id, "check_in", f"Checked in at {time_str} ({'flexible' if user_details.get('has_flexible_schedule', False) else 'fixed'} schedule)")
    
    return {"message": "Checked in successfully", "time": time_str, "is_late": is_late, "schedule_type": attendance_data["schedule_type"]}

@api_router.post("/attendance/check-out")
async def check_out(current_user: User = Depends(get_current_user)):
    """Check out attendance"""
    uae_time = get_uae_time()
    date_str = uae_time.strftime("%Y-%m-%d")
    time_str = uae_time.strftime("%H:%M:%S")
    
    # Find today's attendance
    attendance = await db.attendance.find_one({"user_id": current_user.id, "date": date_str})
    if not attendance:
        raise HTTPException(status_code=400, detail="No check-in record found for today")
    
    if attendance.get("check_out"):
        raise HTTPException(status_code=400, detail="Already checked out today")
    
    # Calculate working hours
    check_in_time = datetime.strptime(attendance["check_in"], "%H:%M:%S")
    check_out_time = datetime.strptime(time_str, "%H:%M:%S")
    working_hours = (check_out_time - check_in_time).total_seconds() / 3600
    
    await db.attendance.update_one(
        {"user_id": current_user.id, "date": date_str},
        {"$set": {"check_out": time_str, "working_hours": working_hours}}
    )
    
    await log_activity(current_user.id, "check_out", f"Checked out at {time_str}")
    
    return {"message": "Checked out successfully", "time": time_str, "working_hours": working_hours}

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

@api_router.post("/leaves", response_model=Leave)
async def create_leave_request(
    user_id: str = None,
    user_name: str = None,
    start_date: str = None,
    end_date: str = None,
    reason: str = None,
    days_count: int = None,
    file: UploadFile = File(None),
    current_user: User = Depends(get_current_user)
):
    """Create leave request with optional file attachment"""
    
    # Handle file upload
    attachment_url = None
    if file:
        # Generate unique filename
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = uploads_dir / filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        attachment_url = f"/uploads/{filename}"
    
    leave_dict = {
        "user_id": user_id or current_user.id,
        "user_name": user_name or current_user.name,
        "start_date": start_date,
        "end_date": end_date,
        "reason": reason,
        "days_count": days_count,
        "attachment_url": attachment_url
    }
    
    leave = Leave(**leave_dict)
    await db.leaves.insert_one(leave.dict())
    
    await log_activity(current_user.id, "leave_requested", 
                      f"Requested leave from {start_date} to {end_date}")
    
    return leave

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
            "visit_type": record.get("visit_type", ""),
            "client_name": record.get("client_name", ""),
            "start_time": record.get("start_time", ""),
            "end_time": record.get("end_time", ""),
            "report": record.get("report", ""),
            "status": record.get("status", "pending"),
            "approved_by": record.get("approved_by"),
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
            "report": record.get("report", ""),
            "status": record.get("status", "pending"),
            "approved_by": record.get("approved_by"),
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
            present_today = await db.attendance.count_documents({"date": today, "status": {"$in": ["present", "late"]}})
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
            report_data.append({
                "user_name": record.get("user_name", ""),
                "date": record.get("date", ""),
                "check_in": record.get("check_in", ""),
                "check_out": record.get("check_out", ""),
                "working_hours": record.get("working_hours", 0),
                "status": record.get("status", ""),
                "is_late": record.get("is_late", False)
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
            report_data.append({
                "user_name": record.get("user_name", ""),
                "date": record.get("date", ""),
                "check_in": record.get("check_in", ""),
                "check_out": record.get("check_out", ""),
                "working_hours": record.get("working_hours", 0),
                "status": record.get("status", ""),
                "is_late": record.get("is_late", False)
            })
        
        headers = ["Employee", "Date", "Check In", "Check Out", "Working Hours", "Status", "Late"]
        headers_ar = ["الموظف", "التاريخ", "الحضور", "الانصراف", "ساعات العمل", "الحالة", "متأخر"]
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
                    "Present" if record["status"] == "present" else "Late" if record["status"] == "late" else "Absent",
                    "Yes" if record["is_late"] else "No"
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
                    "Present" if record["status"] == "present" else "Late" if record["status"] == "late" else "Absent",
                    "Yes" if record["is_late"] else "No"
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
            report_data.append({
                "user_name": record.get("user_name", ""),
                "date": record.get("date", ""),
                "check_in": record.get("check_in", ""),
                "check_out": record.get("check_out", ""),
                "working_hours": record.get("working_hours", 0),
                "status": record.get("status", ""),
                "is_late": record.get("is_late", False)
            })
        
        headers = ["Employee", "Date", "Check In", "Check Out", "Working Hours", "Status", "Late"]
        headers_ar = ["الموظف", "التاريخ", "الحضور", "الانصراف", "ساعات العمل", "الحالة", "متأخر"]
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
                    "Present" if record["status"] == "present" else "Late" if record["status"] == "late" else "Absent",
                    "Yes" if record["is_late"] else "No"
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
                    "Present" if record["status"] == "present" else "Late" if record["status"] == "late" else "Absent",
                    "Yes" if record["is_late"] else "No"
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
    """Calculate payroll for a specific month (Admin only)"""
    try:
        # Validate month format (YYYY-MM)
        datetime.strptime(month, "%Y-%m")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM")
    
    # Get all active users
    users = await db.users.find({"is_active": True}).to_list(1000)
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
        
        # Calculate salary based on daily rate
        calculated_salary = working_days * user["daily_rate"]
        
        # Apply monthly salary cap
        final_salary = min(calculated_salary, user["monthly_salary"])
        
        payroll_data.append({
            "user_id": user["id"],
            "name": user["name"],
            "position": user["position"],
            "monthly_salary": user["monthly_salary"],
            "daily_rate": user["daily_rate"],
            "working_days": working_days,
            "total_hours": round(total_hours, 2),
            "late_days": late_days,
            "calculated_salary": round(calculated_salary, 2),
            "final_salary": round(final_salary, 2),
            "month": month
        })
    
    return payroll_data

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
        
        # Set column widths
        column_widths = [20, 15, 15, 12, 12, 12, 12, 15]
        for i, width in enumerate(column_widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = width
        
        # Company header with logo styling
        ws.merge_cells('A1:H1')
        company_cell = ws['A1']
        company_cell.value = "TANSEEQ TAX CONSULTANCY"
        company_cell.font = Font(name="Arial", size=20, bold=True, color="FFFFFF")
        company_cell.fill = PatternFill(start_color="2B5797", end_color="1B4477", fill_type="solid")
        company_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[1].height = 40
        
        # Logo area (simulated with styling)
        ws.merge_cells('A2:H2')
        logo_cell = ws['A2']
        logo_cell.value = "مكتب استشارات ضريبية متخصص"
        logo_cell.font = Font(name="Arial", size=12, color="4472C4", italic=True)
        logo_cell.fill = PatternFill(start_color="E6EFFF", end_color="E6EFFF", fill_type="solid")
        logo_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[2].height = 25
        
        # Report title with enhanced styling
        ws.merge_cells('A3:H3')
        title_cell = ws['A3']
        title_cell.value = f"Payroll Report - تقرير الرواتب"
        title_cell.font = Font(name="Arial", size=16, bold=True, color="1F4E79")
        title_cell.fill = PatternFill(start_color="F0F8FF", end_color="F0F8FF", fill_type="solid")
        title_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[3].height = 30
        
        # Enhanced period info
        ws.merge_cells('A4:H4')
        period_cell = ws['A4']
        period_cell.value = f"الشهر: {month} | عدد الموظفين: {len(payroll_data)} | تاريخ الإنشاء: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        period_cell.font = Font(name="Arial", size=10, color="555555")
        period_cell.fill = PatternFill(start_color="F8F9FA", end_color="F8F9FA", fill_type="solid")
        period_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[4].height = 25
        
        # Add decorative separator
        ws.merge_cells('A5:H5')
        separator_cell = ws['A5']
        separator_cell.value = "=" * 80
        separator_cell.font = Font(name="Arial", size=8, color="CCCCCC")
        separator_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[5].height = 10
        
        # Headers with enhanced styling
        headers = ["Name", "Monthly Salary", "Daily Rate", "Working Days", "Total Hours", "Late Days", "Final Salary"]
        headers_ar = ["الاسم", "الراتب الشهري", "الراتب اليومي", "أيام العمل", "إجمالي الساعات", "الأيام المتأخرة", "الراتب النهائي"]
        
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
        for row_idx, employee in enumerate(payroll_data, header_row + 1):
            row_color = "F2F2F2" if row_idx % 2 == 0 else "FFFFFF"
            
            values = [
                employee["name"],
                employee["position"],
                f"AED {employee['monthly_salary']:.2f}",
                f"AED {employee['daily_rate']:.2f}",
                str(employee["working_days"]),
                f"{employee.get('total_hours', 0):.1f}h",
                str(employee.get("late_days", 0)),
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
        
        # Footer
        footer_row = len(payroll_data) + header_row + 2
        ws.merge_cells(f'A{footer_row}:H{footer_row}')
        footer_cell = ws[f'A{footer_row}']
        footer_cell.value = "TANSEEQ TAX CONSULTANCY - Employee Management System"
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
        report_title_text = Paragraph("Payroll Report<br/>تقرير الرواتب", title_style)
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
        
        # Create table data
        table_data = [["Name", "Position", "Monthly Salary", "Daily Rate", "Working Days", "Final Salary"]]
        for employee in payroll_data:
            table_data.append([
                employee["name"][:20],  # Truncate long names
                employee["position"][:15],
                f"AED {employee['monthly_salary']:.2f}",
                f"AED {employee['daily_rate']:.2f}",
                str(employee["working_days"]),
                f"AED {employee['final_salary']:.2f}"
            ])
        
        # Create table with enhanced styling
        table = Table(table_data, colWidths=[2.2*inch, 1.5*inch, 1.3*inch, 1.3*inch, 1*inch, 1.3*inch])
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
        story.append(Spacer(1, 30))
        
        # Professional footer
        footer_style = ParagraphStyle(
            'FooterStyle',
            parent=styles['Normal'],
            fontSize=10,
            alignment=1,
            textColor=colors.Color(0.4, 0.4, 0.4),
            fontName='Helvetica-Oblique'
        )
        footer_text = Paragraph("TANSEEQ TAX CONSULTANCY - Employee Management System", footer_style)
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