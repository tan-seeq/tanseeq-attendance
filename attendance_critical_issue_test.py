#!/usr/bin/env python3
"""
CRITICAL ISSUE TESTING: 9:15 AM Late Tracking Rule Implementation
Testing the actual functionality vs expected behavior for Scenario 2
"""

import requests
import json
import os
from datetime import datetime, timedelta

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://attend-deduct-hr.preview.emergentagent.com')
BASE_URL = f"{BACKEND_URL}/api"

class CriticalIssueAnalyzer:
    def __init__(self):
        self.session = requests.Session()
        self.super_admin_token = None
        self.findings = []
        
    def log_finding(self, category: str, issue: str, severity: str, details: str):
        """Log critical findings"""
        finding = {
            "category": category,
            "issue": issue,
            "severity": severity,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.findings.append(finding)
        print(f"🚨 {severity.upper()}: {category} - {issue}")
        print(f"   Details: {details}")
        
    def authenticate_super_admin(self) -> bool:
        """Authenticate as Super Admin"""
        try:
            response = self.session.post(
                f"{BASE_URL}/auth/login",
                json={"email": "admin@tanseeq.com", "password": "ADMIN"},
                timeout=30
            )
            
            if response.status_code == 200:
                self.super_admin_token = response.json()["access_token"]
                return True
            else:
                self.log_finding("Authentication", "Super Admin login failed", "CRITICAL", 
                               f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_finding("Authentication", "Super Admin login exception", "CRITICAL", str(e))
            return False
    
    def get_headers(self) -> dict:
        """Get authorization headers"""
        return {
            "Authorization": f"Bearer {self.super_admin_token}",
            "Content-Type": "application/json"
        }
    
    def analyze_attendance_records_structure(self):
        """Analyze the structure of existing attendance records"""
        print("\n🔍 ANALYZING ATTENDANCE RECORDS STRUCTURE")
        
        try:
            response = self.session.get(f"{BASE_URL}/attendance", headers=self.get_headers(), timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                records = data if isinstance(data, list) else data.get("attendance", [])
                
                print(f"Total attendance records found: {len(records)}")
                
                # Analyze field presence
                field_analysis = {
                    "late_minutes": 0,
                    "early_departure_minutes": 0,
                    "deducted_hours": 0,
                    "is_late": 0,
                    "check_in": 0,
                    "check_out": 0,
                    "working_hours": 0
                }
                
                late_tracking_issues = []
                
                for record in records:
                    if isinstance(record, dict):
                        # Count field presence
                        for field in field_analysis:
                            if field in record:
                                field_analysis[field] += 1
                        
                        # Check for 9:15 AM rule violations
                        check_in = record.get("check_in")
                        late_minutes = record.get("late_minutes", 0)
                        is_late = record.get("is_late", False)
                        
                        if check_in and ":" in check_in:
                            try:
                                time_parts = check_in.split(":")
                                hour = int(time_parts[0])
                                minute = int(time_parts[1])
                                
                                # Should be late if after 9:15 AM
                                should_be_late = hour > 9 or (hour == 9 and minute > 15)
                                
                                if should_be_late and late_minutes == 0:
                                    late_tracking_issues.append({
                                        "user_name": record.get("user_name", "Unknown"),
                                        "date": record.get("date", "Unknown"),
                                        "check_in": check_in,
                                        "late_minutes": late_minutes,
                                        "is_late": is_late,
                                        "expected_late_minutes": self.calculate_expected_late_minutes(hour, minute)
                                    })
                            except:
                                pass
                
                # Report field analysis
                print(f"\n📊 FIELD PRESENCE ANALYSIS:")
                for field, count in field_analysis.items():
                    percentage = (count / len(records)) * 100 if records else 0
                    print(f"  {field}: {count}/{len(records)} ({percentage:.1f}%)")
                    
                    if field in ["late_minutes", "early_departure_minutes", "deducted_hours"] and count == 0:
                        self.log_finding("Database Schema", f"Missing {field} field", "CRITICAL",
                                       f"0 out of {len(records)} records have the {field} field")
                
                # Report 9:15 AM rule violations
                if late_tracking_issues:
                    self.log_finding("9:15 AM Rule", "Late tracking not working", "CRITICAL",
                                   f"{len(late_tracking_issues)} records should be late but have late_minutes=0")
                    
                    print(f"\n🚨 9:15 AM RULE VIOLATIONS ({len(late_tracking_issues)} found):")
                    for issue in late_tracking_issues[:10]:  # Show first 10
                        print(f"  {issue['user_name']} on {issue['date']}: check_in={issue['check_in']}, "
                              f"late_minutes={issue['late_minutes']} (expected: {issue['expected_late_minutes']})")
                
                return len(late_tracking_issues) == 0
                
            else:
                self.log_finding("API Access", "Failed to get attendance records", "CRITICAL",
                               f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_finding("Analysis", "Exception during attendance analysis", "CRITICAL", str(e))
            return False
    
    def calculate_expected_late_minutes(self, hour: int, minute: int) -> int:
        """Calculate expected late minutes based on 9:15 AM rule"""
        if hour > 9 or (hour == 9 and minute > 15):
            # Calculate minutes after 9:15
            total_minutes = hour * 60 + minute
            threshold_minutes = 9 * 60 + 15  # 9:15 AM
            return total_minutes - threshold_minutes
        return 0
    
    def test_attendance_edit_functionality(self):
        """Test if attendance editing properly calculates and stores late_minutes"""
        print("\n🔍 TESTING ATTENDANCE EDIT FUNCTIONALITY")
        
        try:
            # Get an attendance record to edit
            response = self.session.get(f"{BASE_URL}/attendance", headers=self.get_headers(), timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                records = data if isinstance(data, list) else data.get("attendance", [])
                
                if records:
                    record = records[0]
                    attendance_id = record["id"]
                    original_check_in = record.get("check_in")
                    
                    print(f"Testing edit of record {attendance_id}")
                    print(f"Original check_in: {original_check_in}")
                    
                    # Edit to a time that should be late (09:30 = 15 minutes late)
                    edit_data = {"check_in": "09:30:00"}
                    
                    edit_response = self.session.put(
                        f"{BASE_URL}/attendance/{attendance_id}",
                        json=edit_data,
                        headers=self.get_headers(),
                        timeout=30
                    )
                    
                    if edit_response.status_code == 200:
                        print(f"Edit successful: {edit_response.json()}")
                        
                        # Get the updated record
                        updated_response = self.session.get(f"{BASE_URL}/attendance", headers=self.get_headers(), timeout=30)
                        
                        if updated_response.status_code == 200:
                            updated_data = updated_response.json()
                            updated_records = updated_data if isinstance(updated_data, list) else updated_data.get("attendance", [])
                            
                            # Find the updated record
                            updated_record = None
                            for r in updated_records:
                                if r.get("id") == attendance_id:
                                    updated_record = r
                                    break
                            
                            if updated_record:
                                new_check_in = updated_record.get("check_in")
                                new_late_minutes = updated_record.get("late_minutes", "MISSING")
                                new_is_late = updated_record.get("is_late")
                                
                                print(f"Updated check_in: {new_check_in}")
                                print(f"Updated late_minutes: {new_late_minutes}")
                                print(f"Updated is_late: {new_is_late}")
                                
                                # Check if late_minutes was calculated correctly
                                if new_check_in == "09:30:00":
                                    if new_late_minutes == "MISSING" or new_late_minutes == 0:
                                        self.log_finding("Attendance Edit", "late_minutes not calculated on edit", "CRITICAL",
                                                       f"Edited check_in to 09:30:00 but late_minutes is {new_late_minutes} (expected: 15)")
                                        return False
                                    elif new_late_minutes == 15:
                                        print("✅ late_minutes correctly calculated on edit")
                                        return True
                                    else:
                                        self.log_finding("Attendance Edit", "late_minutes incorrectly calculated", "HIGH",
                                                       f"Expected 15 minutes late, got {new_late_minutes}")
                                        return False
                                else:
                                    self.log_finding("Attendance Edit", "check_in not updated", "HIGH",
                                                   f"Expected 09:30:00, got {new_check_in}")
                                    return False
                            else:
                                self.log_finding("Attendance Edit", "Updated record not found", "HIGH",
                                               "Could not find the updated attendance record")
                                return False
                        else:
                            self.log_finding("Attendance Edit", "Failed to get updated records", "HIGH",
                                           f"Status: {updated_response.status_code}")
                            return False
                    else:
                        self.log_finding("Attendance Edit", "Edit request failed", "HIGH",
                                       f"Status: {edit_response.status_code}, Response: {edit_response.text}")
                        return False
                else:
                    self.log_finding("Attendance Edit", "No records to edit", "MEDIUM",
                                   "No attendance records available for testing")
                    return False
            else:
                self.log_finding("Attendance Edit", "Failed to get records for editing", "HIGH",
                               f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_finding("Attendance Edit", "Exception during edit test", "HIGH", str(e))
            return False
    
    def test_absence_creation(self):
        """Test absence record creation"""
        print("\n🔍 TESTING ABSENCE CREATION")
        
        try:
            # Get a user ID from existing records
            response = self.session.get(f"{BASE_URL}/employees/list", headers=self.get_headers(), timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                employees = data if isinstance(data, list) else data.get("employees", [])
                
                if employees:
                    employee = employees[0]
                    user_id = employee.get("id")
                    user_name = employee.get("name", "Test User")
                    
                    absence_data = {
                        "employee_id": user_id,
                        "employee_name": user_name,
                        "date": (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
                        "reason": "مرض",
                        "absence_type": "sick_leave"
                    }
                    
                    absence_response = self.session.post(
                        f"{BASE_URL}/attendance/create-absence",
                        json=absence_data,
                        headers=self.get_headers(),
                        timeout=30
                    )
                    
                    if absence_response.status_code in [200, 201]:
                        print(f"✅ Absence created successfully: {absence_response.json()}")
                        return True
                    else:
                        self.log_finding("Absence Creation", "Failed to create absence", "HIGH",
                                       f"Status: {absence_response.status_code}, Response: {absence_response.text}")
                        return False
                else:
                    self.log_finding("Absence Creation", "No employees found", "MEDIUM",
                                   "No employees available for absence creation test")
                    return False
            else:
                self.log_finding("Absence Creation", "Failed to get employee list", "HIGH",
                               f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_finding("Absence Creation", "Exception during absence test", "HIGH", str(e))
            return False
    
    def test_deductions_integration(self):
        """Test integration with deductions system"""
        print("\n🔍 TESTING DEDUCTIONS INTEGRATION")
        
        try:
            current_month = datetime.now().strftime('%Y-%m')
            
            response = self.session.post(
                f"{BASE_URL}/deductions/calculate-monthly?month={current_month}",
                headers=self.get_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Monthly deductions calculation successful")
                
                # Check if the response includes attendance-related deductions
                if isinstance(data, (list, dict)):
                    data_str = str(data).lower()
                    if "late" in data_str or "attendance" in data_str or "deduction" in data_str:
                        print("✅ Deductions system includes attendance data")
                        return True
                    else:
                        self.log_finding("Deductions Integration", "No attendance data in deductions", "MEDIUM",
                                       "Deductions calculation doesn't seem to include attendance-based deductions")
                        return False
                else:
                    self.log_finding("Deductions Integration", "Invalid deductions response", "HIGH",
                                   f"Unexpected response format: {type(data)}")
                    return False
            else:
                self.log_finding("Deductions Integration", "Deductions calculation failed", "HIGH",
                               f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_finding("Deductions Integration", "Exception during deductions test", "HIGH", str(e))
            return False
    
    def run_critical_analysis(self):
        """Run comprehensive critical issue analysis"""
        print("🚨 CRITICAL ISSUE ANALYSIS: 9:15 AM Late Tracking Rule")
        print("=" * 80)
        
        if not self.authenticate_super_admin():
            print("❌ Cannot proceed without Super Admin authentication")
            return False
        
        # Run all tests
        tests = [
            ("Attendance Records Structure", self.analyze_attendance_records_structure),
            ("Attendance Edit Functionality", self.test_attendance_edit_functionality),
            ("Absence Creation", self.test_absence_creation),
            ("Deductions Integration", self.test_deductions_integration)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed_tests += 1
                    print(f"✅ {test_name}: PASSED")
                else:
                    print(f"❌ {test_name}: FAILED")
            except Exception as e:
                print(f"💥 {test_name}: EXCEPTION - {str(e)}")
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 CRITICAL ANALYSIS SUMMARY")
        print("=" * 80)
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"Tests Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        # Critical findings summary
        critical_findings = [f for f in self.findings if f["severity"] == "CRITICAL"]
        high_findings = [f for f in self.findings if f["severity"] == "HIGH"]
        
        print(f"\n🚨 CRITICAL Issues: {len(critical_findings)}")
        print(f"⚠️ HIGH Priority Issues: {len(high_findings)}")
        
        if critical_findings:
            print(f"\n🚨 CRITICAL ISSUES FOUND:")
            for finding in critical_findings:
                print(f"  • {finding['category']}: {finding['issue']}")
                print(f"    {finding['details']}")
        
        if high_findings:
            print(f"\n⚠️ HIGH PRIORITY ISSUES:")
            for finding in high_findings:
                print(f"  • {finding['category']}: {finding['issue']}")
                print(f"    {finding['details']}")
        
        # Save detailed findings
        self.save_findings()
        
        # Determine overall status
        if len(critical_findings) > 0:
            print(f"\n🚨 OVERALL STATUS: CRITICAL ISSUES FOUND - SYSTEM NOT READY FOR PRODUCTION")
            return False
        elif len(high_findings) > 2:
            print(f"\n⚠️ OVERALL STATUS: MULTIPLE HIGH PRIORITY ISSUES - NEEDS ATTENTION")
            return False
        else:
            print(f"\n✅ OVERALL STATUS: SYSTEM FUNCTIONAL WITH MINOR ISSUES")
            return True
    
    def save_findings(self):
        """Save findings to evidence file"""
        try:
            evidence_dir = "/app/closure-evidence/network/scenario-02"
            os.makedirs(evidence_dir, exist_ok=True)
            
            findings_file = f"{evidence_dir}/critical_issues_analysis.json"
            with open(findings_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "analysis_summary": {
                        "total_findings": len(self.findings),
                        "critical_issues": len([f for f in self.findings if f["severity"] == "CRITICAL"]),
                        "high_priority_issues": len([f for f in self.findings if f["severity"] == "HIGH"]),
                        "timestamp": datetime.now().isoformat()
                    },
                    "detailed_findings": self.findings,
                    "backend_url": BACKEND_URL
                }, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Critical analysis saved to: {findings_file}")
            
        except Exception as e:
            print(f"⚠️ Failed to save findings: {str(e)}")

def main():
    """Main execution function"""
    analyzer = CriticalIssueAnalyzer()
    success = analyzer.run_critical_analysis()
    
    if success:
        print("\n🎉 Critical Analysis COMPLETED - System functional with acceptable issues")
        exit(0)
    else:
        print("\n🚨 Critical Analysis COMPLETED - CRITICAL ISSUES FOUND")
        exit(1)

if __name__ == "__main__":
    main()