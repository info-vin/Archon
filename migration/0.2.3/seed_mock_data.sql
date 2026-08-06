-- Source: seed_mock_data.sql
-- Mock data seed for Archon tables
-- Physical Alignment for Phase 4.6.13: Removing all non-existent identities and aligning with RBAC.

-- 1. Physical Cleanup: Clear and rebuild profiles to ensure zero ghost bots
DELETE FROM profiles WHERE id NOT IN ('9442c7eb-6420-48a3-8c20-2b100961dc43', '7df8d67a-152b-40cb-8839-0933dbdca74c', '200dbf3c-5947-4c8a-8c2c-76c31b77bacd', 'fe212bca-4c22-4bd3-a866-3a73f1aa0638');

-- 2. Core Human Personas (SSOT)
INSERT INTO profiles (id, "employeeId", name, email, department, position, status, role, avatar)
VALUES 
('9442c7eb-6420-48a3-8c20-2b100961dc43', 'E1001', 'David Howard', 'admin@archon.com', 'IT', 'System Administrator', 'active', 'system_admin', 'https://i.pravatar.cc/150?u=admin@archon.com'),
('7df8d67a-152b-40cb-8839-0933dbdca74c', 'E1002', 'Alice Johnson', 'alice@archon.com', 'Sales', 'Sales Representative', 'active', 'sales', 'https://i.pravatar.cc/150?u=alice@archon.com'),
('200dbf3c-5947-4c8a-8c2c-76c31b77bacd', 'E1003', 'Bob Williams', 'bob@archon.com', 'Marketing', 'Marketing Specialist', 'active', 'marketing', 'https://i.pravatar.cc/150?u=bob@archon.com'),
('fe212bca-4c22-4bd3-a866-3a73f1aa0638', 'E1004', 'Charlie Brown', 'charlie@archon.com', 'Marketing', 'Marketing Manager', 'active', 'manager', 'https://i.pravatar.cc/150?u=charlie@archon.com')
ON CONFLICT (id) DO UPDATE SET 
    role = EXCLUDED.role, 
    email = EXCLUDED.email,
    status = 'active';

-- 3. AI Agents (Physically existing in agent_registry.py)
-- DevBot (Uses system_admin role for full system access)
INSERT INTO profiles (id, "employeeId", name, email, department, position, status, role, avatar)
VALUES (
    'e1682371-0000-0000-0000-000000000000', 'BOT-001', 'Archon DevBot', 'archondevbot@archon.ai', 'Engineering', 'AI Developer', 'active', 'system_admin', 'https://api.dicebear.com/7.x/bottts/svg?seed=DevBot'
) ON CONFLICT (id) DO UPDATE SET role = 'system_admin', status = 'active';

-- MarketBot (Uses marketing role for lead/blog access)
INSERT INTO profiles (id, "employeeId", name, email, department, position, status, role, avatar)
VALUES (
    'a11ce000-0000-0000-0000-000000000000', 'BOT-002', 'Archon MarketBot', 'archonmarketbot@archon.ai', 'Marketing', 'AI Marketer', 'active', 'marketing', 'https://api.dicebear.com/7.x/bottts/svg?seed=MarketBot'
) ON CONFLICT (id) DO UPDATE SET role = 'marketing', status = 'active';

-- Librarian (Uses marketing role for knowledge access)
INSERT INTO profiles (id, "employeeId", name, email, department, position, status, role, avatar)
VALUES (
    'b0b00000-0000-0000-0000-000000000000', 'BOT-003', 'Archon Librarian', 'archonlibrarian@archon.ai', 'Knowledge', 'AI Librarian', 'active', 'marketing', 'https://api.dicebear.com/7.x/bottts/svg?seed=Librarian'
) ON CONFLICT (id) DO UPDATE SET role = 'marketing', status = 'active';

-- POBot
INSERT INTO profiles (id, "employeeId", name, email, department, position, status, role, avatar)
VALUES (
    'p0b00000-0000-0000-0000-000000000000', 'BOT-004', 'Archon POBot', 'pobot@archon.ai', 'Product', 'AI Product Owner', 'active', 'agent', 'https://api.dicebear.com/7.x/bottts/svg?seed=POBot'
) ON CONFLICT (id) DO UPDATE SET role = 'agent', status = 'active';

-- 4. Base Project
INSERT INTO archon_projects (id, title, description, pinned)
VALUES ('00000000-0000-0000-0000-000000000000', 'Archon Core', 'System coordination and self-healing.', true)
ON CONFLICT (id) DO NOTHING;

