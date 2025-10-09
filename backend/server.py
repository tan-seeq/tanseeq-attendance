from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.responses import JSONResponse, Response
from typing import Optional, List
from datetime import datetime, timezone, date
import uuid
from motor.motor_asyncio import AsyncIOMotorClient

# ... existing imports and setup remain unchanged ...

# Existing code above ...

# ================= Salary Letter Endpoint (patched for Ledger parity) =================
@app.get("/api/payroll/cycles/{cycle_id}/employees/{employee_id}/letter")
async def generate_salary_letter(
    cycle_id: str,
    employee_id: str,
    format: str = "html",
    current_user: dict = Depends(get_current_user)
):
    """
    إنشاء رسالة راتب شهرية للموظف
    format: html or pdf
    """
    try:
        # جلب دورة الراتب
        cycle = await db.payroll_cycles.find_one({"id": cycle_id})
        if not cycle:
            raise HTTPException(status_code=404, detail="دورة الراتب غير موجودة")
        
        # جلب ملخص راتب الموظف
        employee_summary = await db.employee_payroll_summaries.find_one({
            "payroll_cycle_id": cycle_id,
            "employee_id": employee_id
        })
        
        if not employee_summary:
            raise HTTPException(status_code=404, detail="لم يتم العثور على بيانات راتب الموظف")
        
        # جلب بيانات الموظف
        employee = await db.users.find_one({"id": employee_id})
        if not employee:
            raise HTTPException(status_code=404, detail="الموظف غير موجود")
        
        # حساب المعدلات
        base_salary = employee_summary.get("base_salary", 0)
        daily_rate = base_salary / 30
        hourly_rate = daily_rate / 8
        minute_rate = hourly_rate / 60
        
        # جلب تفاصيل الخصومات من Payroll Ledger
        # Patch: use cycle_id (not payroll_cycle_id) and source_type (not entry_type)
        ledger_entries = await db.payroll_ledger.find({
            "employee_id": employee_id,
            "cycle_id": cycle_id
        }).to_list(None)
        
        # تنسيق: إزالة _id لتسلسل JSON
        for entry in ledger_entries:
            entry.pop("_id", None)
        
        # تصنيف البنود
        attendance_deductions = []
        leave_adjustments = []
        manual_deductions = []
        advance_installments = []
        custody_adjustments = []
        
        for entry in ledger_entries:
            entry_type = entry.get("source_type", "")
            amount = float(entry.get("amount", 0) or 0)
            description = entry.get("description", "")
            
            if entry_type == "ATTENDANCE_DEDUCTION":
                attendance_deductions.append({
                    "description": description,
                    "amount": amount
                })
            elif entry_type == "LEAVE_ADJUSTMENT":
                leave_adjustments.append({
                    "description": description,
                    "amount": amount
                })
            elif entry_type == "MANUAL_DEDUCTION":
                manual_deductions.append({
                    "description": description,
                    "amount": amount
                })
            elif entry_type == "ADVANCE_INSTALLMENT":
                advance_installments.append({
                    "description": description,
                    "amount": amount,
                    # reference_id is the source_id for installment linkage
                    "reference_id": entry.get("source_id", "")
                })
            elif entry_type == "CUSTODY_ADJUSTMENT":
                custody_adjustments.append({
                    "description": description,
                    "amount": amount
                })
        
        # حساب الإجماليات (استخدام القيمة المطلقة للخصومات)
        total_attendance_deductions = sum(abs(d["amount"]) for d in attendance_deductions)
        total_leave_adjustments = sum(d["amount"] for d in leave_adjustments)  # قد تكون موجبة أو سالبة
        total_manual_deductions = sum(abs(d["amount"]) for d in manual_deductions)
        total_advance_deductions = sum(abs(d["amount"]) for d in advance_installments)
        total_custody_adjustments = sum(d["amount"] for d in custody_adjustments)  # قد تكون موجبة أو سالبة
        
        # جلب تفاصيل السلف (إذا وجدت) عبر أول قسط
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
        
        # إعداد البيانات للقالب
        from uae_datetime_utils import get_uae_date_str
        letter_data = {
            "statement_date": get_uae_date_str(),
            "employee_name": employee.get("name", ""),
            "employee_code": employee.get("id", "")[:8],
            "period_label": f"{cycle.get('month', '')}",
            "base_salary": f"{base_salary:,.2f}",
            "daily_rate": f"{daily_rate:,.4f}",
            "hourly_rate": f"{hourly_rate:,.4f}",
            "minute_rate": f"{minute_rate:,.6f}",
            
            # الإجازات
            "leave_summary": "لا توجد" if not leave_adjustments else f"{len(leave_adjustments)} تعديل(ات)",
            "leave_lines": leave_adjustments,
            
            # الغياب والتأخير
            "absence_summary": attendance_deductions,
            "attendance_deductions_total": f"{total_attendance_deductions:,.2f}",
            
            # الخصومات اليدوية
            "manual_deductions_total": f"{total_manual_deductions:,.2f}",
            "manual_lines": manual_deductions,
            
            # السلف
            "advance_details": advance_details,
            "advance_installments_list": advance_installments,
            "advance_deductions_total": f"{total_advance_deductions:,.2f}",
            
            # العهد
            "custody_adjustments_total": f"{total_custody_adjustments:,.2f}",
            "custody_lines": custody_adjustments,
            
            # الصافي
            "net_pay": f"{employee_summary.get('net_salary', 0):,.2f}",
            "gross_salary": f"{employee_summary.get('gross_salary', 0):,.2f}",
            "total_deductions": f"{employee_summary.get('total_deductions', 0):,.2f}",
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
            from fastapi.responses import HTMLResponse
            # Build deductions rows
            deductions_rows = ""
            # Attendance
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
            # Manual
            if manual_deductions:
                for d in manual_deductions:
                    deductions_rows += f"""
                    <tr>
                        <td>خصم يدوي</td>
                        <td>{d['description']}</td>
                        <td style='color:#dc2626;font-weight:bold;'>{abs(d['amount']):.2f}</td>
                    </tr>
                    """
            # Advance installments
            if advance_installments:
                for d in advance_installments:
                    deductions_rows += f"""
                    <tr>
                        <td>قسط سلفة</td>
                        <td>{d['description']}</td>
                        <td style='color:#dc2626;font-weight:bold;'>{abs(d['amount']):.2f}</td>
                    </tr>
                    """
            html = f"""
            <html><body>
            <h2>Salary Letter - {letter_data['employee_name']}</h2>
            <p>Statement Date (UAE): {letter_data['statement_date']}</p>
            <table border='1' cellpadding='6' cellspacing='0' width='100%'>
            <thead><tr><th>البند</th><th>الوصف</th><th>المبلغ</th></tr></thead>
            <tbody>{deductions_rows}</tbody>
            </table>
            <p><strong>الصافي:</strong> {letter_data['net_pay']}</p>
            </body></html>
            """
            return HTMLResponse(content=html)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating salary letter: {str(e)}")

# ... rest of server.py remains unchanged ...
