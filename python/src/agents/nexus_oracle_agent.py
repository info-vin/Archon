"""
NexusOracleAgent - Consolidates Charlie's Nexus dashboard metrics using PydanticAI.
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from .base_agent import ArchonDependencies, BaseAgent

logger = logging.getLogger(__name__)


@dataclass
class NexusDependencies(ArchonDependencies):
    """Dependencies for the Nexus Oracle Agent."""
    progress_callback: Any | None = None


class PriorityAction(BaseModel):
    """Actions requiring Charlie's attention."""
    action_id: str
    target: str = Field(description="The target entity (e.g. Bob, DevBot, Acme Corp).")
    risk_level: str = Field(description="CRITICAL, WARNING, or INFO.")
    reason: str = Field(description="Explanation of why this action is flagged.")
    one_click_tool: str = Field(description="Name of the action or tool button to resolve the issue.")


class ShortTermKPIs(BaseModel):
    """Structured short-term KPIs for the last 24h."""
    daily_token_cost: float = Field(description="Total token cost over the last 24 hours in USD.")
    active_error_counts: int = Field(description="Total active system error log counts.")
    system_telemetry: dict = Field(description="System telemetry properties: errors_24h, cost_24h, active_agents, rag, knowledge_stats.")
    team_readiness: dict = Field(description="Team force readiness details.")
    pending_approvals: list[dict] = Field(description="List of pending approval blog/lead records. Do NOT return a count, return the actual list of objects.")
    active_alerts: list[dict] = Field(description="List of active system alerts.")


class LongTermTrends(BaseModel):
    """Structured strategic trends over 7d/30d."""
    monthly_budget_forecast: str = Field(description="Budget forecast summary string.")
    roi_trend: str = Field(description="ROI trend description.")
    efficiency_trend: str = Field(description="System efficiency trend summary.")
    ai_token_usage_30d: dict | None = Field(default=None, description="Detailed 30d AI Usage stats.")
    knowledge_base_roi: dict | None = Field(default=None, description="Knowledge base ROI analysis details.")
    collaboration_synergy: dict | None = Field(default=None, description="Team collaboration synergy metrics.")
    sla_reliability: dict | None = Field(default=None, description="SLA reliability metrics.")
    commander_trends: list[dict] = Field(default_factory=list, description="Manager metrics trends list.")
    business_risks: list[dict] = Field(default_factory=list, description="Business risks list.")


class ConsolidatedNexusState(BaseModel):
    """Consolidated state schema for the Manager Nexus dashboard."""
    system_status: str = Field(description="Overall system color code: RED, YELLOW, or GREEN.")
    health_score: int = Field(description="Integer health score from 0 to 100.")

    # Split metrics into short-term vs long-term cycles
    short_term_kpis: ShortTermKPIs = Field(description="Structured key metrics for the last 24h.")
    long_term_trends: LongTermTrends = Field(description="Structured strategic metrics over 7d/30d.")

    main_bottleneck: str = Field(description="The most critical bottleneck currently slowing down workflow operations.")
    recommended_actions: list[PriorityAction] = Field(description="A prioritized list of alerts and approvals requiring Charlie's review.")


