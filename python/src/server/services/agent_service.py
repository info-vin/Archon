# python/src/server/services/agent_service.py


from typing import Any

from ..config.logfire_config import get_logger
from .agent_registry import get_agent_config
from .agent_tool_executor import AgentToolExecutor
from .dev_ops_agent_service import DevOpsAgentService
from .shared_constants import AI_AGENT_ROLES


class AgentService:
    """Service for handling business logic related to AI agents."""

    def __init__(self, mcp_client=None) -> None:
        self.tool_executor = AgentToolExecutor(mcp_client)
        self.dev_ops = DevOpsAgentService(self.tool_executor)

    @property
    def mcp_client(self) -> Any:
        return self.tool_executor.mcp_client

    @mcp_client.setter
    def mcp_client(self, value: Any) -> None:
        self.tool_executor.mcp_client = value

    async def get_assignable_agents(self, user_role: str | None = None) -> list[dict]:
        all_agents = []
        for role_name, agent_id in AI_AGENT_ROLES.items():
            all_agents.append(
                {"id": agent_id, "name": role_name, "role": role_name, "tools": [], "description": "AI Agent"}
            )

        from src.server.utils import get_supabase_client

        from .shared_constants import AgentUUIDs

        system_bots = [AgentUUIDs.PO_BOT, AgentUUIDs.CLOCKWORK]

        # 1. Try to load role mapping dynamically from database
        try:
            supabase = get_supabase_client()
            res = supabase.table("archon_role_agents").select("agent_key").eq("user_role", user_role or "").execute()
            if res.data:
                allowed_keys = {row["agent_key"] for row in res.data}

                from .agent_registry import get_agent_uuid
                allowed_ids = {get_agent_uuid(k) for k in allowed_keys if get_agent_uuid(k)}

                filtered = []
                for agent in all_agents:
                    agent_id = str(agent["id"])
                    if agent_id in allowed_ids:
                        config = get_agent_config(agent_id)
                        if config:
                            agent["tools"] = config.get("tools", [])
                            agent["description"] = config.get("system_prompt", "").split("\n")[0]
                        filtered.append(agent)
                return filtered
        except Exception:
            pass

        # 2. Fallback to static mapping in case database is down or not seeded
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

    async def run_agent_task(self, task_id: str, agent_id: str, immediate: bool = False):
        from ..services.projects.task_service import task_service

        logger = get_logger(__name__)

        if not immediate:
            logger.info(f"📥 Enqueuing task '{task_id}' for AI agent '{agent_id}'.")
            success, result = await task_service.update_task(task_id, {"status": "dispatched", "assignee": agent_id})
            if not success:
                logger.error(f"Failed to enqueue task: {result.get('error')}")
            return

        logger.info(f"🚀 AI agent '{agent_id}' starting physical work on task '{task_id}'.")

        # When immediate=True, we move to 'doing' (or it might be 'processing' from worker)
        success, result = await task_service.update_task(task_id, {"status": "doing", "assignee": agent_id})
        if not success:
            logger.error(f"Failed to update task status to doing: {result.get('error')}")
            return

        await self._run_general_agent_task(task_id, agent_id)

    async def _award_agent_xp(self, agent_id: str, task_data: dict, output_message: str):
        from .shared_constants import AgentUUIDs
        from .stats import stats_service

        # Physical Scoring instead of random (Phase 4.6.15)
        # We derive metadata from the task context
        meta = {
            "lint_passed": "Success" in output_message if output_message else False,  # Heuristic for self-healing
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

        import httpx

        from ..services.projects.task_service import task_service

        logger = get_logger(__name__)

        # 1. Determine task_type for dynamic prompt routing
        task_title = task_data.get("title", "")
        task_type = "General"
        # Temporary hack: Deduce task_type from title since UI lacks a dropdown
        if "Marketing Data Deep Dive" in task_title or "行銷數據" in task_title:
            task_type = "Marketing Data Deep Dive"
        elif "[Daily Report]" in task_title:
            task_type = "Daily Executive Summary"

        prompt = f"Task: {task_title}\n\nDetails: {task_data.get('description', '')}"

        # 2. Call WorkflowEngine via httpx
        from ..schemas.settings import NetworkConfig
        from ..services.settings_service import SettingsService
        try:
            net_config = NetworkConfig.model_validate(SettingsService().get_all_settings())
            agents_url = net_config.agents_service_url
        except Exception:
            agents_url = NetworkConfig().agents_service_url

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
                        "step_count": data.get("metadata", {}).get("step_count", 0),
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

        success, task_response = await task_service.get_task(task_id)
        if not (success and task_response and "task" in task_response):
            return
        task_data = task_response["task"]

        # Phase 5.1.0 Milestone 1: Delegate execution to the Agent Dispatcher (Strategy Pattern)
        from .agents.dispatcher import agent_dispatcher

        strategy = agent_dispatcher.get_strategy(agent_id, task_data)
        logger.info(f"🚀 Dispatching task '{task_id}' for agent '{agent_id}' using {strategy.__class__.__name__}")

        await strategy.execute(task_id, task_data, agent_id, self)


agent_service = AgentService()
