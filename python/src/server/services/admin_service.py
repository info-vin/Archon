from typing import Any, cast

from ..config.logfire_config import get_logger
from ..repositories.base_repository import BaseRepository

logger = get_logger(__name__)


class AdminService(BaseRepository):
    def __init__(self):
        super().__init__()
    async def get_all_users(self, limit: int = 100, role_filter: str | None = None) -> list[dict[str, Any]]:
        """
        Fetch all users from public.profiles.
        In a real production app, we should iterate/paginate properly.
        """
        try:
            supabase = self.supabase_client
            query = supabase.table("profiles").select("*").order("name")

            if role_filter and role_filter != "all":
                query = query.eq("role", role_filter)

            success, res = self.execute_query(query.limit(limit), "Failed to fetch users")
            return cast(list[dict[str, Any]], res.get("data", []) if success else [])
        except Exception as e:
            logger.error(f"AdminService: Failed to fetch users: {e}")
            raise

    async def update_user_role(self, user_id: str, new_role: str, current_admin_email: str) -> dict[str, Any]:
        """
        Update a user's role in both public.profiles and auth.users metadata.
        Synchronizing with auth metadata ensures the change is reflected in JWT tokens immediately.
        """
        try:
            supabase = self.supabase_client

            # Log the action
            logger.info(f"AdminService: Role update | target={user_id} | role={new_role} | by={current_admin_email}")

            # 1. Update public.profiles (Source of truth for profile data)
            payload = {
                "role": new_role,
                # "updated_at": "now()" # profiles might not have updated_at
            }
            query = supabase.table("profiles").update(payload).eq("id", user_id)
            success, res = self.execute_query(query, "Failed to update user role", require_data=True)
            if not success:
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

            data = res.get("data", [{}])[0]

            # 3. Log the audit event physically in archon_logs (Phase 5.8)
            try:
                audit_log = {
                    "source": "admin_action",
                    "level": "INFO",
                    "message": f"User role updated: {user_id} -> {new_role}",
                    "type": "audit",
                    "details": {
                        "target_user_id": user_id,
                        "new_role": new_role,
                        "updated_by": current_admin_email,
                        "version": "v4.6.31",
                    },
                }
                self.execute_query(supabase.table("archon_logs").insert(audit_log), "Audit logging failed")
            except Exception as log_err:
                logger.error(f"AdminService: Audit logging failed: {log_err}")

            return cast(dict[str, Any], data)

        except Exception as e:
            logger.error(f"AdminService: Failed to update role: {e}")
            raise

    async def get_rbac_matrix(self) -> list[dict[str, Any]]:
        """Fetch the full role-permission matrix from the database."""
        try:
            supabase = self.supabase_client
            query = supabase.table("archon_roles_permissions").select("*").order("role")
            success, res = self.execute_query(query, "Failed to fetch RBAC matrix")
            return cast(list[dict[str, Any]], res.get("data", []) if success else [])
        except Exception as e:
            logger.error(f"AdminService: Failed to fetch RBAC matrix: {e}")
            raise

    async def update_rbac_role(self, role: str, permissions: list[str], description: str | None = None) -> dict[str, Any]:
        """Update or create a role's permissions in the dynamic matrix."""
        try:
            supabase = self.supabase_client
            payload: dict[str, Any] = {
                "role": role.lower(),
                "permissions": permissions,
            }
            if description is not None:
                payload["description"] = description

            query = supabase.table("archon_roles_permissions").upsert(payload)
            success, res = self.execute_query(query, f"Failed to update role {role}", require_data=True)
            if not success:
                raise ValueError(f"Failed to update role {role}")

            # Clear RBACService cache to ensure changes take effect immediately
            from .rbac_service import RBACService

            RBACService._matrix_cache = None

            # Log the audit event physically in archon_logs (Phase 5.8)
            try:
                audit_log = {
                    "source": "admin_action",
                    "level": "INFO",
                    "message": f"RBAC Matrix updated for role: {role}",
                    "type": "audit",
                    "details": {"role": role, "permissions": permissions, "version": "v4.6.31"},
                }
                self.execute_query(supabase.table("archon_logs").insert(audit_log), "Audit logging failed")
            except Exception as log_err:
                logger.error(f"AdminService: RBAC audit logging failed: {log_err}")

            return cast(dict[str, Any], res.get("data", [{}])[0])
        except Exception as e:
            logger.error(f"AdminService: Failed to update RBAC role {role}: {e}")
            raise

    async def get_document_versions(self, limit: int = 100) -> list[dict[str, Any]]:
        query = self.supabase_client.table("archon_document_versions").select("*").order("created_at", desc=True).limit(limit)
        success, res = self.execute_query(query, "Failed to fetch document versions")
        return cast(list[dict[str, Any]], res.get("data", []) if success else [])

    async def list_crawler_targets(self, department: str | None = None) -> list[dict[str, Any]]:
        query = self.supabase_client.table("archon_crawler_targets").select("*")
        if department:
            query = query.eq("department", department)
        query = query.order("created_at")
        success, res = self.execute_query(query, "Failed to list crawler targets")
        return cast(list[dict[str, Any]], res.get("data", []) if success else [])

    async def create_crawler_target(self, data: dict[str, Any]) -> dict[str, Any]:
        query = self.supabase_client.table("archon_crawler_targets").insert(data)
        success, res = self.execute_query(query, "Failed to create target", require_data=True)
        if not success:
            raise ValueError("Failed to create target")
        return cast(dict[str, Any], res.get("data", [{}])[0])

    async def delete_crawler_target(self, target_id: str) -> None:
        query = self.supabase_client.table("archon_crawler_targets").delete().eq("id", target_id)
        self.execute_query(query, f"Failed to delete target {target_id}")

    async def get_admin_logs(self, type: str | None = None, time_range: str | None = "7d") -> list[dict[str, Any]]:
        from datetime import datetime, timedelta
        query = self.supabase_client.table("archon_logs").select("*")
        if type:
            query = query.eq("type", type)
        if time_range:
            days = int(time_range.replace("d", "")) if time_range.endswith("d") else 7
            cutoff_time = (datetime.now() - timedelta(days=days)).isoformat()
            query = query.gte("created_at", cutoff_time)
        query = query.order("created_at", desc=True)
        success, res = self.execute_query(query, "Failed to fetch admin logs")
        return cast(list[dict[str, Any]], res.get("data", []) if success else [])

admin_service = AdminService()
