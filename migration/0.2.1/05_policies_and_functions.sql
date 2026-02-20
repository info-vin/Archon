--
-- Name: archive_task(uuid, text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE OR REPLACE FUNCTION public.archive_task(task_id_param uuid, archived_by_param text DEFAULT 'system'::text) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
DECLARE
    task_exists BOOLEAN;
BEGIN
    -- Check if task exists and is not already archived
    SELECT EXISTS(
        SELECT 1 FROM archon_tasks
        WHERE id = task_id_param AND archived = FALSE
    ) INTO task_exists;

    IF NOT task_exists THEN
        RETURN FALSE;
    END IF;

    -- Archive the task
    UPDATE archon_tasks
    SET
        archived = TRUE,
        archived_at = NOW(),
        archived_by = archived_by_param,
        updated_at = NOW()
    WHERE id = task_id_param;

    -- Also archive all subtasks
    UPDATE archon_tasks
    SET
        archived = TRUE,
        archived_at = NOW(),
        archived_by = archived_by_param,
        updated_at = NOW()
    WHERE parent_task_id = task_id_param AND archived = FALSE;

    RETURN TRUE;
END;
$$;


ALTER FUNCTION public.archive_task(task_id_param uuid, archived_by_param text) OWNER TO postgres;

--
-- Name: get_counts_by_source(text[]); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE OR REPLACE FUNCTION public.get_counts_by_source(source_ids_param text[]) RETURNS TABLE(source_id text, chunk_count bigint, code_example_count bigint)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        s.source_id,
        COALESCE(cp_counts.count, 0) AS chunk_count,
        COALESCE(ce_counts.count, 0) AS code_example_count
    FROM
        public.archon_sources s
    LEFT JOIN (
        SELECT
            p.source_id,
            COUNT(*) as count
        FROM
            public.archon_crawled_pages p
        WHERE
            p.source_id = ANY(source_ids_param)
        GROUP BY
            p.source_id
    ) AS cp_counts ON s.source_id = cp_counts.source_id
    LEFT JOIN (
        SELECT
            e.source_id,
            COUNT(*) as count
        FROM
            public.archon_code_examples e
        WHERE
            e.source_id = ANY(source_ids_param)
        GROUP BY
            e.source_id
    ) AS ce_counts ON s.source_id = ce_counts.source_id
    WHERE
        s.source_id = ANY(source_ids_param);
END;
$$;


ALTER FUNCTION public.get_counts_by_source(source_ids_param text[]) OWNER TO postgres;

--
-- Name: hybrid_search_archon_code_examples(public.vector, text, integer, jsonb, text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE OR REPLACE FUNCTION public.hybrid_search_archon_code_examples(query_embedding public.vector, query_text text, match_count integer DEFAULT 10, filter jsonb DEFAULT '{}'::jsonb, source_filter text DEFAULT NULL::text) RETURNS TABLE(id bigint, url character varying, chunk_number integer, content text, summary text, metadata jsonb, source_id text, similarity double precision, match_type text)
    LANGUAGE plpgsql
    AS $$
DECLARE
    max_vector_results INT;
    max_text_results INT;
BEGIN
    -- Calculate how many results to fetch from each search type
    max_vector_results := match_count;
    max_text_results := match_count;
    
    RETURN QUERY
    WITH vector_results AS (
        -- Vector similarity search
        SELECT 
            ce.id,
            ce.url,
            ce.chunk_number,
            ce.content,
            ce.summary,
            ce.metadata,
            ce.source_id,
            1 - (ce.embedding <=> query_embedding) AS vector_sim
        FROM archon_code_examples ce
        WHERE ce.metadata @> filter
            AND (source_filter IS NULL OR ce.source_id = source_filter)
            AND ce.embedding IS NOT NULL
        ORDER BY ce.embedding <=> query_embedding
        LIMIT max_vector_results
    ),
    text_results AS (
        -- Full-text search with ranking (searches both content and summary)
        SELECT 
            ce.id,
            ce.url,
            ce.chunk_number,
            ce.content,
            ce.summary,
            ce.metadata,
            ce.source_id,
            ts_rank_cd(ce.content_search_vector, plainto_tsquery('english', query_text)) AS text_sim
        FROM archon_code_examples ce
        WHERE ce.metadata @> filter
            AND (source_filter IS NULL OR ce.source_id = source_filter)
            AND ce.content_search_vector @@ plainto_tsquery('english', query_text)
        ORDER BY text_sim DESC
        LIMIT max_text_results
    ),
    combined_results AS (
        -- Combine results from both searches
        SELECT 
            COALESCE(v.id, t.id) AS id,
            COALESCE(v.url, t.url) AS url,
            COALESCE(v.chunk_number, t.chunk_number) AS chunk_number,
            COALESCE(v.content, t.content) AS content,
            COALESCE(v.summary, t.summary) AS summary,
            COALESCE(v.metadata, t.metadata) AS metadata,
            COALESCE(v.source_id, t.source_id) AS source_id,
            COALESCE(v.vector_sim, t.text_sim, 0)::float8 AS similarity,
            CASE 
                WHEN v.id IS NOT NULL AND t.id IS NOT NULL THEN 'hybrid'
                WHEN v.id IS NOT NULL THEN 'vector'
                ELSE 'keyword'
            END AS match_type
        FROM vector_results v
        FULL OUTER JOIN text_results t ON v.id = t.id
    )
    SELECT * FROM combined_results
    ORDER BY similarity DESC
    LIMIT match_count;
END;
$$;


ALTER FUNCTION public.hybrid_search_archon_code_examples(query_embedding public.vector, query_text text, match_count integer, filter jsonb, source_filter text) OWNER TO postgres;

--
-- Name: FUNCTION hybrid_search_archon_code_examples(query_embedding public.vector, query_text text, match_count integer, filter jsonb, source_filter text); Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON FUNCTION public.hybrid_search_archon_code_examples(query_embedding public.vector, query_text text, match_count integer, filter jsonb, source_filter text) IS 'Performs hybrid search on code examples combining vector similarity and full-text search';


--
-- Name: hybrid_search_archon_crawled_pages(public.vector, text, integer, jsonb, text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE OR REPLACE FUNCTION public.hybrid_search_archon_crawled_pages(query_embedding public.vector, query_text text, match_count integer DEFAULT 10, filter jsonb DEFAULT '{}'::jsonb, source_filter text DEFAULT NULL::text) RETURNS TABLE(id bigint, url character varying, chunk_number integer, content text, metadata jsonb, source_id text, similarity double precision, match_type text)
    LANGUAGE plpgsql
    AS $$
DECLARE
    max_vector_results INT;
    max_text_results INT;
BEGIN
    -- Calculate how many results to fetch from each search type
    max_vector_results := match_count;
    max_text_results := match_count;
    
    RETURN QUERY
    WITH vector_results AS (
        -- Vector similarity search
        SELECT 
            cp.id,
            cp.url,
            cp.chunk_number,
            cp.content,
            cp.metadata,
            cp.source_id,
            1 - (cp.embedding <=> query_embedding) AS vector_sim
        FROM archon_crawled_pages cp
        WHERE cp.metadata @> filter
            AND (source_filter IS NULL OR cp.source_id = source_filter)
            AND cp.embedding IS NOT NULL
        ORDER BY cp.embedding <=> query_embedding
        LIMIT max_vector_results
    ),
    text_results AS (
        -- Full-text search with ranking
        SELECT 
            cp.id,
            cp.url,
            cp.chunk_number,
            cp.content,
            cp.metadata,
            cp.source_id,
            ts_rank_cd(cp.content_search_vector, plainto_tsquery('english', query_text)) AS text_sim
        FROM archon_crawled_pages cp
        WHERE cp.metadata @> filter
            AND (source_filter IS NULL OR cp.source_id = source_filter)
            AND cp.content_search_vector @@ plainto_tsquery('english', query_text)
        ORDER BY text_sim DESC
        LIMIT max_text_results
    ),
    combined_results AS (
        -- Combine results from both searches
        SELECT 
            COALESCE(v.id, t.id) AS id,
            COALESCE(v.url, t.url) AS url,
            COALESCE(v.chunk_number, t.chunk_number) AS chunk_number,
            COALESCE(v.content, t.content) AS content,
            COALESCE(v.metadata, t.metadata) AS metadata,
            COALESCE(v.source_id, t.source_id) AS source_id,
            COALESCE(v.vector_sim, t.text_sim, 0)::float8 AS similarity,
            CASE 
                WHEN v.id IS NOT NULL AND t.id IS NOT NULL THEN 'hybrid'
                WHEN v.id IS NOT NULL THEN 'vector'
                ELSE 'keyword'
            END AS match_type
        FROM vector_results v
        FULL OUTER JOIN text_results t ON v.id = t.id
    )
    SELECT * FROM combined_results
    ORDER BY similarity DESC
    LIMIT match_count;
END;
$$;


ALTER FUNCTION public.hybrid_search_archon_crawled_pages(query_embedding public.vector, query_text text, match_count integer, filter jsonb, source_filter text) OWNER TO postgres;

--
-- Name: FUNCTION hybrid_search_archon_crawled_pages(query_embedding public.vector, query_text text, match_count integer, filter jsonb, source_filter text); Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON FUNCTION public.hybrid_search_archon_crawled_pages(query_embedding public.vector, query_text text, match_count integer, filter jsonb, source_filter text) IS 'Performs hybrid search combining vector similarity and full-text search with configurable weighting';


--
-- Name: match_archon_code_examples(public.vector, integer, jsonb, text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE OR REPLACE FUNCTION public.match_archon_code_examples(query_embedding public.vector, match_count integer DEFAULT 10, filter jsonb DEFAULT '{}'::jsonb, source_filter text DEFAULT NULL::text) RETURNS TABLE(id bigint, url character varying, chunk_number integer, content text, summary text, metadata jsonb, source_id text, similarity double precision)
    LANGUAGE plpgsql
    AS $$
#variable_conflict use_column
BEGIN
  RETURN QUERY
  SELECT
    id,
    url,
    chunk_number,
    content,
    summary,
    metadata,
    source_id,
    1 - (archon_code_examples.embedding <=> query_embedding) AS similarity
  FROM archon_code_examples
  WHERE metadata @> filter
    AND (source_filter IS NULL OR source_id = source_filter)
  ORDER BY archon_code_examples.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;


ALTER FUNCTION public.match_archon_code_examples(query_embedding public.vector, match_count integer, filter jsonb, source_filter text) OWNER TO postgres;

--
-- Name: match_archon_crawled_pages(public.vector, integer, jsonb, text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE OR REPLACE FUNCTION public.match_archon_crawled_pages(query_embedding public.vector, match_count integer DEFAULT 10, filter jsonb DEFAULT '{}'::jsonb, source_filter text DEFAULT NULL::text) RETURNS TABLE(id bigint, url character varying, chunk_number integer, content text, metadata jsonb, source_id text, similarity double precision)
    LANGUAGE plpgsql
    AS $$
#variable_conflict use_column
BEGIN
  RETURN QUERY
  SELECT
    id,
    url,
    chunk_number,
    content,
    metadata,
    source_id,
    1 - (archon_crawled_pages.embedding <=> query_embedding) AS similarity
  FROM archon_crawled_pages
  WHERE metadata @> filter
    AND (source_filter IS NULL OR source_id = source_filter)
  ORDER BY archon_crawled_pages.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;


ALTER FUNCTION public.match_archon_crawled_pages(query_embedding public.vector, match_count integer, filter jsonb, source_filter text) OWNER TO postgres;

--
-- Name: reset_test_database(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE OR REPLACE FUNCTION public.reset_test_database() RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    TRUNCATE TABLE archon_tasks RESTART IDENTITY CASCADE;
    TRUNCATE TABLE archon_projects RESTART IDENTITY CASCADE;
    TRUNCATE TABLE archon_settings RESTART IDENTITY CASCADE;
    TRUNCATE TABLE profiles RESTART IDENTITY CASCADE;
    
    -- Add other tables here if seed_mock_data.sql starts inserting into them
    
    RAISE NOTICE 'Test database data cleared.';
END;
$$;


ALTER FUNCTION public.reset_test_database() OWNER TO postgres;

--
-- Name: seed_test_database(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE OR REPLACE FUNCTION public.seed_test_database() RETURNS void
    LANGUAGE plpgsql
    AS $$
DECLARE
    proj1_id UUID;
    proj2_id UUID;
BEGIN
    -- Seed for profiles table (MOCK_EMPLOYEES)
    INSERT INTO profiles (id, "employeeId", name, email, department, position, status, role, avatar) VALUES
    ('1', 'E1001', 'David Howard', 'admin@archon.com', 'IT', 'System Administrator', 'active', 'Admin', 'https://i.pravatar.cc/150?u=admin@archon.com'),
    ('2', 'E1002', 'Alice Johnson', 'alice@archon.com', 'Engineering', 'Project Manager', 'active', 'PM', 'https://i.pravatar.cc/150?u=alice@archon.com'),
    ('3', 'E1003', 'Bob Williams', 'bob@archon.com', 'Engineering', 'Frontend Developer', 'active', 'Engineer', 'https://i.pravatar.cc/150?u=bob@archon.com'),
    ('4', 'E1004', 'Charlie Brown', 'charlie@archon.com', 'Marketing', 'Marketing Specialist', 'active', 'Marketer', 'https://i.pravatar.cc/150?u=charlie@archon.com'),
    ('5', 'agent-mr-001', 'Market Researcher', 'market.researcher@archon.com', 'AI', 'Market Researcher', 'active', 'Market Researcher', 'https://i.pravatar.cc/150?u=agent-mr-001')
    ON CONFLICT (id) DO NOTHING;

    -- Seed for archon_projects table, ensuring idempotency
    -- Project 1: Archon Core Platform
    IF NOT EXISTS (SELECT 1 FROM archon_projects WHERE title = 'Archon Core Platform') THEN
        INSERT INTO archon_projects (title, description) VALUES
        ('Archon Core Platform', 'Development of the main Archon task management system.')
        RETURNING id INTO proj1_id;
    ELSE
        SELECT id INTO proj1_id FROM archon_projects WHERE title = 'Archon Core Platform';
    END IF;

    -- Project 2: Website Redesign
    IF NOT EXISTS (SELECT 1 FROM archon_projects WHERE title = 'Website Redesign') THEN
        INSERT INTO archon_projects (title, description) VALUES
        ('Website Redesign', 'Complete overhaul of the public-facing marketing website.')
        RETURNING id INTO proj2_id;
    ELSE
        SELECT id INTO proj2_id FROM archon_projects WHERE title = 'Website Redesign';
    END IF;

    -- Seed for archon_tasks table using the captured project UUIDs, ensuring idempotency
    -- Task 1
    IF NOT EXISTS (SELECT 1 FROM archon_tasks WHERE project_id = proj1_id AND title = 'Implement Supabase Integration') THEN
        INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, created_at, updated_at) VALUES
        (proj1_id, 'Implement Supabase Integration', '', 'done', 'Alice Johnson', 1, '2024-09-01T10:00:00Z', '2024-09-05T10:00:00Z');
    END IF;

    -- Task 2
    IF NOT EXISTS (SELECT 1 FROM archon_tasks WHERE project_id = proj1_id AND title = 'Develop Kanban View') THEN
        INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, created_at, updated_at) VALUES
        (proj1_id, 'Develop Kanban View', '', 'doing', 'Bob Williams', 2, '2024-09-02T10:00:00Z', '2024-09-06T10:00:00Z');
    END IF;

    -- Task 3
    IF NOT EXISTS (SELECT 1 FROM archon_tasks WHERE project_id = proj2_id AND title = 'Design new landing page mockups') THEN
        INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, created_at, updated_at) VALUES
        (proj2_id, 'Design new landing page mockups', '', 'todo', 'Unassigned', 1, '2024-09-03T10:00:00Z', '2024-09-03T10:00:00Z');
    END IF;

    -- Task 4
    IF NOT EXISTS (SELECT 1 FROM archon_tasks WHERE project_id = proj1_id AND title = 'Fix authentication bug') THEN
        INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, created_at, updated_at) VALUES
        (proj1_id, 'Fix authentication bug', 'Users are reporting intermittent login failures.', 'review', 'Alice Johnson', 3, '2024-09-04T10:00:00Z', '2024-09-08T10:00:00Z');
    END IF;

    -- Seed for archon_settings table
    INSERT INTO archon_settings (key, value, is_encrypted, category, description) VALUES
    ('PROJECTS_ENABLED', 'true', false, 'features', 'Enable or disable Projects and Tasks functionality'),
    ('STYLE_GUIDE_ENABLED', 'true', false, 'features', 'Show UI style guide and components in navigation')
    ON CONFLICT (key) DO NOTHING;

    -- Set the default LLM provider to Google
    INSERT INTO archon_settings (key, value, is_encrypted, category, description)
    VALUES ('LLM_PROVIDER', 'google', false, 'ai', 'The primary LLM provider for embeddings and generation.')
    ON CONFLICT (key) DO UPDATE SET
        value = EXCLUDED.value,
        updated_at = NOW();

    RAISE NOTICE 'Test database seeded.';
END;
$$;


ALTER FUNCTION public.seed_test_database() OWNER TO postgres;

--
-- Name: update_updated_at_column(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE OR REPLACE FUNCTION public.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_updated_at_column() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
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
-- Name: customers Allow authenticated read access; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Allow authenticated read access" ON public.customers FOR SELECT TO authenticated USING (true);


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

CREATE POLICY "Allow authenticated users to read and update archon_projects" ON public.archon_projects TO authenticated USING (true);


--
-- Name: archon_tasks Allow authenticated users to read and update archon_tasks; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Allow authenticated users to read and update archon_tasks" ON public.archon_tasks TO authenticated USING (true);


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
-- Name: market_insights Allow authenticated users to view insights; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Allow authenticated users to view insights" ON public.market_insights FOR SELECT USING ((auth.role() = 'authenticated'::text));


--
-- Name: leads Allow authenticated users to view leads; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Allow authenticated users to view leads" ON public.leads FOR SELECT USING ((auth.role() = 'authenticated'::text));


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
-- Name: customers Allow write access for sales and management; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Allow write access for sales and management" ON public.customers USING ((((auth.jwt() ->> 'role'::text) = 'service_role'::text) OR (EXISTS ( SELECT 1
   FROM public.profiles
  WHERE ((profiles.id = (auth.uid())::text) AND (profiles.role = ANY (ARRAY['admin'::text, 'manager'::text, 'sales'::text, 'system_admin'::text])))))));


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
-- Name: customers; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.customers ENABLE ROW LEVEL SECURITY;

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
-- Name: market_insights; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.market_insights ENABLE ROW LEVEL SECURITY;

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
-- Name: subscriptions; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;

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
-- Name: TABLE customers; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.customers TO authenticated;
GRANT ALL ON TABLE public.customers TO service_role;


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
-- Name: TABLE market_insights; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.market_insights TO authenticated;
GRANT ALL ON TABLE public.market_insights TO service_role;


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
-- Name: TABLE subscriptions; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.subscriptions TO authenticated;
GRANT ALL ON TABLE public.subscriptions TO service_role;


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

