#!/usr/bin/env python3
"""
Debug Advanced Deductions System Issues
"""

import asyncio
import aiohttp
import json
from datetime import datetime

BACKEND_URL = "https://hrapp-tanseeq.emergent.host/api"
CREDENTIALS = {"email": "admin@tanseeq.com", "password": "ADMIN"}

async def debug_deductions():
    async with aiohttp.ClientSession() as session:
        # Authenticate
        async with session.post(f"{BACKEND_URL}/auth/login", json=CREDENTIALS) as response:
            auth_data = await response.json()
            token = auth_data["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
        
        print("🔍 DEBUGGING DEDUCTIONS ENDPOINTS")
        print("=" * 50)
        
        # Test monthly calculation with detailed response
        print("\n1. Testing Monthly Calculation:")
        async with session.post(
            f"{BACKEND_URL}/deductions/calculate-monthly?month=2025-10", 
            headers=headers
        ) as response:
            print(f"Status: {response.status}")
            response_text = await response.text()
            print(f"Raw Response: {response_text}")
            
            if response.status == 200:
                try:
                    data = json.loads(response_text)
                    print(f"Parsed JSON: {json.dumps(data, indent=2)}")
                except:
                    print("Failed to parse JSON")
        
        # Test custom period calculation
        print("\n2. Testing Custom Period Calculation:")
        async with session.post(
            f"{BACKEND_URL}/deductions/calculate?mode=custom&from_date=2025-10-01&to_date=2025-10-15", 
            headers=headers
        ) as response:
            print(f"Status: {response.status}")
            response_text = await response.text()
            print(f"Raw Response: {response_text}")
            
            if response.status == 200:
                try:
                    data = json.loads(response_text)
                    print(f"Parsed JSON: {json.dumps(data, indent=2)}")
                except:
                    print("Failed to parse JSON")
        
        # Test employees endpoint to see if there are employees
        print("\n3. Testing Employees List:")
        async with session.get(f"{BACKEND_URL}/employees/list", headers=headers) as response:
            print(f"Status: {response.status}")
            response_text = await response.text()
            print(f"Raw Response: {response_text[:500]}...")  # First 500 chars
        
        # Test deductions list
        print("\n4. Testing Deductions List:")
        async with session.get(f"{BACKEND_URL}/deductions", headers=headers) as response:
            print(f"Status: {response.status}")
            response_text = await response.text()
            print(f"Raw Response: {response_text[:500]}...")  # First 500 chars

if __name__ == "__main__":
    asyncio.run(debug_deductions())