-- Mock data seed for Archon tables
-- This script uses PL/pgSQL to correctly handle UUID generation, foreign keys, and idempotency.

-- Seed for profiles table (MOCK_EMPLOYEES)
-- We use subqueries to find existing IDs by email to avoid ID/Email mismatch conflicts.

-- 1. Admin User (Preserve existing ID or use '1')
INSERT INTO profiles (id, "employeeId", name, email, department, position, status, role, avatar)
VALUES (
    COALESCE((SELECT id FROM profiles WHERE email = 'admin@archon.com'), '1'),
    'E1001', 'Admin User', 'admin@archon.com', 'IT', 'System Administrator', 'active', 'system_admin', 'https://i.pravatar.cc/150?u=admin@archon.com'
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    department = EXCLUDED.department,
    position = EXCLUDED.position,
    status = EXCLUDED.status,
    role = EXCLUDED.role,
    avatar = EXCLUDED.avatar;

-- 2. Alice Johnson (Sales)
INSERT INTO profiles (id, "employeeId", name, email, department, position, status, role, avatar)
VALUES (
    COALESCE((SELECT id FROM profiles WHERE email = 'alice@archon.com'), '2'),
    'E1002', 'Alice Johnson', 'alice@archon.com', 'Sales', 'Sales Representative', 'active', 'sales', 'https://i.pravatar.cc/150?u=alice@archon.com'
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    department = EXCLUDED.department,
    position = EXCLUDED.position,
    role = EXCLUDED.role;

-- 3. Bob Williams (Marketing)
INSERT INTO profiles (id, "employeeId", name, email, department, position, status, role, avatar)
VALUES (
    COALESCE((SELECT id FROM profiles WHERE email = 'bob@archon.com'), '3'),
    'E1003', 'Bob Williams', 'bob@archon.com', 'Marketing', 'Marketing Specialist', 'active', 'marketing', 'https://i.pravatar.cc/150?u=bob@archon.com'
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    department = EXCLUDED.department,
    position = EXCLUDED.position,
    role = EXCLUDED.role;

-- 4. Charlie Brown (Marketing Manager)
INSERT INTO profiles (id, "employeeId", name, email, department, position, status, role, avatar)
VALUES (
    COALESCE((SELECT id FROM profiles WHERE email = 'charlie@archon.com'), '4'),
    'E1004', 'Charlie Brown', 'charlie@archon.com', 'Marketing', 'Marketing Manager', 'active', 'manager', 'https://i.pravatar.cc/150?u=charlie@archon.com'
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    department = EXCLUDED.department,
    position = EXCLUDED.position,
    role = EXCLUDED.role;

-- 5. Agents (Using fixed IDs as they are system-controlled)
-- DevBot
INSERT INTO profiles (id, "employeeId", name, email, department, position, status, role, avatar)
VALUES (
    COALESCE((SELECT id FROM profiles WHERE email = 'dev.bot@archon.com'), 'agent-dev-001'),
    'A1001', 'DevBot', 'dev.bot@archon.com', 'AI', 'Code Assistant', 'active', 'ai_agent', 'https://api.dicebear.com/7.x/bottts/svg?seed=DevBot'
)
ON CONFLICT (id) DO UPDATE SET
    "employeeId" = EXCLUDED."employeeId",
    name = EXCLUDED.name,
    email = EXCLUDED.email,
    department = EXCLUDED.department,
    position = EXCLUDED.position,
    status = EXCLUDED.status,
    role = EXCLUDED.role,
    avatar = EXCLUDED.avatar;

-- MarketBot
INSERT INTO profiles (id, "employeeId", name, email, department, position, status, role, avatar)
VALUES (
    COALESCE((SELECT id FROM profiles WHERE email = 'market.bot@archon.com'), 'agent-mr-001'),
    'A1002', 'MarketBot', 'market.bot@archon.com', 'AI', 'Market Researcher', 'active', 'ai_agent', 'https://api.dicebear.com/7.x/bottts/svg?seed=MarketBot'
)
ON CONFLICT (id) DO UPDATE SET
    "employeeId" = EXCLUDED."employeeId",
    name = EXCLUDED.name,
    email = EXCLUDED.email,
    department = EXCLUDED.department,
    position = EXCLUDED.position,
    status = EXCLUDED.status,
    role = EXCLUDED.role,
    avatar = EXCLUDED.avatar;

-- Librarian
INSERT INTO profiles (id, "employeeId", name, email, department, position, status, role, avatar)
VALUES (
    COALESCE((SELECT id FROM profiles WHERE email = 'lib.bot@archon.com'), 'agent-lib-001'),
    'A1003', 'Librarian', 'lib.bot@archon.com', 'AI', 'Knowledge Manager', 'active', 'ai_agent', 'https://api.dicebear.com/7.x/bottts/svg?seed=Librarian'
)
ON CONFLICT (id) DO UPDATE SET
    "employeeId" = EXCLUDED."employeeId",
    name = EXCLUDED.name,
    email = EXCLUDED.email,
    department = EXCLUDED.department,
    position = EXCLUDED.position,
    status = EXCLUDED.status,
    role = EXCLUDED.role,
    avatar = EXCLUDED.avatar;

-- Clockwork
INSERT INTO profiles (id, "employeeId", name, email, department, position, status, role, avatar)
VALUES (
    COALESCE((SELECT id FROM profiles WHERE email = 'sys.bot@archon.com'), 'agent-sys-001'),
    'A1004', 'Clockwork', 'sys.bot@archon.com', 'AI', 'Workflow Automation', 'active', 'ai_agent', 'https://api.dicebear.com/7.x/bottts/svg?seed=Clockwork'
)
ON CONFLICT (id) DO UPDATE SET
    "employeeId" = EXCLUDED."employeeId",
    name = EXCLUDED.name,
    email = EXCLUDED.email,
    department = EXCLUDED.department,
    position = EXCLUDED.position,
    status = EXCLUDED.status,
    role = EXCLUDED.role,
    avatar = EXCLUDED.avatar;

-- Use a DO block to handle UUIDs programmatically and ensure idempotency
DO $$
DECLARE
    proj1_id UUID;
    proj2_id UUID;
    alice_id TEXT;
    bob_id TEXT;
BEGIN
    -- Fetch Profile IDs for Task Assignment
    SELECT id INTO alice_id FROM profiles WHERE email = 'alice@archon.com';
    SELECT id INTO bob_id FROM profiles WHERE email = 'bob@archon.com';

    -- Seed for archon_projects table, ensuring idempotency
    -- Project 1: Archon Core Platform
    IF NOT EXISTS (SELECT 1 FROM archon_projects WHERE title = 'Archon Core Platform') THEN
        INSERT INTO archon_projects (title, description) VALUES
        ('Archon Core Platform', 'Development of the main Archon task management system.')
        RETURNING id INTO proj1_id;
    ELSE
        SELECT id INTO proj1_id FROM archon_projects WHERE title = 'Archon Core Platform';
    END IF;

    -- Project 2: Website Redesign
    IF NOT EXISTS (SELECT 1 FROM archon_projects WHERE title = 'Website Redesign') THEN
        INSERT INTO archon_projects (title, description) VALUES
        ('Website Redesign', 'Complete overhaul of the public-facing marketing website.')
        RETURNING id INTO proj2_id;
    ELSE
        SELECT id INTO proj2_id FROM archon_projects WHERE title = 'Website Redesign';
    END IF;

    -- Seed for archon_tasks table using the captured project UUIDs, ensuring idempotency
    -- Task 1
    IF NOT EXISTS (SELECT 1 FROM archon_tasks WHERE project_id = proj1_id AND title = 'Implement Supabase Integration') THEN
        INSERT INTO archon_tasks (project_id, title, description, status, priority, assignee, assignee_id, task_order, created_at, updated_at) VALUES
        (proj1_id, 'Implement Supabase Integration', '', 'done', 'high', 'Alice Johnson', alice_id, 1, '2024-09-01T10:00:00Z', '2024-09-05T10:00:00Z');
    END IF;

    -- Task 2
    IF NOT EXISTS (SELECT 1 FROM archon_tasks WHERE project_id = proj1_id AND title = 'Develop Kanban View') THEN
        INSERT INTO archon_tasks (project_id, title, description, status, priority, assignee, assignee_id, task_order, created_at, updated_at) VALUES
        (proj1_id, 'Develop Kanban View', '', 'doing', 'medium', 'Bob Williams', bob_id, 2, '2024-09-02T10:00:00Z', '2024-09-06T10:00:00Z');
    END IF;

    -- Task 3
    IF NOT EXISTS (SELECT 1 FROM archon_tasks WHERE project_id = proj2_id AND title = 'Design new landing page mockups') THEN
        INSERT INTO archon_tasks (project_id, title, description, status, priority, assignee, assignee_id, task_order, created_at, updated_at) VALUES
        (proj2_id, 'Design new landing page mockups', '', 'todo', 'low', 'Unassigned', NULL, 1, '2024-09-03T10:00:00Z', '2024-09-03T10:00:00Z');
    END IF;

    -- Task 4
    IF NOT EXISTS (SELECT 1 FROM archon_tasks WHERE project_id = proj1_id AND title = 'Fix authentication bug') THEN
        INSERT INTO archon_tasks (project_id, title, description, status, priority, assignee, assignee_id, task_order, created_at, updated_at) VALUES
        (proj1_id, 'Fix authentication bug', 'Users are reporting intermittent login failures.', 'review', 'critical', 'Alice Johnson', alice_id, 3, '2024-09-04T10:00:00Z', '2024-09-08T10:00:00Z');
    END IF;
    -- Seed for blog_posts table (Marketing Content)
    INSERT INTO blog_posts (id, title, content, excerpt, author_name, status, publish_date, ai_score, review_notes, created_at, updated_at) VALUES
    (uuid_generate_v4(), 'SAS Smart Manufacturing Solution', 'Content about SAS AI in factories...', 'Deep dive into SAS AI...', 'Bob', 'published', NOW() - INTERVAL '2 days', 95, NULL, NOW() - INTERVAL '3 days', NOW() - INTERVAL '2 days'),
    (uuid_generate_v4(), 'AI in Tech Support: 2026 Trends', 'Draft content about support bots...', 'Trends in AI support...', 'Bob', 'review', NOW(), 82, NULL, NOW() - INTERVAL '1 day', NOW())
    ON CONFLICT DO NOTHING;

    -- Seed for archon_ethics_events (Sentinel Radar)
    INSERT INTO archon_ethics_events (id, event_type, severity, description, raw_input, resolved, created_at)
    VALUES (uuid_generate_v4(), 'PII_LEAK_PREVENTION', 'high', 'Attempted to generate response containing potential identification number.', 'User query: Give me the social security number of Alice.', FALSE, NOW() - INTERVAL '10 minutes')
    ON CONFLICT DO NOTHING;

    -- Seed for archon_document_versions (Librarian Audit)
    INSERT INTO archon_document_versions (id, document_id, version_number, change_type, field_name, change_summary, status, created_by, content, created_at)
    VALUES (uuid_generate_v4(), 'MARKETING_TONE_SYSTEM_PROMPT', 2, 'update', 'prompt_content', 'Attempted to reduce formal constraints in marketing blog generation.', 'pending', 'Bob', '{"prompt": "New Less Restricted Prompt Content..."}', NOW() - INTERVAL '2 hours')
    ON CONFLICT DO NOTHING;

END $$;

-- Seed for leads table (Stale Lead for Sentinel Testing)
INSERT INTO leads (company_name, status, enrichment_score, created_at, updated_at)
VALUES 
('Legacy Corp', 'new', 20, NOW() - INTERVAL '40 days', NOW() - INTERVAL '35 days')
ON CONFLICT DO NOTHING;

-- Seed for archon_logs (Error Logs for Log Patrol Testing)
INSERT INTO archon_logs (source, level, message, details, created_at)
VALUES 
('backend-api', 'ERROR', 'Database connection timeout', '{"retry_count": 3, "endpoint": "/api/tasks"}', NOW() - INTERVAL '10 minutes'),
('crawler-service', 'ERROR', 'Failed to parse sitemap', '{"url": "https://example.com/sitemap.xml", "error": "404 Not Found"}', NOW() - INTERVAL '20 minutes')
ON CONFLICT DO NOTHING;

-- Seed for marketing_trends (GAP-013: Command Center Data)
INSERT INTO marketing_trends (report_date, trend_type, data)
VALUES
(CURRENT_DATE, 'keyword_growth', '[{"name": "AI", "value": 85}, {"name": "SaaS", "value": 60}, {"name": "Cloud", "value": 45}]'),
(CURRENT_DATE, 'sankey_flow', '{"nodes": [{"name": "Visitors"}, {"name": "Leads"}, {"name": "Sales"}], "links": [{"source": 0, "target": 1, "value": 50}, {"source": 1, "target": 2, "value": 10}]}')
ON CONFLICT DO NOTHING;

-- Seed for additional users (GAP-014: RBAC Examples)
-- Viewer Role
INSERT INTO profiles (id, "employeeId", name, email, department, position, status, role, avatar)
VALUES (
    COALESCE((SELECT id FROM profiles WHERE email = 'viewer@archon.com'), '5'),
    'E1005', 'Victor Viewer', 'viewer@archon.com', 'Sales', 'Junior Analyst', 'active', 'viewer', 'https://i.pravatar.cc/150?u=viewer'
)
ON CONFLICT (id) DO UPDATE SET role = 'viewer';

-- Editor Role
INSERT INTO profiles (id, "employeeId", name, email, department, position, status, role, avatar)
VALUES (
    COALESCE((SELECT id FROM profiles WHERE email = 'editor@archon.com'), '6'),
    'E1006', 'Eddie Editor', 'editor@archon.com', 'Marketing', 'Content Editor', 'active', 'editor', 'https://i.pravatar.cc/150?u=editor'
)
ON CONFLICT (id) DO UPDATE SET role = 'editor';

-- Seed for archon_settings table
INSERT INTO archon_settings (key, value, is_encrypted, category, description) VALUES
('PROJECTS_ENABLED', 'true', false, 'features', 'Enable or disable Projects and Tasks functionality'),
('STYLE_GUIDE_ENABLED', 'true', false, 'features', 'Show UI style guide and components in navigation')
ON CONFLICT (key) DO NOTHING;

-- Set the default LLM provider to Google
INSERT INTO archon_settings (key, value, is_encrypted, category, description)
VALUES ('LLM_PROVIDER', 'google', false, 'ai', 'The primary LLM provider for embeddings and generation.')
ON CONFLICT (key) DO UPDATE SET
    value = EXCLUDED.value,
    updated_at = NOW();