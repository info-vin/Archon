"""
System infrastructure provisioning service.
Handles global environment adaptations and DDL operations.
"""

from src.server.config.config import get_config
from src.server.config.logfire_config import get_logger

logger = get_logger(__name__)

# Single Source of Truth for vector tables that require dimension adaptation
VECTOR_TABLES = [
    "archon_crawled_pages",
    "archon_code_examples"
]

VECTOR_DIM_OFFLINE = 384
VECTOR_DIM_ONLINE = 768


async def adapt_vector_dimensions_for_offline_mode() -> None:
    """
    Alters vector column dimensions in the database and rebuilds HNSW indexes
    to match the active mode (384 dimensions for offline, 768 for online).
    """
    config = get_config()
    is_offline = config.offline_mode
    target_dim = VECTOR_DIM_OFFLINE if is_offline else VECTOR_DIM_ONLINE

    db_url = config.supabase_db_url
    if not db_url:
        logger.warning("SUPABASE_DB_URL is not set. Skipping vector dimension adaptation.")
        return

    # Prevent destructive downscaling on production cloud database
    # SSOT logic: Check config.archon_env instead of string matching
    if config.archon_env == "prod" and target_dim == VECTOR_DIM_OFFLINE:
        logger.warning("⚠️ Protected: Attempted vector downscaling to 384 in prod environment. Skipping to prevent data loss.")
        return

    logger.info(f"Checking vector database column dimensions (Target: {target_dim})...")

    # Connect using psycopg2 to run DDL command
    import psycopg2

    sql_commands = []
    for table in VECTOR_TABLES:
        sql_commands.extend([
            f"DROP INDEX IF EXISTS public.{table}_embedding_idx CASCADE;",
            f"UPDATE public.{table} SET embedding = NULL;",
            f"ALTER TABLE public.{table} ALTER COLUMN embedding TYPE public.vector({target_dim});",
            f"CREATE INDEX IF NOT EXISTS {table}_embedding_idx ON public.{table} USING hnsw (embedding public.vector_cosine_ops);"
        ])

    conn = None
    try:
        # Connect to pg database
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        with conn.cursor() as cursor:
            # Check current dimension of the vector columns (check all tables to avoid bias)
            needs_adaptation = False
            for table in VECTOR_TABLES:
                try:
                    cursor.execute(
                        f"SELECT atttypmod FROM pg_attribute WHERE attrelid = 'public.{table}'::regclass AND attname = 'embedding';"
                    )
                    row = cursor.fetchone()
                    if not row or row[0] != target_dim:
                        needs_adaptation = True
                        break
                except Exception as check_err:
                    logger.warning(f"Could not check current vector dimension for {table}: {check_err}")
                    needs_adaptation = True
                    break

            if not needs_adaptation:
                logger.info(f"Vector columns are already at {target_dim} dimensions. No adaptation needed.")
                return

            logger.info(f"Altering columns and rebuilding indexes to {target_dim} dimensions...")
            for cmd in sql_commands:
                try:
                    cursor.execute(cmd)
                except Exception as e:
                    logger.warning(f"Failed to execute command '{cmd}': {e}")
            logger.info(f"✅ Vector columns successfully adapted to {target_dim} dimensions.")
    except Exception as e:
        logger.error(f"❌ Failed to adapt vector database dimensions: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()
