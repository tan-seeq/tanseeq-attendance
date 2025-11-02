#!/usr/bin/env python3
"""
Live Streaming Frontend Audit Progress Backend Test
==================================================

Test the live streaming functionality for frontend audit progress as requested:
- Authenticate as Super Admin (admin@tanseeq.com / ADMIN)
- POST progress markers sequentially to /api/live/progress/frontend
- Verify by GET /api/live/logs
- Save evidence to /app/evidence/live/frontend_progress_init.json

Base URL: https://hrapp-tanseeq-replaced-1761028017.emergent.host/api
"""

import requests
import json
import os
import time
from datetime import datetime
from pathlib import Path

# Configuration
BASE_URL = "https://hrapp-tanseeq-replaced-1761028017.emergent.host/api"
EVIDENCE_DIR = "/app/evidence/live"
EVIDENCE_FILE = "/app/evidence/live/frontend_progress_init.json"

# Test credentials
SUPER_ADMIN_EMAIL = "admin@tanseeq.com"
SUPER_ADMIN_PASSWORD = "ADMIN"

# Progress messages to post sequentially
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

class LiveStreamingTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = {
            "test_name": "Live Streaming Frontend Audit Progress",
            "base_url": BASE_URL,
            "timestamp": datetime.now().isoformat(),
            "authentication": {},
            "progress_posts": [],
            "live_logs": {},
            "summary": {}
        }
        
        # Ensure evidence directory exists
        os.makedirs(EVIDENCE_DIR, exist_ok=True)
    
    def authenticate(self):
        """Step 1: Authenticate as Super Admin and store token"""
        print("🔐 Step 1: Authenticating as Super Admin...")
        
        login_url = f"{BASE_URL}/auth/login"
        login_data = {
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        }
        
        try:
            response = self.session.post(login_url, json=login_data, timeout=30)
            
            self.test_results["authentication"] = {
                "url": login_url,
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "response_size": len(response.content),
                "headers": dict(response.headers)
            }
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                
                if self.token:
                    # Set authorization header for future requests
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.token}",
                        "Content-Type": "application/json"
                    })
                    
                    self.test_results["authentication"]["token_received"] = True
                    self.test_results["authentication"]["user_info"] = data.get("user", {})
                    print(f"✅ Authentication successful - Token received")
                    print(f"   User: {data.get('user', {}).get('name', 'Unknown')}")
                    print(f"   Role: {data.get('user', {}).get('role', 'Unknown')}")
                    return True
                else:
                    print("❌ Authentication failed - No token in response")
                    self.test_results["authentication"]["error"] = "No token in response"
                    return False
            else:
                print(f"❌ Authentication failed - Status: {response.status_code}")
                try:
                    error_data = response.json()
                    self.test_results["authentication"]["error"] = error_data
                    print(f"   Error: {error_data}")
                except:
                    self.test_results["authentication"]["error"] = response.text
                    print(f"   Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            self.test_results["authentication"]["error"] = str(e)
            return False
    
    def post_progress_messages(self):
        """Step 2: POST progress markers sequentially"""
        print("\n📡 Step 2: Posting progress markers sequentially...")
        
        if not self.token:
            print("❌ Cannot post progress - No authentication token")
            return False
        
        progress_url = f"{BASE_URL}/live/progress/frontend"
        success_count = 0
        
        for i, message in enumerate(PROGRESS_MESSAGES, 1):
            print(f"   📤 Posting message {i}/{len(PROGRESS_MESSAGES)}: {message}")
            
            payload = {"message": message}
            
            try:
                response = self.session.post(progress_url, json=payload, timeout=30)
                
                result = {
                    "sequence": i,
                    "message": message,
                    "url": progress_url,
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                    "timestamp": datetime.now().isoformat(),
                    "response_size": len(response.content)
                }
                
                if response.status_code == 200:
                    try:
                        response_data = response.json()
                        result["response_data"] = response_data
                        success_count += 1
                        print(f"      ✅ Success - {response_data}")
                    except:
                        result["response_text"] = response.text
                        print(f"      ✅ Success - {response.text}")
                else:
                    try:
                        error_data = response.json()
                        result["error"] = error_data
                        print(f"      ❌ Failed - Status: {response.status_code}, Error: {error_data}")
                    except:
                        result["error"] = response.text
                        print(f"      ❌ Failed - Status: {response.status_code}, Error: {response.text}")
                
                self.test_results["progress_posts"].append(result)
                
                # Small delay between posts to simulate real frontend audit
                time.sleep(0.5)
                
            except Exception as e:
                print(f"      ❌ Exception: {e}")
                result = {
                    "sequence": i,
                    "message": message,
                    "url": progress_url,
                    "error": str(e),
                    "success": False,
                    "timestamp": datetime.now().isoformat()
                }
                self.test_results["progress_posts"].append(result)
        
        print(f"\n📊 Progress posting summary: {success_count}/{len(PROGRESS_MESSAGES)} successful")
        return success_count > 0
    
    def verify_live_logs(self):
        """Step 3: Verify by GET /live/logs and include last ~20 lines"""
        print("\n📋 Step 3: Verifying live logs...")
        
        if not self.token:
            print("❌ Cannot verify logs - No authentication token")
            return False
        
        logs_url = f"{BASE_URL}/live/logs"
        
        try:
            response = self.session.get(logs_url, timeout=30)
            
            self.test_results["live_logs"] = {
                "url": logs_url,
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "timestamp": datetime.now().isoformat(),
                "response_size": len(response.content)
            }
            
            if response.status_code == 200:
                try:
                    logs_data = response.json()
                    self.test_results["live_logs"]["response_data"] = logs_data
                    
                    # Extract last ~20 lines as requested
                    lines = logs_data.get("lines", [])
                    last_20_lines = lines[-20:] if len(lines) > 20 else lines
                    
                    self.test_results["live_logs"]["last_20_lines"] = last_20_lines
                    self.test_results["live_logs"]["total_lines"] = len(lines)
                    
                    print(f"✅ Live logs retrieved successfully")
                    print(f"   Total lines: {len(lines)}")
                    print(f"   Last 20 lines: {len(last_20_lines)}")
                    
                    # Display last few lines for verification
                    print("\n📄 Last few log entries:")
                    for line in last_20_lines[-5:]:
                        print(f"   {line.strip()}")
                    
                    return True
                    
                except Exception as e:
                    print(f"❌ Error parsing logs response: {e}")
                    self.test_results["live_logs"]["parse_error"] = str(e)
                    self.test_results["live_logs"]["response_text"] = response.text
                    return False
            else:
                try:
                    error_data = response.json()
                    self.test_results["live_logs"]["error"] = error_data
                    print(f"❌ Failed to get logs - Status: {response.status_code}, Error: {error_data}")
                except:
                    self.test_results["live_logs"]["error"] = response.text
                    print(f"❌ Failed to get logs - Status: {response.status_code}, Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Exception getting logs: {e}")
            self.test_results["live_logs"]["error"] = str(e)
            return False
    
    def save_evidence(self):
        """Step 4: Save evidence to /app/evidence/live/frontend_progress_init.json"""
        print(f"\n💾 Step 4: Saving evidence to {EVIDENCE_FILE}...")
        
        try:
            # Calculate summary statistics
            total_posts = len(self.test_results["progress_posts"])
            successful_posts = sum(1 for post in self.test_results["progress_posts"] if post.get("success", False))
            
            self.test_results["summary"] = {
                "total_progress_messages": total_posts,
                "successful_posts": successful_posts,
                "success_rate": f"{(successful_posts/total_posts*100):.1f}%" if total_posts > 0 else "0%",
                "authentication_success": self.test_results["authentication"].get("success", False),
                "logs_retrieval_success": self.test_results["live_logs"].get("success", False),
                "overall_success": (
                    self.test_results["authentication"].get("success", False) and
                    successful_posts > 0 and
                    self.test_results["live_logs"].get("success", False)
                )
            }
            
            # Save to file
            with open(EVIDENCE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"✅ Evidence saved successfully")
            print(f"   File: {EVIDENCE_FILE}")
            print(f"   Size: {os.path.getsize(EVIDENCE_FILE)} bytes")
            
            return True
            
        except Exception as e:
            print(f"❌ Error saving evidence: {e}")
            return False
    
    def run_test(self):
        """Run the complete live streaming test"""
        print("🚀 Starting Live Streaming Frontend Audit Progress Test")
        print("=" * 60)
        
        # Step 1: Authentication
        if not self.authenticate():
            print("\n❌ Test failed at authentication step")
            self.save_evidence()
            return False
        
        # Step 2: Post progress messages
        if not self.post_progress_messages():
            print("\n❌ Test failed at progress posting step")
            self.save_evidence()
            return False
        
        # Step 3: Verify logs
        if not self.verify_live_logs():
            print("\n❌ Test failed at logs verification step")
            self.save_evidence()
            return False
        
        # Step 4: Save evidence
        if not self.save_evidence():
            print("\n❌ Test failed at evidence saving step")
            return False
        
        # Final summary
        print("\n🎉 Live Streaming Test Completed Successfully!")
        print("=" * 60)
        
        summary = self.test_results["summary"]
        print(f"📊 Test Summary:")
        print(f"   Authentication: {'✅' if summary['authentication_success'] else '❌'}")
        print(f"   Progress Posts: {summary['successful_posts']}/{summary['total_progress_messages']} ({summary['success_rate']})")
        print(f"   Logs Retrieval: {'✅' if summary['logs_retrieval_success'] else '❌'}")
        print(f"   Overall Success: {'✅' if summary['overall_success'] else '❌'}")
        
        if self.test_results["live_logs"].get("last_20_lines"):
            print(f"\n📄 Last 20 log lines saved to evidence file")
        
        return summary['overall_success']

def main():
    """Main test execution"""
    tester = LiveStreamingTester()
    success = tester.run_test()
    
    if success:
        print(f"\n✅ All tests passed! Evidence saved to {EVIDENCE_FILE}")
        exit(0)
    else:
        print(f"\n❌ Some tests failed. Check evidence file: {EVIDENCE_FILE}")
        exit(1)

if __name__ == "__main__":
    main()