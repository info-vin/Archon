"""
RAG Agent - Conversational Search and Retrieval with PydanticAI

This agent enables users to search and chat with documents stored in the RAG system.
It uses the perform_rag_query functionality to retrieve relevant content and provide
intelligent responses based on the retrieved information.
"""

import logging
import os
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field
from pydantic_ai import Agent

from .base_agent import ArchonDependencies, BaseAgent

logger = logging.getLogger(__name__)


@dataclass
class RagDependencies(ArchonDependencies):
    """Dependencies for RAG operations."""

    project_id: str | None = None
    source_filter: str | None = None
    match_count: int = 5
    progress_callback: Any | None = None  # Callback for progress updates


class RagQueryResult(BaseModel):
    """Structured output for RAG query results."""

    query_type: str = Field(description="Type of query: search, explain, summarize, compare")
    original_query: str = Field(description="The original user query")
    refined_query: str | None = Field(description="Refined query used for search if different from original")
    results_found: int = Field(description="Number of relevant results found")
    sources: list[str] = Field(description="List of unique sources referenced")
    answer: str = Field(description="The synthesized answer based on retrieved content")
    citations: list[dict[str, Any]] = Field(description="Citations with source and relevance info")
    success: bool = Field(description="Whether the query was successful")
    message: str = Field(description="Status message or error description")


class RagAgent(BaseAgent[RagDependencies, str]):
    """
    Conversational agent for RAG-based document search and retrieval.

    Capabilities:
    - Search documents using natural language queries
    - Filter by specific sources
    - Search code examples
    - Provide synthesized answers with citations
    - Explain concepts found in documentation
    """

    def __init__(self, model: str | None = None, **kwargs):
        # Use provided model or fall back to default
        if model is None:
            model = os.getenv("RAG_AGENT_MODEL")

        super().__init__(model=model, name="RagAgent", retries=3, enable_rate_limiting=True, **kwargs)

    def _create_agent(self, **kwargs) -> Agent[RagDependencies, str]:
        """Create the PydanticAI agent with tools and prompts."""
        system_prompt = self.get_system_prompt()

        agent: Agent[RagDependencies, str] = Agent(
            model=self.model,
            deps_type=RagDependencies,
            system_prompt=system_prompt,
            **kwargs,
        )

        # Register dynamic system prompt for context
        from src.agents.rag.tools import (
            add_search_context_prompt,
            list_available_sources_tool,
            refine_search_query_tool,
            search_code_examples_tool,
            search_documents_tool,
        )

        agent.system_prompt(add_search_context_prompt)

        # Register tools for RAG operations
        agent.tool(search_documents_tool)
        agent.tool(list_available_sources_tool)
        agent.tool(search_code_examples_tool)
        agent.tool(refine_search_query_tool)

        return agent

    def get_system_prompt(self) -> str:
        """Get the base system prompt for this agent."""
        default_prompt = """You are a RAG (Retrieval-Augmented Generation) Assistant that helps users search and understand documentation through conversation.

**Your Capabilities:**
- Search through crawled documentation using semantic search
- Filter searches by specific sources or domains
- Find relevant code examples
- Synthesize information from multiple sources
- Provide clear, cited answers based on retrieved content
- Explain technical concepts found in documentation

**Your Approach:**
1. **Understand the query** - Interpret what the user is looking for
2. **Search effectively** - Use appropriate search terms and filters
3. **Analyze results** - Review retrieved content for relevance
4. **Synthesize answers** - Combine information from multiple sources
5. **Cite sources** - Always provide references to source documents

**Common Queries:**
- "What resources/sources are available?" → Use list_available_sources tool
- "Search for X" → Use search_documents tool
- "Find code examples for Y" → Use search_code_examples tool
- "What documentation do you have?" → Use list_available_sources tool

**Search Strategies:**
- For conceptual questions: Use broader search terms
- For specific features: Use exact terminology
- For code examples: Search for function names, patterns
- For comparisons: Search for each item separately

**Response Guidelines:**
- Provide direct answers based on retrieved content
- Include relevant quotes from sources
- Cite sources with URLs when available
- Admit when information is not found
- Suggest alternative searches if needed"""
        try:
            from server.services.prompt_service import prompt_service

            return str(
                prompt_service.get_prompt(
                    "rag_agent_prompt",
                    default=default_prompt,
                )
            )
        except (ImportError, Exception) as e:
            logger.warning(f"Could not load prompt from service (fallback to default): {e}")
            return default_prompt

    async def run_conversation(
        self,
        user_message: str,
        project_id: str | None = None,
        source_filter: str | None = None,
        match_count: int = 5,
        user_id: str | None = None,
        progress_callback: Any | None = None,
    ) -> RagQueryResult:
        """
        Run the agent for conversational RAG queries.

        Args:
            user_message: The user's search query or question
            project_id: Optional project ID for context
            source_filter: Optional source domain to filter results
            match_count: Maximum number of results to return
            user_id: ID of the user making the request
            progress_callback: Optional callback for progress updates

        Returns:
            Structured RagQueryResult
        """
        deps = RagDependencies(
            project_id=project_id,
            source_filter=source_filter,
            match_count=match_count,
            user_id=user_id,
            progress_callback=progress_callback,
        )

        try:
            # Run the agent and get the string response
            response_text = await self.run(user_message, deps)
            self.logger.info("RAG query completed successfully")

            # Create a structured result from the response text
            # Try to extract some basic information from the response
            query_type = "search"  # Default type
            results_found = 0
            sources = []

            # Simple analysis of the response to gather metadata
            if "found" in response_text.lower() and "results" in response_text.lower():
                # Try to extract number of results
                import re

                match = re.search(r"found (\d+)", response_text.lower())
                if match:
                    results_found = int(match.group(1))

            if "available sources" in response_text.lower():
                query_type = "list_sources"
            elif "code example" in response_text.lower():
                query_type = "code_search"
            elif "no results" in response_text.lower():
                results_found = 0

            # Extract source references if present
            source_lines = [line for line in response_text.split("\n") if "Source:" in line]
            sources = [line.split("Source:")[-1].strip() for line in source_lines]

            return RagQueryResult(
                query_type=query_type,
                original_query=user_message,
                refined_query=None,
                results_found=results_found,
                sources=list(set(sources)),  # Remove duplicates
                answer=response_text,
                citations=[],  # Could be enhanced to extract citations
                success=True,
                message="Query completed successfully",
            )

        except Exception as e:
            self.logger.error(f"RAG query failed: {str(e)}")
            # Return error result
            return RagQueryResult(
                query_type="error",
                original_query=user_message,
                refined_query=None,
                results_found=0,
                sources=[],
                answer=f"I encountered an error while searching: {str(e)}",
                citations=[],
                success=False,
                message=f"Failed to process query: {str(e)}",
            )


# Note: RagAgent instances should be created on-demand in API endpoints
# to avoid initialization issues during module import
