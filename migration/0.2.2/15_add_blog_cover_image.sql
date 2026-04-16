-- Phase 4.6.40: Physical Gap Closure
-- Add missing cover_image column to blog_posts for Nana Banana integration.

ALTER TABLE public.blog_posts ADD COLUMN IF NOT EXISTS cover_image TEXT;

COMMENT ON COLUMN public.blog_posts.cover_image IS 'AI generated cover image (Base64 or URL) from Nana Banana.';
