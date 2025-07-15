from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
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

class LeaveCreate(LeaveBase):
    pass

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

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: User = Depends(get_admin_user)):
    """Delete user (Admin only)"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.users.delete_one({"id": user_id})
    await log_activity(current_user.id, "user_deleted", f"Deleted user {user['email']}")
    
    return {"message": "User deleted successfully"}

# ============ ATTENDANCE ENDPOINTS ============

@api_router.get("/attendance")
async def get_attendance(current_user: User = Depends(get_current_user)):
    """Get attendance records"""
    query = {}
    if current_user.role == "user":
        query["user_id"] = current_user.id
    
    attendance = await db.attendance.find(query).to_list(1000)
    return attendance

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
    
    leaves = await db.leaves.find(query).to_list(1000)
    return leaves

@api_router.post("/leaves", response_model=Leave)
async def create_leave_request(leave_data: LeaveCreate, current_user: User = Depends(get_current_user)):
    """Create leave request"""
    leave = Leave(**leave_data.dict())
    await db.leaves.insert_one(leave.dict())
    
    await log_activity(current_user.id, "leave_requested", f"Requested leave from {leave_data.start_date} to {leave_data.end_date}")
    
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
    
    field_exits = await db.field_exits.find(query).to_list(1000)
    return field_exits

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
    logs = await db.activity_logs.find().sort("timestamp", -1).to_list(1000)
    return logs

# ============ REPORTS ENDPOINTS ============

@api_router.get("/reports/attendance")
async def get_attendance_report(current_user: User = Depends(get_admin_user)):
    """Get attendance report (Admin only)"""
    attendance = await db.attendance.find().to_list(1000)
    return attendance

@api_router.get("/reports/leaves")
async def get_leaves_report(current_user: User = Depends(get_admin_user)):
    """Get leaves report (Admin only)"""
    leaves = await db.leaves.find().to_list(1000)
    return leaves

@api_router.get("/reports/payroll")
async def get_payroll_report(current_user: User = Depends(get_admin_user)):
    """Get payroll report (Admin only)"""
    users = await db.users.find({"is_active": True}).to_list(1000)
    payroll_data = []
    
    for user in users:
        # Get attendance for current month
        current_month = get_uae_time().strftime("%Y-%m")
        attendance = await db.attendance.find({"user_id": user["id"], "date": {"$regex": f"^{current_month}"}}).to_list(1000)
        
        total_days = len(attendance)
        total_hours = sum([a.get("working_hours", 0) for a in attendance if a.get("working_hours")])
        
        payroll_data.append({
            "user_id": user["id"],
            "name": user["name"],
            "position": user["position"],
            "monthly_salary": user["monthly_salary"],
            "daily_rate": user["daily_rate"],
            "total_days": total_days,
            "total_hours": total_hours,
            "calculated_salary": min(user["monthly_salary"], total_days * user["daily_rate"])
        })
    
    return payroll_data

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