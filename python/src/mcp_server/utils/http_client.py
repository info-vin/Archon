"""
HTTP client utilities for MCP Server.

Provides consistent HTTP client configuration and API call helpers.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from urllib.parse import urljoin

import httpx

from src.server.config.service_discovery import get_api_url

from .timeout_config import get_default_timeout, get_polling_timeout

logger = logging.getLogger(__name__)


@asynccontextmanager
async def get_http_client(
    timeout: httpx.Timeout | None = None, for_polling: bool = False
) -> AsyncIterator[httpx.AsyncClient]:
    """
    Create an HTTP client with consistent configuration.
    """
    if timeout is None:
        timeout = get_polling_timeout() if for_polling else get_default_timeout()

    async with httpx.AsyncClient(timeout=timeout) as client:
        yield client


async def call_api(
    method: str,
    path: str,
    timeout: httpx.Timeout | None = None,
    for_polling: bool = False,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Consolidated helper to call backend API from MCP features.

    Args:
        method: HTTP method (GET, POST, etc.)
        path: API path (relative to base URL)
        timeout: Optional custom timeout
        for_polling: Whether this is a polling request
        **kwargs: Additional arguments for httpx request (json, params, etc.)

    Returns:
        JSON result as a dictionary
    """
    try:
        api_url = get_api_url()
        url = urljoin(api_url, path)

        async with get_http_client(timeout=timeout, for_polling=for_polling) as client:
            response = await client.request(method, url, **kwargs)

            if response.status_code in (200, 201):
                return {"success": True, **response.json()}
            else:
                error_detail = response.text
                logger.error(f"API Error {response.status_code} on {path}: {error_detail}")
                return {"success": False, "error": f"HTTP {response.status_code}: {error_detail}"}

    except Exception as e:
        logger.error(f"Failed to call API {path}: {e}")
        return {"success": False, "error": str(e)}
