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
