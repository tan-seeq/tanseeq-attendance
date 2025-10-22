@api_router.post("/deductions/calculate-monthly")
async def calculate_monthly_deductions_endpoint(
    month: str = Query(..., description="Month in YYYY-MM format"),
    current_user: User = Depends(get_super_admin_user)
):
    """
    حساب خصومات التأخير والغياب لشهر معين باستخدام النظام المتقدم
    ✅ Uses advanced_deductions_system for accurate calculations
    ✅ Returns detailed daily breakdown for each employee
    """
    try:
        # Validate month format
        if not month or '-' not in month:
            raise HTTPException(
                status_code=400,
                detail="تنسيق الشهر غير صحيح. يجب أن يكون بصيغة YYYY-MM مثل 2025-10"
            )
        
        parts = month.split('-')
        if len(parts) != 2:
            raise HTTPException(
                status_code=400,
                detail="تنسيق الشهر غير صحيح. يجب أن يكون بصيغة YYYY-MM مثل 2025-10"
            )
        
        year_str, month_str = parts
        year = int(year_str)
        month_num = int(month_str)
        
        if year < 2020 or year > 2100:
            raise HTTPException(status_code=400, detail="السنة خارج النطاق المقبول")
        
        if month_num < 1 or month_num > 12:
            raise HTTPException(status_code=400, detail="الشهر يجب أن يكون بين 1 و 12")
        
        # Use advanced_deductions_system
        from advanced_deductions_system import calculate_monthly_deductions as calc_monthly
        
        deduction_summaries = await calc_monthly(
            db=db,
            year=year,
            month=month_num
        )
        
        # Calculate cycle dates for display
        if month_num == 1:
            cycle_start = date(year - 1, 12, 29)
        else:
            cycle_start = date(year, month_num - 1, 29)
        cycle_end = date(year, month_num, 28)
        
        # Convert to API response format
        results = []
        total_deductions = 0
        
        for summary in deduction_summaries:
            # Build daily_breakdown from daily_records
            daily_breakdown = []
            for day in summary.daily_records:
                status = "absent" if day.is_absent else "present"
                working_hours = day.total_work_minutes / 60 if day.total_work_minutes > 0 else 0
                
                daily_breakdown.append({
                    "date": day.date,
                    "status": status,
                    "check_in": day.check_in if day.check_in else "-",
                    "check_out": day.check_out if day.check_out else "-",
                    "total_work_minutes": day.total_work_minutes,
                    "late_minutes": day.late_minutes,
                    "early_leave_minutes": day.early_leave_minutes,
                    "deficit_minutes": day.deficit_minutes,
                    "working_hours": round(working_hours, 2),
                    "deduction_amount": round(day.deduction_amount, 2),
                    "is_absent": day.is_absent
                })
            
            results.append({
                "employee_id": summary.employee_id,
                "employee_name": summary.employee_name,
                "monthly_salary": summary.basic_salary,
                "late_deduction": round(summary.late_deduction, 2),
                "absence_deduction": round(summary.absence_deduction, 2),
                "total_deduction": round(summary.total_deduction_amount, 2),
                "deduction_details": summary.deduction_details,
                "late_count": summary.late_count,
                "absence_count": summary.absence_count,
                "total_late_minutes": summary.total_late_minutes,
                "daily_breakdown": daily_breakdown
            })
            total_deductions += summary.total_deduction_amount
        
        return {
            "success": True,
            "mode": "monthly",
            "month": month,
            "cycle_window": {
                "from_date": cycle_start.isoformat(),
                "to_date": cycle_end.isoformat(),
                "description": f"دورة شهرية: 29-28"
            },
            "employees": results,
            "total_deductions": round(total_deductions, 2),
            "employee_count": len(results),
            "note": "✅ Advanced Deductions with Daily Breakdown"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"❌ Monthly Calculation Error: {str(e)}")
        print(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"خطأ في حساب الخصومات: {str(e)}")
