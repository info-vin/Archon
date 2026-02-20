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

