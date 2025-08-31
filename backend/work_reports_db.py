"""
PostgreSQL Database Setup and Models for Daily Work Report + Clients Master Feature
This module is completely isolated from the main MongoDB-based TANSEEQ HR system
"""

import os
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    create_engine, Column, String, Text, DateTime, Boolean, Float, 
    Integer, ForeignKey, JSON, LargeBinary
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from pydantic import BaseModel, Field
from cryptography.fernet import Fernet
import base64
import json

# Database setup - Using SQLite for compatibility
DATABASE_URL = "sqlite:///./work_reports.db"

# SQLAlchemy setup
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Encryption key for client credentials
ENCRYPTION_KEY = os.environ.get('WORK_REPORTS_ENCRYPTION_KEY', 
                               base64.urlsafe_b64encode(os.urandom(32)).decode())

# ============ DATABASE MODELS ============

class Client(Base):
    __tablename__ = "clients"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_name = Column(String(255), nullable=False)
    company_name_ar = Column(String(255))  # Arabic name
    client_code = Column(String(50), unique=True)
    industry = Column(String(100))
    contact_person = Column(String(255))
    phone = Column(String(50))
    email = Column(String(255))
    address = Column(Text)
    tax_number = Column(String(100))
    commercial_registration = Column(String(100))
    is_active = Column(Boolean, default=True)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255))
    
    # Relationships
    credentials = relationship("ClientCredential", back_populates="client", cascade="all, delete-orphan")
    work_logs = relationship("WorkLog", back_populates="client")

class ClientCredential(Base):
    __tablename__ = "client_credentials"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String(36), ForeignKey("clients.id"), nullable=False)
    credential_type = Column(String(100), nullable=False)  # fta, ministry, bank, portal, etc.
    username = Column(String(255))
    email = Column(String(255))
    password = Column(String(500))  # Plain text password (no encryption)
    encrypted_password = Column(LargeBinary)  # Legacy field (not used)
    portal_url = Column(String(500))
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    client = relationship("Client", back_populates="credentials")

class ActivityType(Base):
    __tablename__ = "activity_types"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    name_ar = Column(String(255))  # Arabic name
    category = Column(String(100))  # tax, accounting, consulting, legal, etc.
    description = Column(Text)
    default_rate = Column(Float)  # Default hourly rate
    is_billable = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    work_logs = relationship("WorkLog", back_populates="activity_type")

class WorkLog(Base):
    __tablename__ = "work_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String(36), ForeignKey("clients.id"), nullable=False)
    activity_type_id = Column(String(36), ForeignKey("activity_types.id"), nullable=False)
    user_id = Column(String(255), nullable=False)  # Reference to TANSEEQ HR user
    user_name = Column(String(255), nullable=False)
    date = Column(DateTime, nullable=False)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    duration_minutes = Column(Integer)  # Duration in minutes
    description = Column(Text, nullable=False)
    notes = Column(Text)
    is_billable = Column(Boolean, default=True)
    hourly_rate = Column(Float)
    total_amount = Column(Float)  # duration * rate
    status = Column(String(50), default='active')  # active, invoiced, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    client = relationship("Client", back_populates="work_logs")
    activity_type = relationship("ActivityType", back_populates="work_logs")

# ============ PYDANTIC MODELS ============

class ClientBase(BaseModel):
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
    notes: Optional[str] = None

class ClientCreate(ClientBase):
    pass

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
    notes: Optional[str] = None

class ClientResponse(ClientBase):
    id: str
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    
    class Config:
        from_attributes = True

class ClientCredentialBase(BaseModel):
    credential_type: str
    username: Optional[str] = None
    email: Optional[str] = None
    portal_url: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True

class ClientCredentialCreate(ClientCredentialBase):
    password: Optional[str] = None  # Will be encrypted before storing

class ClientCredentialResponse(ClientCredentialBase):
    id: str
    client_id: str
    last_used: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    # Note: password is never returned for security
    
    class Config:
        from_attributes = True

