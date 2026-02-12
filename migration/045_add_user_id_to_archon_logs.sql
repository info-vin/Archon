-- Migration: 045_add_user_id_to_archon_logs.sql
-- Description: Add missing 'user_id' column to archon_logs table to support user-specific auditing and stats.
-- Date: 2026-02-12

DO $$
BEGIN
    -- Add 'user_id' column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'archon_logs' AND COLUMN_NAME = 'user_id') THEN
        ALTER TABLE archon_logs ADD COLUMN user_id UUID;
        
        -- Add index for efficient filtering by user
        CREATE INDEX IF NOT EXISTS idx_archon_logs_user_id ON archon_logs(user_id);
    END IF;
END $$;

-- Register migration
INSERT INTO schema_migrations (version) VALUES ('045_add_user_id_to_archon_logs') ON CONFLICT (version) DO NOTHING;
