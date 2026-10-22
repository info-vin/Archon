from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.server.services.crawler_service import CrawlerService


@pytest.fixture
def mock_supabase():
    return MagicMock()


@pytest.fixture
def mock_rbac():
    mock = MagicMock()
    mock.get_crawler_constraints.return_value = {
        "max_depth": 2,
        "max_concurrent": 3,
        "allowed_domains": ["example.com", "docs.example.com"],
    }
    return mock


@pytest.mark.asyncio
async def test_crawler_service_blocked_domain(mock_supabase, mock_rbac):
    with patch("src.server.services.crawler_service.get_supabase_client", return_value=mock_supabase), \
         patch("src.server.services.crawler_service.RBACService", return_value=mock_rbac):
        service = CrawlerService(user_role="member")
        res = await service.fetch_and_analyze("https://unauthorized-domain.com/page")
        assert res["status"] == "error"
        assert "not in whitelist" in res.get("message", "")


@pytest.mark.asyncio
async def test_crawler_service_admin_allowed_any_domain(mock_supabase, mock_rbac):
    html_content = "<html><head><title>Test Page</title></head><body><h1>Hello World</h1></body></html>"

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.headers = {"Content-Type": "text/html"}
    mock_response.text = html_content
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response

    mock_client_cm = MagicMock()
    mock_client_cm.__aenter__.return_value = mock_client
    mock_client_cm.__aexit__.return_value = None

    with patch("src.server.services.crawler_service.get_supabase_client", return_value=mock_supabase), \
         patch("src.server.services.crawler_service.RBACService", return_value=mock_rbac), \
         patch("httpx.AsyncClient", return_value=mock_client_cm):

        service = CrawlerService(user_role="admin")
        res = await service.fetch_and_analyze("https://external-site.com/page")

        assert res["status"] == "success"
        assert res["type"] == "page"
        assert res["title"] == "Test Page"
        assert "Hello World" in res.get("content", "")


@pytest.mark.asyncio
async def test_crawler_service_sitemap_xml(mock_supabase, mock_rbac):
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
       <url>
          <loc>https://example.com/page1</loc>
       </url>
       <url>
          <loc>https://example.com/page2</loc>
       </url>
    </urlset>"""

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.headers = {"Content-Type": "application/xml"}
    mock_response.text = xml_content
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response

    mock_client_cm = MagicMock()
    mock_client_cm.__aenter__.return_value = mock_client
    mock_client_cm.__aexit__.return_value = None

    with patch("src.server.services.crawler_service.get_supabase_client", return_value=mock_supabase), \
         patch("src.server.services.crawler_service.RBACService", return_value=mock_rbac), \
         patch("httpx.AsyncClient", return_value=mock_client_cm):

        service = CrawlerService(user_role="member")
        res = await service.fetch_and_analyze("https://example.com/sitemap.xml")

        assert res["status"] == "success"
        assert res["type"] == "sitemap"
        assert res.get("is_batch") is True
        assert res.get("discovered_links") == ["https://example.com/page1", "https://example.com/page2"]


@pytest.mark.asyncio
async def test_crawler_service_http_error(mock_supabase, mock_rbac):
    mock_client = AsyncMock()
    mock_client.get.side_effect = httpx.HTTPStatusError("404 Not Found", request=MagicMock(), response=MagicMock())

    mock_client_cm = MagicMock()
    mock_client_cm.__aenter__.return_value = mock_client
    mock_client_cm.__aexit__.return_value = None

    with patch("src.server.services.crawler_service.get_supabase_client", return_value=mock_supabase), \
         patch("src.server.services.crawler_service.RBACService", return_value=mock_rbac), \
         patch("httpx.AsyncClient", return_value=mock_client_cm):

        service = CrawlerService(user_role="member")
        res = await service.fetch_and_analyze("https://example.com/nonexistent")

        assert res["status"] == "error"
        assert "404 Not Found" in res.get("message", "")
