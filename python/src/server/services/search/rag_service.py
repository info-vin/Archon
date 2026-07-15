"""
RAG Service - Thin Coordinator

This service acts as a coordinator that delegates to specific strategy implementations.
It combines multiple RAG strategies in a pipeline fashion:

1. Base vector search
2. + Hybrid search (if enabled) - combines vector + keyword
3. + Reranking (if enabled) - reorders results using CrossEncoder
4. + Agentic RAG (if enabled) - enhanced code example search

Multiple strategies can be enabled simultaneously and work together.
"""

import os
from typing import Any

# Google GenAI for Web Grounding
from google import genai
from google.genai import types

from src.server.repositories.base_repository import BaseRepository

from ...config.logfire_config import get_logger, safe_span
from ...utils import get_supabase_client
from ..embeddings.embedding_service import create_embedding
from .agentic_rag_strategy import AgenticRAGStrategy

# Import all strategies
from .base_search_strategy import BaseSearchStrategy
from .hybrid_search_strategy import HybridSearchStrategy
from .reranking_strategy import reranking_strategy

logger = get_logger(__name__)


class RAGService(BaseRepository):
    """
    Coordinator service that orchestrates multiple RAG strategies.

    This service delegates to strategy implementations and combines them
    based on configuration settings.
    """

    def __init__(self, supabase_client=None):
        """Initialize RAG service as a coordinator for search strategies"""
        super().__init__(supabase_client or get_supabase_client())

        # Initialize base strategy (always needed)
        self.base_strategy = BaseSearchStrategy(self.supabase_client)

        # Initialize optional strategies
        self.hybrid_strategy = HybridSearchStrategy(self.supabase_client, self.base_strategy)
        self.agentic_strategy = AgenticRAGStrategy(self.supabase_client, self.base_strategy)

        # Phase 4.6.28: Neural Bridge Configuration
        from src.server.schemas.settings import RagConfig
        from src.server.services.settings_service import SettingsService
        try:
            settings_service = SettingsService(self.supabase_client)
            config = RagConfig.model_validate(settings_service.get_all_settings())
        except Exception:
            config = RagConfig()

        self.agents_enabled = config.agents_enabled
        self.agents_url = os.getenv("AGENTS_SERVICE_URL", "http://archon-agents:8052")

        # Initialize reranking strategy based on settings
        self.reranking_strategy = None
        use_reranking = config.use_reranking

        if use_reranking:
            # Physical Optimization: Use the singleton to avoid 15s loading delay
            self.reranking_strategy = reranking_strategy
            if not self.reranking_strategy.is_available():
                logger.warning("Reranking singleton is not available (model failed to load)")
                self.reranking_strategy = None
            else:
                logger.info("Reranking strategy attached from singleton")

    def get_setting(self, key: str, default: str = "false") -> str:
        """Get a setting from credential service (deprecated, use rag_config)."""
        from .rag_config import get_setting

        return get_setting(key, default)

    def get_bool_setting(self, key: str, default: bool = False) -> bool:
        """Get a boolean setting from credential service."""
        from src.server.services.search.rag_config import get_bool_setting

        return get_bool_setting(key, default)

    async def search_documents(
        self,
        query: str,
        match_count: int = 5,
        filter_metadata: dict | None = None,
        use_hybrid_search: bool = False,
        cached_api_key: str | None = None,
        min_score: float | None = None,
    ) -> list[dict[str, Any]]:
        """
        Document search with hybrid search capability.

        Args:
            query: Search query string
            match_count: Number of results to return
            filter_metadata: Optional metadata filter dict
            use_hybrid_search: Whether to use hybrid search
            cached_api_key: Deprecated parameter for compatibility

        Returns:
            List of matching documents
        """
        with safe_span(
            "rag_search_documents",
            query_length=len(query),
            match_count=match_count,
            hybrid_enabled=use_hybrid_search,
        ) as span:
            try:
                # Create embedding for the query
                query_embedding = await create_embedding(query)

                if not query_embedding:
                    logger.error("Failed to create embedding for query")
                    return []

                if use_hybrid_search:
                    # Use hybrid strategy
                    results = await self.hybrid_strategy.search_documents_hybrid(
                        query=query,
                        query_embedding=query_embedding,
                        match_count=match_count,
                        filter_metadata=filter_metadata,
                    )
                    span.set_attribute("search_mode", "hybrid")
                else:
                    # Use basic vector search from base strategy
                    results = await self.base_strategy.vector_search(
                        query_embedding=query_embedding,
                        match_count=match_count,
                        filter_metadata=filter_metadata,
                        min_score=min_score,
                    )
                    span.set_attribute("search_mode", "vector")

                span.set_attribute("results_found", len(results))
                return results

            except Exception as e:
                logger.error(f"Document search failed: {e}")
                span.set_attribute("error", str(e))
                return []

    async def search_code_examples(
        self,
        query: str,
        match_count: int = 10,
        filter_metadata: dict[str, Any] | None = None,
        source_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search for code examples - delegates to agentic strategy.

        Args:
            query: Query text
            match_count: Maximum number of results to return
            filter_metadata: Optional metadata filter
            source_id: Optional source ID to filter results

        Returns:
            List of matching code examples
        """
        return await self.agentic_strategy.search_code_examples(
            query=query,
            match_count=match_count,
            filter_metadata=filter_metadata,
            source_id=source_id,
            use_enhancement=True,
        )

    async def perform_web_research(self, query: str) -> tuple[str, str]:
        """
        Executes Google Search Grounding via Gemini.
        Returns (content, source_id).
        """
        from src.server.services.search.web_research_strategy import perform_web_research_impl

        return await perform_web_research_impl(query, genai, types)

    async def perform_rag_query(
        self,
        query: str,
        source: str | None = None,
        match_count: int = 5,
        filter_metadata: dict | None = None,
        min_score: float | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        """
        Perform a comprehensive RAG query that combines all enabled strategies.

        Pipeline:
        1. Start with vector search
        2. Apply hybrid search if enabled
        3. Apply reranking if enabled

        Args:
            query: The search query
            source: Optional source domain to filter results
            match_count: Maximum number of results to return

        Returns:
            Tuple of (success, result_dict)
        """
        from src.server.services.search.rag_pipeline_executor import execute_rag_pipeline

        return await execute_rag_pipeline(
            rag_service=self,
            query=query,
            source=source,
            match_count=match_count,
            filter_metadata=filter_metadata,
            min_score=min_score,
        )

    async def search_code_examples_service(
        self, query: str, source_id: str | None = None, match_count: int = 5
    ) -> tuple[bool, dict[str, Any]]:
        """
        Search for code examples using agentic strategy with hybrid search and reranking.

        Pipeline for code examples:
        1. Check if agentic RAG is enabled
        2. Use agentic strategy for enhanced code search
        3. Apply hybrid search if enabled
        4. Apply reranking if enabled

        Args:
            query: The search query
            source_id: Optional source ID to filter results
            match_count: Maximum number of results to return

        Returns:
            Tuple of (success, result_dict)
        """
        from src.server.services.search.code_search_service import execute_code_search_pipeline

        return await execute_code_search_pipeline(self, query, source_id, match_count)
