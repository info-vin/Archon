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

