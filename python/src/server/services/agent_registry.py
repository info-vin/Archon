"""
Agent Registry: Maps AI Agent IDs to their Brains (Prompts) and Hands (MCP Tools).
Standardized with Physical UUID resolution for Phase 4.6.15.
"""

from functools import lru_cache
from typing import cast

from ..prompts.marketing_prompts import BLOG_DRAFT_SYSTEM_PROMPT
from ..prompts.pm_prompts import USER_STORY_SYSTEM_PROMPT
from ..prompts.rag_prompts import LIBRARIAN_SYSTEM_PROMPT
from ..utils import get_supabase_client

TOOL_CONFIG = {
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
    config = TOOL_CONFIG.get(tool_name, {})
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


AGENT_CONFIG = {
    "market-bot": {
        "name": "Archon MarketBot",
        "system_prompt": BLOG_DRAFT_SYSTEM_PROMPT,
        "tools": ["search_job_market", "generate_sales_email"],
        "default_tool": "search_job_market",
    },
    "librarian": {
        "name": "Archon Librarian",
        "system_prompt": LIBRARIAN_SYSTEM_PROMPT,
        "tools": [
            "rag_search_knowledge_base",
            "rag_get_available_sources",
            "rag_search_code_examples",
            "perform_web_crawl",
        ],
    },
    "po-bot": {
        "name": "Archon POBot",
        "system_prompt": USER_STORY_SYSTEM_PROMPT,
        "tools": ["list_projects", "manage_task"],
    },
    "dev-bot": {
        "name": "Archon DevBot",
        "system_prompt": "You are Archon DevBot. Use tools to fix code or generate assets.",
        "tools": ["rag_search_code_examples", "generate_logo", "apply_modification", "execute_shell_command"],
    },
}


@lru_cache(maxsize=20)
def get_agent_uuid(agent_key: str) -> str | None:
    """
    Physically resolves an internal Agent Key to its current Supabase Auth UUID.
    Example: get_agent_uuid("dev-bot") -> "e1682371-..."
    """
    config = AGENT_CONFIG.get(agent_key)
    if not config:
        return None

    agent_name = config["name"]
    try:
        supabase = get_supabase_client()
        # Search by display name defined in AGENT_CONFIG
        res = supabase.table("profiles").select("id").eq("name", agent_name).execute()
        if res.data:
            return str(res.data[0]["id"])
        return None
    except Exception:
        return None


def get_agent_config(agent_id: str) -> dict | None:
    """
    Retrieves the configuration for a specific agent.
    Handles mapping from human-friendly roles to registry keys.
    """
    from .shared_constants import AgentUUIDs
    mapping = {
        "ai-market-bot": "market-bot",
        "ai-librarian": "librarian",
        "ai-po-bot": "po-bot",
        "ai-dev-bot": "dev-bot",
        AgentUUIDs.MARKET_BOT: "market-bot",
        AgentUUIDs.LIBRARIAN: "librarian",
        AgentUUIDs.PO_BOT: "po-bot",
        AgentUUIDs.DEV_BOT: "dev-bot",
        AgentUUIDs.CLOCKWORK: "clockwork",
    }

    key = mapping.get(agent_id, agent_id)
    return AGENT_CONFIG.get(key)
