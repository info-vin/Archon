import asyncio
from decimal import Decimal
from typing import NotRequired, TypedDict, cast

from ..config.config import get_config
from ..config.logfire_config import get_logger
from .client_manager import get_supabase_client

logger = get_logger(__name__)


class TokenUsagePayloadDTO(TypedDict):
    request_id: str
    user_id: str | None
    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    context_type: str | None
    created_at: str


class TokenUsageRowDTO(TypedDict):
    cost_usd: NotRequired[float]
    created_at: str
    model: str
    provider: str
    user_id: NotRequired[str | None]


class DailyCostAggregationDTO(TypedDict):
    date: str
    cost: float
    request_count: int
    models: set[str]
    agent_costs: NotRequired[dict[str, float]]


class DailyCostDTO(TypedDict):
    date: str
    cost: float
    request_count: int
    models: list[str]
    agent_costs: NotRequired[dict[str, float]]


class TokenUsageService:
    @staticmethod
    async def log_usage(
        request_id: str,
        model: str,
        provider: str,
        input_tokens: int,
        output_tokens: int,
        user_id: str | None = None,
        context_type: str | None = None,
    ) -> None:
        """
        Log token usage to the database with cost calculation.
        This is designed to be "fire and forget" - errors are logged but don't stop execution.
        """
        try:
            # calculate cost using global config (Phase 4.6.15)
            config = get_config()
            pricing = config.token_pricing

            # Use specific model pricing or fallback to a standard lite model
            from ..config.model_ssot import SYSTEM_MODELS

            rates = pricing.get(model, pricing.get(SYSTEM_MODELS["DEFAULT_TEXT"].split("/")[-1]))

            if provider == "ollama":
                rates = pricing.get("ollama", {"input": 0, "output": 0})

            cost = Decimal(0)
            if rates:
                # (tokens / 1,000,000) * rate
                input_cost = (Decimal(input_tokens) / Decimal(1_000_000)) * Decimal(rates["input"])
                output_cost = (Decimal(output_tokens) / Decimal(1_000_000)) * Decimal(rates["output"])
                cost = input_cost + output_cost

            supabase = get_supabase_client()

            payload: TokenUsagePayloadDTO = {
                "request_id": request_id,
                "user_id": user_id,
                "model": model,
                "provider": provider,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": float(cost),
                "context_type": context_type,
                "created_at": "now()",
            }

            from ..repositories.base_repository import BaseRepository

            base_repo = BaseRepository(supabase)

            def _log_to_db() -> None:
                base_repo.execute_query(
                    supabase.table("token_usage").insert(payload),
                    error_context="Failed to log token usage",
                )

            await asyncio.to_thread(_log_to_db)

            # --- PHYSICAL XP REWARD SYSTEM (Phase 4.6.15) ---
            if user_id:
                # Check if this user_id belongs to an AI Agent to reward XP
                try:
                    from .agent_registry import FALLBACK_AGENT_CONFIG

                    agent_names = [cfg["name"] for cfg in FALLBACK_AGENT_CONFIG.values()]

                    # We need the display name to award XP via StatsService
                    success, res_dict = base_repo.execute_query(
                        supabase.table("profiles").select("name").eq("id", user_id),
                        error_context="Failed to query profiles for XP",
                    )
                    if success and res_dict.get("data") and res_dict["data"][0]["name"] in agent_names:
                        agent_display_name = str(res_dict["data"][0]["name"])
                        from .stats import StatsService

                        stats_service = StatsService()
                        await stats_service.add_agent_action_log(
                            agent_name=agent_display_name,
                            xp_change=1,  # Micro-reward for model execution
                            message=f"Computational contribution for {context_type or 'general_task'}",
                            details={"token_request_id": request_id, "model": model},
                        )
                except Exception as xp_err:
                    logger.warning(f"XP Reward skipped: {xp_err}")

            if provider != "ollama":
                logger.debug(f"💰 Token Usage Logged: {model} | {input_tokens}/{output_tokens} | ${cost:.6f}")

        except Exception as e:
            # We don't want to break the app if logging fails, but we should know about it.
            logger.error(f"Failed to log token usage: {e}")

    @staticmethod
    async def get_daily_cost(days: int = 7) -> list[DailyCostDTO]:
        """
        Get daily aggregated cost for the last N days.
        """
        try:
            supabase = get_supabase_client()
            from datetime import UTC, datetime, timedelta

            since = datetime.now(UTC) - timedelta(days=days)

            from ..repositories.base_repository import BaseRepository

            base_repo = BaseRepository(supabase)

            def _fetch_data() -> list[TokenUsageRowDTO]:
                success, res_dict = base_repo.execute_query(
                    supabase.table("token_usage")
                    .select("cost_usd, created_at, model, provider, user_id")
                    .gt("created_at", since.isoformat())
                    .order("created_at", desc=True)
                    .limit(5000),
                    error_context="Failed to fetch token usage",
                )
                return cast(list[TokenUsageRowDTO], res_dict.get("data", []) if success else [])

            data = await asyncio.to_thread(_fetch_data)

            # Aggregate by date
            daily_stats: dict[str, DailyCostAggregationDTO] = {}
            for row in data:
                date_str = row["created_at"].split("T")[0]
                if date_str not in daily_stats:
                    daily_stats[date_str] = {
                        "date": date_str,
                        "cost": 0.0,
                        "request_count": 0,
                        "models": set(),
                        "agent_costs": {},
                    }

                daily_stats[date_str]["cost"] += row.get("cost_usd", 0.0)
                daily_stats[date_str]["request_count"] += 1
                daily_stats[date_str]["models"].add(row["model"])

                agent_costs = daily_stats[date_str].setdefault("agent_costs", {})

                u_id = row.get("user_id")
                if u_id:
                    from .agent_registry import FALLBACK_AGENT_CONFIG, get_agent_config, get_agent_uuid

                    agent_name = str(u_id)
                    for agent_key in FALLBACK_AGENT_CONFIG.keys():
                        if get_agent_uuid(agent_key) == str(u_id):
                            try:
                                dyn_config = get_agent_config(agent_key)
                                if dyn_config is not None:
                                    agent_name = str(dyn_config["name"])
                                else:
                                    agent_name = str(FALLBACK_AGENT_CONFIG[agent_key]["name"])
                            except Exception:
                                agent_name = str(FALLBACK_AGENT_CONFIG[agent_key]["name"])
                            break

                    agent_costs[agent_name] = agent_costs.get(agent_name, 0.0) + row.get("cost_usd", 0.0)

            # Convert to list and sort
            result: list[DailyCostDTO] = []
            for d in sorted(daily_stats.keys()):
                item = daily_stats[d]
                dto_item: DailyCostDTO = {
                    "date": item["date"],
                    "cost": item["cost"],
                    "request_count": item["request_count"],
                    "models": list(item["models"]),
                }
                if "agent_costs" in item and item["agent_costs"]:
                    dto_item["agent_costs"] = item["agent_costs"]
                result.append(dto_item)

            return result

        except Exception as e:
            logger.error(f"Failed to fetch daily cost: {e}")
            return []
