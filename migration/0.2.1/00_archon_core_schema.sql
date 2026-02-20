-- Archon Core Schema (Consolidated from 000-035)

-- Source: 000_unified_schema.sql
-- =====================================================
-- Archon Complete Database Setup (Unified v1)
-- =====================================================
-- This script combines migrations from 'spike' and 'feature' branches
-- into a single, authoritative file for this branch.
-- =====================================================

-- =====================================================
-- SECTION 1: EXTENSIONS
-- =====================================================

-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- =====================================================
-- SECTION 2: CREDENTIALS AND SETTINGS
-- =====================================================

-- Credentials and Configuration Management Table
CREATE TABLE IF NOT EXISTS archon_settings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    key VARCHAR(255) UNIQUE NOT NULL,
    value TEXT,                    -- For plain text config values
    encrypted_value TEXT,          -- For encrypted sensitive data (bcrypt hashed)
    is_encrypted BOOLEAN DEFAULT FALSE,
    category VARCHAR(100),         -- Group related settings (e.g., 'rag_strategy', 'api_keys', 'server_config')
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_archon_settings_key ON archon_settings(key);
CREATE INDEX IF NOT EXISTS idx_archon_settings_category ON archon_settings(category);

-- Create trigger to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_archon_settings_updated_at ON archon_settings;
CREATE TRIGGER update_archon_settings_updated_at
    BEFORE UPDATE ON archon_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create RLS (Row Level Security) policies for settings
ALTER TABLE archon_settings ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow service role full access" ON archon_settings;
CREATE POLICY "Allow service role full access" ON archon_settings
    FOR ALL USING (auth.role() = 'service_role');

DROP POLICY IF EXISTS "Allow authenticated users to read and update" ON archon_settings;
CREATE POLICY "Allow authenticated users to read and update" ON archon_settings
    FOR ALL TO authenticated
    USING (true);

-- =====================================================
-- SECTION 3: INITIAL SETTINGS DATA
-- =====================================================

-- Server Configuration
INSERT INTO archon_settings (key, value, is_encrypted, category, description) VALUES
('MCP_TRANSPORT', 'dual', false, 'server_config', 'MCP server transport mode - sse (web clients), stdio (IDE clients), or dual (both)'),
('HOST', 'localhost', false, 'server_config', 'Host to bind to if using sse as the transport (leave empty if using stdio)'),
('PORT', '8051', false, 'server_config', 'Port to listen on if using sse as the transport (leave empty if using stdio)'),
('MODEL_CHOICE', 'gpt-4.1-nano', false, 'rag_strategy', 'The LLM you want to use for summaries and contextual embeddings. Generally this is a very cheap and fast LLM like gpt-4.1-nano')
ON CONFLICT (key) DO NOTHING;

-- RAG Strategy Configuration (all default to true)
INSERT INTO archon_settings (key, value, is_encrypted, category, description) VALUES
('USE_CONTEXTUAL_EMBEDDINGS', 'false', false, 'rag_strategy', 'Enhances embeddings with contextual information for better retrieval'),
('CONTEXTUAL_EMBEDDINGS_MAX_WORKERS', '3', false, 'rag_strategy', 'Maximum parallel workers for contextual embedding generation (1-10)'),
('USE_HYBRID_SEARCH', 'true', false, 'rag_strategy', 'Combines vector similarity search with keyword search for better results'),
('USE_AGENTIC_RAG', 'true', false, 'rag_strategy', 'Enables code example extraction, storage, and specialized code search functionality'),
('USE_RERANKING', 'true', false, 'rag_strategy', 'Applies cross-encoder reranking to improve search result relevance')
ON CONFLICT (key) DO NOTHING;

-- Monitoring Configuration
INSERT INTO archon_settings (key, value, is_encrypted, category, description) VALUES
('LOGFIRE_ENABLED', 'true', false, 'monitoring', 'Enable or disable Pydantic Logfire logging and observability platform'),
('PROJECTS_ENABLED', 'true', false, 'features', 'Enable or disable Projects and Tasks functionality')
ON CONFLICT (key) DO NOTHING;

-- Placeholder for sensitive credentials (to be added via Settings UI)
INSERT INTO archon_settings (key, encrypted_value, is_encrypted, category, description) VALUES
('OPENAI_API_KEY', NULL, true, 'api_keys', 'OpenAI API Key for embedding model (text-embedding-3-small). Get from: https://help.openai.com/en/articles/4936850-where-do-i-find-my-openai-api-key')
ON CONFLICT (key) DO NOTHING;

-- LLM Provider configuration settings
INSERT INTO archon_settings (key, value, is_encrypted, category, description) VALUES
('LLM_PROVIDER', 'openai', false, 'rag_strategy', 'LLM provider to use: openai, ollama, or google'),
('LLM_BASE_URL', NULL, false, 'rag_strategy', 'Custom base URL for LLM provider (mainly for Ollama, e.g., http://localhost:11434/v1)'),
('EMBEDDING_MODEL', 'text-embedding-3-small', false, 'rag_strategy', 'Embedding model for vector search and similarity matching (required for all embedding operations)')
ON CONFLICT (key) DO NOTHING;

-- Add provider API key placeholders
INSERT INTO archon_settings (key, encrypted_value, is_encrypted, category, description) VALUES
('GOOGLE_API_KEY', NULL, true, 'api_keys', 'Google API Key for Gemini models. Get from: https://aistudio.google.com/apikey')
ON CONFLICT (key) DO NOTHING;

-- Code Extraction Settings Migration
INSERT INTO archon_settings (key, value, is_encrypted, category, description) VALUES
-- Length Settings
('MIN_CODE_BLOCK_LENGTH', '250', false, 'code_extraction', 'Base minimum length for code blocks in characters'),
('MAX_CODE_BLOCK_LENGTH', '5000', false, 'code_extraction', 'Maximum length before stopping code block extension in characters'),
('CONTEXT_WINDOW_SIZE', '1000', false, 'code_extraction', 'Number of characters of context to preserve before and after code blocks'),
-- Detection Features
('ENABLE_COMPLETE_BLOCK_DETECTION', 'true', false, 'code_extraction', 'Extend code blocks to natural boundaries like closing braces'),
('ENABLE_LANGUAGE_SPECIFIC_PATTERNS', 'true', false, 'code_extraction', 'Use specialized patterns for different programming languages'),
('ENABLE_CONTEXTUAL_LENGTH', 'true', false, 'code_extraction', 'Adjust minimum length based on surrounding context (example, snippet, implementation)'),
-- Content Filtering
('ENABLE_PROSE_FILTERING', 'true', false, 'code_extraction', 'Filter out documentation text mistakenly wrapped in code blocks'),
('MAX_PROSE_RATIO', '0.15', false, 'code_extraction', 'Maximum allowed ratio of prose indicators (0-1) in code blocks'),
('MIN_CODE_INDICATORS', '3', false, 'code_extraction', 'Minimum number of code patterns required (brackets, operators, keywords)'),
('ENABLE_DIAGRAM_FILTERING', 'true', false, 'code_extraction', 'Exclude diagram languages like Mermaid, PlantUML from code extraction'),
-- Processing Settings
('CODE_EXTRACTION_MAX_WORKERS', '3', false, 'code_extraction', 'Number of parallel workers for generating code summaries'),
('ENABLE_CODE_SUMMARIES', 'true', false, 'code_extraction', 'Generate AI-powered summaries and names for extracted code examples')
ON CONFLICT (key) DO NOTHING;

-- Crawling Performance Settings
INSERT INTO archon_settings (key, value, is_encrypted, category, description) VALUES
('CRAWL_BATCH_SIZE', '50', false, 'rag_strategy', 'Number of URLs to crawl in parallel per batch (10-100)'),
('CRAWL_MAX_CONCURRENT', '10', false, 'rag_strategy', 'Maximum concurrent browser sessions for crawling (1-20)'),
('CRAWL_WAIT_STRATEGY', 'domcontentloaded', false, 'rag_strategy', 'When to consider page loaded: domcontentloaded, networkidle, or load'),
('CRAWL_PAGE_TIMEOUT', '30000', false, 'rag_strategy', 'Maximum time to wait for page load in milliseconds'),
('CRAWL_DELAY_BEFORE_HTML', '0.5', false, 'rag_strategy', 'Time to wait for JavaScript rendering in seconds (0.1-5.0)')
ON CONFLICT (key) DO NOTHING;

-- Document Storage Performance Settings
INSERT INTO archon_settings (key, value, is_encrypted, category, description) VALUES
('DOCUMENT_STORAGE_BATCH_SIZE', '100', false, 'rag_strategy', 'Number of document chunks to process per batch (50-200) - increased for better performance'),
('EMBEDDING_BATCH_SIZE', '200', false, 'rag_strategy', 'Number of embeddings to create per API call (100-500) - increased for better throughput'),
('DELETE_BATCH_SIZE', '100', false, 'rag_strategy', 'Number of URLs to delete in one database operation (50-200) - increased for better performance'),
('ENABLE_PARALLEL_BATCHES', 'true', false, 'rag_strategy', 'Enable parallel processing of document batches')
ON CONFLICT (key) DO UPDATE SET
    value = EXCLUDED.value,
    description = EXCLUDED.description;

-- Advanced Performance Settings
INSERT INTO archon_settings (key, value, is_encrypted, category, description) VALUES
('MEMORY_THRESHOLD_PERCENT', '80', false, 'rag_strategy', 'Memory usage threshold for crawler dispatcher (50-90)'),
('DISPATCHER_CHECK_INTERVAL', '0.5', false, 'rag_strategy', 'How often to check memory usage in seconds (0.1-2.0)'),
('CODE_EXTRACTION_BATCH_SIZE', '40', false, 'rag_strategy', 'Number of code blocks to extract per batch (20-100) - increased for better performance'),
('CODE_SUMMARY_MAX_WORKERS', '3', false, 'rag_strategy', 'Maximum parallel workers for code summarization (1-10)'),
('CONTEXTUAL_EMBEDDING_BATCH_SIZE', '50', false, 'rag_strategy', 'Number of chunks to process in contextual embedding batch API calls (20-100)')
ON CONFLICT (key) DO UPDATE SET
    value = EXCLUDED.value,
    description = EXCLUDED.description;

COMMENT ON TABLE archon_settings IS 'Stores application configuration including API keys, RAG settings, and code extraction parameters';

-- =====================================================
-- SECTION 4: KNOWLEDGE BASE TABLES
-- =====================================================

