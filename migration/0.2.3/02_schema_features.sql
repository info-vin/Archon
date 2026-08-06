-- Source: 03_tables_business.sql
-- Name: archon_sources; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.archon_sources (
    source_id text NOT NULL,
    source_url text,
    source_display_name text,
    summary text,
    total_word_count integer DEFAULT 0,
    title text,
    metadata jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);


ALTER TABLE public.archon_sources OWNER TO postgres;

--
-- Name: COLUMN archon_sources.source_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.archon_sources.source_id IS 'Unique hash identifier for the source (16-char SHA256 hash of URL)';


--
-- Name: COLUMN archon_sources.source_url; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.archon_sources.source_url IS 'The original URL that was crawled to create this source';


--
-- Name: COLUMN archon_sources.source_display_name; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.archon_sources.source_display_name IS 'Human-readable name for UI display (e.g., "GitHub - microsoft/typescript")';


--
-- Name: COLUMN archon_sources.title; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.archon_sources.title IS 'Descriptive title for the source (e.g., "Pydantic AI API Reference")';


--
-- Name: COLUMN archon_sources.metadata; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.archon_sources.metadata IS 'JSONB field storing knowledge_type, tags, and other metadata';


--
-- Name: blog_posts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.blog_posts (
    id text DEFAULT gen_random_uuid() NOT NULL,
    title text NOT NULL,
    excerpt text,
    content text NOT NULL,
    author_name text,
    publish_date timestamp with time zone,
    image_url text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    status text DEFAULT 'draft'::text,
    source_lead_id uuid,
    publish_at timestamp with time zone,
    target_brand text DEFAULT 'Archon'::text,
    review_notes text,
    generation_metadata jsonb DEFAULT '{}'::jsonb,
    ai_score integer DEFAULT 100,
    lead_id uuid
);


ALTER TABLE public.blog_posts OWNER TO postgres;

--
-- Name: COLUMN blog_posts.source_lead_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.blog_posts.source_lead_id IS 'The sales lead that inspired this content (Traceability)';


--
-- Name: COLUMN blog_posts.target_brand; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.blog_posts.target_brand IS 'Brand channel (e.g., Archon, Nano, Banana)';


--
-- Name: leads; Type: TABLE; Schema: public; Owner: postgres
--
CREATE TABLE public.leads (
    id uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    company_name text NOT NULL,
    source_job_url text,
    status text DEFAULT 'new'::text,
    identified_need text,
    assigned_sales_id uuid,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    job_title text,
    description_snippet text,
    contact_name text,
    contact_email text,
    contact_phone text,
    linked_project_id uuid,
    last_contacted_at timestamp with time zone,
    next_followup_date timestamp with time zone,
    company_website text,
    enrichment_status text DEFAULT 'pending'::text,
    enrichment_score integer DEFAULT 0,
    last_enriched_at timestamp with time zone,
    auto_archived_reason text,
    email text,
    source text DEFAULT 'manual'::text,
    pitch_content text,
    lost_reason text,
    lost_competitor text,
    tenant_id UUID DEFAULT 'd3b07384-d113-4456-a111-c91823710000'
);


ALTER TABLE public.leads OWNER TO postgres;

--
-- Name: COLUMN leads.lost_reason; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.leads.lost_reason IS 'Reason why the lead was lost or rejected.';


--
-- Name: COLUMN leads.lost_competitor; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.leads.lost_competitor IS 'Competitor the lead chose instead of our solution, if known.';


