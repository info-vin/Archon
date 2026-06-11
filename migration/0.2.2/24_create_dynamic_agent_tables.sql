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
