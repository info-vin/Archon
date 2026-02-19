from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from src.server.api_routes.marketing_api import (
    DraftBlogRequest,
    PitchRequest,
    draft_blog_post,
    generate_pitch,
    nana_banana_proxy,
)


@pytest.mark.asyncio
async def test_generate_pitch_no_key_real_logic():
    """
    Ensures generate_pitch returns 401 (Unauthorized) when API key is missing,
    adhering to real logic without mocks.
    """
    user = {"id": "test-user-id", "role": "sales"}
    request = PitchRequest(job_title="AI Engineer", company="TechCorp", description="Needs RAG expert")

    with patch("src.server.api_routes.marketing_api.credential_service") as MockCreds:
        # Simulate missing API key
        MockCreds.get_credential = AsyncMock(return_value=None)
        MockCreds.get_active_provider = AsyncMock(return_value={"chat_model": "gemini-2.0-flash"})

        with pytest.raises(HTTPException) as excinfo:
            await generate_pitch(request=request, current_user=user)

        # ASSERT: No Mock Fallback, we expect 401 Unauthorized
        assert excinfo.value.status_code == 401
        assert "API Key not configured" in excinfo.value.detail

@pytest.mark.asyncio
async def test_draft_blog_failure():
    """
    Ensures blog drafting returns 500 on LLM failure (No fallback for text content).
    """
    user = {"id": "test-user-id", "role": "marketing", "email": "test@archon.ai"}
    request = DraftBlogRequest(topic="AI Benefits")

    with patch("src.server.api_routes.marketing_api.genai.Client") as MockGenAI:
        MockGenAI.return_value.models.generate_content.side_effect = Exception("LLM failure")
        with patch("src.server.api_routes.marketing_api.credential_service") as MockCreds:
            MockCreds.get_credential = AsyncMock(return_value="fake-key")
            with pytest.raises(HTTPException) as excinfo:
                await draft_blog_post(request=request, current_user=user)
            assert excinfo.value.status_code == 500

@pytest.mark.asyncio
async def test_nana_banana_tier_fallback():
    """
    Simulates Native Render Failure -> Assert switches to Fallback (Pollinations).
    """
    user = {"id": "test-user-id", "role": "marketing"}
    with patch("src.server.api_routes.marketing_api.genai.Client") as MockGenAI:
        mock_enrich = MagicMock()
        mock_enrich.text = "Enhanced Prompt"
        # 1st call OK, 2nd call fails
        MockGenAI.return_value.models.generate_content.side_effect = [mock_enrich, Exception("No Imagen")]

        with patch("src.server.api_routes.marketing_api.credential_service") as MockCreds:
            MockCreds.get_credential = AsyncMock(return_value="fake-key")
            result = await nana_banana_proxy(request={"prompt": "City"}, current_user=user)
            assert result["tier"] == "fallback_pollinations"
            assert "pollinations.ai" in result["image_url"]

@pytest.mark.asyncio
async def test_nana_banana_emergency_picsum():
    """
    Simulates COMPLETE Failure (LLM down) -> Assert switches to Emergency (Picsum).
    """
    user = {"id": "test-user-id", "role": "marketing"}
    # Simulate LLM crash at the very first step
    with patch("src.server.api_routes.marketing_api.genai.Client") as MockGenAI:
        MockGenAI.return_value.models.generate_content.side_effect = Exception("Total API Blackout")

        with patch("src.server.api_routes.marketing_api.credential_service") as MockCreds:
            MockCreds.get_credential = AsyncMock(return_value="fake-key")
            result = await nana_banana_proxy(request={"prompt": "Cyberpunk"}, current_user=user)

            # ASSERT: Bob is unconscious, system uses Picsum
            assert result["tier"] == "emergency_picsum"
            assert result["status"] == "success"
            assert "picsum.photos" in result["image_url"]
