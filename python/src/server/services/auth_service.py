# python/src/server/services/auth_service.py

from typing import Any, cast

from src.server.repositories.base_repository import BaseRepository

from ..config.logfire_config import get_logger
from ..utils import get_supabase_client

logger = get_logger(__name__)


class AuthService(BaseRepository):
    def __init__(self, supabase_client=None):
        super().__init__(supabase_client or get_supabase_client())

    def get_all_users(self) -> list[dict[str, Any]]:
        """
        Lists all users from the profiles table.
        Returns a list of profile dicts.
        """
        try:
            response = self.supabase_client.table("profiles").select("*").execute()
            return list(response.data) if response.data else []
        except Exception as e:
            logger.error(f"Error fetching users: {e}")
            return []

    def register_user(self, email: str, password: str, name: str, role: str = "employee") -> dict[str, Any]:
        """
        Registers a new user in Supabase Auth and creates a profile.
        """
        return self.create_user_by_admin(email, password, name, role)

    def create_user_by_admin(
        self, email: str, password: str, name: str, role: str = "employee", status: str = "active"
    ) -> dict[str, Any]:
        """
        Creates a user via admin privileges.
        """
        from gotrue.types import AdminUserAttributes

        try:
            # 1. Create Auth User via Admin API
            attributes: AdminUserAttributes = {
                "email": email,
                "password": password,
                "email_confirm": True,
                "user_metadata": {"name": name, "role": role},
            }

            user_response = self.supabase_client.auth.admin.create_user(attributes)
            if not user_response.user:
                raise ValueError("Auth creation failed")

            user_id = user_response.user.id

            # 2. Create Profile
            profile_data = {
                "id": user_id,
                "email": email,
                "name": name,
                "role": role,
                "status": status,
                "avatar": f"https://i.pravatar.cc/150?u={user_id}",
            }

            self.supabase_client.table("profiles").upsert(profile_data).execute()
            return profile_data
        except Exception as e:
            logger.error(f"Admin user creation error: {e}")
            raise e

    def update_user_email(self, user_id: str, new_email: str) -> None:
        """
        Updates user email via Admin API.
        """
        try:
            logger.info(f"Updating email for {user_id} to {new_email}")

            # 1. Update Auth
            self.supabase_client.auth.admin.update_user_by_id(user_id, {"email": new_email})

            # 2. Update Profile
            self.supabase_client.table("profiles").update({"email": new_email}).eq("id", user_id).execute()

        except Exception as e:
            logger.error(f"Error updating email: {e}", exc_info=True)
            raise e

    def update_user_by_admin(self, user_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        """
        Updates a user's role, status, or permissions as an Admin.
        """
        try:
            logger.info(f"Admin updating user {user_id}: {updates.keys()}")

            # 1. Sync Role to Auth User Metadata if it changed
            if "role" in updates:
                self.supabase_client.auth.admin.update_user_by_id(user_id, {"user_metadata": {"role": updates["role"]}})

            # 2. Update Profile table
            res = self.supabase_client.table("profiles").update(updates).eq("id", user_id).execute()

            if res.data:
                return cast(dict[str, Any], res.data[0])
            raise ValueError(f"Failed to update profile for {user_id}")

        except Exception as e:
            logger.error(f"Error updating user by admin: {e}", exc_info=True)
            raise e
