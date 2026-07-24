# Phase 5.9.13: Agent 資料庫狀態斷點持久化 (Checkpointing) 與 人工審核 (HITL) 架構實作計畫

> **階段編號**: Phase 5.9.13  
> **當前狀態**: 已完成 / 100% 測試驗證通過 🟢 (Completed & Verified)  
> **目標子系統**: `python/src/agents/` (Agent 引擎), `python/src/server/api_routes/` (API 路由), `migration/` (資料庫遷移)  
> **核心目標**: 為長任務 Agent 引入資料庫層級的狀態斷點持久化 (State Checkpointing)，並針對高風險工具調用建立 Human-in-the-Loop (HITL) 人工審核機制。

---

## 1. 執行摘要與痛點診斷

### 當前系統限制
1. **Agent 記憶體無狀態執行 (缺乏斷點續傳能力)**：
   - Agent 執行狀態 (`state.py`、思考迴圈、步驟索引) 目前完全保存在記憶體中。
   - 若容器 (`archon-agents` 服務埠 `:8052`) 重啟、網路超時或雲端部署更新，正在執行的長任務會徹底遺失，必須從第 0 步重新執行。
2. **與 LLM 模型與 Free Tier 額度的直接關係**：
   - **痛點**：長任務若在第 7 步中斷重跑，必須從第 0 步重新調用 7 次 LLM API。這會重複發送長 Context 文本，**極易瞬間觸發 Google Gemini API Free Tier 的 15 RPM (Requests Per Minute) 限制或 429 Too Many Requests 錯誤**，甚至耗盡每日免費配額 (RPD)。
   - **效益**：引進 Checkpoint 後，Agent 直接載入第 7 步快照並從第 8 步繼續，**完全零重複 API 呼叫，精準保護 Free Tier 免費額度不被浪費**。
3. **高風險操作缺乏人工防線 (缺乏 HITL 人工審核)**：
   - Agent 工具調用（例如：執行程式碼部署、刪除檔案、修改資料庫 Schema）均為自動直接執行。
   - 缺少統一的 `SUSPENDED` (掛起) 狀態與前端 Admin UI 的授權審核機制。

### 提案架構解決方案
- **資料庫層級狀態斷點持久化 (State Checkpointing)**：在每次 Action / Observation 循環後，將步驟快照 (`conversation_id`, `step_index`, `state_snapshot`, `status`) 即時寫入 Supabase 資料庫。
- **HITL 人工審核工作流**：在執行高風險工具前自動暫停 Agent，將狀態切換為 `PENDING_APPROVAL`，透過 SSE 推送通知至前端 (`enduser-ui` / `archon-ui`)，並等待使用者透過 API 執行 `APPROVE` (核准) 或 `REJECT` (駁回)。

---

## 2. 資料庫 Schema 設計 (`migration/0.2.2/33_create_agent_checkpoints_and_approvals.sql`)

```sql
-- 遷移腳本: 33_create_agent_checkpoints_and_approvals.sql

-- 1. Agent 狀態斷點持久化資料表
CREATE TABLE IF NOT EXISTS public.agent_checkpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id TEXT NOT NULL,
    step_index INT NOT NULL,
    agent_role TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('RUNNING', 'PENDING_APPROVAL', 'COMPLETED', 'FAILED', 'CANCELLED')),
    state_snapshot JSONB NOT NULL,
    last_tool_call JSONB DEFAULT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT unq_conv_step UNIQUE(conversation_id, step_index)
);

CREATE INDEX IF NOT EXISTS idx_agent_checkpoints_conv ON public.agent_checkpoints(conversation_id);
CREATE INDEX IF NOT EXISTS idx_agent_checkpoints_status ON public.agent_checkpoints(status);

-- 2. Human-in-the-Loop 人工審核待處理資料表
CREATE TABLE IF NOT EXISTS public.agent_pending_approvals (
    approval_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id TEXT NOT NULL,
    checkpoint_id UUID REFERENCES public.agent_checkpoints(id) ON DELETE CASCADE,
    tool_name TEXT NOT NULL,
    tool_args JSONB NOT NULL,
    risk_level TEXT NOT NULL DEFAULT 'HIGH',
    status TEXT NOT NULL CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED', 'EXPIRED')),
    reviewer_id TEXT DEFAULT NULL,
    review_reason TEXT DEFAULT NULL,
    expires_at TIMESTAMPTZ NOT NULL DEFAULT (timezone('utc'::text, now()) + interval '30 minutes'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_agent_approvals_status ON public.agent_pending_approvals(status);
```

