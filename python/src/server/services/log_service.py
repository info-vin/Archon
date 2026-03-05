"""
Log Service Module for Archon

This module provides business logic for logging Gemini interactions.
"""
from datetime import datetime

from ..config.logfire_config import get_logger
from ..repositories.base_repository import BaseRepository
from ..utils import get_supabase_client

logger = get_logger(__name__)

class LogService(BaseRepository):
    """Service class for logging operations"""

    def __init__(self, supabase_client=None):
        """Initialize with optional supabase client"""
        client = supabase_client or get_supabase_client()
        super().__init__(client)

    def create_log_entry(self, log_data: dict) -> tuple[bool, dict]:
        """
        Creates a new log entry in the gemini_logs table.

        Args:
            log_data: A dictionary containing the log data.
                      Expected keys: user_input, gemini_response, project_name, user_name.

        Returns:
            Tuple of (success, result_dict)
        """
        # Prepare data for insertion
        insert_data = {
            "user_input": log_data.get("user_input"),
            "gemini_response": log_data.get("gemini_response"),
            "project_name": log_data.get("project_name"),
            "user_name": log_data.get("user_name"),
            "created_at": datetime.now().isoformat(),
        }

        # Validate required field
        if not insert_data["gemini_response"]:
            logger.warning("Attempted to create a log entry with no gemini_response.")
            return False, {"error": "gemini_response is a required field."}

        def _query():
            return self.supabase_client.table("gemini_logs").insert(insert_data).execute()

        success, result = self.execute_query(
            query_func=_query,
            error_context="Failed to insert log into database",
            require_data=True
        )

        if success and result["data"]:
            logger.info(f"Successfully created log entry with id: {result['data'][0]['id']}")
            return True, {"log": result["data"][0]}

        logger.error(f"Failed to create log entry in database. Response: {result['error']}")
        return False, {"error": result.get("error", "Failed to insert log into database.")}
