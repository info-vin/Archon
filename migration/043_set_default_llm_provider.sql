-- Migration: 043_set_default_llm_provider.sql
-- Description: Set default LLM provider to 'google' to align with available API keys
-- Date: 2026-02-12

-- Insert or Update default provider setting
INSERT INTO archon_settings (key, value, category, description, is_system_protected)
VALUES ('DEFAULT_LLM_PROVIDER', 'google', 'llm', 'Default LLM Provider (openai, google, anthropic)', false)
ON CONFLICT (key) DO UPDATE SET value = 'google';

-- Also update MODEL_CHOICE if exists to a google model
UPDATE archon_settings SET value = 'gemini-1.5-flash' WHERE key = 'MODEL_CHOICE' AND value LIKE 'gpt%';

-- Register migration
INSERT INTO schema_migrations (version) VALUES ('043_set_default_llm_provider') ON CONFLICT (version) DO NOTHING;
