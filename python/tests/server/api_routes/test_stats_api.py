from unittest.mock import MagicMock, patch

import pytest

from src.server.api_routes.stats_api import get_member_performance, get_tasks_by_status


@pytest.mark.asyncio
async def test_get_tasks_by_status():
    mock_data = [{"name": "todo", "value": 2}, {"name": "done", "value": 1}]

    with patch("src.server.api_routes.stats_api.stats_service.get_tasks_by_status", return_value=mock_data):
        result = await get_tasks_by_status()

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
