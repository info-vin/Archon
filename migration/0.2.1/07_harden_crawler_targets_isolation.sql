
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
