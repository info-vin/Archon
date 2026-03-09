"""
DocumentAgent - Conversational Document Management with PydanticAI

This agent enables users to create, update, and modify project documents through
natural conversation. Refactored for L2 modularity.
"""

import logging
import os
import uuid
from datetime import datetime
from typing import Any

from pydantic_ai import Agent, RunContext

from .base_agent import BaseAgent
from .document import logic
from .document.models import DocumentDependencies, DocumentOperation

logger = logging.getLogger(__name__)


class DocumentAgent(BaseAgent[DocumentDependencies, DocumentOperation]):
    """
    Conversational agent for document management.
    Facade pattern maintained for full backward compatibility.
    """

    def __init__(self, model: str | None = None, supabase_client: Any = None, **kwargs):
        if model is None:
            model = os.getenv("DOCUMENT_AGENT_MODEL", "openai:gpt-4o")

        super().__init__(
            model=model, name="DocumentAgent", retries=3, enable_rate_limiting=True, **kwargs
        )
        self.supabase_client = supabase_client

    def _create_agent(self, **kwargs) -> Agent[DocumentDependencies, DocumentOperation]:
        """Create the PydanticAI agent with tools and prompts."""
        system_prompt = self.get_system_prompt()

        agent: Agent[DocumentDependencies, DocumentOperation] = Agent(
            model=self.model,
            deps_type=DocumentDependencies,
            system_prompt=system_prompt,
            **kwargs,
        )

        @agent.system_prompt
        async def add_project_context(ctx: RunContext[DocumentDependencies]) -> str:
            return f"""
**Current Project Context:**
- Project ID: {ctx.deps.project_id}
- User ID: {ctx.deps.user_id or "Unknown"}
- Current Document: {ctx.deps.current_document_id or "None"}
- Timestamp: {datetime.now().isoformat()}
"""

        @agent.tool
        async def list_documents(ctx: RunContext[DocumentDependencies]) -> str:
            """List all documents in the current project."""
            return await logic.list_documents_logic(self.supabase_client, ctx.deps.project_id)

        @agent.tool
        async def get_document(ctx: RunContext[DocumentDependencies], document_title: str) -> str:
            """Get the content of a specific document by title."""
            return await logic.get_document_logic(self.supabase_client, ctx.deps.project_id, document_title)

        @agent.tool
        async def create_document(
            ctx: RunContext[DocumentDependencies],
            title: str,
            document_type: str,
            content_description: str,
        ) -> str:
            """Create a new document with structured content."""
            return await logic.create_document_logic(
                ctx.deps.project_id, ctx.deps.user_id, title, document_type, content_description, ctx.deps.progress_callback
            )

        @agent.tool
        async def update_document(
            ctx: RunContext[DocumentDependencies],
            document_title: str,
            section_to_update: str,
            new_content: str,
            update_description: str,
        ) -> str:
            """Update a specific section of an existing document."""
            return await logic.update_document_logic(
                ctx.deps.project_id, document_title, section_to_update, new_content, update_description
            )

        @agent.tool
        async def create_feature_plan(
            ctx: RunContext[DocumentDependencies],
            feature_name: str,
            feature_description: str,
            user_stories: str,
        ) -> str:
            """Create a React Flow feature plan."""
            return await logic.create_feature_plan_logic(
                ctx.deps.project_id, ctx.deps.user_id, feature_name, feature_description, user_stories
            )

        @agent.tool
        async def create_erd(
            ctx: RunContext[DocumentDependencies],
            system_name: str,
            entity_descriptions: str,
            relationships_description: str,
        ) -> str:
            """Create an Entity Relationship Diagram description and schema."""
            return await logic.create_erd_logic(
                ctx.deps.project_id, ctx.deps.user_id, system_name, entity_descriptions, relationships_description
            )

        @agent.tool
        async def request_approval(
            ctx: RunContext[DocumentDependencies],
            document_title: str,
            change_summary: str,
            change_type: str = "update",
        ) -> str:
            """Request approval for document changes."""
            return await logic.request_approval_logic(
                ctx.deps.project_id, ctx.deps.user_id, document_title, change_summary, change_type
            )

        return agent

    def get_system_prompt(self) -> str:
        """Fetch the system prompt from the prompt service."""
        from ..services.prompt_service import prompt_service
        default_prompt = "You are a Document Management Assistant."
        prompt: str = prompt_service.get_prompt("document_agent_prompt", default_prompt)
        return prompt

    def _generate_block_id(self) -> str:
        """Generate a unique block ID (Facade)."""
        return str(uuid.uuid4())

    def _create_block(self, block_type: str, content: str, properties: dict[str, Any] | None = None) -> dict[str, Any]:
        """Create a document block (Facade)."""
        return {
            "id": self._generate_block_id(),
            "type": block_type,
            "content": content,
            "properties": properties or {"text": content}
        }

    async def run_conversation(
        self,
        user_message: str,
        project_id: str,
        user_id: str | None = None,
        current_document_id: str | None = None,
        progress_callback: Any | None = None,
    ) -> DocumentOperation:
        """Run the agent for conversational document management."""
        deps = DocumentDependencies(
            project_id=project_id,
            user_id=user_id,
            current_document_id=current_document_id,
            progress_callback=progress_callback,
        )

        try:
            result = await self.run(user_message, deps)
            return result
        except Exception as e:
            self.logger.error(f"Document operation failed: {str(e)}")
            return DocumentOperation(
                operation_type="error", document_id=None, document_type=None,
                title=None, success=False, message=f"Failed: {str(e)}",
                changes_made=[], content_preview=None,
            )
