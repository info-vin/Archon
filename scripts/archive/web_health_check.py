#!/usr/bin/env python3
"""
Web UI Health Check Script

Performs a health check on the specified URLs with exponential backoff retries.
Used by GitHub Actions to monitor Vercel deployments.
"""

import asyncio
import httpx
import sys
from src.server.utils.retry_utils import retry_with_backoff
from src.server.config.logfire_config import get_logger

logger = get_logger("web_health_check")

# URLs to check
URLS = [
    "https://archon-jet.vercel.app/",
    "https://archon-enduser.vercel.app/"
]

@retry_with_backoff(max_retries=5, initial_delay=2.0)
async def check_url(url: str):
    """
    Checks the health status of a URL.
    Raises exception if status is not 200, triggering retry_with_backoff.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10.0)
        if response.status_code != 200:
            raise Exception(f"Health check failed for {url} with status: {response.status_code}")
        logger.info(f"✅ Health check successful for {url}")
        return True

async def main():
    results = await asyncio.gather(*(check_url(url) for url in URLS), return_exceptions=True)
    
    success = True
    for url, result in zip(URLS, results):
        if isinstance(result, Exception):
            logger.error(f"❌ Health check failed for {url}: {result}")
            success = False
            
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
