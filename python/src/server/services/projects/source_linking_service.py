# python/src/server/services/projects/source_linking_service.py

from typing import Any

from src.server.repositories.base_repository import BaseRepository

from ...config.logfire_config import get_logger

logger = get_logger(__name__)

class SourceLinkingService(BaseRepository):
    """Service class for managing project-source relationships"""

    def __init__(self, supabase_client=None):
        """Initialize with optional supabase client"""
        super().__init__(supabase_client)

    async def get_project_sources(self, project_id: str) -> tuple[bool, dict[str, Any]]:
        """
        Get all linked sources for a project, separated by type.
        """
        def _query():
            return (
                self.supabase_client.table("archon_project_sources")
                .select("source_id, notes")
                .eq("project_id", project_id)
                .execute()
            )

        success, result = self.execute_query(_query, "Failed to fetch project sources")
        if not success:
            return False, result

        sources = result.get("data", [])
        return True, {
            "technical_sources": [s["source_id"] for s in sources if s.get("notes") == "technical"],
            "business_sources": [s["source_id"] for s in sources if s.get("notes") == "business"]
        }

    async def update_project_sources(
        self,
        project_id: str,
        technical_sources: list[str] | None = None,
        business_sources: list[str] | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        """
        Update project sources, replacing existing ones if provided.
        """
        try:
            # 1. Clear existing links
            def _delete():
                return self.supabase_client.table("archon_project_sources").delete().eq("project_id", project_id).execute()

            self.execute_query(_delete, "Failed to clear project sources", require_data=False)

            # 2. Batch insert new links
            all_links = []
            if technical_sources:
                for s_id in technical_sources:
                    all_links.append({"project_id": project_id, "source_id": s_id, "notes": "technical"})
            if business_sources:
                for s_id in business_sources:
                    all_links.append({"project_id": project_id, "source_id": s_id, "notes": "business"})

            if all_links:
                def _insert():
                    return self.supabase_client.table("archon_project_sources").insert(all_links).execute()
                return self.execute_query(_insert, "Failed to batch link sources")

            return True, {"message": "No sources to link"}
        except Exception as e:
            return False, {"error": str(e)}

    async def link_sources(self, project_id: str, technical_source_ids: list[str], business_source_ids: list[str]) -> tuple[bool, dict[str, Any]]:
        """
        Legacy wrapper for link_sources.
        """
        return await self.update_project_sources(project_id, technical_source_ids, business_source_ids)

    async def format_project_with_sources(self, project: dict[str, Any]) -> dict[str, Any]:
        """
        Enriches a project dictionary with its linked technical and business sources.
        """
        project_id = project.get("id")
        if not project_id:
            return project

        success, sources_res = await self.get_project_sources(project_id)
        if success:
            project["technical_sources"] = sources_res.get("technical_sources", [])
            project["business_sources"] = sources_res.get("business_sources", [])
        else:
            project["technical_sources"] = []
            project["business_sources"] = []

        return project

    async def format_projects_with_sources(self, projects: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Enriches a list of projects with their linked sources.
        """
        import asyncio
        tasks = [self.format_project_with_sources(p) for p in projects]
        return await asyncio.gather(*tasks)
