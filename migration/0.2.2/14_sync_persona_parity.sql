-- migration/0.2.2/14_sync_persona_parity.sql
-- Phase 4.6.34: Final Workflow Alignment for Alice, Bob, Charlie, David, and Agents
-- Synchronizes DB RBAC matrix with python/src/server/auth/permissions.py scopes.

-- 1. Ensure Alice (Sales) has the correct marketing and leads scopes
UPDATE public.archon_roles_permissions
SET permissions = ARRAY['task:create', 'task:read:own', 'task:read:team', 'task:update:own', 'agent:trigger:mkt', 'leads:view:all', 'stats:view:own'],
    updated_at = NOW()
WHERE role = 'sales';

-- 2. Ensure Charlie (Manager) has full triggering and stats scopes
UPDATE public.archon_roles_permissions
SET permissions = ARRAY['task:create', 'task:read:team', 'task:update:own', 'user:manage:team', 'agent:trigger:dev', 'agent:trigger:mkt', 'agent:trigger:know', 'stats:view:team', 'leads:view:all', 'brand:manage', 'code:approve', 'mcp:manage', 'content:publish', 'content:reject', 'info:request'],
    updated_at = NOW()
WHERE role = 'manager';

-- 3. Ensure Agents (ai_agent) have the required know scope
UPDATE public.archon_roles_permissions
SET permissions = ARRAY['task:read:own', 'task:read:team', 'agent:trigger:know', 'stats:view:own'],
    updated_at = NOW()
WHERE role = 'ai_agent';

-- 4. Ensure David (system_admin) has the new delete scope if applicable
UPDATE public.archon_roles_permissions
SET permissions = ARRAY['task:create', 'task:read:own', 'task:read:team', 'task:read:all', 'task:update:own', 'task:update:all', 'user:manage', 'user:manage:team', 'mcp:manage', 'stats:view:own', 'stats:view:team', 'stats:view:all', 'agent:trigger:dev', 'agent:trigger:mkt', 'agent:trigger:know', 'leads:view:all', 'content:publish', 'content:reject', 'info:request', 'brand:manage'],
    updated_at = NOW()
WHERE role = 'system_admin';
