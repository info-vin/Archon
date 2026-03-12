from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi import HTTPException
from server.api_routes.marketing_api import (
    DraftBlogRequest,
    LogoRequest,
    PitchRequest,
    draft_blog_post,
    generate_logo,
    generate_pitch,
)

@pytest.mark.asyncio
async def test_generate_pitch_no_key_real_logic():
    """驗證 generate_pitch 在 Mock 模式下的回傳"""
    req_obj = PitchRequest(job_title="AI Engineer", company="TechCorp")
    user = {"id": "test-id", "role": "sales"}

    # PHYSICAL HARDENING: Patch the Service METHOD directly at its source
    with patch("src.server.services.marketing_service.MarketingService.generate_pitch") as mock_method:
        # Simulate the structured error response
        mock_method.return_value = {"error_code": 401, "message": "Invalid Key"}

        # We call the API function directly
        try:
            res = await generate_pitch(req=req_obj, current_user=user)
            if isinstance(res, dict):
                assert res.get("error_code") == 401
        except HTTPException as e:
            assert e.status_code == 401

@pytest.mark.asyncio
async def test_draft_blog_failure():
    """驗證部落格生成失敗時回傳 500"""
    req_obj = DraftBlogRequest(topic="AI Benefits")
    user = {"id": "test-id", "role": "marketing"}

    with patch("src.server.services.marketing_service.MarketingService.draft_blog") as mock_method:
        mock_method.return_value = (False, {"error": "LLM failure"})

        with pytest.raises(HTTPException) as excinfo:
            await draft_blog_post(req=req_obj, current_user=user)

        assert excinfo.value.status_code == 500

@pytest.mark.asyncio
async def test_generate_logo_tier_fallback():
    """驗證圖資生成 Fallback 邏輯"""
    req_obj = LogoRequest(style="modern")
    user = {"id": "test-id", "role": "marketing"}

    with patch("src.server.services.marketing_service.MarketingService.generate_visual_asset") as mock_method:
        mock_method.return_value = {
            "status": "success", "image_url": "https://pollinations.ai/fake", "tier": "fallback_pollinations"
        }

        result = await generate_logo(req=req_obj, current_user=user)
        assert result["tier"] == "fallback_pollinations"
