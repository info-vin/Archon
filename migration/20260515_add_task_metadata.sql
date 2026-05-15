-- Migration: Add Metadata Column to archon_tasks
-- Date: 2026-05-15
-- Description: Adds a jsonb metadata column to archon_tasks to support parameterized AI tasks.

ALTER TABLE public.archon_tasks ADD COLUMN IF NOT EXISTS metadata jsonb DEFAULT '{}'::jsonb;

COMMENT ON COLUMN public.archon_tasks.metadata IS 'JSONB field for task-specific parameters (e.g. lead_ids, topic, etc.)';
