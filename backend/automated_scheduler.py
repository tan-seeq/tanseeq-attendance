#!/usr/bin/env python3
"""
TANSEEQ HR System - Automated Scheduler Service
خدمة الجدولة التلقائية لنظام TANSEEQ للموارد البشرية

Features:
- 09:30 AM: Send late warnings automatically
- 06:00 PM: Send absence warnings automatically  
- End of month: Calculate and apply penalties automatically
- Daily: Send penalty notifications when applied
"""

import os
import asyncio
import schedule
import time
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import requests
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/automated_scheduler.log'),
        logging.StreamHandler()
    ]
)

# Create logs directory
Path('/app/logs').mkdir(exist_ok=True)

# MongoDB connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017/tanseeq_hr")
API_BASE_URL = os.environ.get("BACKEND_URL", "http://localhost:8001/api")

client = AsyncIOMotorClient(MONGO_URL)
db = client[os.environ.get('DB_NAME', 'tanseeq_hr')]

class AutomatedScheduler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    async def get_system_token(self):
        """Get system token for API calls"""
        try:
            # Login as system user (we'll create a system user)
            response = requests.post(f"{API_BASE_URL}/auth/login", json={
                "email": "hatem@tanseeq.com",
                "password": os.environ.get('ADMIN_PASSWORD', 'hatem123')
            })
            
            if response.status_code == 200:
                return response.json().get("access_token")
            else:
                self.logger.error(f"Failed to get system token: {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting system token: {str(e)}")
            return None

    async def send_automated_late_warnings(self):
        """Send late warnings automatically at 09:30 AM"""
        try:
            self.logger.info("🔄 Starting automated late warnings...")
            
            token = await self.get_system_token()
            if not token:
                self.logger.error("❌ Could not get system token for late warnings")
                return False

            # Make API call to send late warnings
            response = requests.post(
                f"{API_BASE_URL}/notifications/late-warning",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                result = response.json()
                notifications_sent = result.get('notifications_sent', 0)
                self.logger.info(f"✅ Late warnings sent successfully: {notifications_sent} employees notified")
                
                # Log to system activities
                await self.log_system_activity(
                    "automated_late_warnings", 
                    f"Sent {notifications_sent} late warning notifications automatically"
                )
                return True
            else:
                self.logger.error(f"❌ Failed to send late warnings: {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error in automated late warnings: {str(e)}")
            return False

    async def send_automated_absence_warnings(self):
        """Send absence warnings automatically at 06:00 PM"""
        try:
            self.logger.info("🔄 Starting automated absence warnings...")
            
            token = await self.get_system_token()
            if not token:
                self.logger.error("❌ Could not get system token for absence warnings")
                return False

            # Make API call to send absence warnings
            response = requests.post(
                f"{API_BASE_URL}/notifications/absence-warning",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                result = response.json()
                notifications_sent = result.get('notifications_sent', 0)
                absent_employees = result.get('absent_employees', 0)
                self.logger.info(f"✅ Absence warnings sent successfully: {notifications_sent} notifications for {absent_employees} absent employees")
                
                # Log to system activities
                await self.log_system_activity(
                    "automated_absence_warnings", 
                    f"Sent {notifications_sent} absence warning notifications for {absent_employees} absent employees automatically"
                )
                return True
            else:
                self.logger.error(f"❌ Failed to send absence warnings: {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error in automated absence warnings: {str(e)}")
            return False

    async def process_monthly_penalties(self):
        """Process monthly penalties automatically at end of month"""
        try:
            # Check if this is the last day of the month
            today = datetime.now()
            tomorrow = today + timedelta(days=1)
            
            if today.month != tomorrow.month:  # Last day of month
                self.logger.info("🔄 Starting automated monthly penalty processing...")
                
                token = await self.get_system_token()
                if not token:
                    self.logger.error("❌ Could not get system token for penalty processing")
                    return False

                # Get current month in YYYY-MM format
                current_month = today.strftime("%Y-%m")
                
                # Calculate penalties
                calc_response = requests.get(
                    f"{API_BASE_URL}/penalties/late/{current_month}",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if calc_response.status_code == 200:
                    penalties = calc_response.json()
                    
                    if penalties:  # If there are penalties to apply
                        # Apply penalties
                        apply_response = requests.post(
                            f"{API_BASE_URL}/penalties/apply/{current_month}",
                            headers={"Authorization": f"Bearer {token}"}
                        )
                        
                        if apply_response.status_code == 200:
                            result = apply_response.json()
                            total_employees = result.get('total_employees', 0)
                            total_penalty_amount = result.get('total_penalty_amount', 0)
                            
                            self.logger.info(f"✅ Monthly penalties applied successfully: {total_employees} employees, AED {total_penalty_amount}")
                            
                            # Send penalty notifications to each employee
                            for penalty in penalties:
                                if penalty.get('penalty_amount', 0) > 0:
                                    await self.send_penalty_notification(
                                        penalty['user_id'], 
                                        penalty['penalty_amount'], 
                                        f"خصم التأخير للشهر {current_month}"
                                    )
                            
                            # Log to system activities
                            await self.log_system_activity(
                                "automated_monthly_penalties", 
                                f"Applied monthly penalties: {total_employees} employees, AED {total_penalty_amount}"
                            )
                            return True
                        else:
                            self.logger.error(f"❌ Failed to apply penalties: {apply_response.text}")
                            return False
                    else:
                        self.logger.info("✅ No penalties to apply this month")
                        return True
                else:
                    self.logger.error(f"❌ Failed to calculate penalties: {calc_response.text}")
                    return False
            else:
                # Not end of month
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Error in automated penalty processing: {str(e)}")
            return False

    async def send_penalty_notification(self, user_id: str, penalty_amount: float, penalty_reason: str):
        """Send penalty notification to specific user"""
        try:
            token = await self.get_system_token()
            if not token:
                return False

            response = requests.post(
                f"{API_BASE_URL}/notifications/penalty-applied/{user_id}?penalty_amount={penalty_amount}&penalty_reason={penalty_reason}",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                result = response.json()
                user_name = result.get('user_name', 'Unknown')
                self.logger.info(f"✅ Penalty notification sent to {user_name}: AED {penalty_amount}")
                return True
            else:
                self.logger.error(f"❌ Failed to send penalty notification: {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error sending penalty notification: {str(e)}")
            return False

    async def log_system_activity(self, action: str, details: str):
        """Log system activity to database"""
        try:
            activity_log = {
                "id": f"system_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "user_id": "system",
                "user_name": "نظام التشغيل التلقائي",
                "action": action,
                "details": details,
                "timestamp": datetime.utcnow()
            }
            
            await db.activity_logs.insert_one(activity_log)
            
        except Exception as e:
            self.logger.error(f"❌ Error logging system activity: {str(e)}")

    def schedule_jobs(self):
        """Schedule all automated jobs"""
        self.logger.info("🚀 Starting TANSEEQ Automated Scheduler Service")
        self.logger.info("📋 Scheduled Jobs:")
        self.logger.info("   • 09:30 AM (UAE): Automated Late Warnings")
        self.logger.info("   • 06:00 PM (UAE): Automated Absence Warnings") 
        self.logger.info("   • 11:59 PM (UAE): Monthly Penalty Processing")
        
        # Schedule late warnings at 9:30 AM UAE time daily
        schedule.every().day.at("09:30").do(lambda: asyncio.run(self.send_automated_late_warnings()))
        
        # Schedule absence warnings at 6:00 PM UAE time daily
        schedule.every().day.at("18:00").do(lambda: asyncio.run(self.send_automated_absence_warnings()))
        
        # Schedule monthly penalty processing at 11:59 PM daily (will only run on last day of month)
        schedule.every().day.at("23:59").do(lambda: asyncio.run(self.process_monthly_penalties()))
        
        self.logger.info("✅ All jobs scheduled successfully!")
        
    def run(self):
        """Run the scheduler"""
        self.schedule_jobs()
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                self.logger.info("\n⏹️ Automated Scheduler Service stopped by user.")
                break
            except Exception as e:
                self.logger.error(f"❌ Scheduler error: {str(e)}")
                time.sleep(300)  # Wait 5 minutes before retrying

async def run_test():
    """Run test of all automated functions"""
    scheduler = AutomatedScheduler()
    
    print("🧪 Testing Automated Functions...")
    
    # Test late warnings
    print("\n1️⃣ Testing Late Warnings:")
    result1 = await scheduler.send_automated_late_warnings()
    print(f"   Result: {'✅ Success' if result1 else '❌ Failed'}")
    
    # Test absence warnings
    print("\n2️⃣ Testing Absence Warnings:")
    result2 = await scheduler.send_automated_absence_warnings()
    print(f"   Result: {'✅ Success' if result2 else '❌ Failed'}")
    
    # Test penalty processing (will only process if end of month)
    print("\n3️⃣ Testing Penalty Processing:")
    result3 = await scheduler.process_monthly_penalties()
    print(f"   Result: {'✅ Success' if result3 else '❌ Failed'}")
    
    print(f"\n🎯 Overall Results: {sum([result1, result2, result3])}/3 tests passed")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Run tests
        asyncio.run(run_test())
    else:
        # Run scheduler service
        scheduler = AutomatedScheduler()
        scheduler.run()