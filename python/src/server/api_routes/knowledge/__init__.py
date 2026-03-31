"""
Knowledge API Sub-Package - Domain State
"""

import asyncio

# Global state for tracking active background tasks in this domain
active_crawl_tasks: dict[str, asyncio.Task] = {}
