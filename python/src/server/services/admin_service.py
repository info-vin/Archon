from typing import Any, NotRequired, TypedDict, cast

from ..config.logfire_config import get_logger
from ..repositories.base_repository import BaseRepository

logger = get_logger(__name__)


class UserProfileDTO(TypedDict):
    id: str
    name: NotRequired[str | None]
    role: NotRequired[str | None]
    email: NotRequired[str | None]
    created_at: NotRequired[str | None]
    updated_at: NotRequired[str | None]


class RBACRoleDTO(TypedDict):
    role: str
    permissions: list[str]
    description: NotRequired[str | None]


class DocumentVersionDTO(TypedDict):
    id: NotRequired[str]
    document_id: NotRequired[str | None]
    project_id: NotRequired[str | None]
    task_id: NotRequired[str | None]
    created_by: NotRequired[str | None]
    change_type: NotRequired[str | None]
    field_name: NotRequired[str | None]
    old_value: NotRequired[str | None]
    new_value: NotRequired[str | None]
    content: NotRequired[dict[str, Any] | None]
    status: NotRequired[str | None]
    change_summary: NotRequired[str | None]
    version_number: NotRequired[int | None]
    created_at: NotRequired[str | None]


class CrawlerTargetDTO(TypedDict):
    id: NotRequired[str]
    target_url: str
    department: NotRequired[str | None]
    status: NotRequired[str | None]
    is_active: NotRequired[bool | None]
    max_depth: NotRequired[int | None]
    description: NotRequired[str | None]
    whitelist: NotRequired[list[str] | None]
    update_frequency: NotRequired[str | None]
    created_at: NotRequired[str | None]
    updated_at: NotRequired[str | None]


class AdminLogDTO(TypedDict):
    id: NotRequired[str]
    source: NotRequired[str]
    level: NotRequired[str]
    message: NotRequired[str]
    details: NotRequired[dict[str, Any] | None]
    created_at: NotRequired[str]
    type: NotRequired[str]


