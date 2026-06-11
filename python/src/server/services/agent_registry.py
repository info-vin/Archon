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
from .prompt_service import prompt_service

DEVBOT_DEFAULT_PROMPT = """你是一隻具備極強數學腦與邏輯推理能力的專家級軟體工程師 (Archon DevBot)。
在解決任何代碼、演算法或架構設計問題時，你必須嚴格遵守以下思維規範：

1. 【思維鏈 (Chain of Thought) 演繹原則】：
   - 對於任何非微不足道的邏輯或計算問題，在輸出最終代碼或結論之前，必須在思維過程中進行明確的步驟拆解與邊界分析。
   - 對於關鍵演算法，應使用數學符號或形式化虛擬碼定義其輸入、輸出、不變式 (Invariant) 與前置/後置條件。

2. 【嚴格數學邊界分析與防禦性約束】：
   - 審查數值計算時，必須對整數溢出、浮點數精確度丟失 (如 NaN/Infinity)、除以零、陣列索引越界等極端情況進行顯式防護。
   - 對於時間與空間複雜度 (Big-O)，必須進行明確的推導說明，並證明所選演算法在當前規模下的最優性。

3. 【定理證明思維限制 (Lean 4 定理證明約束)】：
   - 寫代碼或設計核心邏輯時，應如同在 Lean 4 定理證明器中進行型別與邏輯證明一般，確保每個分支與邊界情況的正確性皆有明確的邏輯依據支撐。
   - 避免模糊的「通常情況下成立」之假設，必須涵蓋所有可能引發錯誤的邊角案例 (Edge Cases)。

4. 【工具使用規範】：
   - 充分利用你所擁有的知識庫與 RAG 工具 (如 `rag_search_code_examples`) 查閱過往正確實作。
   - 進行代碼變更時，確保修改的精準與簡潔，嚴防 regression。

請保持專業、邏輯嚴密，並始終以高標準的軟體工程質量與數學嚴謹性解決問題。"""

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
    "supervisor": {
        "name": "Archon Supervisor",
        "model_tier": "pro",
        "system_prompt": "Routing Agent (Prompt injected dynamically via WorkflowEngine)",
        "tools": [],
    },
    "market-bot": {
        "name": "Archon MarketBot",
        "model_tier": "lite",
        "system_prompt": BLOG_DRAFT_SYSTEM_PROMPT,
        "tools": ["search_job_market", "generate_sales_email"],
        "default_tool": "search_job_market",
    },
    "librarian": {
        "name": "Archon Librarian",
        "model_tier": "lite",
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
        "model_tier": "pro",
        "system_prompt": USER_STORY_SYSTEM_PROMPT,
        "tools": ["list_projects", "manage_task"],
    },
    "dev-bot": {
        "name": "Archon DevBot",
        "model_tier": "pro",
        "system_prompt": prompt_service.get_prompt("DEVBOT_SYSTEM_PROMPT", DEVBOT_DEFAULT_PROMPT),
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
        AgentUUIDs.SUPERVISOR: "supervisor",
        AgentUUIDs.MARKET_BOT: "market-bot",
        AgentUUIDs.LIBRARIAN: "librarian",
        AgentUUIDs.PO_BOT: "po-bot",
        AgentUUIDs.DEV_BOT: "dev-bot",
        AgentUUIDs.CLOCKWORK: "clockwork",
    }

    key = mapping.get(agent_id, agent_id)
    return AGENT_CONFIG.get(key)
