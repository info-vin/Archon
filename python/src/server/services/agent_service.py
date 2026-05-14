# python/src/server/services/agent_service.py

from typing import Any, cast

from ..config.logfire_config import get_logger
from .agent_registry import get_agent_config
from .agent_tool_executor import AgentToolExecutor
from .credential_service import credential_service
from .dev_ops_agent_service import DevOpsAgentService
from .llm_provider_service import get_llm_client
from .shared_constants import AI_AGENT_ROLES


class AgentService:
    """Service for handling business logic related to AI agents."""

    def __init__(self, mcp_client=None):
        self.tool_executor = AgentToolExecutor(mcp_client)
        self.dev_ops = DevOpsAgentService(self.tool_executor)

    @property
    def mcp_client(self):
        return self.tool_executor.mcp_client

    @mcp_client.setter
    def mcp_client(self, value):
        self.tool_executor.mcp_client = value

    async def get_assignable_agents(self, user_role: str | None = None) -> list[dict]:
        all_agents = []
        for role_name, agent_id in AI_AGENT_ROLES.items():
            all_agents.append(
                {"id": agent_id, "name": role_name, "role": role_name, "tools": [], "description": "AI Agent"}
            )

        from .shared_constants import AgentUUIDs
        system_bots = [AgentUUIDs.PO_BOT, AgentUUIDs.CLOCKWORK]

        if not user_role or user_role in ["admin", "system_admin", "manager"]:
            for agent in all_agents:
                agent_id = str(agent["id"])
                if agent_id in system_bots:
                    continue
                config = get_agent_config(agent_id)
                if config:
                    agent["tools"] = config.get("tools", [])
            return [a for a in all_agents if str(a["id"]) not in system_bots]

        filtered = []
        for agent in all_agents:
            agent_id = str(agent["id"])
            config = get_agent_config(agent_id)
            if config:
                agent["tools"] = config.get("tools", [])
                agent["description"] = config.get("system_prompt", "").split("\n")[0]
            if user_role == "sales" and agent_id == AgentUUIDs.MARKET_BOT:
                filtered.append(agent)
            elif user_role == "marketing" and agent_id in [AgentUUIDs.MARKET_BOT, AgentUUIDs.LIBRARIAN]:
                filtered.append(agent)
        return filtered

    async def run_agent_task(self, task_id: str, agent_id: str):
        from ..services.projects.task_service import task_service

        logger = get_logger(__name__)
        logger.info(f"AI agent '{agent_id}' starting work on task '{task_id}'.")

        success, result = await task_service.update_task(task_id, {"status": "doing", "assignee": agent_id})
        if not success:
            logger.error(f"Failed to update task status: {result.get('error')}")
            return

        await self._run_general_agent_task(task_id, agent_id)

    async def _award_agent_xp(self, agent_id: str, task_data: dict, output_message: str):
        from .shared_constants import AgentUUIDs
        from .stats import stats_service

        # Physical Scoring instead of random (Phase 4.6.15)
        # We derive metadata from the task context
        meta = {
            "lint_passed": "Success" in output_message,  # Heuristic for self-healing
            "required_terms": ["Archon"] if agent_id == AgentUUIDs.LIBRARIAN else [],
        }

        score = stats_service.calculate_ai_score(output_message, meta)
        # Translate 0-100 score to 0-15 XP
        xp = int(score / 6.6)

        # Grounded ID check from registry (e.g. ai-dev-bot -> Archon DevBot)
        from .agent_registry import get_agent_config

        config = get_agent_config(agent_id)
        display_name = config["name"] if config else agent_id

        msg = f"Completed {display_name} task: {task_data.get('title', 'Unknown')}"

        await stats_service.add_agent_action_log(
            agent_name=display_name,
            agent_id=agent_id,
            xp_change=xp,
            message=msg,
            details={"task_id": task_data.get("id"), "score": score},
        )

    async def _run_workflow_engine_task(self, task_id: str, task_data: dict, agent_id: str):
        """Phase 5.0.2: Bridges the execution to the isolated archon-agents WorkflowEngine container."""
        from ..services.projects.task_service import task_service
        import os
        import httpx
        
        logger = get_logger(__name__)
        
        # 1. Determine task_type for dynamic prompt routing
        task_type = task_data.get("task_type", "General")
        prompt = f"Task: {task_data['title']}\n\nDetails: {task_data.get('description', '')}"

        # 2. Call WorkflowEngine via httpx
        agents_url = os.getenv("AGENTS_SERVICE_URL", "http://archon-agents:8052")
        try:
            # Group chats take time, set a safe timeout
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    f"{agents_url}/agents/workflow/run",
                    json={"prompt": prompt, "context": {"task_type": task_type}},
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("success"):
                    await task_service.update_task(task_id, {"status": "done"})
                    
                    # Milestone 2: Save the entire JSON state, not just final_result
                    messages = data.get("metadata", {}).get("messages", [])
                    final_result = data.get("result", "")
                    
                    save_payload = {
                        "content": final_result,
                        "messages": messages,
                        "step_count": data.get("metadata", {}).get("step_count", 0)
                    }
                    await task_service.save_agent_output(task_id, save_payload, agent_id)
                    await self._award_agent_xp(agent_id, task_data, str(final_result))
                else:
                    logger.error(f"WorkflowEngine failed: {data.get('error')}")
                    await task_service.update_task(task_id, {"status": "failed"})
                    
        except httpx.RequestError as e:
            logger.error(f"Network error calling WorkflowEngine: {e}")
            await task_service.update_task(task_id, {"status": "failed"})
        except Exception as e:
            logger.error(f"Unexpected error in WorkflowEngine execution: {e}")
            await task_service.update_task(task_id, {"status": "failed"})

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

        from .shared_constants import AgentUUIDs
        # Direct Pipeline Check for Librarian
        if agent_id == AgentUUIDs.LIBRARIAN and task_data.get("crawler_target_id"):
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
                    await crawler.orchestrate_crawl(
                        {
                            "url": target["target_url"],
                            "max_depth": target.get("max_depth", 2),
                            "user_role": "system_admin",
                        }
                    )
                    output_msg = f"Direct crawler pipeline started for {target['target_url']}"
                    await task_service.update_task(task_id, {"status": "done"})
                    await self._award_agent_xp(agent_id, task_data, output_msg)
                    return
                except Exception as e:
                    logger.error(f"Direct crawl failed: {e}")
                    await task_service.update_task(task_id, {"status": "failed"})
                    return

        # Grounded Reasoning: Provide both title and description to the Agent
        task_desc = task_data.get("description", "No description provided.")
        messages = [
            {"role": "system", "content": config["system_prompt"]},
            {"role": "user", "content": f"Task: {task_data['title']}\n\nDetails: {task_desc}"},
        ]

        # Physical Synchronization: Fetch dynamic tools from MCP (Phase 4.6.19)
        all_mcp_tools: list[dict[str, Any]] = []
        if self.mcp_client:
            all_mcp_tools = await self.mcp_client.list_tools()
            logger.info(f"Dynamic Tool Discovery: Synced {len(all_mcp_tools)} tools from MCP.")

        agent_tools_list: list[str] = list(config.get("tools", []))
        agent_tools = [t for t in all_mcp_tools if cast(dict, t["function"])["name"] in agent_tools_list]

        # If any tools are requested but not found in MCP, they will naturally be missing
        # from tools_param, ensuring we don't call non-existent or shadow tools.
        tools_param = agent_tools if agent_tools else None

        try:
            admin_api_key = await credential_service.get_credential(
                "GEMINI_API_KEY"
            ) or await credential_service.get_credential("GOOGLE_API_KEY")
            from ..config.model_ssot import SYSTEM_MODELS

            tier = config.get("model_tier", "lite")
            model_key = "DEFAULT_PRO" if tier == "pro" else "DEFAULT_TEXT"
            active_model = SYSTEM_MODELS[model_key]

            from .system.rate_limiter import GlobalThrottler
            await GlobalThrottler.wait_for_capacity(tier=tier)

            async with get_llm_client(api_key=admin_api_key) as client:
                response = await client.chat.completions.create(
                    model=active_model, messages=messages, tools=tools_param
                )
                res_msg = response.choices[0].message
                if res_msg.tool_calls and self.mcp_client:
                    messages.append(res_msg)
                    tool_results = await self.tool_executor.handle_tool_calls(res_msg.tool_calls, agent_id=agent_id)
                    messages.extend(tool_results)
                    final_response = await client.chat.completions.create(
                        model=active_model, messages=messages, tools=tools_param
                    )
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
