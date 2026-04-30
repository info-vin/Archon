
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from ...utils import get_supabase_client

logger = logging.getLogger(__name__)

class MetricsManager:
    """
    Handles technical metrics, trends, and ROI calculations for Archon.
    Physical Realization of Phase 4.6.24 modularization standard.
    """

    def __init__(self, supabase_client=None):
        self.supabase = supabase_client or get_supabase_client()

    async def get_commander_trends(self) -> list[dict[str, Any]]:
        """Strategic 30-day trend data including full Velocity (GAP-034)."""
        thirty_days_ago = (datetime.now(UTC) - timedelta(days=30)).isoformat()

        # 1. Token Analytics (Bob/Alice Usage)
        marketing_res = self.supabase.table("profiles").select("id").eq("role", "marketing").execute()
        m_ids = [r["id"] for r in (marketing_res.data or [])]
        token_map: dict[str, int] = {}
        if m_ids:
            token_res = (
                self.supabase.table("token_usage")
                .select("created_at, total_tokens")
                .in_("user_id", m_ids)
                .gt("created_at", thirty_days_ago)
                .execute()
            )
            for row in token_res.data or []:
                d = str(row["created_at"][:10])
                token_map[d] = token_map.get(d, 0) + int(row["total_tokens"])

        # 2. Velocity Aggregation (GAP-034)
        velocity_raw: dict[str, list[float]] = {}

        def add_velocity(date_str: str, duration_hours: float):
            d = date_str[:10]
            if d not in velocity_raw:
                velocity_raw[d] = []
            velocity_raw[d].append(max(0.1, min(168.0, duration_hours)))

        # A. Blog Velocity
        blog_res = (
            self.supabase.table("blog_posts")
            .select("created_at, updated_at")
            .in_("status", ["published", "changes_requested"])
            .gt("updated_at", thirty_days_ago)
            .execute()
        )
        for row in blog_res.data or []:
            start = datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(row["updated_at"].replace("Z", "+00:00"))
            add_velocity(row["updated_at"], (end - start).total_seconds() / 3600)

        # B. Task Velocity (SLA Tracking)
        task_res = (
            self.supabase.table("archon_tasks")
            .select("created_at, completed_at")
            .eq("status", "done")
            .gt("completed_at", thirty_days_ago)
            .execute()
        )
        for row in task_res.data or []:
            start = datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(row["completed_at"].replace("Z", "+00:00"))
            add_velocity(row["completed_at"], (end - start).total_seconds() / 3600)

        # C. Lead Conversion Velocity
        lead_res = (
            self.supabase.table("leads")
            .select("created_at, updated_at")
            .eq("status", "converted")
            .gt("updated_at", thirty_days_ago)
            .execute()
        )
        for row in lead_res.data or []:
            start = datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(row["updated_at"].replace("Z", "+00:00"))
            add_velocity(row["updated_at"], (end - start).total_seconds() / 3600)

        all_dates = sorted(set(list(token_map.keys()) + list(velocity_raw.keys())))
        return [
            {
                "date": date[5:],
                "bob_tokens": token_map.get(date, 0),
                "decision_hours": round(sum(velocity_raw[date]) / len(velocity_raw[date]), 1)
                if date in velocity_raw else 0.0,
            }
            for date in all_dates
        ]

    async def get_force_readiness(self) -> dict[str, Any]:
        """Combat Power HUD: 90-Day Full Range."""
        try:
            now = datetime.now(UTC)
            ninety_days_ago = (now - timedelta(days=90)).isoformat()
            res = (
                self.supabase.table("archon_tasks")
                .select("id, completed_at, assignee")
                .eq("status", "done")
                .gt("completed_at", ninety_days_ago)
                .execute()
            )
            all_done_tasks = [t for t in (res.data or []) if t.get("assignee") and t.get("assignee") != "Unassigned"]
            total_done = len(all_done_tasks)
            baseline_daily = round(total_done / 90, 2)

            daily_actual: dict[str, int] = {}
            for task in all_done_tasks:
                if task.get("completed_at"):
                    d = task["completed_at"][:10]
                    daily_actual[d] = daily_actual.get(d, 0) + 1

            trend_data = []
            for i in range(90, -1, -1):
                date_str = (now - timedelta(days=i)).strftime("%Y-%m-%d")
                trend_data.append({
                    "date": date_str[5:],
                    "actual": daily_actual.get(date_str, 0),
                    "baseline": baseline_daily
                })

            ai_names = ["DevBot", "MarketBot", "Librarian", "POBot", "Clockwork"]
            ai_done = 0
            for t in all_done_tasks:
                assignee_str = str(t.get("assignee", ""))
                for bot in ai_names:
                    if bot in assignee_str:
                        ai_done += 1
                        break

            automation_rate = round((ai_done / total_done) * 100, 1) if total_done > 0 else 0.0

            return {
                "baseline": baseline_daily,
                "trend": trend_data,
                "total_done_90d": total_done,
                "automation_rate": automation_rate,
                "timestamp": now.isoformat(),
            }
        except Exception as e:
            logger.error(f"MetricsManager: Force readiness failed: {e}")
            return {"baseline": 0, "trend": []}

    async def get_knowledge_roi(self) -> dict[str, Any]:
        """Knowledge Graph ROI calculation (Phase 4.6.15)."""
        now = datetime.now(UTC)
        cutoff = (now - timedelta(days=60)).isoformat()
        try:
            sources_res = self.supabase.table("archon_sources").select("source_id, source_url, created_at").gt("created_at", cutoff).execute()
            pages_res = self.supabase.table("archon_crawled_pages").select("source_id, created_at").gt("created_at", cutoff).execute()

            sources = sources_res.data or []
            pages = pages_res.data or []

            from urllib.parse import urlparse
            def get_domain(url: str) -> str:
                try:
                    return urlparse(url).netloc or "Local Docs"
                except Exception:
                    return "Unknown"

            parsed_sources = []
            for s in sources:
                if raw := s.get("created_at"):
                    try:
                        parsed_sources.append((s, datetime.fromisoformat(str(raw).replace("Z", "+00:00"))))
                    except Exception:
                        pass

            parsed_pages = []
            for p in pages:
                if raw := p.get("created_at"):
                    try:
                        parsed_pages.append((p, datetime.fromisoformat(str(raw).replace("Z", "+00:00"))))
                    except Exception:
                        pass

            trend_data = []
            for i in range(60, 0, -14):
                w_start, w_end = now - timedelta(days=i), now - timedelta(days=i - 14)
                w_sources = [s for s, dt in parsed_sources if w_start <= dt < w_end]
                w_pages = [p for p, dt in parsed_pages if w_start <= dt < w_end]
                trend_data.append({
                    "date": w_start.strftime("%m-%d"),
                    "conversion": round((len(w_pages) / len(w_sources)) * 100, 1) if w_sources else 0.0,
                    "scanned": len(w_sources),
                    "saved": len(w_pages),
                })

            return {
                "overall_conversion": round((len(pages) / len(sources)) * 100, 1) if sources else 0.0,
                "trend": trend_data,
                "timestamp": now.isoformat(),
            }
        except Exception as e:
            logger.error(f"MetricsManager: Knowledge ROI failed: {e}")
            return {"overall_conversion": 0.0, "trend": []}

    async def get_sla_reliability(self) -> dict[str, Any]:
        """6-Month SLA Attainment logic."""
        now = datetime.now(UTC)
        cutoff = (now - timedelta(days=180)).isoformat()
        try:
            res = self.supabase.table("archon_tasks").select("id, completed_at, due_date").eq("status", "done").gt("completed_at", cutoff).execute()
            all_tasks = res.data or []
            parsed_tasks = []
            for t in all_tasks:
                if raw_comp := t.get("completed_at"):
                    try:
                        comp_dt = datetime.fromisoformat(str(raw_comp).replace("Z", "+00:00"))
                        parsed_tasks.append((t, comp_dt))
                    except Exception:
                        pass

            trend = []
            for i in range(180, 0, -14):
                w_start, w_end = now - timedelta(days=i), now - timedelta(days=i - 14)
                window_tasks = [(t, comp_dt) for t, comp_dt in parsed_tasks if w_start <= comp_dt < w_end]
                if not window_tasks:
                    trend.append({"date": w_start.strftime("%m-%d"), "rate": 100.0, "count": 0})
                    continue
                met = 0
                for t, comp_dt in window_tasks:
                    if not t.get("due_date"):
                        met += 1
                    else:
                        try:
                            d_dt = datetime.fromisoformat(str(t["due_date"]).replace("Z", "+00:00"))
                            if comp_dt <= d_dt:
                                met += 1
                        except Exception:
                            pass
                trend.append({"date": w_start.strftime("%m-%d"), "rate": round((met / len(window_tasks)) * 100, 1), "count": len(window_tasks)})
            return {"current_sla": trend[-1]["rate"] if trend else 100.0, "trend": trend, "total_analyzed": len(all_tasks)}
        except Exception as e:
            logger.error(f"MetricsManager: SLA failed: {e}")
            return {"current_sla": 0.0, "trend": []}

    async def get_detailed_ai_usage(self, days: int = 30) -> dict[str, Any]:
        """Provides AI usage stats with daily breakdown and real data flag."""
        from ..token_usage_service import TokenUsageService
        daily_costs = await TokenUsageService.get_daily_cost(days=days)
        # PERFORMANCE: Replaced sum(x for ...) generators with a single standard for-loop pass
        total_monthly_usd = 0.0
        total_monthly_tokens = 0
        for d in daily_costs:
            total_monthly_usd += d["cost"]
            total_monthly_tokens += d.get("request_count", 0) * 1000
        return {
            "total_monthly_usd": round(total_monthly_usd, 4),
            "total_monthly_tokens": int(total_monthly_tokens),
            "total_cost_usd": round(total_monthly_usd, 4),
            "total_used": int(total_monthly_tokens),
            "usage_percentage": min(100, round((total_monthly_tokens / 100000) * 100, 1)),
            "daily_costs": daily_costs,
            "burn_trend": [{"date": d["date"], "cost": d["cost"]} for d in daily_costs],
            "is_real_data": True,
            "budget_limit": 100.0,
            "team": []
        }

    async def get_recent_token_usage(self, limit: int = 20) -> list[dict[str, Any]]:
        """Retrieves recent individual token usage transactions."""
        try:
            # Physical Fix: Remove JOIN query (PGRST200) as FK relationship may not exist
            res = self.supabase.table("token_usage").select("*").order("created_at", desc=True).limit(limit).execute()
            formatted = []
            for row in (res.data or []):
                # Fallback for entities without profile mapping (e.g. Agents)
                formatted.append({
                    "id": row["id"],
                    "timestamp": row["created_at"],
                    "user_name": row.get("entity_name", "Archon Agent"), # Use entity_name if recorded
                    "role": row.get("entity_role", "ai_agent"),
                    "model": row["model"],
                    "tokens": row.get("total_tokens", 0),
                    "cost": float(row.get("estimated_cost_usd", 0.0) or 0.0),
                    "context": row.get("context_type", "General")
                })
            return formatted
        except Exception as e:
            logger.error(f"MetricsManager: Recent token usage fetch failed: {e}")
            return []

    async def get_marketing_intelligence(self) -> dict[str, Any]:
        """Marketing 2.0: Deep Lead Analysis & ROI (Phase 4.6.42)."""
        try:
            res = self.supabase.table("leads").select("*").execute()
            leads = res.data or []

            # 1. Conversion Funnel (Physical Data)
            funnel = {
                "new": 0, "contacted": 0, "shortlisted": 0, "converted": 0, "archived": 0
            }
            for lead in leads:
                s = lead.get("status", "new")
                if s in funnel:
                    funnel[s] += 1

            # 2. Industry/Job Distribution (Keyword Proxy)
            categories = {
                "AI/ML": ["AI", "Machine Learning", "ML", "Deep Learning"],
                "Data/Analytics": ["Data", "Analyst", "Statistics"],
                "Engineering": ["Engineer", "Developer", "Backend", "Frontend", "Python"],
                "Marketing/Sales": ["Marketing", "Sales", "Business", "Brand"],
                "Management": ["Manager", "Director", "VP", "Lead"]
            }

            distribution: dict[str, int] = dict.fromkeys(categories, 0)
            distribution["Other"] = 0

            # PERFORMANCE: Precalculate uppercase keywords outside the loop to avoid redundant allocations
            categories_upper = {cat: [k.upper() for k in keywords] for cat, keywords in categories.items()}

            for lead in leads:
                title = str(lead.get("job_title") or "").upper()
                found = False
                for cat, keywords_upper in categories_upper.items():
                    if any(k in title for k in keywords_upper):
                        distribution[cat] += 1
                        found = True
                        break
                if not found:
                    distribution["Other"] += 1

            # 3. ROI & Velocity
            # Calculate average conversion velocity (GAP-034)
            velocity_sum = 0.0
            converted_count = 0
            for lead in leads:
                if lead.get("status") == "converted" and lead.get("updated_at") and lead.get("created_at"):
                    start = datetime.fromisoformat(lead["created_at"].replace("Z", "+00:00"))
                    end = datetime.fromisoformat(lead["updated_at"].replace("Z", "+00:00"))
                    velocity_sum += (end - start).total_seconds() / 3600
                    converted_count += 1

            avg_velocity = round(velocity_sum / converted_count, 1) if converted_count > 0 else 0.0

            return {
                "total_leads": len(leads),
                "funnel": funnel,
                "distribution": distribution,
                "metrics": {
                    "avg_conversion_hours": avg_velocity,
                    "high_value_percentage": round((distribution["AI/ML"] + distribution["Management"]) / len(leads) * 100, 1) if leads else 0.0
                },
                "timestamp": datetime.now(UTC).isoformat()
            }
        except Exception as e:
            logger.error(f"MetricsManager: Marketing intelligence failed: {e}")
            return {"error": str(e)}

    def _window_check(self, item: dict[str, Any], start: datetime, end: datetime) -> bool:
        try:
            raw_val = item.get("created_at") or item.get("completed_at")
            if isinstance(raw_val, str):
                dt = datetime.fromisoformat(raw_val.replace('Z', '+00:00'))
                return start <= dt < end
            return False
        except Exception:
            return False
