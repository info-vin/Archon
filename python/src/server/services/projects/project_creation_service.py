"""
Project Creation Service Module for Archon

This module handles the complex project creation workflow including
AI-assisted documentation generation and progress tracking.
"""

# Removed direct logging import - using unified config
from dataclasses import asdict, dataclass, field
from typing import Any

from src.server.repositories.base_repository import BaseRepository

from ...config.logfire_config import get_logger

logger = get_logger(__name__)


@dataclass
class ProjectCreationResultDTO:
    data: list[dict[str, Any]]


@dataclass
class ProjectDataDTO:
    title: str
    description: str | None
    github_repo: str | None
    docs: list[Any] = field(default_factory=list)
    features: list[Any] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)



class ProjectCreationService(BaseRepository):
    """Service class for advanced project creation with AI assistance"""

    def __init__(self, supabase_client: Any = None) -> None:
        """Initialize with optional supabase client"""
        super().__init__(supabase_client)

    async def create_project_with_ai(
        self,
        progress_id: str,
        title: str,
        description: str | None = None,
        github_repo: str | None = None,
        **kwargs: Any,
    ) -> tuple[bool, ProjectCreationResultDTO | dict[str, Any]]:
        """
        Create a project with AI-assisted documentation generation.

        Args:
            progress_id: Progress tracking identifier
            title: Project title
            description: Project description
            github_repo: GitHub repository URL

        Returns:
            Tuple of (success, result_dict)
        """
        _ = kwargs
        logger.info(
            f"🏗️ [PROJECT-CREATION] Starting create_project_with_ai for progress_id: {progress_id}, title: {title}"
        )
        project_data = ProjectDataDTO(
            title=title,
            description=description,
            github_repo=github_repo,
        )

        # Dataclass serialization for supabase insertion
        insert_payload = asdict(project_data)

        query = self.supabase_client.table("archon_projects").insert(insert_payload) # 合法
        success, result = self.execute_query(query_func=query, error_context="DB operation logged error")
        if success:
            # TODO: Extract properties via 'result["data"]' as per original logic
            return True, ProjectCreationResultDTO(data=result.get("data", []))
        return False, result

    async def _generate_ai_documentation(
        self,
        progress_id: str,
        project_id: str,
        title: str,
        description: str | None,
        github_repo: str | None,
    ) -> bool:
        """
        Generate AI documentation for the project.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if LLM provider is configured
            from ..credential_service import credential_service
            from ..credentials.provider_configs import get_active_provider

            provider_config = await get_active_provider(credential_service, "llm")

            if not provider_config:
                # No LLM provider configured, skip AI documentation
                return False

            # Import DocumentAgent (lazy import to avoid startup issues)
            from ...agents.document_agent import DocumentAgent

            # Initialize DocumentAgent
            document_agent = DocumentAgent()

            # Generate comprehensive PRD using conversation
            prd_request = (
                f"Create a PRD document titled '{title} - Product Requirements Document' for a project called '{title}'"
            )
            if description:
                prd_request += f" with the following description: {description}"
            if github_repo:
                prd_request += f" (GitHub repo: {github_repo})"

            # Create a progress callback for the document agent
            async def agent_progress_callback(update_data: dict[str, Any]) -> Any:
                pass  # Progress tracking removed

            # Run the document agent to create PRD
            agent_result = await document_agent.run_conversation(
                user_message=prd_request,
                project_id=project_id,
                user_id="system",
                progress_callback=agent_progress_callback,
            )

            if agent_result.success:
                return True
            else:
                return False

        except Exception as ai_error:
            logger.warning(f"AI generation failed, continuing with basic project: {ai_error}")

            return False
