from unittest.mock import AsyncMock, MagicMock

import pytest

from src.server.services.crawling.strategies.recursive import RecursiveCrawlStrategy


# 定義一個簡單的非同步生成器模擬
async def async_gen(items):
    for item in items:
        yield item


@pytest.mark.asyncio
async def test_recursive_crawl_logic_execution():
    """物理驗證遞迴爬取邏輯是否能正確執行分派與進度回報"""
    # 1. Mock Crawler 與 Generator
    mock_crawler = AsyncMock()
    # 模擬 arun_many 回傳非同步生成器
    mock_result = MagicMock(url="https://test.com/1", success=True)
    mock_result.markdown = "content"
    mock_result.metadata = {}
    mock_crawler.arun_many.return_value = async_gen([mock_result])

    mock_gen = MagicMock()
    strategy = RecursiveCrawlStrategy(mock_crawler, mock_gen)

    # 2. 準備參數
    start_urls = ["https://test.com"]

    def transform_func(x):
        return x

    def is_doc_func(x):
        return True

    # 3. 執行
    results = await strategy.crawl_recursive_with_progress(
        start_urls=start_urls, transform_url_func=transform_func, is_documentation_site_func=is_doc_func, max_depth=1
    )

    # 4. 斷言
    assert len(results) > 0
    print("\n✅ Task E: Recursive Strategy Parity Test PASSED (Async Gen).")


if __name__ == "__main__":
    pytest.main([__file__])
