import asyncio
import time
from typing import cast

from ...config.logfire_config import get_logger

logger = get_logger(__name__)


# --- Mock Classes ---
class MockMessage:
    def __init__(self, content):
        self.content = content
        self.reasoning_content = None


class MockChoice:
    def __init__(self, content):
        self.message = MockMessage(content)


class MockResponse:
    def __init__(self, content):
        self.choices = [MockChoice(content)]
        self.usage = None


class MockCompletions:
    def __init__(self, provider_name):
        self.provider_name = provider_name

    async def create(self, *args, **kwargs):
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
    def __init__(self, provider_name):
        self.completions = MockCompletions(provider_name)


class MockLLMClient:
    def __init__(self, provider_name="mock"):
        self.chat = MockChat(provider_name)
        self.models = None

    async def close(self):
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

    async def aclose(self):
        await self.close()


# --- Tracking Classes ---
class UsageTrackingCompletions:
    def __init__(self, original_completions, context):
        self._original = original_completions
        self._context = context

    async def create(self, *args, **kwargs):
        import os

        from ...utils.retry_utils import retry_with_backoff

        @retry_with_backoff(max_retries=5, initial_delay=2.0)
        async def _execute(override_key: str | None = None):
            # If an override key is provided and we are using Google's endpoint via OpenAI SDK
            # The API key is usually passed in default_headers['x-goog-api-key'] or as the bearer token
            original_client = self._original._client

            # Temporary override of the client's API key for this request if needed
            original_api_key = original_client.api_key
            original_headers = getattr(original_client, 'default_headers', {})

            try:
                if override_key:
                    original_client.api_key = override_key
                    if "x-goog-api-key" in original_headers:
                        new_headers = dict(original_headers)
                        new_headers["x-goog-api-key"] = override_key
                        original_client.default_headers = new_headers

                return await self._original.create(*args, **kwargs)
            finally:
                # Restore original credentials
                if override_key:
                    original_client.api_key = original_api_key
                    original_client.default_headers = original_headers

        try:
            response = await _execute()
        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg and ("Quota exceeded" in err_msg or "RESOURCE_EXHAUSTED" in err_msg):
                provider = self._context.get("provider", "unknown")
                if provider == "google":
                    primary_key = os.getenv("GEMINI_API_KEY")
                    google_key_backup = os.getenv("GOOGLE_API_KEY")
                    if google_key_backup and google_key_backup != primary_key:
                        logger.warning("⚠️ Primary GEMINI_API_KEY exhausted in archon-server. Rotating to backup GOOGLE_API_KEY...")
                        try:
                            response = await _execute(override_key=google_key_backup)
                        except Exception as fallback_e:
                            logger.error(f"❌ Backup GOOGLE_API_KEY also failed: {fallback_e}")
                            raise fallback_e
                    else:
                        raise e
                else:
                    raise e
            else:
                raise e

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
    def __init__(self, original_chat, context):
        self._original = original_chat
        self.completions = UsageTrackingCompletions(original_chat.completions, context)

    def __getattr__(self, name):
        return getattr(self._original, name)


class UsageTrackingClient:
    def __init__(self, original_client, user_id, request_id, provider):
        self._original = original_client
        self._context = {"user_id": user_id, "request_id": request_id, "provider": provider}
        self.chat = UsageTrackingChat(original_client.chat, self._context)

    def __getattr__(self, name):
        return getattr(self._original, name)
