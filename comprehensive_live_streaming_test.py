#!/usr/bin/env python3
"""
Comprehensive Live Streaming Test - Local vs Production
======================================================

Tests live streaming functionality on both local and production environments
to document deployment status and functionality.
"""

import requests
import json
import os
from datetime import datetime
from pathlib import Path

# Configuration
LOCAL_URL = "http://localhost:8001/api"
PRODUCTION_URL = "https://hrapp-tanseeq-replaced-1761028017.emergent.host/api"
EVIDENCE_DIR = "/app/evidence/live"
EVIDENCE_FILE = "/app/evidence/live/comprehensive_live_streaming_test.json"

# Test credentials
SUPER_ADMIN_EMAIL = "admin@tanseeq.com"
SUPER_ADMIN_PASSWORD = "ADMIN"

# Progress messages
PROGRESS_MESSAGES = [
    "START: Frontend audit initiated",
    "STEP 1: Login page reached", 
    "STEP 2: Dashboard loaded after login",
    "STEP 3: Attendance page opened (read-only)",
    "STEP 4: Advanced Deductions October calculation started",
    "STEP 5: Advanced Deductions October calculation completed",
    "STEP 6: Advanced Deductions November calculation started",
    "STEP 7: Advanced Deductions November calculation completed",
    "STEP 8: Payroll cycles page opened",
    "COMPLETE: Frontend audit route sweep finished"
]

