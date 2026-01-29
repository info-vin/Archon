-- Migration: 019_add_prompts_rls.sql
-- Description: Adds RLS policies for archon_prompts table.
-- Fixes: "prompt 需要哪些supasbase RLS 表?"
-- Date: 2026-01-29

-- 1. Enable RLS on archon_prompts (if not already)
ALTER TABLE archon_prompts ENABLE ROW LEVEL SECURITY;

-- 2. Drop existing policies to avoid conflicts
DROP POLICY IF EXISTS "Enable read access for all authenticated users" ON archon_prompts;
DROP POLICY IF EXISTS "Enable write access for admins" ON archon_prompts;

-- 3. Create Policy: Authenticated users (including Agents) can READ prompts
CREATE POLICY "Enable read access for all authenticated users"
ON archon_prompts FOR SELECT
TO authenticated
USING (true);

-- 4. Create Policy: Only System Admins can MODIFY prompts
-- Note: 'system_admin' role check depends on how role is stored. 
-- Using generic 'authenticated' for now or 'service_role' (which bypasses RLS) is safer if we don't have JWT claims set up perfectly.
-- For Admin UI (User), they are 'authenticated'. We should strictly check for admin role if possible,
-- but typically Admin UI operations might use Service Role or we rely on App Logic.
-- Let's allow update for authenticated for now, or check public.profiles if we want strictness.
-- Ideally:
-- USING (auth.uid() IN (SELECT id FROM public.profiles WHERE role IN ('system_admin', 'admin')))

CREATE POLICY "Enable write access for admins"
ON archon_prompts FOR UPDATE
TO authenticated
USING (
  exists (
    select 1 from public.profiles
    where profiles.id = auth.uid()
    and profiles.role in ('system_admin', 'admin')
  )
)
WITH CHECK (
  exists (
    select 1 from public.profiles
    where profiles.id = auth.uid()
    and profiles.role in ('system_admin', 'admin')
  )
);

-- Register Migration
INSERT INTO schema_migrations (version) VALUES ('019_add_prompts_rls') ON CONFLICT (version) DO NOTHING;
