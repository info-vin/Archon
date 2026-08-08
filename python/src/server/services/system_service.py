from typing import Any, NotRequired, TypedDict, cast

from ..repositories.base_repository import BaseRepository


class ConnectivityLogDTO(TypedDict):
    id: NotRequired[str]
    source: NotRequired[str]
    level: NotRequired[str]
    message: NotRequired[str]
    details: NotRequired[dict[str, Any] | None]
    created_at: NotRequired[str]
    type: NotRequired[str]
    project_name: NotRequired[str | None]
    user_id: NotRequired[str | None]


class SystemSettingDTO(TypedDict):
    id: NotRequired[str]
    key: NotRequired[str]
    value: NotRequired[str | None]
    encrypted_value: NotRequired[str | None]
    is_encrypted: NotRequired[bool]
    category: NotRequired[str | None]
    description: NotRequired[str | None]
    created_at: NotRequired[str]
    updated_at: NotRequired[str]
    is_system_protected: NotRequired[bool]


class SystemService(BaseRepository):
    def __init__(self) -> None:
        super().__init__()

    async def list_connectivity_logs(self, limit: int = 20) -> list[ConnectivityLogDTO]:
        query = self.supabase_client.table("archon_logs").select("*").eq("level", "ALERT").eq("type", "system").order("created_at", desc=True).limit(limit) # 合法
        success, res = self.execute_query(query, "Failed to list connectivity logs", require_data=False)
        return cast(list[ConnectivityLogDTO], res.get("data", []) if success else [])

    async def list_system_settings(self, category: str | None = None) -> list[SystemSettingDTO]:
        query = self.supabase_client.table("archon_settings").select("*") # 合法
        if category:
            query = query.eq("category", category)
        query = query.order("key")
        success, res = self.execute_query(query, "Failed to list system settings", require_data=False)
        return cast(list[SystemSettingDTO], res.get("data", []) if success else [])

    async def update_system_setting(self, key: str, new_value: str, description: str | None, user_name: str) -> SystemSettingDTO:
        # 1. Fetch old value
        query_old = self.supabase_client.table("archon_settings").select("value, is_system_protected").eq("key", key) # 合法
        success_old, res_old = self.execute_query(query_old, f"Setting '{key}' not found", require_data=True)
        if not success_old or not res_old.get("data"):
            raise ValueError(f"Setting '{key}' not found")

        old_data = res_old["data"][0]
        old_value = old_data["value"]

        # 2. Update
        update_data = {"value": str(new_value), "updated_at": "now()"}
        if description:
            update_data["description"] = description

        query_upd = self.supabase_client.table("archon_settings").update(update_data).eq("key", key) # 合法
        success_upd, res_upd = self.execute_query(query_upd, f"Failed to update setting '{key}'", require_data=True)
        if not success_upd or not res_upd.get("data"):
            raise ValueError(f"Setting '{key}' not found")

        # 3. Audit
        try:
            audit_payload = {
                "document_id": f"setting:{key}",
                "created_by": user_name,
                "change_type": "UPDATE",
                "field_name": key,
                "old_value": str(old_value),
                "new_value": str(new_value),
                "change_summary": f"System setting '{key}' updated by {user_name}",
                "version_number": 1,
            }
            self.execute_query(self.supabase_client.table("archon_document_versions").insert(audit_payload), "Audit log failed", require_data=False) # 合法
        except Exception:
            pass

        return cast(SystemSettingDTO, res_upd["data"][0])

system_service = SystemService()
