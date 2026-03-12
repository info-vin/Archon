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
