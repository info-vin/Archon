-- Migration: 033_add_review_notes_to_blog_posts.sql
-- Description: Add review_notes column to blog_posts table for Charlie's rejection feedback
-- Date: 2026-02-09

ALTER TABLE blog_posts
ADD COLUMN IF NOT EXISTS review_notes TEXT;

-- Register Migration
INSERT INTO schema_migrations (version) VALUES ('033_add_review_notes_to_blog_posts') ON CONFLICT (version) DO NOTHING;
