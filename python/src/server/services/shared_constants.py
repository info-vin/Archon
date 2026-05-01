# python/src/server/services/shared_constants.py
from dataclasses import dataclass


@dataclass(frozen=True)
class AgentUUIDs:
    """
    Physical Source of Truth for AI Agent Identities (Phase 4.6.47 Grounded).
    Eliminates hardcoded strings while maintaining test stability.
    """
    MARKET_BOT = "a11ce000-0000-0000-0000-000000000000"
    LIBRARIAN = "b0b00000-0000-0000-0000-000000000000"
    DEV_BOT = "e1682371-0000-0000-0000-000000000000"
    PO_BOT = "p0b00000-0000-0000-0000-000000000000"
    CLOCKWORK = "e1bf7a99-44bf-44ce-a460-cb4e31e798f4"

# Known AI agent roles that can be assigned tasks
AI_AGENT_ROLES = {
    "MarketBot (Sales)": AgentUUIDs.MARKET_BOT,
    "Librarian (Knowledge)": AgentUUIDs.LIBRARIAN,
    "DevBot (Engineering)": AgentUUIDs.DEV_BOT,
    "POBot (Product)": AgentUUIDs.PO_BOT,
    "Clockwork (Ops)": AgentUUIDs.CLOCKWORK,
}
