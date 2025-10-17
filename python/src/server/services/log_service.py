"""
Log Service Module for Archon

This module provides business logic for logging Gemini interactions.
"""
from datetime import datetime

from ..config.logfire_config import get_logger
from ..utils import get_supabase_client

logger = get_logger(__name__)

class LogService:
    """Service class for logging operations"""

    def __init__(self, supabase_client=None):
        """Initialize with optional supabase client"""
        self.supabase_client = supabase_client or get_supabase_client()

    def create_log_entry(self, log_data: dict) -> tuple[bool, dict]:
        """
        Creates a new log entry in the gemini_logs table.

        Args:
            log_data: A dictionary containing the log data.
                      Expected keys: user_input, gemini_response, project_name, user_name.

        Returns:
            Tuple of (success, result_dict)
        """
        try:
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

            response = self.supabase_client.table("gemini_logs").insert(insert_data).execute()

            if response.data:
                logger.info(f"Successfully created log entry with id: {response.data[0]['id']}")
                return True, {"log": response.data[0]}
            else:
                logger.error(f"Failed to create log entry in database. Response: {response}")
                return False, {"error": "Failed to insert log into database."}

        except Exception as e:
            logger.error(f"Error creating log entry: {e}", exc_info=True)
            return False, {"error": str(e)}
