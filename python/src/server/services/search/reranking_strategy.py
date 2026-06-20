"""
Reranking Strategy

Implements result reranking using CrossEncoder models to improve search result ordering.
The reranking process re-scores search results based on query-document relevance using
a trained neural model, typically improving precision over initial retrieval scores.

Uses the cross-encoder/ms-marco-MiniLM-L-6-v2 model for reranking by default.
"""

from typing import Any

from ..llm.models import DEFAULT_RERANKING_MODEL

try:
    from sentence_transformers import CrossEncoder

    CROSSENCODER_AVAILABLE = True
except ImportError:
    CrossEncoder: Any = None  # type: ignore
    CROSSENCODER_AVAILABLE = False

from ...config.logfire_config import get_logger, safe_span

logger = get_logger(__name__)


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
        """Compatibility placeholder: Reranking now strictly remote-only."""
        return None

    def is_available(self) -> bool:
        """Check if reranking is available (remote agents enabled)."""
        import os
        return os.getenv("AGENTS_ENABLED", "false").lower() == "true"

    def build_query_document_pairs(
        self, query: str, results: list[dict[str, Any]], content_key: str = "content"
    ) -> tuple[list[list[str]], list[int]]:
        """Placeholder interface."""
        return [], []

    def apply_rerank_scores(
        self,
        results: list[dict[str, Any]],
        scores: list[float],
        valid_indices: list[int],
        top_k: int | None = None,
    ) -> list[dict[str, Any]]:
        """Placeholder interface."""
        return results

    async def rerank_results(
        self, query: str, results: list[dict[str, Any]], top_k: int | None = None, **kwargs
    ) -> list[dict[str, Any]]:
        """Interface for remote reranking strategy."""
        return results

    async def rerank_results_async(
        self, query: str, results: list[dict[str, Any]], top_k: int | None = None
    ) -> list[dict[str, Any]]:
        """Interface for remote reranking strategy."""
        return results



# --- Singleton Pattern for Performance Optimization ---
# Pre-initialize the strategy instance to avoid re-loading the model on every request.
# Phase 4.6.25: Enables system-wide pre-loading.
reranking_strategy = RerankingStrategy()
