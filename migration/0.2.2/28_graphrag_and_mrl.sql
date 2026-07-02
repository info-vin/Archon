-- Name: hybrid_match_chunks (MRL Support); Type: FUNCTION; Schema: public; Owner: postgres
-- 
-- Phase 5.8.6 MRL & GraphRAG Implementation
-- Overwrites hybrid_match_chunks to support truncate_dim for Matryoshka Representation Learning

DROP FUNCTION IF EXISTS public.hybrid_match_chunks(public.vector, text, integer, float, jsonb, text);

CREATE OR REPLACE FUNCTION public.hybrid_match_chunks(
    query_embedding public.vector, 
    query_text text, 
    match_count integer DEFAULT 10, 
    similarity_threshold float DEFAULT 0.0,
    filter jsonb DEFAULT '{}'::jsonb, 
    source_filter text DEFAULT NULL::text,
    truncate_dim integer DEFAULT NULL
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
        -- Vector similarity search with MRL dynamic slicing
        SELECT 
            cp.id,
            cp.url,
            cp.chunk_number,
            cp.content,
            cp.metadata,
            cp.source_id,
            CASE 
                WHEN truncate_dim IS NOT NULL THEN
                    -- MRL slice calculation
                    1 - ((((cp.embedding::real[])[1:truncate_dim])::vector) <=> (((query_embedding::real[])[1:truncate_dim])::vector))
                ELSE
                    -- Standard calculation
                    1 - (cp.embedding <=> query_embedding)
            END AS vector_sim
        FROM archon_crawled_pages cp
        WHERE cp.metadata @> filter
            AND (source_filter IS NULL OR cp.source_id = source_filter)
            AND cp.embedding IS NOT NULL
            AND (
                CASE WHEN truncate_dim IS NOT NULL THEN
                    1 - ((((cp.embedding::real[])[1:truncate_dim])::vector) <=> (((query_embedding::real[])[1:truncate_dim])::vector))
                ELSE
                    1 - (cp.embedding <=> query_embedding)
                END
            ) >= similarity_threshold
        ORDER BY 
            CASE WHEN truncate_dim IS NOT NULL THEN
                (((cp.embedding::real[])[1:truncate_dim])::vector) <=> (((query_embedding::real[])[1:truncate_dim])::vector)
            ELSE
                cp.embedding <=> query_embedding
            END
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


-- ============================================================================
-- GraphRAG Pure Postgres Implementation
-- Creates dynamic schema and Recursive CTE function for 2-hop / n-hop traversal
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.knowledge_entities (
    id bigserial PRIMARY KEY,
    name text NOT NULL,
    type text,
    description text,
    metadata jsonb DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS public.knowledge_relationships (
    id bigserial PRIMARY KEY,
    source_entity_id bigint REFERENCES public.knowledge_entities(id) ON DELETE CASCADE,
    target_entity_id bigint REFERENCES public.knowledge_entities(id) ON DELETE CASCADE,
    relation_type text NOT NULL,
    weight float DEFAULT 1.0,
    metadata jsonb DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_krel_source ON public.knowledge_relationships(source_entity_id);
CREATE INDEX IF NOT EXISTS idx_krel_target ON public.knowledge_relationships(target_entity_id);

CREATE OR REPLACE FUNCTION public.graph_reasoning_n_hop(
    start_entity_name text,
    max_hops integer DEFAULT 2
) RETURNS TABLE(
    path text,
    hop_count integer,
    final_entity text
)
LANGUAGE sql
AS $$
    WITH RECURSIVE graph_cte AS (
        -- Base case: find the starting entity
        SELECT 
            e.id as current_id, 
            e.name as path, 
            0 as hop_count,
            e.name as current_name
        FROM knowledge_entities e
        WHERE e.name ILIKE start_entity_name

        UNION ALL

        -- Recursive step: join with relationships to find neighbors
        SELECT 
            r.target_entity_id as current_id,
            g.path || ' -> ' || e.name as path,
            g.hop_count + 1 as hop_count,
            e.name as current_name
        FROM graph_cte g
        JOIN knowledge_relationships r ON g.current_id = r.source_entity_id
        JOIN knowledge_entities e ON r.target_entity_id = e.id
        WHERE g.hop_count < max_hops
    )
    SELECT path, hop_count, current_name as final_entity
    FROM graph_cte
    ORDER BY hop_count ASC, path ASC;
$$;
