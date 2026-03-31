
import re
import logging
from urllib.parse import urlparse
from ....config.logfire_config import get_logger

logger = get_logger(__name__)

class URLNamingUtil:
    """
    Utilities for URL transformation and human-readable naming.
    
    This provides user-friendly names for common source patterns
    while falling back to the domain for unknown patterns.
    Fulfills Phase 4.6 requirement for physical UI alignment.
    """

    @staticmethod
    def transform_github_url(url: str) -> str:
        """
        Transform GitHub web URLs to raw content URLs for better crawling.
        
        Example: 
            https://github.com/owner/repo/blob/main/file.md 
            -> https://raw.githubusercontent.com/owner/repo/main/file.md
            
        Args:
            url: The GitHub URL to transform.
            
        Returns:
            The transformed raw content URL or the original URL if not a blob.
        """
        try:
            # Only transform blob URLs (standard view pages)
            if "github.com" not in url or "/blob/" not in url:
                return url
            
            # Transformation logic: replace domain and strip /blob/
            raw_url = url.replace("github.com", "raw.githubusercontent.com")
            raw_url = raw_url.replace("/blob/", "/")
            
            return raw_url
        except Exception as e:
            logger.warning(f"Error transforming GitHub URL {url}: {e}")
            return url

    @staticmethod
    def extract_display_name(url: str) -> str:
        """
        Extract a human-readable display name from URL.

        This creates user-friendly names for common source patterns
        while falling back to the domain for unknown patterns.

        Args:
            url: The URL to extract a display name from

        Returns:
            A human-readable string suitable for UI display
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Remove www prefix for cleaner display
            if domain.startswith("www."):
                domain = domain[4:]

            # Handle empty domain (might be a file path or malformed URL)
            if not domain:
                if url.startswith("/"):
                    return f"Local: {url.split('/')[-1] if '/' in url else url}"
                return url[:50] + "..." if len(url) > 50 else url

            path = parsed.path.strip("/")

            # Special handling for GitHub repositories and API
            if "github.com" in domain:
                # Check if it's an API endpoint
                if domain.startswith("api."):
                    return "GitHub API"

                parts = path.split("/")
                if len(parts) >= 2:
                    owner = parts[0]
                    repo = parts[1].replace(".git", "")  # Remove .git extension if present
                    return f"GitHub - {owner}/{repo}"
                elif len(parts) == 1 and parts[0]:
                    return f"GitHub - {parts[0]}"
                return "GitHub"

            # Special handling for documentation sites
            if domain.startswith("docs."):
                # Extract the service name from docs.X.com/org
                service_name = domain.replace("docs.", "").split(".")[0]
                base_name = f"{service_name.title()}" if service_name else "Documentation"

                # Special handling for special files - preserve the filename
                if path:
                    # Check for llms.txt files
                    if "llms" in path.lower() and path.endswith(".txt"):
                        return f"{base_name} - Llms.Txt"
                    # Check for sitemap files
                    elif "sitemap" in path.lower() and path.endswith(".xml"):
                        return f"{base_name} - Sitemap.Xml"
                    # Check for any other special .txt files
                    elif path.endswith(".txt"):
                        filename = path.split("/")[-1] if "/" in path else path
                        return f"{base_name} - {filename.title()}"

                return f"{base_name} Documentation" if service_name else "Documentation"

            # Handle readthedocs.io subdomains
            if domain.endswith(".readthedocs.io"):
                project = domain.replace(".readthedocs.io", "")
                return f"{project.title()} Docs"

            # Handle common documentation patterns
            doc_patterns = [
                ("fastapi.tiangolo.com", "FastAPI Documentation"),
                ("pydantic.dev", "Pydantic Documentation"),
                ("python.org", "Python Documentation"),
                ("djangoproject.com", "Django Documentation"),
                ("flask.palletsprojects.com", "Flask Documentation"),
                ("numpy.org", "NumPy Documentation"),
                ("pandas.pydata.org", "Pandas Documentation"),
            ]

            for pattern, name in doc_patterns:
                if pattern in domain:
                    # Add path context if available
                    if path and len(path) > 1:
                        # Get first meaningful path segment
                        path_segment = path.split("/")[0] if "/" in path else path
                        if path_segment and path_segment not in [
                            "docs",
                            "doc",
                            "documentation",
                            "api",
                            "en",
                        ]:
                            return f"{name} - {path_segment.title()}"
                    return name

            # For API endpoints
            if "api." in domain or "/api" in path:
                service = domain.replace("api.", "").split(".")[0]
                return f"{service.title()} API"

            # Special handling for sitemap.xml and llms.txt on any site
            if path:
                if "sitemap" in path.lower() and path.endswith(".xml"):
                    # Get base domain name
                    display = domain
                    for tld in [".com", ".org", ".io", ".dev", ".net", ".ai", ".app"]:
                        if display.endswith(tld):
                            display = display[:-len(tld)]
                            break
                    display_parts = display.replace("-", " ").replace("_", " ").split(".")
                    formatted = " ".join(part.title() for part in display_parts)
                    return f"{formatted} - Sitemap.Xml"
                elif "llms" in path.lower() and path.endswith(".txt"):
                    # Get base domain name
                    display = domain
                    for tld in [".com", ".org", ".io", ".dev", ".net", ".ai", ".app"]:
                        if display.endswith(tld):
                            display = display[:-len(tld)]
                            break
                    display_parts = display.replace("-", " ").replace("_", " ").split(".")
                    formatted = " ".join(part.title() for part in display_parts)
                    return f"{formatted} - Llms.Txt"

            # Default: Use domain with nice formatting
            display = domain
            for tld in [".com", ".org", ".io", ".dev", ".net", ".ai", ".app"]:
                if display.endswith(tld):
                    display = display[: -len(tld)]
                    break

            # Capitalize first letter of each word
            display_parts = display.replace("-", " ").replace("_", " ").split(".")
            formatted = " ".join(part.title() for part in display_parts)

            # Add path context if it's meaningful
            if path and len(path) > 1 and "/" not in path:
                formatted += f" - {path.title()}"

            return formatted

        except Exception as e:
            logger.debug(f"Error extracting display name for {url}: {e}")
            return url
