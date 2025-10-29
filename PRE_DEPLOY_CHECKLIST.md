# Pre-Deploy Checklist - TANSEEQ HR v1.0.0

## ✅ Completed by AI Agent

### 1. Database Backup
- [x] Full MongoDB backup created: `/app/backups/pre_deploy_20251008_043539/`
- [x] Backup size: 1.2MB
- [x] Collections backed up: 40+ collections
- [ ] **TODO (User):** Test restore procedure before deployment

### 2. Test Data Cleanup
- [x] QA_* clients: 0 found, 0 deleted
- [x] QA test visits: 0 found, 0 deleted  
- [x] QA test logs: 0 found, 0 deleted
- [x] QA test deductions: 0 found, 0 deleted
- [x] Database is clean ✅

### 3. Documentation
- [x] CHANGELOG created: `/app/CHANGELOG_v1.0.0.md`
- [x] Defect log: `/app/evidence/defect_log.md`
- [x] Final QA report: `/app/evidence/FINAL_QA_REPORT.md`
- [x] Unresolved issues: `/app/defects_unresolved.md`
- [x] Future roadmap: `/app/roadmap.md`

---

## ⚠️ REQUIRES USER ACTION

### 4. Environment Variables Review

**Current Backend ENV:**
```bash
MONGO_URL="mongodb://localhost:27017"
DB_NAME="tanseeq_hr"
SECRET_KEY="tanseeq-secret-key-2025-very-secure-key"  # ⚠️ CHANGE FOR PRODUCTION
ADMIN_PASSWORD="hatem123"  # ⚠️ CHANGE FOR PRODUCTION
```

**Current Frontend ENV:**
```bash
REACT_APP_BACKEND_URL=https://attendance-calc-4.preview.emergentagent.com  # ⚠️ UPDATE TO PRODUCTION URL
```

**🔴 CRITICAL - Must Change for Production:**
- [ ] `SECRET_KEY` - Generate new strong secret key (min 32 chars)
- [ ] `ADMIN_PASSWORD` - Change from default
- [ ] `REACT_APP_BACKEND_URL` - Update to production URL
- [ ] `MONGO_URL` - Verify production MongoDB connection string

**Recommended Production Values:**
```bash
# Generate strong secret key:
SECRET_KEY="$(openssl rand -base64 32)"

# Or use: https://randomkeygen.com/
```

### 5. Test Account Security

**⚠️ SECURITY CRITICAL:**

Current test account: `admin@tanseeq.com` / `ADMIN`

**Options:**
- [ ] **Option A:** Change password to strong password (min 12 chars, mixed case, numbers, symbols)
- [ ] **Option B:** Disable account in production
- [ ] **Option C:** Restrict to audit-only access

**To change password:**
```javascript
// Run in MongoDB shell:
use tanseeq_hr
db.users.updateOne(
  { email: "admin@tanseeq.com" },
  { $set: { 
    password: "NEW_HASHED_PASSWORD_HERE",  // Use bcrypt hash
    updated_at: new Date().toISOString()
  }}
)
```

### 6. MFA (Multi-Factor Authentication)

**⚠️ NOT IMPLEMENTED YET**

MFA is not currently implemented in the application. This is a **HIGH PRIORITY** future enhancement.

**Recommended for v1.1.0:**
- [ ] Add TOTP-based MFA
- [ ] Require MFA for Super Admin accounts
- [ ] SMS/Email backup codes

**Workaround for now:**
- Use very strong passwords (20+ characters)
- Implement IP whitelist if possible
- Monitor login activity logs

---

## 📋 Schema/Migrations

### Current State
- [x] No pending migrations
- [x] MongoDB collections stable
- [x] Indexes in place for payroll_cycles, employee_payroll_summaries, installment_schedules
- [x] All data integrity verified

### Collections Summary
```
Total Collections: 40+
Critical Collections:
  - users (8 users)
  - payroll_cycles (6 cycles)
  - employee_payroll_summaries (36 summaries)
  - installment_schedules (12 schedules)
  - payroll_deductions (20 deductions)
  - payroll_line_items (linked)
```

**No migrations needed for v1.0.0 deployment** ✅

---

## 🚀 Deployment Steps (User Must Execute)

### Step 1: Save to GitHub
```bash
# In Emergent UI:
1. Click "Save to GitHub" button
2. Commit message: "Release v1.0.0 - Production ready"
3. Create tag: v1.0.0-prod
```

### Step 2: Update Environment Variables
```bash
# In Emergent deployment settings:
1. Update REACT_APP_BACKEND_URL to production URL
2. Update SECRET_KEY to new strong value
3. Update ADMIN_PASSWORD
4. Save changes
```

### Step 3: Deploy
```bash
# In Emergent UI:
1. Click "Deploy" button
2. Select environment: Production
3. Confirm deployment
4. Wait ~10 minutes
```

### Step 4: Post-Deploy Smoke Test (15 minutes)

**Test the following in order:**

#### 4.1 Dashboard
- [ ] Navigate to `/dashboard`
- [ ] Page loads without errors (<3 seconds)
- [ ] No console errors (F12)
- [ ] Sidebar displays correctly (RTL)

#### 4.2 Payroll System
- [ ] Navigate to `/payroll-cycles`
- [ ] Verify cycles display (should show 6 cycles)
- [ ] Click "عرض" (View) button on a cycle
- [ ] Navigate to `/payroll-summary/:id`
- [ ] Verify employee summaries display
- [ ] Verify deductions appear (not 0.00)
- [ ] Click "حساب الرواتب" (Calculate) - verify success
- [ ] Click "قفل الدورة" (Lock) - enter reason (min 10 chars) - verify success
- [ ] Click "فتح الدورة" (Unlock) - enter reason - verify success
- [ ] Click "PDF" export - verify file downloads and opens
- [ ] Click "Excel" export - verify file downloads
- [ ] Verify totals match between screen and exports (1:1)

