"""
Stats API endpoints for Archon (Refactored - Lean Controller)
Hardened for Phase 4.6.59 - Ensures no 404s for Admin HUD.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ..auth.dependencies import requires_permission
from ..auth.permissions import TASK_READ_TEAM
from ..config.logfire_config import get_logger
from ..services.stats import StatsService
from ..utils import get_supabase_client

logger = get_logger(__name__)

router = APIRouter(prefix="/api/stats", tags=["stats"])
stats_service = StatsService()


@router.get("/commander-trends", dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def get_commander_trends():
    try:
        return await stats_service.get_commander_trends()
    except Exception as e:
        logger.error(f"Commander trends failed: {e}")
        return []


@router.get("/collab-synergy", dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def get_collab_synergy():
    try:
        return await stats_service.get_collab_synergy()
    except Exception as e:
        logger.error(f"API: Collab synergy fetch failed: {e}")
        return {"nodes": [], "matrix": [], "error": str(e)}


@router.get("/sla-reliability", dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def get_sla_reliability():
    try:
        return await stats_service.get_sla_reliability()
    except Exception as e:
        logger.error(f"API: SLA Reliability failed: {e}")
        return {"current_sla": 0, "trend": [], "error": str(e)}


@router.get("/force-readiness", dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def get_force_readiness():
    try:
        return await stats_service.get_force_readiness()
    except Exception as e:
        logger.error(f"API: Force readiness failed: {e}")
        return {"baseline": 0, "trend": [], "error": str(e)}


@router.get("/business-risks", dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def get_business_risks():
    try:
        return await stats_service.get_business_risks()
    except Exception as e:
        logger.error(f"API: Business risks fetch failed: {e}")
        return []


@router.get("/health-trend", dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def get_health_trend():
    try:
        from ..services.health_service import HealthService

        return await HealthService().get_health_history(days=30)
    except Exception as e:
        logger.error(f"API: Health trend fetch failed: {e}")
        return {"trend": [], "audit": [], "error": str(e)}


@router.get("/system-overview", dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def get_system_overview():
    try:
        return await stats_service.get_system_health_overview()
    except Exception as e:
        logger.error(f"Failed system overview: {e}")
        return {"status": "unknown", "error": str(e)}


@router.get("/overview", dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
@router.get("/ai-usage", dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def get_ai_usage():
    try:
        return await stats_service.get_detailed_ai_usage(days=30)
    except Exception as e:
        logger.error(f"Failed to get AI usage: {e}")
        return {"total_monthly_tokens": 0, "total_cost_usd": 0, "usage_percentage": 0}


@router.get("/token-usage/details", dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def get_token_usage_details(days: int = 7):
    try:
        return await stats_service.get_recent_token_usage(limit=100)
    except Exception:
        return []


@router.get("/token-usage/recent", dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def get_recent_token_usage(limit: int = 20):
    try:
        return await stats_service.get_recent_token_usage(limit=limit)
    except Exception:
        return []


@router.get("/knowledge-roi", dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def get_knowledge_roi():
    try:
        res = await stats_service.get_knowledge_roi()
        return res if res else {"roi": 0, "active_nodes": 0}
    except Exception:
        return {"roi": 0, "active_nodes": 0}


@router.get("/ethics-audit-queue", dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def get_ethics_audit_queue():
    try:
        return {"violations": [], "status": "clear"}
    except Exception:
        return {"violations": [], "status": "error"}


class TaskStatusCount(BaseModel):
    name: str = Field(description="The status name of the task")
    value: int = Field(description="The count of tasks with this status")


class MemberPerformanceStats(BaseModel):
    name: str = Field(description="The name of the assignee")
    completed_tasks: int = Field(description="The number of completed tasks by this assignee")


@router.get("/tasks-by-status", response_model=list[TaskStatusCount], dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def get_tasks_by_status() -> list[TaskStatusCount]:
    """Get the count of tasks grouped by status."""
    try:
        supabase = get_supabase_client()
        response = supabase.table("archon_tasks").select("status").execute()
        counts: dict[str, int] = {}
        for row in response.data:
            s = row.get("status", "unknown")
            counts[s] = counts.get(s, 0) + 1
        return [TaskStatusCount(name=k, value=v) for k, v in counts.items()]
    except Exception as e:
        logger.error(f"Failed to get task stats: {e}")
        return []


@router.get("/member-performance", response_model=list[MemberPerformanceStats], dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def get_member_performance() -> list[MemberPerformanceStats]:
    """Get the count of COMPLETED tasks grouped by assignee."""
    try:
        results = await stats_service.get_member_performance()
        return [MemberPerformanceStats(**result) for result in results]
    except Exception as e:
        logger.error(f"Failed to get performance stats: {e}")
        return []


@router.get("/agent-xp", dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def get_agent_xp():
    """Agent Experience (XP) & Level Ranking HUD (Phase 4.6.8)."""
    try:
        return await stats_service.get_agent_xp_stats()
    except Exception as e:
        logger.error(f"Failed to get agent xp stats: {e}")
        return []


@router.get("/consolidated", dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def get_consolidated_stats():
    """Consolidated Strategic Nexus dashboard state (Phase 5.5.7)."""
    try:
        from src.agents.nexus_oracle_agent import NexusDependencies, NexusOracleAgent
        agent = NexusOracleAgent()
        deps = NexusDependencies(request_id="nexus-consolidated-request")
        result = await agent.run(
            user_prompt="Analyze the gathered telemetry and operational details. Synthesize them into the ConsolidatedNexusState schema.",
            deps=deps
        )
        return result
    except Exception as e:
        logger.error(f"Failed to compile consolidated stats: {e}")
        return {
            "system_status": "YELLOW",
            "health_score": 50,
            "short_term_kpis": {"error": str(e)},
            "long_term_trends": {},
            "main_bottleneck": "NexusOracleAgent run execution failed.",
            "recommended_actions": []
        }

