import asyncio
import random
from typing import Any, cast

from ..config.logfire_config import get_logger
from ..config.model_ssot import SYSTEM_MODELS
from ..utils import get_supabase_client
from ..utils.retry_utils import retry_with_backoff

# Import new crawler client
from .crawling.clients.job104_client import CrawlerBlockedException, Job104Crawler, JobData

logger = get_logger(__name__)


class JobBoardService:
    """
    Service to interact with external job boards.
    Delegates actual HTTP crawling to Job104Crawler.
    """

    @staticmethod
    def _cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
        import math
        dot = sum(a * b for a, b in zip(vec1, vec2, strict=False))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        return dot / (norm1 * norm2) if norm1 and norm2 else 0.0

    async def _get_baseline_embedding(self) -> list[float] | None:
        if getattr(self, "_baseline_embedding_cache", None) is not None:
            return self._baseline_embedding_cache # type: ignore

        import os
        from pathlib import Path

        from ..services.embeddings.embedding_service import create_embedding

        # Resolve PROJECT_ROOT dynamically
        project_root = os.environ.get("PROJECT_ROOT")
        if not project_root:
            project_root = str(Path(__file__).resolve().parent.parent.parent.parent)

        # Read AGENTS.md
        agents_md_path = os.path.join(project_root, "AGENTS.md")

        try:
            with open(agents_md_path, encoding="utf-8") as f:
                content = f.read()
                # Extract the core capabilities
                if "## MCP Tools Available" in content:
                    core_text = "Archon Core Capabilities:\n" + content.split("## MCP Tools Available")[1][:2000]
                else:
                    core_text = content[:2000]
                self._baseline_embedding_cache = await create_embedding(core_text)
                return self._baseline_embedding_cache
        except Exception as e:
            logger.error(f"Failed to read or embed AGENTS.md: {e}")
            return None

    def __init__(self):
        self.supabase = get_supabase_client()
        from ..utils.rate_limiter import RateLimitConfig, RateLimiter
        self.rate_limiter = RateLimiter(RateLimitConfig())
        self.crawler = Job104Crawler()

    async def search_jobs(self, keyword: str, limit: int = 8, client: Any = None) -> list[JobData]:
        # Delegate search to crawler
        jobs = await self.crawler.search_jobs(keyword, limit, client)
        # Infer Needs (Async AI processing concurrently)
        import asyncio
        needs = await asyncio.gather(*(self._infer_need(job) for job in jobs))
        for job, need in zip(jobs, needs, strict=False):
            job.identified_need = need
        return jobs

    async def auto_fetch_daily_leads(self) -> int:
        logger.info("Starting daily lead auto-fetch...")
        total_new_leads = 0

        from ..services.settings_service import SettingsService
        settings = SettingsService(self.supabase)

        try:
            from ..schemas.settings import CrawlerJobConfig
            config = CrawlerJobConfig.model_validate(settings.get_all_settings())
        except Exception as e:
            logger.warning(f"Failed to parse CrawlerJobConfig, falling back to defaults: {e}")
            from ..schemas.settings import CrawlerJobConfig
            config = CrawlerJobConfig()

        keywords = [k.strip() for k in config.crawler_job_keywords.split(",")]
        limit = config.crawler_job_limit

        session = self.crawler.create_session()
        try:
            for keyword in keywords:
                try:
                    jobs = await self.search_jobs(keyword, limit=limit, client=session)
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
        finally:
            session.close()

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

        baseline_embedding = await self._get_baseline_embedding()

        async def _process_single_job(job: JobData) -> dict | None:
            try:
                identified_need = job.identified_need or await self._infer_need(job)

                # RAG Vector Matching
                if baseline_embedding:
                    from ..services.embeddings.embedding_service import create_embedding
                    need_embedding = await create_embedding(identified_need)
                    if need_embedding:
                        sim = self._cosine_similarity(baseline_embedding, need_embedding)
                        from ..schemas.settings import CrawlerJobConfig
                        from ..services.settings_service import SettingsService
                        try:
                            settings = SettingsService(self.supabase)
                            config = CrawlerJobConfig.model_validate(settings.get_all_settings())
                        except Exception:
                            config = CrawlerJobConfig()

                        threshold = config.lead_gen_similarity_threshold

                        if sim < threshold:
                            # Log discarded
                            self.supabase.table("archon_logs").insert({
                                "source": "job_board_service_rag",
                                "level": "DEBUG",
                                "message": f"Lead discarded. Similarity: {sim:.3f} < {threshold}. Company: {job.company}"
                            }).execute()
                            return None

                return {
                    "company_name": job.company,
                    "job_title": job.title,
                    "description_snippet": job.description[:500] if job.description else None,
                    "source_job_url": job.url,
                    "status": "new",
                    "identified_need": identified_need,
                }
            except Exception as e:
                logger.error(f"Failed to process lead data: {e}")
                return None

        # PERFORMANCE: Replaced sequential await self._infer_need(job) with asyncio.gather
        import asyncio
        new_jobs = [job for job in jobs if job.url not in existing_urls]
        if new_jobs:
            results = await asyncio.gather(*[_process_single_job(job) for job in new_jobs])
            for job, lead_data in zip(new_jobs, results, strict=False):
                if lead_data:
                    leads_to_insert.append(lead_data)
                    jobs_to_insert.append(job)

        if leads_to_insert:
            try:
                res = self.supabase.table("leads").insert(leads_to_insert).execute()
                if res.data:
                    new_leads_count += len(res.data)

                    from ..services.agent_registry import get_agent_config
                    market_bot_config = cast(dict[str, Any], get_agent_config("market-bot") or {})
                    agent_name = market_bot_config.get("name", "Archon MarketBot")

                    async def _log_action(job, content):
                        await stats_service.add_agent_action_log(
                            agent_name=agent_name,
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
                "你是一位銷售助理。請用繁體中文列出該職缺的：\n"
                "- **技術棧**\n"
                "- **痛點預測**\n\n"
                "Job: {title} at {company}\n"
                "Desc: {desc}"
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
