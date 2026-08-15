"""
Agentic RAG Strategy

Implements agentic RAG functionality for intelligent code example extraction and search.
This strategy focuses on code-specific search and retrieval, providing enhanced
search capabilities for code examples, documentation, and programming-related content.

Key features:
- Enhanced query processing for code-related searches
- Specialized embedding strategies for code content
- Code example extraction and retrieval
- Programming language and framework-aware search
"""

from typing import TYPE_CHECKING, Any, cast

from supabase import Client

from src.server.repositories.base_repository import BaseRepository

from ...config.logfire_config import get_logger, safe_span
from ..embeddings.embedding_service import create_embedding

logger = get_logger(__name__)


class AgenticRAGStrategy(BaseRepository):
    """Strategy class implementing agentic RAG for code example search and extraction"""

    def __init__(self, supabase_client: Client, base_strategy) -> None:
        """
        Initialize agentic RAG strategy.

        Args:
            supabase_client: Supabase client for database operations
            base_strategy: Base strategy for vector search
        """
        super().__init__(supabase_client)
        self.base_strategy = base_strategy

    def is_enabled(self) -> bool:
        """Check if agentic RAG is enabled via configuration."""
        from src.server.services.search.rag_config import get_bool_setting

        return get_bool_setting("USE_AGENTIC_RAG", False)

    async def search_code_examples(
        self,
        query: str,
        match_count: int = 10,
        filter_metadata: dict[str, Any] | None = None,
        source_id: str | None = None,
        use_enhancement: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Search for code examples using vector similarity.

        Args:
            query: Search query text
            match_count: Maximum number of results to return
            filter_metadata: Optional metadata filter
            source_id: Optional source ID to filter results

        Returns:
            List of matching code examples
        """
        with safe_span("agentic_code_search", query_length=len(query), match_count=match_count) as span:
            try:
                # Create embedding for the query (no enhancement)
                query_embedding = await create_embedding(query)

                if not query_embedding:
                    logger.error("Failed to create embedding for code example query")
                    return []

                # Prepare filters
                combined_filter = filter_metadata or {}
                if source_id:
                    combined_filter["source"] = source_id

                # Use base strategy for vector search
                results = cast(
                    list[dict[str, Any]],
                    await self.base_strategy.vector_search(
                        query_embedding=query_embedding,
                        match_count=match_count,
                        filter_metadata=combined_filter,
                        table_rpc="match_archon_code_examples",
                    ),
                )

                span.set_attribute("results_found", len(results))

                logger.debug(f"Agentic code search found {len(results)} results for query: {query[:50]}...")

                return results

            except Exception as e:
                logger.error(f"Error in agentic code example search: {e}")
                span.set_attribute("error", str(e))
                return []

    async def perform_agentic_search(
        self,
        query: str,
        source_id: str | None = None,
        match_count: int = 5,
        include_context: bool = True,
    ) -> tuple[bool, dict[str, Any]]:
        """
        Perform a comprehensive agentic RAG search for code examples with enhanced formatting.

        Args:
            query: The search query
            source_id: Optional source ID to filter results
            match_count: Maximum number of results to return
            include_context: Whether to include contextual information in results

        Returns:
            Tuple of (success, result_dict)
        """
        with safe_span(
            "agentic_rag_search",
            query_length=len(query),
            source_id=source_id,
            match_count=match_count,
        ) as span:
            try:
                # Check if agentic RAG is enabled
                if not self.is_enabled():
                    return False, {
                        "error": "Agentic RAG (code example extraction) is disabled. Enable USE_AGENTIC_RAG setting to use this feature.",
                        "query": query,
                    }

                # Prepare filter if source is provided
                filter_metadata = None
                if source_id and source_id.strip():
                    filter_metadata = {"source": source_id}

                # Perform code example search
                results = await self.search_code_examples(
                    query=query,
                    match_count=match_count,
                    filter_metadata=filter_metadata,
                    source_id=source_id,
                    use_enhancement=True,
                )

                # Format results for API response
                formatted_results = []
                for result in results:
                    formatted_result = {
                        "url": result.get("url"),
                        "code": result.get("content"),
                        "summary": result.get("summary"),
                        "metadata": result.get("metadata", {}),
                        "source_id": result.get("source_id"),
                        "similarity": result.get("similarity", 0.0),
                    }

                    # Add additional context if requested
                    if include_context:
                        from src.server.services.search.result_formatters import extract_code_context

                        formatted_result["chunk_number"] = result.get("chunk_number")
                        formatted_result["context"] = extract_code_context(result)

                    formatted_results.append(formatted_result)

                response_data = {
                    "query": query,
                    "source_filter": source_id,
                    "search_mode": "agentic_rag",
                    "strategy": "enhanced_code_search",
                    "results": formatted_results,
                    "count": len(formatted_results),
                    "enhanced_query_used": True,
                }

                span.set_attribute("results_returned", len(formatted_results))
                span.set_attribute("success", True)

                logger.info(f"Agentic RAG search completed - {len(formatted_results)} code examples found")

                return True, response_data

            except Exception as e:
                logger.error(f"Agentic RAG search failed: {e}")
                span.set_attribute("error", str(e))
                span.set_attribute("success", False)

                return False, {
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "query": query,
                    "source_filter": source_id,
                    "search_mode": "agentic_rag",
                }


# Utility functions for standalone usage
def create_agentic_rag_strategy(supabase_client: Client) -> AgenticRAGStrategy:
    """Create an agentic RAG strategy instance."""
    from .base_search_strategy import BaseSearchStrategy

    base_strategy = BaseSearchStrategy(supabase_client)
    return AgenticRAGStrategy(supabase_client, base_strategy)


async def search_code_examples_agentic(
    client: Client,
    query: str,
    match_count: int = 10,
    filter_metadata: dict[str, Any] | None = None,
    source_id: str | None = None,
) -> list[dict[str, Any]]:
    """
    Standalone function for agentic code example search.

    Args:
        client: Supabase client
        query: Search query
        match_count: Number of results to return
        filter_metadata: Optional metadata filter
        source_id: Optional source filter

    Returns:
        List of code example results
    """
    strategy = create_agentic_rag_strategy(client)
    return await strategy.search_code_examples(query, match_count, filter_metadata, source_id)


if TYPE_CHECKING:
    from src.server.services.search.query_analyzer import CodeQueryAnalysisResult

def analyze_query_for_code_search(query: str) -> "CodeQueryAnalysisResult":
    """
    Standalone function to analyze if a query is code-related.

    Args:
        query: Query to analyze

    Returns:
        CodeQueryAnalysisResult: Analysis results
    """
    from src.server.services.search.query_analyzer import analyze_code_query

    return analyze_code_query(query)
