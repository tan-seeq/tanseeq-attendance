# TANSEEQ HR Management System - PRD

## Original Problem Statement
Full-stack HR management application for TANSEEQ Tax Consultancy. Arabic-first (RTL) application managing attendance, payroll, advances/loans, notifications, leaves, field exits, marketing visits, and work reports.

## Tech Stack
- **Backend**: FastAPI + MongoDB (Motor) + Pydantic + ReportLab (PDF) + arabic-reshaper + python-bidi + APScheduler
- **Frontend**: React.js + Axios + TailwindCSS + Heroicons
- **Email**: GoDaddy SMTP (smtpout.secureserver.net:587) via smtplib
- **Fonts**: Amiri Arabic (RTL PDF support)
- **Scheduler**: APScheduler (AsyncIOScheduler + CronTrigger)

## Key Credentials
- Super Admin: admin@tanseeq.com / ADMIN
- SMTP: Taxagent@tan-seeq.co via smtpout.secureserver.net:587

## Architecture
```
/app/
├── backend/
│   ├── server.py              # Core backend (~15300 lines)
│   ├── pdf_generator.py       # Arabic PDF salary slip generation
│   ├── email_service.py       # Arabic SMTP with friendly error messages
│   ├── attendance_engine.py
│   ├── fonts/Amiri-Regular.ttf, Amiri-Bold.ttf
│   └── requirements.txt
├── frontend/
│   └── src/components/
│       ├── Admin/SalarySlips.js  # 4 tabs: slips, auto-report, email, logs
│       ├── Admin/SystemHealth.js
│       ├── Dashboard/HRDashboard.js
│       └── ...
```

## Completed Work (All Sessions)

### Session 1-2: Core Features + Refactoring
- All HR modules, Admin Config, Live Monitoring, PDF Slips, Email Integration

### Session 3: Production Stability (2026-03-31)
- HRDashboard crash fix, date overflow bug, backend defensive coding

### Session 4: New Features (2026-03-31)
- Auto email notifications lateness/absence, Arabic PDF, System Health page

### Session 5: Auto Monthly Report (2026-03-31)
- APScheduler cron job (day 28), manual trigger, config UI, run history

### Session 6: Post-Deployment Bug Fixes (2026-03-31)
- [x] **SMTP error messages**: Raw Python errors replaced with Arabic messages (فشل في المصادقة, فشل الاتصال, etc.)
- [x] **React Error #31**: Fixed all places where Pydantic validation objects were rendered in JSX
- [x] **Safe error handling**: All frontend alert() calls now handle object/array `detail` fields from FastAPI
- [x] **email_service.py**: Specific exception handling for SMTPAuthenticationError, SMTPConnectError, SMTPRecipientsRefused

## Pending Tasks
### P2 (Backlog)
- [ ] Further refactoring of App.js (~6380 lines)
