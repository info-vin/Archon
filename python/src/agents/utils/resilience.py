import logging
import os
from typing import Any

import pydantic_ai
from pydantic_ai import Agent

from src.server.utils.retry_utils import retry_with_backoff

logger = logging.getLogger(__name__)

# Version helper to handle PydanticAI breaking changes
PAI_V1 = not pydantic_ai.__version__.startswith("0.")

def get_pydantic_ai_output(result: Any) -> Any:
    """Compatibility helper to get result data/output across versions."""
    return getattr(result, "output", getattr(result, "data", None))

async def run_agent_with_global_resilience(agent: Agent[Any, Any], prompt: str, **run_kwargs) -> Any:
    """
    Executes a PydanticAI agent run with exponential backoff for 503/429 errors.
    Supports Google API Key rotation (GEMINI_API_KEY -> GOOGLE_API_KEY).
    This function should be used globally across all agents.
    """

    @retry_with_backoff(max_retries=5, initial_delay=2.0)
    async def _execute(override_key: str | None = None):
        if override_key:
            from pydantic_ai.models.gemini import GeminiModel
            
            # Phase 5.1.5: Version-aware Provider Selection
            if PAI_V1:
                from pydantic_ai.providers.google import GoogleProvider as ProviderClass
            else:
                from pydantic_ai.providers.google_gla import GoogleGLAProvider as ProviderClass

            provider = ProviderClass(api_key=override_key)
            # We need to recreate the model with the new provider
            # Assuming agent.model is set, but agent.model could be a string or a Model instance.
            # In PydanticAI, we can pass model=... to .run() to override.
            # We extract the model name from the agent's current model.
            model_name = getattr(agent.model, 'model_name', None)
            if not model_name:
                # If it's a string initially
                model_name = agent.model if isinstance(agent.model, str) else "gemini-3.1-flash-lite"

            backup_model: Any = GeminiModel(model_name, provider=provider)
            return await agent.run(prompt, model=backup_model, **run_kwargs)

        return await agent.run(prompt, **run_kwargs)

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