--
-- Name: vendors; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.vendors (
    id uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    name text NOT NULL,
    service_type text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    pain_points text,
    owner_id uuid,
    status text DEFAULT 'qualified'::text,
    contact_info jsonb DEFAULT '{}'::jsonb,
    contact_email text,
    description text,
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.vendors OWNER TO postgres;

--
-- Name: TABLE vendors; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.vendors IS '儲存供應商和合作夥伴資訊。';


--
-- Name: COLUMN vendors.name; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.vendors.name IS '供應商的完整名稱或公司名稱。';


--
-- Name: COLUMN vendors.service_type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.vendors.service_type IS '供應商提供的服務類別（例如："Software", "Consulting"）。';


--
-- Name: archon_code_examples id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archon_code_examples ALTER COLUMN id SET DEFAULT nextval('public.archon_code_examples_id_seq'::regclass);


--
-- Name: archon_crawled_pages id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archon_crawled_pages ALTER COLUMN id SET DEFAULT nextval('public.archon_crawled_pages_id_seq'::regclass);

--
-- Name: archon_document_versions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.archon_document_versions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    project_id uuid,
    task_id uuid,
    field_name text NOT NULL,
    version_number integer NOT NULL,
    content jsonb NOT NULL,
    change_summary text,
    change_type text DEFAULT 'update'::text,
    document_id text,
    created_by text DEFAULT 'system'::text,
    created_at timestamp with time zone DEFAULT now(),
    status text DEFAULT 'approved'::text,
    CONSTRAINT chk_version_identity CHECK (((project_id IS NOT NULL) OR (task_id IS NOT NULL) OR (document_id IS NOT NULL) OR (field_name = ANY (ARRAY['sales_pitch'::text, 'web_research'::text, 'knowledge_file'::text, 'system_prompt'::text, 'system_setting'::text]))))
);


ALTER TABLE public.archon_document_versions OWNER TO postgres;

--
-- Name: TABLE archon_document_versions; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.archon_document_versions IS 'Version control for JSONB fields in projects only - task versioning has been removed to simplify MCP operations';


--
-- Name: COLUMN archon_document_versions.task_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.archon_document_versions.task_id IS 'DEPRECATED: No longer used for new versions, kept for historical task version data';


--
-- Name: COLUMN archon_document_versions.field_name; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.archon_document_versions.field_name IS 'Name of JSONB field being versioned (docs, features, data) - task fields and prd removed as unused';


--
-- Name: COLUMN archon_document_versions.content; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.archon_document_versions.content IS 'Full snapshot of field content at this version';


--
-- Name: COLUMN archon_document_versions.change_type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.archon_document_versions.change_type IS 'Type of change: create, update, delete, restore, backup';


--
-- Name: COLUMN archon_document_versions.document_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.archon_document_versions.document_id IS 'For docs arrays, the specific document ID that was changed';


--
-- Name: archon_project_sources; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.archon_project_sources (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    project_id uuid,
    source_id text NOT NULL,
    linked_at timestamp with time zone DEFAULT now(),
    created_by text DEFAULT 'system'::text,
    notes text
);


ALTER TABLE public.archon_project_sources OWNER TO postgres;

--
-- Name: archon_projects; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.archon_projects (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    title text NOT NULL,
    description text DEFAULT ''::text,
    docs jsonb DEFAULT '[]'::jsonb,
    features jsonb DEFAULT '[]'::jsonb,
    data jsonb DEFAULT '[]'::jsonb,
    github_repo text,
    pinned boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    tenant_id UUID DEFAULT 'd3b07384-d113-4456-a111-c91823710000'
);


ALTER TABLE public.archon_projects OWNER TO postgres;

--


-- Source: 04_tables_ops.sql
-- Name: archon_tasks; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.archon_tasks (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    project_id uuid,
    parent_task_id uuid,
    title text NOT NULL,
    description text DEFAULT ''::text,
    status public.task_status DEFAULT 'todo'::public.task_status,
    assignee text DEFAULT 'User'::text,
    task_order integer DEFAULT 0,
    feature text,
    sources jsonb DEFAULT '[]'::jsonb,
    code_examples jsonb DEFAULT '[]'::jsonb,
    attachments jsonb,
    archived boolean DEFAULT false,
    archived_at timestamp with time zone,
    archived_by text,
    due_date timestamp with time zone,
    priority text,
    completed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    assignee_id text,
    estimated_hours double precision DEFAULT 0,
    actual_hours double precision DEFAULT 0,
    collaborator_agent_ids text[] DEFAULT '{}'::text[],
    tenant_id UUID DEFAULT 'd3b07384-d113-4456-a111-c91823710000',
    CONSTRAINT archon_tasks_assignee_check CHECK (((assignee IS NOT NULL) AND (assignee <> ''::text)))
);


