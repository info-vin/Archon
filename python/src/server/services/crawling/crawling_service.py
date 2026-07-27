"""
Crawling Service Module for Archon RAG

This module combines crawling functionality and orchestration.
It handles web crawling operations including single page crawling,
batch crawling, recursive crawling, and overall orchestration with progress tracking.
"""

import asyncio
import uuid
from collections.abc import Awaitable, Callable
from typing import Any

# Import strategies
# Import operations
from src.server.repositories.base_repository import BaseRepository

from ...config.logfire_config import get_logger, safe_logfire_info
from ...utils import get_supabase_client
from ...utils.progress.progress_tracker import ProgressTracker
from .handlers.orchestrator import CrawlOrchestrator
from .handlers.registry import (
    register_orchestration,
)
from .handlers.url_type_router import URLTypeRouter
from .helpers.site_config import SiteConfig

# Import helpers
from .helpers.url_handler import URLHandler
from .progress_mapper import ProgressMapper
from .strategies.batch import BatchCrawlStrategy
from .strategies.recursive import RecursiveCrawlStrategy
from .strategies.single_page import SinglePageCrawlStrategy
from .strategies.sitemap import SitemapCrawlStrategy

logger = get_logger(__name__)


class CrawlingService(BaseRepository):
    """
    Service class for web crawling and orchestration operations.
    Combines functionality from both CrawlingService and CrawlOrchestrationService.
    """

    def __init__(self, crawler=None, supabase_client: Any = None, progress_id=None) -> None:
        """
        Initialize the crawling service.

        Args:
            crawler: The Crawl4AI crawler instance
            supabase_client: The Supabase client for database operations
            progress_id: Optional progress ID for HTTP polling updates
        """
        super().__init__(supabase_client or get_supabase_client())
        self.crawler = crawler
        self.progress_id = progress_id
        self.progress_tracker: Any = None

        # Initialize helpers
        self.url_handler = URLHandler()
        self.site_config = SiteConfig()
        self.markdown_generator = self.site_config.get_markdown_generator()

        # Initialize strategies
        self.batch_strategy = BatchCrawlStrategy(crawler, self.markdown_generator)
        self.recursive_strategy = RecursiveCrawlStrategy(crawler, self.markdown_generator)
        self.single_page_strategy = SinglePageCrawlStrategy(crawler, self.markdown_generator)
        self.sitemap_strategy = SitemapCrawlStrategy()

        # Initialize operations
        from ..storage.document_storage import DocumentStorageFacade

        self.doc_storage_ops = DocumentStorageFacade(self.supabase_client)

        # Track progress state across all stages to prevent UI resets
        self.progress_state = {"progressId": self.progress_id} if self.progress_id else {}
        # Initialize progress mapper to prevent backwards jumps
        self.progress_mapper = ProgressMapper()
        # Initialize handlers
        self.url_type_router = URLTypeRouter(self)
        self.orchestrator = CrawlOrchestrator(self)
        # Cancellation support
        self._cancelled = False

    def set_progress_id(self, progress_id: str):
        """Set the progress ID for HTTP polling updates."""
        self.progress_id = progress_id
        if self.progress_id:
            self.progress_state = {"progressId": self.progress_id}
            # Initialize progress tracker for HTTP polling
            self.progress_tracker = ProgressTracker(progress_id, operation_type="crawl")

    def cancel(self):
        """Cancel the crawl operation."""
        self._cancelled = True
        safe_logfire_info(f"Crawl operation cancelled | progress_id={self.progress_id}")

    def is_cancelled(self) -> bool:
        """Check if the crawl operation has been cancelled."""
        return self._cancelled

    def _check_cancellation(self):
        """Check if cancelled and raise an exception if so."""
        if self._cancelled:
            raise asyncio.CancelledError("Crawl operation was cancelled by user")

    async def _create_crawl_progress_callback(self, base_status: str) -> Callable[[str, int, str], Awaitable[None]]:
        """Create a progress callback for crawling operations.

        Args:
            base_status: The base status to use for progress updates

        Returns:
            Async callback function with signature (status: str, progress: int, message: str, **kwargs) -> None
        """

        async def callback(status: str, progress: int, message: str, **kwargs):
            if self.progress_tracker:
                # Debug log what we're receiving
                safe_logfire_info(
                    f"Progress callback received | status={status} | progress={progress} | "
                    f"total_pages={kwargs.get('total_pages', 'N/A')} | processed_pages={kwargs.get('processed_pages', 'N/A')} | "
                    f"kwargs_keys={list(kwargs.keys())}"
                )

                # Update progress via tracker (stores in memory for HTTP polling)
                await self.progress_tracker.update(status=base_status, progress=progress, log=message, **kwargs)
                safe_logfire_info(
                    f"Updated crawl progress | progress_id={self.progress_id} | status={base_status} | progress={progress} | "
                    f"total_pages={kwargs.get('total_pages', 'N/A')} | processed_pages={kwargs.get('processed_pages', 'N/A')}"
                )

        return callback

    async def _handle_progress_update(self, task_id: str, update: dict[str, Any]) -> None:
        """
        Handle progress updates from background task.

        Args:
            task_id: The task ID for the progress update
            update: Dictionary containing progress update data
        """
        if self.progress_tracker:
            # Update progress via tracker for HTTP polling
            await self.progress_tracker.update(
                status=update.get("status", "processing"),
                progress=update.get("progress", update.get("percentage", 0)),  # Support both for compatibility
                log=update.get("log", "Processing..."),
                **{k: v for k, v in update.items() if k not in ["status", "progress", "percentage", "log"]},
            )

    # Simple delegation methods for backward compatibility
    async def crawl_single_page(self, url: str, retry_count: int = 3) -> dict[str, Any]:
        """Crawl a single web page."""
        return await self.single_page_strategy.crawl_single_page(
            url,
            self.url_handler.transform_github_url,
            self.site_config.is_documentation_site,
            retry_count,
        )

    async def crawl_markdown_file(
        self,
        url: str,
        progress_callback: Callable[[str, int, str], Awaitable[None]] | None = None,
        start_progress: int = 10,
        end_progress: int = 20,
    ) -> list[dict[str, Any]]:
        """Crawl a .txt or markdown file."""
        return await self.single_page_strategy.crawl_markdown_file(
            url,
            self.url_handler.transform_github_url,
            progress_callback,
            start_progress,
            end_progress,
        )

    async def parse_sitemap(self, sitemap_url: str) -> list[str]:
        """Parse a sitemap and extract URLs."""
        return await self.sitemap_strategy.parse_sitemap(sitemap_url, self._check_cancellation)

    async def crawl_batch_with_progress(
        self,
        urls: list[str],
        max_concurrent: int | None = None,
        progress_callback: Callable[[str, int, str], Awaitable[None]] | None = None,
        start_progress: int = 15,
        end_progress: int = 60,
    ) -> list[dict[str, Any]]:
        """Batch crawl multiple URLs in parallel."""
        return await self.batch_strategy.crawl_batch_with_progress(
            urls,
            self.url_handler.transform_github_url,
            self.site_config.is_documentation_site,
            max_concurrent,
            progress_callback,
            start_progress,
            end_progress,
            self._check_cancellation,  # Pass cancellation check
        )

    async def crawl_recursive_with_progress(
        self,
        start_urls: list[str],
        max_depth: int = 3,
        max_concurrent: int | None = None,
        progress_callback: Callable[[str, int, str], Awaitable[None]] | None = None,
        start_progress: int = 10,
        end_progress: int = 60,
    ) -> list[dict[str, Any]]:
        """Recursively crawl internal links from start URLs."""
        return await self.recursive_strategy.crawl_recursive_with_progress(
            start_urls,
            self.url_handler.transform_github_url,
            self.site_config.is_documentation_site,
            max_depth,
            max_concurrent,
            progress_callback,
            start_progress,
            end_progress,
            self._check_cancellation,  # Pass cancellation check
        )

    # Orchestration methods
    async def orchestrate_crawl(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        Main orchestration method - non-blocking using asyncio.create_task.

        Args:
            request: The crawl request containing url, knowledge_type, tags, max_depth, etc.

        Returns:
            Dict containing task_id and status
        """
        url = str(request.get("url", ""))
        safe_logfire_info(f"Starting background crawl orchestration | url={url}")

        # Create task ID
        task_id = self.progress_id or str(uuid.uuid4())

        # Register this orchestration service for cancellation support
        if self.progress_id:
            register_orchestration(self.progress_id, self)

        # Start the crawl as an async task in the main event loop
        asyncio.create_task(self.orchestrator.run(request, task_id))

        # Return immediately
        return {
            "task_id": task_id,
            "status": "started",
            "message": f"Crawl operation started for {url}",
            "progress_id": self.progress_id,
        }


# Alias for backward compatibility
CrawlOrchestrationService = CrawlingService
