-- Consolidated Migration: 031_rbac_and_policies_refinement.sql
-- Covers: 032, 035, 036, (Policies from 031, 034)
-- Purpose: Unified RBAC flags and RLS policies for settings, prompts, and tokens.

-- 1. RBAC Flags
ALTER TABLE public.archon_prompts ADD COLUMN IF NOT EXISTS is_system_protected BOOLEAN DEFAULT false;
ALTER TABLE public.archon_settings ADD COLUMN IF NOT EXISTS is_system_protected BOOLEAN DEFAULT false;

UPDATE public.archon_prompts SET is_system_protected = false;
UPDATE public.archon_settings SET is_system_protected = true 
WHERE key IN ('SUPABASE_URL', 'SUPABASE_SERVICE_KEY', 'GEMINI_API_KEY', 'GOOGLE_API_KEY', 'ANTHROPIC_API_KEY', 'OPENAI_API_KEY');

-- 2. RLS Enablement
ALTER TABLE public.attendance_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.archon_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.archon_prompts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.blog_posts ENABLE ROW LEVEL SECURITY;

-- 3. Unified Policies
-- Attendance
DROP POLICY IF EXISTS "Users can view own attendance" ON public.attendance_logs;
CREATE POLICY "Users can view own attendance" ON public.attendance_logs FOR SELECT USING (auth.uid() = user_id);
DROP POLICY IF EXISTS "Users can insert own attendance" ON public.attendance_logs;
CREATE POLICY "Users can insert own attendance" ON public.attendance_logs FOR INSERT WITH CHECK (auth.uid() = user_id);
DROP POLICY IF EXISTS "Users can update own attendance" ON public.attendance_logs;
CREATE POLICY "Users can update own attendance" ON public.attendance_logs FOR UPDATE USING (auth.uid() = user_id);

-- Tokens
DROP POLICY IF EXISTS "Managers can view all token usage" ON public.archon_token_usage;
CREATE POLICY "Managers can view all token usage" ON public.archon_token_usage FOR SELECT USING (
    EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid()::text AND role = 'manager')
);

-- Prompts
DROP POLICY IF EXISTS "Admins can update all prompts" ON public.archon_prompts;
CREATE POLICY "Admins can update all prompts" ON public.archon_prompts FOR UPDATE USING (
    (SELECT role FROM public.profiles WHERE id = auth.uid()::text) IN ('system_admin', 'admin')
);
DROP POLICY IF EXISTS "Managers can update business prompts" ON public.archon_prompts;
CREATE POLICY "Managers can update business prompts" ON public.archon_prompts FOR UPDATE USING (
    (SELECT role FROM public.profiles WHERE id = auth.uid()::text) = 'manager' AND is_system_protected = false
);

-- Settings
DROP POLICY IF EXISTS "Admin can update everything" ON public.archon_settings;
CREATE POLICY "Admin can update everything" ON public.archon_settings FOR UPDATE USING (
    (SELECT role FROM public.profiles WHERE id = auth.uid()::text) IN ('system_admin', 'admin')
);
DROP POLICY IF EXISTS "Manager can update non-protected settings" ON public.archon_settings;
CREATE POLICY "Manager can update non-protected settings" ON public.archon_settings FOR UPDATE USING (
    (SELECT role FROM public.profiles WHERE id = auth.uid()::text) = 'manager' AND is_system_protected = false
);

-- Blog Metadata
DROP POLICY IF EXISTS "Marketing and Admins can update blog metadata" ON public.blog_posts;
CREATE POLICY "Marketing and Admins can update blog metadata" ON public.blog_posts FOR UPDATE USING (
    (SELECT role FROM public.profiles WHERE id = auth.uid()::text) IN ('marketing', 'manager', 'admin', 'system_admin')
);

-- Register Migration
INSERT INTO schema_migrations (version) VALUES ('031_rbac_and_policies_refinement') ON CONFLICT (version) DO NOTHING;