class ActivityTypeBase(BaseModel):
    name: str
    name_ar: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    default_rate: Optional[float] = None
    is_billable: bool = True
    is_active: bool = True

class ActivityTypeCreate(ActivityTypeBase):
    pass

class ActivityTypeResponse(ActivityTypeBase):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class WorkLogBase(BaseModel):
    client_id: str
    activity_type_id: str
    date: datetime
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    description: str
    notes: Optional[str] = None
    is_billable: bool = True
    hourly_rate: Optional[float] = None

class WorkLogCreate(WorkLogBase):
    pass

class WorkLogUpdate(BaseModel):
    client_id: Optional[str] = None
    activity_type_id: Optional[str] = None
    date: Optional[datetime] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    is_billable: Optional[bool] = None
    hourly_rate: Optional[float] = None
    status: Optional[str] = None

class WorkLogResponse(WorkLogBase):
    id: str
    user_id: str
    user_name: str
    total_amount: Optional[float] = None
    status: str
    created_at: datetime
    updated_at: datetime
    client_name: Optional[str] = None
    activity_name: Optional[str] = None
    
    class Config:
        from_attributes = True

# ============ ENCRYPTION UTILITIES ============

class CredentialEncryption:
    """Handle AES-256-GCM encryption for client credentials"""
    
    def __init__(self):
        self.cipher = Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)
    
    def encrypt_password(self, password: str) -> bytes:
        """Encrypt password using AES-256-GCM"""
        if not password:
            return b''
        return self.cipher.encrypt(password.encode('utf-8'))
    
    def decrypt_password(self, encrypted_password: bytes) -> str:
        """Decrypt password"""
        if not encrypted_password:
            return ''
        return self.cipher.decrypt(encrypted_password).decode('utf-8')

# Initialize encryption utility
credential_encryption = CredentialEncryption()

# ============ DATABASE UTILITIES ============

