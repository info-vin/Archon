"""
Agent Chat API - Polling-based chat with SSE proxy to AI agents
"""

import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/agent-chat", tags=["agent-chat"])

# Simple in-memory session storage
sessions: dict[str, dict] = {}


# Request/Response models
class CreateSessionRequest(BaseModel):
    project_id: str | None = None
    agent_type: str = "rag"


class ChatMessage(BaseModel):
    id: str
    content: str
    sender: str
    timestamp: datetime
    agent_type: str | None = None


class CreateSessionResponse(BaseModel):
    session_id: str


class SessionResponse(BaseModel):
    id: str
    session_id: str
    project_id: str | None
    agent_type: str | None
    messages: list[ChatMessage]
    created_at: str


class SendMessageRequest(BaseModel):
    message: str


class SendMessageResponse(BaseModel):
    status: str


# REST Endpoints (minimal for frontend compatibility)
@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session(request: CreateSessionRequest) -> CreateSessionResponse:
    """Create a new chat session."""
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "id": session_id,
        "session_id": session_id,  # Frontend expects this
        "project_id": request.project_id,
        "agent_type": request.agent_type,
        "messages": [],
        "created_at": datetime.now().isoformat(),
    }
    logger.info(f"Created chat session {session_id} with agent_type: {request.agent_type}")
    return CreateSessionResponse(session_id=session_id)


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str) -> SessionResponse:
    """Get session information."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionResponse(**sessions[session_id])


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessage])
async def get_messages(session_id: str) -> list[ChatMessage]:
    """Get messages for a session (for polling)."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = sessions[session_id].get("messages", [])
    return [ChatMessage(**msg) for msg in messages]


@router.post("/sessions/{session_id}/messages", response_model=SendMessageResponse)
async def send_message(session_id: str, request: SendMessageRequest) -> SendMessageResponse:
    """REST endpoint for sending messages."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    # Store user message
    user_msg = {
        "id": str(uuid.uuid4()),
        "content": request.message,
        "sender": "user",
        "timestamp": datetime.now().isoformat(),
    }
    sessions[session_id]["messages"].append(user_msg)

    # Note: Agent responses would be processed here if agents service was enabled
    # For now, just return success
    return SendMessageResponse(status="sent")
