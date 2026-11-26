"""
Phase 5.15 Stage 2 (P2): Bidirectional Telegram Bot Gateway (Facade).

Delegates HTTP/Proxy transport to telegram_proxy_client and command/HITL
handling to telegram_command_handlers while preserving public signatures.
"""

from __future__ import annotations

import asyncio
import hmac
from collections import deque
from typing import Any

import httpx

from src.agents.approval_manager import AgentApprovalManager
from src.agents.workflow import WorkflowEngine
from src.server.config.logfire_config import get_logger
from src.server.schemas.settings import NotificationConfig
from src.server.services.settings_service import SettingsService
from src.server.utils import get_supabase_client

from .telegram_command_handlers import handle_callback_query, handle_message, parse_task_command
from .telegram_proxy_client import poll_missed_updates_with_offset, post_telegram_api

logger = get_logger(__name__)

_TELEGRAM_TASK_PREFIX = "[Telegram]"


class TelegramBotGateway:
    """Bidirectional Telegram command & HITL approval gateway."""

    def __init__(self, max_dedup_ids: int = 500) -> None:
        self._processed_update_ids: deque[int] = deque(maxlen=max_dedup_ids)

    async def get_config(self) -> NotificationConfig:
        def _fetch() -> dict[str, Any]:
            sb = get_supabase_client()
            return SettingsService(sb).get_all_settings()

        try:
            raw = await asyncio.to_thread(_fetch)
            return NotificationConfig.model_validate(raw)
        except Exception as e:
            logger.warning(f"TelegramBotGateway: Failed to load NotificationConfig: {e}")
            return NotificationConfig()

    @staticmethod
    def verify_webhook_secret(header_secret: str | None, config: NotificationConfig) -> bool:
        """Fail-closed verification of X-Telegram-Bot-Api-Secret-Token."""
        expected = (config.telegram_webhook_secret or "").strip()
        if not expected or not header_secret:
            return False
        return hmac.compare_digest(header_secret.strip(), expected)

    @staticmethod
    def is_chat_allowed(chat_id: str | int | None, config: NotificationConfig) -> bool:
        """Checks whether the sender chat_id is in the configured allowlist."""
        if chat_id is None:
            return False
        allowed: set[str] = set()
        if config.telegram_chat_id:
            allowed.add(str(config.telegram_chat_id).strip())
        if config.telegram_allowed_chat_ids:
            for item in config.telegram_allowed_chat_ids.split(","):
                if item.strip():
                    allowed.add(item.strip())
        return str(chat_id).strip() in allowed

    async def _post_telegram_api(
        self, method: str, payload: dict[str, Any], config: NotificationConfig
    ) -> dict[str, Any]:
        # Pass module-level httpx.AsyncClient so unit tests patching telegram_bot_gateway.httpx.AsyncClient work cleanly.
        return await post_telegram_api(method, payload, config, http_client_cls=httpx.AsyncClient)

    async def send_approval_card(
        self,
        approval_id: str,
        title: str,
        summary: str,
        chat_id: str | None = None,
        config: NotificationConfig | None = None,
    ) -> bool:
        """Sends an interactive Telegram approval card with Approve/Reject inline buttons."""
        cfg = config or await self.get_config()
        target_chat = chat_id or cfg.telegram_chat_id
        if not target_chat:
            logger.warning("TelegramBotGateway: No target chat_id configured for approval card.")
            return False

        payload: dict[str, Any] = {
            "chat_id": str(target_chat),
            "text": f"🛡️ *待審批動作*\n*{title}*\n\n{summary[:800]}",
            "parse_mode": "Markdown",
            "reply_markup": {
                "inline_keyboard": [
                    [
                        {"text": "✅ 核准執行", "callback_data": f"approve:{approval_id}"},
                        {"text": "❌ 退回取消", "callback_data": f"reject:{approval_id}"},
                    ]
                ]
            },
        }
        res = await self._post_telegram_api("sendMessage", payload, cfg)
        return bool(res.get("ok"))

    async def handle_update(
        self,
        update: dict[str, Any],
        config: NotificationConfig | None = None,
        approval_mgr: AgentApprovalManager | None = None,
        workflow_engine: WorkflowEngine | None = None,
    ) -> dict[str, Any]:
        """Processes a single Telegram update (message or callback_query) idempotently."""
        update_id = update.get("update_id")
        if isinstance(update_id, int):
            if update_id in self._processed_update_ids:
                return {"status": "duplicate_ignored", "update_id": update_id}
            self._processed_update_ids.append(update_id)

        cfg = config or await self.get_config()

        if "callback_query" in update and isinstance(update["callback_query"], dict):
            return await handle_callback_query(
                update["callback_query"],
                cfg,
                is_chat_allowed_fn=self.is_chat_allowed,
                post_api_fn=self._post_telegram_api,
                approval_mgr=approval_mgr,
                workflow_engine=workflow_engine,
            )

        if "message" in update and isinstance(update["message"], dict):
            return await handle_message(
                update["message"],
                cfg,
                is_chat_allowed_fn=self.is_chat_allowed,
                post_api_fn=self._post_telegram_api,
                approval_mgr=approval_mgr,
                create_task_fn=self._create_inbound_task,
                dispatch_task_fn=self._dispatch_inbound_task,
            )

        return {"status": "ignored", "reason": "unsupported_update_type"}

    async def _create_inbound_task(self, task_body: str, assignee_id: str, assignee_name: str) -> str:
        from .telegram_command_handlers import create_inbound_task

        return await create_inbound_task(task_body, assignee_id, assignee_name)

    @staticmethod
    def _dispatch_inbound_task(task_id: str, assignee_id: str) -> None:
        from .telegram_command_handlers import dispatch_inbound_task

        dispatch_inbound_task(task_id, assignee_id)

    @staticmethod
    def _parse_task_command(text: str) -> tuple[str, str, str]:
        return parse_task_command(text)

    async def poll_missed_updates(self, config: NotificationConfig | None = None) -> int:
        """HF Space wake-up recovery: polls missed updates with persisted offset to prevent replays."""
        cfg = config or await self.get_config()
        return await poll_missed_updates_with_offset(
            cfg,
            post_api_fn=self._post_telegram_api,
            handle_update_fn=lambda upd, c: self.handle_update(upd, config=c),
        )

    async def notify_task_completion(
        self,
        task_id: str,
        task_title: str,
        content: str,
        success: bool = True,
        config: NotificationConfig | None = None,
    ) -> bool:
        """Pushes completion/failure summary back to Telegram for tasks created via Telegram."""
        if not task_title.startswith(_TELEGRAM_TASK_PREFIX):
            return False
        cfg = config or await self.get_config()
        if not cfg.telegram_chat_id:
            return False
        icon = "✅" if success else "❌"
        status_label = "已完成" if success else "執行失敗"
        clean_title = task_title.replace(_TELEGRAM_TASK_PREFIX, "", 1).strip()
        text = f"{icon} 工單 `{task_id[:8]}` {status_label}\n主題：{clean_title[:100]}\n\n{content[:1200]}"
        res = await self._post_telegram_api("sendMessage", {"chat_id": str(cfg.telegram_chat_id), "text": text}, cfg)
        return bool(res.get("ok"))


telegram_bot_gateway = TelegramBotGateway()
