
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

    @property
    def bot_token(self) -> str | None:
        return self._get_config().telegram_token

    @property
    def chat_id(self) -> str | None:
        return self._get_config().telegram_chat_id

    @property
    def api_url(self) -> str | None:
        token = self.bot_token
        return f"https://api.telegram.org/bot{token}/sendMessage" if token else None

    async def send_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        """Sends a message via Telegram Bot API."""
        if not self.bot_token or not self.chat_id or not self.api_url:
            logger.warning("TelegramService: TELEGRAM_TOKEN or TELEGRAM_TO not configured. Skipping alert.")
            return False

        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(self.api_url, json=payload)
                response.raise_for_status()
                logger.info("✅ TelegramService: Message sent successfully.")
                return True
        except httpx.HTTPError as e:
            logger.error(f"❌ TelegramService: Failed to send message: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ TelegramService: Unexpected error sending message: {e}")
            return False

telegram_service = TelegramService()
