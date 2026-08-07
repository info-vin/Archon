"""
Database migration tracking and management service.
"""

import hashlib
from pathlib import Path
from typing import Any

import aiofiles
from supabase import Client

from ..config.logfire_config import get_logger
from ..config.version import ARCHON_VERSION
from .client_manager import get_supabase_client

logger = get_logger(__name__)


class MigrationRecord:
    """Represents a migration record from the database."""

    def __init__(self, data: dict[str, Any]) -> None:
        self.id = data.get("id")
        self.version = data.get("version")
        self.migration_name = data.get("migration_name") or data.get("version")
        self.applied_at = data.get("migrated_at") or data.get("applied_at")
        self.checksum = data.get("checksum")


class PendingMigration:
    """Represents a pending migration from the filesystem."""

    def __init__(self, version: str, name: str, sql_content: str, file_path: str) -> None:
        self.version = version
        self.name = name
        self.sql_content = sql_content
        self.file_path = file_path
        self.checksum = self._calculate_checksum(sql_content)

    def _calculate_checksum(self, content: str) -> str:
        """Calculate MD5 checksum of migration content."""
        return hashlib.md5(content.encode()).hexdigest()


class MigrationService:
    """Service for managing database migrations."""

    def __init__(self) -> None:
        self._supabase: Client | None = None
        self._table_name = "schema_migrations"  # Default standard
        # This robustly handles both Docker and local environments by first checking
        # for the fixed Docker path, then falling back to a path calculated
        # relative to this file's location, making it independent of the
        # current working directory.
        docker_migrations_path = Path("/app/migration")
        if docker_migrations_path.exists():
            self._migrations_dir = docker_migrations_path
        else:
            # For local execution, robustly find the project root relative to this file.
            # python/src/server/services -> python/src/server -> python/src -> python -> project_root
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            self._migrations_dir = project_root / "migration"

    def _get_supabase_client(self) -> Client:
        """Get or create Supabase client."""
        if not self._supabase:
            self._supabase = get_supabase_client()
        return self._supabase

    async def check_migrations_table_exists(self) -> bool:
        """
        Check if the migrations tracking table exists in the database.
        Checks for 'schema_migrations' (new standard) and 'archon_migrations' (legacy).

        Returns:
            True if table exists, False otherwise
        """
        supabase = self._get_supabase_client()

        # Direct Probe (Most reliable across all Supabase configs)
        try:
            # Try new standard first
            supabase.table("schema_migrations").select("version").limit(0).execute() # 合法
            self._table_name = "schema_migrations"
            return True
        except Exception:
            try:
                # Fallback to legacy
                supabase.table("archon_migrations").select("id").limit(0).execute() # 合法
                self._table_name = "archon_migrations"
                return True
            except Exception:
                return False

    async def get_applied_migrations(self) -> list[MigrationRecord]:
        """
        Get list of applied migrations from the database.

        Returns:
            List of MigrationRecord objects
        """
        try:
            # Check if table exists first
            if not await self.check_migrations_table_exists():
                logger.info("Migrations table does not exist, returning empty list")
                return []

            supabase = self._get_supabase_client()

            # Determine order column based on table name (Physical Hardening)
            order_col = "migrated_at" if self._table_name == "schema_migrations" else "applied_at"

            result = supabase.table(self._table_name).select("*").order(order_col, desc=True).execute() # 合法

            return [MigrationRecord(row) for row in result.data]
        except Exception as e:
            logger.error(f"Error fetching applied migrations: {e}")
            # Return empty list if we can't fetch migrations
            return []

    async def scan_migration_directory(self) -> list[PendingMigration]:
        """
        Scan the migration directory for all SQL files.

        Returns:
            List of PendingMigration objects
        """
        migrations: list[PendingMigration] = []

        if not self._migrations_dir.exists():
            logger.warning(f"Migration directory does not exist: {self._migrations_dir}")
            return migrations

        # Scan root migration directory for SQL files
        for sql_file in sorted(self._migrations_dir.glob("*.sql")):
            try:
                # Read SQL content
                async with aiofiles.open(sql_file, encoding="utf-8") as f:
                    sql_content = await f.read()

                # Extract migration name (filename without extension)
                migration_name = sql_file.stem

                # Create pending migration object
                migration = PendingMigration(
                    version="0.0.0",  # Standard root version
                    name=migration_name,
                    sql_content=sql_content,
                    file_path=str(sql_file.relative_to(self._migrations_dir.parent)),
                )
                migrations.append(migration)
            except Exception as e:
                logger.error(f"Error reading migration file {sql_file}: {e}")

        # Scan all version directories
        for version_dir in sorted(self._migrations_dir.iterdir()):
            if not version_dir.is_dir():
                continue

            version = version_dir.name

            # Physical Hardening: Only scan the current version directory or the '0.0.0' placeholder.
            # This prevents obsolete version folders (e.g., 0.1.0, 0.2.1) from cluttering the UI
            # with "pending" warnings when the system is already at 0.2.2+.
            if version != ARCHON_VERSION and version != "0.0.0":
                logger.debug(f"Skipping obsolete migration directory: {version}")
                continue

            # Scan all SQL files in version directory
            for sql_file in sorted(version_dir.glob("*.sql")):
                try:
                    # Read SQL content
                    async with aiofiles.open(sql_file, encoding="utf-8") as f:
                        sql_content = await f.read()

                    # Extract migration name
                    # Physical Alignment: Include version prefix if not in root to match DB records
                    if version != "0.0.0":
                        migration_name = f"{version}/{sql_file.stem}"
                    else:
                        migration_name = sql_file.stem

                    # Create pending migration object
                    migration = PendingMigration(
                        version=version,
                        name=migration_name,
                        sql_content=sql_content,
                        file_path=str(sql_file.relative_to(self._migrations_dir.parent)),
                    )
                    migrations.append(migration)
                except Exception as e:
                    logger.error(f"Error reading migration file {sql_file}: {e}")

        return migrations

    async def get_pending_migrations(self) -> list[PendingMigration]:
        """
        Get list of pending migrations by comparing filesystem with database.

        Returns:
            List of PendingMigration objects that haven't been applied
        """
        # Get all migrations from filesystem
        all_migrations = await self.scan_migration_directory()

        # Check if migrations table exists
        if not await self.check_migrations_table_exists():
            # Bootstrap case - all migrations are pending
            logger.info("Migrations table doesn't exist, all migrations are pending")
            return all_migrations

        # Get applied migrations from database
        applied_migrations = await self.get_applied_migrations()

        # Create set of applied migration identifiers
        # Support matching by migration_name (new) or combination
        applied_names = {m.migration_name for m in applied_migrations}

        # Filter out applied migrations
        pending = [m for m in all_migrations if m.name not in applied_names]

        return pending

    async def get_migration_status(self) -> dict[str, Any]:
        """
        Get comprehensive migration status.

        Returns:
            Dictionary with pending and applied migrations info
        """
        pending = await self.get_pending_migrations()
        applied = await self.get_applied_migrations()

        # Check if bootstrap is required
        bootstrap_required = not await self.check_migrations_table_exists()

        return {
            "pending_migrations": [
                {
                    "version": m.version,
                    "name": m.name,
                    "sql_content": m.sql_content,
                    "file_path": m.file_path,
                    "checksum": m.checksum,
                }
                for m in pending
            ],
            "applied_migrations": [
                {
                    "version": m.version,
                    "migration_name": m.migration_name,
                    "applied_at": m.applied_at,
                    "checksum": m.checksum,
                }
                for m in applied
            ],
            "has_pending": len(pending) > 0,
            "bootstrap_required": bootstrap_required,
            "current_version": ARCHON_VERSION,
            "pending_count": len(pending),
            "applied_count": len(applied),
        }

    async def adapt_vector_dimensions_for_offline_mode(self) -> None:
        """
        Alters vector column dimensions in the database and rebuilds HNSW indexes
        to match the active mode (384 dimensions for offline, 768 for online).
        """
        from ..config.config import get_config
        config = get_config()
        is_offline = config.offline_mode
        target_dim = 384 if is_offline else 768

        db_url = config.supabase_db_url
        if not db_url:
            logger.warning("SUPABASE_DB_URL is not set. Skipping vector dimension adaptation.")
            return

        # Prevent destructive downscaling on production cloud database (supabase.co)
        if "supabase.co" in db_url and target_dim == 384:
            logger.warning("⚠️ Protected: Attempted vector downscaling to 384 on cloud database. Skipping to prevent data loss.")
            return

        logger.info(f"Checking vector database column dimensions (Target: {target_dim})...")

        # Connect using psycopg2 to run DDL command
        import psycopg2

        sql_commands = [
            "DROP INDEX IF EXISTS public.archon_crawled_pages_embedding_idx CASCADE;",
            "UPDATE public.archon_crawled_pages SET embedding = NULL;",
            f"ALTER TABLE public.archon_crawled_pages ALTER COLUMN embedding TYPE public.vector({target_dim});",
            "CREATE INDEX IF NOT EXISTS archon_crawled_pages_embedding_idx ON public.archon_crawled_pages USING hnsw (embedding public.vector_cosine_ops);",

            "DROP INDEX IF EXISTS public.archon_code_examples_embedding_idx CASCADE;",
            "UPDATE public.archon_code_examples SET embedding = NULL;",
            f"ALTER TABLE public.archon_code_examples ALTER COLUMN embedding TYPE public.vector({target_dim});",
            "CREATE INDEX IF NOT EXISTS archon_code_examples_embedding_idx ON public.archon_code_examples USING hnsw (embedding public.vector_cosine_ops);"
        ]

        conn = None
        try:
            # Connect to pg database
            conn = psycopg2.connect(db_url)
            conn.autocommit = True
            with conn.cursor() as cursor:
                # Check current dimension of the vector columns
                try:
                    cursor.execute(
                        "SELECT atttypmod FROM pg_attribute WHERE attrelid = 'public.archon_crawled_pages'::regclass AND attname = 'embedding';"
                    )
                    row = cursor.fetchone()
                    if row and row[0] == target_dim:
                        logger.info(f"Vector columns are already at {target_dim} dimensions. No adaptation needed.")
                        return
                except Exception as check_err:
                    logger.warning(f"Could not check current vector dimension: {check_err}")

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


# Export singleton instance
migration_service = MigrationService()
