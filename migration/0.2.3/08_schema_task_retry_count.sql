-- Phase 5.10.5: Zombie Task Recovery & DLQ
-- Add retry_count column to archon_tasks for Dead Letter Queue pattern

ALTER TABLE public.archon_tasks ADD COLUMN IF NOT EXISTS retry_count INT DEFAULT 0;
