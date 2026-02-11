from typing import Any

import httpx
from bs4 import BeautifulSoup

from ..config.logfire_config import get_logger
from ..utils import get_supabase_client
from .rbac_service import RBACService

logger = get_logger(__name__)

class CrawlerService:
    """
    Enterprise-grade Crawler Service (Phase 4.7)
    Integrates with BeautifulSoup for static/XML parsing and
    prepared for Crawl4AI for dynamic content.
    """

    def __init__(self, user_role: str = "member"):
        self.supabase = get_supabase_client()
        self.rbac = RBACService()
        self.user_role = user_role
        self.constraints = self.rbac.get_crawler_constraints(user_role)

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }

    async def fetch_and_analyze(self, url: str) -> dict[str, Any]:
        """
        Main entry point for Charlie/Bot.
        Analyzes the URL, detects type, and returns structured data.
        """
        # 1. RBAC Domain Check
        domain = url.split("//")[-1].split("/")[0]
        allowed_domains = self.constraints.get("allowed_domains", [])

        if self.user_role.lower() not in ["admin", "system_admin"]:
            if domain not in allowed_domains:
                logger.warning(f"Crawler: Domain blocked | domain={domain}")
                return {"status": "error", "message": f"Domain '{domain}' not in whitelist."}

        # 2. Fetch
        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=30.0, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()

                content_type = response.headers.get("Content-Type", "").lower()

                # 3. Route to specific parsers
                if "xml" in content_type or url.endswith(".xml") or "sitemap" in url.lower():
                    return self._process_sitemap(response.text, url)
                else:
                    return self._process_html(response.text, url)

        except Exception as e:
            logger.error(f"Crawler: Execution failed for {url} | error={e}")
            return {"status": "error", "message": str(e)}

    def _process_html(self, html: str, url: str) -> dict[str, Any]:
        """Parses standard HTML pages."""
        soup = BeautifulSoup(html, "html.parser")

        # Metadata
        title = soup.title.string if soup.title else url

        # Clean text
        for s in soup(["script", "style", "nav", "footer"]):
            s.decompose()
        text = soup.get_text(separator=" ", strip=True)

        return {
            "status": "success",
            "type": "page",
            "title": title.strip() if title else url,
            "content": text,
            "url": url,
            "is_batch": False
        }

    def _process_sitemap(self, xml: str, url: str) -> dict[str, Any]:
        """
        Parses Sitemap XML and returns a list of discovered URLs.
        """
        soup = BeautifulSoup(xml, features="xml")
        links = [loc.text.strip() for loc in soup.find_all("loc")]

        return {
            "status": "success",
            "type": "sitemap",
            "title": f"Sitemap: {url}",
            "content": f"Discovered {len(links)} links in sitemap. Ready for batch ingestion.",
            "url": url,
            "discovered_links": links,
            "is_batch": True
        }
