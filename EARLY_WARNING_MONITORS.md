# Early-Warning Monitoring System

## Purpose
Proactive detection of critical issues before they impact production operations.

## Critical Monitors

### 1. Negative Net Salary Detection

**Purpose**: Alert when payroll calculation results in negative net salary
**Severity**: HIGH
**Implementation**:

```python
# Add to payroll_integration_engine.py

async def check_negative_salaries(cycle_id: str, db: AsyncIOMotorDatabase):
    """
    Monitor: Negative Net Salary Detection
    Alert when any employee has negative net salary in cycle
    """
    negative_salaries = []
    
    summaries = await db.employee_payroll_summaries.find({
        "payroll_cycle_id": cycle_id
    }).to_list(length=None)
    
    for summary in summaries:
        net_salary = summary.get("net_salary", 0)
        if net_salary < 0:
            negative_salaries.append({
                "employee_id": summary.get("employee_id"),
                "employee_name": summary.get("employee_name"),
                "gross_salary": summary.get("gross_salary"),
                "total_deductions": summary.get("total_deductions"),
                "net_salary": net_salary,
                "cycle_id": cycle_id,
                "cycle_month": summary.get("month")
            })
    
    if negative_salaries:
        # Log critical alert
        logger.critical(f"🚨 NEGATIVE SALARY ALERT: {len(negative_salaries)} employees")
        for emp in negative_salaries:
            logger.critical(f"  - {emp['employee_name']}: Net = {emp['net_salary']} AED")
        
        # Send notification to Super Admin
        await send_critical_alert(
            title="⚠️ تحذير: رواتب سالبة",
            message=f"يوجد {len(negative_salaries)} موظف براتب صافي سالب",
            details=negative_salaries
        )
    
    return negative_salaries
```

**Trigger Points**:
- After payroll recalculation
- Before cycle lock
- During salary slip generation

**Alert Recipients**: Super Admin, Finance Manager

---

### 2. Ledger-Payroll Discrepancy Monitor

**Purpose**: Detect mismatch between ledger entries and payroll summaries
**Severity**: CRITICAL
**Implementation**:

```python
async def verify_ledger_payroll_balance(cycle_id: str, db: AsyncIOMotorDatabase):
    """
    Monitor: Ledger-Payroll Balance Verification
    Ensures ledger totals match payroll summary totals
    """
    # Get payroll summary totals
    summaries = await db.employee_payroll_summaries.find({
        "payroll_cycle_id": cycle_id
    }).to_list(length=None)
    
    payroll_total = sum(s.get("net_salary", 0) for s in summaries)
    
    # Get ledger totals
    ledger_entries = await db.payroll_ledger.find({
        "cycle_id": cycle_id
    }).to_list(length=None)
    
    ledger_total = sum(e.get("amount", 0) for e in ledger_entries)
    
    # Calculate discrepancy
    discrepancy = abs(payroll_total - ledger_total)
    tolerance = 1.0  # 1 AED tolerance for rounding
    
    if discrepancy > tolerance:
        logger.critical(f"🚨 LEDGER DISCREPANCY ALERT: Cycle {cycle_id}")
        logger.critical(f"  Payroll Total: {payroll_total:.2f} AED")
        logger.critical(f"  Ledger Total: {ledger_total:.2f} AED")
        logger.critical(f"  Discrepancy: {discrepancy:.2f} AED")
        
        await send_critical_alert(
            title="⚠️ اختلاف في حسابات الرواتب",
            message=f"فرق {discrepancy:.2f} درهم بين الرواتب والقيود المحاسبية",
            details={
                "cycle_id": cycle_id,
                "payroll_total": payroll_total,
                "ledger_total": ledger_total,
                "discrepancy": discrepancy
            }
        )
        
        return False  # Validation failed
    
    return True  # Validation passed
```

**Trigger Points**:
- Before cycle lock
- After any manual adjustment
- Daily reconciliation job

**Alert Recipients**: Super Admin, Finance Manager, System Admin

---

### 3. Zero-KB Export Detection

**Purpose**: Detect failed export operations (empty files)
**Severity**: MEDIUM
**Implementation**:

```python
async def check_export_file_size(file_path: str, min_size: int = 1024):
    """
    Monitor: Export File Size Validation
    Ensures exports generate valid files (>1KB)
    """
    import os
    
    if not os.path.exists(file_path):
        logger.error(f"🚨 EXPORT ERROR: File not created: {file_path}")
        return False
    
    file_size = os.path.getsize(file_path)
    
    if file_size < min_size:
        logger.warning(f"⚠️ SMALL EXPORT FILE: {file_path} ({file_size} bytes)")
        
        await send_warning_alert(
            title="تحذير: ملف تصدير صغير",
            message=f"الملف {os.path.basename(file_path)} حجمه {file_size} بايت فقط",
            details={"file_path": file_path, "file_size": file_size}
        )
        
        return False
    
    logger.info(f"✅ Export file valid: {file_path} ({file_size} bytes)")
    return True

# Add to export endpoints
@app.get("/api/reports/attendance/export")
async def export_attendance_report(format: str):
    file_path = generate_attendance_report(format)
    
    # Monitor export file
    if not await check_export_file_size(file_path, min_size=2048):
        raise HTTPException(
            status_code=500, 
            detail="فشل تصدير التقرير - الملف فارغ"
        )
    
    return FileResponse(file_path)
```

