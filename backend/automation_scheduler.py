#!/usr/bin/env python3
"""
TANSEEQ HR System - Automated Notification & Penalty Scheduler
نظام التنبيهات والخصومات التلقائية
"""

import os
import asyncio
import schedule
import time
import aiohttp
import json
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MongoDB connection
MONGO_URL = os.environ.get("MONGO_URL")
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8001/api")  # Internal backend URL

class AutomationScheduler:
    def __init__(self):
        self.client = AsyncIOMotorClient(MONGO_URL)
        self.db = self.client[os.environ.get('DB_NAME', 'tanseeq_hr')]
        self.session = None
        
    async def get_admin_token(self):
        """Get admin authentication token for API calls"""
        try:
            async with aiohttp.ClientSession() as session:
                # Try to login with Hatem (Super Admin) credentials
                login_data = {
                    "email": "hatem@tanseeq.com",
                    "password": os.environ.get('ADMIN_PASSWORD', 'hatem123')
                }
                
                async with session.post(f"{BACKEND_URL}/auth/login", json=login_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("access_token")
                    else:
                        logger.error(f"Failed to get admin token: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error getting admin token: {str(e)}")
            return None
    
    async def send_automatic_late_warnings(self):
        """Send automatic late warning notifications"""
        try:
            logger.info("🚨 Running automatic late warning notifications...")
            token = await self.get_admin_token()
            if not token:
                logger.error("Failed to get admin token for late warnings")
                return
            
            headers = {"Authorization": f"Bearer {token}"}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{BACKEND_URL}/notifications/late-warning", headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"✅ Late warnings sent: {result.get('notifications_sent', 0)} notifications")
                    else:
                        logger.error(f"Failed to send late warnings: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error in automatic late warnings: {str(e)}")
    
    async def send_automatic_absence_warnings(self):
        """Send automatic absence warning notifications"""
        try:
            logger.info("📭 Running automatic absence warning notifications...")
            token = await self.get_admin_token()
            if not token:
                logger.error("Failed to get admin token for absence warnings")
                return
            
            headers = {"Authorization": f"Bearer {token}"}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{BACKEND_URL}/notifications/absence-warning", headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"✅ Absence warnings sent: {result.get('notifications_sent', 0)} notifications")
                    else:
                        logger.error(f"Failed to send absence warnings: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error in automatic absence warnings: {str(e)}")
    
    async def apply_automatic_monthly_penalties(self):
        """Automatically apply monthly penalties at end of month"""
        try:
            # Get previous month in YYYY-MM format
            today = datetime.now()
            first_day = today.replace(day=1)
            last_month = (first_day - timedelta(days=1))
            month_str = last_month.strftime("%Y-%m")
            
            logger.info(f"💰 Running automatic monthly penalty application for {month_str}...")
            
            token = await self.get_admin_token()
            if not token:
                logger.error("Failed to get admin token for penalty application")
                return
            
            headers = {"Authorization": f"Bearer {token}"}
            
            async with aiohttp.ClientSession() as session:
                # First calculate penalties to see if there are any
                async with session.get(f"{BACKEND_URL}/penalties/late/{month_str}", headers=headers) as response:
                    if response.status == 200:
                        penalties = await response.json()
                        if len(penalties) > 0:
                            # Apply penalties
                            async with session.post(f"{BACKEND_URL}/penalties/apply/{month_str}", headers=headers) as apply_response:
                                if apply_response.status == 200:
                                    result = await apply_response.json()
                                    logger.info(f"✅ Monthly penalties applied: {result.get('total_employees', 0)} employees, AED {result.get('total_penalty_amount', 0)}")
                                    
                                    # Send penalty notifications to affected employees
                                    for penalty_record in result.get('penalties', []):
                                        await self.send_penalty_notification(
                                            penalty_record['user_id'],
                                            penalty_record['penalty_amount'],
                                            f"خصم تأخيرات شهر {month_str}"
                                        )
                                else:
                                    logger.error(f"Failed to apply penalties: {apply_response.status}")
                        else:
                            logger.info(f"No penalties to apply for {month_str}")
                    else:
                        logger.error(f"Failed to calculate penalties: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error in automatic monthly penalties: {str(e)}")
    
    async def send_penalty_notification(self, user_id: str, penalty_amount: float, penalty_reason: str):
        """Send penalty notification to user"""
        try:
            token = await self.get_admin_token()
            if not token:
                return
            
            headers = {"Authorization": f"Bearer {token}"}
            params = {
                "penalty_amount": penalty_amount,
                "penalty_reason": penalty_reason
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{BACKEND_URL}/notifications/penalty-applied/{user_id}", 
                                      headers=headers, params=params) as response:
                    if response.status == 200:
                        logger.info(f"✅ Penalty notification sent to user {user_id}")
                    else:
                        logger.error(f"Failed to send penalty notification to {user_id}: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error sending penalty notification: {str(e)}")
    
    def run_scheduler(self):
        """Run the automated scheduler"""
        logger.info("🤖 TANSEEQ HR Automation Scheduler Starting...")
        logger.info("=" * 60)
        
        # Schedule daily tasks
        # Late warnings: Check at 9:30 AM (after normal work start time)
        schedule.every().day.at("09:30").do(lambda: asyncio.run(self.send_automatic_late_warnings()))
        
        # Absence warnings: Check at 11:00 AM (give people time to arrive)
        schedule.every().day.at("11:00").do(lambda: asyncio.run(self.send_automatic_absence_warnings()))
        
        # Monthly penalty application: Run on 1st day of each month at 2:00 AM
        schedule.every().day.at("02:00").do(self._check_and_apply_monthly_penalties)
        
        logger.info("⏰ Scheduled Tasks:")
        logger.info("  - Daily Late Warnings: 09:30 AM UAE")
        logger.info("  - Daily Absence Warnings: 11:00 AM UAE") 
        logger.info("  - Monthly Penalty Application: 1st of month, 02:00 AM UAE")
        logger.info("=" * 60)
        logger.info("✅ Automation scheduler is running. Press Ctrl+C to stop.")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("🛑 Automation scheduler stopped by user")
        except Exception as e:
            logger.error(f"❌ Scheduler error: {str(e)}")
    
    def _check_and_apply_monthly_penalties(self):
        """Check if today is 1st of month and apply penalties"""
        today = datetime.now()
        if today.day == 1:  # Only run on 1st day of month
            asyncio.run(self.apply_automatic_monthly_penalties())

if __name__ == "__main__":
    try:
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Create and run automation service
        service = AutomationScheduler()
        service.run_scheduler()
        
    except Exception as e:
        print(f"❌ Failed to start automation scheduler: {str(e)}")