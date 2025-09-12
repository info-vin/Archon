-- Mock data seed for Archon tables
-- Generated from enduser-ui-fe/src/services/api.ts

-- Seed for profiles table (MOCK_EMPLOYEES)
INSERT INTO profiles (id, "employeeId", name, email, department, position, status, role, avatar) VALUES
('1', 'E1001', 'Admin User', 'admin@archon.com', 'IT', 'System Administrator', 'active', 'Admin', 'https://i.pravatar.cc/150?u=admin@archon.com'),
('2', 'E1002', 'Alice Johnson', 'alice@archon.com', 'Engineering', 'Project Manager', 'active', 'PM', 'https://i.pravatar.cc/150?u=alice@archon.com'),
('3', 'E1003', 'Bob Williams', 'bob@archon.com', 'Engineering', 'Frontend Developer', 'active', 'Engineer', 'https://i.pravatar.cc/150?u=bob@archon.com'),
('4', 'E1004', 'Charlie Brown', 'charlie@archon.com', 'Marketing', 'Marketing Specialist', 'active', 'Marketer', 'https://i.pravatar.cc/150?u=charlie@archon.com'),
('5', 'agent-mr-001', 'Market Researcher', 'market.researcher@archon.com', 'AI', 'Market Researcher', 'active', 'Market Researcher', 'https://i.pravatar.cc/150?u=agent-mr-001');

-- Seed for archon_projects table (MOCK_PROJECTS)
INSERT INTO archon_projects (id, title, description, status, "projectManagerId") VALUES
('proj-1', 'Archon Core Platform', 'Development of the main Archon task management system.', 'active', '1'),
('proj-2', 'Website Redesign', 'Complete overhaul of the public-facing marketing website.', 'planning', '2');

-- Seed for archon_tasks table (MOCK_TASKS)
INSERT INTO archon_tasks (id, project_id, title, description, status, assignee, task_order, priority, due_date, created_at, updated_at) VALUES
('task-1', 'proj-1', 'Implement Supabase Integration', '', 'done', 'Alice Johnson', 1, 'critical', '2024-09-10T23:59:59Z', '2024-09-01T10:00:00Z', '2024-09-05T10:00:00Z'),
('task-2', 'proj-1', 'Develop Kanban View', '', 'doing', 'Bob Williams', 2, 'high', '2024-09-15T23:59:59Z', '2024-09-02T10:00:00Z', '2024-09-06T10:00:00Z'),
('task-3', 'proj-2', 'Design new landing page mockups', '', 'todo', 'Unassigned', 1, 'medium', '2024-09-20T23:59:59Z', '2024-09-03T10:00:00Z', '2024-09-03T10:00:00Z'),
('task-4', 'proj-1', 'Fix authentication bug', 'Users are reporting intermittent login failures.', 'review', 'Alice Johnson', 3, 'high', '2024-09-12T23:59:59Z', '2024-09-04T10:00:00Z', '2024-09-08T10:00:00Z');
