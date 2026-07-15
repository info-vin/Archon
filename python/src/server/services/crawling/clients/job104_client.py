import asyncio
import random
from typing import cast

from curl_cffi import requests as curl_requests
from pydantic import BaseModel

from ....config.logfire_config import get_logger

logger = get_logger(__name__)


class CrawlerBlockedException(Exception):
    """Raised when the crawler is blocked by WAF or CAPTCHA."""
    pass


class JobData(BaseModel):
    title: str
    company: str
    location: str | None = None
    salary: str | None = None
    url: str | None = None
    description: str | None = None
    description_full: str | None = None
    skills: list[str] | None = None
    source: str = "104"
    company_website: str | None = None
    identified_need: str | None = None
    real_id: str | None = None


class Job104Crawler:
    """
    Dedicated Anti-WAF Client for 104 Job Board.
    Uses SYNC requests for core API calls to bypass Async TLS fingerprinting (WAF).
    """

    DEFAULT_BASE_URL = "https://www.104.com.tw/jobs/search/api/jobs"
    DEFAULT_DETAIL_BASE_URL = "https://www.104.com.tw/job/ajax/content/"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.104.com.tw/jobs/search/",
        "Accept": "application/json, text/plain, */*",
        "X-Requested-With": "XMLHttpRequest",
    }

    def __init__(self, base_url: str = DEFAULT_BASE_URL, detail_base_url: str = DEFAULT_DETAIL_BASE_URL):
        self.base_url = base_url
        self.detail_base_url = detail_base_url

    def _fetch_from_104_sync(self, client: curl_requests.Session, keyword: str, limit: int) -> list[JobData]:
        params = {
            "ro": "0",
            "kwop": "7",
            "keyword": keyword,
            "order": "1",
            "asc": "0",
            "page": "1",
            "mode": "s",
            "jobsource": "2018indexpoc",
        }
        try:
            response = client.get(self.base_url, params=params)
            if response.status_code != 200 or "application/json" not in response.headers.get("content-type", ""):
                return []

            data = response.json()
            raw_jobs = data.get("data", [])
            parsed_jobs = []
            for item in raw_jobs[:limit]:
                raw_link = item.get("link", {}).get("job", "")
                url = f"https:{raw_link}" if raw_link.startswith("//") else raw_link
                real_id = url.split("?")[0].split("/job/")[1] if "/job/" in url else None
                parsed_jobs.append(
                    JobData(
                        title=item.get("jobName", "Unknown"),
                        company=item.get("custName", "Unknown"),
                        url=url,
                        description=item.get("jobDesc", ""),
                        source="104",
                        real_id=real_id,
                    )
                )
            return parsed_jobs
        except Exception:
            return []

    def _fetch_job_detail_sync(self, client: curl_requests.Session, job_id: str, job_url: str | None) -> str | None:
        try:
            url = f"{self.detail_base_url}{job_id}"
            headers = self.HEADERS.copy()
            if job_url:
                headers["Referer"] = job_url
                client.get(job_url, headers=headers)
            response = client.get(url, headers=headers)
            return (
                response.json().get("data", {}).get("jobDetail", {}).get("jobDescription")
                if response.status_code == 200
                else None
            )
        except Exception:
            return None

    async def search_jobs(self, keyword: str, limit: int = 8) -> list[JobData]:
        logger.info(f"Searching jobs (Sync-Thru Mode) | keyword={keyword}")

        def _fetch_all():
            headers = self.HEADERS.copy()
            with curl_requests.Session(impersonate="chrome120", headers=headers, timeout=20.0) as client:
                warmup_res = None
                try:
                    warmup_res = client.get(f"https://www.104.com.tw/jobs/search/?keyword={keyword}")
                    if warmup_res.status_code == 403:
                        logger.warning("403 Detected during warm-up. WAF might be blocking curl_cffi.")
                        import time
                        time.sleep(5)
                except Exception as e:
                    logger.warning(f"Warm-up failed: {e}")

                jobs = self._fetch_from_104_sync(client, keyword, limit)
                if not jobs:
                    if warmup_res and warmup_res.status_code == 403:
                        raise CrawlerBlockedException("104 WAF Blocked access.")
                    return []

                for i, job in enumerate(jobs):
                    if job.real_id:
                        if i > 0:
                            import time
                            time.sleep(random.uniform(2.0, 5.0))
                        detail = self._fetch_job_detail_sync(client, job.real_id, job.url)
                        job.description_full = detail or f"[Snippet Only] {job.description}"
                return jobs

        try:
            loop = asyncio.get_event_loop()
            jobs = cast(list[JobData], await loop.run_in_executor(None, _fetch_all))
            return jobs
        except CrawlerBlockedException:
            raise
        except Exception as e:
            logger.error(f"Job search failed: {e}")
            return []
