-- Source: 10_security_rls.sql
-- Name: archon_settings Admin can update everything; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Admin can update everything" ON public.archon_settings FOR UPDATE USING ((( SELECT profiles.role
   FROM public.profiles
  WHERE (profiles.id = (auth.uid())::text)) = ANY (ARRAY['system_admin'::text, 'admin'::text])));


--
-- Name: archon_prompts Admins can update all prompts; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Admins can update all prompts" ON public.archon_prompts FOR UPDATE USING ((( SELECT profiles.role
   FROM public.profiles
  WHERE (profiles.id = (auth.uid())::text)) = ANY (ARRAY['system_admin'::text, 'admin'::text])));


--
-- Name: token_usage Admins can view all token usage; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Admins can view all token usage" ON public.token_usage FOR SELECT USING ((auth.uid() IN ( SELECT (profiles.id)::uuid AS id
   FROM public.profiles
  WHERE (profiles.role = ANY (ARRAY['admin'::text, 'system_admin'::text])))));


--
-- Name: archon_logs Allow admins to view archon logs; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Allow admins to view archon logs" ON public.archon_logs FOR SELECT TO authenticated USING ((EXISTS ( SELECT 1
   FROM public.profiles
  WHERE ((profiles.id = (auth.uid())::text) AND (profiles.role = ANY (ARRAY['admin'::text, 'system_admin'::text, 'manager'::text]))))));


--
-- Name: gemini_logs Allow admins to view gemini logs; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Allow admins to view gemini logs" ON public.gemini_logs FOR SELECT TO authenticated USING ((EXISTS ( SELECT 1
   FROM public.profiles
  WHERE ((profiles.id = (auth.uid())::text) AND (profiles.role = ANY (ARRAY['admin'::text, 'system_admin'::text, 'manager'::text]))))));


--
-- Name: archon_extraction_schemas Allow all authenticated users to view schemas; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Allow all authenticated users to view schemas" ON public.archon_extraction_schemas FOR SELECT USING (((auth.role() = 'authenticated'::text) OR (auth.role() = 'service_role'::text)));


--
-- Name: gemini_logs Allow app logging; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Allow app logging" ON public.gemini_logs FOR INSERT TO authenticated WITH CHECK (true);




--
-- Name: proposed_changes Allow authenticated users to create proposals; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Allow authenticated users to create proposals" ON public.proposed_changes FOR INSERT WITH CHECK ((auth.role() = 'authenticated'::text));


--
-- Name: vendors Allow authenticated users to insert vendors; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Allow authenticated users to insert vendors" ON public.vendors FOR INSERT TO authenticated WITH CHECK (true);


--
-- Name: archon_settings Allow authenticated users to read and update; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Allow authenticated users to read and update" ON public.archon_settings TO authenticated USING (true);


--
-- Name: archon_project_sources Allow authenticated users to read and update archon_project_sou; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Allow authenticated users to read and update archon_project_sou" ON public.archon_project_sources TO authenticated USING (true);


--
-- Name: archon_projects Allow authenticated users to read and update archon_projects; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Allow authenticated users to read and update archon_projects" ON public.archon_projects TO authenticated USING (tenant_id = public.get_auth_tenant_id()) WITH CHECK (tenant_id = public.get_auth_tenant_id());


--
-- Name: archon_tasks Allow authenticated users to read and update archon_tasks; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Allow authenticated users to read and update archon_tasks" ON public.archon_tasks TO authenticated USING (true);

CREATE POLICY "Allow system to insert tasks" ON public.archon_tasks FOR INSERT WITH CHECK (true);


--
-- Name: archon_document_versions Allow authenticated users to read archon_document_versions; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Allow authenticated users to read archon_document_versions" ON public.archon_document_versions FOR SELECT TO authenticated USING (true);


--
-- Name: archon_prompts Allow authenticated users to read archon_prompts; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Allow authenticated users to read archon_prompts" ON public.archon_prompts FOR SELECT TO authenticated USING (true);


--
-- Name: profiles Allow authenticated users to read profiles; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Allow authenticated users to read profiles" ON public.profiles FOR SELECT TO authenticated USING (true);


--
-- Name: vendors Allow authenticated users to select vendors; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Allow authenticated users to select vendors" ON public.vendors FOR SELECT TO authenticated USING (true);


--
-- Name: vendors Allow authenticated users to update vendors; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Allow authenticated users to update vendors" ON public.vendors FOR UPDATE TO authenticated USING (true);




