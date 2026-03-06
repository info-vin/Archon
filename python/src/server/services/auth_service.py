# python/src/server/services/auth_service.py

from typing import Any

from server.repositories.base_repository import BaseRepository

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

    def create_user_by_admin(self, email: str, password: str, name: str, role: str = "employee", status: str = "active") -> dict[str, Any]:
        """
        Creates a user via admin privileges.
        """
        try:
            # 1. Sign up in Auth
            auth_res = self.supabase_client.auth.sign_up({
                "email": email,
                "password": password,
                "options": {"data": {"full_name": name, "role": role}}
            })
            if not auth_res.user:
                raise ValueError("Auth signup failed")

            user_id = auth_res.user.id

            # 2. Create Profile
            profile_data = {
                "id": user_id,
                "email": email,
                "full_name": name,
                "role": role,
                "status": status
            }
            self.supabase_client.table("profiles").upsert(profile_data).execute()
            return profile_data
        except Exception as e:
            logger.error(f"Registration error: {e}")
            raise e
