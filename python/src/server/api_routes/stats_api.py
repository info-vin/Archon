"""
Stats API endpoints for Archon (Refactored - Lean Controller)

Delegates all business logic and aggregations to StatsService.
"""

from datetime import UTC, datetime, timedelta
from typing import cast

from fastapi import APIRouter, Depends, HTTPException

from ..auth.dependencies import get_current_user
from ..config.logfire_config import get_logger
from ..services.health_service import HealthService
from ..services.stats_service import StatsService
from ..utils import get_supabase_client

logger = get_logger(__name__)

router = APIRouter(prefix="/api/stats", tags=["stats"])
stats_service = StatsService()

async def require_admin(user=Depends(get_current_user)):
    if user.get("role") not in ["admin", "system_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

async def require_manager_or_admin(user=Depends(get_current_user)):
    role = (user.get("role") or "").lower()
    if role not in ["manager", "admin", "system_admin"]:
        raise HTTPException(status_code=403, detail="Manager or Admin access required")
    return user

def calculate_ai_score(content: str) -> int:
    """Delegates to StatsService."""
    return StatsService.calculate_ai_score(content)

@router.get("/commander-trends", dependencies=[Depends(require_manager_or_admin)])
async def get_commander_trends():
    """Strategic 30-day trend data for Charlie."""
    try:
        return await stats_service.get_commander_trends()
    except Exception as e:
        logger.error(f"Commander trends failed: {e}")
        return []

@router.get("/collab-synergy", dependencies=[Depends(require_manager_or_admin)])
async def get_collab_synergy():
    """Synergy Momentum Matrix (9x9)."""
    try:
        return await stats_service.get_collab_synergy()
    except Exception as e:
        logger.error(f"API: Collab synergy fetch failed: {e}")
        return {"nodes": [], "matrix": [], "error": str(e)}

@router.post("/approve-prompt-change/{version_id}", dependencies=[Depends(require_manager_or_admin)])
async def approve_prompt_change(version_id: str):
    """Charlie approves a pending prompt change."""
    try:
        supabase = get_supabase_client()
        res = supabase.table("archon_document_versions").update({"status": "approved"}).eq("id", version_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Version not found")
        return {"success": True, "message": "Prompt change approved"}
    except Exception as e:
        logger.error(f"API: Prompt approval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/knowledge-roi", dependencies=[Depends(require_manager_or_admin)])
async def get_knowledge_roi():
    """Knowledge Graph ROI: 60-Day Conversion Efficiency."""
    try:
        return await stats_service.get_knowledge_roi()
    except Exception as e:
        logger.error(f"API: Knowledge ROI failed: {e}")
        return {"overall_conversion": 0, "trend": [], "top_domains": [], "error": str(e)}

@router.get("/ethics-audit-queue", dependencies=[Depends(require_manager_or_admin)])
async def get_ethics_audit_queue():
    """Ethics & Prompt Audit Queue."""
    try:
        supabase = get_supabase_client()
        ethics_res = supabase.table("archon_ethics_events").select("*").eq("resolved", False).order("created_at", desc=True).limit(5).execute()
        versions_res = supabase.table("archon_document_versions").select("*").eq("status", "pending").order("created_at", desc=True).limit(5).execute()
        return {
            "violations": ethics_res.data or [],
            "pending_versions": versions_res.data or [],
            "total_pending": len(ethics_res.data or []) + len(versions_res.data or [])
        }
    except Exception as e:
        logger.error(f"API: Ethics audit queue failed: {e}")
        return {"violations": [], "pending_versions": [], "total_pending": 0}

@router.get("/sla-reliability", dependencies=[Depends(require_manager_or_admin)])
async def get_sla_reliability():
    """Strategic Reliability HUD: 6-Month (180D) SLA Attainment."""
    try:
        return await stats_service.get_sla_reliability()
    except Exception as e:
        logger.error(f"API: SLA Reliability failed: {e}")
        return {"current_sla": 0, "trend": [], "error": str(e)}

@router.get("/tasks-by-status")
async def get_tasks_by_status():
    """Get the count of tasks grouped by status."""
    try:
        supabase = get_supabase_client()
        response = supabase.table("archon_tasks").select("status").execute()
        counts: dict[str, int] = {}
        for row in response.data:
            s = row.get("status", "unknown")
            counts[s] = counts.get(s, 0) + 1
        return [{"name": k, "value": v} for k, v in counts.items()]
    except Exception as e:
        logger.error(f"Failed to get task stats: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/member-performance")
async def get_member_performance():
    """Get the count of COMPLETED tasks grouped by assignee."""
    try:
        supabase = get_supabase_client()
        response = supabase.table("archon_tasks").select("assignee").eq("status", "done").execute()
        counts: dict[str, int] = {}
        for row in response.data:
            a = row.get("assignee", "Unassigned")
            counts[a] = counts.get(a, 0) + 1
        result = [{"name": k, "completed_tasks": v} for k, v in counts.items()]
        result.sort(key=lambda x: cast(int, x["completed_tasks"]), reverse=True)
        return result[:10]
    except Exception as e:
        logger.error(f"Failed to get performance stats: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/system-overview", dependencies=[Depends(require_manager_or_admin)])
async def get_system_overview():
    """Consolidated health and performance overview."""
    try:
        supabase = get_supabase_client()
        health_service = HealthService()
        rag_health = await health_service.check_rag_integrity()
        one_day_ago = (datetime.now(UTC) - timedelta(hours=24)).isoformat()

        # Simple Error Count (Execute and ignore result if unused)
        supabase.table("archon_logs").select("id", count="exact").eq("level", "ERROR").gt("created_at", one_day_ago).execute()

        # Token Burn
        cost_res = supabase.table("token_usage").select("cost_usd").gt("created_at", one_day_ago).execute()
        total_cost_24h = sum(float(r.get("cost_usd", 0)) for r in (cost_res.data or []))

        return {
            "status": "healthy" if rag_health.get("status") == "healthy" else "degraded",
            "cost_24h": round(total_cost_24h, 4),
            "timestamp": datetime.now(UTC).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed system overview: {e}")
        return {"status": "unknown", "error": str(e)}
