-- Migration: Add assignee_id to archon_tasks and link to profiles
-- Purpose: Switch from name-based assignment to ID-based assignment for robust RBAC.

-- 1. Add the new column
ALTER TABLE archon_tasks 
ADD COLUMN IF NOT EXISTS assignee_id TEXT; -- Using TEXT to match profiles.id type

-- 2. Create Foreign Key constraint
-- We reference public.profiles because it contains both human users and AI agents
DO $$ BEGIN
    ALTER TABLE archon_tasks 
    ADD CONSTRAINT fk_archon_tasks_assignee 
    FOREIGN KEY (assignee_id) 
    REFERENCES profiles(id)
    ON DELETE SET NULL;
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 3. Create Index for performance
CREATE INDEX IF NOT EXISTS idx_archon_tasks_assignee_id ON archon_tasks(assignee_id);

-- 4. Data Migration: Backfill assignee_id based on assignee (Name)
-- This is a best-effort update for existing data.
UPDATE archon_tasks t
SET assignee_id = p.id
FROM profiles p
WHERE t.assignee = p.name
  AND t.assignee_id IS NULL;

-- 5. Handle 'User' or 'Unassigned' cases (optional, leave as NULL)
-- If assignee is 'User', we might leave it NULL or assign to a default if one exists.

-- 6. Register migration
INSERT INTO schema_migrations (version) 
VALUES ('007_add_assignee_id_to_tasks') 
ON CONFLICT (version) DO NOTHING;
