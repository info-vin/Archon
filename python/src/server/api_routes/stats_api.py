"""
Stats API endpoints for Archon

Handles:
- Task distribution statistics (Tasks by Status)
- Team performance metrics (Member Performance)
"""

from datetime import UTC, datetime, timedelta
from typing import cast

from fastapi import APIRouter, Depends, HTTPException

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

@router.get("/system-overview", dependencies=[Depends(require_manager_or_admin)])
async def get_system_overview():
    """
    Consolidated health and performance overview.
    Now accessible to Managers and provides a complete view of registered agents.
    """
    try:
        supabase = get_supabase_client()
        health_service = HealthService()

        # 1. RAG Health
        rag_health = await health_service.check_rag_integrity()

        # 2. Error Log Stats (Last 24h)
        one_day_ago = (datetime.now(UTC) - timedelta(hours=24)).isoformat()
        error_res = supabase.table("archon_logs").select("id", count="exact")\
            .eq("level", "ERROR").gt("created_at", one_day_ago).execute()
        error_count = error_res.count if error_res.count is not None else 0

        # 3. Dynamic Agent Status (SSOT Fix - BUG-037)
        from ..services.agent_registry import AGENT_CONFIG
        one_hour_ago = (datetime.now(UTC) - timedelta(hours=1)).isoformat()

        # Define all expected system agents
        all_agents_def = [
            {"id": "clockwork", "name": "Clockwork", "role": "Scheduler"},
            {"id": "sentinel", "name": "Sentinel", "role": "Business Guard"}
        ]
        # Add registered AI agents
        for agent_id, config in AGENT_CONFIG.items():
            all_agents_def.append({
                "id": str(agent_id),
                "name": str(config["name"]),
                "role": "AI Assistant"
            })

        # Get recent activity from logs
        logs_res = supabase.table("archon_logs").select("source, message")\
            .gt("created_at", one_hour_ago).execute()
        active_sources = {log["source"].lower() for log in (logs_res.data or [])}

        # Get recent activity from tokens
        token_res = supabase.table("token_usage").select("context_type")\
            .gt("created_at", one_hour_ago).execute()
        active_contexts = {t["context_type"].lower() for t in (token_res.data or []) if t.get("context_type")}

        active_agents_details = []
        for agent in all_agents_def:
            # Heuristic for activity: Match source ID or context type
            is_active = (
                agent["id"].lower() in active_sources or
                "clockwork" in active_sources and agent["id"] == "clockwork" or
                any(agent["id"].lower() in ctx for ctx in active_contexts) or
                (agent["id"] == "market-bot" and any("blog" in ctx for ctx in active_contexts))
            )
            active_agents_details.append({
                "id": agent["id"],
                "name": agent["name"],
                "role": agent["role"],
                "status": "active" if is_active else "standby"
            })

        # 5. Knowledge Stats
        # Count total pages and chunks
        pages_res = supabase.table("archon_crawled_pages").select("id", count="exact").execute()
        # approximate chunks if not tracked directly, or query distinct source_id
        # For now, we assume archon_crawled_pages represents chunks/pages.
        knowledge_stats = {
            "total_nodes": pages_res.count or 0,
            "total_chunks": pages_res.count or 0 # 1:1 for now
        }

        # 6. Ethics Status (Last 24h)
        ethics_res = supabase.table("archon_ethics_events").select("id", count="exact")\
            .gt("created_at", one_day_ago).execute()
        ethics_count = ethics_res.count or 0

        # 7. Collab Score (Last 30 days)
        # Logic: Count tasks where updated_by != assignee (proxy for collaboration)
        thirty_days_ago = (datetime.now(UTC) - timedelta(days=30)).isoformat()
        # Note: 'updated_by' might not exist on all tasks, fallback to logs or simple active user count
        # Simplified: Count distinct active users in last 30d logs
        active_users_res = supabase.table("archon_logs").select("user_id")\
            .gt("created_at", thirty_days_ago).execute()
        distinct_users = len({log["user_id"] for log in (active_users_res.data or []) if log.get("user_id")})
        collab_score = min(100, distinct_users * 20) # 5 users = 100%

        # 8. Velocity Score (Last 14 days)
        # Logic: Avg completion time for tasks done in last 14d
        fourteen_days_ago = (datetime.now(UTC) - timedelta(days=14)).isoformat()
        done_tasks_res = supabase.table("archon_tasks").select("created_at, completed_at")\
            .eq("status", "done").gt("completed_at", fourteen_days_ago).execute()

        velocity_score = 0
        if done_tasks_res.data:
            total_hours = 0.0
            count = 0
            for task in done_tasks_res.data:
                if task.get("created_at") and task.get("completed_at"):
                    start = datetime.fromisoformat(task["created_at"])
                    end = datetime.fromisoformat(task["completed_at"])
                    diff = (end - start).total_seconds() / 3600
                    total_hours += diff
                    count += 1
            if count > 0:
                avg_hours = total_hours / count
                # Benchmarking: < 24h = 100, 48h = 50
                velocity_score = max(0, min(100, int(100 - (avg_hours - 24))))

        # 9. Cost 24h (Real-time)
        cost_res = supabase.table("token_usage").select("cost_usd").gt("created_at", one_day_ago).execute()
        total_cost_24h = sum(float(r.get("cost_usd", 0)) for r in (cost_res.data or []))
        return {
            "status": "healthy" if rag_health.get("status") == "healthy" and error_count < 10 else "degraded",
            "rag": rag_health,
            "integrity_score": rag_health.get("score", 99.8), # Fallback if health service not updated yet
            "errors_24h": error_count,
            "active_agents": active_agents_details,
            "cost_24h": round(total_cost_24h, 4),
            "knowledge_stats": knowledge_stats,
            "ethics_status": {"violations_24h": ethics_count},
            "collab_score": collab_score,
            "velocity_score": velocity_score,
            "velocity_in_days": round(avg_hours / 24, 1) if 'avg_hours' in locals() else 0.0,
            "timestamp": datetime.now(UTC).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get system overview: {e}")
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
        response = supabase.table("archon_tasks").select("status").execute()

        status_counts: dict[str, int] = {}
        for row in response.data:
            s = row.get("status", "unknown")
            status_counts[s] = status_counts.get(s, 0) + 1

        result = [
            {"name": status, "value": count}
            for status, count in status_counts.items()
        ]
        return result
    except Exception as e:
        logger.error(f"Failed to get task stats: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/member-performance")
async def get_member_performance():
    """
    Get the count of COMPLETED tasks grouped by assignee.
    """
    try:
        logger.info("Fetching member performance stats")
        supabase = get_supabase_client()
        response = supabase.table("archon_tasks") \
            .select("assignee") \
            .eq("status", "done") \
            .execute()

        member_counts: dict[str, int] = {}
        for row in response.data:
            assignee = row.get("assignee", "Unassigned")
            member_counts[assignee] = member_counts.get(assignee, 0) + 1

        result = [
            {"name": assignee, "completed_tasks": count}
            for assignee, count in member_counts.items()
        ]
        result.sort(key=lambda x: cast(int, x["completed_tasks"]), reverse=True)
        return result[:10]
    except Exception as e:
        logger.error(f"Failed to get performance stats: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/ai-usage", dependencies=[Depends(require_manager_or_admin)])
async def get_ai_usage():
    """
    Get AI token usage statistics.
    Source: 'token_usage' table (Real Data).
    """
    try:
        logger.info("Fetching AI usage stats (Real Data)")
        supabase = get_supabase_client()

        # 1. Fetch Daily Costs (Last 30 days)
        daily_costs_data = await TokenUsageService.get_daily_cost(days=30)
        total_real_cost = sum(d["cost"] for d in daily_costs_data)

        # 2. Fetch Detailed Usage (Last 7 days for list view)
        since = (datetime.now(UTC) - timedelta(days=7)).isoformat()
        usage_res = supabase.table("token_usage")\
            .select("*")\
            .gt("created_at", since)\
            .order("created_at", desc=True)\
            .limit(100).execute()

        usage_data = usage_res.data or []

        # 3. Resolve User Names
        user_ids = list({str(row["user_id"]) for row in usage_data if row.get("user_id")})
        profiles_map = {}
        if user_ids:
            prof_res = supabase.table("profiles").select("id, name, email").in_("id", user_ids).execute()
            profiles_map = {str(p["id"]): p for p in (prof_res.data or [])}

        details = []
        user_cost_map = {}

        for row in usage_data:
            user_id = str(row.get("user_id")) if row.get("user_id") else None
            profile = profiles_map.get(user_id) if user_id else None

            # Determine Source Type
            source_type = "Machine"
            user_name = f"Agent ({row.get('model', 'Unknown')})"

            if profile:
                source_type = "Human" # Alice, Bob
                user_name = profile.get("name", "Unknown User")
            elif not user_id:
                 # No user_id usually means System/Background
                 user_name = "System (Background)"

            cost = float(row.get("cost_usd", 0))

            details.append({
                "id": row["id"],
                "timestamp": row["created_at"],
                "source_type": source_type,
                "user_name": user_name,
                "model": row.get("model"),
                "tokens": row.get("total_tokens", 0),
                "cost": cost
            })

            # Aggregate for Breakdown Chart
            if user_name not in user_cost_map:
                user_cost_map[user_name] = {"calls": 0, "tokens": 0, "cost": 0.0}
            user_cost_map[user_name]["calls"] += 1
            user_cost_map[user_name]["tokens"] += row.get("total_tokens", 0)
            user_cost_map[user_name]["cost"] += cost

        # Format Breakdown
        breakdown = [
            {"name": k, "calls": v["calls"], "tokens": v["tokens"], "cost": round(v["cost"], 4)}
            for k, v in user_cost_map.items()
        ]
        breakdown.sort(key=lambda x: cast(float, x["cost"]), reverse=True)

        # 4. Fetch Budget Limit
        settings_res = supabase.table("archon_settings").select("value").eq("key", "monthly_budget_limit").execute()
        budget_limit = 100000.0
        if settings_res.data:
            try:
                budget_limit = float(settings_res.data[0]["value"])
            except (ValueError, TypeError):
                pass

        return {
            "total_budget": budget_limit,
            "total_used": 0, # Legacy field, deprecated
            "total_cost_usd": round(total_real_cost, 4),
            "usage_percentage": round((total_real_cost / budget_limit) * 100, 1) if budget_limit > 0 else 0,
            "usage_by_user": breakdown,
            "daily_costs": daily_costs_data,
            "details": details,
            "is_real_data": True
        }

    except Exception as e:
        logger.error(f"Failed to get AI usage stats: {e}")
        return {
            "error": str(e),
            "usage_by_user": [],
            "daily_costs": [],
            "details": []
        }
