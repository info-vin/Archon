-- Rescue script: Fix missing Supervisor and Clockwork agents
-- This script safely inserts the missing agents into the profiles table.
-- It can be safely executed multiple times.

-- 1. Supervisor (Group Chat)
INSERT INTO profiles (id, "employeeId", name, email, department, position, status, role, avatar)
VALUES (
    'f0f00000-0000-0000-0000-000000000000', 'BOT-SUP', 'Supervisor (Group Chat)', 'supervisor@archon.ai', 'Management', 'AI Supervisor', 'active', 'ai_agent', 'https://api.dicebear.com/7.x/bottts/svg?seed=Supervisor'
) ON CONFLICT (id) DO UPDATE SET role = 'ai_agent', status = 'active';

-- 2. Clockwork (Ops)
INSERT INTO profiles (id, "employeeId", name, email, department, position, status, role, avatar)
VALUES (
    'e1bf7a99-44bf-44ce-a460-cb4e31e798f4', 'BOT-CLK', 'Clockwork (Ops)', 'clockwork@archon.ai', 'Operations', 'AI Ops', 'active', 'ai_agent', 'https://api.dicebear.com/7.x/bottts/svg?seed=Clockwork'
) ON CONFLICT (id) DO UPDATE SET role = 'ai_agent', status = 'active';

-- 3. PresentationBot (Slides)
INSERT INTO profiles (id, "employeeId", name, email, department, position, status, role, avatar)
VALUES (
    'd0d00000-0000-0000-0000-000000000000', 'BOT-PPT', 'PresentationBot (Slides)', 'presentation@archon.ai', 'Design', 'AI Designer', 'active', 'ai_agent', 'https://api.dicebear.com/7.x/bottts/svg?seed=PresentationBot'
) ON CONFLICT (id) DO UPDATE SET role = 'ai_agent', status = 'active';
