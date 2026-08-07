import time
from typing import Any, cast

from supabase import Client
from src.server.repositories.base_repository import BaseRepository

class CredentialRepository(BaseRepository):
    """
    Repository handling raw database CRUD operations for the archon_settings table.
    Decoupled from cache and business rules of CredentialManager.
    """

    def __init__(self, supabase_client: Client) -> None:
        super().__init__(supabase_client)

    def fetch_all(self) -> list[dict[str, Any]]:
        """Fetch all credentials from database."""
        for attempt in range(2):
            try:
                success, res = self.execute_query(
                    self.supabase_client.table("archon_settings").select("*"),
                    "Fetch all credentials"
                )
                if success and res.get("data") is not None:
                    return cast(list[dict[str, Any]], res["data"])
                return []
            except Exception as e:
                if attempt == 0 and ("ConnectionTerminated" in str(e) or "RemoteProtocolError" in str(e)):
                    time.sleep(0.5)
                    continue
                raise
        return []

    def fetch_by_category(self, category: str) -> list[dict[str, Any]]:
        """Fetch all credentials for a specific category."""
        for attempt in range(2):
            try:
                success, res = self.execute_query(
                    self.supabase_client.table("archon_settings").select("*").eq("category", category),
                    f"Fetch credentials for category {category}"
                )
                if success and res.get("data") is not None:
                    return cast(list[dict[str, Any]], res["data"])
                return []
            except Exception as e:
                if attempt == 0 and ("ConnectionTerminated" in str(e) or "RemoteProtocolError" in str(e)):
                    time.sleep(0.5)
                    continue
                raise
        return []

    def fetch_non_system_protected(self) -> list[dict[str, Any]]:
        """Fetch non-system-protected credentials (primarily for Admin UI)."""
        success, res = self.execute_query(
            self.supabase_client.table("archon_settings").select("*").eq("is_system_protected", False),
            "Fetch non-system-protected credentials"
        )
        if not success:
            # Fallback if is_system_protected column does not exist yet in target database schema
            success, res = self.execute_query(
                self.supabase_client.table("archon_settings").select("*"),
                "Fetch all credentials fallback"
            )
        return cast(list[dict[str, Any]], res.get("data", [])) if success and res.get("data") is not None else []

    def upsert(self, data: dict[str, Any]) -> None:
        """Upsert a credential into the database."""
        self.execute_query(
            self.supabase_client.table("archon_settings").upsert(data, on_conflict="key"),
            "Upsert credential"
        )

    def delete(self, key: str) -> None:
        """Delete a credential from the database by key."""
        self.execute_query(
            self.supabase_client.table("archon_settings").delete().eq("key", key),
            "Delete credential",
            require_data=False
        )
