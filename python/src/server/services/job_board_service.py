import asyncio
import random
from typing import cast

from curl_cffi import requests as curl_requests
from pydantic import BaseModel

from ..config.logfire_config import get_logger
from ..config.model_ssot import SYSTEM_MODELS
from ..utils import get_supabase_client
from ..utils.retry_utils import retry_with_backoff

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
        from ..utils.rate_limiter import RateLimitConfig, RateLimiter
        self.rate_limiter = RateLimiter(RateLimitConfig())

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
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    ]

    # REAL DATA ONLY: MOCK_JOBS remains empty
    MOCK_JOBS: list[JobData] = []

    async def search_jobs(self, keyword: str, limit: int = 8) -> list[JobData]:
        logger.info(f"Searching jobs (Sync-Thru Mode) | keyword={keyword}")

        # CRITICAL: Using SYNC Client inside async thread pool to bypass WAF TLS fingerprinting
        def _fetch_all():
            headers = self.HEADERS.copy()
            # User-Agent rotation is natively handled by curl_cffi impersonate="chrome120"

            with curl_requests.Session(impersonate="chrome120", headers=headers, timeout=20.0) as client:
                warmup_res = None
                try:
                    # 1. Warm-up
                    warmup_res = client.get(f"https://www.104.com.tw/jobs/search/?keyword={keyword}")
                    if warmup_res.status_code == 403:
                        logger.warning("403 Detected during warm-up. WAF might be blocking curl_cffi.")
                        import time

                        time.sleep(5)
                except Exception as e:
                    logger.warning(f"Warm-up failed: {e}")

                # 2. Fetch List
                jobs = self._fetch_from_104_sync(client, keyword, limit)
                if not jobs:
                    if warmup_res and warmup_res.status_code == 403:
                        raise CrawlerBlockedException("104 WAF Blocked access.")
                    return []

                # 3. Fetch Details
                for i, job in enumerate(jobs):
                    if job.real_id:
                        if i > 0:
                            import time

                            time.sleep(random.uniform(2.0, 5.0))  # Increased delay for safety

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
        except CrawlerBlockedException:
            raise
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
            except CrawlerBlockedException as e:
                logger.error(f"Crawler blocked by WAF for '{keyword}': {e}")
                self.supabase.table("archon_logs").insert({
                    "source": "job_board_service",
                    "level": "ALERT",
                    "message": f"104 Crawler Blocked by WAF: {e}"
                }).execute()
                break  # Stop crawling other keywords if blocked
            except Exception as e:
                logger.error(f"Error auto-fetching for '{keyword}': {e}")
            await asyncio.sleep(random.uniform(2.0, 4.0))
        return total_new_leads

    async def identify_leads_and_save(self, jobs: list[JobData]) -> int:
        new_leads_count = 0
        from .stats import StatsService

        stats_service = StatsService()

        leads_to_insert = []
        jobs_to_insert = []

        # FIX N+1 SELECT: Bulk query existing URLs
        job_urls = [job.url for job in jobs if job.url]
        existing_urls = set()
        if job_urls:
            try:
                existing = (
                    self.supabase.table("leads")
                    .select("source_job_url")
                    .in_("source_job_url", job_urls)
                    .execute()
                )
                if existing.data:
                    existing_urls = {row["source_job_url"] for row in existing.data}
            except Exception as e:
                logger.error(f"Failed to fetch existing leads: {e}")

        for job in jobs:
            if job.url in existing_urls:
                continue

            try:
                lead_data = {
                    "company_name": job.company,
                    "job_title": job.title,
                    "description_snippet": job.description[:500] if job.description else None,
                    "source_job_url": job.url,
                    "status": "new",
                    "identified_need": job.identified_need or await self._infer_need(job),
                }
                leads_to_insert.append(lead_data)
                jobs_to_insert.append(job)
            except Exception as e:
                logger.error(f"Failed to process lead data: {e}")

        if leads_to_insert:
            try:
                res = self.supabase.table("leads").insert(leads_to_insert).execute()
                if res.data:
                    new_leads_count += len(res.data)

                    async def _log_action(job, content):
                        await stats_service.add_agent_action_log(
                            agent_name="Alice",
                            xp_change=10,
                            message=f"Identified new lead: {job.company}",
                            details={"company": job.company},
                            content=content,
                        )

                    tasks = [
                        _log_action(jobs_to_insert[idx], inserted_lead.get("identified_need", jobs_to_insert[idx].identified_need))
                        for idx, inserted_lead in enumerate(res.data)
                    ]
                    if tasks:
                        await asyncio.gather(*tasks)
            except Exception as e:
                logger.error(f"Failed to bulk insert leads: {e}")

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

            from ..services.prompt_service import prompt_service

            client = genai.Client(api_key=api_key)

            default_prompt = (
                "You are a sales assistant helping Alice (Sales Rep) analyze a job posting quickly on her mobile phone.\n"
                "Job: {title} at {company}\n"
                "Desc: {desc}\n\n"
                "Output exactly 2 short markdown bullet points (max 50 words each) using Traditional Chinese (繁體中文):\n"
                "- **技術棧**: [關鍵字與技術需求]\n"
                "- **痛點預測**: [可能面臨的業務痛點與需求]"
            )

            prompt_template = prompt_service.get_prompt("ALICE_INFER_NEED", default=default_prompt)
            prompt = prompt_template.format(
                title=job.title, company=job.company, desc=(job.description_full or job.description)
            )

            @retry_with_backoff(max_retries=4, initial_delay=2.0)
            async def _call_gemini():
                return await client.aio.models.generate_content(model=SYSTEM_MODELS["DEFAULT_TEXT"], contents=prompt)

            await self.rate_limiter.acquire(estimated_tokens=400)
            response = await _call_gemini()
            return str(response.text).strip() if response.text else f"Hiring for {job.title}"
        except Exception as e:
            logger.error(f"Need inference failed: {e}")
            return f"Hiring for {job.title}"

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
            url = f"{self.DEFAULT_DETAIL_BASE_URL}{job_id}"
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
