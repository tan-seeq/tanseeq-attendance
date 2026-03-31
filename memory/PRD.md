# TANSEEQ HR Management System - PRD

## Original Problem Statement
Full-stack HR management application for TANSEEQ Tax Consultancy. Features: attendance tracking, payroll management, leave/field-exit management, advances/loans, notifications, reporting, PDF salary slips, SMTP email integration.

## Tech Stack
- **Backend**: FastAPI, MongoDB (Motor), APScheduler
- **Frontend**: React.js, Tailwind CSS, Heroicons
- **PDF**: ReportLab with arabic-reshaper + python-bidi
- **Email**: Microsoft 365 SMTP with fallback

## Code Architecture (Post-Refactoring)
```
/app/
├── backend/
│   ├── server.py                 # Core API + startup events
│   ├── email_service.py          # SMTP with fallback
│   ├── pdf_generator.py          # Arabic PDF generation
│   ├── attendance_engine.py      # Attendance processing
│   ├── work_reports_mongo.py     # Work reports DB layer
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.js                # LEAN: 349 lines (routing only)
│   │   ├── config.js             # BACKEND_URL, API exports
│   │   ├── contexts/
│   │   │   ├── AuthContext.js
│   │   │   └── LanguageContext.js
│   │   └── components/
│   │       ├── Auth/Login.js
│   │       ├── Layout/Layout.js
│   │       ├── Dashboard/Dashboard.js
│   │       ├── Attendance/
│   │       │   ├── Attendance.js
│   │       │   └── AttendanceManagement.js
│   │       ├── Employees/Employees.js
│   │       ├── FieldExits/
│   │       │   ├── FieldExits.js
│   │       │   └── FieldExitManagement.js
│   │       ├── Leaves/
│   │       │   ├── Leaves.js
│   │       │   └── LeaveManagement.js
│   │       ├── Payroll/Payroll.js
│   │       ├── Reports/
│   │       │   ├── ReportsPage.js
│   │       │   ├── OvertimeReport.js
│   │       │   └── (other report components)
│   │       ├── Admin/
│   │       │   ├── AdminConfig.js
│   │       │   ├── AdminRequestCreation.js
│   │       │   ├── AttachmentViewer.js
│   │       │   ├── BackupManagement.js
│   │       │   ├── LiveMonitoring.js
│   │       │   ├── SalarySlips.js
│   │       │   └── SystemHealth.js
│   │       └── (other existing components)
│   └── .env
└── memory/PRD.md
```

## What's Been Implemented

### Session 7 (2026-03-31): Deployment Fix
- [x] Wrapped all `create_index` calls with try-except for MongoDB Atlas OperationFailure
- [x] Removed unused PostgreSQL env variables from backend/.env

### Session 8 (2026-03-31): Major Refactoring + Time Format Fix + English-Only Reports
- [x] **App.js refactored**: 6386 lines → 349 lines (95% reduction)
- [x] Extracted 15 components into dedicated files
- [x] Fixed missing Cog6ToothIcon import in Dashboard.js
- [x] **Fixed time-only format parsing**: Production Atlas DB stores check_in/check_out as `"09:00:00"` (time-only). Parser now handles: time-only (`HH:MM:SS`), full datetime (`YYYY-MM-DD HH:MM:SS`), and ISO format (`YYYY-MM-DDTHH:MM:SS`)
- [x] **All PDFs and reports converted to English**: Rewrote pdf_generator.py, payroll Excel export, attendance Excel report, salary email template, enhanced payroll report - zero Arabic text in any exported document

### Earlier Sessions (Completed)
- [x] Tarek's check-in issue fixed
- [x] Advances & Loans module
- [x] Notification system overhaul
- [x] Manual attendance/absence entry
- [x] Custom attendance report
- [x] Weekend logic (Fri/Sat)
- [x] Arabic PDF salary slips
- [x] APScheduler auto-reports
- [x] Microsoft 365 SMTP integration
- [x] System Health monitoring page

## Pending Tasks

### P2 (Backlog)
- [ ] Build Mini Admin UI at `/admin/config` for managing Exceptions and Import Mappings
- [ ] Live monitoring dashboard enhancements at `/admin/live`
- [ ] Sample PDF salary letters
- [ ] October calibration mode proof
