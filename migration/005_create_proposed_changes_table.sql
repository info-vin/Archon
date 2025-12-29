-- migration/005_create_proposed_changes_table.sql

-- This table stores AI-proposed changes that require human approval before execution.
CREATE TABLE IF NOT EXISTS public.proposed_changes (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'executed', 'failed')),
    type TEXT NOT NULL,
    request_payload jsonb NOT NULL,
    user_id uuid REFERENCES public.profiles(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

-- Add comments to the table and columns for clarity.
COMMENT ON TABLE public.proposed_changes IS 'Stores AI-proposed changes that require human approval before execution.';
COMMENT ON COLUMN public.proposed_changes.status IS 'The current status of the proposal (pending, approved, rejected, executed, failed).';
COMMENT ON COLUMN public.proposed_changes.type IS 'The type of action proposed (e.g., file_write, git_checkout, shell_command).';
COMMENT ON COLUMN public.proposed_changes.request_payload IS 'The JSON payload containing all necessary data for the action (e.g., file path, content, branch name).';
COMMENT ON COLUMN public.proposed_changes.user_id IS 'The user who initiated the action that led to this proposal.';

-- Create indexes for faster queries on frequently filtered columns.
CREATE INDEX IF NOT EXISTS idx_proposed_changes_status ON public.proposed_changes(status);
CREATE INDEX IF NOT EXISTS idx_proposed_changes_user_id ON public.proposed_changes(user_id);

-- The trigger_set_timestamp function is assumed to be created in 000_unified_schema.sql.
-- This trigger ensures the updated_at column is automatically updated when a row is modified.
CREATE OR REPLACE TRIGGER on_proposed_changes_update
BEFORE UPDATE ON public.proposed_changes
FOR EACH ROW
EXECUTE PROCEDURE public.trigger_set_timestamp();
