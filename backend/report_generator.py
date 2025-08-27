"""
Advanced PDF Report Generation for TANSEEQ Work Reports
Supports Arabic RTL text and professional layouts
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfutils
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from io import BytesIO
import pandas as pd
from sqlalchemy.orm import Session
from work_reports_db import WorkLog, Client, ActivityType, get_work_reports_db

class WorkReportsPDFGenerator:
    """Generate professional PDF reports for work logs and analytics"""
    
    def __init__(self):
        self.setup_fonts()
        
    def setup_fonts(self):
        """Setup Arabic and English fonts for PDF generation"""
        try:
            # Register Arabic font (fallback to default if not available)
            # In production, add actual Arabic font files
            pass
        except Exception as e:
            print(f"Font setup warning: {e}")
    
    def generate_daily_report(
        self, 
        user_id: str,
        date: datetime,
        db: Session
    ) -> BytesIO:
        """Generate daily work report for a specific user and date"""
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Report header
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        title = Paragraph(f"Daily Work Report - تقرير العمل اليومي<br/>{date.strftime('%Y-%m-%d')}", title_style)
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Get work logs for the date
        work_logs = db.query(WorkLog).filter(
            WorkLog.user_id == user_id,
            WorkLog.date >= date.replace(hour=0, minute=0, second=0),
            WorkLog.date < date.replace(hour=0, minute=0, second=0) + timedelta(days=1)
        ).all()
        
        if not work_logs:
            no_data = Paragraph("No work logs found for this date - لا توجد سجلات عمل لهذا التاريخ", styles['Normal'])
            story.append(no_data)
        else:
            # Summary statistics
            total_minutes = sum([log.duration_minutes or 0 for log in work_logs])
            total_hours = total_minutes / 60
            billable_logs = [log for log in work_logs if log.is_billable]
            billable_minutes = sum([log.duration_minutes or 0 for log in billable_logs])
            billable_hours = billable_minutes / 60
            total_revenue = sum([log.total_amount or 0 for log in billable_logs])
            
            # Summary table
            summary_data = [
                ['Metric - المقياس', 'Value - القيمة'],
                ['Total Hours - إجمالي الساعات', f'{total_hours:.1f}h'],
                ['Billable Hours - ساعات قابلة للفوترة', f'{billable_hours:.1f}h'],
                ['Total Revenue - إجمالي الإيرادات', f'AED {total_revenue:.2f}'],
                ['Number of Tasks - عدد المهام', str(len(work_logs))],
            ]
            
            summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 20))
            
            # Detailed work logs
            detail_title = Paragraph("Detailed Work Log - سجل العمل التفصيلي", styles['Heading2'])
            story.append(detail_title)
            story.append(Spacer(1, 12))
            
            # Work logs table
            log_data = [['Time - الوقت', 'Client - العميل', 'Activity - النشاط', 'Duration - المدة', 'Amount - المبلغ']]
            
            for log in work_logs:
                start_time = log.start_time.strftime('%H:%M') if log.start_time else '-'
                end_time = log.end_time.strftime('%H:%M') if log.end_time else '-'
                time_str = f"{start_time} - {end_time}"
                
                client_name = log.client.company_name if log.client else 'Unknown'
                activity_name = log.activity_type.name if log.activity_type else 'Unknown'
                duration_str = f"{log.duration_minutes or 0}min"
                amount_str = f"AED {log.total_amount or 0:.2f}" if log.is_billable else 'Non-billable'
                
                log_data.append([
                    time_str,
                    client_name[:30] + '...' if len(client_name) > 30 else client_name,
                    activity_name[:25] + '...' if len(activity_name) > 25 else activity_name,
                    duration_str,
                    amount_str
                ])
            
            logs_table = Table(log_data, colWidths=[1.2*inch, 2*inch, 2*inch, 1*inch, 1.3*inch])
            logs_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.navy),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightgrey, colors.white])
            ]))
            
            story.append(logs_table)
        
        # Footer
        story.append(Spacer(1, 30))
        footer = Paragraph(
            f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')} - تم الإنتاج في<br/>"
            "TANSEEQ Work Reports System - نظام تقارير العمل تنسيق",
            styles['Normal']
        )
        story.append(footer)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def generate_monthly_summary(
        self,
        user_id: str,
        year: int,
        month: int,
        db: Session
    ) -> BytesIO:
        """Generate comprehensive monthly summary report"""
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Date range
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(seconds=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(seconds=1)
        
        # Report header
        title = Paragraph(
            f"Monthly Work Summary - ملخص العمل الشهري<br/>{start_date.strftime('%B %Y')}",
            styles['Title']
        )
        story.append(title)
        story.append(Spacer(1, 20))
        
        # Get all work logs for the month
        work_logs = db.query(WorkLog).filter(
            WorkLog.user_id == user_id,
            WorkLog.date >= start_date,
            WorkLog.date <= end_date
        ).all()
        
        if not work_logs:
            story.append(Paragraph("No work logs found for this month", styles['Normal']))
        else:
            # Generate analytics chart
            chart_buffer = self.generate_analytics_chart(work_logs, start_date, end_date)
            if chart_buffer:
                chart_img = Image(chart_buffer, width=6*inch, height=4*inch)
                story.append(chart_img)
                story.append(Spacer(1, 20))
            
            # Client breakdown
            client_summary = {}
            for log in work_logs:
                client_name = log.client.company_name if log.client else 'Unknown'
                if client_name not in client_summary:
                    client_summary[client_name] = {'hours': 0, 'revenue': 0, 'tasks': 0}
                
                client_summary[client_name]['hours'] += (log.duration_minutes or 0) / 60
                client_summary[client_name]['revenue'] += log.total_amount or 0
                client_summary[client_name]['tasks'] += 1
            
            # Client summary table
            client_data = [['Client - العميل', 'Hours - الساعات', 'Revenue - الإيرادات', 'Tasks - المهام']]
            for client, stats in sorted(client_summary.items(), key=lambda x: x[1]['revenue'], reverse=True):
                client_data.append([
                    client[:40] + '...' if len(client) > 40 else client,
                    f"{stats['hours']:.1f}h",
                    f"AED {stats['revenue']:.2f}",
                    str(stats['tasks'])
                ])
            
            client_table = Table(client_data, colWidths=[3*inch, 1*inch, 1.5*inch, 1*inch])
            client_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(Paragraph("Client Summary - ملخص العملاء", styles['Heading2']))
            story.append(client_table)
        
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def generate_analytics_chart(
        self,
        work_logs: List[WorkLog],
        start_date: datetime,
        end_date: datetime
    ) -> Optional[BytesIO]:
        """Generate analytics charts for work logs"""
        try:
            # Create DataFrame for analysis
            data = []
            for log in work_logs:
                data.append({
                    'date': log.date.date(),
                    'hours': (log.duration_minutes or 0) / 60,
                    'revenue': log.total_amount or 0,
                    'client': log.client.company_name if log.client else 'Unknown'
                })
            
            if not data:
                return None
                
            df = pd.DataFrame(data)
            
            # Create figure with subplots
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))
            fig.suptitle('Work Analytics - تحليل العمل', fontsize=16)
            
            # Daily hours trend
            daily_hours = df.groupby('date')['hours'].sum()
            ax1.plot(daily_hours.index, daily_hours.values, marker='o', linewidth=2)
            ax1.set_title('Daily Hours Trend')
            ax1.set_ylabel('Hours')
            ax1.grid(True, alpha=0.3)
            
            # Daily revenue trend  
            daily_revenue = df.groupby('date')['revenue'].sum()
            ax2.plot(daily_revenue.index, daily_revenue.values, marker='s', color='green', linewidth=2)
            ax2.set_title('Daily Revenue Trend')
            ax2.set_ylabel('AED')
            ax2.grid(True, alpha=0.3)
            
            # Top clients by hours
            client_hours = df.groupby('client')['hours'].sum().head(5)
            ax3.bar(range(len(client_hours)), client_hours.values, color='orange')
            ax3.set_title('Top Clients by Hours')
            ax3.set_ylabel('Hours')
            ax3.set_xticks(range(len(client_hours)))
            ax3.set_xticklabels([name[:15] for name in client_hours.index], rotation=45)
            
            # Revenue distribution
            client_revenue = df.groupby('client')['revenue'].sum().head(5)
            ax4.pie(client_revenue.values, labels=[name[:15] for name in client_revenue.index], autopct='%1.1f%%')
            ax4.set_title('Revenue Distribution')
            
            plt.tight_layout()
            
            # Save to buffer
            chart_buffer = BytesIO()
            plt.savefig(chart_buffer, format='png', dpi=300, bbox_inches='tight')
            chart_buffer.seek(0)
            plt.close(fig)
            
            return chart_buffer
            
        except Exception as e:
            print(f"Chart generation error: {e}")
            return None
    
    def generate_client_report(
        self,
        client_id: str,
        start_date: datetime,
        end_date: datetime,
        db: Session
    ) -> BytesIO:
        """Generate detailed client work report"""
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Get client info
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            story.append(Paragraph("Client not found", styles['Normal']))
            doc.build(story)
            buffer.seek(0)
            return buffer
        
        # Report header
        title = Paragraph(
            f"Client Work Report - تقرير عمل العميل<br/>{client.company_name}<br/>"
            f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            styles['Title']
        )
        story.append(title)
        story.append(Spacer(1, 20))
        
        # Client information
        client_info = [
            ['Field - الحقل', 'Value - القيمة'],
            ['Company Name - اسم الشركة', client.company_name],
            ['Client Code - رمز العميل', client.client_code or '-'],
            ['Contact Person - الشخص المسؤول', client.contact_person or '-'],
            ['Phone - الهاتف', client.phone or '-'],
            ['Email - البريد الإلكتروني', client.email or '-'],
        ]
        
        info_table = Table(client_info, colWidths=[2.5*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 20))
        
        # Get work logs for this client
        work_logs = db.query(WorkLog).filter(
            WorkLog.client_id == client_id,
            WorkLog.date >= start_date,
            WorkLog.date <= end_date
        ).order_by(WorkLog.date.desc()).all()
        
        if work_logs:
            # Summary stats
            total_hours = sum([(log.duration_minutes or 0) / 60 for log in work_logs])
            total_revenue = sum([log.total_amount or 0 for log in work_logs if log.is_billable])
            avg_hourly_rate = total_revenue / total_hours if total_hours > 0 else 0
            
            summary_data = [
                ['Metric - المقياس', 'Value - القيمة'],
                ['Total Hours - إجمالي الساعات', f'{total_hours:.1f}h'],
                ['Total Revenue - إجمالي الإيرادات', f'AED {total_revenue:.2f}'],
                ['Average Rate - المعدل المتوسط', f'AED {avg_hourly_rate:.2f}/hour'],
                ['Number of Sessions - عدد الجلسات', str(len(work_logs))],
            ]
            
            summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(Paragraph("Work Summary - ملخص العمل", styles['Heading2']))
            story.append(summary_table)
            story.append(Spacer(1, 20))
            
            # Detailed work logs
            log_data = [['Date - التاريخ', 'Activity - النشاط', 'Duration - المدة', 'Description - الوصف', 'Amount - المبلغ']]
            
            for log in work_logs:
                log_data.append([
                    log.date.strftime('%Y-%m-%d'),
                    log.activity_type.name if log.activity_type else 'Unknown',
                    f"{log.duration_minutes or 0}min",
                    log.description[:50] + '...' if len(log.description) > 50 else log.description,
                    f"AED {log.total_amount or 0:.2f}" if log.is_billable else 'N/A'
                ])
            
            detail_table = Table(log_data, colWidths=[1*inch, 1.5*inch, 0.8*inch, 2.5*inch, 1*inch])
            detail_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.navy),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightblue, colors.white])
            ]))
            
            story.append(Paragraph("Detailed Work Log - سجل العمل التفصيلي", styles['Heading2']))
            story.append(detail_table)
        else:
            story.append(Paragraph("No work logs found for this period", styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        return buffer

# Global report generator instance
report_generator = WorkReportsPDFGenerator()