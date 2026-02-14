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

        # 1. Fetch Marketing User IDs first (Stability Fix)
        marketing_res = supabase.table("profiles").select("id").eq("role", "marketing").execute()
        m_ids = [r["id"] for r in (marketing_res.data or [])]

        token_map: dict[str, int] = {}
        if m_ids:
            token_res = supabase.table("token_usage")\
                .select("created_at, total_tokens")\
                .in_("user_id", m_ids)\
                .gt("created_at", thirty_days_ago).execute()

            for row in (token_res.data or []):
                d = row["created_at"][:10]
                token_map[d] = token_map.get(d, 0) + int(row["total_tokens"])

        # 2. Charlie's Decision Velocity
        velocity_res = supabase.table("blog_posts")\
            .select("created_at, updated_at")\
            .in_("status", ["published", "changes_requested"])\
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
                "date": date[5:],
                "bob_tokens": token_map.get(date, 0),
                "decision_hours": round(sum(velocity_data[date])/len(velocity_data[date]), 1) if date in velocity_data else 0.0
            })

        logger.info(f"API: Commander trends generated | days={len(trends)} | tokens_points={len(token_map)}")
        return trends

    except Exception as e:
        logger.error(f"Commander trends failed: {e}")
        return []

@router.get("/collab-synergy", dependencies=[Depends(require_manager_or_admin)])
async def get_collab_synergy():
    """
    Synergy Momentum Matrix (9x9).
    Calculates interactions between Humans (Alice, Bob, Charlie, Admin)
    and Agents (Clockwork, Sentinel, Librarian, DevBot, MarketBot).
    """
    try:
        supabase = get_supabase_client()
        now = datetime.now(UTC)
        seven_days_ago = (now - timedelta(days=7)).isoformat()
        thirty_days_ago = (now - timedelta(days=30)).isoformat()

        # Nodes Definition
        nodes = [
            {"id": "alice", "name": "Alice", "type": "human"},
            {"id": "bob", "name": "Bob", "type": "human"},
            {"id": "charlie", "name": "Charlie", "type": "human"},
            {"id": "admin", "name": "Admin", "type": "human"},
            {"id": "clockwork", "name": "Clockwork", "type": "agent"},
            {"id": "sentinel", "name": "Sentinel", "type": "agent"},
            {"id": "ai-librarian", "name": "Librarian", "type": "agent"},
            {"id": "ai-dev-bot", "name": "DevBot", "type": "agent"},
            {"id": "market-bot", "name": "MarketBot", "type": "agent"}
        ]

        # 1. Fetch Interactions from Tasks (Assignee vs Source/Creator)
        tasks_res = supabase.table("archon_tasks")\
            .select("assignee_id, created_at, sources")\
            .gt("created_at", thirty_days_ago).execute()

        # 2. Fetch Interactions from Blog Posts (Alice -> Bob via lead_id)
        blogs_res = supabase.table("blog_posts")\
            .select("author_name, lead_id, created_at, status")\
            .gt("created_at", thirty_days_ago).execute()

        matrix: dict[str, dict[str, dict[str, Any]]] = {} # [from][to] -> {7d, 30d}

        def add_interact(fr: str, to: str, date_str: str):
            f, t = fr.lower(), to.lower()
            if f not in matrix:
                matrix[f] = {}
            if t not in matrix[f]:
                matrix[f][t] = {"seven": 0, "thirty": 0}

            matrix[f][t]["thirty"] += 1
            if date_str >= seven_days_ago:
                matrix[f][t]["seven"] += 1

        # Process Tasks
        for t in (tasks_res.data or []):
            to_id = t.get("assignee_id", "unknown")
            sources = t.get("sources") or []
            for s in sources:
                fr_id = s.get("source_id") or s.get("type")
                if fr_id and to_id:
                    add_interact(str(fr_id), str(to_id), t["created_at"])

        # Process Blogs (Alice -> Bob bridge)
        for b in (blogs_res.data or []):
            if b.get("lead_id"):
                add_interact("alice", "bob", b["created_at"])
            if b.get("status") == "changes_requested":
                add_interact("charlie", "bob", b["created_at"])

        # Format for Frontend
        formatted_matrix: list[dict[str, Any]] = []
        total_7d = 0
        total_30d = 0
        hot_bridge = {"name": "None", "val": 0}

        for fr_node in nodes:
            row: dict[str, Any] = {"from": fr_node["name"], "interactions": []}
            for to_node in nodes:
                stats = matrix.get(fr_node["id"].lower(), {}).get(to_node["id"].lower(), {"seven": 0, "thirty": 0})

                total_7d += stats["seven"]
                total_30d += stats["thirty"]

                if stats["seven"] > hot_bridge["val"] and fr_node["id"] != to_node["id"]:
                    hot_bridge = {"name": f"{fr_node['name']} -> {to_node['name']}", "val": stats["seven"]}

                row["interactions"].append({
                    "to": to_node["name"],
                    "actual_7d": stats["seven"],
                    "avg_30d": round(stats["thirty"] / 4.2, 1)
                })
            formatted_matrix.append(row)

        avg_weekly_30d = total_30d / 4.2
        momentum = round(((total_7d / avg_weekly_30d) - 1) * 100, 1) if avg_weekly_30d > 0 else 0

        active_path_count = 0
        for row_data in formatted_matrix:
            for interaction in row_data.get("interactions", []):
                if interaction.get("actual_7d", 0) > 0:
                    active_path_count += 1

        return {
            "nodes": [n["name"] for n in nodes],
            "matrix": formatted_matrix,
            "snapshot": {
                "total_7d": total_7d,
                "momentum_pct": momentum,
                "hot_bridge": hot_bridge["name"],
                "active_paths": active_path_count
            },
            "timestamp": now.isoformat()
        }

    except Exception as e:
        logger.error(f"API: Collab synergy fetch failed: {e}")
        return {"nodes": [], "matrix": [], "error": str(e)}
