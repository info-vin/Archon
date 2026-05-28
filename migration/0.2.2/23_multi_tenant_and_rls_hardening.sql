-- Migration 23: Multi-Tenant Schema and RLS Hardening
-- 1. Add tenant_id columns to key tables with default system tenant UUID
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS tenant_id UUID DEFAULT 'd3b07384-d113-4456-a111-c91823710000';
ALTER TABLE public.archon_projects ADD COLUMN IF NOT EXISTS tenant_id UUID DEFAULT 'd3b07384-d113-4456-a111-c91823710000';
ALTER TABLE public.archon_tasks ADD COLUMN IF NOT EXISTS tenant_id UUID DEFAULT 'd3b07384-d113-4456-a111-c91823710000';
ALTER TABLE public.leads ADD COLUMN IF NOT EXISTS tenant_id UUID DEFAULT 'd3b07384-d113-4456-a111-c91823710000';
ALTER TABLE public.token_usage ADD COLUMN IF NOT EXISTS tenant_id UUID DEFAULT 'd3b07384-d113-4456-a111-c91823710000';

-- 2. Create helper function to fetch user's tenant ID without circular dependency on profiles policy
CREATE OR REPLACE FUNCTION public.get_auth_tenant_id()
RETURNS UUID SECURITY DEFINER AS $$
BEGIN
  RETURN (SELECT tenant_id FROM public.profiles WHERE id = auth.uid()::text LIMIT 1);
END;
$$ LANGUAGE plpgsql STABLE;

-- 3. Restructure Row Level Security (RLS) policies for tenant isolation
-- Profiles RLS
DROP POLICY IF EXISTS "Allow authenticated users to read profiles" ON public.profiles;
CREATE POLICY "Allow authenticated users to read profiles" ON public.profiles
    FOR SELECT TO authenticated USING (tenant_id = public.get_auth_tenant_id());

-- Projects RLS
DROP POLICY IF EXISTS "Allow authenticated users to read and update archon_projects" ON public.archon_projects;
CREATE POLICY "Allow authenticated users to read and update archon_projects" ON public.archon_projects
    TO authenticated USING (tenant_id = public.get_auth_tenant_id()) WITH CHECK (tenant_id = public.get_auth_tenant_id());

-- Tasks RLS
DROP POLICY IF EXISTS "Allow authenticated users to read and update archon_tasks" ON public.archon_tasks;
CREATE POLICY "Allow authenticated users to read and update archon_tasks" ON public.archon_tasks
    TO authenticated USING (tenant_id = public.get_auth_tenant_id()) WITH CHECK (tenant_id = public.get_auth_tenant_id());

-- Leads RLS
DROP POLICY IF EXISTS "Allow authenticated users to view leads" ON public.leads;
CREATE POLICY "Allow authenticated users to view leads" ON public.leads
    FOR SELECT TO authenticated USING (tenant_id = public.get_auth_tenant_id());
