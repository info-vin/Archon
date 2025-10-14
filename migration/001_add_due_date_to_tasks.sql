-- This script adds the due_date column to the tasks table if it doesn't exist.
ALTER TABLE archon_tasks
ADD COLUMN IF NOT EXISTS due_date TIMESTAMPTZ;

-- Register this migration script as executed in the tracking table.
-- The version identifier is based on the file name.
INSERT INTO schema_migrations (version) VALUES ('001_add_due_date_to_tasks') ON CONFLICT (version) DO NOTHING;