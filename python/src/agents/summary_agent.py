"""
SummaryAgent - A simple AI agent for summarizing text content.
"""

import logging
import os
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from .base_agent import ArchonDependencies, BaseAgent
from .mcp_client import get_mcp_client  # Agent needs to call MCP to update task status/output

logger = logging.getLogger(__name__)


@dataclass
class SummaryDependencies(ArchonDependencies):
    """Dependencies for summary operations."""
    text_to_summarize: str = ""
    task_id: str = ""
    project_id: str = ""
    progress_callback: Any | None = None  # Callback for progress updates


class SummaryOperation(BaseModel):
    """Structured output for summary operations."""
    summary: str = Field(description="The concise summary of the provided text.")
    original_length: int = Field(description="Length of the original text.")
    summary_length: int = Field(description="Length of the generated summary.")
    success: bool = Field(description="Whether the summary operation was successful.")
    message: str = Field(description="Human-readable message about the operation.")


class SummaryAgent(BaseAgent[SummaryDependencies, SummaryOperation]):
    """
    A simple agent that summarizes text content.
    """

    def __init__(self, model: str = None, **kwargs):
        if model is None:
            model = os.getenv("SUMMARY_AGENT_MODEL", "openai:gpt-4o-mini") # Use a cheaper model for summary

        super().__init__(
            model=model, name="SummaryAgent", retries=3, enable_rate_limiting=True, **kwargs
        )

    def _create_agent(self, **kwargs) -> Agent:
        """Create the PydanticAI agent with tools and prompts."""
        agent = Agent(
            model=self.model,
            deps_type=SummaryDependencies,
            result_type=SummaryOperation,
            system_prompt="You are a concise summarization assistant. Your goal is to provide accurate and brief summaries of any given text. Use the 'summarize_text' tool to process user requests.",
            **kwargs,
        )

        @agent.tool
        async def summarize_text(ctx: RunContext[SummaryDependencies]) -> SummaryOperation:
            """
            Summarizes the provided text content.
            """
            text = ctx.deps.text_to_summarize
            task_id = ctx.deps.task_id
            project_id = ctx.deps.project_id
            progress_callback = ctx.deps.progress_callback

            if not text:
                return SummaryOperation(
                    summary="", original_length=0, summary_length=0,
                    success=False, message="No text provided for summarization."
                )

            if progress_callback:
                await progress_callback({
                    "step": "summarization",
                    "log": "✍️ Generating summary..."
                })

            # --- Call LLM for summarization ---
            # In a real scenario, this would involve a call to an LLM.
            # This call will be mocked in the unit test.
            import litellm
            response = await litellm.completion(
                model=self.model,
                messages=[{"role": "user", "content": f"Summarize this text: {text}"}]
            )
            generated_summary = response['choices'][0]['message']['content']

            # Report output back to archon-server via MCP Client
            mcp_client = await get_mcp_client()

            await mcp_client.call_tool(
                tool_name="manage_task",
                action="update",
                project_id=project_id,
                task_id=task_id,
                output={
                    "agent": self.name,
                    "summary": generated_summary,
                    "original_text_length": len(text)
                },
            )

            if progress_callback:
                await progress_callback({
                    "step": "summarization",
                    "log": "✅ Summary generated and reported."
                })

            return SummaryOperation(
                summary=generated_summary,
                original_length=len(text),
                summary_length=len(generated_summary),
                success=True,
                message="Text summarized successfully and reported via MCP."
            )

        return agent

    def get_system_prompt(self) -> str:
        """Get the base system prompt for this agent."""
        return "You are a concise summarization assistant. Your goal is to provide accurate and brief summaries of any given text. Use the 'summarize_text' tool to process user requests."
