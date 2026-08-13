from unittest.mock import MagicMock

import pytest

from src.server.prompts import ALL_PROMPTS
from src.server.services.prompt_service import PromptService


@pytest.fixture
def mock_supabase():
    client = MagicMock()
    # Mock for list_prompts -> select("*")
    client.table().select.return_value.execute.return_value = MagicMock(data=[])
    # Mock for get_prompt fallback -> select("prompt").eq()
    client.table().select().eq.return_value.execute.return_value = MagicMock(data=[])
    # Mock for upsert
    client.table().upsert.return_value.execute.return_value = MagicMock(data=[])
    return client


@pytest.mark.asyncio
async def test_prompt_service_ssot_sync(mock_supabase):
    """Test that prompt_service automatically loads ALL_PROMPTS and upserts."""
    # Reset singleton state
    PromptService._reset_for_testing()

    service = PromptService(supabase_client=mock_supabase)

    # Run load_prompts (simulating lifespan startup)
    await service.load_prompts()

    # 1. Verify ALL_PROMPTS are loaded into cache
    assert "BLOG_DRAFT" in service._prompts
    assert service._prompts["BLOG_DRAFT"] == ALL_PROMPTS["BLOG_DRAFT"]

    # 2. Verify Upsert was called for all baseline prompts
    # Since DB was mocked to return [], all ALL_PROMPTS should trigger an upsert
    mock_supabase.table().upsert.assert_called()

    # 3. Verify get_prompt works WITHOUT default
    retrieved = service.get_prompt("BLOG_DRAFT")
    assert retrieved == ALL_PROMPTS["BLOG_DRAFT"]

    # 4. Verify get_prompt fallback works if cache is manually cleared, preventing N+1
    service._prompts.clear()
    retrieved_fallback = service.get_prompt("BLOG_DRAFT")
    assert retrieved_fallback == ALL_PROMPTS["BLOG_DRAFT"]
    # Verify it re-populated cache
    assert "BLOG_DRAFT" in service._prompts
