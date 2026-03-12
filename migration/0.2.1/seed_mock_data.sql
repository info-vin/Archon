-- Mock data seed for Archon tables
-- This script uses PL/pgSQL to correctly handle UUID generation, foreign keys, and idempotency.

-- 1. Physical Cleanup: Remove profiles that use Agent emails but have wrong IDs
DELETE FROM profiles 
WHERE email IN ('dev.bot@archon.com', 'market.bot@archon.com', 'lib.bot@archon.com', 'pm.bot@archon.com')
AND id NOT IN ('ai-dev-bot', 'ai-market-bot', 'ai-librarian', 'ai-pm-bot');

-- Seed for profiles table (MOCK_EMPLOYEES)
-- 1. Admin User
INSERT INTO profiles (id, "employeeId", name, email, department, position, status, role, avatar)
VALUES (
    COALESCE((SELECT id FROM profiles WHERE email = 'admin@archon.com'), '1'),
    'E1001', 'David Howard', 'admin@archon.com', 'IT', 'System Administrator', 'active', 'system_admin', 'https://i.pravatar.cc/150?u=admin@archon.com'
) ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, role = EXCLUDED.role;

-- 2. Alice Johnson (Sales)
INSERT INTO profiles (id, "employeeId", name, email, department, position, status, role, avatar)
VALUES (
    COALESCE((SELECT id FROM profiles WHERE email = 'alice@archon.com'), '2'),
    'E1002', 'Alice Johnson', 'alice@archon.com', 'Sales', 'Sales Representative', 'active', 'sales', 'https://i.pravatar.cc/150?u=alice@archon.com'
) ON CONFLICT (id) DO UPDATE SET role = EXCLUDED.role;

-- 3. Bob Williams (Marketing)
INSERT INTO profiles (id, "employeeId", name, email, department, position, status, role, avatar)
VALUES (
    COALESCE((SELECT id FROM profiles WHERE email = 'bob@archon.com'), '3'),
    'E1003', 'Bob Williams', 'bob@archon.com', 'Marketing', 'Marketing Specialist', 'active', 'marketing', 'https://i.pravatar.cc/150?u=bob@archon.com'
) ON CONFLICT (id) DO UPDATE SET role = EXCLUDED.role;

-- 4. Charlie Brown (Marketing Manager)
INSERT INTO profiles (id, "employeeId", name, email, department, position, status, role, avatar)
VALUES (
    COALESCE((SELECT id FROM profiles WHERE email = 'charlie@archon.com'), '4'),
    'E1004', 'Charlie Brown', 'charlie@archon.com', 'Marketing', 'Marketing Manager', 'active', 'manager', 'https://i.pravatar.cc/150?u=charlie@archon.com'
) ON CONFLICT (id) DO UPDATE SET role = EXCLUDED.role;

-- 5. Agents
INSERT INTO profiles (id, "employeeId", name, email, department, position, status, role, avatar)
VALUES ('ai-dev-bot', 'BOT-001', 'Archon DevBot', 'dev.bot@archon.com', 'Engineering', 'AI Developer', 'active', 'system_admin', 'https://api.dicebear.com/7.x/bottts/svg?seed=DevBot')
ON CONFLICT (id) DO UPDATE SET role = EXCLUDED.role, status = 'active';

INSERT INTO profiles (id, "employeeId", name, email, department, position, status, role, avatar)
VALUES ('ai-market-bot', 'BOT-002', 'Archon MarketBot', 'market.bot@archon.com', 'Marketing', 'AI Marketer', 'active', 'marketing', 'https://api.dicebear.com/7.x/bottts/svg?seed=MarketBot')
ON CONFLICT (id) DO UPDATE SET role = EXCLUDED.role, status = 'active';

INSERT INTO profiles (id, "employeeId", name, email, department, position, status, role, avatar)
VALUES ('ai-librarian', 'BOT-003', 'Archon Librarian', 'lib.bot@archon.com', 'Knowledge', 'AI Librarian', 'active', 'marketing', 'https://api.dicebear.com/7.x/bottts/svg?seed=Librarian')
ON CONFLICT (id) DO UPDATE SET role = EXCLUDED.role, status = 'active';

INSERT INTO profiles (id, "employeeId", name, email, department, position, status, role, avatar)
VALUES ('ai-pm-bot', 'BOT-004', 'Archon PM Bot', 'pm.bot@archon.com', 'Management', 'AI Project Manager', 'active', 'manager', 'https://api.dicebear.com/7.x/bottts/svg?seed=PMBot')
ON CONFLICT (id) DO UPDATE SET role = EXCLUDED.role, status = 'active';

-- Seed for archon_projects
INSERT INTO archon_projects (id, title, description, pinned)
VALUES (
    '00000000-0000-0000-0000-000000000000',
    'Archon Core Development',
    'Main project for tracking Archon system development and self-healing tasks.',
    true
) ON CONFLICT (id) DO NOTHING;

-- Seed for archon_tasks
INSERT INTO archon_tasks (title, description, status, priority, project_id, assignee_id, assignee, is_recurring, schedule_config)
VALUES 
('Daily Market Intelligence', 'MarketBot summarizes tech job market leads into blog drafts.', 'todo', 'high', '00000000-0000-0000-0000-000000000000', 'ai-market-bot', 'Archon MarketBot', true, '{"frequency": "daily"}'),
('System Health Audit', 'DevBot performs L1 diagnostics on core APIs and services.', 'done', 'medium', '00000000-0000-0000-0000-000000000000', 'ai-dev-bot', 'Archon DevBot', true, '{"frequency": "daily"}'),
('Knowledge Base Pruning', 'Librarian indexes new resources and archives stale entries.', 'todo', 'medium', '00000000-0000-0000-0000-000000000000', 'ai-librarian', 'Archon Librarian', true, '{"frequency": "weekly"}')
ON CONFLICT DO NOTHING;

-- Seed for archon_prompts (Aligned with physical Schema in 04_system_and_logs.sql)
INSERT INTO archon_prompts (prompt_name, prompt, is_system_protected, description)
VALUES 
('SALES_PITCH', 'You are a senior sales representative for Archon. Write a personalized, highly persuasive sales pitch...', true, 'Default Sales Pitch Template'),
('BLOG_DRAFT', 'You are Bob, a marketing expert. Write an engaging blog post about AI trends...', true, 'Default Blog Post Template'),
('MARKET_INTELLIGENCE', 'Analyze the following job leads and identify emerging market trends...', true, 'Market Intelligence Analysis Prompt')
ON CONFLICT (prompt_name) DO UPDATE SET prompt = EXCLUDED.prompt;
