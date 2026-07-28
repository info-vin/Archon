# python/src/server/services/settings_service.py

from typing import Any, TypedDict

from src.server.repositories.base_repository import BaseRepository

from ..config.logfire_config import get_logger
from ..utils import get_supabase_client


class DatabaseStatisticsDict(TypedDict):
    projects: int
    tasks: int
    crawled_pages: int
    settings: int

logger = get_logger(__name__)


class SettingsService(BaseRepository):
    """Service for handling business logic related to application settings and statistics."""

    def __init__(self, supabase_client: Any = None) -> None:
        """Initialize with optional supabase client."""
        client = supabase_client or get_supabase_client()
        super().__init__(client)

    def get_database_statistics(self) -> tuple[bool, DatabaseStatisticsDict | str]:
        """
        Retrieves record counts for various tables in the database.

        Returns:
            A tuple containing a success boolean and either a dictionary of table counts or an error message.
        """
        tables_info: DatabaseStatisticsDict = {
            "projects": 0,
            "tasks": 0,
            "crawled_pages": 0,
            "settings": 0
        }

        # Get projects count
        def _get_projects():
            return self.supabase_client.table("archon_projects").select("id", count="exact").execute()

        success, result = self.execute_query(
            query_func=_get_projects, error_context="Error getting projects count", require_data=False
        )
        if not success:
            return False, result["error"]
        tables_info["projects"] = result.get("count", 0) or 0

        # Get tasks count
        def _get_tasks():
            return self.supabase_client.table("archon_tasks").select("id", count="exact").execute()

        success, result = self.execute_query(
            query_func=_get_tasks, error_context="Error getting tasks count", require_data=False
        )
        if not success:
            return False, result["error"]
        tables_info["tasks"] = result.get("count", 0) or 0

        # Get crawled pages count
        def _get_pages():
            return self.supabase_client.table("archon_crawled_pages").select("id", count="exact").execute()

        success, result = self.execute_query(
            query_func=_get_pages, error_context="Error getting pages count", require_data=False
        )
        if not success:
            return False, result["error"]
        tables_info["crawled_pages"] = result.get("count", 0) or 0

        # Get settings count
        def _get_settings():
            return self.supabase_client.table("archon_settings").select("id", count="exact").execute()

        success, result = self.execute_query(
            query_func=_get_settings, error_context="Error getting settings count", require_data=False
        )
        if not success:
            return False, result["error"]
        tables_info["settings"] = result.get("count", 0) or 0

        return True, tables_info

    def get_setting(self, key: str, default: str | None = None) -> str | None:
        """Retrieve a specific setting value."""

        def _query():
            res = self.supabase_client.table("archon_settings").select("value").eq("key", key).execute()
            res.data = res.data[0] if res.data else {}
            return res

        success, result = self.execute_query(
            query_func=_query, error_context=f"Error fetching setting {key}", require_data=True
        )
        if success and result.get("data"):
            return str(result["data"].get("value", default))
        return default

    def get_all_settings(self) -> dict[str, str]:
        """Retrieve all settings as a dictionary."""

        def _query():
            return self.supabase_client.table("archon_settings").select("key, value").execute()

        success, result = self.execute_query(
            query_func=_query, error_context="Error fetching all settings", require_data=False
        )
        if success and result["data"]:
            return {item["key"]: item["value"] for item in result["data"]}
        return {}

    def set_setting(self, key: str, value: str) -> bool:
        """Upsert a specific setting value."""

        def _query():
            return self.supabase_client.table("archon_settings").upsert(
                {"key": key, "value": value}, on_conflict="key"
            ).execute()

        success, result = self.execute_query(
            query_func=_query, error_context=f"Error setting {key}", require_data=False
        )
        return success