--
-- Name: leads Allow authenticated users to view leads; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Allow authenticated users to view leads" ON public.leads FOR SELECT USING ((auth.role() = 'authenticated'::text));

CREATE POLICY "Allow system to insert leads" ON public.leads FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow system to update leads" ON public.leads FOR UPDATE USING (true);


--
-- Name: proposed_changes Allow authenticated users to view proposals; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Allow authenticated users to view proposals" ON public.proposed_changes FOR SELECT USING ((auth.role() = 'authenticated'::text));


--
-- Name: proposed_changes Allow full access to admins; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Allow full access to admins" ON public.proposed_changes USING (((auth.jwt() ->> 'role'::text) = 'service_role'::text));


--
-- Name: archon_extraction_schemas Allow managers and admins to manage schemas; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Allow managers and admins to manage schemas" ON public.archon_extraction_schemas USING (((auth.role() = 'service_role'::text) OR (( SELECT profiles.role
   FROM public.profiles
  WHERE (profiles.id = (auth.uid())::text)) = ANY (ARRAY['manager'::text, 'admin'::text, 'system_admin'::text]))));


--
-- Name: archon_ethics_events Allow managers and admins to view ethics logs; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Allow managers and admins to view ethics logs" ON public.archon_ethics_events FOR SELECT USING (((auth.role() = 'service_role'::text) OR (( SELECT profiles.role
   FROM public.profiles
  WHERE (profiles.id = (auth.uid())::text)) = ANY (ARRAY['manager'::text, 'system_admin'::text]))));


--
-- Name: marketing_trends Allow marketing view; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Allow marketing view" ON public.marketing_trends FOR SELECT TO authenticated USING ((EXISTS ( SELECT 1
   FROM public.profiles
  WHERE ((profiles.id = (auth.uid())::text) AND (profiles.role = ANY (ARRAY['marketing'::text, 'manager'::text, 'admin'::text, 'system_admin'::text]))))));


--
-- Name: archon_code_examples Allow public read access to archon_code_examples; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Allow public read access to archon_code_examples" ON public.archon_code_examples FOR SELECT USING (true);


--
-- Name: archon_crawled_pages Allow public read access to archon_crawled_pages; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Allow public read access to archon_crawled_pages" ON public.archon_crawled_pages FOR SELECT USING (true);


--
-- Name: archon_sources Allow public read access to archon_sources; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Allow public read access to archon_sources" ON public.archon_sources FOR SELECT USING (true);


--
-- Name: blog_posts Allow public read access to blog_posts; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Allow public read access to blog_posts" ON public.blog_posts FOR SELECT USING (true);


--
-- Name: archon_settings Allow service role full access; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Allow service role full access" ON public.archon_settings USING ((auth.role() = 'service_role'::text));


--
-- Name: archon_document_versions Allow service role full access to archon_document_versions; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Allow service role full access to archon_document_versions" ON public.archon_document_versions USING ((auth.role() = 'service_role'::text));


--
-- Name: archon_project_sources Allow service role full access to archon_project_sources; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Allow service role full access to archon_project_sources" ON public.archon_project_sources USING ((auth.role() = 'service_role'::text));


--
-- Name: archon_projects Allow service role full access to archon_projects; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Allow service role full access to archon_projects" ON public.archon_projects USING ((auth.role() = 'service_role'::text));


--
-- Name: archon_prompts Allow service role full access to archon_prompts; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Allow service role full access to archon_prompts" ON public.archon_prompts USING ((auth.role() = 'service_role'::text));


--
-- Name: archon_tasks Allow service role full access to archon_tasks; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Allow service role full access to archon_tasks" ON public.archon_tasks USING ((auth.role() = 'service_role'::text));


--
-- Name: profiles Allow service role full access to profiles; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Allow service role full access to profiles" ON public.profiles USING ((auth.role() = 'service_role'::text));


--
-- Name: archon_ethics_events Allow service role to insert ethics logs; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Allow service role to insert ethics logs" ON public.archon_ethics_events FOR INSERT WITH CHECK ((auth.role() = 'service_role'::text));


--
-- Name: archon_logs Allow system logging; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Allow system logging" ON public.archon_logs FOR INSERT TO authenticated WITH CHECK (true);



--
-- Name: archon_prompts Enable read access for all authenticated users; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Enable read access for all authenticated users" ON public.archon_prompts FOR SELECT TO authenticated USING (true);


