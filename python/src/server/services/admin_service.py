from typing import Any, cast

from ..config.logfire_config import get_logger
from ..utils import get_supabase_client

logger = get_logger(__name__)


class AdminService:
    @staticmethod
    async def get_all_users(limit: int = 100, role_filter: str | None = None) -> list[dict[str, Any]]:
        """
        Fetch all users from public.profiles.
        In a real production app, we should iterate/paginate properly.
        """
        try:
            supabase = get_supabase_client()
            query = supabase.table("profiles").select("*").order("name")

            if role_filter and role_filter != "all":
                query = query.eq("role", role_filter)

            response = query.limit(limit).execute()
            data = response.data if response.data else []
            return cast(list[dict[str, Any]], data)
        except Exception as e:
            logger.error(f"AdminService: Failed to fetch users: {e}")
            raise

    @staticmethod
    async def update_user_role(user_id: str, new_role: str, current_admin_email: str) -> dict[str, Any]:
        """
        Update a user's role in both public.profiles and auth.users metadata.
        Synchronizing with auth metadata ensures the change is reflected in JWT tokens immediately.
        """
        try:
            supabase = get_supabase_client()

            # Log the action
            logger.info(f"AdminService: Role update | target={user_id} | role={new_role} | by={current_admin_email}")

            # 1. Update public.profiles (Source of truth for profile data)
            payload = {
                "role": new_role,
                # "updated_at": "now()" # profiles might not have updated_at
            }
            res = supabase.table("profiles").update(payload).eq("id", user_id).execute()

            if not res.data:
                raise ValueError("User not found in profiles or update failed")

            # 2. Update auth.users metadata (Source of truth for JWT/Permissions)
            # Since get_supabase_client uses SERVICE_KEY, we have admin privileges.
            try:
                # Note: supabase-py admin methods are sync
                supabase.auth.admin.update_user_by_id(user_id, {"user_metadata": {"role": new_role}})
                logger.info(f"AdminService: Synced metadata role for {user_id}")
            except Exception as auth_err:
                # Log but don't fail the whole request if only metadata sync fails
                # (though it's critical for RBAC)
                logger.error(f"AdminService: Auth metadata sync failed for {user_id}: {auth_err}")

            data = res.data[0]
            return cast(dict[str, Any], data)

        except Exception as e:
            logger.error(f"AdminService: Failed to update role: {e}")
            raise
