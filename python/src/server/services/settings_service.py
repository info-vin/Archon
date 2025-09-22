# python/src/server/services/settings_service.py

from ..utils import get_supabase_client
from ..config.logfire_config import get_logger

logger = get_logger(__name__)

class SettingsService:
    """Service for handling business logic related to application settings and statistics."""

    def __init__(self, supabase_client=None):
        """Initialize with optional supabase client."""
        self.supabase_client = supabase_client or get_supabase_client()

    def get_database_statistics(self) -> tuple[bool, dict | str]:
        """
        Retrieves record counts for various tables in the database.

        Returns:
            A tuple containing a success boolean and either a dictionary of table counts or an error message.
        """
        try:
            tables_info = {}

            # Get projects count
            projects_response = (
                self.supabase_client.table("archon_projects").select("id", count="exact").execute()
            )
            tables_info["projects"] = (
                projects_response.count if projects_response.count is not None else 0
            )

            # Get tasks count
            tasks_response = self.supabase_client.table("archon_tasks").select("id", count="exact").execute()
            tables_info["tasks"] = tasks_response.count if tasks_response.count is not None else 0

            # Get crawled pages count
            pages_response = (
                self.supabase_client.table("archon_crawled_pages").select("id", count="exact").execute()
            )
            tables_info["crawled_pages"] = (
                pages_response.count if pages_response.count is not None else 0
            )

            # Get settings count
            settings_response = (
                self.supabase_client.table("archon_settings").select("id", count="exact").execute()
            )
            tables_info["settings"] = (
                settings_response.count if settings_response.count is not None else 0
            )

            return True, tables_info

        except Exception as e:
            logger.error(f"Error getting database statistics: {e}", exc_info=True)
            return False, f"Error getting database statistics: {e}"
