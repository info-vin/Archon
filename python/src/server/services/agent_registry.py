"""
Agent Registry: Maps AI Agent IDs to their Brains (Prompts) and Hands (MCP Tools).
Standardized with Physical UUID resolution for Phase 4.6.15.
"""

from functools import lru_cache
from ..utils import get_supabase_client
from ..prompts.marketing_prompts import BLOG_DRAFT_SYSTEM_PROMPT
from ..prompts.pm_prompts import USER_STORY_SYSTEM_PROMPT
from ..prompts.rag_prompts import LIBRARIAN_SYSTEM_PROMPT

AGENT_CONFIG = {
    "market-bot": {
        "name": "Archon MarketBot",
        "system_prompt": BLOG_DRAFT_SYSTEM_PROMPT,
        "tools": [
            "search_job_market",
            "generate_sales_email"
        ],
        "default_tool": "search_job_market"
    },
    "librarian": {
        "name": "Archon Librarian",
        "system_prompt": LIBRARIAN_SYSTEM_PROMPT,
        "tools": [
            "perform_rag_query",
            "get_available_sources",
            "perform_web_crawl"
        ]
    },

    "po-bot": {
        "name": "Archon POBot",
        "system_prompt": USER_STORY_SYSTEM_PROMPT,
        "tools": [
            "list_projects",
            "manage_task"
        ]
    },
    "dev-bot": {
        "name": "Archon DevBot",
        "system_prompt": "You are Archon DevBot. Use tools to fix code or generate assets.",
        "tools": [
            "search_code_examples",
            "generate_logo",
            "apply_modification"
        ]
    }
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
    # Map roles from AI_AGENT_ROLES
    mapping = {
        "ai-market-bot": "market-bot",
        "ai-librarian": "librarian",
        "ai-po-bot": "po-bot",
        "ai-dev-bot": "dev-bot"
    }

    key = mapping.get(agent_id, agent_id)
    return AGENT_CONFIG.get(key)
