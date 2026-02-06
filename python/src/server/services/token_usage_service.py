from decimal import Decimal
from typing import Any

from ..config.logfire_config import get_logger
from ..utils import get_supabase_client

logger = get_logger(__name__)

# Pricing Map (USD per 1M tokens) - Updated 2026-02-03
# Values are illustrative approximations.
PRICING_MAP = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
    "gemini-2.5-flash": {"input": 0.10, "output": 0.40},
    "gemini-2.5-flash-lite": {"input": 0.05, "output": 0.20}, # Nano Banana Lite
    "gemini-2.5-flash-image": {"input": 0.00, "output": 2.00}, # $0.002 per image (heuristic)
    "text-embedding-004": {"input": 0.02, "output": 0.00},
    "claude-3-5-sonnet": {"input": 3.00, "output": 15.00},
    "ollama": {"input": 0.00, "output": 0.00}, # Local is free
}

class TokenUsageService:
    @staticmethod
    async def log_usage(
        request_id: str,
        model: str,
        provider: str,
        input_tokens: int,
        output_tokens: int,
        user_id: str | None = None,
        context_type: str | None = None
    ) -> None:
        """
        Log token usage to the database with cost calculation.
        This is designed to be "fire and forget" - errors are logged but don't stop execution.
        """
        try:
            # calculate cost
            rates = PRICING_MAP.get(model, PRICING_MAP.get("gemini-2.5-flash-lite"))
            if provider == "ollama":
                rates = PRICING_MAP["ollama"]

            cost = Decimal(0)
            if rates:
                 # (tokens / 1,000,000) * rate
                 input_cost = (Decimal(input_tokens) / Decimal(1_000_000)) * Decimal(rates["input"])
                 output_cost = (Decimal(output_tokens) / Decimal(1_000_000)) * Decimal(rates["output"])
                 cost = input_cost + output_cost

            supabase = get_supabase_client()

            payload = {
                "request_id": request_id,
                "user_id": user_id,
                "model": model,
                "provider": provider,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": float(cost),
                "context_type": context_type,
                "created_at": "now()"
            }

            # Using fire-and-forget approach or await?
            # Ideally async, but Supabase client is synchronous requests wrapped in async usually?
            # Our get_supabase_client returns a sync client usually, but let's check.
            # Assuming postgrest-py execute() is sync, we might want to run in thread if blocking.
            # But for now, direct call is fine as it's critical data.

            supabase.table("token_usage").insert(payload).execute()

            if provider != "ollama":
                logger.debug(f"💰 Token Usage Logged: {model} | {input_tokens}/{output_tokens} | ${cost:.6f}")

        except Exception as e:
            # We don't want to break the app if logging fails, but we should know about it.
            logger.error(f"Failed to log token usage: {e}")

    @staticmethod
    async def get_daily_cost(days: int = 7) -> list[dict[str, Any]]:
        """
        Get daily aggregated cost for the last N days.
        """
        try:
            supabase = get_supabase_client()
            from datetime import UTC, datetime, timedelta
            since = datetime.now(UTC) - timedelta(days=days)

            # Fetch last N days raw data
            res = supabase.table("token_usage").select("cost_usd, created_at, model, provider")\
                .gt("created_at", since.isoformat())\
                .order("created_at", desc=True).limit(5000).execute()

            data = res.data if res.data else []

            # Aggregate by date
            daily_stats: dict[str, dict[str, Any]] = {}
            for row in data:
                # created_at is ISO string e.g. "2026-02-06T12:00:00+00:00"
                date_str = row["created_at"].split("T")[0]
                if date_str not in daily_stats:
                    daily_stats[date_str] = {
                        "date": date_str,
                        "cost": 0.0,
                        "request_count": 0,
                        "models": set()
                    }

                daily_stats[date_str]["cost"] += row.get("cost_usd", 0)
                daily_stats[date_str]["request_count"] += 1
                daily_stats[date_str]["models"].add(row["model"])

            # Convert to list and sort
            result = []
            for d in sorted(daily_stats.keys()):
                item = daily_stats[d]
                item["models"] = list(item["models"]) # Convert set to list for JSON serialization
                result.append(item)

            return result

        except Exception as e:
            logger.error(f"Failed to fetch daily cost: {e}")
            return []
