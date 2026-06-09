-- migration/0.2.2/04_rbac_dynamic.sql
-- Phase 4.6.31 & 5.6: Dynamic RBAC Implementation

-- 1. Create the Dynamic RBAC Matrix Table
CREATE TABLE IF NOT EXISTS public.archon_roles_permissions (
    role TEXT PRIMARY KEY,
    permissions TEXT[] NOT NULL DEFAULT '{}',
    description TEXT,
    is_system_protected BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Seed Initial Dynamic Matrix (SSOT)
INSERT INTO public.archon_roles_permissions (role, permissions, description, is_system_protected)
VALUES 
('system_admin', 
 ARRAY['task:create', 'task:read:own', 'task:read:team', 'task:read:all', 'task:update:own', 'task:update:all', 'task:delete', 'user:manage', 'user:manage:team', 'mcp:manage', 'stats:view:own', 'stats:view:team', 'stats:view:all', 'agent:trigger:dev', 'agent:trigger:mkt', 'agent:trigger:know', 'leads:view:all', 'content:publish', 'content:reject', 'info:request', 'brand:manage', 'assign:system_admin', 'assign:manager', 'assign:sales', 'assign:marketing', 'assign:employee', 'assign:ai_agent', 'assign:all'], 
 'System Administrator with full access', true),
('manager', 
 ARRAY['task:create', 'task:read:team', 'task:update:own', 'user:manage:team', 'agent:trigger:dev', 'agent:trigger:mkt', 'agent:trigger:know', 'stats:view:team', 'leads:view:all', 'brand:manage', 'code:approve', 'mcp:manage', 'content:publish', 'content:reject', 'info:request', 'leads:view:marketing', 'assign:manager', 'assign:sales', 'assign:marketing', 'assign:employee', 'assign:ai_agent'], 
 'Department manager', true),
('sales', 
 ARRAY['task:create', 'task:read:own', 'task:read:team', 'task:update:own', 'agent:trigger:mkt', 'leads:view:all', 'leads:view:sales', 'stats:view:own', 'assign:sales', 'assign:ai_agent'], 
 'Sales persona Alice', true),
('marketing', 
 ARRAY['task:create', 'task:read:own', 'task:read:team', 'task:update:own', 'agent:trigger:mkt', 'agent:trigger:know', 'stats:view:own', 'leads:view:all', 'brand:manage', 'info:request', 'assign:marketing', 'assign:ai_agent'], 
 'Marketing persona Bob', true),
('ai_agent', 
 ARRAY['task:read:own', 'task:read:team', 'agent:trigger:know', 'stats:view:own', 'assign:ai_agent'], 
 'Automated agents like DevBot', true),
('employee', 
 ARRAY['task:create', 'task:read:own', 'task:update:own', 'agent:trigger:know', 'stats:view:own', 'assign:employee', 'assign:ai_agent'], 
 'Generic employee', true)
ON CONFLICT (role) DO UPDATE SET 
    permissions = EXCLUDED.permissions,
    description = EXCLUDED.description;
