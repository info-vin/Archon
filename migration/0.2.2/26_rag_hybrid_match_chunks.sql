-- Name: hybrid_match_chunks(public.vector, text, integer, float, jsonb, text); Type: FUNCTION; Schema: public; Owner: postgres
-- 
-- Phase 5.8.0 Semantic Infiltration
-- Provides a hybrid RAG search function combining vector and full-text search with dynamic similarity threshold filtering.

CREATE OR REPLACE FUNCTION public.hybrid_match_chunks(
    query_embedding public.vector, 
    query_text text, 
    match_count integer DEFAULT 10, 
    similarity_threshold float DEFAULT 0.0,
    filter jsonb DEFAULT '{}'::jsonb, 
    source_filter text DEFAULT NULL::text
) RETURNS TABLE(
    id bigint, 
    url character varying, 
    chunk_number integer, 
    content text, 
    metadata jsonb, 
    source_id text, 
    similarity double precision, 
    match_type text
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH vector_results AS (
        -- Vector similarity search with noise filtering (threshold)
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
            AND 1 - (cp.embedding <=> query_embedding) >= similarity_threshold
        ORDER BY cp.embedding <=> query_embedding
        LIMIT match_count
    ),
    text_results AS (
        -- Full-text search (FTS) with ranking
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
        LIMIT match_count
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
    SELECT c.id, c.url, c.chunk_number, c.content, c.metadata, c.source_id, c.similarity, c.match_type 
    FROM combined_results c
    ORDER BY c.similarity DESC
    LIMIT match_count;
END;
$$;

ALTER FUNCTION public.hybrid_match_chunks(query_embedding public.vector, query_text text, match_count integer, similarity_threshold float, filter jsonb, source_filter text) OWNER TO postgres;

COMMENT ON FUNCTION public.hybrid_match_chunks(query_embedding public.vector, query_text text, match_count integer, similarity_threshold float, filter jsonb, source_filter text) IS 'Performs hybrid search for Archon RAG Deck-builder with dynamic noise filtering threshold';
