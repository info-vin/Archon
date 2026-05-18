-- Migration: Harden Agent Outputs in archon_tasks.attachments
-- Date: 2026-05-15
-- Description: Converts legacy attachment formats to the new Pydantic-compliant AgentOutputSchema.
-- Version: 1.0 (Phase 5.1.0 Remediation)

WITH unnested_attachments AS (
    -- 1. Unnest all attachments from all tasks
    SELECT 
        id as task_id,
        jsonb_array_elements(COALESCE(attachments, '[]'::jsonb)) as att
    FROM public.archon_tasks
    WHERE attachments IS NOT NULL AND jsonb_array_length(attachments) > 0
),
transformed_attachments AS (
    -- 2. Transform each element to the new schema
    SELECT 
        task_id,
        jsonb_build_object(
            'agent_id', COALESCE(att->>'agent_id', '00000000-0000-0000-0000-000000000000'),
            'timestamp', COALESCE(att->>'timestamp', att->>'created_at', now()::text),
            'output_type', 
                CASE 
                    WHEN (att->'output') ? 'summary' AND (att->'output') ? 'decisions' THEN 'group_chat'
                    WHEN (att->'output') IS NOT NULL AND jsonb_typeof(att->'output') = 'object' THEN 'structured'
                    ELSE 'text'
                END,
            'output', 
                CASE 
                    -- Handle legacy Supervisor format (if it had summary/decisions directly in att or nested in output)
                    WHEN (att->>'summary') IS NOT NULL THEN 
                        jsonb_build_object(
                            'summary', att->>'summary',
                            'decisions', COALESCE(att->'decisions', '[]'::jsonb),
                            'next_steps', COALESCE(att->'next_steps', '[]'::jsonb),
                            'raw_responses', '{}'::jsonb
                        )
                    -- Handle existing output object
                    WHEN (att->'output') IS NOT NULL THEN att->'output'
                    -- Fallback: Use whatever is in response/content
                    ELSE COALESCE(att->'response', att->'content', att)
                END,
            'metadata', COALESCE(att->'metadata', '{}'::jsonb)
        ) as new_att
    FROM unnested_attachments
),
aggregated_attachments AS (
    -- 3. Re-aggregate by task_id
    SELECT 
        task_id,
        jsonb_agg(new_att) as final_attachments
    FROM transformed_attachments
    GROUP BY task_id
)
-- 4. Update the main table
UPDATE public.archon_tasks t
SET 
    attachments = a.final_attachments,
    updated_at = now()
FROM aggregated_attachments a
WHERE t.id = a.task_id;

-- Add a comment to the column to document the schema
COMMENT ON COLUMN public.archon_tasks.attachments IS 'JSONB list of AgentOutputSchema: {agent_id, timestamp, output_type, output, metadata}';
