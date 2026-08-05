# python/src/server/services/auth_service.py

from typing import Any, NotRequired, TypedDict, cast

from src.server.repositories.base_repository import BaseRepository

from ..config.logfire_config import get_logger
from ..utils import get_supabase_client

logger = get_logger(__name__)


class UserProfileDictDTO(TypedDict):
    id: str
    employeeId: NotRequired[str | None]
    name: str
    email: str
    department: NotRequired[str | None]
    position: NotRequired[str | None]
    status: NotRequired[str | None]
    role: NotRequired[str | None]
    avatar: NotRequired[str | None]
    permission_overrides: NotRequired[dict[str, Any] | None]
    tenant_id: NotRequired[str | None]


class AuthService(BaseRepository):
    def __init__(self, supabase_client: Any = None) -> None:
        super().__init__(supabase_client or get_supabase_client())

    def get_all_users(self) -> list[UserProfileDictDTO]:
        """
        Lists all users from the profiles table.
        Returns a list of profile dicts.
        """
        query = self.supabase_client.table("profiles").select("*")
        success, res = self.execute_query(query, "Error fetching users", require_data=False)
        return cast(list[UserProfileDictDTO], res.get("data", []) if success else [])

    def register_user(self, email: str, password: str, name: str, role: str = "employee") -> UserProfileDictDTO:
        """
        Registers a new user in Supabase Auth and creates a profile.
        """
        return self.create_user_by_admin(email, password, name, role)

    def create_user_by_admin(
        self, email: str, password: str, name: str, role: str = "employee", status: str = "active"
    ) -> UserProfileDictDTO:
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

            query = self.supabase_client.table("profiles").upsert(profile_data)
            self.execute_query(query, f"Error creating profile for {user_id}", require_data=False)
            return cast(UserProfileDictDTO, profile_data)
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
            query = self.supabase_client.table("profiles").update({"email": new_email}).eq("id", user_id)
            self.execute_query(query, f"Error updating email in profile for {user_id}", require_data=False)

        except Exception as e:
            logger.error(f"Error updating email: {e}", exc_info=True)
            raise e

    def update_user_by_admin(self, user_id: str, updates: dict[str, Any]) -> UserProfileDictDTO:
        """
        Updates a user's role, status, or permissions as an Admin.
        """
        try:
            logger.info(f"Admin updating user {user_id}: {updates.keys()}")

            # 1. Sync Role to Auth User Metadata if it changed
            if "role" in updates:
                self.supabase_client.auth.admin.update_user_by_id(user_id, {"user_metadata": {"role": updates["role"]}})

            # 2. Update Profile table
            query = self.supabase_client.table("profiles").update(updates).eq("id", user_id)
            success, res = self.execute_query(query, f"Failed to update profile for {user_id}", require_data=False)

            if success and res.get("data"):
                return cast(UserProfileDictDTO, res["data"][0])
            raise ValueError(f"Failed to update profile for {user_id}")

        except Exception as e:
            logger.error(f"Error updating user by admin: {e}", exc_info=True)
            raise e
