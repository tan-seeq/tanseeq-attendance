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


def generate_english_salary_letter_pdf(letter_data, attendance_deductions, manual_deductions, advance_installments):
    """Generate English-only salary letter PDF"""
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    
    # Create styles
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=12,
        textColor=colors.HexColor('#1e40af')
    )
    
    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        alignment=TA_LEFT,
        spaceAfter=8,
        textColor=colors.HexColor('#1e40af')
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        alignment=TA_LEFT,
        spaceAfter=6
    )
    
    bold_style = ParagraphStyle(
        'Bold',
        parent=normal_style,
        fontName='Helvetica-Bold'
    )
    
    # Build document
    story = []
    
    # Header
    story.append(Paragraph("TANSEEQ TAX CONSULTANCY", title_style))
    story.append(Paragraph("Salary Statement", title_style))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(f"Date: {letter_data['statement_date']}", normal_style))
    story.append(Paragraph(f"To: Mr./Ms. {letter_data['employee_name']}", normal_style))
    story.append(Paragraph(f"Employee ID: {letter_data['employee_code']}", normal_style))
    story.append(Paragraph(f"Period: {letter_data['period_label']}", normal_style))
    story.append(Spacer(1, 0.5*cm))
    
    # Introduction
    story.append(Paragraph("Dear Employee,", normal_style))
    story.append(Paragraph(
        f"This letter outlines your salary details for the period <b>{letter_data['period_label']}</b> "
        "as calculated according to company policies:",
        normal_style
    ))
    story.append(Spacer(1, 0.5*cm))
    
    # Section 1: Basic Salary Information
    story.append(Paragraph("1) BASIC SALARY INFORMATION", heading_style))
    
    basic_data = [
        ["Description", "Amount (AED)"],
        ["Basic Salary", letter_data['base_salary']],
        ["Daily Rate", f"{letter_data['daily_rate']} (= {letter_data['base_salary']} ÷ 30)"],
        ["Hourly Rate", f"{letter_data['hourly_rate']} (= Daily ÷ 8)"],
        ["Per Minute Rate", f"{letter_data['minute_rate']} (= Hourly ÷ 60)"]
    ]
    
    basic_table = Table(basic_data, colWidths=[10*cm, 6*cm])
    basic_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0f9ff')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(basic_table)
    story.append(Spacer(1, 0.5*cm))
    
    # Section 2: Deductions
    story.append(Paragraph("2) DEDUCTIONS BREAKDOWN", heading_style))
    
    deductions_data = [
        ["Type", "Description", "Amount (AED)"]
    ]
    
    # Attendance deductions
    if attendance_deductions and len(attendance_deductions) > 0:
        for d in attendance_deductions:
            desc_english = d['description'].replace('خصومات الحضور والتأخير', 'Attendance & Lateness')
            desc_english = desc_english.replace('تأخير', 'late')
            desc_english = desc_english.replace('مرات', 'times')
            desc_english = desc_english.replace('دقيقة قابلة للخصم', 'deductible minutes')
            deductions_data.append([
                "Attendance",
                desc_english,
                f"{d['amount']:.2f}"
            ])
    
    # Manual deductions
    if manual_deductions and len(manual_deductions) > 0:
        for d in manual_deductions:
            deductions_data.append([
                "Manual",
                d['description'],
                f"{d['amount']:.2f}"
            ])
    
    # Advance installments
    if advance_installments and len(advance_installments) > 0:
        for d in advance_installments:
            desc_english = d['description'].replace('قسط سلفة رقم', 'Installment #')
            desc_english = desc_english.replace('استحقاق', 'Due:')
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
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(deductions_table)
    story.append(Spacer(1, 0.5*cm))
    
    # Section 3: Net Salary
    story.append(Paragraph("3) NET SALARY SUMMARY", heading_style))
    
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
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.5*cm))
    
    # Note
    story.append(Paragraph(
        f"<i>Note: This statement is generated automatically from the Payroll Ledger system "
        f"based on company policy. Payroll Cycle ID: {letter_data['cycle_code']}</i>",
        normal_style
    ))
    story.append(Spacer(1, 1*cm))
    
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
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('BOX', (0, 0), (0, -1), 1, colors.grey),
        ('BOX', (1, 0), (1, -1), 1, colors.grey),
    ]))
    story.append(signature_table)
    story.append(Spacer(1, 1*cm))
    
    # Footer
    story.append(Paragraph("<b>TANSEEQ TAX CONSULTANCY</b>", ParagraphStyle(
        'Footer',
        parent=normal_style,
        alignment=TA_CENTER,
        fontSize=10,
        textColor=colors.grey
    )))
    story.append(Paragraph("With best regards", ParagraphStyle(
        'Footer2',
        parent=normal_style,
        alignment=TA_CENTER,
        fontSize=9,
        textColor=colors.grey
    )))
    
    # Build PDF
    doc.build(story)
    
    buffer.seek(0)
    return buffer.getvalue()
