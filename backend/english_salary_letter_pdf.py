"""
English Salary Letter PDF Generator
=====================================
Generates clean English-only salary letters in PDF format
Avoids all Arabic RTL complexity
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
import io


def translate_description_to_english(description):
    """
    Translate Arabic descriptions to English for PDF
    """
    # Common translations
    translations = {
        # General terms
        'خصم': 'Deduction',
        'خصومات': 'Deductions',
        'يدوي': 'manual',
        'حضور': 'attendance',
        'تأخير': 'late arrival',
        'غياب': 'absence',
        'سلفة': 'advance',
        'قسط': 'installment',
        'درهم': 'AED',
        'دقيقة': 'minute',
        'دقائق': 'minutes',
        'يوم': 'day',
        'أيام': 'days',
        'ساعة': 'hour',
        'ساعات': 'hours',
        'مرة': 'time',
        'مرات': 'times',
        'قابلة للخصم': 'deductible',
        'الحضور والتأخير': 'Attendance & Lateness',
        'تم تعديله بواسطة الإدارة': 'adjusted by management',
        'رقم': '#',
        'استحقاق': 'Due:',
        
        # Full phrases
        'خصومات الحضور والتأخير': 'Attendance & Lateness Deductions',
        'خصم حضور/تأخير': 'Attendance/Late Deduction',
        'خصم يدوي': 'Manual Deduction',
        'قسط سلفة': 'Advance Installment',
        'خصم سلفة': 'Advance Deduction',
    }
    
    # Start with original description
    result = description
    
    # Remove " - " separator patterns with numbers (e.g., "- 93.45 -")
    import re
    result = re.sub(r'\s*-\s*\d+\.?\d*\s*-?\s*', ' ', result)
    result = re.sub(r'\s*-\s*late\s*-\s*', ' ', result)
    
    # Replace Arabic terms
    for arabic, english in translations.items():
        result = result.replace(arabic, english)
    
    # Clean up extra spaces and dashes
    result = re.sub(r'\s+-\s+', ' - ', result)
    result = re.sub(r'\s+', ' ', result)
    result = result.strip(' -')
    
    # If still contains Arabic or is too messy, use generic description
    if any('\u0600' <= c <= '\u06FF' for c in result):
        # Still has Arabic characters, use generic
        if 'late' in description.lower() or 'تأخير' in description:
            return 'Late arrival deduction'
        elif 'manual' in description.lower() or 'يدوي' in description:
            return 'Manual deduction'
        elif 'advance' in description.lower() or 'سلفة' in description:
            return 'Advance installment'
        elif 'attendance' in description.lower() or 'حضور' in description:
            return 'Attendance deduction'
        else:
            return 'Deduction'
    
    return result


def generate_english_salary_letter_pdf(letter_data, attendance_deductions, manual_deductions, advance_installments):
    """Generate English-only salary letter PDF"""
    
    buffer = io.BytesIO()
    # Reduced margins to fit content in one page
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                           rightMargin=1*cm, leftMargin=1*cm, 
                           topMargin=1*cm, bottomMargin=1*cm)
    
    # Create styles
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=14,  # Reduced from 18
        alignment=TA_CENTER,
        spaceAfter=4,  # Reduced from 12
        textColor=colors.HexColor('#1e40af')
    )
    
    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,  # Reduced from 14
        alignment=TA_LEFT,
        spaceAfter=4,  # Reduced from 8
        textColor=colors.HexColor('#1e40af')
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,  # Reduced from 11
        alignment=TA_LEFT,
        spaceAfter=2  # Reduced from 6
    )
    
    # Build document
    story = []
    
    # Header - compact
    story.append(Paragraph("TANSEEQ TAX CONSULTANCY", title_style))
    story.append(Paragraph("Salary Statement", title_style))
    story.append(Spacer(1, 0.2*cm))
    # Compact header info
    header_info = f"Date: {letter_data['statement_date']} | Employee: {letter_data['employee_name']} | ID: {letter_data['employee_code']} | Period: {letter_data['period_label']}"
    story.append(Paragraph(header_info, normal_style))
    story.append(Spacer(1, 0.3*cm))
    
    # Section 1: Deductions
    story.append(Paragraph("1) DEDUCTIONS BREAKDOWN", heading_style))
    
    deductions_data = [
        ["Type", "Description", "Amount (AED)"]
    ]
    
    # Attendance deductions
    if attendance_deductions and len(attendance_deductions) > 0:
        for d in attendance_deductions:
            desc_english = translate_description_to_english(d['description'])
            deductions_data.append([
                "Attendance",
                desc_english,
                f"{d['amount']:.2f}"
            ])
    
    # Manual deductions
    if manual_deductions and len(manual_deductions) > 0:
        for d in manual_deductions:
            desc_english = translate_description_to_english(d['description'])
            deductions_data.append([
                "Manual",
                desc_english,
                f"{d['amount']:.2f}"
            ])
    
    # Advance installments
    if advance_installments and len(advance_installments) > 0:
        for d in advance_installments:
            desc_english = translate_description_to_english(d['description'])
            deductions_data.append([
                "Advance",
                desc_english,
                f"{d['amount']:.2f}"
            ])
    
    # If no deductions
    if len(deductions_data) == 1:
        deductions_data.append(["--", "No deductions", "0.00"])
    
    # Add total row
    deductions_data.append([
        "TOTAL DEDUCTIONS",
        "",
        letter_data['total_deductions']
    ])
    
    deductions_table = Table(deductions_data, colWidths=[3*cm, 9*cm, 4*cm])
    deductions_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -2), 10),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 11),
        ('BACKGROUND', (0, 1), (-1, -2), colors.HexColor('#ffffff')),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#dc2626')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),  # Reduced
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),  # Reduced
    ]))
    story.append(deductions_table)
    story.append(Spacer(1, 0.2*cm))
    
    # Section 2: Net Salary
    story.append(Paragraph("2) NET SALARY SUMMARY", heading_style))
    
    summary_data = [
        ["Description", "Amount (AED)"],
        ["Gross Salary", letter_data['gross_salary']],
        ["Total Deductions", f"({letter_data['total_deductions']})"],
        ["NET PAYABLE", letter_data['net_pay']]
    ]
    
    summary_table = Table(summary_data, colWidths=[10*cm, 6*cm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -2), 10),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 13),
        ('BACKGROUND', (0, 1), (-1, -2), colors.HexColor('#f0f9ff')),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#059669')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),  # Reduced
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),  # Reduced
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.2*cm))
    
    # Compact note
    story.append(Paragraph(
        f"<i><font size=8>Auto-generated. Cycle ID: {letter_data['cycle_code']}</font></i>",
        normal_style
    ))
    story.append(Spacer(1, 0.3*cm))
    
    # Signatures
    signature_data = [
        ["Employee Signature:", "HR Signature:"],
        ["", ""],
        ["Name: _____________", "Name: _____________"],
        ["Date: _____________", "Date: _____________"]
    ]
    
    signature_table = Table(signature_data, colWidths=[8*cm, 8*cm])
    signature_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 5),  # Reduced
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),  # Reduced
        ('BOX', (0, 0), (0, -1), 1, colors.grey),
        ('BOX', (1, 0), (1, -1), 1, colors.grey),
    ]))
    story.append(signature_table)
    
    # Build PDF
    doc.build(story)
    
    buffer.seek(0)
    return buffer.getvalue()
