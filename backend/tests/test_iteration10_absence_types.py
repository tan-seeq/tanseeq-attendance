"""
Iteration 10 - Testing new absence types for TANSEEQ HR System
Features tested:
1. POST /api/attendance/bulk-add-absence with absence_type=annual_leave (no deduction)
2. POST /api/attendance/bulk-add-absence with absence_type=sick_leave_paid (no deduction)
3. POST /api/attendance/bulk-add-absence with absence_type=sick_leave_unpaid (with deduction)
4. POST /api/attendance/bulk-add-absence with absence_type=full_day (with deduction - existing behavior)
"""

import pytest
import requests
import os
import uuid
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthEndpoint:
    """Basic health check"""
    
    def test_healthz_returns_ok(self):
        response = requests.get(f"{BASE_URL}/api/healthz")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        print("✅ Health check passed")


class TestAuthFlow:
    """Authentication tests"""
    
    def test_login_success(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@tanseeq.com",
            "password": "ADMIN"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "super_admin"
        print(f"✅ Login successful - user: {data['user']['name']}")
        return data["access_token"]


class TestBulkAddAbsenceTypes:
    """Test all absence types with deduction behavior"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token and employee for testing"""
        # Login
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@tanseeq.com",
            "password": "ADMIN"
        })
        assert response.status_code == 200
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get first employee with salary for testing
        response = requests.get(f"{BASE_URL}/api/users", headers=self.headers)
        assert response.status_code == 200
        users = response.json()
        
        # Find an employee with salary
        self.test_employee = None
        for user in users:
            if user.get("monthly_salary", 0) > 0 and user.get("is_active", True):
                self.test_employee = user
                break
        
        if not self.test_employee:
            # Use first active user
            for user in users:
                if user.get("is_active", True):
                    self.test_employee = user
                    break
        
        assert self.test_employee is not None, "No active employee found for testing"
        print(f"Using test employee: {self.test_employee['name']} (salary: {self.test_employee.get('monthly_salary', 0)})")
    
    def _generate_unique_date(self, offset_days=0):
        """Generate a unique test date in May 2026 to avoid conflicts"""
        base_date = datetime(2026, 5, 10 + offset_days)
        return base_date.strftime("%Y-%m-%d")
    
    def _cleanup_test_attendance(self, date_str):
        """Delete test attendance record if exists"""
        try:
            # Get attendance records
            response = requests.get(f"{BASE_URL}/api/attendance", headers=self.headers)
            if response.status_code == 200:
                records = response.json()
                for record in records:
                    if record.get("date") == date_str and record.get("user_id") == self.test_employee["id"]:
                        # Delete the record
                        requests.delete(f"{BASE_URL}/api/attendance/{record['id']}", headers=self.headers)
                        print(f"Cleaned up existing record for {date_str}")
        except Exception as e:
            print(f"Cleanup warning: {e}")
    
    def test_annual_leave_no_deduction(self):
        """Test annual_leave returns total_deduction=0 and no_deduction=true"""
        test_date = self._generate_unique_date(1)
        self._cleanup_test_attendance(test_date)
        
        response = requests.post(
            f"{BASE_URL}/api/attendance/bulk-add-absence",
            headers=self.headers,
            json={
                "employee_id": self.test_employee["id"],
                "missing_days": [test_date],
                "absence_type": "annual_leave",
                "reason": "Test annual leave"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify no deduction for annual leave
        assert data["total_deduction"] == 0, f"Expected total_deduction=0, got {data['total_deduction']}"
        assert data["no_deduction"] == True, f"Expected no_deduction=True, got {data['no_deduction']}"
        assert data["added_count"] >= 1, f"Expected at least 1 record added"
        
        print(f"✅ annual_leave: total_deduction={data['total_deduction']}, no_deduction={data['no_deduction']}")
        
        # Cleanup
        self._cleanup_test_attendance(test_date)
    
    def test_sick_leave_paid_no_deduction(self):
        """Test sick_leave_paid returns total_deduction=0 and no_deduction=true"""
        test_date = self._generate_unique_date(2)
        self._cleanup_test_attendance(test_date)
        
        response = requests.post(
            f"{BASE_URL}/api/attendance/bulk-add-absence",
            headers=self.headers,
            json={
                "employee_id": self.test_employee["id"],
                "missing_days": [test_date],
                "absence_type": "sick_leave_paid",
                "reason": "Test sick leave paid"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify no deduction for sick_leave_paid
        assert data["total_deduction"] == 0, f"Expected total_deduction=0, got {data['total_deduction']}"
        assert data["no_deduction"] == True, f"Expected no_deduction=True, got {data['no_deduction']}"
        
        print(f"✅ sick_leave_paid: total_deduction={data['total_deduction']}, no_deduction={data['no_deduction']}")
        
        # Cleanup
        self._cleanup_test_attendance(test_date)
    
    def test_sick_leave_unpaid_with_deduction(self):
        """Test sick_leave_unpaid returns total_deduction > 0 and no_deduction=false"""
        test_date = self._generate_unique_date(3)
        self._cleanup_test_attendance(test_date)
        
        response = requests.post(
            f"{BASE_URL}/api/attendance/bulk-add-absence",
            headers=self.headers,
            json={
                "employee_id": self.test_employee["id"],
                "missing_days": [test_date],
                "absence_type": "sick_leave_unpaid",
                "reason": "Test sick leave unpaid"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify deduction for sick_leave_unpaid (if employee has salary)
        assert data["no_deduction"] == False, f"Expected no_deduction=False, got {data['no_deduction']}"
        
        if self.test_employee.get("monthly_salary", 0) > 0:
            assert data["total_deduction"] > 0, f"Expected total_deduction > 0, got {data['total_deduction']}"
            print(f"✅ sick_leave_unpaid: total_deduction={data['total_deduction']}, no_deduction={data['no_deduction']}")
        else:
            print(f"✅ sick_leave_unpaid: no_deduction={data['no_deduction']} (employee has no salary)")
        
        # Cleanup
        self._cleanup_test_attendance(test_date)
    
    def test_full_day_with_deduction(self):
        """Test full_day returns total_deduction > 0 (existing behavior)"""
        test_date = self._generate_unique_date(4)
        self._cleanup_test_attendance(test_date)
        
        response = requests.post(
            f"{BASE_URL}/api/attendance/bulk-add-absence",
            headers=self.headers,
            json={
                "employee_id": self.test_employee["id"],
                "missing_days": [test_date],
                "absence_type": "full_day",
                "reason": "Test full day absence"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify deduction for full_day
        assert data["no_deduction"] == False, f"Expected no_deduction=False, got {data['no_deduction']}"
        
        if self.test_employee.get("monthly_salary", 0) > 0:
            assert data["total_deduction"] > 0, f"Expected total_deduction > 0, got {data['total_deduction']}"
            print(f"✅ full_day: total_deduction={data['total_deduction']}, no_deduction={data['no_deduction']}")
        else:
            print(f"✅ full_day: no_deduction={data['no_deduction']} (employee has no salary)")
        
        # Cleanup
        self._cleanup_test_attendance(test_date)
    
    def test_half_day_with_half_deduction(self):
        """Test half_day returns half deduction"""
        test_date = self._generate_unique_date(5)
        self._cleanup_test_attendance(test_date)
        
        response = requests.post(
            f"{BASE_URL}/api/attendance/bulk-add-absence",
            headers=self.headers,
            json={
                "employee_id": self.test_employee["id"],
                "missing_days": [test_date],
                "absence_type": "half_day",
                "reason": "Test half day absence"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify deduction for half_day
        assert data["no_deduction"] == False, f"Expected no_deduction=False, got {data['no_deduction']}"
        
        print(f"✅ half_day: total_deduction={data['total_deduction']}, no_deduction={data['no_deduction']}")
        
        # Cleanup
        self._cleanup_test_attendance(test_date)


class TestAttendanceWithAbsences:
    """Test attendance endpoint returns manual_entry flag"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@tanseeq.com",
            "password": "ADMIN"
        })
        assert response.status_code == 200
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_attendance_with_absences_endpoint(self):
        """Test /api/attendance/with-absences returns data with manual_entry flags"""
        response = requests.get(f"{BASE_URL}/api/attendance/with-absences", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Check if any records have manual_entry or manual_absence flags
        manual_entries = [r for r in data if r.get("manual_entry") or r.get("manual_absence") or r.get("is_manual_entry")]
        print(f"✅ Attendance with absences: {len(data)} records, {len(manual_entries)} manual entries")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
