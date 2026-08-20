"""
PresentationAgent - Retrieves knowledge, queries NotebookLM, and archives results to Google Drive.
"""

import logging
import os
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from ..base_agent import ArchonDependencies, BaseAgent
from ..mcp_client import get_mcp_client

logger = logging.getLogger(__name__)


@dataclass
class PresentationDependencies(ArchonDependencies):
    """Dependencies for presentation operations."""

    topic: str = ""
    notebook_id: str = ""
    task_id: str = ""
    project_id: str = ""
    progress_callback: Any | None = None


class PresentationOperation(BaseModel):
    """Structured output for presentation operations."""

    content: str = Field(description="The generated presentation content or answers.")
    gdrive_file_id: str = Field(description="The Google Drive file ID of the archived presentation.")
    success: bool = Field(description="Whether the presentation agent flow succeeded.")
    message: str = Field(description="Summary message of the operation.")


class PresentationAgent(BaseAgent[PresentationDependencies, PresentationOperation]):
    """
    Agent that handles presentation generation via NotebookLM and Google Drive archiving.
    """

    def __init__(self, model: str | None = None, **kwargs):
        if model is None:
            model = os.getenv("PRESENTATION_AGENT_MODEL")

        super().__init__(model=model, name="PresentationAgent", retries=3, enable_rate_limiting=True, **kwargs)

    def _create_agent(self, **kwargs) -> Agent[PresentationDependencies, PresentationOperation]:
        """Create the PydanticAI agent with tools and prompts."""
        from src.server.services.prompt_service import prompt_service
        from src.server.services.shared_constants import PromptNameEnum

        system_prompt = prompt_service.get_prompt(
            PromptNameEnum.PRESENTATION_AGENT_PROMPT,
            "You are a presentation assistant. Retrieve knowledge, query NotebookLM, and archive to Drive.",
        )

        agent = Agent(
            model=self.model,
            deps_type=PresentationDependencies,
            system_prompt=system_prompt,
            **kwargs,
        )

        @agent.tool
        async def generate_and_archive(ctx: RunContext[PresentationDependencies]) -> PresentationOperation:
            """
            Queries NotebookLM for the topic, generates presentation content, and simulates archiving to Google Drive.
            """
            return await self.generate_and_archive(ctx)

        return agent

    async def generate_and_archive(self, ctx: RunContext[PresentationDependencies]) -> PresentationOperation:
        """
        Implementation of the generate_and_archive tool logic.
        """
        topic = ctx.deps.topic
        notebook_id = ctx.deps.notebook_id
        task_id = ctx.deps.task_id
        project_id = ctx.deps.project_id
        progress_callback = ctx.deps.progress_callback

        if progress_callback:
            await progress_callback({"step": "query", "log": f"🔍 Querying NotebookLM for topic: {topic}..."})

        mcp_client = await get_mcp_client(agent_type="presentation")

        # 1. Query NotebookLM using the custom ask question tool
        try:
            import json

            result_str = await mcp_client.call_tool(
                tool_name="notebooklm_ask_question",
                notebook_id=notebook_id,
                question=f"Generate a detailed outline and slides content for: {topic}",
            )

            # Check if it was returned as JSON string
            try:
                result = json.loads(result_str)
            except Exception:
                result = {"success": True, "answer": result_str}
        except Exception as e:
            logger.error(f"Error querying NotebookLM in agent: {e}")
            result = {"success": False, "error": str(e)}

        if not result.get("success", False):
            return PresentationOperation(
                content="",
                gdrive_file_id="",
                success=False,
                message=f"NotebookLM query failed: {result.get('error')}",
            )

        answer_content = result.get("answer", "")

        if progress_callback:
            await progress_callback({"step": "archive", "log": "📁 Archiving presentation to Google Drive..."})

        # 2. Archive to Google Drive via true MCP Tool
        try:
            import json

            upload_result_str = await mcp_client.call_tool(
                tool_name="gdrive_upload_file",
                filename=f"Presentation_{topic.replace(' ', '_')}",
                content=answer_content,
                mime_type="text/plain",
            )
            upload_result = json.loads(upload_result_str)
        except Exception as e:
            logger.error(f"Error calling gdrive_upload_file: {e}")
            upload_result = {"success": False, "error": str(e)}

        if not upload_result.get("success", False):
            return PresentationOperation(
                content=answer_content,
                gdrive_file_id="",
                success=False,
                message=f"Google Drive upload failed: {upload_result.get('error')}",
            )

        real_file_id = upload_result.get("file_id", "")

        # Update task output via manage_task
        await mcp_client.call_tool(
            tool_name="manage_task",
            action="update",
            project_id=project_id,
            task_id=task_id,
            output={
                "agent": self.name,
                "content": answer_content,
                "gdrive_file_id": real_file_id,
            },
        )

        if progress_callback:
            await progress_callback(
                {"step": "complete", "log": "✅ Presentation archived and reported successfully."}
            )

        return PresentationOperation(
            content=answer_content,
            gdrive_file_id=real_file_id,
            success=True,
            message="Presentation generated and archived successfully.",
        )

    def get_system_prompt(self) -> str:
        """Get the base system prompt for this agent."""
        return "You are a presentation assistant. Retrieve knowledge, query NotebookLM, and archive to Drive."
