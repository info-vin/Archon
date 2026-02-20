-- migration/025_crawler_rbac_settings.sql

-- 1. Insert Crawler RBAC Settings into archon_settings
-- Using category 'crawler_rbac' to group these settings

INSERT INTO archon_settings (key, value, is_encrypted, category, description) VALUES
('CRAWL_MAX_DEPTH_SALES', '2', false, 'crawler_rbac', 'Maximum crawl depth for Sales role (Alice)'),
('CRAWL_MAX_DEPTH_MARKETING', '3', false, 'crawler_rbac', 'Maximum crawl depth for Marketing role (Bob)'),
('CRAWL_MAX_DEPTH_MANAGER', '5', false, 'crawler_rbac', 'Maximum crawl depth for Manager role (Charlie)'),
('CRAWL_MAX_DEPTH_ADMIN', '10', false, 'crawler_rbac', 'Maximum crawl depth for Admin role'),

('CRAWL_CONCURRENT_MAX_SALES', '3', false, 'crawler_rbac', 'Max parallel pages within one crawl for Sales'),
('CRAWL_CONCURRENT_MAX_MARKETING', '5', false, 'crawler_rbac', 'Max parallel pages within one crawl for Marketing'),
('CRAWL_CONCURRENT_MAX_MANAGER', '10', false, 'crawler_rbac', 'Max parallel pages within one crawl for Manager'),
('CRAWL_CONCURRENT_MAX_ADMIN', '20', false, 'crawler_rbac', 'Max parallel pages within one crawl for Admin'),

('CRAWL_ALLOWED_DOMAINS_RESTRICTED', '104.com.tw,github.com,google.com', false, 'crawler_rbac', 'Whitelisted domains for non-admin users (comma separated)')
ON CONFLICT (key) DO UPDATE SET
    value = EXCLUDED.value,
    description = EXCLUDED.description;

-- 2. Register migration
INSERT INTO schema_migrations (version) VALUES ('025_crawler_rbac_settings') ON CONFLICT (version) DO NOTHING;
