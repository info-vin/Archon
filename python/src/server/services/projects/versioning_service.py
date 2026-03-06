# python/src/server/services/projects/versioning_service.py

from typing import Any, cast

from server.repositories.base_repository import BaseRepository

from ...config.logfire_config import get_logger

logger = get_logger(__name__)

class VersioningService(BaseRepository):
    """Service class for document versioning operations"""

    def __init__(self, supabase_client=None):
        """Initialize with optional supabase client"""
        super().__init__(supabase_client)

    def create_version(
        self,
        project_id: str,
        field_name: str,
        content: dict[str, Any],
        change_summary: str | None = None,
        change_type: str = "update",
        document_id: str | None = None,
        created_by: str = "system",
    ) -> tuple[bool, dict[str, Any]]:
        """
        Creates a new version record for a project document field.
        """
        # 1. Get latest version number
        def _get_latest():
            return (
                self.supabase_client.table("archon_document_versions")
                .select("version_number")
                .eq("project_id", project_id)
                .eq("field_name", field_name)
                .order("version_number", desc=True)
                .limit(1)
                .execute()
            )

        success, res = self.execute_query(_get_latest, "Failed to fetch latest version")
        latest_version = 0
        if success and res.get("data"):
            latest_version = res["data"][0].get("version_number", 0)

        # 2. Insert new version
        new_version_data = {
            "project_id": project_id,
            "document_id": document_id,
            "field_name": field_name,
            "content": content,
            "version_number": latest_version + 1,
            "change_summary": change_summary,
            "change_type": change_type,
            "created_by": created_by,
        }

        def _insert():
            return self.supabase_client.table("archon_document_versions").insert(new_version_data).execute()

        return cast(tuple[bool, dict[str, Any]], self.execute_query(_insert, "Failed to create new version"))

    async def get_version_history(self, project_id: str) -> tuple[bool, dict[str, Any]]:
        """Retrieve the version history for a specific project."""
        def _query():
            return (
                self.supabase_client.table("archon_document_versions")
                .select("*")
                .eq("project_id", project_id)
                .order("created_at", desc=True)
                .execute()
            )
        return cast(tuple[bool, dict[str, Any]], self.execute_query(_query, "Failed to fetch version history"))

    async def get_all_versions(self) -> tuple[bool, dict[str, Any]]:
        """Retrieve all document versions across all projects."""
        def _query():
            return (
                self.supabase_client.table("archon_knowledge_items")
                .select("*")
                .order("created_at", desc=True)
                .limit(100)
                .execute()
            )
        return cast(tuple[bool, dict[str, Any]], self.execute_query(_query, "Failed to fetch all versions"))
