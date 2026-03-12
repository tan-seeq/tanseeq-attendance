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

## User Roles
- **Super Admin**: Full system access, edit/delete permissions
- **Admin**: Management access
- **User (Employee)**: Self-service attendance, leave requests

## Key Credentials
- Super Admin: admin@tanseeq.com / ADMIN
- DB Name: tanseeq_hr

## What's Been Implemented
- Login/Auth system with JWT
- Dashboard with stats
- Attendance tracking (check-in/check-out)
- Employee management (CRUD)
- Payroll cycles and summaries
- Advances & Loans module (requests, repayments, admin control)
- Notification system (send, acknowledge, modal)
- Manual attendance entry (bulk add)
- Manual absence entry (with payroll deductions)
- Custom attendance report (Excel/CSV export)
- Leave management
- Field exit management
- Marketing visits
- Work reports module
- Weekend logic (Friday + Saturday)
- Attendance edit/delete for super admins

## Completed Fixes (Feb 2026)
- [x] Deployment fix: MongoDB createIndex permission error handled with try/except
- [x] Custom Report modal: Added missing modal JSX for report generation
- [x] Edit/Delete buttons: Verified working for super_admin role
- [x] Notification modal UX: Added session-based dismissal to prevent re-showing after close

## Pending/Upcoming Tasks
### P0 (Critical)
- [ ] Refactor AttendanceManagement component out of App.js (600+ lines)

### P1 (Important)
- [ ] Fix E2E test failures: Advance Request flow, Payroll Report Download flow
- [ ] Fix notification acknowledge errors for some notification types

### P2 (Backlog)
- [ ] Build Mini Admin UI at /admin/config for Exceptions and Import Mappings
- [ ] Sample PDF salary letters
- [ ] October calibration mode auto-disabling proof
- [ ] Live monitoring dashboard at /admin/live

## Architecture
- Backend: /app/backend/server.py (14000+ lines - needs refactoring)
- Frontend: /app/frontend/src/App.js (7800+ lines - needs refactoring)
- Key modules: attendance_engine.py, payroll_integration_engine.py, advances_model.py
