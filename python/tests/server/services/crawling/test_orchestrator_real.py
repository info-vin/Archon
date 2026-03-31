from unittest.mock import AsyncMock, patch

import pytest

from src.server.services.crawling.crawling_service import CrawlingService


@pytest.mark.asyncio
async def test_orchestrate_crawl_entry_calls_orchestrator():
    """物理驗證 CrawlingService 入口是否能正確觸發模組化後的編排器"""
    with patch("src.server.services.crawling.crawling_service.get_supabase_client"):
        service = CrawlingService()
        with patch.object(service.orchestrator, "run", new_callable=AsyncMock) as mock_run:
            request = {"url": "https://example.com"}
            result = await service.orchestrate_crawl(request)

            # 驗證返回結構包含 task_id (對齊 4.6.16 實體代碼)
            assert "task_id" in result
            assert result["status"] == "started"
            mock_run.assert_called_once()
            print("\n✅ Task B1: Crawling Service to Orchestrator Link verified.")


if __name__ == "__main__":
    pytest.main([__file__])
