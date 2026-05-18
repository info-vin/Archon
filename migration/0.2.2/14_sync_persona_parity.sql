-- migration/0.2.2/14_sync_persona_parity.sql
-- Phase 4.6.34: Final Identity and Workflow Alignment
-- This script fixes the "String vs UUID" mismatch for AI Agents and synchronizes RBAC.

-- 1. Physically convert AI Agent IDs to valid UUIDs (Phase 4.6.15 Standards)
-- We use fixed UUIDs to ensure referential integrity with the token_usage table.

-- Create temp mapping table
CREATE TEMP TABLE agent_mapping (
    old_id text,
    new_id text,
    agent_name text
);

INSERT INTO agent_mapping (old_id, new_id, agent_name) VALUES
('ai-market-bot', 'a11ce000-0000-0000-0000-000000000000', 'Archon MarketBot'),
('ai-dev-bot', 'e1682371-0000-0000-0000-000000000000', 'Archon DevBot'),
('ai-librarian', 'b0b00000-0000-0000-0000-000000000000', 'Archon Librarian'),
('ai-po-bot', 'p0b00000-0000-0000-0000-000000000000', 'Archon POBot');

-- Update profiles table with real UUIDs
-- We use DELETE + INSERT to change the primary key type (or value) safely
DELETE FROM public.profiles WHERE id IN (SELECT old_id FROM agent_mapping);

INSERT INTO public.profiles (id, name, email, role, status)
SELECT new_id::text, agent_name, lower(replace(agent_name, ' ', '')) || '@archon.ai', 'agent', 'active'
FROM agent_mapping
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    role = EXCLUDED.role;

-- 2. Ensure Alice (Sales) and Bob (Marketing) Scopes are matched to 4.6.34 reality
UPDATE public.archon_roles_permissions
SET permissions = ARRAY['task:create', 'task:read:own', 'task:read:team', 'task:update:own', 'agent:trigger:mkt', 'leads:view:all', 'stats:view:own', 'brand:manage', 'leads:view:marketing'],
    updated_at = NOW()
WHERE role IN ('sales', 'marketing');

-- 3. Ensure Charlie (Manager) and David (Admin) have full HUD scopes
UPDATE public.archon_roles_permissions
SET permissions = ARRAY['task:create', 'task:read:team', 'task:update:own', 'user:manage:team', 'agent:trigger:dev', 'agent:trigger:mkt', 'agent:trigger:know', 'stats:view:team', 'leads:view:all', 'brand:manage', 'code:approve', 'mcp:manage', 'content:publish', 'content:reject', 'info:request', 'leads:view:marketing'],
    updated_at = NOW()
WHERE role = 'manager';

DROP TABLE agent_mapping;
