import math
import os
from pathlib import Path
from typing import Any

from ...config.logfire_config import get_logger
from ...config.model_ssot import SYSTEM_MODELS
from ...utils.retry_utils import retry_with_backoff
from .clients.job104_client import JobData

logger = get_logger(__name__)

class LeadEvaluator:
    """
    Evaluates job leads using AI, RAG, and Vector Similarity.
    Separated from JobBoardService to maintain Single Responsibility Principle.
    """

    def __init__(self, rate_limiter: Any):
        self.rate_limiter = rate_limiter
        self._core_text_cache: str | None = None
        self._baseline_embedding_cache: list[float] | None = None

    @staticmethod
    def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
        dot = sum(a * b for a, b in zip(vec1, vec2, strict=False))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        return dot / (norm1 * norm2) if norm1 and norm2 else 0.0

    async def get_core_text(self) -> str | None:
        if self._core_text_cache is not None:
            return self._core_text_cache

        # 多路徑陣列探測法相容 Host 與 Docker
        possible_paths = [
            "/app/AGENTS.md",  # Docker 環境
            str(Path(__file__).resolve().parent.parent.parent.parent.parent.parent / "AGENTS.md"),  # 本機開發環境
        ]

        agents_md_path = None
        for p in possible_paths:
            if os.path.exists(p):
                agents_md_path = p
                break

        if not agents_md_path:
            logger.error("Could not find AGENTS.md in any of the probe paths!")
            return None

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

    async def generate_llm_response(
        self,
        prompt_name: str,
        default_prompt: str,
        format_kwargs: dict[str, Any],
        estimated_tokens: int = 500,
        max_retries: int = 3,
        initial_delay: float = 2.0,
    ) -> str | None:
        try:
            from ...services.llm_provider_service import get_llm_client
            from ...services.prompt_service import prompt_service

            async with get_llm_client() as client:
                prompt_template = prompt_service.get_prompt(prompt_name, default=default_prompt)
                prompt = prompt_template.format(**format_kwargs)

                @retry_with_backoff(max_retries=max_retries, initial_delay=initial_delay)
                async def _call_llm() -> Any:
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

    async def get_hyde_baseline_embedding(self) -> list[float] | None:
        if self._baseline_embedding_cache is not None:
            return self._baseline_embedding_cache

        from ...services.embeddings.embedding_service import create_embedding

        core_text = await self.get_core_text()
        if not core_text:
            return None

        from ...prompts.sales_prompts import ALICE_HYDE_BASELINE_DEFAULT
        llm_text = await self.generate_llm_response(
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

    async def llm_judge(self, job: JobData) -> bool:
        core_text = await self.get_core_text()
        if not core_text:
            return False

        from ...prompts.sales_prompts import ALICE_LEAD_JUDGE_DEFAULT

        content = await self.generate_llm_response(
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

    async def infer_need(self, job: JobData) -> str:
        from ...prompts.sales_prompts import ALICE_INFER_NEED_DEFAULT

        content = await self.generate_llm_response(
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
