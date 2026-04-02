-- Mock data seed for Archon tables
-- Physical Alignment for Phase 4.6.13: Removing all non-existent identities and aligning with RBAC.

-- 1. Physical Cleanup: Clear and rebuild profiles to ensure zero ghost bots
DELETE FROM profiles WHERE id NOT IN ('1', '2', '3', '4');

-- 2. Core Human Personas (SSOT)
INSERT INTO profiles (id, "employeeId", name, email, department, position, status, role, avatar)
VALUES 
('1', 'E1001', 'David Howard', 'admin@archon.com', 'IT', 'System Administrator', 'active', 'system_admin', 'https://i.pravatar.cc/150?u=admin@archon.com'),
('2', 'E1002', 'Alice Johnson', 'alice@archon.com', 'Sales', 'Sales Representative', 'active', 'sales', 'https://i.pravatar.cc/150?u=alice@archon.com'),
('3', 'E1003', 'Bob Williams', 'bob@archon.com', 'Marketing', 'Marketing Specialist', 'active', 'marketing', 'https://i.pravatar.cc/150?u=bob@archon.com'),
('4', 'E1004', 'Charlie Brown', 'charlie@archon.com', 'Marketing', 'Marketing Manager', 'active', 'manager', 'https://i.pravatar.cc/150?u=charlie@archon.com')
ON CONFLICT (id) DO UPDATE SET 
    role = EXCLUDED.role, 
    email = EXCLUDED.email,
    status = 'active';

-- 3. AI Agents (Physically existing in agent_registry.py)
-- DevBot (Uses system_admin role for full system access)
INSERT INTO profiles (id, "employeeId", name, email, department, position, status, role, avatar)
VALUES (
    'ai-dev-bot', 'BOT-001', 'Archon DevBot', 'dev.bot@archon.com', 'Engineering', 'AI Developer', 'active', 'system_admin', 'https://api.dicebear.com/7.x/bottts/svg?seed=DevBot'
) ON CONFLICT (id) DO UPDATE SET role = 'system_admin', status = 'active';

-- MarketBot (Uses marketing role for lead/blog access)
INSERT INTO profiles (id, "employeeId", name, email, department, position, status, role, avatar)
VALUES (
    'ai-market-bot', 'BOT-002', 'Archon MarketBot', 'market.bot@archon.com', 'Marketing', 'AI Marketer', 'active', 'marketing', 'https://api.dicebear.com/7.x/bottts/svg?seed=MarketBot'
) ON CONFLICT (id) DO UPDATE SET role = 'marketing', status = 'active';

-- Librarian (Uses marketing role for knowledge access)
INSERT INTO profiles (id, "employeeId", name, email, department, position, status, role, avatar)
VALUES (
    'ai-librarian', 'BOT-003', 'Archon Librarian', 'lib.bot@archon.com', 'Knowledge', 'AI Librarian', 'active', 'marketing', 'https://api.dicebear.com/7.x/bottts/svg?seed=Librarian'
) ON CONFLICT (id) DO UPDATE SET role = 'marketing', status = 'active';

-- 4. Base Project
INSERT INTO archon_projects (id, title, description, pinned)
VALUES ('00000000-0000-0000-0000-000000000000', 'Archon Core', 'System coordination and self-healing.', true)
ON CONFLICT (id) DO NOTHING;

-- 5. Standard System Prompts
INSERT INTO archon_prompts (prompt_name, prompt, is_system_protected, description)
VALUES 
('SALES_PITCH', 'You are Alice, a senior sales rep...', true, 'Sales Pitch Generation'),
('BLOG_DRAFT', 'You are Bob, a marketing expert...', true, 'Blog Post Generation'),
('MARKET_INTELLIGENCE', 'Analyze leads and identify trends...', true, 'Market Insight Logic')
ON CONFLICT (prompt_name) DO UPDATE SET prompt = EXCLUDED.prompt;
-- Mock Data for Sentinel Verification
-- Inserts stale leads to trigger alerts

INSERT INTO leads (
    id, 
    company_name, 
    contact_name, 
    email, 
    status, 
    source, 
    enrichment_score, 
    created_at, 
    updated_at
) VALUES 
(
    '00000000-0000-0000-0000-111111111111', 
    'Stale Corp Inc', 
    'Old Contact', 
    'contact@stale.com', 
    'new', 
    'manual', 
    10, 
    NOW() - INTERVAL '30 days', 
    NOW() - INTERVAL '20 days' -- > 14 days old
),
(
    '00000000-0000-0000-0000-222222222222', 
    'Legacy Systems Ltd', 
    'Jane Legacy', 
    'jane@legacy.com', 
    'contacted', 
    'manual', 
    60, -- High score but stale
    NOW() - INTERVAL '60 days', 
    NOW() - INTERVAL '45 days'
)
ON CONFLICT (id) DO UPDATE 
SET updated_at = EXCLUDED.updated_at, status = EXCLUDED.status;
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
