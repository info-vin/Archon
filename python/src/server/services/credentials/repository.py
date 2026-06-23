from typing import Any, cast

from supabase import Client


class CredentialRepository:
    """
    Repository handling raw database CRUD operations for the archon_settings table.
    Decoupled from cache and business rules of CredentialManager.
    """

    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    def fetch_all(self) -> list[dict[str, Any]]:
        """Fetch all credentials from database."""
        import time
        for attempt in range(2):
            try:
                result = self.supabase.table("archon_settings").select("*").execute()
                return cast(list[dict[str, Any]], result.data)
            except Exception as e:
                if attempt == 0 and ("ConnectionTerminated" in str(e) or "RemoteProtocolError" in str(e)):
                    time.sleep(0.5)
                    continue
                raise
        return []

    def fetch_by_category(self, category: str) -> list[dict[str, Any]]:
        """Fetch all credentials for a specific category."""
        import time
        for attempt in range(2):
            try:
                result = self.supabase.table("archon_settings").select("*").eq("category", category).execute()
                return cast(list[dict[str, Any]], result.data)
            except Exception as e:
                if attempt == 0 and ("ConnectionTerminated" in str(e) or "RemoteProtocolError" in str(e)):
                    time.sleep(0.5)
                    continue
                raise
        return []

    def fetch_non_system_protected(self) -> list[dict[str, Any]]:
        """Fetch non-system-protected credentials (primarily for Admin UI)."""
        try:
            result = self.supabase.table("archon_settings").select("*").eq("is_system_protected", False).execute()
        except Exception:
            # Fallback if is_system_protected column does not exist yet in target database schema
            result = self.supabase.table("archon_settings").select("*").execute()
        return cast(list[dict[str, Any]], result.data)

    def upsert(self, data: dict[str, Any]) -> None:
        """Upsert a credential into the database."""
        self.supabase.table("archon_settings").upsert(data, on_conflict="key").execute()

    def delete(self, key: str) -> None:
        """Delete a credential from the database by key."""
        self.supabase.table("archon_settings").delete().eq("key", key).execute()
