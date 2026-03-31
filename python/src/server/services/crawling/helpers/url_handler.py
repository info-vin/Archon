
import logging
import hashlib
import re
from typing import Any, List
from urllib.parse import urljoin, urlparse
from .constants import BINARY_EXTENSIONS
from .naming import URLNamingUtil

logger = logging.getLogger(__name__)

class URLHandler:
    """
    Service for handling and normalizing URLs for crawling operations.
    
    This class provides static methods for identifying file types, transforming 
    repository URLs, and extracting human-readable display names. 
    Maintains backward compatibility by delegating to helper modules.
    """

    @staticmethod
    def is_sitemap(url: str) -> bool:
        """
        Identify if a URL is likely a sitemap based on path and file name.
        
        Args:
            url: The URL to check.
            
        Returns:
            True if it's a sitemap, False otherwise.
        """
        try:
            parsed = urlparse(url)
            # Match files like sitemap.xml, sitemap_index.xml, etc.
            return parsed.path.lower().endswith('.xml') and 'sitemap' in parsed.path.lower()
        except Exception as e:
            logger.warning(f"Error checking if URL is sitemap: {e}")
            return False

    @staticmethod
    def is_markdown(url: str) -> bool:
        """Check if a URL points to a markdown file."""
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
        """
        Check if a URL points to a binary file that shouldn't be crawled.
        Uses centralized BINARY_EXTENSIONS for maintainability.
        
        Args:
            url: URL to check.
            
        Returns:
            True if URL is a binary file, False otherwise.
        """
        try:
            # Remove query parameters and fragments
            parsed = urlparse(url)
            path = parsed.path.lower()

            # Check if the path ends with any binary extension
            for ext in BINARY_EXTENSIONS:
                if path.endswith(ext):
                    logger.debug(f"Skipping binary file: {url} (matched extension: {ext})")
                    return True

            return False
        except Exception as e:
            logger.warning(f"Error checking if URL is binary: {e}")
            return False

    @staticmethod
    def transform_github_url(url: str) -> str:
        """Delegates GitHub transformation to the naming utility."""
        return URLNamingUtil.transform_github_url(url)

    @staticmethod
    def generate_unique_source_id(url: str) -> str:
        """
        Generates a unique, consistent 16-character source ID from a URL.
        
        This uses SHA-256 to ensure that the same URL always produces 
        the same ID across different sessions.
        
        Args:
            url: The normalized URL.
            
        Returns:
            A 16-character hexadecimal string.
        """
        return hashlib.sha256(url.encode()).hexdigest()[:16]

    @staticmethod
    def extract_markdown_links(content: str, base_url: str | None = None) -> list[str]:
        """
        Extract absolute links from markdown content.
        
        Handles standard markdown [text](url) patterns and 
        converts relative links to absolute if base_url is provided.
        
        Args:
            content: The raw markdown text.
            base_url: Optional base URL for resolving relative links.
            
        Returns:
            A deduplicated list of URLs.
        """
        links = []
        # Support standard markdown links: [text](url)
        # Using a non-greedy match for the URL part
        inline_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        
        for _, link in inline_links:
            # Skip fragment-only links or obviously invalid ones
            if not link or link.startswith('#'):
                continue
                
            if base_url:
                try:
                    # Logic parity with Phase 4.6: resolve relative paths
                    link = urljoin(base_url, link)
                except Exception:
                    pass
            links.append(link)
            
        return list(set(links))

    @staticmethod
    def is_link_collection_file(url: str, content: str | None = None) -> bool:
        """
        Detects if a file is primarily a list of links (like llms.txt).
        
        Uses both filename heuristics and content density analysis 
        to determine if the file should be treated as a navigation hub.
        """
        try:
            parsed = urlparse(url)
            filename = parsed.path.split('/')[-1].lower()
            
            # Tier 1: Known filename heuristics
            if filename in ['llms.txt', 'sitemap.xml']:
                logger.info(f"Link collection detected by filename: {filename}")
                return True
            
            # Tier 2: Pattern matching for collection files
            if filename.endswith(('.txt', '.md')):
                if 'full' not in filename:
                    patterns = ['llms', 'links', 'resources', 'references']
                    if any(filename.startswith(p) for p in patterns):
                        return True
            
            # Tier 3: Content-based density analysis
            if content:
                links = URLHandler.extract_markdown_links(content, url)
                total_links = len(links)
                content_len = len(content.strip())
                
                if content_len > 0:
                    # 50 chars per link threshold (link density > 2%)
                    if total_links > 10 or (total_links > 3 and (total_links * 50 / content_len) > 1.0):
                        logger.info(f"Link collection detected by density: {total_links} links found.")
                        return True
                        
            return False
        except Exception as e:
            logger.warning(f"Error in collection detection: {e}")
            return False

    @staticmethod
    def extract_display_name(url: str) -> str:
        """Delegates display name extraction to naming utility."""
        return URLNamingUtil.extract_display_name(url)

    def is_self_link(self, link: str, base_url: str) -> bool:
        """
        Determines if a link belongs to the same domain as the base URL.
        Useful for preventing out-of-scope crawling.
        """
        try:
            base_domain = urlparse(base_url).netloc
            link_domain = urlparse(link).netloc
            # If link_domain is empty, it's likely a relative path on the same host
            return not link_domain or link_domain == base_domain
        except Exception:
            return False
