"""
Self-Tuning Service for Archon
Physically realizes the 'Cognitive Infra' by evolving System Prompts
based on observed errors in archon_logs.
"""

import logging
from typing import Any

import aiofiles

from ...repositories.base_repository import BaseRepository
from ...utils import get_supabase_client
from ..llm_provider_service import get_llm_client
from ..propose_change_service import ProposeChangeService
from ..shared_constants import AgentUUIDs

logger = logging.getLogger(__name__)


class SelfTuningService(BaseRepository):
    def __init__(self, supabase_client: Any = None) -> None:
        super().__init__(supabase_client or get_supabase_client())
        self.proposer = ProposeChangeService(self.supabase_client)

    async def tune_prompt_from_error(self, log_id: str) -> dict[str, Any]:
        """
        Analyze a specific error log and propose a prompt improvement.
        """
        try:
            # 1. Fetch the error context - robust fetch
            query = self.supabase_client.table("archon_logs").select("*").eq("id", log_id) # 合法
            success, res = self.execute_query(query, "Failed to fetch log")
            if not success or not res.get("data"):
                return {"success": False, "error": f"Log {log_id} not found"}

            log = res["data"][0]
            error_msg = log.get("message")
            details = log.get("details") or {}

            # 2. Identify the related prompt file
            agent_name = details.get("agent_name", "DevBot")
            prompt_map = {
                "Alice": "python/src/server/prompts/sales_prompts.py",
                "Bob": "python/src/server/prompts/marketing_prompts.py",
                "Charlie": "python/src/server/prompts/pm_prompts.py",
                "DevBot": "python/src/server/prompts/dev_ops_prompts.py",
            }

            file_path = prompt_map.get(agent_name, prompt_map["DevBot"])

            # 3. Read current prompt
            try:
                async with aiofiles.open(file_path) as f:
                    current_code = await f.read()
            except FileNotFoundError:
                return {"success": False, "error": f"Prompt file not found: {file_path}"}

            # 4. Use LLM to propose improvement
            async with get_llm_client() as client:
                tuning_prompt = f"""
Analyze the following ERROR log and the related SYSTEM PROMPT code.
ERROR: {error_msg}
DETAILS: {details}

CURRENT PROMPT CODE:
{current_code}

Propose a surgical modification to the prompt string within this code to prevent this error.
Return ONLY the full corrected file content.
"""
                from ...config.model_ssot import SYSTEM_MODELS

                response = await client.chat.completions.create(
                    model=SYSTEM_MODELS["DEFAULT_TEXT"],
                    messages=[{"role": "user", "content": tuning_prompt}],
                    temperature=0.1,
                )
                new_content = response.choices[0].message.content.strip()

            # 5. Create a Physical Proposal
            proposal = await self.proposer.create_file_proposal(
                file_path=file_path,
                new_content=new_content,
                summary=f"Cognitive Self-Tuning: Optimization for {agent_name} based on error {log_id}",
                user_id=AgentUUIDs.DEV_BOT,
            )

            return {"success": True, "proposal_id": proposal["id"], "file_path": file_path}

        except Exception as e:
            logger.error(f"SelfTuning: Failed to tune prompt: {e}")
            return {"success": False, "error": str(e)}


# Singleton
self_tuning_service = SelfTuningService()
