"""
Log Service Module for Archon

This module provides business logic for logging Gemini interactions.
"""

from datetime import datetime
from typing import Any, NotRequired, TypedDict

from supabase import Client

from src.server.repositories.base_repository import BaseRepository

from ..config.logfire_config import get_logger
from ..utils import get_supabase_client

logger = get_logger(__name__)


class LogDataDTO(TypedDict):
    user_input: NotRequired[str | None]
    gemini_response: NotRequired[str | None]
    project_name: NotRequired[str | None]
    user_name: NotRequired[str | None]


class LogEntryResultDTO(TypedDict):
    log: NotRequired[dict[str, Any]]
    error: NotRequired[str]


class LogService(BaseRepository):
    """Service class for logging operations"""

    def __init__(self, supabase_client: Client | None = None) -> None:
        """Initialize with optional supabase client"""
        client = supabase_client or get_supabase_client()
        super().__init__(client)

    def create_log_entry(self, log_data: LogDataDTO) -> tuple[bool, LogEntryResultDTO]:
        """
        Creates a new log entry in the archon_logs table.

        Args:
            log_data: A dictionary containing the log data.
                      Expected keys: user_input, gemini_response, project_name, user_name.

        Returns:
            Tuple of (success, result_dict)
        """
        gemini_resp = str(log_data.get("gemini_response") or "Unknown AI Response")
        # Prepare data for archon_logs (Unified Logging Pattern)
        insert_data = {
            "source": log_data.get("project_name", "system"),
            "level": "ERROR" if "Error" in gemini_resp else "INFO",
            "message": gemini_resp[:500],
            "details": {"user_input": log_data.get("user_input"), "user_name": log_data.get("user_name")},
            "created_at": datetime.now().isoformat(),
            "project_name": log_data.get("project_name"),
        }

        # Validate required field
        if not insert_data["message"]:
            logger.warning("Attempted to create a log entry with no message.")
            return False, {"error": "message is a required field."}

        query = self.supabase_client.table("archon_logs").insert(insert_data) # 合法
        success, result = self.execute_query(
            query_func=query, error_context="Failed to insert log into database", require_data=True
        )

        if success and result["data"]:
            logger.info(f"Successfully created log entry with id: {result['data'][0]['id']}")
            return True, {"log": result["data"][0]}

        logger.error(f"Failed to create log entry in database. Response: {result['error']}")
        return False, {"error": result.get("error", "Failed to insert log into database.")}

    async def record_interaction(self, user_id: str, log_data: LogDataDTO) -> LogEntryResultDTO:
        """Compatibility wrapper for API routes."""
        success, res = self.create_log_entry(log_data)
        return res if success else {"error": "Failed to log"}

    async def get_active_alerts(self) -> list[dict[str, Any]]:
        """Physical Placeholder for Charlie's Sentinel Alerts."""
        return []


# Singleton export for modular APIs
log_service = LogService()
