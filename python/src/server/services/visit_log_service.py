"""
Visit Log Service - Business logic for tracking customer interactions.
"""
from typing import Any, Optional
from src.server.repositories.base_repository import BaseRepository
from src.server.utils import get_supabase_client

class VisitLogService(BaseRepository):
    def __init__(self, supabase_client=None):
        super().__init__(supabase_client or get_supabase_client())

    async def list_logs(self, lead_id: Optional[str] = None) -> tuple[bool, Any]:
        def _query():
            q = self.supabase_client.table("visit_logs").select("*")
            if lead_id:
                q = q.eq("lead_id", lead_id)
            return q.execute()
        return self.execute_query(_query, "Failed to list logs")

    async def create_log(self, data: dict) -> tuple[bool, Any]:
        def _query():
            return self.supabase_client.table("visit_logs").insert(data).execute()
        return self.execute_query(_query, "Failed to create log")

# Singleton export
visit_log_service = VisitLogService()
