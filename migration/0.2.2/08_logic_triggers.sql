-- Name: archon_projects update_archon_projects_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_archon_projects_updated_at BEFORE UPDATE ON public.archon_projects FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: archon_prompts update_archon_prompts_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_archon_prompts_updated_at BEFORE UPDATE ON public.archon_prompts FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: archon_settings update_archon_settings_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_archon_settings_updated_at BEFORE UPDATE ON public.archon_settings FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: archon_tasks update_archon_tasks_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_archon_tasks_updated_at BEFORE UPDATE ON public.archon_tasks FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: blog_posts update_blog_posts_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_blog_posts_updated_at BEFORE UPDATE ON public.blog_posts FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: leads update_leads_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_leads_updated_at BEFORE UPDATE ON public.leads FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
