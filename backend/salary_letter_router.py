"""
Salary Letter Router - Order-safe implementation
=================================================
This router is built as a factory to avoid import-time dependency issues.
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, Response
from pathlib import Path


def build_salary_letter_router(get_current_user_dep):
    """
    Build salary letter router with proper dependency injection.
    This avoids import-time crashes by accepting get_current_user as a parameter.
    """
    router = APIRouter(tags=["Salary Letters"])

    @router.get("/api/payroll/cycles/{cycle_id}/employees/{employee_id}/letter")
    async def generate_salary_letter(
        cycle_id: str,
        employee_id: str,
        request: Request,
        format: str = "html",
        current_user: dict = Depends(get_current_user_dep),
    ):
        """
        إنشاء رسالة راتب شهرية للموظف
        Generate monthly salary letter for employee
        
        Args:
            cycle_id: Payroll cycle ID
            employee_id: Employee ID
            format: Output format (html or pdf)
            
        Returns:
            HTML or PDF salary letter with ledger data
        """
        try:
            # ✅ Safe DB access for Atlas/sandbox (no global db)
            db = getattr(request.app.state, "db", None)
            if db is None:
                raise HTTPException(status_code=500, detail="Database not initialized")

            # جلب دورة الراتب
            cycle = await db.payroll_cycles.find_one({"id": cycle_id})
            if not cycle:
                raise HTTPException(status_code=404, detail="دورة الراتب غير موجودة")

            # جلب ملخص راتب الموظف
            employee_summary = await db.employee_payroll_summaries.find_one({
                "cycle_id": cycle_id,  # ✅ cycle_id (not payroll_cycle_id)
                "employee_id": employee_id
            })
            
            if not employee_summary:
                raise HTTPException(status_code=404, detail="لم يتم العثور على بيانات راتب الموظف")

            # جلب بيانات الموظف
            employee = await db.users.find_one({"id": employee_id})
            if not employee:
                raise HTTPException(status_code=404, detail="الموظف غير موجود")

            # حساب المعدلات
            base_salary = float(employee_summary.get("base_salary", 0) or 0)
            daily_rate = base_salary / 30 if base_salary else 0
            hourly_rate = daily_rate / 8 if daily_rate else 0
            minute_rate = hourly_rate / 60 if hourly_rate else 0

            # ✅ Ledger parity: source_type + cycle_id
            ledger_entries = await db.payroll_ledger.find({
                "employee_id": employee_id,
                "cycle_id": cycle_id  # ✅ cycle_id (not payroll_cycle_id)
            }).to_list(None)
            
            # Remove MongoDB _id
            for entry in ledger_entries:
                entry.pop("_id", None)

            # تصنيف البنود
            attendance_deductions, leave_adjustments = [], []
            manual_deductions, advance_installments, custody_adjustments = [], [], []

            for entry in ledger_entries:
                source_type = entry.get("source_type", "")
                amount = float(entry.get("amount", 0) or 0)
                description = entry.get("description", "")

                if source_type == "ATTENDANCE_DEDUCTION":
                    attendance_deductions.append({"description": description, "amount": amount})
                elif source_type == "LEAVE_ADJUSTMENT":
                    leave_adjustments.append({"description": description, "amount": amount})
                elif source_type == "MANUAL_DEDUCTION":
                    manual_deductions.append({"description": description, "amount": amount})
                elif source_type == "ADVANCE_INSTALLMENT":
                    advance_installments.append({
                        "description": description,
                        "amount": amount,
                        "reference_id": entry.get("source_id", "")
                    })
                elif source_type == "CUSTODY_ADJUSTMENT":
                    custody_adjustments.append({"description": description, "amount": amount})

            # حساب الإجماليات
            total_attendance_deductions = sum(abs(d["amount"]) for d in attendance_deductions)
            total_leave_adjustments = sum(d["amount"] for d in leave_adjustments)
            total_manual_deductions = sum(abs(d["amount"]) for d in manual_deductions)
            total_advance_deductions = sum(abs(d["amount"]) for d in advance_installments)
            total_custody_adjustments = sum(d["amount"] for d in custody_adjustments)

            # جلب تفاصيل السلف (إن وجدت)
            advance_details = None
            if advance_installments:
                first_ref = advance_installments[0].get("reference_id", "")
                if first_ref:
                    installment = await db.individual_installments.find_one({"id": first_ref})
                    if installment:
                        schedule_id = installment.get("schedule_id", "")
                        schedule = await db.installment_schedules.find_one({"id": schedule_id})
                        if schedule:
                            advance_id = schedule.get("advance_transaction_id", "")
                            advance = await db.advance_transactions.find_one({"id": advance_id})
                            if advance:
                                advance_details = {
                                    "total_amount": advance.get("amount", 0),
                                    "installments_count": schedule.get("number_of_installments", 0),
                                    "current_installment_number": installment.get("installment_number", 0),
                                    "current_installment_amount": installment.get("scheduled_amount", 0),
                                    "current_installment_date": installment.get("due_date", ""),
                                    "remaining_installments": schedule.get("number_of_installments", 0) - installment.get("installment_number", 0)
                                }

            # ✅ تنسيق التواريخ بصيغة dd/MM/yyyy
            from uae_datetime_utils import format_uae_date_dmy
            
            letter_data = {
                "statement_date": format_uae_date_dmy(),  # ✅ dd/MM/yyyy Asia/Dubai
                "employee_name": employee.get("name", ""),
                "employee_code": employee.get("id", "")[:8],
                "period_label": f"{cycle.get('month', '')} {cycle.get('year', '')}",
                "base_salary": f"{base_salary:,.2f}",
                "daily_rate": f"{daily_rate:,.4f}",
                "hourly_rate": f"{hourly_rate:,.4f}",
                "minute_rate": f"{minute_rate:,.6f}",
                "leave_summary": "لا توجد" if not leave_adjustments else f"{len(leave_adjustments)} تعديل(ات)",
                "leave_lines": leave_adjustments,
                "absence_summary": attendance_deductions,
                "attendance_deductions_total": f"{total_attendance_deductions:,.2f}",
                "manual_deductions_total": f"{total_manual_deductions:,.2f}",
                "manual_lines": manual_deductions,
                "advance_details": advance_details,
                "advance_installments_list": advance_installments,
                "advance_deductions_total": f"{total_advance_deductions:,.2f}",
                "custody_adjustments_total": f"{total_custody_adjustments:,.2f}",
                "custody_lines": custody_adjustments,
                "net_pay": f"{float(employee_summary.get('net_salary', 0) or 0):,.2f}",
                "gross_salary": f"{float(employee_summary.get('gross_salary', 0) or 0):,.2f}",
                "total_deductions": f"{float(employee_summary.get('total_deductions', 0) or 0):,.2f}",
                "cycle_code": cycle_id[:8]
            }

            if format == "pdf":
                from english_salary_letter_pdf import generate_english_salary_letter_pdf
                pdf_content = generate_english_salary_letter_pdf(
                    letter_data,
                    attendance_deductions,
                    manual_deductions,
                    advance_installments
                )
                return Response(
                    content=pdf_content,
                    media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=salary_letter_{cycle_id}_{employee_id}.pdf"}
                )
            else:
                # Build deductions table
                deductions_rows = ""
                if attendance_deductions:
                    for d in attendance_deductions:
                        deductions_rows += f"""
                        <tr>
                            <td>خصم حضور/تأخير</td>
                            <td>{d['description']}</td>
                            <td style='color:#dc2626;font-weight:bold;'>{abs(d['amount']):.2f}</td>
                        </tr>
                        """
                else:
                    deductions_rows += """
                    <tr><td colspan='3' style='text-align:center;color:#666;'>✓ لا توجد خصومات حضور</td></tr>
                    """
                
                if manual_deductions:
                    for d in manual_deductions:
                        deductions_rows += f"""
                        <tr>
                            <td>خصم يدوي</td>
                            <td>{d['description']}</td>
                            <td style='color:#dc2626;font-weight:bold;'>{abs(d['amount']):.2f}</td>
                        </tr>
                        """
                
                if advance_installments:
                    for d in advance_installments:
                        deductions_rows += f"""
                        <tr>
                            <td>قسط سلفة</td>
                            <td>{d['description']}</td>
                            <td style='color:#dc2626;font-weight:bold;'>{abs(d['amount']):.2f}</td>
                        </tr>
                        """

                # Simple HTML template
                html = f"""
                <!DOCTYPE html>
                <html dir="rtl" lang="ar">
                <head>
                    <meta charset="UTF-8">
                    <title>رسالة راتب - {letter_data['employee_name']}</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; padding: 20px; direction: rtl; }}
                        .letter {{ background: white; padding: 30px; max-width: 800px; margin: 0 auto; }}
                        .header {{ text-align: center; border-bottom: 2px solid #1e40af; padding-bottom: 15px; margin-bottom: 20px; }}
                        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
                        th, td {{ padding: 10px; border: 1px solid #ddd; text-align: right; }}
                        th {{ background-color: #f3f4f6; font-weight: bold; }}
                        .summary {{ background-color: #dbeafe; padding: 15px; margin: 20px 0; border-radius: 5px; }}
                    </style>
                </head>
                <body>
                    <div class="letter">
                        <div class="header">
                            <h2>شركة التنسيق</h2>
                            <p>رسالة راتب</p>
                        </div>
                        <p><strong>الموظف:</strong> {letter_data['employee_name']} ({letter_data['employee_code']})</p>
                        <p><strong>التاريخ:</strong> {letter_data['statement_date']}</p>
                        <p><strong>الفترة:</strong> {letter_data['period_label']}</p>
                        
                        <h3>الخصومات والبنود</h3>
                        <table>
                            <thead>
                                <tr><th>البند</th><th>الوصف</th><th>المبلغ (درهم)</th></tr>
                            </thead>
                            <tbody>{deductions_rows}</tbody>
                        </table>
                        
                        <div class="summary">
                            <p><strong>الراتب الإجمالي:</strong> {letter_data['gross_salary']} درهم</p>
                            <p><strong>إجمالي الخصومات:</strong> {letter_data['total_deductions']} درهم</p>
                            <p style="font-size: 1.2em;"><strong>صافي الراتب:</strong> {letter_data['net_pay']} درهم</p>
                        </div>
                    </div>
                </body>
                </html>
                """
                return HTMLResponse(content=html)

        except HTTPException:
            raise
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Error generating salary letter: {str(e)}")

    return router
