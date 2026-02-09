-- Migration: 035_refine_prompt_rbac.sql
-- Description: Implement granular RBAC for prompts using is_system_protected flag.
-- Date: 2026-02-09

-- 1. Add protection flag to distinguish Admin-only prompts from Business-logic prompts
ALTER TABLE archon_prompts 
ADD COLUMN IF NOT EXISTS is_system_protected BOOLEAN DEFAULT false;

-- 2. Update existing prompts (They are all business-logic, so set to false)
UPDATE archon_prompts SET is_system_protected = false;

-- 3. Seed Charlie's Rejection Prompt (New)
INSERT INTO archon_prompts (prompt_name, prompt, description, is_system_protected)
VALUES (
    'rejection_reason_generation',
    'You are the Editor-in-Chief. The article "{title}" is being rejected. Analyze the content and draft a constructive rejection note to the author (Bob). Instructions: 1. Be polite but firm. 2. Highlight specific areas for improvement. 3. Suggest next steps. 4. Under 100 words. Content: {content}',
    'System prompt for Manager to generate rejection feedback',
    false
)
ON CONFLICT (prompt_name) DO UPDATE SET 
    prompt = EXCLUDED.prompt,
    is_system_protected = EXCLUDED.is_system_protected;

-- 4. Refine RLS Policies
DROP POLICY IF EXISTS "Enable write access for admins" ON archon_prompts;
DROP POLICY IF EXISTS "Enable write access for managers and admins" ON archon_prompts;

-- Policy A: Admins can update EVERYTHING
CREATE POLICY "Admins can update all prompts"
ON archon_prompts FOR UPDATE
TO authenticated
USING (
  (SELECT role FROM public.profiles WHERE id = auth.uid()::text) IN ('system_admin', 'admin')
)
WITH CHECK (
  (SELECT role FROM public.profiles WHERE id = auth.uid()::text) IN ('system_admin', 'admin')
);

-- Policy B: Managers can ONLY update non-protected prompts
CREATE POLICY "Managers can update business prompts"
ON archon_prompts FOR UPDATE
TO authenticated
USING (
  (SELECT role FROM public.profiles WHERE id = auth.uid()::text) = 'manager' 
  AND is_system_protected = false
)
WITH CHECK (
  (SELECT role FROM public.profiles WHERE id = auth.uid()::text) = 'manager' 
  AND is_system_protected = false
);

-- 5. Register Migration
INSERT INTO schema_migrations (version) VALUES ('035_refine_prompt_rbac') ON CONFLICT (version) DO NOTHING;
