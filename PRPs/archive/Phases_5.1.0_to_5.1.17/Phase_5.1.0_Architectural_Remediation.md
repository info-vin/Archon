# Phase 5.1.0: Architectural Remediation & Scalability Plan

> **Document Status**: 📝 Proposed Plan (2026-05-15)
> **Goal**: 解決 Phase 4.6 至 5.0.2 快速迭代市場所累積的五大核心技術債，將 Archon 從一個「防禦力點滿但擴展性受限」的 MVP 系統，重構為具備高併發、高擴充性、與強型別安全的企業級微服務架構。

## 1. 核心問題與重構目標

本計畫針對以下五大架構痛點進行根除：
1. **控制流耦合 (God Method)**: `agent_service.py` 內部過多的 `if/else` Agent ID 判斷，違反開閉原則。
2. **JSONB 型別失憶 (Type Safety Blindspots)**: 缺乏靜態型別保護，導致編譯期無法抓出資料結構變異。
3. **高昂的測試稅 (High MBT Maintenance)**: XState 與 Playwright 的高度耦合降低了小功能的開發敏捷度。
4. **被免費額度綁架 (Throttling Bottlenecks)**: 物理 `sleep` 阻塞破壞了非同步架構的吞吐量潛力。
5. **狀態撕裂 (State Tearing)**: 前端、後端與資料庫各自維護獨立的狀態機，缺乏單一真實來源 (SSOT)。

---

## 2. 實作里程碑與工作清單 (Execution Milestones)

### Milestone 1: 控制流解耦與策略模式 (Task Routing & Dispatch)
- [x] **1.1 定義 Agent 派發介面**: 在 `python/src/server/services/agents/` 下建立 `AgentDispatcher` 介面與 `BaseAgentStrategy` 抽象類別。
- [x] **1.2 實作具體策略**: 建立 `SupervisorStrategy` (橋接 8052 Port), `LibrarianStrategy` (爬蟲管線), 與 `DefaultLLMStrategy`。
- [x] **1.3 重構主入口**: 移除 `_run_general_agent_task` 內部的 hardcode 判斷。改為透過 Registry 動態獲取 Strategy 執行 `await strategy.execute(task_id)`。
- [x] **1.4 整合測試通過**: 確保所有策略在整合測試中均能正確運作並通過綠燈。

### Milestone 2: Pydantic 型別防護網 (JSONB Boundary Validation)
- [x] **2.1 定義 Schema**: 新增 `python/src/server/schemas/agent_outputs.py`，建立 `GroupChatOutputSchema`, `LogDetailsSchema` 等嚴格的 Pydantic Models。
- [x] **2.2 寫入攔截**: 修改 `task_service.save_agent_output`，在寫入 Supabase 前強制呼叫 `schema.model_validate` 進行檢驗。
- [x] **2.3 讀取轉型**: 修改 `get_task` 等查詢函式，將 DB 回傳的 JSONB 轉型為強型別 Python 物件，確保後續業務邏輯受到 MyPy 保護。

### Milestone 3: 資料庫結構一致性清理 (Database Integrity Clean-up)
- [x] **3.1 遷移腳本**: 產生 `migration/20260515_harden_agent_outputs.sql`，將舊的 `attachments` 陣列中的物件轉換為具備 `output_type` 與 `metadata` 的新格式。
- [x] **3.2 深度修復**: 針對 Supervisor 的 JSONB 內容，若偵測到 legacy 欄位（如 `response_text`），自動映射為 `summary`。
- [x] **3.3 真實環境驗證**: 向使用者請求授權，在 Supabase Cloud 執行該遷移腳本並觀察結果。

### Milestone 4: 任務佇列與效能解耦 (Queue & Worker Architecture)
- [x] **4.1 引入 DB Queue (或 Celery)**: 取代 `GlobalThrottler` 中的 `asyncio.sleep`。在前端發出請求時，僅將 Task 寫入資料庫並回傳 `202 Accepted`。
- [x] **4.2 實作 Async Worker**: 撰寫獨立的背景 Worker 進程，依據當前的 API 速率限制 (Rate Limit Tokens) 從 Queue 中拉取任務執行，徹底消除 HTTP Request 的物理阻塞。

