-- Seed Supervisor Agent Profile for Group Chat Routing
-- Phase 5.0.2

-- 1. Ensure Supervisor exists in auth.users
INSERT INTO auth.users (id, instance_id, aud, role, email, encrypted_password, email_confirmed_at, created_at, updated_at)
VALUES (
    'f0f00000-0000-0000-0000-000000000000',
    '00000000-0000-0000-0000-000000000000',
    'authenticated',
    'authenticated',
    'supervisor@archon.ai',
    crypt('agent_password_123!@#', gen_salt('bf')),
    NOW(),
    NOW(),
    NOW()
) ON CONFLICT (id) DO NOTHING;

-- 2. Insert Supervisor profile
INSERT INTO public.profiles (id, "employeeId", name, email, department, "position", status, role, avatar)
VALUES (
    'f0f00000-0000-0000-0000-000000000000',
    'A9001',
    'Archon Supervisor',
    'supervisor@archon.ai',
    'AI Agents',
    'Group Chat Orchestrator',
    'active',
    'agent',
    'https://api.dicebear.com/7.x/bottts/svg?seed=Supervisor&backgroundColor=e2e8f0'
) ON CONFLICT (id) DO NOTHING;