-- Create the sources table
CREATE TABLE IF NOT EXISTS archon_sources (
    source_id TEXT PRIMARY KEY,
    source_url TEXT,
    source_display_name TEXT,
    summary TEXT,
    total_word_count INTEGER DEFAULT 0,
    title TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_archon_sources_title ON archon_sources(title);
CREATE INDEX IF NOT EXISTS idx_archon_sources_url ON archon_sources(source_url);
CREATE INDEX IF NOT EXISTS idx_archon_sources_display_name ON archon_sources(source_display_name);
CREATE INDEX IF NOT EXISTS idx_archon_sources_metadata ON archon_sources USING GIN(metadata);
CREATE INDEX IF NOT EXISTS idx_archon_sources_knowledge_type ON archon_sources((metadata->>'knowledge_type'));

-- Add comments to document the columns
COMMENT ON COLUMN archon_sources.source_id IS 'Unique hash identifier for the source (16-char SHA256 hash of URL)';
COMMENT ON COLUMN archon_sources.source_url IS 'The original URL that was crawled to create this source';
COMMENT ON COLUMN archon_sources.source_display_name IS 'Human-readable name for UI display (e.g., "GitHub - microsoft/typescript")';
COMMENT ON COLUMN archon_sources.title IS 'Descriptive title for the source (e.g., "Pydantic AI API Reference")';
COMMENT ON COLUMN archon_sources.metadata IS 'JSONB field storing knowledge_type, tags, and other metadata';

-- Create the documentation chunks table
CREATE TABLE IF NOT EXISTS archon_crawled_pages (
    id BIGSERIAL PRIMARY KEY,
    url VARCHAR NOT NULL,
    chunk_number INTEGER NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    source_id TEXT NOT NULL,
    embedding VECTOR(768),  -- Google's text-embedding-004 model has 768 dimensions
    content_search_vector tsvector GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(url, chunk_number),
    FOREIGN KEY (source_id) REFERENCES archon_sources(source_id)
);

-- Create indexes for better performance
CREATE INDEX ON archon_crawled_pages USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_archon_crawled_pages_metadata ON archon_crawled_pages USING GIN (metadata);
CREATE INDEX idx_archon_crawled_pages_source_id ON archon_crawled_pages (source_id);
CREATE INDEX idx_archon_crawled_pages_content_search ON archon_crawled_pages USING GIN (content_search_vector);
CREATE INDEX idx_archon_crawled_pages_content_trgm ON archon_crawled_pages USING GIN (content gin_trgm_ops);

-- Create the code_examples table
CREATE TABLE IF NOT EXISTS archon_code_examples (
    id BIGSERIAL PRIMARY KEY,
    url VARCHAR NOT NULL,
    chunk_number INTEGER NOT NULL,
    content TEXT NOT NULL,  -- The code example content
    summary TEXT NOT NULL,  -- Summary of the code example
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    source_id TEXT NOT NULL,
    embedding VECTOR(768),  -- Google's text-embedding-004 model has 768 dimensions
    content_search_vector tsvector GENERATED ALWAYS AS (to_tsvector('english', content || ' ' || COALESCE(summary, ''))) STORED,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(url, chunk_number),
    FOREIGN KEY (source_id) REFERENCES archon_sources(source_id)
);

-- Create indexes for better performance
CREATE INDEX ON archon_code_examples USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_archon_code_examples_metadata ON archon_code_examples USING GIN (metadata);
CREATE INDEX idx_archon_code_examples_source_id ON archon_code_examples (source_id);
CREATE INDEX idx_archon_code_examples_content_search ON archon_code_examples USING GIN (content_search_vector);
CREATE INDEX idx_archon_code_examples_content_trgm ON archon_code_examples USING GIN (content gin_trgm_ops);
CREATE INDEX idx_archon_code_examples_summary_trgm ON archon_code_examples USING GIN (summary gin_trgm_ops);

-- =====================================================
-- SECTION 5: SEARCH FUNCTIONS
-- =====================================================

-- Create a function to search for documentation chunks
CREATE OR REPLACE FUNCTION match_archon_crawled_pages (
  query_embedding VECTOR(768),
  match_count INT DEFAULT 10,
  filter JSONB DEFAULT '{}'::jsonb,
  source_filter TEXT DEFAULT NULL
) RETURNS TABLE (
  id BIGINT,
  url VARCHAR,
  chunk_number INTEGER,
  content TEXT,
  metadata JSONB,
  source_id TEXT,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
#variable_conflict use_column
BEGIN
  RETURN QUERY
  SELECT
    id,
    url,
    chunk_number,
    content,
    metadata,
    source_id,
    1 - (archon_crawled_pages.embedding <=> query_embedding) AS similarity
  FROM archon_crawled_pages
  WHERE metadata @> filter
    AND (source_filter IS NULL OR source_id = source_filter)
  ORDER BY archon_crawled_pages.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- Create a function to search for code examples
CREATE OR REPLACE FUNCTION match_archon_code_examples (
  query_embedding VECTOR(768),
  match_count INT DEFAULT 10,
  filter JSONB DEFAULT '{}'::jsonb,
  source_filter TEXT DEFAULT NULL
) RETURNS TABLE (
  id BIGINT,
  url VARCHAR,
  chunk_number INTEGER,
  content TEXT,
  summary TEXT,
  metadata JSONB,
  source_id TEXT,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
#variable_conflict use_column
BEGIN
  RETURN QUERY
  SELECT
    id,
    url,
    chunk_number,
    content,
    summary,
    metadata,
    source_id,
    1 - (archon_code_examples.embedding <=> query_embedding) AS similarity
  FROM archon_code_examples
  WHERE metadata @> filter
    AND (source_filter IS NULL OR source_id = source_filter)
  ORDER BY archon_code_examples.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- =====================================================
-- SECTION 5B: HYBRID SEARCH FUNCTIONS WITH TS_VECTOR
-- =====================================================

-- Hybrid search function for archon_crawled_pages
CREATE OR REPLACE FUNCTION hybrid_search_archon_crawled_pages(
    query_embedding vector(768),
    query_text TEXT,
    match_count INT DEFAULT 10,
    filter JSONB DEFAULT '{}'::jsonb,
    source_filter TEXT DEFAULT NULL
)
RETURNS TABLE (
    id BIGINT,
    url VARCHAR,
    chunk_number INTEGER,
    content TEXT,
    metadata JSONB,
    source_id TEXT,
    similarity FLOAT,
    match_type TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    max_vector_results INT;
    max_text_results INT;
BEGIN
    -- Calculate how many results to fetch from each search type
    max_vector_results := match_count;
    max_text_results := match_count;
    
    RETURN QUERY
    WITH vector_results AS (
        -- Vector similarity search
        SELECT 
            cp.id,
            cp.url,
            cp.chunk_number,
            cp.content,
            cp.metadata,
            cp.source_id,
            1 - (cp.embedding <=> query_embedding) AS vector_sim
        FROM archon_crawled_pages cp
        WHERE cp.metadata @> filter
            AND (source_filter IS NULL OR cp.source_id = source_filter)
            AND cp.embedding IS NOT NULL
        ORDER BY cp.embedding <=> query_embedding
        LIMIT max_vector_results
    ),
    text_results AS (
        -- Full-text search with ranking
        SELECT 
            cp.id,
            cp.url,
            cp.chunk_number,
            cp.content,
            cp.metadata,
            cp.source_id,
            ts_rank_cd(cp.content_search_vector, plainto_tsquery('english', query_text)) AS text_sim
        FROM archon_crawled_pages cp
        WHERE cp.metadata @> filter
            AND (source_filter IS NULL OR cp.source_id = source_filter)
            AND cp.content_search_vector @@ plainto_tsquery('english', query_text)
        ORDER BY text_sim DESC
        LIMIT max_text_results
    ),
    combined_results AS (
        -- Combine results from both searches
        SELECT 
            COALESCE(v.id, t.id) AS id,
            COALESCE(v.url, t.url) AS url,
            COALESCE(v.chunk_number, t.chunk_number) AS chunk_number,
            COALESCE(v.content, t.content) AS content,
            COALESCE(v.metadata, t.metadata) AS metadata,
            COALESCE(v.source_id, t.source_id) AS source_id,
            COALESCE(v.vector_sim, t.text_sim, 0)::float8 AS similarity,
            CASE 
                WHEN v.id IS NOT NULL AND t.id IS NOT NULL THEN 'hybrid'
                WHEN v.id IS NOT NULL THEN 'vector'
                ELSE 'keyword'
            END AS match_type
        FROM vector_results v
        FULL OUTER JOIN text_results t ON v.id = t.id
    )
    SELECT * FROM combined_results
    ORDER BY similarity DESC
    LIMIT match_count;
END;
$$;

-- Hybrid search function for archon_code_examples
CREATE OR REPLACE FUNCTION hybrid_search_archon_code_examples(
    query_embedding vector(768),
    query_text TEXT,
    match_count INT DEFAULT 10,
    filter JSONB DEFAULT '{}'::jsonb,
    source_filter TEXT DEFAULT NULL
)
RETURNS TABLE (
    id BIGINT,
    url VARCHAR,
    chunk_number INTEGER,
    content TEXT,
    summary TEXT,
    metadata JSONB,
    source_id TEXT,
    similarity FLOAT,
    match_type TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    max_vector_results INT;
    max_text_results INT;
BEGIN
    -- Calculate how many results to fetch from each search type
    max_vector_results := match_count;
    max_text_results := match_count;
    
    RETURN QUERY
    WITH vector_results AS (
        -- Vector similarity search
        SELECT 
            ce.id,
            ce.url,
            ce.chunk_number,
            ce.content,
            ce.summary,
            ce.metadata,
            ce.source_id,
            1 - (ce.embedding <=> query_embedding) AS vector_sim
        FROM archon_code_examples ce
        WHERE ce.metadata @> filter
            AND (source_filter IS NULL OR ce.source_id = source_filter)
            AND ce.embedding IS NOT NULL
        ORDER BY ce.embedding <=> query_embedding
        LIMIT max_vector_results
    ),
    text_results AS (
        -- Full-text search with ranking (searches both content and summary)
        SELECT 
            ce.id,
            ce.url,
            ce.chunk_number,
            ce.content,
            ce.summary,
            ce.metadata,
            ce.source_id,
            ts_rank_cd(ce.content_search_vector, plainto_tsquery('english', query_text)) AS text_sim
        FROM archon_code_examples ce
        WHERE ce.metadata @> filter
            AND (source_filter IS NULL OR ce.source_id = source_filter)
            AND ce.content_search_vector @@ plainto_tsquery('english', query_text)
        ORDER BY text_sim DESC
        LIMIT max_text_results
    ),
    combined_results AS (
        -- Combine results from both searches
        SELECT 
            COALESCE(v.id, t.id) AS id,
            COALESCE(v.url, t.url) AS url,
            COALESCE(v.chunk_number, t.chunk_number) AS chunk_number,
            COALESCE(v.content, t.content) AS content,
            COALESCE(v.summary, t.summary) AS summary,
            COALESCE(v.metadata, t.metadata) AS metadata,
            COALESCE(v.source_id, t.source_id) AS source_id,
            COALESCE(v.vector_sim, t.text_sim, 0)::float8 AS similarity,
            CASE 
                WHEN v.id IS NOT NULL AND t.id IS NOT NULL THEN 'hybrid'
                WHEN v.id IS NOT NULL THEN 'vector'
                ELSE 'keyword'
            END AS match_type
        FROM vector_results v
        FULL OUTER JOIN text_results t ON v.id = t.id
    )
    SELECT * FROM combined_results
    ORDER BY similarity DESC
    LIMIT match_count;
END;
$$;

COMMENT ON FUNCTION hybrid_search_archon_crawled_pages IS 'Performs hybrid search combining vector similarity and full-text search with configurable weighting';
COMMENT ON FUNCTION hybrid_search_archon_code_examples IS 'Performs hybrid search on code examples combining vector similarity and full-text search';

-- =====================================================
-- SECTION 6: RLS POLICIES FOR KNOWLEDGE BASE
-- =====================================================

-- Enable RLS on the knowledge base tables
ALTER TABLE archon_crawled_pages ENABLE ROW LEVEL SECURITY;
ALTER TABLE archon_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE archon_code_examples ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow public read access to archon_crawled_pages" ON archon_crawled_pages;
CREATE POLICY "Allow public read access to archon_crawled_pages"
  ON archon_crawled_pages
  FOR SELECT
  TO public
  USING (true);

DROP POLICY IF EXISTS "Allow public read access to archon_sources" ON archon_sources;
CREATE POLICY "Allow public read access to archon_sources"
  ON archon_sources
  FOR SELECT
  TO public
  USING (true);

DROP POLICY IF EXISTS "Allow public read access to archon_code_examples" ON archon_code_examples;
CREATE POLICY "Allow public read access to archon_code_examples"
  ON archon_code_examples
  FOR SELECT
  TO public
  USING (true);

-- =====================================================
-- SECTION 7: PROJECTS AND TASKS MODULE
-- =====================================================

-- Task status enumeration
DO $$ BEGIN
    CREATE TYPE task_status AS ENUM ('todo','doing','review','done');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Projects table
CREATE TABLE IF NOT EXISTS archon_projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  description TEXT DEFAULT '',
  docs JSONB DEFAULT '[]'::jsonb,
  features JSONB DEFAULT '[]'::jsonb,
  data JSONB DEFAULT '[]'::jsonb,
  github_repo TEXT,
  pinned BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tasks table
CREATE TABLE IF NOT EXISTS archon_tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES archon_projects(id) ON DELETE CASCADE,
  parent_task_id UUID REFERENCES archon_tasks(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  description TEXT DEFAULT '',
  status task_status DEFAULT 'todo',
  assignee TEXT DEFAULT 'User' CHECK (assignee IS NOT NULL AND assignee != ''),
  task_order INTEGER DEFAULT 0,
  feature TEXT,
  sources JSONB DEFAULT '[]'::jsonb,
  code_examples JSONB DEFAULT '[]'::jsonb,
  attachments JSONB,
  archived BOOLEAN DEFAULT false,
  archived_at TIMESTAMPTZ NULL,
  archived_by TEXT NULL,
  due_date TIMESTAMPTZ,
  priority TEXT,
  completed_at TIMESTAMPTZ NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Project Sources junction table for many-to-many relationship
CREATE TABLE IF NOT EXISTS archon_project_sources (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES archon_projects(id) ON DELETE CASCADE,
  source_id TEXT NOT NULL, -- References sources in the knowledge base
  linked_at TIMESTAMPTZ DEFAULT NOW(),
  created_by TEXT DEFAULT 'system',
  notes TEXT,
  UNIQUE(project_id, source_id)
);

-- Document Versions table for version control of project JSONB fields only
CREATE TABLE IF NOT EXISTS archon_document_versions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES archon_projects(id) ON DELETE CASCADE,
  task_id UUID REFERENCES archon_tasks(id) ON DELETE CASCADE, -- DEPRECATED: No longer used, kept for historical data
  field_name TEXT NOT NULL, -- 'docs', 'features', 'data', 'prd' (task fields no longer versioned)
  version_number INTEGER NOT NULL,
  content JSONB NOT NULL, -- Full snapshot of the field content
  change_summary TEXT, -- Human-readable description of changes
  change_type TEXT DEFAULT 'update', -- 'create', 'update', 'delete', 'restore', 'backup'
  document_id TEXT, -- For docs array, store the specific document ID
  created_by TEXT DEFAULT 'system',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  CONSTRAINT chk_project_or_task CHECK (
    (project_id IS NOT NULL AND task_id IS NULL) OR
    (project_id IS NULL AND task_id IS NOT NULL)
  ),
  UNIQUE(project_id, task_id, field_name, version_number)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_archon_tasks_project_id ON archon_tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_archon_tasks_status ON archon_tasks(status);
CREATE INDEX IF NOT EXISTS idx_archon_tasks_assignee ON archon_tasks(assignee);
CREATE INDEX IF NOT EXISTS idx_archon_tasks_order ON archon_tasks(task_order);
CREATE INDEX IF NOT EXISTS idx_archon_tasks_archived ON archon_tasks(archived);
CREATE INDEX IF NOT EXISTS idx_archon_tasks_archived_at ON archon_tasks(archived_at);
CREATE INDEX IF NOT EXISTS idx_archon_project_sources_project_id ON archon_project_sources(project_id);
CREATE INDEX IF NOT EXISTS idx_archon_project_sources_source_id ON archon_project_sources(source_id);
CREATE INDEX IF NOT EXISTS idx_archon_document_versions_project_id ON archon_document_versions(project_id);
CREATE INDEX IF NOT EXISTS idx_archon_document_versions_task_id ON archon_document_versions(task_id);
CREATE INDEX IF NOT EXISTS idx_archon_document_versions_field_name ON archon_document_versions(field_name);
CREATE INDEX IF NOT EXISTS idx_archon_document_versions_version_number ON archon_document_versions(version_number);
CREATE INDEX IF NOT EXISTS idx_archon_document_versions_created_at ON archon_document_versions(created_at);

-- Apply triggers to tables
CREATE OR REPLACE TRIGGER update_archon_projects_updated_at
    BEFORE UPDATE ON archon_projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE OR REPLACE TRIGGER update_archon_tasks_updated_at
    BEFORE UPDATE ON archon_tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Soft delete function for tasks
CREATE OR REPLACE FUNCTION archive_task(
    task_id_param UUID,
    archived_by_param TEXT DEFAULT 'system'
)
RETURNS BOOLEAN AS $$
DECLARE
    task_exists BOOLEAN;
BEGIN
    -- Check if task exists and is not already archived
    SELECT EXISTS(
        SELECT 1 FROM archon_tasks
        WHERE id = task_id_param AND archived = FALSE
    ) INTO task_exists;

    IF NOT task_exists THEN
        RETURN FALSE;
    END IF;

    -- Archive the task
    UPDATE archon_tasks
    SET
        archived = TRUE,
        archived_at = NOW(),
        archived_by = archived_by_param,
        updated_at = NOW()
    WHERE id = task_id_param;

    -- Also archive all subtasks
    UPDATE archon_tasks
    SET
        archived = TRUE,
        archived_at = NOW(),
        archived_by = archived_by_param,
        updated_at = NOW()
    WHERE parent_task_id = task_id_param AND archived = FALSE;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

COMMENT ON COLUMN archon_tasks.assignee IS 'The agent or user assigned to this task. Can be any valid agent name or "User"';
COMMENT ON COLUMN archon_tasks.archived IS 'Soft delete flag - TRUE if task is archived/deleted';
COMMENT ON COLUMN archon_tasks.archived_at IS 'Timestamp when task was archived';
COMMENT ON COLUMN archon_tasks.archived_by IS 'User/system that archived the task';

COMMENT ON TABLE archon_document_versions IS 'Version control for JSONB fields in projects only - task versioning has been removed to simplify MCP operations';
COMMENT ON COLUMN archon_document_versions.field_name IS 'Name of JSONB field being versioned (docs, features, data) - task fields and prd removed as unused';
COMMENT ON COLUMN archon_document_versions.content IS 'Full snapshot of field content at this version';
COMMENT ON COLUMN archon_document_versions.change_type IS 'Type of change: create, update, delete, restore, backup';
COMMENT ON COLUMN archon_document_versions.document_id IS 'For docs arrays, the specific document ID that was changed';
COMMENT ON COLUMN archon_document_versions.task_id IS 'DEPRECATED: No longer used for new versions, kept for historical task version data';

-- =====================================================
-- SECTION 8: PROMPTS TABLE
-- =====================================================

-- Prompts table for managing agent system prompts
CREATE TABLE IF NOT EXISTS archon_prompts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  prompt_name TEXT UNIQUE NOT NULL,
  prompt TEXT NOT NULL,
  description TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_archon_prompts_name ON archon_prompts(prompt_name);

-- Add trigger to automatically update updated_at timestamp
CREATE OR REPLACE TRIGGER update_archon_prompts_updated_at
    BEFORE UPDATE ON archon_prompts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- SECTION 9: RLS POLICIES FOR PROJECTS MODULE
-- =====================================================

-- Enable Row Level Security (RLS) for all tables
ALTER TABLE archon_projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE archon_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE archon_project_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE archon_document_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE archon_prompts ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for service role (full access)
DROP POLICY IF EXISTS "Allow service role full access to archon_projects" ON archon_projects;
CREATE POLICY "Allow service role full access to archon_projects" ON archon_projects
    FOR ALL USING (auth.role() = 'service_role');

DROP POLICY IF EXISTS "Allow service role full access to archon_tasks" ON archon_tasks;
CREATE POLICY "Allow service role full access to archon_tasks" ON archon_tasks
    FOR ALL USING (auth.role() = 'service_role');

DROP POLICY IF EXISTS "Allow service role full access to archon_project_sources" ON archon_project_sources;
CREATE POLICY "Allow service role full access to archon_project_sources" ON archon_project_sources
    FOR ALL USING (auth.role() = 'service_role');

DROP POLICY IF EXISTS "Allow service role full access to archon_document_versions" ON archon_document_versions;
CREATE POLICY "Allow service role full access to archon_document_versions" ON archon_document_versions
    FOR ALL USING (auth.role() = 'service_role');

DROP POLICY IF EXISTS "Allow service role full access to archon_prompts" ON archon_prompts;
CREATE POLICY "Allow service role full access to archon_prompts" ON archon_prompts
    FOR ALL USING (auth.role() = 'service_role');

-- Create RLS policies for authenticated users
DROP POLICY IF EXISTS "Allow authenticated users to read and update archon_projects" ON archon_projects;
CREATE POLICY "Allow authenticated users to read and update archon_projects" ON archon_projects
    FOR ALL TO authenticated
    USING (true);

DROP POLICY IF EXISTS "Allow authenticated users to read and update archon_tasks" ON archon_tasks;
CREATE POLICY "Allow authenticated users to read and update archon_tasks" ON archon_tasks
    FOR ALL TO authenticated
    USING (true);

DROP POLICY IF EXISTS "Allow authenticated users to read and update archon_project_sources" ON archon_project_sources;
CREATE POLICY "Allow authenticated users to read and update archon_project_sources" ON archon_project_sources
    FOR ALL TO authenticated
    USING (true);

DROP POLICY IF EXISTS "Allow authenticated users to read archon_document_versions" ON archon_document_versions;
CREATE POLICY "Allow authenticated users to read archon_document_versions" ON archon_document_versions
    FOR SELECT TO authenticated
    USING (true);

DROP POLICY IF EXISTS "Allow authenticated users to read archon_prompts" ON archon_prompts;
CREATE POLICY "Allow authenticated users to read archon_prompts" ON archon_prompts
    FOR SELECT TO authenticated
    USING (true);

-- =====================================================
-- SECTION 11: PROFILES TABLE (for enduser-ui)
-- =====================================================
CREATE TABLE IF NOT EXISTS profiles (
    id TEXT PRIMARY KEY,
    "employeeId" TEXT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    department TEXT,
    position TEXT,
    status TEXT,
    role TEXT,
    avatar TEXT
);
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow authenticated users to read profiles" ON profiles;
CREATE POLICY "Allow authenticated users to read profiles" ON profiles
    FOR SELECT TO authenticated
    USING (true);

DROP POLICY IF EXISTS "Allow service role full access to profiles" ON profiles;
CREATE POLICY "Allow service role full access to profiles" ON profiles
    FOR ALL USING (auth.role() = 'service_role');

-- =====================================================
-- SECTION 12: BLOG POSTS TABLE (for enduser-ui)
-- =====================================================
CREATE TABLE IF NOT EXISTS blog_posts (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    excerpt TEXT,
    content TEXT NOT NULL, -- Added based on Pydantic model
    author_name TEXT,
    publish_date TIMESTAMPTZ,
    image_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(), -- Added based on Pydantic model
    updated_at TIMESTAMPTZ DEFAULT NOW()  -- Added for consistency
);
ALTER TABLE blog_posts ENABLE ROW LEVEL SECURITY;

-- Add trigger to automatically update updated_at timestamp
CREATE OR REPLACE TRIGGER update_blog_posts_updated_at
    BEFORE UPDATE ON blog_posts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP POLICY IF EXISTS "Allow public read access to blog_posts" ON blog_posts;
CREATE POLICY "Allow public read access to blog_posts" ON blog_posts
    FOR SELECT TO public
    USING (true);

-- =====================================================
-- SECTION 13: FEATURE-BRANCH TABLES
-- =====================================================

-- From 20250901_create_gemini_logs_table.sql
CREATE TABLE IF NOT EXISTS gemini_logs (
    id SERIAL PRIMARY KEY,
    user_input TEXT,
    gemini_response TEXT NOT NULL,
    project_name VARCHAR(255),
    user_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- From 20250905_add_customers_and_vendors_tables.sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    email TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS vendors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    service_type TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE customers IS '儲存客戶資訊。';
COMMENT ON COLUMN customers.name IS '客戶的完整名稱或公司名稱。';
COMMENT ON COLUMN customers.email IS '客戶的主要聯絡電子郵件。';
COMMENT ON TABLE vendors IS '儲存供應商和合作夥伴資訊。';
COMMENT ON COLUMN vendors.name IS '供應商的完整名稱或公司名稱。';
COMMENT ON COLUMN vendors.service_type IS '供應商提供的服務類別（例如："Software", "Consulting"）。';

-- =====================================================
-- SETUP COMPLETE
-- =====================================================

-- Source: 001_add_due_date_to_tasks.sql
-- This script adds the due_date column to the tasks table if it doesn't exist.
ALTER TABLE archon_tasks
ADD COLUMN IF NOT EXISTS due_date TIMESTAMPTZ;

-- Register this migration script as executed in the tracking table.
-- The version identifier is based on the file name.
INSERT INTO schema_migrations (version) VALUES ('001_add_due_date_to_tasks') ON CONFLICT (version) DO NOTHING;

-- Source: 002_create_schema_migrations_table.sql
-- migration/002_create_schema_migrations_table.sql
-- This table tracks which migration scripts have been executed.

CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(255) PRIMARY KEY,
    migrated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);


-- Source: 003_add_get_counts_by_source_function.sql
-- This function efficiently gets the chunk count and code example count for a given array of source_ids.
-- It is designed to be called from the backend service to avoid N+1 query problems when listing knowledge items.

CREATE OR REPLACE FUNCTION get_counts_by_source(source_ids_param text[])
RETURNS TABLE (source_id text, chunk_count bigint, code_example_count bigint)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        s.source_id,
        COALESCE(cp_counts.count, 0) AS chunk_count,
        COALESCE(ce_counts.count, 0) AS code_example_count
    FROM
        public.archon_sources s
    LEFT JOIN (
        SELECT
            p.source_id,
            COUNT(*) as count
        FROM
            public.archon_crawled_pages p
        WHERE
            p.source_id = ANY(source_ids_param)
        GROUP BY
            p.source_id
    ) AS cp_counts ON s.source_id = cp_counts.source_id
    LEFT JOIN (
        SELECT
            e.source_id,
            COUNT(*) as count
        FROM
            public.archon_code_examples e
        WHERE
            e.source_id = ANY(source_ids_param)
        GROUP BY
            e.source_id
    ) AS ce_counts ON s.source_id = ce_counts.source_id
    WHERE
        s.source_id = ANY(source_ids_param);
END;
$$;

-- Register this migration
INSERT INTO schema_migrations (version) VALUES ('003_add_get_counts_by_source_function') ON CONFLICT (version) DO NOTHING;


-- Source: 004_create_test_utility_functions.sql
-- migration/004_create_test_utility_functions.sql

-- This migration file creates utility functions for testing purposes.
-- These functions are designed to be called via Supabase RPC from backend test endpoints.

-- Note: This script assumes the schema has already been created (e.g., by 000_unified_schema.sql).
-- It only provides functions for data manipulation (reset/seed).

-- Ensure schema_migrations table exists to record this.
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(255) PRIMARY KEY,
    applied_at TIMESTAMPTZ DEFAULT NOW()
);

-- Function to reset the database (clear data from seeded tables)
CREATE OR REPLACE FUNCTION reset_test_database()
RETURNS void AS $$
BEGIN
    TRUNCATE TABLE archon_tasks RESTART IDENTITY CASCADE;
    TRUNCATE TABLE archon_projects RESTART IDENTITY CASCADE;
    TRUNCATE TABLE archon_settings RESTART IDENTITY CASCADE;
    TRUNCATE TABLE profiles RESTART IDENTITY CASCADE;
    
    -- Add other tables here if seed_mock_data.sql starts inserting into them
    
    RAISE NOTICE 'Test database data cleared.';
END;
$$ LANGUAGE plpgsql;

-- Function to seed the database
CREATE OR REPLACE FUNCTION seed_test_database()
RETURNS void AS $$
DECLARE
    proj1_id UUID;
    proj2_id UUID;
BEGIN
    -- Seed for profiles table (MOCK_EMPLOYEES)
    INSERT INTO profiles (id, "employeeId", name, email, department, position, status, role, avatar) VALUES
    ('1', 'E1001', 'David Howard', 'admin@archon.com', 'IT', 'System Administrator', 'active', 'Admin', 'https://i.pravatar.cc/150?u=admin@archon.com'),
    ('2', 'E1002', 'Alice Johnson', 'alice@archon.com', 'Engineering', 'Project Manager', 'active', 'PM', 'https://i.pravatar.cc/150?u=alice@archon.com'),
    ('3', 'E1003', 'Bob Williams', 'bob@archon.com', 'Engineering', 'Frontend Developer', 'active', 'Engineer', 'https://i.pravatar.cc/150?u=bob@archon.com'),
    ('4', 'E1004', 'Charlie Brown', 'charlie@archon.com', 'Marketing', 'Marketing Specialist', 'active', 'Marketer', 'https://i.pravatar.cc/150?u=charlie@archon.com'),
    ('5', 'agent-mr-001', 'Market Researcher', 'market.researcher@archon.com', 'AI', 'Market Researcher', 'active', 'Market Researcher', 'https://i.pravatar.cc/150?u=agent-mr-001')
    ON CONFLICT (id) DO NOTHING;

    -- Seed for archon_projects table, ensuring idempotency
    -- Project 1: Archon Core Platform
    IF NOT EXISTS (SELECT 1 FROM archon_projects WHERE title = 'Archon Core Platform') THEN
        INSERT INTO archon_projects (title, description) VALUES
        ('Archon Core Platform', 'Development of the main Archon task management system.')
        RETURNING id INTO proj1_id;
    ELSE
        SELECT id INTO proj1_id FROM archon_projects WHERE title = 'Archon Core Platform';
    END IF;

    -- Project 2: Website Redesign
    IF NOT EXISTS (SELECT 1 FROM archon_projects WHERE title = 'Website Redesign') THEN
        INSERT INTO archon_projects (title, description) VALUES
        ('Website Redesign', 'Complete overhaul of the public-facing marketing website.')
        RETURNING id INTO proj2_id;
    ELSE
        SELECT id INTO proj2_id FROM archon_projects WHERE title = 'Website Redesign';
    END IF;

    -- Seed for archon_tasks table using the captured project UUIDs, ensuring idempotency
    -- Task 1
    IF NOT EXISTS (SELECT 1 FROM archon_tasks WHERE project_id = proj1_id AND title = 'Implement Supabase Integration') THEN
        INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, created_at, updated_at) VALUES
        (proj1_id, 'Implement Supabase Integration', '', 'done', 'Alice Johnson', 1, '2024-09-01T10:00:00Z', '2024-09-05T10:00:00Z');
    END IF;

    -- Task 2
    IF NOT EXISTS (SELECT 1 FROM archon_tasks WHERE project_id = proj1_id AND title = 'Develop Kanban View') THEN
        INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, created_at, updated_at) VALUES
        (proj1_id, 'Develop Kanban View', '', 'doing', 'Bob Williams', 2, '2024-09-02T10:00:00Z', '2024-09-06T10:00:00Z');
    END IF;

    -- Task 3
    IF NOT EXISTS (SELECT 1 FROM archon_tasks WHERE project_id = proj2_id AND title = 'Design new landing page mockups') THEN
        INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, created_at, updated_at) VALUES
        (proj2_id, 'Design new landing page mockups', '', 'todo', 'Unassigned', 1, '2024-09-03T10:00:00Z', '2024-09-03T10:00:00Z');
    END IF;

    -- Task 4
    IF NOT EXISTS (SELECT 1 FROM archon_tasks WHERE project_id = proj1_id AND title = 'Fix authentication bug') THEN
        INSERT INTO archon_tasks (project_id, title, description, status, assignee, task_order, created_at, updated_at) VALUES
        (proj1_id, 'Fix authentication bug', 'Users are reporting intermittent login failures.', 'review', 'Alice Johnson', 3, '2024-09-04T10:00:00Z', '2024-09-08T10:00:00Z');
    END IF;

    -- Seed for archon_settings table
    INSERT INTO archon_settings (key, value, is_encrypted, category, description) VALUES
    ('PROJECTS_ENABLED', 'true', false, 'features', 'Enable or disable Projects and Tasks functionality'),
    ('STYLE_GUIDE_ENABLED', 'true', false, 'features', 'Show UI style guide and components in navigation')
    ON CONFLICT (key) DO NOTHING;

    -- Set the default LLM provider to Google
    INSERT INTO archon_settings (key, value, is_encrypted, category, description)
    VALUES ('LLM_PROVIDER', 'google', false, 'ai', 'The primary LLM provider for embeddings and generation.')
    ON CONFLICT (key) DO UPDATE SET
        value = EXCLUDED.value,
        updated_at = NOW();

    RAISE NOTICE 'Test database seeded.';
END;
$$ LANGUAGE plpgsql;
-- Register this migration
INSERT INTO schema_migrations (version) VALUES ('004_create_test_utility_functions') ON CONFLICT (version) DO NOTHING;


-- Source: 005_create_proposed_changes_table.sql
-- migration/005_create_proposed_changes_table.sql

-- 1. Create Enumerated Types for Status and Type
--    Using custom types ensures data integrity and consistency.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'change_status') THEN
        CREATE TYPE change_status AS ENUM ('pending', 'approved', 'rejected', 'executed', 'failed');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'change_type') THEN
        CREATE TYPE change_type AS ENUM ('file', 'git', 'shell');
    END IF;
