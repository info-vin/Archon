"""
Phase 5.15 Stage 2 (P2): Bidirectional Telegram Bot Gateway.

Handles inbound Telegram commands (/task, /status, @agent), inline approval
callbacks (approve:<id>, reject:<id>), idempotent update_id deduplication,
strict chat_id allowlisting, and optional getUpdates wake-up catch-up for HF Space.
"""

from __future__ import annotations

import asyncio
import hmac
from collections import deque
from enum import StrEnum
from typing import Any

import httpx

from src.agents.approval_manager import AgentApprovalManager
from src.agents.workflow import WorkflowEngine
from src.server.config.logfire_config import get_logger
from src.server.repositories.base_repository import BaseRepository
from src.server.schemas.settings import NotificationConfig
from src.server.services.scheduler.utils import get_default_project_id
from src.server.services.settings_service import SettingsService
from src.server.services.shared_constants import AgentNames, AgentUUIDs
from src.server.utils import get_supabase_client

logger = get_logger(__name__)

_LAST_UPDATE_SETTING_KEY = "TELEGRAM_LAST_UPDATE_ID"


class TelegramApprovalAction(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"

_MENTION_AGENT_MAP: dict[str, tuple[str, str]] = {
    "@supervisor": (AgentUUIDs.SUPERVISOR, AgentNames.SUPERVISOR),
    "@librarian": (AgentUUIDs.LIBRARIAN, AgentNames.LIBRARIAN),
    "@marketbot": (AgentUUIDs.MARKET_BOT, AgentNames.MARKET_BOT),
    "@devbot": (AgentUUIDs.DEV_BOT, AgentNames.DEV_BOT),
    "@pobot": (AgentUUIDs.PO_BOT, AgentNames.PO_BOT),
}


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
        if not config.telegram_token:
            return {"ok": False, "error": "Missing TELEGRAM_TOKEN"}
        base_url = config.telegram_api_base_url.rstrip("/")
        url = f"{base_url}/bot{config.telegram_token}/{method}"
        try:
            async with httpx.AsyncClient(timeout=config.telegram_timeout) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data if isinstance(data, dict) else {"ok": True}
        except Exception as e:
            logger.error(f"TelegramBotGateway: API call '{method}' failed: {e}")
            return {"ok": False, "error": str(e)}

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
            return await self._handle_callback_query(
                update["callback_query"], cfg, approval_mgr=approval_mgr, workflow_engine=workflow_engine
            )

        if "message" in update and isinstance(update["message"], dict):
            return await self._handle_message(update["message"], cfg, approval_mgr=approval_mgr)

        return {"status": "ignored", "reason": "unsupported_update_type"}

    async def _handle_callback_query(
        self,
        callback: dict[str, Any],
        config: NotificationConfig,
        approval_mgr: AgentApprovalManager | None = None,
        workflow_engine: WorkflowEngine | None = None,
    ) -> dict[str, Any]:
        chat_id = callback.get("message", {}).get("chat", {}).get("id")
        if not self.is_chat_allowed(chat_id, config):
            logger.warning(f"TelegramBotGateway: Blocked unauthorized callback from chat_id={chat_id}")
            return {"status": "unauthorized"}

        data = str(callback.get("data") or "").strip()
        callback_id = str(callback.get("id") or "")
        if ":" not in data:
            return {"status": "ignored", "reason": "invalid_callback_data"}

        action_raw, approval_id = data.split(":", 1)
        try:
            action = TelegramApprovalAction(action_raw)
        except ValueError:
            return {"status": "ignored", "reason": "unknown_action"}
        if not approval_id:
            return {"status": "ignored", "reason": "missing_approval_id"}

        mgr = approval_mgr or AgentApprovalManager()
        approved = action == TelegramApprovalAction.APPROVE
        dto = await mgr.review_approval(
            approval_id=approval_id,
            approved=approved,
            reviewer_id=f"telegram:{chat_id}",
            reason="Approved via Telegram" if approved else "Rejected via Telegram",
        )

        resumed = False
        if approved and dto.conversation_id:
            engine = workflow_engine or WorkflowEngine()
            resume_res = await engine.resume_from_checkpoint(dto.conversation_id)
            resumed = bool(resume_res.get("success"))

        reply_text = (
            f"✅ 已核准 ({approval_id[:8]})" + ("，流程已續跑完成。" if resumed else "，狀態已更新。")
            if approved
            else f"❌ 已退回 ({approval_id[:8]})。"
        )
        if callback_id:
            await self._post_telegram_api(
                "answerCallbackQuery", {"callback_query_id": callback_id, "text": reply_text}, config
            )
        await self._post_telegram_api("sendMessage", {"chat_id": str(chat_id), "text": reply_text}, config)
        return {"status": "processed", "action": action.value, "approval_id": approval_id, "resumed": resumed}

    async def _handle_message(
        self,
        message: dict[str, Any],
        config: NotificationConfig,
        approval_mgr: AgentApprovalManager | None = None,
    ) -> dict[str, Any]:
        chat_id = message.get("chat", {}).get("id")
        if not self.is_chat_allowed(chat_id, config):
            logger.warning(f"TelegramBotGateway: Blocked unauthorized message from chat_id={chat_id}")
            return {"status": "unauthorized"}

        text = str(message.get("text") or "").strip()
        if not text:
            return {"status": "ignored", "reason": "empty_text"}

        if text.startswith("/status"):
            mgr = approval_mgr or AgentApprovalManager()
            pending = await mgr.list_pending_approvals()
            reply = f"📊 Archon 狀態正常\n待審批項目：{len(pending)} 筆"
            await self._post_telegram_api("sendMessage", {"chat_id": str(chat_id), "text": reply}, config)
            return {"status": "processed", "command": "status", "pending_count": len(pending)}

        assignee_id, assignee_name, task_body = self._parse_task_command(text)
        if not task_body:
            return {"status": "ignored", "reason": "not_a_command"}

        task_id = await self._create_inbound_task(task_body, assignee_id, assignee_name)
        reply = f"📥 已建立工單 `{task_id[:8]}` 指派給 {assignee_name}：\n{task_body[:200]}"
        await self._post_telegram_api("sendMessage", {"chat_id": str(chat_id), "text": reply}, config)
        return {"status": "processed", "command": "task", "task_id": task_id, "assignee_id": assignee_id}

    @staticmethod
    def _parse_task_command(text: str) -> tuple[str, str, str]:
        lowered = text.lower()
        for mention, (aid, aname) in _MENTION_AGENT_MAP.items():
            if lowered.startswith(mention):
                return aid, aname, text[len(mention) :].strip()
        if lowered.startswith("/task"):
            return AgentUUIDs.SUPERVISOR, AgentNames.SUPERVISOR, text[5:].strip()
        return AgentUUIDs.SUPERVISOR, AgentNames.SUPERVISOR, ""

    async def _create_inbound_task(self, instruction: str, assignee_id: str, assignee_name: str) -> str:
        def _insert() -> str:
            sb = get_supabase_client()
            repo = BaseRepository(sb)
            project_id = get_default_project_id(sb)
            payload = {
                "project_id": project_id,
                "title": f"[Telegram] {instruction[:80]}",
                "description": instruction,
                "assignee": assignee_name,
                "assignee_id": assignee_id,
                "status": "todo",
            }
            success, res = repo.execute_query(sb.table("archon_tasks").insert(payload), "Create Telegram inbound task")
            if success and res.get("data"):
                return str(res["data"][0]["id"])
            raise RuntimeError("Failed to create inbound Telegram task")

        return await asyncio.to_thread(_insert)

    async def poll_missed_updates(self, config: NotificationConfig | None = None) -> int:
        """HF Space wake-up recovery: polls missed updates with persisted offset to prevent replays."""
        cfg = config or await self.get_config()
        if not cfg.telegram_token:
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

        res = await self._post_telegram_api("getUpdates", payload, cfg)
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
                await self.handle_update(upd, config=cfg)
                processed += 1
        if max_seen > 0:
            await asyncio.to_thread(_save_last_update_id, max_seen)
        return processed


telegram_bot_gateway = TelegramBotGateway()
