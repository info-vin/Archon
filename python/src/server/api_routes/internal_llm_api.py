import os

import httpx
from fastapi import APIRouter, HTTPException, Request, Response

from src.server.config.logfire_config import get_logger
from src.server.services.threading_service import get_threading_service

logger = get_logger(__name__)

router = APIRouter(prefix="/internal/llm", tags=["internal_llm"])


@router.post("/gemini/v1beta/{path:path}")
async def proxy_gemini_v1beta(path: str, request: Request):
    """
    Transparent proxy for Gemini API to enforce centralized Rate Limiting.
    All LLM requests from archon-agents and archon-mcp route through here.
    """
    body = await request.body()
    # Rough estimate of tokens based on payload size (4 chars ~ 1 token)
    estimated_tokens = max(100, len(body) // 4)

    threading_service = get_threading_service()

    async with threading_service.rate_limited_operation(estimated_tokens=estimated_tokens):
        headers = dict(request.headers)
        # Remove host header to avoid SSL/DNS mismatch at target
        headers.pop("host", None)

        # Inject API key if missing (so agents don't strictly need it in their env, though they might have it)
        if "x-goog-api-key" not in headers:
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                headers["x-goog-api-key"] = api_key

        target_url = f"https://generativelanguage.googleapis.com/v1beta/{path}"

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(target_url, content=body, headers=headers, timeout=120.0)

                # We need to filter out hop-by-hop headers from the response to avoid HTTP protocol errors
                excluded_headers = ["content-encoding", "content-length", "transfer-encoding", "connection"]
                resp_headers = {k: v for k, v in resp.headers.items() if k.lower() not in excluded_headers}

                return Response(content=resp.content, status_code=resp.status_code, headers=resp_headers)
            except httpx.RequestError as exc:
                logger.error(f"LLM Gateway Network Error: {exc}")
                raise HTTPException(status_code=502, detail=f"Bad Gateway: {str(exc)}") from exc
