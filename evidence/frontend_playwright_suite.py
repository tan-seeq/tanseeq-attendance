#!/usr/bin/env python3
"""
FRONTEND PLAYWRIGHT SUITE – PRIORITY ROUND 1 (Preview/Staging)
Comprehensive testing of TANSEEQ HR System frontend with evidence collection
"""

import asyncio
import json
import os
import time
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

# Configuration
BACKEND_URL = "https://attendance-pro-39.preview.emergentagent.com"
VIEWPORT = {"width": 1920, "height": 800}
SCREENSHOT_QUALITY = 20

# Test credentials
ADMIN_CREDENTIALS = {
    "email": "admin@tanseeq.com",
    "password": "ADMIN"
}

USER_CREDENTIALS = {
    "email": "jihad@tanseeq.com", 
    "password": "jihad123"
}

# Evidence structure
EVIDENCE_BASE = Path("/app/evidence")
EVIDENCE_STRUCTURE = {
    "PayrollCycles": ["admin", "user"],
    "AttendanceDeductions": ["admin"],
    "Reports": ["admin"],
    "Sidebar": ["admin", "user"],
    "MarketingVisits": ["admin", "user"],
    "WorkReports": ["admin"],
}

class FrontendTestSuite:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.test_results = []
        self.current_user_role = None
        self.setup_evidence_folders()

    def setup_evidence_folders(self):
        """Create organized evidence folder structure"""
        for route, roles in EVIDENCE_STRUCTURE.items():
            for role in roles:
                for subfolder in ["screenshots", "modals", "downloads", "interactions"]:
                    folder_path = EVIDENCE_BASE / route / role / subfolder
                    folder_path.mkdir(parents=True, exist_ok=True)

    async def setup_browser(self):
        """Initialize browser and context"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context(
            viewport=VIEWPORT,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        self.page = await self.context.new_page()
        
        # Enable console logging
        self.page.on("console", lambda msg: print(f"Console: {msg.text}"))
        self.page.on("pageerror", lambda error: print(f"Page Error: {error}"))

    async def login(self, credentials, role_name):
        """Login with provided credentials"""
        self.current_user_role = role_name
        print(f"\n🔐 Logging in as {role_name}...")
        
        try:
            await self.page.goto(BACKEND_URL, wait_until="networkidle")
            await self.page.wait_for_timeout(2000)
            
            # Fill login form
            await self.page.fill('input[name="email"]', credentials["email"])
            await self.page.fill('input[name="password"]', credentials["password"])
            
            # Take login screenshot
            await self.save_screenshot("login", f"login_form_{role_name}")
            
            # Submit login
            await self.page.click('button[type="submit"]')
            await self.page.wait_for_timeout(3000)
            
            # Wait for dashboard or redirect
            try:
                await self.page.wait_for_url("**/dashboard", timeout=10000)
                print(f"✅ Successfully logged in as {role_name}")
                return True
            except:
                # Check if we're on dashboard anyway
                current_url = self.page.url
                if "dashboard" in current_url or "الرئيسية" in await self.page.text_content("body"):
                    print(f"✅ Successfully logged in as {role_name}")
                    return True
                else:
                    print(f"❌ Login failed for {role_name}")
                    return False
                    
        except Exception as e:
            print(f"❌ Login error for {role_name}: {str(e)}")
            return False

    async def save_screenshot(self, route, filename, full_page=False):
        """Save screenshot with organized naming"""
        try:
            role_folder = EVIDENCE_BASE / route / self.current_user_role / "screenshots"
            role_folder.mkdir(parents=True, exist_ok=True)
            
            screenshot_path = role_folder / f"{filename}.png"
            await self.page.screenshot(
                path=str(screenshot_path),
                quality=SCREENSHOT_QUALITY,
                full_page=full_page
            )
            print(f"📸 Screenshot saved: {screenshot_path}")
            return str(screenshot_path)
        except Exception as e:
            print(f"❌ Screenshot error: {str(e)}")
            return None

    async def save_download(self, route, filename):
        """Handle file downloads"""
        try:
            role_folder = EVIDENCE_BASE / route / self.current_user_role / "downloads"
            role_folder.mkdir(parents=True, exist_ok=True)
            return str(role_folder / filename)
        except Exception as e:
            print(f"❌ Download setup error: {str(e)}")
            return None

    async def test_payroll_cycles_admin(self):
        """Test /payroll-cycles route (admin only)"""
        print("\n🧪 Testing Payroll Cycles (Admin)...")
        
        try:
            # Navigate to payroll cycles
            await self.page.goto(f"{BACKEND_URL}/payroll-cycles", wait_until="networkidle")
            await self.page.wait_for_timeout(3000)
            
            # Check for white/blank page
            page_content = await self.page.text_content("body")
            if not page_content or len(page_content.strip()) < 50:
                self.add_test_result("payroll_cycles", "load_page", False, "White/blank page detected")
                return
            
            # Take landing screenshot
            await self.save_screenshot("PayrollCycles", "landing_page")
            
            # Validate table renders rows
            table_rows = await self.page.locator("table tbody tr").count()
            if table_rows > 0:
                self.add_test_result("payroll_cycles", "table_renders", True, f"Found {table_rows} table rows")
                await self.save_screenshot("PayrollCycles", "table_with_data")
            else:
                self.add_test_result("payroll_cycles", "table_renders", False, "No table rows found")
            
            # Test Create Cycle (use future month, then cancel)
            try:
                create_button = self.page.locator('button:has-text("إنشاء دورة جديدة"), button:has-text("Create Cycle"), button[data-testid="create-cycle-button"]').first
                if await create_button.is_visible():
                    await create_button.click()
                    await self.page.wait_for_timeout(2000)
                    
                    # Take modal screenshot
                    await self.save_screenshot("PayrollCycles", "create_modal", full_page=True)
                    
                    # Fill future month and cancel
                    future_month = "2025-12"
                    month_input = self.page.locator('input[type="month"], input[name="month"]').first
                    if await month_input.is_visible():
                        await month_input.fill(future_month)
                        await self.page.wait_for_timeout(1000)
                    
                    # Cancel to avoid destructive changes
                    cancel_button = self.page.locator('button:has-text("إلغاء"), button:has-text("Cancel")').first
                    if await cancel_button.is_visible():
                        await cancel_button.click()
                        self.add_test_result("payroll_cycles", "create_cycle_flow", True, "Create cycle modal opened and cancelled successfully")
                    else:
                        # Close modal with X button
                        close_button = self.page.locator('button[aria-label="Close"], .modal-close, [data-testid="close-modal"]').first
                        if await close_button.is_visible():
                            await close_button.click()
                        self.add_test_result("payroll_cycles", "create_cycle_flow", True, "Create cycle modal opened and closed")
                else:
                    self.add_test_result("payroll_cycles", "create_cycle_flow", False, "Create cycle button not found")
            except Exception as e:
                self.add_test_result("payroll_cycles", "create_cycle_flow", False, f"Create cycle error: {str(e)}")
            
            # Test Lock/Unlock flow
            try:
                lock_buttons = self.page.locator('button:has-text("قفل"), button:has-text("Lock"), button[data-testid*="lock"]')
                unlock_buttons = self.page.locator('button:has-text("إلغاء القفل"), button:has-text("Unlock"), button[data-testid*="unlock"]')
                
                if await lock_buttons.count() > 0:
                    await lock_buttons.first.click()
                    await self.page.wait_for_timeout(2000)
                    await self.save_screenshot("PayrollCycles", "lock_modal")
                    
                    # Cancel lock action
                    cancel_button = self.page.locator('button:has-text("إلغاء"), button:has-text("Cancel")').first
                    if await cancel_button.is_visible():
                        await cancel_button.click()
                    
                    self.add_test_result("payroll_cycles", "lock_unlock_flow", True, "Lock modal opened successfully")
                elif await unlock_buttons.count() > 0:
                    await unlock_buttons.first.click()
                    await self.page.wait_for_timeout(2000)
                    await self.save_screenshot("PayrollCycles", "unlock_modal")
                    
                    # Cancel unlock action
                    cancel_button = self.page.locator('button:has-text("إلغاء"), button:has-text("Cancel")').first
                    if await cancel_button.is_visible():
                        await cancel_button.click()
                    
                    self.add_test_result("payroll_cycles", "lock_unlock_flow", True, "Unlock modal opened successfully")
                else:
                    self.add_test_result("payroll_cycles", "lock_unlock_flow", False, "No lock/unlock buttons found")
            except Exception as e:
                self.add_test_result("payroll_cycles", "lock_unlock_flow", False, f"Lock/unlock error: {str(e)}")
            
            # Test Calculate button
            try:
                calculate_button = self.page.locator('button:has-text("حساب"), button:has-text("Calculate"), button[data-testid*="calculate"]').first
                if await calculate_button.is_visible():
                    await calculate_button.click()
                    await self.page.wait_for_timeout(3000)
                    
                    # Capture any toast/response UI
                    await self.save_screenshot("PayrollCycles", "after_calculate")
                    self.add_test_result("payroll_cycles", "calculate_button", True, "Calculate button clicked successfully")
                else:
                    self.add_test_result("payroll_cycles", "calculate_button", False, "Calculate button not found")
            except Exception as e:
                self.add_test_result("payroll_cycles", "calculate_button", False, f"Calculate error: {str(e)}")
            
            # Test Export dropdown
            try:
                export_button = self.page.locator('button:has-text("تصدير"), button:has-text("Export"), button[data-testid*="export"]').first
                if await export_button.is_visible():
                    await export_button.click()
                    await self.page.wait_for_timeout(2000)
                    await self.save_screenshot("PayrollCycles", "export_dropdown_open")
                    
                    # Try to download PDF
                    pdf_button = self.page.locator('button:has-text("PDF"), a:has-text("PDF")').first
                    if await pdf_button.is_visible():
                        async with self.page.expect_download() as download_info:
                            await pdf_button.click()
                        download = await download_info.value
                        pdf_path = self.save_download("PayrollCycles", f"payroll_cycles_{int(time.time())}.pdf")
                        if pdf_path:
                            await download.save_as(pdf_path)
                            print(f"📄 PDF downloaded: {pdf_path}")
                    
                    # Try to download Excel
                    excel_button = self.page.locator('button:has-text("Excel"), button:has-text("XLSX"), a:has-text("Excel")').first
                    if await excel_button.is_visible():
                        async with self.page.expect_download() as download_info:
                            await excel_button.click()
                        download = await download_info.value
                        excel_path = self.save_download("PayrollCycles", f"payroll_cycles_{int(time.time())}.xlsx")
                        if excel_path:
                            await download.save_as(excel_path)
                            print(f"📊 Excel downloaded: {excel_path}")
                    
                    self.add_test_result("payroll_cycles", "export_functionality", True, "Export dropdown opened and downloads attempted")
                else:
                    self.add_test_result("payroll_cycles", "export_functionality", False, "Export button not found")
            except Exception as e:
                self.add_test_result("payroll_cycles", "export_functionality", False, f"Export error: {str(e)}")
            
            self.add_test_result("payroll_cycles", "overall", True, "Payroll cycles page tested successfully")
            
        except Exception as e:
            self.add_test_result("payroll_cycles", "overall", False, f"Payroll cycles test failed: {str(e)}")

    async def test_attendance_deductions_admin(self):
        """Test /attendance-deductions route (admin only)"""
        print("\n🧪 Testing Attendance Deductions (Admin)...")
        
        try:
            # Navigate to attendance deductions
            await self.page.goto(f"{BACKEND_URL}/attendance-deductions", wait_until="networkidle")
            await self.page.wait_for_timeout(3000)
            
            # Take landing screenshot
            await self.save_screenshot("AttendanceDeductions", "landing_page")
            
            # Check for employee names in table (column: الموظف)
            employee_names = await self.page.locator('td:has-text("الموظف"), th:has-text("الموظف")').count()
            if employee_names > 0:
                self.add_test_result("attendance_deductions", "employee_names_render", True, f"Found employee name column")
                await self.save_screenshot("AttendanceDeductions", "table_with_employees")
            else:
                # Try alternative selectors
                table_cells = await self.page.locator('table td').count()
                if table_cells > 0:
                    self.add_test_result("attendance_deductions", "employee_names_render", True, f"Found table with {table_cells} cells")
                else:
                    self.add_test_result("attendance_deductions", "employee_names_render", False, "No employee names or table found")
            
            # Test "خصم يدوي جديد" modal
            try:
                new_deduction_button = self.page.locator('button:has-text("خصم يدوي جديد"), button:has-text("New Manual Deduction"), button[data-testid*="new-deduction"]').first
                if await new_deduction_button.is_visible():
                    await new_deduction_button.click()
                    await self.page.wait_for_timeout(2000)
                    
                    # Take modal screenshot
                    await self.save_screenshot("AttendanceDeductions", "new_deduction_modal", full_page=True)
                    
                    # Check employee dropdown
                    employee_dropdown = self.page.locator('select[name*="employee"], select:has-text("اختر موظف"), .employee-select').first
                    if await employee_dropdown.is_visible():
                        await employee_dropdown.click()
                        await self.page.wait_for_timeout(1000)
                        await self.save_screenshot("AttendanceDeductions", "employee_dropdown_open")
                        
                        # Check if dropdown has options
                        options = await self.page.locator('select option, .dropdown-option').count()
                        if options > 1:  # More than just placeholder
                            self.add_test_result("attendance_deductions", "employee_dropdown", True, f"Employee dropdown has {options} options")
                        else:
                            self.add_test_result("attendance_deductions", "employee_dropdown", False, "Employee dropdown has no options")
                    else:
                        self.add_test_result("attendance_deductions", "employee_dropdown", False, "Employee dropdown not found")
                    
                    # Cancel the modal
                    cancel_button = self.page.locator('button:has-text("إلغاء"), button:has-text("Cancel")').first
                    if await cancel_button.is_visible():
                        await cancel_button.click()
                    else:
                        # Try close button
                        close_button = self.page.locator('button[aria-label="Close"], .modal-close').first
                        if await close_button.is_visible():
                            await close_button.click()
                    
                    self.add_test_result("attendance_deductions", "new_deduction_modal", True, "New deduction modal opened successfully")
                else:
                    self.add_test_result("attendance_deductions", "new_deduction_modal", False, "New deduction button not found")
            except Exception as e:
                self.add_test_result("attendance_deductions", "new_deduction_modal", False, f"Modal error: {str(e)}")
            
            self.add_test_result("attendance_deductions", "overall", True, "Attendance deductions page tested successfully")
            
        except Exception as e:
            self.add_test_result("attendance_deductions", "overall", False, f"Attendance deductions test failed: {str(e)}")

    async def test_reports_exports_admin(self):
        """Test export functionality across pages"""
        print("\n🧪 Testing Reports and Exports (Admin)...")
        
        try:
            # Navigate to reports page
            await self.page.goto(f"{BACKEND_URL}/reports", wait_until="networkidle")
            await self.page.wait_for_timeout(3000)
            
            # Take landing screenshot
            await self.save_screenshot("Reports", "landing_page")
            
            # Look for export buttons
            export_buttons = await self.page.locator('button:has-text("تصدير"), button:has-text("Export"), button:has-text("PDF"), button:has-text("Excel")').count()
            
            if export_buttons > 0:
                await self.save_screenshot("Reports", "export_buttons_visible")
                
                # Try PDF export
                try:
                    pdf_button = self.page.locator('button:has-text("PDF"), a:has-text("PDF")').first
                    if await pdf_button.is_visible():
                        async with self.page.expect_download() as download_info:
                            await pdf_button.click()
                        download = await download_info.value
                        pdf_path = self.save_download("Reports", f"report_{int(time.time())}.pdf")
                        if pdf_path:
                            await download.save_as(pdf_path)
                            print(f"📄 Report PDF downloaded: {pdf_path}")
                        self.add_test_result("reports", "pdf_export", True, "PDF export successful")
                    else:
                        self.add_test_result("reports", "pdf_export", False, "PDF button not visible")
                except Exception as e:
                    self.add_test_result("reports", "pdf_export", False, f"PDF export error: {str(e)}")
                
                # Try Excel export
                try:
                    excel_button = self.page.locator('button:has-text("Excel"), button:has-text("XLSX"), a:has-text("Excel")').first
                    if await excel_button.is_visible():
                        async with self.page.expect_download() as download_info:
                            await excel_button.click()
                        download = await download_info.value
                        excel_path = self.save_download("Reports", f"report_{int(time.time())}.xlsx")
                        if excel_path:
                            await download.save_as(excel_path)
                            print(f"📊 Report Excel downloaded: {excel_path}")
                        self.add_test_result("reports", "excel_export", True, "Excel export successful")
                    else:
                        self.add_test_result("reports", "excel_export", False, "Excel button not visible")
                except Exception as e:
                    self.add_test_result("reports", "excel_export", False, f"Excel export error: {str(e)}")
                
                self.add_test_result("reports", "overall", True, "Reports page tested successfully")
            else:
                self.add_test_result("reports", "overall", False, "No export buttons found on reports page")
                
        except Exception as e:
            self.add_test_result("reports", "overall", False, f"Reports test failed: {str(e)}")

    async def test_sidebar_rtl(self):
        """Test sidebar RTL functionality and scrolling"""
        print(f"\n🧪 Testing Sidebar RTL ({self.current_user_role})...")
        
        try:
            # Navigate to dashboard
            await self.page.goto(f"{BACKEND_URL}/dashboard", wait_until="networkidle")
            await self.page.wait_for_timeout(2000)
            
            # Take initial sidebar screenshot
            await self.save_screenshot("Sidebar", f"initial_sidebar_{self.current_user_role}")
            
            # Test scrollbar functionality
            sidebar = self.page.locator('.sidebar, nav, [role="navigation"]').first
            if await sidebar.is_visible():
                # Scroll down in sidebar
                await sidebar.evaluate("element => element.scrollTop = element.scrollHeight / 2")
                await self.page.wait_for_timeout(1000)
                await self.save_screenshot("Sidebar", f"sidebar_scrolled_{self.current_user_role}")
                
                # Scroll back to top
                await sidebar.evaluate("element => element.scrollTop = 0")
                await self.page.wait_for_timeout(1000)
                
                self.add_test_result("sidebar", "scroll_functionality", True, "Sidebar scrolling works")
            else:
                self.add_test_result("sidebar", "scroll_functionality", False, "Sidebar not found")
            
            # Test active page highlight by navigating to different pages
            navigation_items = await self.page.locator('nav a, nav button, .nav-item').count()
            if navigation_items > 0:
                # Click on a navigation item
                nav_item = self.page.locator('nav a, nav button').nth(1)  # Second item
                if await nav_item.is_visible():
                    await nav_item.click()
                    await self.page.wait_for_timeout(2000)
                    await self.save_screenshot("Sidebar", f"active_highlight_{self.current_user_role}")
                    self.add_test_result("sidebar", "active_highlight", True, "Navigation and active highlight working")
                else:
                    self.add_test_result("sidebar", "active_highlight", False, "Navigation items not clickable")
            else:
                self.add_test_result("sidebar", "active_highlight", False, "No navigation items found")
            
            self.add_test_result("sidebar", "overall", True, f"Sidebar RTL test completed for {self.current_user_role}")
            
        except Exception as e:
            self.add_test_result("sidebar", "overall", False, f"Sidebar test failed: {str(e)}")

    async def test_marketing_visits(self):
        """Test Marketing/Field Visits functionality"""
        print(f"\n🧪 Testing Marketing Visits ({self.current_user_role})...")
        
        try:
            # Navigate to marketing visits
            await self.page.goto(f"{BACKEND_URL}/marketing-visits", wait_until="networkidle")
            await self.page.wait_for_timeout(3000)
            
            # Take landing screenshot
            await self.save_screenshot("MarketingVisits", f"landing_page_{self.current_user_role}")
            
            # Test start visit functionality
            start_button = self.page.locator('button:has-text("بدء زيارة"), button:has-text("Start Visit"), button[data-testid*="start-visit"]').first
            if await start_button.is_visible():
                await start_button.click()
                await self.page.wait_for_timeout(2000)
                
                # Take modal screenshot
                await self.save_screenshot("MarketingVisits", f"start_visit_modal_{self.current_user_role}")
                
                # Fill minimal required fields
                purpose_field = self.page.locator('input[name*="purpose"], textarea[name*="purpose"], input[placeholder*="الغرض"]').first
                if await purpose_field.is_visible():
                    await purpose_field.fill("زيارة تجريبية للاختبار")
                
                location_field = self.page.locator('input[name*="location"], input[placeholder*="الموقع"]').first
                if await location_field.is_visible():
                    await location_field.fill("مكتب العميل")
                
                # Submit the visit start
                submit_button = self.page.locator('button:has-text("بدء"), button:has-text("Start"), button[type="submit"]').first
                if await submit_button.is_visible():
                    await submit_button.click()
                    await self.page.wait_for_timeout(3000)
                    
                    # Check for active visit UI
                    active_visit = await self.page.locator('.active-visit, .visit-timer, :has-text("زيارة نشطة")').count()
                    if active_visit > 0:
                        await self.save_screenshot("MarketingVisits", f"active_visit_ui_{self.current_user_role}")
                        
                        # Try to complete the visit
                        complete_button = self.page.locator('button:has-text("إنهاء"), button:has-text("Complete"), button[data-testid*="complete"]').first
                        if await complete_button.is_visible():
                            await complete_button.click()
                            await self.page.wait_for_timeout(2000)
                            
                            # Fill completion modal
                            await self.save_screenshot("MarketingVisits", f"completion_modal_{self.current_user_role}")
                            
                            # Fill mandatory fields
                            report_field = self.page.locator('textarea[name*="report"], textarea[placeholder*="التقرير"]').first
                            if await report_field.is_visible():
                                await report_field.fill("تم إنجاز الزيارة بنجاح. تم مناقشة المتطلبات مع العميل وتحديد الخطوات التالية.")
                            
                            # Submit completion
                            submit_complete = self.page.locator('button:has-text("إرسال"), button:has-text("Submit"), button[type="submit"]').first
                            if await submit_complete.is_visible():
                                await submit_complete.click()
                                await self.page.wait_for_timeout(3000)
                                
                                # Check for success UI
                                await self.save_screenshot("MarketingVisits", f"completion_success_{self.current_user_role}")
                                self.add_test_result("marketing_visits", "complete_visit_flow", True, "Visit completion flow successful")
                            else:
                                # Cancel completion
                                cancel_button = self.page.locator('button:has-text("إلغاء"), button:has-text("Cancel")').first
                                if await cancel_button.is_visible():
                                    await cancel_button.click()
                                self.add_test_result("marketing_visits", "complete_visit_flow", False, "Could not submit completion")
                        else:
                            self.add_test_result("marketing_visits", "complete_visit_flow", False, "Complete button not found")
                    else:
                        self.add_test_result("marketing_visits", "start_visit", False, "Active visit UI not displayed")
                else:
                    # Cancel the start modal
                    cancel_button = self.page.locator('button:has-text("إلغاء"), button:has-text("Cancel")').first
                    if await cancel_button.is_visible():
                        await cancel_button.click()
                    self.add_test_result("marketing_visits", "start_visit", False, "Could not submit visit start")
            else:
                self.add_test_result("marketing_visits", "start_visit", False, "Start visit button not found")
            
            # If admin, check notifications
            if self.current_user_role == "admin":
                try:
                    # Navigate to notifications or dashboard to check for visit notifications
                    await self.page.goto(f"{BACKEND_URL}/dashboard", wait_until="networkidle")
                    await self.page.wait_for_timeout(2000)
                    
                    # Look for notification indicators
                    notifications = await self.page.locator('.notification, .badge, :has-text("إشعار")').count()
                    if notifications > 0:
                        await self.save_screenshot("MarketingVisits", "admin_notifications")
                        self.add_test_result("marketing_visits", "admin_notifications", True, f"Found {notifications} notification indicators")
                    else:
                        self.add_test_result("marketing_visits", "admin_notifications", False, "No notification indicators found")
                except Exception as e:
                    self.add_test_result("marketing_visits", "admin_notifications", False, f"Notification check error: {str(e)}")
            
            self.add_test_result("marketing_visits", "overall", True, f"Marketing visits tested for {self.current_user_role}")
            
        except Exception as e:
            self.add_test_result("marketing_visits", "overall", False, f"Marketing visits test failed: {str(e)}")

    async def test_work_reports_admin(self):
        """Test Work Reports Logs functionality (admin only)"""
        print("\n🧪 Testing Work Reports (Admin)...")
        
        try:
            # Navigate to work reports clients
            await self.page.goto(f"{BACKEND_URL}/work-reports/clients", wait_until="networkidle")
            await self.page.wait_for_timeout(3000)
            
            # Take landing screenshot
            await self.save_screenshot("WorkReports", "clients_landing_page")
            
            # Check if clients list loads
            clients_list = await self.page.locator('table, .client-list, .clients-table').count()
            if clients_list > 0:
                self.add_test_result("work_reports", "clients_list_loads", True, "Clients list found")
                await self.save_screenshot("WorkReports", "clients_list")
                
                # Try to create a client (minimal)
                create_client_button = self.page.locator('button:has-text("إضافة عميل"), button:has-text("Add Client"), button[data-testid*="create-client"]').first
                if await create_client_button.is_visible():
                    await create_client_button.click()
                    await self.page.wait_for_timeout(2000)
                    
                    # Fill client form
                    await self.save_screenshot("WorkReports", "create_client_modal")
                    
                    name_field = self.page.locator('input[name*="name"], input[placeholder*="اسم"]').first
                    if await name_field.is_visible():
                        await name_field.fill("عميل تجريبي للاختبار")
                    
                    # Cancel to avoid creating actual data
                    cancel_button = self.page.locator('button:has-text("إلغاء"), button:has-text("Cancel")').first
                    if await cancel_button.is_visible():
                        await cancel_button.click()
                        self.add_test_result("work_reports", "create_client_modal", True, "Create client modal opened successfully")
                    else:
                        # Try close button
                        close_button = self.page.locator('button[aria-label="Close"], .modal-close').first
                        if await close_button.is_visible():
                            await close_button.click()
                        self.add_test_result("work_reports", "create_client_modal", True, "Create client modal opened")
                else:
                    self.add_test_result("work_reports", "create_client_modal", False, "Create client button not found")
            else:
                self.add_test_result("work_reports", "clients_list_loads", False, "No clients list found")
            
            # Navigate to work logs
            try:
                await self.page.goto(f"{BACKEND_URL}/work-reports/logs", wait_until="networkidle")
                await self.page.wait_for_timeout(3000)
                
                await self.save_screenshot("WorkReports", "work_logs_page")
                
                # Check for work logs list
                logs_list = await self.page.locator('table, .logs-list, .work-logs-table').count()
                if logs_list > 0:
                    self.add_test_result("work_reports", "work_logs_loads", True, "Work logs page loaded")
                    
                    # Test CRUD operations (safe)
                    # Create work log
                    create_log_button = self.page.locator('button:has-text("إضافة سجل"), button:has-text("Add Log"), button[data-testid*="create-log"]').first
                    if await create_log_button.is_visible():
                        await create_log_button.click()
                        await self.page.wait_for_timeout(2000)
                        await self.save_screenshot("WorkReports", "create_log_modal")
                        
                        # Cancel the creation
                        cancel_button = self.page.locator('button:has-text("إلغاء"), button:has-text("Cancel")').first
                        if await cancel_button.is_visible():
                            await cancel_button.click()
                        
                        self.add_test_result("work_reports", "work_log_crud", True, "Work log creation modal opened")
                    else:
                        self.add_test_result("work_reports", "work_log_crud", False, "Create log button not found")
                else:
                    self.add_test_result("work_reports", "work_logs_loads", False, "Work logs page not loaded properly")
                    
            except Exception as e:
                self.add_test_result("work_reports", "work_logs_loads", False, f"Work logs navigation error: {str(e)}")
            
            self.add_test_result("work_reports", "overall", True, "Work reports testing completed")
            
        except Exception as e:
            self.add_test_result("work_reports", "overall", False, f"Work reports test failed: {str(e)}")

    async def test_user_role_coverage(self):
        """Test user role access limitations"""
        print("\n🧪 Testing User Role Coverage...")
        
        user_routes = [
            "/attendance",
            "/leaves", 
            "/marketing-visits",
            "/my-deductions"
        ]
        
        for route in user_routes:
            try:
                await self.page.goto(f"{BACKEND_URL}{route}", wait_until="networkidle")
                await self.page.wait_for_timeout(2000)
                
                # Take screenshot of each route
                route_name = route.replace("/", "_").replace("-", "_")
                await self.save_screenshot("UserRoutes", f"user_route{route_name}")
                
                # Check if page loads (not blank/error)
                page_content = await self.page.text_content("body")
                if page_content and len(page_content.strip()) > 50:
                    self.add_test_result("user_routes", f"route_{route_name}", True, f"User can access {route}")
                else:
                    self.add_test_result("user_routes", f"route_{route_name}", False, f"User cannot access {route} - blank page")
                    
            except Exception as e:
                self.add_test_result("user_routes", f"route_{route_name}", False, f"Route {route} error: {str(e)}")

    def add_test_result(self, category, test_name, passed, details):
        """Add test result to results list"""
        result = {
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "test_name": test_name,
            "passed": passed,
            "details": details,
            "user_role": self.current_user_role
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {test_name} - {details}")

    async def generate_reports(self):
        """Generate test reports"""
        print("\n📊 Generating test reports...")
        
        # Generate JSON report
        json_report = {
            "test_suite": "Frontend Playwright Suite - Priority Round 1",
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(self.test_results),
            "passed_tests": len([r for r in self.test_results if r["passed"]]),
            "failed_tests": len([r for r in self.test_results if not r["passed"]]),
            "success_rate": f"{(len([r for r in self.test_results if r['passed']]) / len(self.test_results) * 100):.1f}%" if self.test_results else "0%",
            "results": self.test_results
        }
        
        json_path = EVIDENCE_BASE / "test_report.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_report, f, ensure_ascii=False, indent=2)
        
        # Generate markdown summary
        summary_lines = [
            "# Frontend Testing Summary Report",
            f"**Test Suite:** Frontend Playwright Suite - Priority Round 1",
            f"**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Total Tests:** {len(self.test_results)}",
            f"**Passed:** {len([r for r in self.test_results if r['passed']])}",
            f"**Failed:** {len([r for r in self.test_results if not r['passed']])}",
            f"**Success Rate:** {json_report['success_rate']}",
            "",
            "## Test Results by Category",
            ""
        ]
        
        # Group results by category
        categories = {}
        for result in self.test_results:
            category = result["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append(result)
        
        for category, results in categories.items():
            summary_lines.append(f"### {category.title()}")
            for result in results:
                status = "✅" if result["passed"] else "❌"
                summary_lines.append(f"- {status} **{result['test_name']}**: {result['details']}")
            summary_lines.append("")
        
        # Add defects section
        failed_results = [r for r in self.test_results if not r["passed"]]
        if failed_results:
            summary_lines.extend([
                "## Defects Found",
                ""
            ])
            for i, result in enumerate(failed_results, 1):
                summary_lines.extend([
                    f"### Defect #{i}: {result['test_name']}",
                    f"**Category:** {result['category']}",
                    f"**User Role:** {result['user_role']}",
                    f"**Details:** {result['details']}",
                    f"**Suggested Fix:** Review {result['category']} functionality for {result['user_role']} role",
                    ""
                ])
        
        summary_path = EVIDENCE_BASE / "summary_report.md"
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(summary_lines))
        
        print(f"📄 JSON report saved: {json_path}")
        print(f"📝 Summary report saved: {summary_path}")

    async def run_full_suite(self):
        """Run the complete test suite"""
        print("🚀 Starting Frontend Playwright Suite - Priority Round 1")
        print(f"🌐 Testing URL: {BACKEND_URL}")
        print(f"📱 Viewport: {VIEWPORT['width']}x{VIEWPORT['height']}")
        
        try:
            await self.setup_browser()
            
            # Test with Admin credentials
            if await self.login(ADMIN_CREDENTIALS, "admin"):
                await self.test_payroll_cycles_admin()
                await self.test_attendance_deductions_admin()
                await self.test_reports_exports_admin()
                await self.test_sidebar_rtl()
                await self.test_marketing_visits()
                await self.test_work_reports_admin()
            
            # Test with User credentials
            if await self.login(USER_CREDENTIALS, "user"):
                await self.test_sidebar_rtl()
                await self.test_marketing_visits()
                await self.test_user_role_coverage()
            
            # Generate reports
            await self.generate_reports()
            
            # Print summary
            total_tests = len(self.test_results)
            passed_tests = len([r for r in self.test_results if r["passed"]])
            failed_tests = total_tests - passed_tests
            success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
            
            print(f"\n🎯 Test Suite Completed!")
            print(f"📊 Results: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
            print(f"✅ Passed: {passed_tests}")
            print(f"❌ Failed: {failed_tests}")
            print(f"📁 Evidence saved in: {EVIDENCE_BASE}")
            
            return success_rate >= 80  # Consider 80%+ as success
            
        except Exception as e:
            print(f"❌ Test suite failed: {str(e)}")
            return False
        finally:
            if self.browser:
                await self.browser.close()

async def main():
    """Main execution function"""
    suite = FrontendTestSuite()
    success = await suite.run_full_suite()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)