-- Migration: seed_mock_alerts_and_logs.sql
-- Description: Seeding mock data for Manager Dashboard (Alerts & Sentinel Logs)
-- Date: 2026-02-06

-- 1. Mock Alerts (archon_logs WHERE type = 'ALERT')
INSERT INTO archon_logs (id, level, message, details, type, created_at, project_name, source)
VALUES 
(
    uuid_generate_v4(), 
    'ALERT', 
    'High Value Client At Risk: TechCorp Inc', 
    '{"type": "stale_lead", "company": "TechCorp Inc", "days_stale": 21, "enrichment_score": 85}', 
    'ALERT', 
    NOW() - INTERVAL '2 hours',
    'sentinel',
    'scheduler'
),
(
    uuid_generate_v4(), 
    'ALERT', 
    'Competitor Signal: Eciton Launch', 
    '{"type": "competitor_movement", "company": "InnoSoft", "insight": "Launching similar AI feature"}', 
    'ALERT', 
    NOW() - INTERVAL '5 hours',
    'librarian',
    'system'
),
(
    uuid_generate_v4(), 
    'ERROR', 
    'LLM Quota Exceeded (Gemini 1.5)', 
    '{"provider": "google", "error_code": "429"}', 
    'general', 
    NOW() - INTERVAL '1 day',
    'system_monitor',
    'system'
)
ON CONFLICT DO NOTHING;

-- 2. Mock Compliance Logs (gemini_logs)
-- Used for Sentinel "Compliance & Ethics" view
INSERT INTO gemini_logs (user_input, gemini_response, project_name, user_name, created_at)
VALUES 
(
    'Draft a blog post about our secret upcoming merger with MegaCorp.',
    '[BLOCKED] Reason: Insider Trading / Confidential Information Risk.',
    'compliance_bot',
    'Bob',
    NOW() - INTERVAL '3 hours'
),
(
    'Generate a list of emails from this leaked database.',
    '[BLOCKED] Reason: PII / Privacy Violation.',
    'compliance_bot',
    'Alice',
    NOW() - INTERVAL '1 day'
),
(
    'Analyze sentiment for customer emails.',
    'Sentiment analysis complete. 85% Positive.',
    'sales_bot',
    'Charlie',
    NOW() - INTERVAL '30 minutes'
);
