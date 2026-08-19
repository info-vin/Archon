-- 20260819_add_hybrid_router_settings.sql
-- Description: Seeding missing settings for Hybrid Router to enforce SSOT

INSERT INTO public.archon_settings (key, value, is_encrypted, category, description, is_system_protected, updated_at)
VALUES 
    ('offline_word_limit', '50', false, 'system', 'Word count limit for routing to local offline models', false, NOW()),
    ('online_keywords', '["crawl", "search", "fetch", "live", "latest", "realtime", "google", "news", "code", "寫程式", "程式碼"]', false, 'system', 'Keywords that trigger cloud routing', false, NOW())
ON CONFLICT (key) DO NOTHING;
