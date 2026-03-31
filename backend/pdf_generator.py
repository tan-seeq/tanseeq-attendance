"""
PDF Salary Slip Generator - TANSEEQ HR System
Generates professional Arabic salary slips with full RTL Arabic support
"""
import io
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Paragraph, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Arabic text shaping
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_ARABIC = True
except ImportError:
    HAS_ARABIC = False

# Register Arabic fonts
FONT_DIR = os.path.join(os.path.dirname(__file__), 'fonts')
FONT_NAME = 'Helvetica'
FONT_BOLD = 'Helvetica-Bold'
AR_FONT = 'Amiri'
AR_FONT_BOLD = 'Amiri-Bold'
HAS_AR_FONT = False

try:
    amiri_regular = os.path.join(FONT_DIR, 'Amiri-Regular.ttf')
    amiri_bold = os.path.join(FONT_DIR, 'Amiri-Bold.ttf')
    if os.path.exists(amiri_regular) and os.path.exists(amiri_bold):
        pdfmetrics.registerFont(TTFont(AR_FONT, amiri_regular))
        pdfmetrics.registerFont(TTFont(AR_FONT_BOLD, amiri_bold))
        HAS_AR_FONT = True
        print("Arabic fonts registered successfully")
except Exception as e:
    print(f"Could not register Arabic fonts: {e}")


def ar(text):
    """Reshape and reorder Arabic text for correct PDF rendering"""
    if not text or not HAS_ARABIC:
        return str(text)
    text = str(text)
    try:
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except Exception:
        return text


def get_fonts():
    """Return the appropriate font pair"""
    if HAS_AR_FONT:
        return AR_FONT, AR_FONT_BOLD
    return FONT_NAME, FONT_BOLD


