import asyncio
import json
from collections.abc import Callable, Coroutine
from typing import Any, TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from collections.abc import Iterable
    from src.agents.mcp_client import MCPClient

class ToolOutputDict(TypedDict):
    role: str
    tool_call_id: str
    content: str


from ..config.logfire_config import get_logger


class AgentToolExecutor:
    def __init__(self, mcp_client: 'MCPClient | None' = None) -> None:
        self.mcp_client = mcp_client
        self._native_tools: dict[str, Callable[..., Coroutine[Any, Any, str]]] = {}

    async def check_poisson_gate(self, agent_id: str, required_level: int) -> tuple[bool, str]:
        """
        Enforces dynamic governance based on Agent XP Levels (Phase 4.6.15).
        Returns: (is_trusted, current_level_description)
        """
        if required_level <= 0:
            return True, "Level 0 (Intern)"

        from .stats import stats_service

        try:
            # 1. Fetch unified XP rankings
            rankings = await stats_service.get_agent_xp_stats()

            # 2. Extract level for the specific agent using slug (agent_id)
            agent_xp_info = next((r for r in rankings if r.get("agent_id") == agent_id), None)

            if not agent_xp_info:
                get_logger(__name__).warning(
                    f"Poisson Gate: No XP record found for agent '{agent_id}'. Denying L{required_level}+ access."
                )
                return False, "Unknown (XP 0)"

            level_str = agent_xp_info.get("level", "Intern")
            if level_str == "Intern":
                current_level = 0
            else:
                try:
                    current_level = int(level_str.split(" ")[1])
                except (IndexError, ValueError):
                    current_level = 0

            return current_level >= required_level, level_str
        except Exception as e:
            get_logger(__name__).error(f"Poisson Gate (Level Sync) failed: {e}")
            return False, "Error"

    async def handle_tool_calls(self, tool_calls: 'Iterable[Any]', agent_id: str) -> list[ToolOutputDict]:
        logger = get_logger(__name__)
        from .agent_registry import get_agent_config, get_tool_min_level

        config = get_agent_config(agent_id)
        display_name = config["name"] if config else agent_id

        tool_outputs: list[ToolOutputDict] = []
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            call_id = tool_call.id
            logger.info(f"[MCP] Agent {display_name} ({agent_id}) requesting tool execution: {function_name}")
            try:
                required_level = get_tool_min_level(function_name)
                is_trusted, curr_level = await self.check_poisson_gate(agent_id=agent_id, required_level=required_level)

                if not is_trusted:
                    logger.warning(
                        f"[Poisson Gate] Blocked unauthorized attempt by {agent_id} for tool {function_name}. (Level {curr_level} < {required_level})"
                    )
                    result = f"Poisson Security Block: Your current level is {curr_level}, but {function_name} requires Level {required_level}."
                else:
                    if function_name in self._native_tools:
                        result = await self._native_tools[function_name](agent_id, **arguments)
                    elif self.mcp_client:
                        # Support direct mock method calls if available
                        if hasattr(self.mcp_client, function_name) and callable(
                            getattr(self.mcp_client, function_name)
                        ):
                            method = getattr(self.mcp_client, function_name)
                            result = (
                                await method(**arguments)
                                if asyncio.iscoroutinefunction(method)
                                else method(**arguments)
                            )
                        else:
                            result = await self.mcp_client.call_tool(function_name, **arguments)
                    else:
                        result = f"Tool {function_name} not available."

                tool_outputs.append(ToolOutputDict(role="tool", tool_call_id=call_id, content=str(result)))
            except Exception as e:
                logger.error(f"[MCP] Tool execution failed ({function_name}): {e}")
                tool_outputs.append(ToolOutputDict(role="tool", tool_call_id=call_id, content=str(e)))
        return tool_outputs
