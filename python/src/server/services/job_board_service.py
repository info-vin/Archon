import asyncio
import random
from typing import Any, NotRequired, TypedDict, cast

from curl_cffi.requests import Session
from supabase import Client

from ..config.logfire_config import get_logger
from ..repositories.base_repository import BaseRepository
from ..schemas.settings import CrawlerJobConfig
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
    enrichment_status: NotRequired[str | None]
    enrichment_score: NotRequired[int | None]
    identified_need: str




class JobBoardService(BaseRepository):
    """
    Service to interact with external job boards.
    Delegates actual HTTP crawling to Job104Crawler.
    """



    def __init__(self, supabase_client: Client | None = None) -> None:
        super().__init__(supabase_client or get_supabase_client())
        self.supabase = self.supabase_client
        from ..utils.rate_limiter import RateLimitConfig, RateLimiter
        self.rate_limiter = RateLimiter(RateLimitConfig())
        self.crawler = Job104Crawler()
        from .crawling.lead_evaluator import LeadEvaluator
        self.evaluator = LeadEvaluator(self.rate_limiter)

    def _get_crawler_config(self) -> CrawlerJobConfig:
        from ..services.settings_service import SettingsService
        try:
            settings = SettingsService(self.supabase)
            return CrawlerJobConfig.model_validate(settings.get_all_settings())
        except Exception as e:
            logger.warning(f"Failed to parse CrawlerJobConfig, falling back to defaults: {e}")
            return CrawlerJobConfig()

    def _log_archon(self, source: str, level: str, message: str) -> None:
        try:
            query = self.supabase.table("archon_logs").insert({"source": source, "level": level, "message": message})
            self.execute_query(query, error_context="Write to archon_logs")
        except Exception as e:
            logger.error(f"Failed to write to archon_logs: {e}")

    async def search_jobs(self, keyword: str, limit: int = 8, client: Session | None = None, page: int = 1) -> list[JobData]:
        # Delegate search to crawler
        jobs = await self.crawler.search_jobs(keyword, limit, client, page=page)
        for job in jobs:
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
            for keyword in keywords:
                keyword_new_leads = 0
                for page in range(1, max_pages + 1):
                    logger.info(f"Crawling page {page} for keyword '{keyword}'...")
                    try:
                        jobs = await self.search_jobs(keyword, limit=limit, client=session, page=page)
                        if jobs:
                            new_leads = await self.identify_leads_and_save(jobs)
                            keyword_new_leads += new_leads
                            total_new_leads += new_leads
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

                    if keyword_new_leads > 0:
                        logger.info(f"Successfully fetched {keyword_new_leads} new leads for '{keyword}'. Moving to next keyword.")
                        break
                    else:
                        logger.info(f"0 leads fetched for '{keyword}' after page {page}. Falling back to next page...")

                if blocked:
                    break
        finally:
            session.close()

        return total_new_leads

    @staticmethod
    def _apply_ab_quota(candidates: list[tuple[JobData, LeadDataDTO, str]]) -> list[tuple[JobData, LeadDataDTO, str]]:
        """Apply A:B = 60:40 quota to qualified leads without multiplying score weights."""
        qualified_a = [c for c in candidates if c[1]["status"] == "qualified" and c[2] == "A"]
        qualified_b = [c for c in candidates if c[1]["status"] == "qualified" and c[2] == "B"]
        if not qualified_a or not qualified_b:
            return candidates

        # 60:40 quota => max B qualified = floor(len(A) * 40 / 60)
        max_b = max(1, (len(qualified_a) * 40) // 60)
        qualified_b_sorted = sorted(qualified_b, key=lambda c: c[1].get("enrichment_score") or 0, reverse=True)
        demote_urls = {c[0].url for c in qualified_b_sorted[max_b:]}
        for job, lead_data, category in candidates:
            if category == "B" and lead_data["status"] == "qualified" and job.url in demote_urls:
                lead_data["status"] = "archived"
        return candidates

    async def identify_leads_and_save(self, jobs: list[JobData]) -> int:
        new_leads_count = 0
        from .stats import StatsService

        stats_service = StatsService()

        leads_to_insert: list[LeadDataDTO] = []
        jobs_to_insert: list[JobData] = []
        rejected_logs: list[dict[str, Any]] = []

        # FIX N+1 SELECT: Bulk query existing URLs
        job_urls = [job.url for job in jobs if job.url]
        existing_urls = set()
        if job_urls:
            query = self.supabase.table("leads").select("source_job_url").in_("source_job_url", job_urls) # 合法
            success, result = self.execute_query(query, "Fetch existing leads urls")
            if success and result.get("data"):
                existing_urls = {row["source_job_url"] for row in result.get("data", [])}

        baseline_embedding = await self.evaluator.get_hyde_baseline_embedding()

        async def _process_single_job(job: JobData) -> tuple[LeadDataDTO, str] | None:
            try:
                # RAG Vector Matching against HyDE Baseline
                if not baseline_embedding:
                    logger.error(f"Lead discarded. HyDE Baseline missing, failing fast. Company: {job.company}")
                    rejected_logs.append({
                        "source": "job_board_service_triage",
                        "level": "INFO",
                        "message": f"Lead rejected [layer1_baseline_missing]: {job.company} - {job.title}",
                        "details": {
                            "stage": "layer1_baseline_missing",
                            "company": job.company,
                            "job_title": job.title,
                            "url": job.url,
                            "keyword": job.keyword,
                            "reason": "HyDE Baseline missing",
                        },
                    })
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

                # Layer 1: Fast Fail on Vector Similarity (G1 structured rejection log)
                if sim < threshold:
                    rejected_logs.append({
                        "source": "job_board_service_triage",
                        "level": "INFO",
                        "message": f"Lead rejected [layer1_similarity]: {job.company} - {job.title}",
                        "details": {
                            "stage": "layer1_similarity",
                            "company": job.company,
                            "job_title": job.title,
                            "url": job.url,
                            "keyword": job.keyword,
                            "similarity": round(sim, 4),
                            "threshold": threshold,
                            "category": "X",
                            "confidence": 0.0,
                            "reason": f"Similarity {sim:.3f} < {threshold}",
                        },
                    })
                    return None

                # Layer 2: Structured LLM Classification A/B/C/X + G4 rejection reason
                judge_result = await self.evaluator.evaluate_lead_structured(job)
                if not judge_result.is_qualified:
                    rejected_logs.append({
                        "source": "job_board_service_triage",
                        "level": "INFO",
                        "message": f"Lead rejected [layer2_llm_judge:{judge_result.category}]: {job.company} - {job.title}",
                        "details": {
                            "stage": "layer2_llm_judge",
                            "company": job.company,
                            "job_title": job.title,
                            "url": job.url,
                            "keyword": job.keyword,
                            "similarity": round(sim, 4),
                            "category": judge_result.category,
                            "confidence": judge_result.confidence,
                            "reason": judge_result.reason,
                        },
                    })
                    return None

                # Generate the identified need only if it passes both layers
                base_need = job.identified_need or await self.evaluator.infer_need(job)
                identified_need = f"[{judge_result.category}類 | 信心 {judge_result.confidence:.0%}] {judge_result.reason}\n{base_need}"

                score = int(round(judge_result.confidence * 100)) if judge_result.confidence > 0 else int(round(sim * 100))
                # Qualified status for high-intent matches (>= 72), else archived
                lead_status = "qualified" if score >= 72 else "archived"

                lead_dto: LeadDataDTO = {
                    "company_name": job.company,
                    "job_title": job.title,
                    "description_snippet": job.description[:500] if job.description else None,
                    "source_job_url": job.url,
                    "status": lead_status,
                    "enrichment_status": "completed",
                    "enrichment_score": score,
                    "identified_need": identified_need,
                }
                return lead_dto, judge_result.category
            except Exception as e:
                logger.error(f"Failed to process lead data: {e}")
                return None

        # PERFORMANCE: Replaced sequential await self._infer_need(job) with asyncio.gather
        import asyncio
        new_jobs = [job for job in jobs if job.url not in existing_urls]
        candidates: list[tuple[JobData, LeadDataDTO, str]] = []
        if new_jobs:
            results = await asyncio.gather(*[_process_single_job(job) for job in new_jobs])
            for job, res_item in zip(new_jobs, results, strict=False):
                if res_item:
                    lead_data, category = res_item
                    candidates.append((job, lead_data, category))

        # G1: Bulk insert structured rejection logs (no per-item insert in loop)
        if rejected_logs:
            self.execute_query(
                self.supabase.table("archon_logs").insert(rejected_logs),  # 合法
                "Bulk insert rejected lead triage logs",
            )

        # Apply A:B = 60:40 quota before persisting
        for job, lead_data, _ in self._apply_ab_quota(candidates):
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

                async def _log_action(job: JobData, content: str) -> None:
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
