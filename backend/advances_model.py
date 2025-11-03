"""
Employee Advances & Custody Management System
نظام إدارة السلف والعهد للموظفين

Features:
- Employee advance/custody management
- Invoice/receipt attachments
- Automatic deduction calculations
- Balance tracking
- Super admin oversight
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum
import uuid
from uae_datetime_utils import get_uae_now

# Transaction Types
class TransactionType(str, Enum):
    ADVANCE = "advance"           # سلفة
    CUSTODY = "custody"           # عهدة
    EXPENSE = "expense"           # مصروف
    RETURN = "return"             # إرجاع (سداد سلفة/عهدة)
    ADJUSTMENT = "adjustment"     # تسوية
    ADVANCE_SETTLEMENT = "advance_settlement"  # تسوية سلفة مع الراتب

# Transaction Status
class TransactionStatus(str, Enum):
    PENDING = "pending"           # في الانتظار
    APPROVED = "approved"         # معتمد
    REJECTED = "rejected"         # مرفوض
    COMPLETED = "completed"       # مكتمل

# Expense Categories
class ExpenseCategory(str, Enum):
    TRANSPORTATION = "transportation"     # مواصلات
    MEALS = "meals"                      # وجبات
    ACCOMMODATION = "accommodation"       # إقامة
    SUPPLIES = "supplies"                # لوازم مكتبية
    FUEL = "fuel"                        # وقود
    MAINTENANCE = "maintenance"          # صيانة
    CLIENT_ENTERTAINMENT = "client_entertainment"  # ضيافة عملاء
    TRAVEL = "travel"                    # سفر
    COMMUNICATIONS = "communications"     # اتصالات
    OTHER = "other"                      # أخرى

# File Attachment Model
class Attachment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    file_type: str  # MIME type
    uploaded_at: datetime = Field(default_factory=lambda: get_uae_now())  # UAE timezone

# Base Transaction Model
class AdvanceTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str
    employee_name: str
    
    # Transaction Details
    transaction_type: TransactionType
    amount: float = Field(..., gt=0, description="المبلغ")
    currency: str = Field(default="AED", description="العملة")
    
    # Expense Details (for expense transactions)
    category: Optional[ExpenseCategory] = None
    description: str = Field(..., min_length=5, description="الوصف")
    expense_date: Optional[str] = None  # For expenses
    
    # Attachments (Invoices/Receipts)
    attachments: List[Attachment] = Field(default_factory=list)
    
    # Status & Approval
    status: TransactionStatus = Field(default=TransactionStatus.PENDING)
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: get_uae_now())  # UAE timezone
    updated_at: datetime = Field(default_factory=lambda: get_uae_now())  # UAE timezone
    notes: Optional[str] = None

    @validator('description')
    def validate_description(cls, v):
        if len(v.strip()) < 5:
            raise ValueError('الوصف يجب أن يحتوي على 5 أحرف على الأقل')
        return v.strip()

# Employee Balance Model
class EmployeeBalance(BaseModel):
    employee_id: str = Field(..., unique=True)
    employee_name: str
    
    # Balance Details
    total_advances: float = Field(default=0.0, description="إجمالي السلف")
    total_custody: float = Field(default=0.0, description="إجمالي العهد")
    total_expenses: float = Field(default=0.0, description="إجمالي المصروفات")
    total_returns: float = Field(default=0.0, description="إجمالي المُرجع")
    
    # Calculated Balances
    remaining_advance: float = Field(default=0.0, description="السلفة المتبقية")
    remaining_custody: float = Field(default=0.0, description="العهدة المتبقية")
    total_available: float = Field(default=0.0, description="إجمالي الرصيد المتاح")
    
    # Metadata
    last_transaction_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: get_uae_now())  # UAE timezone
    updated_at: datetime = Field(default_factory=lambda: get_uae_now())  # UAE timezone

# Request Models
class CreateAdvanceRequest(BaseModel):
    employee_id: Optional[str] = None  # Optional - يتم أخذه من current_user إذا لم يتم تحديده
    transaction_type: TransactionType
    amount: float = Field(..., gt=0)
    description: str = Field(..., min_length=5)
    category: Optional[ExpenseCategory] = None
    expense_date: Optional[str] = None
    notes: Optional[str] = None

class CreateExpenseRequest(BaseModel):
    amount: float = Field(..., gt=0)
    category: ExpenseCategory
    description: str = Field(..., min_length=5)
    expense_date: str
    notes: Optional[str] = None

class ApprovalRequest(BaseModel):
    status: TransactionStatus
    notes: Optional[str] = None

class RepaymentRequest(BaseModel):
    employee_id: str
    amount: float = Field(..., gt=0)
    repayment_date: Optional[str] = None  # YYYY-MM-DD
    method: Optional[str] = None          # cash/bank/other
    reference: Optional[str] = None
    notes: Optional[str] = None

# Response Models
class TransactionResponse(BaseModel):
    id: str
    employee_id: str
    employee_name: str
    transaction_type: str
    amount: float
    currency: str
    category: Optional[str] = None
    description: str
    expense_date: Optional[str] = None
    attachments: List[Dict[str, Any]]
    status: str
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    created_at: str
    notes: Optional[str] = None

# Settlement Request Model
class AdvanceSettlementRequest(BaseModel):
    employee_id: str
    settlement_amount: float
    settlement_date: str  # YYYY-MM-DD format
    salary_month: str     # e.g., "2024-10"
    notes: Optional[str] = None

class BalanceResponse(BaseModel):
    employee_id: str
    employee_name: str
    total_advances: float
    total_custody: float
    total_expenses: float
    total_returns: float
    remaining_advance: float
    remaining_custody: float
    total_available: float  # Total available balance (remaining_advance + remaining_custody)
    last_transaction_date: Optional[str] = None

# Database Helper Functions
class AdvancesDB:
    """Helper class for database operations"""
    
    @staticmethod
    def transaction_to_dict(transaction: AdvanceTransaction) -> Dict[str, Any]:
        """Convert AdvanceTransaction to dictionary for MongoDB storage"""
        data = transaction.dict()
        
        # Convert datetime objects to UTC ISO strings for MongoDB
        if data['created_at']:
            data['created_at'] = data['created_at'].isoformat()
        if data['updated_at']:
            data['updated_at'] = data['updated_at'].isoformat()
        if data['approved_at']:
            data['approved_at'] = data['approved_at'].isoformat()
            
        # Handle attachments timestamps
        for attachment in data.get('attachments', []):
            if isinstance(attachment.get('uploaded_at'), datetime):
                attachment['uploaded_at'] = attachment['uploaded_at'].isoformat()
                
        return data
    
    @staticmethod
    def dict_to_transaction(data: Dict[str, Any]) -> AdvanceTransaction:
        """Convert dictionary from MongoDB to AdvanceTransaction"""
        # Convert ISO strings back to datetime objects
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
        if isinstance(data.get('updated_at'), str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
        if isinstance(data.get('approved_at'), str):
            data['approved_at'] = datetime.fromisoformat(data['approved_at'].replace('Z', '+00:00'))
            
        # Handle attachments timestamps
        for attachment in data.get('attachments', []):
            if isinstance(attachment.get('uploaded_at'), str):
                attachment['uploaded_at'] = datetime.fromisoformat(
                    attachment['uploaded_at'].replace('Z', '+00:00')
                )
        
        # Remove MongoDB _id if present
        if '_id' in data:
            del data['_id']
            
        return AdvanceTransaction(**data)
    
    @staticmethod
    async def calculate_employee_balance(db, employee_id: str) -> EmployeeBalance:
        """Calculate employee balance from all transactions"""
        transactions = await db.advance_transactions.find({
            "employee_id": employee_id,
            "status": TransactionStatus.APPROVED
        }).to_list(1000)
        
        # Get employee info
        employee = await db.users.find_one({"id": employee_id})
        employee_name = employee.get("name", "Unknown") if employee else "Unknown"
        
        # Initialize totals
        totals = {
            "total_advances": 0.0,
            "total_custody": 0.0,
            "total_expenses": 0.0,
            "total_returns": 0.0
        }
        
        last_transaction_date = None
        
        # Calculate totals from transactions
        for transaction in transactions:
            amount = float(transaction.get("amount", 0))
            tx_type = transaction.get("transaction_type")
            
            if tx_type == TransactionType.ADVANCE:
                totals["total_advances"] += amount
            elif tx_type == TransactionType.CUSTODY:
                totals["total_custody"] += amount
            elif tx_type == TransactionType.EXPENSE:
                totals["total_expenses"] += amount
            elif tx_type == TransactionType.RETURN or tx_type == TransactionType.ADVANCE_SETTLEMENT:
                totals["total_returns"] += amount
            
            # Track last transaction date
            tx_date = transaction.get("created_at")
            if isinstance(tx_date, str):
                tx_date = datetime.fromisoformat(tx_date.replace('Z', '+00:00'))
            if not last_transaction_date or (tx_date and tx_date > last_transaction_date):
                last_transaction_date = tx_date
        
        # Calculate remaining balances according to business rules:
        # Returns and advance_settlement reduce advances balance
        adv_and_cust_total = totals["total_advances"] + totals["total_custody"]
        proportion_adv = (totals["total_advances"] / adv_and_cust_total) if adv_and_cust_total > 0 else 0
        proportion_cust = (totals["total_custody"] / adv_and_cust_total) if adv_and_cust_total > 0 else 0
        
        remaining_advance = totals["total_advances"] - totals["total_returns"] * proportion_adv
        # For custody, we deduct all expenses and proportional returns
        remaining_custody = totals["total_custody"] - totals["total_expenses"] - totals["total_returns"] * proportion_cust
        
        # Ensure no negative values
        remaining_advance = max(0, remaining_advance)
        remaining_custody = max(0, remaining_custody)
        
        # Calculate total available balance
        total_available = remaining_advance + remaining_custody
        
        return EmployeeBalance(
            employee_id=employee_id,
            employee_name=employee_name,
            total_advances=totals["total_advances"],
            total_custody=totals["total_custody"],
            total_expenses=totals["total_expenses"],
            total_returns=totals["total_returns"],
            remaining_advance=max(0, remaining_advance),
            remaining_custody=max(0, remaining_custody),
            total_available=total_available,
            last_transaction_date=last_transaction_date
        )

# Arabic Translations
TRANSACTION_TYPE_AR = {
    TransactionType.ADVANCE: "سلفة",
    TransactionType.CUSTODY: "عهدة", 
    TransactionType.EXPENSE: "مصروف",
    TransactionType.RETURN: "إرجاع",
    TransactionType.ADJUSTMENT: "تسوية",
    TransactionType.ADVANCE_SETTLEMENT: "تسوية سلفة مع الراتب"
}

TRANSACTION_STATUS_AR = {
    TransactionStatus.PENDING: "في الانتظار",
    TransactionStatus.APPROVED: "معتمد",
    TransactionStatus.REJECTED: "مرفوض",
    TransactionStatus.COMPLETED: "مكتمل"
}

EXPENSE_CATEGORY_AR = {
    ExpenseCategory.TRANSPORTATION: "مواصلات",
    ExpenseCategory.MEALS: "وجبات",
    ExpenseCategory.ACCOMMODATION: "إقامة",
    ExpenseCategory.SUPPLIES: "لوازم مكتبية",
    ExpenseCategory.FUEL: "وقود",
    ExpenseCategory.MAINTENANCE: "صيانة",
    ExpenseCategory.CLIENT_ENTERTAINMENT: "ضيافة عملاء",
    ExpenseCategory.TRAVEL: "سفر",
    ExpenseCategory.COMMUNICATIONS: "اتصالات",
    ExpenseCategory.OTHER: "أخرى"
}
