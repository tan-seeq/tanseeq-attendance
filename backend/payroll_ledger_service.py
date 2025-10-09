"""
Payroll Ledger Service - نظام القيود المحاسبية للرواتب
نظام تلقائي بالكامل - كل حدث يولد قيد تلقائياً
"""

from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone
from typing import List, Dict, Optional
import uuid
import logging
from uae_datetime_utils import to_iso_string_uae, get_uae_now

logger = logging.getLogger(__name__)

# أنواع القيود
class LedgerSourceType:
    ATTENDANCE_DEDUCTION = "ATTENDANCE_DEDUCTION"  # خصم تأخير/غياب
    LEAVE_ADJUSTMENT = "LEAVE_ADJUSTMENT"  # أجر/خصم مرتبط بالإجازة
    MANUAL_DEDUCTION = "MANUAL_DEDUCTION"  # خصم يدوي
    ADVANCE_INSTALLMENT = "ADVANCE_INSTALLMENT"  # قسط سلفة
    CUSTODY_ADJUSTMENT = "CUSTODY_ADJUSTMENT"  # تعديل/تسوية عهدة


class PayrollLedgerService:
    """خدمة إدارة القيود المحاسبية للرواتب"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.ledger_collection = db.payroll_ledger
    
    async def create_entry(
        self,
        employee_id: str,
        cycle_id: str,
        source_type: str,
        source_id: str,
        amount: float,
        description: str,
        created_by: str,
        description_ar: str = "",
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        إنشاء قيد جديد في دفتر الأستاذ مع ضمان Strict Idempotency
        Create new ledger entry with strict idempotency guarantee
        
        Idempotency Strategy:
        - Uses composite key: cycle_id + employee_id + source_type + source_id
        - Returns existing entry if duplicate detected (no exception)
        - Atomic upsert operation to prevent race conditions
        """
        # إنشاء مفتاح فريد للتأكد من عدم التكرار
        idempotency_key = f"{cycle_id}_{employee_id}_{source_type}_{source_id}"
        
        # التحقق من وجود القيد مسبقاً (idempotency check)
        existing = await self.ledger_collection.find_one(
            {"idempotency_key": idempotency_key},
            {"_id": 0}  # Exclude MongoDB _id
        )
        
        if existing:
            # القيد موجود مسبقاً - إرجاعه مباشرة (idempotent)
            logger.info(f"Idempotency: Entry already exists for key {idempotency_key[:50]}...")
            return existing
        
        # إنشاء القيد الجديد
        entry = {
            "id": str(uuid.uuid4()),
            "idempotency_key": idempotency_key,
            "employee_id": employee_id,
            "cycle_id": cycle_id,
            "source_type": source_type,
            "source_id": source_id,
            "amount": amount,
            "description": description,
            "description_ar": description_ar or description,
            "metadata": metadata or {},
            "created_by": created_by,
            "created_at": to_iso_string_uae(),
            "is_reversed": False,
            "reversed_by": None,
            "reversed_at": None,
            "reversal_reason": None
        }
        
        try:
            # Atomic insert with duplicate key handling
            await self.ledger_collection.insert_one(entry)
            logger.info(f"Created ledger entry: {entry['id']} for {source_type}")
        except Exception as e:
            # Handle potential race condition (duplicate key error)
            if "duplicate" in str(e).lower() or "E11000" in str(e):
                logger.warning(f"Race condition detected for {idempotency_key[:50]}... - fetching existing")
                existing = await self.ledger_collection.find_one(
                    {"idempotency_key": idempotency_key},
                    {"_id": 0}
                )
                if existing:
                    return existing
            raise  # Re-raise if not a duplicate key error
        
        # إزالة _id من MongoDB للتسهيل
        if "_id" in entry:
            del entry["_id"]
        
        return entry
    
    async def reverse_entry(
        self,
        entry_id: str,
        reversed_by: str,
        reason: str
    ) -> Dict:
        """
        عكس قيد (Reversal) - لا حذف مدمّر
        """
        
        # جلب القيد الأصلي
        original_entry = await self.ledger_collection.find_one({"id": entry_id})
        if not original_entry:
            raise ValueError(f"Entry {entry_id} not found")
        
        if original_entry.get("is_reversed"):
            raise ValueError(f"Entry {entry_id} already reversed")
        
        # تحديث القيد الأصلي
        await self.ledger_collection.update_one(
            {"id": entry_id},
            {
                "$set": {
                    "is_reversed": True,
                    "reversed_by": reversed_by,
                    "reversed_at": to_iso_string_uae(),
                    "reversal_reason": reason
                }
            }
        )
        
        # إنشاء قيد عكسي
        reversal_entry = {
            "id": str(uuid.uuid4()),
            "idempotency_key": f"reversal_{original_entry['idempotency_key']}",
            "employee_id": original_entry["employee_id"],
            "cycle_id": original_entry["cycle_id"],
            "source_type": original_entry["source_type"],
            "source_id": original_entry["source_id"],
            "amount": -original_entry["amount"],  # عكس المبلغ
            "description": f"عكس: {original_entry['description']}",
            "description_ar": f"عكس: {original_entry['description']}",
            "metadata": {
                "original_entry_id": entry_id,
                "reversal_reason": reason
            },
            "created_by": reversed_by,
            "created_at": to_iso_string_uae(),
            "is_reversed": False,
            "reversed_by": None,
            "reversed_at": None,
            "reversal_reason": None
        }
        
        await self.ledger_collection.insert_one(reversal_entry)
        return reversal_entry
    
    async def get_entries_for_cycle(
        self,
        cycle_id: str,
        employee_id: Optional[str] = None
    ) -> List[Dict]:
        """
        جلب جميع القيود لدورة معينة
        """
        query = {"cycle_id": cycle_id}
        if employee_id:
            query["employee_id"] = employee_id
        
        entries = await self.ledger_collection.find(query).to_list(None)
        
        # Clean up MongoDB ObjectId for JSON serialization
        for entry in entries:
            if "_id" in entry:
                del entry["_id"]
        
        return entries
    
    async def get_employee_summary(
        self,
        cycle_id: str,
        employee_id: str
    ) -> Dict:
        """
        حساب ملخص القيود لموظف في دورة معينة
        """
        entries = await self.get_entries_for_cycle(cycle_id, employee_id)
        
        # تجميع حسب نوع القيد
        summary = {
            "attendance_deductions": 0,
            "leave_adjustments": 0,
            "manual_deductions": 0,
            "advance_installments": 0,
            "custody_adjustments": 0,
            "total_adjustments": 0,
            "entries_count": len(entries),
            "entries_by_type": {}
        }
        
        for entry in entries:
            source_type = entry["source_type"]
            amount = entry["amount"]
            
            if source_type == LedgerSourceType.ATTENDANCE_DEDUCTION:
                summary["attendance_deductions"] += abs(amount)
            elif source_type == LedgerSourceType.LEAVE_ADJUSTMENT:
                summary["leave_adjustments"] += amount
            elif source_type == LedgerSourceType.MANUAL_DEDUCTION:
                summary["manual_deductions"] += abs(amount)
            elif source_type == LedgerSourceType.ADVANCE_INSTALLMENT:
                summary["advance_installments"] += abs(amount)
            elif source_type == LedgerSourceType.CUSTODY_ADJUSTMENT:
                summary["custody_adjustments"] += amount
            
            summary["total_adjustments"] += amount
            
            # تجميع حسب النوع
            if source_type not in summary["entries_by_type"]:
                summary["entries_by_type"][source_type] = []
            summary["entries_by_type"][source_type].append(entry)
        
        return summary
    
    async def recalculate_employee_payroll(
        self,
        cycle_id: str,
        employee_id: str,
        base_salary: float,
        allowances: float = 0
    ) -> Dict:
        """
        إعادة حساب راتب الموظف بناءً على القيود
        """
        summary = await self.get_employee_summary(cycle_id, employee_id)
        
        # حساب صافي الراتب
        gross_salary = base_salary + allowances
        
        total_deductions = (
            summary["attendance_deductions"] +
            summary["manual_deductions"] +
            summary["advance_installments"]
        )
        
        # Leave adjustments و custody adjustments يمكن أن تكون موجبة أو سالبة
        adjustments = summary["leave_adjustments"] + summary["custody_adjustments"]
        
        net_salary = gross_salary + adjustments - total_deductions
        
        return {
            "employee_id": employee_id,
            "cycle_id": cycle_id,
            "base_salary": base_salary,
            "allowances": allowances,
            "gross_salary": gross_salary,
            "attendance_deductions": summary["attendance_deductions"],
            "leave_adjustments": summary["leave_adjustments"],
            "manual_deductions": summary["manual_deductions"],
            "advance_installments": summary["advance_installments"],
            "custody_adjustments": summary["custody_adjustments"],
            "total_deductions": total_deductions,
            "total_adjustments": adjustments,
            "net_salary": max(0, net_salary),  # لا يمكن أن يكون سالب
            "ledger_entries_count": summary["entries_count"]
        }


