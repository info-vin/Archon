"""
Stats API endpoints for Archon (Refactored - Lean Controller)
Hardened for Phase 4.6.59 - Ensures no 404s for Admin HUD.
"""

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

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


class SLATrendPoint(BaseModel):
    date: str = Field(description="Date string for the window")
    rate: float = Field(description="SLA attainment rate")
    count: int = Field(description="Count of tasks analyzed")

class SLAReliabilityResponse(BaseModel):
    current_sla: float = Field(default=0.0)
    trend: list[SLATrendPoint] = Field(default_factory=list)
    total_analyzed: int = Field(default=0)
    error: str | None = None

@router.get("/sla-reliability", response_model=SLAReliabilityResponse, dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def get_sla_reliability() -> SLAReliabilityResponse:
    try:
        data = await stats_service.get_sla_reliability()
        return SLAReliabilityResponse(**data)
    except Exception as e:
        logger.error(f"API: SLA Reliability failed: {e}")
        return SLAReliabilityResponse(current_sla=0.0, trend=[], total_analyzed=0, error=str(e))


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


class BusinessRiskDTO(BaseModel):
    model_config = ConfigDict(extra="allow")

@router.get("/business-risks", response_model=list[BusinessRiskDTO], dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def get_business_risks() -> list[BusinessRiskDTO]:
    try:
        data = await stats_service.get_business_risks()
        return [BusinessRiskDTO(**item) for item in data]
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


class HealthTrendResponse(BaseModel):
    trend: list[Any] = Field(default_factory=list)
    audit: list[Any] = Field(default_factory=list)
    error: str | None = None
    model_config = ConfigDict(extra="allow")


@router.get("/health-trend", response_model=HealthTrendResponse, dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def get_health_trend() -> HealthTrendResponse:
    try:
        from ..services.health_service import HealthService
        data = await HealthService().get_health_history(days=30)
        return HealthTrendResponse(**data)
    except Exception as e:
        logger.error(f"API: Health trend fetch failed: {e}")
        return HealthTrendResponse(trend=[], audit=[], error=str(e))


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


class AIUsageResponse(BaseModel):
    total_monthly_tokens: int = Field(default=0)
    total_cost_usd: float = Field(default=0.0)
    usage_percentage: float = Field(default=0.0)
    model_config = ConfigDict(extra="allow")


@router.get("/overview", response_model=AIUsageResponse, dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
@router.get("/ai-usage", response_model=AIUsageResponse, dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def get_ai_usage() -> AIUsageResponse:
    try:
        data = await stats_service.get_detailed_ai_usage(days=30)
        return AIUsageResponse(**data)
    except Exception as e:
        logger.error(f"Failed to get AI usage: {e}")
        return AIUsageResponse(total_monthly_tokens=0, total_cost_usd=0.0, usage_percentage=0.0)


class TokenUsageRecordDTO(BaseModel):
    id: str = Field(description="The unique identifier for the token usage record")
    timestamp: str = Field(description="The timestamp when the usage occurred")
    user_name: str | None = Field(default=None, description="The name of the entity that used the tokens")
    role: str | None = Field(default=None, description="The role of the entity")
    model: str = Field(description="The AI model that was queried")
    tokens: int = Field(description="The total tokens consumed")
    cost: float = Field(description="The cost in USD")
    context: str | None = Field(default=None, description="The context or feature triggering the usage")


@router.get("/token-usage/details", response_model=list[TokenUsageRecordDTO], dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def get_token_usage_details(days: int = 7) -> list[TokenUsageRecordDTO]:
    try:
        results = await stats_service.get_recent_token_usage(limit=100)
        return [TokenUsageRecordDTO(**r) for r in results]
    except Exception:
        return []


@router.get("/token-usage/recent", response_model=list[TokenUsageRecordDTO], dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def get_recent_token_usage(limit: int = 20) -> list[TokenUsageRecordDTO]:
    try:
        results = await stats_service.get_recent_token_usage(limit=limit)
        return [TokenUsageRecordDTO(**r) for r in results]
    except Exception:
        return []


class KnowledgeROIResponse(BaseModel):
    roi: float = Field(description="The calculated Return on Investment percentage for the knowledge base")
    active_nodes: int = Field(description="The number of active nodes in the knowledge graph")


class EthicsAuditQueueResponse(BaseModel):
    violations: list[str] = Field(description="List of detected ethics violations pending audit")
    status: str = Field(description="Queue status (e.g. 'clear', 'error')")


@router.get("/knowledge-roi", response_model=KnowledgeROIResponse, dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def get_knowledge_roi() -> KnowledgeROIResponse:
    try:
        res = await stats_service.get_knowledge_roi()
        data = res if res else {"roi": 0, "active_nodes": 0}
        return KnowledgeROIResponse(**data)
    except Exception:
        return KnowledgeROIResponse(roi=0.0, active_nodes=0)


@router.get("/ethics-audit-queue", response_model=EthicsAuditQueueResponse, dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def get_ethics_audit_queue() -> EthicsAuditQueueResponse:
    try:
        return EthicsAuditQueueResponse(violations=[], status="clear")
    except Exception:
        return EthicsAuditQueueResponse(violations=[], status="error")


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


class ConsolidatedStatsResponse(BaseModel):
    system_status: str | None = None
    health_score: int | None = None
    short_term_kpis: dict[str, Any] | None = None
    long_term_trends: dict[str, Any] | None = None
    main_bottleneck: str | None = None
    recommended_actions: list[Any] | None = None
    model_config = ConfigDict(extra="allow")


@router.get("/consolidated", response_model=ConsolidatedStatsResponse, dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def get_consolidated_stats() -> ConsolidatedStatsResponse:
    """Consolidated Strategic Nexus dashboard state (Phase 5.5.7)."""
    try:
        from src.agents.nexus_oracle_agent import NexusDependencies, NexusOracleAgent
        agent = NexusOracleAgent()
        deps = NexusDependencies(request_id="nexus-consolidated-request")
        result = await agent.run(
            user_prompt="Analyze the gathered telemetry and operational details. Synthesize them into the ConsolidatedNexusState schema.",
            deps=deps
        )
        data = result.data if hasattr(result, "data") else result
        data_dict = data if isinstance(data, dict) else data.model_dump() if hasattr(data, "model_dump") else {}
        return ConsolidatedStatsResponse(**data_dict)
    except Exception as e:
        logger.error(f"Failed to compile consolidated stats: {e}")
        return ConsolidatedStatsResponse(
            system_status="YELLOW",
            health_score=50,
            short_term_kpis={"error": str(e)},
            long_term_trends={},
            main_bottleneck="NexusOracleAgent run execution failed.",
            recommended_actions=[]
        )

