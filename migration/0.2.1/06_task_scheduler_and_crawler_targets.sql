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