def get_work_reports_db():
    """Dependency to get PostgreSQL database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_work_reports_tables():
    """Create all tables for work reports module"""
    Base.metadata.create_all(bind=engine)

def init_default_activity_types(db: Session):
    """Initialize default activity types"""
    default_activities = [
        {
            "name": "Tax Declaration Preparation",
            "name_ar": "إعداد الإقرار الضريبي",
            "category": "tax",
            "description": "Preparation of various tax declarations",
            "default_rate": 150.0,
            "is_billable": True
        },
        {
            "name": "VAT Return Filing", 
            "name_ar": "تقديم إقرار ضريبة القيمة المضافة",
            "category": "tax",
            "description": "Filing VAT returns with FTA",
            "default_rate": 200.0,
            "is_billable": True
        },
        {
            "name": "Financial Statement Review",
            "name_ar": "مراجعة القوائم المالية", 
            "category": "accounting",
            "description": "Review and analysis of financial statements",
            "default_rate": 180.0,
            "is_billable": True
        },
        {
            "name": "Client Meeting",
            "name_ar": "اجتماع العميل",
            "category": "consulting",
            "description": "Meeting with client for consultation",
            "default_rate": 250.0,
            "is_billable": True
        },
        {
            "name": "Document Review",
            "name_ar": "مراجعة المستندات",
            "category": "legal",
            "description": "Review of legal and financial documents",
            "default_rate": 120.0,
            "is_billable": True
        },
        {
            "name": "Administrative Tasks",
            "name_ar": "المهام الإدارية",
            "category": "admin", 
            "description": "General administrative work",
            "default_rate": 80.0,
            "is_billable": False
        }
    ]
    
    for activity_data in default_activities:
        # Check if activity already exists
        existing = db.query(ActivityType).filter(ActivityType.name == activity_data["name"]).first()
        if not existing:
            activity = ActivityType(**activity_data)
            db.add(activity)
    
    db.commit()

# ============ AUDIT LOG MODEL ============

class WorkReportsAuditLog(Base):
    __tablename__ = "work_reports_audit_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(255), nullable=False)
    user_name = Column(String(255), nullable=False)
    action = Column(String(100), nullable=False)  # create, update, delete, view, export
    table_name = Column(String(100))  # clients, work_logs, etc.
    record_id = Column(String(255))
    before_value = Column(JSON)
    after_value = Column(JSON)
    ip_address = Column(String(50))
    user_agent = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
# ============ 2FA SECURITY MODEL ============

class User2FA(Base):
    __tablename__ = "user_2fa_settings"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(255), nullable=False, unique=True)
    secret_key = Column(LargeBinary)  # Encrypted TOTP secret
    is_enabled = Column(Boolean, default=False)
    backup_codes = Column(JSON)  # Encrypted backup codes
    last_used_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class PasswordAccessSession(Base):
    __tablename__ = "password_access_sessions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(255), nullable=False)
    credential_id = Column(String(36), ForeignKey("client_credentials.id"))
    session_token = Column(String(255), unique=True)
    expires_at = Column(DateTime, nullable=False)
    ip_address = Column(String(50))
    user_agent = Column(Text)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# ============ USER PERMISSIONS MODEL ============

class UserWorkReportsPermission(Base):
    __tablename__ = "user_work_reports_permissions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(255), nullable=False, unique=True)  # Reference to TANSEEQ HR user
    user_name = Column(String(255), nullable=False)
    user_email = Column(String(255))
    
    # Work Reports Permissions
    can_view_clients = Column(Boolean, default=True)
    can_create_clients = Column(Boolean, default=False)
    can_edit_clients = Column(Boolean, default=False)
    can_delete_clients = Column(Boolean, default=False)
    can_import_clients = Column(Boolean, default=False)
    
    # Work Logs Permissions
    can_view_own_logs = Column(Boolean, default=True)
    can_view_all_logs = Column(Boolean, default=False)
    can_create_work_logs = Column(Boolean, default=True)
    can_edit_own_logs = Column(Boolean, default=True)
    can_edit_all_logs = Column(Boolean, default=False)
    can_delete_own_logs = Column(Boolean, default=False)
    can_delete_all_logs = Column(Boolean, default=False)
    
    # Sensitive Data Permissions (Most Important)
    can_view_credentials = Column(Boolean, default=False)
    can_view_usernames = Column(Boolean, default=True)
    can_view_emails = Column(Boolean, default=True)
    can_reveal_passwords = Column(Boolean, default=False)
    can_create_credentials = Column(Boolean, default=False)
    can_edit_credentials = Column(Boolean, default=False)
    can_delete_credentials = Column(Boolean, default=False)
    
    # Reports and Export Permissions
    can_generate_reports = Column(Boolean, default=True)
    can_export_excel = Column(Boolean, default=False)
    can_export_pdf = Column(Boolean, default=True)
    can_view_analytics = Column(Boolean, default=True)
    
    # Administrative Permissions
    can_view_audit_logs = Column(Boolean, default=False)
    can_manage_permissions = Column(Boolean, default=False)
    can_setup_sample_data = Column(Boolean, default=False)
    
    # Permission Level (for easy management)
    permission_level = Column(String(50), default="user")  # user, supervisor, admin, super_admin
    
    # Metadata
    granted_by = Column(String(255))
    granted_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    notes = Column(Text)

# ============ PERMISSION TEMPLATES ============

PERMISSION_TEMPLATES = {
    "user": {
        "name": "موظف عادي - User",
        "description": "صلاحيات أساسية للموظفين العاديين",
        "permissions": {
            "can_view_clients": True,
            "can_create_clients": False,
            "can_edit_clients": False,
            "can_delete_clients": False,
            "can_import_clients": False,
            "can_view_own_logs": True,
            "can_view_all_logs": False,
            "can_create_work_logs": True,
            "can_edit_own_logs": True,
            "can_edit_all_logs": False,
            "can_delete_own_logs": False,
            "can_delete_all_logs": False,
            "can_view_credentials": True,
            "can_view_usernames": True,
            "can_view_emails": True,
            "can_reveal_passwords": False,
            "can_create_credentials": False,
            "can_edit_credentials": False,
            "can_delete_credentials": False,
            "can_generate_reports": True,
            "can_export_excel": False,
            "can_export_pdf": True,
            "can_view_analytics": True,
            "can_view_audit_logs": False,
            "can_manage_permissions": False,
            "can_setup_sample_data": False
        }
    },
    "supervisor": {
        "name": "مشرف - Supervisor", 
        "description": "صلاحيات إشرافية مع الوصول لكلمات المرور",
        "permissions": {
            "can_view_clients": True,
            "can_create_clients": True,
            "can_edit_clients": True,
            "can_delete_clients": False,
            "can_import_clients": True,
            "can_view_own_logs": True,
            "can_view_all_logs": True,
            "can_create_work_logs": True,
            "can_edit_own_logs": True,
            "can_edit_all_logs": True,
            "can_delete_own_logs": True,
            "can_delete_all_logs": False,
            "can_view_credentials": True,
            "can_view_usernames": True,
            "can_view_emails": True,
            "can_reveal_passwords": True,
            "can_create_credentials": True,
            "can_edit_credentials": True,
            "can_delete_credentials": False,
            "can_generate_reports": True,
            "can_export_excel": True,
            "can_export_pdf": True,
            "can_view_analytics": True,
            "can_view_audit_logs": False,
            "can_manage_permissions": False,
            "can_setup_sample_data": False
        }
    },
    "admin": {
        "name": "مدير - Admin",
        "description": "صلاحيات إدارية كاملة",
        "permissions": {
            "can_view_clients": True,
            "can_create_clients": True,
            "can_edit_clients": True,
            "can_delete_clients": True,
            "can_import_clients": True,
            "can_view_own_logs": True,
            "can_view_all_logs": True,
            "can_create_work_logs": True,
            "can_edit_own_logs": True,
            "can_edit_all_logs": True,
            "can_delete_own_logs": True,
            "can_delete_all_logs": True,
            "can_view_credentials": True,
            "can_view_usernames": True,
            "can_view_emails": True,
            "can_reveal_passwords": True,
            "can_create_credentials": True,
            "can_edit_credentials": True,
            "can_delete_credentials": True,
            "can_generate_reports": True,
            "can_export_excel": True,
            "can_export_pdf": True,
            "can_view_analytics": True,
            "can_view_audit_logs": True,
            "can_manage_permissions": True,
            "can_setup_sample_data": True
        }
    }
}

# ============ PERMISSION MODELS FOR API ============

class UserPermissionResponse(BaseModel):
    id: str
    user_id: str
    user_name: str
    user_email: Optional[str]
    permission_level: str
    can_view_credentials: bool
    can_reveal_passwords: bool
    can_manage_permissions: bool
    is_active: bool
    granted_by: Optional[str]
    granted_at: datetime
    last_updated: datetime
    
    class Config:
        from_attributes = True

class PermissionUpdateRequest(BaseModel):
    permission_level: Optional[str] = None
    can_view_clients: Optional[bool] = None
    can_create_clients: Optional[bool] = None
    can_edit_clients: Optional[bool] = None
    can_delete_clients: Optional[bool] = None
    can_import_clients: Optional[bool] = None
    can_view_credentials: Optional[bool] = None
    can_reveal_passwords: Optional[bool] = None
    can_create_credentials: Optional[bool] = None
    can_edit_credentials: Optional[bool] = None
    can_delete_credentials: Optional[bool] = None
    can_generate_reports: Optional[bool] = None
    can_export_excel: Optional[bool] = None
    can_manage_permissions: Optional[bool] = None
    notes: Optional[str] = None

def log_work_reports_activity(
    db: Session,
    user_id: str,
    user_name: str, 
    action: str,
    table_name: str = None,
    record_id: str = None,
    before_value: dict = None,
    after_value: dict = None,
    ip_address: str = None,
    user_agent: str = None
):
    """Log audit activity for work reports module"""
    audit_log = WorkReportsAuditLog(
        user_id=user_id,
        user_name=user_name,
        action=action,
        table_name=table_name,
        record_id=record_id,
        before_value=before_value,
        after_value=after_value,
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(audit_log)
    db.commit()