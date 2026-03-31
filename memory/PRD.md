# TANSEEQ HR Management System - PRD

## Original Problem Statement
Full-stack HR management application for TANSEEQ Tax Consultancy. Features: attendance tracking, payroll management, leave/field-exit management, advances/loans, notifications, reporting, PDF salary slips, SMTP email integration.

## Tech Stack
- **Backend**: FastAPI, MongoDB (Motor), APScheduler
- **Frontend**: React.js, Tailwind CSS, Heroicons
- **PDF**: ReportLab (English-only output)
- **Email**: Microsoft 365 SMTP with fallback

## Code Architecture (Post-Refactoring)
```
/app/
├── backend/
│   ├── server.py                 # Core API + startup events
│   ├── time_utils.py             # Robust time parsing utilities (NEW)
│   ├── email_service.py          # SMTP with fallback (English)
│   ├── pdf_generator.py          # English PDF generation
│   ├── advanced_deductions_system.py # Monthly deductions
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
│   │       ├── Leaves/
│   │       ├── Payroll/Payroll.js
│   │       ├── Reports/
│   │       ├── Admin/
│   │       │   ├── AdminConfig.js
│   │       │   ├── LiveMonitoring.js
│   │       │   ├── SalarySlips.js
│   │       │   └── SystemHealth.js
│   │       └── (other components)
│   └── .env
└── memory/PRD.md
```

## What's Been Implemented

### Session 9 (2026-03-31): Critical Deployment Fix - Time Parsing
- [x] **Created `/app/backend/time_utils.py`**: Shared robust time parsing utility handling all DB formats: `"09:00:00"`, `"2025-10-01 09:00:00"`, `"2025-10-01T09:00:00"`, `"09:00"`
- [x] **Fixed `advanced_deductions_system.py`**: Replaced rigid `strptime("%H:%M:%S")` with `safe_parse_time()`
- [x] **Fixed `server.py` (4 locations)**: Lines 8477, 8599, 11311, 12888 - all check_in/check_out parsing now robust
- [x] **Fixed `fix_historical_attendance_data.py`**: Uses `safe_parse_time()` instead of format loop
- [x] **Fixed `forensic_data_fixes.py`**: Same robust parsing applied
- [x] **Fixed `import_october_real_data.py`**: Same robust parsing applied
- [x] **Verified Custom Report feature**: POST `/api/attendance/custom-report` works correctly (backend returns base64 file, frontend decodes and downloads)
- [x] **Verified Edit/Delete buttons**: 163 edit + 163 delete buttons visible for super_admin on Attendance Management page
- [x] **Testing: 100% pass rate** - 10/10 backend tests, all frontend features verified

### Session 8 (2026-03-31): Major Refactoring + English-Only Reports
- [x] App.js refactored: 6386 → 349 lines (95% reduction)
- [x] Extracted 15 components into dedicated files
- [x] All PDFs, reports, and emails converted to 100% English
- [x] October Calibration Proof added to System Health
- [x] Live Monitoring metrics fixed
- [x] Salary Letter Endpoint re-enabled (English HTML template)

### Session 7 (2026-03-31): Deployment Fix (MongoDB)
- [x] Wrapped all `create_index` calls with try-except for MongoDB Atlas OperationFailure

### Earlier Sessions (Completed)
- [x] Tarek's check-in issue fixed
- [x] Advances & Loans module
- [x] Notification system overhaul
- [x] Manual attendance/absence entry
- [x] Custom attendance report
- [x] Weekend logic (Fri/Sat)
- [x] APScheduler auto-reports
- [x] Microsoft 365 SMTP integration
- [x] System Health monitoring page

## Pending Tasks

### P1 (Important)
- [ ] Refactor `backend/server.py` (15,000+ lines) into modular route files

### P2 (Backlog)
- [ ] Build Mini Admin UI at `/admin/config` for managing Exceptions and Import Mappings
- [ ] Live monitoring dashboard enhancements at `/admin/live`
- [ ] Sample PDF salary letters
