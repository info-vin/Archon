import asyncio
import random
from typing import Any, TypedDict, cast

from ..config.logfire_config import get_logger
from ..repositories.base_repository import BaseRepository
from ..utils import get_supabase_client

# Import new crawler client
from .crawling.clients.job104_client import CrawlerBlockedException, Job104Crawler, JobData

logger = get_logger(__name__)


class LeadDataDTO(TypedDict):
    company_name: str
    job_title: str
    description_snippet: str | None
    source_job_url: str | None
    status: str
    identified_need: str



class JobBoardService(BaseRepository):
    """
    Service to interact with external job boards.
    Delegates actual HTTP crawling to Job104Crawler.
    """



    def __init__(self, supabase_client: Any = None) -> None:
        super().__init__(supabase_client or get_supabase_client())
        self.supabase = self.supabase_client
        from ..utils.rate_limiter import RateLimitConfig, RateLimiter
        self.rate_limiter = RateLimiter(RateLimitConfig())
        self.crawler = Job104Crawler()
        from .crawling.lead_evaluator import LeadEvaluator
        self.evaluator = LeadEvaluator(self.rate_limiter)

    def _get_crawler_config(self) -> Any:
        from ..schemas.settings import CrawlerJobConfig
        from ..services.settings_service import SettingsService
        try:
            settings = SettingsService(self.supabase)
            return CrawlerJobConfig.model_validate(settings.get_all_settings())
        except Exception as e:
            logger.warning(f"Failed to parse CrawlerJobConfig, falling back to defaults: {e}")
            from ..schemas.settings import CrawlerJobConfig
            return CrawlerJobConfig()

    def _log_archon(self, source: str, level: str, message: str) -> None:
        try:
            query = self.supabase.table("archon_logs").insert({"source": source, "level": level, "message": message})
            self.execute_query(query, error_context="Write to archon_logs")
        except Exception as e:
            logger.error(f"Failed to write to archon_logs: {e}")

    async def search_jobs(self, keyword: str, limit: int = 8, client: Any = None, page: int = 1) -> list[JobData]:
        # Delegate search to crawler
        jobs = await self.crawler.search_jobs(keyword, limit, client, page=page)
        # Infer Needs (Async AI processing concurrently)
        import asyncio
        needs = await asyncio.gather(*(self.evaluator.infer_need(job) for job in jobs))
        for job, need in zip(jobs, needs, strict=False):
            job.identified_need = need
            job.keyword = keyword
        return jobs

    async def auto_fetch_daily_leads(self) -> int:
        logger.info("Starting daily lead auto-fetch...")
        total_new_leads = 0

        config = self._get_crawler_config()
        keywords = [k.strip() for k in config.crawler_job_keywords.split(",")]
        limit = config.crawler_job_limit
        max_pages = getattr(config, "crawler_max_pages", 3)

        session = self.crawler.create_session()
        try:
            blocked = False
            for page in range(1, max_pages + 1):
                logger.info(f"Crawling page {page} for all keywords...")
                for keyword in keywords:
                    try:
                        jobs = await self.search_jobs(keyword, limit=limit, client=session, page=page)
                        if jobs:
                            total_new_leads += await self.identify_leads_and_save(jobs)
                    except CrawlerBlockedException as e:
                        logger.error(f"Crawler blocked by WAF for '{keyword}': {e}")
                        self._log_archon(
                            source="job_board_service",
                            level="ALERT",
                            message=f"104 Crawler Blocked by WAF: {e}"
                        )
                        blocked = True
                        break  # Stop crawling other keywords if blocked
                    except Exception as e:
                        logger.error(f"Error auto-fetching for '{keyword}' on page {page}: {e}")
                    await asyncio.sleep(random.uniform(config.crawler_waf_delay_min, config.crawler_waf_delay_max))

                if blocked:
                    break

                if total_new_leads > 0:
                    logger.info(f"Successfully fetched {total_new_leads} new leads. Stopping auto-fetch.")
                    break
                else:
                    logger.info(f"0 leads fetched after page {page}. Falling back to next page...")
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
            query = self.supabase.table("leads").select("source_job_url").in_("source_job_url", job_urls) # 合法
            success, result = self.execute_query(query, "Fetch existing leads urls")
            if success and result.get("data"):
                existing_urls = {row["source_job_url"] for row in result.get("data", [])}

        baseline_embedding = await self.evaluator.get_hyde_baseline_embedding()

        async def _process_single_job(job: JobData) -> LeadDataDTO | None:
            try:
                # RAG Vector Matching against HyDE Baseline
                if not baseline_embedding:
                    logger.error(f"Lead discarded. HyDE Baseline missing, failing fast. Company: {job.company}")
                    return None

                from ..services.embeddings.embedding_service import create_embedding
                desc = job.description_full or job.description or ""
                job_text = f"{job.title} {desc[:1500]}"
                job_embedding = await create_embedding(job_text)

                if not job_embedding:
                    return None

                sim = self.evaluator.cosine_similarity(baseline_embedding, job_embedding)
                config = self._get_crawler_config()
                threshold = config.lead_gen_similarity_threshold

                # Layer 1: Fast Fail on Vector Similarity
                if sim < threshold:
                    # Log discarded
                    self._log_archon(
                        source="job_board_service_rag",
                        level="DEBUG",
                        message=f"Lead discarded. Similarity: {sim:.3f} < {threshold}. Keyword: {job.keyword}. Company: {job.company}"
                    )
                    return None

                # Layer 2: LLM Judge (Reject competitors)
                is_lead = await self.evaluator.llm_judge(job)
                if not is_lead:
                    self._log_archon(
                        source="job_board_service_judge",
                        level="DEBUG",
                        message=f"Lead discarded by LLM Judge. Similarity: {sim:.3f}. Keyword: {job.keyword}. Company: {job.company}"
                    )
                    return None

                # Generate the identified need only if it passes both layers
                identified_need = job.identified_need or await self.evaluator.infer_need(job)

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
            query = self.supabase.table("leads").insert(leads_to_insert) # 合法
            success, result = self.execute_query(query, "Bulk insert leads")

            if success and result.get("data"):
                res_data = result.get("data", [])
                new_leads_count += len(res_data)

                from ..services.agent_registry import get_agent_config
                market_bot_config = cast(dict[str, Any], get_agent_config("market-bot") or {})
                agent_name = market_bot_config.get("name", "Archon MarketBot")

                async def _log_action(job: Any, content: str) -> None:
                    await stats_service.add_agent_action_log(
                        agent_name=agent_name,
                        xp_change=10,
                        message=f"Identified new lead: {job.company}",
                        details={"company": job.company},
                        content=content,
                    )

                tasks = [
                    _log_action(jobs_to_insert[idx], inserted_lead.get("identified_need", jobs_to_insert[idx].identified_need))
                    for idx, inserted_lead in enumerate(res_data)
                ]
                if tasks:
                    await asyncio.gather(*tasks)

        return new_leads_count
