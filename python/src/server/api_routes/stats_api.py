"""
Stats API endpoints for Archon

Handles:
- Task distribution statistics (Tasks by Status)
- Team performance metrics (Member Performance)
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status

from ..auth.dependencies import get_current_user
from ..config.logfire_config import get_logger
from ..services.health_service import HealthService
from ..services.token_usage_service import TokenUsageService
from ..utils import get_supabase_client

logger = get_logger(__name__)

router = APIRouter(prefix="/api/stats", tags=["stats"])

async def require_admin(user=Depends(get_current_user)):
    # Simple role check helper
    if user.get("role") not in ["admin", "system_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

async def require_manager_or_admin(user=Depends(get_current_user)):
    role = (user.get("role") or "").lower()
    if role not in ["manager", "admin", "system_admin"]:
        raise HTTPException(status_code=403, detail="Manager or Admin access required")
    return user

@router.get("/system-overview", dependencies=[Depends(require_admin)])
async def get_system_overview():
    """
    Consolidated health and performance overview for the Admin Dashboard.
    Integrates RAG Health, Error Log Counts, and Real Token Costs.
    """
    try:
        supabase = get_supabase_client()
        health_service = HealthService()

        # 1. RAG Health (Using existing check)
        rag_health = await health_service.check_rag_integrity()

        # 2. Error Log Stats (Last 24h)
        one_day_ago = (datetime.now(UTC) - timedelta(hours=24)).isoformat()
        # Note: 'count' param in select requires exact=True/Planned etc.
        # But supabase-py select(count='exact') returns count in .count property
        error_res = supabase.table("archon_logs").select("id", count="exact")\
            .eq("level", "ERROR").gt("created_at", one_day_ago).execute()
        error_count = error_res.count if error_res.count is not None else 0

        # 3. Active Agents Status
        # Check Scheduler Logs for recent activity
        one_hour_ago = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
        clockwork_res = supabase.table("archon_logs").select("id", count="exact")\
            .eq("source", "clockwork-scheduler").gt("created_at", one_hour_ago).execute()
        clockwork_active = (clockwork_res.count or 0) > 0

        active_agents = []
        if clockwork_active:
            active_agents.append("Clockwork (Scheduler)")
        # Assume others are services
        active_agents.extend(["Sentinel (Guard)", "Librarian (RAG)"])

        # 4. Token Cost (Last 24h)
        # We can reuse get_daily_cost logic but simpler here
        token_res = supabase.table("token_usage").select("cost_usd")\
            .gt("created_at", one_day_ago).execute()
        total_cost_24h = sum(float(row["cost_usd"]) for row in (token_res.data or []))

        return {
            "status": "healthy" if rag_health.get("status") == "healthy" and error_count < 10 else "degraded",
            "rag": rag_health,
            "errors_24h": error_count,
            "active_agents": active_agents,
            "cost_24h": round(total_cost_24h, 4),
            "timestamp": datetime.now(UTC).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get system overview: {e}")
        # Fail gracefully
        return {
            "status": "unknown",
            "error": str(e)
        }



@router.get("/tasks-by-status")
async def get_tasks_by_status():
    """
    Get the count of tasks grouped by status.
    Returns: List of { name: status, value: count }
    """
    try:
        logger.info("Fetching task distribution stats")
        supabase = get_supabase_client()

        # Optimization: Create a DB function for this in the future if data grows large.
        # Current approach: Fetch only 'status' field.
        response = supabase.table("archon_tasks").select("status").execute()

        # Aggregate in Python
        status_counts: dict[str, int] = {}
        for row in response.data:
            s = row.get("status", "unknown")
            status_counts[s] = status_counts.get(s, 0) + 1

        # Format for Recharts
        result = [
            {"name": status, "value": count}
            for status, count in status_counts.items()
        ]

        logger.info(f"Task stats retrieved | statuses={list(status_counts.keys())}")
        return result

    except Exception as e:
        logger.error(f"Failed to get task stats | error={str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": str(e)}
        ) from e


@router.get("/member-performance")
async def get_member_performance():
    """
    Get the count of COMPLETED tasks grouped by assignee.
    Returns: List of { name: assignee, completed_tasks: count }
    """
    try:
        logger.info("Fetching member performance stats")
        supabase = get_supabase_client()

        # Fetch 'assignee' for all tasks where status is 'done'
        response = supabase.table("archon_tasks") \
            .select("assignee") \
            .eq("status", "done") \
            .execute()

        # Aggregate in Python
        member_counts: dict[str, int] = {}
        for row in response.data:
            assignee = row.get("assignee", "Unassigned")
            member_counts[assignee] = member_counts.get(assignee, 0) + 1

        # Format and Sort (Top performers first)
        result: list[dict[str, Any]] = [
            {"name": assignee, "completed_tasks": count}
            for assignee, count in member_counts.items()
        ]
        result.sort(key=lambda x: x["completed_tasks"], reverse=True)

        # Limit to top 10
        result = result[:10]

        logger.info(f"Performance stats retrieved | members_count={len(result)}")
        return result

    except Exception as e:
        logger.error(f"Failed to get performance stats | error={str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": str(e)}
        ) from e

@router.get("/ai-usage", dependencies=[Depends(require_manager_or_admin)])
async def get_ai_usage():
    """
    Get AI token usage statistics.
    Hybrid approach:
    1. Returns legacy 'gemini_logs' estimated stats for Charlie (Team Management).
    2. Returns real 'token_usage' cost stats and details.
    """
    try:
        logger.info("Fetching AI usage stats with details")
        supabase = get_supabase_client()

        # --- Legacy Path (Estimated from logs) ---
        response = supabase.table("gemini_logs").select("user_name").execute()
        logs = response.data or []
        total_calls = len(logs)
        estimated_used = total_calls * 500

        user_counts: dict[str, int] = {}
        for log in logs:
            user = log.get("user_name") or "Unknown"
            user_counts[user] = user_counts.get(user, 0) + 1

        breakdown: list[dict[str, Any]] = [
            {"name": user, "calls": count, "tokens": count * 500}
            for user, count in user_counts.items()
        ]
        breakdown.sort(key=lambda x: x["tokens"], reverse=True)

        # --- New Path (Real Cost & Details) ---
        # Fetch daily stats for the last 30 days
        daily_costs = await TokenUsageService.get_daily_cost(days=30)
        total_real_cost = sum(d["cost"] for d in daily_costs)

        # Detailed usage (last 7 days)
        since = (datetime.now(UTC) - timedelta(days=7)).isoformat()
        usage_res = supabase.table("token_usage")\
            .select("*")\
            .gt("created_at", since)\
            .order("created_at", desc=True)\
            .limit(100).execute()

        usage_data = usage_res.data or []
        user_ids = list({row["user_id"] for row in usage_data if row.get("user_id")})

        profiles_map = {}
        if user_ids:
            prof_res = supabase.table("profiles").select("id, name, email")\
                .in_("id", user_ids).execute()
            profiles_map = {p["id"]: p for p in (prof_res.data or [])}

        details = []
        for row in usage_data:
            user_id = row.get("user_id")
            profile = profiles_map.get(str(user_id)) if user_id else None
            details.append({
                "id": row["id"],
                "timestamp": row["created_at"],
                "source_type": "Human" if profile else "Machine",
                "user_name": profile["name"] if profile else f"Agent ({row['model']})",
                "model": row["model"],
                "tokens": row["total_tokens"],
                "cost": float(row["cost_usd"])
            })

        return {
            "total_budget": 100000,
            "total_used": estimated_used,
            "usage_percentage": round((estimated_used / 100000) * 100, 1),
            "usage_by_user": breakdown,
            "total_cost_usd": round(total_real_cost, 4),
            "daily_costs": daily_costs,
            "details": details,
            "is_real_data": True
        }

    except Exception as e:
        logger.error(f"Failed to get AI usage stats | error={str(e)}")
        # Return fallback data
        return {
            "total_budget": 100000,
            "total_used": 0,
            "usage_percentage": 0,
            "usage_by_user": [],
            "total_cost_usd": 0.0,
            "daily_costs": [],
            "details": [],
            "error": str(e)
        }
