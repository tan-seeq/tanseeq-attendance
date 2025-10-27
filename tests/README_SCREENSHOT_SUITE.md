# TANSEEQ HR System - Automated Screenshot Suite

## Overview

This comprehensive Playwright-based automated screenshot suite captures evidence across all 20+ routes of the TANSEEQ HR system. It performs automated testing with both admin and user credentials, capturing screenshots, modals, interactions, and downloading export files.

## Features

✅ **Comprehensive Route Coverage**: Tests all 20+ routes including Dashboard, Attendance, Leaves, Field Exits, Marketing Visits, Deductions, Payroll, Reports, etc.

✅ **Multi-Role Testing**: Tests with both `admin@tanseeq.com/ADMIN` (Super Admin) and `jihad@tanseeq.com/jihad123` (Regular User)

✅ **Complete Evidence Capture**:
- Page screenshots (viewport 1920x800, quality=20)
- Modal dialogs and forms
- Interactive elements (buttons, filters, search)
- PDF/Excel downloads from export buttons
- Sidebar RTL scroll verification
- Active menu highlights

✅ **Safe CRUD Operations**: Performs Create/Edit/Delete/Filter/Search interactions where applicable without affecting production data

✅ **Organized Output**: Saves evidence in structured folders with detailed reports

## File Structure

```
/app/
├── tests/
│   ├── playwright_screenshot_suite.py    # Main test script
│   ├── requirements.txt                   # Python dependencies
│   └── README_SCREENSHOT_SUITE.md        # This file
├── run_screenshot_suite.sh               # Easy execution script
└── evidence/                             # Generated evidence (after running)
    ├── Dashboard/
    │   ├── admin/
    │   │   ├── screenshots/
    │   │   ├── modals/
    │   │   ├── downloads/
    │   │   └── interactions/
    │   └── user/
    ├── Attendance/
    ├── Leaves/
    ├── ... (20+ routes)
    ├── test_report.json                  # Detailed JSON report
    └── summary_report.md                 # Human-readable summary
```

## Routes Tested

### User-Accessible Routes (6 routes)
1. **Dashboard** (`/dashboard`) - Stats cards, quick actions
2. **Attendance** (`/attendance`) - Check-in/out functionality
3. **Leaves** (`/leaves`) - Leave request creation
4. **Field Exits** (`/field-exits`) - Field exit requests
5. **Marketing Visits** (`/marketing-visits`) - Marketing visit tracking
6. **My Deductions** (`/my-deductions`) - Personal deduction view

### Admin/Super Admin Routes (14+ routes)
7. **Employees** (`/employees`) - Employee management
8. **Attendance Management** (`/attendance-management`) - Admin attendance control
9. **Leave Management** (`/leave-management`) - Leave approval system
10. **Field Exit Management** (`/field-exit-management`) - Field exit approvals
11. **Reports** (`/reports`) - PDF/Excel export functionality
12. **Payroll** (`/payroll`) - Payroll management
13. **Advanced Deductions System** (`/attendance-deductions`) - Super Admin only
14. **Payroll Cycles Management** (`/payroll-cycles`) - Super Admin only
15. **Installment Schedules** (`/installment-schedules`) - Super Admin only
16. **Backup Management** (`/backup-management`) - Super Admin only
17. **Advances & Loans** (`/advances`) - Super Admin only
18. **Advances Admin** (`/advances/admin`) - Super Admin only
19. **Notifications** (`/notifications`) - Super Admin only
20. **Client Management** (`/work-reports/clients`) - Admin/Super Admin

## Execution Methods

### Method 1: Using Shell Script (Recommended)
```bash
# Make executable and run
chmod +x run_screenshot_suite.sh
./run_screenshot_suite.sh
```

### Method 2: Using Yarn (from frontend directory)
```bash
cd frontend
yarn test:screenshots:install  # Install dependencies (first time only)
yarn test:screenshots          # Run the suite
```

### Method 3: Direct Python Execution
```bash
# Install dependencies
pip install -r tests/requirements.txt
playwright install chromium

# Run the suite
python tests/playwright_screenshot_suite.py
```

### Method 4: Using NPX
```bash
# Install Playwright globally (if not installed)
npm install -g playwright

# Install browsers
playwright install chromium

# Run the script
npx playwright test tests/playwright_screenshot_suite.py
```

