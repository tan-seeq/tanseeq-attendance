"""
Marketing Visits System - Data Models and Business Logic
نظام الزيارات الخارجية التسويقية - نماذج البيانات وقواعد العمل
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum
import uuid

# Visit Status Enum
class VisitStatus(str, Enum):
    STARTED = "started"          # بدأت الزيارة
    COMPLETED = "completed"      # اكتملت الزيارة  
    CANCELLED = "cancelled"      # ألغيت الزيارة

# Visit Purpose Types
class VisitPurpose(str, Enum):
    CLIENT_MEETING = "client_meeting"        # لقاء عميل
    MARKETING = "marketing"                  # تسويق
    FOLLOW_UP = "follow_up"                 # متابعة
    NEW_CLIENT = "new_client"               # عميل جديد
    DOCUMENT_COLLECTION = "document_collection"  # جمع مستندات
    CONSULTATION = "consultation"            # استشارة
    SITE_VISIT = "site_visit"               # زيارة موقع
    OTHER = "other"                         # أخرى

# Visit Result Types  
class VisitResult(str, Enum):
    SUCCESSFUL = "successful"               # ناجحة
    PARTIALLY_SUCCESSFUL = "partially_successful"  # ناجحة جزئياً
    UNSUCCESSFUL = "unsuccessful"           # غير ناجحة
    RESCHEDULED = "rescheduled"            # أُجلت
    CLIENT_UNAVAILABLE = "client_unavailable"  # العميل غير متاح

# GPS Location Model
class GPSLocation(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    accuracy: Optional[float] = None  # GPS accuracy in meters
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Visit Report Model (التقرير الإلزامي)
class VisitReport(BaseModel):
    summary: str = Field(..., min_length=20, description="ملخص الزيارة")
    details: str = Field(..., min_length=50, description="تفاصيل الزيارة")
    result: VisitResult = Field(..., description="نتيجة الزيارة")
    next_actions: str = Field(..., min_length=10, description="الإجراءات القادمة")
    attachments: Optional[List[str]] = Field(default_factory=list, description="المرفقات (اختياري)")
    client_feedback: Optional[str] = Field(None, description="ملاحظات العميل")
    
    @validator('summary')
    def validate_summary(cls, v):
        if len(v.strip()) < 20:
            raise ValueError('ملخص الزيارة يجب أن يحتوي على 20 حرف على الأقل')
        return v.strip()
    
    @validator('details')
    def validate_details(cls, v):
        if len(v.strip()) < 50:
            raise ValueError('تفاصيل الزيارة يجب أن تحتوي على 50 حرف على الأقل')
        return v.strip()

# Marketing Visit Model (النموذج الأساسي)
class MarketingVisit(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str = Field(..., description="معرف الموظف")
    employee_name: str = Field(..., description="اسم الموظف")
    
    # Visit Information
    client_name: str = Field(..., min_length=2, description="اسم العميل")
    location_name: str = Field(..., min_length=2, description="اسم المكان")
    area: str = Field(..., min_length=2, description="المنطقة")
    purpose: VisitPurpose = Field(..., description="غرض الزيارة")
    purpose_details: Optional[str] = Field(None, description="تفاصيل إضافية للغرض")
    
    # Timing (Server-generated timestamps)
    start_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = Field(None, description="وقت الإنهاء")
    duration_minutes: Optional[int] = Field(None, description="مدة الزيارة بالدقائق")
    
    # GPS Locations
    start_location: Optional[GPSLocation] = Field(None, description="موقع البدء")
    end_location: Optional[GPSLocation] = Field(None, description="موقع الإنهاء")
    
    # Visit Status and Report
    status: VisitStatus = Field(default=VisitStatus.STARTED)
    report: Optional[VisitReport] = Field(None, description="تقرير الزيارة")
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Super Admin Notification
    admin_notified: bool = Field(default=False, description="تم إشعار السوبر أدمن")

# Request Models for API
class StartVisitRequest(BaseModel):
    client_name: str = Field(..., min_length=2, max_length=100)
    location_name: str = Field(..., min_length=2, max_length=100)
    area: str = Field(..., min_length=2, max_length=50)
    purpose: VisitPurpose
    purpose_details: Optional[str] = Field(None, max_length=500)
    gps_location: Optional[GPSLocation] = None

class CompleteVisitRequest(BaseModel):
    visit_report: VisitReport
    gps_location: Optional[GPSLocation] = None

# Response Models
class VisitResponse(BaseModel):
    id: str
    employee_id: str
    employee_name: str
    client_name: str
    location_name: str
    area: str
    purpose: str
    purpose_details: Optional[str]
    start_time: str
    end_time: Optional[str] = None
    duration_minutes: Optional[int] = None
    status: str
    report: Optional[Dict[str, Any]] = None
    start_location: Optional[Dict[str, Any]] = None
    end_location: Optional[Dict[str, Any]] = None

class ActiveVisitResponse(BaseModel):
    id: str
    client_name: str
    location_name: str
    area: str
    purpose: str
    start_time: str
    elapsed_minutes: int
    can_complete: bool = True

# Database Helper Functions
class MarketingVisitsDB:
    """Helper class for database operations"""
    
    @staticmethod
    def visit_to_dict(visit: MarketingVisit) -> Dict[str, Any]:
        """Convert MarketingVisit to dictionary for MongoDB storage"""
        data = visit.dict()
        # Convert datetime objects to UTC ISO strings for MongoDB
        if data['start_time']:
            data['start_time'] = data['start_time'].isoformat()
        if data['end_time']:
            data['end_time'] = data['end_time'].isoformat()
        if data['created_at']:
            data['created_at'] = data['created_at'].isoformat()
        if data['updated_at']:
            data['updated_at'] = data['updated_at'].isoformat()
        
        # Handle GPS locations
        if data.get('start_location') and data['start_location'].get('timestamp'):
            data['start_location']['timestamp'] = data['start_location']['timestamp'].isoformat()
        if data.get('end_location') and data['end_location'].get('timestamp'):
            data['end_location']['timestamp'] = data['end_location']['timestamp'].isoformat()
            
        return data
    
    @staticmethod
    def dict_to_visit(data: Dict[str, Any]) -> MarketingVisit:
        """Convert dictionary from MongoDB to MarketingVisit"""
        # Convert ISO strings back to datetime objects
        if isinstance(data.get('start_time'), str):
            data['start_time'] = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
        if isinstance(data.get('end_time'), str):
            data['end_time'] = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
        if isinstance(data.get('updated_at'), str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
            
        # Handle GPS locations timestamps
        if data.get('start_location') and isinstance(data['start_location'].get('timestamp'), str):
            data['start_location']['timestamp'] = datetime.fromisoformat(
                data['start_location']['timestamp'].replace('Z', '+00:00')
            )
        if data.get('end_location') and isinstance(data['end_location'].get('timestamp'), str):
            data['end_location']['timestamp'] = datetime.fromisoformat(
                data['end_location']['timestamp'].replace('Z', '+00:00')
            )
            
        # Remove MongoDB _id if present
        if '_id' in data:
            del data['_id']
            
        return MarketingVisit(**data)

# Purpose Translations (Arabic/English)
PURPOSE_TRANSLATIONS = {
    VisitPurpose.CLIENT_MEETING: {"ar": "لقاء عميل", "en": "Client Meeting"},
    VisitPurpose.MARKETING: {"ar": "تسويق", "en": "Marketing"},
    VisitPurpose.FOLLOW_UP: {"ar": "متابعة", "en": "Follow Up"},
    VisitPurpose.NEW_CLIENT: {"ar": "عميل جديد", "en": "New Client"},
    VisitPurpose.DOCUMENT_COLLECTION: {"ar": "جمع مستندات", "en": "Document Collection"},
    VisitPurpose.CONSULTATION: {"ar": "استشارة", "en": "Consultation"},
    VisitPurpose.SITE_VISIT: {"ar": "زيارة موقع", "en": "Site Visit"},
    VisitPurpose.OTHER: {"ar": "أخرى", "en": "Other"}
}

RESULT_TRANSLATIONS = {
    VisitResult.SUCCESSFUL: {"ar": "ناجحة", "en": "Successful"},
    VisitResult.PARTIALLY_SUCCESSFUL: {"ar": "ناجحة جزئياً", "en": "Partially Successful"},
    VisitResult.UNSUCCESSFUL: {"ar": "غير ناجحة", "en": "Unsuccessful"},
    VisitResult.RESCHEDULED: {"ar": "أُجلت", "en": "Rescheduled"},
    VisitResult.CLIENT_UNAVAILABLE: {"ar": "العميل غير متاح", "en": "Client Unavailable"}
}