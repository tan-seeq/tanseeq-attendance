# TANSEEQ HR Management System - PRD

## Original Problem Statement
Full-stack HR management application for TANSEEQ Tax Consultancy. Arabic-first (RTL) application managing attendance, payroll, advances/loans, notifications, leaves, field exits, marketing visits, and work reports.

## Tech Stack
- **Backend**: FastAPI + MongoDB (Motor) + Pydantic + ReportLab (PDF) + arabic-reshaper + python-bidi
- **Frontend**: React.js + Axios + TailwindCSS + Heroicons
- **Email**: GoDaddy SMTP (smtpout.secureserver.net:587) via smtplib
- **Fonts**: Amiri Arabic (RTL PDF support)
- **Language**: Arabic (RTL) primary

## User Roles
- **Super Admin**: Full system access, config, health monitoring
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
│   ├── server.py              # Core backend (~15000 lines)
│   ├── pdf_generator.py       # Arabic PDF salary slip generation
│   ├── email_service.py       # Arabic SMTP email service with templates
│   ├── attendance_engine.py   # Attendance logic
│   ├── fonts/                 # Amiri Arabic font files
│   │   ├── Amiri-Regular.ttf
│   │   └── Amiri-Bold.ttf
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.js
│   │   ├── config.js
│   │   ├── contexts/
│   │   │   ├── AuthContext.js
│   │   │   └── LanguageContext.js
│   │   └── components/
│   │       ├── Attendance/AttendanceManagement.js
│   │       ├── Admin/
│   │       │   ├── AdminConfig.js
│   │       │   ├── LiveMonitoring.js
│   │       │   ├── SalarySlips.js
│   │       │   └── SystemHealth.js     # NEW
│   │       ├── Dashboard/HRDashboard.js
│   │       └── ...
│   └── .env
```

## Completed Work

### Session 1 - Core Features
- Login/Auth, Dashboard, Attendance, Employee CRUD
- Payroll, Advances & Loans, Notifications
- Manual attendance/absence, Custom reports

### Session 2 - Features & Refactoring
- Deployment fix (MongoDB indexes, /health endpoint)
- AttendanceManagement refactoring (extracted from App.js)
- Admin Config, Live Monitoring, PDF Salary Slips
- Email Integration (GoDaddy SMTP)

### Session 3 - Production Stability (2026-03-31)
- HRDashboard crash fix (Promise.allSettled + DEFAULT_KPIS)
- Date overflow bug fix (calendar.monthrange)
- Backend defensive coding (safe dict access)
- SalarySlips Promise.allSettled fix

### Session 4 - New Features (2026-03-31)
- [x] **Auto email notifications**: Lateness/absence triggers send emails to employee + all super admins (fire-and-forget)
- [x] **Arabic PDF support**: Amiri font + arabic_reshaper + python-bidi for full RTL Arabic salary slips
- [x] **System Health page**: /system-health with real-time monitoring of MongoDB, SMTP, API, Auth, Storage services
- [x] **Arabic email templates**: lateness, absence, lateness_admin, absence_admin notification templates

## Key API Endpoints

### System Health
- `GET /api/system/health-check` - Comprehensive service health check (super admin only)

### PDF & Email
- `GET /api/salary-slip/{employee_id}/{cycle_month}` - Generate Arabic PDF
- `POST /api/email/test` - Test SMTP connection
- `POST /api/email/send-salary-slip` - Send salary slip email
- `GET/PUT /api/email/preferences` - Email notification preferences

### Deductions
- `POST /api/deductions/calculate-monthly?month=YYYY-MM` - Monthly deductions
- `POST /api/deductions/calculate?mode=custom` - Custom period

### Admin Config
- `GET/PUT /api/admin/config/system` - System configuration
- `GET/POST/DELETE /api/admin/config/exceptions` - Attendance exceptions

## Pending Tasks

### P2 (Backlog)
- [ ] Further refactoring of App.js (still ~6380 lines)
- [ ] Dashboard and Employees component extraction from App.js
