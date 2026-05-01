-- RAG Strategy & Code Extraction Default Settings
-- Fixes cases where critical parameters are 0 or empty or missing

INSERT INTO archon_settings (key, value, is_encrypted, category, description, updated_at)
VALUES 
-- RAG Strategy
('CRAWL_MAX_CONCURRENT', '5', false, 'rag_strategy', 'Maximum concurrent crawl operations', NOW()),
('CRAWL_BATCH_SIZE', '10', false, 'rag_strategy', 'Number of URLs to crawl in one batch', NOW()),
('CRAWL_PAGE_TIMEOUT', '30000', false, 'rag_strategy', 'Timeout per page in milliseconds', NOW()),
('EMBEDDING_BATCH_SIZE', '100', false, 'rag_strategy', 'Number of chunks to embed in one batch', NOW()),
('DOCUMENT_STORAGE_BATCH_SIZE', '50', false, 'rag_strategy', 'Number of documents to store in one batch', NOW()),
('MEMORY_THRESHOLD_PERCENT', '85', false, 'rag_strategy', 'Memory usage threshold for flow control', NOW()),
('MODEL_CHOICE', 'gemini-3.1-flash-lite-preview', false, 'rag_strategy', 'Primary AI model for RAG operations', NOW()),
('USE_CONTEXTUAL_EMBEDDINGS', 'false', false, 'rag_strategy', 'Whether to use contextual embedding enhancement', NOW()),
('CONTEXTUAL_EMBEDDINGS_MAX_WORKERS', '3', false, 'rag_strategy', 'Max workers for contextual embedding', NOW()),
('USE_HYBRID_SEARCH', 'true', false, 'rag_strategy', 'Whether to combine vector and keyword search', NOW()),
('USE_AGENTIC_RAG', 'true', false, 'rag_strategy', 'Whether to use AI agents for query refinement', NOW()),
('USE_RERANKING', 'true', false, 'rag_strategy', 'Enable reranking of search results', NOW()),
('LLM_PROVIDER', 'google', false, 'rag_strategy', 'AI Provider for RAG', NOW()),
('EMBEDDING_PROVIDER', 'google', false, 'rag_strategy', 'Embedding Provider', NOW()),
('EMBEDDING_MODEL', 'gemini-embedding-001', false, 'rag_strategy', 'Embedding model name', NOW()),
('CRAWL_WAIT_STRATEGY', 'domcontentloaded', false, 'rag_strategy', 'Crawler wait strategy', NOW()),
('DELETE_BATCH_SIZE', '100', false, 'rag_strategy', 'Batch size for deletions', NOW()),
('ENABLE_PARALLEL_BATCHES', 'true', false, 'rag_strategy', 'Enable parallel batch processing', NOW()),
('DISPATCHER_CHECK_INTERVAL', '30', false, 'rag_strategy', 'Interval for task dispatcher check', NOW()),
('CODE_EXTRACTION_BATCH_SIZE', '50', false, 'rag_strategy', 'Batch size for code extraction', NOW()),
('CODE_SUMMARY_MAX_WORKERS', '3', false, 'rag_strategy', 'Max workers for code summarization', NOW()),
('MARKETING_MODEL', 'gemini-3.1-flash-lite-preview', false, 'rag_strategy', 'Model used for Alice and Bob marketing tasks', NOW()),

-- Code Extraction Settings
('MIN_CODE_BLOCK_LENGTH', '250', false, 'code_extraction', 'Minimum characters for a valid code block', NOW()),
('MAX_CODE_BLOCK_LENGTH', '5000', false, 'code_extraction', 'Maximum characters for a code block', NOW()),
('ENABLE_COMPLETE_BLOCK_DETECTION', 'true', false, 'code_extraction', 'Detect complete logical code blocks', NOW()),
('ENABLE_LANGUAGE_SPECIFIC_PATTERNS', 'true', false, 'code_extraction', 'Use language-specific extraction rules', NOW()),
('ENABLE_PROSE_FILTERING', 'true', false, 'code_extraction', 'Filter out prose from code files', NOW()),
('MAX_PROSE_RATIO', '0.15', false, 'code_extraction', 'Maximum allowed prose-to-code ratio', NOW()),
('MIN_CODE_INDICATORS', '3', false, 'code_extraction', 'Required indicators to identify code', NOW()),
('ENABLE_DIAGRAM_FILTERING', 'true', false, 'code_extraction', 'Filter out diagram-like text', NOW()),
('ENABLE_CONTEXTUAL_LENGTH', 'true', false, 'code_extraction', 'Adjust block length based on context', NOW()),
('CODE_EXTRACTION_MAX_WORKERS', '3', false, 'code_extraction', 'Workers for extraction process', NOW()),
('CONTEXT_WINDOW_SIZE', '1000', false, 'code_extraction', 'Context window for extraction', NOW()),
('ENABLE_CODE_SUMMARIES', 'true', false, 'code_extraction', 'Generate AI summaries for code blocks', NOW())

ON CONFLICT (key) DO UPDATE SET 
    value = EXCLUDED.value,
    description = EXCLUDED.description,
    updated_at = NOW();
