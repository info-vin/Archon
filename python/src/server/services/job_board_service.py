from typing import Any, List, Optional
import httpx
import json
import asyncio
from pydantic import BaseModel

from ..config.logfire_config import get_logger, logfire

logger = get_logger(__name__)

class JobData(BaseModel):
    title: str
    company: str
    location: Optional[str] = None
    salary: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    skills: Optional[List[str]] = None
    source: str = "104"

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
            title="Senior Python Backend Engineer",
            company="Archon Tech Inc.",
            location="Taipei City",
            salary="1.5M - 2.5M TWD/Year",
            url="https://www.104.com.tw/job/mock1",
            description="We are looking for an expert in FastAPI, AsyncIO, and AI Agents.",
            skills=["Python", "FastAPI", "Docker", "PostgreSQL"],
            source="mock"
        ),
        JobData(
            title="AI Fullstack Developer",
            company="Future Systems",
            location="Remote",
            salary="Negotiable",
            url="https://www.104.com.tw/job/mock2",
            description="Build the next generation of AI tools using React and Python.",
            skills=["React", "TypeScript", "Python", "LangChain"],
            source="mock"
        )
    ]

    @classmethod
    async def search_jobs(cls, keyword: str, limit: int = 10) -> List[JobData]:
        """
        Search for jobs using keyword.
        Attempts to fetch from 104 API first. If it fails (network/blocking), returns Mock data.
        """
        logfire.info(f"Searching jobs | keyword={keyword} | limit={limit}")
        
        try:
            jobs = await cls._fetch_from_104(keyword, limit)
            if jobs:
                logfire.info(f"Successfully fetched jobs from 104 | count={len(jobs)}")
                return jobs
            else:
                logfire.warning("104 API returned empty list, falling back to mock")
                return cls.MOCK_JOBS
                
        except Exception as e:
            logfire.error(f"Job search failed | error={str(e)} | switching_to_fallback=True")
            return cls.MOCK_JOBS

    @classmethod
    async def _fetch_from_104(cls, keyword: str, limit: int) -> List[JobData]:
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
