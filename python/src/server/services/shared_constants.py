# python/src/server/services/shared_constants.py
from dataclasses import dataclass
from enum import StrEnum


@dataclass(frozen=True)
class AgentNames:
    SUPERVISOR = "Supervisor (Group Chat)"
    MARKET_BOT = "MarketBot (Sales)"
    LIBRARIAN = "Librarian (Knowledge)"
    DEV_BOT = "DevBot (Engineering)"
    PO_BOT = "POBot (Product)"
    CLOCKWORK = "Clockwork (Ops)"


@dataclass(frozen=True)
class AgentUUIDs:
    """
    Physical Source of Truth for AI Agent Identities (Phase 4.6.47 Grounded).
    Eliminates hardcoded strings while maintaining test stability.
    """

    SUPERVISOR = "f0f00000-0000-0000-0000-000000000000"
    MARKET_BOT = "a11ce000-0000-0000-0000-000000000000"
    LIBRARIAN = "b0b00000-0000-0000-0000-000000000000"
    DEV_BOT = "e1682371-0000-0000-0000-000000000000"
    PO_BOT = "p0b00000-0000-0000-0000-000000000000"
    CLOCKWORK = "e1bf7a99-44bf-44ce-a460-cb4e31e798f4"


class ProcessingMode(StrEnum):
    """Processing modes for different workload types"""

    CPU_INTENSIVE = "cpu_intensive"  # AI summaries, embeddings, heavy computation
    IO_BOUND = "io_bound"  # Database operations, file I/O
    NETWORK_BOUND = "network_bound"  # External API calls, web requests
    WEBSOCKET_SAFE = "websocket_safe"  # Operations that need to yield for WebSocket health


# Known AI agent roles that can be assigned tasks
AI_AGENT_ROLES = {
    "Supervisor (Group Chat)": AgentUUIDs.SUPERVISOR,
    "MarketBot (Sales)": AgentUUIDs.MARKET_BOT,
    "Librarian (Knowledge)": AgentUUIDs.LIBRARIAN,
    "DevBot (Engineering)": AgentUUIDs.DEV_BOT,
    "POBot (Product)": AgentUUIDs.PO_BOT,
    "Clockwork (Ops)": AgentUUIDs.CLOCKWORK,
}
