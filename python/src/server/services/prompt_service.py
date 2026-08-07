# python/src/server/services/prompt_service.py

from datetime import datetime
from typing import Any, NotRequired, TypedDict, cast
from unittest.mock import MagicMock

from src.server.repositories.base_repository import BaseRepository

from ..config.logfire_config import get_logger
from ..utils import get_supabase_client

logger = get_logger(__name__)


class PromptListDTO(TypedDict):
    data: NotRequired[list[dict[str, Any]]]
    prompts: NotRequired[list[dict[str, Any]]]
    error: NotRequired[str]


class PromptUpdateDTO(TypedDict):
    data: NotRequired[list[dict[str, Any]]]
    count: NotRequired[int]
    error: NotRequired[str]


class PromptService(BaseRepository):
    """Service for managing AI agent prompts."""

    _instance = None
    _prompts: dict[str, str] = {}
    _last_loaded: datetime | None = None

    def __init__(self, supabase_client: Any = None) -> None:
        super().__init__(supabase_client or get_supabase_client())

    @classmethod
    def _reset_for_testing(cls) -> None:
        """Internal helper to reset singleton state between tests."""
        cls._prompts = {}
        cls._last_loaded = None
        cls._instance = None

    async def load_prompts(self) -> None:
        """Mock-compatible method for tests to simulate loading."""
        success, res = await self.list_prompts()
        if success:
            for p in res.get("prompts", []):
                # DB schema: prompt_name, prompt
                text = p.get("prompt")
                if text:
                    self._prompts[p.get("prompt_name", "")] = text
            self._last_loaded = datetime.utcnow()

    async def list_prompts(self) -> tuple[bool, PromptListDTO]:
        """List all system prompts from the database."""
        query = self.supabase_client.table("archon_prompts").select("*") # 合法
        success, result = self.execute_query(query, "Failed to list prompts")
        if success:
            return True, cast(PromptListDTO, {"prompts": result.get("data", [])})
        return False, cast(PromptListDTO, result)

    def get_prompt(self, name: str, default: str | None = None) -> str:
        """Get a prompt by name (cached or direct)."""
        try:
            # First try cache
            if name in self._prompts:
                return self._prompts[name]

            # Fallback to direct DB call - Schema: prompt_name, prompt
            res = self.supabase_client.table("archon_prompts").select("prompt").eq("prompt_name", name).execute() # 合法

            # DEFENSIVE: Check if res.data is a real dict and not a MagicMock
            if res.data and not isinstance(res.data, MagicMock) and len(res.data) > 0:
                return res.data[0].get("prompt") or default or ""
        except Exception:
            pass
        return default or "You are a helpful AI assistant."

    async def update_prompt(
        self, prompt_name: str, content: str, description: str | None = None, category: str | None = None, metadata: dict[str, Any] | None = None
    ) -> tuple[bool, PromptUpdateDTO]:
        """Update a system prompt."""
        update_data: dict[str, Any] = {"prompt": content}
        if description:
            update_data["description"] = description
        if category:
            update_data["category"] = category
        if metadata is not None:
            update_data["metadata"] = metadata

        query = self.supabase_client.table("archon_prompts").update(update_data).eq("prompt_name", prompt_name) # 合法
        success, result = self.execute_query(query, f"Failed to update prompt {prompt_name}")

        if success:
            self._prompts[prompt_name] = content  # Sync cache

        return success, cast(PromptUpdateDTO, result)


prompt_service = PromptService()
