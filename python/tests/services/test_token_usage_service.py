
from unittest.mock import MagicMock, patch

import pytest

from src.server.services.token_usage_service import TokenUsageService


@pytest.fixture
def mock_supabase():
    with patch("src.server.services.token_usage_service.get_supabase_client") as mock:
        client = MagicMock()
        mock.return_value = client
        yield client

@pytest.fixture
def service():
    return TokenUsageService()

@pytest.mark.asyncio
async def test_log_usage(service, mock_supabase):
    # Mock the chain: supabase.table().insert().execute()
    mock_table = MagicMock()
    mock_insert = MagicMock()
    mock_execute = MagicMock()

    mock_supabase.table.return_value = mock_table
    mock_table.insert.return_value = mock_insert
    mock_insert.execute.return_value = mock_execute

    await service.log_usage(
        request_id="req-123",
        model="gpt-4o",
        provider="openai",
        input_tokens=100,
        output_tokens=50,
        user_id="user-1"
    )

    # Verify any of the calls was to token_usage
    # (Multiple calls now due to XP system querying profiles)
    mock_supabase.table.assert_any_call("token_usage")

    # Verify payload contains calculated cost
    # Input: 100 * 2.50/1M = 0.00025
    # Output: 50 * 10.00/1M = 0.0005
    # Total: 0.00075

    args, _ = mock_table.insert.call_args
    payload = args[0]

    assert payload["request_id"] == "req-123"
    assert payload["model"] == "gpt-4o"
    assert payload["input_tokens"] == 100
    assert payload["cost_usd"] == pytest.approx(0.00075)

@pytest.mark.asyncio
async def test_log_usage_ollama(service, mock_supabase):
    mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock()

    await service.log_usage(
        request_id="req-456",
        model="llama3",
        provider="ollama",
        input_tokens=1000,
        output_tokens=1000,
        user_id="user-1"
    )

    args, _ = mock_supabase.table.return_value.insert.call_args
    payload = args[0]

    assert payload["cost_usd"] == 0.0  # Ollama should be free
