-- Migration: 047_fix_blog_posts_lead_id
-- Description: Ensures lead_id exists in blog_posts for collab synergy analysis.

DO $$
BEGIN
    -- 1. Add lead_id column if missing
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'blog_posts' AND column_name = 'lead_id') THEN
        ALTER TABLE blog_posts ADD COLUMN lead_id UUID;
    END IF;

    -- 2. Add Foreign Key if missing
    IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name = 'fk_blog_posts_lead') THEN
        ALTER TABLE blog_posts ADD CONSTRAINT fk_blog_posts_lead FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE SET NULL;
    END IF;
END $$;

-- Register migration
INSERT INTO schema_migrations (version) VALUES ('047_fix_blog_posts_lead_id') ON CONFLICT (version) DO NOTHING;
