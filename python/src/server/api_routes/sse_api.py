
"""
SSE API Router for Archon (Phase 5.1.0)
Endpoints for real-time task status updates.
"""

from typing import Any

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from src.server.utils.sse_manager import sse_manager

router = APIRouter(prefix="/api/sse", tags=["sse"])


@router.get("/tasks")
async def task_stream() -> Any:
    """
    SSE stream for task status updates.
    Clients can subscribe to receive real-time updates when tasks change.
    """
    subscriber_id, queue = await sse_manager.subscribe()
    return StreamingResponse(
        sse_manager.event_generator(subscriber_id, queue),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable Nginx buffering
        },
    )
