import logging

from pydantic import BaseModel, Field

from server.services.crawling.crawling_service import CrawlingService
from server.services.job_board_service import JobBoardService

logger = logging.getLogger(__name__)


class SearchJobMarketTool(BaseModel):
    """
    Searches for job market data (e.g., from 104 Job Bank) to gather requirements for a specific role.
    Use this to understand what skills and qualifications are currently in demand.
    """

    keyword: str = Field(
        ..., description="The job title or keyword to search for (e.g., 'Python Engineer', 'Marketing Manager')."
    )
    limit: int = Field(8, description="Maximum number of job listings to retrieve. Default is 8.")

    async def execute(self) -> str:
        """Executes the job search."""
        try:
            # Call the service
            jobs = await JobBoardService.search_jobs(keyword=self.keyword, limit=self.limit)

            if not jobs:
                return f"No jobs found for keyword '{self.keyword}'."

            # Format the output for the Agent
            result_str = f"Found {len(jobs)} jobs for '{self.keyword}':\n\n"
            for i, job in enumerate(jobs, 1):
                skills_str = ", ".join(job.skills) if job.skills else "None"
                result_str += f"{i}. {job.title} at {job.company}\n"
                result_str += f"   Location: {job.location}\n"
                result_str += f"   Salary: {job.salary}\n"
                result_str += f"   Skills: {skills_str}\n"
                result_str += f"   URL: {job.url}\n\n"

            return result_str

        except Exception as e:
            return f"Error searching job market: {str(e)}"


class PerformWebCrawlTool(BaseModel):
    """
    Triggers a deep background web crawl for a given URL via the CrawlingService.
    Useful for building knowledge bases and researching competitors.
    """

    tool_name: str = "perform_web_crawl"
    url: str = Field(..., description="The target URL to crawl")
    max_depth: int = Field(2, description="Maximum link depth (default 2)")

    async def execute(self) -> str:
        """Trigger a deep background web crawl."""
        try:
            logger.info(f"🕷️ MCP Tool: Starting crawl for {self.url}")
            crawler = CrawlingService()
            # Note: We use admin role as default for system-triggered crawls
            await crawler.orchestrate_crawl({"url": self.url, "max_depth": self.max_depth, "user_role": "admin"})
            return f"✅ Successfully started background web crawl for {self.url}"
        except Exception as e:
            return f"❌ Crawler error: {str(e)}"


marketing_tools = [
    SearchJobMarketTool,
]


marketing_crawler_tools = [
    PerformWebCrawlTool,
]
