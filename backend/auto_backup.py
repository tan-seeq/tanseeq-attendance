#!/usr/bin/env python3
"""
TANSEEQ HR System - Auto Backup Service
خدمة النسخ الاحتياطي التلقائي لقاعدة البيانات
"""

import os
import asyncio
import schedule
import time
import subprocess
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import zipfile
import shutil
from pathlib import Path

# MongoDB connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017/tanseeq_hr")
BACKUP_DIR = "/app/backups"

# Create backups directory
Path(BACKUP_DIR).mkdir(exist_ok=True)

class AutoBackupService:
    def __init__(self):
        self.client = AsyncIOMotorClient(MONGO_URL)
        self.db = self.client.tanseeq_hr
        
    async def create_backup(self):
        """Create daily backup of the database"""
        try:
            print(f"🔄 Starting backup at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Create timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_folder = f"{BACKUP_DIR}/backup_{timestamp}"
            
            # Create backup folder
            Path(backup_folder).mkdir(exist_ok=True)
            
            # Get database name from URL
            db_name = MONGO_URL.split('/')[-1] if '/' in MONGO_URL else 'tanseeq_hr'
            
            # Use mongodump to create backup
            dump_command = [
                "mongodump",
                "--uri", MONGO_URL,
                "--out", backup_folder
            ]
            
            # Execute mongodump
            result = subprocess.run(dump_command, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Database dump successful: {backup_folder}")
                
                # Create ZIP archive
                zip_path = f"{backup_folder}.zip"
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(backup_folder):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, backup_folder)
                            zipf.write(file_path, arcname)
                
                # Remove original folder, keep only ZIP
                shutil.rmtree(backup_folder)
                
                # Get file size
                file_size = os.path.getsize(zip_path) / (1024 * 1024)  # MB
                
                print(f"✅ Backup compressed: {zip_path} ({file_size:.2f} MB)")
                
                # Log backup to database
                await self.log_backup(zip_path, file_size, "success")
                
                # Clean old backups (keep last 30 days)
                await self.cleanup_old_backups()
                
                return True
                
            else:
                error_msg = result.stderr
                print(f"❌ Database dump failed: {error_msg}")
                await self.log_backup("", 0, "failed", error_msg)
                return False
                
        except Exception as e:
            print(f"❌ Backup failed with exception: {str(e)}")
            await self.log_backup("", 0, "failed", str(e))
            return False
    
    async def log_backup(self, file_path: str, file_size: float, status: str, error: str = ""):
        """Log backup operation to database"""
        try:
            log_entry = {
                "id": f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "timestamp": datetime.utcnow(),
                "file_path": file_path,
                "file_size_mb": file_size,
                "status": status,
                "error": error,
                "created_at": datetime.utcnow()
            }
            
            await self.db.backup_logs.insert_one(log_entry)
            print(f"📝 Backup logged: {status}")
            
        except Exception as e:
            print(f"⚠️ Failed to log backup: {str(e)}")
    
    async def cleanup_old_backups(self):
        """Remove backup files older than 30 days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=30)
            removed_count = 0
            
            # List all backup files
            for backup_file in Path(BACKUP_DIR).glob("backup_*.zip"):
                # Extract date from filename
                try:
                    date_str = backup_file.stem.split('_')[1]  # backup_20250116_142530
                    file_date = datetime.strptime(date_str, "%Y%m%d")
                    
                    if file_date < cutoff_date:
                        backup_file.unlink()  # Delete file
                        removed_count += 1
                        print(f"🗑️ Removed old backup: {backup_file.name}")
                        
                except Exception as e:
                    print(f"⚠️ Could not process backup file {backup_file}: {str(e)}")
            
            if removed_count > 0:
                print(f"🧹 Cleaned up {removed_count} old backup files")
            else:
                print("🧹 No old backup files to clean")
                
        except Exception as e:
            print(f"❌ Cleanup failed: {str(e)}")
    
    async def get_backup_stats(self):
        """Get backup statistics"""
        try:
            # Count backup files
            backup_files = list(Path(BACKUP_DIR).glob("backup_*.zip"))
            total_files = len(backup_files)
            
            # Calculate total size
            total_size = sum(f.stat().st_size for f in backup_files) / (1024 * 1024 * 1024)  # GB
            
            # Get latest backup
            latest_backup = None
            if backup_files:
                latest_backup = max(backup_files, key=lambda f: f.stat().st_mtime)
                latest_date = datetime.fromtimestamp(latest_backup.stat().st_mtime)
            
            # Get backup logs from database
            recent_logs = await self.db.backup_logs.find().sort("timestamp", -1).limit(5).to_list(5)
            
            stats = {
                "total_backups": total_files,
                "total_size_gb": round(total_size, 2),
                "latest_backup": latest_backup.name if latest_backup else None,
                "latest_backup_date": latest_date.strftime("%Y-%m-%d %H:%M:%S") if latest_backup else None,
                "recent_logs": recent_logs,
                "backup_directory": BACKUP_DIR
            }
            
            return stats
            
        except Exception as e:
            print(f"❌ Error getting backup stats: {str(e)}")
            return {}
    
    def run_scheduler(self):
        """Run the backup scheduler"""
        print("🚀 Starting TANSEEQ Auto-backup Service")
        print(f"📂 Backup Directory: {BACKUP_DIR}")
        print(f"🕐 Scheduled: Daily at 02:00 AM (UAE Time)")
        
        # Schedule daily backup at 2 AM UAE time
        schedule.every().day.at("02:00").do(lambda: asyncio.run(self.create_backup()))
        
        # Optional: Schedule weekly cleanup
        schedule.every().sunday.at("03:00").do(lambda: asyncio.run(self.cleanup_old_backups()))
        
        print("✅ Scheduler started. Press Ctrl+C to stop.")
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                print("\n⏹️ Backup service stopped.")
                break
            except Exception as e:
                print(f"❌ Scheduler error: {str(e)}")
                time.sleep(300)  # Wait 5 minutes before retrying

async def manual_backup():
    """Run manual backup for testing"""
    service = AutoBackupService()
    success = await service.create_backup()
    
    if success:
        stats = await service.get_backup_stats()
        print("\n📊 Backup Statistics:")
        print(f"   Total Backups: {stats.get('total_backups', 0)}")
        print(f"   Total Size: {stats.get('total_size_gb', 0)} GB")
        print(f"   Latest: {stats.get('latest_backup_date', 'None')}")
    
    service.client.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "manual":
        # Run manual backup for testing
        print("🔧 Running manual backup for testing...")
        asyncio.run(manual_backup())
    else:
        # Run scheduler
        service = AutoBackupService()
        service.run_scheduler()