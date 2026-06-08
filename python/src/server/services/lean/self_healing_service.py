# python/src/server/services/lean/self_healing_service.py

import os
import re
from typing import Any

from ...config.logfire_config import get_logger
from ...utils import get_supabase_client
from ..llm.clients import get_llm_client
from ..prompt_service import prompt_service
from ..storage.code_storage_service import add_code_examples_to_supabase
from .compiler_service import lean_compiler_service

logger = get_logger(__name__)

class LeanSelfHealingService:
    """Orchestrates 2-stage proof repair (local and cloud escalation) & database seeding."""

    def __init__(self, compiler_service=None, db_client=None):
        self.compiler_service = compiler_service or lean_compiler_service
        self.db_client = db_client or get_supabase_client()

    async def heal_proof(self, file_path: str, proof_context: str) -> dict[str, Any]:
        """Orchestrates compilation, capture errors, repair loop, and database seeding."""
        # 1. Run initial build
        logger.info(f"Initial compilation check for {file_path}")
        result = self.compiler_service.run_build()
        if result["success"]:
            logger.info("Compilation passed initially. No healing needed.")
            return {"success": True, "stage": "none", "output": result}

        if "error" in result and not result.get("errors"):
            logger.error(f"Compiler runner error: {result['error']}. Aborting self-healing.")
            return {"success": False, "error": f"Compiler unavailable: {result['error']}"}

        original_code = ""
        if os.path.exists(file_path):
            with open(file_path, encoding="utf-8") as f:
                original_code = f.read()

        errors = result.get("errors", [])
        logger.warning(f"Compilation failed with {len(errors)} errors. Initiating repair loop.")

        # --- Stage 1: Local Ollama Repair ---
        logger.info("Starting Stage 1: Local Ollama Repair Loop (K=2)")
        last_error_context = str(errors)

        for attempt in range(1, 3):
            logger.info(f"Local Repair Attempt {attempt}/2")
            repaired_code = await self._request_llm_repair(
                provider="ollama",
                original_code=original_code,
                error_info=last_error_context,
                proof_context=proof_context,
                retry_count=attempt
            )

            if repaired_code:
                # Write and compile
                self._write_code_to_file(file_path, repaired_code)
                build_res = self.compiler_service.run_build()
                if build_res["success"]:
                    logger.info("Stage 1 (Local Ollama) repair succeeded!")
                    await self._seed_successful_proof(file_path, repaired_code, "local_ollama")
                    return {"success": True, "stage": "local_ollama", "attempts": attempt}
                else:
                    last_error_context = str(build_res.get("errors", []))
                    logger.warning(f"Attempt {attempt} failed to compile: {last_error_context}")

        # --- Stage 2: Cloud Escalation ---
        logger.info("Stage 1 failed. Initiating Stage 2: Cloud Escalation")
        repaired_code_cloud = await self._request_llm_repair(
            provider="google",  # Default cloud provider
            original_code=original_code,
            error_info=last_error_context,
            proof_context=proof_context,
            retry_count=2
        )

        if repaired_code_cloud:
            self._write_code_to_file(file_path, repaired_code_cloud)
            build_res = self.compiler_service.run_build()
            if build_res["success"]:
                logger.info("Stage 2 (Cloud Escalation) repair succeeded!")
                await self._seed_successful_proof(file_path, repaired_code_cloud, "cloud_escalation")
                return {"success": True, "stage": "cloud_escalation"}
            else:
                logger.error(f"Stage 2 failed to compile: {build_res.get('errors')}")

        return {"success": False, "error": "Self-healing failed to resolve compilation errors"}

    async def _request_llm_repair(
        self, provider: str, original_code: str, error_info: str, proof_context: str, retry_count: int
    ) -> str | None:
        """Requests repair from the specified LLM provider."""
        system_prompt = prompt_service.get_prompt(
            "LEAN_4_DEVELOPER_ASSISTANT",
            "You are a Lean 4 logic programming copilot. Your objective is to help write correct formal proofs, choose mathematical tactics (like intro, rfl, simp, induction), and repair compile failures. Ensure output is syntactically valid Lean 4 code."
        )

        user_prompt = (
            f"We have a Lean 4 compile failure.\n\n"
            f"Here is the compiler error information:\n{error_info}\n\n"
            f"Original proof context:\n{proof_context}\n\n"
            f"Current file code:\n{original_code}\n\n"
            f"Please repair the code. Return only the complete corrected Lean 4 code wrapped in standard ```lean ... ``` blocks."
        )

        try:
            from ...config.model_ssot import SYSTEM_MODELS
            cloud_model = SYSTEM_MODELS["DEFAULT_PRO"].split("/")[-1]
            async with get_llm_client(provider=provider) as client:
                response = await client.chat.completions.create(
                    model="gemma3" if provider == "ollama" else cloud_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    extra_body={"retry_count": retry_count}
                )
                raw_content = response.choices[0].message.content
                return self._extract_lean_code(raw_content)
        except Exception as e:
            logger.error(f"LLM call to provider {provider} failed: {e}")
            return None

    def _extract_lean_code(self, raw_content: str) -> str:
        """Extracts code blocks within ```lean ... ```."""
        match = re.search(r"```lean\n(.*?)\n```", raw_content, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        # Fallback to general code blocks if specific language is missing
        match_general = re.search(r"```\n(.*?)\n```", raw_content, re.DOTALL)
        if match_general:
            return match_general.group(1).strip()
        return raw_content.strip()

    def _write_code_to_file(self, file_path: str, code: str) -> None:
        """Writes the repaired code to file."""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)

    async def _seed_successful_proof(self, file_path: str, code: str, method: str) -> None:
        """Seeds successful repairs into the code_examples database for RAG."""
        try:
            logger.info(f"Seeding successful proof into code_examples for {file_path}")
            url = f"file://{os.path.abspath(file_path)}"
            meta = {"source_id": "lean_self_healing", "language": "lean", "method": method}

            await add_code_examples_to_supabase(
                client=self.db_client,
                urls=[url],
                chunk_numbers=[0],
                code_examples=[code],
                summaries=[f"Successfully healed Lean 4 proof for {os.path.basename(file_path)} via {method}"],
                metadatas=[meta]
            )
        except Exception as e:
            logger.error(f"Failed to seed proof to database: {e}")

self_healing_service = LeanSelfHealingService()
