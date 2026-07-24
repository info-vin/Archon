-- Migration: 33_create_agent_checkpoints_and_approvals.sql
-- Phase 5.9.13: Agent DB State Checkpointing & Human-in-the-Loop (HITL) Architecture

-- 1. Agent Checkpoint Table for State Persistence
CREATE TABLE IF NOT EXISTS public.agent_checkpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id TEXT NOT NULL,
    step_index INT NOT NULL,
    agent_role TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('RUNNING', 'PENDING_APPROVAL', 'COMPLETED', 'FAILED', 'CANCELLED')),
    state_snapshot JSONB NOT NULL,
    last_tool_call JSONB DEFAULT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT unq_conv_step UNIQUE(conversation_id, step_index)
);

CREATE INDEX IF NOT EXISTS idx_agent_checkpoints_conv ON public.agent_checkpoints(conversation_id);
CREATE INDEX IF NOT EXISTS idx_agent_checkpoints_status ON public.agent_checkpoints(status);

-- 2. Human-in-the-Loop Pending Approvals Table
CREATE TABLE IF NOT EXISTS public.agent_pending_approvals (
    approval_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id TEXT NOT NULL,
    checkpoint_id UUID REFERENCES public.agent_checkpoints(id) ON DELETE CASCADE,
    tool_name TEXT NOT NULL,
    tool_args JSONB NOT NULL,
    risk_level TEXT NOT NULL DEFAULT 'HIGH',
    status TEXT NOT NULL CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED', 'EXPIRED')),
    reviewer_id TEXT DEFAULT NULL,
    review_reason TEXT DEFAULT NULL,
    expires_at TIMESTAMPTZ NOT NULL DEFAULT (timezone('utc'::text, now()) + interval '30 minutes'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_agent_approvals_status ON public.agent_pending_approvals(status);
