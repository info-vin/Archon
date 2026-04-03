--
-- PostgreSQL database dump
--


-- Dumped from database version 17.4
-- Dumped by pg_dump version 17.8 (Debian 17.8-0+deb13u1)


--
-- Name: change_status; Type: TYPE; Schema: public; Owner: postgres
--

DO $$ BEGIN
    CREATE TYPE public.change_status AS ENUM ('pending', 'approved', 'rejected', 'executed', 'failed');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

--
-- Name: change_type; Type: TYPE; Schema: public; Owner: postgres
--

DO $$ BEGIN
    CREATE TYPE public.change_type AS ENUM ('file', 'git', 'shell');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

--
-- Name: task_status; Type: TYPE; Schema: public; Owner: postgres
--

DO $$ BEGIN
    CREATE TYPE public.task_status AS ENUM ('todo', 'doing', 'review', 'done', 'failed', 'processing', 'dispatched', 'pending', 'archived', 'cancelled');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

--
-- Name: project_status; Type: TYPE; Schema: public; Owner: postgres
--

DO $$ BEGIN
    CREATE TYPE public.project_status AS ENUM ('planning', 'active', 'archived', 'completed');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

--
-- Name: blog_status; Type: TYPE; Schema: public; Owner: postgres
--

DO $$ BEGIN
    CREATE TYPE public.blog_status AS ENUM ('draft', 'review', 'changes_requested', 'published');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

--
-- Name: archon_settings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.archon_settings (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    key character varying(255) NOT NULL,
    value text,
    encrypted_value text,
    is_encrypted boolean DEFAULT false,
    category character varying(100),
    description text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_system_protected boolean DEFAULT false
);


ALTER TABLE public.archon_settings OWNER TO postgres;

--
-- Name: TABLE archon_settings; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.archon_settings IS 'Stores application configuration including API keys, RAG settings, and code extraction parameters';


--
-- Name: profiles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.profiles (
    id text NOT NULL,
    "employeeId" text,
    name text NOT NULL,
    email text NOT NULL,
    department text,
    "position" text,
    status text,
    role text,
    avatar text,
    permission_overrides jsonb DEFAULT '{}'::jsonb
);


ALTER TABLE public.profiles OWNER TO postgres;

--
-- Name: archon_code_examples; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.archon_code_examples (
    id bigint NOT NULL,
    url character varying NOT NULL,
    chunk_number integer NOT NULL,
    content text NOT NULL,
    summary text NOT NULL,
    metadata jsonb DEFAULT '{}'::jsonb NOT NULL,
    source_id text NOT NULL,
    embedding public.vector(768),
    content_search_vector tsvector GENERATED ALWAYS AS (to_tsvector('english'::regconfig, ((content || ' '::text) || COALESCE(summary, ''::text)))) STORED,
    created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);


ALTER TABLE public.archon_code_examples OWNER TO postgres;

--
-- Name: archon_code_examples_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.archon_code_examples_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.archon_code_examples_id_seq OWNER TO postgres;

--
-- Name: archon_code_examples_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.archon_code_examples_id_seq OWNED BY public.archon_code_examples.id;


--
-- Name: archon_crawled_pages; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.archon_crawled_pages (
    id bigint NOT NULL,
    url character varying NOT NULL,
    chunk_number integer NOT NULL,
    content text NOT NULL,
    metadata jsonb DEFAULT '{}'::jsonb NOT NULL,
    source_id text NOT NULL,
    embedding public.vector(768),
    content_search_vector tsvector GENERATED ALWAYS AS (to_tsvector('english'::regconfig, content)) STORED,
    created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL,
    title text
);


ALTER TABLE public.archon_crawled_pages OWNER TO postgres;

--
-- Name: archon_crawled_pages_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.archon_crawled_pages_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.archon_crawled_pages_id_seq OWNER TO postgres;

--
-- Name: archon_crawled_pages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.archon_crawled_pages_id_seq OWNED BY public.archon_crawled_pages.id;


--
-- Name: archon_crawler_targets; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.archon_crawler_targets (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    target_url text NOT NULL,
    max_depth integer DEFAULT 5,
    is_active boolean DEFAULT true,
    description text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.archon_crawler_targets OWNER TO postgres;

--
-- Name: archon_extraction_schemas; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.archon_extraction_schemas (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name text NOT NULL,
    domain_pattern text NOT NULL,
    schema_definition jsonb DEFAULT '{}'::jsonb NOT NULL,
    target_role text,
    description text,
    is_active boolean DEFAULT true,
    created_by uuid,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.archon_extraction_schemas OWNER TO postgres;

--
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
    lost_competitor text
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
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.archon_projects OWNER TO postgres;

--
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
-- Name: customers; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.customers (
    id uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    name text NOT NULL,
    email text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.customers OWNER TO postgres;

--
-- Name: TABLE customers; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.customers IS '儲存客戶資訊。';


--
-- Name: COLUMN customers.name; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.customers.name IS '客戶的完整名稱或公司名稱。';


--
-- Name: COLUMN customers.email; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.customers.email IS '客戶的主要聯絡電子郵件。';


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
-- Name: market_insights; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.market_insights (
    id uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    keyword text NOT NULL,
    insight_summary text,
    related_blog_id text,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.market_insights OWNER TO postgres;

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
-- Name: subscriptions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.subscriptions (
    id uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    email text NOT NULL,
    lead_id uuid,
    status text DEFAULT 'active'::text,
    tags text[],
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.subscriptions OWNER TO postgres;

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
    created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
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

