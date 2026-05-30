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
