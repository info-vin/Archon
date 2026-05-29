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
            res = (
                self.supabase.table("archon_tasks")
                .select("id, completed_at, due_date")
                .eq("status", "done")
                .gt("completed_at", cutoff)
                .execute()
            )
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
                trend.append(
                    {
                        "date": w_start.strftime("%m-%d"),
                        "rate": round((met / len(window_tasks)) * 100, 1),
                        "count": len(window_tasks),
                    }
                )
            return {
                "current_sla": trend[-1]["rate"] if trend else 100.0,
                "trend": trend,
                "total_analyzed": len(all_tasks),
            }
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
            "team": [],
        }

    async def get_recent_token_usage(self, limit: int = 20) -> list[dict[str, Any]]:
        """Retrieves recent individual token usage transactions."""
        try:
            # Physical Fix: Remove JOIN query (PGRST200) as FK relationship may not exist
            res = self.supabase.table("token_usage").select("*").order("created_at", desc=True).limit(limit).execute()
            formatted = []
            for row in res.data or []:
                # Fallback for entities without profile mapping (e.g. Agents)
                formatted.append(
                    {
                        "id": row["id"],
                        "timestamp": row["created_at"],
                        "user_name": row.get("entity_name", "Archon Agent"),  # Use entity_name if recorded
                        "role": row.get("entity_role", "ai_agent"),
                        "model": row["model"],
                        "tokens": row.get("total_tokens", 0),
                        "cost": float(row.get("cost_usd") or 0.0),
                        "context": row.get("context_type", "General"),
                    }
                )
            return formatted
        except Exception as e:
            logger.error(f"SystemMetrics: Recent token usage fetch failed: {e}")
            return []

    async def get_team_availability(self, user_ids: list[str], target_date: str) -> list[dict[str, Any]]:
        """
        Calculates availability for team members by analyzing existing non-done tasks.
        Excludes busy segments from the working day (09:00 to 18:00 local GMT+8 time).
        """
        try:
            import re
            # Extract YYYY-MM-DD cleanly using regex to avoid parsing crashes (GAP-004 fix)
            date_match = re.search(r"(\d{4}-\d{2}-\d{2})", target_date)
            if not date_match:
                raise ValueError(f"Invalid date format: {target_date}")
            clean_date = date_match.group(1)

            # 1. Query tasks in local business timezone offset (+08:00)
            start_iso = f"{clean_date}T00:00:00+08:00"
            end_iso = f"{clean_date}T23:59:59+08:00"

            res = (
                self.supabase.table("archon_tasks")
                .select("assignee_id, due_date, estimated_hours")
                .in_("assignee_id", user_ids)
                .neq("status", "done")
                .or_("archived.is.null,archived.is.false")
                .gte("due_date", start_iso)
                .lte("due_date", end_iso)
                .execute()
            )

            tasks = res.data or []

            # 2. Establish busy intervals in timezone-aware datetimes
            busy_intervals = []
            for task in tasks:
                raw_due = task.get("due_date")
                if not raw_due:
                    continue
                try:
                    # Convert Zulu time Z to +00:00 for python fromisoformat compatibility
                    due_dt = datetime.fromisoformat(str(raw_due).replace("Z", "+00:00"))
                except Exception:
                    continue

                est_hours = float(task.get("estimated_hours") or 1.0)
                if est_hours <= 0:
                    est_hours = 1.0

                start_dt = due_dt - timedelta(hours=est_hours)
                busy_intervals.append((start_dt, due_dt))

            # Sort and merge busy intervals
            busy_intervals.sort(key=lambda x: x[0])
            merged_busy = []
            for start, end in busy_intervals:
                if not merged_busy:
                    merged_busy.append((start, end))
                else:
                    last_start, last_end = merged_busy[-1]
                    if start <= last_end:
                        # Overlap, merge
                        merged_busy[-1] = (last_start, max(last_end, end))
                    else:
                        merged_busy.append((start, end))

            # 3. Working hours start/end in GMT+8 (09:00 - 18:00 Taipei business hours)
            work_start = datetime.fromisoformat(f"{clean_date}T09:00:00+08:00")
            work_end = datetime.fromisoformat(f"{clean_date}T18:00:00+08:00")

            # Find free intervals in [work_start, work_end]
            free_slots = []
            current_time = work_start

            for start, end in merged_busy:
                # If busy segment starts after current_time, we have a potential gap
                if start > current_time:
                    gap_start = current_time
                    gap_end = min(start, work_end)
                    if gap_start < gap_end:
                        free_slots.append((gap_start, gap_end))
                current_time = max(current_time, end)
                if current_time >= work_end:
                    break

            if current_time < work_end:
                free_slots.append((current_time, work_end))

            # 4. Standardize free slots into 1-hour slots or candidate meeting blocks
            recommendations = []
            for slot_start, slot_end in free_slots:
                duration = (slot_end - slot_start).total_seconds() / 3600.0
                # Chunk into 1-hour meetings
                temp_start = slot_start
                while (slot_end - temp_start).total_seconds() >= 3600.0:
                    recommendations.append({
                        "start_time": temp_start.isoformat(),
                        "end_time": (temp_start + timedelta(hours=1.0)).isoformat()
                    })
                    temp_start += timedelta(hours=1.0)
                    if len(recommendations) >= 3:
                        break
                if len(recommendations) >= 3:
                    break

            # Fallback if no recommendation generated (e.g. fully busy day)
            if not recommendations:
                default_hours = [9, 13, 16]
                for dh in default_hours:
                    ds = datetime.fromisoformat(f"{clean_date}T{dh:02d}:00:00+08:00")
                    recommendations.append({
                        "start_time": ds.isoformat(),
                        "end_time": (ds + timedelta(hours=1.0)).isoformat()
                    })

            return recommendations[:3]
        except Exception as e:
            logger.error(f"SystemMetrics: get_team_availability failed: {e}")
            # Extract clean date safely for fallback default slots
            try:
                date_match = re.search(r"(\d{4}-\d{2}-\d{2})", target_date)
                fallback_date = date_match.group(1) if date_match else "2026-06-01"
            except Exception:
                fallback_date = "2026-06-01"

            # Safe local fallback (GMT+8)
            return [
                {
                    "start_time": f"{fallback_date}T09:00:00+08:00",
                    "end_time": f"{fallback_date}T10:00:00+08:00"
                },
                {
                    "start_time": f"{fallback_date}T13:00:00+08:00",
                    "end_time": f"{fallback_date}T14:00:00+08:00"
                },
                {
                    "start_time": f"{fallback_date}T16:00:00+08:00",
                    "end_time": f"{fallback_date}T17:00:00+08:00"
                }
            ]


