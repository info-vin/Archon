# python/src/server/services/health_service.py

from typing import cast

from server.repositories.base_repository import BaseRepository

from ..utils import get_supabase_client


class HealthService(BaseRepository):
    """
    Service for checking the health of system components including the database.
    """

    def __init__(self, supabase_client=None):
        super().__init__(supabase_client or get_supabase_client())

    def check_db_health(self) -> bool:
        """Checks if the database is reachable and responding."""
        def _query():
            return self.supabase_client.table("profiles").select("id", count="exact").limit(1).execute()

        success, _ = self.execute_query(_query, "DB health check failed")
        return cast(bool, success)

    def verify_auth_config(self) -> bool:
        """Verifies if the Supabase Auth configuration is valid."""
        try:
            # Minimal check to see if auth client is initialized
            return self.supabase_client.auth is not None
        except Exception:
            return False
