"""
PresentationAgent - Retrieves knowledge, queries NotebookLM, and archives results to Google Drive.
"""

import logging
import os
import uuid
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
    content: str = Field(description="The finalized comprehensive presentation content or script.")
    gdrive_file_id: str = Field(description="The Google Drive file ID of the archived presentation.")
    success: bool = Field(description="Whether the presentation agent flow succeeded.")
    message: str = Field(description="Summary message of the operation.")


class PresentationAgent(BaseAgent[PresentationDependencies, PresentationOperation]):
    """
    Agent that autonomously researches via NotebookLM and Librarian, then archives to Google Drive.
    """

    def __init__(self, model: str | None = None, **kwargs):
        if model is None:
            model = os.getenv("PRESENTATION_AGENT_MODEL")
        super().__init__(model=model, name="PresentationAgent", retries=3, enable_rate_limiting=True, **kwargs)

    def _create_agent(self, **kwargs) -> Agent[PresentationDependencies, PresentationOperation]:
        """Create the PydanticAI agent with distinct tools for autonomous reasoning."""
        from src.server.services.prompt_service import prompt_service
        from src.server.services.shared_constants import PromptNameEnum

        system_prompt = prompt_service.get_prompt(
            PromptNameEnum.PRESENTATION_AGENT_PROMPT,
            "You are an expert Presentation Agent. Your job is to create comprehensive slide deck content by first querying NotebookLM for deep insights, and finally generating and uploading a native PPTX slide deck to Google Drive using NotebookLM's native Slide Deck generation API."
        )

        agent = Agent(  # type: ignore[call-overload]
            model=self.model,
            deps_type=PresentationDependencies,
            output_type=PresentationOperation,
            system_prompt=system_prompt,
            **kwargs,
        )

        @agent.tool
        async def query_notebooklm(ctx: RunContext[PresentationDependencies], question: str) -> str:
            """Query NotebookLM for insights on the current topic. Use this to gather data before generating the slide deck."""
            if ctx.deps.progress_callback:
                await ctx.deps.progress_callback({"step": "query_notebooklm", "log": f"🧠 Querying NotebookLM: {question}"})

            mcp_client = await get_mcp_client(agent_type="presentation")
            import json
            try:
                res = await mcp_client.call_tool(
                    tool_name="notebooklm_ask_question",
                    notebook_id=ctx.deps.notebook_id,
                    question=question,
                )
                try:
                    return str(json.loads(res).get("answer", res))
                except Exception:
                    return str(res)
            except Exception as e:
                return f"Error querying NotebookLM: {str(e)}"

        @agent.tool
        async def generate_and_upload_pptx(ctx: RunContext[PresentationDependencies], instructions: str, title: str) -> str:
            """Generate a native PPTX Slide Deck in NotebookLM based on instructions, download it, and upload it to Google Drive."""
            if ctx.deps.progress_callback:
                await ctx.deps.progress_callback({"step": "generate_pptx", "log": f"📊 Generating native PPTX via NotebookLM with instructions: {instructions[:50]}..."})

            import json

            from notebooklm import NotebookLMClient

            # 1. Use NotebookLM Client directly to generate PPTX
            try:
                auth_json_path = os.path.join(os.path.expanduser("~"), ".notebooklm", "profiles", "default", "storage_state.json")
                if not os.path.exists(auth_json_path) and os.getenv("NOTEBOOKLM_AUTH_JSON"):
                    os.makedirs(os.path.dirname(auth_json_path), exist_ok=True)
                    with open(auth_json_path, "w") as f:
                        f.write(os.getenv("NOTEBOOKLM_AUTH_JSON") or "")

                ctx_client = NotebookLMClient.from_storage()
                async with ctx_client as client:
                    status = await client.artifacts.generate_slide_deck(
                        notebook_id=ctx.deps.notebook_id,
                        instructions=instructions
                    )

                    task_id = getattr(status, "task_id", None)
                    if not task_id and isinstance(status, dict):
                        task_id = status.get("task_id")

                    if not task_id:
                        return "Failed to generate PPTX in NotebookLM: No task ID returned."

                    # Wait for completion
                    final_status = await client.artifacts.wait_for_completion(ctx.deps.notebook_id, task_id)
                    if getattr(final_status, "status", None) != "completed":
                        return f"PPTX generation did not complete successfully. Status: {final_status}"

                    artifact_id = getattr(final_status, "artifact_id", None)
                    if not artifact_id and isinstance(final_status, dict):
                        artifact_id = final_status.get("artifact_id") or final_status.get("id")

                    # Download PPTX
                    output_path = f"/tmp/notebooklm_{uuid.uuid4().hex}.pptx"
                    await client.artifacts.download_slide_deck(
                        notebook_id=ctx.deps.notebook_id,
                        output_path=output_path,
                        artifact_id=artifact_id,
                        output_format="pptx"
                    )
            except Exception as e:
                logger.error(f"Error generating PPTX via NotebookLM: {e}")
                return f"Error generating PPTX via NotebookLM: {str(e)}"

            if ctx.deps.progress_callback:
                await ctx.deps.progress_callback({"step": "upload_gdrive", "log": f"📁 Uploading native PPTX '{title}' to Google Drive..."})

            # 2. Upload to Google Drive
            mcp_client = await get_mcp_client(agent_type="presentation")
            try:
                res = await mcp_client.call_tool(
                    tool_name="gdrive_upload_file",
                    filename=f"{title}.pptx",
                    content="",
                    mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    local_file_path=output_path
                )
                try:
                    data = json.loads(res)
                    if data.get("success"):
                        file_id = data.get("file_id", "")

                        # Clean up temp file
                        if os.path.exists(output_path):
                            os.remove(output_path)

                        # Update task in DB
                        if ctx.deps.task_id and ctx.deps.project_id:
                            await mcp_client.call_tool(
                                tool_name="manage_task",
                                action="update",
                                project_id=ctx.deps.project_id,
                                task_id=ctx.deps.task_id,
                                output={
                                    "agent": self.name,
                                    "content": f"Successfully generated and uploaded PPTX. Instructions used: {instructions}",
                                    "gdrive_file_id": file_id,
                                }
                            )
                        return str(file_id)
                    return f"Upload failed: {data.get('error')}"
                except Exception:
                    return str(res)
            except Exception as e:
                return f"Error uploading to Google Drive: {str(e)}"

        return agent  # type: ignore[no-any-return]

    def get_system_prompt(self) -> str:
        return "You are an expert Presentation Agent using NotebookLM's native PPTX generation."
