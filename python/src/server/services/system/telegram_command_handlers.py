"""Inbound Telegram command (/task, /status, @agent) and HITL approval callback handlers."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from enum import StrEnum
from typing import Any

from src.agents.approval_manager import AgentApprovalManager
from src.agents.workflow import WorkflowEngine
from src.server.config.logfire_config import get_logger
from src.server.repositories.base_repository import BaseRepository
from src.server.schemas.settings import NotificationConfig
from src.server.services.scheduler.utils import get_default_project_id
from src.server.services.shared_constants import AI_AGENT_ROLES, AgentNames, AgentUUIDs
from src.server.utils import get_supabase_client

logger = get_logger(__name__)


class TelegramApprovalAction(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"


def parse_task_command(text: str) -> tuple[str, str, str]:
    """Parse `/task ...` or `@agent ...` using AI_AGENT_ROLES SSOT."""
    stripped = text.strip()
    lowered = stripped.lower()
    if lowered.startswith("@"):
        mention_token = lowered.split(None, 1)[0][1:]
        for role_name, role_uuid in AI_AGENT_ROLES.items():
            base = role_name.split("(")[0].strip().lower()
            aliases = {base}
            if base.endswith("bot"):
                aliases.add(base[:-3])
            if mention_token in aliases:
                body = stripped[len(mention_token) + 1 :].strip()
                return role_uuid, role_name, body
    if lowered.startswith("/task"):
        return AgentUUIDs.SUPERVISOR, AgentNames.SUPERVISOR, stripped[5:].strip()
    return AgentUUIDs.SUPERVISOR, AgentNames.SUPERVISOR, ""


def dispatch_inbound_task(task_id: str, assignee_id: str) -> None:
    """Trigger background execution via AgentService immediately."""
    from src.server.services.agent_service import agent_service

    async def _run() -> None:
        try:
            await agent_service.run_agent_task(task_id=task_id, agent_id=assignee_id)
        except Exception as e:
            logger.error(f"TelegramBotGateway: Background execution failed for task {task_id}: {e}", exc_info=True)

    asyncio.create_task(_run())


async def create_inbound_task(instruction: str, assignee_id: str, assignee_name: str) -> str:
    """Persist an inbound Telegram task in archon_tasks."""

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


async def handle_callback_query(
    callback: dict[str, Any],
    config: NotificationConfig,
    is_chat_allowed_fn: Callable[[str | int | None, NotificationConfig], bool],
    post_api_fn: Callable[[str, dict[str, Any], NotificationConfig], Awaitable[dict[str, Any]]],
    approval_mgr: AgentApprovalManager | None = None,
    workflow_engine: WorkflowEngine | None = None,
) -> dict[str, Any]:
    """Handle Inline Approve/Reject callback queries and resume checkpointed workflows."""
    chat_id = callback.get("message", {}).get("chat", {}).get("id")
    if not is_chat_allowed_fn(chat_id, config):
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
    try:
        dto = await mgr.review_approval(
            approval_id=approval_id,
            approved=approved,
            reviewer_id=f"telegram:{chat_id}",
            reason="Approved via Telegram" if approved else "Rejected via Telegram",
        )
    except ValueError:
        msg = f"⚠️ 審批單 ({approval_id[:8]}) 不存在或已失效。"
        if callback_id:
            await post_api_fn("answerCallbackQuery", {"callback_query_id": callback_id, "text": msg}, config)
        return {"status": "not_found", "approval_id": approval_id}

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
        await post_api_fn("answerCallbackQuery", {"callback_query_id": callback_id, "text": reply_text}, config)
    await post_api_fn("sendMessage", {"chat_id": str(chat_id), "text": reply_text}, config)
    return {"status": "processed", "action": action.value, "approval_id": approval_id, "resumed": resumed}


async def handle_message(
    message: dict[str, Any],
    config: NotificationConfig,
    is_chat_allowed_fn: Callable[[str | int | None, NotificationConfig], bool],
    post_api_fn: Callable[[str, dict[str, Any], NotificationConfig], Awaitable[dict[str, Any]]],
    approval_mgr: AgentApprovalManager | None = None,
    create_task_fn: Callable[[str, str, str], Awaitable[str]] | None = None,
    dispatch_task_fn: Callable[[str, str], None] | None = None,
) -> dict[str, Any]:
    """Handle inbound `/status`, `/task`, and `@agent` text messages."""
    chat_id = message.get("chat", {}).get("id")
    if not is_chat_allowed_fn(chat_id, config):
        logger.warning(f"TelegramBotGateway: Blocked unauthorized message from chat_id={chat_id}")
        return {"status": "unauthorized"}

    text = str(message.get("text") or "").strip()
    if not text:
        return {"status": "ignored", "reason": "empty_text"}

    if text.startswith("/status"):
        mgr = approval_mgr or AgentApprovalManager()
        pending = await mgr.list_pending_approvals()
        reply = f"📊 Archon 狀態正常\n待審批項目：{len(pending)} 筆"
        send_res = await post_api_fn("sendMessage", {"chat_id": str(chat_id), "text": reply}, config)
        return {
            "status": "processed",
            "command": "status",
            "pending_count": len(pending),
            "reply_sent": bool(send_res.get("ok")),
        }

    assignee_id, assignee_name, task_body = parse_task_command(text)
    if not task_body:
        return {"status": "ignored", "reason": "not_a_command"}

    create_fn = create_task_fn or create_inbound_task
    task_id = await create_fn(task_body, assignee_id, assignee_name)
    dispatch_fn = dispatch_task_fn or dispatch_inbound_task
    dispatch_fn(task_id, assignee_id)
    reply = f"📥 已建立並啟動工單 `{task_id[:8]}` 指派給 {assignee_name}：\n{task_body[:200]}"
    send_res = await post_api_fn("sendMessage", {"chat_id": str(chat_id), "text": reply}, config)
    return {
        "status": "processed",
        "command": "task",
        "task_id": task_id,
        "assignee_id": assignee_id,
        "dispatched": True,
        "reply_sent": bool(send_res.get("ok")),
    }
