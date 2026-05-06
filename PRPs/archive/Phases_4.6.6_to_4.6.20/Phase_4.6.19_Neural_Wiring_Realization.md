# Phase 4.6.19: 神經連結實體化 (Neural Wiring Realization)

> **文件狀態**: 🛠️ 執行中 (Physical Implementation Mode) - 2026-03-25
> **目標**: 徹底修復 4.7 遺留的結構性假象。實作 MCP 工具的動態發現機制，確保 Agent 具備物理真實的「感知-意圖-執行」閉環。

---

## 🛠️ 物理落地任務 (Implementation Targets)

### 1. 實作 MCP 動態發現 (Discovery Fix)
*   **內容**: 在 `python/src/agents/mcp_client.py` 中新增 `list_tools()` 接口。
*   **技術細節**: 物理調用 MCP Server 的 `/rpc` 端點，獲取真實工具清單與 Schema。
*   **驗證**: 呼叫 `mcp_client.list_tools()` 必須回傳非空的 JSON 列表。

### 2. 重構 Agent 工具注入 (Logic Fix)
*   **內容**: 修改 `python/src/server/services/agent_service.py`。
*   **技術細節**: 
    - 徹底刪除硬編碼的 `all_mcp_tools` 列表。
    - 改在 `_run_general_agent_task` 啟動時動態請求 `MCPClient`。
*   **驗證**: Agent 的 `tools` 參數與 MCP Server 實體數據 100% 同步。

### 3. 建立物理整合測試 (Sovereignty Fix)
*   **內容**: 撰寫 `python/tests/integration/test_phase46_19_neural_wiring.py`。
*   **驗證**: 物理撥測一次「Agent 觸發工具 -> MCP 執行 -> 結果回填 Context」的完整循環。

---

## 📊 最終物理產出 (Final DoD)
1.  **動態感知**: 任何在 MCP Server 新增的工具，Agent 在下一秒呼叫時能物理感知且正確調用。
2.  **主權驗證**: 整合測試通過，證明「神經連結」不再是硬編碼的幻想。
3.  **無感升級**: 新增 Agent 技能只需調整 MCP Server，無需再修改 `AgentService` 的工具定義。
