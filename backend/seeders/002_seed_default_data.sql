-- TANSEEQ Work Reports Database Seeder
-- Version: 002
-- Description: Seed default activity types and sample data
-- Date: 2025-08-27

USE work_reports_db;

-- Insert default activity types
INSERT INTO activity_types (name, name_ar, category, description, default_rate, is_billable, is_active) VALUES
('Tax Declaration Preparation', 'إعداد الإقرار الضريبي', 'tax', 'Preparation of various tax declarations', 150.00, TRUE, TRUE),
('VAT Return Filing', 'تقديم إقرار ضريبة القيمة المضافة', 'tax', 'Filing VAT returns with FTA', 200.00, TRUE, TRUE),
('Financial Statement Review', 'مراجعة القوائم المالية', 'accounting', 'Review and analysis of financial statements', 180.00, TRUE, TRUE),
('Client Meeting', 'اجتماع العميل', 'consulting', 'Meeting with client for consultation', 250.00, TRUE, TRUE),
('Document Review', 'مراجعة المستندات', 'legal', 'Review of legal and financial documents', 120.00, TRUE, TRUE),
('Administrative Tasks', 'المهام الإدارية', 'admin', 'General administrative work', 80.00, FALSE, TRUE),
('Audit Support', 'دعم التدقيق', 'audit', 'Support during external audits', 300.00, TRUE, TRUE),
('Compliance Review', 'مراجعة الامتثال', 'compliance', 'Regulatory compliance review', 220.00, TRUE, TRUE),
('Financial Planning', 'التخطيط المالي', 'consulting', 'Strategic financial planning sessions', 280.00, TRUE, TRUE),
('Training Session', 'جلسة تدريبية', 'training', 'Client staff training on procedures', 150.00, TRUE, TRUE)
ON CONFLICT (name) DO NOTHING;

-- Insert sample client (for demonstration)
INSERT INTO clients (
    company_name, 
    company_name_ar, 
    client_code, 
    industry, 
    contact_person, 
    phone, 
    email, 
    address, 
    tax_number, 
    commercial_registration,
    notes,
    created_by
) VALUES (
    'Test Client Company Ltd',
    'شركة العميل التجريبية المحدودة', 
    'TCL25086',
    'Technology',
    'Ahmed Al-Rashid',
    '+971501234567',
    'ahmed@testclient.ae',
    'Dubai Internet City, Dubai, UAE',
    '100123456789003',
    '1234567893',
    'Sample client for testing Work Reports system',
    'System Seeder'
) ON CONFLICT (client_code) DO NOTHING;

-- Insert sample work log (using the client and activity type created above)
INSERT INTO work_logs (
    client_id,
    activity_type_id,
    user_id,
    user_name,
    date,
    start_time,
    end_time,
    duration_minutes,
    description,
    notes,
    is_billable,
    hourly_rate,
    total_amount,
    status
) SELECT 
    c.id,
    at.id,
    'hatem-user-id',
    'Hatem Mohamed Ahmed',
    CURRENT_DATE,
    CURRENT_TIMESTAMP - INTERVAL '3 hours',
    CURRENT_TIMESTAMP - INTERVAL '30 minutes',
    150, -- 2.5 hours
    'Monthly VAT return preparation and filing for Q3 2025',
    'Client requested expedited processing due to deadline',
    TRUE,
    200.00,
    500.00, -- 150 minutes * 200 AED/hour / 60
    'active'
FROM clients c, activity_types at 
WHERE c.client_code = 'TCL25086' 
AND at.name = 'VAT Return Filing'
LIMIT 1
ON CONFLICT DO NOTHING;

-- Create audit log entry for seeding
INSERT INTO work_reports_audit_logs (user_id, user_name, action, table_name, after_value)
VALUES (
    'system', 
    'Database Seeder', 
    'seed_data', 
    'multiple', 
    '{
        "activity_types_created": 10,
        "sample_client_created": 1,
        "sample_work_log_created": 1,
        "seeder_version": "002"
    }'::jsonb
);

-- Verify seeded data counts
DO $$
DECLARE
    activity_count INTEGER;
    client_count INTEGER;
    log_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO activity_count FROM activity_types WHERE is_active = TRUE;
    SELECT COUNT(*) INTO client_count FROM clients WHERE is_active = TRUE;
    SELECT COUNT(*) INTO log_count FROM work_logs WHERE status = 'active';
    
    RAISE NOTICE 'Seeding completed successfully:';
    RAISE NOTICE 'Activity Types: %', activity_count;
    RAISE NOTICE 'Clients: %', client_count;
    RAISE NOTICE 'Work Logs: %', log_count;
END $$;

COMMIT;