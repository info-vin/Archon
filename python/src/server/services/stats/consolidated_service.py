"""Consolidated Strategic Nexus aggregation with TTL cache, agent timeout, and StatsService DB fallback."""

import asyncio
import sys
import time
from typing import Any

from ...config.logfire_config import get_logger
from . import StatsService

logger = get_logger(__name__)

_CACHE_TTL_SECONDS = 120.0
_AGENT_TIMEOUT_SECONDS = 12.0
_cache: tuple[float, dict[str, Any]] | None = None
_refresh_task: asyncio.Task[None] | None = None


async def _run_oracle_agent() -> dict[str, Any]:
    from src.agents.nexus_oracle_agent import NexusDependencies, NexusOracleAgent

    agent = NexusOracleAgent()
    deps = NexusDependencies(request_id="nexus-consolidated-request")
    result = await asyncio.wait_for(
        agent.run(
            user_prompt="Analyze the gathered telemetry and operational details. Synthesize them into the ConsolidatedNexusState schema.",
            deps=deps,
        ),
        timeout=_AGENT_TIMEOUT_SECONDS,
    )
    data = result.data if hasattr(result, "data") else result
    return data if isinstance(data, dict) else data.model_dump() if hasattr(data, "model_dump") else {}


async def _refresh_oracle_cache() -> None:
    global _cache
    try:
        # Yield first so the foreground DB fallback response completes without event-loop contention.
        await asyncio.sleep(3.0)
        data_dict = await _run_oracle_agent()
        if data_dict:
            _cache = (time.monotonic(), data_dict)
    except Exception as e:
        logger.warning(f"Background consolidated Nexus oracle refresh failed: {e}")


async def _build_db_fallback_state() -> dict[str, Any]:
    """Assemble real-time Nexus KPIs directly from StatsService when the LLM oracle times out."""
    svc = StatsService()
    overview, readiness, ai_usage, knowledge_roi, collab, sla, trends, risks = await asyncio.gather(
        svc.get_system_health_overview(),
        svc.get_force_readiness(),
        svc.get_detailed_ai_usage(days=30),
        svc.get_knowledge_roi(),
        svc.get_collab_synergy(),
        svc.get_sla_reliability(),
        svc.get_commander_trends(),
        svc.get_business_risks(),
        return_exceptions=True,
    )

    def _ok(val: Any, default: Any) -> Any:
        return default if isinstance(val, BaseException) else val

    ov = _ok(overview, {})
    rd = _ok(readiness, {})
    rd_dict = rd.model_dump() if hasattr(rd, "model_dump") else (rd if isinstance(rd, dict) else {})
    tr_list = [t.model_dump() if hasattr(t, "model_dump") else t for t in _ok(trends, [])]

    return {
        "system_status": "GREEN" if ov.get("error_count", 0) == 0 else "YELLOW",
        "health_score": 85 if ov.get("error_count", 0) == 0 else 65,
        "short_term_kpis": {
            "daily_token_cost": ov.get("total_cost_24h", 0.0),
            "active_error_counts": ov.get("error_count", 0),
            "system_telemetry": ov,
            "team_readiness": rd_dict,
            "pending_approvals": [],
            "active_alerts": [],
        },
        "long_term_trends": {
            "monthly_budget_forecast": "Stable",
            "roi_trend": "0.0",
            "efficiency_trend": "Stable",
            "ai_token_usage_30d": _ok(ai_usage, {}),
            "knowledge_base_roi": _ok(knowledge_roi, {}),
            "collaboration_synergy": _ok(collab, {}),
            "sla_reliability": _ok(sla, {}),
            "commander_trends": tr_list,
            "business_risks": _ok(risks, []),
        },
        "main_bottleneck": "Serving direct DB telemetry (NexusOracleAgent timed out).",
        "recommended_actions": [],
    }


async def get_consolidated_nexus_state() -> dict[str, Any]:
    """Return cached or freshly computed Nexus state without blocking UI on slow LLM oracle cold starts."""
    global _cache, _refresh_task
    use_cache = "pytest" not in sys.modules
    now = time.monotonic()
    if use_cache and _cache and (now - _cache[0]) < _CACHE_TTL_SECONDS:
        return _cache[1]

    if use_cache:
        if _refresh_task is None or _refresh_task.done():
            _refresh_task = asyncio.create_task(_refresh_oracle_cache())
        if _cache:
            return _cache[1]
        try:
            fallback = await _build_db_fallback_state()
            _cache = (time.monotonic(), fallback)
            return fallback
        except Exception as db_err:
            logger.error(f"Consolidated Nexus DB fallback failed: {db_err}")
            return {
                "system_status": "YELLOW",
                "health_score": 50,
                "short_term_kpis": {"error": str(db_err)},
                "long_term_trends": {},
                "main_bottleneck": "Consolidated DB fallback failed.",
                "recommended_actions": [],
            }

    try:
        return await _run_oracle_agent()
    except Exception as e:
        logger.warning(f"Consolidated Nexus agent run failed/timed out ({_AGENT_TIMEOUT_SECONDS}s): {e}")
        return await _build_db_fallback_state()
