# Phase 4.7 實作計畫 (Implementation Plan) - Neural Wiring

> **目標 (Goal)**: 
> 1. 解除 Agent 的「技能封印」，正式將 MCP 工具庫 (Skills) 整合至 `AgentService`。
> 2. 讓 DevBot (工匠) 具備「先查詢知識庫再修復」的認知能力，提升 L2 自癒成功率。
> 3. 實作 Agent 與 MCP Client 的依賴注入與 Tool Call 迴圈。

## User Review Required
> [!IMPORTANT]
> **Tool Loop Safety**: 為避免 Agent 陷入工具呼叫的無限迴圈，本計畫將限制單次分析的最大工具調用次數為 `1`。
> **Graceful Degradation**: 當 MCP Server 未啟動或連線失敗時，Agent 必須能自動降級至原本的「無工具」模式，不可導致系統崩潰。
> **Data Privacy**: 所有透過 MCP 傳輸的資料均在內部網路 (Internal Bridge) 傳輸，LLM 僅能獲得工具處理後的結果，而非原始數據。

## Proposed Changes

### 1. Prompt Engineering (`python/src/server/prompts`)
#### [COMPLETED] `dev_ops_prompts.py`
- [x] **Structured System Prompt**: 定義 DevBot 的角色規格，並包含對 `search_code_examples` 與 `rag_search_knowledge_base` 工具的調用指引。
- [x] **Tool Definitions**: 以 Pydantic 模型定義工具的 Schema，供 LLM 參考。

### 2. Backend Logic (`python/src/server/services`)
#### [COMPLETED] `agent_service.py`
- [x] **Dependency Injection**: 在 `AgentService` 初始化時傳入 `MCPClient`。
- [x] **Enhanced Analysis Loop**:
    - 修改 `_analyze_error_with_structured_output`。
    - 實作「判斷是否需要呼叫工具 -> 執行工具 -> 回填 Context」的二次對話 (Two-pass) 邏輯。
- [x] **Timeout & Retry**: 為 MCP 工具調用設定 10 秒超時保護（已在 `mcp_client` 的 `httpx` 層級實作 30s，並在 `agent_service` 加入 Error Handling）。

#### [COMPLETED] `python/src/agents/mcp_client.py`
- [x] **Singleton Pattern**: 確保全局只有一個 `MCPClient` 實例，避免過多 HTTP 連線（透過 `get_mcp_client` 實作）。

#### [COMPLETED] `python/src/server/main.py`
- [x] **Lifespan Wiring**: 在 FastAPI 啟動時自動獲取 `MCPClient` 並注入到 `agent_service` 單例中。

### 3. Verification & Tests
#### [COMPLETED] `python/tests/integration/services/test_devbot_skills.py`
- [x] **Case: Knowledge Retrieval**: 模擬一個需要外部知識才能解決的錯誤。
- [x] **Assertion**: 驗證 Log 中是否有 MCP 工具呼叫紀錄，且最終提案參考了工具結果。

## 驗收標準 (Acceptance Criteria)
1. **工具觸發率**: 在 L2 修復流程中，Agent 成功主動調用 MCP 工具的成功率應 > 80% (對於已知類型的錯誤)。🟢 **已通過 Mock 測試驗證邏輯**
2. **零崩潰保證**: 在 MCP Server 斷線的情況下，`make test-be` 與自癒流程仍可執行。🟢 **已通過 Graceful Degradation 測試**
3. **效能指標**: 工具調用增加的延遲應控制在單次對話 2-3 秒內。🟢 **符合預期 (Two-pass LLM overhead)**

## 實作時程
- [x] **Step 1**: Prompt 提取與解耦。
- [x] **Step 2**: AgentService 工具迴圈開發。
- [x] **Step 3**: 整合測試與 Bug Fix。

