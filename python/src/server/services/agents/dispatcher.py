"""
Phase 5.1.0: Agent Dispatcher & Strategy Pattern
Resolves the 'God Method' coupling in agent_service.py by encapsulating
different agent execution behaviors into independent strategies.
"""

from abc import ABC, abstractmethod
from typing import Any, cast

from src.server.config.logfire_config import get_logger
from src.server.config.model_ssot import SYSTEM_MODELS
from src.server.services.agent_registry import get_agent_config
from src.server.services.crawling.crawling_service import CrawlingService
from src.server.services.credential_service import credential_service
from src.server.services.llm.clients import get_llm_client
from src.server.services.projects.task_service import task_service
from src.server.services.shared_constants import AgentUUIDs
from src.server.services.system.rate_limiter import GlobalThrottler
from src.server.utils import get_supabase_client

logger = get_logger(__name__)


class BaseAgentStrategy(ABC):
    @abstractmethod
    async def execute(self, task_id: str, task_data: dict[str, Any], agent_id: str, agent_service: Any) -> None:
        """Executes the specific strategy for the given agent and task."""
        pass


class SupervisorStrategy(BaseAgentStrategy):
    """Routes the task to the isolated archon-agents WorkflowEngine container."""

    async def execute(self, task_id: str, task_data: dict[str, Any], agent_id: str, agent_service: Any) -> None:
        logger.info(f"🌉 Strategy: Routing task '{task_id}' to WorkflowEngine (Supervisor).")
        # Leverage the existing HTTP bridge method in AgentService for now
        await agent_service._run_workflow_engine_task(task_id, task_data, agent_id)


class LibrarianDirectStrategy(BaseAgentStrategy):
    """Bypasses LLM and directly triggers the crawling pipeline if the description is empty."""

    async def execute(self, task_id: str, task_data: dict[str, Any], agent_id: str, agent_service: Any) -> None:
        logger.info(f"[{agent_id}] Strategy: Direct crawler pipeline triggered for empty description")
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
            await agent_service._award_agent_xp(agent_id, task_data, output_msg)
        except Exception as e:
            logger.error(f"Direct crawl failed: {e}")
            await task_service.update_task(task_id, {"status": "failed"})


class DefaultLLMStrategy(BaseAgentStrategy):
    """The traditional single-turn LLM execution via Google GenAI."""

    async def execute(self, task_id: str, task_data: dict[str, Any], agent_id: str, agent_service: Any) -> None:
        config = get_agent_config(agent_id)
        if not config:
            logger.error(f"Agent '{agent_id}' not found.")
            await task_service.update_task(task_id, {"status": "failed"})
            return

        task_desc = task_data.get("description", "No description provided.")
        messages = [
            {"role": "system", "content": config["system_prompt"]},
            {"role": "user", "content": f"Task: {task_data['title']}\n\nDetails: {task_desc}"},
        ]

        # Physical Synchronization: Fetch dynamic tools from MCP (Phase 4.6.19)
        all_mcp_tools: list[dict[str, Any]] = []
        if agent_service.mcp_client:
            all_mcp_tools = await agent_service.mcp_client.list_tools()
            logger.info(f"Dynamic Tool Discovery: Synced {len(all_mcp_tools)} tools from MCP.")

        agent_tools_list: list[str] = list(config.get("tools", []))
        agent_tools = [t for t in all_mcp_tools if cast(dict, t["function"])["name"] in agent_tools_list]

        tools_param = agent_tools if agent_tools else None

        try:
            admin_api_key = await credential_service.get_credential(
                "GEMINI_API_KEY"
            ) or await credential_service.get_credential("GOOGLE_API_KEY")

            tier = config.get("model_tier", "lite")
            model_key = "DEFAULT_PRO" if tier == "pro" else "DEFAULT_TEXT"
            active_model = SYSTEM_MODELS[model_key]

            await GlobalThrottler.wait_for_capacity(tier=tier)

            async with get_llm_client(api_key=admin_api_key) as client:
                logger.info(
                    f"Generating content using SDK for model {active_model} with {len(agent_tools_list)} tools."
                )

                response = await client.chat.completions.create(
                    model=active_model, messages=messages, tools=tools_param
                )
                res_msg = response.choices[0].message
                if res_msg.tool_calls and agent_service.mcp_client:
                    messages.append(res_msg)
                    tool_results = await agent_service.tool_executor.handle_tool_calls(
                        res_msg.tool_calls, agent_id=agent_id
                    )
                    messages.extend(tool_results)
                    final_response = await client.chat.completions.create(
                        model=active_model, messages=messages, tools=tools_param
                    )
                    final_output = final_response.choices[0].message.content
                else:
                    final_output = res_msg.content

                # Save output & update status
                await task_service.update_task(task_id, {"status": "done"})

                # Phase 5.0.2 DB Compatibility: wrap in object
                save_payload = {"content": final_output}
                await task_service.save_agent_output(task_id, save_payload, agent_id)

                await agent_service._award_agent_xp(agent_id, task_data, final_output)

        except Exception as e:
            logger.error(f"Error executing DefaultLLMStrategy: {e}")
            await task_service.update_task(task_id, {"status": "failed"})


