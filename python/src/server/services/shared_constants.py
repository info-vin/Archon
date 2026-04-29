# python/src/server/services/shared_constants.py
from dataclasses import dataclass

@dataclass(frozen=True)
class AgentUUIDs:
    """
    Physical Source of Truth for AI Agent Identities (Phase 4.6.47 Grounded).
    Used to eliminate hardcoded strings across the system.
    """
    MARKET_BOT = "f3f1c1cc-29c9-4036-bd86-a4a58edad237"
    LIBRARIAN = "579f988b-4b92-49b4-956a-28d4810eeaad"
    DEV_BOT = "bcb00484-30bd-46fb-9e39-84b2ec4ced31"
    PO_BOT = "abdd3904-f4b9-42be-ab04-15935da7c3a8"
    CLOCKWORK = "e1bf7a99-44bf-44ce-a460-cb4e31e798f4"

# Known AI agent roles that can be assigned tasks
# Format: { "Display Name": "agent-id" }
AI_AGENT_ROLES = {
    "MarketBot (Sales)": AgentUUIDs.MARKET_BOT,
    "Librarian (Knowledge)": AgentUUIDs.LIBRARIAN,
    "DevBot (Engineering)": AgentUUIDs.DEV_BOT,
    "POBot (Product)": AgentUUIDs.PO_BOT,
    "Clockwork (Ops)": AgentUUIDs.CLOCKWORK,
}
