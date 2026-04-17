import asyncio
import random
from typing import cast

import httpx
from pydantic import BaseModel

from ..config.logfire_config import get_logger
from ..utils import get_supabase_client

logger = get_logger(__name__)


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


class JobBoardService:
    """
    Service to interact with external job boards (specifically 104.com.tw).
    Uses SYNC requests for core API calls to bypass Async TLS fingerprinting (WAF).
    MOCK DATA REMOVED: System only returns real data or empty list.
    """

    DEFAULT_BASE_URL = "https://www.104.com.tw/jobs/search/api/jobs"
    DEFAULT_DETAIL_BASE_URL = "https://www.104.com.tw/job/ajax/content/"

    def __init__(self):
        self.supabase = get_supabase_client()

    async def _get_base_url(self) -> str:
        try:
            from ..services.settings_service import SettingsService
            settings = SettingsService(self.supabase)
            return settings.get_setting("CRAWLER_104_SEARCH_API", self.DEFAULT_BASE_URL) or self.DEFAULT_BASE_URL
        except Exception:
            return self.DEFAULT_BASE_URL

    async def _get_detail_url(self) -> str:
        try:
            from ..services.settings_service import SettingsService
            settings = SettingsService(self.supabase)
            return (
                settings.get_setting("CRAWLER_104_DETAIL_API", self.DEFAULT_DETAIL_BASE_URL)
                or self.DEFAULT_DETAIL_BASE_URL
            )
        except Exception:
            return self.DEFAULT_DETAIL_BASE_URL

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.104.com.tw/jobs/search/",
        "Accept": "application/json, text/plain, */*",
        "X-Requested-With": "XMLHttpRequest",
    }

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"
    ]

    # REAL DATA ONLY: MOCK_JOBS remains empty
    MOCK_JOBS: list[JobData] = []

    async def search_jobs(self, keyword: str, limit: int = 8) -> list[JobData]:
        logger.info(f"Searching jobs (Sync-Thru Mode) | keyword={keyword}")

        # CRITICAL: Using SYNC Client inside async thread pool to bypass WAF TLS fingerprinting
        def _fetch_all():
            headers = self.HEADERS.copy()
            headers["User-Agent"] = random.choice(self.USER_AGENTS)

            with httpx.Client(headers=headers, follow_redirects=True, timeout=20.0) as client:
                try:
                    # 1. Warm-up
                    warmup_res = client.get(f"https://www.104.com.tw/jobs/search/?keyword={keyword}")
                    if warmup_res.status_code == 403:
                        logger.warning("403 Detected during warm-up. UA rotation triggered.")
                        headers["User-Agent"] = random.choice(self.USER_AGENTS)
                        client.headers.update(headers)
                        import time
                        time.sleep(5)
                except Exception as e:
                    logger.warning(f"Warm-up failed: {e}")

                # 2. Fetch List
                jobs = self._fetch_from_104_sync(client, keyword, limit)
                if not jobs:
                    return []

                # 3. Fetch Details
                for i, job in enumerate(jobs):
                    if job.real_id:
                        if i > 0:
                            import time
                            time.sleep(random.uniform(2.0, 5.0)) # Increased delay for safety

                        detail = self._fetch_job_detail_sync(client, job.real_id, job.url)
                        job.description_full = detail or f"[Snippet Only] {job.description}"

                return jobs

        # Run sync blocks in executor to not block event loop
        try:
            loop = asyncio.get_event_loop()
            jobs = cast(list[JobData], await loop.run_in_executor(None, _fetch_all))

            # 5. Infer Needs (Async AI processing)
            for job in jobs:
                job.identified_need = await self._infer_need(job)

            logger.info(f"Job search completed | count={len(jobs)}")
            return jobs
        except Exception as e:
            logger.error(f"Job search failed: {e}")
            return []

    async def auto_fetch_daily_leads(self) -> int:
        logger.info("Starting daily lead auto-fetch...")
        total_new_leads = 0
        keywords = ["Python", "AI", "Marketing", "Sales"]
        for keyword in keywords:
            try:
                jobs = await self.search_jobs(keyword, limit=4)
                if jobs:
                    total_new_leads += await self.identify_leads_and_save(jobs)
            except Exception as e:
                logger.error(f"Error auto-fetching for '{keyword}': {e}")
            await asyncio.sleep(random.uniform(2.0, 4.0))
        return total_new_leads

    async def identify_leads_and_save(self, jobs: list[JobData]) -> int:
        new_leads_count = 0
        from .stats_service import StatsService
        stats_service = StatsService()

        for job in jobs:
            try:
                existing = self.supabase.table("leads").select("id").eq("company_name", job.company).eq("source_job_url", job.url).execute()
                if existing.data:
                    continue

                lead_data = {
                    "company_name": job.company,
                    "job_title": job.title,
                    "description_snippet": job.description[:500] if job.description else None,
                    "source_job_url": job.url,
                    "status": "new",
                    "identified_need": job.identified_need or await self._infer_need(job),
                }
                res = self.supabase.table("leads").insert(lead_data).execute()
                if res.data:
                    new_leads_count += 1
                    await stats_service.add_agent_action_log(
                        agent_name="Alice", xp_change=10,
                        message=f"Identified new lead: {job.company}",
                        details={"company": job.company}, content=lead_data["identified_need"]
                    )
            except Exception as e:
                logger.error(f"Failed to save lead: {e}")
        return new_leads_count

    async def _infer_need(self, job: JobData) -> str:
        try:
            from ..services.credential_service import credential_service
            api_key = await credential_service.get_credential(
                "GEMINI_API_KEY"
            ) or await credential_service.get_credential("GOOGLE_API_KEY")
            if not api_key:
                return f"Hiring for {job.title}"

            from google import genai
            client = genai.Client(api_key=api_key)
            prompt = f"Analyze job needs: {job.title} at {job.company}. Desc: {job.description_full or job.description}"
            response = client.models.generate_content(model="gemini-2.0-flash-lite", contents=prompt)
            return str(response.text).strip() if response.text else f"Hiring for {job.title}"
        except Exception:
            return f"Hiring for {job.title}"

    def _fetch_from_104_sync(self, client: httpx.Client, keyword: str, limit: int) -> list[JobData]:
        params = {"ro": "0", "kwop": "7", "keyword": keyword, "order": "1", "asc": "0", "page": "1", "mode": "s", "jobsource": "2018indexpoc"}
        try:
            # Manually get path to avoid await in sync method
            base_url = self.DEFAULT_BASE_URL
            response = client.get(base_url, params=params)
            if response.status_code != 200 or "application/json" not in response.headers.get("content-type", ""):
                return []

            data = response.json()
            raw_jobs = data.get("data", [])
            parsed_jobs = []
            for item in raw_jobs[:limit]:
                raw_link = item.get("link", {}).get("job", "")
                url = f"https:{raw_link}" if raw_link.startswith("//") else raw_link
                real_id = url.split("?")[0].split("/job/")[1] if "/job/" in url else None
                parsed_jobs.append(JobData(
                    title=item.get("jobName", "Unknown"), company=item.get("custName", "Unknown"),
                    url=url, description=item.get("jobDesc", ""), source="104", real_id=real_id
                ))
            return parsed_jobs
        except Exception:
            return []

    def _fetch_job_detail_sync(self, client: httpx.Client, job_id: str, job_url: str | None) -> str | None:
        try:
            url = f"{self.DEFAULT_DETAIL_BASE_URL}{job_id}"
            headers = self.HEADERS.copy()
            if job_url:
                headers["Referer"] = job_url
                client.get(job_url, headers=headers)
            response = client.get(url, headers=headers)
            return response.json().get("data", {}).get("jobDetail", {}).get("jobDescription") if response.status_code == 200 else None
        except Exception:
            return None
