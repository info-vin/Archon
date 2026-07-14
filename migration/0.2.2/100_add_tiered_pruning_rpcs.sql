-- Phase 5.9.3: Tiered Database Pruning RPCs
-- Provides secure endpoints for the Python backend to check DB size and execute complex cross-table deletions.

-- 1. Get current database size in MB
CREATE OR REPLACE FUNCTION get_db_size_mb()
RETURNS float
LANGUAGE sql
SECURITY DEFINER
AS $$
  SELECT (pg_database_size(current_database()) / 1048576.0)::float;
$$;

-- 2. Prune orphan vectors (returns number of deleted rows)
-- Cleans up chunks that have lost their parent source or have a NULL source_id
CREATE OR REPLACE FUNCTION prune_orphan_vectors()
RETURNS int
LANGUAGE sql
SECURITY DEFINER
AS $$
  WITH deleted AS (
    DELETE FROM archon_crawled_pages 
    WHERE source_id IS NULL OR source_id NOT IN (SELECT source_id FROM archon_sources)
    RETURNING id
  )
  SELECT count(*)::int FROM deleted;
$$;
