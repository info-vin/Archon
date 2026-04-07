-- Name: archon_code_examples archon_code_examples_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archon_code_examples
    ADD CONSTRAINT archon_code_examples_pkey PRIMARY KEY (id);


--
-- Name: archon_code_examples archon_code_examples_url_chunk_number_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archon_code_examples
    ADD CONSTRAINT archon_code_examples_url_chunk_number_key UNIQUE (url, chunk_number);


--
-- Name: archon_crawled_pages archon_crawled_pages_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archon_crawled_pages
    ADD CONSTRAINT archon_crawled_pages_pkey PRIMARY KEY (id);


--
-- Name: archon_crawled_pages archon_crawled_pages_url_chunk_number_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archon_crawled_pages
    ADD CONSTRAINT archon_crawled_pages_url_chunk_number_key UNIQUE (url, chunk_number);


--
-- Name: archon_crawler_targets archon_crawler_targets_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archon_crawler_targets
    ADD CONSTRAINT archon_crawler_targets_pkey PRIMARY KEY (id);


--
-- Name: archon_crawler_targets archon_crawler_targets_target_url_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archon_crawler_targets
    ADD CONSTRAINT archon_crawler_targets_target_url_key UNIQUE (target_url);


--
-- Name: archon_document_versions archon_document_versions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archon_document_versions
    ADD CONSTRAINT archon_document_versions_pkey PRIMARY KEY (id);


--
-- Name: archon_document_versions archon_document_versions_project_id_task_id_field_name_vers_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archon_document_versions
    ADD CONSTRAINT archon_document_versions_project_id_task_id_field_name_vers_key UNIQUE (project_id, task_id, field_name, version_number);


--
-- Name: archon_ethics_events archon_ethics_events_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archon_ethics_events
    ADD CONSTRAINT archon_ethics_events_pkey PRIMARY KEY (id);


--
-- Name: archon_extraction_schemas archon_extraction_schemas_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archon_extraction_schemas
    ADD CONSTRAINT archon_extraction_schemas_pkey PRIMARY KEY (id);


--
-- Name: archon_logs archon_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archon_logs
    ADD CONSTRAINT archon_logs_pkey PRIMARY KEY (id);


--
-- Name: archon_project_sources archon_project_sources_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archon_project_sources
    ADD CONSTRAINT archon_project_sources_pkey PRIMARY KEY (id);


--
-- Name: archon_project_sources archon_project_sources_project_id_source_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archon_project_sources
    ADD CONSTRAINT archon_project_sources_project_id_source_id_key UNIQUE (project_id, source_id);


--
-- Name: archon_projects archon_projects_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archon_projects
    ADD CONSTRAINT archon_projects_pkey PRIMARY KEY (id);


--
-- Name: archon_prompts archon_prompts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archon_prompts
    ADD CONSTRAINT archon_prompts_pkey PRIMARY KEY (id);


--
-- Name: archon_prompts archon_prompts_prompt_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archon_prompts
    ADD CONSTRAINT archon_prompts_prompt_name_key UNIQUE (prompt_name);


--
-- Name: archon_settings archon_settings_key_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archon_settings
    ADD CONSTRAINT archon_settings_key_key UNIQUE (key);


--
-- Name: archon_settings archon_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archon_settings
    ADD CONSTRAINT archon_settings_pkey PRIMARY KEY (id);


--
-- Name: archon_sources archon_sources_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archon_sources
    ADD CONSTRAINT archon_sources_pkey PRIMARY KEY (source_id);


--
-- Name: archon_tasks archon_tasks_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archon_tasks
    ADD CONSTRAINT archon_tasks_pkey PRIMARY KEY (id);


--
-- Name: attendance_logs attendance_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.attendance_logs
    ADD CONSTRAINT attendance_logs_pkey PRIMARY KEY (id);


--
-- Name: blog_posts blog_posts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.blog_posts
    ADD CONSTRAINT blog_posts_pkey PRIMARY KEY (id);


--
-- Name: customers customers_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT customers_pkey PRIMARY KEY (id);


--
-- Name: gemini_logs gemini_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.gemini_logs
    ADD CONSTRAINT gemini_logs_pkey PRIMARY KEY (id);


--
-- Name: leads leads_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.leads
    ADD CONSTRAINT leads_pkey PRIMARY KEY (id);


--
-- Name: market_insights market_insights_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.market_insights
    ADD CONSTRAINT market_insights_pkey PRIMARY KEY (id);


--
-- Name: marketing_trends marketing_trends_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.marketing_trends
    ADD CONSTRAINT marketing_trends_pkey PRIMARY KEY (id);


--
-- Name: profiles profiles_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.profiles
    ADD CONSTRAINT profiles_email_key UNIQUE (email);


--
-- Name: profiles profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.profiles
    ADD CONSTRAINT profiles_pkey PRIMARY KEY (id);


--
-- Name: proposed_changes proposed_changes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.proposed_changes
    ADD CONSTRAINT proposed_changes_pkey PRIMARY KEY (id);


--
-- Name: subscriptions subscriptions_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.subscriptions
    ADD CONSTRAINT subscriptions_email_key UNIQUE (email);


--
-- Name: subscriptions subscriptions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.subscriptions
    ADD CONSTRAINT subscriptions_pkey PRIMARY KEY (id);


--
-- Name: token_usage token_usage_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.token_usage
    ADD CONSTRAINT token_usage_pkey PRIMARY KEY (id);


--
-- Name: vendors vendors_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vendors
    ADD CONSTRAINT vendors_pkey PRIMARY KEY (id);


--
-- Name: visit_logs visit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.visit_logs
    ADD CONSTRAINT visit_logs_pkey PRIMARY KEY (id);


--
