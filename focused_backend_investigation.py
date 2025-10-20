#!/usr/bin/env python3
"""
Focused Backend Investigation for Specific Issues
"""

import asyncio
import aiohttp
import json

BACKEND_URL = "https://payroll-hardening.preview.emergentagent.com/api"
CREDENTIALS = {
    "super_admin": {"email": "hatem@tan-seeq.co", "password": "hatem123"},
    "admin": {"email": "admin@tanseeq.com", "password": "ADMIN"},
    "user": {"email": "jihad@tanseeq.com", "password": "jihad123"}
}

class FocusedTester:
    def __init__(self):
        self.session = None
        self.tokens = {}
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def authenticate(self, role: str) -> str:
        if role in self.tokens:
            return self.tokens[role]
            
        creds = CREDENTIALS[role]
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=creds,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    token = data.get("access_token")
                    self.tokens[role] = token
                    return token
                else:
                    return None
        except Exception as e:
            return None
    
    async def make_request(self, method: str, endpoint: str, role: str = "super_admin", 
                          json_data: dict = None, params: dict = None) -> tuple:
        token = await self.authenticate(role)
        if not token:
            return None, "Authentication failed"
        
        headers = {"Authorization": f"Bearer {token}"}
        if json_data:
            headers["Content-Type"] = "application/json"
        
        url = f"{BACKEND_URL}{endpoint}"
        
        try:
            async with self.session.request(
                method, url, 
                json=json_data, 
                params=params,
                headers=headers
            ) as response:
                try:
                    response_data = await response.json()
                except:
                    response_data = await response.text()
                
                return response, response_data
        except Exception as e:
            return None, f"Request exception: {str(e)}"
    
    async def investigate_installment_issues(self):
        print("🔍 Investigating Installment Schedule Issues...")
        
        # Get advances first
        response, data = await self.make_request("GET", "/advances/admin/all-transactions", "super_admin")
        if response and response.status == 200:
            advances = data.get("transactions", [])
            approved_advances = [t for t in advances if t.get("status") == "approved"]
            
            if approved_advances:
                advance_id = approved_advances[0]["id"]
                print(f"Testing with advance ID: {advance_id}")
                
                # Try different installment data formats
                test_cases = [
                    {
                        "installments_count": 3,
                        "installment_amount": 100.0,
                        "start_date": "2025-02-01"
                    },
                    {
                        "advance_id": advance_id,
                        "installments_count": 3,
                        "installment_amount": 100.0,
                        "start_date": "2025-02-01"
                    },
                    {
                        "installments_count": 3,
                        "installment_amount": 100.0,
                        "start_date": "2025-02-01",
                        "description": "Test installment schedule"
                    }
                ]
                
                for i, test_data in enumerate(test_cases):
                    print(f"\nTest case {i+1}: {test_data}")
                    response, result = await self.make_request(
                        "POST", f"/advances/{advance_id}/installments", 
                        "super_admin", test_data
                    )
                    print(f"Status: {response.status if response else 'No response'}")
                    print(f"Response: {result}")
                    
                    if response and response.status == 200:
                        break
    
    async def investigate_payroll_endpoints(self):
        print("\n🔍 Investigating Payroll Endpoints...")
        
        # Get payroll cycles
        response, data = await self.make_request("GET", "/payroll/cycles", "super_admin")
        if response and response.status == 200:
            cycles = data if isinstance(data, list) else data.get("cycles", [])
            if cycles:
                cycle_id = cycles[0]["id"]
                print(f"Testing with cycle ID: {cycle_id}")
                
                # Test different employee endpoints
                endpoints_to_test = [
                    f"/payroll/cycles/{cycle_id}/employees",
                    f"/payroll/cycles/{cycle_id}/line-items",
                    f"/payroll/cycles/{cycle_id}/summaries",
                    f"/payroll/cycles/{cycle_id}/payroll-summaries"
                ]
                
                for endpoint in endpoints_to_test:
                    response, result = await self.make_request("GET", endpoint, "super_admin")
                    print(f"\nEndpoint: {endpoint}")
                    print(f"Status: {response.status if response else 'No response'}")
                    if response and response.status != 200:
                        print(f"Error: {result}")
                    elif response:
                        print(f"Success: Found {len(result) if isinstance(result, list) else 'data'}")
    
    async def investigate_timezone_issues(self):
        print("\n🔍 Investigating Timezone Issues...")
        
        # Test specific endpoints for timezone format
        endpoints = [
            "/payroll/cycles",
            "/advances/my-transactions", 
            "/notifications/my"
        ]
        
        for endpoint in endpoints:
            response, data = await self.make_request("GET", endpoint, "super_admin")
            if response and response.status == 200:
                print(f"\nEndpoint: {endpoint}")
                
                # Sample a few datetime fields
                sample_datetimes = []
                
                def extract_datetimes(obj, path=""):
                    if isinstance(obj, dict):
                        for key, value in obj.items():
                            if key in ["created_at", "updated_at", "sent_at", "start_time", "end_time"]:
                                if isinstance(value, str):
                                    sample_datetimes.append(f"{path}.{key}: {value}")
                            elif isinstance(value, (dict, list)):
                                extract_datetimes(value, f"{path}.{key}")
                    elif isinstance(obj, list):
                        for i, item in enumerate(obj[:3]):  # Sample first 3 items
                            extract_datetimes(item, f"{path}[{i}]")
                
                extract_datetimes(data)
                
                for dt in sample_datetimes[:5]:  # Show first 5 samples
                    print(f"  {dt}")
                    
    async def run_investigation(self):
        print("🚀 Starting Focused Backend Investigation")
        print("=" * 60)
        
        await self.investigate_installment_issues()
        await self.investigate_payroll_endpoints()
        await self.investigate_timezone_issues()

async def main():
    async with FocusedTester() as tester:
        await tester.run_investigation()

if __name__ == "__main__":
    asyncio.run(main())