import logging
from typing import Any

from ...config.logfire_config import safe_span

logger = logging.getLogger(__name__)

async def execute_code_search_pipeline(
    rag_service: Any, query: str, source_id: str | None = None, match_count: int = 5
) -> tuple[bool, dict[str, Any]]:
    """
    Delegated implementation of search_code_examples_service from RAGService.
    """
    with safe_span(
        "code_examples_pipeline",
        query_length=len(query),
        source_id=source_id,
        match_count=match_count,
    ) as span:
        try:
            if not rag_service.agentic_strategy.is_enabled():
                return False, {
                    "error": "Code example extraction is disabled. Enable USE_AGENTIC_RAG setting to use this feature.",
                    "query": query,
                }

            use_hybrid_search = rag_service.get_bool_setting("USE_HYBRID_SEARCH", False)
            use_reranking = rag_service.get_bool_setting("USE_RERANKING", False)

            search_match_count = match_count
            if use_reranking and rag_service.reranking_strategy:
                search_match_count = match_count * 5
                logger.debug(f"Reranking enabled for code search - fetching {search_match_count} candidates")

            filter_metadata = {"source": source_id} if source_id and source_id.strip() else None

            if use_hybrid_search:
                results = await rag_service.hybrid_strategy.search_code_examples_hybrid(
                    query=query,
                    match_count=search_match_count,
                    filter_metadata=filter_metadata,
                    source_id=source_id,
                )
            else:
                results = await rag_service.agentic_strategy.search_code_examples(
                    query=query,
                    match_count=search_match_count,
                    filter_metadata=filter_metadata,
                    source_id=source_id,
                )

            if rag_service.reranking_strategy and results:
                try:
                    results = await rag_service.reranking_strategy.rerank_results(
                        query, results, content_key="content", top_k=match_count
                    )
                    logger.debug(
                        f"Code reranking applied: {search_match_count} candidates -> {len(results)} final results"
                    )
                except Exception as e:
                    logger.warning(f"Code reranking failed: {e}")
                    if len(results) > match_count:
                        results = results[:match_count]

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
                if "rerank_score" in result:
                    formatted_result["rerank_score"] = result["rerank_score"]
                formatted_results.append(formatted_result)

            response_data = {
                "query": query,
                "source_filter": source_id,
                "search_mode": "hybrid" if use_hybrid_search else "vector",
                "reranking_applied": rag_service.reranking_strategy is not None,
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