END$$;

-- 2. Create the proposed_changes Table
--    This table is the core of the "propose-approve-execute" security model.
--    It stores all AI-proposed changes, their status, and the necessary data
--    to execute them upon approval.
CREATE TABLE IF NOT EXISTS proposed_changes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Core Attributes
    status change_status NOT NULL DEFAULT 'pending',
    type change_type NOT NULL,

    -- The request_payload stores the specifics of the proposed change.
    -- For example, for a 'file' type, it would contain:
    -- { "file_path": "src/main.py", "new_content": "..." }
    request_payload JSONB NOT NULL,

    -- Approval Tracking
    approved_by UUID REFERENCES auth.users(id),
    approved_at TIMESTAMPTZ,

    -- Execution Tracking
    executed_at TIMESTAMPTZ,
    execution_log TEXT
);

-- 3. Add Indexes for Performance
--    We will frequently query by status and type.
CREATE INDEX IF NOT EXISTS idx_proposed_changes_status ON proposed_changes(status);
CREATE INDEX IF NOT EXISTS idx_proposed_changes_type ON proposed_changes(type);

-- 4. Enable Row-Level Security (RLS)
--    This is a critical security measure to ensure users can only see and
--    act on changes they are authorized to.
ALTER TABLE proposed_changes ENABLE ROW LEVEL SECURITY;