--
-- Name: archon_prompts Enable write access for admins; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Enable write access for admins" ON public.archon_prompts FOR UPDATE TO authenticated USING ((EXISTS ( SELECT 1
   FROM public.profiles
  WHERE ((profiles.id = (auth.uid())::text) AND (profiles.role = ANY (ARRAY['system_admin'::text, 'admin'::text])))))) WITH CHECK ((EXISTS ( SELECT 1
   FROM public.profiles
  WHERE ((profiles.id = (auth.uid())::text) AND (profiles.role = ANY (ARRAY['system_admin'::text, 'admin'::text]))))));


--
-- Name: archon_settings Manager can update non-protected settings; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Manager can update non-protected settings" ON public.archon_settings FOR UPDATE USING (((( SELECT profiles.role
   FROM public.profiles
  WHERE (profiles.id = (auth.uid())::text)) = 'manager'::text) AND (is_system_protected = false)));


--
-- Name: archon_crawler_targets Managers and Admins can view crawler targets; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Managers and Admins can view crawler targets" ON public.archon_crawler_targets FOR SELECT USING ((( SELECT profiles.role
   FROM public.profiles
  WHERE (profiles.id = (auth.uid())::text)) = ANY (ARRAY['admin'::text, 'system_admin'::text, 'manager'::text])));


--
-- Name: archon_prompts Managers can update business prompts; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Managers can update business prompts" ON public.archon_prompts FOR UPDATE USING (((( SELECT profiles.role
   FROM public.profiles
  WHERE (profiles.id = (auth.uid())::text)) = 'manager'::text) AND (is_system_protected = false)));


--
-- Name: token_usage Managers can view all token usage; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Managers can view all token usage" ON public.token_usage FOR SELECT USING ((EXISTS ( SELECT 1
   FROM public.profiles
  WHERE ((profiles.id = (auth.uid())::text) AND (profiles.role = 'manager'::text)))));


--
-- Name: blog_posts Marketing and Admins can update blog metadata; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Marketing and Admins can update blog metadata" ON public.blog_posts FOR UPDATE USING ((( SELECT profiles.role
   FROM public.profiles
  WHERE (profiles.id = (auth.uid())::text)) = ANY (ARRAY['marketing'::text, 'manager'::text, 'admin'::text, 'system_admin'::text])));


--
-- Name: leads Marketing view story candidates; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Marketing view story candidates" ON public.leads FOR SELECT TO authenticated USING (((((auth.jwt() ->> 'role'::text) = 'marketing'::text) OR (EXISTS ( SELECT 1
   FROM public.profiles
  WHERE ((profiles.id = (auth.uid())::text) AND (profiles.role = 'marketing'::text))))) AND ((status = 'WON'::text) OR (enrichment_score >= 80))));


--
-- Name: visit_logs Marketing view story logs; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Marketing view story logs" ON public.visit_logs FOR SELECT TO authenticated USING (((EXISTS ( SELECT 1
   FROM public.leads
  WHERE ((leads.id = visit_logs.lead_id) AND ((leads.status = 'WON'::text) OR (leads.enrichment_score >= 80))))) AND (((auth.jwt() ->> 'role'::text) = 'marketing'::text) OR (EXISTS ( SELECT 1
   FROM public.profiles
  WHERE ((profiles.id = (auth.uid())::text) AND (profiles.role = 'marketing'::text)))))));


--
-- Name: archon_crawler_targets Only Admins can manage crawler targets; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Only Admins can manage crawler targets" ON public.archon_crawler_targets USING ((( SELECT profiles.role
   FROM public.profiles
  WHERE (profiles.id = (auth.uid())::text)) = ANY (ARRAY['admin'::text, 'system_admin'::text])));


--
-- Name: attendance_logs Users can insert own attendance; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Users can insert own attendance" ON public.attendance_logs FOR INSERT WITH CHECK ((auth.uid() = user_id));


--
-- Name: visit_logs Users can insert own visits; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Users can insert own visits" ON public.visit_logs FOR INSERT TO authenticated WITH CHECK ((auth.uid() = user_id));


--
-- Name: attendance_logs Users can update own attendance; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Users can update own attendance" ON public.attendance_logs FOR UPDATE USING ((auth.uid() = user_id));


--
-- Name: attendance_logs Users can view own attendance; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Users can view own attendance" ON public.attendance_logs FOR SELECT USING ((auth.uid() = user_id));


