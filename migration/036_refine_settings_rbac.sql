-- Migration: 036_refine_settings_rbac.sql
-- Description: Implement granular RBAC for system settings. Protect API keys while allowing Charlie to edit business configs.
-- Date: 2026-02-09

-- 1. Add protection flag
ALTER TABLE archon_settings 
ADD COLUMN IF NOT EXISTS is_system_protected BOOLEAN DEFAULT false;

-- 2. Protect critical infrastructure settings
UPDATE archon_settings SET is_system_protected = true 
WHERE key IN (
    'SUPABASE_URL', 
    'SUPABASE_SERVICE_KEY', 
    'GEMINI_API_KEY', 
    'GOOGLE_API_KEY', 
    'ANTHROPIC_API_KEY', 
    'OPENAI_API_KEY'
);

-- 3. Mark crawler and model logic as Manager-editable
UPDATE archon_settings SET is_system_protected = false 
WHERE key LIKE 'CRAWL_%' 
   OR key LIKE '%_MODEL' 
   OR key = 'MODEL_CHOICE';

-- 4. Refine RLS (Optional, since we have API-level check, but safer)
-- The existing tables might not have RLS, let's check and enable if needed.
ALTER TABLE archon_settings ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow manager/admin to manage settings" ON archon_settings;
CREATE POLICY "Admin can update everything"
ON archon_settings FOR UPDATE TO authenticated
USING ((SELECT role FROM public.profiles WHERE id = auth.uid()::text) IN ('system_admin', 'admin'));

CREATE POLICY "Manager can update non-protected settings"
ON archon_settings FOR UPDATE TO authenticated
USING (
    (SELECT role FROM public.profiles WHERE id = auth.uid()::text) = 'manager'
    AND is_system_protected = false
);

-- 5. Register Migration
INSERT INTO schema_migrations (version) VALUES ('036_refine_settings_rbac') ON CONFLICT (version) DO NOTHING;
