-- migration/022_add_blog_lead_relation.sql
-- Description: Connect Blog Posts to Sales Leads and enable Bob's Content Loop
-- Date: 2026-02-02

-- 1. Add columns to blog_posts for traceability and operations
ALTER TABLE blog_posts 
ADD COLUMN IF NOT EXISTS source_lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS publish_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS target_brand TEXT DEFAULT 'Archon';

COMMENT ON COLUMN blog_posts.source_lead_id IS 'The sales lead that inspired this content (Traceability)';
COMMENT ON COLUMN blog_posts.target_brand IS 'Brand channel (e.g., Archon, Nano, Banana)';

-- 2. Update RLS for visit_logs to allow Marketing to read specific logs
-- This is necessary because 020 restricted visit_logs to owner/admin/manager/sales
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'visit_logs' AND policyname = 'Marketing view story logs'
    ) THEN
        CREATE POLICY "Marketing view story logs" ON visit_logs
        FOR SELECT
        TO authenticated
        USING (
            EXISTS (
                SELECT 1 FROM leads 
                WHERE leads.id = visit_logs.lead_id 
                AND (leads.status = 'WON' OR leads.enrichment_score >= 80)
            )
            AND (
                auth.jwt() ->> 'role' = 'marketing' OR 
                EXISTS (
                    SELECT 1 FROM profiles 
                    WHERE id = auth.uid()::text AND role = 'marketing'
                )
            )
        );
    END IF;
END $$;

-- 3. Update RLS for leads (Explicit policy for Marketing context)
-- Note: While a permissive policy exists, this explicitly defines Marketing's authorized view
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'leads' AND policyname = 'Marketing view story candidates'
    ) THEN
        CREATE POLICY "Marketing view story candidates" ON leads
        FOR SELECT
        TO authenticated
        USING (
            (
                auth.jwt() ->> 'role' = 'marketing' OR 
                EXISTS (
                    SELECT 1 FROM profiles 
                    WHERE id = auth.uid()::text AND role = 'marketing'
                )
            )
            AND (status = 'WON' OR enrichment_score >= 80)
        );
    END IF;
END $$;

-- 4. Register Migration
INSERT INTO schema_migrations (version) VALUES ('022_add_blog_lead_relation') ON CONFLICT (version) DO NOTHING;
