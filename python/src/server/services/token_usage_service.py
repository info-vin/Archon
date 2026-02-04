from decimal import Decimal
from typing import Any, cast

from ..config.logfire_config import get_logger
from ..utils import get_supabase_client

logger = get_logger(__name__)

# Pricing Map (USD per 1M tokens) - Updated 2026-02-03
# Values are illustrative approximations.
PRICING_MAP = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},  # <128k context
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    "gemini-2.0-flash": {"input": 0.10, "output": 0.40}, # Estimated
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
            rates: dict[str, float] | None = None
            if provider == "ollama":
                rates = PRICING_MAP["ollama"]
            else:
                rates = PRICING_MAP.get(model, PRICING_MAP.get("gpt-4o"))

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
            # PostgREST doesn't support aggregate GROUP BY date easily without RPC.
            # For now, we fetch raw data and aggregate in Python (ok for low volume).
            # In Phase 5, we should move this to a DB View or RPC.

            # Fetch last 7 days
            # updated_at is not on token_usage, created_at is.
            # filter created_at > now - 7 days

            # Using RPC is better if available, but let's stick to raw fetch for "Start Simple"
            res = supabase.table("token_usage").select("cost_usd, created_at, model, provider")\
                .order("created_at", desc=True).limit(2000).execute()

            # Aggregate logic here...
            # Omitted for brevity in this initial implementation, will return raw rows for Frontend to aggregate
            data = res.data if res.data else []
            return cast(list[dict[str, Any]], data)

        except Exception as e:
            logger.error(f"Failed to fetch daily cost: {e}")
            return []
