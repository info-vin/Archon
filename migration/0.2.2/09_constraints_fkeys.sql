-- Name: archon_code_examples archon_code_examples_source_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archon_code_examples
    ADD CONSTRAINT archon_code_examples_source_id_fkey FOREIGN KEY (source_id) REFERENCES public.archon_sources(source_id);


--
-- Name: archon_crawled_pages archon_crawled_pages_source_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archon_crawled_pages
    ADD CONSTRAINT archon_crawled_pages_source_id_fkey FOREIGN KEY (source_id) REFERENCES public.archon_sources(source_id);


--
-- Name: archon_document_versions archon_document_versions_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archon_document_versions
    ADD CONSTRAINT archon_document_versions_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.archon_projects(id) ON DELETE CASCADE;


--
-- Name: archon_document_versions archon_document_versions_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archon_document_versions
    ADD CONSTRAINT archon_document_versions_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.archon_tasks(id) ON DELETE CASCADE;


--
-- Name: archon_extraction_schemas archon_extraction_schemas_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archon_extraction_schemas
    ADD CONSTRAINT archon_extraction_schemas_created_by_fkey FOREIGN KEY (created_by) REFERENCES auth.users(id);


--
-- Name: archon_project_sources archon_project_sources_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archon_project_sources
    ADD CONSTRAINT archon_project_sources_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.archon_projects(id) ON DELETE CASCADE;


--
-- Name: archon_tasks archon_tasks_parent_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archon_tasks
    ADD CONSTRAINT archon_tasks_parent_task_id_fkey FOREIGN KEY (parent_task_id) REFERENCES public.archon_tasks(id) ON DELETE CASCADE;


--
-- Name: archon_tasks archon_tasks_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archon_tasks
    ADD CONSTRAINT archon_tasks_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.archon_projects(id) ON DELETE CASCADE;


--
-- Name: attendance_logs attendance_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.attendance_logs
    ADD CONSTRAINT attendance_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: blog_posts blog_posts_source_lead_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.blog_posts
    ADD CONSTRAINT blog_posts_source_lead_id_fkey FOREIGN KEY (source_lead_id) REFERENCES public.leads(id) ON DELETE SET NULL;


--
-- Name: archon_tasks fk_archon_tasks_assignee; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archon_tasks
    ADD CONSTRAINT fk_archon_tasks_assignee FOREIGN KEY (assignee_id) REFERENCES public.profiles(id) ON DELETE SET NULL;


--
-- Name: blog_posts fk_blog_posts_lead; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.blog_posts
    ADD CONSTRAINT fk_blog_posts_lead FOREIGN KEY (lead_id) REFERENCES public.leads(id) ON DELETE SET NULL;


--
-- Name: leads leads_assigned_sales_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.leads
    ADD CONSTRAINT leads_assigned_sales_id_fkey FOREIGN KEY (assigned_sales_id) REFERENCES auth.users(id);


--
-- Name: leads leads_linked_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.leads
    ADD CONSTRAINT leads_linked_project_id_fkey FOREIGN KEY (linked_project_id) REFERENCES public.archon_projects(id);


--
-- Name: market_insights market_insights_related_blog_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.market_insights
    ADD CONSTRAINT market_insights_related_blog_id_fkey FOREIGN KEY (related_blog_id) REFERENCES public.blog_posts(id);


--
-- Name: proposed_changes proposed_changes_approved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.proposed_changes
    ADD CONSTRAINT proposed_changes_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES auth.users(id);


--
-- Name: subscriptions subscriptions_lead_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.subscriptions
    ADD CONSTRAINT subscriptions_lead_id_fkey FOREIGN KEY (lead_id) REFERENCES public.leads(id);


--
-- Name: token_usage token_usage_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.token_usage
    ADD CONSTRAINT token_usage_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id);


--
-- Name: vendors vendors_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vendors
    ADD CONSTRAINT vendors_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES auth.users(id);


--
-- Name: visit_logs visit_logs_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.visit_logs
    ADD CONSTRAINT visit_logs_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customers(id);


--
-- Name: visit_logs visit_logs_lead_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.visit_logs
    ADD CONSTRAINT visit_logs_lead_id_fkey FOREIGN KEY (lead_id) REFERENCES public.leads(id);


--
-- Name: visit_logs visit_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.visit_logs
    ADD CONSTRAINT visit_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id);


--
