from typing import TYPE_CHECKING, Any

from src.server.services.crawling.helpers.rbac_rules import get_role_based_max_depth
from src.server.services.credential_service import credential_service

if TYPE_CHECKING:
    from ..crawling_service import CrawlingService


class URLTypeRouter:
    """
    Handles URL type detection and dispatches to appropriate crawling strategies.
    Physically isolated for Phase 4.6.16 modularization.
    """

    def __init__(self, service: "CrawlingService"):
        self.service = service

    async def crawl_by_url_type(self, url: str, request: dict[str, Any]) -> tuple:
        """
        Detect URL type and perform appropriate crawling.

        Returns:
            Tuple of (crawl_results, crawl_type)
        """
        crawl_results = []
        crawl_type = None

        if self.service.url_handler.is_txt(url) or self.service.url_handler.is_markdown(url):
            # Handle text files
            crawl_type = "llms-txt" if "llms" in url.lower() else "text_file"
            if self.service.progress_tracker:
                await self.service.progress_tracker.update(
                    status="crawling",
                    progress=10,
                    log="Detected text file, fetching content...",
                    crawl_type=crawl_type,
                    current_url=url,
                )
            crawl_results = await self.service.crawl_markdown_file(
                url,
                progress_callback=await self.service._create_crawl_progress_callback("crawling"),
                start_progress=5,
                end_progress=10,
            )
            # Check if this is a link collection file and extract links
            if crawl_results and len(crawl_results) > 0:
                content = crawl_results[0].get("markdown", "")
                if self.service.url_handler.is_link_collection_file(url, content):
                    # Extract links from the content
                    extracted_links = self.service.url_handler.extract_markdown_links(content, url)

                    # Filter out self-referential links to avoid redundant crawling
                    if extracted_links:
                        extracted_links = [
                            link for link in extracted_links if not self.service.url_handler.is_self_link(link, url)
                        ]
                        # Log filtered count if needed

                    # Filter out binary files
                    if extracted_links:
                        extracted_links = [
                            link for link in extracted_links if not self.service.url_handler.is_binary_file(link)
                        ]

                    if extracted_links:
                        batch_results = await self.service.crawl_batch_with_progress(
                            extracted_links,
                            max_concurrent=request.get("max_concurrent"),
                            progress_callback=await self.service._create_crawl_progress_callback("crawling"),
                            start_progress=10,
                            end_progress=20,
                        )
                        crawl_results.extend(batch_results)
                        crawl_type = "link_collection_with_crawled_links"

        elif self.service.url_handler.is_sitemap(url):
            # Handle sitemaps
            crawl_type = "sitemap"
            if self.service.progress_tracker:
                await self.service.progress_tracker.update(
                    status="crawling",
                    progress=10,
                    log="Detected sitemap, parsing URLs...",
                    crawl_type=crawl_type,
                    current_url=url,
                )
            sitemap_urls = await self.service.parse_sitemap(url)

            if sitemap_urls:
                crawl_results = await self.service.crawl_batch_with_progress(
                    sitemap_urls,
                    progress_callback=await self.service._create_crawl_progress_callback("crawling"),
                    start_progress=15,
                    end_progress=20,
                )

        else:
            # Handle regular webpages with recursive crawling
            crawl_type = "normal"
            user_role = request.get("user_role")
            rbac_limit = await get_role_based_max_depth(user_role, credential_service)

            requested_depth = request.get("max_depth")
            if requested_depth is not None:
                max_depth = min(int(requested_depth), rbac_limit)
            else:
                max_depth = rbac_limit

            if self.service.progress_tracker:
                await self.service.progress_tracker.update(
                    status="crawling",
                    progress=10,
                    log=f"Starting recursive crawl with max depth {max_depth}...",
                    crawl_type=crawl_type,
                    current_url=url,
                )

            crawl_results = await self.service.crawl_recursive_with_progress(
                [url],
                max_depth=max_depth,
                max_concurrent=None,
                progress_callback=await self.service._create_crawl_progress_callback("crawling"),
                start_progress=3,
                end_progress=8,
            )

        return crawl_results, crawl_type
