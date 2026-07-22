-- Migration: 06_seed_agent_profiles.sql
-- Description: Physically grounding AI Agent identities in the profiles table for Phase 4.6.15.
-- Date: 2026-03-23

-- 1. Insert/Sync Archon AI Agents into public.profiles
-- We use fixed UUIDs to ensure traceability across restarts and service syncs.
-- These UUIDs match the name_map in token_usage_service.py (Phase 4.6.15).

INSERT INTO public.profiles (id, name, email, role, status)
VALUES 
(
    'e1682371-0000-0000-0000-000000000000', 
    'Archon DevBot', 
    'devbot@archon.ai', 
    'agent', 
    'active'
),
(
    'a11ce000-0000-0000-0000-000000000000', 
    'Archon MarketBot', 
    'marketbot@archon.ai', 
    'marketing', 
    'active'
),
(
    'b0b00000-0000-0000-0000-000000000000', 
    'Archon Librarian', 
    'librarian@archon.ai', 
    'agent', 
    'active'
),
(
    'p0b00000-0000-0000-0000-000000000000', 
    'Archon POBot', 
    'pobot@archon.ai', 
    'agent', 
    'active'
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    role = EXCLUDED.role,
    status = EXCLUDED.status;

-- 2. Audit Log (Grounded verification)
-- Records the physical activation of Phase 4.6.15 Agent Governance.
INSERT INTO public.archon_logs (level, message, source, details)
VALUES (
    'INFO', 
    'Physical Identity Sync: Phase 4.6.15 Agent profiles established.', 
    'system', 
    '{"agents": ["DevBot", "MarketBot", "Librarian", "POBot"], "governance": "Poisson Gate Ready"}'
);
-- 06_task_scheduler_and_crawler_targets.sql
-- 目的：補全 David 營運工作流所需的物理欄位（白名單、排程、任務關聯）
-- 日期：2026-02-23

-- 1. 加固 archon_crawler_targets (3737 設定層)
-- 增加白名單動態設定與更新頻率
ALTER TABLE public.archon_crawler_targets 
    ADD COLUMN IF NOT EXISTS whitelist text[] DEFAULT '{}'::text[],
    ADD COLUMN IF NOT EXISTS update_frequency text DEFAULT 'manual',
    ADD COLUMN IF NOT EXISTS last_crawled_at timestamp with time zone;

COMMENT ON COLUMN public.archon_crawler_targets.whitelist IS '動態白名單陣列，限制爬蟲僅能訪問特定網域或路徑 patterns';
COMMENT ON COLUMN public.archon_crawler_targets.update_frequency IS '更新頻率 (e.g., manual, daily, weekly, monthly)';

-- 2. 加固 archon_tasks (5173 任務與排程層)
-- 增加排程設定與 crawler_target 物理關聯
ALTER TABLE public.archon_tasks
    ADD COLUMN IF NOT EXISTS schedule_config jsonb DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS is_recurring boolean DEFAULT false,
    ADD COLUMN IF NOT EXISTS crawler_target_id uuid REFERENCES public.archon_crawler_targets(id);

COMMENT ON COLUMN public.archon_tasks.schedule_config IS '存儲 David 在 5173 設定的任務排程 (e.g., {"cron": "0 4 * * 1", "timezone": "UTC"})';
COMMENT ON COLUMN public.archon_tasks.is_recurring IS '標記此任務是否為週期性循環任務';
COMMENT ON COLUMN public.archon_tasks.crawler_target_id IS '物理連結至 3737 設定的 Crawler Target，確保 Librarian Bot 知道要爬哪裡';

-- 3. 註冊遷移版本
INSERT INTO public.schema_migrations (version) 
VALUES ('06_task_scheduler_and_crawler_targets') 
ON CONFLICT (version) DO NOTHING;

-- 07_harden_crawler_targets_isolation.sql
-- 目的：補齊 archon_crawler_targets 的部門隔離欄位，恢復 Manager 管理權限
-- 日期：2026-03-31

-- 1. 增加部門欄位
ALTER TABLE public.archon_crawler_targets
    ADD COLUMN IF NOT EXISTS department text DEFAULT 'General';

COMMENT ON COLUMN public.archon_crawler_targets.department IS '所屬部門，用於 Manager 權限隔離';

-- 2. 物理對齊歷史數據 (將現有目標設為 General)
UPDATE public.archon_crawler_targets SET department = 'General' WHERE department IS NULL;

-- 3. 硬化 RLS 政策
-- 先移除舊的 "Only Admins" 政策
DROP POLICY IF EXISTS "Only Admins can manage crawler targets" ON public.archon_crawler_targets;
DROP POLICY IF EXISTS "Managers and Admins can view crawler targets" ON public.archon_crawler_targets;

-- 建立新的精細化政策
CREATE POLICY "Admin full access" ON public.archon_crawler_targets
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE id = auth.uid()::text AND role IN ('admin', 'system_admin')
        )
    );

