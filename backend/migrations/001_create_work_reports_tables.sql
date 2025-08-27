-- TANSEEQ Work Reports Database Migration
-- Version: 001
-- Description: Create initial tables for Daily Work Report + Clients Master feature
-- Date: 2025-08-27

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS work_reports_db;
USE work_reports_db;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Clients table
CREATE TABLE IF NOT EXISTS clients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_name VARCHAR(255) NOT NULL,
    company_name_ar VARCHAR(255),
    client_code VARCHAR(50) UNIQUE,
    industry VARCHAR(100),
    contact_person VARCHAR(255),
    phone VARCHAR(50),
    email VARCHAR(255),
    address TEXT,
    tax_number VARCHAR(100),
    commercial_registration VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255)
);

-- 2. Client credentials table (AES-256-GCM encrypted passwords)
CREATE TABLE IF NOT EXISTS client_credentials (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    credential_type VARCHAR(100) NOT NULL, -- fta, ministry, bank, portal, etc.
    username VARCHAR(255),
    email VARCHAR(255),
    encrypted_password BYTEA, -- AES-256-GCM encrypted
    portal_url VARCHAR(500),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    last_used TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Activity types table
CREATE TABLE IF NOT EXISTS activity_types (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    name_ar VARCHAR(255), -- Arabic name
    category VARCHAR(100), -- tax, accounting, consulting, legal, etc.
    description TEXT,
    default_rate DECIMAL(10,2), -- Default hourly rate
    is_billable BOOLEAN DEFAULT TRUE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Work logs table
CREATE TABLE IF NOT EXISTS work_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id),
    activity_type_id UUID NOT NULL REFERENCES activity_types(id),
    user_id VARCHAR(255) NOT NULL, -- Reference to TANSEEQ HR user
    user_name VARCHAR(255) NOT NULL,
    date TIMESTAMP NOT NULL,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration_minutes INTEGER, -- Duration in minutes
    description TEXT NOT NULL,
    notes TEXT,
    is_billable BOOLEAN DEFAULT TRUE,
    hourly_rate DECIMAL(10,2),
    total_amount DECIMAL(10,2), -- duration * rate
    status VARCHAR(50) DEFAULT 'active', -- active, invoiced, cancelled
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Audit logs table for security tracking
CREATE TABLE IF NOT EXISTS work_reports_audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    user_name VARCHAR(255) NOT NULL,
    action VARCHAR(100) NOT NULL, -- create, update, delete, view, export
    table_name VARCHAR(100), -- clients, work_logs, etc.
    record_id VARCHAR(255),
    before_value JSONB,
    after_value JSONB,
    ip_address VARCHAR(50),
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_clients_company_name ON clients(company_name);
CREATE INDEX IF NOT EXISTS idx_clients_client_code ON clients(client_code);
CREATE INDEX IF NOT EXISTS idx_clients_is_active ON clients(is_active);

CREATE INDEX IF NOT EXISTS idx_client_credentials_client_id ON client_credentials(client_id);
CREATE INDEX IF NOT EXISTS idx_client_credentials_type ON client_credentials(credential_type);

CREATE INDEX IF NOT EXISTS idx_activity_types_category ON activity_types(category);
CREATE INDEX IF NOT EXISTS idx_activity_types_is_active ON activity_types(is_active);

CREATE INDEX IF NOT EXISTS idx_work_logs_client_id ON work_logs(client_id);
CREATE INDEX IF NOT EXISTS idx_work_logs_user_id ON work_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_work_logs_date ON work_logs(date);
CREATE INDEX IF NOT EXISTS idx_work_logs_status ON work_logs(status);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON work_reports_audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON work_reports_audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON work_reports_audit_logs(timestamp);

-- Add update trigger for updated_at columns
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_clients_updated_at BEFORE UPDATE ON clients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_client_credentials_updated_at BEFORE UPDATE ON client_credentials
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_work_logs_updated_at BEFORE UPDATE ON work_logs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Migration completed successfully
INSERT INTO work_reports_audit_logs (user_id, user_name, action, table_name, after_value)
VALUES ('system', 'Database Migration', 'migration_001', 'schema', '{"version": "001", "description": "Initial work reports tables created"}');

COMMIT;