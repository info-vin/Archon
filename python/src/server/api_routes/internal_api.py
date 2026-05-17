"""
Internal API endpoints for inter-service communication.

These endpoints are meant to be called only by other services in the Archon system,
not by external clients. They provide internal functionality like credential sharing.
"""

import logging
import os
import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel

from ..services.credential_service import credential_service

logger = logging.getLogger(__name__)

# Create router with internal prefix
router = APIRouter(prefix="/internal", tags=["internal"])


def is_internal_request(request: Request) -> bool:
    """
    Check if a request is coming from within the internal network.
    This is a basic security check for internal API endpoints.
    """
    client_host = request.client.host if request.client else "unknown"

    # Allow requests from localhost/127.0.0.1
    if client_host in ("127.0.0.1", "localhost", "::1", "testclient"):
        return True

    # Allow requests from Docker internal network (typically 172.x.x.x)
    if client_host.startswith("172."):
        return True

    # Check for X-Internal-Key header (used for inter-service auth)
    internal_key = os.getenv("ARCHON_INTERNAL_KEY")
    request_key = request.headers.get("X-Internal-Key")
    if internal_key and request_key == internal_key:
        return True

    return False


class TokenUsagePayload(BaseModel):
    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    context_type: str = "agentic_workflow"


@router.post("/stats/token-usage")
async def log_token_usage(payload: TokenUsagePayload, request: Request):
    """
    Internal endpoint to log token usage from agents service.
    Phase 5.4: Fix Token Logging Gap.
    """
    if not is_internal_request(request):
        client_host = request.client.host if request.client else "unknown"
        logger.warning(f"Unauthorized access to internal token-usage from {client_host}")
        raise HTTPException(status_code=403, detail="Access forbidden")

    try:
        from ..services.token_usage_service import TokenUsageService

        await TokenUsageService.log_usage(
            request_id=str(uuid.uuid4()),
            model=payload.model,
            provider=payload.provider,
            input_tokens=payload.input_tokens,
            output_tokens=payload.output_tokens,
            context_type=payload.context_type,
        )
        return {"success": True}
    except Exception as e:
        logger.error(f"Error logging token usage: {e}")
        raise HTTPException(status_code=500, detail="Failed to log token usage") from e


@router.get("/credentials/agents")
async def get_agent_credentials(request: Request) -> dict[str, Any]:
    """
    Get credentials needed by the agents service.
    """
    # Check if request is from internal source
    if not is_internal_request(request):
        client_host = request.client.host if request.client else "unknown"
        logger.warning(f"Unauthorized access to internal credentials from {client_host}")
        raise HTTPException(status_code=403, detail="Access forbidden")

    try:
        from ..config.model_ssot import SYSTEM_MODELS

        credentials = {
            "OPENAI_API_KEY": await credential_service.get_credential("OPENAI_API_KEY"),
            "GEMINI_API_KEY": await credential_service.get_credential("GEMINI_API_KEY"),
            "GOOGLE_API_KEY": await credential_service.get_credential("GOOGLE_API_KEY"),
            "ANTHROPIC_API_KEY": await credential_service.get_credential("ANTHROPIC_API_KEY"),
            "LOGFIRE_TOKEN": await credential_service.get_credential("LOGFIRE_TOKEN"),
            "AGENT_RATE_LIMIT_ENABLED": await credential_service.get_credential(
                "AGENT_RATE_LIMIT_ENABLED", default="true"
            ),
            "AGENT_MAX_RETRIES": await credential_service.get_credential("AGENT_MAX_RETRIES", default="3"),
            "MCP_SERVICE_URL": await credential_service.get_credential(
                "MCP_SERVICE_URL", default="http://archon-mcp:8051"
            ),
            "LOG_LEVEL": await credential_service.get_credential("LOG_LEVEL", default="INFO"),
            # Phase 5.4.5: Global Model SSOT Hardening
            "SUPERVISOR_AGENT_MODEL": SYSTEM_MODELS["DEFAULT_PRO"].split("/")[-1],
            "WORKER_AGENT_MODEL": SYSTEM_MODELS["DEFAULT_TEXT"].split("/")[-1],
            "DOCUMENT_AGENT_MODEL": SYSTEM_MODELS["DEFAULT_PRO"].split("/")[-1],
            "RAG_AGENT_MODEL": SYSTEM_MODELS["DEFAULT_TEXT"].split("/")[-1],
        }

        logger.info(f"Provided credentials to agents service from {request.client.host if request.client else 'unknown'}")
        return credentials

    except Exception as e:
        logger.error(f"Error retrieving agent credentials: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve credentials") from e


