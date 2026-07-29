# python/src/server/services/profile_service.py

from typing import Any

from src.server.models.auth_models import UserProfileDTO
from src.server.repositories.base_repository import BaseRepository

from ..config.logfire_config import get_logger
from ..utils import get_supabase_client

logger = get_logger(__name__)


class ProfileService(BaseRepository):
    """Service for handling business logic related to user profiles."""

    def __init__(self, supabase_client: Any = None) -> None:
        """Initialize with optional supabase client."""
        client = supabase_client or get_supabase_client()
        super().__init__(client)

    def list_all_users(self) -> tuple[bool, list[UserProfileDTO] | str]:
        """
        Retrieves all user profiles from the database (basic info only).

        Returns:
            A tuple containing a success boolean and either a list of users or an error message.
        """

        query = self.supabase_client.table("profiles").select("id, name, role")
        success, result = self.execute_query(
            query_func=query, error_context="Failed to retrieve profiles", require_data=False
        )
        if success:
            profiles = result["data"] or []
            return True, [UserProfileDTO(**p) for p in profiles]
        return False, result["error"]

    def list_full_profiles(self) -> tuple[bool, list[UserProfileDTO] | str]:
        """
        Retrieves all user profiles with all fields from the database.
        Intended for administrative use.

        Returns:
            A tuple containing a success boolean and either a list of users or an error message.
        """

        query = self.supabase_client.table("profiles").select("*")
        success, result = self.execute_query(
            query_func=query, error_context="Failed to retrieve full profiles", require_data=False
        )
        if success:
            profiles = result["data"] or []
            return True, [UserProfileDTO(**p) for p in profiles]
        return False, result["error"]

    def get_user_role(self, user_name: str) -> tuple[bool, str | None]:
        """
        Retrieves the role for a specific user by name.

        Args:
            user_name: The name of the user to look up.

        Returns:
            A tuple containing a success boolean and the user's role or None if not found.
        """

        query = self.supabase_client.table("profiles").select("role").eq("name", user_name).limit(1)
        # Returning True, None instead of False when no role is found.
        success, result = self.execute_query(
            query_func=query,
            error_context=f"An unexpected error occurred while retrieving role for user '{user_name}'",
            require_data=False,
        )

        if success:
            return True, result["data"][0].get("role") if result["data"] else None
        return False, None

    def get_profile(self, user_id: str) -> tuple[bool, UserProfileDTO | str | None]:
        """
        Retrieves a user profile by ID.

        Args:
            user_id: The UUID of the user.

        Returns:
            A tuple containing success boolean and the profile data (with flattened permissions).
        """

        query = self.supabase_client.table("profiles").select("*").eq("id", user_id).limit(1)
        success, result = self.execute_query(
            query_func=query, error_context=f"Failed to fetch profile for {user_id}", require_data=True
        )

        if success and result["data"]:
            profile = result["data"][0]
            # Permissions are now handled by the dynamic RBAC service or frontend fallback
            return True, UserProfileDTO(**profile)

        return False, "Profile not found"

    def update_profile(self, user_id: str, updates: dict) -> tuple[bool, UserProfileDTO | str]:
        """
        Updates a user profile.

        Args:
            user_id: The UUID of the user to update.
            updates: A dictionary of fields to update.

        Returns:
            A tuple containing success boolean and the updated profile data (or error message).
        """
        if "id" in updates:
            del updates["id"]

        logger.info(f"Updating profile for {user_id} with: {updates.keys()}")

        query = self.supabase_client.table("profiles").update(updates).eq("id", user_id)
        success, result = self.execute_query(
            query_func=query, error_context=f"Failed to update profile for {user_id}", require_data=True
        )
        if success:
            data = result["data"]
            profile_data = data[0] if isinstance(data, list) else data
            return True, UserProfileDTO(**profile_data)
        return False, result.get("error", "Update failed or returned no data.")
