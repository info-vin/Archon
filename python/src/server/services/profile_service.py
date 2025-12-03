# python/src/server/services/profile_service.py

from ..config.logfire_config import get_logger
from ..utils import get_supabase_client

logger = get_logger(__name__)

class ProfileService:
    """Service for handling business logic related to user profiles."""

    def __init__(self, supabase_client=None):
        """Initialize with optional supabase client."""
        self.supabase_client = supabase_client or get_supabase_client()

    def list_all_users(self) -> tuple[bool, list[dict] | str]:
        """
        Retrieves all user profiles from the database.

        Returns:
            A tuple containing a success boolean and either a list of users or an error message.
        """
        try:
            response = self.supabase_client.table("profiles").select("id, name, role").execute()
            if response.data is None:
                logger.warning("Could not fetch profiles from database.")
                return True, []
            return True, response.data
        except Exception as e:
            logger.error(f"Failed to list profiles: {e}", exc_info=True)
            return False, f"Failed to retrieve profiles: {e}"

    def get_user_role(self, user_name: str) -> tuple[bool, str | None]:
        """
        Retrieves the role for a specific user by name.

        Args:
            user_name: The name of the user to look up.

        Returns:
            A tuple containing a success boolean and the user's role or None if not found.
        """
        try:
            # Use limit(1) to safely handle potential duplicate names instead of .single()
            response = self.supabase_client.table("profiles").select("role").eq("name", user_name).limit(1).execute()
            if response.data:
                # If data is returned, take the role from the first record
                return True, response.data[0].get("role")
            # If no user is found, it's not an error, just return no role
            return True, None
        except Exception as e:
            # An exception here points to a more serious issue (e.g., DB connection)
            logger.error(f"An unexpected error occurred while retrieving role for user '{user_name}': {e}")
            return False, None
