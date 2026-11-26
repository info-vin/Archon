"""
Phase 5.15 Stage 2 (P2) Tests:
1. Unified Agent Card & A2A Direct Handoff (zero SupervisorNode / 3.6-flash bounce)
2. WorkflowEngine Checkpoint Persistence & Resume
3. Telegram Bidirectional Webhook Security (403 fail-closed, chat_id whitelist, dedup, /task, inline approval)
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.agents.approval_manager import ApprovalRequestDTO
from src.agents.checkpoint_manager import CheckpointDTO
from src.agents.workflow.a2a_handoff import (
    DEFAULT_AGENT_CARDS,
    parse_handoff_directive,
    resolve_direct_handoff,
)
from src.agents.workflow.engine import WorkflowEngine
from src.agents.workflow.state import SharedState
from src.server.api_routes.telegram_webhook_api import router as telegram_webhook_router
from src.server.schemas.settings import NotificationConfig
from src.server.services.shared_constants import AgentUUIDs
from src.server.services.system.telegram_bot_gateway import TelegramBotGateway


class _FakeLLMResult:
    def __init__(self, output: str) -> None:
        self.output = output
        self.data = output


def test_parse_and_resolve_a2a_handoff_rules() -> None:
    cleaned, target, reason = parse_handoff_directive(
        "已查出 Gemini 3.8 資訊。\n[HANDOFF: marketbot | 交由 MarketBot 撰寫草稿]"
    )
    assert cleaned == "已查出 Gemini 3.8 資訊。"
    assert target == "marketbot"
    assert reason == "交由 MarketBot 撰寫草稿"

    state = SharedState(step_count=1, max_steps=5)
    # Allowed hop
    assert resolve_direct_handoff("librarian", "marketbot", reason, state) == "marketbot"
    assert len(state.handoff_history) == 1
    assert state.step_count == 2

    # Blocked self-loop
    assert resolve_direct_handoff("librarian", "librarian", "loop", state) == "supervisor"

    # Blocked unauthorized target
    assert resolve_direct_handoff("summary", "devbot", "unauthorized", state) == "supervisor"

    # Circuit breaker at max_steps
    state.step_count = state.max_steps
    assert resolve_direct_handoff("librarian", "marketbot", "too many hops", state) == "end"

    # SSOT UUIDs on AgentCard
    assert DEFAULT_AGENT_CARDS["supervisor"].agent_uuid == AgentUUIDs.SUPERVISOR
    assert DEFAULT_AGENT_CARDS["librarian"].agent_uuid == AgentUUIDs.LIBRARIAN


@pytest.mark.asyncio
async def test_a2a_direct_handoff_bypasses_supervisor() -> None:
    """Librarian -> MarketBot -> end directly, with 0 calls to SupervisorNode."""
    fake_outputs = iter(
        [
            _FakeLLMResult("RAG 事實整理完成 [HANDOFF: marketbot | 進入草稿撰寫]"),
            _FakeLLMResult("部落格草稿完成 [HANDOFF: end | 任務完成]"),
        ]
    )

    async def _fake_run(*args, **kwargs):
        return next(fake_outputs)

    fake_checkpoint_mgr = MagicMock()
    fake_checkpoint_mgr.save_checkpoint = AsyncMock(return_value="cp-001")

    with (
        patch("src.agents.workflow.nodes._run_agent_with_retry", side_effect=_fake_run),
        patch("src.agents.workflow.nodes.SupervisorNode.run", new_callable=AsyncMock) as mock_sup,
        patch("src.agents.rag_agent.RagAgent") as mock_rag_cls,
    ):
        mock_rag_cls.return_value = SimpleNamespace(_agent=MagicMock())
        engine = WorkflowEngine()
        res = await engine.run_workflow(
            "請查資料並寫草稿",
            conversation_id="conv-a2a-1",
            start_agent="librarian",
            checkpoint_mgr=fake_checkpoint_mgr,
        )

    assert res["success"] is True
    assert mock_sup.await_count == 0
    assert len(res["handoff_history"]) == 2
    assert res["handoff_history"][0]["from"] == "librarian"
    assert res["handoff_history"][0]["to"] == "marketbot"
    assert res["handoff_history"][1]["to"] == "end"
    assert "部落格草稿完成" in str(res["final_result"])
    fake_checkpoint_mgr.save_checkpoint.assert_awaited_once()


@pytest.mark.asyncio
async def test_workflow_resume_from_checkpoint() -> None:
    """Restores SharedState from saved checkpoint and completes from saved agent_role."""
    saved_state = SharedState(
        messages=[
            {"role": "user", "content": "寫一篇新聞分析"},
            {"role": "librarian", "content": "已收集 3 筆來源"},
        ],
        step_count=2,
        conversation_id="conv-resume-1",
        status="WAITING_APPROVAL",
    )
    stored_dto = CheckpointDTO(
        id="cp-99",
        conversation_id="conv-resume-1",
        step_index=2,
        agent_role="marketbot",
        status="RUNNING",
        state_snapshot=saved_state.model_dump(),
    )

    fake_checkpoint_mgr = MagicMock()
    fake_checkpoint_mgr.load_latest_checkpoint = AsyncMock(return_value=stored_dto)
    fake_checkpoint_mgr.save_checkpoint = AsyncMock(return_value="cp-100")

    async def _fake_run(*args, **kwargs):
        return _FakeLLMResult("續跑完成草稿 [HANDOFF: end | done]")

    with patch("src.agents.workflow.nodes._run_agent_with_retry", side_effect=_fake_run):
        engine = WorkflowEngine()
        res = await engine.resume_from_checkpoint("conv-resume-1", checkpoint_mgr=fake_checkpoint_mgr)

    assert res["success"] is True
    assert "續跑完成草稿" in str(res["final_result"])
    fake_checkpoint_mgr.load_latest_checkpoint.assert_awaited_once_with("conv-resume-1")
    fake_checkpoint_mgr.save_checkpoint.assert_awaited_once()


def test_telegram_webhook_security_and_commands() -> None:
    """Verifies fail-closed 403 secret check, chat_id whitelist, dedup, and @agent routing."""
    app = FastAPI()
    app.include_router(telegram_webhook_router)
    client = TestClient(app)

    cfg = NotificationConfig.model_validate(
        {
            "TELEGRAM_TOKEN": "12345:fake-token",
            "TELEGRAM_TO": "10001",
            "TELEGRAM_WEBHOOK_SECRET": "top-secret-token",
        }
    )

    gateway = TelegramBotGateway()

    with (
        patch("src.server.api_routes.telegram_webhook_api.telegram_bot_gateway", gateway),
        patch.object(gateway, "get_config", new=AsyncMock(return_value=cfg)),
        patch.object(gateway, "_post_telegram_api", new=AsyncMock(return_value={"ok": True})),
        patch.object(gateway, "_create_inbound_task", new=AsyncMock(return_value="task-abc-123")) as mock_create,
        patch.object(gateway, "_dispatch_inbound_task") as mock_dispatch,
    ):
        # 1. Missing secret -> 403
        resp_no_secret = client.post("/api/telegram/webhook", json={"update_id": 1})
        assert resp_no_secret.status_code == 403

        # 2. Wrong secret -> 403
        resp_bad_secret = client.post(
            "/api/telegram/webhook",
            headers={"X-Telegram-Bot-Api-Secret-Token": "wrong"},
            json={"update_id": 1},
        )
        assert resp_bad_secret.status_code == 403

        # 3. Unauthorized chat_id -> rejected without creating task
        resp_unauth = client.post(
            "/api/telegram/webhook",
            headers={"X-Telegram-Bot-Api-Secret-Token": "top-secret-token"},
            json={"update_id": 2, "message": {"chat": {"id": 99999}, "text": "/task hack"}},
        )
        assert resp_unauth.status_code == 200
        assert resp_unauth.json()["status"] == "unauthorized"
        assert mock_create.await_count == 0

        # 4. Authorized @librarian command -> creates task assigned to Librarian SSOT UUID
        resp_ok = client.post(
            "/api/telegram/webhook",
            headers={"X-Telegram-Bot-Api-Secret-Token": "top-secret-token"},
            json={"update_id": 3, "message": {"chat": {"id": 10001}, "text": "@librarian 查詢最新 RAG 規範"}},
        )
        assert resp_ok.status_code == 200
        body = resp_ok.json()
        assert body["status"] == "processed"
        assert body["detail"]["assignee_id"] == AgentUUIDs.LIBRARIAN
        assert body["detail"]["dispatched"] is True
        assert mock_create.await_count == 1
        mock_dispatch.assert_called_once_with("task-abc-123", AgentUUIDs.LIBRARIAN)

        # 5. Duplicate update_id -> idempotent ignore
        resp_dup = client.post(
            "/api/telegram/webhook",
            headers={"X-Telegram-Bot-Api-Secret-Token": "top-secret-token"},
            json={"update_id": 3, "message": {"chat": {"id": 10001}, "text": "@librarian 查詢最新 RAG 規範"}},
        )
        assert resp_dup.status_code == 200
        assert resp_dup.json()["status"] == "duplicate_ignored"
        assert mock_create.await_count == 1


@pytest.mark.asyncio
async def test_telegram_inline_approval_resumes_checkpoint() -> None:
    """Clicking approve:<id> in Telegram updates approval and resumes workflow checkpoint."""
    cfg = NotificationConfig.model_validate(
        {
            "TELEGRAM_TOKEN": "12345:fake-token",
            "TELEGRAM_TO": "10001",
            "TELEGRAM_WEBHOOK_SECRET": "top-secret-token",
        }
    )
    gateway = TelegramBotGateway()

    approved_dto = ApprovalRequestDTO(
        approval_id="appr-777",
        conversation_id="conv-hitl-777",
        checkpoint_id="cp-777",
        tool_name="propose_code_fix",
        tool_args={"file_path": "a.py"},
        status="APPROVED",
    )
    fake_approval_mgr = MagicMock()
    fake_approval_mgr.review_approval = AsyncMock(return_value=approved_dto)

    fake_engine = MagicMock()
    fake_engine.resume_from_checkpoint = AsyncMock(return_value={"success": True})

    with patch.object(gateway, "_post_telegram_api", new=AsyncMock(return_value={"ok": True})) as mock_api:
        res = await gateway.handle_update(
            {
                "update_id": 42,
                "callback_query": {
                    "id": "cbq-1",
                    "data": "approve:appr-777",
                    "message": {"chat": {"id": 10001}},
                },
            },
            config=cfg,
            approval_mgr=fake_approval_mgr,
            workflow_engine=fake_engine,
        )

    assert res["status"] == "processed"
    assert res["action"] == "approve"
    assert res["resumed"] is True
    fake_approval_mgr.review_approval.assert_awaited_once()
    fake_engine.resume_from_checkpoint.assert_awaited_once_with("conv-hitl-777")
    assert mock_api.await_count == 2  # answerCallbackQuery + sendMessage

    # Adversarial reverse check: expired/non-existent approval must NOT crash with 500
    fake_approval_mgr.review_approval = AsyncMock(side_effect=ValueError("Approval request ghost not found"))
    with patch.object(gateway, "_post_telegram_api", new=AsyncMock(return_value={"ok": True})) as mock_api_ghost:
        res_ghost = await gateway.handle_update(
            {
                "update_id": 43,
                "callback_query": {
                    "id": "cbq-ghost",
                    "data": "approve:00000000-0000-0000-0000-000000000000",
                    "message": {"chat": {"id": 10001}},
                },
            },
            config=cfg,
            approval_mgr=fake_approval_mgr,
            workflow_engine=fake_engine,
        )
    assert res_ghost["status"] == "not_found"
    assert mock_api_ghost.await_count == 1


@pytest.mark.asyncio
async def test_telegram_gateway_proxy_routing_and_completion_notify() -> None:
    """Verifies proxy routing for sendMessage/answerCallbackQuery/getUpdates and [Telegram] task callback."""
    cfg = NotificationConfig.model_validate(
        {
            "TELEGRAM_TOKEN": "12345:fake-token",
            "TELEGRAM_TO": "10001",
            "TELEGRAM_PROXY_URL": "https://proxy.example.com/api/telegram",
        }
    )
    gateway = TelegramBotGateway()
    captured: list[tuple[str, dict]] = []

    class _FakeResp:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"ok": True, "result": {"reply_markup": {"inline_keyboard": []}}}

    class _FakeAsyncClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url: str, json: dict):
            captured.append((url, json))
            return _FakeResp()

    with patch("src.server.services.system.telegram_bot_gateway.httpx.AsyncClient", _FakeAsyncClient):
        ok_card = await gateway.send_approval_card("appr-1", "發佈草稿", "摘要", config=cfg)
        assert ok_card is True
        await gateway._post_telegram_api("answerCallbackQuery", {"callback_query_id": "cb1"}, cfg)
        await gateway._post_telegram_api("getUpdates", {"offset": 10}, cfg)
        assert await gateway.notify_task_completion("tid-12345678", "Normal Task", "done", config=cfg) is False
        assert (
            await gateway.notify_task_completion("tid-12345678", "[Telegram] 查資料", "完成結果", config=cfg) is True
        )

    assert len(captured) == 4
    assert all(url == "https://proxy.example.com/api/telegram" for url, _ in captured)
    assert captured[0][1]["method"] == "sendMessage"
    assert "reply_markup" in captured[0][1]
    assert captured[1][1]["method"] == "answerCallbackQuery"
    assert captured[2][1]["method"] == "getUpdates"
    assert captured[3][1]["method"] == "sendMessage"


@pytest.mark.asyncio
async def test_workflow_route_wires_production_checkpoint_manager() -> None:
    """Verifies /agents/workflow/run passes AgentCheckpointManager and task_id as conversation_id."""
    from src.agents.models import WorkflowRequest
    from src.agents.routes.workflow import run_workflow

    fake_mgr = MagicMock()
    with (
        patch("src.agents.routes.workflow.AgentCheckpointManager", return_value=fake_mgr),
        patch("src.agents.routes.workflow.WorkflowEngine.run_workflow", new_callable=AsyncMock) as mock_run,
    ):
        mock_run.return_value = {"success": True, "final_result": "OK", "step_count": 1, "messages": []}
        resp = await run_workflow(WorkflowRequest(prompt="test", context={"task_type": "general", "task_id": "task-42"}))

    assert resp.success is True
    mock_run.assert_awaited_once_with(
        "test",
        task_type="general",
        conversation_id="task-42",
        checkpoint_mgr=fake_mgr,
    )
