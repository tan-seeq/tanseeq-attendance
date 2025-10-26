#!/usr/bin/env python3
"""
Debug script to understand payroll cycle structure
"""

import requests
import json

# Configuration
BACKEND_URL = "https://hr-unification.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
    "email": "admin@tanseeq.com",
    "password": "ADMIN"
}

def main():
    session = requests.Session()
    
    # Authenticate
    response = session.post(f"{BACKEND_URL}/auth/login", json=ADMIN_CREDENTIALS)
    if response.status_code != 200:
        print(f"Authentication failed: {response.text}")
        return
    
    token = response.json().get("access_token")
    session.headers.update({"Authorization": f"Bearer {token}"})
    
    # Get cycles
    response = session.get(f"{BACKEND_URL}/payroll/cycles")
    if response.status_code != 200:
        print(f"Failed to get cycles: {response.text}")
        return
    
    cycles = response.json()
    print(f"Found {len(cycles)} cycles:")
    for i, cycle in enumerate(cycles):
        print(f"  {i+1}. {cycle.get('cycle_name', 'Unknown')} (ID: {cycle.get('id')})")
    
    if not cycles:
        print("No cycles found")
        return
    
    # Check first cycle summary
    cycle_id = cycles[0].get("id")
    print(f"\nChecking summary for cycle: {cycle_id}")
    
    response = session.get(f"{BACKEND_URL}/payroll/cycles/{cycle_id}/summary")
    print(f"Summary response status: {response.status_code}")
    
    if response.status_code == 200:
        summary = response.json()
        print(f"Summary structure:")
        print(json.dumps(summary, indent=2, default=str))
    else:
        print(f"Summary error: {response.text}")

if __name__ == "__main__":
    main()