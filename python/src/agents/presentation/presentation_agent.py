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
            from src.server.config.model_ssot import SYSTEM_MODELS
            model = SYSTEM_MODELS["DEFAULT_PRO"].split("/")[-1]
        super().__init__(model=model, name="PresentationAgent", retries=3, enable_rate_limiting=True, **kwargs)

    def _create_agent(self, **kwargs) -> Agent[PresentationDependencies, PresentationOperation]:
        """Create the PydanticAI agent with distinct tools for autonomous reasoning."""
        from src.server.services.prompt_service import prompt_service
        from src.server.services.shared_constants import PromptNameEnum

        system_prompt = prompt_service.get_prompt(
            PromptNameEnum.PRESENTATION_AGENT_PROMPT,
            "You are an expert Presentation Agent. Your job is to create comprehensive slide deck content by first querying NotebookLM for deep insights, and finally generating and uploading a native PPTX slide deck to Google Drive using NotebookLM's native Slide Deck generation API."
        )

        agent = Agent(
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

            from src.server.services.settings_service import SettingsService
            from src.server.utils.notebooklm_auth import sync_notebooklm_session

            # 1. Use NotebookLM Client directly to generate PPTX
            try:
                settings = SettingsService()
                async with sync_notebooklm_session(settings):
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

                        # --- Phase 5.11.3: Download PDF for Dual-Track Storage ---
                        output_path_pdf = f"/tmp/notebooklm_{uuid.uuid4().hex}.pdf"
                        await client.artifacts.download_slide_deck(
                            notebook_id=ctx.deps.notebook_id,
                            output_path=output_path_pdf,
                            artifact_id=artifact_id,
                        output_format="pdf"
                    )
            except Exception as e:
                logger.error(f"Error generating PPTX via NotebookLM: {e}")
                return f"Error generating PPTX via NotebookLM: {str(e)}"

            if ctx.deps.progress_callback:
                await ctx.deps.progress_callback({"step": "upload_gdrive", "log": f"📁 Uploading native PPTX '{title}' to Google Drive..."})

            # 2. Upload to Google Drive (PPTX)
            mcp_client = await get_mcp_client(agent_type="presentation")
            try:
                res = await mcp_client.call_tool(
                    tool_name="gdrive_upload_file",
                    filename=f"{title}.pptx",
                    content="",
                    mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    local_file_path=output_path
                )

                # --- Phase 5.11.3: Process PDF for Supabase Knowledge Base (Dual-Track) ---
                if ctx.deps.progress_callback:
                    await ctx.deps.progress_callback({"step": "upload_supabase", "log": "🗄️ Indexing PDF to Supabase Knowledge Base..."})
                try:
                    if os.path.exists(output_path_pdf):
                        import pdfplumber

                        from src.server.services.storage.storage_services import DocumentStorageService
                        from src.server.utils import get_supabase_client

                        # 1. Extract text & vectorize
                        pdf_text = ""
                        with pdfplumber.open(output_path_pdf) as pdf:
                            for page in pdf.pages:
                                extracted = page.extract_text()
                                if extracted:
                                    pdf_text += extracted + "\n"
                        storage_service = DocumentStorageService()
                        await storage_service.upload_document(
                            file_content=pdf_text,
                            filename=f"{title}.pdf",
                            source_id="notebooklm_presentation",
                            knowledge_type="presentation"
                        )

                        # 2. Upload binary to Storage
                        supabase = get_supabase_client()
                        with open(output_path_pdf, "rb") as f:
                            supabase.storage.from_("knowledge_base").upload(
                                path=f"presentations/{title}_{uuid.uuid4().hex[:8]}.pdf",
                                file=f.read(),
                                file_options={"content-type": "application/pdf", "upsert": "true"}
                            )
                        os.remove(output_path_pdf)
                except Exception as pdf_e:
                    logger.error(f"Error processing PDF dual-track: {pdf_e}")

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

        return agent

    def get_system_prompt(self) -> str:
        return "You are an expert Presentation Agent using NotebookLM's native PPTX generation."
