-- Migration: 035_create_crawler_targets_table.sql
-- Description: Physically separate Crawler URIs from LLM API Keys to prevent exposure in 3737 UI.
-- RLS: Manager can View, Admin can Manage.

-- 1. Create specialized table for Crawler Targets
CREATE TABLE IF NOT EXISTS public.archon_crawler_targets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    target_url TEXT NOT NULL UNIQUE,
    max_depth INTEGER DEFAULT 5,
    is_active BOOLEAN DEFAULT true,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 2. Enable RLS
ALTER TABLE public.archon_crawler_targets ENABLE ROW LEVEL SECURITY;

-- 3. Define Policies
-- SELECT: Admins and Managers
DROP POLICY IF EXISTS "Managers and Admins can view crawler targets" ON public.archon_crawler_targets;
CREATE POLICY "Managers and Admins can view crawler targets" ON public.archon_crawler_targets 
FOR SELECT USING (
    (SELECT role FROM public.profiles WHERE id = auth.uid()::text) IN ('admin', 'system_admin', 'manager')
);

-- ALL OPS: Admins only (David)
DROP POLICY IF EXISTS "Only Admins can manage crawler targets" ON public.archon_crawler_targets;
CREATE POLICY "Only Admins can manage crawler targets" ON public.archon_crawler_targets 
FOR ALL USING (
    (SELECT role FROM public.profiles WHERE id = auth.uid()::text) IN ('admin', 'system_admin')
);

-- 4. Seed initial data (Moving from settings)
INSERT INTO public.archon_crawler_targets (target_url, max_depth, description)
VALUES 
('https://www.104.com.tw', 5, 'Main recruitment target for Alice'),
('https://github.com', 3, 'Technical scouting target')
ON CONFLICT (target_url) DO NOTHING;

-- 5. Targeted Isolation: Hide only URI-based endpoints from 3737 API lists
-- Technical parameters like CRAWL_BATCH_SIZE will remain visible in 3737.
UPDATE public.archon_settings 
SET category = 'crawler_ops' 
WHERE key IN ('CRAWLER_104_SEARCH_API', 'CRAWLER_104_DETAIL_API');

-- 6. Register migration
INSERT INTO public.schema_migrations (version) VALUES ('035_create_crawler_targets_table') ON CONFLICT (version) DO NOTHING;
