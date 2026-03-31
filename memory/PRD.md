# TANSEEQ HR Management System - PRD

## Original Problem Statement
Full-stack HR management application for TANSEEQ Tax Consultancy. Arabic-first (RTL) application managing attendance, payroll, advances/loans, notifications, leaves, field exits, marketing visits, and work reports.

## Tech Stack
- **Backend**: FastAPI + MongoDB (Motor) + Pydantic + ReportLab (PDF)
- **Frontend**: React.js + Axios + TailwindCSS
- **Data**: pandas + openpyxl for Excel exports
- **Email**: GoDaddy SMTP (smtpout.secureserver.net:587)
- **Language**: Arabic (RTL) primary

## User Roles
- **Super Admin**: Full system access, edit/delete permissions, config management
- **Admin**: Management access
- **User (Employee)**: Self-service attendance, leave requests

## Key Credentials
- Super Admin: admin@tanseeq.com / ADMIN
- Employee: hatem@tan-seeq.co / hatem123
- DB Name: tanseeq_hr
- SMTP: Taxagent@tan-seeq.co via smtpout.secureserver.net:587

## Architecture
```
/app/
├── backend/
│   ├── server.py              # Core backend (~14900 lines)
│   ├── pdf_generator.py       # PDF salary slip generation
│   ├── email_service.py       # SMTP email service
│   ├── attendance_engine.py   # Attendance logic
│   ├── advances_model.py      # Advances data models
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.js             # Main app (~6360 lines)
│   │   ├── config.js          # API constants
│   │   ├── contexts/
│   │   │   ├── AuthContext.js
│   │   │   └── LanguageContext.js
│   │   └── components/
│   │       ├── Attendance/AttendanceManagement.js
│   │       ├── Admin/
│   │       │   ├── AdminConfig.js
│   │       │   ├── LiveMonitoring.js
│   │       │   └── SalarySlips.js
│   │       ├── Dashboard/HRDashboard.js
│   │       ├── AttendanceDeductions/
│   │       │   ├── MyAttendanceDeductions.js
│   │       │   └── MonthlyDeductionsCalculator.js
│   │       └── ...
│   └── .env
```

## Completed Work (All Sessions)

### Core Features (Session 1)
- Login/Auth, Dashboard, Attendance, Employee CRUD
- Payroll, Advances & Loans, Notifications
- Manual attendance/absence, Custom reports
- Leave/Field exit/Marketing visits, Work reports

### Session 2 Fixes & Features
- [x] Deployment fix (MongoDB indexes, /health endpoint)
- [x] Custom Report modal, Manual absence bug
- [x] Login resilience, Notification UX
- [x] AttendanceManagement refactoring (1254 lines extracted from App.js)
- [x] AuthContext & LanguageContext extracted
- [x] Admin Config (/admin/config)
- [x] Live Monitoring (/admin/live)
- [x] PDF Salary Slips
- [x] Email Integration (GoDaddy SMTP)

### Session 3 - Production Stability Fixes (2026-03-31)
- [x] **HRDashboard crash fix** - Changed Promise.all to Promise.allSettled with DEFAULT_KPIS fallback
- [x] **Date overflow bug** - Fixed cycle date calculation for months without day 29 (Feb)
- [x] **Backend defensive coding** - All employee loops use .get() instead of dict['key'] access
- [x] **User model resilience** - get_current_user has fallback User construction for prod DB mismatches
- [x] **Payroll cycles _id fix** - pop("_id") instead of str(_id) to prevent serialization issues
- [x] **Email test endpoint** - Wrapped in try/except to prevent 500 crashes
- [x] **Clients endpoint** - Returns [] on error instead of raising 500
- [x] **SalarySlips page** - Promise.allSettled prevents cascade failure
- [x] **Ledger endpoint** - Fixed dict-typed current_user and added _id removal

## Pending Tasks

### P2 (Backlog)
- [ ] Further refactoring of App.js (still ~6360 lines)
- [ ] Auto-trigger email notifications on lateness/absence events
- [ ] Arabic content in PDF salary slips

## Key API Endpoints
### PDF & Email
- `GET /api/salary-slip/{employee_id}/{cycle_month}` - Generate PDF
- `POST /api/email/test` - Test SMTP connection
- `POST /api/email/send-salary-slip` - Send individual salary slip
- `GET/PUT /api/email/preferences` - Email notification preferences

### Deductions
- `POST /api/deductions/calculate-monthly?month=YYYY-MM` - Monthly deductions
- `POST /api/deductions/calculate?mode=custom&from_date=&to_date=` - Custom period

### Admin Config
- `GET/PUT /api/admin/config/system` - System configuration
- `GET/POST/DELETE /api/admin/config/exceptions` - Attendance exceptions

### Monitoring
- `GET /api/live/metrics` - Real-time metrics
- `GET /api/live/logs` - Server logs
- `GET /api/healthz` - Kubernetes health probe
