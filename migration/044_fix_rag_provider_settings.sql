-- Migration: 044_fix_rag_provider_settings.sql
-- Description: Configure RAG strategy to use Google/Gemini by default
-- Date: 2026-02-12

-- 1. Set LLM Provider for RAG
INSERT INTO archon_settings (key, value, category, description, is_system_protected)
VALUES ('LLM_PROVIDER', 'google', 'rag_strategy', 'Active LLM Provider for RAG', false)
ON CONFLICT (key) DO UPDATE SET value = 'google';

-- 2. Set Embedding Provider explicitly
INSERT INTO archon_settings (key, value, category, description, is_system_protected)
VALUES ('EMBEDDING_PROVIDER', 'google', 'rag_strategy', 'Primary Embedding Provider', false)
ON CONFLICT (key) DO UPDATE SET value = 'google';

-- 3. Set Embedding Model
INSERT INTO archon_settings (key, value, category, description, is_system_protected)
VALUES ('EMBEDDING_MODEL', 'gemini-embedding-001', 'rag_strategy', 'Embedding Model Name', false)
ON CONFLICT (key) DO UPDATE SET value = 'gemini-embedding-001';

-- 4. Set Chat Model Choice
INSERT INTO archon_settings (key, value, category, description, is_system_protected)
VALUES ('MODEL_CHOICE', 'gemini-1.5-flash', 'rag_strategy', 'Selected Chat Model', false)
ON CONFLICT (key) DO UPDATE SET value = 'gemini-1.5-flash';

-- Register migration
INSERT INTO schema_migrations (version) VALUES ('044_fix_rag_provider_settings') ON CONFLICT (version) DO NOTHING;
