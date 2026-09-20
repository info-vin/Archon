
import httpx

from src.server.config.logfire_config import get_logger
from src.server.schemas.settings import NotificationConfig
from src.server.services.settings_service import SettingsService
from src.server.utils import get_supabase_client

logger = get_logger(__name__)

class TelegramService:
    def __init__(self) -> None:
        pass

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
                    await asyncio.sleep(2)  # 合法

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

                query = sb.table("archon_tasks").insert({
                    "title": "[System] Pending Telegram Alert",
                    "description": text,
                    "status": "todo",
                    "project_id": project_id
                })
                repo.execute_query(query, "Failed to write to archon_tasks")
                logger.info("📦 TelegramService: Successfully persisted failed message to archon_tasks.")
            except Exception as ex:
                logger.error(f"TelegramService: Failed to persist to archon_tasks: {repr(ex)}")

        await asyncio.to_thread(_insert_task)

    async def send_message(self, text: str, parse_mode: str = "Markdown", is_retry: bool = False) -> bool:
        """Sends a message via Telegram Bot API."""
        import asyncio
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
            payload = {
                "bot_token": bot_token,
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode
            }
        else:
            api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode
            }

        max_retries = config.telegram_retries
        for attempt in range(max_retries):
            try:
                # Use SSOT configured timeout to absorb network spikes
                async with httpx.AsyncClient(timeout=config.telegram_timeout) as client:
                    response = await client.post(api_url, json=payload)
                    response.raise_for_status()
                    logger.info("✅ TelegramService: Message sent successfully.")
                    return True
            except httpx.RequestError as e:
                # Catch connection errors, timeouts, etc. Use repr(e) to avoid empty string logs
                err_msg = f"TelegramService: Network error sending message (Attempt {attempt + 1}/{max_retries}): {repr(e)}"
                logger.error(f"❌ {err_msg}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)  # 合法
                else:
                    await self._log_to_db("ERROR", err_msg)
                    if not is_retry:
                        await self._queue_failed_message(text)
            except httpx.HTTPStatusError as e:
                # Catch 400, 401, 404, etc.
                err_msg = f"TelegramService: HTTP error sending message: {repr(e)} - Response: {e.response.text}"
                logger.error(f"❌ {err_msg}")
                await self._log_to_db("ERROR", err_msg)
                # Note: 4xx errors are usually bad requests (e.g. text too long), queuing them will just fail again.
                # However, 5xx errors (Bad Gateway) might be recoverable.
                if e.response.status_code >= 500 and not is_retry:
                    await self._queue_failed_message(text)
                return False
            except Exception as e:
                err_msg = f"TelegramService: Unexpected error sending message: {repr(e)}"
                logger.error(f"❌ {err_msg}")
                await self._log_to_db("ERROR", err_msg)
                return False

        return False

telegram_service = TelegramService()