class DraftFromLeadsStrategy(BaseAgentStrategy):
    """Phase 5.1.1: Executes the blog drafting pipeline from lead parameters."""

    async def execute(self, task_id: str, task_data: dict[str, Any], agent_id: str, agent_service: Any) -> None:
        logger.info(f"[{agent_id}] Strategy: Blog drafting pipeline triggered for task {task_id}")
        try:
            # 1. Extract lead_ids from metadata or description
            lead_ids = task_data.get("metadata", {}).get("lead_ids", [])
            if not lead_ids:
                # Fallback to description parsing if metadata column not present
                desc = task_data.get("description", "")
                if "[PARAM:LEAD_IDS:" in desc:
                    params = desc.split("[PARAM:LEAD_IDS:")[1].split("]")[0]
                    lead_ids = params.split(",")

            if not lead_ids:
                raise ValueError("No lead_ids found in task parameters.")

            # 2. Call the physical handler
            from src.server.services.marketing.content_handler import ContentHandler

            handler = ContentHandler(get_supabase_client())

            output_msg = await handler.draft_from_leads_physical(task_id, lead_ids)

            # 3. Update task
            await task_service.update_task(task_id, {"status": "done"})
            await agent_service._award_agent_xp(agent_id, task_data, output_msg)

        except Exception as e:
            logger.error(f"DraftFromLeadsStrategy failed: {e}")
            await task_service.update_task(task_id, {"status": "failed"})


class AgentDispatcher:
    """Routes tasks to the appropriate strategy based on agent_id and task_data."""

    def __init__(self):
        self._strategies: list[tuple[Any, BaseAgentStrategy]] = []
        self._default_strategy = DefaultLLMStrategy()

        # Register strategies (Condition function, Strategy instance)
        self.register_strategy(lambda a_id, t_data: a_id == AgentUUIDs.SUPERVISOR, SupervisorStrategy())
        self.register_strategy(
            lambda a_id, t_data: (
                a_id == AgentUUIDs.LIBRARIAN
                and t_data.get("crawler_target_id")
                and not t_data.get("description", "").strip()
            ),
            LibrarianDirectStrategy(),
        )
        self.register_strategy(
            lambda a_id, t_data: (
                a_id == AgentUUIDs.LIBRARIAN
                and t_data.get("crawler_target_id")
                and t_data.get("description", "").strip().lower() in ["periodic sync", "knowledge sync"]
            ),
            LibrarianDirectStrategy(),
        )
        self.register_strategy(
            lambda a_id, t_data: (
                a_id == AgentUUIDs.MARKET_BOT
                and (t_data.get("feature") == "blog_drafting" or "AI Draft from Leads" in t_data.get("title", ""))
            ),
            DraftFromLeadsStrategy(),
        )

    def register_strategy(self, condition_func: Any, strategy: BaseAgentStrategy):
        self._strategies.append((condition_func, strategy))

    def get_strategy(self, agent_id: str, task_data: dict[str, Any]) -> BaseAgentStrategy:
        for condition_func, strategy in self._strategies:
            if condition_func(agent_id, task_data):
                return strategy
        return self._default_strategy


agent_dispatcher = AgentDispatcher()
