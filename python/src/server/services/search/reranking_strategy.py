"""
Reranking Strategy

Implements result reranking using CrossEncoder models to improve search result ordering.
The reranking process re-scores search results based on query-document relevance using
a trained neural model, typically improving precision over initial retrieval scores.

Uses the cross-encoder/ms-marco-MiniLM-L-6-v2 model for reranking by default.
"""

from typing import Any

try:
    from sentence_transformers import CrossEncoder

    CROSSENCODER_AVAILABLE = True
except ImportError:
    CrossEncoder = None
    CROSSENCODER_AVAILABLE = False

from ...config.logfire_config import get_logger, safe_span

logger = get_logger(__name__)

# Default reranking model
DEFAULT_RERANKING_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


class RerankingStrategy:
    """Strategy class implementing result reranking using CrossEncoder models"""

    def __init__(self, model_name: str = DEFAULT_RERANKING_MODEL, model_instance: Any | None = None):
        """
        Initialize reranking strategy.

        Args:
            model_name: Name/path of the CrossEncoder model to use
            model_instance: Pre-loaded CrossEncoder instance or any object with a predict method (optional)
        """
        self.model_name = model_name
        self.model = model_instance or self._load_model()

    @classmethod
    def from_model(cls, model: Any, model_name: str = "custom_model") -> "RerankingStrategy":
        """
        Create a RerankingStrategy from any model with a predict method.

        This factory method is useful for tests or when using non-CrossEncoder models.

        Args:
            model: Any object with a predict(pairs) method
            model_name: Optional name for the model

        Returns:
            RerankingStrategy instance using the provided model
        """
        return cls(model_name=model_name, model_instance=model)

    def _load_model(self) -> Any:
        """Load the CrossEncoder model for reranking."""
        import os
        agents_enabled = os.getenv("AGENTS_ENABLED", "false").lower() == "true"

        if not CROSSENCODER_AVAILABLE:
            if not agents_enabled:
                logger.warning("sentence-transformers not available - reranking disabled")
            else:
                logger.info("Local sentence-transformers not available, but Neural Bridge (Agents) is enabled.")
            return None

        try:
            logger.info(f"Loading reranking model: {self.model_name}")
            return CrossEncoder(self.model_name)
        except Exception as e:
            logger.error(f"Failed to load reranking model {self.model_name}: {e}")
            return None

    def is_available(self) -> bool:
        """Check if reranking is available (model loaded successfully or remote agents enabled)."""
        import os
        agents_enabled = os.getenv("AGENTS_ENABLED", "false").lower() == "true"
        return self.model is not None or agents_enabled

    def build_query_document_pairs(
        self, query: str, results: list[dict[str, Any]], content_key: str = "content"
    ) -> tuple[list[list[str]], list[int]]:
        """
        Build query-document pairs for the reranking model.

        Args:
            query: The search query
            results: List of search results
            content_key: The key in each result dict containing text content

        Returns:
            Tuple of (query-document pairs, valid indices)
        """
        texts = []
        valid_indices = []

        for i, result in enumerate(results):
            content = result.get(content_key, "")
            if content and isinstance(content, str):
                texts.append(content)
                valid_indices.append(i)
            else:
                logger.warning(f"Result {i} has no valid content for reranking")

        query_doc_pairs = [[query, text] for text in texts]
        return query_doc_pairs, valid_indices

    def apply_rerank_scores(
        self,
        results: list[dict[str, Any]],
        scores: list[float],
        valid_indices: list[int],
        top_k: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Apply reranking scores to results and sort them.

        Args:
            results: List of search results
            scores: Reranking scores
            valid_indices: Indices of results that were reranked
            top_k: Maximum number of results to return (optional)

        Returns:
            Reranked and sorted results
        """
        # Create a new list for ranked results
        reranked_results = []

        # Map scores back to original results
        for score_idx, original_idx in enumerate(valid_indices):
            result = results[original_idx].copy()
            result["rerank_score"] = float(scores[score_idx])
            reranked_results.append(result)

        # Handle results that couldn't be reranked (keep them at the bottom if needed)
        # For now, we only return results that were successfully reranked

        # Sort by rerank score descending
        reranked_results.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)

        if top_k:
            reranked_results = reranked_results[:top_k]

        return reranked_results

    async def rerank_results(
        self, query: str, results: list[dict[str, Any]], top_k: int | None = None, **kwargs
    ) -> list[dict[str, Any]]:
        """
        Asynchronously rerank search results. Main interface for the strategy.
        Supports extra arguments like content_key for backward compatibility.

        Args:
            query: The search query
            results: List of results to rerank
            top_k: Number of results to return (optional)
            **kwargs: Additional parameters (e.g. content_key)

        Returns:
            Sorted and reranked results
        """
        if not self.is_available() or not results:
            return results

        try:
            content_key = kwargs.get("content_key", "content")
            # 1. Build pairs
            pairs, valid_indices = self.build_query_document_pairs(query, results, content_key=content_key)

            if not pairs:
                return results

            # 2. Get scores from model - Offload to thread to keep event loop free
            if self.model is None:
                logger.info("Local model is None, skipping local reranking (Remote Agents mode).")
                return results[:top_k] if top_k else results

            import asyncio
            scores = await asyncio.to_thread(self.model.predict, pairs)

            # 3. Apply and sort
            return self.apply_rerank_scores(results, list(scores), valid_indices, top_k)
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            return results

    async def rerank_results_async(
        self, query: str, results: list[dict[str, Any]], top_k: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Asynchronously rerank search results.

        Args:
            query: The search query
            results: List of results to rerank
            top_k: Number of results to return (optional)

        Returns:
            Sorted and reranked results
        """
        if not self.is_available() or not results:
            return results

        with safe_span("rerank_results", query=query, result_count=len(results)) as span:
            try:
                # 1. Build pairs
                pairs, valid_indices = self.build_query_document_pairs(query, results)

                if not pairs:
                    return results

                # 2. Get scores from model
                # Predict is typically a heavy blocking operation, but we're in an async context
                # For heavy models, this should be offloaded to a thread pool
                import asyncio

                scores = await asyncio.to_thread(self.model.predict, pairs)

                # 3. Apply and sort
                ranked_results = self.apply_rerank_scores(results, list(scores), valid_indices, top_k)

                if span:
                    span.set_attribute("top_score", ranked_results[0].get("rerank_score") if ranked_results else 0)

                return ranked_results
            except Exception as e:
                logger.error(f"Reranking failed: {e}")
                return results


# --- Singleton Pattern for Performance Optimization ---
# Pre-initialize the strategy instance to avoid re-loading the model on every request.
# Phase 4.6.25: Enables system-wide pre-loading.
reranking_strategy = RerankingStrategy()
