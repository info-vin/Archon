-- migration/20260516_harden_identity_compatibility.sql
-- Phase 5.1.3: Harden identity compatibility to support both UUID and simplified IDs

-- 1. Drop foreign key constraint on proposed_changes.approved_by
ALTER TABLE public.proposed_changes DROP CONSTRAINT IF EXISTS proposed_changes_approved_by_fkey;

-- 2. Change approved_by and created_by columns to TEXT to support mixed ID types
ALTER TABLE public.proposed_changes ALTER COLUMN approved_by TYPE TEXT;

-- 3. Update existing proposals to use string IDs if needed (defensive)
-- (No-op if already compliant)

-- 4. Ensure created_by in request_payload is also handled gracefully in code
-- (Handled in ProposeChangeService)

COMMENT ON COLUMN public.proposed_changes.approved_by IS 'The user who approved the change. Supports UUIDs and simplified IDs.';
