from typing import Any

from ...config.logfire_config import get_logger, safe_span

logger = get_logger(__name__)

async def execute_rag_pipeline(
    rag_service: Any,
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
            use_hybrid_search = rag_service.get_bool_setting("USE_HYBRID_SEARCH", False)
            use_reranking = rag_service.get_bool_setting("USE_RERANKING", False)

            search_match_count = match_count
            if use_reranking and rag_service.reranking_strategy:
                search_match_count = match_count * 5
                logger.debug(
                    f"Reranking enabled - fetching {search_match_count} candidates for {match_count} final results"
                )

            # Step 0: Web Research (if enabled)
            enable_web_research = filter_metadata.get("enable_web_research") if filter_metadata else False
            if not enable_web_research:
                enable_web_research = rag_service.get_bool_setting("ENABLE_WEB_RESEARCH", False)

            web_research_results = []
            if enable_web_research:
                try:
                    web_content, source_id = await rag_service.perform_web_research(query)
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
            results = await rag_service.search_documents(
                query=query,
                match_count=search_match_count,
                filter_metadata=final_filter,
                use_hybrid_search=use_hybrid_search,
                min_score=min_score,
            )

            # Merge web research results
            if web_research_results:
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

                    # Policy Boosting
                    if "policy" in res_metadata.get("tags", []):
                        boosted_score = min(1.0, base_score + 0.15)
                        logger.info(f"RAG: Applying Policy Boost | score {base_score:.3f} -> {boosted_score:.3f}")
                        base_score = boosted_score

                    formatted_result = {
                        "id": result.get("id", f"result_{i}"),
                        "content": result.get("content", "")[:1000],
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
                use_reranking = rag_service.get_bool_setting("USE_RERANKING", False)
                if use_reranking:
                    if rag_service.agents_enabled:
                        from src.server.services.search.remote_rerank_service import execute_remote_rerank
                        formatted_results = await execute_remote_rerank(
                            agents_url=rag_service.agents_url,
                            query=query,
                            results=formatted_results,
                            content_key="content",
                            top_k=match_count,
                            fallback_strategy=rag_service.reranking_strategy
                        )
                        reranking_applied = True
                    elif rag_service.reranking_strategy:
                        try:
                            formatted_results = await rag_service.reranking_strategy.rerank_results(
                                query, formatted_results, content_key="content", top_k=match_count
                            )
                            reranking_applied = True
                            logger.debug(
                                f"Reranking applied: {search_match_count} candidates -> {len(formatted_results)} final results"
                            )
                        except Exception as e:
                            logger.warning(f"Reranking failed: {e}")
                            reranking_applied = False
                            if len(formatted_results) > match_count:
                                formatted_results = formatted_results[:match_count]
                elif len(formatted_results) > match_count:
                    formatted_results = formatted_results[:match_count]

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