class ComprehensiveLiveStreamingTester:
    def __init__(self):
        self.test_results = {
            "test_name": "Comprehensive Live Streaming Test - Local vs Production",
            "timestamp": datetime.now().isoformat(),
            "environments": {
                "local": {"base_url": LOCAL_URL},
                "production": {"base_url": PRODUCTION_URL}
            },
            "summary": {}
        }
        
        # Ensure evidence directory exists
        os.makedirs(EVIDENCE_DIR, exist_ok=True)
    
    def test_environment(self, env_name, base_url):
        """Test live streaming functionality for a specific environment"""
        print(f"\n🌐 Testing {env_name.upper()} Environment: {base_url}")
        print("=" * 60)
        
        session = requests.Session()
        env_results = {
            "base_url": base_url,
            "authentication": {},
            "endpoint_availability": {},
            "progress_streaming": {},
            "logs_verification": {}
        }
        
        # Step 1: Authentication
        print("🔐 Step 1: Authentication...")
        login_url = f"{base_url}/auth/login"
        login_data = {
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        }
        
        try:
            response = session.post(login_url, json=login_data, timeout=30)
            env_results["authentication"] = {
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "response_size": len(response.content)
            }
            
            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                if token:
                    session.headers.update({
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    })
                    env_results["authentication"]["token_received"] = True
                    env_results["authentication"]["user_info"] = data.get("user", {})
                    print(f"   ✅ Authentication successful")
                else:
                    print(f"   ❌ No token received")
                    env_results["authentication"]["error"] = "No token in response"
                    return env_results
            else:
                print(f"   ❌ Authentication failed - Status: {response.status_code}")
                try:
                    env_results["authentication"]["error"] = response.json()
                except:
                    env_results["authentication"]["error"] = response.text
                return env_results
                
        except Exception as e:
            print(f"   ❌ Authentication error: {e}")
            env_results["authentication"]["error"] = str(e)
            return env_results
        
        # Step 2: Test endpoint availability
        print("🔍 Step 2: Testing endpoint availability...")
        endpoints = [
            ("GET", "/live/logs"),
            ("GET", "/live/metrics"),
            ("POST", "/live/progress/frontend")
        ]
        
        for method, endpoint in endpoints:
            try:
                url = f"{base_url}{endpoint}"
                if method == "GET":
                    response = session.get(url, timeout=30)
                else:
                    response = session.post(url, json={"message": "Test"}, timeout=30)
                
                env_results["endpoint_availability"][endpoint] = {
                    "method": method,
                    "status_code": response.status_code,
                    "available": response.status_code != 404,
                    "response_size": len(response.content)
                }
                
                status_icon = "✅" if response.status_code != 404 else "❌"
                print(f"   {status_icon} {method} {endpoint}: {response.status_code}")
                
            except Exception as e:
                env_results["endpoint_availability"][endpoint] = {
                    "method": method,
                    "error": str(e),
                    "available": False
                }
                print(f"   ❌ {method} {endpoint}: Error - {e}")
        
        # Step 3: Test progress streaming (only if endpoints are available)
        progress_endpoint_available = env_results["endpoint_availability"].get("/live/progress/frontend", {}).get("available", False)
        
        if progress_endpoint_available:
            print("📡 Step 3: Testing progress streaming...")
            success_count = 0
            env_results["progress_streaming"]["messages"] = []
            
            for i, message in enumerate(PROGRESS_MESSAGES[:3], 1):  # Test first 3 messages
                try:
                    response = session.post(f"{base_url}/live/progress/frontend", 
                                          json={"message": message}, timeout=30)
                    
                    result = {
                        "sequence": i,
                        "message": message,
                        "status_code": response.status_code,
                        "success": response.status_code == 200
                    }
                    
                    if response.status_code == 200:
                        success_count += 1
                        print(f"   ✅ Message {i}: {message}")
                    else:
                        print(f"   ❌ Message {i}: Failed - {response.status_code}")
                    
                    env_results["progress_streaming"]["messages"].append(result)
                    
                except Exception as e:
                    print(f"   ❌ Message {i}: Error - {e}")
                    env_results["progress_streaming"]["messages"].append({
                        "sequence": i,
                        "message": message,
                        "error": str(e),
                        "success": False
                    })
            
            env_results["progress_streaming"]["success_count"] = success_count
            env_results["progress_streaming"]["total_messages"] = len(PROGRESS_MESSAGES[:3])
            
        else:
            print("📡 Step 3: Skipping progress streaming - endpoint not available")
            env_results["progress_streaming"]["skipped"] = "Endpoint not available"
        
        # Step 4: Test logs verification (only if endpoint is available)
        logs_endpoint_available = env_results["endpoint_availability"].get("/live/logs", {}).get("available", False)
        
        if logs_endpoint_available:
            print("📋 Step 4: Testing logs verification...")
            try:
                response = session.get(f"{base_url}/live/logs", timeout=30)
                env_results["logs_verification"] = {
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                    "response_size": len(response.content)
                }
                
                if response.status_code == 200:
                    logs_data = response.json()
                    lines = logs_data.get("lines", [])
                    env_results["logs_verification"]["total_lines"] = len(lines)
                    env_results["logs_verification"]["last_5_lines"] = lines[-5:] if lines else []
                    print(f"   ✅ Logs retrieved - {len(lines)} lines")
                else:
                    print(f"   ❌ Logs failed - Status: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Logs error: {e}")
                env_results["logs_verification"]["error"] = str(e)
        else:
            print("📋 Step 4: Skipping logs verification - endpoint not available")
            env_results["logs_verification"]["skipped"] = "Endpoint not available"
        
        return env_results
    
    def run_comprehensive_test(self):
        """Run comprehensive test on both environments"""
        print("🚀 Starting Comprehensive Live Streaming Test")
        print("Testing both Local and Production environments")
        print("=" * 80)
        
        # Test local environment
        self.test_results["environments"]["local"].update(
            self.test_environment("local", LOCAL_URL)
        )
        
        # Test production environment
        self.test_results["environments"]["production"].update(
            self.test_environment("production", PRODUCTION_URL)
        )
        
        # Generate summary
        self.generate_summary()
        
        # Save results
        self.save_results()
        
        # Print final summary
        self.print_final_summary()
    
    def generate_summary(self):
        """Generate test summary"""
        local = self.test_results["environments"]["local"]
        production = self.test_results["environments"]["production"]
        
        self.test_results["summary"] = {
            "local_environment": {
                "authentication_success": local.get("authentication", {}).get("success", False),
                "endpoints_available": sum(1 for ep in local.get("endpoint_availability", {}).values() 
                                         if ep.get("available", False)),
                "total_endpoints": len(local.get("endpoint_availability", {})),
                "progress_streaming_success": local.get("progress_streaming", {}).get("success_count", 0),
                "logs_verification_success": local.get("logs_verification", {}).get("success", False)
            },
            "production_environment": {
                "authentication_success": production.get("authentication", {}).get("success", False),
                "endpoints_available": sum(1 for ep in production.get("endpoint_availability", {}).values() 
                                         if ep.get("available", False)),
                "total_endpoints": len(production.get("endpoint_availability", {})),
                "progress_streaming_success": production.get("progress_streaming", {}).get("success_count", 0),
                "logs_verification_success": production.get("logs_verification", {}).get("success", False)
            },
            "deployment_status": {
                "local_fully_functional": (
                    local.get("authentication", {}).get("success", False) and
                    local.get("endpoint_availability", {}).get("/live/progress/frontend", {}).get("available", False) and
                    local.get("logs_verification", {}).get("success", False)
                ),
                "production_has_live_endpoints": (
                    production.get("endpoint_availability", {}).get("/live/progress/frontend", {}).get("available", False)
                ),
                "deployment_issue": not production.get("endpoint_availability", {}).get("/live/progress/frontend", {}).get("available", False)
            }
        }
    
    def save_results(self):
        """Save test results to evidence file"""
        try:
            with open(EVIDENCE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False, default=str)
            print(f"\n💾 Results saved to: {EVIDENCE_FILE}")
        except Exception as e:
            print(f"\n❌ Error saving results: {e}")
    
    def print_final_summary(self):
        """Print final test summary"""
        print("\n🎯 COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)
        
        summary = self.test_results["summary"]
        
        print("📊 LOCAL ENVIRONMENT:")
        local = summary["local_environment"]
        print(f"   Authentication: {'✅' if local['authentication_success'] else '❌'}")
        print(f"   Endpoints Available: {local['endpoints_available']}/{local['total_endpoints']}")
        print(f"   Progress Streaming: {local['progress_streaming_success']} messages")
        print(f"   Logs Verification: {'✅' if local['logs_verification_success'] else '❌'}")
        
        print("\n📊 PRODUCTION ENVIRONMENT:")
        prod = summary["production_environment"]
        print(f"   Authentication: {'✅' if prod['authentication_success'] else '❌'}")
        print(f"   Endpoints Available: {prod['endpoints_available']}/{prod['total_endpoints']}")
        print(f"   Progress Streaming: {prod['progress_streaming_success']} messages")
        print(f"   Logs Verification: {'✅' if prod['logs_verification_success'] else '❌'}")
        
        print("\n🚀 DEPLOYMENT STATUS:")
        deploy = summary["deployment_status"]
        print(f"   Local Fully Functional: {'✅' if deploy['local_fully_functional'] else '❌'}")
        print(f"   Production Has Live Endpoints: {'✅' if deploy['production_has_live_endpoints'] else '❌'}")
        print(f"   Deployment Issue Detected: {'⚠️ YES' if deploy['deployment_issue'] else '✅ NO'}")
        
        if deploy['deployment_issue']:
            print("\n⚠️  CRITICAL FINDING:")
            print("   Live streaming endpoints are working locally but not available in production.")
            print("   This indicates a deployment synchronization issue.")
            print("   The production environment needs to be updated with the latest server.py")

def main():
    """Main test execution"""
    tester = ComprehensiveLiveStreamingTester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()