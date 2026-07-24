"""
Crawler Manager Service
"""

from typing import Optional

try:
    from crawl4ai import AsyncWebCrawler, BrowserConfig
except ImportError:
    AsyncWebCrawler = None
    BrowserConfig = None

from ..config.logfire_config import get_logger, safe_logfire_info

logger = get_logger(__name__)


class CrawlerManager:
    """Manages the global crawler instance."""

    _instance: Optional["CrawlerManager"] = None
    _crawler: AsyncWebCrawler | None = None
    _initialized: bool = False

    def __new__(cls) -> "CrawlerManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def get_crawler(self) -> AsyncWebCrawler:
        """Get or create the crawler instance."""
        if not self._initialized:
            await self.initialize()
        return self._crawler

    async def initialize(self) -> None:
        """Initialize the crawler if not already initialized."""
        if self._initialized:
            safe_logfire_info("Crawler already initialized, skipping")
            return

        try:
            safe_logfire_info("Initializing Crawl4AI crawler...")
            logger.info("=== CRAWLER INITIALIZATION START ===")

            # Check if crawl4ai is available
            if not AsyncWebCrawler or not BrowserConfig:
                logger.error("ERROR: crawl4ai not available")
                raise ImportError("crawl4ai is not installed or available")

            browser_config = BrowserConfig(
                headless=True,
                verbose=False,
                viewport_width=1920,
                viewport_height=1080,
                user_agent="Mozilla/5.0",
                browser_type="chromium",
                extra_args=["--no-sandbox"],
            )

            # Initialize crawler with the correct parameter name
            self._crawler = AsyncWebCrawler(config=browser_config)
            await self._crawler.__aenter__()
            self._initialized = True

        except Exception as e:
            self._crawler = None
            self._initialized = False
            raise Exception(f"Failed to initialize Crawl4AI crawler: {e}") from e

    async def cleanup(self) -> None:
        """Clean up the crawler resources."""
        if self._crawler and self._initialized:
            try:
                await self._crawler.__aexit__(None, None, None)
            except Exception:
                pass
            finally:
                self._crawler = None
                self._initialized = False


# Global instance management (Phase 4.6.23 Hardening)
_crawler_manager: CrawlerManager | None = None


def get_manager() -> CrawlerManager:
    """Lazy initializer for the global manager."""
    global _crawler_manager
    if _crawler_manager is None:
        _crawler_manager = CrawlerManager()
    return _crawler_manager


async def get_crawler() -> AsyncWebCrawler | None:
    """Get the global crawler instance."""
    return await get_manager().get_crawler()


async def initialize_crawler() -> None:
    """Initialize the global crawler."""
    await get_manager().initialize()


async def cleanup_crawler() -> None:
    """Clean up the global crawler."""
    await get_manager().cleanup()