#### 4.3 Attendance Deductions
- [ ] Navigate to `/attendance-deductions`
- [ ] Verify employee names visible (Arabic names, not IDs)
- [ ] Click "+ خصم جديد" (New Deduction)
- [ ] Fill form: Select employee, Amount: 100, Reason: "Test"
- [ ] Save - verify success message
- [ ] Try creating deduction with Amount: 0 - **Should fail** with error message
- [ ] Edit the created deduction
- [ ] Delete the test deduction
- [ ] Navigate back to payroll and verify deduction reflected

#### 4.4 Reports
- [ ] Navigate to `/reports`
- [ ] Generate attendance report for current month
- [ ] Export PDF - verify download and content
- [ ] Export Excel - verify download
- [ ] Verify totals match screen display

#### 4.5 Sidebar & Navigation
- [ ] Scroll through sidebar menu
- [ ] Verify 3cm empty space at bottom
- [ ] Click different menu items
- [ ] Verify active page highlighting works
- [ ] Verify Arabic text displays correctly (RTL)

#### 4.6 Work Reports
- [ ] Navigate to work reports/logs page
- [ ] Test date filter - verify results
- [ ] Test search - verify results
- [ ] Test pagination - verify pages change
- [ ] All requests return 200 OK

#### 4.7 Notifications
- [ ] Login as employee: `jihad@tanseeq.com` / `jihad123`
- [ ] Check for notification modal
- [ ] Click "تأكيد الاطلاع" - **Should work without error**
- [ ] Verify notification clears
- [ ] Check notification badge updates

**🎯 Success Criteria:** All checkboxes above must pass

---

## 📊 Monitoring Setup (Post-Deploy)

### Emergent Platform (Built-in)
- [x] Access logs via Emergent dashboard
- [x] Basic uptime monitoring available

### External Tools (Recommended)
- [ ] **UptimeRobot** - Free tier for uptime monitoring
  - Setup: https://uptimerobot.com
  - Monitor: Production URL
  - Alert: Email/SMS on downtime
  
- [ ] **Sentry** - Error tracking
  - Setup: https://sentry.io
  - Install: `yarn add @sentry/react`
  - Config: Add DSN to environment
  
- [ ] **LogRocket** - Session replay (optional)
  - Setup: https://logrocket.com
  - Useful for debugging user issues

### Alert Thresholds
Set up alerts for:
- [ ] Error rate > 1% over 10 minutes
- [ ] Response time P95 > 800ms
- [ ] Export failures > 3 consecutive
- [ ] Database connection failures

---

## 🔄 Rollback Plan

**If critical issues occur post-deployment:**

### Option 1: Emergent Rollback Feature
```bash
1. Open Emergent dashboard
2. Navigate to deployment history
3. Click "Rollback" to previous stable version
4. Confirm rollback
```

### Option 2: Manual Revert
```bash
1. In GitHub, revert to previous tag
2. Deploy from previous commit
3. If needed, restore database backup:
   mongorestore --uri="mongodb://PROD_URL" /path/to/backup
```

### When to Rollback
- Critical functionality broken (payroll calculation, authentication)
- Error rate > 5%
- Data corruption detected
- Security vulnerability discovered

---

## 📁 Archive & Documentation

### Files to Archive
- [x] `/app/evidence/FINAL_QA_REPORT.md`
- [x] `/app/evidence/defect_log.md`
- [x] `/app/evidence/coverage_matrix.csv`
- [x] `/app/CHANGELOG_v1.0.0.md`
- [x] `/app/PRE_DEPLOY_CHECKLIST.md` (this file)
- [x] `/app/backups/pre_deploy_20251008_043539/` (1.2MB)

### Archive Location
**Recommended:** Create release folder in project:
```bash
mkdir -p releases/v1.0.0/
cp -r /app/evidence releases/v1.0.0/
cp /app/CHANGELOG_v1.0.0.md releases/v1.0.0/
cp /app/PRE_DEPLOY_CHECKLIST.md releases/v1.0.0/
```

---

## ✅ Final Checklist

### Before Clicking "Deploy"
- [ ] Database backup created and verified
- [ ] QA data cleaned
- [ ] Environment variables updated for production
- [ ] Admin password changed
- [ ] SECRET_KEY updated
- [ ] REACT_APP_BACKEND_URL updated
- [ ] Changelog reviewed
- [ ] Smoke test plan understood
- [ ] Rollback plan ready
- [ ] Monitoring tools configured
- [ ] Team notified about deployment window

### After Deployment
- [ ] Smoke tests passed (15 min)
- [ ] Error logs reviewed (first 30 min)
- [ ] Performance metrics normal
- [ ] User acceptance testing (if applicable)
- [ ] Archive documentation
- [ ] Update internal wiki/docs

---

## 🎯 Deployment Readiness: 85%

### Ready ✅
- Code stability
- Testing coverage
- Bug fixes
- Documentation

### Pending ⚠️
- Environment variables update (User action)
- Password changes (User action)
- External monitoring setup (User action)

### Not Available (Platform Limitations)
- MFA (not implemented - future v1.1.0)
- Feature Flags (not needed for v1.0.0)
- CDN Invalidation (Emergent doesn't use CDN)
- Canary Deployment (Emergent doesn't support)

---

**🚀 STATUS: READY FOR DEPLOYMENT AFTER USER COMPLETES PENDING TASKS**

*Generated: October 8, 2025*
*Platform: Emergent*
*Release: v1.0.0-prod*
