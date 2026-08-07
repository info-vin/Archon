from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.server.services.scheduler.jobs.patrol_infra import run_infrastructure_audit


@pytest.mark.asyncio
@patch("src.server.utils.get_supabase_client")
@patch("src.server.repositories.base_repository.BaseRepository")
@patch("httpx.AsyncClient.get", new_callable=AsyncMock)
@patch("os.getenv")
async def test_run_infrastructure_audit_success(mock_getenv, mock_get, mock_repo_class, mock_get_supabase):
    """Test infrastructure audit passing all checks."""
    def getenv_side_effect(key, default=None):
        if key == "FRONTEND_URL":
            return "https://mock.vercel.app"
        if key == "HUGGINGFACE_ENDPOINT":
            return "https://mock.hf.space"
        return default
    mock_getenv.side_effect = getenv_side_effect

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_get.return_value = mock_resp

    mock_supabase = MagicMock()
    mock_get_supabase.return_value = mock_supabase

    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo

    class MockCount:
        count = 10
        data = 100.0

    mock_repo.execute_query.side_effect = [
        (True, MockCount()), # Check Supabase Connections
        (True, MockCount()), # Get DB Size
        (True, None),        # Prune info/debug logs
        (True, None),        # Prune token usage
        (True, MockCount()), # Get new DB Size
    ]

    await run_infrastructure_audit()

    assert mock_get.call_count == 2
    assert mock_repo.execute_query.call_count == 5


@pytest.mark.asyncio
@patch("src.server.utils.get_supabase_client")
@patch("src.server.repositories.base_repository.BaseRepository")
@patch("httpx.AsyncClient.get", new_callable=AsyncMock)
@patch("os.getenv")
async def test_run_infrastructure_audit_failure(mock_getenv, mock_get, mock_repo_class, mock_get_supabase):
    """Test infrastructure audit detecting failures and logging them."""
    def getenv_side_effect(key, default=None):
        if key == "FRONTEND_URL":
            return "https://mock.vercel.app"
        if key == "HUGGINGFACE_ENDPOINT":
            return "https://mock.hf.space"
        return default
    mock_getenv.side_effect = getenv_side_effect

    mock_resp = MagicMock()
    mock_resp.status_code = 503
    mock_get.return_value = mock_resp

    mock_supabase = MagicMock()
    mock_get_supabase.return_value = mock_supabase

    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo

    class MockCount:
        count = 60
        data = 100.0

    mock_repo.execute_query.side_effect = [
        (True, MockCount()), # Check Supabase Connections
        (True, MockCount()), # Get DB Size
        (True, None),        # Prune info/debug logs
        (True, None),        # Prune token usage
        (True, MockCount()), # Get new DB Size
        (True, None)         # Log infra errors
    ]

    await run_infrastructure_audit()

    assert mock_repo.execute_query.call_count == 6
    log_call = mock_repo.execute_query.call_args_list[5]
    assert "Log infra errors" in str(log_call)
