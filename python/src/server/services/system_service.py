from typing import Any, NotRequired, TypedDict, cast

from supabase import Client

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


class DocumentVersionDTO(TypedDict):
    document_id: str
    created_by: str
    change_type: str
    field_name: str
    version_number: int
    change_summary: str
    content: dict[str, Any]


class SystemService(BaseRepository):
    def __init__(self, supabase_client: Client | None = None) -> None:
        super().__init__(supabase_client)

    async def list_connectivity_logs(self, limit: int = 20) -> list[ConnectivityLogDTO]:
        query = self.supabase_client.table("archon_logs").select("*").eq("level", "ALERT").eq("type", "system").order("created_at", desc=True).limit(limit) # 合法
        success, res = await self.execute_query_async(query, "Failed to list connectivity logs", require_data=False)
        raw_data = res.get("data", []) if success and isinstance(res.get("data"), list) else []
        return [cast(ConnectivityLogDTO, item) for item in raw_data if isinstance(item, dict)]

    async def list_system_settings(self, category: str | None = None) -> list[SystemSettingDTO]:
        query = self.supabase_client.table("archon_settings").select("*") # 合法
        if category:
            query = query.eq("category", category)
        query = query.order("key")
        success, res = await self.execute_query_async(query, "Failed to list system settings", require_data=False)
        raw_data = res.get("data", []) if success and isinstance(res.get("data"), list) else []
        return [cast(SystemSettingDTO, item) for item in raw_data if isinstance(item, dict)]

    async def update_system_setting(self, key: str, new_value: str, description: str | None, user_name: str) -> SystemSettingDTO:
        # 1. Fetch old value
        query_old = self.supabase_client.table("archon_settings").select("value, is_system_protected").eq("key", key) # 合法
        success_old, res_old = await self.execute_query_async(query_old, f"Setting '{key}' not found", require_data=True)
        old_list = res_old.get("data") if success_old and isinstance(res_old.get("data"), list) else []
        old_data = old_list[0] if old_list and isinstance(old_list[0], dict) else None
        if old_data is None:
            raise ValueError(f"Setting '{key}' not found")

        old_value = old_data.get("value")

        # 2. Update
        update_data = {"value": str(new_value), "updated_at": "now()"}
        if description:
            update_data["description"] = description

        query_upd = self.supabase_client.table("archon_settings").update(update_data).eq("key", key) # 合法
        success_upd, res_upd = await self.execute_query_async(query_upd, f"Failed to update setting '{key}'", require_data=True)
        upd_list = res_upd.get("data") if success_upd and isinstance(res_upd.get("data"), list) else []
        upd_item = upd_list[0] if upd_list and isinstance(upd_list[0], dict) else None
        if upd_item is None:
            raise ValueError(f"Setting '{key}' not found")

        # 3. Audit
        try:
            audit_payload: DocumentVersionDTO = {
                "document_id": f"setting:{key}",
                "created_by": user_name,
                "change_type": "UPDATE",
                "field_name": "system_setting",
                "version_number": 1,
                "change_summary": f"System setting '{key}' updated by {user_name}",
                "content": {
                    "setting_key": key,
                    "old_value": old_value,
                    "new_value": str(new_value),
                },
            }
            await self.execute_query_async(self.supabase_client.table("archon_document_versions").insert(audit_payload), "Audit log failed", require_data=False) # 合法
        except Exception:
            pass

        return cast(SystemSettingDTO, upd_item)

system_service = SystemService()
