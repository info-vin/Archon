"""
Stats API endpoints for Archon

Handles:
- Task distribution statistics (Tasks by Status)
- Team performance metrics (Member Performance)
"""

from datetime import UTC, datetime, timedelta
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException

from ..auth.dependencies import get_current_user
from ..config.logfire_config import get_logger
from ..services.health_service import HealthService
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

def calculate_ai_score(content: str) -> int:
    """
    Refined Business Integrity Scoring (Deduction Based).
    - Base: 100
    - Confidential Leak: -50 (Capped at 0)
    - Word count < 50: -50
    - Word count < 200: -20
    - Missing Header (#): -10
    """
    score = 100
    if "CONFIDENTIAL" in content.upper():
        score -= 50

    words = content.split()
    word_count = len(words)
    if word_count < 50:
        score -= 50
    elif word_count < 200:
        score -= 20

    if "# " not in content:
        score -= 10

    return max(0, score)

@router.get("/commander-trends", dependencies=[Depends(require_manager_or_admin)])
async def get_commander_trends():
    """
    Strategic 30-day trend data for Charlie.
    Returns: { date, bob_tokens, decision_hours }
    """
    try:
        supabase = get_supabase_client()
        thirty_days_ago = (datetime.now(UTC) - timedelta(days=30)).isoformat()

        # 1. Bob's Token Burn (Marketing Role)
        token_res = supabase.table("token_usage")\
            .select("created_at, total_tokens")\
            .in_("user_id", supabase.table("profiles").select("id").eq("role", "marketing"))\
            .gt("created_at", thirty_days_ago).execute()

        token_map: dict[str, int] = {}
        for row in (token_res.data or []):
            d = row["created_at"][:10]
            token_map[d] = token_map.get(d, 0) + int(row["total_tokens"])

        # 2. Charlie's Decision Velocity (Max 24h)
        # Time from created_at to first resolution (published/rejected)
        velocity_res = supabase.table("blog_posts")\
            .select("created_at, updated_at")\
            .in_("status", ["published", "changes_requested", "rejected"])\
            .gt("updated_at", thirty_days_ago).execute()

        velocity_data: dict[str, list[float]] = {}
        for row in (velocity_res.data or []):
            d = row["updated_at"][:10]
            start = datetime.fromisoformat(row["created_at"].replace('Z', '+00:00'))
            end = datetime.fromisoformat(row["updated_at"].replace('Z', '+00:00'))
            # Calculate hours and cap at 24.0
            hours = min(24.0, (end - start).total_seconds() / 3600)
            if d not in velocity_data:
                velocity_data[d] = []
            velocity_data[d].append(hours)

        # 3. Merge Trends
        all_dates = sorted(set(list(token_map.keys()) + list(velocity_data.keys())))
        trends = []
        for date in all_dates:
            trends.append({
                "date": date[5:], # MM-DD for UI
                "bob_tokens": token_map.get(date, 0),
                "decision_hours": round(sum(velocity_data[date])/len(velocity_data[date]), 1) if date in velocity_data else 0.0
            })

        return trends

    except Exception as e:
        logger.error(f"Commander trends failed: {e}")
        return []

