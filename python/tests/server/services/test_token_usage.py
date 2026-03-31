import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Add python root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from src.server.services.token_usage_service import TokenUsageService


@pytest.mark.asyncio
async def test_log_usage_pricing():
    """Test that cost is calculated correctly for known models."""

    mock_supabase = MagicMock()
    mock_table = MagicMock()
    mock_supabase.table.return_value = mock_table
    mock_table.insert.return_value = mock_table
    mock_table.execute.return_value = MagicMock(data=[])

    with patch("src.server.services.token_usage_service.get_supabase_client", return_value=mock_supabase):
        # Case 1: GPT-4o input/output (2.5 / 10.0)
        # 1M input = $2.5, 1M output = $10.0 => Total $12.5
        await TokenUsageService.log_usage(
            request_id="test-123",
            model="gpt-4o",
            provider="openai",
            input_tokens=1_000_000,
            output_tokens=1_000_000,
            user_id="user-1",
        )

        args, _ = mock_table.insert.call_args
        payload = args[0]
        assert payload["model"] == "gpt-4o"
        assert payload["input_tokens"] == 1_000_000
        assert payload["cost_usd"] == 12.5

        # Case 2: Ollama (Free)
        await TokenUsageService.log_usage(
            request_id="test-456",
            model="llama3",
            provider="ollama",
            input_tokens=5000,
            output_tokens=200,
            user_id="user-2",
        )

        args, _ = mock_table.insert.call_args
        payload = args[0]
        assert payload["provider"] == "ollama"
        assert payload["cost_usd"] == 0.0


@pytest.mark.asyncio
async def test_log_usage_unknown_model_fallback():
    """Test fallback pricing for unknown models (defaults to gpt-4o currently)."""

    mock_supabase = MagicMock()
    mock_table = MagicMock()
    mock_supabase.table.return_value = mock_table
    mock_table.insert.return_value = mock_table

    with patch("src.server.services.token_usage_service.get_supabase_client", return_value=mock_supabase):
        await TokenUsageService.log_usage(
            request_id="test-789",
            model="unknown-super-model",
            provider="openai",
            input_tokens=1_000_000,
            output_tokens=1_000_000,
        )

        args, _ = mock_table.insert.call_args
        payload = args[0]
        # Should use gemini-2.5-flash-lite pricing as default fallback in realized implementation
        assert payload["cost_usd"] == 0.25
