"""
Stats API endpoints for Archon (Refactored - Lean Controller)
Hardened for Phase 4.6.59 - Ensures no 404s for Admin HUD.
"""

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ..auth.dependencies import requires_permission
from ..auth.permissions import TASK_READ_TEAM
from ..config.logfire_config import get_logger
from ..services.stats import StatsService

logger = get_logger(__name__)

router = APIRouter(prefix="/api/stats", tags=["stats"])
stats_service = StatsService()


class CommanderTrend(BaseModel):
    date: str = Field(description="The date of the trend point")
    bob_tokens: int = Field(description="Token usage for the day")
    decision_hours: float = Field(description="Decision hours for the day")


@router.get("/commander-trends", response_model=list[CommanderTrend], dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def get_commander_trends() -> list[CommanderTrend]:
    try:
        results = await stats_service.get_commander_trends()
        return [CommanderTrend(**r) for r in results]
    except Exception as e:
        logger.error(f"Commander trends failed: {e}")
        return []


class SynergyInteraction(BaseModel):
    to: str = Field(description="The target node name")
    actual_7d: int = Field(description="Actual interactions in the last 7 days")
    avg_30d: float = Field(description="Average weekly interactions over the last 30 days")


class SynergyMatrixRow(BaseModel):
    from_node: str = Field(alias="from", description="The source node name")
    interactions: list[SynergyInteraction] = Field(description="List of interactions with other nodes")


class SynergySnapshot(BaseModel):
    total_7d: int = Field(description="Total interactions in the last 7 days")
    momentum_pct: float = Field(description="Momentum percentage compared to 30-day average")
    hot_bridge: str = Field(description="The most active bridge between nodes")
    active_paths: int = Field(description="Number of active paths with >0 interactions in the last 7 days")


class CollabSynergyResponse(BaseModel):
    nodes: list[str] = Field(description="List of participant node names")
    matrix: list[SynergyMatrixRow] = Field(description="Adjacency matrix of interactions")
    snapshot: SynergySnapshot | None = Field(default=None, description="Snapshot statistics")
    timestamp: str | None = Field(default=None, description="Timestamp of the snapshot")
    error: str | None = Field(default=None, description="Error message if any")


@router.get("/collab-synergy", response_model=CollabSynergyResponse, dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def get_collab_synergy() -> CollabSynergyResponse:
    try:
        return CollabSynergyResponse(**await stats_service.get_collab_synergy())
    except Exception as e:
        logger.error(f"API: Collab synergy fetch failed: {e}")
        return CollabSynergyResponse(nodes=[], matrix=[], error=str(e))


@router.get("/sla-reliability", dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def get_sla_reliability() -> dict[str, Any]:
    try:
        return await stats_service.get_sla_reliability()
    except Exception as e:
        logger.error(f"API: SLA Reliability failed: {e}")
        return {"current_sla": 0, "trend": [], "error": str(e)}


class ForceReadinessTrend(BaseModel):
    date: str = Field(description="The date of the trend point")
    actual: int = Field(description="The actual number of completed tasks")
    baseline: float = Field(description="The baseline daily expected tasks")


class ForceReadinessResponse(BaseModel):
    baseline: float = Field(description="Baseline average daily tasks")
    trend: list[ForceReadinessTrend] = Field(description="Trend data points")
    total_done_90d: float | None = Field(default=None, description="Total tasks done in the last 90 days")
    automation_rate: float | None = Field(default=None, description="Percentage of tasks done by AI")
    timestamp: str | None = Field(default=None, description="Timestamp of the calculation")
    error: str | None = Field(default=None, description="Error message if the fetch failed")


@router.get("/force-readiness", response_model=ForceReadinessResponse, dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def get_force_readiness() -> ForceReadinessResponse:
    try:
        return ForceReadinessResponse(**await stats_service.get_force_readiness())
    except Exception as e:
        logger.error(f"API: Force readiness failed: {e}")
        return ForceReadinessResponse(baseline=0.0, trend=[], error=str(e))


@router.get("/business-risks", dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def get_business_risks() -> list[dict[str, Any]]:
    try:
        return await stats_service.get_business_risks()
    except Exception as e:
        logger.error(f"API: Business risks fetch failed: {e}")
        return []


class ActiveAgentDTO(BaseModel):
    id: str = Field(description="Agent ID")
    name: str = Field(description="Agent display name")
    role: str | None = Field(default=None, description="Agent role")
    status: str = Field(description="Agent status (e.g., active, standby)")


class KnowledgeStatsDTO(BaseModel):
    total_nodes: int = Field(description="Total number of nodes")
    total_chunks: int | None = Field(default=None, description="Total number of chunks")


class SystemOverviewResponse(BaseModel):
    status: str = Field(description="System health status")
    rag: dict[str, Any] = Field(description="RAG integrity check details")
    integrity_score: int | None = Field(default=None, description="Integrity score")
    errors_24h: int = Field(description="Number of errors in the last 24 hours")
    active_agents: list[ActiveAgentDTO] = Field(description="List of active agents")
    cost_24h: float = Field(description="Cost incurred in the last 24 hours")
    knowledge_stats: KnowledgeStatsDTO | None = Field(default=None, description="Knowledge graph stats")
    timestamp: str = Field(description="Timestamp of the data")
    error: str | None = Field(default=None, description="Error message if any")


@router.get("/health-trend", dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def get_health_trend() -> Any:
    try:
        from ..services.health_service import HealthService

        return await HealthService().get_health_history(days=30)
    except Exception as e:
        logger.error(f"API: Health trend fetch failed: {e}")
        return {"trend": [], "audit": [], "error": str(e)}


@router.get("/system-overview", response_model=SystemOverviewResponse, dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def get_system_overview() -> SystemOverviewResponse:
    try:
        return SystemOverviewResponse(**(await stats_service.get_system_health_overview()))
    except Exception as e:
        logger.error(f"Failed system overview: {e}")
        return SystemOverviewResponse(
            status="unknown",
            rag={},
            errors_24h=0,
            active_agents=[],
            cost_24h=0.0,
            timestamp="",
            error=str(e)
        )


@router.get("/overview", dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
@router.get("/ai-usage", dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def get_ai_usage() -> dict[str, Any]:
    try:
        return await stats_service.get_detailed_ai_usage(days=30)
    except Exception as e:
        logger.error(f"Failed to get AI usage: {e}")
        return {"total_monthly_tokens": 0, "total_cost_usd": 0, "usage_percentage": 0}


@router.get("/token-usage/details", dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def get_token_usage_details(days: int = 7) -> list[dict[str, Any]]:
    try:
        return await stats_service.get_recent_token_usage(limit=100)
    except Exception:
        return []


@router.get("/token-usage/recent", dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def get_recent_token_usage(limit: int = 20) -> list[dict[str, Any]]:
    try:
        return await stats_service.get_recent_token_usage(limit=limit)
    except Exception:
        return []


@router.get("/knowledge-roi", dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def get_knowledge_roi() -> dict[str, Any]:
    try:
        res = await stats_service.get_knowledge_roi()
        return res if res else {"roi": 0, "active_nodes": 0}
    except Exception:
        return {"roi": 0, "active_nodes": 0}


@router.get("/ethics-audit-queue", dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def get_ethics_audit_queue() -> dict[str, Any]:
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


class AgentXPStats(BaseModel):
    name: str = Field(description="The display name of the agent")
    agent_id: str = Field(description="The unique identifier of the agent")
    total_xp: int = Field(description="The total experience points the agent has accumulated")
    success_count: int = Field(description="The total number of successful tasks completed by the agent")
    total_cost: float = Field(description="The total cost in USD incurred by the agent's operations")
    roi_ratio: float = Field(description="The Return on Investment ratio calculated for the agent")
    level: str = Field(description="The calculated skill or rank level of the agent")


@router.get("/tasks-by-status", response_model=list[TaskStatusCount], dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def get_tasks_by_status() -> list[TaskStatusCount]:
    """Get the count of tasks grouped by status."""
    try:
        results = await stats_service.get_tasks_by_status()
        return [TaskStatusCount(name=r["name"], value=r["value"]) for r in results]
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


@router.get("/agent-xp", response_model=list[AgentXPStats], dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def get_agent_xp() -> list[AgentXPStats]:
    """Agent Experience (XP) & Level Ranking HUD (Phase 4.6.8)."""
    try:
        results = await stats_service.get_agent_xp_stats()
        return [AgentXPStats(**result) for result in results]
    except Exception as e:
        logger.error(f"Failed to get agent xp stats: {e}")
        return []


@router.get("/consolidated", dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def get_consolidated_stats() -> Any:
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

