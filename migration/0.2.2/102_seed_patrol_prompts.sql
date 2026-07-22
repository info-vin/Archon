-- Seed Patrol and Report Prompts for SSOT Migration
INSERT INTO public.archon_prompts (prompt_name, prompt, description, category)
VALUES (
    'LEADS_PATROL_PROMPT',
    'Please write an engaging 600-word daily blog post summarizing today''s tech job market movements.

Data points ({lead_count} leads):
{lead_summary}

Focus on industry trends and written in Traditional Chinese (繁體中文).
Use the tool to save this blog post as a DRAFT.',
    'Prompt for generating daily marketing leads blog post.',
    'SYSTEM_AGENT'
),
(
    'SYS_ERROR_PATROL_PROMPT',
    'Clockwork detected the following errors in the last hour:
{error_summary}

Please analyze and fix.',
    'Prompt for reporting system errors detected by patrol.',
    'SYSTEM_AGENT'
),
(
    'TECH_DEBT_CLEANUP_PROMPT',
    'Clockwork detected the following technical debt that needs archiving or cleanup:

{warnings_str}

Please review and clean up the workspace.',
    'Prompt for tech debt cleanup tasks.',
    'SYSTEM_AGENT'
),
(
    'TECH_DEBT_SSOT_AUDIT_PROMPT',
    'Clockwork detected the following hardcoded values (Network/Models/Prompts) that violate SSOT rules:

{warnings_str}

Please extract these to config variables, model_ssot.py, or PromptService.',
    'Prompt for reporting SSOT violations in the codebase.',
    'SYSTEM_AGENT'
),
(
    'DAILY_EXECUTIVE_SUMMARY_PROMPT',
    '昨日系統運行數據如下：

{context_md}

請啟動星環群聊，協調 Alice, Bob, DevBot 進行討論，最後由 Supervisor (Charlie) 彙整並提供每日執行摘要報告。',
    'Prompt for triggering the daily executive summary group chat.',
    'SYSTEM_AGENT'
)
ON CONFLICT (prompt_name) DO UPDATE SET
    prompt = EXCLUDED.prompt,
    description = EXCLUDED.description;

-- Register migration version
INSERT INTO public.schema_migrations (version) 
VALUES ('102_seed_patrol_prompts') 
ON CONFLICT (version) DO NOTHING;
