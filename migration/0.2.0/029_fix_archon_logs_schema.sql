-- Migration: 029_fix_archon_logs_schema.sql
-- Description: Add missing 'type' and 'project_name' columns to archon_logs table to support Manager Dashboard.
-- Date: 2026-02-07

DO $$
BEGIN
    -- Add 'type' column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'archon_logs' AND COLUMN_NAME = 'type') THEN
        ALTER TABLE archon_logs ADD COLUMN type TEXT DEFAULT 'general';
    END IF;

    -- Add 'project_name' column if it doesn't exist (used as 'source' in some contexts)
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'archon_logs' AND COLUMN_NAME = 'project_name') THEN
        ALTER TABLE archon_logs ADD COLUMN project_name TEXT;
    END IF;
END $$;

-- Register migration
INSERT INTO schema_migrations (version) VALUES ('029_fix_archon_logs_schema') ON CONFLICT (version) DO NOTHING;
