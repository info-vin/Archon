-- Migration: Add status to blog_posts and extend leads table for Phase 4.4
-- Target: Bob (Marketing) & Alice (Sales)

-- 1. Update blog_posts for Kanban
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'blog_posts' AND column_name = 'status') THEN
        ALTER TABLE blog_posts ADD COLUMN status TEXT DEFAULT 'published';
    END IF;
END $$;

-- 2. Update leads for Sales Nexus
ALTER TABLE leads 
    ADD COLUMN IF NOT EXISTS contact_name TEXT,
    ADD COLUMN IF NOT EXISTS contact_email TEXT,
    ADD COLUMN IF NOT EXISTS contact_phone TEXT,
    ADD COLUMN IF NOT EXISTS next_followup_date TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS linked_project_id TEXT REFERENCES projects(id);

-- 3. Ensure uniqueness for crawler efficiency
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_leads_source_url') THEN
        CREATE UNIQUE INDEX idx_leads_source_url ON leads(source_job_url);
    END IF;
END $$;
