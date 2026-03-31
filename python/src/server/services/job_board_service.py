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
    Uses direct AJAX simulation for performance.
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

    # REAL DATA ONLY: MOCK_JOBS is now empty
    MOCK_JOBS: list[JobData] = []

    async def search_jobs(self, keyword: str, limit: int = 10) -> list[JobData]:
        logger.info(f"Searching jobs | keyword={keyword} | limit={limit}")

        async with httpx.AsyncClient(timeout=20.0, headers=self.HEADERS, follow_redirects=True) as client:
            try:
                # 1. Fetch List
                jobs = await self._fetch_from_104(client, keyword, limit)

                if not jobs:
                    logger.warning("104 API returned empty list or blocked.")
                    return []

                # 2. Fetch Details
                for i, job in enumerate(jobs):
                    if job.real_id:
                        if i > 0:
                            await asyncio.sleep(random.uniform(1.3, 2.7))

                        try:
                            detail = await self._fetch_job_detail(client, job.real_id, job.url)
                            if detail:
                                job.description_full = detail
                            else:
                                job.description_full = f"[Snippet Only] {job.description}"
                        except Exception as e:
                            logger.warning(f"Failed to fetch job detail | url={job.url} | error={e}")
                            job.description_full = f"[Snippet Only] {job.description}"

                    # Infer need after description is fetched
                    job.identified_need = await self._infer_need(job)

                logger.info(f"Job search completed | count={len(jobs)}")
                return jobs

            except Exception as e:
                logger.error(f"Job search failed | error={str(e)}")
                return []

    async def auto_fetch_daily_leads(self) -> int:
        logger.info("Starting daily lead auto-fetch...")
        total_new_leads = 0
        keywords = ["Python", "AI", "Marketing", "Sales"]

        for keyword in keywords:
            try:
                jobs = await self.search_jobs(keyword, limit=4)
                if jobs:
                    new_leads_count = await self.identify_leads_and_save(jobs)
                    total_new_leads += new_leads_count
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
                existing = (
                    self.supabase.table("leads")
                    .select("id")
                    .eq("company_name", job.company)
                    .eq("source_job_url", job.url)
                    .execute()
                )
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

                # Physical Verification: Stop phantom logs if insert failed
                if not res.data and hasattr(res, "error") and res.error:
                    logger.error(f"Failed to save lead | company={job.company} | error={res.error}")
                    continue

                new_leads_count += 1

                # Reward XP for identifying a lead (Phase 4.6.15 Integration)
                await stats_service.add_agent_action_log(
                    agent_name="Alice",
                    xp_change=10,
                    message=f"Identified new lead: {job.company}",
                    details={"company": job.company, "job_title": job.title},
                    content=lead_data["identified_need"],
                )
            except Exception as e:
                logger.error(f"Failed to save lead | company={job.company} | error={str(e)}")
        return new_leads_count

    async def _infer_need(self, job: JobData) -> str:
        try:
            from ..services.credential_service import credential_service

            api_key = await credential_service.get_credential(
                "GEMINI_API_KEY"
            ) or await credential_service.get_credential("GOOGLE_API_KEY")
            if not api_key:
                return f"Hiring for {job.title} at {job.company}"

            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)
            prompt = (
                "Analyze this job posting and extract 2-5 technical tags and a summary of AI/Automation needs.\n"
                f"Format: [Tag1] [Tag2] Summary.\nJob: {job.title} at {job.company}\nDesc: {job.description_full or job.description}"
            )

            response = client.models.generate_content(
                model="gemini-2.0-flash-lite", contents=prompt, config=types.GenerateContentConfig(temperature=0.2)
            )
            return str(response.text).strip() if response.text else f"Hiring for {job.title}"
        except Exception:
            return f"Hiring for {job.title}"

    async def _fetch_from_104(self, client: httpx.AsyncClient, keyword: str, limit: int) -> list[JobData]:
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
        # Pre-warm session
        await client.get("https://www.104.com.tw/jobs/search/", params={"keyword": keyword})

        base_url = await self._get_base_url()
        response = await client.get(base_url, params=params)
        if response.status_code != 200:
            return []

        data = response.json()
        raw_jobs = data.get("data", [])
        parsed_jobs = []

        for item in raw_jobs[:limit]:
            raw_link = item.get("link", {}).get("job", "")
            real_id = None
            url = None
            if raw_link:
                url = f"https:{raw_link}" if raw_link.startswith("//") else raw_link
                if "/job/" in url:
                    real_id = url.split("?")[0].split("/job/")[1]

            parsed_jobs.append(
                JobData(
                    title=item.get("jobName", "Unknown"),
                    company=item.get("custName", "Unknown"),
                    location=item.get("jobAddrNoDesc"),
                    salary=item.get("salaryDesc"),
                    url=url,
                    description=item.get("jobDesc", ""),
                    source="104",
                    real_id=real_id,
                )
            )
        return parsed_jobs

    async def _fetch_job_detail(self, client: httpx.AsyncClient, job_id: str, job_url: str | None) -> str | None:
        try:
            if not job_id:
                return None
            detail_base = await self._get_detail_url()
            ajax_url = f"{detail_base}{job_id}"

            headers = self.HEADERS.copy()
            if job_url:
                headers["Referer"] = job_url
                # CRITICAL: Physical Warm-up for Detail AJAX
                await client.get(job_url, headers={"User-Agent": headers["User-Agent"]}, follow_redirects=True)

            response = await client.get(ajax_url, headers=headers)
            if response.status_code != 200:
                return None

            data = response.json()
            res = data.get("data", {}).get("jobDetail", {}).get("jobDescription")
            return cast(str, res) if res else None
        except Exception:
            return None
