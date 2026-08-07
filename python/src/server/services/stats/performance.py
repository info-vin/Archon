import logging
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from ...repositories.base_repository import BaseRepository
from ...utils import get_supabase_client

logger = logging.getLogger(__name__)




class PerformanceManager(BaseRepository):
    """
    Handles AI Agent scoring, XP tracking, and collaboration synergy.
    1:1 Physical Parity with original StatsService implementation.
    """

    def __init__(self, supabase_client: Any = None) -> None:
        super().__init__(supabase_client or get_supabase_client())
        self.supabase = self.supabase_client

    @staticmethod
    def calculate_ai_score(content: str | None, metadata: dict | None = None) -> int:
        """Physical Business Integrity Scoring (Phase 4.6.15)."""
        if not content:
            return 0
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

    async def add_agent_action_log(
        self,
        agent_name: str,
        xp_change: int,
        message: str,
        details: dict | None = None,
        content: str | None = None,
        agent_id: str | None = None,
    ) -> None:
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
                    "timestamp_v": "v4.6.23",  # Updated for identity alignment
                },
            }
            self.execute_query(self.supabase.table("archon_logs").insert(payload), "Insert action log") # 合法
        except Exception as e:
            logger.error(f"PerformanceManager: Action log failed: {e}")

    async def get_collab_synergy(self) -> dict[str, Any]:
        """Calculates synergy matrix interactions with Dynamic Nodes (Phase 4.6.39)."""
        now = datetime.now(UTC)
        seven_days_ago = (now - timedelta(days=7)).isoformat()
        thirty_days_ago = (now - timedelta(days=30)).isoformat()

        # Dynamic Nodes Extraction
        success_p, profiles_res = self.execute_query(self.supabase.table("profiles").select("id, name, email"), "Get profiles") # 合法
        profile_map = {str(p["id"]): p["name"] for p in (profiles_res.get("data", []) if success_p else [])}
        email_to_name = {str(p["email"]).split("@")[0].lower(): p["name"] for p in (profiles_res.get("data", []) if success_p else [])}

        success_t, tasks_res = self.execute_query(
            self.supabase.table("archon_tasks") # 合法
            .select("assignee_id, created_at, sources")
            .gt("created_at", thirty_days_ago),
            "Get tasks synergy"
        )
        success_b, blogs_res = self.execute_query(
            self.supabase.table("blog_posts") # 合法
            .select("author_name, lead_id, created_at, status")
            .gt("created_at", thirty_days_ago),
            "Get blogs synergy"
        )
        success_l, logs_res = self.execute_query(
            self.supabase.table("archon_logs") # 合法
            .select("source")
            .eq("level", "ALERT")
            .gt("created_at", thirty_days_ago),
            "Get logs synergy"
        )

        active_participants = set()
        matrix: dict[str, dict[str, dict[str, int]]] = {}

        def add_interact(fr: str, to: str, date_str: str) -> None:
            f, t = fr.lower(), to.lower()
            active_participants.add(f)
            active_participants.add(t)
            if f not in matrix:
                matrix[f] = {}
            if t not in matrix[f]:
                matrix[f][t] = {"seven": 0, "thirty": 0}
            matrix[f][t]["thirty"] += 1
            if date_str >= seven_days_ago:
                matrix[f][t]["seven"] += 1

        for t in (tasks_res.get("data", []) if success_t else []):
            to_id = str(t.get("assignee_id", "unknown"))
            sources_list = cast(list[dict[str, Any]], t.get("sources") or [])
            for s in sources_list:
                fr_id = str(s.get("source_id") or s.get("type"))
                if fr_id and to_id:
                    add_interact(fr_id, to_id, t["created_at"])

        for b in (blogs_res.get("data", []) if success_b else []):
            author = str(b.get("author_name") or "bob").lower()
            if b.get("lead_id"):
                add_interact("alice", author, b["created_at"])
            if b.get("status") == "changes_requested":
                add_interact("charlie", author, b["created_at"])
            elif b.get("status") == "published":
                add_interact(author, "charlie", b["created_at"])

        for log_entry in (logs_res.get("data", []) if success_l else []):
            if log_entry.get("source") == "twin_scout":
                add_interact("twin_scout", "charlie", thirty_days_ago)  # Alert Charlie

        # Build dynamic nodes list from discovered participants
        # Sort to ensure UI stability
        sorted_participants = sorted(active_participants)
        nodes_list = []
        for p_id in sorted_participants:
            name = profile_map.get(p_id) or email_to_name.get(p_id) or p_id.capitalize()
            nodes_list.append({"id": p_id, "name": name})

        formatted_matrix: list[dict[str, Any]] = []
        total_7d, total_30d = 0, 0
        hot_bridge_name = "None"
        hot_bridge_val = 0

        for fr_node in nodes_list:
            row: dict[str, Any] = {"from": fr_node["name"], "interactions": []}
            for to_node in nodes_list:
                stats = matrix.get(fr_node["id"].lower(), {}).get(to_node["id"].lower(), {"seven": 0, "thirty": 0})
                total_7d += stats["seven"]
                total_30d += stats["thirty"]
                if stats["seven"] > hot_bridge_val and fr_node["id"] != to_node["id"]:
                    hot_bridge_val = stats["seven"]
                    hot_bridge_name = f"{fr_node['name']} -> {to_node['name']}"

                actual_avg_30d = round(stats["thirty"] / 4.28, 1)
                row["interactions"].append(
                    {"to": to_node["name"], "actual_7d": stats["seven"], "avg_30d": actual_avg_30d}
                )
            formatted_matrix.append(row)

        avg_weekly_30d = total_30d / 4.28
        momentum = round(((total_7d / avg_weekly_30d) - 1) * 100, 1) if avg_weekly_30d > 0 else 0.0

        # PERFORMANCE: Replaced nested list comprehension with a standard for loop to avoid memory allocation overhead
        active_paths_count = 0
        for r in formatted_matrix:
            for i in r["interactions"]:
                if i["actual_7d"] > 0:
                    active_paths_count += 1

        # Return dynamic synergy data
        return {
            "nodes": [n["name"] for n in nodes_list],
            "matrix": formatted_matrix,
            "snapshot": {
                "total_7d": total_7d,
                "momentum_pct": momentum,
                "hot_bridge": hot_bridge_name,
                "active_paths": active_paths_count,
            },
            "timestamp": now.isoformat(),
        }

    async def get_agent_xp_stats(self) -> list[dict[str, Any]]:
        """Calculates XP, Success Count, and Total Cost for all agents (Phase 5.5)."""
        try:
            success_xp, xp_res = self.execute_query(self.supabase.table("archon_logs").select("details").eq("source", "agent_action"), "Get XP logs") # 合法
            xp_map: dict[str, int] = {}
            success_map: dict[str, int] = {}

            for row in (xp_res.get("data", []) if success_xp else []):
                details = row.get("details") or {}
                name = details.get("agent_name") or details.get("agent_id") or "Unknown Agent"
                xp_change = int(details.get("xp_change", 0))

                # Accumulate Total XP
                xp_map[name] = xp_map.get(name, 0) + xp_change

                # Accumulate Success Count (Positive XP Change)
                if xp_change > 0:
                    success_map[name] = success_map.get(name, 0) + 1

            # Fetch overrides for Level 7 check
            success_o, overrides_res = self.execute_query(
                self.supabase.table("profiles") # 合法
                .select("id, name, role, permission_overrides")
                .eq("role", "ai_agent"),
                "Get agent overrides"
            )
            o_data = overrides_res.get("data", []) if success_o else []
            overrides_map = {r.get("id"): r.get("permission_overrides", {}) for r in o_data}
            name_to_overrides = {r.get("name"): r.get("permission_overrides", {}) for r in o_data}

            success_c, cost_res = self.execute_query(self.supabase.table("token_usage").select("user_id, cost_usd"), "Get token usage") # 合法
            from ..agent_registry import FALLBACK_AGENT_CONFIG, get_agent_config, get_agent_uuid

            agent_id_to_name: dict[str, str] = {}
            for config_key in FALLBACK_AGENT_CONFIG:
                u_id = get_agent_uuid(config_key)
                if u_id:
                    config = get_agent_config(config_key)
                    if config:
                        agent_id_to_name[u_id] = str(config.get("name", "Unknown"))

            cost_map: dict[str, float] = {}
            for row in (cost_res.get("data", []) if success_c else []):
                u_id = row.get("user_id")
                if isinstance(u_id, str) and u_id in agent_id_to_name:
                    target_name = agent_id_to_name[u_id]
                    cost_map[target_name] = cost_map.get(target_name, 0.0) + float(row.get("cost_usd", 0))

            result = []
            for key in FALLBACK_AGENT_CONFIG:
                config = get_agent_config(key)
                if not config:
                    continue
                name = str(config.get("name", "Unknown"))
                slug = f"ai-{key}"
                u_id = get_agent_uuid(key)

                total_xp = xp_map.get(name, 0) or xp_map.get(slug, 0)
                success_count = success_map.get(name, 0) or success_map.get(slug, 0)
                total_cost = cost_map.get(name, 0.0)
                roi = round(total_xp / total_cost, 2) if total_cost > 0 else 0.0

                # Get overrides for this specific agent
                agent_overrides = overrides_map.get(u_id) or name_to_overrides.get(name) or {}

                result.append(
                    {
                        "name": name,
                        "agent_id": slug,
                        "total_xp": total_xp,
                        "success_count": success_count,
                        "total_cost": round(total_cost, 4),
                        "roi_ratio": roi,
                        "level": self._get_agent_level(success_count, agent_overrides),
                    }
                )
            result.sort(key=lambda x: cast(int, x["success_count"]), reverse=True)
            return result
        except Exception as e:
            logger.error(f"PerformanceManager: XP Stats failed: {e}")
            return []

    async def get_member_performance(self) -> list[dict[str, Any]]:
        """Calculates performance for human members."""
        try:
            success, res = self.execute_query(self.supabase.table("archon_tasks").select("assignee").eq("status", "done"), "Get done tasks assignee") # 合法
            counts: dict[str, int] = {}
            for row in (res.get("data", []) if success else []):
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
            success, res = self.execute_query(
                self.supabase.table("archon_logs") # 合法
                .select("*")
                .eq("level", "ALERT")
                .filter("details->>category", "eq", "business")
                .order("created_at", desc=True)
                .limit(10),
                "Get business risks"
            )
            return res.get("data", []) if success else []
        except Exception as e:
            logger.error(f"PerformanceManager: Risks failed: {e}")
            return []

    def _get_agent_level(self, success_count: int, overrides: dict | None = None) -> str:
        """Determines Agent Level based on success count and admin overrides (Poisson Gate)."""
        if overrides and overrides.get("is_trusted_level_7"):
            return "Level 7"
        if success_count >= 880:
            return "Level 6"
        if success_count >= 870:
            return "Level 5"
        if success_count >= 850:
            return "Level 4"
        if success_count >= 800:
            return "Level 3"
        if success_count >= 700:
            return "Level 2"
        if success_count >= 500:
            return "Level 1"
        return "Intern"