-- 5. Create RLS Policies
--    Define who can do what with the data.
--
--    - Admins can do anything.
--    - Authenticated users can create proposals.
--    - Authenticated users can view their own proposals and any pending proposals.
--    - Only specific roles (e.g., 'service_role' for backend, maybe a future 'manager' role) can approve.
DROP POLICY IF EXISTS "Allow full access to admins" ON proposed_changes;
CREATE POLICY "Allow full access to admins"
    ON proposed_changes FOR ALL
    USING ((auth.jwt() ->> 'role') = 'service_role'); -- Using service_role as admin for now

DROP POLICY IF EXISTS "Allow authenticated users to create proposals" ON proposed_changes;
CREATE POLICY "Allow authenticated users to create proposals"
    ON proposed_changes FOR INSERT
    WITH CHECK (auth.role() = 'authenticated');

DROP POLICY IF EXISTS "Allow authenticated users to view proposals" ON proposed_changes;
CREATE POLICY "Allow authenticated users to view proposals"
    ON proposed_changes FOR SELECT
    USING (auth.role() = 'authenticated');


-- 6. Add Comments for Clarity
COMMENT ON TABLE proposed_changes IS 'Stores AI-proposed changes that require human approval before execution.';
COMMENT ON COLUMN proposed_changes.status IS 'The current status of the proposed change (e.g., pending, approved).';
COMMENT ON COLUMN proposed_changes.type IS 'The type of change proposed (e.g., file, git, shell).';
COMMENT ON COLUMN proposed_changes.request_payload IS 'A JSON object containing the detailed parameters for the change.';
COMMENT ON COLUMN proposed_changes.approved_by IS 'The user who approved the change.';


-- Source: 006_create_sales_intel_tables.sql
-- Migration: 006_create_sales_intel_tables.sql
-- Description: Creates tables for Sales Intelligence (Leads and Market Insights)
-- Date: 2026-01-05

-- 1. 潛在客戶表 (Leads Table)
-- Stores companies identified via job market search that have potential needs.
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_name TEXT NOT NULL,          -- 公司名稱
    source_job_url TEXT,                 -- 來源職缺連結
    status TEXT DEFAULT 'new',           -- 狀態: new, contacted, qualified, converted
    identified_need TEXT,                -- 識別出的需求 (e.g. "Needs BI Tool")
    assigned_sales_id UUID REFERENCES auth.users(id), -- 分配給哪位業務
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. 市場洞察表 (Market Insights Table)
-- Stores aggregated data or specific analysis results generated by Agents.
CREATE TABLE IF NOT EXISTS market_insights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    keyword TEXT NOT NULL,               -- 搜尋關鍵字 (e.g. "Business Analyst")
    insight_summary TEXT,                -- AI 生成的市場分析摘要
    related_blog_id TEXT REFERENCES blog_posts(id), -- 建議搭配的部落格文章 (Text to match blog_posts.id)
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add updated_at trigger for leads
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_leads_updated_at ON leads;
CREATE TRIGGER update_leads_updated_at
    BEFORE UPDATE ON leads
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (RLS)
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE market_insights ENABLE ROW LEVEL SECURITY;

-- Simple policies (Can be refined later based on RBAC requirements)
-- Allow authenticated users to select records
DROP POLICY IF EXISTS "Allow authenticated users to view leads" ON leads;
CREATE POLICY "Allow authenticated users to view leads" ON leads
    FOR SELECT USING (auth.role() = 'authenticated');

DROP POLICY IF EXISTS "Allow authenticated users to view insights" ON market_insights;
CREATE POLICY "Allow authenticated users to view insights" ON market_insights
    FOR SELECT USING (auth.role() = 'authenticated');

-- 註冊此遷移腳本的版本
INSERT INTO schema_migrations (version) VALUES ('006_create_sales_intel_tables') ON CONFLICT (version) DO NOTHING;



-- Source: 007_add_assignee_id_to_tasks.sql
-- Migration: Add assignee_id to archon_tasks and link to profiles
-- Purpose: Switch from name-based assignment to ID-based assignment for robust RBAC.

-- 1. Add the new column
ALTER TABLE archon_tasks 
ADD COLUMN IF NOT EXISTS assignee_id TEXT; -- Using TEXT to match profiles.id type

-- 2. Create Foreign Key constraint
-- We reference public.profiles because it contains both human users and AI agents
DO $$ BEGIN
    ALTER TABLE archon_tasks 
    ADD CONSTRAINT fk_archon_tasks_assignee 
    FOREIGN KEY (assignee_id) 
    REFERENCES profiles(id)
    ON DELETE SET NULL;
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 3. Create Index for performance
CREATE INDEX IF NOT EXISTS idx_archon_tasks_assignee_id ON archon_tasks(assignee_id);

-- 4. Data Migration: Backfill assignee_id based on assignee (Name)
-- This is a best-effort update for existing data.
UPDATE archon_tasks t
SET assignee_id = p.id
FROM profiles p
WHERE t.assignee = p.name
  AND t.assignee_id IS NULL;

-- 5. Handle 'User' or 'Unassigned' cases (optional, leave as NULL)
-- If assignee is 'User', we might leave it NULL or assign to a default if one exists.

-- 6. Register migration
INSERT INTO schema_migrations (version) 
VALUES ('007_add_assignee_id_to_tasks') 
ON CONFLICT (version) DO NOTHING;


-- Source: 008_system_correction_phase44.sql
-- migration/008_system_correction_phase44.sql

-- 1. Enhance Vendors Table (Sales Nexus)
-- Adding fields to support the sales workflow
ALTER TABLE vendors
ADD COLUMN IF NOT EXISTS pain_points TEXT,
ADD COLUMN IF NOT EXISTS owner_id UUID REFERENCES auth.users(id),
ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'qualified',
ADD COLUMN IF NOT EXISTS contact_info JSONB DEFAULT '{}'::jsonb;

