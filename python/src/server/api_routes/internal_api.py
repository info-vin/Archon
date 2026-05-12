"""
Internal API endpoints for inter-service communication.

These endpoints are meant to be called only by other services in the Archon system,
not by external clients. They provide internal functionality like credential sharing.
"""

import logging
import os
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from ..services.credential_service import credential_service

logger = logging.getLogger(__name__)

# Create router with internal prefix
router = APIRouter(prefix="/internal", tags=["internal"])

# Simple IP-based access control for internal endpoints
ALLOWED_INTERNAL_IPS = [
    "127.0.0.1",  # Localhost
    "172.18.0.0/16",  # Docker network range
    "archon-agents",  # Docker service name
    "archon-mcp",  # Docker service name
]


def is_internal_request(request: Request) -> bool:
    """Check if request is from an internal source."""
    if request.client is None:
        return False
    client_host = request.client.host

    # Check if it's a Docker network IP (172.16.0.0/12 range)
    if client_host.startswith("172."):
        parts = client_host.split(".")
        if len(parts) == 4:
            second_octet = int(parts[1])
            # Docker uses 172.16.0.0 - 172.31.255.255
            if 16 <= second_octet <= 31:
                logger.info(f"Allowing Docker network request from {client_host}")
                return True

    # Check if it's localhost
    if client_host in ["127.0.0.1", "::1", "localhost"]:
        return True

    return False


@router.get("/health")
async def internal_health():
    """Internal health check endpoint."""
    return {"status": "healthy", "service": "internal-api"}


@router.get("/credentials/agents")
async def get_agent_credentials(request: Request) -> dict[str, Any]:
    """
    Get credentials needed by the agents service.

    This endpoint is only accessible from internal services and provides
    the necessary credentials for AI agents to function.
    """
    # Check if request is from internal source
    if not is_internal_request(request):
        logger.warning("Unauthorized access to internal credentials")
        raise HTTPException(status_code=403, detail="Access forbidden")

    try:
        # Get credentials needed by agents
        credentials = {
            # API Keys
            "OPENAI_API_KEY": await credential_service.get_credential("OPENAI_API_KEY", decrypt=True),
            "GEMINI_API_KEY": await credential_service.get_credential("GEMINI_API_KEY", decrypt=True),

            # Model configurations
            "DOCUMENT_AGENT_MODEL": await credential_service.get_credential("DOCUMENT_AGENT_MODEL"),
            "RAG_AGENT_MODEL": await credential_service.get_credential("RAG_AGENT_MODEL"),
            "TASK_AGENT_MODEL": await credential_service.get_credential("TASK_AGENT_MODEL"),
            "SUMMARY_AGENT_MODEL": await credential_service.get_credential("SUMMARY_AGENT_MODEL"),
            # Rate limiting settings
            "AGENT_RATE_LIMIT_ENABLED": await credential_service.get_credential(
                "AGENT_RATE_LIMIT_ENABLED", default="true"
            ),
            "AGENT_MAX_RETRIES": await credential_service.get_credential("AGENT_MAX_RETRIES", default="3"),
            # MCP endpoint
            "MCP_SERVICE_URL": f"http://archon-mcp:{os.getenv('ARCHON_MCP_PORT')}",
            # Additional settings
            "LOG_LEVEL": await credential_service.get_credential("LOG_LEVEL", default="INFO"),
        }

        # Filter out None values
        credentials = {k: v for k, v in credentials.items() if v is not None}

        client_host = request.client.host if request.client is not None else "unknown"
        logger.info(f"Provided credentials to agents service from {client_host}")
        return credentials

    except Exception as e:
        logger.error(f"Error retrieving agent credentials: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve credentials") from e


@router.get("/credentials/mcp")
async def get_mcp_credentials(request: Request) -> dict[str, Any]:
    """
    Get credentials needed by the MCP service.

    This endpoint provides credentials for the MCP service if needed in the future.
    """
    # Check if request is from internal source
    if not is_internal_request(request):
        client_host = request.client.host if request.client else "unknown"
        logger.warning(f"Unauthorized access to internal credentials from {client_host}")
        raise HTTPException(status_code=403, detail="Access forbidden")

    try:
        credentials = {
            # MCP might need some credentials in the future
            "LOG_LEVEL": await credential_service.get_credential("LOG_LEVEL", default="INFO"),
        }

        logger.info(f"Provided credentials to MCP service from {client_host}")
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

        return {"status": "success", "message": "Background jobs queued successfully"}
    except Exception as e:
        logger.error(f"Error triggering jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