# ============================================
# Trigger Functions - تنفيذ تلقائي
# ============================================

async def trigger_attendance_deduction(
    db: AsyncIOMotorDatabase,
    employee_id: str,
    cycle_id: str,
    attendance_record_id: str,
    late_minutes: int,
    deduction_amount: float,
    created_by: str = "system"
):
    """
    Trigger: عند إقفال سجل الحضور مع تأخير
    يولد قيد ATTENDANCE_DEDUCTION تلقائياً
    """
    ledger = PayrollLedgerService(db)
    
    await ledger.create_entry(
        employee_id=employee_id,
        cycle_id=cycle_id,
        source_type=LedgerSourceType.ATTENDANCE_DEDUCTION,
        source_id=attendance_record_id,
        amount=-abs(deduction_amount),  # سالب للخصم
        description=f"خصم تأخير: {late_minutes} دقيقة",
        created_by=created_by,
        metadata={
            "late_minutes": late_minutes,
            "attendance_record_id": attendance_record_id
        }
    )


async def trigger_leave_adjustment(
    db: AsyncIOMotorDatabase,
    employee_id: str,
    cycle_id: str,
    leave_id: str,
    leave_type: str,
    days: int,
    adjustment_amount: float,
    created_by: str = "system"
):
    """
    Trigger: عند الموافقة على إجازة
    يولد قيد LEAVE_ADJUSTMENT تلقائياً (موجب أو سالب حسب النوع)
    """
    ledger = PayrollLedgerService(db)
    
    description = f"إجازة {leave_type}: {days} أيام"
    
    await ledger.create_entry(
        employee_id=employee_id,
        cycle_id=cycle_id,
        source_type=LedgerSourceType.LEAVE_ADJUSTMENT,
        source_id=leave_id,
        amount=adjustment_amount,  # سالب لإجازة بدون أجر، موجب للمدفوعة
        description=description,
        created_by=created_by,
        metadata={
            "leave_id": leave_id,
            "leave_type": leave_type,
            "days": days
        }
    )


