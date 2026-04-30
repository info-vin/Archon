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
        self.agents_enabled = self.get_bool_setting("AGENTS_ENABLED", False)
        self.agents_url = os.getenv("AGENTS_SERVICE_URL", "http://archon-agents:8052")

        # Initialize reranking strategy based on settings
        self.reranking_strategy = None
        use_reranking = self.get_bool_setting("USE_RERANKING", False)
        if use_reranking:
            # Physical Optimization: Use the singleton to avoid 15s loading delay
            self.reranking_strategy = reranking_strategy
            if not self.reranking_strategy.is_available():
                logger.warning("Reranking singleton is not available (model failed to load)")
                self.reranking_strategy = None
            else:
                logger.info("Reranking strategy attached from singleton")

    def get_setting(self, key: str, default: str = "false") -> str:
        """Get a setting from the credential service or fall back to environment variable."""
        try:
            from ..credential_service import credential_service

            if hasattr(credential_service, "_cache") and credential_service._cache_initialized:
                cached_value = credential_service._cache.get(key)
                if isinstance(cached_value, dict) and cached_value.get("is_encrypted"):
                    encrypted_value = cached_value.get("encrypted_value")
                    if encrypted_value:
                        try:
                            return credential_service._decrypt_value(encrypted_value)
                        except Exception:
                            pass
                elif cached_value:
                    return str(cached_value)
            # Fallback to environment variable
            return os.getenv(key, default)
        except Exception:
            return os.getenv(key, default)

    def get_bool_setting(self, key: str, default: bool = False) -> bool:
        """Get a boolean setting from credential service."""
        value = self.get_setting(key, "false" if not default else "true")
        return value.lower() in ("true", "1", "yes", "on")

    async def _remote_rerank(self, query: str, results: list[dict], content_key: str, top_k: int) -> list[dict]:
        """Performs reranking via remote agents service (Phase 4.6.28)."""
        import httpx

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.agents_url}/ml/rerank",
                    json={
                        "query": query,
                        "results": results,
                        "content_key": content_key,
                        "top_k": top_k,
                    },
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        logger.info("Remote reranking successful via Agents service.")
                        from typing import Any, cast
                        return cast(list[dict[str, Any]], data.get("results", []))

                logger.warning(f"Remote rerank failed (Status {response.status_code}). Falling back...")
        except Exception as e:
            logger.warning(f"Remote rerank connection error: {e}. Falling back...")

        # Fallback to local if available, else return original
        if self.reranking_strategy:
            return await self.reranking_strategy.rerank_results(
                query, results, top_k=top_k, content_key=content_key
            )
        return results[:top_k]

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
        from .web_research_strategy import perform_web_research_impl
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
        with safe_span("rag_query_pipeline", query_length=len(query), source=source, match_count=match_count) as span:
            try:
                logger.info(f"RAG query started: {query[:100]}{'...' if len(query) > 100 else ''}")

                # Build filter metadata
                search_filter = {"source": source} if source else {}
                if filter_metadata:
                    search_filter.update(filter_metadata)

                final_filter = search_filter if search_filter else None

                # Check which strategies are enabled
                use_hybrid_search = self.get_bool_setting("USE_HYBRID_SEARCH", False)
                use_reranking = self.get_bool_setting("USE_RERANKING", False)

                search_match_count = match_count
                if use_reranking and self.reranking_strategy:
                    # Fetch 5x the requested amount when reranking is enabled
                    # The reranker will select the best from this larger pool
                    search_match_count = match_count * 5
                    logger.debug(
                        f"Reranking enabled - fetching {search_match_count} candidates for {match_count} final results"
                    )

                # Step 0: Web Research (if enabled)
                # Check setting or parameter
                enable_web_research = filter_metadata.get("enable_web_research") if filter_metadata else False
                if not enable_web_research:
                    enable_web_research = self.get_bool_setting("ENABLE_WEB_RESEARCH", False)

                web_research_results = []
                if enable_web_research:
                    try:
                        web_content, source_id = await self.perform_web_research(query)
                        if web_content:
                            web_research_results.append(
                                {
                                    "id": source_id,
                                    "content": web_content,
                                    "metadata": {"type": "web_research", "source_id": source_id},
                                    "similarity": 1.0,  # Artificially high score to ensure visibility
                                }
                            )
                            logger.info(f"Web research successful: {source_id}")
                    except Exception as e:
                        logger.warning(f"Web research failed: {e}")

                # Step 1 & 2: Get results (with hybrid search if enabled)
                results = await self.search_documents(
                    query=query,
                    match_count=search_match_count,
                    filter_metadata=final_filter,
                    use_hybrid_search=use_hybrid_search,
                    min_score=min_score,
                )

                # Merge web research results
                if web_research_results:
                    # Prepend web results
                    results = web_research_results + results

                span.set_attribute("raw_results_count", len(results))
                span.set_attribute("hybrid_search_enabled", use_hybrid_search)
                span.set_attribute("web_research_enabled", enable_web_research)

                # Format results for processing
                formatted_results = []
                for i, result in enumerate(results):
                    try:
                        res_metadata = result.get("metadata", {})
                        base_score = float(result.get("similarity") or 0.0)

                        # 1.6 - Policy Boosting: Increase score for high-authority documents
                        if "policy" in res_metadata.get("tags", []):
                            boosted_score = min(1.0, base_score + 0.15)
                            logger.info(f"RAG: Applying Policy Boost | score {base_score:.3f} -> {boosted_score:.3f}")
                            base_score = boosted_score

                        formatted_result = {
                            "id": result.get("id", f"result_{i}"),
                            "content": result.get("content", "")[:1000],  # Limit content
                            "metadata": res_metadata,
                            "similarity_score": base_score,
                        }
                        formatted_results.append(formatted_result)
                    except Exception as format_error:
                        logger.warning(f"Failed to format result {i}: {format_error}")
                        continue

                # Step 3: Apply reranking if we have a strategy or if enabled
                reranking_applied = False
                if formatted_results:
                    use_reranking = self.get_bool_setting("USE_RERANKING", False)
                    if use_reranking:
                        if self.agents_enabled:
                            formatted_results = await self._remote_rerank(
                                query, formatted_results, content_key="content", top_k=match_count
                            )
                            reranking_applied = True
                        elif self.reranking_strategy:
                            try:
                                # Pass top_k to limit results to the originally requested count
                                formatted_results = await self.reranking_strategy.rerank_results(
                                    query, formatted_results, content_key="content", top_k=match_count
                                )
                                reranking_applied = True
                                logger.debug(
                                    f"Reranking applied: {search_match_count} candidates -> {len(formatted_results)} final results"
                                )
                            except Exception as e:
                                logger.warning(f"Reranking failed: {e}")
                                reranking_applied = False
                                # If reranking fails but we fetched extra results, trim to requested count
                                if len(formatted_results) > match_count:
                                    formatted_results = formatted_results[:match_count]
                    elif len(formatted_results) > match_count:
                        # Even if reranking is off, we might have fetched match_count * 5, so trim it
                        formatted_results = formatted_results[:match_count]

                # Build response
                response_data = {
                    "results": formatted_results,
                    "query": query,
                    "source": source,
                    "match_count": match_count,
                    "total_found": len(formatted_results),
                    "execution_path": "rag_service_pipeline",
                    "search_mode": "hybrid" if use_hybrid_search else "vector",
                    "reranking_applied": reranking_applied,
                }

                span.set_attribute("final_results_count", len(formatted_results))
                span.set_attribute("reranking_applied", reranking_applied)
                span.set_attribute("success", True)

                logger.info(f"RAG query completed - {len(formatted_results)} results found")
                return True, response_data

            except Exception as e:
                logger.error(f"RAG query failed: {e}")
                span.set_attribute("error", str(e))
                span.set_attribute("success", False)

                return False, {
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "query": query,
                    "source": source,
                    "execution_path": "rag_service_pipeline",
                }

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
        from .code_search_service import execute_code_search_pipeline
        return await execute_code_search_pipeline(self, query, source_id, match_count)
