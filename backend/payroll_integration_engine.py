"""
محرك الربط التكاملي للرواتب والخصومات والسلف
Integrated Payroll-Deductions-Advances Engine

Core Functions:
- Auto-link deductions to open payroll cycles
- Generate installment schedules for advances
- Real-time salary recalculation
- Deduction ceiling enforcement
- Cross-system synchronization
"""

from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
import uuid
import calendar
from dateutil.relativedelta import relativedelta

from payroll_models import (
    PayrollCycle, PayrollStatus, PayrollLineItem, PayrollItemType,
    InstallmentSchedule, IndividualInstallment, InstallmentStatus,
    EmployeePayrollSummary, DeductionCeiling, EmployeeDeductionCeiling,
    PayrollDB, get_month_boundaries, validate_deduction_ceiling
)

try:
    from attendance_models import (
        PayrollDeduction, DeductionType, DeductionCategory
    )
except ImportError:
    # Handle case where attendance_models might not be available
    PayrollDeduction = None
    DeductionType = None  
    DeductionCategory = None

try:
    from advances_model import (
        AdvanceTransaction, TransactionType, TransactionStatus
    )
except ImportError:
    # Handle case where advances_model might not be available
    AdvanceTransaction = None
    TransactionType = None
    TransactionStatus = None

