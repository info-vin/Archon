
import httpx

from src.server.config.logfire_config import get_logger
from src.server.schemas.settings import NotificationConfig
from src.server.services.settings_service import SettingsService
from src.server.utils import get_supabase_client

logger = get_logger(__name__)

class TelegramService:
    def __init__(self) -> None:
        pass

    def _get_config(self) -> NotificationConfig:
        try:
            supabase = get_supabase_client()
            settings_service = SettingsService(supabase)
            raw_settings = settings_service.get_all_settings()
            return NotificationConfig.model_validate(raw_settings)
        except Exception as e:
            logger.warning(f"TelegramService: Failed to parse NotificationConfig: {e}")
            return NotificationConfig()

    async def send_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        """Sends a message via Telegram Bot API."""
        import asyncio
        config = self._get_config()
        bot_token = config.telegram_token
        chat_id = config.telegram_chat_id

        if not bot_token or not chat_id:
            logger.warning("TelegramService: TELEGRAM_TOKEN or TELEGRAM_TO not configured. Skipping alert.")
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
                logger.error(f"❌ TelegramService: Network error sending message (Attempt {attempt + 1}/{max_retries}): {repr(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)  # 合法
            except httpx.HTTPStatusError as e:
                # Catch 400, 401, 404, etc.
                logger.error(f"❌ TelegramService: HTTP error sending message: {repr(e)} - Response: {e.response.text}")
                return False
            except Exception as e:
                logger.error(f"❌ TelegramService: Unexpected error sending message: {repr(e)}")
                return False

        return False

telegram_service = TelegramService()
