-- Migration: 030_add_system_log_setting.sql
-- Description: Official entry for system log level configuration.
-- Date: 2026-02-07

INSERT INTO archon_settings (key, value, category, description)
VALUES (
    'system.log_level', 
    'INFO', 
    'diagnostics', 
    '控制 API 存取日誌的詳細程度 (DEBUG, INFO, WARNING, ERROR)。修改後即時生效。'
) ON CONFLICT (key) DO NOTHING;

-- Register migration
INSERT INTO schema_migrations (version) VALUES ('030_add_system_log_setting') ON CONFLICT (version) DO NOTHING;
