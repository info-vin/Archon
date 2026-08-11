"""
Database migration tracking and management service.
"""

import hashlib
from pathlib import Path
from typing import NotRequired, TypedDict

import aiofiles
from supabase import Client

from ..config.logfire_config import get_logger
from ..config.version import ARCHON_VERSION
from .client_manager import get_supabase_client


class MigrationRecordDTO(TypedDict):
    id: NotRequired[int]
    version: NotRequired[str]
    migration_name: NotRequired[str]
    migrated_at: NotRequired[str]
    applied_at: NotRequired[str]
    checksum: NotRequired[str]


class PendingMigrationInfoDTO(TypedDict):
    version: str
    name: str
    sql_content: str
    file_path: str
    checksum: str


class AppliedMigrationInfoDTO(TypedDict):
    version: str | None
    migration_name: str | None
    applied_at: str | None
    checksum: str | None


class MigrationStatusDTO(TypedDict):
    pending_migrations: list[PendingMigrationInfoDTO]
    applied_migrations: list[AppliedMigrationInfoDTO]
    bootstrap_required: bool
    has_pending: bool
    current_version: str
    pending_count: int
    applied_count: int

logger = get_logger(__name__)


class MigrationRecord:
    """Represents a migration record from the database."""

    def __init__(self, data: MigrationRecordDTO) -> None:
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
        from src.server.repositories.base_repository import BaseRepository
        repo = BaseRepository(supabase)
        success_new, res_new = repo.execute_query(
            supabase.table("schema_migrations").select("version").limit(0),
            "Check new standard",
            max_retries=0
        )
        if success_new:
            self._table_name = "schema_migrations"
            return True

        success_legacy, res_legacy = repo.execute_query(
            supabase.table("archon_migrations").select("id").limit(0),
            "Check legacy standard",
            max_retries=0
        )
        if success_legacy:
            self._table_name = "archon_migrations"
            return True

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

            from src.server.repositories.base_repository import BaseRepository
            repo = BaseRepository(supabase)
            success, result = repo.execute_query(
                supabase.table(self._table_name).select("*").order(order_col, desc=True),
                "Fetch applied migrations"
            )

            return [MigrationRecord(row) for row in result.get("data", [])] if success else []
        except Exception as e:
            logger.error(f"Error fetching applied migrations: {e}")
            # Return empty list if we can't fetch migrations
            return []

    async def scan_migration_directory(self) -> list[PendingMigration]:
        """Scan the migration directory for all SQL files."""
        migrations: list[PendingMigration] = []

        if not self._migrations_dir.exists():
            logger.warning(f"Migration directory does not exist: {self._migrations_dir}")
            return migrations

        async def _process_file(sql_file: Path, version: str) -> None:
            try:
                async with aiofiles.open(sql_file, encoding="utf-8") as f:
                    content = await f.read()
                name = sql_file.stem if version == "0.0.0" else f"{version}/{sql_file.stem}"
                migrations.append(PendingMigration(
                    version=version, name=name, sql_content=content,
                    file_path=str(sql_file.relative_to(self._migrations_dir.parent))
                ))
            except Exception as e:
                logger.error(f"Error reading {sql_file}: {e}")

        # Scan root
        for f in sorted(self._migrations_dir.glob("*.sql")):
            await _process_file(f, "0.0.0")

        # Scan versions (only current and root placeholder)
        for v_dir in sorted(self._migrations_dir.iterdir()):
            if v_dir.is_dir() and v_dir.name in (ARCHON_VERSION, "0.0.0"):
                for f in sorted(v_dir.glob("*.sql")):
                    await _process_file(f, v_dir.name)

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

    async def get_migration_status(self) -> MigrationStatusDTO:
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




# Export singleton instance
migration_service = MigrationService()