class NexusOracleAgent(BaseAgent[NexusDependencies, ConsolidatedNexusState]):
    """
    NexusOracleAgent gathers system health, token usage, pending approvals, and active tasks.
    It summarizes them into a simplified ConsolidatedNexusState for Charlie.
    """

    def __init__(self, model: str | None = None, **kwargs):
        if model is None:
            # Fallback to model_ssot default or environment variable
            model = os.getenv("SUPERVISOR_AGENT_MODEL")
            if not model:
                from src.server.config.model_ssot import SYSTEM_MODELS
                model = SYSTEM_MODELS["DEFAULT_PRO"]

        if isinstance(model, str):
            model = model.replace("models/", "")
            if ":" not in model:
                model = f"google-gla:{model}"

        super().__init__(model=model, name="NexusOracleAgent", retries=3, enable_rate_limiting=True, **kwargs)

    def _create_agent(self, **kwargs) -> Agent[NexusDependencies, ConsolidatedNexusState]:
        """Create the PydanticAI agent configuration."""
        from src.server.services.prompt_service import prompt_service

        default_prompt = (
            "You are Charlie's strategic dashboard orchestrator. Your objective is to digest multiple raw system metric sources "
            "(health checks, token consumption logs, pending approvals, pending blog drafts, and team SLA status) and consolidate them into a simplified, "
            "cohesive overview. Keep your descriptions concise. Identify the main bottleneck and prioritize actions requiring the manager's attention. "
            "IMPORTANT: You MUST include all items from the 'pending_blogs' list under short_term_kpis['pending_approvals'], ensuring you preserve their exact fields "
            "(such as id, title, author_name, created_at, content, target_brand) and add the key-value pair 'type': 'blog' to each item so the frontend dashboard can render them."
        )
        system_prompt = prompt_service.get_prompt("nexus_oracle_agent_prompt", default_prompt)

        from src.agents.utils.resilience import PAI_V1

        agent_kwargs = {
            "model": self.model,
            "deps_type": NexusDependencies,
            "system_prompt": system_prompt,
            **kwargs,
        }
        if PAI_V1:
            agent_kwargs["output_type"] = ConsolidatedNexusState
        else:
            agent_kwargs["result_type"] = ConsolidatedNexusState

        agent = Agent(**agent_kwargs)

        @agent.tool
        async def gather_nexus_data(ctx: RunContext[NexusDependencies]) -> dict:
            """
            Asynchronously queries all existing backend services for current system and operational metrics.
            """
            from src.server.services.stats import stats_service
            from src.server.utils import get_supabase_client

            supabase = get_supabase_client()

            async def run_query(query):
                try:
                    return await asyncio.to_thread(query.execute)
                except Exception as e:
                    logger.warning(f"NexusOracleAgent query failed: {e}")
                    return e

            # Execute gather tasks in parallel to avoid endpoint lag (Map-Reduce)
            results = await asyncio.gather(
                stats_service.get_system_health_overview(),
                stats_service.get_force_readiness(),
                stats_service.get_detailed_ai_usage(days=30),
                stats_service.get_knowledge_roi(),
                stats_service.get_sla_reliability(),
                stats_service.get_collab_synergy(),
                stats_service.get_business_risks(),
                # Fetch pending approvals & changes directly from DB/service layers
                run_query(supabase.table("archon_logs").select("*").eq("level", "ALERT").limit(10)),
                run_query(supabase.table("archon_approvals").select("*").eq("status", "pending")),
                run_query(supabase.table("blog_posts").select("*").eq("status", "review")),
                return_exceptions=True
            )

            # Extract list values safely
            telemetry = results[0] if not isinstance(results[0], Exception) else {}
            readiness = results[1] if not isinstance(results[1], Exception) else {}
            ai_usage = results[2] if not isinstance(results[2], Exception) else {}
            k_roi = results[3] if not isinstance(results[3], Exception) else {}
            sla = results[4] if not isinstance(results[4], Exception) else {}
            synergy = results[5] if not isinstance(results[5], Exception) else {}
            biz_risks = results[6] if not isinstance(results[6], Exception) else []
            alerts_res = results[7]
            approvals_res = results[8]
            blogs_res = results[9]

            alerts = getattr(alerts_res, "data", []) if not isinstance(alerts_res, Exception) else []
            approvals = getattr(approvals_res, "data", []) if not isinstance(approvals_res, Exception) else []
            blogs = getattr(blogs_res, "data", []) if not isinstance(blogs_res, Exception) else []

            return {
                "system_telemetry": telemetry,
                "team_readiness": readiness,
                "ai_token_usage_30d": ai_usage,
                "knowledge_base_roi": k_roi,
                "sla_reliability": sla,
                "collaboration_synergy": synergy,
                "business_risks": biz_risks,
                "active_alerts": alerts,
                "pending_approvals": approvals,
                "pending_blogs": blogs
            }

        return agent

    def get_system_prompt(self) -> str:
        """Get the base system prompt."""
        return "You are Charlie's strategic dashboard orchestrator. Your objective is to digest multiple raw system metric sources and consolidate them. Ensure pending blog drafts are formatted as type: 'blog' inside short_term_kpis['pending_approvals']."
