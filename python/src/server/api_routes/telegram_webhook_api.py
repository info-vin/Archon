"""
Phase 5.15 Stage 2 (P2): Telegram Bidirectional Webhook API.

Thin controller enforcing X-Telegram-Bot-Api-Secret-Token verification and
delegating inbound updates to TelegramBotGateway.
"""

from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from src.server.config.logfire_config import get_logger
from src.server.services.system.telegram_bot_gateway import telegram_bot_gateway

logger = get_logger(__name__)

router = APIRouter(prefix="/api/telegram", tags=["telegram"])


class TelegramWebhookResponse(BaseModel):
    ok: bool
    status: str
    detail: dict[str, Any] | None = None


@router.post("/webhook", response_model=TelegramWebhookResponse)
async def telegram_webhook(
    payload: dict[str, Any],
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> TelegramWebhookResponse:
    """Receives inbound Telegram Bot API webhook updates with fail-closed secret verification."""
    config = await telegram_bot_gateway.get_config()
    if not telegram_bot_gateway.verify_webhook_secret(x_telegram_bot_api_secret_token, config):
        logger.warning("TelegramWebhook: Rejected request with invalid or missing secret token.")
        raise HTTPException(status_code=403, detail="Invalid Telegram webhook secret token")

    result = await telegram_bot_gateway.handle_update(payload, config=config)
    return TelegramWebhookResponse(
        ok=result.get("status") != "unauthorized",
        status=str(result.get("status", "unknown")),
        detail=result,
    )


@router.post("/poll-missed", response_model=TelegramWebhookResponse)
async def telegram_poll_missed(
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> TelegramWebhookResponse:
    """HF Space wake-up catch-up endpoint: polls missed Telegram updates with persisted offset."""
    config = await telegram_bot_gateway.get_config()
    if not telegram_bot_gateway.verify_webhook_secret(x_telegram_bot_api_secret_token, config):
        raise HTTPException(status_code=403, detail="Invalid Telegram webhook secret token")

    processed = await telegram_bot_gateway.poll_missed_updates(config=config)
    return TelegramWebhookResponse(ok=True, status="polled", detail={"processed": processed})
