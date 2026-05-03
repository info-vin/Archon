import asyncio
from collections.abc import Callable
from typing import Any

from src.server.config.logfire_config import search_logger


class ProgressTracker:
    """Manages progress reporting and SSE communication for storage operations."""

    def __init__(self, progress_callback: Callable | None = None):
        self.progress_callback = progress_callback

    async def report_progress(self, message: str, progress: int, batch_info: dict[str, Any] | None = None):
        if self.progress_callback and asyncio.iscoroutinefunction(self.progress_callback):
            try:
                if batch_info:
                    await self.progress_callback("document_storage", progress, message, **batch_info)
                else:
                    await self.progress_callback("document_storage", progress, message)
            except Exception as e:
                search_logger.warning(f"Progress callback failed: {e}. Storage continuing...")

    async def embedding_progress_wrapper(self, message: str, percentage: float, current_progress: int, batch_num: int):
        # Forward rate limiting messages to the main progress callback
        if self.progress_callback and "rate limit" in message.lower():
            try:
                await self.progress_callback(
                    "document_storage",
                    current_progress,
                    message,
                    batch=batch_num,
                    type="rate_limit_wait",
                )
            except Exception as e:
                search_logger.warning(f"Progress callback failed during rate limiting: {e}")

    async def report_final_progress(self, total_contents: int, total_batches: int):
        if self.progress_callback and asyncio.iscoroutinefunction(self.progress_callback):
            try:
                await self.progress_callback(
                    "document_storage",
                    100,
                    f"Document storage completed: {total_contents} chunks stored in {total_batches} batches",
                    completed_batches=total_batches,
                    total_batches=total_batches,
                    current_batch=total_batches,
                    chunks_processed=total_contents,
                )
            except Exception as e:
                search_logger.warning(f"Progress callback failed during completion: {e}. Storage still successful.")
