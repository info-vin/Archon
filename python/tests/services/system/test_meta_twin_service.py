from unittest.mock import AsyncMock, MagicMock

import pytest

from src.server.services.system.meta_twin_service import MetaTwinService, meta_twin_service


@pytest.fixture
def mock_supabase():
    client = MagicMock()
    return client


@pytest.fixture
def service(mock_supabase):
    return MetaTwinService(supabase_client=mock_supabase)


def test_meta_twin_service_init(service, mock_supabase):
    assert service.supabase_client == mock_supabase
    assert meta_twin_service is not None


@pytest.mark.asyncio
async def test_run_telemetry_audit_no_logs(service, mock_supabase):
    mock_query = MagicMock()
    mock_supabase.table.return_value.select.return_value.gt.return_value = mock_query

    mock_execute = MagicMock(return_value=(True, {"data": []}))
    service.execute_query = mock_execute

    result = await service.run_telemetry_audit()

    assert result["status"] == "completed"
    assert result["diagnoses_count"] == 0
    assert result["corrections_count"] == 0
    assert result["diagnoses"] == []
    assert result["corrections"] == []


@pytest.mark.asyncio
async def test_run_telemetry_audit_rate_limit_risk(service, mock_supabase):
    mock_logs = [
        {"source": "test_agent", "level": "ERROR", "message": "HTTP 429 rate limit exceeded", "created_at": "2026-01-01T00:00:00Z"},
        {"source": "test_agent", "level": "ERROR", "message": "HTTP 429 rate limit exceeded", "created_at": "2026-01-01T00:01:00Z"},
        {"source": "test_agent", "level": "ERROR", "message": "rate limit error", "created_at": "2026-01-01T00:02:00Z"},
    ]

    mock_query = MagicMock()
    mock_supabase.table.return_value.select.return_value.gt.return_value = mock_query
    service.execute_query = MagicMock(return_value=(True, {"data": mock_logs}))

    service.switch_model_to_fallback = AsyncMock(return_value=True)

    result = await service.run_telemetry_audit()

    assert result["status"] == "completed"
    assert result["diagnoses_count"] == 1
    assert result["corrections_count"] == 1
    assert result["diagnoses"][0]["issue"] == "RATE_LIMIT_RISK"
    assert result["corrections"][0]["action"] == "MODEL_SWAP"


@pytest.mark.asyncio
async def test_switch_model_to_fallback(service, mock_supabase):
    mock_upsert = MagicMock()
    mock_supabase.table.return_value.upsert.return_value = mock_upsert
    service.execute_query = MagicMock(return_value=(True, {}))

    success = await service.switch_model_to_fallback("test_agent", "models/gemini-3.1-flash-lite")
    assert success is True


@pytest.mark.asyncio
async def test_throttle_concurrency(service, mock_supabase):
    mock_upsert = MagicMock()
    mock_supabase.table.return_value.upsert.return_value = mock_upsert
    service.execute_query = MagicMock(return_value=(True, {}))

    success = await service.throttle_concurrency("test_agent", 1)
    assert success is True