**Trigger Points**:
- After every PDF/Excel export
- Scheduled export jobs

**Alert Recipients**: Super Admin, System Admin

---

### 4. High Error Rate Monitor (500 Errors)

**Purpose**: Detect spike in 500 Internal Server Errors
**Severity**: HIGH
**Implementation**:

```python
from collections import deque
from datetime import datetime, timedelta

class ErrorRateMonitor:
    def __init__(self, window_minutes=5, threshold=10):
        self.errors = deque()
        self.window = timedelta(minutes=window_minutes)
        self.threshold = threshold
    
    def record_error(self, endpoint: str, error: str):
        """Record 500 error occurrence"""
        self.errors.append({
            "timestamp": datetime.utcnow(),
            "endpoint": endpoint,
            "error": error
        })
        
        # Cleanup old errors
        cutoff = datetime.utcnow() - self.window
        while self.errors and self.errors[0]["timestamp"] < cutoff:
            self.errors.popleft()
        
        # Check threshold
        if len(self.errors) >= self.threshold:
            self.send_alert()
    
    async def send_alert(self):
        """Send alert when error threshold exceeded"""
        error_count = len(self.errors)
        endpoints = [e["endpoint"] for e in self.errors]
        most_common = max(set(endpoints), key=endpoints.count)
        
        logger.critical(f"🚨 HIGH ERROR RATE: {error_count} errors in {self.window.seconds//60} minutes")
        logger.critical(f"  Most affected endpoint: {most_common}")
        
        await send_critical_alert(
            title="⚠️ معدل أخطاء عالي",
            message=f"{error_count} خطأ في آخر {self.window.seconds//60} دقيقة",
            details={
                "error_count": error_count,
                "most_affected": most_common,
                "window_minutes": self.window.seconds // 60
            }
        )

# Global monitor instance
error_monitor = ErrorRateMonitor()

# Add to exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    endpoint = request.url.path
    await error_monitor.record_error(endpoint, str(exc))
    
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
```

**Trigger Points**:
- Every 500 error
- Real-time monitoring

**Alert Recipients**: System Admin, DevOps Team

---

### 5. Attendance Late Tracking Failure Monitor

**Purpose**: Detect when late tracking (9:15 AM rule) is not working
**Severity**: HIGH
**Implementation**:

```python
async def verify_late_tracking(db: AsyncIOMotorDatabase):
    """
    Monitor: Late Tracking Rule Verification
    Checks if late_minutes is being calculated correctly
    """
    # Get today's attendance records
    today = datetime.now().strftime("%Y-%m-%d")
    records = await db.attendance.find({
        "date": today,
        "check_in": {"$exists": True}
    }).to_list(length=None)
    
    violations = []
    
    for record in records:
        check_in = record.get("check_in")
        late_minutes = record.get("late_minutes", 0)
        
        if check_in and ":" in check_in:
            hour, minute = map(int, check_in.split(":")[:2])
            
            # Should be late if after 9:15
            should_be_late = hour > 9 or (hour == 9 and minute > 15)
            
            if should_be_late and late_minutes == 0:
                violations.append({
                    "user_name": record.get("user_name"),
                    "check_in": check_in,
                    "late_minutes": late_minutes,
                    "expected": "Should be late"
                })
    
    if violations:
        logger.warning(f"⚠️ LATE TRACKING ISSUE: {len(violations)} records")
        
        await send_warning_alert(
            title="تحذير: مشكلة في تتبع التأخير",
            message=f"{len(violations)} سجل حضور لم يحسب التأخير بشكل صحيح",
            details=violations
        )
        
        return False
    
    return True
```

**Trigger Points**:
- End of business day (6 PM)
- Before deductions calculation

**Alert Recipients**: HR Manager, System Admin

---

### 6. Database Connection Health Monitor

**Purpose**: Monitor MongoDB connection health
**Severity**: CRITICAL
**Implementation**:

```python
import asyncio

async def monitor_database_health():
    """
    Monitor: Database Connection Health
    Continuously checks MongoDB connection
    """
    while True:
        try:
            # Ping database
            await db.command("ping")
            logger.debug("✅ Database connection healthy")
            
        except Exception as e:
            logger.critical(f"🚨 DATABASE CONNECTION ERROR: {str(e)}")
            
            await send_critical_alert(
                title="⚠️ خطأ في الاتصال بقاعدة البيانات",
                message="فشل الاتصال بقاعدة البيانات MongoDB",
                details={"error": str(e)}
            )
        
        # Check every 60 seconds
        await asyncio.sleep(60)

# Start monitor on application startup
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(monitor_database_health())
```

**Trigger Points**:
- Continuous (every 60 seconds)

**Alert Recipients**: System Admin, DevOps Team

---

## Alert Notification System

### Implementation

