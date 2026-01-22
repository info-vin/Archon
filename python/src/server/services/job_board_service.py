import asyncio
import random

import httpx
from pydantic import BaseModel

from ..config.logfire_config import get_logger, logfire
from ..utils import get_supabase_client

logger = get_logger(__name__)

class JobData(BaseModel):
    title: str
    company: str
    location: str | None = None
    salary: str | None = None
    url: str | None = None
    description: str | None = None
    description_full: str | None = None # ADDED: Full Job Description
    skills: list[str] | None = None
    source: str = "104"
    company_website: str | None = None # ADDED: Official Company Website
    identified_need: str | None = None  # ADDED: AI/Logic inferred need
    real_id: str | None = None # Internal Use: For AJAX fetching

class JobBoardService:
    """
    Service to interact with external job boards (specifically 104.com.tw).
    Uses direct AJAX simulation for performance, with a Mock fallback for reliability.
    """

    # UPDATED: Valid Endpoint as of Jan 2026
    BASE_URL = "https://www.104.com.tw/jobs/search/api/jobs"
    DETAIL_BASE_URL = "https://www.104.com.tw/job/ajax/content/"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.104.com.tw/jobs/search/",
        "Accept": "application/json, text/plain, */*",
        "X-Requested-With": "XMLHttpRequest"
    }

    # Static Mock Data for Fallback
    MOCK_JOBS = [
        JobData(
            title="Senior Data Analyst",
            company="Retail Corp",
            location="Taipei City",
            salary="1.5M - 2.5M TWD/Year",
            url="https://www.104.com.tw/job/mock-retail-1",
            description="We are looking for an expert in BI tools and SQL.",
            description_full="Full job description: We are looking for an expert in BI tools and SQL. Responsibilities include...",
            skills=["SQL", "Tableau", "Python"],
            source="mock",
            identified_need="Hiring Data Analyst -> Potential BI Tool Customer"
        ),
        JobData(
            title="AI Solutions Engineer",
            company="Future Systems",
            location="Remote",
            salary="Negotiable",
            url="https://www.104.com.tw/job/mock-ai-1",
            description="Build the next generation of AI tools using LLMs.",
            description_full="Full job description: Build the next generation of AI tools using LLMs. Requirements: 5+ years exp...",
            skills=["Python", "LangChain", "OpenAI"],
            source="mock",
            identified_need="Developing AI Features -> Needs LLM Ops / Archon"
        )
    ]

    @classmethod
    async def search_jobs(cls, keyword: str, limit: int = 10) -> list[JobData]:
        """
        Search for jobs using keyword and identify potential leads.
        Now also fetches full job details for each result.
        """
        logfire.info(f"Searching jobs | keyword={keyword} | limit={limit}")

        # Use a single session for the entire lifecycle to maintain cookies (Anti-Scraping)
        async with httpx.AsyncClient(timeout=20.0, headers=cls.HEADERS, follow_redirects=True) as client:
            try:
                # 1. Fetch List
                jobs = await cls._fetch_from_104(client, keyword, limit)

                if not jobs:
                    logfire.warning("104 API returned empty list, falling back to mock")
                    jobs = cls.MOCK_JOBS
                else:
                    # 2. Fetch Details (Only if we have real jobs)
                    for i, job in enumerate(jobs):
                        # Infer need first
                        job.identified_need = cls._infer_need(job)

                        if job.real_id:
                            # Throttling: Random delay to mimic human behavior
                            if i > 0:
                                delay = random.uniform(1.5, 3.0)
                                await asyncio.sleep(delay)

                            try:
                                detail = await cls._fetch_job_detail(client, job.real_id, job.url)
                                if detail:
                                    job.description_full = detail
                                    logfire.info(f"Fetched detail | id={job.real_id} | len={len(detail)}")
                                else:
                                    job.description_full = f"[Snippet Only] {job.description}"
                            except Exception as e:
                                logfire.warning(f"Failed to fetch job detail | url={job.url} | error={e}")
                                job.description_full = f"[Snippet Only] {job.description}"
                        else:
                            job.description_full = f"[Snippet Only] {job.description}"

                logfire.info(f"Job search completed | count={len(jobs)}")
                return jobs

            except Exception as e:
                logfire.error(f"Job search failed | error={str(e)} | switching_to_fallback=True")
                # Ensure mock jobs also have inferred needs
                for job in cls.MOCK_JOBS:
                    if not job.identified_need:
                        job.identified_need = cls._infer_need(job)
                return cls.MOCK_JOBS

    @classmethod
    async def identify_leads_and_save(cls, jobs: list[JobData]) -> int:
        """
        Filters jobs into leads and saves them to the 'leads' database table.
        Returns the number of new leads saved.
        """
        supabase = get_supabase_client()
        new_leads_count = 0

        for job in jobs:
            try:
                # 1. Check if lead already exists (by company name and source URL)
                existing = supabase.table("leads").select("id").eq("company_name", job.company).eq("source_job_url", job.url).execute()

                if existing.data:
                    continue

                # 2. Save new lead
                lead_data = {
                    "company_name": job.company,
                    "source_job_url": job.url,
                    "status": "new",
                    "identified_need": job.identified_need or cls._infer_need(job)
                }

                # Store full description in metadata if possible, or extend table later.
                # For now, we just stick to the existing schema.

                supabase.table("leads").insert(lead_data).execute()
                new_leads_count += 1
                logfire.info(f"New lead identified and saved | company={job.company}")

            except Exception as e:
                logfire.error(f"Failed to save lead | company={job.company} | error={str(e)}")

        return new_leads_count

    @staticmethod
    def _infer_need(job: JobData) -> str:
        """
        Simple heuristic logic to infer business need from job title/description.
        In a real scenario, this could be an LLM-powered analysis.
        """
        title = job.title.lower()
        desc = (job.description or "").lower()

        if "analyst" in title or "data" in title or "tableau" in desc:
            return "Hiring Data Talent -> High potential for BI/Data Tooling."
        elif "ai" in title or "ml" in title or "llm" in desc:
            return "Building AI Capabilities -> Target for Archon/Agent framework."
        elif "marketing" in title or "sales" in title:
            return "Expanding Growth Team -> Needs Sales Intelligence/Lead Gen tools."
        else:
            return f"Hiring for {job.title} -> General digital transformation lead."

    @classmethod
    async def _fetch_from_104(cls, client: httpx.AsyncClient, keyword: str, limit: int) -> list[JobData]:
        """
        Internal method to fetch job list.
        Now uses the passed client to share session cookies.
        """
        params = {
            "ro": "0",
            "kwop": "7",
            "keyword": keyword,
            "expansionType": "area,spec,com,job,wf,wktm",
            "order": "1",
            "asc": "0",
            "page": "1",
            "mode": "s",
            "jobsource": "2018indexpoc",
        }

        # Visit search home first to set cookies (Important!)
        await client.get("https://www.104.com.tw/jobs/search/", params={"keyword": keyword})

        response = await client.get(cls.BASE_URL, params=params)

        if response.status_code != 200:
            raise Exception(f"API Error: {response.status_code}")

        data = response.json()

        # Validation
        if "data" not in data:
            raise Exception("Invalid API Response Structure")

        raw_jobs = data.get("data", [])
        parsed_jobs = []

        for item in raw_jobs[:limit]:
            # Safe Extraction
            title = item.get("jobName", "Unknown Title")
            company = item.get("custName", "Unknown Company")

            # Extract URL securely and get the real Job ID (alphanumeric)
            # 104 returns link dictionary with 'job' key like "//www.104.com.tw/job/8u3r5?jobsource=..."
            raw_link = item.get("link", {}).get("job", "")

            real_id = None
            url = None

            if raw_link:
                url = f"https:{raw_link}" if raw_link.startswith("//") else raw_link
                # Extract ID: /job/8u3r5? -> 8u3r5
                try:
                    if "/job/" in url:
                        # Extract the segment after /job/ and before any ?
                        real_id = url.split("?")[0].split("/job/")[1]
                except Exception:
                    pass
            else:
                # Fallback construction (usually won't work for AJAX but keeps URL valid)
                job_no = item.get("jobNo")
                url = f"https://www.104.com.tw/job/{job_no}" if job_no else None

            # Description snippet
            desc = item.get("jobDesc", "")

            # Location & Salary
            location = item.get("jobAddrNoDesc") or item.get("jobAddress")
            salary = item.get("salaryDesc")

            # Tags/Skills
            skills = []
            tags = item.get("tags", [])
            if tags:
                skills = [t.get("desc") for t in tags if "desc" in t]

            parsed_jobs.append(JobData(
                title=title,
                company=company,
                location=location,
                salary=salary,
                url=url,
                description=desc,
                skills=skills,
                source="104",
                real_id=real_id # Stored for next step
            ))

        return parsed_jobs

    @classmethod
    async def _fetch_job_detail(cls, client: httpx.AsyncClient, job_id: str, job_url: str | None) -> str | None:
        """
        Fetches the full job description using the shared client.
        Requires valid job_id (alphanumeric) and job_url (for Referer).
        """
        try:
            if not job_id:
                return None

            ajax_url = f"{cls.DETAIL_BASE_URL}{job_id}"

            # Headers must have Referer matching the job page
            headers = cls.HEADERS.copy()
            if job_url:
                headers["Referer"] = job_url

            response = await client.get(ajax_url, headers=headers)

            if response.status_code != 200:
                logfire.warning(f"Job AJAX fetch failed | status={response.status_code} | url={ajax_url}")
                return None

            data = response.json()

            # Extract description from JSON structure
            # Path: data -> jobDetail -> jobDescription
            job_desc = data.get("data", {}).get("jobDetail", {}).get("jobDescription")

            if job_desc:
                return job_desc

            return None

        except Exception as e:
            logfire.warning(f"Error fetching job detail via AJAX | id={job_id} | error={e}")
            return None
