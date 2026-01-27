import asyncio
import random

import httpx
import pytest
from pydantic import BaseModel

# --- Configuration ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
]

class JobData(BaseModel):
    title: str
    company: str
    real_id: str | None = None
    url: str | None = None
    description_len: int = 0
    status: str = "Pending"
    error_msg: str | None = None

@pytest.mark.external
@pytest.mark.asyncio
async def test_104_crawler_reliability():
    """
    Integration test for 104 Job Search Crawler.
    Verifies that we can fetch job lists and details without 403 Forbidden.
    """
    keyword = "python"
    limit = 3
    base_headers = {
        "Accept": "application/json, text/plain, */*",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.104.com.tw/jobs/search/"
    }

    headers = base_headers.copy()
    headers["User-Agent"] = random.choice(USER_AGENTS)

    async with httpx.AsyncClient(timeout=20.0, headers=headers, follow_redirects=True) as client:
        # Phase 1: Search List
        search_url = "https://www.104.com.tw/jobs/search/api/jobs"
        params = {
            "ro": "0", "kwop": "7", "keyword": keyword,
            "expansionType": "area,spec,com,job,wf,wktm",
            "order": "1", "asc": "0", "page": "1", "mode": "s", "jobsource": "2018indexpoc"
        }

        print(f"📡 Fetching list from {search_url}...")
        resp = await client.get(search_url, params=params)

        assert resp.status_code == 200, f"List Fetch Failed (Status: {resp.status_code})"

        data = resp.json().get("data", [])
        if not data:
            pytest.skip("No jobs found for keyword, skipping detail check.")

        target_jobs = data[:limit]
        processed_count = 0
        success_count = 0

        for i, item in enumerate(target_jobs):
            processed_count += 1
            real_id = None
            raw_link = item.get("link", {}).get("job", "")

            # ID Extraction
            if "/job/" in raw_link:
                try:
                    real_id = raw_link.split("?")[0].split("/job/")[1]
                except Exception:
                    pass

            if not real_id:
                print(f"⚠️ Skipped item {i}: No Real ID found.")
                continue

            # Throttling
            if i > 0:
                await asyncio.sleep(random.uniform(1.0, 2.0))

            # Phase 2: Detail Fetch
            ajax_url = f"https://www.104.com.tw/job/ajax/content/{real_id}"
            detail_headers = headers.copy()
            detail_headers["Referer"] = f"https://www.104.com.tw/job/{real_id}"

            print(f"📡 Fetching details for {real_id}...")
            d_resp = await client.get(ajax_url, headers=detail_headers)

            # We allow some failures (e.g. job closed), but main connectivity should work
            if d_resp.status_code == 200:
                d_data = d_resp.json()
                content = d_data.get("data", {}).get("jobDetail", {}).get("jobDescription", "")
                if content:
                    success_count += 1
            else:
                print(f"❌ Failed to fetch detail {real_id}: {d_resp.status_code}")

        # Assertion: If we processed jobs, we expect at least 60% success rate to consider the crawler health "Good"
        # 104 often has anti-bot or expired jobs, so 100% isn't always possible in CI
        if processed_count > 0:
            success_rate = success_count / processed_count
            assert success_rate >= 0.6, f"Success rate ({success_rate:.1%}) too low. 104 might be blocking or changing API."
