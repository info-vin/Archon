-- Name: archon_code_examples_embedding_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX archon_code_examples_embedding_idx ON public.archon_code_examples USING ivfflat (embedding public.vector_cosine_ops);


--
-- Name: archon_crawled_pages_embedding_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX archon_crawled_pages_embedding_idx ON public.archon_crawled_pages USING ivfflat (embedding public.vector_cosine_ops);


--
-- Name: idx_archon_code_examples_content_search; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_archon_code_examples_content_search ON public.archon_code_examples USING gin (content_search_vector);


--
-- Name: idx_archon_code_examples_content_trgm; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_archon_code_examples_content_trgm ON public.archon_code_examples USING gin (content public.gin_trgm_ops);


--
-- Name: idx_archon_code_examples_metadata; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_archon_code_examples_metadata ON public.archon_code_examples USING gin (metadata);


--
-- Name: idx_archon_code_examples_source_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_archon_code_examples_source_id ON public.archon_code_examples USING btree (source_id);


--
-- Name: idx_archon_code_examples_summary_trgm; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_archon_code_examples_summary_trgm ON public.archon_code_examples USING gin (summary public.gin_trgm_ops);


--
-- Name: idx_archon_crawled_pages_content_search; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_archon_crawled_pages_content_search ON public.archon_crawled_pages USING gin (content_search_vector);


--
-- Name: idx_archon_crawled_pages_content_trgm; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_archon_crawled_pages_content_trgm ON public.archon_crawled_pages USING gin (content public.gin_trgm_ops);


--
-- Name: idx_archon_crawled_pages_metadata; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_archon_crawled_pages_metadata ON public.archon_crawled_pages USING gin (metadata);


--
-- Name: idx_archon_crawled_pages_source_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_archon_crawled_pages_source_id ON public.archon_crawled_pages USING btree (source_id);


--
-- Name: idx_archon_document_versions_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_archon_document_versions_created_at ON public.archon_document_versions USING btree (created_at);


--
-- Name: idx_archon_document_versions_field_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_archon_document_versions_field_name ON public.archon_document_versions USING btree (field_name);


--
-- Name: idx_archon_document_versions_project_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_archon_document_versions_project_id ON public.archon_document_versions USING btree (project_id);


--
-- Name: idx_archon_document_versions_task_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_archon_document_versions_task_id ON public.archon_document_versions USING btree (task_id);


--
-- Name: idx_archon_document_versions_version_number; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_archon_document_versions_version_number ON public.archon_document_versions USING btree (version_number);


--
-- Name: idx_archon_logs_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_archon_logs_created_at ON public.archon_logs USING btree (created_at DESC);


--
-- Name: idx_archon_logs_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_archon_logs_user_id ON public.archon_logs USING btree (user_id);


--
-- Name: idx_archon_project_sources_project_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_archon_project_sources_project_id ON public.archon_project_sources USING btree (project_id);


--
-- Name: idx_archon_project_sources_source_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_archon_project_sources_source_id ON public.archon_project_sources USING btree (source_id);


--
-- Name: idx_archon_prompts_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_archon_prompts_name ON public.archon_prompts USING btree (prompt_name);


--
-- Name: idx_archon_settings_category; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_archon_settings_category ON public.archon_settings USING btree (category);


--
-- Name: idx_archon_settings_key; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_archon_settings_key ON public.archon_settings USING btree (key);


--
-- Name: idx_archon_sources_display_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_archon_sources_display_name ON public.archon_sources USING btree (source_display_name);


--
-- Name: idx_archon_sources_knowledge_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_archon_sources_knowledge_type ON public.archon_sources USING btree (((metadata ->> 'knowledge_type'::text)));


--
-- Name: idx_archon_sources_metadata; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_archon_sources_metadata ON public.archon_sources USING gin (metadata);


--
-- Name: idx_archon_sources_title; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_archon_sources_title ON public.archon_sources USING btree (title);


--
-- Name: idx_archon_sources_url; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_archon_sources_url ON public.archon_sources USING btree (source_url);


--
-- Name: idx_archon_tasks_archived; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_archon_tasks_archived ON public.archon_tasks USING btree (archived);


--
-- Name: idx_archon_tasks_archived_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_archon_tasks_archived_at ON public.archon_tasks USING btree (archived_at);


--
-- Name: idx_archon_tasks_assignee; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_archon_tasks_assignee ON public.archon_tasks USING btree (assignee);


--
-- Name: idx_archon_tasks_assignee_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_archon_tasks_assignee_id ON public.archon_tasks USING btree (assignee_id);


--
-- Name: idx_archon_tasks_order; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_archon_tasks_order ON public.archon_tasks USING btree (task_order);


--
-- Name: idx_archon_tasks_project_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_archon_tasks_project_id ON public.archon_tasks USING btree (project_id);


--
-- Name: idx_archon_tasks_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_archon_tasks_status ON public.archon_tasks USING btree (status);


--
-- Name: idx_attendance_user_time; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_attendance_user_time ON public.attendance_logs USING btree (user_id, clock_in_time DESC);


--
-- Name: idx_blog_posts_metadata; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_blog_posts_metadata ON public.blog_posts USING gin (generation_metadata);


--
-- Name: idx_leads_source_url; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX idx_leads_source_url ON public.leads USING btree (source_job_url);


--
-- Name: idx_proposed_changes_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_proposed_changes_status ON public.proposed_changes USING btree (status);


--
-- Name: idx_proposed_changes_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_proposed_changes_type ON public.proposed_changes USING btree (type);


--
-- Name: idx_token_usage_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_token_usage_created_at ON public.token_usage USING btree (created_at DESC);


--
-- Name: idx_token_usage_model; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_token_usage_model ON public.token_usage USING btree (model);


--
-- Name: idx_token_usage_request_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_token_usage_request_id ON public.token_usage USING btree (request_id);


--
-- Name: idx_token_usage_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_token_usage_user_id ON public.token_usage USING btree (user_id);


--