### Milestone 5: 狀態單一真實來源與 SSE 同步 (State Synchronization)
- [x] **5.1 確立 SSOT**: 宣告 `archon_tasks.status` 為全系統唯一的狀態真相。
- [x] **5.2 後端事件推播**: 當 LangGraph (WorkflowEngine) 完成一個節點的執行時，更新 DB 並透過 Server-Sent Events (SSE) 或 WebSocket 發布狀態變更事件。
- [x] **5.3 前端狀態機降級**: 修改 `salesCartMachine.ts` 等前端狀態機，將其降級為「純粹接收 SSE Event 並切換 UI」的被動狀態機，移除主動輪詢與自我推斷邏輯。

### Milestone 6: 測試準則與維護成本優化 (MBT Guidelines)
- [x] **6.1 確立測試邊界**: 撰寫 `PRPs/ai_docs/UI_TESTING_GUIDELINES.md`，明訂只有跨模組的核心業務 (如 Persona Workflow) 才需強制使用 XState + Playwright MBT。
- [x] **6.2 引入視覺容忍度**: 在 Playwright 設定中引入 Visual Regression Testing (VRT) 的 `maxDiffPixelRatio`，避免微小的 CSS 調整引發 E2E 測試連鎖崩鎖。

---

## 3. 潛在風險與防禦計畫 (Risk Mitigation)
*   **歷史資料不相容**: 導入 Milestone 2 (Pydantic 驗證) 時，可能會因為過去 `agent_output` 結構不一致引發 `ValidationError`。**防禦**: 撰寫 `migration/0.3.0/sanitize_jsonb_data.py` 腳本，在啟動新版 API 前清洗所有歷史資料。
*   **SSE 斷線重連**: Milestone 4 依賴長連線，行動網路可能不穩定。**防禦**: 實作 Event ID 與 Last-Event-ID 機制，確保重連後能拉取斷線期間錯失的狀態變更。

---

## 4. 核心工程教訓 (Core Engineering Lessons Recorded)
1. **「功能完成」不等於「物理對齊」**：Phase 5.0.2 的幽靈開發教訓告訴我們，新增了完美的方法 (`_run_workflow_engine_task`) 卻沒有在主控制流中呼叫，只是一種自我安慰的「樂觀路徑」。未來的每一個核心交流道，都必須強制綁定 `@patch` 斷言測試 (Anti-Ghost Test) 來確保物理貫通。
2. **極致的彈性往往是技術債的溫床**：為了迭代速度過度濫用 JSONB，帶來了嚴重的型別失憶症，導致編譯期的靜態檢查 (MyPy) 對這些欄位完全失效。架構的彈性必須建立在「邊界強校驗 (Boundary Validation, 如 Pydantic)」之上，否則資料庫久而久之只會變成無結構的未爆彈。
3. **沒有不勞而獲的擴展性**：將架構與 Free Tier 綁定（例如在核心調度中寫死 `sleep` 以迴避 429 錯誤），在初期雖然能快速且低成本上線，但這本質上是一種「效能技術債」。真正的企業級架構必須正視非同步佇列 (Queue) 與 Worker 的必要性，以工程手段 (非同步消化) 解決物理限制，而不是用逃避的方式 (單執行緒阻塞)。
4. **狀態撕裂是分散式系統的隱形殺手**：前端、後端與資料庫若各自為政維護狀態機，必然導致最終的狀態不一致（如前端顯示完成但後端還在跑）。我們必須堅持單一真實來源 (SSOT) 原則，並勇敢地將前端降級為單純的被動事件接收器 (Event Listener)。

---

## 5. 下一步 (Next Steps)
*   等待架構師與團隊進行技術審查 (Tech Review)。
*   審查通過後，優先由 Milestone 1 (策略模式) 開始動工，以隔離後續擴展新 Agent 時的風險。
