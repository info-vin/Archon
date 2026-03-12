--
-- PostgreSQL database dump
--


-- Dumped from database version 17.4
-- Dumped by pg_dump version 17.8 (Debian 17.8-0+deb13u1)


--
-- Name: change_status; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.change_status AS ENUM (
    'pending',
    'approved',
    'rejected',
    'executed',
    'failed'
);


ALTER TYPE public.change_status OWNER TO postgres;

--
-- Name: change_type; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.change_type AS ENUM (
    'file',
    'git',
    'shell'
);


ALTER TYPE public.change_type OWNER TO postgres;

--
-- Name: task_status; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.task_status AS ENUM (
    'todo',
    'doing',
    'review',
    'done',
    'failed',
    'processing',
    'dispatched',
    'pending',
    'archived',
    'cancelled'
);


ALTER TYPE public.task_status OWNER TO postgres;

--
-- Name: project_status; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.project_status AS ENUM (
    'planning',
    'active',
    'archived',
    'completed'
);


ALTER TYPE public.project_status OWNER TO postgres;

--
-- Name: blog_status; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.blog_status AS ENUM (
    'draft',
    'review',
    'changes_requested',
    'published'
);


ALTER TYPE public.blog_status OWNER TO postgres;

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

