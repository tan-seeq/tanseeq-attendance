"""
Email Service - TANSEEQ HR System
Handles SMTP email sending via GoDaddy with Arabic templates
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import logging

logger = logging.getLogger("email_service")

SMTP_HOST = os.environ.get('SMTP_HOST', 'smtpout.secureserver.net')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_EMAIL = os.environ.get('SMTP_EMAIL', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
SMTP_FROM_NAME = os.environ.get('SMTP_FROM_NAME', 'Al Tanseeq HR System')


def send_email(to_email: str, subject: str, html_body: str, attachments: list = None) -> dict:
    """Send email via GoDaddy SMTP"""
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

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)

        logger.info(f"Email sent successfully to {to_email}")
        return {"success": True, "message": f"Email sent to {to_email}"}
    except Exception as e:
        logger.error(f"Email failed to {to_email}: {e}")
        return {"success": False, "error": str(e)}


def send_salary_slip_email(to_email: str, employee_name: str, cycle_month: str, pdf_data: bytes) -> dict:
    """Send salary slip PDF via email"""
    subject = f"كشف الراتب - {cycle_month} | Al Tanseeq"
    html_body = f"""
    <div dir="rtl" style="font-family: 'Segoe UI', Tahoma, Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #2b6cb0, #1a365d); color: white; padding: 25px; text-align: center; border-radius: 12px 12px 0 0;">
            <h2 style="margin: 0;">التنسيق للاستشارات الضريبية</h2>
            <p style="margin: 5px 0 0; opacity: 0.9;">كشف الراتب الشهري</p>
        </div>
        <div style="padding: 25px; background: #f7fafc; border: 1px solid #e2e8f0;">
            <p>الموظف/ة العزيز/ة <strong>{employee_name}</strong>،</p>
            <p>مرفق كشف الراتب الخاص بك لفترة <strong>{cycle_month}</strong>.</p>
            <p>يرجى الاطلاع على المرفق للتفاصيل الكاملة.</p>
            <p style="color: #718096; font-size: 12px; margin-top: 20px;">هذا بريد آلي من نظام الموارد البشرية - التنسيق</p>
        </div>
        <div style="background: #2d3748; color: #a0aec0; padding: 15px; text-align: center; font-size: 11px; border-radius: 0 0 12px 12px;">
            <p style="margin: 0;">نظام الموارد البشرية - التنسيق للاستشارات الضريبية</p>
        </div>
    </div>
    """
    return send_email(to_email, subject, html_body, [{"filename": f"salary_slip_{cycle_month}.pdf", "data": pdf_data}])


def send_notification_email(to_email: str, employee_name: str, notification_type: str, details: dict) -> dict:
    """Send notification email for lateness/absence/advance with Arabic templates"""

    templates = {
        'lateness': {
            'subject': f'تنبيه تأخير - {details.get("date", "")} | التنسيق',
            'color': '#dd6b20',
            'title': 'تنبيه تأخير',
            'body': f"""
                <p>الموظف/ة العزيز/ة <strong>{employee_name}</strong>،</p>
                <p>نود إبلاغكم بأنه تم تسجيل <strong>تأخير</strong> في الحضور:</p>
                <div style="background: #fffaf0; border-right: 4px solid #dd6b20; padding: 12px; margin: 10px 0; border-radius: 4px;">
                    <p><strong>التاريخ:</strong> {details.get('date', '-')}</p>
                    <p><strong>الوقت المتوقع:</strong> {details.get('expected_time', '09:15')}</p>
                    <p><strong>وقت الحضور:</strong> {details.get('actual_time', '-')}</p>
                    <p><strong>مدة التأخير:</strong> {details.get('late_minutes', 0)} دقيقة</p>
                </div>
                <p style="color: #718096; font-size: 13px;">يرجى الالتزام بمواعيد العمل الرسمية.</p>
            """
        },
        'absence': {
            'subject': f'تنبيه غياب - {details.get("date", "")} | التنسيق',
            'color': '#c53030',
            'title': 'تنبيه غياب',
            'body': f"""
                <p>الموظف/ة العزيز/ة <strong>{employee_name}</strong>،</p>
                <p>نود إبلاغكم بأنه تم تسجيل <strong>غياب</strong>:</p>
                <div style="background: #fff5f5; border-right: 4px solid #c53030; padding: 12px; margin: 10px 0; border-radius: 4px;">
                    <p><strong>التاريخ:</strong> {details.get('date', '-')}</p>
                    <p><strong>نوع الغياب:</strong> {details.get('absence_type', 'يوم كامل')}</p>
                    <p><strong>السبب:</strong> {details.get('reason', 'غير محدد')}</p>
                </div>
            """
        },
        'lateness_admin': {
            'subject': f'تنبيه: تأخير الموظف {employee_name} - {details.get("date", "")}',
            'color': '#dd6b20',
            'title': 'تنبيه تأخير موظف',
            'body': f"""
                <p>تم تسجيل تأخير للموظف <strong>{employee_name}</strong>:</p>
                <div style="background: #fffaf0; border-right: 4px solid #dd6b20; padding: 12px; margin: 10px 0; border-radius: 4px;">
                    <p><strong>الموظف:</strong> {employee_name}</p>
                    <p><strong>التاريخ:</strong> {details.get('date', '-')}</p>
                    <p><strong>وقت الحضور:</strong> {details.get('actual_time', '-')}</p>
                    <p><strong>مدة التأخير:</strong> {details.get('late_minutes', 0)} دقيقة</p>
                </div>
            """
        },
        'absence_admin': {
            'subject': f'تنبيه: غياب الموظف {employee_name} - {details.get("date", "")}',
            'color': '#c53030',
            'title': 'تنبيه غياب موظف',
            'body': f"""
                <p>تم تسجيل غياب للموظف <strong>{employee_name}</strong>:</p>
                <div style="background: #fff5f5; border-right: 4px solid #c53030; padding: 12px; margin: 10px 0; border-radius: 4px;">
                    <p><strong>الموظف:</strong> {employee_name}</p>
                    <p><strong>التاريخ:</strong> {details.get('date', '-')}</p>
                    <p><strong>نوع الغياب:</strong> {details.get('absence_type', 'يوم كامل')}</p>
                    <p><strong>عدد الأيام:</strong> {details.get('days_count', 1)}</p>
                </div>
            """
        },
        'advance_request': {
            'subject': f'طلب سلفة جديد - {employee_name} | التنسيق',
            'color': '#2b6cb0',
            'title': 'طلب سلفة جديد',
            'body': f"""
                <p>تم تقديم طلب سلفة جديد:</p>
                <div style="background: #ebf8ff; border-right: 4px solid #2b6cb0; padding: 12px; margin: 10px 0; border-radius: 4px;">
                    <p><strong>الموظف:</strong> {employee_name}</p>
                    <p><strong>المبلغ:</strong> {details.get('amount', 0)} درهم</p>
                    <p><strong>النوع:</strong> {details.get('type', 'سلفة')}</p>
                    <p><strong>السبب:</strong> {details.get('reason', 'غير محدد')}</p>
                </div>
            """
        }
    }

    template = templates.get(notification_type, templates['lateness'])

    html_body = f"""
    <div dir="rtl" style="font-family: 'Segoe UI', Tahoma, Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, {template['color']}, #2d3748); color: white; padding: 25px; text-align: center; border-radius: 12px 12px 0 0;">
            <h2 style="margin: 0;">التنسيق للاستشارات الضريبية</h2>
            <p style="margin: 5px 0 0; opacity: 0.9;">{template['title']}</p>
        </div>
        <div style="padding: 25px; background: #f7fafc; border: 1px solid #e2e8f0;">
            {template['body']}
            <p style="color: #718096; font-size: 12px; margin-top: 20px;">هذا بريد آلي من نظام الموارد البشرية - التنسيق</p>
        </div>
        <div style="background: #2d3748; color: #a0aec0; padding: 15px; text-align: center; font-size: 11px; border-radius: 0 0 12px 12px;">
            <p style="margin: 0;">نظام الموارد البشرية - التنسيق للاستشارات الضريبية</p>
        </div>
    </div>
    """

    return send_email(to_email, template['subject'], html_body)
