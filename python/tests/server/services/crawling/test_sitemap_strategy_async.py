
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from src.server.services.crawling.strategies.sitemap import SitemapCrawlStrategy

@pytest.mark.asyncio
async def test_parse_sitemap_success():
    """Test successful sitemap parsing."""
    strategy = SitemapCrawlStrategy()
    sitemap_url = "http://example.com/sitemap.xml"
    xml_content = b"""<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url><loc>http://example.com/page1</loc></url>
        <url><loc>http://example.com/page2</loc></url>
    </urlset>"""

    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = xml_content

    # Mock httpx.AsyncClient
    with patch("httpx.AsyncClient") as MockClient:
        mock_client_instance = AsyncMock()
        MockClient.return_value.__aenter__.return_value = mock_client_instance
        mock_client_instance.get.return_value = mock_response

        urls = await strategy.parse_sitemap(sitemap_url)

        assert len(urls) == 2
        assert "http://example.com/page1" in urls
        assert "http://example.com/page2" in urls

        # Verify get was called with correct URL
        mock_client_instance.get.assert_called_once_with(sitemap_url)

@pytest.mark.asyncio
async def test_parse_sitemap_http_error():
    """Test handling of HTTP errors (non-200 status)."""
    strategy = SitemapCrawlStrategy()
    sitemap_url = "http://example.com/sitemap.xml"

    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.content = b""

    with patch("httpx.AsyncClient") as MockClient:
        mock_client_instance = AsyncMock()
        MockClient.return_value.__aenter__.return_value = mock_client_instance
        mock_client_instance.get.return_value = mock_response

        urls = await strategy.parse_sitemap(sitemap_url)

        assert urls == []
        mock_client_instance.get.assert_called_once_with(sitemap_url)

@pytest.mark.asyncio
async def test_parse_sitemap_cancellation():
    """Test that cancellation check is called."""
    strategy = SitemapCrawlStrategy()
    sitemap_url = "http://example.com/sitemap.xml"
    cancellation_check = MagicMock()

    # Mock response to avoid actual network call if check passes (it won't in this test logic, but good practice)
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"<root></root>"

    with patch("httpx.AsyncClient") as MockClient:
        mock_client_instance = AsyncMock()
        MockClient.return_value.__aenter__.return_value = mock_client_instance
        mock_client_instance.get.return_value = mock_response

        await strategy.parse_sitemap(sitemap_url, cancellation_check=cancellation_check)

        cancellation_check.assert_called_once()

@pytest.mark.asyncio
async def test_parse_sitemap_request_error():
    """Test handling of httpx RequestError."""
    import httpx
    strategy = SitemapCrawlStrategy()
    sitemap_url = "http://example.com/sitemap.xml"

    with patch("httpx.AsyncClient") as MockClient:
        mock_client_instance = AsyncMock()
        MockClient.return_value.__aenter__.return_value = mock_client_instance
        # Simulate a network error
        mock_client_instance.get.side_effect = httpx.RequestError("Network Error")

        urls = await strategy.parse_sitemap(sitemap_url)

        assert urls == []

@pytest.mark.asyncio
async def test_parse_sitemap_xml_parse_error():
    """Test handling of invalid XML content."""
    strategy = SitemapCrawlStrategy()
    sitemap_url = "http://example.com/sitemap.xml"

    # Invalid XML
    xml_content = b"NOT XML"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = xml_content

    with patch("httpx.AsyncClient") as MockClient:
        mock_client_instance = AsyncMock()
        MockClient.return_value.__aenter__.return_value = mock_client_instance
        mock_client_instance.get.return_value = mock_response

        urls = await strategy.parse_sitemap(sitemap_url)

        # Should handle error gracefully and return empty list
        assert urls == []
