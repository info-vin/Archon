-- 20261020_add_steering_focus_and_storage_ttl.sql
-- Description: Add MANAGEMENT_STEERING_FOCUS and STORAGE_PODCAST_TTL_DAYS to archon_settings (Phase 5.12.1)

INSERT INTO public.archon_settings (key, value, is_encrypted, category, description, is_system_protected, updated_at)
VALUES 
    ('MANAGEMENT_STEERING_FOCUS', '', false, 'scheduler', '每週/每月高階戰略會議之管理者重點關注焦點與驗證假設 (Management Steering Focus)', false, NOW()),
    ('STORAGE_PODCAST_TTL_DAYS', '14', false, 'storage', 'Supabase Storage 歷史 Podcast 音檔過期清理天數 (TTL in days)', false, NOW())
ON CONFLICT (key) DO UPDATE 
SET 
    description = EXCLUDED.description,
    updated_at = NOW();
