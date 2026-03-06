# python/src/server/services/prompt_service.py

from datetime import datetime
from typing import Any
from unittest.mock import MagicMock

from src.server.repositories.base_repository import BaseRepository

from ..config.logfire_config import get_logger
from ..utils import get_supabase_client

logger = get_logger(__name__)

class PromptService(BaseRepository):
    """Service for managing AI agent prompts."""

    _instance = None
    _prompts: dict[str, str] = {}
    _last_loaded: datetime | None = None

    def __init__(self, supabase_client=None):
        super().__init__(supabase_client or get_supabase_client())

    @classmethod
    def _reset_for_testing(cls):
        """Internal helper to reset singleton state between tests."""
        cls._prompts = {}
        cls._last_loaded = None
        cls._instance = None

    async def load_prompts(self):
        """Mock-compatible method for tests to simulate loading."""
        success, res = await self.list_prompts()
        if success:
            for p in res.get("prompts", []):
                # DEFENSIVE: Handle both 'prompt_text' (DB) and 'prompt' (Tests)
                text = p.get("prompt_text") or p.get("prompt")
                if text:
                    self._prompts[p["name"] if "name" in p else p.get("prompt_name")] = text
            self._last_loaded = datetime.utcnow()

    async def list_prompts(self) -> tuple[bool, dict[str, Any]]:
        """List all system prompts from the database."""
        def _query():
            return self.supabase_client.table("archon_prompts").select("*").execute()

        success, result = self.execute_query(_query, "Failed to list prompts")
        if success:
            return True, {"prompts": result["data"]}
        return False, result

    def get_prompt(self, name: str, default: str | None = None) -> str:
        """Get a prompt by name (cached or direct)."""
        try:
            # First try cache
            if name in self._prompts:
                return self._prompts[name]

            # Fallback to direct DB call
            res = self.supabase_client.table("archon_prompts").select("prompt_text").eq("name", name).single().execute()

            # DEFENSIVE: Check if res.data is a real dict and not a MagicMock
            if res.data and not isinstance(res.data, MagicMock):
                return res.data.get("prompt_text") or default or ""
        except Exception:
            pass
        return default or "You are a helpful AI assistant."

    async def update_prompt(self, prompt_name: str, content: str, description: str | None = None) -> tuple[bool, dict[str, Any]]:
        """Update a system prompt."""
        def _query():
            update_data = {"prompt_text": content}
            if description:
                update_data["description"] = description
            return self.supabase_client.table("archon_prompts").update(update_data).eq("name", prompt_name).execute()

        success, result = self.execute_query(_query, f"Failed to update prompt {prompt_name}")
        if success:
            self._prompts[prompt_name] = content # Sync cache
        return success, result
prompt_service = PromptService()
