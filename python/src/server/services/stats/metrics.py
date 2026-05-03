import logging
from typing import Any

from ...utils import get_supabase_client
from .domains.agent_metrics import AgentMetrics
from .domains.knowledge_metrics import KnowledgeMetrics
from .domains.marketing_metrics import MarketingMetrics
from .domains.system_metrics import SystemMetrics

logger = logging.getLogger(__name__)

class MetricsManager:
    """
    Handles technical metrics, trends, and ROI calculations for Archon.
    Physical Realization of Phase 4.6.24 modularization standard.
    Acts as a Coordinator delegating to domain-specific metric classes.
    """

    def __init__(self, supabase_client=None):
        self.supabase = supabase_client or get_supabase_client()
        self.agent_metrics = AgentMetrics(self.supabase)
        self.knowledge_metrics = KnowledgeMetrics(self.supabase)
        self.system_metrics = SystemMetrics(self.supabase)
        self.marketing_metrics = MarketingMetrics(self.supabase)

    async def get_commander_trends(self) -> list[dict[str, Any]]:
        return await self.agent_metrics.get_commander_trends()

    async def get_force_readiness(self) -> dict[str, Any]:
        return await self.agent_metrics.get_force_readiness()

    async def get_knowledge_roi(self) -> dict[str, Any]:
        return await self.knowledge_metrics.get_knowledge_roi()

    async def get_sla_reliability(self) -> dict[str, Any]:
        return await self.system_metrics.get_sla_reliability()

    async def get_detailed_ai_usage(self, days: int = 30) -> dict[str, Any]:
        return await self.system_metrics.get_detailed_ai_usage(days)

    async def get_recent_token_usage(self, limit: int = 20) -> list[dict[str, Any]]:
        return await self.system_metrics.get_recent_token_usage(limit)

    async def get_marketing_intelligence(self, user_id: str | None = None) -> dict[str, Any]:
        return await self.marketing_metrics.get_marketing_intelligence(user_id)
