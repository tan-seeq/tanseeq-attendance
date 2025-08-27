# 🚀 TANSEEQ Work Reports - Production Deployment Guide

## 📋 Pre-Deployment Checklist

### Environment Requirements
- [x] PostgreSQL 15+ server configured
- [x] Redis server for session management (optional)
- [x] SSL certificates for HTTPS
- [x] Domain/subdomain configured
- [x] Backup storage configured

### Security Requirements
- [x] Firewall rules configured
- [x] Database access restricted to application servers only
- [x] SSL/TLS encryption enabled
- [x] Security headers configured in reverse proxy

---

## 🔧 Environment Variables Configuration

### Backend (.env)
```bash
# Database Configuration
POSTGRES_HOST=your-postgres-server.com
POSTGRES_PORT=5432
POSTGRES_DB=work_reports_production
POSTGRES_USER=work_reports_user
POSTGRES_PASSWORD=your-super-secure-password

# Encryption Configuration
WORK_REPORTS_ENCRYPTION_KEY=your-256-bit-base64-encoded-encryption-key

# Application Configuration
SECRET_KEY=your-jwt-secret-key-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENVIRONMENT=production

# MongoDB (existing HR system - DO NOT CHANGE)
MONGO_URL=mongodb://your-mongo-server:27017
DB_NAME=tanseeq_hr

# Audit & Logging
LOG_LEVEL=INFO
AUDIT_LOG_RETENTION_DAYS=2555 # 7 years for compliance
```

### Frontend (.env.production)
```bash
REACT_APP_BACKEND_URL=https://your-production-domain.com
REACT_APP_ENVIRONMENT=production
GENERATE_SOURCEMAP=false
```

---

## 🔐 Security Key Generation

### 1. Encryption Key Generation
```bash
# Generate AES-256 encryption key
python3 -c "
import os, base64
key = os.urandom(32)  # 256 bits
encoded_key = base64.urlsafe_b64encode(key).decode()
print(f'WORK_REPORTS_ENCRYPTION_KEY={encoded_key}')
"
```

### 2. JWT Secret Key
```bash
# Generate secure JWT secret
openssl rand -base64 64
```

### 3. Database Password
```bash
# Generate secure database password
openssl rand -base64 32
```

---

## 💾 Database Setup

### 1. Create PostgreSQL Database
```sql
-- Connect as postgres superuser
CREATE USER work_reports_user WITH PASSWORD 'your-secure-password';
CREATE DATABASE work_reports_production OWNER work_reports_user;
GRANT ALL PRIVILEGES ON DATABASE work_reports_production TO work_reports_user;

-- Enable UUID extension
\c work_reports_production
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

### 2. Run Migrations
```bash
# Execute migration scripts in order
psql -h your-postgres-server -U work_reports_user -d work_reports_production -f migrations/001_create_work_reports_tables.sql

# Run seeders
psql -h your-postgres-server -U work_reports_user -d work_reports_production -f seeders/002_seed_default_data.sql
```

### 3. Database Security
```sql
-- Revoke unnecessary permissions
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON DATABASE work_reports_production FROM PUBLIC;

-- Create read-only user for reports
CREATE USER work_reports_readonly WITH PASSWORD 'readonly-password';
GRANT CONNECT ON DATABASE work_reports_production TO work_reports_readonly;
GRANT USAGE ON SCHEMA public TO work_reports_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO work_reports_readonly;
```

---

## 🔄 Key Rotation Policy

### Encryption Key Rotation (Quarterly)
```bash
# 1. Generate new encryption key
NEW_KEY=$(python3 -c "import os, base64; print(base64.urlsafe_b64encode(os.urandom(32)).decode())")

# 2. Update environment variable
# 3. Restart application with dual-key support
# 4. Migrate encrypted data to new key
# 5. Remove old key after migration
```

### JWT Secret Rotation (Monthly)
```bash
# 1. Generate new JWT secret
NEW_JWT_SECRET=$(openssl rand -base64 64)

# 2. Deploy new secret with grace period
# 3. Force re-authentication after 24 hours
```

### Database Password Rotation (Bi-annually)
```bash
# 1. Create new database user
# 2. Update application configuration
# 3. Test connectivity
# 4. Remove old database user
```

---

## 🚀 Deployment Steps

### 1. Backend Deployment
```bash
# Build and deploy backend
cd backend/
pip install -r requirements.txt
python -m uvicorn server:app --host 0.0.0.0 --port 8000 --workers 4

