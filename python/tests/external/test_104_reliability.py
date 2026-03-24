import httpx
import pytest

from src.server.services.job_board_service import JobBoardService


@pytest.mark.asyncio
@pytest.mark.external
async def test_104_crawler_reliability():
    """物理驗證與 104 的真實連通性 (預熱 + AJAX)"""
    service = JobBoardService()
    # 測試一個確定的職缺 ID
    job_id = "8pws1"

    async with httpx.AsyncClient(timeout=15.0, headers=service.HEADERS, follow_redirects=True) as client:
        # 1. 預熱
        await client.get(f"https://www.104.com.tw/job/{job_id}")

        # 2. AJAX
        ajax_url = f"{service.DEFAULT_DETAIL_BASE_URL}{job_id}"
        resp = await client.get(ajax_url)

        assert resp.status_code == 200
        assert "application/json" in resp.headers.get("Content-Type", "")
        data = resp.json()
        assert "data" in data
        print(f"\n✅ 104 Real-time Data Probe: PASSED (Found {data['data'].get('custName')})")

if __name__ == "__main__":
    pytest.main([__file__])
