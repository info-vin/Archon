import logging
import os
from typing import Any

import pydantic_ai
from pydantic_ai import Agent

from src.server.utils.retry_utils import retry_with_backoff

from .state import SharedState

logger = logging.getLogger(__name__)

PAI_V1 = not pydantic_ai.__version__.startswith("0.")

# --- Resilience Helpers (Phase 5.4.4) ---
async def _run_agent_with_retry(agent: Agent[Any, Any], prompt: str, ctx_state: SharedState, model_name: str, deps: Any = None) -> Any:
    """
    Executes an agent run with exponential backoff for 503/429 errors.
    Supports Google API Key rotation (GEMINI_API_KEY -> GOOGLE_API_KEY).
    """

    @retry_with_backoff(max_retries=5, initial_delay=2.0)
    async def _execute(override_key: str | None = None):
        if override_key:
            # Re-initialize the model with the backup key if we hit a hard quota.
            from pydantic_ai.models.gemini import GeminiModel

            # Phase 5.1.5: Version-aware Provider Selection
            if PAI_V1:
                from pydantic_ai.providers.google import GoogleProvider as ProviderClass
            else:
                from pydantic_ai.providers.google_gla import GoogleGLAProvider as ProviderClass  # type: ignore

            provider = ProviderClass(api_key=override_key)
            backup_model: Any = GeminiModel(model_name, provider=provider)  # type: ignore
            return await agent.run(prompt, model=backup_model, deps=deps)
        return await agent.run(prompt, deps=deps)
    try:
        return await _execute()
    except Exception as e:
        err_msg = str(e)
        if "429" in err_msg and ("Quota exceeded" in err_msg or "RESOURCE_EXHAUSTED" in err_msg):
            primary_key = os.getenv("GEMINI_API_KEY")
            google_key_backup = os.getenv("GOOGLE_API_KEY")

            if google_key_backup and google_key_backup != primary_key:
                logger.warning("⚠️ Primary GEMINI_API_KEY exhausted. Rotating to backup GOOGLE_API_KEY...")
                try:
                    return await _execute(override_key=google_key_backup)
                except Exception as fallback_e:
                    logger.error(f"❌ Backup GOOGLE_API_KEY also failed: {fallback_e}")
                    raise fallback_e
            else:
                logger.error(f"❌ [Hard Limit] Google API Quota exceeded and no backup rotation possible: {err_msg}")
                raise RuntimeError(f"API Daily Limit Exceeded. Details: {err_msg}") from e
        raise


def _get_output(result: Any) -> Any:
    """Compatibility helper to get result data/output across versions."""
    return getattr(result, "output", getattr(result, "data", None))


def _accumulate_usage(ctx_state: SharedState, result: Any, model_name: str):
    """Utility to safely extract and add usage tokens."""
    try:
        usage = result.usage()
        ctx_state.input_tokens += usage.request_tokens or 0
        ctx_state.output_tokens += usage.response_tokens or 0
        ctx_state.model_used = model_name
    except Exception:
        pass


def _build_pruned_history(messages: list[dict[str, Any]], max_messages: int = 6) -> str:
    """
    Cost Optimization (Context Pruning):
    Keeps the original goal (first message) and the most recent N messages.
    Prevents token explosion on deep multi-agent recursion.
    """
    if len(messages) <= max_messages:
        pruned = messages
    else:
        # Keep the user's initial prompt [0] + the last (max_messages - 1) messages
        pruned = [messages[0]] + messages[-(max_messages - 1):]
    return "\n".join([f"{m['role']}: {m['content']}" for m in pruned])