# Or using Docker
docker build -t tanseeq-work-reports-backend .
docker run -d --env-file .env.production -p 8000:8000 tanseeq-work-reports-backend
```

### 2. Frontend Deployment
```bash
# Build production frontend
cd frontend/
yarn install --frozen-lockfile
yarn build

# Deploy to web server (nginx example)
sudo cp -r build/* /var/www/work-reports/
sudo systemctl reload nginx
```

### 3. Database Migration
```bash
# Run database migrations
python manage.py migrate
python manage.py seed_data
```

---

## 📊 Monitoring & Health Checks

### Application Health Endpoints
```
GET /api/health           # Application health
GET /api/work-reports/dashboard  # Work reports module health
```

### Database Health Check
```sql
-- Check connection and basic functionality
SELECT 
    COUNT(*) as total_clients,
    (SELECT COUNT(*) FROM work_logs WHERE date >= CURRENT_DATE - INTERVAL '7 days') as recent_logs
FROM clients WHERE is_active = true;
```

### Log Monitoring
```bash
# Application logs
tail -f /var/log/tanseeq/work-reports.log

# Audit logs (security events)
tail -f /var/log/tanseeq/audit.log

# Database logs
tail -f /var/log/postgresql/postgresql.log
```

---

## 🛡️ Security Hardening

### 1. Network Security
- Database server accessible only from application servers
- Application server behind reverse proxy (nginx/Apache)
- SSL/TLS termination at proxy level
- Rate limiting configured
- IP whitelisting for admin functions

### 2. Application Security
- All passwords encrypted with AES-256-GCM
- JWT tokens with short expiration
- Role-based access control enforced
- Input validation and sanitization
- SQL injection protection via ORM

### 3. Audit Compliance
- All credential access logged
- Failed login attempts tracked
- Data modification audit trail
- Automated security alerts
- Regular security scans

---

## 📋 Post-Deployment Verification

### 1. Functional Tests
```bash
# Test API endpoints
curl -X GET "https://your-domain.com/api/health"
curl -X POST "https://your-domain.com/api/auth/login" -d '{"email":"test@example.com","password":"test"}'

# Test Work Reports module
curl -X GET "https://your-domain.com/api/work-reports/dashboard" -H "Authorization: Bearer TOKEN"
```

### 2. Security Tests
- [ ] SSL certificate valid and properly configured
- [ ] All HTTP redirects to HTTPS
- [ ] Security headers present (HSTS, CSP, etc.)
- [ ] Admin functions require proper authentication
- [ ] Credential decryption requires re-authentication

### 3. Performance Tests
- [ ] Page load times < 3 seconds
- [ ] API response times < 500ms
- [ ] Database query performance acceptable
- [ ] Memory usage within limits

---

## 🚨 Rollback Procedure

### Emergency Rollback
1. **Stop new deployments**
2. **Revert to previous application version**
3. **Restore database backup if needed**
4. **Update DNS if required**
5. **Notify stakeholders**

### Rollback Commands
```bash
# Rollback application
docker stop tanseeq-work-reports-backend
docker run -d tanseeq-work-reports-backend:previous-version

# Rollback database (if needed)
pg_restore -h server -U user -d work_reports_production backup_file.sql
```

---

## 📞 Support Information

### Critical Issues
- **Database Down**: Contact DB team immediately
- **Authentication Issues**: Check JWT secret and user permissions  
- **Encryption Errors**: Verify encryption key configuration
- **Performance Issues**: Check server resources and database connections

### Monitoring Alerts
- High error rates (>5%)
- Slow response times (>2s)
- Failed authentications (>10/hour)
- Database connection failures
- Disk space warnings (<20% free)

---

**⚠️ IMPORTANT SECURITY NOTES:**

1. **Never commit production secrets to version control**
2. **Rotate encryption keys quarterly**
3. **Monitor audit logs for suspicious activity**
4. **Backup encrypted data securely**
5. **Test disaster recovery procedures monthly**

---

*Last Updated: August 27, 2025*
*Deployment Version: 1.0.0*
*Security Clearance: Internal Use Only*