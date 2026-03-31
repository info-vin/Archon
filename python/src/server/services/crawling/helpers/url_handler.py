
import hashlib
import logging
import re
from urllib.parse import urljoin, urlparse

from .constants import BINARY_EXTENSIONS
from .naming import URLNamingUtil

logger = logging.getLogger(__name__)

class URLHandler:
    """
    Service for handling and normalizing URLs for crawling operations.
    Fulfills Phase 4.6 requirement for physical URL consistency and source ID integrity.
    """

    @staticmethod
    def generate_unique_source_id(url: str) -> str:
        """
        Generates a unique, consistent 16-char source ID from a URL.
        CRITICAL: Calls canonicalize_url first to ensure physical parity.
        """
        standard_url = URLNamingUtil.canonicalize_url(url)
        return hashlib.sha256(standard_url.encode()).hexdigest()[:16]

    @staticmethod
    def is_sitemap(url: str) -> bool:
        try:
            parsed = urlparse(url)
            return parsed.path.lower().endswith('.xml') and 'sitemap' in parsed.path.lower()
        except Exception:
            return False

    @staticmethod
    def is_markdown(url: str) -> bool:
        try:
            parsed = urlparse(url)
            return parsed.path.lower().endswith(('.md', '.mdx', '.markdown'))
        except Exception:
            return False

    @staticmethod
    def is_txt(url: str) -> bool:
        """Check if a URL points to a standard text file."""
        try:
            parsed = urlparse(url)
            return parsed.path.lower().endswith('.txt')
        except Exception:
            return False

    @staticmethod
    def is_binary_file(url: str) -> bool:
        """Check if URL points to a binary file using physical extension whitelist."""
        try:
            parsed = urlparse(url)
            path = parsed.path.lower()
            for ext in BINARY_EXTENSIONS:
                if path.endswith(ext):
                    return True
            return False
        except Exception:
            return False

    @staticmethod
    def transform_github_url(url: str) -> str:
        return URLNamingUtil.transform_github_url(url)

    @staticmethod
    def extract_markdown_links(content: str, base_url: str | None = None) -> list[str]:
        """Physical link extraction from markdown content with absolute resolution."""
        links = []
        # Logic parity with Phase 4.6: [text](url)
        inline_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        for _, link in inline_links:
            if not link or link.startswith('#'):
                continue
            if base_url:
                try:
                    link = urljoin(base_url, link)
                except Exception:
                    pass
            links.append(link)
        return list(set(links))

    @staticmethod
    def is_link_collection_file(url: str, content: str | None = None) -> bool:
        """Detects if a file is primarily a list of links (density analysis)."""
        parsed = urlparse(url)
        filename = parsed.path.split('/')[-1].lower()
        if filename in ['llms.txt', 'sitemap.xml']:
            return True

        if content:
            links = URLHandler.extract_markdown_links(content, url)
            total_links = len(links)
            content_len = len(content.strip())
            if content_len > 0:
                # 50 chars per link threshold (link density > 2% logic from original)
                if total_links > 10 or (total_links > 3 and (total_links * 50 / content_len) > 1.0):
                    return True
        return False

    @staticmethod
    def extract_display_name(url: str) -> str:
        return URLNamingUtil.extract_display_name(url)

    def is_self_link(self, link: str, base_url: str) -> bool:
        """Checks if link belongs to the same domain."""
        try:
            base_domain = urlparse(base_url).netloc
            link_domain = urlparse(link).netloc
            return not link_domain or link_domain == base_domain
        except Exception:
            return False
