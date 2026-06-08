# python/src/server/services/llm/hybrid_router.py

import json
import os
from typing import Any, cast

from ...config.logfire_config import get_logger

logger = get_logger(__name__)

class HybridRouter:
    """Routes LLM inference queries between Tier 1 (Cloud) and Tier 3 (Local Ollama)."""

    def __init__(self, matrix_path: str | None = None):
        if matrix_path:
            self.matrix_path = matrix_path
        else:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
            self.matrix_path = os.path.join(base_dir, ".twin", "diagnostics", "hardware_capability_matrix.json")
        self.capability_matrix = self._load_matrix()

    def _load_matrix(self) -> dict[str, Any]:
        """Loads the hardware capability matrix json."""
        if os.path.exists(self.matrix_path):
            try:
                with open(self.matrix_path, encoding="utf-8") as f:
                    return cast(dict[str, Any], json.load(f))
            except Exception as e:
                logger.error(f"Failed to load hardware capability matrix: {e}")
        return {}

    def evaluate_complexity(self, proof_context: str) -> int:
        """Estimates AST complexity / proof size.

        A simple robust heuristic:
        - Word count * 2
        - Occurrences of keywords (theorem, lemma, induction, cases, simp, rw, have, show) * 10
        - Length of hypotheses and goals.
        """
        if not proof_context:
            return 0

        words = proof_context.split()
        score = len(words) * 2

        keywords = ["theorem", "lemma", "induction", "cases", "simp", "rw", "have", "show", "exact", "apply"]
        for kw in keywords:
            score += proof_context.lower().count(kw) * 10

        return score

    def should_escalate_to_cloud(self, proof_context: str, retry_count: int = 0, threshold: int = 150) -> bool:
        """Determines if the request should be outsourced to cloud (Tier 1)."""
        # Rule 1: Too many retries (K >= 2)
        if retry_count >= 2:
            logger.info(f"Escalation Triggered: retry_count ({retry_count}) >= 2")
            return True

        # Rule 2: Proof complexity threshold exceeded (S >= threshold)
        complexity = self.evaluate_complexity(proof_context)
        if complexity >= threshold:
            logger.info(f"Escalation Triggered: AST complexity ({complexity}) >= {threshold}")
            return True

        # Rule 3: Local hardware is extremely slow (e.g. tokens_per_sec < 2.0 for gemma3:4b)
        models_info = self.capability_matrix.get("models", {})
        gemma3_info = models_info.get("gemma3:4b", {})
        if gemma3_info and gemma3_info.get("tokens_per_sec", 10.0) < 2.0:
            logger.info("Escalation Triggered: Local inference speed is too slow")
            return True

        return False

hybrid_router = HybridRouter()
