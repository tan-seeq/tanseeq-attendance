# TANSEEQ HR Management System - PRD

## Original Problem Statement
Full-stack HR management application for TANSEEQ Tax Consultancy. Arabic-first (RTL) application managing attendance, payroll, advances/loans, notifications, leaves, field exits, marketing visits, and work reports.

## Tech Stack
- **Backend**: FastAPI + MongoDB (Motor) + Pydantic
- **Frontend**: React.js + Axios + TailwindCSS
- **Data**: pandas + openpyxl for Excel exports
- **Language**: Arabic (RTL) primary

## Core Requirements
- Employee check-in/check-out attendance tracking
- Payroll management with deductions
- Advances & Loans module with employee requests and admin control
- Notification system for admin-to-employee communications
- Manual attendance/absence entry for super admins
- Custom attendance reports with Excel/CSV export
- Leave management
- Field exit management
- Marketing visits tracking
- Work reports module
- Admin configuration panel
- Live monitoring dashboard

## User Roles
- **Super Admin**: Full system access, edit/delete permissions, config management
- **Admin**: Management access
- **User (Employee)**: Self-service attendance, leave requests

## Key Credentials
- Super Admin: admin@tanseeq.com / ADMIN
- Employee: hatem@tan-seeq.co / hatem123
- DB Name: tanseeq_hr

## Architecture (Post-Refactoring)
```
/app/
├── backend/
│   ├── server.py              # Core backend (14500+ lines)
│   ├── attendance_engine.py   # Attendance logic engine
│   ├── advances_model.py      # Advances data models
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.js             # Main app (6350 lines - reduced from 7883)
│   │   ├── config.js          # NEW: API constants
│   │   ├── contexts/
│   │   │   ├── AuthContext.js  # NEW: Auth provider/hook
│   │   │   └── LanguageContext.js # NEW: Language provider/hook
│   │   └── components/
│   │       ├── Attendance/
│   │       │   └── AttendanceManagement.js  # NEW: Extracted (1254 lines)
│   │       ├── Admin/
│   │       │   ├── AdminConfig.js     # NEW: System config page
│   │       │   └── LiveMonitoring.js  # NEW: Live monitoring dashboard
│   │       ├── AdvancesLoans/
│   │       ├── IntegratedPayroll/
│   │       ├── NotificationModal.js
│   │       └── ...
│   └── .env
```

## Completed Work
### Session 1 (Previous)
- Login/Auth system with JWT
- Dashboard with stats
- Attendance tracking (check-in/check-out)
- Employee management (CRUD)
- Payroll cycles and summaries
- Advances & Loans module
- Notification system
- Manual attendance/absence entry
- Custom attendance report
- Leave/Field exit management
- Marketing visits & Work reports
- Weekend logic (Friday + Saturday)

### Session 2 (Current - March 2026)
- [x] Deployment fix: MongoDB createIndex permission error (try/except)
- [x] Health endpoint: Added /health for Kubernetes probes
- [x] Custom Report modal: Added missing modal JSX
- [x] Manual Absence bug: Fixed salary field name mismatch
- [x] Login resilience: Default values for missing user fields
- [x] Notification UX: Session-based dismissal (sessionStorage)
- [x] Notification console fix: Handle API response format {notifications:[...]}
- [x] **MAJOR REFACTORING**: Extracted AttendanceManagement (1254 lines) from App.js
- [x] **MAJOR REFACTORING**: Extracted AuthContext and LanguageContext to separate files
- [x] **NEW FEATURE**: Admin Config page (/admin/config) with 3 tabs
- [x] **NEW FEATURE**: Live Monitoring dashboard (/admin/live) with metrics

## Pending Tasks
### P2 (Backlog)
- [ ] Sample PDF salary letters
- [ ] October calibration mode auto-disabling proof
- [ ] Further refactoring of App.js (still 6350 lines)

## Key API Endpoints (New)
- `GET/PUT /api/admin/config/system` - System configuration
- `GET/POST/DELETE /api/admin/config/exceptions` - Attendance exceptions
- `GET/PUT /api/admin/config/import-mappings` - Import column mappings
- `GET /api/live/metrics` - Real-time server metrics
- `GET /api/live/logs` - Recent server logs
- `GET /health` - Kubernetes health probe
