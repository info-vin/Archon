-- Mock data seed for Archon tables
-- This script uses PL/pgSQL to correctly handle UUID generation and foreign keys.

-- Seed for profiles table (MOCK_EMPLOYEES)
-- This table uses TEXT for id, so direct insertion is fine.
INSERT INTO profiles (id, "employeeId", name, email, department, position, status, role, avatar) VALUES
('1', 'E1001', 'Admin User', 'admin@archon.com', 'IT', 'System Administrator', 'active', 'Admin', 'https://i.pravatar.cc/150?u=admin@archon.com'),
('2', 'E1002', 'Alice Johnson', 'alice@archon.com', 'Engineering', 'Project Manager', 'active', 'PM', 'https://i.pravatar.cc/150?u=alice@archon.com'),
('3', 'E1003', 'Bob Williams', 'bob@archon.com', 'Engineering', 'Frontend Developer', 'active', 'Engineer', 'https://i.pravatar.cc/150?u=bob@archon.com'),
('4', 'E1004', 'Charlie Brown', 'charlie@archon.com', 'Marketing', 'Marketing Specialist', 'active', 'Marketer', 'https://i.pravatar.cc/150?u=charlie@archon.com'),
('5', 'agent-mr-001', 'Market Researcher', 'market.researcher@archon.com', 'AI', 'Market Researcher', 'active', 'Market Researcher', 'https://i.pravatar.cc/150?u=agent-mr-001')
ON CONFLICT (id) DO NOTHING;

-- Use a DO block to handle UUIDs programmatically
DO $$
DECLARE
    proj1_id UUID;
    proj2_id UUID;
BEGIN
    -- Seed for archon_projects table and capture the generated UUIDs
    INSERT INTO archon_projects (title, description) VALUES
    ('Archon Core Platform', 'Development of the main Archon task management system.')
    RETURNING id INTO proj1_id;

    INSERT INTO archon_projects (title, description) VALUES
    ('Website Redesign', 'Complete overhaul of the public-facing marketing website.')
    RETURNING id INTO proj2_id;

    -- Seed for archon_tasks table using the captured project UUIDs
    -- Note: We let the 'id' for tasks be auto-generated as well.
    INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, created_at, updated_at) VALUES
    (proj1_id, 'Implement Supabase Integration', '', 'done', 'Alice Johnson', 1, '2024-09-01T10:00:00Z', '2024-09-05T10:00:00Z'),
    (proj1_id, 'Develop Kanban View', '', 'doing', 'Bob Williams', 2, '2024-09-02T10:00:00Z', '2024-09-06T10:00:00Z'),
    (proj2_id, 'Design new landing page mockups', '', 'todo', 'Unassigned', 1, '2024-09-03T10:00:00Z', '2024-09-03T10:00:00Z'),
    (proj1_id, 'Fix authentication bug', 'Users are reporting intermittent login failures.', 'review', 'Alice Johnson', 3, '2024-09-04T10:00:00Z', '2024-09-08T10:00:00Z');
END $$;
