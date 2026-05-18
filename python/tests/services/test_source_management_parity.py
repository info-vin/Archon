from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.server.services.source_management.logic.ai_metadata import extract_source_summary


@pytest.mark.asyncio
async def test_extract_source_summary_logic():
    """物理驗證摘要提取邏輯是否能正確呼叫 LLM (OpenAI-style) 並返回結果"""
    # 1. 準備模擬回應
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Test Summary Content"))]

    # 2. 準備模擬 Client
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    # 3. 準備模擬非同步上下文管理器
    @asynccontextmanager
    async def mock_llm_context(*args, **kwargs):
        yield mock_client

    # 4. 執行測試
    with patch("src.server.services.source_management.logic.ai_metadata.get_llm_client", side_effect=mock_llm_context):
        with patch(
            "src.server.services.credential_service.CredentialService.get_credentials_by_category",
            new_callable=AsyncMock,
        ) as mock_creds:
            mock_creds.return_value = {"MODEL_CHOICE": "test-model"}

            summary = await extract_source_summary("test-source", "test content")

            # 斷言
            assert summary == "Test Summary Content"
            print("\n✅ Task F: AI Metadata Parity Test PASSED.")


if __name__ == "__main__":
    pytest.main([__file__])
