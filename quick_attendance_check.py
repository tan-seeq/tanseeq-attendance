#!/usr/bin/env python3
"""
Quick attendance status check before adversarial testing
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://payroll-hardening.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

async def check_attendance_status():
    """Check current attendance status"""
    
    session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
    
    try:
        # Authenticate
        creds = {'email': 'jihad@tanseeq.com', 'password': 'jihad123'}
        async with session.post(f"{API_BASE}/auth/login", json=creds) as resp:
            if resp.status == 200:
                data = await resp.json()
                token = data['access_token']
                print(f"✅ Authenticated as jihad@tanseeq.com")
            else:
                print(f"❌ Authentication failed")
                return
        
        # Check current attendance
        headers = {'Authorization': f'Bearer {token}'}
        async with session.get(f"{API_BASE}/attendance", headers=headers) as resp:
            if resp.status == 200:
                attendance_data = await resp.json()
                print(f"📊 Current attendance records: {len(attendance_data)}")
                
                # Check today's attendance
                today = datetime.now().strftime('%Y-%m-%d')
                today_records = [r for r in attendance_data if r.get('date') == today]
                
                if today_records:
                    record = today_records[0]
                    print(f"📅 Today's record: Check-in: {record.get('check_in')}, Check-out: {record.get('check_out')}")
                    print(f"   Status: {record.get('status')}, Late: {record.get('is_late')}")
                    print(f"   Late minutes: {record.get('late_minutes', 0)}")
                else:
                    print(f"📅 No attendance record for today ({today})")
                    
            else:
                error = await resp.text()
                print(f"❌ Could not get attendance: {error}")
                
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(check_attendance_status())