--
-- Name: visit_logs Users can view own visits; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Users can view own visits" ON public.visit_logs FOR SELECT TO authenticated USING (((auth.uid() = user_id) OR (EXISTS ( SELECT 1
   FROM public.profiles
  WHERE ((profiles.id = (auth.uid())::text) AND (profiles.role = ANY (ARRAY['admin'::text, 'manager'::text, 'system_admin'::text])))))));


--
-- Name: token_usage Users can view their own usage; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Users can view their own usage" ON public.token_usage FOR SELECT USING ((auth.uid() = user_id));


--
-- Name: archon_sources admin_all_sources; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY admin_all_sources ON public.archon_sources TO authenticated USING ((EXISTS ( SELECT 1
   FROM public.profiles
  WHERE ((profiles.id = (auth.uid())::text) AND (profiles.role = ANY (ARRAY['system_admin'::text, 'admin'::text]))))));


--
-- Name: archon_code_examples; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.archon_code_examples ENABLE ROW LEVEL SECURITY;

--
-- Name: archon_crawled_pages; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.archon_crawled_pages ENABLE ROW LEVEL SECURITY;

--
-- Name: archon_crawler_targets; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.archon_crawler_targets ENABLE ROW LEVEL SECURITY;

--
-- Name: archon_document_versions; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.archon_document_versions ENABLE ROW LEVEL SECURITY;

--
-- Name: archon_ethics_events; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.archon_ethics_events ENABLE ROW LEVEL SECURITY;

--
-- Name: archon_extraction_schemas; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.archon_extraction_schemas ENABLE ROW LEVEL SECURITY;

--
-- Name: archon_logs; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.archon_logs ENABLE ROW LEVEL SECURITY;

--
-- Name: archon_project_sources; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.archon_project_sources ENABLE ROW LEVEL SECURITY;

--
-- Name: archon_projects; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.archon_projects ENABLE ROW LEVEL SECURITY;

--
-- Name: archon_prompts; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.archon_prompts ENABLE ROW LEVEL SECURITY;

--
-- Name: archon_settings; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.archon_settings ENABLE ROW LEVEL SECURITY;

--
-- Name: archon_sources; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.archon_sources ENABLE ROW LEVEL SECURITY;

--
-- Name: archon_tasks; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.archon_tasks ENABLE ROW LEVEL SECURITY;

--
-- Name: attendance_logs; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.attendance_logs ENABLE ROW LEVEL SECURITY;

--
-- Name: blog_posts; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.blog_posts ENABLE ROW LEVEL SECURITY;

--
-- Name: archon_code_examples child_code_isolation; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY child_code_isolation ON public.archon_code_examples FOR SELECT TO authenticated USING ((EXISTS ( SELECT 1
   FROM public.archon_sources s
  WHERE (s.source_id = archon_code_examples.source_id))));


--
-- Name: archon_crawled_pages child_pages_isolation; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY child_pages_isolation ON public.archon_crawled_pages FOR SELECT TO authenticated USING ((EXISTS ( SELECT 1
   FROM public.archon_sources s
  WHERE (s.source_id = archon_crawled_pages.source_id))));



--
-- Name: archon_sources dept_isolation_read; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY dept_isolation_read ON public.archon_sources FOR SELECT TO authenticated USING ((((metadata ->> 'department'::text) = 'Public'::text) OR ((metadata ->> 'department'::text) IS NULL) OR ((metadata ->> 'department'::text) = ( SELECT profiles.department
   FROM public.profiles
  WHERE (profiles.id = (auth.uid())::text))) OR (EXISTS ( SELECT 1
   FROM public.profiles
  WHERE ((profiles.id = (auth.uid())::text) AND (profiles.role = ANY (ARRAY['manager'::text, 'project_manager'::text])))))));


--
-- Name: archon_sources dept_isolation_write; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY dept_isolation_write ON public.archon_sources FOR INSERT TO authenticated WITH CHECK (((metadata ->> 'department'::text) = ( SELECT profiles.department
   FROM public.profiles
  WHERE (profiles.id = (auth.uid())::text))));


--
-- Name: gemini_logs; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.gemini_logs ENABLE ROW LEVEL SECURITY;

--
-- Name: leads; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.leads ENABLE ROW LEVEL SECURITY;


--
-- Name: marketing_trends; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.marketing_trends ENABLE ROW LEVEL SECURITY;

