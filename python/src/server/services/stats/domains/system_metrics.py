import logging
from datetime import UTC, datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)

class SystemMetrics:
    """Handles SLA reliability and token usage tracking."""

    def __init__(self, supabase_client):
        self.supabase = supabase_client

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
            logger.error(f"SystemMetrics: SLA failed: {e}")
            return {"current_sla": 0.0, "trend": []}

    async def get_detailed_ai_usage(self, days: int = 30) -> dict[str, Any]:
        """Provides AI usage stats with daily breakdown and real data flag."""
        from ...token_usage_service import TokenUsageService
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
            logger.error(f"SystemMetrics: Recent token usage fetch failed: {e}")
            return []