class AdminService(BaseRepository):
    def __init__(self) -> None:
        super().__init__()

    async def get_all_users(self, limit: int = 100, role_filter: str | None = None) -> list[UserProfileDTO]:
        """
        Fetch all users from public.profiles.
        In a real production app, we should iterate/paginate properly.
        """
        try:
            supabase = self.supabase_client
            query = supabase.table("profiles").select("*").order("name")  # 合法

            if role_filter and role_filter != "all":
                query = query.eq("role", role_filter)

            success, res = await self.execute_query_async(query.limit(limit), "Failed to fetch users")
            if not success or not isinstance(res, dict):
                return []
            raw_data = res.get("data")
            if not isinstance(raw_data, list):
                return []
            return [cast(UserProfileDTO, item) for item in raw_data if isinstance(item, dict) and "id" in item]
        except Exception as e:
            logger.error(f"AdminService: Failed to fetch users: {e}")
            raise

    async def update_user_role(self, user_id: str, new_role: str, current_admin_email: str) -> UserProfileDTO:
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
            }
            query = supabase.table("profiles").update(payload).eq("id", user_id)  # 合法
            success, res = await self.execute_query_async(query, "Failed to update user role", require_data=True)
            if not success or not isinstance(res, dict):
                raise ValueError("User not found in profiles or update failed")

            raw_data = res.get("data")
            if not isinstance(raw_data, list) or not raw_data or not isinstance(raw_data[0], dict):
                raise ValueError("User update succeeded but returned invalid record shape")
            data = raw_data[0]

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
                await self.execute_query_async(supabase.table("archon_logs").insert(audit_log), "Audit logging failed")  # 合法
            except Exception as log_err:
                logger.error(f"AdminService: Audit logging failed: {log_err}")

            return cast(UserProfileDTO, data)

        except Exception as e:
            logger.error(f"AdminService: Failed to update role: {e}")
            raise

    async def get_rbac_matrix(self) -> list[RBACRoleDTO]:
        """Fetch the full role-permission matrix from the database."""
        try:
            supabase = self.supabase_client
            query = supabase.table("archon_roles_permissions").select("*").order("role")  # 合法
            success, res = await self.execute_query_async(query, "Failed to fetch RBAC matrix")
            if not success or not isinstance(res, dict):
                return []
            raw_data = res.get("data")
            if not isinstance(raw_data, list):
                return []
            return [cast(RBACRoleDTO, item) for item in raw_data if isinstance(item, dict) and "role" in item and "permissions" in item]
        except Exception as e:
            logger.error(f"AdminService: Failed to fetch RBAC matrix: {e}")
            raise

    async def update_rbac_role(self, role: str, permissions: list[str], description: str | None = None) -> RBACRoleDTO:
        """Update or create a role's permissions in the dynamic matrix."""
        try:
            supabase = self.supabase_client
            payload: dict[str, Any] = {
                "role": role.lower(),
                "permissions": permissions,
            }
            if description is not None:
                payload["description"] = description

            query = supabase.table("archon_roles_permissions").upsert(payload)  # 合法
            success, res = await self.execute_query_async(query, f"Failed to update role {role}", require_data=True)
            if not success or not isinstance(res, dict):
                raise ValueError(f"Failed to update role {role}")

            raw_data = res.get("data")
            if not isinstance(raw_data, list) or not raw_data or not isinstance(raw_data[0], dict):
                raise ValueError(f"Role update succeeded but returned invalid record shape for {role}")
            role_record = raw_data[0]

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
                await self.execute_query_async(supabase.table("archon_logs").insert(audit_log), "Audit logging failed")  # 合法
            except Exception as log_err:
                logger.error(f"AdminService: RBAC audit logging failed: {log_err}")

            return cast(RBACRoleDTO, role_record)
        except Exception as e:
            logger.error(f"AdminService: Failed to update RBAC role {role}: {e}")
            raise

    async def get_document_versions(self, limit: int = 100) -> list[DocumentVersionDTO]:
        query = self.supabase_client.table("archon_document_versions").select("*").order("created_at", desc=True).limit(limit)  # 合法
        success, res = await self.execute_query_async(query, "Failed to fetch document versions")
        if not success or not isinstance(res, dict):
            return []
        raw_data = res.get("data")
        if not isinstance(raw_data, list):
            return []
        return [cast(DocumentVersionDTO, item) for item in raw_data if isinstance(item, dict)]

    async def list_crawler_targets(self, department: str | None = None) -> list[CrawlerTargetDTO]:
        query = self.supabase_client.table("archon_crawler_targets").select("*")  # 合法
        if department:
            query = query.eq("department", department)
        query = query.order("created_at")
        success, res = await self.execute_query_async(query, "Failed to list crawler targets")
        if not success or not isinstance(res, dict):
            return []
        raw_data = res.get("data")
        if not isinstance(raw_data, list):
            return []
        return [cast(CrawlerTargetDTO, item) for item in raw_data if isinstance(item, dict) and "target_url" in item]

    async def create_crawler_target(self, data: CrawlerTargetDTO | dict[str, Any]) -> CrawlerTargetDTO:
        query = self.supabase_client.table("archon_crawler_targets").insert(data)  # 合法
        success, res = await self.execute_query_async(query, "Failed to create target", require_data=True)
        if not success or not isinstance(res, dict):
            raise ValueError("Failed to create target")
        raw_data = res.get("data")
        if not isinstance(raw_data, list) or not raw_data or not isinstance(raw_data[0], dict):
            raise ValueError("Created crawler target but returned invalid record shape")
        return cast(CrawlerTargetDTO, raw_data[0])

    async def delete_crawler_target(self, target_id: str) -> None:
        query = self.supabase_client.table("archon_crawler_targets").delete().eq("id", target_id)  # 合法
        await self.execute_query_async(query, f"Failed to delete target {target_id}")

    async def get_admin_logs(self, type: str | None = None, time_range: str | None = "7d") -> list[AdminLogDTO]:
        from datetime import datetime, timedelta

        query = self.supabase_client.table("archon_logs").select("*")  # 合法
        if type:
            query = query.eq("type", type)
        if time_range:
            days = int(time_range.replace("d", "")) if time_range.endswith("d") else 7
            cutoff_time = (datetime.now() - timedelta(days=days)).isoformat()
            query = query.gte("created_at", cutoff_time)
        query = query.order("created_at", desc=True)
        success, res = await self.execute_query_async(query, "Failed to fetch admin logs")
        if not success or not isinstance(res, dict):
            return []
        raw_data = res.get("data")
        if not isinstance(raw_data, list):
            return []
        return [cast(AdminLogDTO, item) for item in raw_data if isinstance(item, dict)]


admin_service = AdminService()
