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
        Retrieves all user profiles from the database (basic info only).

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

    def list_full_profiles(self) -> tuple[bool, list[dict] | str]:
        """
        Retrieves all user profiles with all fields from the database.
        Intended for administrative use.

        Returns:
            A tuple containing a success boolean and either a list of users or an error message.
        """
        try:
            response = self.supabase_client.table("profiles").select("*").execute()
            if response.data is None:
                return True, []
            return True, response.data
        except Exception as e:
            logger.error(f"Failed to list full profiles: {e}", exc_info=True)
            return False, f"Failed to retrieve full profiles: {e}"

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

    def get_profile(self, user_id: str) -> tuple[bool, dict | str | None]:
        """
        Retrieves a user profile by ID.

        Args:
            user_id: The UUID of the user.

        Returns:
            A tuple containing success boolean and the profile data (or error message/None).
        """
        try:
            response = self.supabase_client.table("profiles").select("*").eq("id", user_id).single().execute()
            # .single() raises an exception if not found in some versions, or returns data/error
            # If response.data is populated, we have the user
            return True, response.data
        except Exception as e:
            # Distinguish between not found and actual error if possible, but for now generic catch
            # Supabase-py often raises postgrest.exceptions.APIError for 406/404
            logger.warning(f"Failed to fetch profile for {user_id}: {e}")
            return False, str(e)

    def update_profile(self, user_id: str, updates: dict) -> tuple[bool, dict | str]:
        """
        Updates a user profile.

        Args:
            user_id: The UUID of the user to update.
            updates: A dictionary of fields to update.

        Returns:
            A tuple containing success boolean and the updated profile data (or error message).
        """
        try:
            # Prevent updating immutable fields if any (id should not be in updates ideally)
            if "id" in updates:
                del updates["id"]

            logger.info(f"Updating profile for {user_id} with: {updates.keys()}")

            # Fix: Simplify query chain for sync client compatibility (remove .select().single())
            response = self.supabase_client.table("profiles").update(updates).eq("id", user_id).execute()

            # Check for data or error
            if response.data:
                # Return first item if list, else item
                return True, response.data[0] if isinstance(response.data, list) else response.data

            # Fallback if no data returned (though select() should ensure it)
            return False, "Update failed or returned no data."

        except Exception as e:
            logger.error(f"Failed to update profile for {user_id}: {e}", exc_info=True)
            return False, str(e)
