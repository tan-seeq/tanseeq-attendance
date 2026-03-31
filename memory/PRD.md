# TANSEEQ HR Management System - PRD

## Original Problem Statement
Full-stack HR management application for TANSEEQ Tax Consultancy. Arabic-first (RTL) application managing attendance, payroll, advances/loans, notifications, leaves, field exits, marketing visits, and work reports.

## Tech Stack
- **Backend**: FastAPI + MongoDB (Motor) + Pydantic + ReportLab (PDF) + arabic-reshaper + python-bidi + APScheduler
- **Frontend**: React.js + Axios + TailwindCSS + Heroicons
- **Email**: GoDaddy SMTP (smtpout.secureserver.net:587) via smtplib
- **Fonts**: Amiri Arabic (RTL PDF support)
- **Scheduler**: APScheduler (AsyncIOScheduler + CronTrigger)
- **Language**: Arabic (RTL) primary

## User Roles
- **Super Admin**: Full system access, config, health monitoring, auto-reports
- **Admin**: Management access
- **User (Employee)**: Self-service attendance, leave requests

## Key Credentials
- Super Admin: admin@tanseeq.com / ADMIN
- Employee: hatem@tan-seeq.co / hatem123
- SMTP: Taxagent@tan-seeq.co via smtpout.secureserver.net:587

## Architecture
```
/app/
├── backend/
│   ├── server.py              # Core backend (~15280 lines)
│   ├── pdf_generator.py       # Arabic PDF salary slip generation
│   ├── email_service.py       # Arabic SMTP email service with templates
│   ├── attendance_engine.py   # Attendance logic
│   ├── fonts/                 # Amiri Arabic font files
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.js
│   │   ├── contexts/AuthContext.js, LanguageContext.js
│   │   └── components/
│   │       ├── Admin/
│   │       │   ├── SalarySlips.js     # 4 tabs: slips, auto-report, email settings, logs
│   │       │   ├── SystemHealth.js    # Service health monitoring
│   │       │   ├── AdminConfig.js
│   │       │   └── LiveMonitoring.js
│   │       ├── Dashboard/HRDashboard.js
│   │       └── ...
│   └── .env
```

## Completed Work

### Session 1-2 - Core Features + Refactoring
- All HR modules (attendance, payroll, advances, notifications, etc.)
- Admin Config, Live Monitoring, PDF Salary Slips, Email Integration

### Session 3 - Production Stability (2026-03-31)
- HRDashboard crash fix, date overflow bug, backend defensive coding

### Session 4 - New Features (2026-03-31)
- [x] Auto email notifications for lateness/absence
- [x] Arabic PDF support (Amiri font + RTL)
- [x] System Health page (/system-health)

### Session 5 - Auto Monthly Report (2026-03-31)
- [x] **Monthly report auto-send**: APScheduler cron job (day 28, 8:00 AM) sends all employees email + PDF
- [x] **Manual trigger**: POST /api/payroll/send-monthly-reports runs in background (asyncio.create_task)
- [x] **Auto-report config**: Enable/disable + day selector (1-28) saved to DB
- [x] **Report history**: Full run history with sent/failed/total per run
- [x] **UI**: New "التقرير التلقائي" tab in SalarySlips page with toggle, day picker, send now, history

## Key API Endpoints

### Auto Monthly Reports
- `POST /api/payroll/send-monthly-reports` - Manual trigger (background task)
- `GET/PUT /api/payroll/auto-report-config` - Auto-scheduler config
- `GET /api/payroll/auto-report-history` - Run history

### System Health
- `GET /api/system/health-check` - Comprehensive service health

### PDF & Email
- `GET /api/salary-slip/{employee_id}/{cycle_month}` - Generate Arabic PDF
- `POST /api/email/test` - Test SMTP
- `POST /api/email/send-salary-slip` - Individual salary slip

## Pending Tasks

### P2 (Backlog)
- [ ] Further refactoring of App.js (still ~6380 lines)
- [ ] Dashboard and Employees component extraction
