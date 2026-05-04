"""
Retry Utilities for AI Services

Provides exponential backoff and jitter for resilient API calls.
"""
import asyncio
import functools
import random
from collections.abc import Callable
from typing import Any, TypeVar

from ..config.logfire_config import get_logger

logger = get_logger("retry_utils")

T = TypeVar("T")

def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
):
    """
    Decorator for retrying async functions with exponential backoff.

    Args:
        max_retries: Maximum number of retries (0 means try once).
        initial_delay: Delay before the first retry in seconds.
        backoff_factor: Multiplier for the delay after each retry.
        jitter: Whether to add random noise to the delay.
        retryable_exceptions: Tuple of exceptions that should trigger a retry.
    """
    def decorator(func: Callable[..., Any]):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            delay = initial_delay
            last_err = None
            for i in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_err = e
                    if i == max_retries:
                        break

                    err_msg = str(e).lower()
                    # Identify 429/503 errors specifically
                    if "429" in err_msg or "rate limit" in err_msg:
                        logger.warning(f"Rate limit (429) hit. Retry {i+1}/{max_retries} in {delay:.1f}s")
                    elif "503" in err_msg or "overloaded" in err_msg:
                        logger.warning(f"Server overloaded (503) hit. Retry {i+1}/{max_retries} in {delay:.1f}s")
                    else:
                        logger.warning(f"Operation failed ({type(e).__name__}): {e}. Retry {i+1}/{max_retries} in {delay:.1f}s")

                    await asyncio.sleep(delay)
                    delay *= backoff_factor
                    if jitter:
                        delay += random.uniform(0, 0.1 * delay)

            if last_err is not None:
                logger.error(f"Operation failed after {max_retries} retries: {last_err}")
                raise last_err
            raise RuntimeError("Operation failed unexpectedly")
        return wrapper
    return decorator
