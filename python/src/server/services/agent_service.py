# python/src/server/services/agent_service.py

import asyncio
import json
import re
import uuid
from typing import Any, cast

from ..config.logfire_config import get_logger
from ..prompts.dev_ops_prompts import DEVBOT_TOOLS, get_devbot_analysis_prompt
from ..utils import get_supabase_client
from ..utils.code_modifier import CodeModifier
from .agent_registry import get_agent_config
from .credential_service import credential_service
from .llm_provider_service import get_llm_client
from .shared_constants import AI_AGENT_ROLES


class AgentService:
    """Service for handling business logic related to AI agents."""

    def __init__(self, mcp_client=None):
        self.code_modifier = CodeModifier(base_path=".")
        self.mcp_client = mcp_client

    async def _check_poisson_gate(self, agent_id: str, required_level: int) -> bool:
        """
        Enforces Poisson-based success thresholds for refactoring levels.
        L1: Always (Basic fixes)
        L2: >300 | L3: >420 | L4: >500 | L5: >550 | L6: >580
        """
        if required_level <= 1:
            return True

        thresholds = {2: 300, 3: 420, 4: 500, 5: 550, 6: 580}
        min_success = thresholds.get(required_level, 9999)

        try:
            supabase = get_supabase_client()
            # Dynamic Success Ledger query
            res = supabase.table("archon_logs").select("id", count="exact")\
                .eq("source", agent_id)\
                .ilike("message", "%Succeeded%").execute()

            success_count = res.count if res.count is not None else 0
            return success_count >= min_success
        except Exception as e:
            get_logger(__name__).error(f"Poisson Gate Check failed: {e}")
            return False

    async def _handle_tool_calls(self, tool_calls) -> list[dict]:
        logger = get_logger(__name__)
        tool_outputs = []
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            call_id = tool_call.id
            logger.info(f"[MCP] Agent requesting tool execution: {function_name}")
            try:
                result = "Tool execution failed"
                if function_name == "apply_modification":
                    file_path = arguments.get("file_path")
                    content = arguments.get("content")
                    if file_path and content:
                        self.code_modifier.apply_modification(file_path, content)
                        result = f"Successfully modified {file_path}"
                elif self.mcp_client:
                    # Support direct mock method calls if available
                    if hasattr(self.mcp_client, function_name) and callable(getattr(self.mcp_client, function_name)):
                        method = getattr(self.mcp_client, function_name)
                        if asyncio.iscoroutinefunction(method):
                            result = await method(**arguments)
                        else:
                            result = method(**arguments)
                    else:
                        result = await self.mcp_client.call_tool(function_name, **arguments)

                tool_outputs.append({"role": "tool", "tool_call_id": call_id, "content": str(result)})
            except Exception as e:
                logger.error(f"[MCP] Tool execution failed ({function_name}): {e}")
                tool_outputs.append({"role": "tool", "tool_call_id": call_id, "content": str(e)})
        return tool_outputs

    async def _analyze_error_with_structured_output(self, command: str, stderr: str) -> dict[str, Any] | None:
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
            model = "gemini-2.5-flash-lite"
            admin_api_key = await credential_service.get_credential("GEMINI_API_KEY") or await credential_service.get_credential("GOOGLE_API_KEY")
            async with get_llm_client(api_key=admin_api_key) as client:
                response = await client.chat.completions.create(model=model, messages=messages, tools=tools, tool_choice="auto" if tools else None, temperature=0.1)
                res_msg = response.choices[0].message

                if hasattr(response, "usage") and response.usage:
                    asyncio.create_task(TokenUsageService.log_usage(request_id=f"{request_id}-r1", user_id="system-devbot", model=model, provider="google", input_tokens=response.usage.prompt_tokens, output_tokens=response.usage.completion_tokens, context_type="self_healing"))

                tool_calls = res_msg.tool_calls
                if tool_calls and self.mcp_client:
                    messages.append(res_msg)
                    tool_results = await self._handle_tool_calls(tool_calls)
                    messages.extend(tool_results)
                    final_response = await client.chat.completions.create(model=model, messages=messages, tools=tools, response_format={"type": "json_object"})
                    content = final_response.choices[0].message.content.strip()
                else:
                    content = res_msg.content.strip()

                if not content:
                    return None
                try:
                    return cast(dict[str, Any], json.loads(content))
                except Exception:
                    match = re.search(r'\{.*\}', content, re.DOTALL)
                    return json.loads(match.group(0)) if match else None
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return {"file_path": None, "reasoning": f"Analysis: Check syntax. Error: {e}"}

    async def run_command_with_self_healing(self, command: str, task_id: str | None = None) -> tuple[bool, str]:
        logger = get_logger(__name__)
        task_id = task_id or f"auto-{uuid.uuid4().hex[:8]}"
        logger.info(f"Executing command with self-healing (L2): {command}")

        process = await asyncio.create_subprocess_shell(command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            logger.info(f"Command '{command}' succeeded initially.")
            return True, stdout.decode().strip()

        logger.warning(f"Command '{command}' failed. Starting Active Repair Loop.")
        fix_proposal = await self._analyze_error_with_structured_output(command, stderr.decode().strip()[-2000:])

        # --- Poisson Gate Check (1.5 Governance) ---
        # Self-healing involving file modification is classified as Level 2 (Moderate)
        is_trusted = await self._check_poisson_gate(agent_id="system-devbot", required_level=2)
        if not is_trusted:
            logger.warning("Poisson Gate: Insufficient credibility for Level 2 auto-repair. Switching to Proposal mode.")
            return False, f"Poisson Security Block: Agent requires >300 successes for Level 2 auto-repair. Proposal: {fix_proposal.get('reasoning') if fix_proposal else 'Check logs'}"

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

            process_retry = await asyncio.create_subprocess_shell(command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            await process_retry.communicate()
            if process_retry.returncode == 0:
                lint_proc = await asyncio.create_subprocess_shell("make lint-be", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                await lint_proc.communicate()
                if lint_proc.returncode != 0:
                    return await self.run_command_with_self_healing("make lint-be", task_id=task_id)
                return True, f"Repair successful on {sandbox_branch}. Reasoning: {fix_proposal.get('reasoning')}"
            else:
                self.code_modifier.revert_sandbox(original_branch)
                return False, "Fix verification failed"
        except Exception as e:
            self.code_modifier.revert_sandbox(original_branch)
            return False, f"Repair error: {e}"

    async def get_assignable_agents(self, user_role: str | None = None) -> list[dict]:
        all_agents = []
        for role_name, agent_id in AI_AGENT_ROLES.items():
            all_agents.append({"id": agent_id, "name": role_name, "role": role_name, "tools": [], "description": "AI Agent"})

        if not user_role or user_role in ["admin", "system_admin", "manager"]:
            for agent in all_agents:
                config = get_agent_config(str(agent["id"]))
                if config:
                    agent["tools"] = config.get("tools", [])
            return all_agents

        filtered = []
        for agent in all_agents:
            agent_id = str(agent["id"])
            config = get_agent_config(agent_id)
            if config:
                agent["tools"] = config.get("tools", [])
                agent["description"] = config.get("system_prompt", "").split("\n")[0]
            if user_role == "sales" and agent_id == "ai-market-bot":
                filtered.append(agent)
            elif user_role == "marketing" and agent_id in ["ai-market-bot", "ai-librarian"]:
                filtered.append(agent)
        return filtered

    async def run_agent_task(self, task_id: str, agent_id: str, command: str | None = None):
        from ..services.projects.task_service import task_service
        logger = get_logger(__name__)
        logger.info(f"AI agent '{agent_id}' starting work on task '{task_id}'.")

        success, result = await task_service.update_task(task_id, {"status": "processing", "assignee": agent_id})
        if not success:
            logger.error(f"Failed to update task status: {result.get('error')}")
            return

        if command:
            success, output = await self.run_command_with_self_healing(command, task_id=task_id)
            await task_service.update_task(task_id, {"status": "done" if success else "failed", "output": output})
        else:
            await self._run_general_agent_task(task_id, agent_id)

    async def _run_general_agent_task(self, task_id: str, agent_id: str):
        from ..services.projects.task_service import task_service
        logger = get_logger(__name__)
        config = get_agent_config(agent_id)
        if not config:
            logger.error(f"Agent '{agent_id}' not found.")
            await task_service.update_task(task_id, {"status": "failed", "output": f"Agent {agent_id} missing"})
            return

        success, task_data = await task_service.get_task(task_id)
        if not (success and task_data):
            return

        messages = [{"role": "system", "content": config["system_prompt"]}, {"role": "user", "content": f"Task: {task_data['title']}"}]

        # Consistent tool param for Mock matching
        all_mcp_tools: list[dict[str, Any]] = [
            {"type": "function", "function": {"name": "search_job_market", "description": "Search 104", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}}}},
            {"type": "function", "function": {"name": "perform_rag_query", "description": "Search RAG", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}}}}
        ]
        agent_tools_list: list[str] = list(config.get("tools", []))
        agent_tools = [t for t in all_mcp_tools if cast(dict, t["function"])["name"] in agent_tools_list]
        tools_param = agent_tools if agent_tools else None

        try:
            admin_api_key = await credential_service.get_credential("GEMINI_API_KEY") or await credential_service.get_credential("GOOGLE_API_KEY")
            async with get_llm_client(api_key=admin_api_key) as client:
                response = await client.chat.completions.create(model="gemini-2.5-flash-lite", messages=messages, tools=tools_param)
                res_msg = response.choices[0].message
                if res_msg.tool_calls and self.mcp_client:
                    messages.append(res_msg)
                    tool_results = await self._handle_tool_calls(res_msg.tool_calls)
                    messages.extend(tool_results)
                    final_response = await client.chat.completions.create(model="gemini-2.5-flash-lite", messages=messages, tools=tools_param)
                    final_output = final_response.choices[0].message.content
                else:
                    final_output = res_msg.content

                await task_service.update_task(task_id, {"status": "done", "output": final_output})
        except Exception as e:
            await task_service.update_task(task_id, {"status": "failed", "output": str(e)})

agent_service = AgentService()
