import asyncio
import time

from ...config.logfire_config import get_logger

logger = get_logger(__name__)


class GlobalThrottler:
    """
    A leaky bucket style global throttler to prevent Free Tier rate limiting.
    Specifically designed for Gemini 3.1 Pro (2 RPM) and Flash-Lite (15 RPM).
    """

    _locks: dict[str, asyncio.Lock] = {}
    _last_call_times: dict[str, float] = {}

    @classmethod
    async def wait_for_capacity(cls, tier: str = "lite") -> None:
        """
        Wait asynchronously until enough capacity is available for the requested model tier.
        Bypasses throttling entirely if TESTING=True is set.
        """
        from src.server.config.config import get_config
        if get_config().is_testing:
            return

        if tier not in cls._locks:
            cls._locks[tier] = asyncio.Lock()
            cls._last_call_times[tier] = 0.0

        from src.server.config.model_ssot import SYSTEM_MODELS, get_delay_for_model
        model_key = "DEFAULT_PRO" if tier == "pro" else "DEFAULT_TEXT"
        active_model = SYSTEM_MODELS.get(model_key, "")

        delay_required = get_delay_for_model(active_model)

        async with cls._locks[tier]:
            now = time.time()
            elapsed = now - cls._last_call_times[tier]

            if elapsed < delay_required:
                wait_time = delay_required - elapsed
                logger.info(f"🛡️ Throttler: {tier.capitalize()} quota locked (Model: {active_model}). Waiting {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)

            cls._last_call_times[tier] = time.time()


global_throttler = GlobalThrottler()