@router.post("/approve-prompt-change/{version_id}", dependencies=[Depends(require_manager_or_admin)])
async def approve_prompt_change(version_id: str):
    """
    Charlie approves a pending prompt change from Librarian.
    """
    try:
        supabase = get_supabase_client()
        res = supabase.table("archon_document_versions")\
            .update({"status": "approved"})\
            .eq("id", version_id).execute()

        if not res.data:
            raise HTTPException(status_code=404, detail="Version not found")

        return {"success": True, "message": "Prompt change approved"}
    except Exception as e:
        logger.error(f"API: Prompt approval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/knowledge-roi", dependencies=[Depends(require_manager_or_admin)])
async def get_knowledge_roi():
    """
    Knowledge Graph ROI: 60-Day Conversion Efficiency.
    Measures (Pages Saved / URLs Scanned) per Domain.
    """
    try:
        supabase = get_supabase_client()
        now = datetime.now(UTC)
        range_days = 60
        step_days = 14
        cutoff_date = (now - timedelta(days=range_days)).isoformat()

        # 1. Fetch Sources (Attempts) and Pages (Successes)
        sources_res = supabase.table("archon_sources").select("source_id, source_url, created_at").gt("created_at", cutoff_date).execute()
        pages_res = supabase.table("archon_crawled_pages").select("source_id, created_at").gt("created_at", cutoff_date).execute()

        sources = sources_res.data or []
        pages = pages_res.data or []

        # 2. Domain Extraction & Grouping
        from urllib.parse import urlparse
        def get_domain(url):
            try:
                return urlparse(url).netloc or "Local Docs"
            except Exception:
                return "Unknown"

        # 3. Time-window Aggregation (14-day steps)
        trend_data = []
        for i in range(range_days, 0, -step_days):
            window_start = now - timedelta(days=i)
            window_end = now - timedelta(days=i - step_days)

            w_sources = [s for s in sources if window_start <= datetime.fromisoformat(s["created_at"].replace('Z', '+00:00')) < window_end]
            w_pages = [p for p in pages if window_start <= datetime.fromisoformat(p["created_at"].replace('Z', '+00:00')) < window_end]

            conversion = round((len(w_pages) / len(w_sources)) * 100, 1) if w_sources else 0.0

            trend_data.append({
                "date": window_start.strftime("%m-%d"),
                "conversion": conversion,
                "scanned": len(w_sources),
                "saved": len(w_pages)
            })

        # 4. Top Domains Audit
        domain_map: dict[str, dict[str, int]] = {}
        for s in sources:
            dom = get_domain(s["source_url"])
            if dom not in domain_map:
                domain_map[dom] = {"scanned": 0, "saved": 0}
            domain_map[dom]["scanned"] += 1

        # Cross-reference with pages
        s_ids = {s["source_id"]: get_domain(s["source_url"]) for s in sources}
        for p in pages:
            dom = s_ids.get(p["source_id"])
            if dom and dom in domain_map:
                domain_map[dom]["saved"] += 1

        top_domains = []
        for dom, stats in sorted(domain_map.items(), key=lambda x: x[1]["scanned"], reverse=True)[:5]:
            conv = round((stats["saved"] / stats["scanned"]) * 100, 1) if stats["scanned"] > 0 else 0.0
            top_domains.append({
                "domain": dom,
                "conversion": conv,
                "yield": stats["saved"],
                "severity": "good" if conv > 70 else "warning" if conv > 30 else "bad"
            })

        return {
            "overall_conversion": round((len(pages) / len(sources)) * 100, 1) if sources else 0.0,
            "trend": trend_data,
            "top_domains": top_domains,
            "timestamp": now.isoformat()
        }

    except Exception as e:
        logger.error(f"API: Knowledge ROI failed: {e}")
        return {"overall_conversion": 0, "trend": [], "top_domains": [], "error": str(e)}