---

## 3. 後端 Agent 引擎架構修改

### A. 狀態管理器增強 (`python/src/agents/state.py` & `checkpoint_manager.py`)
```python
# python/src/agents/checkpoint_manager.py
from dataclasses import dataclass
from typing import Any, Dict, Optional
from src.server.utils import get_supabase_client


@dataclass
class CheckpointDTO:
    conversation_id: str
    step_index: int
    agent_role: str
    status: str
    state_snapshot: Dict[str, Any]
    last_tool_call: Optional[Dict[str, Any]] = None


class AgentCheckpointManager:
    """負責將 Agent 狀態快照寫入與讀取自 Supabase 的管理器。"""

    def __init__(self) -> None:
        self.supabase = get_supabase_client()

    async def save_checkpoint(self, dto: CheckpointDTO) -> str:
        res = (
            self.supabase.table("agent_checkpoints")
            .upsert(
                {
                    "conversation_id": dto.conversation_id,
                    "step_index": dto.step_index,
                    "agent_role": dto.agent_role,
                    "status": dto.status,
                    "state_snapshot": dto.state_snapshot,
                    "last_tool_call": dto.last_tool_call,
                }
            )
            .execute()
        )
        return res.data[0]["id"]

    async def load_latest_checkpoint(
        self, conversation_id: str
    ) -> Optional[CheckpointDTO]:
        res = (
            self.supabase.table("agent_checkpoints")
            .select("*")
            .eq("conversation_id", conversation_id)
            .order("step_index", desc=True)
            .limit(1)
            .execute()
        )
        if not res.data:
            return None
        data = res.data[0]
        return CheckpointDTO(**data)
```

### B. 執行引擎 HITL 人工審核閘門 (`python/src/agents/execution_engine.py`)
```python
# 在 Execution Engine 執行工具迴圈中：
if tool_config.is_sensitive:
    # 1. 儲存狀態快照，將狀態設為 PENDING_APPROVAL
    checkpoint_id = await self.checkpoint_mgr.save_checkpoint(
        CheckpointDTO(
            conversation_id=self.conv_id,
            step_index=self.step_idx,
            agent_role=self.role,
            status="PENDING_APPROVAL",
            state_snapshot=self.state.to_dict(),
            last_tool_call={"name": tool_name, "args": tool_args},
        )
    )
    # 2. 建立人工審核請求紀錄
    await self.approval_mgr.create_approval_request(
        checkpoint_id=checkpoint_id, tool_name=tool_name, tool_args=tool_args
    )
    # 3. 發送 SSE 廣播至前端，並暫停 Agent 執行迴圈
    await sse_manager.broadcast(
        "agent_approval_required",
        {
            "conversation_id": self.conv_id,
            "tool_name": tool_name,
            "args": tool_args,
        },
    )
    return "SUSPENDED_WAITING_FOR_APPROVAL"
```

---

## 4. API 路由端點設計 (`python/src/server/api_routes/agent_chat_api.py`)

新增供 Admin UI 審核與恢復執行的 REST API 端點：

| HTTP 方法 | API 路徑 | 功能說明 |
| :--- | :--- | :--- |
| `GET` | `/api/v1/agents/approvals/pending` | 查詢所有待審核的高風險 Tool Call 清單 |
| `POST` | `/api/v1/agents/approvals/{approval_id}/review` | 核准 (Approve) 或駁回 (Reject) 待處理的工具執行 |
| `POST` | `/api/v1/agents/tasks/{conversation_id}/resume` | 從 Supabase 最新斷點快照無縫恢復 Agent 執行 |

---

## 5. 測試與驗證計畫

1. **自動化單元測試**：
   - `python/tests/test_agent_checkpointing.py`: 測試狀態寫入、讀取與從 Mock Supabase 恢復。
   - `python/tests/test_agent_hitl_approval.py`: 測試狀態轉移 (`RUNNING` -> `PENDING_APPROVAL` -> `APPROVED` -> `COMPLETED`)。
2. **整合驗證**：
   - 執行 `uv run pytest python/tests/` 確保既存 Agent 與服務 100% 通過無退化。
