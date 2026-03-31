# python/src/server/services/projects/versioning_service.py

from typing import Any, cast

from src.server.repositories.base_repository import BaseRepository

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

        return self.execute_query(_insert, "Failed to create new version")

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

        return self.execute_query(_query, "Failed to fetch version history")

    def list_all_versions(self) -> tuple[bool, dict[str, Any]]:
        """List all document versions globally."""

        def _query():
            return (
                self.supabase_client.table("archon_document_versions")
                .select("*")
                .order("created_at", desc=True)
                .limit(100)
                .execute()
            )

        success, res = self.execute_query(_query, "Failed to fetch all versions", require_data=False)
        if success:
            return True, {"versions": res.get("data", []), "total_count": len(res.get("data", []))}
        return False, res

    def list_versions(self, project_id: str, field_name: str | None = None) -> tuple[bool, dict[str, Any]]:
        """List version history for a project's JSONB fields."""

        def _query():
            query = self.supabase_client.table("archon_document_versions").select("*").eq("project_id", project_id)
            if field_name:
                query = query.eq("field_name", field_name)
            return query.order("version_number", desc=True).execute()

        success, res = self.execute_query(
            _query, f"Failed to fetch versions for project {project_id}", require_data=False
        )
        if success:
            return True, {"versions": res.get("data", []), "total_count": len(res.get("data", []))}
        return False, res

    def get_version_content(self, project_id: str, field_name: str, version_number: int) -> tuple[bool, dict[str, Any]]:
        """Get a specific version's content."""

        def _query():
            return (
                self.supabase_client.table("archon_document_versions")
                .select("content")
                .eq("project_id", project_id)
                .eq("field_name", field_name)
                .eq("version_number", version_number)
                .single()
                .execute()
            )

        success, res = self.execute_query(_query, "Failed to fetch version content", require_data=True)
        if success:
            return True, cast(dict[str, Any], res.get("data"))
        return False, res

    def restore_version(
        self, project_id: str, field_name: str, version_number: int, restored_by: str = "system"
    ) -> tuple[bool, dict[str, Any]]:
        """Restore a project's JSONB field to a specific version."""
        try:
            # 1. Get the content from the specific version
            success, version_data = self.get_version_content(project_id, field_name, version_number)
            if not success:
                return False, version_data

            content = version_data.get("content")
            if content is None:
                return False, {"error": "Version content is empty"}

            # 2. Update the project table
            def _update_project():
                return (
                    self.supabase_client.table("archon_projects")
                    .update({field_name: content})
                    .eq("id", project_id)
                    .execute()
                )

            proj_success, proj_res = self.execute_query(_update_project, f"Failed to update project {field_name}")
            if not proj_success:
                return False, proj_res

            # 3. Create a new version entry reflecting the restoration
            self.create_version(
                project_id=project_id,
                field_name=field_name,
                content=cast(dict[str, Any], content),
                change_summary=f"Restored to version {version_number}",
                change_type="restore",
                created_by=restored_by,
            )

            return True, {"restored_content": content}
        except Exception as e:
            return False, {"error": str(e)}

    async def get_all_versions(self) -> tuple[bool, dict[str, Any]]:
        """Retrieve all document versions across all projects."""

        def _query():
            return (
                self.supabase_client.table("archon_sources")
                .select("*")
                .order("created_at", desc=True)
                .limit(100)
                .execute()
            )

        return self.execute_query(_query, "Failed to fetch all versions")
