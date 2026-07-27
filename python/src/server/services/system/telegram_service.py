import os

import httpx

from src.server.config.logfire_config import get_logger

logger = get_logger(__name__)

class TelegramService:
    def __init__(self) -> None:
        # We don't read os.getenv here to avoid module-load time evaluation gaps (dotenv might load later).
        pass

    @property
    def bot_token(self):
        return os.getenv("TELEGRAM_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")

    @property
    def chat_id(self):
        return os.getenv("TELEGRAM_TO") or os.getenv("TELEGRAM_CHAT_ID")

    @property
    def api_url(self):
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
