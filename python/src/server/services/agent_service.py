# python/src/server/services/agent_service.py

import asyncio
import json
import re
import uuid
from typing import Any, cast

from ..config.logfire_config import get_logger
from ..prompts.dev_ops_prompts import DEVBOT_TOOLS, get_devbot_analysis_prompt
from ..utils.code_modifier import CodeModifier
from .agent_registry import get_agent_config, get_agent_uuid
from .credential_service import credential_service
from .llm_provider_service import get_llm_client
from .shared_constants import AI_AGENT_ROLES, AgentUUIDs


class AgentService:
    """Service for handling business logic related to AI agents. Physically Hardened for Phase 4.6.47."""

    def __init__(self, mcp_client=None):
        self.code_modifier = CodeModifier(base_path=".")
        self.mcp_client = mcp_client
        from collections.abc import Callable, Coroutine
        self._native_tools: dict[str, Callable[..., Coroutine[Any, Any, str]]] = {}

    async def _check_poisson_gate(self, agent_id: str, required_level: int) -> tuple[bool, str]:
        if required_level <= 0: return True, "Level 0 (Intern)"
        from .stats_service import stats_service
        try:
            rankings = await stats_service.get_agent_xp_stats()
            agent_xp_info = next((r for r in rankings if r.get("agent_id") == agent_id), None)
            if not agent_xp_info: return False, "Unknown (XP 0)"
            level_str = agent_xp_info.get("level", "Intern")
            current_level = 0 if level_str == "Intern" else int(level_str.split(" ")[1])
            return current_level >= required_level, level_str
        except Exception as e:
            get_logger(__name__).error(f"Poisson Gate failed: {e}")
            return False, "Error"

    async def _handle_tool_calls(self, tool_calls, agent_id: str) -> list[dict]:
        logger = get_logger(__name__)
        from .agent_registry import get_tool_min_level
        tool_outputs = []
        for tool_call in tool_calls:
            func_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            call_id = tool_call.id
            try:
                req_level = get_tool_min_level(func_name)
                is_trusted, curr_level = await self._check_poisson_gate(agent_id, req_level)
                if not is_trusted:
                    result = f"Security Block: Level {curr_level} too low for {func_name} (needs {req_level})"
                else:
                    if self.mcp_client: result = await self.mcp_client.call_tool(func_name, **args)
                    else: result = "MCP Client not initialized"
                tool_outputs.append({"role": "tool", "tool_call_id": call_id, "content": str(result)})
            except Exception as e:
                tool_outputs.append({"role": "tool", "tool_call_id": call_id, "content": str(e)})
        return tool_outputs

    async def _analyze_error_with_structured_output(self, command: str, stderr: str, agent_id: str) -> dict[str, Any] | None:
        from ..config.model_ssot import SYSTEM_MODELS
        prompt = get_devbot_analysis_prompt(command, stderr)
        try:
            key = await credential_service.get_credential("GEMINI_API_KEY")
            async with get_llm_client(api_key=key) as client:
                response = await client.chat.completions.create(
                    model=SYSTEM_MODELS["DEFAULT_TEXT"], 
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                return json.loads(response.choices[0].message.content)
        except Exception: return None

    async def run_command_with_self_healing(self, command: str, agent_id: str, task_id: str | None = None) -> tuple[bool, str]:
        logger = get_logger(__name__)
        process = await asyncio.create_subprocess_shell(command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await process.communicate()
        if process.returncode == 0: return True, stdout.decode()
        
        fix_proposal = await self._analyze_error_with_structured_output(command, stderr.decode(), agent_id)
        if not fix_proposal: return False, "Self-healing failed to propose fix"
        
        # Apply fix on sandbox branch
        self.code_modifier.apply_modification(fix_proposal["file_path"], fix_proposal["fixed_content"])
        return True, "Self-healing fix applied (sandbox)"

    async def diagnose_file_health(self, file_path: str) -> dict[str, Any]:
        try:
            with open(file_path, 'r') as f: content = f.read()
            count = len(content.splitlines())
            return {"file_path": file_path, "line_count": count, "healthy": count < 500}
        except Exception as e: return {"error": str(e)}

    async def get_assignable_agents(self, user_role: str | None = None) -> list[dict]:
        all_agents = []
        for role_name, agent_id in AI_AGENT_ROLES.items():
            all_agents.append({"id": agent_id, "name": role_name, "tools": [], "description": "AI Agent"})

        if not user_role or user_role in ["admin", "system_admin", "manager"]:
            system_bots = [AgentUUIDs.PO_BOT, AgentUUIDs.CLOCKWORK]
            return [a for a in all_agents if a["id"] not in system_bots]

        filtered = []
        for agent in all_agents:
            agent_id = str(agent["id"])
            if user_role == "sales" and agent_id == AgentUUIDs.MARKET_BOT:
                filtered.append(agent)
            elif user_role == "marketing" and agent_id in [AgentUUIDs.MARKET_BOT, AgentUUIDs.LIBRARIAN]:
                filtered.append(agent)
        return filtered

    async def run_agent_task(self, task_id: str, agent_id: str):
        from ..services.projects.task_service import task_service
        logger = get_logger(__name__)
        success, result = await task_service.update_task(task_id, {"status": "doing", "assignee": agent_id})
        if success: await self._run_general_agent_task(task_id, agent_id)

    async def _run_general_agent_task(self, task_id: str, agent_id: str):
        from ..services.projects.task_service import task_service
        logger = get_logger(__name__)
        config = get_agent_config(agent_id)
        if not config: return
        success, task_response = await task_service.get_task(task_id)
        if not (success and task_response and "task" in task_response): return
        task_data = task_response["task"]
        try:
            admin_api_key = await credential_service.get_credential("GEMINI_API_KEY")
            from ..config.model_ssot import SYSTEM_MODELS
            async with get_llm_client(api_key=admin_api_key) as client:
                response = await client.chat.completions.create(model=SYSTEM_MODELS["DEFAULT_TEXT"], messages=[{"role": "user", "content": task_data['title']}])
                final_output = response.choices[0].message.content
                await task_service.update_task(task_id, {"status": "done"})
                await task_service.save_agent_output(task_id, {"content": final_output}, agent_id)
        except Exception: await task_service.update_task(task_id, {"status": "failed"})

agent_service = AgentService()
