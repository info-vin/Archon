"""
Stats Package for Archon
Provides centralized metrics and performance auditing.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from ...utils import get_supabase_client
from .metrics import MetricsManager
from .performance import PerformanceManager

logger = logging.getLogger(__name__)


class StatsService:
    """
    Facade for all system statistics.
    Maintains 100% backward compatibility with legacy StatsService.
    """

    def __init__(self, supabase_client=None):
        self.supabase = supabase_client or get_supabase_client()
        self.metrics = MetricsManager(self.supabase)
        self.performance = PerformanceManager(self.supabase)

    # --- METRICS & TRENDS ---
    async def get_tasks_by_status(self) -> list[dict[str, Any]]:
        """Backwards compatibility for frontend stats."""
        try:
            response = self.supabase.table("archon_tasks").select("status").execute()
            counts: dict[str, int] = {}
            for row in response.data:
                s = row.get("status", "unknown")
                counts[s] = counts.get(s, 0) + 1
            return [{"name": k, "value": v} for k, v in counts.items()]
        except Exception as e:
            logger.error(f"StatsService: Tasks by status failed: {e}")
            return []

    async def get_marketing_intelligence(self) -> dict[str, Any]:
        return await self.metrics.get_marketing_intelligence()

    async def get_commander_trends(self) -> list[dict[str, Any]]:
        return await self.metrics.get_commander_trends()

    async def get_force_readiness(self) -> dict[str, Any]:
        return await self.metrics.get_force_readiness()

    async def get_knowledge_roi(self) -> dict[str, Any]:
        return await self.metrics.get_knowledge_roi()

    async def get_sla_reliability(self) -> dict[str, Any]:
        return await self.metrics.get_sla_reliability()

    async def get_detailed_ai_usage(self, days: int = 30) -> dict[str, Any]:
        return await self.metrics.get_detailed_ai_usage(days=days)

    async def get_recent_token_usage(self, limit: int = 20) -> list[dict[str, Any]]:
        return await self.metrics.get_recent_token_usage(limit=limit)

    # --- PERFORMANCE & XP ---
    @staticmethod
    def calculate_ai_score(content: str, metadata: dict | None = None) -> int:
        return PerformanceManager.calculate_ai_score(content, metadata)

    async def add_agent_action_log(
        self,
        agent_name: str,
        xp_change: int,
        message: str,
        details: dict | None = None,
        content: str | None = None,
        agent_id: str | None = None,
    ) -> None:
        await self.performance.add_agent_action_log(agent_name, xp_change, message, details, content, agent_id)

    async def get_agent_xp_stats(self) -> list[dict[str, Any]]:
        return await self.performance.get_agent_xp_stats()

    async def get_member_performance(self) -> list[dict[str, Any]]:
        return await self.performance.get_member_performance()

    async def get_collab_synergy(self) -> dict[str, Any]:
        return await self.performance.get_collab_synergy()

    async def get_business_risks(self) -> list[dict[str, Any]]:
        return await self.performance.get_business_risks()

    async def get_system_health_overview(self) -> dict[str, Any]:
        """Consolidated health and performance overview for Admin (1:1 Restoration)."""
        try:
            from ..health_service import HealthService

            rag_health = await HealthService().check_rag_integrity()
            one_day_ago = (datetime.now(UTC) - timedelta(hours=24)).isoformat()

            # 1. Error Count
            error_res = (
                self.supabase.table("archon_logs")
                .select("id", count="exact")
                .eq("level", "ERROR")
                .gt("created_at", one_day_ago)
                .execute()
            )
            error_count = error_res.count if error_res.count is not None else 0

            # 2. 24h Cost
            cost_res = self.supabase.table("token_usage").select("cost_usd").gt("created_at", one_day_ago).execute()
            total_cost_24h = sum(float(r.get("cost_usd", 0)) for r in (cost_res.data or []))

            # 3. Active Agents
            one_hour_ago = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
            logs_res = self.supabase.table("archon_logs").select("source").gt("created_at", one_hour_ago).execute()
            active_sources = {log["source"] for log in (logs_res.data or [])}
            # PERFORMANCE: Extract string conversion outside loop and unroll nested generator
            active_sources_lower = [s.lower() for s in active_sources]

            agents_manifest = [
                {"id": "clockwork", "name": "Clockwork", "role": "Scheduler"},
                {"id": "sentinel", "name": "Sentinel", "role": "Guard"},
                {"id": "librarian", "name": "Librarian", "role": "RAG Service"},
                {"id": "devbot", "name": "DevBot", "role": "System Engineer"},
            ]

            active_agents = []
            for agent in agents_manifest:
                agent_id = agent["id"]
                is_active = agent_id in active_sources
                if not is_active:
                    for s_lower in active_sources_lower:
                        if agent_id in s_lower:
                            is_active = True
                            break
                active_agents.append({**agent, "status": "active" if is_active else "standby"})

            return {
                "status": "healthy" if rag_health.get("status") == "healthy" and error_count < 10 else "degraded",
                "rag": rag_health,
                "errors_24h": error_count,
                "active_agents": active_agents,
                "cost_24h": round(total_cost_24h, 4),
                "timestamp": datetime.now(UTC).isoformat(),
                "integrity_score": rag_health.get("score", 0),
                "knowledge_stats": {"total_nodes": rag_health.get("details", {}).get("total_sources", 0)},
            }
        except Exception as e:
            logger.error(f"StatsService: Overview failed: {e}")
            return {"status": "error", "error": str(e)}


# Global singleton instance
stats_service = StatsService()
