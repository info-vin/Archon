"""
Reranking Strategy

Implements result reranking using ONNX-optimized CrossEncoder models to improve search result ordering.
The reranking process re-scores search results based on query-document relevance using
a trained neural model, improving precision over initial retrieval scores.

Uses the Xenova/ms-marco-MiniLM-L-6-v2 ONNX model for 0-cost, PyTorch-free inference.
"""

import asyncio
import math
from typing import Any

from ...config.logfire_config import get_logger

logger = get_logger(__name__)

# Fallback values if dependencies are missing
ONNX_AVAILABLE = False
try:
    import numpy as np
    import onnxruntime as ort
    from huggingface_hub import hf_hub_download
    from transformers import AutoTokenizer
    ONNX_AVAILABLE = True
except ImportError:
    pass

DEFAULT_RERANKING_MODEL = "Xenova/ms-marco-MiniLM-L-6-v2"

def sigmoid(x: float) -> float:
    return 1 / (1 + math.exp(-x))

class RerankingStrategy:
    """Strategy class implementing result reranking using ONNX CrossEncoder models"""

    def __init__(self, model_name: str = DEFAULT_RERANKING_MODEL, model_instance: Any | None = None) -> None:
        """
        Initialize ONNX reranking strategy.
        """
        self.model_name = model_name
        self.tokenizer = None
        self.session = None

        if model_instance:
            self.session = model_instance
        else:
            self._load_model()

    @classmethod
    def from_model(cls, model: Any, model_name: str = "custom_model") -> "RerankingStrategy":
        return cls(model_name=model_name, model_instance=model)

    def _load_model(self) -> None:
        """Load the ONNX model and Tokenizer from Hugging Face Hub."""
        if not ONNX_AVAILABLE:
            logger.warning("ONNX/Transformers not available. Reranking will be a no-op.")
            return

        try:
            logger.info(f"Loading ONNX Reranker: {self.model_name}")
            import os
            # Sanitize HF Space environment variables that might contain non-ASCII characters
            # which breaks http.client latin-1 header encoding
            hf_env_keys = ["SPACE_TITLE", "SPACE_AUTHOR_NAME", "SPACE_REPO_NAME"]
            safe_env = {k: os.environ.pop(k) for k in hf_env_keys if k in os.environ}

            try:
                onnx_file = hf_hub_download(repo_id=self.model_name, filename="onnx/model_quantized.onnx")
                self.session = ort.InferenceSession(onnx_file, providers=['CPUExecutionProvider'])
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            finally:
                for k, v in safe_env.items():
                    os.environ[k] = v

            logger.info("ONNX Reranker loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load ONNX Reranker: {e}", exc_info=True)
            self.session = None
            self.tokenizer = None

    def is_available(self) -> bool:
        """Check if reranking is available (ONNX session loaded)."""
        return self.session is not None and self.tokenizer is not None

    def build_query_document_pairs(
        self, query: str, results: list[dict[str, Any]], content_key: str = "content"
    ) -> tuple[list[tuple[str, str]], list[int]]:
        """
        Build (query, document) pairs for the ONNX model.
        Returns:
            - pairs: list of (query, text) tuples
            - valid_indices: indices mapping back to the original results list
        """
        pairs = []
        valid_indices = []
        for i, res in enumerate(results):
            text = res.get(content_key, "").strip()
            if text:
                pairs.append((query, text))
                valid_indices.append(i)
        return pairs, valid_indices

    def apply_rerank_scores(
        self,
        results: list[dict[str, Any]],
        scores: list[float],
        valid_indices: list[int],
        top_k: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Apply scores to results, sort them, and return the top_k.
        """
        if not scores or not valid_indices:
            return results[:top_k] if top_k else results

        scored_results = []

        # Keep items that weren't scored with a score of 0
        unscored_results = [r for i, r in enumerate(results) if i not in valid_indices]
        for r in unscored_results:
            r["relevance_score"] = 0.0
            scored_results.append(r)

        # Add scored items
        for idx, score in zip(valid_indices, scores, strict=False):
            res = dict(results[idx])
            res["relevance_score"] = float(score)
            res["reranked"] = True
            scored_results.append(res)

        # Sort by relevance_score descending
        scored_results.sort(key=lambda x: x.get("relevance_score", 0.0), reverse=True)

        return scored_results[:top_k] if top_k else scored_results

    def _sync_rerank(
        self, query: str, results: list[dict[str, Any]], top_k: int | None = None
    ) -> list[dict[str, Any]]:
        """Synchronous internal method for inference."""
        if not self.is_available() or not results:
            return results[:top_k] if top_k else results

        pairs, valid_indices = self.build_query_document_pairs(query, results)
        if not pairs:
            return results[:top_k] if top_k else results

        try:
            assert self.tokenizer is not None
            assert self.session is not None

            # Tokenize
            inputs = self.tokenizer(pairs, padding=True, truncation=True, return_tensors="np")

            # Prepare ONNX inputs
            onnx_inputs = {k: v.astype(np.int64) for k, v in inputs.items()}

            # Inference
            outputs = self.session.run(None, onnx_inputs)
            logits = outputs[0]

            # Apply sigmoid to get 0-1 scores
            scores = [sigmoid(float(x[0])) for x in logits]

            return self.apply_rerank_scores(results, scores, valid_indices, top_k)

        except Exception as e:
            logger.error(f"ONNX Reranking failed: {e}", exc_info=True)
            # Graceful Fallback: return original results
            return results[:top_k] if top_k else results

    async def rerank_results(
        self, query: str, results: list[dict[str, Any]], top_k: int | None = None, **kwargs
    ) -> list[dict[str, Any]]:
        """Async interface for reranking strategy."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._sync_rerank, query, results, top_k)

    async def rerank_results_async(
        self, query: str, results: list[dict[str, Any]], top_k: int | None = None
    ) -> list[dict[str, Any]]:
        """Async interface for reranking strategy (alias)."""
        return await self.rerank_results(query, results, top_k)


# --- Singleton Pattern for Performance Optimization ---
# Pre-initialize the strategy instance to avoid re-loading the model on every request.
# Phase 4.6.25: Enables system-wide pre-loading.
reranking_strategy = RerankingStrategy()
