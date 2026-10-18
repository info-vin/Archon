import re

import httpx

from src.server.config.logfire_config import get_logger
from src.server.schemas.settings import NotificationConfig
from src.server.services.settings_service import SettingsService
from src.server.utils import get_supabase_client

logger = get_logger(__name__)

class TelegramService:
    def __init__(self) -> None:
        pass

    @staticmethod
    def sanitize_markdown_snippet(text: str, max_length: int = 150) -> str:
        """Sanitizes text for safe Markdown parsing and truncates to a snippet."""
        if not text:
            return ""
        text = re.sub(r'http[s]?://\S+', '', text)
        text = re.sub(r'[*_`\[\]()#]', '', text)
        text = ' '.join(text.split())
        if len(text) > max_length:
            return text[:max_length].strip() + "..."
        return text

    async def _log_to_db(self, level: str, message: str) -> None:
        """Writes directly to archon_logs to ensure errors are visible in Admin UI."""
        import asyncio
        def _insert_log() -> None:
            try:
                from src.server.repositories.base_repository import BaseRepository
                sb = get_supabase_client()
                repo = BaseRepository(sb)
                query = sb.table("archon_logs").insert({
                    "source": "system-telegram",
                    "level": level,
                    "message": message[:500]
                })
                repo.execute_query(query, "Failed to write to archon_logs")
            except Exception as ex:
                logger.error(f"TelegramService: Failed to write to archon_logs: {repr(ex)}")

        await asyncio.to_thread(_insert_log)

    async def _get_config_async(self) -> NotificationConfig:
        import asyncio

        from src.server.utils import get_supabase_client

        def _fetch_db_sync() -> dict[str, str]:
            supabase = get_supabase_client()
            settings_service = SettingsService(supabase)
            return settings_service.get_all_settings()

        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Execute sync DB fetch in a separate thread to prevent event loop starvation
                raw_settings = await asyncio.to_thread(_fetch_db_sync)
                return NotificationConfig.model_validate(raw_settings)
            except Exception as e:
                logger.warning(f"TelegramService: Failed to fetch settings from DB (Attempt {attempt + 1}/{max_retries}): {repr(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2) # 合法  # 合法

        await self._log_to_db("ERROR", "TelegramService: Failed to fetch TELEGRAM_TOKEN from Database after 3 retries (Timeout or network drop).")
        return NotificationConfig()


    async def _queue_failed_message(self, text: str) -> None:
        import asyncio
        def _insert_task() -> None:
            try:
                from src.server.repositories.base_repository import BaseRepository
                sb = get_supabase_client()
                repo = BaseRepository(sb)

                # Fetch any project ID
                success, p_res = repo.execute_query(sb.table("archon_projects").select("id").limit(1), "Fetch project")
                if not success or not p_res.get("data"):
                    logger.error("TelegramService: No project found to attach pending task.")
                    return
                project_id = p_res["data"][0]["id"]

                import json
                query = sb.table("archon_tasks").insert({
                    "title": "[System] Pending Telegram Alert",
                    "description": json.dumps({"text": text, "parse_mode": getattr(self, "_current_parse_mode", "Markdown")}),
                    "status": "todo",
                    "project_id": project_id
                })
                repo.execute_query(query, "Failed to write to archon_tasks")
                logger.info("📦 TelegramService: Successfully persisted failed message to archon_tasks.")
            except Exception as ex:
                logger.error(f"TelegramService: Failed to persist to archon_tasks: {repr(ex)}")

        await asyncio.to_thread(_insert_task)

    @staticmethod
    def split_message_chunks(text: str, max_chunk_size: int = 3800) -> list[str]:
        """Splits long text into multiple chunks at line/paragraph boundaries safely.

        Ensures each chunk does not exceed max_chunk_size (default 3800, well within
        Telegram's 4096 limit). Appends pagination markers if split into multiple parts.
        """
        if not text:
            return []
        if len(text) <= max_chunk_size:
            return [text]

        chunks: list[str] = []
        remaining = text

        while remaining:
            if len(remaining) <= max_chunk_size:
                chunks.append(remaining)
                break

            # Find best split point within max_chunk_size:
            # 1. Double newline (paragraph boundary)
            # 2. Single newline (line boundary)
            # 3. Space (word boundary)
            # 4. Hard cut as last resort
            split_idx = remaining.rfind("\n\n", 0, max_chunk_size)
            if split_idx == -1 or split_idx < max_chunk_size // 3:
                split_idx = remaining.rfind("\n", 0, max_chunk_size)
            if split_idx == -1 or split_idx < max_chunk_size // 3:
                split_idx = remaining.rfind(" ", 0, max_chunk_size)
            if split_idx == -1 or split_idx < max_chunk_size // 3:
                split_idx = max_chunk_size

            chunk = remaining[:split_idx].strip()
            if chunk:
                chunks.append(chunk)
            remaining = remaining[split_idx:].lstrip()

        # Add pagination header if multiple chunks
        total = len(chunks)
        if total > 1:
            return [f"📄 [{i + 1}/{total}]\n{chunk}" for i, chunk in enumerate(chunks)]
        return chunks

    async def _send_single_payload(
        self,
        api_url: str,
        payload: dict[str, str],
        config: NotificationConfig,
        original_chunk: str,
        is_retry: bool = False,
    ) -> bool:
        """Sends a single chunk payload with retries and failure persistence."""
        import asyncio

        max_retries = config.telegram_retries
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=config.telegram_timeout) as client:
                    response = await client.post(api_url, json=payload)
                    response.raise_for_status()
                    logger.info("✅ TelegramService: Message chunk sent successfully.")
                    return True
            except httpx.RequestError as e:
                err_msg = (
                    f"TelegramService: Network error sending message (Attempt {attempt + 1}/{max_retries}): {repr(e)}"
                )
                logger.error(f"❌ {err_msg}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)  # 合法
                else:
                    await self._log_to_db("ERROR", err_msg)
                    if not is_retry:
                        await self._queue_failed_message(original_chunk)
            except httpx.HTTPStatusError as e:
                err_msg = f"TelegramService: HTTP error sending message: {repr(e)} - Response: {e.response.text}"
                logger.error(f"❌ {err_msg}")
                await self._log_to_db("ERROR", err_msg)
                # Fallback: If Telegram rejects due to markdown entity parsing, retry as plain text (no parse_mode)
                if e.response.status_code == 400 and payload.get("parse_mode"):
                    logger.warning("⚠️ TelegramService: 400 parse entity error detected, falling back to plain text payload.")
                    plain_payload = {k: v for k, v in payload.items() if k != "parse_mode"}
                    try:
                        async with httpx.AsyncClient(timeout=config.telegram_timeout) as client:
                            resp_fallback = await client.post(api_url, json=plain_payload)
                            resp_fallback.raise_for_status()
                            logger.info("✅ TelegramService: Fallback plain text chunk sent successfully.")
                            return True
                    except Exception as fb_err:
                        logger.error(f"❌ TelegramService: Fallback plain text failed: {fb_err}")

                if e.response.status_code >= 500:
                    if not is_retry:
                        await self._queue_failed_message(original_chunk)
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2)  # 合法
                        continue
                return False
            except Exception as e:
                err_msg = f"TelegramService: Unexpected error sending message: {repr(e)}"
                logger.error(f"❌ {err_msg}")
                await self._log_to_db("ERROR", err_msg)
                return False

        return False

    async def send_message(self, text: str, parse_mode: str = "Markdown", is_retry: bool = False) -> bool:
        """Sends a message via Telegram Bot API with safe chunking and rate spacing."""
        import asyncio

        self._current_parse_mode = parse_mode
        config = await self._get_config_async()
        bot_token = config.telegram_token
        chat_id = config.telegram_chat_id

        if not bot_token or not chat_id:
            msg = "TelegramService: TELEGRAM_TOKEN or TELEGRAM_TO not configured. Skipping alert."
            logger.warning(msg)
            await self._log_to_db("ERROR", msg)
            return False

        proxy_url = config.telegram_proxy_url
        if proxy_url:
            api_url = proxy_url
            base_payload = {
                "bot_token": bot_token,
                "chat_id": chat_id,
                "parse_mode": parse_mode,
            }
        else:
            api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            base_payload = {
                "chat_id": chat_id,
                "parse_mode": parse_mode,
            }

        chunks = self.split_message_chunks(text)
        if not chunks:
            return True

        overall_success = True
        for i, chunk in enumerate(chunks):
            payload = {**base_payload, "text": chunk}
            chunk_success = await self._send_single_payload(
                api_url=api_url,
                payload=payload,
                config=config,
                original_chunk=chunk,
                is_retry=is_retry,
            )
            if not chunk_success:
                overall_success = False
                logger.error(f"❌ TelegramService: Failed sending chunk {i + 1}/{len(chunks)}. Aborting further chunks.")
                break

            # Rate-limiting defense: 0.5s pause between chunks to stay within Telegram limits
            if i < len(chunks) - 1:
                await asyncio.sleep(0.5)  # 合法

        return overall_success


telegram_service = TelegramService()

