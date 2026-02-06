-- migration/026_create_extraction_schemas.sql

-- 1. Create Extraction Schemas Table
CREATE TABLE IF NOT EXISTS archon_extraction_schemas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    domain_pattern TEXT NOT NULL, -- URL pattern this schema applies to (e.g., "104.com.tw/job/*")
    schema_definition JSONB NOT NULL DEFAULT '{}'::jsonb, -- The fields to extract
    target_role TEXT, -- Optional: restrict this schema to specific roles (e.g., 'sales')
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Add RLS Policies
ALTER TABLE archon_extraction_schemas ENABLE ROW LEVEL SECURITY;

-- Everyone can view schemas (for applying them during crawl)
CREATE POLICY "Allow all authenticated users to view schemas" ON archon_extraction_schemas
    FOR SELECT
    USING (auth.role() = 'authenticated' OR auth.role() = 'service_role');

-- Only Managers and Admins can manage schemas
CREATE POLICY "Allow managers and admins to manage schemas" ON archon_extraction_schemas
    FOR ALL
    USING (
        auth.role() = 'service_role' OR 
        (SELECT role FROM profiles WHERE id = auth.uid()::text) IN ('manager', 'admin', 'system_admin')
    );

-- 3. Register migration
INSERT INTO schema_migrations (version) VALUES ('026_create_extraction_schemas') ON CONFLICT (version) DO NOTHING;
