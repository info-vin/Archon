# python/src/server/services/health_service.py

from ..config.logfire_config import get_logger
from ..utils import get_supabase_client

logger = get_logger(__name__)

class HealthService:
    """Service for checking the health of the application and its dependencies."""

    def __init__(self):
        self.supabase_client = get_supabase_client()

    def check_database_connection(self) -> bool:
        """Checks if the database connection is active."""
        try:
            # A simple query to check the connection
            self.supabase_client.table("users").select("id").limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            return False

    def check_table_existence(self, table_name: str) -> bool:
        """Checks if a specific table exists in the database."""
        try:
            # Note: This is a simplified check. A more robust check might involve
            # querying information_schema, but for this purpose, a select is sufficient.
            self.supabase_client.table(table_name).select("id").limit(1).execute()
            return True
        except Exception:
            # The query will fail if the table does not exist
            return False

    def get_system_health(self) -> dict:
        """Returns a comprehensive health status of the system."""
        db_connected = self.check_database_connection()

        if not db_connected:
            return {
                "status": "unhealthy",
                "database": "disconnected",
                "services": {}
            }

        # List of essential tables to check
        tables_to_check = ["projects", "tasks", "profiles", "gemini_logs"]

        table_statuses = {}
        all_tables_ok = True
        for table in tables_to_check:
            exists = self.check_table_existence(table)
            table_statuses[f"{table}_table"] = exists
            if not exists:
                all_tables_ok = False

        system_status = "healthy" if all_tables_ok else "degraded"

        return {
            "status": system_status,
            "database": "connected",
            "services": {
                "schema": {
                    **table_statuses,
                    "valid": all_tables_ok
                }
            }
        }