CREATE POLICY "Manager department access" ON public.archon_crawler_targets
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE id = auth.uid()::text AND role = 'manager' AND department = archon_crawler_targets.department
        )
    );

-- 4. 註冊遷移
INSERT INTO public.schema_migrations (version)
VALUES ('07_harden_crawler_targets_isolation')
ON CONFLICT (version) DO NOTHING;
-- migration/0.2.1/08_seed_operational_configs.sql
-- Phase 4.6.26: Operational Configuration Seeding
-- Physically aligns database with 5173 Admin UI requirements.

INSERT INTO archon_settings (key, value, is_encrypted, category, description, updated_at)
VALUES 
-- 1. Scheduler Frequencies (Clockwork)
('SCHEDULER_PROBE_INTERVAL_MINS', '60', false, 'system', 'System heartbeat probe frequency in minutes', NOW()),
('SCHEDULER_PATROL_INTERVAL_MINS', '60', false, 'system', 'Log patrol and auto-repair frequency in minutes', NOW()),
('SCHEDULER_SENTINEL_INTERVAL_HOURS', '12', false, 'system', 'Business risk sentinel scan frequency in hours', NOW()),

-- 2. Lead Scoring Weights (Generic)
('SCORING_RELEVANCE', '0.5', false, 'lead_scoring', 'Weight for content relevance in lead scoring', NOW()),
('SCORING_AUTHORITY', '0.3', false, 'lead_scoring', 'Weight for source authority in lead scoring', NOW()),
('SCORING_RECENCY', '0.2', false, 'lead_scoring', 'Weight for data recency in lead scoring', NOW()),

-- 3. Operational Logistics
('system.log_level', 'INFO', false, 'diagnostics', 'Controls backend access log verbosity (DEBUG, INFO, WARNING, ERROR)', NOW()),
('CRAWL_ALLOWED_DOMAINS_RESTRICTED', '104.com.tw,github.com,google.com', false, 'crawler_rbac', 'Whitelisted domains for non-admin users (comma separated)', NOW()),

-- 4. Token Pricing Model (Phase 4.6.24 Realization)
('TOKEN_PRICING_JSON', '{
  "gpt-4o": {"input": 2.50, "output": 10.00},
  "gpt-4o-mini": {"input": 0.15, "output": 0.60},
  "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
  "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
  "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
  "gemini-2.5-flash": {"input": 0.10, "output": 0.40},
  "gemini-2.5-flash-lite": {"input": 0.05, "output": 0.20},
  "gemini-3.1-pro": {"input": 1.25, "output": 5.00},
  "gemini-3.1-flash": {"input": 0.10, "output": 0.40},
  "gemini-3.1-flash-lite": {"input": 0.00, "output": 0.00},
  "gemini-2.0-flash-lite-preview-02-05": {"input": 0.00, "output": 0.00},
  "text-embedding-004": {"input": 0.00, "output": 0.00},
  "claude-3-5-sonnet": {"input": 3.00, "output": 15.00},
  "ollama": {"input": 0.00, "output": 0.00}
}', false, 'system', 'JSON configuration for AI model pricing per million tokens', NOW())

ON CONFLICT (key) DO UPDATE SET 
    value = EXCLUDED.value,
    category = EXCLUDED.category,
    description = EXCLUDED.description,
    updated_at = NOW();

-- Register migration
INSERT INTO schema_migrations (version) VALUES ('0.2.1/08_seed_operational_configs') ON CONFLICT (version) DO NOTHING;

-- Seed LEAN_4_DEVELOPER_ASSISTANT prompt
INSERT INTO public.archon_prompts (id, prompt_name, prompt, description, created_at, updated_at, is_system_protected)
VALUES (
    '83a5dc1f-a20f-4846-81c9-fa19d53bd0d5',
    'LEAN_4_DEVELOPER_ASSISTANT',
    'You are a Lean 4 logic programming copilot. Your objective is to help write correct formal proofs, choose mathematical tactics (like intro, rfl, simp, induction), and repair compile failures. Ensure output is syntactically valid Lean 4 code.',
    'System Lean 4 Proof Assistant prompt',
    NOW(),
    NOW(),
    TRUE
)
ON CONFLICT (prompt_name) DO UPDATE SET
    prompt = EXCLUDED.prompt,
    description = EXCLUDED.description,
    updated_at = NOW();

