# Phase 4.8 實作計畫 (Implementation Plan) - Agent Awakening

> **目標 (Goal)**: 
> 1. 移除 `AgentService` 中的 "Simulated" 虛假邏輯，建立真正的 **Agent Registry**。
> 2. 實作 **General Purpose MCP Loop**，讓 MarketBot, Librarian, POBot 能調用 MCP 工具。
> 3. 補齊所有 Agent 的 System Prompts 與工具掛載配置。

## User Review Required
> [!IMPORTANT]
> **Execution Model**: 本階段將任務執行模式從「寫死的 Python 函式」轉移到「由 LLM 決定的 Tool Calling」。這意味著 Agent 的行為將更具靈活性，但也依賴 Prompt 的品質。
> **Task Atomicity**: 每個 Agent 任務目前被設計為單次觸發 (Request-Response)，暫不支持跨多個 Task 的複雜對話狀態持久化（除非透過資料庫）。

## Proposed Changes

### 1. Agent Infrastructure (`python/src/server/services`)
#### [NEW] `agent_registry.py`
- [ ] 定義 `AGENT_CONFIG`：映射 Agent ID 到對應的 Prompt 函式與 MCP 工具清單。

#### [MODIFY] `agent_service.py`
- [ ] **Removal of Mock Logic**: 刪除 `run_agent_task` 中的 `asyncio.sleep(1)` 模擬區塊。
- [ ] **`_run_general_agent_task`**: 實作通用的工具調用迴圈，支援 PydanticAI 風格的 Think-Act 模式。

### 2. Prompt Engineering (`python/src/server/prompts`)
#### [NEW] `rag_prompts.py` (Librarian)
- [ ] 指導 Librarian 如何使用 `perform_rag_query` 檢索知識庫。

#### [MODIFY] `dev_ops_prompts.py` (DevBot)
- [ ] 擴充支援 `generate_logo` (SVG) 的指令與工具定義。

#### [MODIFY] `marketing_prompts.py` & `pm_prompts.py`
- [ ] 結構化現有 Prompt，確保它們與 OpenAI/Gemini 的 Tool Calling 相容。

### 3. Verification & Tests
#### [NEW] `python/tests/integration/services/test_agent_awakening.py`
- [ ] **MarketBot Integration**: 驗證指派任務後是否觸發爬蟲工具。
- [ ] **Librarian Integration**: 驗證是否觸發 RAG 工具。

## 驗收標準 (Acceptance Criteria)
1. **真實執行**: 在 Task Modal 指派任務後，Task Output 必須包含來自 MCP 工具的真實數據（或測試中的 Mock 數據）。
2. **配置驅動**: 新增或修改 Agent 技能只需調整 `agent_registry.py`，無需修改 `AgentService` 核心程式碼。
3. **錯誤隔離**: 某個 Agent 的工具呼叫失敗不應影響主 API 服務的穩定性。

## 實作進度
- [x] **Step 1**: 建立 Agent Registry 與配置。
- [x] **Step 2**: 補齊 Librarian Prompt 與擴充 DevBot。
- [x] **Step 3**: 重構 AgentService 執行邏輯。
- [x] **Step 4**: 整合測試驗證。

