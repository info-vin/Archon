import asyncio
import random
from typing import Any, TypedDict, cast

from ..config.logfire_config import get_logger
from ..config.model_ssot import SYSTEM_MODELS
from ..utils import get_supabase_client
from ..utils.retry_utils import retry_with_backoff

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
            from ..repositories.base_repository import BaseRepository
            repo = BaseRepository(self.supabase)
            query = self.supabase.table("archon_logs").insert({"source": source, "level": level, "message": message}) # 合法
            repo.execute_query(query, error_context="Write to archon_logs")
        except Exception as e:
            logger.error(f"Failed to write to archon_logs: {e}")

    async def _get_core_text(self) -> str | None:
        if getattr(self, "_core_text_cache", None) is not None:
            return self._core_text_cache # type: ignore

        import os
        from pathlib import Path

        project_root = str(Path(__file__).resolve().parent.parent.parent.parent.parent)

        agents_md_path = os.path.join(project_root, "AGENTS.md")
        if not os.path.exists(agents_md_path):
            agents_md_path = os.path.join(project_root, "..", "AGENTS.md")

        try:
            with open(agents_md_path, encoding="utf-8") as f:
                content = f.read()
                # SSOT: Fallback to first 2000 chars to avoid brittle markdown section parsing
                core_text = "Archon Core Capabilities:\n" + content[:2000]
                self._core_text_cache = core_text
                return self._core_text_cache
        except Exception as e:
            logger.error(f"Failed to read AGENTS.md for core text: {e}")
            return None

    async def _generate_llm_response(
        self,
        prompt_name: str,
        default_prompt: str,
        format_kwargs: dict[str, Any],
        estimated_tokens: int = 500,
        max_retries: int = 3,
        initial_delay: float = 2.0,
    ) -> str | None:
        try:
            from ..services.llm_provider_service import get_llm_client
            from ..services.prompt_service import prompt_service

            async with get_llm_client() as client:
                prompt_template = prompt_service.get_prompt(prompt_name, default=default_prompt)
                prompt = prompt_template.format(**format_kwargs)

                @retry_with_backoff(max_retries=max_retries, initial_delay=initial_delay)
                async def _call_llm():
                    return await client.chat.completions.create(
                        model=SYSTEM_MODELS["DEFAULT_TEXT"],
                        messages=[{"role": "user", "content": prompt}]
                    )

                async with self.rate_limiter.semaphore:
                    await self.rate_limiter.acquire(estimated_tokens=estimated_tokens)
                    response = await _call_llm()

                content = response.choices[0].message.content if response.choices else None
                return str(content).strip() if content else None
        except Exception as e:
            logger.error(f"LLM generation failed for {prompt_name}: {e}")
            return None

    async def _get_hyde_baseline_embedding(self) -> list[float] | None:
        if getattr(self, "_baseline_embedding_cache", None) is not None:
            return self._baseline_embedding_cache # type: ignore

        from ..services.embeddings.embedding_service import create_embedding

        core_text = await self._get_core_text()
        if not core_text:
            return None

        from ..prompts.sales_prompts import ALICE_HYDE_BASELINE_DEFAULT
        llm_text = await self._generate_llm_response(
            prompt_name="ALICE_HYDE_BASELINE",
            default_prompt=ALICE_HYDE_BASELINE_DEFAULT,
            format_kwargs={"core_text": core_text},
            estimated_tokens=500,
            max_retries=3
        )
        hyde_text = llm_text if llm_text else core_text

        try:
            self._baseline_embedding_cache = await create_embedding(hyde_text)
            return self._baseline_embedding_cache
        except Exception as e:
            logger.error(f"Failed to generate HyDE baseline: {e}")
            return None

    async def _llm_judge(self, job: JobData) -> bool:
        core_text = await self._get_core_text()
        if not core_text:
            return False

        from ..prompts.sales_prompts import ALICE_LEAD_JUDGE_DEFAULT

        content = await self._generate_llm_response(
            prompt_name="ALICE_LEAD_JUDGE",
            default_prompt=ALICE_LEAD_JUDGE_DEFAULT,
            format_kwargs={
                "core_text": core_text,
                "title": job.title,
                "desc": (job.description_full or job.description or "")[:1000]
            },
            estimated_tokens=500,
            max_retries=3
        )

        answer = str(content).strip().upper() if content else "NO"
        return "YES" in answer

    def __init__(self) -> None:
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
            job.keyword = keyword
        return jobs

    async def auto_fetch_daily_leads(self) -> int:
        logger.info("Starting daily lead auto-fetch...")
        total_new_leads = 0

        config = self._get_crawler_config()
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
                    self._log_archon(
                        source="job_board_service",
                        level="ALERT",
                        message=f"104 Crawler Blocked by WAF: {e}"
                    )
                    break  # Stop crawling other keywords if blocked
                except Exception as e:
                    logger.error(f"Error auto-fetching for '{keyword}': {e}")
                await asyncio.sleep(random.uniform(config.crawler_waf_delay_min, config.crawler_waf_delay_max))
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
            from ..repositories.base_repository import BaseRepository
            repo = BaseRepository(self.supabase)
            query = self.supabase.table("leads").select("source_job_url").in_("source_job_url", job_urls) # 合法
            success, result = repo.execute_query(query, "Fetch existing leads urls")
            if success and result.get("data"):
                existing_urls = {row["source_job_url"] for row in result.get("data", [])}

        baseline_embedding = await self._get_hyde_baseline_embedding()

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

                sim = self._cosine_similarity(baseline_embedding, job_embedding)
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
                is_lead = await self._llm_judge(job)
                if not is_lead:
                    self._log_archon(
                        source="job_board_service_judge",
                        level="DEBUG",
                        message=f"Lead discarded by LLM Judge. Similarity: {sim:.3f}. Keyword: {job.keyword}. Company: {job.company}"
                    )
                    return None

                # Generate the identified need only if it passes both layers
                identified_need = job.identified_need or await self._infer_need(job)

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
            from ..repositories.base_repository import BaseRepository
            repo = BaseRepository(self.supabase)
            query = self.supabase.table("leads").insert(leads_to_insert) # 合法
            success, result = repo.execute_query(query, "Bulk insert leads")

            if success and result.get("data"):
                res_data = result.get("data", [])
                new_leads_count += len(res_data)

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
                    for idx, inserted_lead in enumerate(res_data)
                ]
                if tasks:
                    await asyncio.gather(*tasks)

        return new_leads_count

    async def _infer_need(self, job: JobData) -> str:
        from ..prompts.sales_prompts import ALICE_INFER_NEED_DEFAULT

        content = await self._generate_llm_response(
            prompt_name="ALICE_INFER_NEED",
            default_prompt=ALICE_INFER_NEED_DEFAULT,
            format_kwargs={
                "title": job.title,
                "company": job.company,
                "desc": (job.description_full or job.description)
            },
            estimated_tokens=400,
            max_retries=4
        )

        return str(content).strip() if content else f"Hiring for {job.title}"
