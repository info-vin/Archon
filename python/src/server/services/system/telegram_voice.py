"""Voice message dispatch helper for TelegramService (proxy-first with direct multipart fallback)."""

from __future__ import annotations

import asyncio
import base64
from collections.abc import Awaitable, Callable
from typing import Any

import httpx

from ...config.logfire_config import get_logger

logger = get_logger(__name__)


async def dispatch_voice_message(
    *,
    voice_bytes: bytes,
    caption: str | None,
    filename: str,
    parse_mode: str,
    config: Any,
    log_to_db: Callable[[str, str], Awaitable[None]],
    send_text_fallback: Callable[[str, str], Awaitable[bool]],
) -> bool:
    """Send a native Telegram voice bubble (sendVoice) with proxy-first and direct fallback."""
    bot_token = config.telegram_token
    chat_id = config.telegram_chat_id

    if not bot_token or not chat_id:
        msg = "TelegramService: TELEGRAM_TOKEN or TELEGRAM_TO not configured. Skipping voice dispatch."
        logger.warning(msg)
        await log_to_db("ERROR", msg)
        return False

    direct_url = f"https://api.telegram.org/bot{bot_token}/sendVoice"
    proxy_url = config.telegram_proxy_url
    max_retries = config.telegram_retries

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=config.telegram_timeout) as client:
                if proxy_url:
                    try:
                        proxy_payload: dict[str, str] = {
                            "bot_token": bot_token,
                            "chat_id": str(chat_id),
                            "voice_base64": base64.b64encode(voice_bytes).decode("ascii"),
                            "filename": filename,
                        }
                        if caption:
                            proxy_payload["caption"] = caption[:1024]
                        if parse_mode:
                            proxy_payload["parse_mode"] = parse_mode

                        p_resp = await client.post(proxy_url, json=proxy_payload)
                        if p_resp.status_code == 400 and parse_mode:
                            proxy_payload.pop("parse_mode", None)
                            p_resp = await client.post(proxy_url, json=proxy_payload)
                        p_resp.raise_for_status()
                        logger.info(f"🎙️ TelegramService: Voice bubble sent via Proxy ({len(voice_bytes)} bytes).")
                        return True
                    except (httpx.RequestError, httpx.HTTPStatusError) as proxy_err:
                        logger.warning(
                            f"TelegramService: Proxy sendVoice failed ({proxy_err}), falling back to Direct..."
                        )

                form_data: dict[str, str] = {"chat_id": str(chat_id)}
                if caption:
                    form_data["caption"] = caption[:1024]
                    if parse_mode:
                        form_data["parse_mode"] = parse_mode

                resp = await client.post(
                    direct_url,
                    data=form_data,
                    files={"voice": (filename, voice_bytes, "audio/wav")},
                )
                if resp.status_code == 400 and parse_mode:
                    form_data.pop("parse_mode", None)
                    resp = await client.post(
                        direct_url,
                        data=form_data,
                        files={"voice": (filename, voice_bytes, "audio/wav")},
                    )
                resp.raise_for_status()
                logger.info(f"🎙️ TelegramService: Voice bubble sent directly ({len(voice_bytes)} bytes).")
                return True
        except Exception as e:
            logger.warning(
                f"TelegramService: Failed to send voice bubble (Attempt {attempt + 1}/{max_retries}): {repr(e)}"
            )
            if attempt < max_retries - 1:
                await asyncio.sleep(2)  # 合法

    err_msg = "TelegramService: Exhausted retries for send_voice."
    logger.error(f"❌ {err_msg}")
    await log_to_db("ERROR", err_msg)
    if caption:
        logger.info("TelegramService: Falling back to text message for failed voice caption.")
        await send_text_fallback(caption, parse_mode)
    return False
