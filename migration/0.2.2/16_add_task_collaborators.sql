-- Migration script to add collaborative agent support to tasks

-- Add a text array column to store the IDs of collaborating agents
ALTER TABLE public.archon_tasks 
ADD COLUMN IF NOT EXISTS collaborator_agent_ids text[] DEFAULT '{}'::text[];

-- Add a comment explaining the column
COMMENT ON COLUMN public.archon_tasks.collaborator_agent_ids IS 'Array of agent profile IDs acting as collaborators (secondary assignees) on this task';
