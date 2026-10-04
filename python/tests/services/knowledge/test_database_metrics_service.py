import pytest
from unittest.mock import MagicMock
from src.server.services.knowledge.database_metrics_service import (
    DatabaseMetricsService,
)

@pytest.mark.asyncio
async def test_get_metrics_success():
    mock_client = MagicMock()

    def mock_table(table_name):
        mock_query = MagicMock()
        mock_query.select.return_value = mock_query
        return mock_query

    mock_client.table.side_effect = mock_table

    service = DatabaseMetricsService(supabase_client=mock_client)

    def fake_execute_query(query, description=""):
        if "Get sources count" in description:
            return True, {"count": 10}
        elif "Get pages count" in description:
            return True, {"count": 50}
        elif "Get code examples count" in description:
            return True, {"count": 5}
        return False, {}

    service.execute_query = fake_execute_query

    metrics = await service.get_metrics()
    assert metrics["sources_count"] == 10
    assert metrics["pages_count"] == 50
    assert metrics["code_examples_count"] == 5
    assert metrics["average_pages_per_source"] == 5.0
    assert "timestamp" in metrics

@pytest.mark.asyncio
async def test_get_storage_statistics_success():
    mock_client = MagicMock()
    mock_query = MagicMock()
    mock_query.select.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_client.table.return_value = mock_query

    service = DatabaseMetricsService(supabase_client=mock_client)

    def fake_execute_query(query, description=""):
        if "Get knowledge type distribution" in description:
            return True, {"data": [{"knowledge_type": "doc"}, {"knowledge_type": "doc"}, {"knowledge_type": "api"}]}
        elif "Get recent activity" in description:
            return True, {"data": [{"source_id": "1", "created_at": "2026-01-01T00:00:00Z"}]}
        return False, {}

    service.execute_query = fake_execute_query

    stats = await service.get_storage_statistics()
    assert stats["knowledge_type_distribution"] == {"doc": 2, "api": 1}
    assert len(stats["recent_sources"]) == 1
    assert stats["recent_sources"][0]["source_id"] == "1"
