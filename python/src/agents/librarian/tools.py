import logging

from pydantic_ai import RunContext

from src.agents.rag_agent import RagDependencies
from src.server.services.crawling.crawling_service import CrawlingService

logger = logging.getLogger(__name__)


async def web_crawl_tool(ctx: RunContext[RagDependencies], url: str) -> str:
    """
    Crawls a specific URL to get the latest information from the web.
    Use this when internal knowledge is insufficient or outdated.
    """
    try:
        logger.info(f"🕸️ [Librarian] Crawling external URL: {url}")

        # Phase 5.1.4: Hardening - Use the global crawler instance
        from src.server.services.crawler_manager import get_crawler

        crawler = await get_crawler()

        if not crawler:
            return "Crawl failed: Browser crawler not initialized or crawl4ai not installed."

        # Initialize CrawlingService with the global crawler
        service = CrawlingService(crawler=crawler)

        result = await service.crawl_single_page(url)

        if not result.get("success", False):
            return f"Crawl failed for {url}: {result.get('error', 'Unknown error')}"

        content = result.get("markdown", "") or result.get("content", "")
        metadata = result.get("metadata", {})
        title = metadata.get("title", "Unknown Title")

        # Truncate for LLM context safety
        if len(content) > 10000:
            content = content[:10000] + "\n... (content truncated for length)"

        return f"--- Crawled Content: {title} ({url}) ---\n\n{content}"

    except Exception as e:
        logger.error(f"Error in web_crawl_tool: {e}")
        return f"Error crawling {url}: {str(e)}"
