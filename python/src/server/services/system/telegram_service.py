
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
        def _insert_log():
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

        def _fetch_db_sync():
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

    async def send_message(self, text: str, parse_mode: str = "Markdown") -> bool:
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

        api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode
        }

        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 30.0s timeout to absorb network spikes
                async with httpx.AsyncClient(timeout=30.0) as client:
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
            except httpx.HTTPStatusError as e:
                # Catch 400, 401, 404, etc.
                err_msg = f"TelegramService: HTTP error sending message: {repr(e)} - Response: {e.response.text}"
                logger.error(f"❌ {err_msg}")
                await self._log_to_db("ERROR", err_msg)
                return False
            except Exception as e:
                err_msg = f"TelegramService: Unexpected error sending message: {repr(e)}"
                logger.error(f"❌ {err_msg}")
                await self._log_to_db("ERROR", err_msg)
                return False

        return False

telegram_service = TelegramService()
