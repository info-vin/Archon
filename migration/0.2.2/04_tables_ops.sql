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

