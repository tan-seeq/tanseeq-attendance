from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File
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
    hire_date: Optional[datetime]
    is_active: bool
    created_at: datetime

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
async def create_user(user_data: UserCreate, current_user: User = Depends(get_admin_user)):
    """Create new user (Admin only)"""
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Hash password
    hashed_password = hash_password(user_data.password)
    
    # Create user
    user_dict = user_data.dict()
    user_dict["password"] = hashed_password
    user = User(**user_dict)
    
    await db.users.insert_one(user.dict())
    
    await log_activity(current_user.id, "user_created", f"Created user {user.email}")
    
    return UserResponse(**user.dict())

@api_router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_data: UserUpdate, current_user: User = Depends(get_admin_user)):
    """Update user (Admin only)"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get update data
    update_data = {k: v for k, v in user_data.dict().items() if v is not None}
    
    if update_data:
        await db.users.update_one({"id": user_id}, {"$set": update_data})
        await log_activity(current_user.id, "user_updated", f"Updated user {user['email']}")
    
    # Return updated user
    updated_user = await db.users.find_one({"id": user_id})
    return UserResponse(**updated_user)

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
async def update_attendance(attendance_id: str, attendance_data: AttendanceUpdate, current_user: User = Depends(get_current_user)):
    """Update attendance record (Hatem only)"""
    if current_user.name != "Hatem Mohamed Ahmed":
        raise HTTPException(status_code=403, detail="Only Hatem can edit attendance records")
    
    attendance = await db.attendance.find_one({"id": attendance_id})
    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    
    # Get update data
    update_data = {k: v for k, v in attendance_data.dict().items() if v is not None}
    
    if update_data:
        # Recalculate working hours if both check_in and check_out are provided
        if attendance_data.check_in and attendance_data.check_out:
            try:
                check_in_time = datetime.strptime(attendance_data.check_in, "%H:%M:%S")
                check_out_time = datetime.strptime(attendance_data.check_out, "%H:%M:%S")
                working_hours = (check_out_time - check_in_time).total_seconds() / 3600
                update_data["working_hours"] = working_hours
            except ValueError:
                pass  # Invalid time format, skip calculation
        
        await db.attendance.update_one({"id": attendance_id}, {"$set": update_data})
        await log_activity(current_user.id, "attendance_edited", f"Edited attendance record {attendance_id} for {attendance['user_name']}")
    
    # Return updated attendance
    updated_attendance = await db.attendance.find_one({"id": attendance_id})
    return updated_attendance

@api_router.post("/attendance/check-in")
async def check_in(current_user: User = Depends(get_current_user)):
    """Check in attendance with custom rules per employee"""
    uae_time = get_uae_time()
    date_str = uae_time.strftime("%Y-%m-%d")
    time_str = uae_time.strftime("%H:%M:%S")
    
    # Check if it's weekend (Friday or Saturday)
    weekday = uae_time.weekday()  # 0 = Monday, 6 = Sunday
    if weekday in [4, 5]:  # Friday = 4, Saturday = 5
        raise HTTPException(status_code=400, detail="Cannot check in on weekends (Friday/Saturday)")
    
    # Check if already checked in today
    existing = await db.attendance.find_one({"user_id": current_user.id, "date": date_str})
    if existing and existing.get("check_in"):
        raise HTTPException(status_code=400, detail="Already checked in today")
    
    # Custom attendance rules
    is_late = False
    if current_user.name == "Hatem Mohamed Ahmed":
        # Hatem has no time restrictions
        is_late = False
    elif current_user.name == "Tarek Wazzan":
        # Tarek can start from 8 AM
        work_start = datetime.strptime("08:00", "%H:%M").time()
        current_time = uae_time.time()
        is_late = current_time > work_start
    else:
        # All others: 9:00 AM - 6:00 PM
        work_start = datetime.strptime("09:00", "%H:%M").time()
        current_time = uae_time.time()
        is_late = current_time > work_start
    
    attendance_data = {
        "id": str(uuid.uuid4()),
        "user_id": current_user.id,
        "user_name": current_user.name,
        "date": date_str,
        "check_in": time_str,
        "status": "late" if is_late else "present",
        "is_late": is_late,
        "created_at": datetime.utcnow()
    }
    
    if existing:
        await db.attendance.update_one(
            {"user_id": current_user.id, "date": date_str},
            {"$set": attendance_data}
        )
    else:
        await db.attendance.insert_one(attendance_data)
    
    await log_activity(current_user.id, "check_in", f"Checked in at {time_str} - {'Late' if is_late else 'On time'}")
    
    return {"message": "Checked in successfully", "time": time_str, "is_late": is_late}

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
async def approve_leave(leave_id: str, current_user: User = Depends(get_admin_user)):
    """Approve leave request (Admin only)"""
    leave = await db.leaves.find_one({"id": leave_id})
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    await db.leaves.update_one(
        {"id": leave_id},
        {"$set": {"status": "approved", "approved_by": current_user.id}}
    )
    
    await log_activity(current_user.id, "leave_approved", f"Approved leave request {leave_id}")
    
    return {"message": "Leave approved successfully"}

@api_router.post("/leaves/{leave_id}/reject")
async def reject_leave(leave_id: str, current_user: User = Depends(get_admin_user)):
    """Reject leave request (Admin only)"""
    leave = await db.leaves.find_one({"id": leave_id})
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    await db.leaves.update_one(
        {"id": leave_id},
        {"$set": {"status": "rejected", "approved_by": current_user.id}}
    )
    
    await log_activity(current_user.id, "leave_rejected", f"Rejected leave request {leave_id}")
    
    return {"message": "Leave rejected successfully"}

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

@api_router.post("/field-exits", response_model=FieldExit)
async def create_field_exit_request(field_exit_data: FieldExitCreate, current_user: User = Depends(get_current_user)):
    """Create field exit request"""
    field_exit = FieldExit(**field_exit_data.dict())
    await db.field_exits.insert_one(field_exit.dict())
    
    # Log the field exit in attendance history
    uae_time = get_uae_time()
    date_str = uae_time.strftime("%Y-%m-%d")
    
    # Check if there's attendance record for today
    attendance_record = await db.attendance.find_one({"user_id": current_user.id, "date": date_str})
    
    if attendance_record:
        # Add field exit info to attendance record
        field_exit_info = {
            "field_exit_id": field_exit.id,
            "visit_type": field_exit_data.visit_type,
            "client_name": field_exit_data.client_name,
            "start_time": field_exit_data.start_time,
            "end_time": field_exit_data.end_time,
            "report": field_exit_data.report
        }
        
        await db.attendance.update_one(
            {"user_id": current_user.id, "date": date_str},
            {"$set": {"field_exit": field_exit_info}}
        )
    
    visit_type_ar = {
        "client_visit": "زيارة عميل",
        "collection": "تحصيل",
        "bank_visit": "زيارة بنك",
        "personal": "شخصي",
        "admin_errand": "مهمة إدارية"
    }
    
    await log_activity(current_user.id, "field_exit_requested", 
                      f"Requested field exit: {visit_type_ar.get(field_exit_data.visit_type, field_exit_data.visit_type)}")
    
    return field_exit

@api_router.put("/field-exits/{field_exit_id}", response_model=FieldExit)
async def update_field_exit_request(field_exit_id: str, field_exit_data: FieldExitUpdate, current_user: User = Depends(get_current_user)):
    """Update field exit request"""
    field_exit = await db.field_exits.find_one({"id": field_exit_id})
    if not field_exit:
        raise HTTPException(status_code=404, detail="Field exit request not found")
    
    # Check permissions
    if current_user.role == "user" and field_exit["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this request")
    
    # Get update data
    update_data = {k: v for k, v in field_exit_data.dict().items() if v is not None}
    
    if update_data:
        await db.field_exits.update_one({"id": field_exit_id}, {"$set": update_data})
        await log_activity(current_user.id, "field_exit_updated", f"Updated field exit request {field_exit_id}")
    
    # Return updated field exit
    updated_field_exit = await db.field_exits.find_one({"id": field_exit_id})
    return FieldExit(**updated_field_exit)

@api_router.post("/field-exits/{field_exit_id}/approve")
async def approve_field_exit(field_exit_id: str, current_user: User = Depends(get_admin_user)):
    """Approve field exit request (Admin only)"""
    field_exit = await db.field_exits.find_one({"id": field_exit_id})
    if not field_exit:
        raise HTTPException(status_code=404, detail="Field exit request not found")
    
    await db.field_exits.update_one(
        {"id": field_exit_id},
        {"$set": {"status": "approved", "approved_by": current_user.id}}
    )
    
    await log_activity(current_user.id, "field_exit_approved", f"Approved field exit request {field_exit_id}")
    
    return {"message": "Field exit approved successfully"}

@api_router.post("/field-exits/{field_exit_id}/reject")
async def reject_field_exit(field_exit_id: str, current_user: User = Depends(get_admin_user)):
    """Reject field exit request (Admin only)"""
    field_exit = await db.field_exits.find_one({"id": field_exit_id})
    if not field_exit:
        raise HTTPException(status_code=404, detail="Field exit request not found")
    
    await db.field_exits.update_one(
        {"id": field_exit_id},
        {"$set": {"status": "rejected", "approved_by": current_user.id}}
    )
    
    await log_activity(current_user.id, "field_exit_rejected", f"Rejected field exit request {field_exit_id}")
    
    return {"message": "Field exit rejected successfully"}

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
async def get_activity_logs(current_user: User = Depends(get_super_admin_user)):
    """Get activity logs (Super admin only)"""
    activity_records = await db.activity_logs.find().sort("timestamp", -1).to_list(1000)
    
    # Convert to clean format without ObjectId
    activity_logs_list = []
    for record in activity_records:
        activity_logs_list.append({
            "id": record.get("id", str(record.get("_id", ""))),
            "user_id": record.get("user_id", ""),
            "action": record.get("action", ""),
            "details": record.get("details", ""),
            "before_value": record.get("before_value"),
            "after_value": record.get("after_value"),
            "timestamp": record.get("timestamp")
        })
    
    return activity_logs_list

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
    """Export payroll data (Admin only)"""
    from io import BytesIO
    from fastapi.responses import StreamingResponse
    
    payroll_data = await calculate_payroll(month, current_user)
    
    if format == "excel":
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
        
        # Create workbook and worksheet
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"Payroll {month}"
        
        # Headers
        headers = ["Name", "Position", "Monthly Salary", "Daily Rate", "Working Days", "Total Hours", "Late Days", "Final Salary"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            cell.alignment = Alignment(horizontal="center")
        
        # Data rows
        for row, employee in enumerate(payroll_data, 2):
            ws.cell(row=row, column=1, value=employee["name"])
            ws.cell(row=row, column=2, value=employee["position"])
            ws.cell(row=row, column=3, value=employee["monthly_salary"])
            ws.cell(row=row, column=4, value=employee["daily_rate"])
            ws.cell(row=row, column=5, value=employee["working_days"])
            ws.cell(row=row, column=6, value=employee["total_hours"])
            ws.cell(row=row, column=7, value=employee["late_days"])
            ws.cell(row=row, column=8, value=employee["final_salary"])
        
        # Auto-adjust columns
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # Save to BytesIO
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        return StreamingResponse(
            BytesIO(output.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=payroll_{month}.xlsx"}
        )
    
    elif format == "pdf":
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        
        output = BytesIO()
        doc = SimpleDocTemplate(output, pagesize=A4)
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        title = Paragraph(f"TANSEEQ Tax Consultancy - Payroll Report {month}", title_style)
        
        # Table data
        table_data = [["Name", "Position", "Monthly Salary", "Daily Rate", "Working Days", "Final Salary"]]
        for employee in payroll_data:
            table_data.append([
                employee["name"],
                employee["position"],
                f"AED {employee['monthly_salary']:.2f}",
                f"AED {employee['daily_rate']:.2f}",
                str(employee["working_days"]),
                f"AED {employee['final_salary']:.2f}"
            ])
        
        # Create table
        table = Table(table_data, colWidths=[2*inch, 1.5*inch, 1.2*inch, 1.2*inch, 1*inch, 1.2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        # Build PDF
        story = [title, Spacer(1, 12), table]
        doc.build(story)
        
        output.seek(0)
        return StreamingResponse(
            BytesIO(output.read()),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=payroll_{month}.pdf"}
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