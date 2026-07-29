import asyncio
import random

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

    USER_AGENTS = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    ]

    def get_headers(self) -> dict:
        return {
            "User-Agent": random.choice(self.USER_AGENTS),
            "Referer": "https://www.104.com.tw/jobs/search/",
            "Accept": "application/json, text/plain, */*",
            "X-Requested-With": "XMLHttpRequest",
        }

    def __init__(self, base_url: str = DEFAULT_BASE_URL, detail_base_url: str = DEFAULT_DETAIL_BASE_URL) -> None:
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
            if response.status_code == 429 or response.status_code == 503:
                logger.warning(f"Temporary block detected: {response.status_code}")
                return []

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
                        description=item.get("description", ""),
                        source="104",
                        real_id=real_id,
                    )
                )
            return parsed_jobs
        except Exception as e:
            logger.exception(f"Error fetching jobs: {e}")
            return []

    def _fetch_job_detail_sync(self, client: curl_requests.Session, job_id: str, job_url: str | None) -> str | None:
        try:
            url = f"{self.detail_base_url}{job_id}"
            headers = self.get_headers()
            if job_url:
                headers["Referer"] = job_url
                client.get(job_url, headers=headers)
            response = client.get(url, headers=headers)
            if response.status_code == 429:
                logger.warning("429 Too Many Requests detected during detail fetch. Backing off.")
                return None
            if response.status_code == 503:
                logger.warning("503 Service Unavailable during detail fetch.")
                return None
            return (
                response.json().get("data", {}).get("jobDetail", {}).get("jobDescription")
                if response.status_code == 200
                else None
            )
        except Exception as e:
            logger.exception(f"Error fetching job detail: {e}")
            return None

    def create_session(self) -> curl_requests.Session:
        import os
        proxy_url = os.environ.get("CRAWLER_PROXY_URL")
        proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
        impersonates = ["chrome110", "chrome120", "safari15_3", "safari17_0", "edge101"]
        return curl_requests.Session(
            impersonate=random.choice(impersonates), headers=self.get_headers(), timeout=20.0, proxies=proxies  # type: ignore
        )

    async def search_jobs(self, keyword: str, limit: int = 8, client: curl_requests.Session | None = None) -> list[JobData]:
        logger.info(f"Searching jobs (Sync-Thru Mode) | keyword={keyword}")

        def _fetch_all(session: curl_requests.Session) -> list[JobData]:
            try:
                warmup_res = None
                try:
                    warmup_res = session.get(f"https://www.104.com.tw/jobs/search/?keyword={keyword}")
                    if warmup_res.status_code == 403:
                        logger.warning("403 Detected during warm-up. WAF might be blocking curl_cffi.")
                        import time
                        time.sleep(10) # Increased backoff
                except Exception as e:
                    logger.warning(f"Warm-up failed: {e}")

                jobs = self._fetch_from_104_sync(session, keyword, limit)
                if not jobs:
                    if warmup_res and warmup_res.status_code == 403:
                        raise CrawlerBlockedException("104 WAF Blocked access.")
                    return []

                for i, job in enumerate(jobs):
                    if job.real_id:
                        if i > 0:
                            import time
                            time.sleep(random.uniform(3.0, 7.0)) # Increased jitter
                        detail = self._fetch_job_detail_sync(session, job.real_id, job.url)
                        job.description_full = detail or f"[Snippet Only] {job.description}"
                return jobs
            except CrawlerBlockedException:
                raise
            except Exception as e:
                logger.error(f"Error in 104 crawler _fetch_all: {e}")
                return []

        if client:
            return await asyncio.to_thread(_fetch_all, client)
        else:
            def _with_session() -> list[JobData]:
                with self.create_session() as new_client:
                    return _fetch_all(new_client)
            return await asyncio.to_thread(_with_session)