```python
async def send_critical_alert(title: str, message: str, details: dict):
    """Send critical alert via multiple channels"""
    
    # 1. Create system notification
    await db.notifications.insert_one({
        "id": str(uuid.uuid4()),
        "recipient_role": "super_admin",
        "subject": title,
        "message": message,
        "type": "system_alert",
        "priority": "critical",
        "is_read": False,
        "requires_acknowledgment": True,
        "created_at": datetime.utcnow(),
        "details": details
    })
    
    # 2. Log to monitoring system
    logger.critical(f"ALERT: {title} - {message}")
    
    # 3. Send email (if configured)
    # await send_email_alert(title, message, details)
    
    # 4. Send SMS (if critical)
    # await send_sms_alert(title, message)

async def send_warning_alert(title: str, message: str, details: dict):
    """Send warning alert (less severe)"""
    
    await db.notifications.insert_one({
        "id": str(uuid.uuid4()),
        "recipient_role": "admin",
        "subject": title,
        "message": message,
        "type": "system_warning",
        "priority": "medium",
        "is_read": False,
        "created_at": datetime.utcnow(),
        "details": details
    })
    
    logger.warning(f"WARNING: {title} - {message}")
```

---

## Dashboard Integration

### Admin Dashboard Alerts Widget

```javascript
// frontend/src/components/AlertsWidget.js

import React, { useEffect, useState } from 'react';
import axios from 'axios';

const AlertsWidget = () => {
    const [alerts, setAlerts] = useState([]);
    
    useEffect(() => {
        const fetchAlerts = async () => {
            try {
                const response = await axios.get('/api/monitoring/alerts');
                setAlerts(response.data.alerts);
            } catch (error) {
                console.error('Failed to fetch alerts:', error);
            }
        };
        
        // Fetch alerts every 30 seconds
        fetchAlerts();
        const interval = setInterval(fetchAlerts, 30000);
        
        return () => clearInterval(interval);
    }, []);
    
    const getSeverityColor = (severity) => {
        switch(severity) {
            case 'CRITICAL': return 'bg-red-500';
            case 'HIGH': return 'bg-orange-500';
            case 'MEDIUM': return 'bg-yellow-500';
            default: return 'bg-blue-500';
        }
    };
    
    return (
        <div className="alerts-widget bg-white p-4 rounded shadow">
            <h3 className="text-lg font-bold mb-3">🔔 تحذيرات النظام</h3>
            
            {alerts.length === 0 ? (
                <p className="text-green-600">✅ لا توجد تحذيرات</p>
            ) : (
                <div className="space-y-2">
                    {alerts.map(alert => (
                        <div key={alert.id} 
                             className={`p-3 rounded ${getSeverityColor(alert.severity)} text-white`}>
                            <div className="font-bold">{alert.title}</div>
                            <div className="text-sm">{alert.message}</div>
                            <div className="text-xs mt-1">{alert.timestamp}</div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default AlertsWidget;
```

---

## Monitoring API Endpoints

```python
@app.get("/api/monitoring/alerts")
async def get_active_alerts(current_user: User = Depends(get_admin_user)):
    """Get active system alerts"""
    alerts = await db.notifications.find({
        "type": {"$in": ["system_alert", "system_warning"]},
        "is_read": False
    }).sort("created_at", -1).limit(10).to_list(length=None)
    
    return {"alerts": alerts}

@app.get("/api/monitoring/health")
async def system_health_check():
    """Comprehensive system health check"""
    health = {
        "status": "healthy",
        "checks": {
            "database": False,
            "payroll_service": False,
            "attendance_service": False
        },
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Check database
    try:
        await db.command("ping")
        health["checks"]["database"] = True
    except:
        health["status"] = "degraded"
    
    # Check payroll service
    try:
        cycles = await db.payroll_cycles.find().limit(1).to_list(length=1)
        health["checks"]["payroll_service"] = True
    except:
        health["status"] = "degraded"
    
    # Check attendance service
    try:
        attendance = await db.attendance.find().limit(1).to_list(length=1)
        health["checks"]["attendance_service"] = True
    except:
        health["status"] = "degraded"
    
    if health["status"] == "degraded":
        logger.warning("⚠️ System health degraded")
    
    return health
```

---

## Deployment Checklist

### Pre-Production
- [ ] All monitors implemented
- [ ] Alert notification system tested
- [ ] Dashboard alerts widget integrated
- [ ] Alert recipients configured
- [ ] Test alerts sent and received

### Post-Production (Day 1)
- [ ] Monitor all alerts for false positives
- [ ] Adjust thresholds if needed
- [ ] Verify alert notifications reaching recipients
- [ ] Test acknowledge/resolve flow

### Ongoing
- [ ] Weekly review of alerts
- [ ] Monthly tuning of thresholds
- [ ] Quarterly audit of monitoring coverage

---

## Status

**Implementation**: ✅ **Documentation Complete**
**Deployment**: ⏳ **Pending Integration**
**Testing**: ⏳ **Requires Production Data**

**Recommendation**: Implement monitors incrementally, starting with Critical severity monitors (Negative Salary, Ledger Discrepancy, Database Health).
