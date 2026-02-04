
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.server.api_routes.marketing_api import DraftBlogRequest, draft_blog_post, nana_banana_proxy


@pytest.mark.asyncio
async def test_draft_blog_fallback_on_llm_failure():
    """
    TC1: Simulate LLM failure in draft_blog_post -> Assert returns Mock Draft via direct function call.
    """
    user = {"id": "test-user-id", "role": "marketing", "email": "test@archon.ai"}
    request = DraftBlogRequest(topic="AI Benefits", keywords="Efficiency", tone="Expert")

    with patch("src.server.api_routes.marketing_api.get_llm_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.chat.completions.create.side_effect = Exception("LLM failure")
        mock_get_client.return_value.__aenter__.return_value = mock_client

        with patch("src.server.api_routes.marketing_api.RAGService") as MockRAG:
            MockRAG.return_value.perform_rag_query = AsyncMock(return_value=(True, {"results": []}))
            with patch("src.server.api_routes.marketing_api.GuardrailService") as MockGuard:
                MockGuard.validate_input.return_value = (True, "")
                MockGuard.audit_output.return_value = (True, "")
                with patch("src.server.api_routes.marketing_api.credential_service") as MockCreds:
                    MockCreds.get_active_provider = AsyncMock(return_value={"chat_model": "gemini-1.5-flash"})
                    MockCreds.get_credentials_by_category = AsyncMock(return_value={"MARKETING_MODEL": "gemini-1.5-flash"})
                    MockCreds.get_credential = AsyncMock(return_value="fake-key")
                    with patch("src.server.api_routes.marketing_api.LogService") as MockLogService:
                        MockLogService.return_value.create_log_entry = Mock()

                        # Directly call the endpoint function to avoid httpx mock collisions
                        response = await draft_blog_post(request=request, current_user=user)

                        assert "[OFFLINE MOCK]" in response.title
                        assert "AI Benefits" in response.title
                        MockLogService.return_value.create_log_entry.assert_called_once()

@pytest.mark.asyncio
async def test_nana_banana_fallback_on_429():
    """
    TC2: Simulate Image API 429 Quota Exceeded -> Assert returns Mock Image via direct function call.
    """
    user = {"id": "test-user-id", "role": "marketing", "email": "test@archon.ai"}

    with patch("src.server.api_routes.marketing_api.genai.Client") as MockGenAI:
        # Mock the SDK to raise an exception (like 429 Resource Exhausted)
        MockGenAI.return_value.models.generate_content.side_effect = Exception("429 Quota Exceeded")

        with patch("src.server.api_routes.marketing_api.credential_service") as MockCreds:
            MockCreds.get_credential = AsyncMock(return_value="fake-key")
            MockCreds.get_credentials_by_category = AsyncMock(return_value={})
            with patch("src.server.api_routes.marketing_api.LogService") as MockLogService:
                MockLogService.return_value.create_log_entry = Mock()

                # Directly call the endpoint function
                result = await nana_banana_proxy(
                    request={"prompt": "Cyberpunk City"},
                    current_user=user
                )

                # ASSERT
                assert result["status"] == "fallback_mock"
                assert "placehold.co" in result["image_url"] or "Nana Banana Fallback" in result["image_url"]
                MockLogService.return_value.create_log_entry.assert_called_once()
