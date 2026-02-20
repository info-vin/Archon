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

