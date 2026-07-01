-- Migration: Enable Row Level Security on missing tables
-- Fixes vulnerability: rls_disabled_in_public

-- 1. archon_roles_permissions
ALTER TABLE public.archon_roles_permissions ENABLE ROW LEVEL SECURITY;
GRANT ALL ON TABLE public.archon_roles_permissions TO authenticated;
GRANT ALL ON TABLE public.archon_roles_permissions TO service_role;
CREATE POLICY "Allow authenticated to read roles" ON public.archon_roles_permissions FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow admins to manage roles" ON public.archon_roles_permissions FOR ALL TO authenticated USING (
    EXISTS (SELECT 1 FROM public.profiles WHERE profiles.id = auth.uid()::text AND profiles.role = ANY (ARRAY['system_admin'::text, 'admin'::text]))
);

-- 2. archon_agents
ALTER TABLE public.archon_agents ENABLE ROW LEVEL SECURITY;
GRANT ALL ON TABLE public.archon_agents TO authenticated;
GRANT ALL ON TABLE public.archon_agents TO service_role;
CREATE POLICY "Allow authenticated to read agents" ON public.archon_agents FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow admins to manage agents" ON public.archon_agents FOR ALL TO authenticated USING (
    EXISTS (SELECT 1 FROM public.profiles WHERE profiles.id = auth.uid()::text AND profiles.role = ANY (ARRAY['system_admin'::text, 'admin'::text]))
);

-- 3. archon_agent_tools
ALTER TABLE public.archon_agent_tools ENABLE ROW LEVEL SECURITY;
GRANT ALL ON TABLE public.archon_agent_tools TO authenticated;
GRANT ALL ON TABLE public.archon_agent_tools TO service_role;
CREATE POLICY "Allow authenticated to read agent tools" ON public.archon_agent_tools FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow admins to manage agent tools" ON public.archon_agent_tools FOR ALL TO authenticated USING (
    EXISTS (SELECT 1 FROM public.profiles WHERE profiles.id = auth.uid()::text AND profiles.role = ANY (ARRAY['system_admin'::text, 'admin'::text]))
);

-- 4. archon_role_agents
ALTER TABLE public.archon_role_agents ENABLE ROW LEVEL SECURITY;
GRANT ALL ON TABLE public.archon_role_agents TO authenticated;
GRANT ALL ON TABLE public.archon_role_agents TO service_role;
CREATE POLICY "Allow authenticated to read role agents" ON public.archon_role_agents FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow admins to manage role agents" ON public.archon_role_agents FOR ALL TO authenticated USING (
    EXISTS (SELECT 1 FROM public.profiles WHERE profiles.id = auth.uid()::text AND profiles.role = ANY (ARRAY['system_admin'::text, 'admin'::text]))
);

-- 5. archon_workflow_flows
ALTER TABLE public.archon_workflow_flows ENABLE ROW LEVEL SECURITY;
GRANT ALL ON TABLE public.archon_workflow_flows TO authenticated;
GRANT ALL ON TABLE public.archon_workflow_flows TO service_role;
CREATE POLICY "Allow authenticated to read workflow flows" ON public.archon_workflow_flows FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow admins to manage workflow flows" ON public.archon_workflow_flows FOR ALL TO authenticated USING (
    EXISTS (SELECT 1 FROM public.profiles WHERE profiles.id = auth.uid()::text AND profiles.role = ANY (ARRAY['system_admin'::text, 'admin'::text]))
);
