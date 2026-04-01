"""
Advanced Attendance & Deduction Engine
محرك احتساب الحضور والخصومات المتقدم - أكتوبر 2025
"""

import asyncio
from datetime import datetime, date, time, timezone, timedelta
from typing import Optional, List, Tuple, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase

from attendance_models import (
    AttendancePolicy, DailyAttendance, MonthlyLatenessCounters, PayrollDeduction,
    SystemNotification, AttendanceSystemConfig, AttendanceStatsResponse,
    DeductionType, DeductionCategory, DeductionSource, AttendanceStatus, NotificationSeverity,
    prepare_for_mongo, parse_from_mongo,
    DEDUCTION_TYPE_AR, DEDUCTION_CATEGORY_AR, ATTENDANCE_STATUS_AR
)

class AttendanceEngine:
    """محرك احتساب الحضور والخصومات المتقدم"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.config = None
        
    async def initialize(self):
        """تهيئة المحرك وتحميل الإعدادات"""
        await self._load_system_config()
        await self._ensure_collections_indexed()
        
    async def _load_system_config(self):
        """تحميل إعدادات النظام"""
        config_doc = await self.db.attendance_config.find_one({})
        if config_doc:
            self.config = AttendanceSystemConfig(**parse_from_mongo(config_doc))
        else:
            # إنشاء إعدادات افتراضية
            self.config = AttendanceSystemConfig()
            await self.db.attendance_config.insert_one(prepare_for_mongo(self.config.dict()))
    
    async def _ensure_collections_indexed(self):
        """إنشاء فهارس قاعدة البيانات - مع حماية من أخطاء الصلاحيات"""
        try:
            # Attendance policies
            await self.db.attendance_policies.create_index([
                ("employee_id", 1), 
                ("effective_from", -1)
            ])
            
            # Daily attendance 
            await self.db.daily_attendance.create_index([
                ("employee_id", 1), 
                ("date", -1)
            ])
            
            # Monthly counters
            await self.db.monthly_lateness_counters.create_index([
                ("employee_id", 1), 
                ("month", -1)
            ])
            
            # Deductions
            await self.db.payroll_deductions.create_index([
                ("employee_id", 1), 
                ("date", -1),
                ("is_voided", 1)
            ])
            
            # Notifications
            await self.db.system_notifications.create_index([
                ("employee_id", 1), 
                ("created_at", -1),
                ("acknowledged_at", 1)
            ])
            print("✅ Attendance engine indexes created successfully")
        except Exception:
            pass  # Silently skip - Atlas restricted users cannot create indexes

    async def get_employee_policy(self, employee_id: str, target_date: date = None) -> AttendancePolicy:
        """الحصول على سياسة حضور الموظف"""
        if target_date is None:
            target_date = date.today()
            
        # البحث عن السياسة المفعلة للتاريخ المحدد
        query = {
            "employee_id": employee_id,
            "effective_from": {"$lte": target_date.isoformat()},
            "$or": [
                {"effective_until": None},
                {"effective_until": {"$gte": target_date.isoformat()}}
            ]
        }
        
        policy_doc = await self.db.attendance_policies.find_one(
            query, 
            sort=[("effective_from", -1)]
        )
        
        if policy_doc:
            return AttendancePolicy(**parse_from_mongo(policy_doc))
        else:
            # إنشاء سياسة افتراضية
            user_doc = await self.db.users.find_one({"id": employee_id})
            if not user_doc:
                raise ValueError(f"Employee {employee_id} not found")
            
            # سياسات خاصة للموظفين
            if user_doc.get("email") == "hatem@tan-seeq.co":
                # حاتم: بدون خصومات
                policy = AttendancePolicy(
                    employee_id=employee_id,
                    employee_name=user_doc.get("name", ""),
                    no_penalties=True,
                    early_start_allowed=True
                )
            elif user_doc.get("name", "").lower() == "طارق" or "tarek" in user_doc.get("email", "").lower():
                # طارق: دخول مبكر وخروج مرن
                policy = AttendancePolicy(
                    employee_id=employee_id,
                    employee_name=user_doc.get("name", ""),
                    start_time=time(8, 0),
                    end_flexible=True,
                    early_start_allowed=True
                )
            else:
                # سياسة افتراضية
                policy = AttendancePolicy(
                    employee_id=employee_id,
                    employee_name=user_doc.get("name", "")
                )
            
            # حفظ السياسة
            await self.db.attendance_policies.insert_one(prepare_for_mongo(policy.dict()))
            return policy

    async def get_monthly_counters(self, employee_id: str, month: str) -> MonthlyLatenessCounters:
        """الحصول على عدادات الشهر"""
        counter_doc = await self.db.monthly_lateness_counters.find_one({
            "employee_id": employee_id,
            "month": month
        })
        
        if counter_doc:
            return MonthlyLatenessCounters(**parse_from_mongo(counter_doc))
        else:
            # إنشاء عدادات جديدة
            user_doc = await self.db.users.find_one({"id": employee_id})
            counter = MonthlyLatenessCounters(
                employee_id=employee_id,
                employee_name=user_doc.get("name", "") if user_doc else "",
                month=month
            )
            await self.db.monthly_lateness_counters.insert_one(prepare_for_mongo(counter.dict()))
            return counter

    def calculate_late_minutes(self, check_in: datetime, policy: AttendancePolicy) -> int:
        """حساب دقائق التأخير"""
        if policy.no_penalties:
            return 0
            
        # تحويل الأوقات إلى نفس المنطقة الزمنية
        policy_start = datetime.combine(check_in.date(), policy.start_time)
        if check_in.tzinfo:
            policy_start = policy_start.replace(tzinfo=check_in.tzinfo)
            
        # الدخول المبكر لا يُحسب كأوفر تايم ولا يغطي التأخير
        if check_in <= policy_start:
            return 0
            
        # حساب دقائق التأخير
        late_delta = check_in - policy_start
        return max(0, int(late_delta.total_seconds() / 60))

    def calculate_early_leave_minutes(self, check_out: datetime, policy: AttendancePolicy) -> int:
        """حساب دقائق الخروج المبكر"""
        if policy.no_penalties or policy.end_flexible:
            return 0
            
        policy_end = datetime.combine(check_out.date(), policy.end_time)
        if check_out.tzinfo:
            policy_end = policy_end.replace(tzinfo=check_out.tzinfo)
            
        if check_out >= policy_end:
            return 0
            
        early_delta = policy_end - check_out
        return max(0, int(early_delta.total_seconds() / 60))

    async def apply_deduction_rules(
        self, 
        employee_id: str, 
        minutes: int, 
        deduction_type: DeductionType,
        use_free_occurrences: bool = True
    ) -> Tuple[PayrollDeduction, bool]:
        """تطبيق قواعد الخصومات المتقدمة - أكتوبر 2025"""
        
        if minutes <= 0:
            return None, False
            
        # الحصول على بيانات الموظف
        user_doc = await self.db.users.find_one({"id": employee_id})
        if not user_doc:
            raise ValueError(f"Employee {employee_id} not found")
            
        employee_name = user_doc.get("name", "")
        daily_rate = user_doc.get("monthly_salary", 0) / 30 if user_doc.get("monthly_salary") else 0
        
        # قواعد الخصم حسب الدقائق
        if minutes > self.config.full_day_threshold_minutes:  # > 120 دقيقة
            category = DeductionCategory.FULL_DAY
            amount = daily_rate
            final_minutes = self.config.working_minutes_per_day
            
        elif minutes >= self.config.half_day_threshold_minutes:  # 60-120 دقيقة
            category = DeductionCategory.HALF_DAY  
            amount = daily_rate / 2
            final_minutes = self.config.working_minutes_per_day // 2
            
        elif minutes > 20:  # > 20 دقيقة
            category = DeductionCategory.MINUTES
            amount = (daily_rate / self.config.working_minutes_per_day) * minutes
            final_minutes = minutes
            
        else:  # 1-20 دقيقة
            # التحقق من المرات المجانية (فقط للتأخير وليس الخروج المبكر)
            if (use_free_occurrences and 
                deduction_type == DeductionType.LATENESS and 
                minutes <= self.config.free_occurrence_max_minutes):
                
                month = date.today().strftime('%Y-%m')
                counters = await self.get_monthly_counters(employee_id, month)
                
                if counters.free_occurrences_used < self.config.free_occurrences_limit:
                    # استخدام مرة مجانية
                    counters.free_occurrences_used += 1
                    await self.db.monthly_lateness_counters.update_one(
                        {"employee_id": employee_id, "month": month},
                        {"$set": {"free_occurrences_used": counters.free_occurrences_used}}
                    )
                    
                    # إنشاء سجل خصم بقيمة 0 (مرة مجانية)
                    deduction = PayrollDeduction(
                        employee_id=employee_id,
                        employee_name=employee_name,
                        deduction_type=deduction_type,
                        category=DeductionCategory.MINUTES,
                        date=date.today(),
                        minutes=0,
                        amount=0.0,
                        daily_rate=daily_rate,
                        reason=f"مرة مجانية ({counters.free_occurrences_used}/{self.config.free_occurrences_limit}) - تأخير {minutes} دقيقة",
                        source=DeductionSource.AUTO
                    )
                    return deduction, True  # True = مرة مجانية
            
            # خصم دقائق عادي
            category = DeductionCategory.MINUTES
            amount = (daily_rate / self.config.working_minutes_per_day) * minutes
            final_minutes = minutes
        
        # إنشاء خصم
        deduction = PayrollDeduction(
            employee_id=employee_id,
            employee_name=employee_name,
            deduction_type=deduction_type,
            category=category,
            date=date.today(),
            minutes=final_minutes,
            amount=amount,
            daily_rate=daily_rate,
            reason=self._generate_deduction_reason(deduction_type, category, final_minutes),
            source=DeductionSource.AUTO
        )
        
        return deduction, False  # False = خصم فعلي

    def _generate_deduction_reason(
        self, 
        deduction_type: DeductionType, 
        category: DeductionCategory, 
        minutes: int
    ) -> str:
        """توليد سبب الخصم"""
        type_ar = DEDUCTION_TYPE_AR.get(deduction_type, str(deduction_type))
        
        if category == DeductionCategory.FULL_DAY:
            return f"{type_ar} - خصم يوم كامل ({minutes} دقيقة)"
        elif category == DeductionCategory.HALF_DAY:
            return f"{type_ar} - خصم نصف يوم ({minutes} دقيقة)"
        else:
            return f"{type_ar} - {minutes} دقيقة"

    async def process_daily_attendance(
        self, 
        employee_id: str, 
        target_date: date,
        check_in: Optional[datetime] = None,
        check_out: Optional[datetime] = None,
        force_recompute: bool = False
    ) -> DailyAttendance:
        """معالجة الحضور اليومي"""
        
        # البحث عن سجل موجود
        existing_doc = await self.db.daily_attendance.find_one({
            "employee_id": employee_id,
            "date": target_date.isoformat()
        })
        
        if existing_doc and not force_recompute:
            return DailyAttendance(**parse_from_mongo(existing_doc))
        
        # الحصول على السياسة
        policy = await self.get_employee_policy(employee_id, target_date)
        
        # إنشاء أو تحديث سجل الحضور
        if existing_doc:
            attendance = DailyAttendance(**parse_from_mongo(existing_doc))
            if check_in:
                attendance.check_in = check_in
            if check_out:
                attendance.check_out = check_out
        else:
            attendance = DailyAttendance(
                employee_id=employee_id,
                employee_name=policy.employee_name,
                date=target_date,
                check_in=check_in,
                check_out=check_out
            )
        
        # حساب التأخير والخروج المبكر
        if attendance.check_in:
            attendance.late_minutes = self.calculate_late_minutes(attendance.check_in, policy)
            
        if attendance.check_out:
            attendance.early_leave_minutes = self.calculate_early_leave_minutes(attendance.check_out, policy)
        elif target_date < date.today():
            # يوم سابق بدون تسجيل انصراف - خصم حتى نهاية الدوام
            policy_end = datetime.combine(target_date, policy.end_time)
            attendance.early_leave_minutes = self.calculate_early_leave_minutes(policy_end, policy)
        
        # تحديد الحالة
        if not attendance.check_in:
            attendance.status = AttendanceStatus.ABSENT
        elif attendance.late_minutes > 0:
            attendance.status = AttendanceStatus.LATE
        elif attendance.early_leave_minutes > 0:
            attendance.status = AttendanceStatus.EARLY_LEAVE
        elif not attendance.check_out and target_date == date.today():
            attendance.status = AttendanceStatus.MISSING_CHECKOUT
        else:
            attendance.status = AttendanceStatus.PRESENT
        
        # حساب ساعات العمل الفعلية
        if attendance.check_in and attendance.check_out:
            work_delta = attendance.check_out - attendance.check_in
            attendance.working_hours = work_delta.total_seconds() / 3600
        
        # تسجيل وقت المعالجة
        attendance.computed_at = get_uae_now()  # UAE timezone
        if existing_doc:
            attendance.recomputed_at = get_uae_now()  # UAE timezone
        
        # حفظ السجل
        attendance_dict = prepare_for_mongo(attendance.dict())
        if existing_doc:
            await self.db.daily_attendance.update_one(
                {"employee_id": employee_id, "date": target_date.isoformat()},
                {"$set": attendance_dict}
            )
        else:
            await self.db.daily_attendance.insert_one(attendance_dict)
        
        # معالجة الخصومات إذا لم تكن معالجة من قبل
        if not policy.no_penalties:
            await self._process_attendance_deductions(attendance, policy)
        
        return attendance

    async def _process_attendance_deductions(self, attendance: DailyAttendance, policy: AttendancePolicy):
        """معالجة خصومات الحضور"""
        deductions_to_create = []
        notifications_to_create = []
        
        # خصم التأخير
        if attendance.late_minutes > 0:
            deduction, is_free = await self.apply_deduction_rules(
                attendance.employee_id,
                attendance.late_minutes,
                DeductionType.LATENESS,
                use_free_occurrences=True
            )
            
            if deduction:
                deduction.reference_id = attendance.id
                deduction.reference_type = "daily_attendance"
                deductions_to_create.append(deduction)
                
                # إشعار
                if is_free:
                    message = f"تم استخدام مرة مجانية للتأخير {attendance.late_minutes} دقيقة"
                    severity = NotificationSeverity.NORMAL
                else:
                    message = f"تم خصم {deduction.amount:.2f} درهم بسبب التأخير {attendance.late_minutes} دقيقة"
                    severity = NotificationSeverity.WARNING
                    
                notification = SystemNotification(
                    employee_id=attendance.employee_id,
                    employee_name=attendance.employee_name,
                    title="إشعار تأخير",
                    message=message,
                    severity=severity,
                    must_acknowledge=True,
                    category="deduction",
                    reference_id=attendance.id
                )
                notifications_to_create.append(notification)
        
        # خصم الخروج المبكر
        if attendance.early_leave_minutes > 0:
            deduction, _ = await self.apply_deduction_rules(
                attendance.employee_id,
                attendance.early_leave_minutes,
                DeductionType.EARLY_LEAVE,
                use_free_occurrences=False  # لا مرات مجانية للخروج المبكر
            )
            
            if deduction:
                deduction.reference_id = attendance.id
                deduction.reference_type = "daily_attendance"
                deductions_to_create.append(deduction)
                
                notification = SystemNotification(
                    employee_id=attendance.employee_id,
                    employee_name=attendance.employee_name,
                    title="إشعار خروج مبكر",
                    message=f"تم خصم {deduction.amount:.2f} درهم بسبب الخروج المبكر {attendance.early_leave_minutes} دقيقة",
                    severity=NotificationSeverity.WARNING,
                    must_acknowledge=True,
                    category="deduction",
                    reference_id=attendance.id
                )
                notifications_to_create.append(notification)
        
        # حفظ الخصومات
        for deduction in deductions_to_create:
            await self.db.payroll_deductions.insert_one(prepare_for_mongo(deduction.dict()))
        
        # حفظ الإشعارات
        for notification in notifications_to_create:
            await self.db.system_notifications.insert_one(prepare_for_mongo(notification.dict()))

    async def create_manual_deduction(
        self, 
        employee_id: str, 
        deduction_type: DeductionType,
        category: DeductionCategory,
        target_date: date,
        minutes: Optional[int] = None,
        amount: Optional[float] = None,
        reason: str = "",
        created_by: str = "",
        attachments: List[Dict[str, Any]] = None
    ) -> PayrollDeduction:
        """إنشاء خصم يدوي من السوبر أدمن"""
        
        # الحصول على بيانات الموظف
        user_doc = await self.db.users.find_one({"id": employee_id})
        if not user_doc:
            raise ValueError(f"Employee {employee_id} not found")
        
        employee_name = user_doc.get("name", "")
        daily_rate = user_doc.get("monthly_salary", 0) / 30 if user_doc.get("monthly_salary") else 0
        
        # حساب المبلغ إذا لم يكن محدداً
        if amount is None and minutes is not None:
            if category == DeductionCategory.FULL_DAY:
                amount = daily_rate
            elif category == DeductionCategory.HALF_DAY:
                amount = daily_rate / 2
            else:
                amount = (daily_rate / self.config.working_minutes_per_day) * minutes
        
        # إنشاء الخصم
        deduction = PayrollDeduction(
            employee_id=employee_id,
            employee_name=employee_name,
            deduction_type=deduction_type,
            category=category,
            date=target_date,
            minutes=minutes or 0,
            amount=amount or 0,
            daily_rate=daily_rate,
            reason=reason,
            source=DeductionSource.MANUAL,
            created_by=created_by,
            attachments=attachments or []
        )
        
        # حفظ الخصم
        await self.db.payroll_deductions.insert_one(prepare_for_mongo(deduction.dict()))
        
        # إنشاء إشعار
        creator_doc = await self.db.users.find_one({"id": created_by})
        creator_name = creator_doc.get("name", "الإدارة") if creator_doc else "الإدارة"
        
        notification = SystemNotification(
            employee_id=employee_id,
            employee_name=employee_name,
            title="خصم يدوي من الإدارة",
            message=f"تم إضافة خصم بمبلغ {amount:.2f} درهم من قبل {creator_name}. السبب: {reason}",
            severity=NotificationSeverity.IMPORTANT,
            must_acknowledge=True,
            category="manual_deduction",
            reference_id=deduction.id
        )
        
        await self.db.system_notifications.insert_one(prepare_for_mongo(notification.dict()))
        
        return deduction

    async def get_attendance_stats(self, employee_id: str, month: str) -> AttendanceStatsResponse:
        """إحصائيات الحضور الشهرية"""
        
        # الحصول على بيانات الموظف
        user_doc = await self.db.users.find_one({"id": employee_id})
        if not user_doc:
            raise ValueError(f"Employee {employee_id} not found")
        
        # الحصول على العدادات الشهرية
        counters = await self.get_monthly_counters(employee_id, month)
        
        # حساب الإحصائيات من سجلات الحضور اليومية
        year, month_num = month.split('-')
        start_date = date(int(year), int(month_num), 1)
        
        # آخر يوم في الشهر
        if int(month_num) == 12:
            end_date = date(int(year) + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(int(year), int(month_num) + 1, 1) - timedelta(days=1)
        
        # جلب سجلات الحضور
        attendance_docs = await self.db.daily_attendance.find({
            "employee_id": employee_id,
            "date": {
                "$gte": start_date.isoformat(),
                "$lte": end_date.isoformat()
            }
        }).to_list(None)
        
        # حساب الإحصائيات
        total_days = len(attendance_docs)
        present_days = len([doc for doc in attendance_docs if doc.get("status") != "absent"])
        late_days = len([doc for doc in attendance_docs if doc.get("status") == "late"])
        absent_days = total_days - present_days
        
        total_late_minutes = sum(doc.get("late_minutes", 0) for doc in attendance_docs)
        
        # حساب إجمالي الخصومات
        deductions_docs = await self.db.payroll_deductions.find({
            "employee_id": employee_id,
            "date": {
                "$gte": start_date.isoformat(),
                "$lte": end_date.isoformat()
            },
            "is_voided": False
        }).to_list(None)
        
        total_deduction_amount = sum(doc.get("amount", 0) for doc in deductions_docs)
        
        return AttendanceStatsResponse(
            employee_id=employee_id,
            employee_name=user_doc.get("name", ""),
            month=month,
            total_days=total_days,
            present_days=present_days,
            late_days=late_days,
            absent_days=absent_days,
            total_late_minutes=total_late_minutes,
            total_deduction_amount=total_deduction_amount,
            free_occurrences_remaining=max(0, counters.free_occurrences_limit - counters.free_occurrences_used)
        )

# ====================
# SCHEDULED TASKS
# ====================

class AttendanceScheduler:
    """مُجدول مهام الحضور"""
    
    def __init__(self, engine: AttendanceEngine):
        self.engine = engine
        
    async def check_missing_checkouts_warning(self):
        """فحص عدم تسجيل الانصراف - تحذير 18:10"""
        current_time = get_uae_now()  # UAE timezone
        today = current_time.date()
        
        if current_time.time() < time(18, 10):
            return  # لم يحن وقت التحذير بعد
        
        # البحث عن الموظفين الذين لم يسجلوا انصراف اليوم
        attendance_docs = await self.engine.db.daily_attendance.find({
            "date": today.isoformat(),
            "check_in": {"$exists": True},
            "check_out": {"$exists": False}
        }).to_list(None)
        
        for doc in attendance_docs:
            # التحقق إذا لم يتم إرسال التحذير من قبل
            existing_notification = await self.engine.db.system_notifications.find_one({
                "employee_id": doc["employee_id"],
                "category": "missing_checkout_warning",
                "reference_id": doc["id"]
            })
            
            if not existing_notification:
                notification = SystemNotification(
                    employee_id=doc["employee_id"],
                    employee_name=doc["employee_name"],
                    title="تحذير: لم تسجل الانصراف",
                    message="لم تقم بتسجيل انصراف اليوم. يرجى تسجيل الانصراف قبل منتصف الليل لتجنب الخصم التلقائي.",
                    severity=NotificationSeverity.WARNING,
                    must_acknowledge=True,
                    category="missing_checkout_warning",
                    reference_id=doc["id"]
                )
                
                await self.engine.db.system_notifications.insert_one(prepare_for_mongo(notification.dict()))
    
    async def process_missing_checkouts_final(self):
        """معالجة عدم تسجيل الانصراف النهائية - 23:59"""
        current_time = get_uae_now()  # UAE timezone
        today = current_time.date()
        
        if current_time.time() < time(23, 59):
            return  # لم يحن الوقت بعد
        
        # البحث عن الموظفين الذين لم يسجلوا انصراف اليوم
        attendance_docs = await self.engine.db.daily_attendance.find({
            "date": today.isoformat(), 
            "check_in": {"$exists": True},
            "check_out": {"$exists": False}
        }).to_list(None)
        
        for doc in attendance_docs:
            employee_id = doc["employee_id"]
            
            # الحصول على السياسة
            policy = await self.engine.get_employee_policy(employee_id, today)
            
            if policy.no_penalties:
                continue  # تخطي الموظفين المعفيين
            
            # إنشاء خصم لعدم تسجيل الانصراف (حتى 18:00)
            policy_end = datetime.combine(today, policy.end_time)
            missing_minutes = self.engine.calculate_early_leave_minutes(policy_end, policy)
            
            if missing_minutes > 0:
                await self.engine.create_manual_deduction(
                    employee_id=employee_id,
                    deduction_type=DeductionType.MISSING_CHECKOUT,
                    category=DeductionCategory.MINUTES,
                    target_date=today,
                    minutes=missing_minutes,
                    reason=f"عدم تسجيل انصراف - خصم حتى {policy.end_time.strftime('%H:%M')}",
                    created_by="system"
                )
                
                # تحديث سجل الحضور
                await self.engine.db.daily_attendance.update_one(
                    {"id": doc["id"]},
                    {"$set": {
                        "status": AttendanceStatus.MISSING_CHECKOUT.value,
                        "early_leave_minutes": missing_minutes,
                        "computed_at": get_uae_now()  # UAE timezone.isoformat()
                    }}
                )

    async def daily_recompute(self):
        """إعادة احتساب الحضور اليومي - 01:00"""
        yesterday = date.today() - timedelta(days=1)
        
        # إعادة احتساب جميع سجلات الأمس
        attendance_docs = await self.engine.db.daily_attendance.find({
            "date": yesterday.isoformat()
        }).to_list(None)
        
        for doc in attendance_docs:
            await self.engine.process_daily_attendance(
                employee_id=doc["employee_id"],
                target_date=yesterday,
                check_in=doc.get("check_in"),
                check_out=doc.get("check_out"), 
                force_recompute=True
            )

    async def monthly_reset(self):
        """تصفير العدادات الشهرية - أول يوم من الشهر"""
        current_date = date.today()
        if current_date.day != 1:
            return  # ليس أول يوم من الشهر
        
        current_month = current_date.strftime('%Y-%m')
        
        # تصفير عدادات جميع الموظفين للشهر الجديد  
        await self.engine.db.monthly_lateness_counters.update_many(
            {"month": current_month},
            {"$set": {
                "free_occurrences_used": 0,
                "reset_at": get_uae_now()  # UAE timezone.isoformat()
            }}
        )