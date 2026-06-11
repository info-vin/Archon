"""
Agent Registry: Maps AI Agent IDs to their Brains (Prompts) and Hands (MCP Tools).
Standardized with Physical UUID resolution for Phase 4.6.15.
"""

from functools import lru_cache
from typing import cast

from ..utils import get_supabase_client
from .prompt_service import prompt_service

TOOL_CONFIG_DEFAULT = {
    "apply_modification": {"min_xp_level": 2, "risk_level": "write"},
    "perform_web_crawl": {"min_xp_level": 1, "risk_level": "write"},
    "search_job_market": {"min_xp_level": 0, "risk_level": "read"},
    "generate_sales_email": {"min_xp_level": 0, "risk_level": "write"},
    "rag_search_knowledge_base": {"min_xp_level": 0, "risk_level": "read"},
    "rag_get_available_sources": {"min_xp_level": 0, "risk_level": "read"},
    "rag_search_code_examples": {"min_xp_level": 0, "risk_level": "read"},
    "list_projects": {"min_xp_level": 0, "risk_level": "read"},
    "manage_task": {"min_xp_level": 0, "risk_level": "write"},
    "search_code_examples": {"min_xp_level": 0, "risk_level": "read"},
    "generate_logo": {"min_xp_level": 0, "risk_level": "write"},
    "execute_shell_command": {"min_xp_level": 2, "risk_level": "write"},
}


def get_tool_min_level(tool_name: str) -> int:
    """Returns the minimum XP level required to execute a tool. (Phase 4.6.46: Dynamic Support)"""
    config = TOOL_CONFIG_DEFAULT.get(tool_name, {})
    static_level = cast(int, config.get("min_xp_level", 0))

    # Physical Realization of Dynamic Feedback Loop
    try:
        from ..services.settings_service import SettingsService

        settings = SettingsService()
        overrides = settings.get_setting("AGENT_TOOL_OVERRIDES")
        if overrides and isinstance(overrides, dict):
            return int(overrides.get(tool_name, {}).get("min_xp_level", static_level))
    except Exception:
        pass

    return static_level


FALLBACK_AGENT_CONFIG = {
    "supervisor": {
        "name": "Archon Supervisor",
        "model_tier": "pro",
        "system_prompt": "You are Charlie, the Supervisor. Review the conversation history. Decide which worker should act next.",
        "tools": [],
    },
    "market-bot": {
        "name": "Archon MarketBot",
        "model_tier": "lite",
        "system_prompt": "You are Archon MarketBot, an expert Marketing Content Writer and blog creator. Respond in Traditional Chinese (繁體中文).",
        "tools": ["search_job_market", "generate_sales_email"],
        "default_tool": "search_job_market",
    },
    "librarian": {
        "name": "Archon Librarian",
        "model_tier": "lite",
        "system_prompt": "You are the Librarian of Archon. Manage knowledge and respond in Traditional Chinese (繁體中文).",
        "tools": [
            "rag_search_knowledge_base",
            "rag_get_available_sources",
            "rag_search_code_examples",
            "perform_web_crawl",
        ],
    },
    "po-bot": {
        "name": "Archon POBot",
        "model_tier": "pro",
        "system_prompt": "You are an expert Product Owner. Refine task descriptions into User Stories.",
        "tools": ["list_projects", "manage_task"],
    },
    "dev-bot": {
        "name": "Archon DevBot",
        "model_tier": "pro",
        "system_prompt": "You are Archon DevBot, an expert software engineer. Solve tasks using tools.",
        "tools": ["rag_search_code_examples", "generate_logo", "apply_modification", "execute_shell_command"],
    },
}


@lru_cache(maxsize=20)
def get_agent_uuid(agent_key: str) -> str | None:
    """
    Physically resolves an internal Agent Key to its current Supabase Auth UUID.
    Example: get_agent_uuid("dev-bot") -> "e1682371-..."
    """
    try:
        supabase = get_supabase_client()
        res = supabase.table("archon_agents").select("id").eq("agent_key", agent_key).execute()
        if res.data:
            return str(res.data[0]["id"])
    except Exception:
        pass

    try:
        supabase = get_supabase_client()
        fallback_name_map = {
            "supervisor": "Archon Supervisor",
            "market-bot": "Archon MarketBot",
            "librarian": "Archon Librarian",
            "po-bot": "Archon POBot",
            "dev-bot": "Archon DevBot"
        }
        agent_name = fallback_name_map.get(agent_key, agent_key)
        res = supabase.table("profiles").select("id").eq("name", agent_name).execute()
        if res.data:
            return str(res.data[0]["id"])
    except Exception:
        pass
    return None


def get_agent_config(agent_id: str) -> dict | None:
    """
    Retrieves the configuration for a specific agent dynamically from database.
    Fallback to FALLBACK_AGENT_CONFIG if database is unavailable.
    """
    from .shared_constants import AgentUUIDs

    mapping = {
        AgentUUIDs.SUPERVISOR: "supervisor",
        AgentUUIDs.MARKET_BOT: "market-bot",
        AgentUUIDs.LIBRARIAN: "librarian",
        AgentUUIDs.PO_BOT: "po-bot",
        AgentUUIDs.DEV_BOT: "dev-bot",
        AgentUUIDs.CLOCKWORK: "clockwork",
    }

    key = mapping.get(agent_id, agent_id)

    try:
        supabase = get_supabase_client()
        res = supabase.table("archon_agents").select("*").eq("agent_key", key).execute()
        if res.data:
            agent_data = res.data[0]
            agent_uuid = agent_data["id"]

            tools_res = supabase.table("archon_agent_tools").select("tool_name").eq("agent_id", agent_uuid).execute()
            tools_list = [row["tool_name"] for row in tools_res.data] if tools_res.data else []

            prompt_name_map = {
                "supervisor": "WORKFLOW_SUPERVISOR_GENERAL",
                "market-bot": "MARKETBOT_SYSTEM_PROMPT",
                "librarian": "LIBRARIAN_SYSTEM_PROMPT",
                "po-bot": "POBOT_SYSTEM_PROMPT",
                "dev-bot": "DEVBOT_SYSTEM_PROMPT",
            }
            prompt_key = prompt_name_map.get(key, f"{key.upper()}_SYSTEM_PROMPT")
            fallback_prompt = FALLBACK_AGENT_CONFIG.get(key, {}).get("system_prompt", "You are a helpful AI assistant.")
            # Ensure fallback_prompt is a string
            str_fallback = str(fallback_prompt) if isinstance(fallback_prompt, list) else str(fallback_prompt)
            system_prompt = prompt_service.get_prompt(prompt_key, str_fallback)

            return {
                "name": agent_data["name"],
                "model_tier": agent_data["model_tier"],
                "system_prompt": system_prompt,
                "tools": tools_list,
                "default_tool": agent_data.get("default_tool"),
            }
    except Exception:
        pass

    return FALLBACK_AGENT_CONFIG.get(key)
