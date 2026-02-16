-- Migration: 038_seed_scoring_settings.sql
-- Description: Persist scoring weights for Lead Enrichment (GAP-024 Optimization)
-- Date: 2026-02-11

-- Insert scoring rules into archon_settings
-- We set is_system_protected to false (default) to allow Manager/Admin to fine-tune business logic

INSERT INTO archon_settings (key, value, category, description)
VALUES 
(
    'SCORING_VITAL_CONTACT', 
    '20', 
    'lead_scoring', 
    '成功提取到有效的聯繫電子郵件時增加的權重分值。'
),
(
    'SCORING_NEWS_FUNDING', 
    '30', 
    'lead_scoring', 
    '檢測到公司近期有融資新聞 (如 Series A/B/C) 時增加的權重分值。'
),
(
    'SCORING_HAS_JOB_URL', 
    '15', 
    'lead_scoring', 
    '線索包含原始職位連結時增加的權重分值。'
),
(
    'SCORING_TECH_MATCH', 
    '10', 
    'lead_scoring', 
    '技術棧與產品高度匹配時增加的權重分值。'
)
ON CONFLICT (key) DO UPDATE SET 
    category = EXCLUDED.category,
    description = EXCLUDED.description;

-- Register migration
INSERT INTO schema_migrations (version) VALUES ('038_seed_scoring_settings') ON CONFLICT (version) DO NOTHING;
