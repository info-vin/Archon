from unittest.mock import AsyncMock, MagicMock

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
    """驗證 generate_pitch 在沒 Key 時回傳 401"""
    request = PitchRequest(job_title="AI Engineer", company="TechCorp", description="Needs RAG expert")
    user = {"id": "test-id", "role": "sales"}

    mock_svc = MagicMock()
    # 模擬 Service 回傳 401
    mock_svc.generate_pitch = AsyncMock(return_value={"error_code": 401, "message": "AI API Key not configured."})

    # 呼叫 API 函數
    with pytest.raises(HTTPException) as excinfo:
        await generate_pitch(request=request, current_user=user, service=mock_svc)

    assert excinfo.value.status_code == 401

@pytest.mark.asyncio
async def test_draft_blog_failure():
    """驗證部落格生成失敗時回傳 500"""
    request = DraftBlogRequest(topic="AI Benefits")
    user = {"id": "test-id", "role": "marketing"}

    mock_svc = MagicMock()
    mock_svc.draft_blog = AsyncMock(return_value=(False, {"error": "LLM failure"}))

    with pytest.raises(HTTPException) as excinfo:
        await draft_blog_post(request=request, current_user=user, service=mock_svc)

    assert excinfo.value.status_code == 500

@pytest.mark.asyncio
async def test_generate_logo_tier_fallback():
    """驗證圖資生成 Fallback 邏輯"""
    request = LogoRequest(style="modern")
    user = {"id": "test-id", "role": "marketing"}

    mock_svc = MagicMock()
    mock_svc.generate_visual_asset = AsyncMock(return_value={
        "status": "success", "image_url": "https://pollinations.ai/fake", "tier": "fallback_pollinations"
    })

    result = await generate_logo(request=request, current_user=user, service=mock_svc)
    assert result["tier"] == "fallback_pollinations"
    assert "pollinations.ai" in result["image_url"]
