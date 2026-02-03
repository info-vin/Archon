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
        Update a user's role in public.profiles.
        Note: This does NOT update auth.users metadata automatically without a trigger or Supabase Admin Client.
        For Phase 4.6.4, we assume profiles is the source of truth for application logic.
        """
        try:
            supabase = get_supabase_client()

            # Log the action
            logger.info(f"AdminService: Role update | target={user_id} | role={new_role} | by={current_admin_email}")

            # Update public.profiles
            payload = {
                "role": new_role,
                # "updated_at": "now()" # profiles might not have updated_at in current schema verify?
                                        # Schema 000 says profiles has no updated_at column explicitly defined in Create Table block
                                        # but usually it's good practice. I'll omit it to be safe based on schema reading.
            }

            res = supabase.table("profiles").update(payload).eq("id", user_id).execute()

            if not res.data:
                raise ValueError("User not found or update failed")

            data = res.data[0]
            return cast(dict[str, Any], data)

        except Exception as e:
            logger.error(f"AdminService: Failed to update role: {e}")
            raise
