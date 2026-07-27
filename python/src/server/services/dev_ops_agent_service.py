import asyncio
import json
import re
import uuid
from typing import Any, cast

import aiofiles

from ..config.logfire_config import get_logger
from ..prompts.dev_ops_prompts import DEVBOT_TOOLS, get_devbot_analysis_prompt
from ..utils.code_modifier import CodeModifier
from .agent_tool_executor import AgentToolExecutor
from .credential_service import credential_service
from .llm_provider_service import get_llm_client


class DevOpsAgentService:
    def __init__(self, tool_executor: AgentToolExecutor) -> None:
        self.code_modifier = CodeModifier(base_path=".")
        self.tool_executor = tool_executor

    @property
    def mcp_client(self):
        return self.tool_executor.mcp_client

    async def _analyze_error_with_structured_output(
        self, command: str, stderr: str, agent_id: str
    ) -> dict[str, Any] | None:
        logger = get_logger(__name__)
        from ..services.search.rag_service import RAGService
        from ..services.token_usage_service import TokenUsageService

        sop_context = ""
        try:
            success, rag_res = await RAGService().perform_rag_query(query=f"SOP for {command}", match_count=2)
            if success:
                for r in rag_res.get("results", []):
                    sop_context += f"\n[SOP]: {r['content']}\n"
        except Exception:
            pass

        prompt = get_devbot_analysis_prompt(command, stderr)
        full_prompt = f"{prompt}\n\n### CONSTRAINTS ###\n{sop_context or 'Standard conventions.'}"
        messages = [{"role": "user", "content": full_prompt}]
        tools = DEVBOT_TOOLS if self.mcp_client else None
        request_id = f"fix-{uuid.uuid4().hex[:8]}"

        try:
            from ..config.model_ssot import SYSTEM_MODELS

            model = SYSTEM_MODELS["DEFAULT_PRO"]
            admin_api_key = await credential_service.get_credential(
                "GEMINI_API_KEY"
            ) or await credential_service.get_credential("GOOGLE_API_KEY")
            from .system.rate_limiter import GlobalThrottler

            await GlobalThrottler.wait_for_capacity(tier="pro")

            async with get_llm_client(api_key=admin_api_key) as client:
                response = await client.chat.completions.create(
                    model=model, messages=messages, tools=tools, tool_choice="auto" if tools else None, temperature=0.1
                )
                res_msg = response.choices[0].message

                if hasattr(response, "usage") and response.usage:
                    from .agent_registry import get_agent_uuid

                    agent_uuid = get_agent_uuid(agent_id)
                    asyncio.create_task(
                        TokenUsageService.log_usage(
                            request_id=f"{request_id}-r1",
                            user_id=agent_uuid,
                            model=model,
                            provider="google",
                            input_tokens=response.usage.prompt_tokens,
                            output_tokens=response.usage.completion_tokens,
                            context_type="self_healing",
                        )
                    )

                tool_calls = res_msg.tool_calls
                if tool_calls and self.mcp_client:
                    messages.append(res_msg)
                    tool_results = await self.tool_executor.handle_tool_calls(tool_calls, agent_id=agent_id)
                    messages.extend(tool_results)
                    final_response = await client.chat.completions.create(
                        model=model, messages=messages, tools=tools, response_format={"type": "json_object"}
                    )
                    content = final_response.choices[0].message.content.strip()
                else:
                    content = res_msg.content.strip()

                if not content:
                    return None
                try:
                    return cast(dict[str, Any], json.loads(content))
                except Exception:
                    match = re.search(r"\{.*\}", content, re.DOTALL)
                    return json.loads(match.group(0)) if match else None
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return {"file_path": None, "reasoning": f"Analysis: Check syntax. Error: {e}"}

    async def run_command_with_self_healing(
        self, command: str, agent_id: str, task_id: str | None = None
    ) -> tuple[bool, str]:
        logger = get_logger(__name__)
        task_id = task_id or f"auto-{uuid.uuid4().hex[:8]}"
        logger.info(f"Executing command with self-healing (L2): {command}")

        process = await asyncio.create_subprocess_shell(
            command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            logger.info(f"Command '{command}' succeeded initially.")
            return True, stdout.decode().strip()

        logger.warning(f"Command '{command}' failed. Starting Active Repair Loop.")
        fix_proposal = await self._analyze_error_with_structured_output(
            command, stderr.decode().strip()[-2000:], agent_id=agent_id
        )

        # --- Poisson Gate Check (1.5 Governance) ---
        # Self-healing involving file modification is classified as Level 2 (Moderate)
        is_trusted, curr_level = await self.tool_executor.check_poisson_gate(agent_id=agent_id, required_level=2)
        if not is_trusted:
            logger.warning(f"Poisson Gate: Insufficient credibility for Level 2 auto-repair. ({curr_level})")
            return (
                False,
                f"Poisson Security Block: Your current level is {curr_level}, but Level 2 is required for autonomous repair. Proposal: {fix_proposal.get('reasoning') if fix_proposal else 'Check logs'}",
            )

        # Test baseline compatibility: If no file path, it's an "Analysis only" path
        if not fix_proposal or not fix_proposal.get("file_path"):
            logger.warning("LLM could not propose a valid code fix.")
            reasoning = fix_proposal.get("reasoning", "No fix proposed") if fix_proposal else "No fix proposed"
            return False, f"Analysis: {reasoning}"

        original_branch = self.code_modifier.get_current_branch()
        sandbox_branch = self.code_modifier.create_sandbox_branch(task_id)
        try:
            self.code_modifier.apply_modification(fix_proposal["file_path"], fix_proposal["fixed_content"])
            logger.info(f"Applied fix to {fix_proposal['file_path']} on branch {sandbox_branch}")

            process_retry = await asyncio.create_subprocess_shell(
                command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            await process_retry.communicate()
            if process_retry.returncode == 0:
                lint_proc = await asyncio.create_subprocess_shell(
                    "make lint-be", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                await lint_proc.communicate()
                if lint_proc.returncode != 0:
                    return await self.run_command_with_self_healing("make lint-be", agent_id=agent_id, task_id=task_id)
                return True, f"Repair successful on {sandbox_branch}. Reasoning: {fix_proposal.get('reasoning')}"
            else:
                self.code_modifier.revert_sandbox(original_branch)
                return False, "Fix verification failed"
        except Exception as e:
            self.code_modifier.revert_sandbox(original_branch)
            return False, f"Repair error: {e}"

    async def diagnose_file_health(self, file_path: str) -> dict[str, Any]:
        """
        Performs a physical diagnostic of a file based on SOP metrics (1.7.1).
        Assigns L1 (Green), L2 (Yellow), or L3 (Red) severity.
        """
        try:
            async with aiofiles.open(file_path, encoding="utf-8") as f:
                content = await f.read()

            lines = content.splitlines()
            line_count = len(lines)

            # Detect anti-patterns: Direct SQL in API controllers
            has_direct_sql = bool(re.search(r"supabase\.table\(|execute\(\)", content))

            # 1.7.1 Logic: Severity Grading
            if line_count > 500 or has_direct_sql:
                severity = 3  # RED / Critical
                advice = "Critical Technical Debt: Exceeds 500 lines or contains direct SQL calls. Refactor to Service layer required."
            elif line_count > 300:
                severity = 2  # YELLOW / Moderate
                advice = "Moderate Technical Debt: Large file detected. Consider extracting helpers."
            else:
                severity = 1  # GREEN / Minor
                advice = "Healthy: File matches standard complexity guidelines."

            return {
                "file_path": file_path,
                "line_count": line_count,
                "has_direct_sql": has_direct_sql,
                "severity_level": severity,
                "advice": advice,
                "timestamp": uuid.uuid4().hex[:8],  # Trace ID
            }
        except Exception as e:
            return {"error": f"Failed to diagnose file: {e}"}
