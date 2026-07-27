"""
Stats Package for Archon
Provides centralized metrics and performance auditing.
"""

import logging
import os
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

    def __init__(self, supabase_client: Any | None = None) -> None:
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

            agents_manifest: list[dict[str, Any]] = [
                {"id": "clockwork", "name": "Clockwork", "role": "Scheduler"},
                {"id": "sentinel", "name": "Sentinel", "role": "Guard"},
                {"id": "librarian", "name": "Librarian", "role": "RAG Service"},
                {"id": "devbot", "name": "DevBot", "role": "System Engineer"},
            ]

            # 4. Phase 5.1.15: Clockwork Jobs Snapshot
            clockwork_jobs: list[dict[str, Any]] = []
            try:
                from ..scheduler_service import scheduler_service

                # Get memory state of scheduler jobs
                active_job_ids = set()
                if scheduler_service._scheduler:
                    for job in scheduler_service._scheduler.get_jobs():
                        active_job_ids.add(job.id)
                        next_run = job.next_run_time.isoformat() if job.next_run_time else None

                        # Handle stateless initial vs loop jobs
                        display_id = job.id.replace("_initial", "")

                        # Determine Category based on phase 5.1.14 design
                        job_type = "stateful_daily"
                        if display_id in ["system_probe", "log_patrol", "task_dispatcher", "model_verification"]:
                            job_type = "stateless_patrol"
                        elif display_id in ["tech_debt_audit", "api_deprecation_scan"]:
                            job_type = "stateful_biweekly"

                        # Deduplicate (preferring the active loop over the initial delay if both exist)
                        existing_job = next((j for j in clockwork_jobs if j["id"] == display_id), None)
                        if existing_job:
                            # Update next_run if this job is scheduled sooner
                            if next_run and (not existing_job["next_run"] or next_run < existing_job["next_run"]):
                                existing_job["next_run"] = next_run
                            existing_job["status"] = "scheduled"
                            continue

                        # Fetch Last Run from DB
                        last_run_db = await scheduler_service._get_last_run(display_id)
                        last_run_iso = last_run_db.isoformat() if last_run_db else None

                        clockwork_jobs.append({
                            "id": display_id,
                            "name": display_id.replace("_", " ").title(),
                            "type": job_type,
                            "last_run": last_run_iso,
                            "next_run": next_run,
                            "status": "scheduled" if next_run else "idle"
                        })

                # Find DB-only jobs that might have completed and been removed from scheduler
                env_prefix = os.environ.get("ARCHON_ENV", "")
                last_run_prefix = f"{env_prefix}LAST_RUN_"

                db_keys_res = self.supabase.table("archon_settings").select("key, value").like("key", f"{last_run_prefix}%").execute()
                for row in (db_keys_res.data or []):
                    job_id = row["key"].replace(last_run_prefix, "").lower()
                    if not any(j["id"] == job_id for j in clockwork_jobs):
                        # Job is not in memory (likely completed for the day)
                        clockwork_jobs.append({
                            "id": job_id,
                            "name": job_id.replace("_", " ").title(),
                            "type": "stateful_daily" if job_id not in ["tech_debt_audit", "api_deprecation_scan"] else "stateful_biweekly",
                            "last_run": row["value"],
                            "next_run": None,
                            "status": "completed"
                        })

            except Exception as e:
                logger.error(f"Failed to fetch clockwork jobs: {e}")

            active_agents = []
            for agent in agents_manifest:
                agent_id = agent["id"]
                is_active = agent_id in active_sources
                if not is_active:
                    for s_lower in active_sources_lower:
                        if agent_id in s_lower:
                            is_active = True
                            break

                agent_data = {**agent, "status": "active" if is_active else "standby"}

                # Attach Phase 5.1.15 data to Clockwork
                if agent_id == "clockwork":
                    agent_data["jobs_snapshot"] = clockwork_jobs

                active_agents.append(agent_data)

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

    async def get_team_availability(self, user_ids: list[str], target_date: str) -> list[dict[str, Any]]:
        """Delegates to SystemMetrics for availability calculation (Phase 5.4.6)."""
        return await self.metrics.system_metrics.get_team_availability(user_ids, target_date)


# Global singleton instance
stats_service = StatsService()
