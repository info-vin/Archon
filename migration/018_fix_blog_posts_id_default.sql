-- Migration: 018_fix_blog_posts_id_default.sql
-- Description: Adds default gen_random_uuid() to blog_posts.id to fix creation error.
-- Fixes: "null value in column id violates not-null constraint"
-- Date: 2026-01-29

-- 1. Ensure pgcrypto is enabled (it should be, but good to be safe)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 2. Alter table to set default for id
ALTER TABLE blog_posts
ALTER COLUMN id SET DEFAULT gen_random_uuid();

-- 3. Ensure other columns have defaults if missing (based on schema review)
ALTER TABLE blog_posts
ALTER COLUMN created_at SET DEFAULT NOW(),
ALTER COLUMN updated_at SET DEFAULT NOW(),
ALTER COLUMN status SET DEFAULT 'draft';

-- Register Migration
INSERT INTO schema_migrations (version) VALUES ('018_fix_blog_posts_id_default') ON CONFLICT (version) DO NOTHING;
