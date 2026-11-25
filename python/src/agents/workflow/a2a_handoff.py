"""
Phase 5.15 Stage 2 (P2): Unified Agent Card & Agent-to-Agent (A2A) Direct Handoff.

Allows Worker nodes to hand off directly to another authorized Worker node
without bouncing back through SupervisorNode (saving gemini-3.6-flash RPD quota),
while enforcing allowlists, anti-loop guards, and max_steps circuit breaking.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from src.server.services.agent_registry import FALLBACK_AGENT_CONFIG, TOOL_CONFIG_DEFAULT
from src.server.services.shared_constants import AgentNames, AgentUUIDs

if TYPE_CHECKING:
    from .state import SharedState

logger = logging.getLogger(__name__)

# Matches: [HANDOFF: marketbot | reason text] or [HANDOFF: end]
_HANDOFF_PATTERN = re.compile(
    r"\[HANDOFF:\s*([a-zA-Z0-9_-]+)(?:\s*\|\s*([^\]]+))?\]",
    re.IGNORECASE,
)


def _write_tools_for_agent(registry_key: str) -> list[str]:
    """Derives write-risk tools from AgentRegistry SSOT (DRY)."""
    cfg = FALLBACK_AGENT_CONFIG.get(registry_key)
    if not cfg:
        return []
    result: list[str] = []
    for tool_name in cfg.get("tools", []):
        tool_cfg = TOOL_CONFIG_DEFAULT.get(tool_name)
        if tool_cfg is not None and tool_cfg.get("risk_level") == "write":
            result.append(tool_name)
    return result


def _tier_for_agent(registry_key: str, default: str = "lite") -> str:
    cfg = FALLBACK_AGENT_CONFIG.get(registry_key)
    return cfg["model_tier"] if cfg else default


class AgentCard(BaseModel):
    """Unified A2A capability & handoff policy card for an Archon agent."""

    agent_key: str
    agent_uuid: str
    name: str
    model_tier: str
    allowed_handoffs: list[str] = Field(default_factory=list)
    requires_approval_tools: list[str] = Field(default_factory=list)


DEFAULT_AGENT_CARDS: dict[str, AgentCard] = {
    "supervisor": AgentCard(
        agent_key="supervisor",
        agent_uuid=AgentUUIDs.SUPERVISOR,
        name=AgentNames.SUPERVISOR,
        model_tier=_tier_for_agent("supervisor", "pro"),
        allowed_handoffs=["marketbot", "librarian", "summary", "devbot", "david", "end", "human"],
    ),
    "librarian": AgentCard(
        agent_key="librarian",
        agent_uuid=AgentUUIDs.LIBRARIAN,
        name=AgentNames.LIBRARIAN,
        model_tier=_tier_for_agent("librarian", "lite"),
        allowed_handoffs=["marketbot", "devbot", "summary", "supervisor", "end"],
        requires_approval_tools=_write_tools_for_agent("librarian"),
    ),
    "marketbot": AgentCard(
        agent_key="marketbot",
        agent_uuid=AgentUUIDs.MARKET_BOT,
        name=AgentNames.MARKET_BOT,
        model_tier=_tier_for_agent("market-bot", "lite"),
        allowed_handoffs=["summary", "librarian", "supervisor", "end"],
        requires_approval_tools=_write_tools_for_agent("market-bot"),
    ),
    "devbot": AgentCard(
        agent_key="devbot",
        agent_uuid=AgentUUIDs.DEV_BOT,
        name=AgentNames.DEV_BOT,
        model_tier=_tier_for_agent("dev-bot", "pro"),
        allowed_handoffs=["david", "summary", "supervisor", "end"],
        requires_approval_tools=_write_tools_for_agent("dev-bot"),
    ),
    "david": AgentCard(
        agent_key="david",
        agent_uuid=AgentUUIDs.DEV_BOT,
        name="David (Senior Developer)",
        model_tier="lite",
        allowed_handoffs=["devbot", "summary", "supervisor", "end"],
        requires_approval_tools=["propose_code_fix"],
    ),
    "summary": AgentCard(
        agent_key="summary",
        agent_uuid=AgentUUIDs.SUPERVISOR,
        name="SummaryNode",
        model_tier="lite",
        allowed_handoffs=["end", "supervisor"],
    ),
}


def get_agent_card(role_key: str) -> AgentCard | None:
    """Returns the unified AgentCard for a workflow role key."""
    return DEFAULT_AGENT_CARDS.get(role_key.lower().strip())


def parse_handoff_directive(raw_text: str) -> tuple[str, str | None, str | None]:
    """
    Extracts an optional `[HANDOFF: <target> | <reason>]` directive from worker output.
    Returns (cleaned_text, target_role_key_or_None, reason_or_None).
    """
    if not raw_text:
        return "", None, None

    match = _HANDOFF_PATTERN.search(raw_text)
    if not match:
        return raw_text, None, None

    target = match.group(1).strip().lower()
    reason = match.group(2).strip() if match.group(2) else "Direct A2A handoff"
    cleaned = _HANDOFF_PATTERN.sub("", raw_text).strip()
    return cleaned, target, reason


def normalize_handoff_target(target: str) -> str:
    """Normalizes common aliases to canonical workflow node keys."""
    aliases = {
        "bob": "marketbot",
        "market-bot": "marketbot",
        "dev-bot": "devbot",
        "done": "end",
    }
    key = target.lower().strip()
    return aliases.get(key, key)


def resolve_direct_handoff(
    current_role: str,
    target_key: str | None,
    reason: str | None,
    state: SharedState,
) -> str:
    """
    Validates a direct A2A handoff against the sender's AgentCard allowlist,
    anti-self-loop guard, and max_steps circuit breaker.
    Returns the validated next node key (defaults to 'supervisor' if not allowed or omitted).
    """
    if not target_key:
        return "supervisor"

    sender = current_role.lower().strip()
    target = normalize_handoff_target(target_key)

    if state.step_count >= state.max_steps:
        logger.warning(f"🚫 [A2A] Max steps ({state.max_steps}) reached during handoff {sender} -> {target}. Ending.")
        return "end"

    if target == sender:
        logger.warning(f"⚠️ [A2A] Blocked self-loop handoff {sender} -> {target}; falling back to supervisor.")
        return "supervisor"

    card = get_agent_card(sender)
    if not card or target not in card.allowed_handoffs:
        logger.warning(f"⚠️ [A2A] Handoff {sender} -> {target} not in allowlist; falling back to supervisor.")
        return "supervisor"

    state.step_count += 1
    state.handoff_history.append(
        {
            "from": sender,
            "to": target,
            "reason": reason or "Direct A2A handoff",
        }
    )
    logger.info(f"🤝 [A2A Direct Handoff] {sender} -> {target} (Reason: {reason or 'Direct A2A handoff'})")
    return target