-- 2. Enhance Tasks Table (Management)
-- Adding time tracking fields
ALTER TABLE archon_tasks
ADD COLUMN IF NOT EXISTS estimated_hours FLOAT DEFAULT 0,
ADD COLUMN IF NOT EXISTS actual_hours FLOAT DEFAULT 0;

-- 3. Enhance Leads Table (Sales Nexus)
-- Adding link to projects and contact details
ALTER TABLE leads
ADD COLUMN IF NOT EXISTS job_title TEXT,           -- ADDED: The hiring position title
ADD COLUMN IF NOT EXISTS description_snippet TEXT,  -- ADDED: Short summary of the job
ADD COLUMN IF NOT EXISTS contact_name TEXT,
ADD COLUMN IF NOT EXISTS contact_email TEXT,
ADD COLUMN IF NOT EXISTS contact_phone TEXT,
ADD COLUMN IF NOT EXISTS linked_project_id UUID REFERENCES archon_projects(id),
ADD COLUMN IF NOT EXISTS last_contacted_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS next_followup_date TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS company_website TEXT; -- ADDED: Official Company Website

-- 4. RAG Enhancement (Librarian)
-- Adding title column for better search result display
ALTER TABLE archon_crawled_pages
ADD COLUMN IF NOT EXISTS title TEXT;

-- Ensure no duplicate leads from same URL
CREATE UNIQUE INDEX IF NOT EXISTS idx_leads_source_url ON leads(source_job_url);

-- 4. Inject "Rebrand" Task for Charlie (Project ECITON)
-- This puts the task on the board for the Manager to see
INSERT INTO archon_tasks (title, description, assignee, status, priority, due_date)
VALUES (
    '[REBRAND] Implement Project Eciton Identity',
    '**Visual Specs**:
* **Style**: Geometric Node-Link Diagram.
* **Palette**: Cyan (#00f2ff) to Purple (#a855f7).
* **Animation**: Pulse effect.

**Action**:
* Assign to **DevBot** to generate `logo-eciton.svg`.',
    'DevBot',
    'todo',
    'high',
    NOW() + INTERVAL '3 days'
);

-- 5. Register Migration Version
INSERT INTO schema_migrations (version) VALUES ('008_system_correction_phase44') ON CONFLICT (version) DO NOTHING;


-- Source: 009_fix_rbac_roles_and_permissions.sql
-- migration/009_fix_rbac_roles_and_permissions.sql

-- 1. Promote Alice and Bob to their specialized roles
-- This aligns the DB data with the roles defined in permissions.py
UPDATE profiles 
SET role = 'sales' 
WHERE email = 'alice@archon.com' AND role = 'member';

UPDATE profiles 
SET role = 'marketing' 
WHERE email = 'bob@archon.com' AND role = 'member';

-- 2. Register Migration
INSERT INTO schema_migrations (version) VALUES ('009_fix_rbac_roles_and_permissions') ON CONFLICT (version) DO NOTHING;


-- Source: 010_bob_and_alice_schema_updates.sql
-- Migration: Add status to blog_posts and extend leads table for Phase 4.4
-- Target: Bob (Marketing) & Alice (Sales)

-- 1. Update blog_posts for Kanban
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'blog_posts' AND column_name = 'status') THEN
        ALTER TABLE blog_posts ADD COLUMN status TEXT DEFAULT 'published';
    END IF;
END $$;

-- 2. Update leads for Sales Nexus
ALTER TABLE leads 
    ADD COLUMN IF NOT EXISTS contact_name TEXT,
    ADD COLUMN IF NOT EXISTS contact_email TEXT,
    ADD COLUMN IF NOT EXISTS contact_phone TEXT,
    ADD COLUMN IF NOT EXISTS next_followup_date TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS linked_project_id TEXT REFERENCES projects(id);

-- 3. Ensure uniqueness for crawler efficiency
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_leads_source_url') THEN
        CREATE UNIQUE INDEX idx_leads_source_url ON leads(source_job_url);
    END IF;
END $$;


-- Source: 011_update_alice_bob_roles.sql
-- Update Alice and Bob roles to match their personas and enable access to specific features
-- Alice -> sales (access to Sales Intel)
-- Bob -> marketing (access to Brand Hub and Sales Intel)

UPDATE profiles
SET role = 'sales'
WHERE email = 'alice@archon.com';

UPDATE profiles
SET role = 'marketing'
WHERE email = 'bob@archon.com';

-- Register this migration
INSERT INTO schema_migrations (version) VALUES ('011_update_alice_bob_roles') ON CONFLICT (version) DO NOTHING;


-- Source: 012_create_archon_logs.sql
-- Create archon_logs table for system-wide event logging (Clockwork, etc)
CREATE TABLE IF NOT EXISTS archon_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source TEXT NOT NULL, -- e.g., 'scheduler', 'bob', 'system'
    level TEXT NOT NULL, -- e.g., 'INFO', 'ERROR', 'WARNING'
    message TEXT NOT NULL,
    details JSONB, -- For storing extra context like probe results
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Add index on created_at for time-based queries
CREATE INDEX IF NOT EXISTS idx_archon_logs_created_at ON archon_logs(created_at DESC);

-- Register migration
INSERT INTO schema_migrations (version) VALUES ('012_create_archon_logs') ON CONFLICT (version) DO NOTHING;