async def trigger_advance_installment(
    db: AsyncIOMotorDatabase,
    employee_id: str,
    cycle_id: str,
    advance_id: str,
    installment_amount: float,
    created_by: str = "system"
):
    """
    Trigger: عند فتح دورة جديدة مع وجود جدول أقساط نشط
    يولد قيد ADVANCE_INSTALLMENT تلقائياً
    """
    ledger = PayrollLedgerService(db)
    
    await ledger.create_entry(
        employee_id=employee_id,
        cycle_id=cycle_id,
        source_type=LedgerSourceType.ADVANCE_INSTALLMENT,
        source_id=f"{advance_id}_{cycle_id}",
        amount=-abs(installment_amount),  # سالب للخصم
        description=f"قسط سلفة شهري: {installment_amount:.2f} درهم",
        created_by=created_by,
        metadata={
            "advance_id": advance_id,
            "installment_amount": installment_amount
        }
    )


async def trigger_manual_deduction(
    db: AsyncIOMotorDatabase,
    employee_id: str,
    cycle_id: str,
    deduction_id: str,
    amount: float,
    reason: str,
    created_by: str
):
    """
    Trigger: عند إضافة خصم يدوي
    يولد قيد MANUAL_DEDUCTION تلقائياً
    """
    ledger = PayrollLedgerService(db)
    
    await ledger.create_entry(
        employee_id=employee_id,
        cycle_id=cycle_id,
        source_type=LedgerSourceType.MANUAL_DEDUCTION,
        source_id=deduction_id,
        amount=-abs(amount),  # سالب للخصم
        description=f"خصم يدوي: {reason}",
        created_by=created_by,
        metadata={
            "deduction_id": deduction_id,
            "reason": reason
        }
    )


async def trigger_custody_adjustment(
    db: AsyncIOMotorDatabase,
    employee_id: str,
    cycle_id: str,
    custody_id: str,
    delta_amount: float,
    reason: str,
    created_by: str
):
    """
    Trigger: عند تعديل/تسوية عهدة
    يولد قيد CUSTODY_ADJUSTMENT تلقائياً
    """
    ledger = PayrollLedgerService(db)
    
    await ledger.create_entry(
        employee_id=employee_id,
        cycle_id=cycle_id,
        source_type=LedgerSourceType.CUSTODY_ADJUSTMENT,
        source_id=custody_id,
        amount=delta_amount,  # موجب أو سالب حسب التعديل
        description=f"تعديل عهدة: {reason}",
        created_by=created_by,
        metadata={
            "custody_id": custody_id,
            "reason": reason,
            "delta_amount": delta_amount
        }
    )