@router.get("/system-overview", dependencies=[Depends(require_manager_or_admin)])
async def get_system_overview():
    """
    Consolidated health and performance overview.
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

        # Define all system entities
        all_agents_def = [
            {"id": "clockwork", "name": "Clockwork", "role": "Scheduler"},
            {"id": "sentinel", "name": "Sentinel", "role": "Guard"}
        ]
        for aid, cfg in AGENT_CONFIG.items():
            all_agents_def.append({
                "id": str(aid),
                "name": str(cfg["name"]),
                "role": "AI Assistant"
            })

        # REAL LOG CHECK
        logs_res = supabase.table("archon_logs").select("source")\
            .gt("created_at", one_hour_ago).execute()
        active_sources = {log["source"].lower() for log in (logs_res.data or [])}

        active_agents_details = []
        for agent in all_agents_def:
            is_active = (agent["id"].lower() in active_sources or
                         any(agent["name"].lower() in src for src in active_sources))
            active_agents_details.append({
                "id": agent["id"],
                "name": agent["name"],
                "role": agent["role"],
                "status": "active" if is_active else "standby"
            })

        # 4. 30-Day Decision Velocity Trend (GAP-028 Analytics)
        thirty_days_ago = (datetime.now(UTC) - timedelta(days=30)).isoformat()
        # Logic: Avg time from creation to resolution per day
        # We use blog_posts as the benchmark for content velocity
        velocity_res = supabase.table("blog_posts")\
            .select("created_at, updated_at")\
            .in_("status", ["published", "changes_requested"])\
            .gt("updated_at", thirty_days_ago).execute()

        velocity_trend = []
        daily_velocity: dict[str, list[float]] = {}
        for post in (velocity_res.data or []):
            d = post["updated_at"][:10]
            start = datetime.fromisoformat(post["created_at"].replace('Z', '+00:00'))
            end = datetime.fromisoformat(post["updated_at"].replace('Z', '+00:00'))
            hours = min(24.0, (end - start).total_seconds() / 3600) # Capped at 24h as per requirement
            if d not in daily_velocity:
                daily_velocity[d] = []
            daily_velocity[d].append(hours)

        for d in sorted(daily_velocity.keys()):
            velocity_trend.append({"date": d[5:], "avg_hours": round(sum(daily_velocity[d])/len(daily_velocity[d]), 1)})

        # 5. Token Burn (Last 24h Real Cost)
        cost_res = supabase.table("token_usage").select("cost_usd").gt("created_at", one_day_ago).execute()
        total_cost_24h = sum(float(r.get("cost_usd", 0)) for r in (cost_res.data or []))

        return {
            "status": "healthy" if rag_health.get("status") == "healthy" and error_count < 10 else "degraded",
            "active_agents": active_agents_details,
            "cost_24h": round(total_cost_24h, 4),
            "velocity_trend": velocity_trend, # Used for ASCII/Recharts visualization
            "ethics_violations_24h": (supabase.table("archon_ethics_events").select("id", count="exact").gt("created_at", one_day_ago).execute()).count or 0,
            "timestamp": datetime.now(UTC).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get system overview: {e}")
        return {
            "status": "unknown",
            "error": str(e)
        }


@router.get("/health-trend", dependencies=[Depends(require_manager_or_admin)])
async def get_health_trend():
    """
    Fetch 30-day health trend for Integrity Chart.
    Calculates Daily Avg and Monthly Baseline from archon_logs.
    """
    try:
        supabase = get_supabase_client()
        thirty_days_ago = (datetime.now(UTC) - timedelta(days=30)).isoformat()

        # Fetch probe logs for the last 30 days
        res = supabase.table("archon_logs")\
            .select("created_at, details")\
            .eq("source", "clockwork-scheduler")\
            .like("message", "%System Probe%")\
            .gt("created_at", thirty_days_ago)\
            .order("created_at", desc=False)\
            .execute()

        logs = res.data or []

        # Aggregate by date
        daily_data: dict[str, list[float]] = {}
        for log in logs:
            date_str = log["created_at"][:10] # YYYY-MM-DD
            # Extract score from details -> score (handle potential string or missing)
            details = log.get("details") or {}
            score = float(details.get("score", 95.0)) # Fallback only if data corrupted
            if date_str not in daily_data:
                daily_data[date_str] = []
            daily_data[date_str].append(score)

        # Format for Recharts
        trend = []
        all_scores = []
        for date in sorted(daily_data.keys()):
            day_avg = sum(daily_data[date]) / len(daily_data[date])
            all_scores.append(day_avg)
            # Monthly average is the mean of all collected scores up to this point
            monthly_avg = sum(all_scores) / len(all_scores)

            trend.append({
                "date": date[5:], # MM-DD for tablet display
                "daily": round(day_avg, 1),
                "baseline": round(monthly_avg, 1)
            })

        # Real Audit Trail (Last 5 events)
        audit_res = supabase.table("archon_logs")\
            .select("created_at, message, level")\
            .eq("source", "clockwork-scheduler")\
            .order("created_at", desc=True)\
            .limit(5)\
            .execute()

        return {
            "trend": trend,
            "audit": audit_res.data or []
        }
    except Exception as e:
        logger.error(f"Health trend calculation failed: {e}")
        return {"trend": [], "audit": [], "error": str(e)}

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
    Consolidated AI usage and collaboration metrics for Manager Nexus.
    SSOT for Costs, Tokens, and Human-Bot Synergy across ALL roles.
    """
    try:
        logger.info("Fetching Master AI Usage Metrics (SSOT - All Roles)")
        supabase = get_supabase_client()

        # 1. Fetch 30-day raw usage
        thirty_days_ago = (datetime.now(UTC) - timedelta(days=30)).isoformat()
        res = supabase.table("token_usage")\
            .select("created_at, cost_usd, total_tokens, user_id, context_type, model")\
            .gt("created_at", thirty_days_ago)\
            .order("created_at", desc=False)\
            .execute()

        usage_data = res.data or []

        # 2. Get All User Profiles (Ensure Alice, Bob, Charlie, Admin are mapped)
        user_ids = list({str(row["user_id"]) for row in usage_data if row.get("user_id")})
        profiles_map = {}
        if user_ids:
            prof_res = supabase.table("profiles").select("id, name, role").in_("id", user_ids).execute()
            profiles_map = {str(p["id"]): p for p in (prof_res.data or [])}

        # 3. Aggregate Metrics
        user_metrics: dict[str, dict[str, Any]] = {}
        daily_burn_map = {}
        cumulative_total_cost = 0.0
        cumulative_total_tokens = 0

        for row in usage_data:
            u_id = str(row.get("user_id")) if row.get("user_id") else "system"
            profile = profiles_map.get(u_id)
            user_name = profile["name"] if profile else ("System (Autonomous)" if u_id == "system" else "Ghost User")

            ts = datetime.fromisoformat(row["created_at"].replace('Z', '+00:00'))
            date_str = ts.strftime("%Y-%m-%d")
            cost = float(row.get("cost_usd", 0))
            tokens = int(row.get("total_tokens", 0))

            # Map context_type to professional Bot Roles for Charlie
            raw_task = row.get("context_type") or "general"
            task_category = "Crawler/Research" if any(k in raw_task.lower() for k in ["search", "crawl", "enrich", "probe"]) else "LLM/Generation"

            if user_name not in user_metrics:
                user_metrics[user_name] = {
                    "name": user_name,
                    "role": (profile["role"] if profile else "system").upper(),
                    "total_cost": 0.0,
                    "total_tokens": 0,
                    "tasks": {},
                    "active_days": {}
                }

            m = user_metrics[user_name]
            m["total_cost"] += cost
            m["total_tokens"] += tokens
            cumulative_total_tokens += tokens

            if task_category not in m["tasks"]:
                m["tasks"][task_category] = {"count": 0, "cost": 0.0, "tokens": 0}
            m["tasks"][task_category]["count"] += 1
            m["tasks"][task_category]["cost"] += cost
            m["tasks"][task_category]["tokens"] += tokens

            if date_str not in m["active_days"]:
                m["active_days"][date_str] = [ts, ts]
            else:
                m["active_days"][date_str][0] = min(m["active_days"][date_str][0], ts)
                m["active_days"][date_str][1] = max(m["active_days"][date_str][1], ts)

            cumulative_total_cost += cost
            daily_burn_map[date_str] = round(cumulative_total_cost, 4)

        # 4. Post-Process
        final_team = []
        for name, data in user_metrics.items():
            durations = [(v[1] - v[0]).total_seconds() / 3600 for v in data["active_days"].values()]
            avg_window = sum(durations) / len(durations) if durations else 0

            final_team.append({
                "name": name,
                "role": data["role"],
                "total_cost": round(data["total_cost"], 4),
                "total_tokens": data["total_tokens"],
                "avg_window": round(avg_window, 1),
                "task_distribution": sorted([{"type": k, **v} for k, v in data["tasks"].items()], key=lambda x: x["cost"], reverse=True)
            })

        s_res = supabase.table("archon_settings").select("value").eq("key", "monthly_budget_limit").execute()
        budget = 100.0
        if s_res.data:
            try:
                budget = float(s_res.data[0]["value"])
            except (ValueError, TypeError):
                pass

        return {
            "team": sorted(final_team, key=lambda x: x["total_cost"], reverse=True),
            "burn_trend": [{"date": d[5:], "cost": c} for d, c in sorted(daily_burn_map.items())],
            "budget_limit": budget,
            "total_monthly_usd": round(cumulative_total_cost, 4),
            "total_monthly_tokens": cumulative_total_tokens
        }

    except Exception as e:
        logger.error(f"Nexus AI Usage sync failed: {e}")
        return {"team": [], "burn_trend": [], "budget_limit": 100, "error": str(e)}
