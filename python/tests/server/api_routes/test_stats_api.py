from unittest.mock import MagicMock, patch

import pytest

from src.server.api_routes.stats_api import get_member_performance, get_tasks_by_status


@pytest.mark.asyncio
async def test_get_tasks_by_status():
    mock_supabase = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [{"status": "todo"}, {"status": "todo"}, {"status": "done"}]
    mock_supabase.table.return_value.select.return_value.execute.return_value = mock_response

    with patch("src.server.api_routes.stats_api.get_supabase_client", return_value=mock_supabase):
        result = await get_tasks_by_status()

        # Sort result for comparison because dict iteration order is insertion-based (usually) but safer to be explicit
        # Or just check membership
        assert len(result) == 2
        result_dumps = [r.model_dump() for r in result]
        assert {"name": "todo", "value": 2} in result_dumps
        assert {"name": "done", "value": 1} in result_dumps


@pytest.mark.asyncio
async def test_get_member_performance():
    mock_data = [{"name": "Alice", "completed_tasks": 2}, {"name": "Bob", "completed_tasks": 1}]

    with patch("src.server.api_routes.stats_api.stats_service.get_member_performance", return_value=mock_data):
        result = await get_member_performance()

        assert len(result) == 2
        assert result[0].name == "Alice"
        assert result[0].completed_tasks == 2
        assert result[1].name == "Bob"
        assert result[1].completed_tasks == 1