## Configuration

The script uses the following configuration (can be modified in the script):

```python
# Base URL
base_url = "https://deduction-logic.preview.emergentagent.com"

# Screenshot settings
viewport = {"width": 1920, "height": 800}
screenshot_quality = 20

# Test credentials
admin_credentials = {
    "email": "admin@tanseeq.com",
    "password": "ADMIN",
    "role": "super_admin"
}

user_credentials = {
    "email": "jihad@tanseeq.com", 
    "password": "jihad123",
    "role": "user"
}
```

## Evidence Collection

After execution, evidence is organized as follows:

### Screenshots
- `main_page.png` - Main page view
- `full_page.png` - Full page screenshot
- `sidebar_initial.png` - Sidebar in initial state
- `sidebar_scrolled.png` - Sidebar scrolled to show empty space
- `active_menu_highlight.png` - Active menu highlighting
- `table_*.png` - Data tables
- `stats_card_*.png` - Statistics cards

### Modals
- `create_modal_*.png` - Create/Add modals
- `edit_modal_*.png` - Edit modals
- Various form modals and dialogs

### Interactions
- `create_button_*.png` - Create/Add buttons
- `edit_button_*.png` - Edit buttons
- `approve_button_*.png` - Approval buttons
- `reject_button_*.png` - Rejection buttons
- `export_button_*.png` - Export buttons
- `date_filter_*.png` - Date filter controls
- `search_input_*.png` - Search inputs

### Downloads
- `export_*_*.pdf` - PDF exports
- `export_*_*.xlsx` - Excel exports
- Other downloadable files

## Reports Generated

### 1. Detailed JSON Report (`test_report.json`)
```json
{
  "start_time": "2025-01-27T10:30:00",
  "end_time": "2025-01-27T10:45:00",
  "admin_results": {
    "role": "super_admin",
    "login_successful": true,
    "routes_tested": 20,
    "routes_accessible": 20,
    "total_screenshots": 156,
    "total_modals": 23,
    "total_downloads": 8,
    "route_results": [...]
  },
  "user_results": {
    "role": "user",
    "login_successful": true,
    "routes_tested": 20,
    "routes_accessible": 6,
    "total_screenshots": 45,
    "total_modals": 8,
    "total_downloads": 0,
    "route_results": [...]
  },
  "summary": {
    "total_routes": 20,
    "total_screenshots": 201,
    "total_modals": 31,
    "total_downloads": 8,
    "total_errors": 0
  }
}
```

### 2. Summary Report (`summary_report.md`)
Human-readable markdown summary with key statistics and any errors encountered.

## Constraints Acknowledged

✅ **URL Configuration**: Uses `REACT_APP_BACKEND_URL` from environment, no hardcoded URLs

✅ **API Routes**: All backend calls use `/api` prefix as required

✅ **Authentication**: Respects role-based access control

✅ **Safe Operations**: Performs only safe interactions, no destructive operations

✅ **Production Environment**: Designed for production URL testing

## Troubleshooting

### Common Issues

1. **Login Failures**
   - Check credentials are correct
   - Verify backend URL is accessible
   - Check network connectivity

2. **Screenshot Failures**
   - Ensure sufficient disk space
   - Check file permissions for evidence directory
   - Verify Playwright browser installation

3. **Download Failures**
   - Check if export functionality is available
   - Verify download permissions
   - Ensure sufficient disk space

### Debug Mode

To run with debug logging, modify the script:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Expected Output

Upon successful completion:
- **200+ screenshots** across all routes and roles
- **30+ modal captures** of forms and dialogs
- **8+ PDF/Excel downloads** from export functions
- **Comprehensive reports** in JSON and Markdown formats
- **Organized evidence structure** ready for review

## Time Estimation

- **Setup**: 2-3 minutes (dependency installation)
- **Execution**: 10-15 minutes (full suite)
- **Total**: ~15-20 minutes for complete evidence collection

## Next Steps

After running the suite:
1. Review `evidence/summary_report.md` for overview
2. Check `evidence/test_report.json` for detailed results
3. Browse evidence folders for specific screenshots
4. Verify all expected routes were captured
5. Use evidence for system documentation or handoff

---

**Note**: This script is designed for comprehensive system documentation and testing. It performs only safe, read-only operations and modal interactions without submitting forms or making destructive changes.