from unittest.mock import MagicMock, patch

import pytest

from src.server.services.prompt_service import PromptService

# --- Test Data ---
MOCK_PROMPTS_DATA = [
    {
        "prompt_name": "user_story_refinement",
        "prompt": "You are POBot...",
        "description": "POBot Prompt",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00"
    },
    {
        "prompt_name": "svg_logo_design",
        "prompt": "You are DevBot...",
        "description": "DevBot Prompt",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00"
    },
    {
        "prompt_name": "blog_post_draft",
        "prompt": "You are MarketBot (Blog)...",
        "description": "MarketBot Blog Prompt",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00"
    },
    {
        "prompt_name": "sales_pitch_generation",
        "prompt": "You are MarketBot (Sales)...",
        "description": "MarketBot Sales Prompt",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00"
    }
]

@pytest.mark.asyncio
async def test_load_prompts_success():
    """
    Test that PromptService correctly loads prompts from the database.
    (Simulating System Admin verifying the Prompt as Data architecture)
    """
    # 1. Setup Mock Supabase Client
    mock_supabase = MagicMock()
    mock_response = MagicMock()
    mock_response.data = MOCK_PROMPTS_DATA

    # Mock the chain: supabase.table().select().execute()
    mock_supabase.table.return_value.select.return_value.execute.return_value = mock_response

    # 2. Patch get_supabase_client to return our mock
    with patch("src.server.services.prompt_service.get_supabase_client", return_value=mock_supabase):
        # 3. Initialize Service (Singleton reset might be needed if tests run in parallel,
        # but here we just call load_prompts directly)
        service = PromptService()

        # Act
        await service.load_prompts()

        # Assert
        # Check if all 4 prompts are loaded
        assert len(service._prompts) == 4
        assert "user_story_refinement" in service._prompts
        assert "svg_logo_design" in service._prompts

        # Verify content match
        assert service.get_prompt("user_story_refinement") == "You are POBot..."
        assert service.get_prompt("svg_logo_design") == "You are DevBot..."

@pytest.mark.asyncio
async def test_load_prompts_empty_db():
    """Test behavior when database returns no prompts."""
    mock_supabase = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [] # Empty list
    mock_supabase.table.return_value.select.return_value.execute.return_value = mock_response

    with patch("src.server.services.prompt_service.get_supabase_client", return_value=mock_supabase):
        service = PromptService()
        await service.load_prompts()

        # Should be empty, but service should not crash
        assert len(service._prompts) == 0
        # Default fallback check
        assert service.get_prompt("non_existent") == "You are a helpful AI assistant."

@pytest.mark.asyncio
async def test_get_prompt_fallback():
    """Test getting a prompt that doesn't exist returns the default."""
    service = PromptService()
    # Ensure empty state
    service._prompts = {}

    result = service.get_prompt("missing_prompt", default="Custom Default")
    assert result == "Custom Default"
