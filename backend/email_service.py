"""
Email Service - TANSEEQ HR System
Handles SMTP email sending with multi-server fallback
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import logging

logger = logging.getLogger("email_service")

# SMTP Configuration with fallback servers
SMTP_SERVERS = [
    'smtp.office365.com',
    'smtpout.secureserver.net',
]
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_EMAIL = os.environ.get('SMTP_EMAIL', 'Taxagent@tan-seeq.co').strip()
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
SMTP_FROM_NAME = os.environ.get('SMTP_FROM_NAME', 'Al Tanseeq HR System')

# Resolved host (set after first successful connection)
SMTP_HOST = os.environ.get('SMTP_SERVER', os.environ.get('SMTP_HOST', 'smtp.office365.com'))
if 'secureserver' in SMTP_HOST:
    SMTP_HOST = 'smtp.office365.com'


def _try_send_via_server(smtp_host, to_email, msg):
    """Try sending via a specific SMTP server"""
    with smtplib.SMTP(smtp_host, SMTP_PORT, timeout=20) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(msg)
    return smtp_host


def send_email(to_email: str, subject: str, html_body: str, attachments: list = None) -> dict:
    """Send email via SMTP with automatic server fallback"""
    try:
        if not SMTP_EMAIL or not SMTP_PASSWORD:
            return {"success": False, "error": "SMTP credentials not configured"}

        msg = MIMEMultipart()
        msg['From'] = f"{SMTP_FROM_NAME} <{SMTP_EMAIL}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        if attachments:
            for att in attachments:
                part = MIMEApplication(att['data'], Name=att['filename'])
                part['Content-Disposition'] = f'attachment; filename="{att["filename"]}"'
                msg.attach(part)

        # Try primary host first, then fallback servers
        servers_to_try = [SMTP_HOST] + [s for s in SMTP_SERVERS if s != SMTP_HOST]
        last_error = None

        for server_host in servers_to_try:
            try:
                used_host = _try_send_via_server(server_host, to_email, msg)
                logger.info(f"Email sent to {to_email} via {used_host}")
                return {"success": True, "message": f"Email sent to {to_email}", "server": used_host}
            except smtplib.SMTPAuthenticationError as e:
                last_error = e
                logger.warning(f"Auth failed on {server_host}, trying next...")
                continue
            except smtplib.SMTPConnectError as e:
                last_error = e
                logger.warning(f"Connect failed on {server_host}, trying next...")
                continue
            except Exception as e:
                last_error = e
                logger.warning(f"Error on {server_host}: {e}, trying next...")
                continue

        # All servers failed
        if isinstance(last_error, smtplib.SMTPAuthenticationError):
            return {"success": False, "error": "SMTP authentication failed. Please check username and password"}
        elif isinstance(last_error, smtplib.SMTPConnectError):
            return {"success": False, "error": "Failed to connect to mail server. Please check server address and port"}
        else:
            return {"success": False, "error": "Failed to send email via all available servers"}

    except Exception as e:
        logger.error(f"Email failed to {to_email}: {e}")
        return {"success": False, "error": "An error occurred while sending the email"}


def send_salary_slip_email(to_email: str, employee_name: str, cycle_month: str, pdf_data: bytes) -> dict:
    """Send salary slip PDF via email"""
    subject = f"Salary Slip - {cycle_month} | TANSEEQ Tax Consultancy"
    html_body = f"""
    <div style="font-family: 'Segoe UI', Tahoma, Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #2b6cb0, #1a365d); color: white; padding: 25px; text-align: center; border-radius: 12px 12px 0 0;">
            <h2 style="margin: 0;">TANSEEQ Tax Consultancy</h2>
            <p style="margin: 5px 0 0; opacity: 0.9;">Monthly Salary Slip</p>
        </div>
        <div style="padding: 25px; background: #f7fafc; border: 1px solid #e2e8f0;">
            <p>Dear <strong>{employee_name}</strong>,</p>
            <p>Please find attached your salary slip for the period <strong>{cycle_month}</strong>.</p>
            <p>Kindly review the attachment for full details.</p>
            <p style="color: #718096; font-size: 12px; margin-top: 20px;">This is an automated email from the HR System - TANSEEQ</p>
        </div>
        <div style="background: #2d3748; color: #a0aec0; padding: 15px; text-align: center; font-size: 11px; border-radius: 0 0 12px 12px;">
            <p style="margin: 0;">HR System - TANSEEQ Tax Consultancy</p>
        </div>
    </div>
    """
    return send_email(to_email, subject, html_body, [{"filename": f"salary_slip_{cycle_month}.pdf", "data": pdf_data}])


def send_notification_email(to_email: str, employee_name: str, notification_type: str, details: dict) -> dict:
    """Send notification email for lateness/absence"""

    templates = {
        'lateness': {
            'subject': f'Lateness Alert - {details.get("date", "")} | TANSEEQ',
            'color': '#dd6b20',
            'title': 'Lateness Alert',
            'body': f"""
                <p>Dear <strong>{employee_name}</strong>,</p>
                <p>Please be informed that a <strong>late arrival</strong> has been recorded:</p>
                <div style="background: #fffaf0; border-left: 4px solid #dd6b20; padding: 12px; margin: 10px 0; border-radius: 4px;">
                    <p><strong>Date:</strong> {details.get('date', '-')}</p>
                    <p><strong>Expected Time:</strong> {details.get('expected_time', '09:15')}</p>
                    <p><strong>Actual Arrival:</strong> {details.get('actual_time', '-')}</p>
                    <p><strong>Late Duration:</strong> {details.get('late_minutes', 0)} minutes</p>
                </div>
                <p style="color: #718096; font-size: 13px;">Please adhere to the official working hours.</p>
            """
        },
        'absence': {
            'subject': f'Absence Alert - {details.get("date", "")} | TANSEEQ',
            'color': '#c53030',
            'title': 'Absence Alert',
            'body': f"""
                <p>Dear <strong>{employee_name}</strong>,</p>
                <p>Please be informed that an <strong>absence</strong> has been recorded:</p>
                <div style="background: #fff5f5; border-left: 4px solid #c53030; padding: 12px; margin: 10px 0; border-radius: 4px;">
                    <p><strong>Date:</strong> {details.get('date', '-')}</p>
                    <p><strong>Absence Type:</strong> {details.get('absence_type', 'Full Day')}</p>
                    <p><strong>Reason:</strong> {details.get('reason', 'Not specified')}</p>
                </div>
            """
        },
        'lateness_admin': {
            'subject': f'Alert: Employee {employee_name} Late - {details.get("date", "")}',
            'color': '#dd6b20',
            'title': 'Employee Lateness Alert',
            'body': f"""
                <p>A late arrival has been recorded for employee <strong>{employee_name}</strong>:</p>
                <div style="background: #fffaf0; border-left: 4px solid #dd6b20; padding: 12px; margin: 10px 0; border-radius: 4px;">
                    <p><strong>Employee:</strong> {employee_name}</p>
                    <p><strong>Date:</strong> {details.get('date', '-')}</p>
                    <p><strong>Arrival Time:</strong> {details.get('actual_time', '-')}</p>
                    <p><strong>Late Duration:</strong> {details.get('late_minutes', 0)} minutes</p>
                </div>
            """
        },
        'absence_admin': {
            'subject': f'Alert: Employee {employee_name} Absent - {details.get("date", "")}',
            'color': '#c53030',
            'title': 'Employee Absence Alert',
            'body': f"""
                <p>An absence has been recorded for employee <strong>{employee_name}</strong>:</p>
                <div style="background: #fff5f5; border-left: 4px solid #c53030; padding: 12px; margin: 10px 0; border-radius: 4px;">
                    <p><strong>Employee:</strong> {employee_name}</p>
                    <p><strong>Date:</strong> {details.get('date', '-')}</p>
                    <p><strong>Absence Type:</strong> {details.get('absence_type', 'Full Day')}</p>
                    <p><strong>Days Count:</strong> {details.get('days_count', 1)}</p>
                </div>
            """
        },
    }

    template = templates.get(notification_type, templates.get('lateness', {'subject': 'Alert', 'color': '#2b6cb0', 'title': 'Alert', 'body': f'<p>{employee_name}</p>'}))

    html_body = f"""
    <div style="font-family: 'Segoe UI', Tahoma, Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, {template['color']}, #2d3748); color: white; padding: 25px; text-align: center; border-radius: 12px 12px 0 0;">
            <h2 style="margin: 0;">TANSEEQ Tax Consultancy</h2>
            <p style="margin: 5px 0 0; opacity: 0.9;">{template['title']}</p>
        </div>
        <div style="padding: 25px; background: #f7fafc; border: 1px solid #e2e8f0;">
            {template['body']}
            <p style="color: #718096; font-size: 12px; margin-top: 20px;">This is an automated email from the HR System - TANSEEQ</p>
        </div>
        <div style="background: #2d3748; color: #a0aec0; padding: 15px; text-align: center; font-size: 11px; border-radius: 0 0 12px 12px;">
            <p style="margin: 0;">HR System - TANSEEQ Tax Consultancy</p>
        </div>
    </div>
    """

    return send_email(to_email, template['subject'], html_body)