class PayrollIntegrationEngine:
    """محرك الربط التكاملي للرواتب"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    # ====================
    # PAYROLL CYCLE MANAGEMENT
    # ====================
    
    async def create_payroll_cycle(self, month: str, created_by: str, created_by_name: str, 
                                 notes: Optional[str] = None) -> PayrollCycle:
        """إنشاء دورة راتب جديدة"""
        
        # التحقق من وجود دورة للشهر
        existing = await self.db.payroll_cycles.find_one({"month": month})
        if existing:
            raise ValueError(f"دورة راتب لشهر {month} موجودة بالفعل")
        
        # حساب التواريخ
        year, month_num = map(int, month.split('-'))
        start_date, end_date = get_month_boundaries(year, month_num)
        cutoff_date = end_date + timedelta(days=5)  # 5 أيام بعد نهاية الشهر
        
        # إنشاء اسم العرض
        month_names = {
            1: "يناير", 2: "فبراير", 3: "مارس", 4: "أبريل", 5: "مايو", 6: "يونيو",
            7: "يوليو", 8: "أغسطس", 9: "سبتمبر", 10: "أكتوبر", 11: "نوفمبر", 12: "ديسمبر"
        }
        display_name = f"دورة راتب {month_names.get(month_num, month_num)} {year}"
        
        # إنشاء الدورة
        cycle = PayrollCycle(
            month=month,
            year=year,
            display_name=display_name,
            start_date=start_date,
            end_date=end_date,
            cutoff_date=cutoff_date,
            created_by=created_by,
            created_by_name=created_by_name,
            notes=notes
        )
        
        # حفظ في قاعدة البيانات
        cycle_data = PayrollDB.prepare_for_mongo(cycle.dict())
        await self.db.payroll_cycles.insert_one(cycle_data)
        
        return cycle
    
    async def get_open_payroll_cycle(self) -> Optional[PayrollCycle]:
        """جلب الدورة المفتوحة الحالية"""
        cycle_data = await self.db.payroll_cycles.find_one({
            "status": PayrollStatus.OPEN,
            "is_locked": False
        })
        
        if cycle_data:
            cycle_data = PayrollDB.parse_from_mongo(cycle_data)
            return PayrollCycle(**cycle_data)
        
        return None
    
    async def lock_payroll_cycle(self, cycle_id: str, locked_by: str, locked_by_name: str,
                               lock_reason: Optional[str] = None) -> bool:
        """قفل دورة راتب"""
        
        result = await self.db.payroll_cycles.update_one(
            {"id": cycle_id, "is_locked": False},
            {
                "$set": {
                    "is_locked": True,
                    "status": PayrollStatus.CLOSED,
                    "locked_by": locked_by,
                    "locked_by_name": locked_by_name,
                    "locked_at": get_uae_now(),  # UAE timezone
                    "lock_reason": lock_reason
                }
            }
        )
        
        return result.modified_count > 0
    
    async def unlock_payroll_cycle(self, cycle_id: str, unlocked_by: str, unlock_reason: str) -> bool:
        """فتح دورة راتب مقفولة (سوبر أدمن فقط)"""
        
        # سجل الفتح في audit log
        await self.log_payroll_activity(
            cycle_id=cycle_id,
            action="unlock_cycle",
            performed_by=unlocked_by,
            details=f"فتح الدورة. السبب: {unlock_reason}"
        )
        
        result = await self.db.payroll_cycles.update_one(
            {"id": cycle_id},
            {
                "$set": {
                    "is_locked": False,
                    "status": PayrollStatus.OPEN,
                    "locked_by": None,
                    "locked_by_name": None,
                    "locked_at": None,
                    "lock_reason": None
                }
            }
        )
        
        return result.modified_count > 0
    
    # ====================
    # AUTOMATIC DEDUCTION LINKING
    # ====================
    
    async def link_deduction_to_payroll(self, deduction: PayrollDeduction) -> bool:
        """ربط خصم تلقائياً بدورة الراتب المناسبة"""
        
        # تحديد الشهر المناسب للخصم
        deduction_month = deduction.date.strftime("%Y-%m")
        
        # البحث عن دورة مفتوحة لنفس الشهر
        target_cycle = await self.db.payroll_cycles.find_one({
            "month": deduction_month,
            "status": PayrollStatus.OPEN,
            "is_locked": False
        })
        
        # إذا لم توجد دورة مفتوحة، جرب الشهر التالي
        if not target_cycle:
            next_month_date = deduction.date.replace(day=1) + relativedelta(months=1)
            next_month = next_month_date.strftime("%Y-%m")
            
            target_cycle = await self.db.payroll_cycles.find_one({
                "month": next_month,
                "status": PayrollStatus.OPEN,
                "is_locked": False
            })
        
        # إذا لم توجد دورة مناسبة، أنشئ تحذير
        if not target_cycle:
            await self.create_deduction_warning(deduction)
            return False
        
        # إنشاء عنصر في كشف الراتب
        line_item = PayrollLineItem(
            payroll_cycle_id=target_cycle["id"],
            employee_id=deduction.employee_id,
            employee_name=deduction.employee_name,
            item_type=self._map_deduction_to_item_type(deduction.deduction_type),
            source_type="attendance_deduction",
            source_id=deduction.id,
            source_reference=f"خصم حضور - {deduction.date}",
            description=deduction.reason,
            description_ar=deduction.category_ar,
            amount=-abs(deduction.amount),  # سالب للخصومات
            is_system_generated=True,
            is_editable=False,
            created_by="system",
            created_by_name="النظام التلقائي"
        )
        
        # حفظ عنصر الراتب
        item_data = PayrollDB.prepare_for_mongo(line_item.dict())
        await self.db.payroll_line_items.insert_one(item_data)
        
        # تحديث إجماليات دورة الراتب
        await self.update_payroll_cycle_totals(target_cycle["id"])
        
        return True
    
    async def create_deduction_warning(self, deduction: PayrollDeduction):
        """إنشاء تحذير عند عدم توفر دورة راتب مناسبة"""
        
        warning = {
            "id": str(uuid.uuid4()),
            "type": "deduction_without_payroll_cycle",
            "employee_id": deduction.employee_id,
            "deduction_id": deduction.id,
            "message": f"خصم بمبلغ {deduction.amount} درهم للموظف {deduction.employee_name} لا يوجد له دورة راتب مفتوحة",
            "created_at": get_uae_now(),  # UAE timezone
            "is_resolved": False
        }
        
        await self.db.payroll_warnings.insert_one(warning)
    
    def _map_deduction_to_item_type(self, deduction_type: DeductionType) -> PayrollItemType:
        """تحويل نوع الخصم إلى نوع عنصر الراتب"""
        mapping = {
            DeductionType.LATENESS: PayrollItemType.DEDUCTION_ATTENDANCE,
            DeductionType.EARLY_LEAVE: PayrollItemType.DEDUCTION_ATTENDANCE,
            DeductionType.MISSING_CHECKOUT: PayrollItemType.DEDUCTION_ATTENDANCE,
            DeductionType.ABSENCE: PayrollItemType.DEDUCTION_ATTENDANCE,
            DeductionType.MANUAL: PayrollItemType.DEDUCTION_MANUAL
        }
        return mapping.get(deduction_type, PayrollItemType.DEDUCTION_OTHER)
    
    # ====================
    # INSTALLMENT SCHEDULE MANAGEMENT
    # ====================
    
    async def create_installment_schedule(self, advance: AdvanceTransaction, 
                                        installment_amount: float, number_of_installments: int,
                                        start_date: date, created_by: str, created_by_name: str,
                                        respect_ceiling: bool = True) -> InstallmentSchedule:
        """إنشاء جدولة أقساط للسلفة"""
        
        # التحقق من أن السلفة معتمدة
        if advance.status != TransactionStatus.APPROVED:
            raise ValueError("لا يمكن جدولة سلفة غير معتمدة")
        
        # التحقق من عدم وجود جدولة سابقة
        existing = await self.db.installment_schedules.find_one({
            "advance_transaction_id": advance.id,
            "is_active": True
        })
        
        if existing:
            raise ValueError("يوجد جدولة أقساط نشطة لهذه السلفة")
        
        # حساب تاريخ الانتهاء
        scheduled_end_date = start_date + relativedelta(months=number_of_installments)
        
        # إنشاء الجدولة
        schedule = InstallmentSchedule(
            advance_transaction_id=advance.id,
            employee_id=advance.employee_id,
            employee_name=advance.employee_name,
            total_amount=advance.amount,
            installment_amount=installment_amount,
            number_of_installments=number_of_installments,
            remaining_balance=advance.amount,
            start_date=start_date,
            scheduled_end_date=scheduled_end_date,
            respect_deduction_ceiling=respect_ceiling,
            created_by=created_by,
            created_by_name=created_by_name
        )
        
        # حفظ الجدولة
        schedule_data = PayrollDB.prepare_for_mongo(schedule.dict())
        await self.db.installment_schedules.insert_one(schedule_data)
        
        # إنشاء الأقساط الفردية
        await self.generate_individual_installments(schedule)
        
        return schedule
    
    async def generate_individual_installments(self, schedule: InstallmentSchedule):
        """إنشاء الأقساط الفردية للجدولة"""
        
        current_date = schedule.start_date
        
        for i in range(schedule.number_of_installments):
            installment = IndividualInstallment(
                schedule_id=schedule.id,
                employee_id=schedule.employee_id,
                installment_number=i + 1,
                scheduled_amount=schedule.installment_amount,
                due_date=current_date
            )
            
            # تعديل المبلغ للقسط الأخير إذا لزم الأمر
            if i == schedule.number_of_installments - 1:
                total_previous = schedule.installment_amount * i
                remaining = schedule.total_amount - total_previous
                installment.scheduled_amount = remaining
            
            installment_data = PayrollDB.prepare_for_mongo(installment.dict())
            await self.db.individual_installments.insert_one(installment_data)
            
            # الانتقال للشهر التالي
            current_date = current_date + relativedelta(months=1)
    
    async def process_monthly_installments(self, payroll_cycle_id: str) -> List[Dict]:
        """معالجة الأقساط الشهرية لدورة راتب"""
        
        # جلب دورة الراتب
        cycle = await self.db.payroll_cycles.find_one({"id": payroll_cycle_id})
        if not cycle:
            raise ValueError("دورة الراتب غير موجودة")
        
        cycle_month = cycle["month"]
        year, month = map(int, cycle_month.split('-'))
        
        # جلب الأقساط المستحقة لهذا الشهر
        start_date, end_date = get_month_boundaries(year, month)
        
        due_installments = await self.db.individual_installments.find({
            "due_date": {"$gte": start_date.isoformat(), "$lte": end_date.isoformat()},
            "status": InstallmentStatus.PENDING
        }).to_list(1000)
        
        processed_installments = []
        
        for installment in due_installments:
            # جلب معلومات الموظف
            employee = await self.db.users.find_one({"id": installment["employee_id"]})
            if not employee:
                continue
            
            # التحقق من سقف الخصومات
            can_deduct, warning = await self.check_deduction_ceiling(
                employee["id"], installment["scheduled_amount"], payroll_cycle_id
            )
            
            if not can_deduct:
                # تأجيل القسط
                await self.db.individual_installments.update_one(
                    {"id": installment["id"]},
                    {
                        "$set": {
                            "status": InstallmentStatus.SKIPPED,
                            "skip_reason": warning,
                            "processed_at": get_uae_now()  # UAE timezone.isoformat()
                        }
                    }
                )
                
                processed_installments.append({
                    "installment_id": installment["id"],
                    "employee_id": installment["employee_id"],
                    "status": "skipped",
                    "reason": warning
                })
                continue
            
            # خصm القسط
            deduction_success = await self.deduct_installment(installment, payroll_cycle_id)
            
            if deduction_success:
                processed_installments.append({
                    "installment_id": installment["id"],
                    "employee_id": installment["employee_id"],
                    "status": "deducted",
                    "amount": installment["scheduled_amount"]
                })
            
        return processed_installments
    
    async def deduct_installment(self, installment: dict, payroll_cycle_id: str) -> bool:
        """خصم قسط من راتب الموظف"""
        
        try:
            # إنشاء عنصر خصم في كشف الراتب
            line_item = PayrollLineItem(
                payroll_cycle_id=payroll_cycle_id,
                employee_id=installment["employee_id"],
                employee_name="",  # سيتم تحديثه
                item_type=PayrollItemType.DEDUCTION_ADVANCE,
                source_type="advance_installment",
                source_id=installment["id"],
                source_reference=f"قسط رقم {installment['installment_number']}",
                description=f"قسط سلفة - القسط {installment['installment_number']}",
                amount=-abs(installment["scheduled_amount"]),
                is_system_generated=True,
                is_editable=False,
                created_by="system",
                created_by_name="نظام الأقساط التلقائي"
            )
            
            # حفظ عنصر الخصم
            item_data = PayrollDB.prepare_for_mongo(line_item.dict())
            await self.db.payroll_line_items.insert_one(item_data)
            
            # تحديث حالة القسط
            await self.db.individual_installments.update_one(
                {"id": installment["id"]},
                {
                    "$set": {
                        "status": InstallmentStatus.DEDUCTED,
                        "actual_amount": installment["scheduled_amount"],
                        "payroll_cycle_id": payroll_cycle_id,
                        "processed_at": get_uae_now()  # UAE timezone.isoformat()
                    }
                }
            )
            
            # تحديث جدولة الأقساط
            await self.update_installment_schedule_progress(installment["schedule_id"])
            
            return True
            
        except Exception as e:
            print(f"Error deducting installment: {e}")
            return False
    
    async def update_installment_schedule_progress(self, schedule_id: str):
        """تحديث تقدم جدولة الأقساط"""
        
        # جلب الجدولة
        schedule = await self.db.installment_schedules.find_one({"id": schedule_id})
        if not schedule:
            return
        
        # حساب الأقساط المكتملة
        completed_installments = await self.db.individual_installments.count_documents({
            "schedule_id": schedule_id,
            "status": InstallmentStatus.DEDUCTED
        })
        
        # حساب الرصيد المتبقي
        paid_amount = completed_installments * schedule["installment_amount"]
        remaining_balance = max(0, schedule["total_amount"] - paid_amount)
        
        # تحديد إذا كانت الجدولة مكتملة
        is_completed = completed_installments >= schedule["number_of_installments"]
        
        # تحديث الجدولة
        updates = {
            "completed_installments": completed_installments,
            "remaining_balance": remaining_balance,
            "is_completed": is_completed,
            "updated_at": get_uae_now()  # UAE timezone.isoformat()
        }
        
        if is_completed:
            updates["actual_end_date"] = get_uae_now()  # UAE timezone.date().isoformat()
        
        await self.db.installment_schedules.update_one(
            {"id": schedule_id},
            {"$set": updates}
        )
    
    # ====================
    # DEDUCTION CEILING MANAGEMENT
    # ====================
    
    async def check_deduction_ceiling(self, employee_id: str, additional_deduction: float,
                                    payroll_cycle_id: str) -> Tuple[bool, str]:
        """فحص سقف الخصومات للموظف"""
        
        # جلب معلومات الموظف
        employee = await self.db.users.find_one({"id": employee_id})
        if not employee:
            return False, "الموظف غير موجود"
        
        # جلب سقف الخصومات المخصص أو استخدام الافتراضي
        ceiling_config = await self.db.employee_deduction_ceilings.find_one({
            "employee_id": employee_id,
            "is_active": True
        })
        
        if not ceiling_config:
            # استخدام السقف الافتراضي (33%)
            ceiling_type = DeductionCeiling.PERCENTAGE
            ceiling_value = 0.33
        else:
            ceiling_type = DeductionCeiling(ceiling_config["ceiling_type"])
            ceiling_value = ceiling_config["ceiling_value"]
        
        # حساب الخصومات الحالية للدورة
        current_deductions = await self.calculate_current_cycle_deductions(employee_id, payroll_cycle_id)
        
        # التحقق من السقف
        employee_salary = employee.get("monthly_salary", 0)
        return validate_deduction_ceiling(
            employee_salary, current_deductions, additional_deduction,
            ceiling_type, ceiling_value
        )
    
    async def calculate_current_cycle_deductions(self, employee_id: str, payroll_cycle_id: str) -> float:
        """حساب إجمالي الخصومات الحالية للموظف في الدورة"""
        
        deduction_items = await self.db.payroll_line_items.find({
            "payroll_cycle_id": payroll_cycle_id,
            "employee_id": employee_id,
            "item_type": {
                "$in": [
                    PayrollItemType.DEDUCTION_ATTENDANCE.value,
                    PayrollItemType.DEDUCTION_ADVANCE.value,
                    PayrollItemType.DEDUCTION_MANUAL.value
                ]
            },
            "is_voided": False
        }).to_list(1000)
        
        total_deductions = sum(abs(item["amount"]) for item in deduction_items)
        return total_deductions
    
    # ====================
    # PAYROLL CALCULATION
    # ====================
    
    async def calculate_employee_payroll(self, employee_id: str, payroll_cycle_id: str) -> EmployeePayrollSummary:
        """حساب راتب موظف محدد لدورة معينة"""
        
        # جلب معلومات الموظف
        employee = await self.db.users.find_one({"id": employee_id})
        if not employee:
            raise ValueError("الموظف غير موجود")
        
        # جلب عناصر الراتب للموظف في هذه الدورة
        line_items = await self.db.payroll_line_items.find({
            "payroll_cycle_id": payroll_cycle_id,
            "employee_id": employee_id,
            "is_voided": False
        }).to_list(1000)
        
        # تصنيف العناصر
        base_salary = employee.get("monthly_salary", 0)
        allowances = 0.0
        overtime = 0.0
        bonuses = 0.0
        attendance_deductions = 0.0
        advance_deductions = 0.0
        manual_deductions = 0.0
        other_deductions = 0.0
        
        for item in line_items:
            amount = item["amount"]
            item_type = PayrollItemType(item["item_type"])
            
            if item_type == PayrollItemType.ALLOWANCE:
                allowances += amount
            elif item_type == PayrollItemType.OVERTIME:
                overtime += amount
            elif item_type == PayrollItemType.BONUS:
                bonuses += amount
            elif item_type == PayrollItemType.DEDUCTION_ATTENDANCE:
                attendance_deductions += abs(amount)
            elif item_type == PayrollItemType.DEDUCTION_ADVANCE:
                advance_deductions += abs(amount)
            elif item_type == PayrollItemType.DEDUCTION_MANUAL:
                manual_deductions += abs(amount)
            else:
                other_deductions += abs(amount)
        
        # حساب الإجماليات
        gross_salary = base_salary + allowances + overtime + bonuses
        total_deductions = attendance_deductions + advance_deductions + manual_deductions + other_deductions
        net_salary = max(0, gross_salary - total_deductions)
        
        # إنشاء الملخص
        summary = EmployeePayrollSummary(
            payroll_cycle_id=payroll_cycle_id,
            employee_id=employee_id,
            employee_name=employee.get("name", ""),
            employee_position=employee.get("position", ""),
            base_salary=base_salary,
            daily_rate=base_salary / 22,
            total_allowances=allowances,
            overtime_amount=overtime,
            bonus_amount=bonuses,
            gross_salary=gross_salary,
            attendance_deductions=attendance_deductions,
            advance_deductions=advance_deductions,
            manual_deductions=manual_deductions,
            other_deductions=other_deductions,
            total_deductions=total_deductions,
            net_salary=net_salary,
            is_calculated=True,
            calculated_at=get_uae_now()  # UAE timezone
        )
        
        # حفظ الملخص
        summary_data = PayrollDB.prepare_for_mongo(summary.dict())
        await self.db.employee_payroll_summaries.update_one(
            {"payroll_cycle_id": payroll_cycle_id, "employee_id": employee_id},
            {"$set": summary_data},
            upsert=True
        )
        
        return summary
    
    async def update_payroll_cycle_totals(self, cycle_id: str):
        """تحديث إجماليات دورة الراتب"""
        
        # جلب جميع ملخصات الموظفين
        summaries = await self.db.employee_payroll_summaries.find({
            "payroll_cycle_id": cycle_id
        }).to_list(1000)
        
        # حساب الإجماليات
        total_employees = len(summaries)
        total_gross_salary = sum(s.get("gross_salary", 0) for s in summaries)
        total_deductions = sum(s.get("total_deductions", 0) for s in summaries)
        total_net_salary = sum(s.get("net_salary", 0) for s in summaries)
        
        # تحديث دورة الراتب
        await self.db.payroll_cycles.update_one(
            {"id": cycle_id},
            {
                "$set": {
                    "total_employees": total_employees,
                    "total_gross_salary": total_gross_salary,
                    "total_deductions": total_deductions,
                    "total_net_salary": total_net_salary,
                    "updated_at": get_uae_now()  # UAE timezone.isoformat()
                }
            }
        )
    
    # ====================
    # AUDIT AND LOGGING
    # ====================
    
    async def log_payroll_activity(self, cycle_id: Optional[str], action: str, performed_by: str,
                                 details: str, metadata: Optional[Dict] = None):
        """تسجيل نشاط في سجل التدقيق"""
        
        log_entry = {
            "id": str(uuid.uuid4()),
            "cycle_id": cycle_id,
            "action": action,
            "performed_by": performed_by,
            "details": details,
            "metadata": metadata or {},
            "timestamp": get_uae_now(),  # UAE timezone
            "ip_address": None,  # يمكن إضافته لاحقاً
            "user_agent": None   # يمكن إضافته لاحقاً
        }
        
        await self.db.payroll_audit_logs.insert_one(log_entry)
    
    # ====================
    # EVENT HANDLING
    # ====================
    
    async def handle_deduction_created(self, deduction: PayrollDeduction):
        """معالجة إنشاء خصم جديد"""
        await self.link_deduction_to_payroll(deduction)
    
    async def handle_advance_approved(self, advance: AdvanceTransaction):
        """معالجة اعتماد سلفة جديدة"""
        # يمكن إنشاء جدولة أقساط تلقائية أو إشعار
        pass
    
    async def handle_payroll_cycle_created(self, cycle: PayrollCycle):
        """معالجة إنشاء دورة راتب جديدة"""
        # معالجة الأقساط المستحقة
        await self.process_monthly_installments(cycle.id)
        
        # إنشاء عناصر الراتب الأساسية للموظفين
        await self.generate_base_salary_items(cycle.id)
    
    async def generate_base_salary_items(self, cycle_id: str):
        """إنشاء عناصر الراتب الأساسية للموظفين"""
        
        # جلب جميع الموظفين النشطين
        employees = await self.db.users.find({
            "role": "user",
            "is_active": True
        }).to_list(1000)
        
        for employee in employees:
            # التحقق من عدم وجود راتب أساسي مسبقاً
            existing = await self.db.payroll_line_items.find_one({
                "payroll_cycle_id": cycle_id,
                "employee_id": employee["id"],
                "item_type": PayrollItemType.BASE_SALARY.value
            })
            
            if existing:
                continue
            
            # إنشاء عنصر الراتب الأساسي
            base_salary_item = PayrollLineItem(
                payroll_cycle_id=cycle_id,
                employee_id=employee["id"],
                employee_name=employee.get("name", ""),
                item_type=PayrollItemType.BASE_SALARY,
                source_type="employee_contract",
                source_id=employee["id"],
                description="الراتب الأساسي",
                description_ar="الراتب الأساسي",
                amount=employee.get("monthly_salary", 0),
                is_recurring=True,
                is_system_generated=True,
                is_editable=False,
                created_by="system",
                created_by_name="النظام"
            )
            
            # حفظ العنصر
            item_data = PayrollDB.prepare_for_mongo(base_salary_item.dict())
            await self.db.payroll_line_items.insert_one(item_data)