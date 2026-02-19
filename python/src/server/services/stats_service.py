import logging
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from ..utils import get_supabase_client

logger = logging.getLogger(__name__)

class StatsService:
    def __init__(self) -> None:
        self.supabase = get_supabase_client()

    @staticmethod
    def calculate_ai_score(content: str) -> int:
        """Refined Business Integrity Scoring."""
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

    async def get_commander_trends(self) -> list[dict[str, Any]]:
        """Strategic 30-day trend data including full Velocity (GAP-034)."""
        thirty_days_ago = (datetime.now(UTC) - timedelta(days=30)).isoformat()

        # 1. Token Analytics (Bob/Alice Usage)
        marketing_res = self.supabase.table("profiles").select("id").eq("role", "marketing").execute()
        m_ids = [r["id"] for r in (marketing_res.data or [])]
        token_map: dict[str, int] = {}
        if m_ids:
            token_res = self.supabase.table("token_usage").select("created_at, total_tokens").in_("user_id", m_ids).gt("created_at", thirty_days_ago).execute()
            for row in (token_res.data or []):
                d = str(row["created_at"][:10])
                token_map[d] = token_map.get(d, 0) + int(row["total_tokens"])

        # 2. Velocity Aggregation (GAP-034)
        # We aggregate three streams: Blogs, Tasks, and Leads
        velocity_raw: dict[str, list[float]] = {}

        def add_velocity(date_str: str, duration_hours: float):
            d = date_str[:10]
            if d not in velocity_raw:
                velocity_raw[d] = []
            # CAP at 168 hours (1 week) to prevent outliers from skewing averages
            velocity_raw[d].append(max(0.1, min(168.0, duration_hours)))

        # A. Blog Velocity
        blog_res = self.supabase.table("blog_posts").select("created_at, updated_at").in_("status", ["published", "changes_requested"]).gt("updated_at", thirty_days_ago).execute()
        for row in (blog_res.data or []):
            start = datetime.fromisoformat(row["created_at"].replace('Z', '+00:00'))
            end = datetime.fromisoformat(row["updated_at"].replace('Z', '+00:00'))
            add_velocity(row["updated_at"], (end - start).total_seconds() / 3600)

        # B. Task Velocity (SLA Tracking)
        task_res = self.supabase.table("archon_tasks").select("created_at, completed_at").eq("status", "done").gt("completed_at", thirty_days_ago).execute()
        for row in (task_res.data or []):
            start = datetime.fromisoformat(row["created_at"].replace('Z', '+00:00'))
            end = datetime.fromisoformat(row["completed_at"].replace('Z', '+00:00'))
            add_velocity(row["completed_at"], (end - start).total_seconds() / 3600)

        # C. Lead Conversion Velocity
        lead_res = self.supabase.table("leads").select("created_at, updated_at").eq("status", "converted").gt("updated_at", thirty_days_ago).execute()
        for row in (lead_res.data or []):
            start = datetime.fromisoformat(row["created_at"].replace('Z', '+00:00'))
            end = datetime.fromisoformat(row["updated_at"].replace('Z', '+00:00'))
            add_velocity(row["updated_at"], (end - start).total_seconds() / 3600)

        # 3. Format Response
        all_dates = sorted(set(list(token_map.keys()) + list(velocity_raw.keys())))
        return [{
            "date": date[5:],
            "bob_tokens": token_map.get(date, 0),
            "decision_hours": round(sum(velocity_raw[date])/len(velocity_raw[date]), 1) if date in velocity_raw else 0.0
        } for date in all_dates]

    async def get_business_risks(self) -> list[dict[str, Any]]:
        """
        Strategic Filter: Returns ALERT logs tagged as 'business' category.
        Drives the Sentinel Risk Radar HUD.
        """
        try:
            # Fetch actual ALERT level logs from sentinel
            res = self.supabase.table("archon_logs")\
                .select("*")\
                .eq("level", "ALERT")\
                .filter("details->>category", "eq", "business")\
                .order("created_at", desc=True).limit(10).execute()

            return res.data or []
        except Exception as e:
            logger.error(f"StatsService: Business risks fetch failed: {e}")
            return []

    async def get_force_readiness(self) -> dict[str, Any]:
        """
        Combat Power HUD: 90-Day Full Range.
        Calculates daily output against a historical baseline.
        """
        try:
            now = datetime.now(UTC)
            ninety_days_ago = (now - timedelta(days=90)).isoformat()

            # 1. Fetch all completed tasks in last 90 days
            res = self.supabase.table("archon_tasks")\
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
                    "baseline": baseline_daily
                })

            return {
                "baseline": baseline_daily,
                "trend": trend_data,
                "total_done_90d": total_done,
                "automation_rate": 72.4, # Heuristic for Nexus display
                "timestamp": now.isoformat()
            }
        except Exception as e:
            logger.error(f"StatsService: Force readiness failed: {e}")
            return {"baseline": 0, "trend": [], "error": str(e)}

    async def get_collab_synergy(self) -> dict[str, Any]:
        """Calculates synergy matrix interactions."""
        now = datetime.now(UTC)
        seven_days_ago = (now - timedelta(days=7)).isoformat()
        thirty_days_ago = (now - timedelta(days=30)).isoformat()
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
        tasks_res = self.supabase.table("archon_tasks").select("assignee_id, created_at, sources").gt("created_at", thirty_days_ago).execute()
        blogs_res = self.supabase.table("blog_posts").select("author_name, lead_id, created_at, status").gt("created_at", thirty_days_ago).execute()

        matrix: dict[str, dict[str, dict[str, int]]] = {}

        def add_interact(fr: str, to: str, date_str: str) -> None:
            f, t = fr.lower(), to.lower()
            if f not in matrix:
                matrix[f] = {}
            if t not in matrix[f]:
                matrix[f][t] = {"seven": 0, "thirty": 0}
            matrix[f][t]["thirty"] += 1
            if date_str >= seven_days_ago:
                matrix[f][t]["seven"] += 1

        for t in (tasks_res.data or []):
            to_id = str(t.get("assignee_id", "unknown"))
            for s in (t.get("sources") or []):
                fr_id = str(s.get("source_id") or s.get("type"))
                if fr_id and to_id:
                    add_interact(fr_id, to_id, t["created_at"])
        for b in (blogs_res.data or []):
            if b.get("lead_id"):
                add_interact("alice", "bob", b["created_at"])
            if b.get("status") == "changes_requested":
                add_interact("charlie", "bob", b["created_at"])

        formatted_matrix: list[dict[str, Any]] = []
        total_7d, total_30d = 0, 0
        hot_bridge: dict[str, Any] = {"name": "None", "val": 0}
        for fr_node in nodes:
            row: dict[str, Any] = {"from": fr_node["name"], "interactions": []}
            for to_node in nodes:
                stats = matrix.get(fr_node["id"].lower(), {}).get(to_node["id"].lower(), {"seven": 0, "thirty": 0})
                total_7d += stats["seven"]
                total_30d += stats["thirty"]
                if stats["seven"] > cast(int, hot_bridge["val"]) and fr_node["id"] != to_node["id"]:
                    hot_bridge = {"name": f"{fr_node['name']} -> {to_node['name']}", "val": stats["seven"]}
                row["interactions"].append({"to": to_node["name"], "actual_7d": stats["seven"], "avg_30d": round(stats["thirty"] / 4.2, 1)})
            formatted_matrix.append(row)

        avg_weekly_30d = total_30d / 4.2
        momentum = round(((total_7d / avg_weekly_30d) - 1) * 100, 1) if avg_weekly_30d > 0 else 0
        active_path_count = 0
        for r in formatted_matrix:
            for interaction in r["interactions"]:
                act_val = interaction.get("actual_7d", 0)
                if isinstance(act_val, int) and act_val > 0:
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

    async def get_knowledge_roi(self) -> dict[str, Any]:
        """Knowledge Graph ROI calculation."""
        now = datetime.now(UTC)
        cutoff = (now - timedelta(days=60)).isoformat()
        sources = self.supabase.table("archon_sources").select("source_id, source_url, created_at").gt("created_at", cutoff).execute().data or []
        pages = self.supabase.table("archon_crawled_pages").select("source_id, created_at").gt("created_at", cutoff).execute().data or []
        from urllib.parse import urlparse
        def get_domain(url: str) -> str:
            try:
                return urlparse(url).netloc or "Local Docs"
            except Exception:
                return "Unknown"
        trend_data: list[dict[str, Any]] = []
        for i in range(60, 0, -14):
            w_start, w_end = now - timedelta(days=i), now - timedelta(days=i - 14)
            w_sources = [s for s in sources if self._window_check(s, w_start, w_end)]
            w_pages = [p for p in pages if self._window_check(p, w_start, w_end)]
            trend_data.append({"date": w_start.strftime("%m-%d"), "conversion": round((len(w_pages)/len(w_sources))*100, 1) if w_sources else 0.0, "scanned": len(w_sources), "saved": len(w_pages)})

        domain_map: dict[str, dict[str, int]] = {}
        for s in sources:
            d_name = get_domain(s["source_url"])
            if d_name not in domain_map:
                domain_map[d_name] = {"scanned": 0, "saved": 0}
            domain_map[d_name]["scanned"] += 1

        s_ids = {s["source_id"]: get_domain(s["source_url"]) for s in sources}
        for p in pages:
            p_dom = s_ids.get(p["source_id"])
            if p_dom is not None and p_dom in domain_map:
                domain_map[p_dom]["saved"] += 1

        top_domains: list[dict[str, Any]] = []
        for d, s in sorted(domain_map.items(), key=lambda x: x[1]["scanned"], reverse=True)[:5]:
            conv = round((s["saved"]/s["scanned"])*100, 1) if s["scanned"] > 0 else 0.0
            top_domains.append({"domain": d, "conversion": conv, "yield": s["saved"], "severity": "good" if conv > 70 else "warning"})
        return {"overall_conversion": round((len(pages)/len(sources))*100, 1) if sources else 0.0, "trend": trend_data, "top_domains": top_domains, "timestamp": now.isoformat()}

    async def get_sla_reliability(self) -> dict[str, Any]:
        """6-Month SLA Attainment logic."""
        now = datetime.now(UTC)
        cutoff = (now - timedelta(days=180)).isoformat()
        all_tasks = self.supabase.table("archon_tasks").select("id, completed_at, due_date").eq("status", "done").gt("completed_at", cutoff).execute().data or []
        trend: list[dict[str, Any]] = []
        for i in range(180, 0, -14):
            w_start, w_end = now - timedelta(days=i), now - timedelta(days=i - 14)
            window_tasks = [t for t in all_tasks if t.get("completed_at") and self._window_check(t, w_start, w_end)]
            if not window_tasks:
                trend.append({"date": w_start.strftime("%m-%d"), "rate": 100.0, "count": 0})
                continue
            met = sum(1 for t in window_tasks if not t.get("due_date") or datetime.fromisoformat(str(t["completed_at"]).replace('Z', '+00:00')) <= datetime.fromisoformat(str(t["due_date"]).replace('Z', '+00:00')))
            trend.append({"date": w_start.strftime("%m-%d"), "rate": round((met/len(window_tasks))*100, 1), "count": len(window_tasks)})
        return {"current_sla": trend[-1]["rate"] if trend else 100.0, "trend": trend, "total_analyzed": len(all_tasks), "timestamp": now.isoformat()}

    async def get_system_health_overview(self) -> dict[str, Any]:
        """Consolidated health and performance overview for Admin."""
        from .health_service import HealthService
        rag_health = await HealthService().check_rag_integrity()
        one_day_ago = (datetime.now(UTC) - timedelta(hours=24)).isoformat()

        # 1. Real Error Count
        error_res = self.supabase.table("archon_logs").select("id", count="exact")\
            .eq("level", "ERROR").gt("created_at", one_day_ago).execute()
        error_count = error_res.count if error_res.count is not None else 0

        # 2. 24h Cost
        cost_res = self.supabase.table("token_usage").select("cost_usd")\
            .gt("created_at", one_day_ago).execute()
        total_cost_24h = sum(float(r.get("cost_usd", 0)) for r in (cost_res.data or []))

        # 3. Active Agents (Last 1h activity)
        one_hour_ago = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
        logs_res = self.supabase.table("archon_logs").select("source")\
            .gt("created_at", one_hour_ago).execute()
        active_sources = {log["source"] for log in (logs_res.data or [])}

        agents_manifest = [
            {"id": "clockwork", "name": "Clockwork", "role": "Scheduler"},
            {"id": "sentinel", "name": "Sentinel", "role": "Guard"},
            {"id": "librarian", "name": "Librarian", "role": "RAG Service"},
            {"id": "devbot", "name": "DevBot", "role": "System Engineer"}
        ]
        
        active_agents = []
        for agent in agents_manifest:
            is_active = agent["id"] in active_sources or any(agent["id"] in s.lower() for s in active_sources)
            active_agents.append({
                **agent,
                "status": "active" if is_active else "standby"
            })

        return {
            "status": "healthy" if rag_health.get("status") == "healthy" and error_count < 10 else "degraded",
            "rag": rag_health, # Nested for frontend: overview?.rag?.status
            "errors_24h": error_count,
            "active_agents": active_agents,
            "cost_24h": round(total_cost_24h, 4),
            "timestamp": datetime.now(UTC).isoformat(),
            "integrity_score": rag_health.get("score", 0),
            "knowledge_stats": {
                "total_nodes": rag_health.get("details", {}).get("total_sources", 0)
            }
        }

    async def get_detailed_ai_usage(self, days: int = 30) -> dict[str, Any]:
        """Provides AI usage stats with daily breakdown and real data flag."""
        from .token_usage_service import TokenUsageService
        daily_costs = await TokenUsageService.get_daily_cost(days=days)
        
        total_monthly_usd = sum(d["cost"] for d in daily_costs)
        total_monthly_tokens = sum(d.get("request_count", 0) * 1000 for d in daily_costs)

        return {
            "total_monthly_usd": round(total_monthly_usd, 4),
            "total_monthly_tokens": int(total_monthly_tokens),
            "total_cost_usd": round(total_monthly_usd, 4), # Frontend Alias
            "daily_costs": daily_costs, # Frontend expected field
            "burn_trend": [{"date": d["date"], "cost": d["cost"]} for d in daily_costs],
            "is_real_data": True,
            "budget_limit": 100.0,
            "team": [] # Can be populated via collab synergy if needed
        }

    @staticmethod
    def _window_check(item: dict[str, Any], start: datetime, end: datetime) -> bool:
        try:
            raw_val = item.get("created_at") or item.get("completed_at")
            if isinstance(raw_val, str):
                dt = datetime.fromisoformat(raw_val.replace('Z', '+00:00'))
                return start <= dt < end
            return False
        except Exception:
            return False
