from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from server.api_routes.pages_api import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)

@pytest.mark.asyncio
async def test_list_pages_endpoint():
    mock_pages = [
        {
            "id": "p1",
            "url": "https://example.com/page1",
            "section_title": "Section 1",
            "section_order": 1,
            "word_count": 100,
            "char_count": 500,
            "chunk_count": 2,
        }
    ]
    with patch("server.services.pages_service.pages_service.list_pages", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = mock_pages
        response = client.get("/api/pages?source_id=s123")
        assert response.status_code == 200
        data = response.json()
        assert data["source_id"] == "s123"
        assert data["total"] == 1
        assert data["pages"][0]["id"] == "p1"

@pytest.mark.asyncio
async def test_get_page_by_url_endpoint():
    mock_page = {
        "id": "p1",
        "source_id": "s123",
        "url": "https://example.com/page1",
        "full_content": "Hello World",
        "section_title": "Section 1",
        "section_order": 1,
        "word_count": 100,
        "char_count": 500,
        "chunk_count": 2,
        "metadata": {},
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z",
    }
    with patch("server.services.pages_service.pages_service.get_page_by_url", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_page
        response = client.get("/api/pages/by-url?url=https://example.com/page1")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "p1"
        assert data["full_content"] == "Hello World"

@pytest.mark.asyncio
async def test_get_page_by_id_endpoint():
    mock_page = {
        "id": "p1",
        "source_id": "s123",
        "url": "https://example.com/page1",
        "full_content": "Hello World",
        "section_title": "Section 1",
        "section_order": 1,
        "word_count": 100,
        "char_count": 500,
        "chunk_count": 2,
        "metadata": {},
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z",
    }
    with patch("server.services.pages_service.pages_service.get_page_by_id", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_page
        response = client.get("/api/pages/p1")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "p1"
