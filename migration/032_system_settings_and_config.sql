-- Consolidated Migration: 032_system_settings_and_config.sql
-- Covers: 030, 038, 041, 043, 044
-- Purpose: Unified system configuration, scoring weights, and LLM/RAG defaults.

-- 1. System Logistics
INSERT INTO public.archon_settings (key, value, category, description) VALUES 
('system.log_level', 'INFO', 'diagnostics', '控制 API 存取日誌的詳細程度。'),
('DEFAULT_LLM_PROVIDER', 'google', 'llm', 'Default LLM Provider (openai, google, anthropic)')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;

-- 2. Lead Scoring Weights
INSERT INTO public.archon_settings (key, value, category, description) VALUES 
('SCORING_VITAL_CONTACT', '20', 'lead_scoring', '成功提取到有效的聯繫電子郵件時增加的權重分值。'),
('SCORING_NEWS_FUNDING', '30', 'lead_scoring', '檢測到公司近期有融資新聞時增加的權重分值。'),
('SCORING_HAS_JOB_URL', '15', 'lead_scoring', '線索包含原始職位連結時增加的權重分值。'),
('SCORING_TECH_MATCH', '10', 'lead_scoring', '技術棧與產品高度匹配時增加的權重分值。')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;

-- 3. Crawler RBAC & Config
INSERT INTO public.archon_settings (key, value, category, description) VALUES 
('CRAWL_MAX_DEPTH_SALES', '2', 'crawler_rbac', '業務角色最大爬取深度。'),
('CRAWL_MAX_DEPTH_MARKETING', '5', 'crawler_rbac', '行銷角色最大爬取深度。'),
('CRAWL_MAX_DEPTH_MANAGER', '10', 'crawler_rbac', '經理角色最大爬取深度。'),
('CRAWL_MAX_DEPTH_ADMIN', '20', 'crawler_rbac', '管理員角色最大爬取深度。'),
('CRAWL_ALLOWED_DOMAINS_RESTRICTED', '104.com.tw,github.com,google.com', 'crawler_rbac', '非管理員角色允許存取的網域清單。'),
('CRAWLER_104_SEARCH_API', 'https://www.104.com.tw/jobs/search/api/jobs', 'crawler_config', '104 職缺搜尋 API 網址。')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;

-- 4. RAG & LLM Strategy
INSERT INTO public.archon_settings (key, value, category, description) VALUES 
('LLM_PROVIDER', 'google', 'rag_strategy', 'Active LLM Provider for RAG'),
('EMBEDDING_PROVIDER', 'google', 'rag_strategy', 'Primary Embedding Provider'),
('EMBEDDING_MODEL', 'gemini-embedding-001', 'rag_strategy', 'Embedding Model Name'),
('MODEL_CHOICE', 'gemini-1.5-flash', 'rag_strategy', 'Selected Chat Model')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;

-- Register Migration
INSERT INTO schema_migrations (version) VALUES ('032_system_settings_and_config') ON CONFLICT (version) DO NOTHING;