ALTER TABLE public.archon_tasks OWNER TO postgres;

--
-- Name: COLUMN archon_tasks.assignee; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.archon_tasks.assignee IS 'The agent or user assigned to this task. Can be any valid agent name or "User"';


--
-- Name: COLUMN archon_tasks.archived; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.archon_tasks.archived IS 'Soft delete flag - TRUE if task is archived/deleted';


--
-- Name: COLUMN archon_tasks.archived_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.archon_tasks.archived_at IS 'Timestamp when task was archived';


--
-- Name: COLUMN archon_tasks.archived_by; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.archon_tasks.archived_by IS 'User/system that archived the task';


--
-- Name: proposed_changes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.proposed_changes (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    status public.change_status DEFAULT 'pending'::public.change_status NOT NULL,
    type public.change_type NOT NULL,
    request_payload jsonb NOT NULL,
    approved_by uuid,
    approved_at timestamp with time zone,
    executed_at timestamp with time zone,
    execution_log text
);


ALTER TABLE public.proposed_changes OWNER TO postgres;

--
-- Name: TABLE proposed_changes; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.proposed_changes IS 'Stores AI-proposed changes that require human approval before execution.';


--
-- Name: COLUMN proposed_changes.status; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.proposed_changes.status IS 'The current status of the proposed change (e.g., pending, approved).';


--
-- Name: COLUMN proposed_changes.type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.proposed_changes.type IS 'The type of change proposed (e.g., file, git, shell).';


--
-- Name: COLUMN proposed_changes.request_payload; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.proposed_changes.request_payload IS 'A JSON object containing the detailed parameters for the change.';


--
-- Name: COLUMN proposed_changes.approved_by; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.proposed_changes.approved_by IS 'The user who approved the change.';

--
-- Name: archon_ethics_events; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.archon_ethics_events (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    severity text NOT NULL,
    event_type text NOT NULL,
    description text,
    raw_input text,
    created_at timestamp with time zone DEFAULT now(),
    resolved boolean DEFAULT false,
    resolution_notes text
);


ALTER TABLE public.archon_ethics_events OWNER TO postgres;

--
-- Name: archon_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.archon_logs (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    source text NOT NULL,
    level text NOT NULL,
    message text NOT NULL,
    details jsonb,
    created_at timestamp with time zone DEFAULT now(),
    type text DEFAULT 'general'::text,
    project_name text,
    user_id uuid
);


ALTER TABLE public.archon_logs OWNER TO postgres;

--
-- Name: archon_prompts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.archon_prompts (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    prompt_name text NOT NULL,
    prompt text NOT NULL,
    description text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_system_protected boolean DEFAULT false
);


ALTER TABLE public.archon_prompts OWNER TO postgres;

--
-- Name: attendance_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.attendance_logs (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    clock_in_time timestamp with time zone DEFAULT now() NOT NULL,
    clock_out_time timestamp with time zone,
    latitude double precision,
    longitude double precision,
    location_name text,
    status text NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT attendance_logs_status_check CHECK ((status = ANY (ARRAY['PRESENT'::text, 'AWAY'::text, 'OFF_WORK'::text, 'MOCK_PRESENT'::text])))
);


ALTER TABLE public.attendance_logs OWNER TO postgres;




