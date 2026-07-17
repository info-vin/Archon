import pytest
from curl_cffi import requests

from src.server.services.crawling.clients.job104_client import Job104Crawler


@pytest.mark.asyncio
@pytest.mark.external
async def test_104_crawler_reliability():
    """物理驗證與 104 的真實連通性 (預熱 + AJAX)"""
    crawler = Job104Crawler()
    # 測試一個確定的職缺 ID
    job_id = "8pws1"

    async with requests.AsyncSession(impersonate="chrome120", timeout=15.0, headers=crawler.get_headers()) as client:
        # 1. 預熱
        await client.get(f"https://www.104.com.tw/job/{job_id}")

        # 2. AJAX
        ajax_url = f"{crawler.detail_base_url}{job_id}"
        resp = await client.get(ajax_url)

        assert resp.status_code == 200
        assert "application/json" in resp.headers.get("Content-Type", "")
        data = resp.json()
        assert "data" in data
        print(f"\n✅ 104 Real-time Data Probe: PASSED (Found {data['data'].get('custName')})")


if __name__ == "__main__":
    pytest.main([__file__])