-- Source: 013_seed_system_prompts.sql
-- migration/013_seed_system_prompts.sql
-- Purpose: Seed the 'archon_prompts' table with the "Golden Prompts" extracted from python/src/server/prompts/*.py.
-- This completes the transition to "Prompt as Data" architecture.

-- 1. Product Owner Prompt (POBot) - from pm_prompts.py
INSERT INTO archon_prompts (prompt_name, prompt, description, created_at, updated_at)
VALUES (
    'user_story_refinement',
    'You are an expert Product Owner (PO) and Business Analyst.
Your goal is to refine vague task descriptions into structured User Stories with Acceptance Criteria.

You MUST use Markdown format.

Output Format:
# [Title]

## User Story
**As a** [role],
**I want to** [action],
**So that** [benefit].

## Acceptance Criteria
Please use Gherkin syntax (Given/When/Then) for at least one criteria if possible.
- [ ] **Scenario 1**:
  - Given [context]
  - When [action]
  - Then [expected result]
- [ ] **Scenario 2**:
  - ...

## Technical Notes
(Optional technical implementation details, e.g., API endpoints, database changes)',
    'System prompt for POBot to refine tasks into user stories',
    NOW(),
    NOW()
)
ON CONFLICT (prompt_name) DO UPDATE SET
    prompt = EXCLUDED.prompt,
    updated_at = NOW();

-- 2. Design Prompt (DevBot) - from design_prompts.py
INSERT INTO archon_prompts (prompt_name, prompt, description, created_at, updated_at)
VALUES (
    'svg_logo_design',
    'You are a master SVG designer.
Your task is to generate clean, geometric, and responsive SVG code based on the user''s description.
- Use only valid SVG elements (rect, circle, path, etc.).
- Ensure the SVG is scalable (viewBox).
- Do not include markdown code blocks in the output, just the raw SVG string.',
    'System prompt for DevBot to generate SVG logos',
    NOW(),
    NOW()
)
ON CONFLICT (prompt_name) DO UPDATE SET
    prompt = EXCLUDED.prompt,
    updated_at = NOW();

-- 3. Marketing Prompt (MarketBot) - from marketing_prompts.py
INSERT INTO archon_prompts (prompt_name, prompt, description, created_at, updated_at)
VALUES (
    'blog_post_draft',
    'You are Bob, an expert Marketing Content Writer for Archon.
Goal: Write a structured, engaging blog post based on the topic and provided Context.

Instructions:
1. Use the provided <reference_context> to ground your writing.
2. Quote or reference specific facts found in the context if relevant.
3. If the context contains ''Test Corp'' or specific sales pitches, subtly weave them in as examples.

Format:
- Title: Catchy and relevant
- Content: Markdown formatted. Introduction -> Key Points -> Conclusion.
- Excerpt: A 2-sentence summary.
- Used References: A list of source names you actually used/referenced from the context.

Return JSON format: { "title": "...", "content": "...", "excerpt": "...", "used_references": ["source1"] }',
    'System prompt for MarketBot to draft blog posts with RAG context',
    NOW(),
    NOW()
)
ON CONFLICT (prompt_name) DO UPDATE SET
    prompt = EXCLUDED.prompt,
    updated_at = NOW();

-- 4. Sales Prompt (MarketBot) - from sales_prompts.py
INSERT INTO archon_prompts (prompt_name, prompt, description, created_at, updated_at)
VALUES (
    'sales_pitch_generation',
    'You are a top-tier Sales Representative for Archon, an AI & Data consultancy.
Your goal is to write a personalized, professional, and compelling email pitch to a hiring manager.
Structure: 1. Hook, 2. Value Prop (reference case study), 3. CTA.

OUTPUT FORMAT:
Please provide the output in two sections:
[ENGLISH PITCH]
(English version here)

[CHINESE PITCH]
(Chinese version here, culturally adapted for Taiwan market)',
    'System prompt for MarketBot to generate personalized sales pitches',
    NOW(),
    NOW()
)
ON CONFLICT (prompt_name) DO UPDATE SET
    prompt = EXCLUDED.prompt,
    updated_at = NOW();

-- 5. Register migration version
INSERT INTO schema_migrations (version) VALUES ('013_seed_system_prompts') ON CONFLICT (version) DO NOTHING;


-- Source: 014_vector_rls_policy.sql
-- migration/014_vector_rls_policy.sql
-- Description: Enable Row-Level Security (RLS) for Vector Store tables to enforce department isolation.
-- Corrected Target Tables: archon_sources, archon_crawled_pages, archon_code_examples.
-- User Table: profiles (not employees).

-- 1. Enable RLS
ALTER TABLE archon_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE archon_crawled_pages ENABLE ROW LEVEL SECURITY;
ALTER TABLE archon_code_examples ENABLE ROW LEVEL SECURITY;

-- 2. Policy for archon_sources (Root of Trust)

-- Admin (System Admin & Admin) can see everything
CREATE POLICY admin_all_sources ON archon_sources
    FOR ALL
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM profiles
            WHERE id = auth.uid()::text 
            AND role IN ('system_admin', 'admin')
        )
    );

-- Department Isolation: Users can only see sources from their own department OR 'Public'
CREATE POLICY dept_isolation_read ON archon_sources
    FOR SELECT
    TO authenticated
    USING (
        -- 1. Public content is visible to all
        (metadata->>'department' = 'Public' OR metadata->>'department' IS NULL)
        OR
        -- 2. User's department matches source department
        (metadata->>'department' = (
            SELECT department FROM profiles WHERE id = auth.uid()::text
        ))
        OR
        -- 3. Managers can see everything (Optional, enabling for now for oversight)
        EXISTS (
            SELECT 1 FROM profiles 
            WHERE id = auth.uid()::text 
            AND role IN ('manager', 'project_manager')
        )
    );

-- Write Policy: Users can only insert/update sources for their own department
CREATE POLICY dept_isolation_write ON archon_sources
    FOR INSERT
    TO authenticated
    WITH CHECK (
        metadata->>'department' = (
            SELECT department FROM profiles WHERE id = auth.uid()::text
        )
    );

-- 3. Cascade Policies for Child Tables
-- Inherit visibility from parent source

CREATE POLICY child_pages_isolation ON archon_crawled_pages
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM archon_sources s
            WHERE s.source_id = archon_crawled_pages.source_id
        )
    );

CREATE POLICY child_code_isolation ON archon_code_examples
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM archon_sources s
            WHERE s.source_id = archon_code_examples.source_id
        )
    );

-- Source: 015_fix_vendors_schema.sql
-- Migration: 015_fix_vendors_schema.sql
-- Description: Adds missing contact_email column to vendors table to support Lead Promotion.
-- Fixes: FB-01 (Promote Lead Failure)
-- Date: 2026-01-29

-- 1. Add contact_email to vendors if it doesn't exist
ALTER TABLE vendors
ADD COLUMN IF NOT EXISTS contact_email TEXT;

-- 2. Add owner_id if it doesn't exist (Safety check, should be in 008)
ALTER TABLE vendors
ADD COLUMN IF NOT EXISTS owner_id UUID REFERENCES auth.users(id);

-- 3. Register Migration
INSERT INTO schema_migrations (version) VALUES ('015_fix_vendors_schema') ON CONFLICT (version) DO NOTHING;


-- Source: 016_fix_vendors_rls.sql
-- Migration: 016_fix_vendors_rls.sql
-- Description: Enables RLS on vendors table and adds policies for authenticated users.
-- Fixes: Lead Promotion failures (Alice/Charlie inability to create vendors)
-- Date: 2026-01-29

-- 1. Enable RLS
ALTER TABLE vendors ENABLE ROW LEVEL SECURITY;

-- 2. Create Policies

-- Allow authenticated users to view vendors
DROP POLICY IF EXISTS "Allow authenticated users to select vendors" ON vendors;
CREATE POLICY "Allow authenticated users to select vendors" ON vendors
    FOR SELECT
    TO authenticated
    USING (true);

-- Allow authenticated users to insert vendors (e.g. promoting leads)
DROP POLICY IF EXISTS "Allow authenticated users to insert vendors" ON vendors;
CREATE POLICY "Allow authenticated users to insert vendors" ON vendors
    FOR INSERT
    TO authenticated
    WITH CHECK (true);

-- Allow authenticated users to update vendors
DROP POLICY IF EXISTS "Allow authenticated users to update vendors" ON vendors;
CREATE POLICY "Allow authenticated users to update vendors" ON vendors
    FOR UPDATE
    TO authenticated
    USING (true);

-- 3. Register Migration
INSERT INTO schema_migrations (version) VALUES ('016_fix_vendors_rls') ON CONFLICT (version) DO NOTHING;


-- Source: 017_add_missing_vendor_columns.sql
-- Migration: 017_add_missing_vendor_columns.sql
-- Description: Adds description, status, and updated_at columns to vendors table.
-- Fixes: Lead Promotion failure due to missing columns.
-- Date: 2026-01-29

ALTER TABLE vendors
ADD COLUMN IF NOT EXISTS description TEXT,
ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'active',
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- Register Migration
INSERT INTO schema_migrations (version) VALUES ('017_add_missing_vendor_columns') ON CONFLICT (version) DO NOTHING;


-- Source: 018_fix_blog_posts_id_default.sql
-- Migration: 018_fix_blog_posts_id_default.sql
-- Description: Adds default gen_random_uuid() to blog_posts.id to fix creation error.
-- Fixes: "null value in column id violates not-null constraint"
-- Date: 2026-01-29

-- 1. Ensure pgcrypto is enabled (it should be, but good to be safe)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 2. Alter table to set default for id
ALTER TABLE blog_posts
ALTER COLUMN id SET DEFAULT gen_random_uuid();

-- 3. Ensure other columns have defaults if missing (based on schema review)
ALTER TABLE blog_posts
ALTER COLUMN created_at SET DEFAULT NOW(),
ALTER COLUMN updated_at SET DEFAULT NOW(),
ALTER COLUMN status SET DEFAULT 'draft';

-- Register Migration
INSERT INTO schema_migrations (version) VALUES ('018_fix_blog_posts_id_default') ON CONFLICT (version) DO NOTHING;


-- Source: 019_add_prompts_rls.sql
-- Migration: 019_add_prompts_rls.sql
-- Description: Adds RLS policies for archon_prompts table.
-- Fixes: "prompt 需要哪些supasbase RLS 表?"
-- Date: 2026-01-29

-- 1. Enable RLS on archon_prompts (if not already)
ALTER TABLE archon_prompts ENABLE ROW LEVEL SECURITY;

-- 2. Drop existing policies to avoid conflicts
DROP POLICY IF EXISTS "Enable read access for all authenticated users" ON archon_prompts;
DROP POLICY IF EXISTS "Enable write access for admins" ON archon_prompts;

-- 3. Create Policy: Authenticated users (including Agents) can READ prompts
CREATE POLICY "Enable read access for all authenticated users"
ON archon_prompts FOR SELECT
TO authenticated
USING (true);

-- 4. Create Policy: Only System Admins can MODIFY prompts
-- Note: 'system_admin' role check depends on how role is stored. 
-- Using generic 'authenticated' for now or 'service_role' (which bypasses RLS) is safer if we don't have JWT claims set up perfectly.
-- For Admin UI (User), they are 'authenticated'. We should strictly check for admin role if possible,
-- but typically Admin UI operations might use Service Role or we rely on App Logic.
-- Let's allow update for authenticated for now, or check public.profiles if we want strictness.
-- Ideally:
-- USING (auth.uid() IN (SELECT id FROM public.profiles WHERE role IN ('system_admin', 'admin')))

CREATE POLICY "Enable write access for admins"
ON archon_prompts FOR UPDATE
TO authenticated
USING (
  exists (
    select 1 from public.profiles
    where profiles.id = auth.uid()::text
    and profiles.role in ('system_admin', 'admin')
  )
)
WITH CHECK (
  exists (
    select 1 from public.profiles
    where profiles.id = auth.uid()::text
    and profiles.role in ('system_admin', 'admin')
  )
);

-- Register Migration
INSERT INTO schema_migrations (version) VALUES ('019_add_prompts_rls') ON CONFLICT (version) DO NOTHING;


-- Source: 020_phase46_schema.sql
-- Migration: 020_phase46_schema.sql
-- Description: Phase 4.6 Schema - Mobile Ops, Market Intelligence, and Security Hardening
-- Date: 2026-01-30

-- =====================================================
-- SECTION 1: SECURITY HARDENING (RLS ENFORCEMENT)
-- =====================================================

-- 1.1 Hardening 'customers' table
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;

-- Policy: Allow Read Access for specific roles (Sales, Marketing, Manager, Admin)
DROP POLICY IF EXISTS "Allow authenticated read access" ON customers;
CREATE POLICY "Allow authenticated read access" ON customers
    FOR SELECT TO authenticated
    USING (true);

-- Policy: Allow Insert/Update for Sales, Managers, Admins (Write Access)
-- Note: Checking against auth.jwt() -> role claim or mapping table
DROP POLICY IF EXISTS "Allow write access for sales and management" ON customers;
CREATE POLICY "Allow write access for sales and management" ON customers
    FOR ALL
    USING (
        auth.jwt() ->> 'role' IN ('service_role') OR
        EXISTS (
            SELECT 1 FROM profiles
            WHERE id = auth.uid()::text
            AND role IN ('admin', 'manager', 'sales', 'system_admin')
        )
    );

-- 1.2 Hardening 'gemini_logs' table
ALTER TABLE gemini_logs ENABLE ROW LEVEL SECURITY;

-- Policy: Admins can view logs
DROP POLICY IF EXISTS "Allow admins to view gemini logs" ON gemini_logs;
CREATE POLICY "Allow admins to view gemini logs" ON gemini_logs
    FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM profiles
            WHERE id = auth.uid()::text
            AND role IN ('admin', 'system_admin', 'manager')
        )
    );

-- Policy: Allow insertions from authenticated users (Application logging)
DROP POLICY IF EXISTS "Allow app logging" ON gemini_logs;
CREATE POLICY "Allow app logging" ON gemini_logs
    FOR INSERT TO authenticated
    WITH CHECK (true);

-- 1.3 Hardening 'archon_logs' table (from 012)
ALTER TABLE archon_logs ENABLE ROW LEVEL SECURITY;

-- Policy: Admins can view logs
DROP POLICY IF EXISTS "Allow admins to view archon logs" ON archon_logs;
CREATE POLICY "Allow admins to view archon logs" ON archon_logs
    FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM profiles
            WHERE id = auth.uid()::text
            AND role IN ('admin', 'system_admin', 'manager')
        )
    );

-- Policy: Allow insertions (System services/Agents usually run as service_role, but for user-triggered events allow auth)
DROP POLICY IF EXISTS "Allow system logging" ON archon_logs;
CREATE POLICY "Allow system logging" ON archon_logs
    FOR INSERT TO authenticated
    WITH CHECK (true);


-- =====================================================
-- SECTION 2: NEW FEATURE TABLES
-- =====================================================

-- 2.1 Visit Logs (Mobile Field Ops)
CREATE TABLE IF NOT EXISTS visit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    customer_id UUID REFERENCES customers(id), -- Optional link to existing customer
    lead_id UUID REFERENCES leads(id),         -- Optional link to lead
    
    -- Location Data
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    location_address TEXT,
    
    -- Content
    voice_transcript TEXT,      -- Transcribed text from Gemini
    summary TEXT,               -- AI Generated summary
    follow_up_tasks TEXT[],     -- Extracted action items
    
    -- Media
    audio_url TEXT,             -- Path to stored audio file
    image_urls TEXT[],          -- Photos taken during visit
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS: Users see their own logs. Managers see team logs.
ALTER TABLE visit_logs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own visits" ON visit_logs;
CREATE POLICY "Users can view own visits" ON visit_logs
    FOR SELECT TO authenticated
    USING (
        auth.uid() = user_id OR
        EXISTS (
            SELECT 1 FROM profiles
            WHERE id = auth.uid()::text
            AND role IN ('admin', 'manager', 'system_admin')
        )
    );

DROP POLICY IF EXISTS "Users can insert own visits" ON visit_logs;
CREATE POLICY "Users can insert own visits" ON visit_logs
    FOR INSERT TO authenticated
    WITH CHECK (auth.uid() = user_id);

-- 2.2 Marketing Trends (Cache for Bob's Dash)
CREATE TABLE IF NOT EXISTS marketing_trends (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_date DATE NOT NULL DEFAULT CURRENT_DATE,
    trend_type TEXT NOT NULL, -- 'keyword_growth', 'sankey_flow', 'industry_need'
    data JSONB NOT NULL,      -- The actual dataset for Recharts
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS: Marketing, Manager, Admin can view
ALTER TABLE marketing_trends ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow marketing view" ON marketing_trends
    FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM profiles
            WHERE id = auth.uid()::text
            AND role IN ('marketing', 'manager', 'admin', 'system_admin')
        )
    );

-- 2.3 Subscriptions (Blog Subscribers)
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    lead_id UUID REFERENCES leads(id), -- If converted from a Lead
    status TEXT DEFAULT 'active',      -- active, unsubscribed
    tags TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;


-- =====================================================
-- SECTION 3: SCHEMA UPDATES
-- =====================================================

-- 3.1 Expand Leads Table for Enrichment Loop
ALTER TABLE leads 
ADD COLUMN IF NOT EXISTS enrichment_status TEXT DEFAULT 'pending', -- pending, success, failed
ADD COLUMN IF NOT EXISTS enrichment_score INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_enriched_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS auto_archived_reason TEXT; -- If automated pruning happens

-- Register Migration
INSERT INTO schema_migrations (version) VALUES ('020_phase46_schema') ON CONFLICT (version) DO NOTHING;


-- Source: 021_phase4_6_config_and_ethics.sql
-- migration/021_phase4_6_config_and_ethics.sql

-- 1. Create Ethics Events Table for Compliance Logging
CREATE TABLE IF NOT EXISTS archon_ethics_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    severity TEXT NOT NULL, -- 'low', 'medium', 'high', 'critical'
    event_type TEXT NOT NULL, -- 'hallucination', 'profanity', 'pii_leak', 'policy_violation'
    description TEXT,
    raw_input TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS for Ethics Table
ALTER TABLE archon_ethics_events ENABLE ROW LEVEL SECURITY;

-- Only Managers and Admins can view ethics logs
CREATE POLICY "Allow managers and admins to view ethics logs" ON archon_ethics_events
    FOR SELECT
    USING (auth.role() = 'service_role' OR (SELECT role FROM profiles WHERE id = auth.uid()::text) IN ('manager', 'system_admin'));

-- Service role can insert logs (backend service)
CREATE POLICY "Allow service role to insert ethics logs" ON archon_ethics_events
    FOR INSERT
    WITH CHECK (auth.role() = 'service_role');


-- 2. Insert Model Configurations (Google Defaults)
INSERT INTO archon_settings (key, value, is_encrypted, category, description) VALUES
('AUDIO_MODEL', 'gemini-2.5-flash', false, 'rag_strategy', 'Model used for voice-to-text transcription'),
('MARKETING_MODEL', 'gemini-1.5-flash', false, 'rag_strategy', 'Model used for generating marketing content (blogs, emails)'),
('NANA_BANANA_MODEL', 'imagen-3', false, 'rag_strategy', 'Model used for image generation services'),
('ENABLE_REAL_ENRICHMENT', 'false', false, 'features', 'Toggle to enable real external API calls for lead enrichment')
ON CONFLICT (key) DO UPDATE SET
    value = EXCLUDED.value,
    description = EXCLUDED.description;

-- Update existing defaults to Google where applicable
UPDATE archon_settings SET value = 'google' WHERE key = 'LLM_PROVIDER';
UPDATE archon_settings SET value = 'gemini-1.5-flash' WHERE key = 'MODEL_CHOICE';

-- Register migration
INSERT INTO schema_migrations (version) VALUES ('021_phase4_6_config_and_ethics') ON CONFLICT (version) DO NOTHING;


-- Source: 022_add_blog_lead_relation.sql
-- migration/022_add_blog_lead_relation.sql
-- Description: Connect Blog Posts to Sales Leads and enable Bob's Content Loop
-- Date: 2026-02-02

-- 1. Add columns to blog_posts for traceability and operations
ALTER TABLE blog_posts 
ADD COLUMN IF NOT EXISTS source_lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS publish_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS target_brand TEXT DEFAULT 'Archon';

COMMENT ON COLUMN blog_posts.source_lead_id IS 'The sales lead that inspired this content (Traceability)';
COMMENT ON COLUMN blog_posts.target_brand IS 'Brand channel (e.g., Archon, Nano, Banana)';

-- 2. Update RLS for visit_logs to allow Marketing to read specific logs
-- This is necessary because 020 restricted visit_logs to owner/admin/manager/sales
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'visit_logs' AND policyname = 'Marketing view story logs'
    ) THEN
        CREATE POLICY "Marketing view story logs" ON visit_logs
        FOR SELECT
        TO authenticated
        USING (
            EXISTS (
                SELECT 1 FROM leads 
                WHERE leads.id = visit_logs.lead_id 
                AND (leads.status = 'WON' OR leads.enrichment_score >= 80)
            )
            AND (
                auth.jwt() ->> 'role' = 'marketing' OR 
                EXISTS (
                    SELECT 1 FROM profiles 
                    WHERE id = auth.uid()::text AND role = 'marketing'
                )
            )
        );
    END IF;
END $$;

-- 3. Update RLS for leads (Explicit policy for Marketing context)
-- Note: While a permissive policy exists, this explicitly defines Marketing's authorized view
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'leads' AND policyname = 'Marketing view story candidates'
    ) THEN
        CREATE POLICY "Marketing view story candidates" ON leads
        FOR SELECT
        TO authenticated
        USING (
            (
                auth.jwt() ->> 'role' = 'marketing' OR 
                EXISTS (
                    SELECT 1 FROM profiles 
                    WHERE id = auth.uid()::text AND role = 'marketing'
                )
            )
            AND (status = 'WON' OR enrichment_score >= 80)
        );
    END IF;
END $$;

-- 4. Register Migration
INSERT INTO schema_migrations (version) VALUES ('022_add_blog_lead_relation') ON CONFLICT (version) DO NOTHING;


-- Source: 023_create_token_usage_table.sql
-- Migration: 023_create_token_usage_table
-- Description: Tracks LLM Token Usage usage and cost for Admin System Health Dashboard

-- 1. Create the table
CREATE TABLE IF NOT EXISTS token_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_id TEXT NOT NULL, -- Correlation ID for tracing (can link to archon_logs)
    user_id UUID REFERENCES auth.users(id), -- Who initiated the request (can be null for system tasks)
    model TEXT NOT NULL, -- e.g. 'gpt-4o', 'gemini-1.5-flash'
    provider TEXT NOT NULL, -- e.g. 'openai', 'google', 'ollama'
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER GENERATED ALWAYS AS (input_tokens + output_tokens) STORED,
    cost_usd NUMERIC(10, 6) DEFAULT 0, -- Store calculated cost (up to 6 decimal places for micro-cents)
    context_type TEXT, -- e.g. 'rag_query', 'blog_generation', 'agent_task'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. Enable RLS
ALTER TABLE token_usage ENABLE ROW LEVEL SECURITY;

-- 3. RLS Policies
-- Admin/System can read all
CREATE POLICY "Admins can view all token usage" ON token_usage
    FOR SELECT
    USING (
        auth.uid() IN (SELECT id::uuid FROM public.profiles WHERE role IN ('admin', 'system_admin'))
    );

-- Users can view their own usage (transparency)
CREATE POLICY "Users can view their own usage" ON token_usage
    FOR SELECT
    USING (auth.uid() = user_id);

-- System (Service Role) can insert
-- Note: Service Role bypasses RLS, but we add an explicit policy for clarity/audit if needed
-- For inserts from backend API (which uses Service Key), RLS is bypassed.

-- 4. Indexes for Analytics
CREATE INDEX idx_token_usage_created_at ON token_usage(created_at DESC);
CREATE INDEX idx_token_usage_user_id ON token_usage(user_id);
CREATE INDEX idx_token_usage_model ON token_usage(model);
CREATE INDEX idx_token_usage_request_id ON token_usage(request_id);

-- 5. Comments
COMMENT ON TABLE token_usage IS 'Tracks LLM token consumption and estimated cost for auditing and system health monitoring.';


-- Source: 024_add_contact_info_to_leads.sql
-- Migration: 024_add_contact_info_to_leads.sql
-- Description: Adds contact info columns to leads table to support Sentinel scoring and Mock Data.
-- Date: 2026-02-06

ALTER TABLE leads
ADD COLUMN IF NOT EXISTS contact_name TEXT,
ADD COLUMN IF NOT EXISTS email TEXT,
ADD COLUMN IF NOT EXISTS source TEXT DEFAULT 'manual';

-- Register Migration
INSERT INTO schema_migrations (version) VALUES ('024_add_contact_info_to_leads') ON CONFLICT (version) DO NOTHING;


-- Source: 025_crawler_rbac_settings.sql
-- migration/025_crawler_rbac_settings.sql

-- 1. Insert Crawler RBAC Settings into archon_settings
-- Using category 'crawler_rbac' to group these settings

INSERT INTO archon_settings (key, value, is_encrypted, category, description) VALUES
('CRAWL_MAX_DEPTH_SALES', '2', false, 'crawler_rbac', 'Maximum crawl depth for Sales role (Alice)'),
('CRAWL_MAX_DEPTH_MARKETING', '3', false, 'crawler_rbac', 'Maximum crawl depth for Marketing role (Bob)'),
('CRAWL_MAX_DEPTH_MANAGER', '5', false, 'crawler_rbac', 'Maximum crawl depth for Manager role (Charlie)'),
('CRAWL_MAX_DEPTH_ADMIN', '10', false, 'crawler_rbac', 'Maximum crawl depth for Admin role'),

('CRAWL_CONCURRENT_MAX_SALES', '3', false, 'crawler_rbac', 'Max parallel pages within one crawl for Sales'),
('CRAWL_CONCURRENT_MAX_MARKETING', '5', false, 'crawler_rbac', 'Max parallel pages within one crawl for Marketing'),
('CRAWL_CONCURRENT_MAX_MANAGER', '10', false, 'crawler_rbac', 'Max parallel pages within one crawl for Manager'),
('CRAWL_CONCURRENT_MAX_ADMIN', '20', false, 'crawler_rbac', 'Max parallel pages within one crawl for Admin'),

('CRAWL_ALLOWED_DOMAINS_RESTRICTED', '104.com.tw,github.com,google.com', false, 'crawler_rbac', 'Whitelisted domains for non-admin users (comma separated)')
ON CONFLICT (key) DO UPDATE SET
    value = EXCLUDED.value,
    description = EXCLUDED.description;

-- 2. Register migration
INSERT INTO schema_migrations (version) VALUES ('025_crawler_rbac_settings') ON CONFLICT (version) DO NOTHING;


-- Source: 026_create_extraction_schemas.sql
-- migration/026_create_extraction_schemas.sql

-- 1. Create Extraction Schemas Table
CREATE TABLE IF NOT EXISTS archon_extraction_schemas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    domain_pattern TEXT NOT NULL, -- URL pattern this schema applies to (e.g., "104.com.tw/job/*")
    schema_definition JSONB NOT NULL DEFAULT '{}'::jsonb, -- The fields to extract
    target_role TEXT, -- Optional: restrict this schema to specific roles (e.g., 'sales')
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Add RLS Policies
ALTER TABLE archon_extraction_schemas ENABLE ROW LEVEL SECURITY;

-- Everyone can view schemas (for applying them during crawl)
DROP POLICY IF EXISTS "Allow all authenticated users to view schemas" ON archon_extraction_schemas;
CREATE POLICY "Allow all authenticated users to view schemas" ON archon_extraction_schemas
    FOR SELECT
    USING (auth.role() = 'authenticated' OR auth.role() = 'service_role');

-- Only Managers and Admins can manage schemas
DROP POLICY IF EXISTS "Allow managers and admins to manage schemas" ON archon_extraction_schemas;
CREATE POLICY "Allow managers and admins to manage schemas" ON archon_extraction_schemas
    FOR ALL
    USING (
        auth.role() = 'service_role' OR 
        (SELECT role FROM profiles WHERE id = auth.uid()::text) IN ('manager', 'admin', 'system_admin')
    );

-- 3. Register migration
INSERT INTO schema_migrations (version) VALUES ('026_create_extraction_schemas') ON CONFLICT (version) DO NOTHING;


-- Source: 027_seed_field_ops_project.sql
-- migration/027_seed_field_ops_project.sql

-- 1. Ensure 'Field Ops' project exists for Mobile Voice-to-Task
-- We'll create it if it doesn't exist.
-- Assuming 'admin' is the default creator if nobody else is found.

DO $$
DECLARE
    admin_id UUID;
    field_ops_id UUID;
BEGIN
    -- Get an admin ID to be the owner
    SELECT id INTO admin_id FROM auth.users WHERE email = 'admin@example.com' LIMIT 1;
    
    -- Fallback to any user if admin not found (dev env)
    IF admin_id IS NULL THEN
        SELECT id INTO admin_id FROM auth.users LIMIT 1;
    END IF;

    -- Only create if not exists
    IF NOT EXISTS (SELECT 1 FROM archon_projects WHERE title = 'Field Ops') THEN
        INSERT INTO archon_projects (title, description)
        VALUES (
            'Field Ops', 
            '預設專案，用於接收行動端語音日誌自動生成的任務。 (Alice Persona)'
        ) RETURNING id INTO field_ops_id;
        
        RAISE NOTICE 'Created Field Ops project with ID %', field_ops_id;
    END IF;
END $$;

-- 2. Register migration
INSERT INTO schema_migrations (version) VALUES ('027_seed_field_ops_project') ON CONFLICT (version) DO NOTHING;


-- Source: 028_seed_voice_prompt.sql
-- migration/028_seed_voice_prompt.sql

-- Seed the voice transcription prompt into the system_prompts table
-- This allows Charlie/Admin to tune the extraction logic via UI.

INSERT INTO archon_prompts (prompt_name, prompt, description, created_at, updated_at)
VALUES (
    'VOICE_TRANSCRIPTION_PROMPT',
    '你是一位專業的業務助理。請準確地將這段銷售拜訪錄音轉錄為繁體中文逐字稿，並總結關鍵對話內容與提取具體後續任務清單。請嚴格以 JSON 格式回傳，包含鍵值：''transcript'', ''summary'', ''tasks'' (字串清單)。',
    'Used by the Visit Log API to process audio files via Gemini. Controls how voice notes are transcribed and what tasks are extracted.',
    NOW(),
    NOW()
)
ON CONFLICT (prompt_name) DO UPDATE SET
    prompt = EXCLUDED.prompt,
    description = EXCLUDED.description,
    updated_at = NOW();

-- Register migration
INSERT INTO schema_migrations (version) VALUES ('028_seed_voice_prompt') ON CONFLICT (version) DO NOTHING;


-- Source: 029_fix_archon_logs_schema.sql
-- Migration: 029_fix_archon_logs_schema.sql
-- Description: Add missing 'type' and 'project_name' columns to archon_logs table to support Manager Dashboard.
-- Date: 2026-02-07

DO $$
BEGIN
    -- Add 'type' column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'archon_logs' AND COLUMN_NAME = 'type') THEN
        ALTER TABLE archon_logs ADD COLUMN type TEXT DEFAULT 'general';
    END IF;

    -- Add 'project_name' column if it doesn't exist (used as 'source' in some contexts)
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'archon_logs' AND COLUMN_NAME = 'project_name') THEN
        ALTER TABLE archon_logs ADD COLUMN project_name TEXT;
    END IF;
END $$;

-- Register migration
INSERT INTO schema_migrations (version) VALUES ('029_fix_archon_logs_schema') ON CONFLICT (version) DO NOTHING;


-- Source: 030_schema_hardening_and_mobile.sql
-- Consolidated Migration: 030_schema_hardening_and_mobile.sql
-- Covers: 031, 033, 034, 037, 039, 040, 045, 046, 047, 048
-- Purpose: Unified table schema changes for Mobile Ops, Blog Feedback, and System Auditing.

-- 1. Attendance & Visit Logs (Mobile Ops)
CREATE TABLE IF NOT EXISTS public.attendance_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    clock_in_time TIMESTAMPTZ NOT NULL DEFAULT now(),
    clock_out_time TIMESTAMPTZ,
    latitude FLOAT,
    longitude FLOAT,
    location_name TEXT,
    status TEXT NOT NULL CHECK (status IN ('PRESENT', 'AWAY', 'OFF_WORK', 'MOCK_PRESENT')), 
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_attendance_user_time ON public.attendance_logs(user_id, clock_in_time DESC);

DO $$ BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'visit_logs' AND column_name = 'visit_type') THEN
        ALTER TABLE public.visit_logs ADD COLUMN visit_type TEXT;
    END IF;
END $$;

-- 2. Blog Posts Enhancements
ALTER TABLE public.blog_posts 
ADD COLUMN IF NOT EXISTS review_notes TEXT,
ADD COLUMN IF NOT EXISTS generation_metadata JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS ai_score INTEGER DEFAULT 100,
ADD COLUMN IF NOT EXISTS lead_id UUID;

CREATE INDEX IF NOT EXISTS idx_blog_posts_metadata ON blog_posts USING GIN (generation_metadata);

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name = 'fk_blog_posts_lead') THEN
        ALTER TABLE blog_posts ADD CONSTRAINT fk_blog_posts_lead FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE SET NULL;
    END IF;
END $$;

-- 3. Leads Enhancements
ALTER TABLE public.leads ADD COLUMN IF NOT EXISTS pitch_content TEXT;

-- 4. Profiles Enhancements
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS permission_overrides JSONB DEFAULT '{}'::jsonb;

-- 5. Audit & Logs Hardening
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'archon_logs' AND COLUMN_NAME = 'user_id') THEN
        ALTER TABLE archon_logs ADD COLUMN user_id UUID;
        CREATE INDEX IF NOT EXISTS idx_archon_logs_user_id ON archon_logs(user_id);
    END IF;
END $$;

ALTER TABLE public.archon_document_versions 
DROP CONSTRAINT IF EXISTS chk_project_or_task,
DROP CONSTRAINT IF EXISTS chk_version_identity,
ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'approved';

ALTER TABLE public.archon_document_versions
ADD CONSTRAINT chk_version_identity 
CHECK (
    (project_id IS NOT NULL) OR (task_id IS NOT NULL) OR (document_id IS NOT NULL) OR
    (field_name IN ('sales_pitch', 'web_research', 'knowledge_file', 'system_prompt', 'system_setting'))
);

ALTER TABLE public.archon_ethics_events 
ADD COLUMN IF NOT EXISTS resolved BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS resolution_notes TEXT;

-- Register Migration
INSERT INTO schema_migrations (version) VALUES ('030_schema_hardening_and_mobile') ON CONFLICT (version) DO NOTHING;


-- Source: 031_rbac_and_policies_refinement.sql
-- Consolidated Migration: 031_rbac_and_policies_refinement.sql
-- Covers: 032, 035, 036, (Policies from 031, 034)
-- Purpose: Unified RBAC flags and RLS policies for settings, prompts, and tokens.

-- 1. RBAC Flags
ALTER TABLE public.archon_prompts ADD COLUMN IF NOT EXISTS is_system_protected BOOLEAN DEFAULT false;
ALTER TABLE public.archon_settings ADD COLUMN IF NOT EXISTS is_system_protected BOOLEAN DEFAULT false;

UPDATE public.archon_prompts SET is_system_protected = false;
UPDATE public.archon_settings SET is_system_protected = true 
WHERE key IN ('SUPABASE_URL', 'SUPABASE_SERVICE_KEY', 'GEMINI_API_KEY', 'GOOGLE_API_KEY', 'ANTHROPIC_API_KEY', 'OPENAI_API_KEY');

-- 2. RLS Enablement
ALTER TABLE public.attendance_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.archon_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.archon_prompts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.blog_posts ENABLE ROW LEVEL SECURITY;

-- 3. Unified Policies
-- Attendance
DROP POLICY IF EXISTS "Users can view own attendance" ON public.attendance_logs;
CREATE POLICY "Users can view own attendance" ON public.attendance_logs FOR SELECT USING (auth.uid() = user_id);
DROP POLICY IF EXISTS "Users can insert own attendance" ON public.attendance_logs;
CREATE POLICY "Users can insert own attendance" ON public.attendance_logs FOR INSERT WITH CHECK (auth.uid() = user_id);
DROP POLICY IF EXISTS "Users can update own attendance" ON public.attendance_logs;
CREATE POLICY "Users can update own attendance" ON public.attendance_logs FOR UPDATE USING (auth.uid() = user_id);

-- Tokens
DROP POLICY IF EXISTS "Managers can view all token usage" ON public.token_usage;
CREATE POLICY "Managers can view all token usage" ON public.token_usage FOR SELECT USING (
    EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid()::text AND role = 'manager')
);

-- Prompts
DROP POLICY IF EXISTS "Admins can update all prompts" ON public.archon_prompts;
CREATE POLICY "Admins can update all prompts" ON public.archon_prompts FOR UPDATE USING (
    (SELECT role FROM public.profiles WHERE id = auth.uid()::text) IN ('system_admin', 'admin')
);
DROP POLICY IF EXISTS "Managers can update business prompts" ON public.archon_prompts;
CREATE POLICY "Managers can update business prompts" ON public.archon_prompts FOR UPDATE USING (
    (SELECT role FROM public.profiles WHERE id = auth.uid()::text) = 'manager' AND is_system_protected = false
);

-- Settings
DROP POLICY IF EXISTS "Admin can update everything" ON public.archon_settings;
CREATE POLICY "Admin can update everything" ON public.archon_settings FOR UPDATE USING (
    (SELECT role FROM public.profiles WHERE id = auth.uid()::text) IN ('system_admin', 'admin')
);
DROP POLICY IF EXISTS "Manager can update non-protected settings" ON public.archon_settings;
CREATE POLICY "Manager can update non-protected settings" ON public.archon_settings FOR UPDATE USING (
    (SELECT role FROM public.profiles WHERE id = auth.uid()::text) = 'manager' AND is_system_protected = false
);

-- Blog Metadata
DROP POLICY IF EXISTS "Marketing and Admins can update blog metadata" ON public.blog_posts;
CREATE POLICY "Marketing and Admins can update blog metadata" ON public.blog_posts FOR UPDATE USING (
    (SELECT role FROM public.profiles WHERE id = auth.uid()::text) IN ('marketing', 'manager', 'admin', 'system_admin')
);

-- Register Migration
INSERT INTO schema_migrations (version) VALUES ('031_rbac_and_policies_refinement') ON CONFLICT (version) DO NOTHING;


-- Source: 032_system_settings_and_config.sql
-- Consolidated Migration: 032_system_settings_and_config.sql
-- Covers: 030, 038, 041, 043, 044
-- Purpose: Unified system configuration, scoring weights, and LLM/RAG defaults.

-- 1. System Logistics
INSERT INTO public.archon_settings (key, value, category, description) VALUES 
('system.log_level', 'INFO', 'diagnostics', '控制 API 存取日誌的詳細程度。'),
('DEFAULT_LLM_PROVIDER', 'google', 'llm', 'Default LLM Provider (openai, google, anthropic)')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;

-- 2. Lead Scoring Weights
INSERT INTO public.archon_settings (key, value, category, description) VALUES 
('SCORING_VITAL_CONTACT', '20', 'lead_scoring', '成功提取到有效的聯繫電子郵件時增加的權重分值。'),
('SCORING_NEWS_FUNDING', '30', 'lead_scoring', '檢測到公司近期有融資新聞時增加的權重分值。'),
('SCORING_HAS_JOB_URL', '15', 'lead_scoring', '線索包含原始職位連結時增加的權重分值。'),
('SCORING_TECH_MATCH', '10', 'lead_scoring', '技術棧與產品高度匹配時增加的權重分值。')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;

-- 3. Crawler RBAC & Config
INSERT INTO public.archon_settings (key, value, category, description) VALUES 
('CRAWL_MAX_DEPTH_SALES', '2', 'crawler_rbac', '業務角色最大爬取深度。'),
('CRAWL_MAX_DEPTH_MARKETING', '5', 'crawler_rbac', '行銷角色最大爬取深度。'),
('CRAWL_MAX_DEPTH_MANAGER', '10', 'crawler_rbac', '經理角色最大爬取深度。'),
('CRAWL_MAX_DEPTH_ADMIN', '20', 'crawler_rbac', '管理員角色最大爬取深度。'),
('CRAWL_ALLOWED_DOMAINS_RESTRICTED', '104.com.tw,github.com,google.com', 'crawler_rbac', '非管理員角色允許存取的網域清單。'),
('CRAWLER_104_SEARCH_API', 'https://www.104.com.tw/jobs/search/api/jobs', 'crawler_config', '104 職缺搜尋 API 網址。')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;

-- 4. RAG & LLM Strategy
INSERT INTO public.archon_settings (key, value, category, description) VALUES 
('LLM_PROVIDER', 'google', 'rag_strategy', 'Active LLM Provider for RAG'),
('EMBEDDING_PROVIDER', 'google', 'rag_strategy', 'Primary Embedding Provider'),
('EMBEDDING_MODEL', 'gemini-embedding-001', 'rag_strategy', 'Embedding Model Name'),
('MODEL_CHOICE', 'gemini-1.5-flash', 'rag_strategy', 'Selected Chat Model'),
('DEFAULT_ALICE_PROJECT_TITLE', 'Field Ops', 'persona_alice', 'Alice 語音日誌自動轉工單的預設關聯專案名稱。')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;

-- Register Migration
INSERT INTO schema_migrations (version) VALUES ('032_system_settings_and_config') ON CONFLICT (version) DO NOTHING;


-- Source: 033_seed_nexus_data.sql
-- Consolidated Migration: 033_seed_nexus_data.sql
-- Covers: 042
-- Purpose: Seed ManagerNexus defaults and AI budget limits.

INSERT INTO public.archon_settings (key, value, category, description, is_system_protected) VALUES 
('marketing_scoring', '{
    "weights": [
        {"key": "VITAL_CONTACT", "label": "Contact Info", "weight": 20},
        {"key": "FUNDING_NEWS", "label": "Funding News", "weight": 30},
        {"key": "JOB_URL", "label": "Hiring Signal", "weight": 15},
        {"key": "TECH_STACK", "label": "Tech Stack Match", "weight": 35}
    ],
    "version": "v1.0.0",
    "updated_by": "System"
}', 'marketing_scoring', 'Marketing Lead Scoring Configuration', false),
('monthly_budget_limit', '100000', 'finance', 'Monthly AI Token Budget (USD)', true)
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;

-- Register Migration
INSERT INTO schema_migrations (version) VALUES ('033_seed_nexus_data') ON CONFLICT (version) DO NOTHING;


-- Source: 034_add_lost_reason_to_leads.sql
-- Migration: 034_add_lost_reason_to_leads.sql
-- Description: Adds columns to capture failure reasons for expertise harvesting (EXP-01)
-- Date: 2026-02-16

-- 1. Add columns to leads table
ALTER TABLE public.leads 
ADD COLUMN IF NOT EXISTS lost_reason TEXT,
ADD COLUMN IF NOT EXISTS lost_competitor TEXT;

-- 2. Add comments for clarity
COMMENT ON COLUMN public.leads.lost_reason IS 'Reason why the lead was lost or rejected.';
COMMENT ON COLUMN public.leads.lost_competitor IS 'Competitor the lead chose instead of our solution, if known.';

-- 3. Register Migration
INSERT INTO public.schema_migrations (version) VALUES ('034_add_lost_reason_to_leads') ON CONFLICT (version) DO NOTHING;


-- Source: 035_create_crawler_targets_table.sql
-- Migration: 035_create_crawler_targets_table.sql
-- Description: Physically separate Crawler URIs from LLM API Keys to prevent exposure in 3737 UI.
-- RLS: Manager can View, Admin can Manage.

-- 1. Create specialized table for Crawler Targets
CREATE TABLE IF NOT EXISTS public.archon_crawler_targets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    target_url TEXT NOT NULL UNIQUE,
    max_depth INTEGER DEFAULT 5,
    is_active BOOLEAN DEFAULT true,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 2. Enable RLS
ALTER TABLE public.archon_crawler_targets ENABLE ROW LEVEL SECURITY;

-- 3. Define Policies
-- SELECT: Admins and Managers
DROP POLICY IF EXISTS "Managers and Admins can view crawler targets" ON public.archon_crawler_targets;
CREATE POLICY "Managers and Admins can view crawler targets" ON public.archon_crawler_targets 
FOR SELECT USING (
    (SELECT role FROM public.profiles WHERE id = auth.uid()::text) IN ('admin', 'system_admin', 'manager')
);

-- ALL OPS: Admins only (David)
DROP POLICY IF EXISTS "Only Admins can manage crawler targets" ON public.archon_crawler_targets;
CREATE POLICY "Only Admins can manage crawler targets" ON public.archon_crawler_targets 
FOR ALL USING (
    (SELECT role FROM public.profiles WHERE id = auth.uid()::text) IN ('admin', 'system_admin')
);

-- 4. Seed initial data (Moving from settings)
INSERT INTO public.archon_crawler_targets (target_url, max_depth, description)
VALUES 
('https://www.104.com.tw', 5, 'Main recruitment target for Alice'),
('https://github.com', 3, 'Technical scouting target')
ON CONFLICT (target_url) DO NOTHING;

-- 5. Targeted Isolation: Hide only URI-based endpoints from 3737 API lists
-- Technical parameters like CRAWL_BATCH_SIZE will remain visible in 3737.
UPDATE public.archon_settings 
SET category = 'crawler_ops' 
WHERE key IN ('CRAWLER_104_SEARCH_API', 'CRAWLER_104_DETAIL_API');

-- 6. Register migration
INSERT INTO public.schema_migrations (version) VALUES ('035_create_crawler_targets_table') ON CONFLICT (version) DO NOTHING;


