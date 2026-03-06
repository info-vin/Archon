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
from .reranking_strategy import RerankingStrategy

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

        # Initialize reranking strategy based on settings
        self.reranking_strategy = None
        use_reranking = self.get_bool_setting("USE_RERANKING", False)
        if use_reranking:
            try:
                self.reranking_strategy = RerankingStrategy()
                logger.info("Reranking strategy loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load reranking strategy: {e}")
                self.reranking_strategy = None

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
        try:
            # Import dependencies locally to avoid cycles
            from ..credential_service import credential_service
            from ..librarian_service import LibrarianService

            # 1. Get API Key
            api_key = await credential_service.get_credential("GEMINI_API_KEY")
            if not api_key:
                api_key = await credential_service.get_credential("GOOGLE_API_KEY")

            if not api_key:
                logger.warning("No GEMINI_API_KEY found for web research")
                return "", ""

            # 2. Init Client
            # client = genai.Client(api_key=api_key) # Deprecated signature?
            # Check if we should use http_options or just pass api_key
            # Ideally use a factory or standard client if possible
            # But for GenAI SDK v1 (google-genai), initialization is:
            client = genai.Client(api_key=api_key)

            # 3. Define Tools
            google_search_tool = types.Tool(
                google_search=types.GoogleSearch()
            )

            # 4. Prompt
            prompt = f"""
            Research the following query and provide a comprehensive summary.
            Focus on factual, up-to-date information.

            Query: {query}
            """

            # 5. Generate with Grounding
            model_id = "gemini-2.0-flash" # Use a capable model
            response = client.models.generate_content(
                model=model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[google_search_tool],
                    response_modalities=["TEXT"],
                )
            )

            # 6. Extract Content & References
            content = ""
            references = []

            # Handling 2.0 SDK response structure
            if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.text:
                        content += part.text

            # Extract grounding metadata if available
            # validation of grounding metadata structure is needed, assuming standard
            if (response.candidates and response.candidates[0].grounding_metadata
                and response.candidates[0].grounding_metadata.grounding_chunks):
                for chunk in response.candidates[0].grounding_metadata.grounding_chunks:
                    if chunk.web and chunk.web.uri:
                        references.append(chunk.web.uri)

            if not content:
                logger.warning("Web research returned empty content")
                return "", ""

            # 7. Archive Result
            librarian = LibrarianService()
            source_id = await librarian.archive_web_research(query, content, references)

            return content, source_id

        except Exception as e:
            logger.error(f"Error performing web research: {e}")
            return "", ""

    async def perform_rag_query(
        self, query: str, source: str | None = None, match_count: int = 5, filter_metadata: dict | None = None, min_score: float | None = None
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
        with safe_span(
            "rag_query_pipeline", query_length=len(query), source=source, match_count=match_count
        ) as span:
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
                    logger.debug(f"Reranking enabled - fetching {search_match_count} candidates for {match_count} final results")

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
                            web_research_results.append({
                                "id": source_id,
                                "content": web_content,
                                "metadata": {"type": "web_research", "source_id": source_id},
                                "similarity": 1.0 # Artificially high score to ensure visibility
                            })
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
                if self.reranking_strategy and formatted_results:
                    try:
                        # Pass top_k to limit results to the originally requested count
                        formatted_results = await self.reranking_strategy.rerank_results(
                            query, formatted_results, content_key="content", top_k=match_count
                        )
                        reranking_applied = True
                        logger.debug(f"Reranking applied: {search_match_count} candidates -> {len(formatted_results)} final results")
                    except Exception as e:
                        logger.warning(f"Reranking failed: {e}")
                        reranking_applied = False
                        # If reranking fails but we fetched extra results, trim to requested count
                        if len(formatted_results) > match_count:
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
        with safe_span(
            "code_examples_pipeline",
            query_length=len(query),
            source_id=source_id,
            match_count=match_count,
        ) as span:
            try:
                # Check if agentic RAG is enabled
                if not self.agentic_strategy.is_enabled():
                    return False, {
                        "error": "Code example extraction is disabled. Enable USE_AGENTIC_RAG setting to use this feature.",
                        "query": query,
                    }

                # Check which strategies are enabled
                use_hybrid_search = self.get_bool_setting("USE_HYBRID_SEARCH", False)
                use_reranking = self.get_bool_setting("USE_RERANKING", False)

                # If reranking is enabled, fetch more candidates
                search_match_count = match_count
                if use_reranking and self.reranking_strategy:
                    search_match_count = match_count * 5
                    logger.debug(f"Reranking enabled for code search - fetching {search_match_count} candidates")

                # Prepare filter
                filter_metadata = {"source": source_id} if source_id and source_id.strip() else None

                if use_hybrid_search:
                    # Use hybrid search for code examples
                    results = await self.hybrid_strategy.search_code_examples_hybrid(
                        query=query,
                        match_count=search_match_count,
                        filter_metadata=filter_metadata,
                        source_id=source_id,
                    )
                else:
                    # Use standard agentic search
                    results = await self.agentic_strategy.search_code_examples(
                        query=query,
                        match_count=search_match_count,
                        filter_metadata=filter_metadata,
                        source_id=source_id,
                    )

                # Apply reranking if we have a strategy
                if self.reranking_strategy and results:
                    try:
                        results = await self.reranking_strategy.rerank_results(
                            query, results, content_key="content", top_k=match_count
                        )
                        logger.debug(f"Code reranking applied: {search_match_count} candidates -> {len(results)} final results")
                    except Exception as e:
                        logger.warning(f"Code reranking failed: {e}")
                        # If reranking fails but we fetched extra results, trim to requested count
                        if len(results) > match_count:
                            results = results[:match_count]

                # Format results
                formatted_results = []
                for result in results:
                    formatted_result = {
                        "url": result.get("url"),
                        "code": result.get("content"),
                        "summary": result.get("summary"),
                        "metadata": result.get("metadata"),
                        "source_id": result.get("source_id"),
                        "similarity": result.get("similarity"),
                    }
                    # Include rerank score if available
                    if "rerank_score" in result:
                        formatted_result["rerank_score"] = result["rerank_score"]
                    formatted_results.append(formatted_result)

                response_data = {
                    "query": query,
                    "source_filter": source_id,
                    "search_mode": "hybrid" if use_hybrid_search else "vector",
                    "reranking_applied": self.reranking_strategy is not None,
                    "results": formatted_results,
                    "count": len(formatted_results),
                }

                span.set_attribute("results_found", len(formatted_results))
                span.set_attribute("hybrid_used", use_hybrid_search)
                span.set_attribute("reranking_used", use_reranking)

                return True, response_data

            except Exception as e:
                logger.error(f"Code example search failed: {e}")
                span.set_attribute("error", str(e))
                return False, {"query": query, "error": str(e)}