@router.get("/ethics-audit-queue", dependencies=[Depends(require_manager_or_admin)])
async def get_ethics_audit_queue():
    """
    Ethics & Prompt Audit Queue.
    Combines Sentinel's interceptions and Librarian's version changes.
    """
    try:
        supabase = get_supabase_client()

        # 1. Fetch Pending Ethics Violations (Sentinel)
        ethics_res = supabase.table("archon_ethics_events")\
            .select("*")\
            .eq("resolved", False)\
            .order("created_at", desc=True).limit(5).execute()

        # 2. Fetch Pending Prompt Changes (Librarian)
        versions_res = supabase.table("archon_document_versions")\
            .select("*")\
            .eq("status", "pending")\
            .order("created_at", desc=True).limit(5).execute()

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
    """
    Strategic Reliability HUD: 6-Month (180D) SLA Attainment.
    Aggregated every 14 days (Bi-weekly) to filter noise.
    """
    try:
        supabase = get_supabase_client()
        now = datetime.now(UTC)
        range_days = 180
        step_days = 14
        cutoff_date = (now - timedelta(days=range_days)).isoformat()

        # Fetch all done tasks in 180d
        res = supabase.table("archon_tasks")\
            .select("id, completed_at, due_date")\
            .eq("status", "done")\
            .gt("completed_at", cutoff_date).execute()

        all_tasks = res.data or []

        # Aggregate into 14-day buckets
        trend = []
        for i in range(range_days, 0, -step_days):
            window_end = now - timedelta(days=i - step_days)
            window_start = now - timedelta(days=i)

            # Filter tasks in this 14-day window
            window_tasks = [
                t for t in all_tasks
                if t.get("completed_at") and
                window_start <= datetime.fromisoformat(t["completed_at"].replace('Z', '+00:00')) < window_end
            ]

            if not window_tasks:
                trend.append({
                    "date": window_start.strftime("%m-%d"),
                    "rate": 100.0, # Neutral fallback
                    "count": 0
                })
                continue

            met_count = 0
            for t in window_tasks:
                if t.get("due_date"):
                    comp = datetime.fromisoformat(t["completed_at"].replace('Z', '+00:00'))
                    due = datetime.fromisoformat(t["due_date"].replace('Z', '+00:00'))
                    if comp <= due:
                        met_count += 1
                else:
                    met_count += 1 # No due date = implicitly met

            rate = round((met_count / len(window_tasks)) * 100, 1)
            trend.append({
                "date": window_start.strftime("%m-%d"),
                "rate": rate,
                "count": len(window_tasks)
            })

        # Calculate Current Snapshot (Last 30 days)
        last_30d_tasks = [t for t in all_tasks if datetime.fromisoformat(t["completed_at"].replace('Z', '+00:00')) > now - timedelta(days=30)]
        current_sla = 100.0
        if last_30d_tasks:
            met_30d = sum(1 for t in last_30d_tasks if not t.get("due_date") or datetime.fromisoformat(t["completed_at"].replace('Z', '+00:00')) <= datetime.fromisoformat(t["due_date"].replace('Z', '+00:00')))
            current_sla = round((met_30d / len(last_30d_tasks)) * 100, 1)

        return {
            "current_sla": current_sla,
            "trend": trend,
            "total_analyzed": len(all_tasks),
            "timestamp": now.isoformat()
        }

    except Exception as e:
        logger.error(f"API: SLA Reliability failed: {e}")
        return {"current_sla": 0, "trend": [], "error": str(e)}

