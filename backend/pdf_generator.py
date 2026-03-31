"""
PDF Salary Slip Generator - TANSEEQ HR System
Generates professional English salary slips
"""
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Paragraph, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

FONT = 'Helvetica'
FONT_BOLD = 'Helvetica-Bold'


def generate_salary_slip(employee: dict, payroll_data: dict, cycle_month: str) -> bytes:
    """Generate a professional English salary slip PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)

    elements = []

    # ====== HEADER ======
    company_name = payroll_data.get('company_name', 'TANSEEQ Tax Consultancy')

    header_data = [
        [Paragraph(f'<b>{company_name}</b>', ParagraphStyle('h', fontName=FONT_BOLD, fontSize=16, alignment=TA_CENTER))],
        [Paragraph('Salary Slip', ParagraphStyle('h2', fontName=FONT, fontSize=12, alignment=TA_CENTER, textColor=colors.HexColor('#2b6cb0')))],
        [Paragraph(f'Period: {cycle_month}', ParagraphStyle('h3', fontName=FONT, fontSize=9, alignment=TA_CENTER, textColor=colors.grey))],
    ]
    header_table = Table(header_data, colWidths=[180*mm])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 5*mm))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#2b6cb0')))
    elements.append(Spacer(1, 5*mm))

    # ====== EMPLOYEE INFO ======
    emp_name = employee.get('name', 'N/A')
    emp_id = employee.get('id', 'N/A')[:8]
    emp_position = employee.get('position', 'N/A')
    emp_email = employee.get('email', 'N/A')
    emp_dept = employee.get('department', 'General')

    info_data = [
        ['Employee Name', emp_name, 'Employee ID', emp_id],
        ['Position', emp_position, 'Email', emp_email],
        ['Department', emp_dept, 'Pay Period', cycle_month],
    ]
    info_table = Table(info_data, colWidths=[35*mm, 55*mm, 35*mm, 55*mm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), FONT_BOLD),
        ('FONTNAME', (2, 0), (2, -1), FONT_BOLD),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#4a5568')),
        ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#4a5568')),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f7fafc')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 8*mm))

    # ====== EARNINGS ======
    basic_salary = payroll_data.get('basic_salary', employee.get('monthly_salary', 0))
    overtime_amount = payroll_data.get('overtime_amount', 0)
    allowances = payroll_data.get('allowances', 0)
    total_earnings = basic_salary + overtime_amount + allowances

    section_style = ParagraphStyle('Section', fontName=FONT_BOLD, fontSize=11, textColor=colors.HexColor('#1a365d'), spaceAfter=8)
    elements.append(Paragraph('<b>Earnings</b>', section_style))

    earnings_data = [
        ['Item', 'Amount (AED)'],
        ['Basic Salary', f'{basic_salary:,.2f}'],
        ['Overtime', f'{overtime_amount:,.2f}'],
        ['Allowances', f'{allowances:,.2f}'],
        ['Total Earnings', f'{total_earnings:,.2f}'],
    ]
    earnings_table = Table(earnings_data, colWidths=[120*mm, 60*mm])
    earnings_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
        ('FONTNAME', (0, -1), (-1, -1), FONT_BOLD),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2b6cb0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ebf8ff')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#2b6cb0')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
    ]))
    elements.append(earnings_table)
    elements.append(Spacer(1, 6*mm))

    # ====== DEDUCTIONS ======
    lateness_deductions = payroll_data.get('lateness_deductions', 0)
    absence_deductions = payroll_data.get('absence_deductions', 0)
    advance_deductions = payroll_data.get('advance_deductions', 0)
    loan_installments = payroll_data.get('loan_installments', 0)
    other_deductions = payroll_data.get('other_deductions', 0)
    total_deductions = lateness_deductions + absence_deductions + advance_deductions + loan_installments + other_deductions

    elements.append(Paragraph('<b>Deductions</b>', section_style))

    deductions_data = [
        ['Item', 'Amount (AED)'],
        ['Lateness Deduction', f'{lateness_deductions:,.2f}'],
        ['Absence Deduction', f'{absence_deductions:,.2f}'],
        ['Advance Repayment', f'{advance_deductions:,.2f}'],
        ['Loan Installment', f'{loan_installments:,.2f}'],
        ['Other Deductions', f'{other_deductions:,.2f}'],
        ['Total Deductions', f'{total_deductions:,.2f}'],
    ]
    deductions_table = Table(deductions_data, colWidths=[120*mm, 60*mm])
    deductions_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
        ('FONTNAME', (0, -1), (-1, -1), FONT_BOLD),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#c53030')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#fff5f5')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#c53030')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
    ]))
    elements.append(deductions_table)
    elements.append(Spacer(1, 6*mm))

    # ====== ATTENDANCE SUMMARY ======
    working_days = payroll_data.get('working_days', 0)
    present_days = payroll_data.get('present_days', 0)
    absent_days = payroll_data.get('absent_days', 0)
    late_days = payroll_data.get('late_days', 0)
    overtime_hours = payroll_data.get('overtime_hours', 0)

    elements.append(Paragraph('<b>Attendance Summary</b>', section_style))

    att_data = [
        ['Item', 'Days / Hours'],
        ['Working Days in Period', str(working_days)],
        ['Days Present', str(present_days)],
        ['Days Absent', str(absent_days)],
        ['Late Incidents', str(late_days)],
        ['Overtime Hours', f'{overtime_hours:.1f}'],
    ]
    att_table = Table(att_data, colWidths=[120*mm, 60*mm])
    att_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
    ]))
    elements.append(att_table)
    elements.append(Spacer(1, 6*mm))

    # ====== ADVANCES & LOANS SUMMARY ======
    advances_balance = payroll_data.get('advances_balance', 0)
    loans_balance = payroll_data.get('loans_balance', 0)

    if advances_balance > 0 or loans_balance > 0:
        elements.append(Paragraph('<b>Advances & Loans Balance</b>', section_style))

        al_data = [
            ['Item', 'Balance (AED)'],
            ['Outstanding Advances', f'{advances_balance:,.2f}'],
            ['Outstanding Loans', f'{loans_balance:,.2f}'],
            ['Total Outstanding', f'{advances_balance + loans_balance:,.2f}'],
        ]
        al_table = Table(al_data, colWidths=[120*mm, 60*mm])
        al_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
            ('FONTNAME', (0, -1), (-1, -1), FONT_BOLD),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#744210')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#fffff0')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ]))
        elements.append(al_table)
        elements.append(Spacer(1, 6*mm))

    # ====== NET SALARY ======
    net_salary = total_earnings - total_deductions

    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#2b6cb0')))
    elements.append(Spacer(1, 3*mm))

    net_data = [
        ['Total Earnings', 'Total Deductions', 'Net Salary'],
        [f'AED {total_earnings:,.2f}', f'AED {total_deductions:,.2f}', f'AED {net_salary:,.2f}'],
    ]
    net_table = Table(net_data, colWidths=[60*mm, 60*mm, 60*mm])
    net_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), FONT_BOLD),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, 1), 11),
        ('TEXTCOLOR', (0, 1), (0, 1), colors.HexColor('#2b6cb0')),
        ('TEXTCOLOR', (1, 1), (1, 1), colors.HexColor('#c53030')),
        ('TEXTCOLOR', (2, 0), (2, 1), colors.HexColor('#276749')),
        ('BACKGROUND', (2, 0), (2, 1), colors.HexColor('#f0fff4')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(net_table)
    elements.append(Spacer(1, 10*mm))

    # ====== FOOTER ======
    footer_style = ParagraphStyle('Footer', fontName=FONT, fontSize=7, textColor=colors.grey, alignment=TA_CENTER)
    generated_at = datetime.now().strftime('%Y-%m-%d %H:%M')
    elements.append(Paragraph('This is a system-generated document. No signature required.', footer_style))
    elements.append(Paragraph(f'Generated: {generated_at} | {company_name}', footer_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
