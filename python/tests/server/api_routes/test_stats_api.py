from unittest.mock import patch

import pytest

from src.server.api_routes.stats_api import (
    get_agent_xp,
    get_member_performance,
    get_recent_token_usage,
    get_tasks_by_status,
    get_token_usage_details,
)


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


@pytest.mark.asyncio
async def test_get_agent_xp():
    mock_data = [
        {
            "name": "Sentinel",
            "agent_id": "ai-sentinel",
            "total_xp": 100,
            "success_count": 10,
            "total_cost": 0.5,
            "roi_ratio": 200.0,
            "level": "Level 1"
        }
    ]

    with patch("src.server.api_routes.stats_api.stats_service.get_agent_xp_stats", return_value=mock_data):
        result = await get_agent_xp()

        assert len(result) == 1
        assert result[0].name == "Sentinel"
        assert result[0].agent_id == "ai-sentinel"
        assert result[0].total_xp == 100
        assert result[0].success_count == 10
        assert result[0].total_cost == 0.5
        assert result[0].roi_ratio == 200.0
        assert result[0].level == "Level 1"



@pytest.mark.asyncio
async def test_get_token_usage_details():
    mock_data = [
        {"id": "1", "timestamp": "2023-10-27T10:00:00Z", "user_name": "Test User", "role": "admin", "model": "gpt-4", "tokens": 100, "cost": 0.01, "context": "Test"}
    ]
    with patch("src.server.api_routes.stats_api.stats_service.get_recent_token_usage", return_value=mock_data):
        result = await get_token_usage_details()
        assert len(result) == 1
        assert result[0].id == "1"
        assert result[0].tokens == 100

@pytest.mark.asyncio
async def test_get_recent_token_usage():
    mock_data = [
        {"id": "2", "timestamp": "2023-10-27T11:00:00Z", "user_name": "Agent X", "role": "ai_agent", "model": "claude", "tokens": 50, "cost": 0.005, "context": "Chat"}
    ]
    with patch("src.server.api_routes.stats_api.stats_service.get_recent_token_usage", return_value=mock_data):
        result = await get_recent_token_usage()
        assert len(result) == 1
        assert result[0].id == "2"
        assert result[0].model == "claude"
