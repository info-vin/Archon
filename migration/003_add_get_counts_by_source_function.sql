-- This function efficiently gets the chunk count and code example count for a given array of source_ids.
-- It is designed to be called from the backend service to avoid N+1 query problems when listing knowledge items.

CREATE OR REPLACE FUNCTION get_counts_by_source(source_ids_param uuid[])
RETURNS TABLE (source_id uuid, chunk_count bigint, code_example_count bigint)
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
            source_id,
            COUNT(*) as count
        FROM
            public.archon_crawled_pages
        WHERE
            source_id = ANY(source_ids_param)
        GROUP BY
            source_id
    ) AS cp_counts ON s.source_id = cp_counts.source_id
    LEFT JOIN (
        SELECT
            source_id,
            COUNT(*) as count
        FROM
            public.archon_code_examples
        WHERE
            source_id = ANY(source_ids_param)
        GROUP BY
            source_id
    ) AS ce_counts ON s.source_id = ce_counts.source_id
    WHERE
        s.source_id = ANY(source_ids_param);
END;
$$;

-- Register this migration
INSERT INTO schema_migrations (version) VALUES ('003_add_get_counts_by_source_function') ON CONFLICT (version) DO NOTHING;
