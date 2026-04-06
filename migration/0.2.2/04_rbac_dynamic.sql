-- migration/0.2.2/04_rbac_dynamic.sql
-- Phase 4.6.31 & 5.6: Dynamic RBAC Implementation

-- 1. Create the Dynamic RBAC Matrix Table
CREATE TABLE IF NOT EXISTS public.archon_roles_permissions (
    role TEXT PRIMARY KEY,
    permissions TEXT[] NOT NULL DEFAULT '{}',
    description TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    is_system_protected BOOLEAN DEFAULT false -- Prevent deletion of core roles
);

-- Enable RLS
ALTER TABLE public.archon_roles_permissions ENABLE ROW LEVEL SECURITY;

-- Policy: Only Admins can modify the matrix
CREATE POLICY "Admins can manage RBAC matrix" 
ON public.archon_roles_permissions 
FOR ALL 
TO authenticated 
USING (
    EXISTS (
        SELECT 1 FROM public.profiles 
        WHERE id = auth.uid() AND role IN ('system_admin', 'admin')
    )
);

-- Policy: Authenticated users can read the matrix
CREATE POLICY "Users can read RBAC matrix" 
ON public.archon_roles_permissions 
FOR SELECT 
TO authenticated 
USING (true);

-- 2. Seed Initial Data (Mirrored from permissions.py current state)
INSERT INTO public.archon_roles_permissions (role, permissions, description, is_system_protected)
VALUES 
('system_admin', 
 ARRAY['task:create', 'task:read:own', 'task:read:team', 'task:read:all', 'task:update:own', 'task:update:all', 'agent:trigger:dev', 'agent:trigger:mkt', 'agent:trigger:know', 'code:approve', 'content:publish', 'content:reject', 'info:request', 'stats:view:own', 'stats:view:team', 'stats:view:all', 'leads:view:all', 'user:manage', 'mcp:manage', 'brand:manage', 'user:manage:team'], 
 'Full system access', true),
('admin', 
 ARRAY['task:create', 'task:read:own', 'task:read:team', 'task:read:all', 'task:update:own', 'task:update:all', 'agent:trigger:dev', 'agent:trigger:mkt', 'agent:trigger:know', 'code:approve', 'content:publish', 'content:reject', 'info:request', 'stats:view:own', 'stats:view:team', 'stats:view:all', 'leads:view:all', 'user:manage', 'mcp:manage', 'brand:manage', 'user:manage:team'], 
 'Alias for system_admin', true),
('manager', 
 ARRAY['task:create', 'task:read:team', 'task:update:own', 'agent:trigger:dev', 'agent:trigger:mkt', 'agent:trigger:know', 'code:approve', 'content:publish', 'content:reject', 'info:request', 'stats:view:team', 'leads:view:all', 'user:manage:team', 'mcp:manage', 'brand:manage'], 
 'Team manager role', true),
('sales', 
 ARRAY['task:create', 'task:read:own', 'task:read:team', 'task:update:own', 'agent:trigger:mkt', 'leads:view:all'], 
 'Sales persona Alice', true),
('marketing', 
 ARRAY['task:create', 'task:read:own', 'task:read:team', 'task:update:own', 'agent:trigger:mkt', 'agent:trigger:know', 'stats:view:own', 'leads:view:all', 'brand:manage', 'info:request'], 
 'Marketing persona Bob', true),
('employee', 
 ARRAY['task:create', 'task:read:own', 'task:update:own', 'agent:trigger:know', 'stats:view:own'], 
 'Generic employee', true)
ON CONFLICT (role) DO UPDATE SET 
    permissions = EXCLUDED.permissions,
    description = EXCLUDED.description;