@router.get("/credentials/mcp")
async def get_mcp_credentials(request: Request) -> dict[str, Any]:
    """
    Get credentials needed by the MCP service.
    """
    # Check if request is from internal source
    if not is_internal_request(request):
        client_host = request.client.host if request.client else "unknown"
        logger.warning(f"Unauthorized access to internal credentials from {client_host}")
        raise HTTPException(status_code=403, detail="Access forbidden")

    try:
        credentials = {
            "LOG_LEVEL": await credential_service.get_credential("LOG_LEVEL", default="INFO"),
        }

        logger.info(f"Provided credentials to MCP service from {request.client.host if request.client else 'unknown'}")
        return credentials

    except Exception as e:
        logger.error(f"Error retrieving MCP credentials: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve credentials") from e


@router.post("/cron/trigger")
async def trigger_cron_jobs(request: Request, background_tasks: BackgroundTasks, api_key: str | None = None):
    """
    Webhook to trigger scheduler jobs externally.
    Allows execution via internal IP or matching ARCHON_CRON_SECRET.
    """
    is_internal = is_internal_request(request)
    valid_api_key = os.getenv("ARCHON_CRON_SECRET")

    if not is_internal:
        if not valid_api_key or api_key != valid_api_key:
            auth_header = request.headers.get("Authorization")
            if not auth_header or auth_header != f"Bearer {valid_api_key}":
                logger.warning("Unauthorized access to trigger-jobs")
                raise HTTPException(status_code=403, detail="Access forbidden")

    try:
        from ..services.scheduler_service import scheduler_service

        # Add all jobs to FastAPI BackgroundTasks so they run concurrently after the response
        background_tasks.add_task(scheduler_service._run_system_probe)
        background_tasks.add_task(scheduler_service._run_auto_fetch_leads)
        background_tasks.add_task(scheduler_service._analyze_token_usage)
        background_tasks.add_task(scheduler_service._run_log_patrol)
        background_tasks.add_task(scheduler_service._run_task_dispatcher)
        background_tasks.add_task(scheduler_service._cleanup_system_probes)

        return {"status": "triggered", "jobs": 6}
    except Exception as e:
        logger.error(f"Error triggering cron jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# --- David's Self-Evolution Endpoints (Phase 5.1.3) ---

@router.get("/david/read")
async def david_read_file(request: Request, path: str):
    """
    Internal endpoint for David to read codebase files.
    """
    if not is_internal_request(request):
        raise HTTPException(status_code=403, detail="Access forbidden")

    if ".." in path or path.startswith("/"):
         raise HTTPException(status_code=400, detail="Invalid path")

    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Internal Read: Failed to read {path}: {e}")
        raise HTTPException(status_code=404, detail=str(e)) from e

@router.post("/david/propose")
async def david_create_proposal(request: Request, payload: dict[str, Any]):
    """
    Internal endpoint for David to submit code change proposals.
    """
    if not is_internal_request(request):
        raise HTTPException(status_code=403, detail="Access forbidden")

    from ..services.propose_change_service import ProposeChangeService
    service = ProposeChangeService()

    file_path = payload.get("file_path")
    new_content = payload.get("new_content")
    summary = payload.get("summary", "AI Generated Fix")

    if not file_path or new_content is None:
        raise HTTPException(status_code=400, detail="Missing file_path or new_content")

    res = await service.create_file_proposal(
        file_path=file_path,
        new_content=new_content,
        summary=summary,
        user_id=None # David is a system agent
    )
    return res
