from unittest.mock import MagicMock, patch

import pytest

from src.server.prompts import ALL_PROMPTS
from src.server.services.prompt_service import PromptService


@pytest.fixture(autouse=True)
def reset_prompt_service():
    """Reset singleton between each test in this file."""
    PromptService._reset_for_testing()
    yield


@pytest.mark.asyncio
async def test_load_prompts_success():
    """Test successful loading of prompts from database."""
    mock_supabase = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [
        {"prompt_name": "blog_post_draft", "prompt": "You are MarketBot (Blog)..."},
        {"prompt_name": "sales_pitch_generation", "prompt": "You are MarketBot (Sales)..."},
        {"prompt_name": "svg_logo_design", "prompt": "You are DevBot..."},
        {"prompt_name": "user_story_refinement", "prompt": "You are POBot..."},
    ]
    # Configure mock behavior for list_prompts which uses self.execute_query
    mock_supabase.table.return_value.select.return_value.execute.return_value = mock_response

    with patch("src.server.services.prompt_service.get_supabase_client", return_value=mock_supabase):
        service = PromptService()
        await service.load_prompts()

        assert len(service._prompts) == 4 + len(ALL_PROMPTS)
        assert service.get_prompt("blog_post_draft") == "You are MarketBot (Blog)..."
        assert service.get_prompt("svg_logo_design") == "You are DevBot..."


@pytest.mark.asyncio
async def test_load_prompts_empty_db():
    """Test behavior when database returns no prompts."""
    mock_supabase = MagicMock()
    mock_response = MagicMock()
    mock_response.data = []  # Empty list
    mock_supabase.table.return_value.select.return_value.execute.return_value = mock_response

    with patch("src.server.services.prompt_service.get_supabase_client", return_value=mock_supabase):
        service = PromptService()
        await service.load_prompts()

        # Should be empty, but service should not crash
        assert len(service._prompts) == len(ALL_PROMPTS)
        # Default fallback check
        assert service.get_prompt("non_existent") == "You are a helpful AI assistant."


@pytest.mark.asyncio
async def test_get_prompt_fallback():
    """Test getting a prompt that doesn't exist returns the default."""
    service = PromptService()
    # Manual reset just in case
    service._prompts = {}

    result = service.get_prompt("missing_prompt", default="Custom Default")
    assert result == "Custom Default"
