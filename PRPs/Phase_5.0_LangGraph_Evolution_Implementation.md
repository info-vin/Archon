# Phase 5.0: Multi-Agent 協作網路與動態 MCP 實作計畫 (Implementation Plan)

> **建立日期**: 2026-05-12
> **狀態**: 執行中 (Implementation)
> **目標**: 解決「AI 之間無法直接協作」與「MCP 工具權限未細分」的痛點。將目前的五大「無狀態單點 Bots」升級為「有狀態的 Supervisor/Worker 協作網路」，並透過邏輯動態掛載實作 MCP 的最小權限原則。

## 1. 實作架構決策 (Architectural Decisions)

基於前期的風險盤點與物理環境驗證，本階段的實作將採取以下「防禦性架構」決策，避免依賴地獄與成本失控：

1.  **純血 PydanticAI 狀態機 (Reject LangGraph)**:
    *   **決策**: 為了避免引入巨大的 LangChain 歷史包袱導致依賴衝突 (Dependency Hell)，我們 **不使用** 原生 `LangGraph` 套件。
    *   **實作**: 參考其 `StateGraph` 的觀念，在 `archon-agents` 中利用原生的 `asyncio` 與 `Pydantic` 實作一個輕量級的**狀態流轉引擎 (State Router)**。
2.  **異質化神經網路 (Heterogeneous Model Topology)**:
    *   **決策**: 嚴格劃分大腦與苦力，拒絕讓高階模型做簡單格式化工作。
    *   **實作**: 
        *   Supervisor (任務分派大腦) 強制綁定 `gemini-3-flash-preview`：負責需要工具調用 (Tool Use) 與深層邏輯判斷的路由工作。
        *   底層 Worker (如 MarketBot, SummaryAgent) 強制降級綁定 `gemini-3.1-flash-lite-preview`：作為「苦力節點 (Worker Node)」，其價格僅為 3 Flash 的一半，且具備超高吞吐量 (約 382 tokens/sec)，專門負責高併發的資料抽取、總結與格式化任務。
3.  **星型群聊架構 (Star-Topology Group Chat)**:
    *   **決策**: 不使用 AutoGen 式的無政府群聊，以防止 Agent 陷入無限客套或偏離主題。
    *   **實作**: 在 pydantic-graph 中實作「主持人中心制」。定義一個共享黑板 (`SharedState`)，所有 Agent 講完話後必須將控制權還給 Supervisor (Manager Node)，由 Manager 決定下一位發言者或終止討論，確保企業級的絕對可控性。
4.  **實體硬化熔斷器 (Physical Circuit Breakers)**:
    *   **決策**: 防禦 LLM 在除錯時的「鬼打牆無限迴圈」，保護 API 額度。
    *   **實作**: 狀態流轉引擎中寫死 `MAX_RECURSION = 3`。超過 3 次自動中斷，並寫入 Supabase `tasks` 表，狀態設為 `Needs Human Review`。
5.  **邏輯拆分式動態 MCP (Logical Dynamic MCP Federation)**:
    *   **決策**: 拒絕將 MCP 拆分為多個 Docker 容器，避免服務發現災難與交易(Transaction)斷層。
    *   **實作**: 在現有單一 `archon-mcp` (Port 8051) 中，實作 **「動態工具暴露 (Dynamic Tool Exposing)」**。Agent 連線時需夾帶身分，MCP 伺服器動態過濾並只回傳該身分有權限存取的 Tool Schema。

---

## 2. 實作里程碑與工作清單 (Execution Milestones)

### Phase 5.1: 邏輯動態 MCP 與 RBAC 整合 (基礎建設)
目標：確保 Agent 取用工具時具有身分邊界，為後續協作打好地基。
- [ ] **任務 5.1.1**: 更新 `agents/mcp_client.py`，在 `ListTools` 請求中加入 `agent_type` 與 `auth_token` 參數。
- [ ] **任務 5.1.2**: 在 `archon-mcp` 端點中，引入 `server.services.rbac_service`，比對請求的 Agent 權限，**動態裁切** Tool Schema (例如：移除 `delete_project` 工具，若呼叫者是 MarketBot)。
- [ ] **任務 5.1.3**: 建立 MCP 權限負面測試 (`tests/integration/test_mcp_dynamic_rbac.py`)，確保越權調用工具會被 403 攔截。