def generate_salary_slip(employee: dict, payroll_data: dict, cycle_month: str) -> bytes:
    """Generate a professional Arabic salary slip PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)

    font, font_bold = get_fonts()
    elements = []
    styles = getSampleStyleSheet()

    # Custom Arabic-aware styles
    title_style = ParagraphStyle('Title', parent=styles['Title'], fontName=font_bold, fontSize=16, alignment=TA_CENTER, spaceAfter=5)
    header_style = ParagraphStyle('Header', parent=styles['Normal'], fontName=font_bold, fontSize=11, textColor=colors.HexColor('#1a365d'), spaceAfter=8, alignment=TA_RIGHT)

    # ====== HEADER ======
    company_name = payroll_data.get('company_name', 'TANSEEQ Tax Consultancy')

    header_data = [
        [Paragraph(f'<b>{ar(company_name)}</b>', ParagraphStyle('h', fontName=font_bold, fontSize=14, alignment=TA_CENTER))],
        [Paragraph(ar('كشف الراتب'), ParagraphStyle('h2', fontName=font, fontSize=11, alignment=TA_CENTER, textColor=colors.HexColor('#2b6cb0')))],
        [Paragraph(f'{ar("الفترة")}: {cycle_month}', ParagraphStyle('h3', fontName=font, fontSize=9, alignment=TA_CENTER, textColor=colors.grey))],
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

    info_data = [
        [emp_id, ar('رقم الموظف'), ar(emp_name), ar('اسم الموظف')],
        [emp_email, ar('البريد الإلكتروني'), ar(emp_position), ar('المسمى الوظيفي')],
        [cycle_month, ar('فترة الدفع'), ar(employee.get('department', 'عام')), ar('القسم')],
    ]
    info_table = Table(info_data, colWidths=[55*mm, 35*mm, 55*mm, 35*mm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (1, 0), (1, -1), font_bold),
        ('FONTNAME', (3, 0), (3, -1), font_bold),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#4a5568')),
        ('TEXTCOLOR', (3, 0), (3, -1), colors.HexColor('#4a5568')),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f7fafc')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('ALIGN', (2, 0), (2, -1), 'LEFT'),
        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 8*mm))

    # ====== EARNINGS ======
    basic_salary = payroll_data.get('basic_salary', employee.get('monthly_salary', 0))
    overtime_amount = payroll_data.get('overtime_amount', 0)
    allowances = payroll_data.get('allowances', 0)
    total_earnings = basic_salary + overtime_amount + allowances

    elements.append(Paragraph(f'<b>{ar("المستحقات")}</b>', header_style))

    earnings_data = [
        [ar('المبلغ (درهم)'), ar('البند')],
        [f'{basic_salary:,.2f}', ar('الراتب الأساسي')],
        [f'{overtime_amount:,.2f}', ar('الساعات الإضافية')],
        [f'{allowances:,.2f}', ar('البدلات')],
        [f'{total_earnings:,.2f}', ar('إجمالي المستحقات')],
    ]
    earnings_table = Table(earnings_data, colWidths=[60*mm, 120*mm])
    earnings_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), font_bold),
        ('FONTNAME', (0, -1), (-1, -1), font_bold),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2b6cb0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ebf8ff')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#2b6cb0')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
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

    elements.append(Paragraph(f'<b>{ar("الخصومات")}</b>', header_style))

    deductions_data = [
        [ar('المبلغ (درهم)'), ar('البند')],
        [f'{lateness_deductions:,.2f}', ar('خصم التأخير')],
        [f'{absence_deductions:,.2f}', ar('خصم الغياب')],
        [f'{advance_deductions:,.2f}', ar('سداد السلف')],
        [f'{loan_installments:,.2f}', ar('أقساط القروض')],
        [f'{other_deductions:,.2f}', ar('خصومات أخرى')],
        [f'{total_deductions:,.2f}', ar('إجمالي الخصومات')],
    ]
    deductions_table = Table(deductions_data, colWidths=[60*mm, 120*mm])
    deductions_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), font_bold),
        ('FONTNAME', (0, -1), (-1, -1), font_bold),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#c53030')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#fff5f5')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#c53030')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
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

    elements.append(Paragraph(f'<b>{ar("ملخص الحضور")}</b>', header_style))

    att_data = [
        [ar('عدد الأيام/الساعات'), ar('البند')],
        [str(working_days), ar('أيام العمل في الفترة')],
        [str(present_days), ar('أيام الحضور')],
        [str(absent_days), ar('أيام الغياب')],
        [str(late_days), ar('مرات التأخير')],
        [f'{overtime_hours:.1f}', ar('ساعات العمل الإضافية')],
    ]
    att_table = Table(att_data, colWidths=[60*mm, 120*mm])
    att_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), font_bold),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
    ]))
    elements.append(att_table)
    elements.append(Spacer(1, 6*mm))

    # ====== ADVANCES & LOANS SUMMARY ======
    advances_balance = payroll_data.get('advances_balance', 0)
    loans_balance = payroll_data.get('loans_balance', 0)

    if advances_balance > 0 or loans_balance > 0:
        elements.append(Paragraph(f'<b>{ar("رصيد السلف والقروض")}</b>', header_style))

        al_data = [
            [ar('الرصيد (درهم)'), ar('البند')],
            [f'{advances_balance:,.2f}', ar('السلف المستحقة')],
            [f'{loans_balance:,.2f}', ar('القروض المستحقة')],
            [f'{advances_balance + loans_balance:,.2f}', ar('إجمالي المستحق')],
        ]
        al_table = Table(al_data, colWidths=[60*mm, 120*mm])
        al_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), font_bold),
            ('FONTNAME', (0, -1), (-1, -1), font_bold),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#744210')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#fffff0')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ]))
        elements.append(al_table)
        elements.append(Spacer(1, 6*mm))

    # ====== NET SALARY ======
    net_salary = total_earnings - total_deductions

    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#2b6cb0')))
    elements.append(Spacer(1, 3*mm))

    net_data = [
        [ar('صافي الراتب'), ar('إجمالي الخصومات'), ar('إجمالي المستحقات'), ''],
        [f'{net_salary:,.2f} {ar("درهم")}', f'{total_deductions:,.2f} {ar("درهم")}', f'{total_earnings:,.2f} {ar("درهم")}', ''],
    ]
    net_table = Table(net_data, colWidths=[50*mm, 50*mm, 50*mm, 30*mm])
    net_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), font_bold),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, 1), 11),
        ('TEXTCOLOR', (2, 1), (2, 1), colors.HexColor('#2b6cb0')),
        ('TEXTCOLOR', (1, 1), (1, 1), colors.HexColor('#c53030')),
        ('TEXTCOLOR', (0, 0), (0, 1), colors.HexColor('#276749')),
        ('BACKGROUND', (0, 0), (0, 1), colors.HexColor('#f0fff4')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (2, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(net_table)
    elements.append(Spacer(1, 10*mm))

    # ====== FOOTER ======
    footer_style = ParagraphStyle('Footer', fontName=font, fontSize=7, textColor=colors.grey, alignment=TA_CENTER)
    generated_at = datetime.now().strftime('%Y-%m-%d %H:%M')
    elements.append(Paragraph(ar('هذا مستند إلكتروني ولا يحتاج إلى توقيع'), footer_style))
    elements.append(Paragraph(f'{ar("تاريخ الإصدار")}: {generated_at} | {ar(company_name)}', footer_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
