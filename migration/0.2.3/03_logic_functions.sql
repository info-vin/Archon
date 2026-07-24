-- Source: 05_logic_functions.sql
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

-- Added from Patch 13: optimize_task_reordering
CREATE OR REPLACE FUNCTION increment_task_orders(
    p_project_id UUID,
    p_status TEXT,
    p_start_order INT
)
RETURNS void AS $$
BEGIN
    UPDATE archon_tasks
    SET 
        task_order = task_order + 1,
        updated_at = NOW()
    WHERE 
        project_id = p_project_id 
        AND status = p_status
        AND task_order >= p_start_order;
END;
$$ LANGUAGE plpgsql;

-- Added from Patch 23: multi_tenant_and_rls_hardening
CREATE OR REPLACE FUNCTION public.get_auth_tenant_id()
RETURNS UUID SECURITY DEFINER AS $$
BEGIN
  RETURN (SELECT tenant_id FROM public.profiles WHERE id = auth.uid()::text LIMIT 1);
END;
$$ LANGUAGE plpgsql STABLE;


-- Source: 06_constraints_main.sql
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


-- Source: 07_logic_indexes.sql
-- Name: archon_code_examples_embedding_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX archon_code_examples_embedding_idx ON public.archon_code_examples USING hnsw (embedding public.vector_cosine_ops);


--
-- Name: archon_crawled_pages_embedding_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX archon_crawled_pages_embedding_idx ON public.archon_crawled_pages USING hnsw (embedding public.vector_cosine_ops);


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

-- Added from Patch 22: performance indexes
CREATE INDEX IF NOT EXISTS idx_archon_tasks_assignee_status ON public.archon_tasks (assignee_id, status);
CREATE INDEX IF NOT EXISTS idx_leads_status_enrichment ON public.leads (status, enrichment_score);
CREATE INDEX IF NOT EXISTS idx_archon_logs_level_type ON public.archon_logs (level, type);
CREATE INDEX IF NOT EXISTS idx_token_usage_provider_cost ON public.token_usage (provider, cost_usd DESC);


-- Source: 08_logic_triggers.sql
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


-- Source: 09_constraints_fkeys.sql
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
-- Name: proposed_changes proposed_changes_approved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.proposed_changes
    ADD CONSTRAINT proposed_changes_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES auth.users(id);




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


-- Source: 26_rag_hybrid_match_chunks.sql
-- Name: hybrid_match_chunks(public.vector, text, integer, float, jsonb, text); Type: FUNCTION; Schema: public; Owner: postgres
-- 
-- Phase 5.8.0 Semantic Infiltration
-- Provides a hybrid RAG search function combining vector and full-text search with dynamic similarity threshold filtering.

CREATE OR REPLACE FUNCTION public.hybrid_match_chunks(
    query_embedding public.vector, 
    query_text text, 
    match_count integer DEFAULT 10, 
    similarity_threshold float DEFAULT 0.0,
    filter jsonb DEFAULT '{}'::jsonb, 
    source_filter text DEFAULT NULL::text
) RETURNS TABLE(
    id bigint, 
    url character varying, 
    chunk_number integer, 
    content text, 
    metadata jsonb, 
    source_id text, 
    similarity double precision, 
    match_type text
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH vector_results AS (
        -- Vector similarity search with noise filtering (threshold)
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
            AND 1 - (cp.embedding <=> query_embedding) >= similarity_threshold
        ORDER BY cp.embedding <=> query_embedding
        LIMIT match_count
    ),
    text_results AS (
        -- Full-text search (FTS) with ranking
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
        LIMIT match_count
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
    SELECT c.id, c.url, c.chunk_number, c.content, c.metadata, c.source_id, c.similarity, c.match_type 
    FROM combined_results c
    ORDER BY c.similarity DESC
    LIMIT match_count;
END;
$$;

ALTER FUNCTION public.hybrid_match_chunks(query_embedding public.vector, query_text text, match_count integer, similarity_threshold float, filter jsonb, source_filter text) OWNER TO postgres;

COMMENT ON FUNCTION public.hybrid_match_chunks(query_embedding public.vector, query_text text, match_count integer, similarity_threshold float, filter jsonb, source_filter text) IS 'Performs hybrid search for Archon RAG Deck-builder with dynamic noise filtering threshold';


-- Source: 100_add_tiered_pruning_rpcs.sql
-- Phase 5.9.3: Tiered Database Pruning RPCs
-- Provides secure endpoints for the Python backend to check DB size and execute complex cross-table deletions.

-- 1. Get current database size in MB
CREATE OR REPLACE FUNCTION get_db_size_mb()
RETURNS float
LANGUAGE sql
SECURITY DEFINER
AS $$
  SELECT (pg_database_size(current_database()) / 1048576.0)::float;
$$;

-- 2. Prune orphan vectors (returns number of deleted rows)
-- Cleans up chunks that have lost their parent source or have a NULL source_id
CREATE OR REPLACE FUNCTION prune_orphan_vectors()
RETURNS int
LANGUAGE sql
SECURITY DEFINER
AS $$
  WITH deleted AS (
    DELETE FROM archon_crawled_pages 
    WHERE source_id IS NULL OR source_id NOT IN (SELECT source_id FROM archon_sources)
    RETURNING id
  )
  SELECT count(*)::int FROM deleted;
$$;


