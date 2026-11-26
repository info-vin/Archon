-- Migration: 20261125_enable_a2a_handoff_prompts.sql
-- Purpose: Append optional A2A direct handoff directive instructions to Worker prompts in archon_prompts
--          so live LLMs can directly hand off between workers without bouncing through SupervisorNode.
-- Idempotent: only appends if '[HANDOFF:' is not already present.

BEGIN;

UPDATE public.archon_prompts
SET prompt = prompt || E'\n若在一般協作任務中明確需要直接交棒，可於文末附加 `[HANDOFF: summary | 簡短交棒理由]` 或 `[HANDOFF: end | 任務完成]`。',
    updated_at = NOW()
WHERE prompt_name = 'WORKFLOW_WORKER_MARKETBOT'
  AND prompt NOT LIKE '%[HANDOFF:%';

UPDATE public.archon_prompts
SET prompt = prompt || E'\n若總結已完整收斂，可於文末附加 `[HANDOFF: end | 總結完成]` 直接結案。',
    updated_at = NOW()
WHERE prompt_name = 'WORKFLOW_WORKER_SUMMARY'
  AND prompt NOT LIKE '%[HANDOFF:%';

UPDATE public.archon_prompts
SET prompt = prompt || E'\n若在一般協作任務中需要直接交棒，可於文末附加 `[HANDOFF: david | 簡短交棒理由]` 或 `[HANDOFF: summary | 簡短交棒理由]`。',
    updated_at = NOW()
WHERE prompt_name = 'WORKFLOW_SCIENTIST_DEVBOT'
  AND prompt NOT LIKE '%[HANDOFF:%';

UPDATE public.archon_prompts
SET prompt = prompt || E'\n若需直接交棒可於文末附加 `[HANDOFF: summary | 簡短交棒理由]` 或 `[HANDOFF: end | 任務完成]`。',
    updated_at = NOW()
WHERE prompt_name = 'WORKFLOW_DATA_DAVID'
  AND prompt NOT LIKE '%[HANDOFF:%';

INSERT INTO public.schema_migrations (version)
VALUES ('20261125_enable_a2a_handoff_prompts')
ON CONFLICT (version) DO NOTHING;

COMMIT;
