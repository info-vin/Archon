from typing import Any, cast
from ..repositories.base_repository import BaseRepository

class SystemService(BaseRepository):
    def __init__(self):
        super().__init__()

    async def list_connectivity_logs(self, limit: int = 20) -> list[dict[str, Any]]:
        query = self.supabase_client.table("archon_logs").select("*").eq("level", "ALERT").eq("type", "system").order("created_at", desc=True).limit(limit)
        success, res = self.execute_query(query, "Failed to list connectivity logs", require_data=False)
        return cast(list[dict[str, Any]], res.get("data", []) if success else [])

    async def list_system_settings(self, category: str | None = None) -> list[dict[str, Any]]:
        query = self.supabase_client.table("archon_settings").select("*")
        if category:
            query = query.eq("category", category)
        query = query.order("key")
        success, res = self.execute_query(query, "Failed to list system settings", require_data=False)
        return cast(list[dict[str, Any]], res.get("data", []) if success else [])

    async def update_system_setting(self, key: str, new_value: str, description: str | None, user_name: str) -> dict[str, Any]:
        # 1. Fetch old value
        query_old = self.supabase_client.table("archon_settings").select("value, is_system_protected").eq("key", key)
        success_old, res_old = self.execute_query(query_old, f"Setting '{key}' not found", require_data=True)
        if not success_old or not res_old.get("data"):
            raise ValueError(f"Setting '{key}' not found")
        
        old_data = res_old["data"][0]
        old_value = old_data["value"]

        # 2. Update
        update_data = {"value": str(new_value), "updated_at": "now()"}
        if description:
            update_data["description"] = description
            
        query_upd = self.supabase_client.table("archon_settings").update(update_data).eq("key", key)
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
            self.execute_query(self.supabase_client.table("archon_document_versions").insert(audit_payload), "Audit log failed", require_data=False)
        except Exception:
            pass

        return cast(dict[str, Any], res_upd["data"][0])

system_service = SystemService()
