# python/src/server/services/agent_service.py

import asyncio
import json
import re
import uuid
from typing import Any, cast

from ..config.logfire_config import get_logger
from ..prompts.dev_ops_prompts import DEVBOT_TOOLS, get_devbot_analysis_prompt
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
        Enforces dynamic governance based on Agent XP Levels (Phase 4.6.15).
        Replaces legacy 'fuzzy success ledger' with physical XP rankings.
        """
        if required_level <= 1:
            return True

        from .stats_service import StatsService
        stats_service = StatsService()

        try:
            # 1. Fetch unified XP rankings
            rankings = await stats_service.get_agent_xp_stats()

            # 2. Extract level for the specific agent
            # Note: agent_id in rankings comes from 'agent_name' in logs
            agent_xp_info = next((r for r in rankings if r["name"] == agent_id or agent_id in r["name"]), None)

            if not agent_xp_info:
                get_logger(__name__).warning(f"Poisson Gate: No XP record found for agent '{agent_id}'. Denying L{required_level}+ access.")
                return False

            # Level string format is "Level X" or "Intern"
            level_str = agent_xp_info.get("level", "Intern")
            if level_str == "Intern":
                current_level = 0
            else:
                try:
                    current_level = int(level_str.split(" ")[1])
                except (IndexError, ValueError):
                    current_level = 0

            return current_level >= required_level
        except Exception as e:
            get_logger(__name__).error(f"Poisson Gate (Level Sync) failed: {e}")
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
                elif function_name == "perform_web_crawl":
                    url = arguments.get("url")
                    max_depth = arguments.get("max_depth", 2)
                    if url:
                        from ..services.crawling.crawling_service import CrawlingService
                        crawler = CrawlingService()
                        await crawler.orchestrate_crawl({
                            "url": url,
                            "max_depth": max_depth,
                            "user_role": "admin"
                        })
                        result = f"Started background web crawl for {url}"
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
                    from .agent_registry import get_agent_uuid
                    agent_uuid = get_agent_uuid("dev-bot")
                    asyncio.create_task(TokenUsageService.log_usage(request_id=f"{request_id}-r1", user_id=agent_uuid, model=model, provider="google", input_tokens=response.usage.prompt_tokens, output_tokens=response.usage.completion_tokens, context_type="self_healing"))

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

    async def diagnose_file_health(self, file_path: str) -> dict[str, Any]:
        """
        Performs a physical diagnostic of a file based on SOP metrics (1.7.1).
        Assigns L1 (Green), L2 (Yellow), or L3 (Red) severity.
        """
        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()

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
                "timestamp": uuid.uuid4().hex[:8] # Trace ID
            }
        except Exception as e:
            return {"error": f"Failed to diagnose file: {e}"}

    async def get_assignable_agents(self, user_role: str | None = None) -> list[dict]:
        all_agents = []
        for role_name, agent_id in AI_AGENT_ROLES.items():
            all_agents.append({"id": agent_id, "name": role_name, "role": role_name, "tools": [], "description": "AI Agent"})

        if not user_role or user_role in ["admin", "system_admin", "manager"]:
            for agent in all_agents:
                agent_id = str(agent["id"])
                if agent_id in ["ai-po-bot", "ai-clockwork"]:
                    continue
                config = get_agent_config(agent_id)
                if config:
                    agent["tools"] = config.get("tools", [])
            return [a for a in all_agents if str(a["id"]) not in ["ai-po-bot", "ai-clockwork"]]

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

        success, result = await task_service.update_task(task_id, {"status": "doing", "assignee": agent_id})
        if not success:
            logger.error(f"Failed to update task status: {result.get('error')}")
            return

        if command:
            success, output = await self.run_command_with_self_healing(command, task_id=task_id)
            await task_service.update_task(task_id, {"status": "done" if success else "failed"})
            if success:
                _, task_resp = await task_service.get_task(task_id)
                if task_resp and "task" in task_resp:
                    await self._award_agent_xp(agent_id, task_resp["task"], output)
        else:
            await self._run_general_agent_task(task_id, agent_id)

    async def _award_agent_xp(self, agent_id: str, task_data: dict, output_message: str):
        import random

        from ..services.stats_service import StatsService
        stats = StatsService()

        # Calculate dynamic XP based on role/complexity
        if agent_id == "ai-market-bot":
            xp = random.randint(5, 10)
            msg = f"Completed marketing task: {task_data.get('title', 'Unknown')}"
        elif agent_id == "ai-po-bot" or agent_id == "system-devbot":
            xp = random.randint(5, 10)
            msg = f"Completed technical/management task: {task_data.get('title', 'Unknown')}"
        elif agent_id == "ai-librarian":
            xp = random.randint(5, 10)
            msg = f"Completed knowledge extraction: {task_data.get('title', 'Unknown')}"
        else:
            xp = random.randint(5, 10)
            msg = f"Completed task: {task_data.get('title', 'Unknown')}"

        await stats.add_agent_action_log(
            agent_name=agent_id,
            xp_change=xp,
            message=msg,
            details={"task_id": task_data.get("id"), "output_preview": output_message[:100]}
        )

    async def _run_general_agent_task(self, task_id: str, agent_id: str):
        from ..services.projects.task_service import task_service
        logger = get_logger(__name__)
        config = get_agent_config(agent_id)
        if not config:
            logger.error(f"Agent '{agent_id}' not found.")
            await task_service.update_task(task_id, {"status": "failed"})
            return

        success, task_response = await task_service.get_task(task_id)
        if not (success and task_response and "task" in task_response):
            return
        task_data = task_response["task"]

        # Direct Pipeline Check for Librarian
        if agent_id == "ai-librarian" and task_data.get("crawler_target_id"):
            description = task_data.get("description", "").strip()
            # If description is empty, bypass LLM and trigger crawling directly
            if not description or description.lower() in ["periodic sync", "knowledge sync"]:
                from ..services.crawling.crawling_service import CrawlingService
                from ..utils import get_supabase_client
                logger.info(f"[{agent_id}] Direct crawler pipeline triggered for empty description")
                try:
                    target_id = task_data["crawler_target_id"]
                    supabase = get_supabase_client()
                    res = supabase.table("archon_crawler_targets").select("*").eq("id", target_id).execute()
                    if not res.data:
                        raise ValueError(f"Crawler target {target_id} not found")
                    target = res.data[0]

                    crawler = CrawlingService()
                    await crawler.orchestrate_crawl({
                        "url": target["target_url"],
                        "max_depth": target.get("max_depth", 2),
                        "user_role": "system_admin"
                    })
                    output_msg = f"Direct crawler pipeline started for {target['target_url']}"
                    await task_service.update_task(task_id, {"status": "done"})
                    await self._award_agent_xp(agent_id, task_data, output_msg)
                    return
                except Exception as e:
                    logger.error(f"Direct crawl failed: {e}")
                    await task_service.update_task(task_id, {"status": "failed"})
                    return

        messages = [{"role": "system", "content": config["system_prompt"]}, {"role": "user", "content": f"Task: {task_data['title']}"}]

        # Consistent tool param for Mock matching
        all_mcp_tools: list[dict[str, Any]] = [
            {"type": "function", "function": {"name": "search_job_market", "description": "Search 104", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}}}},
            {"type": "function", "function": {"name": "perform_rag_query", "description": "Search RAG", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}}}},
            {"type": "function", "function": {"name": "perform_web_crawl", "description": "Crawl web for RAG", "parameters": {"type": "object", "properties": {"url": {"type": "string"}, "max_depth": {"type": "integer"}}}}}
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

                await task_service.update_task(task_id, {"status": "done"})

                # Use save_agent_output to persist LLM's raw final output
                await task_service.save_agent_output(task_id, {"content": final_output}, agent_id)

                await self._award_agent_xp(agent_id, task_data, final_output)
        except Exception:
            await task_service.update_task(task_id, {"status": "failed"})

agent_service = AgentService()
