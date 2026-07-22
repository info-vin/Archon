from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from src.server.config.model_ssot import get_active_fallback
from src.server.services.discovery.providers.google_handler import discover_google_models


@pytest.mark.asyncio
async def test_cloud_native_ssot_validation():
    """
    Test Hugging Face Cloud-Native SSOT Validation.
    Simulates a scenario where `gemini-3.1-flash-lite` (the default Free Tier model)
    is suddenly deprecated and removed from the Google API's active list.
    """

    # 1. Mock the API Response (gemini-3.1-flash-lite is MISSING)
    mock_api_response = {
        "models": [
            {"name": "models/mock-1-flash"},
            {"name": "models/mock-3-pro"},
            {"name": "models/mock-2-flash-lite"}, # This one is available
        ]
    }

    # Mocking aiohttp ClientSession
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = mock_api_response

    mock_session = AsyncMock(spec=aiohttp.ClientSession)
    mock_session.get.return_value.__aenter__.return_value = mock_response

    # Mock get_config
    mock_pricing_db = {
        "mock-1-flash": {"input": 0.0, "output": 0.0},
        "mock-3-pro": {"input": 1.25, "output": 5.0},
        "mock-2-flash-lite": {"input": 0.0, "output": 0.0},
    }

    with patch("src.server.services.discovery.providers.google_handler.get_config") as mock_get_config:
        mock_config_instance = MagicMock()
        mock_config_instance.token_pricing = mock_pricing_db
        mock_get_config.return_value = mock_config_instance

        # 2. Execute Dynamic Discovery
        discovered_models = await discover_google_models("fake-api-key", mock_session)

    # Assert that gemini-3.1-flash-lite is NOT in the discovered models
    discovered_names = [m.name for m in discovered_models]
    assert "gemini-3.1-flash-lite" not in discovered_names, "Deprecated model should be filtered out"
    assert "mock-2-flash-lite" in discovered_names, "Active model should be included"

    # 3. Test Auto-Fallback Trigger (Fallback from gemini-3.1-flash-lite)
    fallback_model_path = get_active_fallback("DEFAULT_TEXT", discovered_names)

    # Assert that it gracefully fell back to the next available Free Tier model
    assert fallback_model_path == "models/mock-2-flash-lite", "Should fallback to another flash-lite model"
