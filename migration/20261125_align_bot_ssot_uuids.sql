-- Migration: 20261125_align_bot_ssot_uuids.sql
-- Purpose: Align cloud Supabase archon_agents & profiles UUIDs to P0 physical SSOT:
--   1. Supervisor: align archon_agents.id from d0e00000-... to f0f00000-... (preserves 106 historical tasks)
--   2. POBot: replace illegal non-hex UUID p0b00000-... in profiles with legal c0a00000-... (0 historical tasks)
--   3. Clockwork: register system ops scheduler in archon_agents
--   4. PresentationBot: retire unused profile (0 historical tasks)
-- Idempotent: safe to run multiple times.

BEGIN;

-- 1. Supervisor: align archon_agents from d0e00000-... to f0f00000-...
-- Update archon_agent_tools FK first if any rows reference d0e00000-...
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM public.archon_agents WHERE agent_key = 'supervisor' AND id = 'd0e00000-0000-0000-0000-000000000000'::uuid) THEN
        -- Delete old row (ON DELETE CASCADE handles any empty tool rows) and re-insert with SSOT UUID f0f00000-...
        DELETE FROM public.archon_agents WHERE agent_key = 'supervisor' AND id = 'd0e00000-0000-0000-0000-000000000000'::uuid;
    END IF;
END $$;

INSERT INTO public.archon_agents (id, agent_key, name, model_tier, default_tool, description)
VALUES (
    'f0f00000-0000-0000-0000-000000000000'::uuid,
    'supervisor',
    'Archon Supervisor',
    'pro',
    NULL,
    'Workflow Routing supervisor.'
)
ON CONFLICT (agent_key) DO UPDATE
SET id = EXCLUDED.id,
    name = EXCLUDED.name,
    model_tier = EXCLUDED.model_tier,
    description = EXCLUDED.description,
    updated_at = NOW();

-- 2. Clockwork: register in archon_agents
INSERT INTO public.archon_agents (id, agent_key, name, model_tier, default_tool, description)
VALUES (
    'e1bf7a99-44bf-44ce-a460-cb4e31e798f4'::uuid,
    'clockwork',
    'Clockwork (Ops)',
    'lite',
    NULL,
    'Automated system patrol and lifecycle scheduler.'
)
ON CONFLICT (agent_key) DO UPDATE
SET name = EXCLUDED.name,
    model_tier = EXCLUDED.model_tier,
    description = EXCLUDED.description,
    updated_at = NOW();

-- 3. POBot: replace illegal non-hex p0b00000-... in profiles with legal c0a00000-...
UPDATE public.profiles
SET id = 'c0a00000-0000-0000-0000-000000000000'
WHERE id = 'p0b00000-0000-0000-0000-000000000000'
  AND NOT EXISTS (SELECT 1 FROM public.profiles WHERE id = 'c0a00000-0000-0000-0000-000000000000');

DELETE FROM public.profiles
WHERE id = 'p0b00000-0000-0000-0000-000000000000'
  AND EXISTS (SELECT 1 FROM public.profiles WHERE id = 'c0a00000-0000-0000-0000-000000000000');

-- 4. PresentationBot: retire unused profile (verified 0 historical tasks)
DELETE FROM public.profiles
WHERE id = 'd0d00000-0000-0000-0000-000000000000';

-- 5. Register migration version
INSERT INTO public.schema_migrations (version)
VALUES ('20261125_align_bot_ssot_uuids')
ON CONFLICT (version) DO NOTHING;

COMMIT;
