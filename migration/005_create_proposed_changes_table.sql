-- migration/005_create_proposed_changes_table.sql

-- 1. Create Enumerated Types for Status and Type
--    Using custom types ensures data integrity and consistency.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'change_status') THEN
        CREATE TYPE change_status AS ENUM ('pending', 'approved', 'rejected', 'executed', 'failed');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'change_type') THEN
        CREATE TYPE change_type AS ENUM ('file', 'git', 'shell');
    END IF;
END$$;

-- 2. Create the proposed_changes Table
--    This table is the core of the "propose-approve-execute" security model.
--    It stores all AI-proposed changes, their status, and the necessary data
--    to execute them upon approval.
CREATE TABLE IF NOT EXISTS proposed_changes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Core Attributes
    status change_status NOT NULL DEFAULT 'pending',
    type change_type NOT NULL,

    -- The request_payload stores the specifics of the proposed change.
    -- For example, for a 'file' type, it would contain:
    -- { "file_path": "src/main.py", "new_content": "..." }
    request_payload JSONB NOT NULL,

    -- Approval Tracking
    approved_by UUID REFERENCES auth.users(id),
    approved_at TIMESTAMPTZ,

    -- Execution Tracking
    executed_at TIMESTAMPTZ,
    execution_log TEXT
);

-- 3. Add Indexes for Performance
--    We will frequently query by status and type.
CREATE INDEX IF NOT EXISTS idx_proposed_changes_status ON proposed_changes(status);
CREATE INDEX IF NOT EXISTS idx_proposed_changes_type ON proposed_changes(type);

-- 4. Enable Row-Level Security (RLS)
--    This is a critical security measure to ensure users can only see and
--    act on changes they are authorized to.
ALTER TABLE proposed_changes ENABLE ROW LEVEL SECURITY;

-- 5. Create RLS Policies
--    Define who can do what with the data.
--
--    - Admins can do anything.
--    - Authenticated users can create proposals.
--    - Authenticated users can view their own proposals and any pending proposals.
--    - Only specific roles (e.g., 'service_role' for backend, maybe a future 'manager' role) can approve.
DROP POLICY IF EXISTS "Allow full access to admins" ON proposed_changes;
CREATE POLICY "Allow full access to admins"
    ON proposed_changes FOR ALL
    USING ((auth.jwt() ->> 'role') = 'service_role'); -- Using service_role as admin for now

DROP POLICY IF EXISTS "Allow authenticated users to create proposals" ON proposed_changes;
CREATE POLICY "Allow authenticated users to create proposals"
    ON proposed_changes FOR INSERT
    WITH CHECK (auth.role() = 'authenticated');

DROP POLICY IF EXISTS "Allow authenticated users to view proposals" ON proposed_changes;
CREATE POLICY "Allow authenticated users to view proposals"
    ON proposed_changes FOR SELECT
    USING (auth.role() = 'authenticated');


-- 6. Add Comments for Clarity
COMMENT ON TABLE proposed_changes IS 'Stores AI-proposed changes that require human approval before execution.';
COMMENT ON COLUMN proposed_changes.status IS 'The current status of the proposed change (e.g., pending, approved).';
COMMENT ON COLUMN proposed_changes.type IS 'The type of change proposed (e.g., file, git, shell).';
COMMENT ON COLUMN proposed_changes.request_payload IS 'A JSON object containing the detailed parameters for the change.';
COMMENT ON COLUMN proposed_changes.approved_by IS 'The user who approved the change.';
