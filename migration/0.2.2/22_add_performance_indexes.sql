-- Migration 22: Add Performance Indexes for RAG & Operations
-- 1. Upgrade Vector Indexes from ivfflat to HNSW for superior performance & recall
DROP INDEX IF EXISTS public.archon_code_examples_embedding_idx;
CREATE INDEX archon_code_examples_embedding_idx ON public.archon_code_examples USING hnsw (embedding public.vector_cosine_ops);

DROP INDEX IF EXISTS public.archon_crawled_pages_embedding_idx;
CREATE INDEX archon_crawled_pages_embedding_idx ON public.archon_crawled_pages USING hnsw (embedding public.vector_cosine_ops);

-- 2. Add Composite B-Tree Indexes on High-frequency operational columns
-- Optimize compound filters for tasks (assignee + status)
CREATE INDEX IF NOT EXISTS idx_archon_tasks_assignee_status ON public.archon_tasks (assignee_id, status);

-- Optimize sales pipeline leads scoring & status retrieval
CREATE INDEX IF NOT EXISTS idx_leads_status_enrichment ON public.leads (status, enrichment_score);

-- Optimize log retrieval by severity level and event type
CREATE INDEX IF NOT EXISTS idx_archon_logs_level_type ON public.archon_logs (level, type);

-- Optimize token and ROI calculation aggregates
CREATE INDEX IF NOT EXISTS idx_token_usage_provider_cost ON public.token_usage (provider, cost_usd DESC);
