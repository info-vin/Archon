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


class LogDetailsDTO(TypedDict):
    user_input: NotRequired[str | None]
    user_name: NotRequired[str | None]


class LogEntryDTO(TypedDict):
    id: NotRequired[str]
    source: NotRequired[str | None]
    level: NotRequired[str | None]
    message: NotRequired[str | None]
    details: NotRequired[LogDetailsDTO | dict[str, Any] | None]
    created_at: NotRequired[str | None]
    project_name: NotRequired[str | None]


class LogEntryResultDTO(TypedDict):
    log: NotRequired[LogEntryDTO]
    error: NotRequired[str]


class SystemAlertDTO(TypedDict):
    id: str
    level: str
    message: str
    created_at: NotRequired[str | None]
    source: NotRequired[str | None]
    project_name: NotRequired[str | None]
    details: NotRequired[dict[str, Any] | None]


class RecentAlertsResultDTO(TypedDict):
    data: NotRequired[list[SystemAlertDTO]]
    error: NotRequired[str]


class LogService(BaseRepository):
    """Service class for logging operations"""

    def __init__(self, supabase_client: Client | None = None) -> None:
        """Initialize with optional supabase client"""
        client = supabase_client or get_supabase_client()
        super().__init__(client)

    async def get_recent_alerts(self, limit: int = 10) -> tuple[bool, RecentAlertsResultDTO]:
        """Retrieve recent alert logs with trimmed payload for AI ingestion."""
        query = (
            self.supabase_client.table("archon_logs")
            .select("id, level, message, created_at, source, project_name, details")
            .eq("level", "ALERT")
            .order("created_at", desc=True)
            .limit(limit)
        ) # 合法
        success, res = await self.execute_query_async(query, "Failed to fetch recent alerts")

        if not success or not isinstance(res, dict):
            raw_err = res.get("error") if isinstance(res, dict) else None
            err_msg = raw_err if isinstance(raw_err, str) else "Failed to fetch recent alerts"
            return False, {"error": err_msg}

        raw_data = res.get("data")
        alerts_list: list[SystemAlertDTO] = []
        if isinstance(raw_data, list):
            for item in raw_data:
                if isinstance(item, dict):
                    alert_item: SystemAlertDTO = {
                        "id": str(item.get("id") or ""),
                        "level": str(item.get("level") or "ALERT"),
                        "message": str(item.get("message") or ""),
                        "created_at": item.get("created_at") if isinstance(item.get("created_at"), str) else None,
                        "source": item.get("source") if isinstance(item.get("source"), str) else None,
                        "project_name": item.get("project_name") if isinstance(item.get("project_name"), str) else None,
                        "details": item.get("details") if isinstance(item.get("details"), dict) else None,
                    }
                    alerts_list.append(alert_item)

        return True, {"data": alerts_list}

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
        details_data: LogDetailsDTO = {
            "user_input": log_data.get("user_input"),
            "user_name": log_data.get("user_name"),
        }
        # Prepare data for archon_logs (Unified Logging Pattern)
        insert_data = {
            "source": log_data.get("project_name", "system") or "system",
            "level": "ERROR" if "Error" in gemini_resp else "INFO",
            "message": gemini_resp[:500],
            "details": details_data,
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

        if success and isinstance(result, dict):
            raw_data = result.get("data")
            if isinstance(raw_data, list) and len(raw_data) > 0 and isinstance(raw_data[0], dict):
                first_row = raw_data[0]
                entry_id = str(first_row.get("id") or "")
                logger.info(f"Successfully created log entry with id: {entry_id}")
                entry_dto: LogEntryDTO = {
                    "id": entry_id,
                    "source": first_row.get("source") if isinstance(first_row.get("source"), str) else None,
                    "level": first_row.get("level") if isinstance(first_row.get("level"), str) else None,
                    "message": first_row.get("message") if isinstance(first_row.get("message"), str) else None,
                    "details": first_row.get("details") if isinstance(first_row.get("details"), dict) else None,
                    "created_at": first_row.get("created_at") if isinstance(first_row.get("created_at"), str) else None,
                    "project_name": first_row.get("project_name") if isinstance(first_row.get("project_name"), str) else None,
                }
                return True, {"log": entry_dto}

        raw_err = result.get("error") if isinstance(result, dict) else None
        err_msg = raw_err if isinstance(raw_err, str) else "Failed to insert log into database."
        logger.error(f"Failed to create log entry in database. Response: {err_msg}")
        return False, {"error": err_msg}

    async def record_interaction(self, user_id: str, log_data: LogDataDTO) -> LogEntryResultDTO:
        """Compatibility wrapper for API routes."""
        success, res = self.create_log_entry(log_data)
        if success:
            return res
        raw_err = res.get("error") if isinstance(res, dict) else None
        err_msg = raw_err if isinstance(raw_err, str) else "Failed to log"
        return {"error": err_msg}

    async def get_active_alerts(self, limit: int = 50) -> list[SystemAlertDTO]:
        """Fetch active system alerts (level=ALERT) from archon_logs table."""
        query = (
            self.supabase_client.table("archon_logs")
            .select("id, level, message, created_at, source, project_name, details")
            .eq("level", "ALERT")
            .order("created_at", desc=True)
            .limit(limit)
        ) # 合法
        success, res = await self.execute_query_async(query, "Failed to fetch active alerts")

        if not success or not isinstance(res, dict):
            return []

        raw_data = res.get("data")
        alerts: list[SystemAlertDTO] = []
        if isinstance(raw_data, list):
            for item in raw_data:
                if isinstance(item, dict) and item.get("id") and item.get("message"):
                    alert: SystemAlertDTO = {
                        "id": str(item["id"]),
                        "level": str(item.get("level") or "ALERT"),
                        "message": str(item["message"]),
                        "created_at": item.get("created_at") if isinstance(item.get("created_at"), str) else None,
                        "source": item.get("source") if isinstance(item.get("source"), str) else None,
                        "project_name": item.get("project_name") if isinstance(item.get("project_name"), str) else None,
                        "details": item.get("details") if isinstance(item.get("details"), dict) else None,
                    }
                    alerts.append(alert)

        return alerts


# Singleton export for modular APIs
log_service = LogService()
