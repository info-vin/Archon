-- Phase 5.9.7: Add category and metadata to archon_prompts

ALTER TABLE public.archon_prompts 
ADD COLUMN IF NOT EXISTS category text DEFAULT 'SYSTEM_AGENT';

ALTER TABLE public.archon_prompts 
ADD COLUMN IF NOT EXISTS metadata jsonb DEFAULT '{}'::jsonb;

-- Ensure that existing rows have the default values explicitly set if they were somehow inserted before this migration but after table creation
UPDATE public.archon_prompts 
SET category = 'SYSTEM_AGENT' WHERE category IS NULL;

UPDATE public.archon_prompts 
SET metadata = '{}'::jsonb WHERE metadata IS NULL;
