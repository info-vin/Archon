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
    skills: list[str] | None = None
    source: str = "104"
    identified_need: str | None = None  # ADDED: AI/Logic inferred need

class JobBoardService:
    """
    Service to interact with external job boards (specifically 104.com.tw).
    Uses direct AJAX simulation for performance, with a Mock fallback for reliability.
    """

    BASE_URL = "https://www.104.com.tw/jobs/search/list"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.104.com.tw/jobs/search/",
        "Accept": "application/json, text/javascript, */*; q=0.01",
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
            skills=["Python", "LangChain", "OpenAI"],
            source="mock",
            identified_need="Developing AI Features -> Needs LLM Ops / Archon"
        )
    ]

    @classmethod
    async def search_jobs(cls, keyword: str, limit: int = 10) -> list[JobData]:
        """
        Search for jobs using keyword and identify potential leads.
        """
        logfire.info(f"Searching jobs | keyword={keyword} | limit={limit}")

        try:
            jobs = await cls._fetch_from_104(keyword, limit)
            if not jobs:
                logfire.warning("104 API returned empty list, falling back to mock")
                jobs = cls.MOCK_JOBS

            # Analyze needs for each job
            for job in jobs:
                job.identified_need = cls._infer_need(job)

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
    async def _fetch_from_104(cls, keyword: str, limit: int) -> list[JobData]:
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
            "langFlag": "0",
            "langStatus": "0",
            "recommendJob": "1",
            "hotJob": "1",
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(cls.BASE_URL, headers=cls.HEADERS, params=params)

            if response.status_code != 200:
                raise Exception(f"API Error: {response.status_code}")

            data = response.json()

            # Validation
            if "data" not in data or "list" not in data["data"]:
                raise Exception("Invalid API Response Structure")

            raw_jobs = data["data"]["list"]
            parsed_jobs = []

            for item in raw_jobs[:limit]:
                # Safe Extraction
                title = item.get("jobName", "Unknown Title")
                company = item.get("custName", "Unknown Company")
                # 104 returns link dictionary or constructed ID
                # Construct URL: https://www.104.com.tw/job/{jobNo}
                job_no = item.get("jobNo")
                url = f"https://www.104.com.tw/job/{job_no}" if job_no else None

                # Description often comes as 'jobDesc' or needs to be fetched separately.
                # In the list view, 'jobDesc' is a snippet.
                desc = item.get("jobDesc", "")  # Often truncated in list view

                # Location
                location = item.get("jobAddrNoDesc") or item.get("jobAddress")

                # Salary
                salary = item.get("salaryDesc")

                # Tags/Skills (Parsing from tags or desc)
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
                    source="104"
                ))

            return parsed_jobs
