-- Migration: 023_create_token_usage_table
-- Description: Tracks LLM Token Usage usage and cost for Admin System Health Dashboard

-- 1. Create the table
CREATE TABLE IF NOT EXISTS token_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_id TEXT NOT NULL, -- Correlation ID for tracing (can link to archon_logs)
    user_id UUID REFERENCES auth.users(id), -- Who initiated the request (can be null for system tasks)
    model TEXT NOT NULL, -- e.g. 'gpt-4o', 'gemini-1.5-flash'
    provider TEXT NOT NULL, -- e.g. 'openai', 'google', 'ollama'
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER GENERATED ALWAYS AS (input_tokens + output_tokens) STORED,
    cost_usd NUMERIC(10, 6) DEFAULT 0, -- Store calculated cost (up to 6 decimal places for micro-cents)
    context_type TEXT, -- e.g. 'rag_query', 'blog_generation', 'agent_task'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. Enable RLS
ALTER TABLE token_usage ENABLE ROW LEVEL SECURITY;

-- 3. RLS Policies
-- Admin/System can read all
CREATE POLICY "Admins can view all token usage" ON token_usage
    FOR SELECT
    USING (
        auth.uid() IN (SELECT id FROM public.profiles WHERE role IN ('admin', 'system_admin'))
    );

-- Users can view their own usage (transparency)
CREATE POLICY "Users can view their own usage" ON token_usage
    FOR SELECT
    USING (auth.uid() = user_id);

-- System (Service Role) can insert
-- Note: Service Role bypasses RLS, but we add an explicit policy for clarity/audit if needed
-- For inserts from backend API (which uses Service Key), RLS is bypassed.

-- 4. Indexes for Analytics
CREATE INDEX idx_token_usage_created_at ON token_usage(created_at DESC);
CREATE INDEX idx_token_usage_user_id ON token_usage(user_id);
CREATE INDEX idx_token_usage_model ON token_usage(model);
CREATE INDEX idx_token_usage_request_id ON token_usage(request_id);

-- 5. Comments
COMMENT ON TABLE token_usage IS 'Tracks LLM token consumption and estimated cost for auditing and system health monitoring.';
