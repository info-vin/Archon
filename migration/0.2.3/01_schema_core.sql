-- Source: 01_foundation_types.sql
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


-- Source: 02_tables_core.sql
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
    permission_overrides jsonb DEFAULT '{}'::jsonb,
    tenant_id UUID DEFAULT 'd3b07384-d113-4456-a111-c91823710000'
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


-- Source: 25_create_user_game_saves.sql
-- Migration: Create user_game_saves table for Archon Agency Tycoon cloud saves
-- Category: Business / Games

CREATE TABLE IF NOT EXISTS public.user_game_saves (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    save_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Owner assignment
ALTER TABLE public.user_game_saves OWNER TO postgres;

-- Enable Row Level Security (RLS)
ALTER TABLE public.user_game_saves ENABLE ROW LEVEL SECURITY;

-- Grants
GRANT ALL ON TABLE public.user_game_saves TO authenticated;
GRANT ALL ON TABLE public.user_game_saves TO service_role;

-- RLS Policies
DROP POLICY IF EXISTS "Users can manage their own game saves" ON public.user_game_saves;
CREATE POLICY "Users can manage their own game saves" 
    ON public.user_game_saves 
    FOR ALL 
    TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Description comment
COMMENT ON TABLE public.user_game_saves IS 'Stores serialized tycoon game progress for authenticated users.';


