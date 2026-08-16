# python/src/server/services/llm/hybrid_router.py

import json
import time

from ...config.logfire_config import get_logger

logger = get_logger(__name__)

class HybridRouter:
    """Routes LLM inference queries between Tier 1 (Cloud) and Tier 3 (Local Ollama)."""

    def __init__(self) -> None:
        self._cache: dict[str, tuple[str | None, float]] = {}
        self._cache_ttl = 60  # seconds

    def _get_setting_cached(self, key: str, default: str | None = None) -> str | None:
        now = time.time()
        if key in self._cache:
            val, timestamp = self._cache[key]
            if now - timestamp < self._cache_ttl:
                return val

        try:
            from src.server.services.settings_service import SettingsService
            new_val = SettingsService().get_setting(key, default)
            val_str: str | None = str(new_val) if new_val is not None else None
            self._cache[key] = (val_str, now)
            return val_str
        except Exception as e:
            logger.error(f"Failed to fetch setting {key}: {e}")
            return default

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

        keywords = ["theorem", "lemma", "induction", "cases", "simp", "rw", "have", "show", "exact", "apply"] # 合法
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

        # Rule 3: Local hardware is extremely slow (latency_ms > DEFAULT_MODEL_LATENCY_MS * 2)
        from src.server.config.model_ssot import DEFAULT_MODEL_LATENCY_MS
        try:
            latency_str = self._get_setting_cached("local_inference_latency_ms", str(DEFAULT_MODEL_LATENCY_MS))
            if latency_str:
                latency_ms = float(latency_str)
                if latency_ms > DEFAULT_MODEL_LATENCY_MS * 2:
                    logger.info(f"Escalation Triggered: Local inference latency is too high ({latency_ms}ms)")
                    return True
        except Exception as e:
            logger.error(f"Failed to parse local inference latency: {e}")

        return False

    def is_query_simple_and_offline(self, messages: list) -> bool:
        """Determines if a chat query is simple and offline-compatible.

        Rules:
        - Word count < 50
        - Absence of online or complex task keywords (e.g. crawl, search, fetch, live, latest, realtime, google, news, code, 寫程式)
        - The local model must be available in the hardware capability matrix.
        """
        # 1. Check if Ollama has available models dynamically via SettingsService (SSOT)
        is_allowed = False
        try:
            models_setting = self._get_setting_cached("ollama_discovered_models")
            allowed_models_setting = self._get_setting_cached("offline_allowed_models", '["qwen", "gemma"]')

            allowed_models = []
            if allowed_models_setting:
                allowed_models = json.loads(allowed_models_setting)

            if models_setting:
                models_data = json.loads(models_setting)
                models_list = models_data.get("models", [])
                for m in models_list:
                    model_name = m.get("name", "").lower()
                    if any(allowed.lower() in model_name for allowed in allowed_models):
                        is_allowed = True
                        break
        except Exception as e:
            logger.error(f"Failed to check dynamic Ollama capabilities: {e}")

        # If no local model is available, we cannot route to Tier 3
        if not is_allowed:
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
