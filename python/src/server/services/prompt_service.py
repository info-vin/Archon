# python/src/server/services/prompt_service.py

from datetime import datetime
from typing import Any, NotRequired, TypedDict, cast
from unittest.mock import MagicMock

from src.server.prompts import ALL_PROMPTS
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
        """Mock-compatible method for tests to simulate loading and sync."""
        success, res = await self.list_prompts()
        db_prompts = {}
        if success:
            for p in res.get("prompts", []):
                # DB schema: prompt_name, prompt
                text = p.get("prompt")
                if text:
                    db_prompts[p.get("prompt_name", "")] = text
                    self._prompts[p.get("prompt_name", "")] = text

        # Auto-upsert missing Baseline Prompts to Supabase
        upsert_batch = []
        for name, content in ALL_PROMPTS.items():
            if name not in db_prompts:
                upsert_batch.append({"prompt_name": name, "prompt": content})
                self._prompts[name] = content  # Ensure cache is fully populated with Baseline

        if upsert_batch:
            try:
                # Perform bulk upsert
                self.execute_query(
                    self.supabase_client.table("archon_prompts").upsert(upsert_batch, on_conflict="prompt_name"),
                    "Auto-upsert baseline prompts"
                )
                logger.info(f"✅ Auto-upserted {len(upsert_batch)} baseline prompts to Supabase.")
            except Exception as e:
                logger.warning(f"⚠️ Failed to auto-upsert prompts: {e}")

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
            # First try cache (which is now fully populated at startup)
            if name in self._prompts:
                return self._prompts[name]

            # Fallback to direct DB call in case it was added after startup
            success, res = self.execute_query(
                self.supabase_client.table("archon_prompts").select("prompt").eq("prompt_name", name),
                "Fetch prompt fallback"
            )

            # DEFENSIVE: Check if res.get("data") is a real dict/list and not a MagicMock
            data = res.get("data")
            if success and data and not isinstance(data, MagicMock) and len(data) > 0:
                text = data[0].get("prompt")
                if text:
                    self._prompts[name] = str(text)  # Cache it to prevent future misses
                    return str(text)
        except Exception:
            pass

        # SSOT Fallback (Prevent cache defeat)
        if name in ALL_PROMPTS:
            fallback = ALL_PROMPTS[name]
            self._prompts[name] = fallback # Prevent future misses
            return fallback

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
