# python/src/server/services/projects/project_service.py

from typing import Any

from src.server.repositories.base_repository import BaseRepository

from ...config.logfire_config import get_logger
from .task_service import TaskService

logger = get_logger(__name__)


class ProjectService(BaseRepository):
    def __init__(self, supabase_client: Any = None) -> None:
        super().__init__(supabase_client)
        self.task_service = TaskService(self.supabase_client)

    async def list_projects(
        self, include_content: bool = True, include_computed_status: bool = False
    ) -> tuple[bool, dict[str, Any]]:

        success, result = self.execute_query(self.supabase_client.table("archon_projects").select("*").order("created_at", desc=True), "Database operation failed") # 合法
        if success:
            projects = result["data"]
            for p in projects:
                # Ensure 'stats' exists for UI/tests
                if "stats" not in p:
                    # Original logic expected docs_count for token optimization tests
                    docs = p.get("docs") or {}
                    docs_count = len(docs) if isinstance(docs, dict) else (len(docs) if isinstance(docs, list) else 0)

                    features = p.get("features") or []
                    features_count = len(features) if isinstance(features, list) else 0

                    # Correct field check for has_data
                    data_field = p.get("data") or {}
                    has_data = bool(data_field)

                    p["stats"] = {
                        "task_count": 0,
                        "completed_tasks": 0,
                        "docs_count": docs_count,
                        "features_count": features_count,
                        "has_data": has_data,
                    }

                if not include_content:
                    # LIGHTWEIGHT: Remove heavy fields
                    p.pop("docs", None)
                    p.pop("features", None)
                    p.pop("data", None)
            return True, {"projects": projects}
        return False, result

    async def create_project(self, title: str, github_repo: str | None = None) -> tuple[bool, dict[str, Any]]:
        project_data: dict[str, Any] = {
            "title": title,
            "github_repo": github_repo,
            "status": "planning",
            "docs": {},
            "features": [],
            "data": {},
        }

        # --- Phase 5.11.3: Lifecycle Provisioning Debt ---
        try:
            from notebooklm import NotebookLMClient

            from src.server.services.settings_service import SettingsService
            from src.server.utils.notebooklm_auth import sync_notebooklm_session

            settings = SettingsService()
            auth_json = settings.get_setting("notebooklm_auth_json", default=None)

            if auth_json:
                async with sync_notebooklm_session(settings):
                    ctx_client = NotebookLMClient.from_storage()
                    async with ctx_client as client:
                        nb = await client.notebooks.create(title=title)
                        nb_id = getattr(nb, "id", None) or (nb.get("id") if isinstance(nb, dict) else None)
                        if nb_id:
                            project_data["data"]["notebook_id"] = nb_id
                            logger.info(f"Provisioned NotebookLM (ID: {nb_id}) for project '{title}'")
        except Exception as e:
            logger.warning(f"Failed to provision NotebookLM during project creation: {e}")


        success, result = self.execute_query(self.supabase_client.table("archon_projects").insert(project_data), "Database operation failed") # 合法
        if success:
            return True, {"project": result["data"][0] if result["data"] else {}}
        return False, result

    async def get_project(self, project_id: str) -> tuple[bool, dict[str, Any]]:

        success, result = self.execute_query(self.supabase_client.table("archon_projects").select("*").eq("id", project_id), "DB operation logged error") # 合法
        if success:
            return True, {"project": result["data"][0] if result["data"] else {}}
        return False, result

    async def update_project(self, project_id: str, project_data: dict[str, Any]) -> tuple[bool, dict[str, Any]]:

        success, result = self.execute_query(self.supabase_client.table("archon_projects").update(project_data).eq("id", project_id), "Database operation failed") # 合法
        if success:
            return True, {"project": result["data"][0] if result["data"] else {}}
        return False, result

    async def delete_project(self, project_id: str) -> tuple[bool, dict[str, Any]]:

        success, result = self.execute_query(self.supabase_client.table("archon_projects").delete().eq("id", project_id), "Database operation failed") # 合法
        if success:
            return True, {"message": "Project deleted successfully"}
        return False, result

    async def get_project_features(self, project_id: str) -> tuple[bool, dict[str, Any]]:
        """Retrieve features for a project."""

        query = self.supabase_client.table("archon_projects").select("features").eq("id", project_id) # 合法
        success, result = self.execute_query(query, f"Failed to fetch features for project {project_id}")
        if success:
            data = result.get("data", [])
            features_data = data[0] if isinstance(data, list) and data else (data if data else {})
            return True, features_data
        return False, result
