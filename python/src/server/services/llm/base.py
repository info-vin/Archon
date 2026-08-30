import asyncio
import time
from typing import Any, cast

from ...config.logfire_config import get_logger

logger = get_logger(__name__)


# --- Mock Classes ---
class MockMessage:
    def __init__(self, content: str) -> None:
        self.content = content
        self.reasoning_content = None


class MockChoice:
    def __init__(self, content: str) -> None:
        self.message = MockMessage(content)


class MockResponse:
    def __init__(self, content: str) -> None:
        self.choices = [MockChoice(content)]
        self.usage = None


class MockCompletions:
    def __init__(self, provider_name: str) -> None:
        self.provider_name = provider_name

    async def create(self, *args: Any, **kwargs: Any) -> Any:
        logger.info(f"MockLLMClient ({self.provider_name}) received request: {kwargs}")
        messages = kwargs.get("messages", [])
        last_user_content = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user_content = m.get("content", "")
                break

        # Original Mock Context-Aware Responses Restored
        response_content = f"✨ [Mock] Magic Content for: {last_user_content[:30]}..."
        if "pitch" in last_user_content.lower() or "job" in last_user_content.lower():
            response_content = "[ENGLISH PITCH]\nHi there, I noticed you're hiring...\n\n[CHINESE PITCH]\n您好，這是一份模擬的銷售信件..."
        elif "image" in last_user_content.lower() or "nana" in last_user_content.lower():
            response_content = "A beautiful futuristic city with glowing lights"

        return MockResponse(response_content)


class MockChat:
    def __init__(self, provider_name: str) -> None:
        self.completions = MockCompletions(provider_name)


class MockLLMClient:
    def __init__(self, provider_name: str = "mock") -> None:
        self.chat = MockChat(provider_name)
        self.models = None

    async def close(self) -> None:
        try:
            from ..token_usage_service import TokenUsageService

            # Simulation of usage logging
            asyncio.create_task(
                TokenUsageService.log_usage(
                    request_id=f"mock-{int(time.time())}",
                    user_id="mock-user-001",
                    model="mock-gpt-4",
                    provider="mock",
                    input_tokens=50,
                    output_tokens=100,
                    context_type="mock_generation",
                )
            )
        except Exception:
            pass

    async def aclose(self) -> None:
        await self.close()


