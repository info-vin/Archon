-- Migration: 041_restore_crawler_settings.sql
-- Description: Restore missing Crawler RBAC limits and persist 104 Crawler URL (GAP-024 Optimization)
-- Date: 2026-02-11

-- 1. Restore RBAC Limits
INSERT INTO public.archon_settings (key, value, category, description)
VALUES 
('CRAWL_MAX_DEPTH_SALES', '2', 'crawler_rbac', '業務角色最大爬取深度。'),
('CRAWL_CONCURRENT_MAX_SALES', '3', 'crawler_rbac', '業務角色最大並發請求數。'),
('CRAWL_MAX_DEPTH_MARKETING', '5', 'crawler_rbac', '行銷角色最大爬取深度。'),
('CRAWL_CONCURRENT_MAX_MARKETING', '5', 'crawler_rbac', '行銷角色最大並發請求數。'),
('CRAWL_MAX_DEPTH_MANAGER', '10', 'crawler_rbac', '經理角色最大爬取深度。'),
('CRAWL_CONCURRENT_MAX_MANAGER', '10', 'crawler_rbac', '經理角色最大並發請求數。'),
('CRAWL_MAX_DEPTH_ADMIN', '20', 'crawler_rbac', '管理員角色最大爬取深度。'),
('CRAWL_CONCURRENT_MAX_ADMIN', '20', 'crawler_rbac', '管理員角色最大並發請求數。'),
('CRAWL_ALLOWED_DOMAINS_RESTRICTED', '104.com.tw,github.com,google.com', 'crawler_rbac', '非管理員角色允許存取的網域清單。')
ON CONFLICT (key) DO UPDATE SET 
    value = EXCLUDED.value,
    category = EXCLUDED.category;

-- 2. Persist 104 Crawler URL (New Feature)
INSERT INTO public.archon_settings (key, value, category, description)
VALUES 
('CRAWLER_104_SEARCH_API', 'https://www.104.com.tw/jobs/search/api/jobs', 'crawler_config', '104 職缺搜尋 API 網址。'),
('CRAWLER_104_DETAIL_API', 'https://www.104.com.tw/job/ajax/content/', 'crawler_config', '104 職缺詳情 API 網址。')
ON CONFLICT (key) DO UPDATE SET 
    value = EXCLUDED.value;

-- Register migration
INSERT INTO schema_migrations (version) VALUES ('041_restore_crawler_settings') ON CONFLICT (version) DO NOTHING;
