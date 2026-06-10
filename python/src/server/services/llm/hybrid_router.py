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

    def is_query_simple_and_offline(self, messages: list) -> bool:
        """Determines if a chat query is simple and offline-compatible.

        Rules:
        - Word count < 50
        - Absence of online or complex task keywords (e.g. crawl, search, fetch, live, latest, realtime, google, news, code, 寫程式)
        - The local model must be available in the hardware capability matrix.
        """
        # 1. Check if Ollama has available models
        models_info = self.capability_matrix.get("models", {})
        qwen_available = models_info.get("qwen2.5:0.5b", {}).get("available", False)
        gemma_available = models_info.get("gemma3:4b", {}).get("available", False)
        gemma_1b_available = models_info.get("gemma3:1b", {}).get("available", False)

        # If no local model is available, we cannot route to Tier 3
        if not (qwen_available or gemma_available or gemma_1b_available):
            return False

        # 2. Extract last user message
        last_user_content = ""
        for m in reversed(messages):
            if isinstance(m, dict):
                role = m.get("role", "")
                content = m.get("content", "") or ""
            else:
                role = getattr(m, "role", "")
                content = getattr(m, "content", "") or ""
            if role == "user":
                last_user_content = content
                break

        if not last_user_content:
            return False

        # 3. Check word count (Simple if < 50 words)
        words = last_user_content.split()
        if len(words) >= 50:
            return False

        # 4. Check offline keywords
        online_keywords = ["crawl", "search", "fetch", "live", "latest", "realtime", "google", "news", "code", "寫程式", "程式碼"]
        for kw in online_keywords:
            if kw in last_user_content.lower():
                return False

        return True

hybrid_router = HybridRouter()