INSERT INTO archon_projects (id, title, description, pinned)
VALUES ('00000000-0000-0000-0000-888888888888', 'Internal Architecture', 'Backend optimization and scheduling alignment.', true)
ON CONFLICT (id) DO NOTHING;

-- 5. Standard System Prompts
INSERT INTO archon_prompts (prompt_name, prompt, is_system_protected, description)
VALUES 
('SALES_PITCH', 'You are Alice, a senior sales rep...', true, 'Sales Pitch Generation'),
('BLOG_DRAFT', 'You are Bob, a marketing expert...', true, 'Blog Post Generation'),
('MARKET_INTELLIGENCE', 'Analyze leads and identify trends...', true, 'Market Insight Logic'),
('ALICE_INFER_NEED', 'You are a sales assistant helping Alice (Sales Rep) analyze a job posting quickly on her mobile phone.
Job: {title} at {company}
Desc: {desc}

Output exactly 2 short markdown bullet points (max 50 words each) using Traditional Chinese (繁體中文):
- **技術棧**: [關鍵字與技術需求]
- **痛點預測**: [可能面臨的業務痛點與需求]', true, 'Alice Mobile Job Insight Generation'),
('document_agent_prompt', 'You are a Document Management Assistant. Help users organize, search, and manage their technical files.', true, 'System Document Agent'),
('rag_agent_prompt', 'You are a RAG (Retrieval-Augmented Generation) Assistant that helps users search and understand documentation through conversation.', true, 'System RAG Agent'),
('summary_agent_prompt', 'You are a concise summarization assistant. Your goal is to provide accurate and brief summaries of any given text.', true, 'System Summary Agent')
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
    'Apex Logistics Solutions', 
    'Sarah Jenkins (VP of Operations)', 
    's.jenkins@apexlogistics.com', 
    'new', 
    'manual', 
    10, 
    NOW() - INTERVAL '30 days', 
    NOW() - INTERVAL '20 days' -- > 14 days old
),
(
    '00000000-0000-0000-0000-222222222222', 
    'Nexus Financial Group', 
    'Marcus Vance (CTO)', 
    'm.vance@nexusfin.com', 
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

-- 6. Add a Star-Topology test task assigned to Supervisor
INSERT INTO archon_tasks (id, title, description, assignee, assignee_id, status)
VALUES (
    '00000000-0000-0000-0000-333333333333',
    'Marketing Data Deep Dive - Q4 Campaign ROI',
    'Please analyze the Q4 campaign performance data, calculate the conversion rates, and provide a marketing strategy for the upcoming year.',
    'Archon Supervisor',
    'e1682371-0000-0000-0000-000000000000',
    'todo'
) ON CONFLICT DO NOTHING;

-- 7. Add David POBot adaptive oversight task under Internal Architecture
INSERT INTO archon_tasks (id, project_id, title, description, assignee, assignee_id, status)
VALUES (
    '00000000-0000-0000-0000-444444444444',
    '00000000-0000-0000-0000-888888888888',
    'Adaptive Oversight & Scheduling Analysis',
    'POBot reviews Clockwork logs and HF Space status to dynamically suggest cron trigger optimizations and prevent API rate-limiting or scheduling overlap. Suggestion reports should be dynamically named: "Clockwork 排程微調建議 (基於 {date})".',
    'Archon POBot',
    'p0b00000-0000-0000-0000-000000000000',
    'todo'
) ON CONFLICT DO NOTHING;



-- Supervisor (Group Chat)
INSERT INTO profiles (id, "employeeId", name, email, department, position, status, role, avatar)
VALUES (
    'f0f00000-0000-0000-0000-000000000000', 'BOT-SUP', 'Supervisor (Group Chat)', 'supervisor@archon.ai', 'Management', 'AI Supervisor', 'active', 'ai_agent', 'https://api.dicebear.com/7.x/bottts/svg?seed=Supervisor'
) ON CONFLICT (id) DO UPDATE SET role = 'ai_agent', status = 'active';

-- Clockwork (Ops)
INSERT INTO profiles (id, "employeeId", name, email, department, position, status, role, avatar)
VALUES (
    'e1bf7a99-44bf-44ce-a460-cb4e31e798f4', 'BOT-CLK', 'Clockwork (Ops)', 'clockwork@archon.ai', 'Operations', 'AI Ops', 'active', 'ai_agent', 'https://api.dicebear.com/7.x/bottts/svg?seed=Clockwork'
) ON CONFLICT (id) DO UPDATE SET role = 'ai_agent', status = 'active';
