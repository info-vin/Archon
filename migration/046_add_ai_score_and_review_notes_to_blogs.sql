-- Migration: 046_add_ai_score_and_review_notes_to_blogs
-- Description: Adds persistent scoring and review notes to blog_posts for feedback loop.

-- 1. Add ai_score column
ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS ai_score INTEGER DEFAULT 100;

-- 2. Add review_notes column
ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS review_notes TEXT;

-- 3. Register this migration
INSERT INTO schema_migrations (version) VALUES ('046_add_ai_score_and_review_notes_to_blogs') ON CONFLICT (version) DO NOTHING;

-- 4. Comments for Clarity
COMMENT ON COLUMN blog_posts.ai_score IS 'AI-generated integrity score based on deduction logic.';
COMMENT ON COLUMN blog_posts.review_notes IS 'Feedback from Charlie (Manager) or AI reviewer for Bob (Marketing).';
