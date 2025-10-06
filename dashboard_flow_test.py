#!/usr/bin/env python3
"""
Dashboard Login Flow Testing
Tests the main dashboard login flow with working credentials
"""

import requests
import json
from datetime import datetime

# Backend URL
BACKEND_URL = "https://hr-management-11.preview.emergentagent.com/api"

# Working credentials from previous test
WORKING_CREDENTIALS = [
    {"email": "admin@tanseeq.com", "password": "admin123", "role": "admin"},
    {"email": "hatem@tan-seeq.co", "password": "hatem123", "role": "super_admin"}
]

class DashboardFlowTest:
    def __init__(self):
        self.results = []
        
    def test_complete_login_flow(self, email, password, expected_role):
        """Test complete login to dashboard flow"""
        print(f"\n🔐 Testing complete login flow for: {email}")
        print("-" * 50)
        
        flow_result = {
            "email": email,
            "password": password,
            "expected_role": expected_role,
            "steps": {}
        }
        
        try:
            # Step 1: Login
            print("Step 1: Authenticating...")
            login_response = requests.post(
                f"{BACKEND_URL}/auth/login",
                json={"email": email, "password": password},
                timeout=10
            )
            
            if login_response.status_code != 200:
                flow_result["steps"]["login"] = {
                    "status": "FAILED",
                    "error": f"HTTP {login_response.status_code}: {login_response.text}"
                }
                print(f"  ❌ Login failed: {login_response.status_code}")
                return flow_result
            
            login_data = login_response.json()
            token = login_data.get("access_token")
            user_info = login_data.get("user", {})
            
            flow_result["steps"]["login"] = {
                "status": "SUCCESS",
                "user_name": user_info.get("name"),
                "user_role": user_info.get("role"),
                "user_position": user_info.get("position"),
                "is_active": user_info.get("is_active")
            }
            print(f"  ✅ Login successful - {user_info.get('name')} ({user_info.get('role')})")
            
            headers = {"Authorization": f"Bearer {token}"}
            
            # Step 2: Get user info
            print("Step 2: Fetching user information...")
            me_response = requests.get(f"{BACKEND_URL}/auth/me", headers=headers, timeout=10)
            
            if me_response.status_code == 200:
                me_data = me_response.json()
                flow_result["steps"]["user_info"] = {
                    "status": "SUCCESS",
                    "data": me_data
                }
                print(f"  ✅ User info retrieved - ID: {me_data.get('id')}")
            else:
                flow_result["steps"]["user_info"] = {
                    "status": "FAILED",
                    "error": f"HTTP {me_response.status_code}"
                }
                print(f"  ❌ User info failed: {me_response.status_code}")
            
            # Step 3: Dashboard stats
            print("Step 3: Loading dashboard statistics...")
            stats_response = requests.get(f"{BACKEND_URL}/dashboard/stats", headers=headers, timeout=10)
            
            if stats_response.status_code == 200:
                stats_data = stats_response.json()
                flow_result["steps"]["dashboard_stats"] = {
                    "status": "SUCCESS",
                    "data": stats_data
                }
                print(f"  ✅ Dashboard stats loaded")
                print(f"    - Total Users: {stats_data.get('total_users', 'N/A')}")
                print(f"    - Today Attendance: {stats_data.get('today_attendance', 'N/A')}")
                print(f"    - Pending Leaves: {stats_data.get('pending_leaves', 'N/A')}")
            else:
                flow_result["steps"]["dashboard_stats"] = {
                    "status": "FAILED",
                    "error": f"HTTP {stats_response.status_code}"
                }
                print(f"  ❌ Dashboard stats failed: {stats_response.status_code}")
            
            # Step 4: Test role-specific access
            print("Step 4: Testing role-specific access...")
            
            if user_info.get("role") == "super_admin":
                # Test super admin endpoints
                endpoints_to_test = [
                    "/users",
                    "/activity-logs",
                    "/advances/admin/all-balances",
                    "/advances/admin/pending-approvals"
                ]
            elif user_info.get("role") == "admin":
                # Test admin endpoints
                endpoints_to_test = [
                    "/users",
                    "/attendance/all",
                    "/leaves/all",
                    "/field-exits/all"
                ]
            else:
                # Test user endpoints
                endpoints_to_test = [
                    "/attendance",
                    "/leaves",
                    "/field-exits"
                ]
            
            role_access_results = {}
            for endpoint in endpoints_to_test:
                try:
                    response = requests.get(f"{BACKEND_URL}{endpoint}", headers=headers, timeout=10)
                    role_access_results[endpoint] = {
                        "status_code": response.status_code,
                        "accessible": response.status_code in [200, 404],
                        "response_size": len(response.text) if response.status_code == 200 else 0
                    }
                    
                    if response.status_code == 200:
                        print(f"    ✅ {endpoint} - Accessible")
                    elif response.status_code == 403:
                        print(f"    🔒 {endpoint} - Access denied (expected for role)")
                    else:
                        print(f"    ❌ {endpoint} - HTTP {response.status_code}")
                        
                except Exception as e:
                    role_access_results[endpoint] = {
                        "status_code": "ERROR",
                        "accessible": False,
                        "error": str(e)
                    }
                    print(f"    ❌ {endpoint} - Error: {str(e)}")
            
            flow_result["steps"]["role_access"] = {
                "status": "COMPLETED",
                "results": role_access_results
            }
            
            # Step 5: Test logout
            print("Step 5: Testing logout...")
            logout_response = requests.post(f"{BACKEND_URL}/auth/logout", headers=headers, timeout=10)
            
            if logout_response.status_code == 200:
                flow_result["steps"]["logout"] = {
                    "status": "SUCCESS"
                }
                print(f"  ✅ Logout successful")
            else:
                flow_result["steps"]["logout"] = {
                    "status": "FAILED",
                    "error": f"HTTP {logout_response.status_code}"
                }
                print(f"  ❌ Logout failed: {logout_response.status_code}")
            
            # Overall flow status
            successful_steps = sum(1 for step in flow_result["steps"].values() 
                                 if step.get("status") in ["SUCCESS", "COMPLETED"])
            total_steps = len(flow_result["steps"])
            
            flow_result["overall_status"] = "SUCCESS" if successful_steps >= 4 else "PARTIAL"
            flow_result["success_rate"] = f"{successful_steps}/{total_steps}"
            
            print(f"\n📊 Flow Summary: {successful_steps}/{total_steps} steps successful")
            
        except Exception as e:
            flow_result["overall_status"] = "ERROR"
            flow_result["error"] = str(e)
            print(f"  ❌ Flow error: {str(e)}")
        
        return flow_result
    
    def run_dashboard_flow_tests(self):
        """Run dashboard flow tests for all working credentials"""
        print("🏠 TANSEEQ DASHBOARD LOGIN FLOW TESTING")
        print("=" * 60)
        print(f"Testing dashboard flow for {len(WORKING_CREDENTIALS)} accounts...")
        print(f"Backend URL: {BACKEND_URL}")
        
        for creds in WORKING_CREDENTIALS:
            result = self.test_complete_login_flow(
                creds["email"], 
                creds["password"], 
                creds["role"]
            )
            self.results.append(result)
        
        # Generate summary
        self.generate_flow_summary()
    
    def generate_flow_summary(self):
        """Generate dashboard flow test summary"""
        print("\n" + "=" * 60)
        print("📊 DASHBOARD FLOW TEST SUMMARY")
        print("=" * 60)
        
        successful_flows = [r for r in self.results if r.get("overall_status") == "SUCCESS"]
        partial_flows = [r for r in self.results if r.get("overall_status") == "PARTIAL"]
        failed_flows = [r for r in self.results if r.get("overall_status") not in ["SUCCESS", "PARTIAL"]]
        
        print(f"Total Accounts Tested: {len(self.results)}")
        print(f"Successful Flows: {len(successful_flows)}")
        print(f"Partial Flows: {len(partial_flows)}")
        print(f"Failed Flows: {len(failed_flows)}")
        print()
        
        for result in self.results:
            print(f"📧 {result['email']} ({result['expected_role']})")
            print(f"   Status: {result.get('overall_status', 'UNKNOWN')}")
            print(f"   Success Rate: {result.get('success_rate', 'N/A')}")
            
            if result.get("steps"):
                for step_name, step_data in result["steps"].items():
                    status_icon = "✅" if step_data.get("status") == "SUCCESS" else "❌" if step_data.get("status") == "FAILED" else "🔄"
                    print(f"   {status_icon} {step_name.replace('_', ' ').title()}")
            print()
        
        # Recommendations
        print("🎯 RECOMMENDATIONS:")
        print("-" * 30)
        
        if successful_flows:
            best_account = successful_flows[0]
            print(f"✅ RECOMMENDED ACCOUNT FOR DASHBOARD ACCESS:")
            print(f"   📧 Email: {best_account['email']}")
            print(f"   🔑 Password: {best_account['password']}")
            print(f"   🎭 Role: {best_account['expected_role']}")
            print(f"   📊 Flow Success: {best_account.get('success_rate', 'N/A')}")
            
            if best_account['expected_role'] == 'super_admin':
                print(f"   💰 Advances & Loans: Full Access Available")
            else:
                print(f"   ⚠️  Limited Access: Admin role only")
        else:
            print("❌ NO FULLY SUCCESSFUL DASHBOARD FLOWS FOUND")
        
        print("\n" + "=" * 60)

def main():
    """Main execution function"""
    print("Starting TANSEEQ Dashboard Flow Test...")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tester = DashboardFlowTest()
    tester.run_dashboard_flow_tests()
    
    # Save results
    with open('/app/dashboard_flow_results.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'results': tester.results
        }, f, indent=2)
    
    print(f"📄 Detailed results saved to: /app/dashboard_flow_results.json")

if __name__ == "__main__":
    main()