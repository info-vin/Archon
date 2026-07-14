import os

import httpx

from src.server.config.logfire_config import get_logger

logger = get_logger(__name__)

class TelegramService:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage" if self.bot_token else None

    async def send_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        """Sends a message via Telegram Bot API."""
        if not self.bot_token or not self.chat_id or not self.api_url:
            logger.warning("TelegramService: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not configured. Skipping alert.")
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