### Phase 5.2: 輕量級 PydanticAI 狀態機實作 (核心引擎)
目標：建立能流轉上下文與呼叫不同 Agent 的中樞神經。
- [ ] **任務 5.2.1**: 定義全域共享狀態 `SharedState(BaseModel)`，包含 `messages` (歷史), `current_assignee`, `artifacts` (共享檔案)。
- [ ] **任務 5.2.2**: 在 `agents/server.py` 新增 `/agents/workflow/run` 端點，作為 Supervisor 網路的唯一入口。
- [ ] **任務 5.2.3**: 實作 `WorkflowEngine` 類別，包含 `_route_next_node()` 函式 (呼叫 gemini-3-flash-preview 判斷下一步交給誰) 以及 `_execute_node()` 函式 (執行底層 Agent)。
- [ ] **任務 5.2.4**: 實作硬體級熔斷機制。在 `WorkflowEngine` 中加入 `step_count` 計數器，當 `step_count > 3` 時觸發 `HumanFallbackException`。

### Phase 5.3: Charlie Supervisor 概念驗證 (實體驗證)
目標：透過具體的「市場分析與入庫」劇本，驗證協作網路的真實可行性。
- [ ] **任務 5.3.1**: 將 Charlie 設定為本劇本的 Supervisor 角色。
- [ ] **任務 5.3.2**: 建立測試情境：「查閱最新 AI 模型資訊，並寫成一篇部落格草稿存入」。
- [ ] **任務 5.3.3**: 監控執行日誌，驗證流轉順序必須為：`User -> Charlie(Supervisor) -> Librarian(RAG 搜尋) -> Charlie -> MarketBot(寫草稿) -> Charlie -> POBot(建立 Task/Blog)`。
- [ ] **任務 5.3.4**: 驗證 Token 成本。查核資料庫紀錄，確保僅有 Charlie 節點耗用 `gemini-3-flash-preview` 額度，其餘節點耗用 `gemini-3.1-flash-lite-preview` 額度。

### Phase 5.4: 核心架構減重與技術債清理 (Architecture Slimming)
目標：消除 Phase 5.1 盤點時發現的 3 個超過 400 行的「上帝類別 (God Class)」檔案，降低維護複雜度。
- [ ] **任務 5.4.1 (MCP Server)**: 重構 `mcp_server.py` (491行)。將龐大的 `MCP_INSTRUCTIONS` 字串抽離至獨立的 Markdown 或設定檔；將 RPC Bridge 與 Tool Registration 邏輯拆分至 `mcp_server/router.py`。
- [ ] **任務 5.4.2 (Document Logic)**: 重構 `document/logic.py` (418行)。將各種文件 (Feature Plan, ERD, PRD) 的 Markdown 模板產生邏輯抽離至 `document/templates/` 目錄。
- [ ] **任務 5.4.3 (RAG Agent)**: 重構 `rag_agent.py` (408行)。將 Pydantic 工具 Schema 定義與搜尋邏輯分離，使其專注於 Agent 狀態流轉。
- [ ] **任務 5.4.4 (Token Logging Fix)**: 修復 Phase 5.3 驗證時發現的 Token 紀錄逃逸問題。在 `workflow_engine.py` 每次完成 Graph 節點執行或結束 Workflow 時，抽取出 `usage` 數據並透過內部 API 寫回 Supabase 的 `token_usage` 表。
- [ ] **任務 5.4.5 (Global Model SSOT Hardening)**: 徹底根除 `agents` 服務中任何形式的模型名稱硬編碼。移除 `os.getenv` 中的字串回退 (Fallback)，強制僅從 `archon_settings` (透過 `AGENT_CREDENTIALS`) 讀取。若缺失則拋出 `ValueError`。

---

## 3. 測試與驗收標準 (Quality Gates)

實作本階段時，必須嚴格遵守以下公證標準：
1. **SSOT 不退讓**: 任何新增加的模型名稱，**絕對**只能透過 `fetch_credentials_from_server` 從 `archon_settings` 取得，嚴禁在 `WorkflowEngine` 中寫死字串。
2. **斷線自癒測試**: 在執行 Phase 5.3 驗證時，必須手動切斷一次 MCP 連線，驗證 `WorkflowEngine` 是否能正確捕捉 Exception，而非讓整個執行緒崩潰消失。
3. **無盡迴圈負面測試**: 故意撰寫一個「永遠無法成功寫入」的 Mock Tool，驗證神經網路是否會在嘗試 3 次後精準觸發熔斷並中止執行。