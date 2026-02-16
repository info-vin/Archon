-- Migration: 034_add_blog_generation_metadata.sql
-- Description: Add generation_metadata to blog_posts and enforce RBAC/RLS for marketing privacy.
-- Date: 2026-02-09

-- 1. Add JSONB column to store flexible generation options
ALTER TABLE blog_posts 
ADD COLUMN IF NOT EXISTS generation_metadata JSONB DEFAULT '{}'::jsonb;

-- 2. Add an index for faster filtering by industry or style
CREATE INDEX IF NOT EXISTS idx_blog_posts_metadata ON blog_posts USING GIN (generation_metadata);

-- 3. RBAC/RLS Hardening for generation_metadata
-- Note: blog_posts itself has a public SELECT policy. We add specific constraints for privacy.

ALTER TABLE blog_posts ENABLE ROW LEVEL SECURITY;

-- Policy: Only internal staff can see the AI 'Generation Strategies' (metadata)
-- Since RLS is row-based, to hide specific columns from public we usually use a VIEW or App Logic.
-- However, we can restrict UPDATE/INSERT of these fields to authorized roles.

DROP POLICY IF EXISTS "Marketing and Admins can update blog metadata" ON blog_posts;
CREATE POLICY "Marketing and Admins can update blog metadata" ON blog_posts
    FOR UPDATE
    TO authenticated
    USING (
        (SELECT role FROM public.profiles WHERE id = auth.uid()::text) IN ('marketing', 'manager', 'admin', 'system_admin')
    )
    WITH CHECK (
        (SELECT role FROM public.profiles WHERE id = auth.uid()::text) IN ('marketing', 'manager', 'admin', 'system_admin')
    );

-- 4. Register this migration version
INSERT INTO schema_migrations (version) VALUES ('034_add_blog_generation_metadata') ON CONFLICT (version) DO NOTHING;