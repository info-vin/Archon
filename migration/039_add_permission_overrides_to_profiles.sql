-- Migration: 039_add_permission_overrides_to_profiles.sql
-- Description: Add granular permission overrides to support user-specific access control (GAP-001)
-- Date: 2026-02-11

-- Add JSONB column for flexible permission overrides
-- Schema: { "permission_name": true/false }
ALTER TABLE public.profiles 
ADD COLUMN IF NOT EXISTS permission_overrides JSONB DEFAULT '{}'::jsonb;

-- Comment for documentation
COMMENT ON COLUMN public.profiles.permission_overrides IS 'User-specific granular permission overrides. True = Grant, False = Revoke.';

-- Register migration
INSERT INTO schema_migrations (version) VALUES ('039_add_permission_overrides_to_profiles') ON CONFLICT (version) DO NOTHING;
