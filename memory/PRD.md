# TANSEEQ HR Management System - PRD

## Original Problem Statement
Full-stack HR management application for TANSEEQ Tax Consultancy. Features: attendance tracking, payroll management, leave/field-exit management, advances/loans, notifications, reporting, PDF salary slips, SMTP email integration.

## Tech Stack
- **Backend**: FastAPI, MongoDB (Motor), APScheduler
- **Frontend**: React.js (PWA), Tailwind CSS, Heroicons
- **PDF**: ReportLab (English-only output)
- **Email**: Microsoft 365 SMTP with fallback

## Code Architecture (Post-Refactoring)
```
/app/
├── backend/
│   ├── server.py                 # Core API + startup events
│   ├── time_utils.py             # Robust time parsing utilities
│   ├── email_service.py          # SMTP with fallback (English)
│   ├── pdf_generator.py          # English PDF generation
│   ├── advanced_deductions_system.py # Monthly deductions
│   ├── attendance_engine.py      # Attendance processing
│   ├── work_reports_mongo.py     # Work reports DB layer
│   └── requirements.txt
├── frontend/
│   ├── public/
│   │   ├── index.html            # PWA meta tags + manifest link
│   │   ├── manifest.json         # PWA manifest (NEW)
│   │   ├── sw.js                 # Service Worker (NEW)
│   │   ├── icon-192.png          # PWA icon 192px (NEW)
│   │   └── icon-512.png          # PWA icon 512px (NEW)
│   ├── src/
│   │   ├── App.js                # LEAN: 349 lines (routing only)
│   │   ├── config.js             # BACKEND_URL, API exports
│   │   ├── index.js              # SW registration (UPDATED)
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

### Session 10 (2026-04-01): Leave Types + Manual Entry Notes + Push Notifications + Telegram Bot
- [x] **Added 5 absence types**: full_day, half_day, annual_leave (no deduction), sick_leave_paid (no deduction), sick_leave_unpaid (with deduction)
- [x] **Backend deduction logic**: Annual leave and paid sick leave skip payroll deductions entirely
- [x] **Notes column**: Added "ملاحظات" column to attendance table showing "إدخال يدوي" badge for manual entries
- [x] **Fixed auto-email on manual absence**: Removed unnecessary email alerts for admin-created absences
- [x] **PWA Push Notifications**: New sidebar section "إشعارات الهاتف" for ALL users
  - Subscribe/unsubscribe push notifications on mobile
  - Admin settings: toggle late/absence notifications, employee/admin recipients
  - Push notifications on late check-in (integrated with check-in endpoint)
  - Service worker handles push events with click-to-open
  - VAPID authentication with pywebpush
- [x] **Telegram Bot @tanseeq_hr_bot**: Free Telegram notifications
  - Employee self-linking via deep link + /start CODE
  - Background polling every 5s for /start commands
  - Auto-notification on late check-in (employee + admin)
  - Admin dashboard: linked employees list, stats
  - Test message functionality
- [x] **Testing: 100% pass rate** - 30/30 total tests across iterations 10, 11 & 12

### Session 9 (2026-03-31): Critical Deployment Fix + PWA
- [x] **Created `/app/backend/time_utils.py`**: Shared robust time parsing utility
- [x] **Fixed time parsing in 6 files**: server.py (4 locations), advanced_deductions_system.py, fix_historical_attendance_data.py, forensic_data_fixes.py, import_october_real_data.py
- [x] **Verified Custom Report & Edit/Delete buttons**: All working (100% test pass)
- [x] **PWA Conversion**: manifest.json, service worker, app icons, iOS/Android meta tags. App installable on all devices.
- [x] **Fixed Dashboard 403 for non-admin users**: `/api/users` call now conditional on admin role, prevents `Promise.all` failure for regular employees

### Session 8 (2026-03-31): Major Refactoring + English-Only Reports
- [x] App.js refactored: 6386 → 349 lines (95% reduction)
- [x] Extracted 15 components into dedicated files
- [x] All PDFs, reports, and emails converted to 100% English
- [x] October Calibration Proof added to System Health
- [x] Live Monitoring metrics fixed

### Session 7 (2026-03-31): Deployment Fix (MongoDB)
- [x] Wrapped all create_index calls with try-except for MongoDB Atlas

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
- [ ] Refactor backend/server.py (15,000+ lines) into modular route files

### P2 (Backlog)
- [ ] Build Mini Admin UI at /admin/config for managing Exceptions and Import Mappings
- [ ] Live monitoring dashboard enhancements at /admin/live
- [ ] Sample PDF salary letters
