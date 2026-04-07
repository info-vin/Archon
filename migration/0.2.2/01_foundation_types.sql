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