--
-- Name: profiles; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

--
-- Name: proposed_changes; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.proposed_changes ENABLE ROW LEVEL SECURITY;


--
-- Name: token_usage; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.token_usage ENABLE ROW LEVEL SECURITY;

--
-- Name: vendors; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.vendors ENABLE ROW LEVEL SECURITY;

--
-- Name: visit_logs; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.visit_logs ENABLE ROW LEVEL SECURITY;

--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE USAGE ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO PUBLIC;
GRANT USAGE ON SCHEMA public TO anon;
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT USAGE ON SCHEMA public TO service_role;


--
-- Name: TABLE archon_code_examples; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.archon_code_examples TO authenticated;
GRANT ALL ON TABLE public.archon_code_examples TO service_role;


--
-- Name: TABLE archon_crawled_pages; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.archon_crawled_pages TO authenticated;
GRANT ALL ON TABLE public.archon_crawled_pages TO service_role;


--
-- Name: TABLE archon_crawler_targets; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.archon_crawler_targets TO authenticated;
GRANT ALL ON TABLE public.archon_crawler_targets TO service_role;


--
-- Name: TABLE archon_document_versions; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.archon_document_versions TO authenticated;
GRANT ALL ON TABLE public.archon_document_versions TO service_role;


--
-- Name: TABLE archon_ethics_events; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.archon_ethics_events TO authenticated;
GRANT ALL ON TABLE public.archon_ethics_events TO service_role;


--
-- Name: TABLE archon_extraction_schemas; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.archon_extraction_schemas TO authenticated;
GRANT ALL ON TABLE public.archon_extraction_schemas TO service_role;


--
-- Name: TABLE archon_logs; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.archon_logs TO authenticated;
GRANT ALL ON TABLE public.archon_logs TO service_role;


--
-- Name: TABLE archon_project_sources; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.archon_project_sources TO authenticated;
GRANT ALL ON TABLE public.archon_project_sources TO service_role;


--
-- Name: TABLE archon_projects; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.archon_projects TO authenticated;
GRANT ALL ON TABLE public.archon_projects TO service_role;


--
-- Name: TABLE archon_prompts; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.archon_prompts TO authenticated;
GRANT ALL ON TABLE public.archon_prompts TO service_role;


--
-- Name: TABLE archon_settings; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.archon_settings TO authenticated;
GRANT ALL ON TABLE public.archon_settings TO service_role;


--
-- Name: TABLE archon_sources; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.archon_sources TO authenticated;
GRANT ALL ON TABLE public.archon_sources TO service_role;


--
-- Name: TABLE archon_tasks; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.archon_tasks TO authenticated;
GRANT ALL ON TABLE public.archon_tasks TO service_role;


--
-- Name: TABLE attendance_logs; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.attendance_logs TO authenticated;
GRANT ALL ON TABLE public.attendance_logs TO service_role;


--
-- Name: TABLE blog_posts; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.blog_posts TO authenticated;
GRANT ALL ON TABLE public.blog_posts TO service_role;




--
-- Name: TABLE gemini_logs; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.gemini_logs TO authenticated;
GRANT ALL ON TABLE public.gemini_logs TO service_role;


--
-- Name: TABLE leads; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.leads TO authenticated;
GRANT ALL ON TABLE public.leads TO service_role;




--
-- Name: TABLE marketing_trends; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.marketing_trends TO authenticated;
GRANT ALL ON TABLE public.marketing_trends TO service_role;


--
-- Name: TABLE profiles; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.profiles TO authenticated;
GRANT ALL ON TABLE public.profiles TO service_role;


--
-- Name: TABLE proposed_changes; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.proposed_changes TO authenticated;
GRANT ALL ON TABLE public.proposed_changes TO service_role;




--
-- Name: TABLE token_usage; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.token_usage TO authenticated;
GRANT ALL ON TABLE public.token_usage TO service_role;


--
-- Name: TABLE vendors; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.vendors TO authenticated;
GRANT ALL ON TABLE public.vendors TO service_role;


--
-- Name: TABLE visit_logs; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.visit_logs TO authenticated;
GRANT ALL ON TABLE public.visit_logs TO service_role;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: public; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON TABLES TO postgres;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON TABLES TO authenticated;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON TABLES TO service_role;


--
-- PostgreSQL database dump complete
--



-- Source: 27_enable_missing_rls.sql
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


