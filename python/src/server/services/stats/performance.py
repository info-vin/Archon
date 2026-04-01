
import logging
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from ...utils import get_supabase_client

logger = logging.getLogger(__name__)

class PerformanceManager:
    """
    Handles AI Agent scoring, XP tracking, and collaboration synergy.
    1:1 Physical Parity with original StatsService implementation.
    """

    def __init__(self, supabase_client=None):
        self.supabase = supabase_client or get_supabase_client()

    @staticmethod
    def calculate_ai_score(content: str, metadata: dict | None = None) -> int:
        """Physical Business Integrity Scoring (Phase 4.6.15)."""
        score = 100
        words = content.split()
        word_count = len(words)
        if word_count < 50:
            score -= 50
        elif word_count < 200:
            score -= 20

        if metadata:
            if metadata.get("returncode") is not None and metadata.get("returncode") != 0:
                score -= 40
            if metadata.get("lint_passed") is False:
                score -= 15
            if metadata.get("required_terms"):
                for term in metadata["required_terms"]:
                    if term.upper() not in content.upper():
                        score -= 10

        if "CONFIDENTIAL" in content.upper():
            score -= 50
        return max(0, score)

    async def add_agent_action_log(self, agent_name: str, xp_change: int, message: str, details: dict | None = None, content: str | None = None, agent_id: str | None = None) -> None:
        """Logs an agent action and updates XP (Grounded Rewards)."""
        try:
            final_xp = xp_change
            if content:
                final_xp = self.calculate_ai_score(content, details)
                logger.info(f"XP Scoring: Calculated dynamic score {final_xp} for {agent_name}")

            payload = {
                "source": "agent_action",
                "level": "INFO" if final_xp >= 0 else "WARNING",
                "message": message,
                "details": {
                    **(details or {}),
                    "agent_name": agent_name,
                    "agent_id": agent_id,
                    "xp_change": final_xp,
                    "timestamp_v": "v4.6.23", # Updated for identity alignment
                },
            }
            self.supabase.table("archon_logs").insert(payload).execute()
        except Exception as e:
            logger.error(f"PerformanceManager: Action log failed: {e}")

    async def get_collab_synergy(self) -> dict[str, Any]:
        """Calculates synergy matrix interactions (Type-Hardened)."""
        now = datetime.now(UTC)
        seven_days_ago = (now - timedelta(days=7)).isoformat()
        thirty_days_ago = (now - timedelta(days=30)).isoformat()

        nodes = [
            {"id": "alice", "name": "Alice"},
            {"id": "bob", "name": "Bob"},
            {"id": "charlie", "name": "Charlie"},
            {"id": "admin", "name": "Admin"},
            {"id": "clockwork", "name": "Clockwork"},
            {"id": "sentinel", "name": "Sentinel"},
            {"id": "ai-librarian", "name": "Librarian"},
            {"id": "ai-dev-bot", "name": "DevBot"},
            {"id": "market-bot", "name": "MarketBot"},
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
            sources_list = cast(list[dict[str, Any]], t.get("sources") or [])
            for s in sources_list:
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
        hot_bridge_name = "None"
        hot_bridge_val = 0

        for fr_node in nodes:
            row: dict[str, Any] = {"from": fr_node["name"], "interactions": []}
            for to_node in nodes:
                stats = matrix.get(fr_node["id"].lower(), {}).get(to_node["id"].lower(), {"seven": 0, "thirty": 0})
                total_7d += stats["seven"]
                total_30d += stats["thirty"]
                if stats["seven"] > hot_bridge_val and fr_node["id"] != to_node["id"]:
                    hot_bridge_val = stats["seven"]
                    hot_bridge_name = f"{fr_node['name']} -> {to_node['name']}"

                actual_avg_30d = round(stats["thirty"] / 4.28, 1)
                row["interactions"].append({
                    "to": to_node["name"],
                    "actual_7d": stats["seven"],
                    "avg_30d": actual_avg_30d
                })
            formatted_matrix.append(row)

        avg_weekly_30d = total_30d / 4.28
        momentum = round(((total_7d / avg_weekly_30d) - 1) * 100, 1) if avg_weekly_30d > 0 else 0.0

        return {
            "nodes": [n["name"] for n in nodes],
            "matrix": formatted_matrix,
            "snapshot": {
                "total_7d": total_7d,
                "momentum_pct": momentum,
                "hot_bridge": hot_bridge_name,
                "active_paths": sum(1 for r in formatted_matrix for i in r["interactions"] if i["actual_7d"] > 0)
            },
            "timestamp": now.isoformat(),
        }

    async def get_agent_xp_stats(self) -> list[dict[str, Any]]:
        """Calculates XP and Total Cost for all agents (Phase 4.6.15 parity)."""
        try:
            xp_res = self.supabase.table("archon_logs").select("details").eq("source", "agent_action").execute()
            xp_map: dict[str, int] = {}
            for row in xp_res.data or []:
                details = row.get("details") or {}
                name = details.get("agent_name") or details.get("agent_id") or "Unknown Agent"
                xp_map[name] = xp_map.get(name, 0) + int(details.get("xp_change", 0))

            cost_res = self.supabase.table("token_usage").select("user_id, cost_usd").execute()
            from ..agent_registry import AGENT_CONFIG, get_agent_uuid

            agent_id_to_name: dict[str, str] = {}
            for config_key in AGENT_CONFIG:
                u_id = get_agent_uuid(config_key)
                if u_id:
                    agent_id_to_name[u_id] = str(AGENT_CONFIG[config_key].get("name", "Unknown"))

            cost_map: dict[str, float] = {}
            for row in cost_res.data or []:
                u_id = row.get("user_id")
                if isinstance(u_id, str) and u_id in agent_id_to_name:
                    target_name = agent_id_to_name[u_id]
                    cost_map[target_name] = cost_map.get(target_name, 0.0) + float(row.get("cost_usd", 0))

            result = []
            for key, config in AGENT_CONFIG.items():
                name = str(config.get("name", "Unknown"))
                slug = f"ai-{key}"
                total_xp = xp_map.get(name, 0) or xp_map.get(slug, 0)
                total_cost = cost_map.get(name, 0.0)
                roi = round(total_xp / total_cost, 2) if total_cost > 0 else 0.0
                result.append({
                    "name": name,
                    "agent_id": slug,
                    "total_xp": total_xp,
                    "total_cost": round(total_cost, 4),
                    "roi_ratio": roi,
                    "level": self._get_agent_level(total_xp)
                })
            result.sort(key=lambda x: cast(int, x["total_xp"]), reverse=True)
            return result
        except Exception as e:
            logger.error(f"PerformanceManager: XP Stats failed: {e}")
            return []

    async def get_member_performance(self) -> list[dict[str, Any]]:
        """Calculates performance for human members."""
        try:
            res = self.supabase.table("archon_tasks").select("assignee").eq("status", "done").execute()
            counts: dict[str, int] = {}
            for row in res.data or []:
                a = row.get("assignee", "Unassigned")
                counts[a] = counts.get(a, 0) + 1
            result = [{"name": k, "completed_tasks": v} for k, v in counts.items()]
            result.sort(key=lambda x: cast(int, x["completed_tasks"]), reverse=True)
            return result[:10]
        except Exception as e:
            logger.error(f"PerformanceManager: Member performance failed: {e}")
            return []

    async def get_business_risks(self) -> list[dict[str, Any]]:
        """Drives the Sentinel Risk Radar HUD."""
        try:
            res = self.supabase.table("archon_logs").select("*").eq("level", "ALERT").filter("details->>category", "eq", "business").order("created_at", desc=True).limit(10).execute()
            return res.data or []
        except Exception as e:
            logger.error(f"PerformanceManager: Risks failed: {e}")
            return []

    def _get_agent_level(self, xp: int) -> str:
        if xp >= 880:
            return "Level 6"
        if xp >= 870:
            return "Level 5"
        if xp >= 850:
            return "Level 4"
        if xp >= 800:
            return "Level 3"
        if xp >= 700:
            return "Level 2"
        if xp >= 500:
            return "Level 1"
        return "Intern"