# --- Tracking Classes ---
class UsageTrackingCompletions:
    def __init__(self, original_completions: Any, context: dict[str, Any]) -> None:
        self._original = original_completions
        self._context = context

    async def create(self, *args: Any, **kwargs: Any) -> Any:

        import openai

        from ...utils.retry_utils import retry_with_backoff
        from ..credential_service import credential_service

        forced_tier_str = await credential_service.get_credential("forced_fallback_tier")
        try:
            forced_tier = int(forced_tier_str) if forced_tier_str else 0
        except Exception:
            forced_tier = 0

        async def _execute_on_hf(model_name: str) -> Any:
            hf_token = await credential_service.get_credential("HF_TOKEN")
            if not hf_token:
                raise ValueError("HF_TOKEN not configured for Tier 2 fallback")
            hf_model = "google/gemma-1.1-2b-it"
            client = openai.AsyncOpenAI(api_key=hf_token, base_url="https://api-inference.huggingface.co/v1/") # 合法
            try:
                kwargs_copy = kwargs.copy()
                kwargs_copy["model"] = hf_model
                return await client.chat.completions.create(*args, **kwargs_copy)
            finally:
                await client.close()

        async def _execute_on_ollama() -> Any:
            from .clients import _get_optimal_ollama_instance
            url = await _get_optimal_ollama_instance("chat", False, None)
            client = openai.AsyncOpenAI(api_key="ollama", base_url=url)
            try:
                kwargs_copy = kwargs.copy()
                kwargs_copy["model"] = "gemma3"
                return await client.chat.completions.create(*args, **kwargs_copy)
            finally:
                await client.close()

        @retry_with_backoff(max_retries=5, initial_delay=2.0)
        async def _execute(override_key: str | None = None) -> Any:
            original_client = self._original._client
            original_api_key = original_client.api_key
            original_headers = getattr(original_client, "default_headers", {})

            try:
                if override_key:
                    original_client.api_key = override_key
                    if "x-goog-api-key" in original_headers:
                        new_headers = dict(original_headers)
                        new_headers["x-goog-api-key"] = override_key
                        original_client.default_headers = new_headers

                return await self._original.create(*args, **kwargs)
            finally:
                if override_key:
                    original_client.api_key = original_api_key
                    original_client.default_headers = original_headers

        # Scan for Lean 4 context
        is_lean = False
        proof_context = ""
        for m in kwargs.get("messages", []):
            if isinstance(m, dict):
                content = m.get("content", "") or ""
            else:
                content = getattr(m, "content", "") or ""
            if "lean 4" in content.lower() or "lake build" in content.lower() or "theorem" in content.lower():
                is_lean = True
                proof_context += content + "\n"

        retry_count = 0
        if "extra_body" in kwargs and isinstance(kwargs["extra_body"], dict):
            retry_count = kwargs["extra_body"].get("retry_count", 0)

        if forced_tier == 2:
            logger.info("Forced Tier 2 Fallback (Hugging Face) by Human Operator")
            credential_service.set_active_tier(2)
            response = await _execute_on_hf(kwargs.get("model", ""))
        elif forced_tier == 3:
            logger.info("Forced Tier 3 Fallback (Ollama) by Human Operator")
            credential_service.set_active_tier(3)
            response = await _execute_on_ollama()
        elif is_lean:
            from .hybrid_router import hybrid_router
            if hybrid_router.should_escalate_to_cloud(proof_context, retry_count):
                logger.info("Hybrid Router: Escalating Lean proof task to Tier 1 Cloud")
                try:
                    response = await _execute()
                    credential_service.set_active_tier(1)
                except Exception:
                    logger.warning("Tier 1 Cloud failed for escalated Lean task, trying Tier 3")
                    credential_service.set_active_tier(3)
                    response = await _execute_on_ollama()
            else:
                logger.info("Hybrid Router: Routing Lean proof task to Tier 3 Ollama (Local)")
                try:
                    credential_service.set_active_tier(3)
                    response = await _execute_on_ollama()
                except Exception:
                    logger.warning("Local Tier 3 failed for Lean task, falling back to Tier 1")
                    response = await _execute()
                    credential_service.set_active_tier(1)
        else:
            try:
                from .hybrid_router import hybrid_router
                if hybrid_router.is_query_simple_and_offline(kwargs.get("messages", [])):
                    logger.info("Hybrid Router: Routing simple query to Tier 3 Ollama (Local)")
                    credential_service.set_active_tier(3)
                    response = await _execute_on_ollama()
                else:
                    response = await _execute()
                    credential_service.set_active_tier(1)
            except Exception as e:
                err_msg = str(e)
                provider = self._context.get("provider", "unknown")
                logger.warning(f"Tier 1 (or simple query local) failed: {err_msg}")

                if forced_tier == 1:
                    raise e

                # Connection Error -> Go straight to Tier 3
                if isinstance(e, openai.APIConnectionError) or "connect" in err_msg.lower():
                    logger.error("Connection error. Bypassing Tier 2, falling back directly to Tier 3 (Ollama)...")
                    try:
                        credential_service.set_active_tier(3)
                        response = await _execute_on_ollama()
                    except Exception as ollama_e:
                        logger.error(f"Tier 3 (Ollama) fallback failed: {ollama_e}")
                        raise ollama_e from e
                # Authentication or Rate Limit Error -> Try Tier 2 (HF)
                elif isinstance(e, (openai.AuthenticationError, openai.RateLimitError)) or "429" in err_msg or "401" in err_msg:
                    try:
                        if provider == "google":
                            from ...config.config import get_config
                            config = get_config()
                            primary_key = config.gemini_api_key
                            google_key_backup = config.google_api_key
                            if google_key_backup and google_key_backup != primary_key:
                                logger.warning("⚠️ Primary GEMINI_API_KEY exhausted. Rotating to backup...")
                                response = await _execute(override_key=google_key_backup)
                                credential_service.set_active_tier(1)
                                return response
                    except Exception as backup_e:
                        logger.error(f"Backup key failed: {backup_e}")
                        e = backup_e

                    logger.warning("Attempting Tier 2 (Hugging Face) fallback...")
                    try:
                        credential_service.set_active_tier(2)
                        response = await _execute_on_hf(kwargs.get("model", ""))
                    except Exception as hf_e:
                        logger.error(f"Tier 2 (HF) failed: {hf_e}. Falling back to Tier 3 (Ollama)...")
                        try:
                            credential_service.set_active_tier(3)
                            response = await _execute_on_ollama()
                        except Exception as ollama_e:
                            logger.error(f"Tier 3 (Ollama) failed: {ollama_e}")
                            raise ollama_e from hf_e
                else:
                    logger.warning("Unhandled Tier 1 error. Trying Tier 3 (Ollama) fallback...")
                    try:
                        credential_service.set_active_tier(3)
                        response = await _execute_on_ollama()
                    except Exception as last_e:
                        logger.error(f"Tier 3 fallback failed: {last_e}")
                        raise e from None

        try:
            if hasattr(response, "usage") and response.usage:
                model = kwargs.get("model", "unknown")
                from ..token_usage_service import TokenUsageService

                # Use ensure_future to not block response (Restored from Original)
                asyncio.ensure_future(
                    TokenUsageService.log_usage(
                        request_id=str(self._context.get("request_id", "")),
                        user_id=cast(str | None, self._context.get("user_id")),
                        model=str(model),
                        provider=str(self._context.get("provider", "unknown")),
                        input_tokens=int(response.usage.prompt_tokens),
                        output_tokens=int(response.usage.completion_tokens),
                        context_type="llm_client_call",
                    )
                )
        except Exception as e:
            logger.warning(f"Failed to log token usage: {e}")
        return response


class UsageTrackingChat:
    def __init__(self, original_chat: Any, context: dict[str, Any]) -> None:
        self._original = original_chat
        self.completions = UsageTrackingCompletions(original_chat.completions, context)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._original, name)


class UsageTrackingClient:
    def __init__(self, original_client: Any, user_id: str | None, request_id: str, provider: str) -> None:
        self._original = original_client
        self._context = {"user_id": user_id, "request_id": request_id, "provider": provider}
        self.chat = UsageTrackingChat(original_client.chat, self._context)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._original, name)
