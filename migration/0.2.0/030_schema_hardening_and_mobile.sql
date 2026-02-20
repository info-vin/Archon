-- Consolidated Migration: 030_schema_hardening_and_mobile.sql
-- Covers: 031, 033, 034, 037, 039, 040, 045, 046, 047, 048
-- Purpose: Unified table schema changes for Mobile Ops, Blog Feedback, and System Auditing.

-- 1. Attendance & Visit Logs (Mobile Ops)
CREATE TABLE IF NOT EXISTS public.attendance_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    clock_in_time TIMESTAMPTZ NOT NULL DEFAULT now(),
    clock_out_time TIMESTAMPTZ,
    latitude FLOAT,
    longitude FLOAT,
    location_name TEXT,
    status TEXT NOT NULL CHECK (status IN ('PRESENT', 'AWAY', 'OFF_WORK', 'MOCK_PRESENT')), 
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_attendance_user_time ON public.attendance_logs(user_id, clock_in_time DESC);

DO $$ BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'visit_logs' AND column_name = 'visit_type') THEN
        ALTER TABLE public.visit_logs ADD COLUMN visit_type TEXT;
    END IF;
END $$;

-- 2. Blog Posts Enhancements
ALTER TABLE public.blog_posts 
ADD COLUMN IF NOT EXISTS review_notes TEXT,
ADD COLUMN IF NOT EXISTS generation_metadata JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS ai_score INTEGER DEFAULT 100,
ADD COLUMN IF NOT EXISTS lead_id UUID;

CREATE INDEX IF NOT EXISTS idx_blog_posts_metadata ON blog_posts USING GIN (generation_metadata);

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name = 'fk_blog_posts_lead') THEN
        ALTER TABLE blog_posts ADD CONSTRAINT fk_blog_posts_lead FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE SET NULL;
    END IF;
END $$;

-- 3. Leads Enhancements
ALTER TABLE public.leads ADD COLUMN IF NOT EXISTS pitch_content TEXT;

-- 4. Profiles Enhancements
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS permission_overrides JSONB DEFAULT '{}'::jsonb;

-- 5. Audit & Logs Hardening
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'archon_logs' AND COLUMN_NAME = 'user_id') THEN
        ALTER TABLE archon_logs ADD COLUMN user_id UUID;
        CREATE INDEX IF NOT EXISTS idx_archon_logs_user_id ON archon_logs(user_id);
    END IF;
END $$;

ALTER TABLE public.archon_document_versions 
DROP CONSTRAINT IF EXISTS chk_project_or_task,
DROP CONSTRAINT IF EXISTS chk_version_identity,
ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'approved';

ALTER TABLE public.archon_document_versions
ADD CONSTRAINT chk_version_identity 
CHECK (
    (project_id IS NOT NULL) OR (task_id IS NOT NULL) OR (document_id IS NOT NULL) OR
    (field_name IN ('sales_pitch', 'web_research', 'knowledge_file', 'system_prompt', 'system_setting'))
);

ALTER TABLE public.archon_ethics_events 
ADD COLUMN IF NOT EXISTS resolved BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS resolution_notes TEXT;

-- Register Migration
INSERT INTO schema_migrations (version) VALUES ('030_schema_hardening_and_mobile') ON CONFLICT (version) DO NOTHING;
