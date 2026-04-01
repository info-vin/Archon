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
