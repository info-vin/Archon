"""Telegram HTTP transport (Vercel Proxy / direct API fallback) and missed-update polling."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from enum import StrEnum
from typing import Any

import httpx

from src.server.config.logfire_config import get_logger
from src.server.schemas.settings import NotificationConfig
from src.server.services.settings_service import SettingsService
from src.server.utils import get_supabase_client

logger = get_logger(__name__)

_LAST_UPDATE_SETTING_KEY = "TELEGRAM_LAST_UPDATE_ID"


class TelegramProxyMethod(StrEnum):
    SEND_MESSAGE = "sendMessage"
    ANSWER_CALLBACK_QUERY = "answerCallbackQuery"
    GET_UPDATES = "getUpdates"


async def post_telegram_api(
    method: str,
    payload: dict[str, Any],
    config: NotificationConfig,
    http_client_cls: Any = httpx.AsyncClient,
) -> dict[str, Any]:
    """Send Telegram Bot API request via Vercel Proxy when configured, falling back to direct API."""
    if not config.telegram_token:
        return {"ok": False, "error": "Missing TELEGRAM_TOKEN"}

    if method in TelegramProxyMethod._value2member_map_ and config.telegram_proxy_url:
        proxy_payload = {"bot_token": config.telegram_token, "method": method, **payload}
        try:
            async with http_client_cls(timeout=config.telegram_timeout) as client:
                resp = await client.post(config.telegram_proxy_url, json=proxy_payload)
                try:
                    data = resp.json()
                except ValueError:
                    data = {}
                status_code = getattr(resp, "status_code", 200)
                if isinstance(status_code, int) and status_code >= 400:
                    logger.warning(
                        f"TelegramBotGateway: Telegram returned HTTP {status_code} via proxy for '{method}': {data}"
                    )
                    return data if isinstance(data, dict) else {"ok": False, "status_code": status_code}
                return data if isinstance(data, dict) else {"ok": True}
        except httpx.RequestError as proxy_err:
            logger.warning(
                f"TelegramBotGateway: Proxy '{method}' unreachable ({proxy_err}), falling back to direct API..."
            )

    base_url = config.telegram_api_base_url.rstrip("/")
    url = f"{base_url}/bot{config.telegram_token}/{method}"
    try:
        async with http_client_cls(timeout=config.telegram_timeout) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data if isinstance(data, dict) else {"ok": True}
    except Exception as e:
        logger.error(f"TelegramBotGateway: API call '{method}' failed: {e}")
        return {"ok": False, "error": str(e)}


async def poll_missed_updates_with_offset(
    config: NotificationConfig,
    post_api_fn: Callable[[str, dict[str, Any], NotificationConfig], Awaitable[dict[str, Any]]],
    handle_update_fn: Callable[[dict[str, Any], NotificationConfig], Awaitable[dict[str, Any]]],
) -> int:
    """HF Space wake-up recovery: polls missed updates with persisted offset to prevent replays."""
    if not config.telegram_token:
        return 0

    def _get_last_offset() -> int:
        try:
            raw = SettingsService(get_supabase_client()).get_setting(_LAST_UPDATE_SETTING_KEY)
            return int(raw) + 1 if raw else 0
        except Exception:
            return 0

    def _save_last_update_id(max_id: int) -> None:
        try:
            SettingsService(get_supabase_client()).set_setting(_LAST_UPDATE_SETTING_KEY, str(max_id))
        except Exception as e:
            logger.warning(f"TelegramBotGateway: Failed to persist {_LAST_UPDATE_SETTING_KEY}: {e}")

    offset = await asyncio.to_thread(_get_last_offset)
    payload: dict[str, Any] = {"timeout": 1, "limit": 20}
    if offset > 0:
        payload["offset"] = offset

    res = await post_api_fn("getUpdates", payload, config)
    updates = res.get("result")
    if not isinstance(updates, list):
        return 0

    processed = 0
    max_seen = 0
    for upd in updates:
        if isinstance(upd, dict):
            uid = upd.get("update_id")
            if isinstance(uid, int) and uid > max_seen:
                max_seen = uid
            await handle_update_fn(upd, config)
            processed += 1

    if max_seen > 0:
        await asyncio.to_thread(_save_last_update_id, max_seen)
    return processed
