"""
API endpoint for logging Gemini interactions.
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional

from ..config.logfire_config import get_logger
from ..services.log_service import LogService

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["Logging"])

class GeminiLogRequest(BaseModel):
    user_input: Optional[str] = None
    gemini_response: str
    project_name: Optional[str] = None
    user_name: Optional[str] = None

@router.post("/record-gemini-log", status_code=status.HTTP_201_CREATED)
async def record_gemini_log(request: GeminiLogRequest):
    """
    Receives a log of a Gemini interaction and records it in the database.
    """
    try:
        logger.info(f"Received request to log Gemini interaction for project: {request.project_name}")
        
        log_service = LogService()
        success, result = log_service.create_log_entry(request.dict())

        if not success:
            logger.error(f"Failed to create log entry: {result.get('error')}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "An unknown error occurred.")
            )

        logger.info(f"Successfully recorded log entry with ID: {result['log']['id']}")
        return {"message": "Log recorded successfully", "log_id": result['log']['id']}

    except HTTPException:
        # Re-raise HTTPException to prevent it from being caught by the generic Exception handler
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred while recording a Gemini log: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred."
        )