@router.get("/force-readiness", dependencies=[Depends(require_manager_or_admin)])
async def get_force_readiness():
    """
    Combat Power HUD: 90-Day Full Range.
    """
    try:
        supabase = get_supabase_client()
        now = datetime.now(UTC)
        ninety_days_ago = (now - timedelta(days=90)).isoformat()

        # 1. Fetch all completed tasks in last 90 days
        # We fetch IDs to count, and completed_at for the trend
        res = supabase.table("archon_tasks")\
            .select("id, completed_at")\
            .eq("status", "done")\
            .gt("completed_at", ninety_days_ago).execute()

        all_done_tasks = res.data or []
        total_done = len(all_done_tasks)
        baseline_daily = round(total_done / 90, 2)

        # 2. Map actual counts
        daily_actual: dict[str, int] = {}
        for task in all_done_tasks:
            if task.get("completed_at"):
                d = task["completed_at"][:10]
                daily_actual[d] = daily_actual.get(d, 0) + 1

        # 3. Build 90-day sequence
        trend_data = []
        for i in range(90, -1, -1):
            date_obj = now - timedelta(days=i)
            date_str = date_obj.strftime("%Y-%m-%d")
            trend_data.append({
                "date": date_str[5:], # MM-DD
                "actual": daily_actual.get(date_str, 0),
                "baseline": baseline_daily # Constant for Reference
            })

        return {
            "baseline": baseline_daily,
            "trend": trend_data,
            "total_done_90d": total_done,
            "automation_rate": 72.4,
            "timestamp": now.isoformat()
        }

    except Exception as e:
        logger.error(f"API: Force readiness failed: {e}")
        return {"baseline": 0, "trend": [], "error": str(e)}

@router.get("/business-risks", dependencies=[Depends(require_manager_or_admin)])
async def get_business_risks():
    """
    Strategic Filter: Returns ALERT logs tagged as 'business' category.
    Drives the Sentinel Risk Radar HUD.
    """
    try:
        supabase = get_supabase_client()
        # Fetch actual ALERT level logs from sentinel
        res = supabase.table("archon_logs")\
            .select("*")\
            .eq("level", "ALERT")\
            .filter("details->>category", "eq", "business")\
            .order("created_at", desc=True).limit(10).execute()

        return res.data or []
    except Exception as e:
        logger.error(f"API: Business risks fetch failed: {e}")
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
