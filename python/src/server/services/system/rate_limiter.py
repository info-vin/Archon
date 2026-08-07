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

    # Delays in seconds required between consecutive calls to the same tier.
    # Pro: 2 RPM -> 1 call every 30s. Use 32s for safety margin.
    # Lite: 15 RPM -> 1 call every 4s. Use 4.5s for safety margin.
    _tier_delays = {"pro": 32.0, "lite": 4.5}

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

        delay_required = cls._tier_delays.get(tier, 5.0)

        async with cls._locks[tier]:
            now = time.time()
            elapsed = now - cls._last_call_times[tier]

            if elapsed < delay_required:
                wait_time = delay_required - elapsed
                logger.info(f"🛡️ Throttler: {tier.capitalize()} quota locked. Waiting {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)

            cls._last_call_times[tier] = time.time()


global_throttler = GlobalThrottler()
