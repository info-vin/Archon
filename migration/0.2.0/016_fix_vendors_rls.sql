-- Migration: 016_fix_vendors_rls.sql
-- Description: Enables RLS on vendors table and adds policies for authenticated users.
-- Fixes: Lead Promotion failures (Alice/Charlie inability to create vendors)
-- Date: 2026-01-29

-- 1. Enable RLS
ALTER TABLE vendors ENABLE ROW LEVEL SECURITY;

-- 2. Create Policies

-- Allow authenticated users to view vendors
DROP POLICY IF EXISTS "Allow authenticated users to select vendors" ON vendors;
CREATE POLICY "Allow authenticated users to select vendors" ON vendors
    FOR SELECT
    TO authenticated
    USING (true);

-- Allow authenticated users to insert vendors (e.g. promoting leads)
DROP POLICY IF EXISTS "Allow authenticated users to insert vendors" ON vendors;
CREATE POLICY "Allow authenticated users to insert vendors" ON vendors
    FOR INSERT
    TO authenticated
    WITH CHECK (true);

-- Allow authenticated users to update vendors
DROP POLICY IF EXISTS "Allow authenticated users to update vendors" ON vendors;
CREATE POLICY "Allow authenticated users to update vendors" ON vendors
    FOR UPDATE
    TO authenticated
    USING (true);

-- 3. Register Migration
INSERT INTO schema_migrations (version) VALUES ('016_fix_vendors_rls') ON CONFLICT (version) DO NOTHING;
