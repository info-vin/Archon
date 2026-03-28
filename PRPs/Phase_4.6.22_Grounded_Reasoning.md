# Phase 4.6.22 實作計畫 (Implementation Plan) - Grounded Reasoning & Parameter Cleanup

> **目標 (Goal)**: 
> 1. **移除最後的模擬分支**：將 `AgentService` 中的 `command` 參數徹底移除，終結「手動注入指令」的非自然行為。
> 2. **落地上下文推理**：將任務的 `description` 納入 LLM 的思考上下文，讓 Agent 透過閱讀任務細節自主決定呼叫工具。
> 3. **對齊測試介面**：修改 `test_api.py`，將測試指令轉化為任務描述，實現「從入口即開始推理」。

## 1. 現狀分析與查證 (Research Findings)

| 組件 | 現狀 (Status Quo) | 存在問題 |
| :--- | :--- | :--- |
| **`AgentService`** | `run_agent_task` 帶有 `command` 參數，並在 `_run_general_agent_task` 中手動插入 User Message。 | **非自然推理**：這是一種「作弊」行為，Agent 不是因為理解任務而動，而是被強迫呼叫工具。 |
| **`Test API`** | `trigger-agent-task` 直接傳遞指令字串。 | **耦合過深**：測試介面與底層非標準路徑耦合。 |
| **上下文缺失** | LLM 目前只看得到 Task `title`，看不到 `description`。 | **資訊斷層**：導致 Agent 無法理解複雜任務背景。 |

## 2. 實體修改計畫 (Implementation Steps)

### 2.1 修改 `python/src/server/services/agent_service.py`
- [x] **移除參數**：
    - 從 `run_agent_task` 簽名中移除 `command: str | None = None`。
    - 從 `_run_general_agent_task` 簽名中移除 `command`。
- [x] **移除模擬注入**：
    - 刪除 `if command: messages.append(...)` 邏輯區塊。
- [x] **強化上下文**：
    - 修改訊息建構：`{"role": "user", "content": f"Task: {task_data['title']}\nDescription: {task_data.get('description', '')}"}`。

### 2.2 修改 `python/src/server/api_routes/test_api.py`
- [x] **重構觸發邏輯**：
    - 在呼叫 `run_agent_task` 前，若 payload 包含 `command`，則先透過 `task_service` 將該指令附加到任務描述中（例如：`[Command Hint]: {command}`）。
    - 呼叫不帶 `command` 參數的 `run_agent_task`。

### 2.3 更新 `GEMINI.md`
- [x] 將今日目標更新為：完成 Phase 4.6.22 落地推理與參數清掃。

## 3. 物理驗證方式 (Verification)

### 3.1 推理鏈驗證 (Reasoning Verification)
*   **操作**：呼叫 `POST /api/test/trigger-agent-task`，payload 包含 `command: "make lint-be"`。
*   **觀測**：
    1.  [x] 檢查資料庫，確認 Task Description 已被正確更新為包含該指令。
    2.  [x] 檢查 `AgentService` 日誌，確認 LLM 收到的 User Message 包含完整的 Title 與 Description。
    3.  [x] 確認 Agent 自主決定呼叫 `execute_shell_command` 而非被程式碼強迫。

### 3.2 回歸測試 (Regression)
*   [x] 執行 `uv run mypy src/server` 確保參數移除後沒有殘留的呼叫錯誤。
*   [x] 執行 `make test-be` (使用隔離環境) 確保 Librarian 的直接管線路徑（不走 LLM）依然運作正常。
