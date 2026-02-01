-- Migration: 020_phase46_schema.sql
-- Description: Phase 4.6 Schema - Mobile Ops, Market Intelligence, and Security Hardening
-- Date: 2026-01-30

-- =====================================================
-- SECTION 1: SECURITY HARDENING (RLS ENFORCEMENT)
-- =====================================================

-- 1.1 Hardening 'customers' table
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;

-- Policy: Allow Read Access for specific roles (Sales, Marketing, Manager, Admin)
DROP POLICY IF EXISTS "Allow authenticated read access" ON customers;
CREATE POLICY "Allow authenticated read access" ON customers
    FOR SELECT TO authenticated
    USING (true);

-- Policy: Allow Insert/Update for Sales, Managers, Admins (Write Access)
-- Note: Checking against auth.jwt() -> role claim or mapping table
DROP POLICY IF EXISTS "Allow write access for sales and management" ON customers;
CREATE POLICY "Allow write access for sales and management" ON customers
    FOR ALL
    USING (
        auth.jwt() ->> 'role' IN ('service_role') OR
        EXISTS (
            SELECT 1 FROM profiles
            WHERE id = auth.uid()::text
            AND role IN ('admin', 'manager', 'sales', 'system_admin')
        )
    );

-- 1.2 Hardening 'gemini_logs' table
ALTER TABLE gemini_logs ENABLE ROW LEVEL SECURITY;

-- Policy: Admins can view logs
DROP POLICY IF EXISTS "Allow admins to view gemini logs" ON gemini_logs;
CREATE POLICY "Allow admins to view gemini logs" ON gemini_logs
    FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM profiles
            WHERE id = auth.uid()::text
            AND role IN ('admin', 'system_admin', 'manager')
        )
    );

-- Policy: Allow insertions from authenticated users (Application logging)
DROP POLICY IF EXISTS "Allow app logging" ON gemini_logs;
CREATE POLICY "Allow app logging" ON gemini_logs
    FOR INSERT TO authenticated
    WITH CHECK (true);

-- 1.3 Hardening 'archon_logs' table (from 012)
ALTER TABLE archon_logs ENABLE ROW LEVEL SECURITY;

-- Policy: Admins can view logs
DROP POLICY IF EXISTS "Allow admins to view archon logs" ON archon_logs;
CREATE POLICY "Allow admins to view archon logs" ON archon_logs
    FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM profiles
            WHERE id = auth.uid()::text
            AND role IN ('admin', 'system_admin', 'manager')
        )
    );

-- Policy: Allow insertions (System services/Agents usually run as service_role, but for user-triggered events allow auth)
DROP POLICY IF EXISTS "Allow system logging" ON archon_logs;
CREATE POLICY "Allow system logging" ON archon_logs
    FOR INSERT TO authenticated
    WITH CHECK (true);


-- =====================================================
-- SECTION 2: NEW FEATURE TABLES
-- =====================================================

-- 2.1 Visit Logs (Mobile Field Ops)
CREATE TABLE IF NOT EXISTS visit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    customer_id UUID REFERENCES customers(id), -- Optional link to existing customer
    lead_id UUID REFERENCES leads(id),         -- Optional link to lead
    
    -- Location Data
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    location_address TEXT,
    
    -- Content
    voice_transcript TEXT,      -- Transcribed text from Gemini
    summary TEXT,               -- AI Generated summary
    follow_up_tasks TEXT[],     -- Extracted action items
    
    -- Media
    audio_url TEXT,             -- Path to stored audio file
    image_urls TEXT[],          -- Photos taken during visit
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS: Users see their own logs. Managers see team logs.
ALTER TABLE visit_logs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own visits" ON visit_logs;
CREATE POLICY "Users can view own visits" ON visit_logs
    FOR SELECT TO authenticated
    USING (
        auth.uid() = user_id OR
        EXISTS (
            SELECT 1 FROM profiles
            WHERE id = auth.uid()::text
            AND role IN ('admin', 'manager', 'system_admin')
        )
    );

DROP POLICY IF EXISTS "Users can insert own visits" ON visit_logs;
CREATE POLICY "Users can insert own visits" ON visit_logs
    FOR INSERT TO authenticated
    WITH CHECK (auth.uid() = user_id);

-- 2.2 Marketing Trends (Cache for Bob's Dash)
CREATE TABLE IF NOT EXISTS marketing_trends (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_date DATE NOT NULL DEFAULT CURRENT_DATE,
    trend_type TEXT NOT NULL, -- 'keyword_growth', 'sankey_flow', 'industry_need'
    data JSONB NOT NULL,      -- The actual dataset for Recharts
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS: Marketing, Manager, Admin can view
ALTER TABLE marketing_trends ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow marketing view" ON marketing_trends
    FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM profiles
            WHERE id = auth.uid()::text
            AND role IN ('marketing', 'manager', 'admin', 'system_admin')
        )
    );

-- 2.3 Subscriptions (Blog Subscribers)
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    lead_id UUID REFERENCES leads(id), -- If converted from a Lead
    status TEXT DEFAULT 'active',      -- active, unsubscribed
    tags TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;


-- =====================================================
-- SECTION 3: SCHEMA UPDATES
-- =====================================================

-- 3.1 Expand Leads Table for Enrichment Loop
ALTER TABLE leads 
ADD COLUMN IF NOT EXISTS enrichment_status TEXT DEFAULT 'pending', -- pending, success, failed
ADD COLUMN IF NOT EXISTS enrichment_score INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_enriched_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS auto_archived_reason TEXT; -- If automated pruning happens

-- Register Migration
INSERT INTO schema_migrations (version) VALUES ('020_phase46_schema') ON CONFLICT (version) DO NOTHING;
