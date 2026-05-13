# Phase 5.0 (5.1-5.3) 物理驗收報告 (Physical Acceptance Report)

> **驗收日期**: 2026-05-12
> **執行者**: Gemini
> **狀態**: 部分完成 (發現斷層)

本報告基於嚴格的物理探針與代碼掃描，比對 `Phase_5.0_LangGraph_Evolution_Implementation.md` 的承諾與當前代碼庫的實際落地狀況。

---

## 🟢 Phase 5.1: 邏輯動態 MCP 與 RBAC 整合

**驗收結果：完全通過 (100% Passed)**

*   **[✓] 任務 5.1.1 (Client 傳遞身分)**: 
    *   **物理證據**: `python/src/agents/mcp_client.py` 第 56 行，在發送 JSON-RPC 時，動態將 `self.agent_type` 寫入 `X-Agent-Type` Header。
*   **[✓] 任務 5.1.2 (Server 動態裁切)**: 
    *   **物理證據**: `python/src/mcp_server/mcp_server.py` 第 280-302 行，成功引入 `server.services.rbac_service.RBACService`，調用 `get_restricted_mcp_tools`，並過濾掉禁止的 Tools。完全消除硬編碼。
*   **[✓] 任務 5.1.3 (負面測試)**: 
    *   **物理證據**: 實體檔案 `python/tests/integration/test_mcp_dynamic_rbac.py` 存在。執行 `pytest` 通過，證明 MarketBot 無法看到也無法調用 `manage_project`。

---

## 🟢 Phase 5.2: 輕量級 PydanticAI 狀態機實作

**驗收結果：完全通過 (100% Passed)**

*   **[✓] 任務 5.2.1 (共享狀態定義)**: 
    *   **物理證據**: `python/src/agents/workflow_engine.py` 第 14 行，定義了 `SharedState(BaseModel)`，包含 messages, current_assignee, artifacts, step_count 等狀態。
*   **[✓] 任務 5.2.2 (端點建立)**: 
    *   **物理證據**: `python/src/agents/server.py` 第 159 行，定義了 `@app.post("/agents/workflow/run")` 端點。
*   **[✓] 任務 5.2.3 (核心引擎與路由)**: 
    *   **物理證據**: `workflow_engine.py` 使用了 `gemini-3-flash-preview` 作為 SupervisorNode 的大腦，並正確宣告 `output_type=SupervisorDecision` 來控制邊界流轉 (Edges)。
*   **[✓] 任務 5.2.4 (實體熔斷器)**: 
    *   **物理證據**: SupervisorNode 內實作了 `if ctx.state.step_count > ctx.state.max_steps:` 的防呆機制，並會回傳 "Circuit Breaker Tripped: Needs Human Review"。

---

## 🔴 Phase 5.3: Charlie Supervisor 概念驗證

**驗收結果：發現斷層 (Gap Detected)**

*   **[✓] 任務 5.3.1 ~ 5.3.3 (劇本與流轉驗證)**: 
    *   **物理證據**: 實體腳本 `python/tests/integration/test_phase53_workflow.py` 已建立。
    *   **執行結果**: 通過。我們成功模擬了 Bob (Marketing) 發起請求，並且在回傳的 `metadata.messages` 中，精準斷言出 `librarian` 與 `marketbot` 都有參與發言，證明星型群聊拓樸 (User -> Charlie -> Librarian -> Charlie -> MarketBot) 在物理上是通的。
*   **[✗] 任務 5.3.4 (驗證 Token 成本資料庫紀錄)**:
    *   **承諾**: 「查核資料庫紀錄，確保僅有 Charlie 節點耗用 `gemini-3-flash-preview` 額度...」
    *   **物理斷層**: 透過探針腳本 `scripts/check_tokens_phase53.py` 查詢 Supabase 的 `token_usage` 表發現，**PydanticAI (archon-agents) 執行 workflow_engine 時，完全沒有將 Token 使用量寫入資料庫！**
    *   **原因**: 目前的 Token 紀錄是由 `archon-server` 內的 `LLMProviderService` 負責寫入的。但在 Phase 5.2 的 `workflow_engine.py` 中，我們讓 PydanticAI 直接透過 `.env` 的金鑰去打 Gemini API，跳過了 Server 的 Token 記錄器。雖然 PydanticAI 的 `AgentRunResult.usage` 有計算 Token，但代碼並未將其持久化到 DB。

---

## 📝 總結與 Next Steps

1.  **Phase 5.1 ~ 5.2 的架構完全成功**，我們確實獲得了一個輕量且具備權限邊界的 Multi-Agent 引擎。
2.  **Phase 5.3 概念驗證暴露出一個系統盲區 (Token 逃逸)**。
3.  **建議行動**: 將此斷層列入接下來的 **Phase 5.4** 技術債清理任務中。我們必須在 `WorkflowEngine` 結束或各個 Node 執行完畢時，將 `run_result.usage` 抽出來，並透過 internal API (如 `POST /internal/stats/token-usage`) 或 MCP 寫回 Supabase，否則未來的 Agentic Workflow 將成為公司 API 費用的黑洞。
