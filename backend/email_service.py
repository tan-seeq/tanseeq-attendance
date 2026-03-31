"""
Email Service - TANSEEQ HR System
SMTP email sending via GoDaddy
"""
import os
import ssl
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

logger = logging.getLogger(__name__)

SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtpout.secureserver.net')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_EMAIL = os.environ.get('SMTP_EMAIL', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
SMTP_FROM_NAME = os.environ.get('SMTP_FROM_NAME', 'Al Tanseeq HR System')


def send_email(to_email: str, subject: str, html_body: str, attachments: list = None) -> dict:
    """Send email via SMTP with optional PDF attachments"""
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        return {"success": False, "error": "SMTP credentials not configured"}
    
    try:
        msg = MIMEMultipart()
        msg['From'] = f'{SMTP_FROM_NAME} <{SMTP_EMAIL}>'
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
        
        if attachments:
            for att in attachments:
                part = MIMEApplication(att['data'], Name=att['filename'])
                part['Content-Disposition'] = f'attachment; filename="{att["filename"]}"'
                msg.attach(part)
        
        context = ssl.create_default_context()
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"Email sent successfully to {to_email}")
        return {"success": True, "message": f"Email sent to {to_email}"}
    
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP auth error: {e}")
        return {"success": False, "error": "Authentication failed - check email/password"}
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Email error: {e}")
        return {"success": False, "error": str(e)}


def send_salary_slip_email(to_email: str, employee_name: str, cycle_month: str, pdf_data: bytes) -> dict:
    """Send salary slip PDF via email"""
    subject = f"Salary Slip - {cycle_month} | {employee_name}"
    
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; direction: rtl;">
        <div style="background: #2b6cb0; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
            <h2 style="margin: 0;">Al Tanseeq Tax Consultancy</h2>
            <p style="margin: 5px 0 0; opacity: 0.9;">HR Management System</p>
        </div>
        <div style="padding: 25px; background: #f7fafc; border: 1px solid #e2e8f0;">
            <p>Dear <strong>{employee_name}</strong>,</p>
            <p>Please find attached your salary slip for <strong>{cycle_month}</strong>.</p>
            <div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 15px; margin: 15px 0;">
                <p style="margin: 0; color: #4a5568;">The attached PDF contains your complete salary details including:</p>
                <ul style="color: #4a5568;">
                    <li>Basic Salary & Earnings</li>
                    <li>Attendance Summary</li>
                    <li>Deductions (Lateness, Absence, Advances)</li>
                    <li>Net Salary</li>
                </ul>
            </div>
            <p style="color: #718096; font-size: 12px;">If you have any questions, please contact the HR department.</p>
        </div>
        <div style="background: #2d3748; color: #a0aec0; padding: 15px; text-align: center; font-size: 11px; border-radius: 0 0 8px 8px;">
            <p style="margin: 0;">This is an automated message from TANSEEQ HR System</p>
        </div>
    </div>
    """
    
    attachments = [{
        'data': pdf_data,
        'filename': f'salary_slip_{cycle_month}_{employee_name.replace(" ", "_")}.pdf'
    }]
    
    return send_email(to_email, subject, html_body, attachments)


def send_notification_email(to_email: str, employee_name: str, notification_type: str, details: dict) -> dict:
    """Send notification email (lateness, absence, advance request)"""
    
    templates = {
        'lateness': {
            'subject': f'Lateness Notice - {details.get("date", "")}',
            'color': '#dd6b20',
            'title': 'Lateness Notice',
            'body': f"""
                <p>Dear <strong>{employee_name}</strong>,</p>
                <p>This is to inform you that a <strong>lateness</strong> has been recorded:</p>
                <div style="background: #fffaf0; border-right: 4px solid #dd6b20; padding: 12px; margin: 10px 0;">
                    <p><strong>Date:</strong> {details.get('date', 'N/A')}</p>
                    <p><strong>Expected:</strong> {details.get('expected_time', 'N/A')}</p>
                    <p><strong>Actual:</strong> {details.get('actual_time', 'N/A')}</p>
                    <p><strong>Late by:</strong> {details.get('late_minutes', 0)} minutes</p>
                    <p><strong>Deduction:</strong> {details.get('deduction', 0)} AED</p>
                </div>
            """
        },
        'absence': {
            'subject': f'Absence Notice - {details.get("date", "")}',
            'color': '#c53030',
            'title': 'Absence Notice',
            'body': f"""
                <p>Dear <strong>{employee_name}</strong>,</p>
                <p>This is to inform you that an <strong>absence</strong> has been recorded:</p>
                <div style="background: #fff5f5; border-right: 4px solid #c53030; padding: 12px; margin: 10px 0;">
                    <p><strong>Date:</strong> {details.get('date', 'N/A')}</p>
                    <p><strong>Type:</strong> {details.get('absence_type', 'Full Day')}</p>
                    <p><strong>Deduction:</strong> {details.get('deduction', 0)} AED</p>
                    <p><strong>Reason:</strong> {details.get('reason', 'N/A')}</p>
                </div>
            """
        },
        'advance_request': {
            'subject': f'Advance Request - {employee_name}',
            'color': '#2b6cb0',
            'title': 'New Advance Request',
            'body': f"""
                <p>A new advance request has been submitted:</p>
                <div style="background: #ebf8ff; border-right: 4px solid #2b6cb0; padding: 12px; margin: 10px 0;">
                    <p><strong>Employee:</strong> {employee_name}</p>
                    <p><strong>Amount:</strong> {details.get('amount', 0)} AED</p>
                    <p><strong>Type:</strong> {details.get('type', 'Advance')}</p>
                    <p><strong>Reason:</strong> {details.get('reason', 'N/A')}</p>
                </div>
            """
        }
    }
    
    template = templates.get(notification_type, templates['lateness'])
    
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: {template['color']}; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
            <h2 style="margin: 0;">Al Tanseeq Tax Consultancy</h2>
            <p style="margin: 5px 0 0; opacity: 0.9;">{template['title']}</p>
        </div>
        <div style="padding: 25px; background: #f7fafc; border: 1px solid #e2e8f0;">
            {template['body']}
            <p style="color: #718096; font-size: 12px; margin-top: 20px;">This is an automated notification from TANSEEQ HR System.</p>
        </div>
        <div style="background: #2d3748; color: #a0aec0; padding: 15px; text-align: center; font-size: 11px; border-radius: 0 0 8px 8px;">
            <p style="margin: 0;">TANSEEQ HR System - Automated Notification</p>
        </div>
    </div>
    """
    
    return send_email(to_email, template['subject'], html_body)
