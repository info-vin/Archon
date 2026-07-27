import logging
from datetime import UTC, datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


class AgentMetrics:
    """Handles agent execution trends and readiness."""

    def __init__(self, supabase_client: Any = None) -> None:
        self.supabase: Any = supabase_client

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
                if date in velocity_raw
                else 0.0,
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
                trend_data.append(
                    {"date": date_str[5:], "actual": daily_actual.get(date_str, 0), "baseline": baseline_daily}
                )

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
            logger.error(f"AgentMetrics: Force readiness failed: {e}")
            return {"baseline": 0, "trend": []}
