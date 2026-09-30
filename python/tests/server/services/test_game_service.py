from unittest.mock import MagicMock

import pytest

from src.server.services.game_service import GameService


@pytest.fixture
def mock_supabase():
    return MagicMock()


@pytest.fixture
def game_service(mock_supabase):
    return GameService(supabase_client=mock_supabase)


@pytest.mark.asyncio
async def test_save_game_success(game_service, mock_supabase):
    mock_query = MagicMock()
    mock_supabase.table.return_value.upsert.return_value = mock_query

    mock_execute_query = MagicMock(return_value=(True, {"data": [{"id": "save-1", "user_id": "u1", "save_data": {"funds": 100}, "updated_at": "now"}]}))
    game_service.execute_query = mock_execute_query

    result = await game_service.save_game("u1", {"funds": 100})
    assert result["id"] == "save-1"
    assert result["user_id"] == "u1"


@pytest.mark.asyncio
async def test_save_game_failure(game_service, mock_supabase):
    mock_query = MagicMock()
    mock_supabase.table.return_value.upsert.return_value = mock_query

    mock_execute_query = MagicMock(return_value=(False, {}))
    game_service.execute_query = mock_execute_query

    with pytest.raises(ValueError, match="Failed to save game state"):
        await game_service.save_game("u1", {"funds": 100})


@pytest.mark.asyncio
async def test_load_game_success(game_service, mock_supabase):
    mock_query = MagicMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value = mock_query

    mock_execute_query = MagicMock(return_value=(True, {"data": [{"save_data": {"funds": 500, "reputation": 10}}]}))
    game_service.execute_query = mock_execute_query

    result = await game_service.load_game("u1")
    assert result is not None
    assert result.get("funds") == 500
    assert result.get("reputation") == 10


@pytest.mark.asyncio
async def test_load_game_not_found(game_service, mock_supabase):
    mock_query = MagicMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value = mock_query

    mock_execute_query = MagicMock(return_value=(True, {"data": []}))
    game_service.execute_query = mock_execute_query

    result = await game_service.load_game("u1")
    assert result is None
