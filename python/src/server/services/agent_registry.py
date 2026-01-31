"""
Agent Registry: Maps AI Agent IDs to their Brains (Prompts) and Hands (MCP Tools).
"""

from ..prompts.marketing_prompts import BLOG_DRAFT_SYSTEM_PROMPT
from ..prompts.pm_prompts import USER_STORY_SYSTEM_PROMPT
from ..prompts.dev_ops_prompts import get_devbot_analysis_prompt, DEVBOT_TOOLS
from ..prompts.rag_prompts import LIBRARIAN_SYSTEM_PROMPT

AGENT_CONFIG = {
    "market-bot": {
        "name": "MarketBot",
        "system_prompt": BLOG_DRAFT_SYSTEM_PROMPT,
        "tools": [
            "search_job_market", 
            "generate_sales_email"
        ],
        "default_tool": "search_job_market"
    },
    "librarian": {
        "name": "Librarian",
        "system_prompt": LIBRARIAN_SYSTEM_PROMPT,
        "tools": [
            "perform_rag_query", 
            "get_available_sources"
        ]
    },

    "po-bot": {
        "name": "POBot",
        "system_prompt": USER_STORY_SYSTEM_PROMPT,
        "tools": [
            "list_projects", 
            "manage_task"
        ]
    },
    "dev-bot": {
        "name": "DevBot",
        "system_prompt": "You are Archon DevBot. Use tools to fix code or generate assets.",
        "tools": [
            "search_code_examples", 
            "generate_logo",
            "apply_modification"
        ]
    }
}

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
