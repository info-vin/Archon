"""
Budget Guard Middleware for FastAPI.

Intercepts requests and aborts with HTTP 402 (Payment Required)
when a tenant's cumulative LLM token consumption costs exceed their allocated budget.
"""

from collections.abc import Callable
from typing import cast

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..auth.internal_auth import INTERNAL_HEADER, internal_header_decision
from ..auth.utils import get_user_from_token
from ..config.logfire_config import get_logger
from ..utils import get_supabase_client

logger = get_logger("budget_guard")


class BudgetGuardMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces tenant-level budget controls on write operations.
    """

    # Endpoints that are safe and should never be blocked by budget
    BYPASS_PATHS = {"/health", "/api/health", "/api/auth", "/docs", "/redoc", "/openapi.json"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # A verified MCP internal credential has no tenant profile. Looking one up
        # fail-closes to HTTP 402, which would block every MCP write. Skipping the
        # tenant budget here does not grant admin: the route allowlist still applies.
        # A present but unacceptable header is rejected with a response, not an exception,
        # because BaseHTTPMiddleware would otherwise surface it as HTTP 500.
        internal_decision = internal_header_decision(request.headers.get(INTERNAL_HEADER))
        if internal_decision == "rejected":
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid authentication credentials"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        if internal_decision == "accepted":
            return cast(Response, await call_next(request))

        # 1. Skip checks for GET requests, health, or auth routes
        if request.method == "GET" or request.url.path in self.BYPASS_PATHS or not request.url.path.startswith("/api/"):
            return cast(Response, await call_next(request))

        # 2. Extract Authorization token
        auth_header = request.headers.get("Authorization", "")
        token = ""
        if auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")

        if not token:
            # Let normal authentication middleware handle missing credentials
            return cast(Response, await call_next(request))

        # 3. Retrieve user profile. HTTPException must not leave this middleware:
        # BaseHTTPMiddleware does not deliver it to FastAPI's HTTPException handler,
        # and the process-wide handler turns it into HTTP 500. The route dependency
        # still authenticates the request.
        try:
            user = await get_user_from_token(token)
        except HTTPException:
            return cast(Response, await call_next(request))
        if not user:
            return cast(Response, await call_next(request))

        # Bypass checks only for trusted internal system-agent or verified DB profile system_admin
        if getattr(user, "id", "") == "system-agent":
            return cast(Response, await call_next(request))

        # 4. Fetch tenant ID and role from profiles, then query total budget consumed
        try:
            supabase = get_supabase_client()

            # Query tenant ID and role from user profile (never trust user_metadata)
            profile_res = supabase.table("profiles").select("tenant_id, role").eq("id", user.id).execute()
            if not profile_res.data:
                return cast(Response, await call_next(request))

            if profile_res.data[0].get("role") == "system_admin":
                return cast(Response, await call_next(request))

            tenant_id = profile_res.data[0]["tenant_id"]

            # Query total token costs for this tenant
            usage_res = supabase.table("token_usage").select("cost_usd").eq("tenant_id", tenant_id).execute()
            total_cost = sum(float(row["cost_usd"] or 0) for row in usage_res.data)

            # Get budget limit from settings
            settings_res = supabase.table("archon_settings").select("value").eq("key", "BUDGET_LIMIT_USD").execute()
            budget_limit = 10.0
            if settings_res.data and settings_res.data[0]["value"]:
                try:
                    budget_limit = float(settings_res.data[0]["value"])
                except ValueError:
                    pass

            # 5. Enforce budget limit
            if total_cost >= budget_limit:
                logger.warning(
                    f"⚠️ [Budget Guard] Blocked request from user={user.email} (Tenant={tenant_id}). "
                    f"Total Cost: ${total_cost:.4f} >= Limit: ${budget_limit:.4f}"
                )
                return JSONResponse(
                    status_code=402,
                    content={
                        "error": "Payment Required",
                        "detail": f"Tenant budget limit exceeded. Total Cost: ${total_cost:.4f} >= Limit: ${budget_limit:.4f}",
                    },
                )

        except Exception as e:
            logger.error(f"[Budget Guard] Error enforcing budget checks: {e}")
            # Fail-closed/Fail-safe: Block write actions on DB connectivity error unless system_admin/agent
            return JSONResponse(
                status_code=402,
                content={
                    "error": "Payment Required",
                    "detail": f"Database verification failure during budget checks: {e}. Operation blocked for safety.",
                },
            )

        return cast(Response, await call_next(request))
