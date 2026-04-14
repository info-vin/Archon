"""
Visit Log Service - Business logic for tracking customer interactions.
"""

from typing import Any

from src.server.repositories.base_repository import BaseRepository
from src.server.utils import get_supabase_client


class VisitLogService(BaseRepository):
    def __init__(self, supabase_client=None):
        super().__init__(supabase_client or get_supabase_client())

    async def list_logs(self, lead_id: str | None = None) -> tuple[bool, Any]:
        def _query():
            q = self.supabase_client.table("visit_logs").select("*")
            if lead_id:
                q = q.eq("lead_id", lead_id)
            return q.execute()

        return self.execute_query(_query, "Failed to list logs")

    async def create_log(self, data: dict) -> tuple[bool, Any]:
        # GAP-011: Physical field alignment (Normalizing payload for DB)
        normalized_data = data.copy()
        if "company_name" in normalized_data and "location_address" not in normalized_data:
            normalized_data["location_address"] = normalized_data.pop("company_name")

        def _query():
            return self.supabase_client.table("visit_logs").insert(normalized_data).execute()

        return self.execute_query(_query, "Failed to create log")

    async def get_attendance_status(self, user_id: str) -> tuple[bool, Any]:
        """Fetches the current attendance status for a user."""

        def _query():
            return (
                self.supabase_client.table("attendance_logs")
                .select("*")
                .eq("user_id", user_id)
                .order("clock_in_time", desc=True)
                .limit(1)
                .execute()
            )

        success, res = self.execute_query(_query, "Failed to fetch attendance status")
        if not success or not res:
            return True, {"status": "OFF_WORK", "clock_in_time": None}

        # Extract data from Supabase response
        data: list[Any] = res if isinstance(res, list) else []
        return True, data[0] if len(data) > 0 else {"status": "OFF_WORK", "clock_in_time": None}


# Singleton export
visit_log_service = VisitLogService()
