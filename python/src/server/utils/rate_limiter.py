import asyncio
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass

from ..config.logfire_config import get_logger

logfire_logger = get_logger("rate_limiter")


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""

    tokens_per_minute: int = 200_000  # OpenAI embedding limit
    requests_per_minute: int = 12  # Conservative limit for Gemini Free Tier (Max 15)
    max_concurrent: int = 1  # Force sequential calls to prevent concurrent 429s
    backoff_multiplier: float = 2.0  # More aggressive exponential backoff
    max_backoff: float = 60.0  # Maximum backoff delay in seconds


class RateLimiter:
    """Thread-safe rate limiter with token bucket algorithm"""

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.request_times: deque[float] = deque()
        self.token_usage: deque[tuple[float, int]] = deque()
        self.current_tokens: int = 0
        self.semaphore = asyncio.Semaphore(config.max_concurrent)
        self._lock = asyncio.Lock()

    async def acquire(self, estimated_tokens: int = 8000, progress_callback: Callable | None = None) -> bool:
        """Acquire permission to make API call with token awareness

        Args:
            estimated_tokens: Estimated number of tokens for the operation
            progress_callback: Optional async callback for progress updates during wait
        """
        while True:  # Loop instead of recursion to avoid stack overflow
            wait_time_to_sleep = None

            async with self._lock:
                now = time.time()

                # Clean old entries
                self._clean_old_entries(now)

                # Check if we can make the request
                if self._can_make_request(estimated_tokens):
                    # Record the request
                    self.request_times.append(now)
                    self.token_usage.append((now, estimated_tokens))
                    self.current_tokens += estimated_tokens
                    return True

                # Calculate wait time if we can't make the request
                wait_time = self._calculate_wait_time(estimated_tokens)
                if wait_time > 0:
                    logfire_logger.info(
                        f"Rate limiting: waiting {wait_time:.1f}s",
                        extra={
                            "tokens": estimated_tokens,
                            "current_usage": self._get_current_usage(),
                        },
                    )
                    wait_time_to_sleep = wait_time
                else:
                    return False

            # Sleep outside the lock to avoid deadlock
            if wait_time_to_sleep is not None:
                # For long waits, break into smaller chunks with progress updates
                if wait_time_to_sleep > 5 and progress_callback is not None:
                    chunks = int(wait_time_to_sleep / 5)  # 5 second chunks
                    for i in range(chunks):
                        await asyncio.sleep(5)
                        remaining = wait_time_to_sleep - (i + 1) * 5
                        if progress_callback is not None:
                            await progress_callback(
                                {
                                    "type": "rate_limit_wait",
                                    "remaining_seconds": max(0, remaining),
                                    "message": f"waiting {max(0, remaining):.1f}s more...",
                                }
                            )
                    # Sleep any remaining time
                    if wait_time_to_sleep % 5 > 0:
                        await asyncio.sleep(wait_time_to_sleep % 5)
                else:
                    await asyncio.sleep(wait_time_to_sleep)
                # Continue the loop to try again

    def _can_make_request(self, estimated_tokens: int) -> bool:
        """Check if request can be made within limits"""
        # Check request rate limit
        if len(self.request_times) >= self.config.requests_per_minute:
            return False

        # Check token usage limit
        if self.current_tokens + estimated_tokens > self.config.tokens_per_minute:
            return False

        return True

    def _clean_old_entries(self, current_time: float):
        """Remove entries older than 1 minute"""
        cutoff_time = current_time - 60

        while self.request_times and self.request_times[0] < cutoff_time:
            self.request_times.popleft()

        while self.token_usage and self.token_usage[0][0] < cutoff_time:
            _, tokens = self.token_usage.popleft()
            self.current_tokens -= tokens

    def _calculate_wait_time(self, estimated_tokens: int) -> float:
        """Calculate how long to wait before retrying"""
        if not self.request_times:
            return 0.0

        oldest_request = self.request_times[0]
        time_since_oldest = time.time() - oldest_request

        if time_since_oldest < 60:
            return 60 - time_since_oldest + 0.1

        return 0.0

    def _get_current_usage(self) -> dict[str, int]:
        """Get current usage statistics"""
        return {
            "requests": len(self.request_times),
            "tokens": self.current_tokens,
            "max_requests": self.config.requests_per_minute,
            "max_tokens": self.config.tokens_per_minute,
        }
