from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.server.services.admin_service import admin_service


@pytest.fixture
def mock_execute_query_async():
    with patch("src.server.services.admin_service.admin_service.execute_query_async", new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
def mock_supabase_client():
    with patch("src.server.services.admin_service.admin_service.supabase_client") as mock:
        yield mock


@pytest.mark.asyncio
async def test_get_all_users(mock_execute_query_async, mock_supabase_client):
    mock_execute_query_async.return_value = (True, {"data": [{"id": "u1", "role": "admin"}, {"id": "u2", "role": "viewer"}]})
    users = await admin_service.get_all_users(limit=10)
    assert len(users) == 2
    assert users[0]["role"] == "admin"
    assert mock_execute_query_async.called


@pytest.mark.asyncio
async def test_update_user_role(mock_execute_query_async, mock_supabase_client):
    async def execute_side_effect(query, *args, **kwargs):
        if "update" in str(query):
            return (True, {"data": [{"id": "u1", "role": "manager"}]})
        return (True, {})

    mock_execute_query_async.side_effect = execute_side_effect
    mock_auth = MagicMock()
    mock_supabase_client.auth = mock_auth
    result = await admin_service.update_user_role("u1", "manager", "admin@test.com")
    assert result["role"] == "manager"
    assert mock_execute_query_async.called


@pytest.mark.asyncio
async def test_get_rbac_matrix(mock_execute_query_async, mock_supabase_client):
    mock_execute_query_async.return_value = (
        True,
        {"data": [{"role": "admin", "permissions": ["all"]}, {"role": "viewer", "permissions": ["read"]}]},
    )
    matrix = await admin_service.get_rbac_matrix()
    assert len(matrix) == 2
    assert matrix[0]["role"] == "admin"


@pytest.mark.asyncio
async def test_update_rbac_role(mock_execute_query_async, mock_supabase_client):
    mock_execute_query_async.return_value = (
        True,
        {"data": [{"role": "manager", "permissions": ["read", "write"], "description": "Dept Manager"}]},
    )
    res = await admin_service.update_rbac_role("manager", ["read", "write"], description="Dept Manager")
    assert res["role"] == "manager"
    assert res["permissions"] == ["read", "write"]


@pytest.mark.asyncio
async def test_get_document_versions(mock_execute_query_async, mock_supabase_client):
    mock_execute_query_async.return_value = (
        True,
        {"data": [{"id": "v1", "document_id": "doc1", "version_number": 1, "field_name": "docs", "content": {"key": "val"}}]},
    )
    versions = await admin_service.get_document_versions(limit=10)
    assert len(versions) == 1
    assert versions[0]["document_id"] == "doc1"
    assert versions[0]["version_number"] == 1


@pytest.mark.asyncio
async def test_list_and_create_crawler_targets(mock_execute_query_async, mock_supabase_client):
    mock_execute_query_async.return_value = (
        True,
        {"data": [{"id": "t1", "target_url": "https://example.com", "department": "Engineering"}]},
    )
    targets = await admin_service.list_crawler_targets(department="Engineering")
    assert len(targets) == 1
    assert targets[0]["target_url"] == "https://example.com"

    mock_execute_query_async.return_value = (
        True,
        {"data": [{"id": "t2", "target_url": "https://archon.ai", "department": "General"}]},
    )
    created = await admin_service.create_crawler_target({"target_url": "https://archon.ai", "department": "General"})
    assert created["id"] == "t2"
    assert created["target_url"] == "https://archon.ai"


@pytest.mark.asyncio
async def test_get_admin_logs(mock_execute_query_async, mock_supabase_client):
    mock_execute_query_async.return_value = (
        True,
        {"data": [{"id": "log1", "source": "admin_action", "level": "INFO", "message": "Role updated", "type": "audit"}]},
    )
    logs = await admin_service.get_admin_logs(type="audit")
    assert len(logs) == 1
    assert logs[0]["id"] == "log1"
    assert logs[0]["message"] == "Role updated"
