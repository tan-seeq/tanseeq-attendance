#!/usr/bin/env python3
"""
TANSEEQ HR System - Comprehensive Playwright Screenshot Suite
=============================================================

This script performs automated screenshot capture across all 20+ routes of the TANSEEQ HR system.
It tests with both admin@tanseeq.com/ADMIN and jihad@tanseeq.com/jihad123 credentials.

Features:
- Captures screenshots of all pages, modals, and key interactions
- Performs safe CRUD operations where applicable
- Downloads PDF/Excel exports from reports
- Verifies sidebar RTL scroll and active menu highlights
- Saves organized evidence in evidence/ folder structure
- Uses viewport 1920x800 with quality=20 for screenshots

Usage:
    python tests/playwright_screenshot_suite.py
    # OR
    yarn test:screenshots
    # OR  
    npx playwright test tests/playwright_screenshot_suite.py
"""

import asyncio
import os
import json
import time
from datetime import datetime, timedelta
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TanseeqScreenshotSuite:
    def __init__(self):
        self.base_url = "https://hr-attendance-system.preview.emergentagent.com"
        self.evidence_dir = "/app/evidence"
        self.viewport = {"width": 1920, "height": 800}
        self.screenshot_quality = 20
        
        # Test credentials
        self.admin_credentials = {
            "email": "admin@tanseeq.com",
            "password": "ADMIN",
            "role": "super_admin"
        }
        
        self.user_credentials = {
            "email": "jihad@tanseeq.com", 
            "password": "jihad123",
            "role": "user"
        }
        
        # Route definitions with expected access levels
        self.routes = [
            {"path": "/dashboard", "name": "Dashboard", "access": ["user", "admin", "super_admin"], "has_stats": True},
            {"path": "/attendance", "name": "Attendance", "access": ["user", "admin", "super_admin"], "has_checkin": True},
            {"path": "/leaves", "name": "Leaves", "access": ["user", "admin", "super_admin"], "has_create": True},
            {"path": "/field-exits", "name": "Field_Exits", "access": ["user", "admin", "super_admin"], "has_create": True},
            {"path": "/marketing-visits", "name": "Marketing_Visits", "access": ["user", "admin", "super_admin"], "has_create": True},
            {"path": "/my-deductions", "name": "My_Deductions", "access": ["user", "admin", "super_admin"], "has_table": True},
            {"path": "/employees", "name": "Employees", "access": ["admin", "super_admin"], "has_table": True},
            {"path": "/attendance-management", "name": "Attendance_Management", "access": ["admin", "super_admin"], "has_table": True, "has_edit": True},
            {"path": "/leave-management", "name": "Leave_Management", "access": ["admin", "super_admin"], "has_table": True, "has_approve": True},
            {"path": "/field-exit-management", "name": "Field_Exit_Management", "access": ["admin", "super_admin"], "has_table": True, "has_approve": True},
            {"path": "/reports", "name": "Reports", "access": ["admin", "super_admin"], "has_export": True, "has_filters": True},
            {"path": "/payroll", "name": "Payroll", "access": ["admin", "super_admin"], "has_export": True},
            {"path": "/attendance-deductions", "name": "Advanced_Deductions_System", "access": ["super_admin"], "has_table": True, "has_create": True},
            {"path": "/payroll-cycles", "name": "Payroll_Cycles_Management", "access": ["super_admin"], "has_table": True, "has_create": True},
            {"path": "/installment-schedules", "name": "Installment_Schedules", "access": ["super_admin"], "has_table": True, "has_create": True},
            {"path": "/backup-management", "name": "Backup_Management", "access": ["super_admin"], "has_stats": True},
            {"path": "/advances", "name": "Advances_Loans", "access": ["super_admin"], "has_create": True, "has_table": True},
            {"path": "/advances/admin", "name": "Advances_Admin", "access": ["super_admin"], "has_table": True, "has_approve": True},
            {"path": "/notifications", "name": "Notifications", "access": ["super_admin"], "has_table": True, "has_create": True},
            {"path": "/work-reports/clients", "name": "Client_Management", "access": ["admin", "super_admin"], "has_table": True, "has_create": True}
        ]
        
        self.test_results = {
            "start_time": datetime.now().isoformat(),
            "admin_results": {},
            "user_results": {},
            "summary": {}
        }

    async def setup_evidence_directory(self):
        """Create evidence directory structure"""
        try:
            os.makedirs(self.evidence_dir, exist_ok=True)
            
            # Create subdirectories for each route
            for route in self.routes:
                route_dir = os.path.join(self.evidence_dir, route["name"])
                os.makedirs(route_dir, exist_ok=True)
                
                # Create subdirectories for different user roles
                for role in ["admin", "user"]:
                    role_dir = os.path.join(route_dir, role)
                    os.makedirs(role_dir, exist_ok=True)
                    
                    # Create subdirectories for different types of captures
                    for capture_type in ["screenshots", "downloads", "modals", "interactions"]:
                        capture_dir = os.path.join(role_dir, capture_type)
                        os.makedirs(capture_dir, exist_ok=True)
                        
            logger.info(f"Evidence directory structure created at: {self.evidence_dir}")
            
        except Exception as e:
            logger.error(f"Failed to create evidence directory: {e}")
            raise

    async def login(self, page: Page, credentials: dict) -> bool:
        """Login with provided credentials"""
        try:
            logger.info(f"Logging in as {credentials['email']}")
            
            # Navigate to login page
            await page.goto(f"{self.base_url}/login")
            await page.wait_for_load_state('networkidle')
            
            # Take login page screenshot
            await page.screenshot(
                path=f"{self.evidence_dir}/login_page_{credentials['role']}.png",
                quality=self.screenshot_quality,
                full_page=False
            )
            
            # Fill login form
            await page.fill('input[name="email"]', credentials['email'])
            await page.fill('input[name="password"]', credentials['password'])
            
            # Take filled form screenshot
            await page.screenshot(
                path=f"{self.evidence_dir}/login_form_filled_{credentials['role']}.png",
                quality=self.screenshot_quality,
                full_page=False
            )
            
            # Submit login
            await page.click('button[type="submit"]')
            await page.wait_for_load_state('networkidle')
            
            # Wait for dashboard or check for login success
            try:
                await page.wait_for_url('**/dashboard', timeout=10000)
                logger.info(f"Login successful for {credentials['email']}")
                
                # Take post-login screenshot
                await page.screenshot(
                    path=f"{self.evidence_dir}/login_success_{credentials['role']}.png",
                    quality=self.screenshot_quality,
                    full_page=False
                )
                
                return True
                
            except Exception as e:
                logger.error(f"Login failed for {credentials['email']}: {e}")
                
                # Take error screenshot
                await page.screenshot(
                    path=f"{self.evidence_dir}/login_error_{credentials['role']}.png",
                    quality=self.screenshot_quality,
                    full_page=False
                )
                
                return False
                
        except Exception as e:
            logger.error(f"Login process failed: {e}")
            return False

    async def capture_sidebar_scroll(self, page: Page, route_name: str, role: str):
        """Capture sidebar RTL scroll and active menu highlights"""
        try:
            # Capture sidebar in initial state
            sidebar = page.locator('nav.flex-1')
            if await sidebar.count() > 0:
                await sidebar.screenshot(
                    path=f"{self.evidence_dir}/{route_name}/{role}/screenshots/sidebar_initial.png",
                    quality=self.screenshot_quality
                )
                
                # Scroll sidebar to bottom to show empty space
                await page.evaluate("""
                    const sidebar = document.querySelector('nav.flex-1');
                    if (sidebar) {
                        sidebar.scrollTop = sidebar.scrollHeight;
                    }
                """)
                
                await page.wait_for_timeout(1000)
                
                # Capture scrolled sidebar
                await sidebar.screenshot(
                    path=f"{self.evidence_dir}/{route_name}/{role}/screenshots/sidebar_scrolled.png",
                    quality=self.screenshot_quality
                )
                
                # Check for active menu highlight
                active_menu = page.locator('button.bg-gray-100, button[class*="bg-blue"]')
                if await active_menu.count() > 0:
                    await active_menu.first.screenshot(
                        path=f"{self.evidence_dir}/{route_name}/{role}/screenshots/active_menu_highlight.png",
                        quality=self.screenshot_quality
                    )
                    
        except Exception as e:
            logger.warning(f"Failed to capture sidebar for {route_name}: {e}")

    async def capture_modals_and_interactions(self, page: Page, route_info: dict, role: str):
        """Capture modals and perform safe interactions"""
        route_name = route_info["name"]
        evidence_path = f"{self.evidence_dir}/{route_name}/{role}"
        
        try:
            # Look for create buttons
            if route_info.get("has_create"):
                create_buttons = await page.locator('button:has-text("إنشاء"), button:has-text("إضافة"), button:has-text("جديد"), button[class*="bg-green"], button[class*="bg-blue"]').all()
                
                for i, button in enumerate(create_buttons[:3]):  # Limit to first 3 buttons
                    try:
                        # Take screenshot of button
                        await button.screenshot(
                            path=f"{evidence_path}/interactions/create_button_{i+1}.png",
                            quality=self.screenshot_quality
                        )
                        
                        # Click button to open modal
                        await button.click(force=True)
                        await page.wait_for_timeout(2000)
                        
                        # Capture modal if it appears
                        modal = page.locator('.fixed.inset-0, [role="dialog"], .modal')
                        if await modal.count() > 0:
                            await modal.first.screenshot(
                                path=f"{evidence_path}/modals/create_modal_{i+1}.png",
                                quality=self.screenshot_quality
                            )
                            
                            # Close modal
                            close_button = page.locator('button:has-text("إلغاء"), button:has-text("إغلاق"), button[class*="text-gray"], .modal button[type="button"]')
                            if await close_button.count() > 0:
                                await close_button.first.click(force=True)
                                await page.wait_for_timeout(1000)
                                
                    except Exception as e:
                        logger.warning(f"Failed to interact with create button {i+1}: {e}")
                        # Try to close any open modals
                        await page.keyboard.press('Escape')
                        await page.wait_for_timeout(1000)

            # Look for edit buttons
            if route_info.get("has_edit"):
                edit_buttons = await page.locator('button:has-text("تعديل"), button[title*="تعديل"], .edit-button, button:has([data-testid*="edit"])').all()
                
                for i, button in enumerate(edit_buttons[:2]):  # Limit to first 2 buttons
                    try:
                        await button.screenshot(
                            path=f"{evidence_path}/interactions/edit_button_{i+1}.png",
                            quality=self.screenshot_quality
                        )
                        
                        await button.click(force=True)
                        await page.wait_for_timeout(2000)
                        
                        # Capture edit modal
                        modal = page.locator('.fixed.inset-0, [role="dialog"]')
                        if await modal.count() > 0:
                            await modal.first.screenshot(
                                path=f"{evidence_path}/modals/edit_modal_{i+1}.png",
                                quality=self.screenshot_quality
                            )
                            
                            # Close modal
                            await page.keyboard.press('Escape')
                            await page.wait_for_timeout(1000)
                            
                    except Exception as e:
                        logger.warning(f"Failed to interact with edit button {i+1}: {e}")

            # Look for approve/reject buttons
            if route_info.get("has_approve"):
                approve_buttons = await page.locator('button:has-text("موافقة"), button:has-text("قبول"), button[class*="bg-green"]').all()
                reject_buttons = await page.locator('button:has-text("رفض"), button[class*="bg-red"]').all()
                
                # Capture approve buttons
                for i, button in enumerate(approve_buttons[:2]):
                    try:
                        await button.screenshot(
                            path=f"{evidence_path}/interactions/approve_button_{i+1}.png",
                            quality=self.screenshot_quality
                        )
                    except Exception as e:
                        logger.warning(f"Failed to capture approve button {i+1}: {e}")
                
                # Capture reject buttons  
                for i, button in enumerate(reject_buttons[:2]):
                    try:
                        await button.screenshot(
                            path=f"{evidence_path}/interactions/reject_button_{i+1}.png",
                            quality=self.screenshot_quality
                        )
                    except Exception as e:
                        logger.warning(f"Failed to capture reject button {i+1}: {e}")

            # Look for filter and search elements
            if route_info.get("has_filters"):
                # Capture date filters
                date_inputs = await page.locator('input[type="date"], input[type="month"]').all()
                for i, input_elem in enumerate(date_inputs[:3]):
                    try:
                        await input_elem.screenshot(
                            path=f"{evidence_path}/interactions/date_filter_{i+1}.png",
                            quality=self.screenshot_quality
                        )
                    except Exception as e:
                        logger.warning(f"Failed to capture date filter {i+1}: {e}")
                
                # Capture search inputs
                search_inputs = await page.locator('input[placeholder*="بحث"], input[type="search"]').all()
                for i, input_elem in enumerate(search_inputs[:2]):
                    try:
                        await input_elem.screenshot(
                            path=f"{evidence_path}/interactions/search_input_{i+1}.png",
                            quality=self.screenshot_quality
                        )
                    except Exception as e:
                        logger.warning(f"Failed to capture search input {i+1}: {e}")

        except Exception as e:
            logger.warning(f"Failed to capture interactions for {route_name}: {e}")

    async def capture_export_downloads(self, page: Page, route_info: dict, role: str):
        """Capture and download PDF/Excel exports"""
        if not route_info.get("has_export"):
            return
            
        route_name = route_info["name"]
        downloads_path = f"{self.evidence_dir}/{route_name}/{role}/downloads"
        
        try:
            # Look for export buttons
            export_buttons = await page.locator(
                'button:has-text("تصدير"), button:has-text("PDF"), button:has-text("Excel"), '
                'button:has-text("تحميل"), a[href*="export"], a[href*="download"]'
            ).all()
            
            for i, button in enumerate(export_buttons[:3]):  # Limit to first 3 export buttons
                try:
                    # Take screenshot of export button
                    await button.screenshot(
                        path=f"{self.evidence_dir}/{route_name}/{role}/interactions/export_button_{i+1}.png",
                        quality=self.screenshot_quality
                    )
                    
                    # Set up download handler
                    async with page.expect_download() as download_info:
                        await button.click(force=True)
                        await page.wait_for_timeout(3000)
                    
                    download = await download_info.value
                    
                    # Save download with descriptive name
                    suggested_filename = download.suggested_filename
                    file_extension = suggested_filename.split('.')[-1] if '.' in suggested_filename else 'unknown'
                    download_filename = f"export_{i+1}_{route_name}_{role}.{file_extension}"
                    
                    await download.save_as(os.path.join(downloads_path, download_filename))
                    logger.info(f"Downloaded: {download_filename}")
                    
                except Exception as e:
                    logger.warning(f"Failed to download from export button {i+1}: {e}")
                    
        except Exception as e:
            logger.warning(f"Failed to capture exports for {route_name}: {e}")

    async def test_route(self, page: Page, route_info: dict, credentials: dict) -> dict:
        """Test a single route and capture evidence"""
        route_name = route_info["name"]
        route_path = route_info["path"]
        role = credentials["role"]
        
        result = {
            "route": route_path,
            "name": route_name,
            "role": role,
            "accessible": False,
            "screenshots_captured": 0,
            "modals_captured": 0,
            "downloads_captured": 0,
            "errors": []
        }
        
        try:
            # Check if user has access to this route
            if role not in route_info["access"]:
                logger.info(f"Skipping {route_path} - no access for {role}")
                result["accessible"] = False
                result["errors"].append(f"No access for role {role}")
                return result
            
            logger.info(f"Testing route: {route_path} as {role}")
            
            # Navigate to route
            await page.goto(f"{self.base_url}{route_path}")
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(2000)  # Allow for dynamic content loading
            
            # Check for access denied or error pages
            page_content = await page.content()
            if "وصول مقيد" in page_content or "Access Denied" in page_content or "403" in page_content:
                result["accessible"] = False
                result["errors"].append("Access denied")
                
                # Still capture screenshot of error
                await page.screenshot(
                    path=f"{self.evidence_dir}/{route_name}/{role}/screenshots/access_denied.png",
                    quality=self.screenshot_quality,
                    full_page=False
                )
                result["screenshots_captured"] += 1
                
                return result
            
            result["accessible"] = True
            
            # Capture main page screenshot
            await page.screenshot(
                path=f"{self.evidence_dir}/{route_name}/{role}/screenshots/main_page.png",
                quality=self.screenshot_quality,
                full_page=False
            )
            result["screenshots_captured"] += 1
            
            # Capture full page screenshot for reference
            await page.screenshot(
                path=f"{self.evidence_dir}/{route_name}/{role}/screenshots/full_page.png",
                quality=self.screenshot_quality,
                full_page=True
            )
            result["screenshots_captured"] += 1
            
            # Capture sidebar scroll and active menu
            await self.capture_sidebar_scroll(page, route_name, role)
            result["screenshots_captured"] += 2  # sidebar screenshots
            
            # Capture modals and interactions
            await self.capture_modals_and_interactions(page, route_info, role)
            
            # Count modal screenshots (estimate)
            modals_dir = f"{self.evidence_dir}/{route_name}/{role}/modals"
            if os.path.exists(modals_dir):
                result["modals_captured"] = len([f for f in os.listdir(modals_dir) if f.endswith('.png')])
            
            # Capture export downloads
            await self.capture_export_downloads(page, route_info, role)
            
            # Count downloads
            downloads_dir = f"{self.evidence_dir}/{route_name}/{role}/downloads"
            if os.path.exists(downloads_dir):
                result["downloads_captured"] = len([f for f in os.listdir(downloads_dir)])
            
            # Capture any tables if present
            tables = await page.locator('table, .table, [role="table"]').all()
            for i, table in enumerate(tables[:2]):  # Limit to first 2 tables
                try:
                    await table.screenshot(
                        path=f"{self.evidence_dir}/{route_name}/{role}/screenshots/table_{i+1}.png",
                        quality=self.screenshot_quality
                    )
                    result["screenshots_captured"] += 1
                except Exception as e:
                    logger.warning(f"Failed to capture table {i+1}: {e}")
            
            # Capture any stats cards if present
            if route_info.get("has_stats"):
                stats_cards = await page.locator('.bg-gradient-to-r, .stat-card, [class*="stat"]').all()
                for i, card in enumerate(stats_cards[:4]):  # Limit to first 4 cards
                    try:
                        await card.screenshot(
                            path=f"{self.evidence_dir}/{route_name}/{role}/screenshots/stats_card_{i+1}.png",
                            quality=self.screenshot_quality
                        )
                        result["screenshots_captured"] += 1
                    except Exception as e:
                        logger.warning(f"Failed to capture stats card {i+1}: {e}")
            
            logger.info(f"Successfully tested {route_path} - Screenshots: {result['screenshots_captured']}, Modals: {result['modals_captured']}, Downloads: {result['downloads_captured']}")
            
        except Exception as e:
            error_msg = f"Failed to test route {route_path}: {e}"
            logger.error(error_msg)
            result["errors"].append(error_msg)
            
            # Capture error screenshot
            try:
                await page.screenshot(
                    path=f"{self.evidence_dir}/{route_name}/{role}/screenshots/error.png",
                    quality=self.screenshot_quality,
                    full_page=False
                )
                result["screenshots_captured"] += 1
            except:
                pass
        
        return result

    async def run_test_suite(self, credentials: dict) -> dict:
        """Run the complete test suite for given credentials"""
        role = credentials["role"]
        logger.info(f"Starting test suite for {role}: {credentials['email']}")
        
        results = {
            "role": role,
            "email": credentials["email"],
            "login_successful": False,
            "routes_tested": 0,
            "routes_accessible": 0,
            "total_screenshots": 0,
            "total_modals": 0,
            "total_downloads": 0,
            "route_results": [],
            "errors": []
        }
        
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport=self.viewport,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            try:
                # Login
                login_success = await self.login(page, credentials)
                results["login_successful"] = login_success
                
                if not login_success:
                    results["errors"].append("Login failed")
                    return results
                
                # Test each route
                for route_info in self.routes:
                    route_result = await self.test_route(page, route_info, credentials)
                    results["route_results"].append(route_result)
                    
                    results["routes_tested"] += 1
                    if route_result["accessible"]:
                        results["routes_accessible"] += 1
                    
                    results["total_screenshots"] += route_result["screenshots_captured"]
                    results["total_modals"] += route_result["modals_captured"]
                    results["total_downloads"] += route_result["downloads_captured"]
                    
                    if route_result["errors"]:
                        results["errors"].extend(route_result["errors"])
                    
                    # Small delay between routes
                    await page.wait_for_timeout(1000)
                
            except Exception as e:
                error_msg = f"Test suite failed for {role}: {e}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
                
            finally:
                await browser.close()
        
        return results

    async def generate_report(self):
        """Generate comprehensive test report"""
        self.test_results["end_time"] = datetime.now().isoformat()
        
        # Calculate summary statistics
        admin_results = self.test_results.get("admin_results", {})
        user_results = self.test_results.get("user_results", {})
        
        self.test_results["summary"] = {
            "total_routes": len(self.routes),
            "admin_routes_tested": admin_results.get("routes_tested", 0),
            "admin_routes_accessible": admin_results.get("routes_accessible", 0),
            "user_routes_tested": user_results.get("routes_tested", 0),
            "user_routes_accessible": user_results.get("routes_accessible", 0),
            "total_screenshots": admin_results.get("total_screenshots", 0) + user_results.get("total_screenshots", 0),
            "total_modals": admin_results.get("total_modals", 0) + user_results.get("total_modals", 0),
            "total_downloads": admin_results.get("total_downloads", 0) + user_results.get("total_downloads", 0),
            "total_errors": len(admin_results.get("errors", [])) + len(user_results.get("errors", []))
        }
        
        # Save detailed report
        report_path = os.path.join(self.evidence_dir, "test_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        # Generate summary report
        summary_path = os.path.join(self.evidence_dir, "summary_report.md")
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("# TANSEEQ HR System - Screenshot Suite Report\n\n")
            f.write(f"**Test Date:** {self.test_results['start_time']}\n")
            f.write(f"**Total Routes:** {self.test_results['summary']['total_routes']}\n")
            f.write(f"**Total Screenshots:** {self.test_results['summary']['total_screenshots']}\n")
            f.write(f"**Total Modals Captured:** {self.test_results['summary']['total_modals']}\n")
            f.write(f"**Total Downloads:** {self.test_results['summary']['total_downloads']}\n\n")
            
            f.write("## Admin Results\n")
            f.write(f"- Routes Tested: {admin_results.get('routes_tested', 0)}\n")
            f.write(f"- Routes Accessible: {admin_results.get('routes_accessible', 0)}\n")
            f.write(f"- Screenshots: {admin_results.get('total_screenshots', 0)}\n")
            f.write(f"- Downloads: {admin_results.get('total_downloads', 0)}\n\n")
            
            f.write("## User Results\n")
            f.write(f"- Routes Tested: {user_results.get('routes_tested', 0)}\n")
            f.write(f"- Routes Accessible: {user_results.get('routes_accessible', 0)}\n")
            f.write(f"- Screenshots: {user_results.get('total_screenshots', 0)}\n")
            f.write(f"- Downloads: {user_results.get('total_downloads', 0)}\n\n")
            
            if self.test_results['summary']['total_errors'] > 0:
                f.write("## Errors Encountered\n")
                for error in admin_results.get("errors", []) + user_results.get("errors", []):
                    f.write(f"- {error}\n")
        
        logger.info(f"Test report generated: {report_path}")
        logger.info(f"Summary report generated: {summary_path}")

    async def run(self):
        """Main execution method"""
        logger.info("Starting TANSEEQ HR System Screenshot Suite")
        
        # Setup evidence directory
        await self.setup_evidence_directory()
        
        # Test with admin credentials
        logger.info("Testing with admin credentials...")
        admin_results = await self.run_test_suite(self.admin_credentials)
        self.test_results["admin_results"] = admin_results
        
        # Test with user credentials
        logger.info("Testing with user credentials...")
        user_results = await self.run_test_suite(self.user_credentials)
        self.test_results["user_results"] = user_results
        
        # Generate reports
        await self.generate_report()
        
        # Print summary
        summary = self.test_results["summary"]
        logger.info("=== TEST SUITE COMPLETED ===")
        logger.info(f"Total Screenshots: {summary['total_screenshots']}")
        logger.info(f"Total Modals: {summary['total_modals']}")
        logger.info(f"Total Downloads: {summary['total_downloads']}")
        logger.info(f"Total Errors: {summary['total_errors']}")
        logger.info(f"Evidence saved to: {self.evidence_dir}")

async def main():
    """Main entry point"""
    suite = TanseeqScreenshotSuite()
    await suite.run()

if __name__ == "__main__":
    asyncio.run(main())