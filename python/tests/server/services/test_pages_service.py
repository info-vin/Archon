from unittest.mock import MagicMock

import pytest

from src.server.services.pages_service import PagesService


@pytest.fixture
def mock_supabase():
    client = MagicMock()
    return client

@pytest.fixture
def pages_service(mock_supabase):
    service = PagesService()
    service.supabase_client = mock_supabase
    return service

@pytest.mark.asyncio
async def test_list_pages_success(pages_service, mock_supabase):
    mock_query = MagicMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value = mock_query
    mock_query.order.return_value.order.return_value = mock_query

    mock_execute_query = MagicMock(return_value=(True, {"data": [{"id": "1", "url": "http://example.com"}]}))
    pages_service.execute_query = mock_execute_query

    result = await pages_service.list_pages(source_id="test_source")

    assert len(result) == 1
    assert result[0]["id"] == "1"

@pytest.mark.asyncio
async def test_list_pages_with_section(pages_service, mock_supabase):
    mock_query = MagicMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value = mock_query
    mock_query.eq.return_value = mock_query
    mock_query.order.return_value.order.return_value = mock_query

    mock_execute_query = MagicMock(return_value=(True, {"data": []}))
    pages_service.execute_query = mock_execute_query

    await pages_service.list_pages(source_id="test_source", section="test_section")
    mock_query.eq.assert_called_with("section_title", "test_section")

@pytest.mark.asyncio
async def test_get_page_by_url_success(pages_service, mock_supabase):
    mock_query = MagicMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value = mock_query

    mock_execute_query = MagicMock(return_value=(True, {"data": [{"id": "1", "url": "http://example.com"}]}))
    pages_service.execute_query = mock_execute_query

    result = await pages_service.get_page_by_url(url="http://example.com")
    assert result is not None
    assert result["id"] == "1"

@pytest.mark.asyncio
async def test_get_page_by_url_not_found(pages_service, mock_supabase):
    mock_query = MagicMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value = mock_query

    mock_execute_query = MagicMock(return_value=(True, {"data": []}))
    pages_service.execute_query = mock_execute_query

    result = await pages_service.get_page_by_url(url="http://example.com")
    assert result is None

@pytest.mark.asyncio
async def test_get_page_by_id_success(pages_service, mock_supabase):
    mock_query = MagicMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value = mock_query

    mock_execute_query = MagicMock(return_value=(True, {"data": [{"id": "1", "url": "http://example.com"}]}))
    pages_service.execute_query = mock_execute_query

    result = await pages_service.get_page_by_id(page_id="1")
    assert result is not None
    assert result["url"] == "http://example.com"

@pytest.mark.asyncio
async def test_get_page_by_id_not_found(pages_service, mock_supabase):
    mock_query = MagicMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value = mock_query

    mock_execute_query = MagicMock(return_value=(False, {}))
    pages_service.execute_query = mock_execute_query

    result = await pages_service.get_page_by_id(page_id="1")
    assert result is None
