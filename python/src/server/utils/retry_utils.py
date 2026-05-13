"""
Retry Utilities for AI Services

Provides exponential backoff and jitter for resilient API calls using tenacity.
"""
import functools
from collections.abc import Callable
from typing import Any, TypeVar

from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
)

from ..config.logfire_config import get_logger

logger = get_logger("retry_utils")

T = TypeVar("T")

def _is_rate_limit_or_overloaded(e: Exception) -> bool:
    """Check if the exception is a 429 Rate Limit or 503 Overloaded error."""
    err_msg = str(e).lower()
    is_retryable = "429" in err_msg or "rate limit" in err_msg or "503" in err_msg or "overloaded" in err_msg
    if is_retryable:
        logger.warning(f"API Rate Limit/Overloaded encountered. Triggering backoff. Details: {str(e)[:100]}")
    return is_retryable

def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0, # Not directly used in tenacity's wait_exponential_jitter default kwargs easily without custom classes, but wait_exponential_jitter has its own defaults
    jitter: bool = True,
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
):
    """
    Decorator for retrying async functions with exponential backoff using tenacity.

    Args:
        max_retries: Maximum number of retries (0 means try once, effectively stop_after_attempt(1)).
        initial_delay: Delay before the first retry in seconds.
        backoff_factor: Ignored in this tenacity implementation in favor of default exponential.
        jitter: Uses tenacity's wait_exponential_jitter if True.
        retryable_exceptions: Tuple of exceptions that should trigger a retry.
    """

    # Configure tenacity retry conditions
    # Increased max to 65 to handle Gemini's 54s cooldowns for Free Tier RPM limits
    wait_strategy = wait_exponential_jitter(initial=initial_delay, max=65) if jitter else wait_exponential_jitter(initial=initial_delay, max=65, jitter=0)

    # Create a custom retry condition combining type and content checks
    def custom_retry_condition(e: BaseException) -> bool:
        if isinstance(e, retryable_exceptions) and isinstance(e, Exception):
            return _is_rate_limit_or_overloaded(e)
        return False

    tenacity_decorator = retry(
        wait=wait_strategy,
        stop=stop_after_attempt(max_retries + 1),
        retry=retry_if_exception(custom_retry_condition),
        reraise=True # Re-raise the last exception instead of RetryError
    )

    def decorator(func: Callable[..., Any]):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Apply the synchronous/asynchronous tenacity decorator transparently
            wrapped_func = tenacity_decorator(func)
            return await wrapped_func(*args, **kwargs)
        return wrapper
    return decorator
