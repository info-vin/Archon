-- Migration: 048_ethics_audit_hardening
-- Description: Adds status and resolution tracking to ethics and audit tables.

-- 1. Hardening Document Versions (Librarian's Audit Trail)
ALTER TABLE archon_document_versions ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'approved';
-- All previous versions are implicitly approved. New ones will be 'pending' if they come from prompt edits.

-- 2. Hardening Ethics Events (Sentinel's Interceptions)
ALTER TABLE archon_ethics_events ADD COLUMN IF NOT EXISTS resolved BOOLEAN DEFAULT FALSE;
ALTER TABLE archon_ethics_events ADD COLUMN IF NOT EXISTS resolution_notes TEXT;

-- 3. Register this migration
INSERT INTO schema_migrations (version) VALUES ('048_ethics_audit_hardening') ON CONFLICT (version) DO NOTHING;
