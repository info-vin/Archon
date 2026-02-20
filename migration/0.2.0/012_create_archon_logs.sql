-- Create archon_logs table for system-wide event logging (Clockwork, etc)
CREATE TABLE IF NOT EXISTS archon_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source TEXT NOT NULL, -- e.g., 'scheduler', 'bob', 'system'
    level TEXT NOT NULL, -- e.g., 'INFO', 'ERROR', 'WARNING'
    message TEXT NOT NULL,
    details JSONB, -- For storing extra context like probe results
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Add index on created_at for time-based queries
CREATE INDEX IF NOT EXISTS idx_archon_logs_created_at ON archon_logs(created_at DESC);

-- Register migration
INSERT INTO schema_migrations (version) VALUES ('012_create_archon_logs') ON CONFLICT (version) DO NOTHING;
