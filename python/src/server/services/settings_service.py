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
        query_projects = self.supabase_client.table("archon_projects").select("id", count="exact") # 合法
        success, result = self.execute_query(
            query_func=query_projects, error_context="Error getting projects count", require_data=False
        )
        if not success:
            return False, result["error"]
        tables_info["projects"] = result.get("count", 0) or 0

        # Get tasks count
        query_tasks = self.supabase_client.table("archon_tasks").select("id", count="exact") # 合法
        success, result = self.execute_query(
            query_func=query_tasks, error_context="Error getting tasks count", require_data=False
        )
        if not success:
            return False, result["error"]
        tables_info["tasks"] = result.get("count", 0) or 0

        # Get crawled pages count
        query_pages = self.supabase_client.table("archon_crawled_pages").select("id", count="exact") # 合法
        success, result = self.execute_query(
            query_func=query_pages, error_context="Error getting pages count", require_data=False
        )
        if not success:
            return False, result["error"]
        tables_info["crawled_pages"] = result.get("count", 0) or 0

        # Get settings count
        query_settings = self.supabase_client.table("archon_settings").select("id", count="exact") # 合法
        success, result = self.execute_query(
            query_func=query_settings, error_context="Error getting settings count", require_data=False
        )
        if not success:
            return False, result["error"]
        tables_info["settings"] = result.get("count", 0) or 0

        return True, tables_info

    def get_setting(self, key: str, default: str | None = None) -> str | None:
        """Retrieve a specific setting value."""

        query = self.supabase_client.table("archon_settings").select("value").eq("key", key) # 合法
        success, result = self.execute_query(
            query_func=query, error_context=f"Error fetching setting {key}", require_data=True
        )
        if success:
            data = result.get("data", [])
            setting_data = data[0] if isinstance(data, list) and data else (data if data else {})
            result["data"] = setting_data
        if success and result.get("data"):
            return str(result["data"].get("value", default))
        return default

    def get_all_settings(self) -> dict[str, str]:
        """Retrieve all settings as a dictionary."""

        query = self.supabase_client.table("archon_settings").select("key, value") # 合法
        success, result = self.execute_query(
            query_func=query, error_context="Error fetching all settings", require_data=False
        )
        if success and result["data"]:
            return {item["key"]: item["value"] for item in result["data"]}
        return {}

    def set_setting(self, key: str, value: str) -> bool:
        """Upsert a specific setting value."""

        query = self.supabase_client.table("archon_settings").upsert( # 合法
            {"key": key, "value": value}, on_conflict="key"
        )
        success, result = self.execute_query(
            query_func=query, error_context=f"Error setting {key}", require_data=False
        )
        return success

    async def upsert_setting(self, payload: dict[str, Any]) -> bool:
        query = self.supabase_client.table("archon_settings").upsert(payload, on_conflict="key") # 合法
        success, res = self.execute_query(query, "Error upserting setting", require_data=False)
        return success