--
-- Name: gemini_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.gemini_logs (
    id integer NOT NULL,
    user_input text,
    gemini_response text NOT NULL,
    project_name character varying(255),
    user_name character varying(255),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.gemini_logs OWNER TO postgres;

--
-- Name: gemini_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.gemini_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.gemini_logs_id_seq OWNER TO postgres;

--
-- Name: gemini_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.gemini_logs_id_seq OWNED BY public.gemini_logs.id;



--
-- Name: marketing_trends; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.marketing_trends (
    id uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    report_date date DEFAULT CURRENT_DATE NOT NULL,
    trend_type text NOT NULL,
    data jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.marketing_trends OWNER TO postgres;


--
-- Name: token_usage; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.token_usage (
    id uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    request_id text NOT NULL,
    user_id uuid,
    model text NOT NULL,
    provider text NOT NULL,
    input_tokens integer DEFAULT 0 NOT NULL,
    output_tokens integer DEFAULT 0 NOT NULL,
    total_tokens integer GENERATED ALWAYS AS ((input_tokens + output_tokens)) STORED,
    cost_usd numeric(10,6) DEFAULT 0,
    context_type text,
    created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL,
    tenant_id UUID DEFAULT 'd3b07384-d113-4456-a111-c91823710000'
);


ALTER TABLE public.token_usage OWNER TO postgres;

--
-- Name: TABLE token_usage; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.token_usage IS 'Tracks LLM token consumption and estimated cost for auditing and system health monitoring.';


--
-- Name: visit_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.visit_logs (
    id uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    user_id uuid NOT NULL,
    customer_id uuid,
    lead_id uuid,
    latitude numeric(10,8),
    longitude numeric(11,8),
    location_address text,
    voice_transcript text,
    summary text,
    follow_up_tasks text[],
    audio_url text,
    image_urls text[],
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    visit_type text
);


ALTER TABLE public.visit_logs OWNER TO postgres;

--
-- Name: gemini_logs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.gemini_logs ALTER COLUMN id SET DEFAULT nextval('public.gemini_logs_id_seq'::regclass);



-- Source: 24_create_dynamic_agent_tables.sql
-- Database tables for Dynamic AI Agent Governance and Workflow Graph Routing
-- Phase 5.7.0: Dynamic Agent Architecture

-- 1. Create archon_agents Table
CREATE TABLE IF NOT EXISTS public.archon_agents (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    agent_key text UNIQUE NOT NULL,      -- e.g. 'dev-bot', 'market-bot'
    name text NOT NULL,                  -- e.g. 'Archon DevBot'
    model_tier text DEFAULT 'lite' NOT NULL CHECK (model_tier IN ('pro', 'lite')),
    default_tool text,
    description text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

-- 2. Create archon_agent_tools Table (Multi-to-Multi Agent Tools relationship)
CREATE TABLE IF NOT EXISTS public.archon_agent_tools (
    agent_id uuid REFERENCES public.archon_agents(id) ON DELETE CASCADE,
    tool_name text NOT NULL,
    PRIMARY KEY (agent_id, tool_name)
);

-- 3. Create archon_role_agents Table (Agent assignment RBAC mapping)
CREATE TABLE IF NOT EXISTS public.archon_role_agents (
    user_role text NOT NULL,             -- e.g. 'sales', 'marketing', 'manager', 'admin'
    agent_key text REFERENCES public.archon_agents(agent_key) ON DELETE CASCADE,
    PRIMARY KEY (user_role, agent_key)
);

-- 4. Create archon_workflow_flows Table (Dynamic routing specification for Graph Engine)
CREATE TABLE IF NOT EXISTS public.archon_workflow_flows (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    workflow_type text UNIQUE NOT NULL,  -- e.g. 'Marketing Data Deep Dive'
    supervisor_prompt_name text NOT NULL, -- references prompt_name in archon_prompts
    node_routing jsonb NOT NULL,         -- routing JSON mapping e.g., {"david": "DavidNode", "marketbot": "MarketBotNode"}
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

-- 5. Seed Initial Config for Agents
INSERT INTO public.archon_agents (id, agent_key, name, model_tier, default_tool, description)
VALUES
  ('e1682371-0000-0000-0000-000000000000', 'dev-bot', 'Archon DevBot', 'pro', NULL, 'Expert software engineer with mathematical logic.'),
  ('a11ce000-0000-0000-0000-000000000000', 'market-bot', 'Archon MarketBot', 'lite', 'search_job_market', 'Marketing Copywriter agent.'),
  ('b0b00000-0000-0000-0000-000000000000', 'librarian', 'Archon Librarian', 'lite', NULL, 'Organizational knowledge and RAG search agent.'),
  ('c0a00000-0000-0000-0000-000000000000', 'po-bot', 'Archon POBot', 'pro', NULL, 'Product Owner and task refiner agent.'),
  ('d0e00000-0000-0000-0000-000000000000', 'supervisor', 'Archon Supervisor', 'pro', NULL, 'Workflow Routing supervisor.')
ON CONFLICT (agent_key) DO UPDATE 
SET name = EXCLUDED.name,
    model_tier = EXCLUDED.model_tier,
    default_tool = EXCLUDED.default_tool,
    description = EXCLUDED.description,
    updated_at = NOW();

-- 6. Seed Tools Authorization
INSERT INTO public.archon_agent_tools (agent_id, tool_name)
VALUES
  -- dev-bot
  ('e1682371-0000-0000-0000-000000000000', 'rag_search_code_examples'),
  ('e1682371-0000-0000-0000-000000000000', 'generate_logo'),
  ('e1682371-0000-0000-0000-000000000000', 'apply_modification'),
  ('e1682371-0000-0000-0000-000000000000', 'execute_shell_command'),
  -- market-bot
  ('a11ce000-0000-0000-0000-000000000000', 'search_job_market'),
  ('a11ce000-0000-0000-0000-000000000000', 'generate_sales_email'),
  -- librarian
  ('b0b00000-0000-0000-0000-000000000000', 'rag_search_knowledge_base'),
  ('b0b00000-0000-0000-0000-000000000000', 'rag_get_available_sources'),
  ('b0b00000-0000-0000-0000-000000000000', 'rag_search_code_examples'),
  ('b0b00000-0000-0000-0000-000000000000', 'perform_web_crawl'),
  -- po-bot
  ('c0a00000-0000-0000-0000-000000000000', 'list_projects'),
  ('c0a00000-0000-0000-0000-000000000000', 'manage_task')
ON CONFLICT DO NOTHING;

-- 7. Seed Role assignment RBAC mapping
INSERT INTO public.archon_role_agents (user_role, agent_key)
VALUES
  -- sales role
  ('sales', 'market-bot'),
  -- marketing role
  ('marketing', 'market-bot'),
  ('marketing', 'librarian'),
  -- managers & admins have access to all non-system agents dynamically. We seed fallback defaults.
  ('manager', 'market-bot'),
  ('manager', 'librarian'),
  ('manager', 'dev-bot'),
  ('admin', 'market-bot'),
  ('admin', 'librarian'),
  ('admin', 'dev-bot'),
  ('system_admin', 'market-bot'),
  ('system_admin', 'librarian'),
  ('system_admin', 'dev-bot')
ON CONFLICT DO NOTHING;

-- 8. Seed Dynamic Workflow Routing Flows
INSERT INTO public.archon_workflow_flows (workflow_type, supervisor_prompt_name, node_routing)
VALUES
  (
    'Marketing Data Deep Dive',
    'WORKFLOW_SUPERVISOR_MARKETING',
    '{"david": "DavidNode", "devbot": "DevBotNode", "bob": "MarketBotNode"}'
  ),
  (
    'Daily Executive Summary',
    'WORKFLOW_SUPERVISOR_DAILY',
    '{"librarian": "LibrarianNode", "summary": "SummaryNode", "marketbot": "MarketBotNode"}'
  ),
  (
    'General',
    'WORKFLOW_SUPERVISOR_GENERAL',
    '{"marketbot": "MarketBotNode", "librarian": "LibrarianNode", "summary": "SummaryNode", "devbot": "DevBotNode", "david": "DavidNode"}'
  )
ON CONFLICT (workflow_type) DO UPDATE
SET supervisor_prompt_name = EXCLUDED.supervisor_prompt_name,
    node_routing = EXCLUDED.node_routing,
    updated_at = NOW();


-- Source: 28_graphrag_and_mrl.sql
-- Name: hybrid_match_chunks (MRL Support); Type: FUNCTION; Schema: public; Owner: postgres
-- 
-- Phase 5.8.6 MRL & GraphRAG Implementation
-- Overwrites hybrid_match_chunks to support truncate_dim for Matryoshka Representation Learning

DROP FUNCTION IF EXISTS public.hybrid_match_chunks(public.vector, text, integer, float, jsonb, text);

CREATE OR REPLACE FUNCTION public.hybrid_match_chunks(
    query_embedding public.vector, 
    query_text text, 
    match_count integer DEFAULT 10, 
    similarity_threshold float DEFAULT 0.0,
    filter jsonb DEFAULT '{}'::jsonb, 
    source_filter text DEFAULT NULL::text,
    truncate_dim integer DEFAULT NULL
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
        -- Vector similarity search with MRL dynamic slicing
        SELECT 
            cp.id,
            cp.url,
            cp.chunk_number,
            cp.content,
            cp.metadata,
            cp.source_id,
            CASE 
                WHEN truncate_dim IS NOT NULL THEN
                    -- MRL slice calculation
                    1 - ((((cp.embedding::real[])[1:truncate_dim])::vector) <=> (((query_embedding::real[])[1:truncate_dim])::vector))
                ELSE
                    -- Standard calculation
                    1 - (cp.embedding <=> query_embedding)
            END AS vector_sim
        FROM archon_crawled_pages cp
        WHERE cp.metadata @> filter
            AND (source_filter IS NULL OR cp.source_id = source_filter)
            AND cp.embedding IS NOT NULL
            AND (
                CASE WHEN truncate_dim IS NOT NULL THEN
                    1 - ((((cp.embedding::real[])[1:truncate_dim])::vector) <=> (((query_embedding::real[])[1:truncate_dim])::vector))
                ELSE
                    1 - (cp.embedding <=> query_embedding)
                END
            ) >= similarity_threshold
        ORDER BY 
            CASE WHEN truncate_dim IS NOT NULL THEN
                (((cp.embedding::real[])[1:truncate_dim])::vector) <=> (((query_embedding::real[])[1:truncate_dim])::vector)
            ELSE
                cp.embedding <=> query_embedding
            END
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


-- ============================================================================
-- GraphRAG Pure Postgres Implementation
-- Creates dynamic schema and Recursive CTE function for 2-hop / n-hop traversal
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.knowledge_entities (
    id bigserial PRIMARY KEY,
    name text NOT NULL,
    type text,
    description text,
    metadata jsonb DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS public.knowledge_relationships (
    id bigserial PRIMARY KEY,
    source_entity_id bigint REFERENCES public.knowledge_entities(id) ON DELETE CASCADE,
    target_entity_id bigint REFERENCES public.knowledge_entities(id) ON DELETE CASCADE,
    relation_type text NOT NULL,
    weight float DEFAULT 1.0,
    metadata jsonb DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_krel_source ON public.knowledge_relationships(source_entity_id);
CREATE INDEX IF NOT EXISTS idx_krel_target ON public.knowledge_relationships(target_entity_id);

CREATE OR REPLACE FUNCTION public.graph_reasoning_n_hop(
    start_entity_name text,
    max_hops integer DEFAULT 2
) RETURNS TABLE(
    path text,
    hop_count integer,
    final_entity text
)
LANGUAGE sql
AS $$
    WITH RECURSIVE graph_cte AS (
        -- Base case: find the starting entity
        SELECT 
            e.id as current_id, 
            e.name as path, 
            0 as hop_count,
            e.name as current_name
        FROM knowledge_entities e
        WHERE e.name ILIKE start_entity_name

        UNION ALL

        -- Recursive step: join with relationships to find neighbors
        SELECT 
            r.target_entity_id as current_id,
            g.path || ' -> ' || e.name as path,
            g.hop_count + 1 as hop_count,
            e.name as current_name
        FROM graph_cte g
        JOIN knowledge_relationships r ON g.current_id = r.source_entity_id
        JOIN knowledge_entities e ON r.target_entity_id = e.id
        WHERE g.hop_count < max_hops
    )
    SELECT path, hop_count, current_name as final_entity
    FROM graph_cte
    ORDER BY hop_count ASC, path ASC;
$$;


-- Source: 33_create_agent_checkpoints_and_approvals.sql
-- Migration: 33_create_agent_checkpoints_and_approvals.sql
-- Phase 5.9.13: Agent DB State Checkpointing & Human-in-the-Loop (HITL) Architecture

-- 1. Agent Checkpoint Table for State Persistence
CREATE TABLE IF NOT EXISTS public.agent_checkpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id TEXT NOT NULL,
    step_index INT NOT NULL,
    agent_role TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('RUNNING', 'PENDING_APPROVAL', 'COMPLETED', 'FAILED', 'CANCELLED')),
    state_snapshot JSONB NOT NULL,
    last_tool_call JSONB DEFAULT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT unq_conv_step UNIQUE(conversation_id, step_index)
);

CREATE INDEX IF NOT EXISTS idx_agent_checkpoints_conv ON public.agent_checkpoints(conversation_id);
CREATE INDEX IF NOT EXISTS idx_agent_checkpoints_status ON public.agent_checkpoints(status);

-- 2. Human-in-the-Loop Pending Approvals Table
CREATE TABLE IF NOT EXISTS public.agent_pending_approvals (
    approval_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id TEXT NOT NULL,
    checkpoint_id UUID REFERENCES public.agent_checkpoints(id) ON DELETE CASCADE,
    tool_name TEXT NOT NULL,
    tool_args JSONB NOT NULL,
    risk_level TEXT NOT NULL DEFAULT 'HIGH',
    status TEXT NOT NULL CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED', 'EXPIRED')),
    reviewer_id TEXT DEFAULT NULL,
    review_reason TEXT DEFAULT NULL,
    expires_at TIMESTAMPTZ NOT NULL DEFAULT (timezone('utc'::text, now()) + interval '30 minutes'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_agent_approvals_status ON public.agent_pending_approvals(status);


-- Source: 30_alter_archon_prompts_schema.sql
-- Phase 5.9.7: Add category and metadata to archon_prompts

ALTER TABLE public.archon_prompts 
ADD COLUMN IF NOT EXISTS category text DEFAULT 'SYSTEM_AGENT';

ALTER TABLE public.archon_prompts 
ADD COLUMN IF NOT EXISTS metadata jsonb DEFAULT '{}'::jsonb;

-- Ensure that existing rows have the default values explicitly set if they were somehow inserted before this migration but after table creation
UPDATE public.archon_prompts 
SET category = 'SYSTEM_AGENT' WHERE category IS NULL;

UPDATE public.archon_prompts 
SET metadata = '{}'::jsonb WHERE metadata IS NULL;

-- 1. Create the Dynamic RBAC Matrix Table
CREATE TABLE IF NOT EXISTS public.archon_roles_permissions (
    role TEXT PRIMARY KEY,
    permissions TEXT[] NOT NULL DEFAULT '{}',
    description TEXT,
    is_system_protected BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

