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
│   ├── server.py              # Core backend
│   ├── pdf_generator.py       # PDF salary slip generation
│   ├── email_service.py       # SMTP email service
│   ├── attendance_engine.py   # Attendance logic
│   ├── advances_model.py      # Advances data models
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.js             # Main app (6360 lines)
│   │   ├── config.js          # API constants
│   │   ├── contexts/
│   │   │   ├── AuthContext.js  # Auth provider/hook
│   │   │   └── LanguageContext.js
│   │   └── components/
│   │       ├── Attendance/
│   │       │   └── AttendanceManagement.js
│   │       ├── Admin/
│   │       │   ├── AdminConfig.js     # System config
│   │       │   ├── LiveMonitoring.js  # Live dashboard
│   │       │   └── SalarySlips.js     # PDF & Email
│   │       └── ...
│   └── .env
```

## Completed Work (All Sessions)
### Core Features (Session 1)
- Login/Auth, Dashboard, Attendance, Employee CRUD
- Payroll, Advances & Loans, Notifications
- Manual attendance/absence, Custom reports
- Leave/Field exit/Marketing visits, Work reports

### Session 2 Fixes
- [x] Deployment fix (MongoDB indexes, /health endpoint)
- [x] Custom Report modal, Manual absence bug
- [x] Login resilience, Notification UX

### Session 2 New Features
- [x] **AttendanceManagement refactoring** (1254 lines extracted from App.js)
- [x] **AuthContext & LanguageContext** extracted to separate files
- [x] **Admin Config** (/admin/config) - System settings, attendance exceptions, import mappings
- [x] **Live Monitoring** (/admin/live) - Real-time metrics, endpoints, logs
- [x] **PDF Salary Slips** - Professional salary slips with full details (earnings, deductions, attendance, advances, net salary)
- [x] **Email Integration** - GoDaddy SMTP with salary slip sending (individual + bulk)
- [x] **Email Notification Preferences** - Configurable auto-notifications for lateness/absence/advances
- [x] **Email Logs** - Complete sending history

## Pending Tasks
### P2 (Backlog)
- [ ] Further refactoring of App.js (still ~6360 lines)
- [ ] Auto-trigger email notifications on lateness/absence events
- [ ] Arabic content in PDF salary slips

## Key API Endpoints
### PDF & Email
- `GET /api/salary-slip/{employee_id}/{cycle_month}` - Generate PDF salary slip
- `POST /api/salary-slips/bulk/{cycle_month}` - Bulk slip data
- `POST /api/email/test` - Test SMTP connection
- `POST /api/email/send-salary-slip` - Send individual salary slip
- `POST /api/email/send-bulk-salary-slips` - Send bulk salary slips
- `GET/PUT /api/email/preferences` - Email notification preferences
- `GET /api/email/logs` - Email sending history

### Admin Config
- `GET/PUT /api/admin/config/system` - System configuration
- `GET/POST/DELETE /api/admin/config/exceptions` - Attendance exceptions
- `GET/PUT /api/admin/config/import-mappings` - Import mappings

### Monitoring
- `GET /api/live/metrics` - Real-time metrics
- `GET /api/live/logs` - Server logs
- `GET /health` - Kubernetes health probe
